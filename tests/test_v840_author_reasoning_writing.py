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
            "5A. Cross-File Chapter Handoff": "b8ddf97618ca7e837ca5194e0af9f654150d348fbb99cb8249f0a9328f11f70d",
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
        # Earlier v8.4 snapshots still protect the substantive proof/algorithm forms.
        frozen = {
            "packs/artifact/proposition_proof.md": "312fe5648c498831eef148505b65b074a8fbfee3",
            "packs/artifact/algorithm_flow.md": "dbd06aacd7216c654789a9002ce682a2065ec0bd",
        }

        def git_blob_sha1(text: str) -> str:
            data = text.encode()
            blob = b"blob " + str(len(data)).encode() + b"\0" + data
            return hashlib.sha1(blob).hexdigest()

        for path, digest in frozen.items():
            with self.subTest(path=path):
                self.assertEqual(git_blob_sha1(read(path)), digest)

        # v8.7.1 R6 intentionally reopens only active release-label/provenance lines.
        # Normalize those exact lines back to the pre-R6 representation, then keep the
        # old whole-file snapshot as a guard against unrelated Adapter/template drift.
        adapter = read("modules/05_writing/latex.md")
        self.assertTrue(adapter.startswith("# Module 05B：LaTeX Adapter\n"))
        self.assertIn("Template-First adapter architecture introduced in v8.0.1", adapter)
        self.assertIn("当前 Skill release 版本只由活动 release carriers", adapter)
        adapter_current = (
            "本模块只负责把已经确定的论文内容放入当前 LaTeX 载体。"
            "**Template-First adapter architecture introduced in v8.0.1**；"
            "当前 Skill release 版本只由活动 release carriers（如 `core/bootstrap.yaml`）声明，"
            "本标题不再携带历史 release 号。本文件不再拥有正文结构或表达规则。"
        )
        adapter_legacy = (
            "本模块只负责把已经确定的论文内容放入当前 LaTeX 载体。"
            "v8.0.0 采用 **Template-First** 架构，本文件不再拥有正文结构或表达规则。"
        )
        normalized_adapter = adapter.replace(
            "# Module 05B：LaTeX Adapter\n",
            "# Module 05B：LaTeX Adapter（v8.0.1）\n",
            1,
        ).replace(adapter_current, adapter_legacy, 1)
        self.assertEqual(
            git_blob_sha1(normalized_adapter),
            "98f90f8caa6c3072316dd8e620add05722abfa4b",
        )

        # v8.7.2 keeps the CUMCM AI-disclosure source in the canonical project but
        # makes its input conditional/truth-bound by default. Keep the exact current
        # orchestration pinned so an unconditional reactivation or unrelated drift fails closed.
        main = read("templates/latex/cumcm/hsk/hsk_main.tex")
        provenance = (
            "% Template-First canonical layout lineage: introduced in v8.0.1 from the A196-inspired template work.\n"
            "% This comment records provenance only; the current Skill release is declared by active release carriers."
        )
        self.assertIn(provenance, main)
        self.assertIn(r"% \input{sections/10_ai_tool_statement}", main)
        active_main = "\n".join(line.split("%", 1)[0] for line in main.splitlines())
        self.assertNotIn(r"\input{sections/10_ai_tool_statement}", active_main)
        normalized_main = main.replace(
            provenance,
            "% v8.0.1 A196-inspired canonical template:",
            1,
        )
        self.assertEqual(
            git_blob_sha1(normalized_main),
            "0552dc0d86c71c69e40d4693d5af564deb26feeb",
        )

        manifest = yaml.safe_load(read("templates/latex/cumcm/hsk/template_manifest.yaml"))
        self.assertEqual(manifest["schema_version"], "1.0.0")
        self.assertEqual(manifest["template_id"], "hsk_cumcm_v8")
        question = manifest["cumcm_question_section"]
        self.assertEqual(question["title_pattern"], "问题{N}模型建立及求解")
        self.assertTrue(question["title_locked"])
        self.assertEqual(question["internal_structure"], "adaptive")
        self.assertEqual(question["functional_slots"], ["model", "solve", "result", "validate"])
        rendering = manifest["core_model_summary_rendering"]
        self.assertFalse(rendering["independent_named_subsection_default"])
        self.assertTrue(rendering["simple_problem_anti_bloat"])
        fixed = manifest["fixed_template_checks"]
        self.assertTrue(fixed["objective_before_constraints"])
        self.assertTrue(fixed["objective_outside_constraint_brace"])
        self.assertFalse(fixed["runtime_semantic_authority"])

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
        self.assertEqual(runtime["version"], "8.7.1")
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
