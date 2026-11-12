"""G2 bounded Assured multi-action route fix; legacy and Gate semantics remain unchanged."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from resolve_runtime import resolve_runtime
from resolve_workflow import resolve_workflow
from runtime_assurance import _bounded_independent_action_intents, resolve_intent_assurance

ROUTER = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_bytes())


class G2BoundedMultiActionTests(unittest.TestCase):
    def test_two_actual_independent_actions_are_selected(self):
        cases = (
            ("修改问题二图表，并调整 LaTeX 论文中的文字说明", ["figures", "latex"]),
            ("进行模型检验，同时编写 LaTeX 论文正文", ["validation", "latex"]),
            ("调整 LaTeX 论文说明，并且修改问题二图表", ["latex", "figures"]),
        )
        for request, expected in cases:
            with self.subTest(request=request):
                plan = resolve_runtime(request=request, competition="CUMCM")
                self.assertEqual(plan["intents"], expected)
                self.assertEqual(plan["assurance"]["intent_resolution"]["selected_intents"], expected)
                self.assertFalse(plan["assurance"]["intent_resolution"]["ambiguity"])
                self.assertEqual(plan["reading_plan"]["profile"], "full")
                self.assertEqual(plan["reading_plan"]["status"], "conservative_fallback")
                # A compound inferred plan must have the same effective boundary
                # projection as a previously available explicitly selected pair.
                explicit = resolve_runtime(expected, competition="CUMCM")
                for field in ("modules", "delivery_scope", "pause_state", "pre_delivery_gates",
                              "terminal_outputs", "pause_for_user_execution",
                              "task_code_execution_allowed"):
                    self.assertEqual(plan[field], explicit[field], (request, field))

    def test_no_unapproved_validation_code_and_no_implicit_gate_pass(self):
        plan = resolve_runtime(
            request="进行模型检验，同时编写 LaTeX 论文正文", competition="CUMCM"
        )
        self.assertEqual(plan["intents"], ["validation", "latex"])
        self.assertEqual(plan["pause_state"], "awaiting_model_approval")
        self.assertNotIn("modules/03_solve_validate.md", plan["modules"])
        self.assertNotIn("modules/03_result_analysis.md", plan["modules"])
        self.assertFalse(plan["task_code_execution_allowed"])

    def test_compound_outputs_remain_candidates_not_current_accepted_evidence(self):
        plan = resolve_runtime(
            request="修改问题二图表，并调整 LaTeX 论文中的文字说明",
            competition="CUMCM",
        )
        # Combining stages may advertise future Figure outputs but must not
        # manufacture approved figures or an accepted workbook in assurance.
        qualified = plan["assurance"]["artifact_assurance"]["effective_artifacts"]
        self.assertNotIn("approved_figures", qualified)
        self.assertNotIn("accepted_solution_workbook", qualified)
        self.assertIn("approved_figures", plan["terminal_outputs"])
        self.assertEqual(
            [gate["name"] for gate in plan["pre_delivery_gates"]],
            ["semantic_governance", "project_sync"],
        )
        writing = plan["writing_runtime"]
        self.assertEqual(writing["execution_mode"], "template_first_progressive_authoring")
        self.assertTrue(writing["full_reasoning_authority_preloaded"])
        stage_ids = [stage["id"] for stage in writing["authoring_sequence"]]
        self.assertIn("draft_semantic_review", stage_ids)
        self.assertIn("final_review_and_delivery", stage_ids)

    def test_explicit_intent_wins_over_compound_request(self):
        request = "修改问题二图表，并调整 LaTeX 论文中的文字说明"
        for explicit in (["figures"], ["latex"], ["figures", "latex"]):
            with self.subTest(explicit=explicit):
                plan = resolve_runtime(explicit, request=request, competition="CUMCM")
                self.assertEqual(plan["intents"], explicit)
                self.assertEqual(plan["assurance"]["intent_resolution"]["confidence_score"], 1.0)

    def test_negated_clause_cannot_trigger_independent_union(self):
        for request in (
            "只修改图表，并不修改 LaTeX 论文",
            "进行模型检验，同时不要编写 LaTeX 论文",
            "请修改图表，并且无需调整 LaTeX 正文",
            "修改图表，同时不需要编写 LaTeX 论文",
        ):
            with self.subTest(request=request):
                selected, diagnostic = resolve_intent_assurance([], request, ROUTER)
                self.assertNotEqual(set(selected), {"figures", "latex"})
                self.assertNotEqual(set(selected), {"validation", "latex"})
                self.assertNotIn("two separately expressed", diagnostic["selection_reason"])

    def test_historical_word_latex_carrier_contract_and_read_only_review(self):
        request = "用 Word 和 LaTeX 写论文草稿"
        self.assertEqual(resolve_runtime(request=request, competition="CUMCM")["intents"], ["latex"])
        self.assertEqual(set(resolve_workflow(request=request, competition="CUMCM")["intents"]),
                         {"docx", "latex"})
        for review in (
            "只审查 LaTeX 论文，不修改",
            "审稿 Word 论文，只给修改建议，不修改文件",
        ):
            plan = resolve_runtime(request=review, competition="CUMCM")
            self.assertEqual(plan["intents"], ["review"])
            self.assertFalse(any("--write" in item["command"]
                                 for item in plan["pre_delivery_gates"]))

    def test_bounded_helper_uses_router_evidence_no_broad_keyword_union(self):
        for request in (
            "写 Word 论文草稿并编译论文",
            "请审查 LaTeX 论文并给出建议",
            "模型检验与 LaTeX 写作",  # no independent positive verb in each clause
            "请完成全流程，并制作图表",
        ):
            with self.subTest(request=request):
                raw, _ = resolve_intent_assurance([], request, ROUTER)
                self.assertFalse({"latex", "validation"}.issubset(set(raw)))
                self.assertFalse({"latex", "figures"}.issubset(set(raw)))
                self.assertFalse({"docx", "latex"}.issubset(set(raw)))

    def test_unrelated_single_action_remains_unmodified(self):
        for request in ("Python绘图", "MATLAB绘图", "请写论文草稿", "开始求解"):
            with self.subTest(request=request):
                base = resolve_workflow(request=request, competition="CUMCM")
                current = resolve_runtime(request=request, competition="CUMCM")
                self.assertEqual(current["intents"], base["intents"])


if __name__ == "__main__":
    unittest.main()
