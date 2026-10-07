from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import artifact_fingerprint
import stage_code
from submission_requirements import current_analysis_artifacts
from tests.test_audit_package_completeness import (
    PACK, VALIDATOR, archive, compile_fixture, complete_project, save_state,
)


def write_files(root, names):
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(("historical fixture: " + name).encode("utf-8"))


def bind_primary(root, state, config, *, body="", backend="python"):
    entry = state["subproblems"]["Q1"]
    if backend == "matlab":
        entry["code"] = "问题一求解/q1_solver.m"
    code = root / entry["code"]
    config["solver_backend"] = backend
    if backend == "matlab":
        literal = json.dumps(config, ensure_ascii=False).replace("'", "''")
        text = f"function {code.stem}()\nRUN_CONFIG=jsondecode('{literal}');\nend\n"
    else:
        text = f"RUN_CONFIG={config!r}\n{body}\ndef main():\n    return 0\n"
    code.write_text(text, encoding="utf-8")
    identity = stage_code.stage_code_fingerprint(root, code, config.get("code_dependencies", []))
    entry["primary_code_sha256"] = identity["entry_sha256"]
    entry["solver_execution"]["primary"] = {
        "bundle_sha256": identity["bundle_sha256"],
        "validated_bundle_sha256": identity["bundle_sha256"],
    }
    for hashes in (entry["artifact_hashes"], entry["validated_artifact_hashes"]):
        hashes["primary_code"] = identity["entry_sha256"]
        hashes["data"] = config["data_sha256"]
    entry["data_hash"] = entry["validated_data_hash"] = config["data_sha256"]
    save_state(root, state)


