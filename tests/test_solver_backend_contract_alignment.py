"""Cross-check active Authority declarations against the real schema/binding gates.

The code-delivery fixture records synthetic upstream qualification; it does not
execute a numerical model or claim that arbitrary XLSX bytes passed a user run.
"""
from copy import deepcopy
import hashlib
from pathlib import Path
import re
import sys
import tempfile
import unittest

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import artifact_fingerprint
import validate_code_delivery as code_delivery
import validate_user_execution as execution

EXECUTION = yaml.safe_load((ROOT / "core/user_execution_contract.yaml").read_text(encoding="utf-8"))
OUTPUT = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
SCHEMA = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
BINDING = EXECUTION["returned_workbook"]["versioned_receipt"]["analysis_primary_binding"]


def required_fields(version, stage):
    delivery = EXECUTION["code_delivery"]
    protocol = delivery["run_receipt_protocol"]
    returned = EXECUTION["returned_workbook"]
    receipt = returned["versioned_receipt"]
    config_fields = set(delivery["canonical_required_config_fields"])
    config_fields.update(protocol["version_required_config_fields"].get(version, []))
    config_fields.update(protocol["version_stage_required_config_fields"].get(version, {}).get(stage, []))
    config_fields.update(delivery["stage_required_config_fields"].get(stage, []))
    receipt_fields = set(returned["required_items"])
    receipt_fields.update(receipt["version_required_fields"].get(version, []))
    receipt_fields.update(receipt["version_stage_required_fields"].get(version, {}).get(stage, []))
    return config_fields, receipt_fields


def analysis_pair(version="1.1.0", backend="python"):
    values = {
        "stage": "analysis", "problem_name": "问题一", "data_paths": ["input.json"],
        "data_sha256": "a" * 64, "solver": "analytic_parameter_sweep", "random_seed": 2026,
        "tolerance": 1e-8, "iteration_or_time_limit": 3,
        "expected_workbook": "问题一求解/问题一结果深化分析.xlsx", "solver_backend": backend,
        BINDING["field"]: "c" * 64, "code_sha256": "d" * 64, "code_bundle_sha256": "e" * 64,
        "execution_owner": "user", "execution_profile": "full_fidelity", "solver_version": "fixture",
        "actual_stop_reason": "all_scenarios_completed", "repetitions_or_scenarios": 3,
        "grid_or_time_range": "declared scenarios", "fallback_used": False, "platform": "fixture",
        **{name: False for name in execution.FALSE_FLAGS},
    }
    config_fields, receipt_fields = required_fields(version, "analysis")
    config = {name: values[name] for name in config_fields}
    receipt = {name: values[name] for name in receipt_fields}
    config["run_receipt_protocol_version"] = version
    receipt["run_receipt_version"] = version
    return config, receipt


