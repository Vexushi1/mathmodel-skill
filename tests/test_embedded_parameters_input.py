from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from artifact_fingerprint import combined_hash, embedded_parameters_hash
from stage_inputs import (
    data_input_files,
    declared_input_files,
    input_files,
    observe_inputs,
)
from validate_code_delivery import _required_config_field_missing


class EmbeddedParametersInputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.parameters = {
            "semi_major": 1.5,
            "eccentricity": 0.1,
            "observer_radius": 1.0,
            "nodes": 512,
            "inclinations_deg": [0, 30, 60, 90],
        }
        self.digest = embedded_parameters_hash(self.parameters)
        self.config = {
            "stage": "primary",
            "problem_name": "问题一",
            "solver_backend": "python",
            "run_receipt_protocol_version": "1.3.0",
            "data_identity_mode": "embedded_parameters",
            "data_paths": [],
            "data_sha256": self.digest,
            "embedded_parameters": self.parameters,
        }
        self.state = {"preprocessing": {"decision": "not_needed"}}

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_embedded_parameters_are_canonical_and_order_independent(self) -> None:
        reordered = {
            "nodes": 512,
            "inclinations_deg": [0, 30, 60, 90],
            "observer_radius": 1.0,
            "eccentricity": 0.1,
            "semi_major": 1.5,
        }
        self.assertEqual(embedded_parameters_hash(self.parameters), embedded_parameters_hash(reordered))
        changed = dict(reordered, semi_major=1.6)
        self.assertNotEqual(embedded_parameters_hash(self.parameters), embedded_parameters_hash(changed))

    def test_embedded_parameters_reject_non_json_or_nonfinite_values(self) -> None:
        for value in ({}, {"bad": float("nan")}, {"bad": float("inf")}, {"bad": (1, 2)}, {1: "bad"}):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    embedded_parameters_hash(value)

    def test_no_external_file_mode_returns_empty_input_set_and_stable_identity(self) -> None:
        self.assertEqual(data_input_files(self.root, self.config), [])
        self.assertEqual(declared_input_files(self.root, self.config), [])
        observed = observe_inputs(self.root, self.config, self.state)
        self.assertEqual(observed["paths"], [])
        self.assertEqual(observed["data_identity_mode"], "embedded_parameters")
        self.assertEqual(observed["data_sha256"], self.digest)
        self.assertEqual(observed["embedded_parameters_sha256"], self.digest)
        self.assertEqual(observed["issues"], [])

    def test_parameter_digest_mismatch_is_reported_and_not_inventoried(self) -> None:
        config = {**self.config, "data_sha256": "0" * 64}
        observed = observe_inputs(self.root, config, self.state)
        self.assertTrue(any("内置参数data_sha256" in item for item in observed["issues"]))
        with self.assertRaises(ValueError):
            data_input_files(self.root, config)

    def test_embedded_mode_rejects_nonempty_or_missing_data_paths(self) -> None:
        for paths in (["problem.pdf"], None):
            with self.subTest(paths=paths):
                config = {**self.config, "data_paths": paths}
                with self.assertRaises(ValueError):
                    data_input_files(self.root, config)

    def test_embedded_mode_is_python_primary_or_analysis_only(self) -> None:
        for update in (
            {"solver_backend": "matlab"},
            {"stage": "preprocessing"},
            {"run_receipt_protocol_version": "1.2.0"},
        ):
            with self.subTest(update=update):
                with self.assertRaises(ValueError):
                    data_input_files(self.root, {**self.config, **update})

    def test_embedded_mode_rejects_auxiliary_files_and_project_level_preprocessing(self) -> None:
        config = {
            **self.config,
            "auxiliary_data_paths": ["extra.csv"],
            "auxiliary_data_sha256": "1" * 64,
        }
        with self.assertRaises(ValueError):
            declared_input_files(self.root, config)
        with self.assertRaises(ValueError):
            observe_inputs(self.root, self.config, {
                "preprocessing": {
                    "decision": "project_level",
                    "status": "accepted",
                    "quality_status": "passed",
                }
            })

    def test_empty_data_paths_are_required_only_in_embedded_mode(self) -> None:
        self.assertFalse(_required_config_field_missing(self.config, "data_paths"))
        combined = {**self.config, "data_identity_mode": "combined"}
        self.assertTrue(_required_config_field_missing(combined, "data_paths"))

    def test_file_backed_combined_mode_remains_unchanged(self) -> None:
        source = self.root / "source.csv"
        source.write_text("x\\n1\\n", encoding="utf-8")
        digest = combined_hash([source], self.root)
        config = {
            "stage": "primary",
            "problem_name": "问题一",
            "solver_backend": "python",
            "run_receipt_protocol_version": "1.1.0",
            "data_identity_mode": "combined",
            "data_paths": ["source.csv"],
            "data_sha256": digest,
        }
        observed = observe_inputs(self.root, config, self.state)
        self.assertEqual(observed["paths"], ["source.csv"])
        self.assertEqual(observed["data_sha256"], digest)
        self.assertEqual(observed["issues"], [])

    def test_input_files_remains_strict_for_actual_files(self) -> None:
        with self.assertRaises(ValueError):
            input_files(self.root, [])


if __name__ == "__main__":
    unittest.main()