class SubmissionCurrentArtifactsTests(unittest.TestCase):
    def test_not_required_excludes_exact_residuals_and_preserves_ordinary_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = complete_project(root, questions=1)
            residuals = {
                "问题一求解/问题一结果深化分析.py", "问题一求解/q1_analysis.m",
                "问题一求解/问题一结果深化分析.xlsx", "问题一结果深化分析.py",
                "结果数据表/问题一/问题一敏感性与鲁棒性结果.xlsx",
            }
            ordinary = {
                "附件/嵌套/问题一结果深化分析.xlsx", "附件/q1_analysis.m",
                "问题一求解/分析说明.txt", "参数分析.txt",
            }
            write_files(root, residuals | ordinary)
            compile_fixture(root, state)
            package = archive(root)
            with zipfile.ZipFile(package) as bundle:
                names = set(bundle.namelist())
            self.assertFalse(residuals & names)
            self.assertTrue(ordinary <= names)
            self.assertTrue({"final_latex/main.log", "final_latex/main.fls"} <= names)
            self.assertTrue(all((root / name).is_file() for name in residuals))
            report = VALIDATOR.validate_package(root, package)
            self.assertEqual(report["status"], "passed", report)

    def test_manual_zip_cannot_reintroduce_unselected_analysis_with_valid_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            complete_project(root, questions=1)
            residual = "问题一求解/问题一结果深化分析.xlsx"
            write_files(root, [residual])
            output = root / "submission/fixture.zip"
            selected = PACK.reproducibility_files(root, output)
            package = archive(root, files=[*selected, root / residual])
            report = VALIDATOR.validate_package(root, package)
            self.assertEqual(report["status"], "failed", report)
            self.assertTrue(any(residual in issue for issue in report["issues"]), report)

    def test_analysis_selection_is_per_question_and_current_backend(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = complete_project(root, analysis="passed")
            inactive = state["subproblems"]["Q2"]
            inactive["result_analysis_status"] = "not_required"
            inactive["result_analysis_requirement_reason"] = "No current alternative-world claim"
            for field in ("result_analysis_code", "result_analysis_workbook", "analysis_code_sha256",
                          "analysis_execution_status"):
                inactive.pop(field, None)
            inactive["solver_execution"].pop("analysis")
            for field in ("artifact_hashes", "validated_artifact_hashes"):
                inactive[field].pop("analysis_code", None)
                inactive[field].pop("result_analysis_workbook", None)
            save_state(root, state)
            write_files(root, ["问题一求解/q1_analysis.m"])
            package = archive(root)
            with zipfile.ZipFile(package) as bundle:
                names = set(bundle.namelist())
            active_paths = {state["subproblems"]["Q1"][field] for field in (
                "result_analysis_code", "result_analysis_workbook",
            )}
            self.assertTrue(active_paths <= names)
            self.assertNotIn("问题一求解/q1_analysis.m", names)
            self.assertFalse(any(name.startswith("问题二求解/") and "结果深化分析" in name for name in names))
            report = VALIDATOR.validate_package(root, package)
            self.assertEqual(report["status"], "passed", report)
            for missing in active_paths:
                with self.subTest(missing=missing):
                    self.assertEqual(VALIDATOR.validate_package(root, archive(root, omit=[missing]))["status"], "failed")

    def test_matlab_primary_survives_not_required_residual_analysis(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = complete_project(root, questions=1)
            _, config = stage_code.parse_stage_config(root / state["subproblems"]["Q1"]["code"])
            state["execution"]["solver_backend"] = "matlab"
            bind_primary(root, state, config, backend="matlab")
            residuals = {"问题一求解/q1_analysis.m", "问题一求解/问题一结果深化分析.py",
                         "问题一求解/问题一结果深化分析.xlsx"}
            write_files(root, residuals)
            package = archive(root)
            with zipfile.ZipFile(package) as bundle:
                names = set(bundle.namelist())
            self.assertIn("问题一求解/q1_solver.m", names)
            self.assertFalse(residuals & names)
            report = VALIDATOR.validate_package(root, package)
            self.assertEqual(report["status"], "passed", report)

    def test_contract_named_file_required_as_current_helper_or_input_is_kept(self):
        for role in ("helper", "input"):
            with self.subTest(role=role), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                state = complete_project(root, questions=1)
                entry = state["subproblems"]["Q1"]
                _, config = stage_code.parse_stage_config(root / entry["code"])
                if role == "helper":
                    relative = "问题一结果深化分析.py"
                    (root / relative).write_text("VALUE = 1\n", encoding="utf-8")
                    config["code_dependencies"] = [{"path": relative, "sha256": hashlib.sha256((root / relative).read_bytes()).hexdigest()}]
                    body = "import 问题一结果深化分析"
                else:
                    relative = "问题一求解/问题一结果深化分析.xlsx"
                    write_files(root, [relative])
                    config["data_paths"].append(relative)
                    config["data_sha256"] = artifact_fingerprint.combined_hash(
                        [root / name for name in config["data_paths"]], root,
                    )
                    body = ""
                bind_primary(root, state, config, body=body)
                package = archive(root)
                with zipfile.ZipFile(package) as bundle:
                    self.assertIn(relative, bundle.namelist())
                report = VALIDATOR.validate_package(root, package)
                self.assertEqual(report["status"], "passed", report)

    def test_pending_and_invalid_not_required_are_not_qualified_by_collection(self):
        for disposition in ("pending", "reasonless", "registered"):
            with self.subTest(disposition=disposition), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                state = complete_project(root, questions=1)
                entry = state["subproblems"]["Q1"]
                if disposition == "pending":
                    entry["result_analysis_status"] = "pending"
                elif disposition == "reasonless":
                    entry.pop("result_analysis_requirement_reason")
                else:
                    entry["result_analysis_workbook"] = "问题一求解/问题一结果深化分析.xlsx"
                    write_files(root, [entry["result_analysis_workbook"]])
                save_state(root, state)
                report = VALIDATOR.validate_package(root, archive(root))
                self.assertEqual(report["status"], "failed", report)

    def test_unrelated_artifact_registration_does_not_exempt_inactive_analysis(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = complete_project(root, questions=1)
            residual = "问题一求解/问题一结果深化分析.xlsx"
            write_files(root, [residual])
            state["artifacts"]["approved_figures"] = [residual]
            save_state(root, state)
            output = root / "submission/fixture.zip"
            selected = PACK.reproducibility_files(root, output)
            self.assertNotIn(root / residual, selected)
            report = VALIDATOR.validate_package(root, archive(root, files=[*selected, root / residual]))
            self.assertEqual(report["status"], "failed", report)
            self.assertTrue(any(residual in issue for issue in report["issues"]), report)

    def test_legacy_backup_without_root_backend_does_not_acquire_modern_qualification(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = complete_project(root, questions=1)
            state.pop("execution")
            save_state(root, state)
            residual = "问题一求解/问题一结果深化分析.xlsx"
            write_files(root, [residual])
            package = archive(root)
            with zipfile.ZipFile(package) as bundle:
                self.assertIn(residual, bundle.namelist())
            self.assertEqual(VALIDATOR.validate_package(root, package)["status"], "failed")

    def test_invalid_root_backend_and_unsafe_registered_analysis_paths_are_refused(self):
        for case in ("invalid_backend", "missing_reason", "escape", "parent_alias"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                state = complete_project(root, questions=1)
                if case == "invalid_backend":
                    state["execution"]["solver_backend"] = "auto"
                elif case == "missing_reason":
                    state["execution"].pop("solver_backend_selection_reason")
                else:
                    state["subproblems"]["Q1"]["result_analysis_workbook"] = (
                        "../outside.xlsx" if case == "escape" else "附件/../问题一求解/问题一结果深化分析.xlsx"
                    )
                save_state(root, state)
                with self.assertRaises(SystemExit):
                    PACK.reproducibility_files(root, root / "submission/fixture.zip")

    def test_current_selection_reports_case_alias(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = complete_project(root, questions=1)
            write_files(root, ["问题一求解/Q1_ANALYSIS.m"])
            _, issues = current_analysis_artifacts(root, state, required_files=[])
            self.assertTrue(issues)

    def test_non_mapping_state_has_controlled_collection_diagnostic(self):
        for content in ("[]", "2", "unexpected", "[broken"):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                complete_project(root, questions=1)
                (root / "state/project_state.yaml").write_text(content, encoding="utf-8")
                with self.assertRaisesRegex(SystemExit, "reproducibility package refused"):
                    PACK.reproducibility_files(root, root / "submission/fixture.zip")

    def test_current_selection_reports_symlink_alias(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = complete_project(root, questions=1)
            target = root / "附件/附件1.xlsx"
            link = root / "问题一求解/问题一结果深化分析.xlsx"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("Host does not permit synthetic symlink creation")
            _, issues = current_analysis_artifacts(root, state, required_files=[])
            self.assertTrue(issues)


if __name__ == "__main__":
    unittest.main()