class SolverBackendContractAlignmentTests(unittest.TestCase):
    def test_advertised_current_implementation_hash_is_an_active_schema_field(self):
        semantics = OUTPUT["project_sync"]["artifact_hash_semantics"]
        validator = jsonschema.Draft202012Validator({"$ref": "#/$defs/artifact_hashes", "$defs": SCHEMA["$defs"]})
        advertised = []
        for description in semantics.values():
            advertised.extend(re.findall(r"subproblem\.artifact_hashes\.([a-z_]+)", description))
        self.assertIn("primary_code", advertised)
        for field in advertised:
            with self.subTest(field=field):
                self.assertEqual(list(validator.iter_errors({field: "a" * 64})), [])
        self.assertTrue(list(validator.iter_errors({"model": "a" * 64})))

    def test_authority_required_analysis_fields_produce_a_valid_binding(self):
        for backend in ("python", "matlab"):
            with self.subTest(backend=backend):
                config, receipt = analysis_pair(backend=backend)
                self.assertEqual(execution.validate_run_receipt_binding(receipt, config), [])

    def test_declared_analysis_upstream_is_required_in_both_interfaces(self):
        field = BINDING["field"]
        for side in ("config", "receipt"):
            for replacement in (None, "", "not-a-hash"):
                with self.subTest(side=side, replacement=replacement):
                    config, receipt = analysis_pair()
                    target = config if side == "config" else receipt
                    if replacement is None:
                        target.pop(field)
                    else:
                        target[field] = replacement
                    issues = execution.validate_run_receipt_binding(receipt, config)
                    self.assertTrue(any(field in issue for issue in issues), issues)

    def test_analysis_binding_rejects_wrong_hash_but_accepts_hex_case(self):
        config, receipt = analysis_pair()
        field = BINDING["field"]
        receipt[field] = "f" * 64
        self.assertTrue(any(field in issue for issue in execution.validate_run_receipt_binding(receipt, config)))
        receipt[field] = config[field].upper()
        self.assertEqual(execution.validate_run_receipt_binding(receipt, config), [])

    def test_legacy_analysis_does_not_inherit_the_new_version_requirement(self):
        config, receipt = analysis_pair("1.0.0")
        self.assertNotIn(BINDING["field"], config)
        self.assertNotIn(BINDING["field"], receipt)
        self.assertEqual(execution.validate_run_receipt_binding(receipt, config), [])

    def analysis_project(self, root):
        folder = root / "问题一求解"
        folder.mkdir()
        data = root / "input.json"
        data.write_text("{}", encoding="utf-8")
        primary = folder / "问题一求解.py"
        primary.write_text("def main():\n    return 0\n", encoding="utf-8")
        workbook = folder / "问题一求解结果.xlsx"
        workbook.write_bytes(b"synthetic accepted source-binding fixture; not numerical execution")
        data_sha = artifact_fingerprint.combined_hash([data], root)
        hashes = {"data": data_sha, "primary_code": hashlib.sha256(primary.read_bytes()).hexdigest(),
                  "solution_workbook": hashlib.sha256(workbook.read_bytes()).hexdigest()}
        entry = {"status": "solved", "code": primary.relative_to(root).as_posix(),
                 "primary_code_sha256": hashes["primary_code"], "data_hash": data_sha,
                 "validated_data_hash": data_sha, "solution_workbook": workbook.relative_to(root).as_posix(),
                 "primary_execution_status": "accepted", "result_quality_status": "passed",
                 "result_analysis_status": "pending", "result_analysis_requirement_reason": "Check parameter sensitivity",
                 "analysis_methods": ["参数敏感性"], "artifact_hashes": hashes,
                 "validated_artifact_hashes": dict(hashes)}
        state = {"project": {"current_phase": "result_analysis"}, "subproblems": {"Q1": entry},
                 "preprocessing": {"decision": "not_needed"}}
        (root / "state").mkdir()
        (root / "state/project_state.yaml").write_text(yaml.safe_dump(state, allow_unicode=True), encoding="utf-8")
        config, receipt = analysis_pair()
        config["data_sha256"] = receipt["data_sha256"] = data_sha
        accepted = state
        for key in BINDING["accepted_state_field"].replace("<question>", "Q1").split("."):
            accepted = accepted[key]
        config[BINDING["field"]] = receipt[BINDING["field"]] = accepted
        return state, config, receipt, folder / "问题一结果深化分析.py", workbook

    def test_code_delivery_binds_declared_upstream_to_current_accepted_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state, config, receipt, script, _ = self.analysis_project(root)
            accepted = config[BINDING["field"]]
            before = deepcopy(state)
            for value, valid in ((accepted, True), (accepted.upper(), True), ("f" * 64, False)):
                with self.subTest(value=value):
                    config[BINDING["field"]] = receipt[BINDING["field"]] = value
                    self.assertEqual(execution.validate_run_receipt_binding(receipt, config), [])
                    script.write_text(f"RUN_CONFIG = {config!r}\n\ndef main():\n    return 0\n\nif __name__ == '__main__':\n    main()\n", encoding="utf-8")
                    issues, _ = code_delivery.validate_script(root, script, "analysis")
                    if valid:
                        self.assertEqual(issues, [])
                    else:
                        self.assertTrue(any("accepted主工作簿" in issue for issue in issues), issues)
            after = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
            self.assertEqual(after, before)

    def test_changed_accepted_file_does_not_become_valid_through_matching_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, config, receipt, script, workbook = self.analysis_project(root)
            workbook.write_bytes(b"different upstream bytes")
            script.write_text(f"RUN_CONFIG = {config!r}\n\ndef main():\n    return 0\n\nif __name__ == '__main__':\n    main()\n", encoding="utf-8")
            self.assertEqual(execution.validate_run_receipt_binding(receipt, config), [])
            issues, _ = code_delivery.validate_script(root, script, "analysis")
            self.assertTrue(any("主工作簿" in issue and "哈希" in issue for issue in issues), issues)


if __name__ == "__main__":
    unittest.main()
