"""Retired numerical files remain visible without regaining current qualification."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import artifact_fingerprint
import stage_code
import sync_project
from submission_requirements import reproducibility_requirements
from validate_model_paper_framework import _implementation_anchor_issues
from tests.test_sync_project import framework_text, write_solution, write_state


def _save(root: Path, state: dict) -> None:
    (root / "state/project_state.yaml").write_text(
        yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8",
    )


def _fixture(root: Path, *, delivered: bool = False) -> dict:
    write_state(root, phase="model_design")
    (root / "模型论文框架.md").write_text(framework_text(), encoding="utf-8")
    folder = root / "问题一求解"
    folder.mkdir()
    (root / "input.json").write_text("{}", encoding="utf-8")
    (folder / "q1_solver.m").write_text("function q1_solver()\nend\n", encoding="utf-8")
    (folder / "问题一结果深化分析.py").write_text("# retired analysis\n", encoding="utf-8")
    (folder / "q1_analysis.m").write_text("function q1_analysis()\nend\n", encoding="utf-8")
    (folder / "q1_plot.m").write_text("% formal figure program\n", encoding="utf-8")
    write_solution(folder / "问题一求解结果.xlsx")
    write_solution(folder / "问题一结果深化分析.xlsx")

    state = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
    state["execution"] = {
        "solver_backend": "python", "solver_backend_selection_reason": "Whole-problem numerical capability review",
    }
    state["preprocessing"] = {"decision": "not_needed"}
    state["data"] = {"sources": [{"name": "input", "path": "input.json", "role": "raw"}]}
    if delivered:
        code = folder / "问题一求解.py"
        data_hash = artifact_fingerprint.combined_hash([root / "input.json"], root)
        config = {
            "stage": "primary", "problem_name": "问题一", "solver_backend": "python",
            "run_receipt_protocol_version": "1.1.0", "data_paths": ["input.json"],
            "data_sha256": data_hash, "data_identity_mode": "combined", "solver": "fixture",
            "random_seed": 0, "tolerance": 1e-8, "iteration_or_time_limit": 1,
            "expected_workbook": "问题一求解/问题一求解结果.xlsx", "code_dependencies": [],
        }
        code.write_text("RUN_CONFIG = " + repr(config) + "\n\ndef main():\n    return 3\n", encoding="utf-8")
        fingerprint = stage_code.stage_code_fingerprint(root, code)
        workbook = folder / "问题一求解结果.xlsx"
        entry = state["subproblems"]["Q1"]
        entry.update(
            status="solved", code=code.relative_to(root).as_posix(),
            primary_code_sha256=fingerprint["entry_sha256"],
            solution_workbook=workbook.relative_to(root).as_posix(),
            matlab_script="问题一求解/q1_plot.m", data_hash=data_hash,
            validated_data_hash=data_hash, primary_execution_status="accepted",
            result_quality_status="passed", result_analysis_status="not_required",
            result_analysis_requirement_reason="Current result needs no extra analysis",
            result_summary_status="current", result_summary_anchor="### Q1",
            solver_execution={"primary": {
                "bundle_sha256": fingerprint["bundle_sha256"],
                "validated_bundle_sha256": fingerprint["bundle_sha256"],
            }},
        )
        hashes = {
            "data": data_hash, "primary_code": fingerprint["entry_sha256"],
            "solution_workbook": hashlib.sha256(workbook.read_bytes()).hexdigest(),
        }
        entry["artifact_hashes"] = dict(hashes)
        entry["validated_artifact_hashes"] = dict(hashes)
        for relative in ("final_latex/main.tex", "final_latex/main.pdf"):
            path = root / relative
            path.parent.mkdir(exist_ok=True)
            path.write_text("synthetic package fixture", encoding="utf-8")
    else:
        (folder / "问题一求解.py").write_text("# retired Python source\n", encoding="utf-8")
    _save(root, state)
    return state


class RetiredArtifactIsolationTests(unittest.TestCase):
    def test_two_syncs_observe_unregistered_files_without_rebinding_them(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _fixture(root)
            orphan = root / "问题二求解"
            orphan.mkdir()
            (orphan / "q2_solver.m").write_text("function q2_solver()\nend\n", encoding="utf-8")
            for _ in range(2):
                report = sync_project.synchronize(root, write=True)
                q1 = report["questions"]["Q1"]
                self.assertIsNone(q1["primary_code"])
                self.assertIsNone(q1["solution_workbook"])
                self.assertIn("问题一求解/问题一求解结果.xlsx", q1["historical_workbooks"])
                self.assertIn("问题一求解/q1_solver.m", q1["solver_execution_observed"]["primary"]["historical_entrypoints"])
                saved = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
                self.assertNotIn("Q2", saved["subproblems"])
                entry = saved["subproblems"]["Q1"]
                for field in ("code", "solution_workbook", "result_analysis_code", "result_analysis_workbook"):
                    self.assertNotIn(field, entry)
                self.assertFalse({"primary_code", "solution_workbook", "analysis_code", "result_analysis_workbook"}
                                 & set(entry["artifact_hashes"]))

    def test_package_requires_registered_current_source_and_excludes_retired_analysis(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = _fixture(root, delivered=True)
            required, issues = reproducibility_requirements(root, state)
            self.assertEqual(issues, [])
            self.assertIn("问题一求解/问题一求解.py", required)
            self.assertIn("问题一求解/q1_plot.m", required)  # Formal MATLAB figures are independent.
            self.assertNotIn("问题一求解/q1_solver.m", required)
            self.assertNotIn("问题一求解/q1_analysis.m", required)
            self.assertNotIn("问题一求解/问题一结果深化分析.py", required)
            self.assertNotIn("问题一求解/问题一结果深化分析.xlsx", required)
            entry = state["subproblems"]["Q1"]
            self.assertEqual(_implementation_anchor_issues(
                entry["code"] + "#main", entry, root, project_backend="python",
            ), [])
            self.assertTrue(_implementation_anchor_issues(
                "问题一求解/q1_solver.m", entry, root, project_backend="python",
            ))

            entry.pop("code")
            _, issues = reproducibility_requirements(root, state)
            self.assertTrue(any("code缺少当前状态登记" in issue for issue in issues), issues)

    def test_not_required_rejects_residual_current_analysis_binding(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = _fixture(root, delivered=True)
            entry = state["subproblems"]["Q1"]
            entry["solver_execution"]["analysis"] = {"bundle_sha256": "a" * 64}
            _, issues = reproducibility_requirements(root, state)
            self.assertTrue(any("not_required阶段仍登记" in issue for issue in issues), issues)

    def test_legacy_policy_conflict_does_not_write_or_promote_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = _fixture(root)
            state["subproblems"]["Q1"]["solver_execution"] = {
                "primary": {"backend": "matlab", "selection_reason": "retired v9 choice"},
            }
            _save(root, state)
            before = (root / "state/project_state.yaml").read_bytes()
            report = sync_project.synchronize(root, write=True)
            self.assertEqual(report["status"], "failed")
            self.assertFalse(report["write_performed"])
            self.assertEqual((root / "state/project_state.yaml").read_bytes(), before)
            self.assertFalse((root / "sync_report.yaml").exists())
            _, issues = reproducibility_requirements(root, state)
            self.assertTrue(any("项目数值后端" in issue for issue in issues))

    def test_registered_workbook_needs_standard_path_and_validated_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = _fixture(root, delivered=True)
            entry = state["subproblems"]["Q1"]
            workbook = root / entry["solution_workbook"]
            retired = workbook.with_name("old_result.xlsx")
            retired.write_bytes(workbook.read_bytes())
            entry["solution_workbook"] = retired.relative_to(root).as_posix()
            _, issues = reproducibility_requirements(root, state)
            self.assertTrue(any("不是当前标准工作簿" in issue for issue in issues), issues)

            entry["solution_workbook"] = workbook.relative_to(root).as_posix()
            workbook.write_bytes(workbook.read_bytes() + b"changed")
            _, issues = reproducibility_requirements(root, state)
            self.assertTrue(any("已验收SHA-256绑定不一致" in issue for issue in issues), issues)


if __name__ == "__main__":
    unittest.main()
