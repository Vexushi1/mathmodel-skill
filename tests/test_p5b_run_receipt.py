from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


CODE = load_module("p5b_validate_code_delivery", ROOT / "scripts" / "validate_code_delivery.py")
RECEIPT = load_module("p5b_validate_user_execution", ROOT / "scripts" / "validate_user_execution.py")


class P5bRunReceiptTests(unittest.TestCase):
    def delivered(self, *, version: str | None = "1.0.0") -> dict:
        config = {
            "stage": "analysis",
            "problem_name": "问题一",
            "data_paths": ["data.csv"],
            "data_sha256": "a" * 64,
            "solver": "BDF",
            "random_seed": 2026,
            "tolerance": 1e-8,
            "iteration_or_time_limit": "full",
            "expected_workbook": "问题一求解/问题一结果深化分析.xlsx",
        }
        if version is not None:
            config["run_receipt_protocol_version"] = version
        return config

    def receipt(self, *, version: str | None = "1.0.0") -> dict:
        receipt = {
            "stage": "analysis",
            "problem_name": "问题一",
            "data_sha256": "a" * 64,
            "solver": "BDF",
            "random_seed": 2026,
            "tolerance": 1e-8,
            "iteration_or_time_limit": "full",
        }
        if version is not None:
            receipt["run_receipt_version"] = version
        return receipt

    def write_script(self, root: Path, protocol: str | None) -> Path:
        (root / "state").mkdir(exist_ok=True)
        (root / "state/project_state.yaml").write_text(yaml.safe_dump({
            "project": {"current_phase": "solve_validate"},
            "execution": {"solver_backend": "python", "solver_backend_selection_reason": "全题审视"},
            "preprocessing": {"decision": "not_needed"},
            "subproblems": {"Q1": {"status": "designed"}},
        }, allow_unicode=True), encoding="utf-8")
        folder = root / "问题一求解"
        folder.mkdir(parents=True, exist_ok=True)
        script = folder / "问题一求解.py"
        config = {
            "stage": "primary",
            "problem_name": "问题一",
            "data_paths": ["data.csv"],
            "data_sha256": "a" * 64,
            "solver": "BDF",
            "random_seed": 2026,
            "tolerance": 1e-8,
            "iteration_or_time_limit": "full",
            "expected_workbook": "问题一求解/问题一求解结果.xlsx",
            "primary_quality_protocol_version": "1.0.0",
        }
        from artifact_fingerprint import combined_hash
        data = root / "data.csv"
        data.write_text("x,y\n1,2\n", encoding="utf-8")
        config["data_sha256"] = combined_hash([data], root)
        if protocol is not None:
            config["run_receipt_protocol_version"] = protocol
        if protocol == "1.1.0":
            config.update(solver_backend="python", code_dependencies=[])
        script.write_text(
            "RUN_CONFIG = " + repr(config)
            + "\n\ndef main():\n    return 0\n\nif __name__ == \"__main__\":\n    raise SystemExit(main())\n",
            encoding="utf-8",
        )
        return script

    def test_v1_handshake_and_echo_pass(self):
        self.assertEqual(
            RECEIPT.validate_run_receipt_binding(self.receipt(), self.delivered()),
            [],
        )

    def test_bound_protocol_cannot_downgrade_to_unversioned_receipt(self):
        issues = RECEIPT.validate_run_receipt_binding(
            self.receipt(version=None), self.delivered()
        )
        self.assertTrue(any("不得通过省略版本标记" in item for item in issues))

    def test_declared_unknown_receipt_version_fails_closed(self):
        issues = RECEIPT.validate_run_receipt_binding(
            self.receipt(version="2.0.0"), self.delivered(version=None)
        )
        self.assertTrue(any("run_receipt_version不受支持" in item for item in issues))

    def test_p5a_transitional_unversioned_pair_remains_read_compatible(self):
        self.assertEqual(
            RECEIPT.validate_run_receipt_binding(
                self.receipt(version=None), self.delivered(version=None)
            ),
            [],
        )

    def test_versioned_receipt_requires_delivered_code_binding(self):
        issues = RECEIPT.validate_run_receipt_binding(self.receipt(), None)
        self.assertTrue(any("必须能静态绑定已交付阶段代码" in item for item in issues))

    def test_echo_mismatch_is_rejected(self):
        receipt = self.receipt()
        receipt["solver"] = "Radau"
        issues = RECEIPT.validate_run_receipt_binding(receipt, self.delivered())
        self.assertTrue(any("RUN_RECEIPT.solver" in item for item in issues))

    def test_numeric_excel_coercion_does_not_create_false_mismatch(self):
        receipt = self.receipt()
        receipt["tolerance"] = "0.00000001"
        receipt["random_seed"] = "2026"
        self.assertEqual(
            RECEIPT.validate_run_receipt_binding(receipt, self.delivered()),
            [],
        )

    def test_code_delivery_requires_current_marker_while_transitional_pair_stays_read_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            current = self.write_script(root, "1.1.0")
            issues, _ = CODE.validate_script(root, current, "primary")
            self.assertEqual(issues, [])
            current.unlink()
            transitional = self.write_script(root, None)
            issues, _ = CODE.validate_script(root, transitional, "primary")
            self.assertTrue(any("项目后端" in item for item in issues), issues)
            self.assertEqual(RECEIPT.validate_run_receipt_binding(
                self.receipt(version=None), self.delivered(version=None)), [])

    def test_code_delivery_rejects_unknown_protocol_marker(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            script = self.write_script(root, "2.0.0")
            issues, _ = CODE.validate_script(root, script, "primary")
            self.assertTrue(any("run_receipt_protocol_version" in item for item in issues))


if __name__ == "__main__":
    unittest.main()
