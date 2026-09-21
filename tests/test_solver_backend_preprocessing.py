"""T18: real XLSX fixtures crossing Python preprocessing 1.0 into solver 1.1.

These checks exercise static delivery and receipt gates, not MATLAB execution.
Numerical values and receipts are explicitly synthetic repository fixtures.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

import openpyxl
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_code_delivery as CODE
import validate_user_execution as RECEIPT
from tests import test_audit_workbook_lifecycle as lifecycle_fixtures
from tests import test_solver_backends as solver_fixtures


class SolverBackendPreprocessingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.prepare_root(Path(temporary.name))

    def prepare_root(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "state").mkdir()
        (self.root / "问题一求解").mkdir()
        (self.root / "data").mkdir()
        raw = self.root / "data/raw.csv"
        raw.write_text("key,value\nA,1\n", encoding="utf-8")
        self.raw_hash = hashlib.sha256(raw.read_bytes()).hexdigest()
        self.solver = solver_fixtures.SolverBackendTests()
        self.solver.root = self.root
        self.pre_config = self.solver.config(
            stage="preprocessing", problem_name="数据预处理", data_paths=["data/raw.csv"],
            data_sha256=self.raw_hash, expected_workbook="数据预处理结果.xlsx",
            run_receipt_protocol_version="1.0.0",
        )
        for field in ("solver_backend", "code_dependencies"):
            self.pre_config.pop(field)
        folder = self.root / "数据预处理"
        folder.mkdir()
        self.pre_code = folder / "数据预处理.py"
        self.write_pre_code()
        self.pre_workbook = folder / "数据预处理结果.xlsx"
        self.state = {
            "project": {"current_phase": "data_preprocessing"},
            "data": {"version_hashes": {"preprocessing_input": self.raw_hash}},
            "preprocessing": {
                "decision": "project_level", "status": "awaiting_user_execution", "quality_status": "pending",
                "code": self.pre_code.relative_to(self.root).as_posix(),
                "code_sha256": hashlib.sha256(self.pre_code.read_bytes()).hexdigest(),
                "covered_raw_sources": ["data/raw.csv"],
            },
            "subproblems": {"Q1": {"status": "designed"}},
        }
        self.save_state()

    def write_pre_code(self):
        self.pre_code.write_text(
            f"RUN_CONFIG = {self.pre_config!r}\ndef main():\n    return 0\n"
            "if __name__ == '__main__':\n    main()\n", encoding="utf-8",
        )

    def save_state(self):
        (self.root / "state/project_state.yaml").write_text(
            yaml.safe_dump(self.state, allow_unicode=True, sort_keys=False), encoding="utf-8",
        )

    def preprocessing_workbook(self, version="1.0.0"):
        fixture = lifecycle_fixtures.WorkbookLifecycleTests()
        _, receipt = fixture.config_sheets()
        receipt.update({name: self.pre_config[name] for name in RECEIPT.RUN_RECEIPT_ECHO_FIELDS})
        receipt.update(run_receipt_version=version, code_sha256=hashlib.sha256(self.pre_code.read_bytes()).hexdigest())
        sheets = fixture.preprocessing_sheets()
        sheets["模型输入"] = [
            ["coefficient", "right_hand_side", "sensitivity_coefficients"],
            [2, 6, "[1.5,2,3]"],
        ]
        sheets["运行配置"] = [["项目", "值"], *receipt.items()]
        book = openpyxl.Workbook()
        book.remove(book.active)
        for name, rows in sheets.items():
            sheet = book.create_sheet(name)
            for row in rows:
                sheet.append(row)
        book.save(self.pre_workbook)
        book.close()

    def accept_preprocessing(self):
        self.preprocessing_workbook()
        self.assertEqual(CODE.validate_script(self.root, self.pre_code, "preprocessing")[0], [])
        self.assertEqual(RECEIPT.validate_one(self.root, self.pre_workbook, self.state, True), [])
        self.assertEqual(self.state["preprocessing"]["status"], "accepted")
        self.assertEqual(self.state["preprocessing"]["quality_status"], "passed")
        self.assertNotIn("solver_execution", self.state["preprocessing"])
        self.assertNotIn("bundle_sha256", self.state["preprocessing"])
        self.save_state()
        return hashlib.sha256(self.pre_workbook.read_bytes()).hexdigest()

    def primary_config(self, digest):
        return self.solver.config(
            "matlab", data_paths=[self.pre_workbook.relative_to(self.root).as_posix()], data_sha256=digest,
            data_identity_mode="preprocessing_workbook",
        )

    def test_accepted_preprocessing_10_file_hash_is_inherited_by_matlab_11_receipt(self):
        digest = self.accept_preprocessing()
        preprocessing = deepcopy(self.state["preprocessing"])
        config = self.primary_config(digest)
        code = self.solver.source(config)
        self.assertEqual(CODE.validate_script(self.root, code, "primary")[0], [])
        entry = self.solver.entry(code, config)
        self.state["subproblems"]["Q1"] = entry
        self.save_state()
        bundle = entry["solver_execution"]["primary"]["bundle_sha256"]
        workbook = self.solver.primary_workbook(code, config, bundle)
        self.assertEqual(RECEIPT.validate_one(self.root, workbook, self.state, True), [])
        self.assertEqual(entry["primary_execution_status"], "accepted")
        self.assertEqual(entry["validated_data_hash"], digest)
        self.assertEqual(entry["validated_artifact_hashes"]["data"], digest)
        self.assertEqual(entry["solver_execution"]["primary"]["validated_bundle_sha256"], bundle)
        self.assertEqual(self.state["preprocessing"], preprocessing)

    def test_matlab_cannot_read_covered_raw_source_even_with_correct_workbook_identity(self):
        digest = self.accept_preprocessing()
        config = self.primary_config(digest)
        for reader in ("readcell", "readtable", "readmatrix"):
            with self.subTest(reader=reader):
                code = self.solver.source(config, f"values = {reader}('data/raw.csv');")
                issues, _ = CODE.validate_script(self.root, code, "primary")
                self.assertTrue(any("不得重新读取已覆盖共享原始数据源" in issue for issue in issues), issues)
        code = self.solver.source(config, "% readcell('data/raw.csv') is only a comment")
        self.assertEqual(CODE.validate_script(self.root, code, "primary")[0], [])
        config["data_paths"].append("data/raw.csv")
        issues, _ = CODE.validate_script(self.root, self.solver.source(config), "primary")
        self.assertTrue(any("已覆盖共享原始数据源" in issue for issue in issues), issues)

    def test_matlab_cannot_substitute_raw_hash_for_preprocessing_workbook_hash(self):
        digest = self.accept_preprocessing()
        self.assertNotEqual(self.raw_hash, digest)
        config = self.primary_config(self.raw_hash)
        issues, _ = CODE.validate_script(self.root, self.solver.source(config), "primary")
        self.assertTrue(any("data_sha256必须等于已验收" in issue for issue in issues), issues)

    def test_preprocessing_cannot_deliver_or_accept_receipt_11(self):
        self.pre_config["run_receipt_protocol_version"] = "1.1.0"
        self.write_pre_code()
        self.state["preprocessing"]["code_sha256"] = hashlib.sha256(self.pre_code.read_bytes()).hexdigest()
        self.save_state()
        self.preprocessing_workbook(version="1.1.0")
        issues, _ = CODE.validate_script(self.root, self.pre_code, "preprocessing")
        self.assertTrue(any("不支持当前阶段" in issue for issue in issues), issues)
        issues = RECEIPT.validate_one(self.root, self.pre_workbook, self.state, True)
        self.assertTrue(any("版本" in issue or "version" in issue for issue in issues), issues)
        self.assertEqual(self.state["preprocessing"]["status"], "rejected")
        self.assertNotIn("solver_execution", self.state["preprocessing"])


def prepare_native_preprocessing(root: Path) -> tuple[dict, str]:
    """Prepare an accepted synthetic 1.0 XLSX for a subsequent real MATLAB run.

    This helper writes fixture data and verifies the old receipt; it does not run
    Python preprocessing or MATLAB and makes no numerical execution claim.
    """
    fixture = SolverBackendPreprocessingTests()
    fixture.prepare_root(Path(root))
    digest = fixture.accept_preprocessing()
    return deepcopy(fixture.state), digest


if __name__ == "__main__":
    unittest.main()
