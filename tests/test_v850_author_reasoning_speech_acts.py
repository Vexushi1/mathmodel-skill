"""v8.5 Author Reasoning Voice contracts and fixed evidence boundaries.

These tests protect routing, semantic invariants and fixed trial facts. They are
not prose-quality scores, pronoun quotas, authorship detectors or mathematical
validity judges.
"""
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "modules/05_writing/paper_writing_protocol.md"
CONTRACT = ROOT / "core/writing_reasoning_contract.yaml"
EXAMPLES = ROOT / "modules/05_writing/references/model_solution_reasoning_examples.md"
CLEANUP = ROOT / "modules/05_writing/ai_cleanup.md"
REVIEW = ROOT / "modules/06_review_delivery.md"
FIXTURE = ROOT / "tests/fixtures/writing_reasoning_voice_cases.yaml"
AUTHORITY = "modules/05_writing/paper_writing_protocol.md#7.3-作者视角与建模解释"


def read(path):
    return path.read_text(encoding="utf-8")


class AuthorReasoningContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reasoning = yaml.safe_load(read(CONTRACT))
        cls.protocol = read(PROTOCOL)
        cls.examples = read(EXAMPLES)
        cls.cleanup = read(CLEANUP)
        cls.review = read(REVIEW)
        cls.trace = cls.reasoning["prose_style"]["human_reasoning_trace"]

    def test_schema_and_single_prose_authority(self):
        self.assertEqual(self.reasoning["schema_version"], "1.8.0")
        self.assertEqual(self.trace["prose_authority"], AUTHORITY)
        self.assertIn("### 7.3 作者视角与建模解释", self.protocol)
        self.assertIn("本文件不新增规定", self.examples)

    def test_speech_act_taxonomy_is_complete_without_pronoun_quota(self):
        expected = {
            "observation", "open_question", "inquiry", "judgment", "choice",
            "reduction", "introduction", "derivation", "interpretation",
            "validation", "qualification",
        }
        self.assertEqual(set(self.trace["speech_acts"]), expected)
        roles = self.trace["subject_roles"]
        self.assertEqual(roles["quota"], "none")
        self.assertIn("pronoun_frequency_target", self.trace["prohibit"])
        self.assertIn("authorship_inference_from_voice", self.trace["prohibit"])

    def test_question_closure_and_claim_strength_are_evidence_bound(self):
        closure = self.trace["question_closure"]
        self.assertEqual(
            set(closure["allowed_outcomes"]),
            {
                "answered_by_downstream_operation",
                "explicitly_deferred_to_named_validation",
                "retained_as_unverified_hypothesis",
            },
        )
        self.assertIn(
            "rhetorical_question_without_mathematical_destination",
            closure["prohibition"],
        )
        self.assertEqual(
            self.trace["claim_strength_alignment"]["rule"],
            "prose_claim_strength_must_not_exceed_evidence_strength",
        )

    def test_reasoning_necessity_and_problem_specificity_are_semantic_checks(self):
        self.assertEqual(
            set(self.trace["necessity_tests"]),
            {"reasoning_necessity", "problem_specificity"},
        )
        section = self.protocol.split("### 7.3 作者视角与建模解释", 1)[1].split("## 8.", 1)[0]
        for phrase in (
            "Author Reasoning Speech Acts",
            "Question Closure",
            "Reasoning Necessity",
            "Problem-Specificity",
            "不按代词频率",
            "不判断作者身份",
        ):
            self.assertIn(phrase, section)

    def test_cleanup_and_review_consume_authority_and_explicitly_reject_voice_scoring(self):
        for text in (self.cleanup, self.review):
            self.assertIn("paper_writing_protocol.md#7.3-作者视角与建模解释", text)
            # These strings are present only to make the prohibited diagnostics explicit;
            # their presence is not an implementation of a score.
            self.assertIn("first_person_ratio", text)
            self.assertIn("human_like_score", text)
            self.assertIn("AI_like_score", text)
            self.assertIn("不得", text)
        for phrase in ("Keep / Compress / Re-subject / Delete", "Problem-Specificity"):
            self.assertIn(phrase, self.cleanup)
        for phrase in ("Author Reasoning Semantic Review", "Question Closure"):
            self.assertIn(phrase, self.review)

    def test_machine_boundary_denies_pronoun_or_authorship_inference(self):
        boundary = set(self.reasoning["machine_audit_boundary"]["must_not_claim"])
        self.assertIn("author_reasoning_quality_from_pronoun_frequency_or_question_marks", boundary)
        self.assertIn("authorship_or_ai_usage_from_author_voice_style", boundary)
        self.assertIn("question_closure_from_surface_phrase_presence_only", boundary)
        self.assertIn("problem_specificity_from_object_name_overlap_only", boundary)

    def test_examples_include_positive_negative_and_no_change_cases(self):
        for phrase in (
            "数学事实不必降级成“我们认为”",
            "自然发问必须闭合",
            "从图像产生想法但不制造因果",
            "启发式结果的作者判断不能越过证据",
            "“不改”也是合法结果",
        ):
            self.assertIn(phrase, self.examples)


class FixedVoiceCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = yaml.safe_load(read(FIXTURE))
        cls.cases = {case["id"]: case for case in data["cases"]}

    def test_fixture_has_eight_non_template_cases(self):
        self.assertEqual(len(self.cases), 8)
        self.assertEqual(len(set(self.cases)), 8)

    def test_prediction_facts_preserve_local_error(self):
        f = self.cases["local_prediction_error"]["facts"]
        residual = [y - p for y, p in zip(f["test_observation"], f["test_prediction"])]
        self.assertEqual(residual, f["residual"])
        self.assertEqual(sum(abs(x) for x in residual) / len(residual), f["mae"])
        self.assertEqual(max(abs(x) for x in residual), f["max_absolute_error"])

    def test_supply_case_really_needs_period_constraints(self):
        f = self.cases["period_specific_supply"]["facts"]
        self.assertFalse(f["interperiod_transfer_allowed"])
        self.assertTrue(all(f["batch_size"] < demand for demand in f["demands"]))
        self.assertGreaterEqual(2 * f["batch_size"], max(f["demands"]))

    def test_heuristic_case_has_no_global_certificate(self):
        f = self.cases["heuristic_best_found"]["facts"]
        self.assertEqual(f["evidence_level"], "HEURISTIC")
        self.assertTrue(f["multistart_checked"])
        self.assertFalse(f["global_certificate"])

    def test_direct_case_protects_anti_bloat(self):
        f = self.cases["direct_heat_balance"]["facts"]
        self.assertTrue(f["direct_relation_sufficient"])
        self.assertFalse(f["solver_needed"])
        self.assertFalse(f["extra_validation_needed"])


if __name__ == "__main__":
    unittest.main()
