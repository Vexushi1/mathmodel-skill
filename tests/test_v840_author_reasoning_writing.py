"""Protect v8.4/v8.5 writing invariants while allowing the approved v8.6 scope.

Snapshots come from PR #108 head 1895fb8 for sections that v8.6 did not
intentionally reopen. v8.5 Author Reasoning Voice remains semantically pinned;
v8.6 may extend model-construction rationale, solver preconditions, parameter
rationale and adaptive subsection/title governance only.

These are scope/regression tests, not prose-quality or authorship scores.
"""
import hashlib
import itertools
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "modules/05_writing/paper_writing_protocol.md"
EXAMPLES = "modules/05_writing/references/model_solution_reasoning_examples.md"
RATIONALE_EXAMPLES = "modules/05_writing/references/model_construction_solution_rationale_examples.md"
AUTHORITY = PROTOCOL + "#7.3-作者视角与建模解释"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class WritingReasoningScopeTests(unittest.TestCase):
    def test_unreopened_chapter_snapshots_remain_pinned(self):
        # v8.6 intentionally changes §§2, 3, 7, 8, 12, 15, 18 and related text.
        # These sections were not reopened and stay pinned to the prior snapshots.
        expected = {
            "4. Local Narrative Chain": "a32d8bce3e0805bdac4bce0105a7fa715473c28fc6392f701ffcd0a320b949b2",
            "5A. Cross-File Chapter Handoff": "77a8b8b8f7301544343a9e867380637ece97705022fc0c0e5a3eee0e009b2f19",
            "6. 前置章节内容": "540c70cf9833269ae02a138d03ab224f0f1c5e40e104dab33df4f84624607e84",
            "10. 结果与验证的分层": "21b6d5111705b6645c4bd90f1a1393d624797d71ece18254ff0ecca81e559872",
            "14. 摘要": "8c2cbf13c739b273f4f3331819b0c0bedcac11df5e7103b6e2ea0a109a540271",
        }
        sections = {m[1]: m[0] for m in re.finditer(
            r"^## ([^\n]+)\n(.*?)(?=^## |\Z)", read(PROTOCOL), re.M | re.S
        )}
        for heading, digest in expected.items():
            with self.subTest(heading=heading):
                self.assertEqual(hashlib.sha256(sections[heading].encode()).hexdigest(), digest)

    def test_template_adapter_and_proof_algorithm_forms_unchanged(self):
        expected = {
            "packs/artifact/proposition_proof.md": "312fe5648c498831eef148505b65b074a8fbfee3",
            "packs/artifact/algorithm_flow.md": "dbd06aacd7216c654789a9002ce682a2065ec0bd",
            "modules/05_writing/latex.md": "98f90f8caa6c3072316dd8e620add05722abfa4b",
            "templates/latex/cumcm/hsk/template_manifest.yaml": "32402842ea88c2a4ce3df052f6c01534b357549f",
            "templates/latex/cumcm/hsk/hsk_main.tex": "789437316271430dee2c5a7ebbdd803f4698ca63",
        }
        for path, digest in expected.items():
            with self.subTest(path=path):
                data = read(path).encode()
                blob = b"blob " + str(len(data)).encode() + b"\0" + data
                self.assertEqual(hashlib.sha1(blob).hexdigest(), digest)

    def test_v85_author_reasoning_voice_semantics_remain_pinned(self):
        contract = yaml.safe_load(read("core/writing_reasoning_contract.yaml"))
        self.assertEqual(contract["schema_version"], "1.8.0")
        trace = contract["prose_style"]["human_reasoning_trace"]
        self.assertEqual(trace["prose_authority"], AUTHORITY)
        self.assertEqual(
            trace["speech_acts"],
            [
                "observation", "open_question", "inquiry", "judgment", "choice",
                "reduction", "introduction", "derivation", "interpretation",
                "validation", "qualification",
            ],
        )
        self.assertEqual(
            trace["question_closure"]["allowed_outcomes"],
            [
                "answered_by_downstream_operation",
                "explicitly_deferred_to_named_validation",
                "retained_as_unverified_hypothesis",
            ],
        )
        self.assertEqual(trace["subject_roles"]["quota"], "none")
        self.assertEqual(
            trace["claim_strength_alignment"]["rule"],
            "prose_claim_strength_must_not_exceed_evidence_strength",
        )
        self.assertEqual(
            trace["necessity_tests"],
            ["reasoning_necessity", "problem_specificity"],
        )
        for item in (
            "pronoun_frequency_target",
            "authorship_inference_from_voice",
            "fabricated_team_consensus",
            "fabricated_trial_and_error_history",
            "rhetorical_question_without_followup",
            "causal_upgrade_from_visual_pattern_only",
            "heuristic_to_global_optimum_upgrade",
            "forced_first_person_in_simple_problem",
            "fixed_phrase_rotation_for_human_impression",
        ):
            self.assertIn(item, trace["prohibit"])

    def test_v86_scope_is_additive_not_a_parallel_authority(self):
        contract = yaml.safe_load(read("core/writing_reasoning_contract.yaml"))
        self.assertIn("model_construction_rationale", contract)
        self.assertIn("precondition_chain", contract["solver_justification"])
        self.assertIn("adaptive_separation", contract["model_establishment_solution_narrative"]["within_question_subsection_architecture"])
        self.assertIn("title_minimality", contract["model_establishment_solution_narrative"]["professional_heading_semantics"])
        self.assertFalse(contract["subsection_granularity"]["hard_count_limit"])
        self.assertFalse(contract["subsection_granularity"]["hard_title_length_limit"])
        for relative in (
            "core/model_construction_rationale_contract.yaml",
            "core/model_applicability_contract.yaml",
            "core/heading_quality_contract.yaml",
            "modules/model_construction_rationale.md",
        ):
            self.assertFalse((ROOT / relative).exists(), relative)

    def test_runtime_keeps_same_stage_topology_and_conditional_examples_only(self):
        runtime = yaml.safe_load(read("core/writing_runtime_contract.yaml"))
        self.assertEqual(runtime["version"], "8.6.0")
        progressive = runtime["template_first_progressive_authoring"]
        stage_ids = [stage["id"] for stage in progressive["stages"]]
        self.assertEqual(
            stage_ids,
            [
                "template_inspection",
                "problem_restatement",
                "problem_analysis",
                "assumptions_symbols_and_preparation",
                "question_model_solution_result_validation",
                "evaluation_references_conclusion_appendix",
                "abstract_title_and_keywords",
                "draft_semantic_review",
                "ai_cleanup",
                "latex_assembly_audit_and_compile",
                "final_review_and_delivery",
            ],
        )
        stages = {stage["id"]: stage for stage in progressive["stages"]}
        conditional = stages["question_model_solution_result_validation"]["conditional_reads_before_relevant_passage"]
        self.assertEqual(conditional["reasoning_example"]["read"], [EXAMPLES])
        self.assertEqual(conditional["model_construction_solution_example"]["read"], [RATIONALE_EXAMPLES])
        for example in (EXAMPLES, RATIONALE_EXAMPLES):
            self.assertTrue((ROOT / example).is_file())
            self.assertNotIn(example, progressive["initial_read_order"])
            self.assertNotIn(example, runtime["ordinary_writing_resource_order"])
            for stage in progressive["stages"]:
                self.assertNotIn(example, stage.get("read_now", []))


class FixedWritingTrialFactsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = yaml.safe_load(read("tests/fixtures/writing_reasoning_cases.yaml"))
        cls.facts = {case["id"]: case["facts"] for case in data["cases"]}
        assert len(cls.facts) == len(data["cases"]) == 4

    def test_heat_balance_and_physical_interval(self):
        f = self.facts["direct_mixing"]
        cold_heat = f["cold_mass_kg"] * (f["target_temperature_c"] - f["cold_temperature_c"])
        hot_drop = f["hot_temperature_c"] - f["target_temperature_c"]
        self.assertGreater(hot_drop, 0)
        self.assertGreater(cold_heat, 0)
        self.assertEqual(cold_heat / hot_drop, f["result_mass_kg"])

    def test_full_integer_candidate_domain_and_unique_solution(self):
        f = self.facts["integer_supply"]
        candidates = list(itertools.product(range(f["batch_capacity_each_period"] + 1), repeat=2))
        self.assertEqual(len(candidates), 9)
        feasible = [x for x in candidates if all(
            f["batch_size"] * batch >= demand for batch, demand in zip(x, f["demand"])
        )]
        self.assertEqual(len(feasible), f["feasible_candidate_count"])
        self.assertEqual(feasible, [tuple(f["result_batches"])])
        self.assertEqual([f["batch_size"] * x for x in feasible[0]], f["result_supply"])
        self.assertEqual(sum(x * c for x, c in zip(feasible[0], f["cost_per_batch"])), f["result_cost"])

    def test_training_fit_and_local_holdout_error(self):
        f = self.facts["linear_prediction"]
        self.assertEqual([2 * t + 1 for t in f["training_t"]], f["training_y"])
        self.assertTrue(set(f["training_t"]).isdisjoint(f["test_t"]))
        pred = [2 * t + 1 for t in f["test_t"]]
        self.assertEqual(pred, f["test_prediction"])
        residual = [y - p for y, p in zip(f["test_y"], pred)]
        self.assertEqual(residual, f["test_residual"])
        self.assertEqual(sum(map(abs, residual)) / len(residual), f["test_mae"])
        i = max(range(len(residual)), key=lambda j: abs(residual[j]))
        self.assertEqual(f["test_t"][i], f["largest_error_t"])
        self.assertEqual(abs(residual[i]), f["largest_absolute_error"])

    def test_declared_inverse_trace_and_position_tolerance(self):
        facts = self.facts["monotone_inverse"]
        a, b = facts["domain"]
        f = lambda x: x * x + 2 * x
        self.assertLess(f(a), facts["target"])
        self.assertGreater(f(b), facts["target"])
        self.assertGreater(2 * a + 2, 0)
        m = (a + b) / 2
        self.assertEqual(m, 1)
        self.assertEqual(f(m), facts["target"])
        self.assertLess((b - a) / (2 ** 22), 1e-6)
        self.assertLess(21 + 1, 30)


if __name__ == "__main__":
    unittest.main()
