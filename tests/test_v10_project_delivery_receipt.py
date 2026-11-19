"""Project-level solver policy at the current delivery and receipt boundary.

The executed scalar program is the repository's isolated maintenance fixture,
not a competition model or a claim about native MATLAB execution.
"""
from __future__ import annotations

from copy import deepcopy
import os
import shlex
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import openpyxl
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import analysis_prerequisites as PREREQUISITES
from resolve_runtime import resolve_runtime
from semantic_identity import inspect_question_semantics, question_sections
import validate_code_delivery as DELIVERY
import validate_user_execution as RECEIPT
from tests.test_copied_support_source_closure import instantiate
from tests.test_solver_backend_end_to_end import prepare as prepare_matlab
from tests.test_v900_semantic_identity_binding import framework, identity, structured_question


class ProjectDeliveryReceiptTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.code, self.config = instantiate(self.root, minimal=True)
        self.state_path = self.root / "state/project_state.yaml"
        state = self.state()
        state["execution"] = {
            "solver_backend": "python",
            "solver_backend_selection_reason": "全题数值需求及环境已审视",
        }
        state["subproblems"]["Q1"]["solver_execution"] = {"primary": {}}
        self.save(state)
        self.workbook = self.root / self.config["expected_workbook"]

    def state(self):
        return yaml.safe_load(self.state_path.read_text(encoding="utf-8"))

    def save(self, state):
        self.state_path.write_text(
            yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def deliver(self):
        issues, parsed = DELIVERY.validate_script(self.root, self.code, "primary")
        self.assertEqual(issues, [])
        self.assertEqual(parsed, self.config)
        DELIVERY.update_state(self.root, parsed, self.code)
        return self.state()

    def execute(self):
        environment = {key: value for key, value in os.environ.items()
                       if key not in {"PYTHONPATH", "HSK_WORKBOOK_SCHEMA"}}
        environment["PYTHONUTF8"] = "1"
        before = self.state_path.read_bytes()
        result = subprocess.run(
            [sys.executable, "-B", str(self.code)], cwd=self.root, env=environment,
            capture_output=True, encoding="utf-8", timeout=45,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.state_path.read_bytes(), before)
        self.assertTrue(self.workbook.is_file())

    def test_delivery_uses_project_policy_and_records_only_bundle_identity(self):
        state = self.deliver()
        entry = state["subproblems"]["Q1"]
        binding = entry["solver_execution"]["primary"]
        self.assertEqual(entry["primary_execution_status"], "awaiting_user_execution")
        self.assertIn("bundle_sha256", binding)
        self.assertNotIn("validated_bundle_sha256", binding)
        self.assertNotIn("backend", binding)
        self.assertNotIn("selection_reason", binding)

    def test_unregistered_standard_file_requires_explicit_delivery(self):
        self.assertEqual(DELIVERY.discover_scripts(self.root), [])
        self.assertEqual(DELIVERY.validate_script(self.root, self.code, "primary")[0], [])
        self.deliver()
        self.assertEqual(DELIVERY.discover_scripts(self.root), [self.code])

    def approved_question_scope(self):
        state = self.state()
        payload = identity()
        payload["preprocessing_decision"] = "not_needed"
        state["semantic_governance_version"] = "1.0.0"
        state["subproblems"]["Q1"].update(
            structured_question(payload),
            problem_contract_status="frozen", semantic_closure_status="passed",
            complexity_sanity_status="passed", semantic_change_categories=["initial_design"],
        )
        state["subproblems"]["Q2"] = {
            "status": "pending", "human_model_approval_status": "pending",
            "depends_on": [{"question": "Q1", "kind": "result"}],
        }
        self.save(state)
        (self.root / "模型论文框架.md").write_text(framework(payload), encoding="utf-8")

    def run_scoped_gates(self, plan, names):
        gates = plan["pre_delivery_gates"]
        self.assertEqual([gate["name"] for gate in gates], names)
        self.assertEqual(plan["runtime_plan"]["pre_delivery_gate_names"], names)
        self.assertEqual(
            [gate["command"] for gate in gates],
            [tool["command"] for tool in plan["reading_plan"]["tool_interfaces"]],
        )
        for gate in gates:
            command, script, *args = shlex.split(gate["command"])
            self.assertEqual(command, "python")
            self.assertEqual(script, gate["path"])
            result = subprocess.run(
                [sys.executable, str(ROOT / script),
                 *(str(self.root) if arg == "<project_root>" else arg for arg in args)],
                cwd=self.root, env={**os.environ, "PYTHONUTF8": "1"},
                capture_output=True, encoding="utf-8", timeout=45,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_resolved_single_question_gates_deliver_and_accept_without_other_question(self):
        self.approved_question_scope()
        self.assertEqual(DELIVERY.discover_scripts(self.root), [])
        plan = resolve_runtime("code_and_solution", project_root=self.root, question="Q1")
        self.assertEqual(plan["assurance"]["status"], "pass", plan["assurance"]["context"])
        self.assertEqual(plan["pause_state"], "awaiting_user_execution")
        commands = {gate["name"]: shlex.split(gate["command"]) for gate in plan["pre_delivery_gates"]}
        self.assertEqual(commands["model_approval"][-2:], ["--question", "Q1"])
        self.assertEqual(commands["code_delivery"][-4:], [
            "--script", self.code.relative_to(self.root).as_posix(), "--stage", "primary",
        ])
        self.run_scoped_gates(plan, ["semantic_governance", "model_approval", "code_delivery"])
        self.assertEqual(self.state()["subproblems"]["Q1"]["primary_execution_status"], "awaiting_user_execution")

        self.execute()
        unrelated = self.root / "问题二求解/问题二求解结果.xlsx"
        unrelated.parent.mkdir()
        unrelated.write_bytes(self.workbook.read_bytes())
        receipt = resolve_runtime("returned_workbook_validation", project_root=self.root, question="Q1")
        self.assertEqual(receipt["assurance"]["status"], "pass", receipt["assurance"]["context"])
        self.assertEqual(shlex.split(receipt["pre_delivery_gates"][1]["command"])[-2:], [
            "--workbook", self.workbook.relative_to(self.root).as_posix(),
        ])
        self.run_scoped_gates(receipt, ["semantic_governance", "user_execution_receipt"])
        result = self.state()["subproblems"]
        self.assertEqual(result["Q1"]["primary_execution_status"], "accepted")
        self.assertEqual(result["Q2"]["human_model_approval_status"], "pending")
        self.assertNotIn("solution_workbook", result["Q2"])

    def test_scoped_receipt_with_multiple_candidates_never_discovers_whole_project(self):
        self.approved_question_scope()
        for path in (self.workbook, self.workbook.with_name("问题一结果深化分析.xlsx")):
            path.touch()
        plan = resolve_runtime("returned_workbook_validation", project_root=self.root, question="Q1")
        self.assertEqual(plan["assurance"]["status"], "review_required")
        self.assertTrue(any("select one returned workbook" in issue
                            for issue in plan["assurance"]["context"]["conflicts"]))
        self.assertEqual(shlex.split(plan["pre_delivery_gates"][1]["command"])[-2:],
                         ["--workbook", "<returned_workbook>"])

    def test_question_receipt_without_current_state_still_requires_explicit_target(self):
        self.state_path.unlink()
        plan = resolve_runtime("returned_workbook_validation", project_root=self.root, question="Q1")
        self.assertEqual(plan["assurance"]["status"], "review_required")
        command = plan["pre_delivery_gates"][1]["command"]
        self.assertEqual(shlex.split(command)[-2:], ["--workbook", "<returned_workbook>"])

    def approve_additional_question(self, question):
        state = self.state()
        payload = dict(identity(), question=question, preprocessing_decision="not_needed")
        section = (framework(payload)
                   .replace("### Q1：", f"### {question}：")
                   .replace("IDENTITY_BEGIN Q1", f"IDENTITY_BEGIN {question}")
                   .replace("IDENTITY_END Q1", f"IDENTITY_END {question}"))
        inspection = inspect_question_semantics(question_sections(section)[question], question)
        entry = state["subproblems"].setdefault(question, {})
        entry.update(
            structured_question(),
            status="designed",
            problem_contract_status="frozen",
            semantic_closure_status="passed",
            complexity_sanity_status="passed",
            semantic_change_categories=["initial_design"],
            semantic_text_hash=inspection["semantic_text_hash"],
        )
        for field in ("semantic_identity_hash", "validated_semantic_identity_hash",
                      "approved_semantic_identity_hash"):
            entry[field] = inspection["semantic_identity_hash"]
        self.save(state)
        with (self.root / "模型论文框架.md").open("a", encoding="utf-8") as file:
            file.write("\n" + section.split("\n", 2)[2])

    def dependency_plan(self, question, *, intent="code_and_solution"):
        before = self.state_path.read_bytes()
        plan = resolve_runtime(intent, project_root=self.root, question=question)
        self.assertEqual(self.state_path.read_bytes(), before)
        return plan, plan["assurance"]["context"].get("dependency_diagnostics")

    def accept_primary_fixture(self):
        self.deliver()
        self.execute()
        state = self.state()
        self.assertEqual(RECEIPT.validate_one(self.root, self.workbook, state, True), [])
        self.save(state)

    def test_missing_upstream_result_is_diagnostic_and_verified_artifact_clears_it(self):
        self.approved_question_scope()
        self.approve_additional_question("Q2")
        unresolved, diagnostic = self.dependency_plan("Q2")
        self.assertEqual(diagnostic["stage"], "primary")
        self.assertEqual(diagnostic["unresolved_result_cycles"], [])
        self.assertEqual(
            [(row["question"], row["upstream"], row["status"])
             for row in diagnostic["result_dependencies"]],
            [("Q2", "Q1", "not_accepted")],
        )
        self.assertTrue(diagnostic["result_dependencies"][0]["reason"])
        self.assertIn("code_delivery", unresolved["runtime_plan"]["pre_delivery_gate_names"])

        self.accept_primary_fixture()
        resume, diagnostic = self.dependency_plan("Q2")
        self.assertEqual(diagnostic["result_dependencies"][0]["status"], "verified")
        for field in ("pre_delivery_gates", "missing_prerequisites", "pause_state"):
            self.assertEqual(unresolved[field], resume[field], field)

        self.workbook.write_bytes(self.workbook.read_bytes() + b"changed after acceptance")
        _, diagnostic = self.dependency_plan("Q2")
        self.assertNotEqual(diagnostic["result_dependencies"][0]["status"], "verified")

    def test_unresolved_result_cycle_is_scoped_and_ends_at_a_verified_result(self):
        self.approved_question_scope()
        self.approve_additional_question("Q2")
        self.approve_additional_question("Q3")
        state = self.state()
        state["subproblems"]["Q1"]["depends_on"] = [{"question": "Q2", "kind": "result"}]
        self.save(state)

        for question in ("Q1", "Q2", None):
            with self.subTest(question=question):
                _, diagnostic = self.dependency_plan(question)
                self.assertEqual(diagnostic["unresolved_result_cycles"], ["Q1 -> Q2 -> Q1"])
                self.assertCountEqual(
                    [(row["question"], row["upstream"]) for row in diagnostic["result_dependencies"]],
                    [("Q1", "Q2"), ("Q2", "Q1")],
                )
        independent, diagnostic = self.dependency_plan("Q3")
        self.assertIsNone(diagnostic)
        self.assertIn("code_delivery", independent["runtime_plan"]["pre_delivery_gate_names"])
        self.assertEqual(independent["assurance"]["status"], "pass")

        self.accept_primary_fixture()
        _, diagnostic = self.dependency_plan("Q2")
        self.assertEqual(diagnostic["unresolved_result_cycles"], [])
        self.assertEqual(
            [(row["question"], row["upstream"], row["status"])
             for row in diagnostic["result_dependencies"]],
            [("Q2", "Q1", "verified")],
        )
        _, analysis = self.dependency_plan("Q1", intent="result_analysis")
        self.assertEqual(analysis["stage"], "analysis")

    def test_legacy_and_model_edges_do_not_close_a_result_cycle(self):
        self.approved_question_scope()
        self.approve_additional_question("Q2")
        state = self.state()
        state["subproblems"]["Q1"]["depends_on"] = [{"question": "Q2", "kind": "result"}]
        state["subproblems"]["Q2"]["depends_on"] = [
            {"question": "Q1", "kind": "model", "note": "joint model equations"}, "Q1",
            {"question": "Q4", "kind": "result"},
        ]
        self.save(state)
        plan, diagnostic = self.dependency_plan("Q1")
        self.assertEqual(diagnostic["unresolved_result_cycles"], [])
        self.assertIn({"question": "Q2", "upstream": "Q1"}, diagnostic["legacy_dependencies"])
        self.assertEqual(
            [(row["question"], row["upstream"], row["status"])
             for row in diagnostic["result_dependencies"]],
            [("Q1", "Q2", "not_accepted"), ("Q2", "Q4", "unregistered")],
        )
        self.assertIn("code_delivery", plan["runtime_plan"]["pre_delivery_gate_names"])
        _, diagnostic = self.dependency_plan("Q1", intent="returned_workbook_validation")
        self.assertIsNone(diagnostic)

    def test_missing_or_conflicting_policy_cannot_deliver(self):
        state = self.state()
        state.pop("execution")
        self.save(state)
        before = self.state_path.read_bytes()
        self.assertTrue(DELIVERY.validate_script(self.root, self.code)[0])
        with self.assertRaises(ValueError):
            DELIVERY.update_state(self.root, self.config, self.code)
        self.assertEqual(self.state_path.read_bytes(), before)

        state["execution"] = {
            "solver_backend": "matlab",
            "solver_backend_selection_reason": "完整项目复核",
        }
        self.save(state)
        before = self.state_path.read_bytes()
        self.assertTrue(any("项目后端" in item for item in DELIVERY.validate_script(self.root, self.code)[0]))
        with self.assertRaisesRegex(ValueError, "项目后端"):
            DELIVERY.update_state(self.root, self.config, self.code)
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_write_rechecks_current_preprocessing_decision_after_static_validation(self):
        issues, parsed = DELIVERY.validate_script(self.root, self.code, "primary")
        self.assertEqual(issues, [])
        state = self.state()
        state["preprocessing"].update(decision="project_level", status="pending", quality_status="pending")
        self.save(state)
        before = self.state_path.read_bytes()
        with self.assertRaisesRegex(ValueError, "必须先验收数据预处理结果"):
            DELIVERY.update_state(self.root, parsed, self.code)
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_matlab_source_obeys_the_same_project_policy_without_native_execution(self):
        root = self.root / "matlab_project"
        prepare_matlab(root)
        state_path = root / "state/project_state.yaml"
        state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        state["execution"] = {
            "solver_backend": "matlab",
            "solver_backend_selection_reason": "全题数值需求及环境已审视",
        }
        record = state["subproblems"]["Q1"]["solver_execution"]["primary"]
        self.assertNotIn("backend", record)
        self.assertNotIn("selection_reason", record)
        state_path.write_text(yaml.safe_dump(state, allow_unicode=True), encoding="utf-8")
        source = root / state["subproblems"]["Q1"]["code"]
        issues, _ = DELIVERY.validate_script(root, source, "primary")
        self.assertEqual(issues, [])

    def test_successful_receipt_validates_bundle_without_adding_stage_selection(self):
        self.deliver()
        self.execute()
        state = self.state()
        self.assertEqual(RECEIPT.validate_one(self.root, self.workbook, state, True), [])
        entry = state["subproblems"]["Q1"]
        binding = entry["solver_execution"]["primary"]
        self.assertEqual(entry["primary_execution_status"], "accepted")
        self.assertEqual(binding["validated_bundle_sha256"], binding["bundle_sha256"])
        self.assertNotIn("backend", binding)

    def test_retired_workbook_and_opposite_receipt_cannot_mutate_current_state(self):
        self.deliver()
        self.execute()
        state = self.state()
        retired = deepcopy(state)
        entry = retired["subproblems"]["Q1"]
        entry.pop("code")
        entry.pop("primary_code_sha256")
        entry["solver_execution"]["primary"].clear()
        before = deepcopy(retired)
        issues = RECEIPT.validate_one(self.root, self.workbook, retired, True)
        self.assertTrue(any("历史工作簿" in item for item in issues))
        self.assertEqual(retired, before)

        book = openpyxl.load_workbook(self.workbook)
        try:
            sheet = book["运行配置"]
            row = next(row for row in sheet.iter_rows(min_row=2)
                       if row[0].value == "solver_backend")
            row[1].value = "matlab"
            book.save(self.workbook)
        finally:
            book.close()
        before = deepcopy(state)
        issues = RECEIPT.validate_one(self.root, self.workbook, state, True)
        self.assertTrue(any("项目后端" in item for item in issues))
        self.assertEqual(state, before)

    def test_old_state_is_read_only_for_analysis_prerequisites(self):
        state = self.state()
        state.pop("execution")
        entry = state["subproblems"]["Q1"]
        self.assertTrue(any("historical" in item or "project backend" in item
                            for item in PREREQUISITES.analysis_issues(
                                self.root, state, entry, require_project_policy=True)))


if __name__ == "__main__":
    unittest.main()
