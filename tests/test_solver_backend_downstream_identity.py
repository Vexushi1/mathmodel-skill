"""Synthetic identity/collection fixtures; these do not claim numerical execution."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import stage_code
import sync_project as sync
from stage_inputs import observe_inputs
from submission_requirements import reproducibility_requirements
from validate_model_paper_framework import _implementation_anchor_issues
from tests.test_audit_package_completeness import archive, VALIDATOR
from tests.test_solver_backend_end_to_end import file_hash, reference_digest, save_state
from tests.test_sync_project import write_state, write_solution, write_analysis
from tests import test_v781_algorithm_closure as trace_fixture


def stage_fixture(root, entry, question, backend, stage, paths, *, mode="combined", digest=None):
    name = stage_code.question_name(question)
    number = stage_code.question_number(question)
    filename = ((name + ("求解.py" if stage == "primary" else "结果深化分析.py")) if backend == "python"
                else f"q{number}_{'solver' if stage == 'primary' else 'analysis'}.m")
    code = root / f"{name}求解" / filename
    code.parent.mkdir(exist_ok=True)
    config = {"stage": stage, "problem_name": name, "solver_backend": backend,
              "run_receipt_protocol_version": "1.1.0", "data_paths": paths,
              "data_sha256": digest or reference_digest(root, paths), "data_identity_mode": mode,
              "solver": "synthetic_fixture", "random_seed": 0, "tolerance": 1e-8,
              "iteration_or_time_limit": 1, "expected_workbook": "unused.xlsx", "code_dependencies": []}
    if stage == "analysis":
        config["primary_workbook_sha256"] = entry["validated_artifact_hashes"]["solution_workbook"]
    if backend == "python":
        code.write_text("RUN_CONFIG = " + repr(config) + "\n# def ghost():\ndef solve_fixture():\n    return 3\n", encoding="utf-8")
    else:
        literal = json.dumps(config, ensure_ascii=False).replace("'", "''")
        code.write_text(f"function {code.stem}()\nRUN_CONFIG = jsondecode('{literal}');\n% function ghost()\nend\n", encoding="utf-8")
    fingerprint = stage_code.stage_code_fingerprint(root, code)
    field = "code" if stage == "primary" else "result_analysis_code"
    entry[field] = code.relative_to(root).as_posix()
    entry[f"{stage}_code_sha256"] = fingerprint["entry_sha256"]
    entry.setdefault("solver_execution", {})[stage] = {
        "bundle_sha256": fingerprint["bundle_sha256"], "validated_bundle_sha256": fingerprint["bundle_sha256"]}
    for key in ("artifact_hashes", "validated_artifact_hashes"):
        entry.setdefault(key, {})[f"{stage}_code"] = fingerprint["entry_sha256"]
    return code, config


def project_fixture(root, backends=("matlab",), *, analysis=False):
    (root / "input.json").write_text('{"coefficient":2,"right_hand_side":6}', encoding="utf-8")
    write_state(root, status="solved")
    state = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
    state["execution"] = {"solver_backend": backends[0],
                          "solver_backend_selection_reason": "Whole-problem synthetic requirement review"}
    state["preprocessing"] = {"decision": "not_needed", "status": "not_applicable", "quality_status": "not_applicable"}
    state["data"] = {"sources": [{"name": "synthetic input", "path": "input.json", "role": "raw"}]}
    baseline = deepcopy(state["subproblems"]["Q1"])
    for number, backend in enumerate(backends, 1):
        question = f"Q{number}"
        name = stage_code.question_name(question)
        directory = root / f"{name}求解"
        directory.mkdir()
        workbook = directory / f"{name}求解结果.xlsx"
        write_solution(workbook)
        entry = deepcopy(baseline)
        state["subproblems"][question] = entry
        paths = ["input.json"] + ([state["subproblems"]["Q1"]["solution_workbook"]] if number > 1 else [])
        entry.update(solution_workbook=workbook.relative_to(root).as_posix(), primary_execution_status="accepted",
                     result_analysis_status="not_required", result_analysis_requirement_reason="Synthetic current-world boundary",
                     data_hash=reference_digest(root, paths), validated_data_hash=reference_digest(root, paths))
        for key in ("artifact_hashes", "validated_artifact_hashes"):
            entry[key] = {"data": entry["data_hash"], "solution_workbook": file_hash(workbook)}
        stage_fixture(root, entry, question, backend, "primary", paths)
    if analysis:
        entry = state["subproblems"]["Q1"]
        entry.update(result_analysis_status="passed", analysis_execution_status="accepted", analysis_methods=["参数敏感性"])
        path = root / "问题一求解/问题一结果深化分析.xlsx"
        write_analysis(path)
        entry["result_analysis_workbook"] = path.relative_to(root).as_posix()
        for key in ("artifact_hashes", "validated_artifact_hashes"):
            entry[key]["result_analysis_workbook"] = file_hash(path)
        stage_fixture(root, entry, "Q1", backends[0], "analysis", ["input.json"])
    save_state(root, state)
    return state


def package_fixture(root, state):
    for relative in ("模型论文框架.md", "final_latex/main.pdf", "final_latex/main.tex"):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Synthetic collection placeholder; not compiled", encoding="utf-8")
    for number, entry in enumerate(state["subproblems"].values(), 1):
        path = (root / entry["code"]).parent / f"q{number}_plot.m"
        path.write_text("% synthetic collection placeholder; not executed", encoding="utf-8")
    save_state(root, state)


class DownstreamInputIdentityTests(unittest.TestCase):
    def test_unchanged_same_backend_inputs_survive_sync_without_mutating_delivery(self):
        for backends in (("python", "python"), ("matlab", "matlab")):
            with self.subTest(backends=backends), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                state = project_fixture(root, backends)
                (root / "unrelated_report.json").write_text("{}", encoding="utf-8")
                before = (root / "state/project_state.yaml").read_bytes()
                report = sync.synchronize(root)
                self.assertEqual(report["state_transitions"], [])
                self.assertEqual(before, (root / "state/project_state.yaml").read_bytes())
                for question, entry in state["subproblems"].items():
                    observed = report["questions"][question]
                    self.assertEqual(observed["artifact_hashes"]["data"], entry["validated_data_hash"])
                    self.assertEqual(observed["issues"], [])
                delivered = deepcopy(state["subproblems"]["Q2"])
                sync._apply_snapshot_to_state(root, state, report["questions"]["Q2"])
                for key in ("solver_execution", "data_hash", "validated_data_hash", "validated_artifact_hashes"):
                    self.assertEqual(state["subproblems"]["Q2"][key], delivered[key])

    def test_mixed_history_cannot_be_accepted_as_current_project(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = project_fixture(root, ("python", "matlab"))
            report = sync.synchronize(root)
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any("Q2.primary" in item and "suffix" in item for item in report["issues"]))
            _, issues = reproducibility_requirements(root, state)
            self.assertTrue(any("项目数值后端" in item for item in issues))

    def test_actual_raw_and_upstream_workbook_changes_invalidate_correct_inputs(self):
        for changed, expected in (("input.json", {"Q1", "Q2"}), ("问题一求解/问题一求解结果.xlsx", {"Q2"})):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                project_fixture(root, ("python", "python"))
                with (root / changed).open("ab") as handle:
                    handle.write(b" ")
                report = sync.synchronize(root)
                sources = {row["source"] for row in report["state_transitions"] if row["event"] == "data_changed"}
                self.assertEqual(sources, expected)

    def test_missing_modern_input_fails_without_falling_back_to_global_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project_fixture(root)
            (root / "input.json").unlink()
            (root / "other.json").write_text("{}", encoding="utf-8")
            report = sync.synchronize(root)
            self.assertNotIn("data", report["questions"]["Q1"]["artifact_hashes"])
            self.assertTrue(any("输入文件不存在" in item for item in report["issues"]))
            self.assertIn("data_changed", [row["event"] for row in report["state_transitions"]])

    def test_analysis_invalid_distinct_inputs_never_replace_primary_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = project_fixture(root, analysis=True)
            entry = state["subproblems"]["Q1"]
            (root / "analysis.json").write_text("{}", encoding="utf-8")
            stage_fixture(root, entry, "Q1", "matlab", "analysis", ["analysis.json"])
            save_state(root, state)
            report = sync.synchronize(root)
            self.assertTrue(any("analysis data_sha256必须继承" in item for item in report["issues"]))
            self.assertEqual(report["questions"]["Q1"]["artifact_hashes"]["data"], entry["data_hash"])
            self.assertEqual(report["state_transitions"], [])
            self.assertEqual(entry["primary_execution_status"], "accepted")
            _, issues = reproducibility_requirements(root, state)
            self.assertTrue(any("analysis data_sha256必须继承" in item for item in issues))

    def test_project_level_observation_uses_plain_accepted_file_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = project_fixture(root)
            path = root / "数据预处理/数据预处理结果.xlsx"
            path.parent.mkdir()
            write_solution(path)  # Identity-only synthetic preprocessing artifact.
            digest = file_hash(path)
            state["preprocessing"] = {"decision": "project_level", "status": "accepted", "quality_status": "passed",
                "workbook": path.relative_to(root).as_posix(), "workbook_sha256": digest, "covered_raw_sources": ["input.json"]}
            entry = state["subproblems"]["Q1"]
            stage_fixture(root, entry, "Q1", "matlab", "primary", [state["preprocessing"]["workbook"]],
                          mode="preprocessing_workbook", digest=digest.upper())
            entry.update(data_hash=digest, validated_data_hash=digest)
            for key in ("artifact_hashes", "validated_artifact_hashes"):
                entry[key]["data"] = digest
            save_state(root, state)
            report = sync.synchronize(root)
            self.assertEqual(report["questions"]["Q1"]["artifact_hashes"]["data"], digest)
            self.assertEqual(report["questions"]["Q1"]["issues"], [])
            self.assertEqual(report["state_transitions"], [])
            with path.open("ab") as handle:
                handle.write(b" ")
            report = sync.synchronize(root)
            self.assertTrue(any("预处理工作簿当前文件SHA-256" in item for item in report["issues"]))

    def test_legacy_10_is_readable_but_cannot_become_current_sync(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = project_fixture(root, ("python",))
            state.pop("execution")
            entry = state["subproblems"]["Q1"]
            code = root / entry["code"]
            code.write_text("RUN_CONFIG = {'run_receipt_protocol_version':'1.0.0'}\n", encoding="utf-8")
            entry.pop("solver_execution")
            entry["primary_code_sha256"] = file_hash(code)
            for key in ("artifact_hashes", "validated_artifact_hashes"):
                entry[key]["primary_code"] = file_hash(code)
            save_state(root, state)
            report = sync.synchronize(root)
            self.assertEqual(report["state_transitions"], [])
            self.assertTrue(any("项目数值后端" in item for item in report["issues"]))
            historical = sync._snapshot_question(root, "问题一", entry,
                sync.load_yaml(sync.DEFAULT_SCHEMA_PATH), report["data_hash"], None)
            self.assertEqual(historical["artifact_hashes"]["data"], report["data_hash"])

    def test_input_path_validation_and_declared_identity_are_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = project_fixture(root)
            _, config = stage_code.parse_stage_config(root / state["subproblems"]["Q1"]["code"])
            for paths in ([], [""], ["../outside.json"], [str(root / "input.json")], ["state"],
                          ["missing.json"], ["input.json", "input.json"], ["INPUT.json"]):
                with self.subTest(paths=paths), self.assertRaises(ValueError):
                    observe_inputs(root, {**config, "data_paths": paths}, state)
            observation = observe_inputs(root, {**config, "data_sha256": "0" * 64}, state)
            self.assertTrue(observation["issues"])
            self.assertEqual(observation["data_sha256"], config["data_sha256"])
            with self.assertRaises(ValueError):
                observe_inputs(root, {**config, "data_identity_mode": "preprocessing_workbook"}, state)


class DownstreamPackageAndTraceTests(unittest.TestCase):
    def test_modern_package_requires_inputs_with_or_without_declared_raw_sources(self):
        for backend in ("python", "matlab"):
            for sources in (True, False):
                with self.subTest(backend=backend, sources=sources), tempfile.TemporaryDirectory() as temp:
                    root = Path(temp)
                    state = project_fixture(root, (backend,), analysis=True)
                    if not sources:
                        state.pop("data")
                    package_fixture(root, state)
                    required, issues = reproducibility_requirements(root, state)
                    self.assertEqual(issues, [])
                    self.assertIn("input.json", required)
                    self.assertEqual(VALIDATOR.validate_package(root, archive(root))["status"], "passed")
                    report = VALIDATOR.validate_package(root, archive(root, omit=["input.json"]))
                    self.assertEqual(report["status"], "failed")
                    self.assertTrue(any("input.json" in item for item in report["issues"]))

    def test_package_detects_changed_input_and_does_not_invent_not_required_analysis(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = project_fixture(root)
            package_fixture(root, state)
            required, issues = reproducibility_requirements(root, state)
            self.assertEqual(issues, [])
            self.assertFalse(any("analysis" in name or "深化分析" in name for name in required))
            (root / "input.json").write_text("changed", encoding="utf-8")
            report = VALIDATOR.validate_package(root, archive(root))
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any("data_sha256" in item for item in report["issues"]))

    def test_missing_or_unsafe_declared_input_blocks_both_sync_and_package(self):
        for paths in ([], [""], ["missing.json"], ["../outside.json"], ["state"]):
            with self.subTest(paths=paths), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                state = project_fixture(root)
                entry = state["subproblems"]["Q1"]
                stage_fixture(root, entry, "Q1", "matlab", "primary", paths, digest=entry["data_hash"])
                package_fixture(root, state)
                report = sync.synchronize(root)
                self.assertNotIn("data", report["questions"]["Q1"]["artifact_hashes"])
                self.assertTrue(any("输入身份" in item for item in report["issues"]))
                self.assertEqual(VALIDATOR.validate_package(root, archive(root))["status"], "failed")

    def test_sync_preflight_checks_real_functions_and_lines_in_both_backends(self):
        for backend in ("python", "matlab"):
            with self.subTest(backend=backend), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                state = project_fixture(root, (backend,))
                entry = state["subproblems"]["Q1"]
                entry.update(framework_section="### Q1：测试", result_summary_anchor="#### 结果摘要")
                symbol = "solve_fixture" if backend == "python" else "q1_solver"
                for target, rejected in ((symbol, False), ("missing_function", True), ("ghost", True), ("999999", True)):
                    text = trace_fixture.TestV781AlgorithmClosure.framework("stepwise", "A1", "stepwise", python_anchor=entry["code"] + "#" + target)
                    (root / "模型论文框架.md").write_text(text, encoding="utf-8")
                    digest = sync.framework_section_hash(root / "模型论文框架.md", entry["framework_section"])
                    for key in ("artifact_hashes", "validated_artifact_hashes"):
                        entry[key]["framework"] = digest
                    issues = sync.contract_preflight_issues(root, "design", root / "state/project_state.yaml",
                        root / "模型论文框架.md", sync.load_yaml(sync.DEFAULT_OUTPUT_CONTRACT_PATH), candidate_state=state)
                    self.assertEqual(bool(issues), rejected, issues)
                    if rejected:
                        self.assertTrue(any("implementation" in issue for issue in issues))
                code = root / entry["code"]
                with code.open("a", encoding="utf-8") as handle:
                    handle.write("\n# changed\n" if backend == "python" else "\n% changed\n")
                text = trace_fixture.TestV781AlgorithmClosure.framework("stepwise", "A1", "stepwise", python_anchor=entry["code"] + "#" + symbol)
                (root / "模型论文框架.md").write_text(text, encoding="utf-8")
                issues = sync.contract_preflight_issues(root, "design", root / "state/project_state.yaml",
                    root / "模型论文框架.md", sync.load_yaml(sync.DEFAULT_OUTPUT_CONTRACT_PATH), candidate_state=state)
                self.assertTrue(any("SHA-256与已交付" in issue for issue in issues))

    def test_sync_preflight_keeps_legacy_free_text_anchor_readable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = project_fixture(root, ("python",))
            state.pop("execution")
            entry = state["subproblems"]["Q1"]
            entry.pop("solver_execution")
            code = root / entry["code"]
            code.write_text("def solve_fixture():\n    return 3\n", encoding="utf-8")
            entry.update(primary_code_sha256=file_hash(code), framework_section="### Q1：测试", result_summary_anchor="#### 结果摘要")
            text = trace_fixture.TestV781AlgorithmClosure.framework("stepwise", "A1", "stepwise", python_anchor="historical solve description")
            (root / "模型论文框架.md").write_text(text, encoding="utf-8")
            for key in ("artifact_hashes", "validated_artifact_hashes"):
                entry[key].update(primary_code=file_hash(code), framework=sync.framework_section_hash(root / "模型论文框架.md", entry["framework_section"]))
            issues = sync.contract_preflight_issues(root, "design", root / "state/project_state.yaml",
                root / "模型论文框架.md", sync.load_yaml(sync.DEFAULT_OUTPUT_CONTRACT_PATH), candidate_state=state)
            self.assertTrue(any("backend" in issue or "后端" in issue for issue in issues), issues)
            self.assertEqual(_implementation_anchor_issues("historical solve description", entry, root), [])


if __name__ == "__main__":
    unittest.main()
