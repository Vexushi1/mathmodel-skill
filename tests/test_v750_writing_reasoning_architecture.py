from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class TestV750WritingReasoningArchitecture(unittest.TestCase):
    def test_reasoning_contract_is_general_not_problem_specific(self):
        data = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(data["scope"]["competitions"], "all")
        families = set(data["scope"]["task_families"])
        for family in (
            "mechanism_geometry",
            "statistics_regression",
            "prediction_time_series",
            "optimization_operations_research",
            "machine_learning",
            "spatial_econometrics",
            "mixed_multi_question",
        ):
            self.assertIn(family, families)
        anti = "\n".join(data["scope"]["anti_template_boundary"])
        self.assertIn("不从单一优秀论文复制", anti)
        self.assertIn("不要求所有论文设置", anti)

    def test_formula_chain_has_source_derivation_destination_and_adaptive_depth(self):
        data = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))
        chain = data["formula_reasoning_chain"]
        self.assertEqual(chain["chain"], ["source", "derivation", "destination"])
        self.assertIn("verified_standard_theorem", chain["source_allowed"])
        self.assertIn("build_constraint", chain["destination_allowed"])
        self.assertIn("按题型自适应", chain["derivation_rule"])
        self.assertIn("下一步如何使用", "\n".join(chain["chain_quality_rules"]))

    def test_shared_foundation_and_progression_are_conditional(self):
        data = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))
        shared = data["shared_foundation"]
        progression = data["cross_question_progression"]
        self.assertEqual(shared["default"], "adaptive")
        self.assertEqual(shared["naming"], "dynamic")
        self.assertIn("question_specific_optimum_or_result", shared["forbidden_contents"])
        self.assertEqual(progression["activate_when"], "actual_dependency_exists")
        self.assertEqual(
            progression["paragraph_information_order"],
            [
                "inherited_structure",
                "new_object_condition_or_requirement",
                "changed_modeling_difficulty",
                "model_and_solver_increment",
            ],
        )

    def test_structure_precedes_algorithm_and_parameters_require_evidence(self):
        data = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))
        simplify = data["structure_before_algorithm"]
        params = data["numerical_parameter_evidence"]
        self.assertEqual(simplify["check_order"][-1], "final_solver_selection")
        self.assertIn("problem_structure", simplify["writing_order"])
        self.assertIn("candidate_range", params["chain"])
        self.assertIn("selected_value", params["chain"])
        self.assertIn("optimization", params["evidence_by_family"])
        self.assertIn("机器学习", (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8"))

    def test_multi_method_validation_has_numerical_and_structural_levels(self):
        data = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))
        two = data["multi_method_validation"]["two_levels"]
        self.assertIn("numerical_consistency", two)
        self.assertIn("structural_consistency", two)
        latex = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        self.assertIn("结构结论", latex)
        self.assertIn("数值接近但结构判断冲突", latex)

    def test_framework_records_reasoning_without_creating_user_sidecar_files(self):
        framework = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        self.assertIn("### 推理结构合同", framework)
        self.assertIn("共享基础模型判断", framework)
        self.assertIn("跨问模型增量", framework)
        self.assertIn("核心公式链索引", framework)
        self.assertIn("数值参数依据", framework)
        self.assertIn("不把内部合同表机械复制进正文", framework)

    def test_reasoning_chain_is_registered_in_manifest_and_output_contract(self):
        manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8"))
        output = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(manifest["contracts"]["writing_reasoning"], "core/writing_reasoning_contract.yaml")
        self.assertIn("formula_reasoning_chain", manifest["artifact_catalog"])
        self.assertIn("formula_reasoning_chain", manifest["modules"]["model_design"]["outputs"])
        self.assertIn("formula_reasoning_chain", manifest["workflow_profiles"]["design"]["terminal_outputs"])
        self.assertEqual(output["writing_reasoning_contract"], "core/writing_reasoning_contract.yaml")
        self.assertEqual(output["writing_policy"]["reasoning_contract"], "core/writing_reasoning_contract.yaml")

    def test_model_design_and_writing_consume_same_authority(self):
        for relative in (
            "modules/02_model_design.md",
            "modules/05_writing/latex.md",
            "modules/05_writing/ai_cleanup.md",
            "packs/artifact/proposition_proof.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("core/writing_reasoning_contract.yaml", text, relative)

    def test_language_contract_keeps_natural_connectors_without_word_ban(self):
        data = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))
        prose = data["prose_style"]
        self.assertEqual(prose["name"], "evidence_driven_undergraduate_academic")
        for word in ("根据", "因此", "进一步", "从而"):
            self.assertIn(word, prose["allow_natural_connectors"])
        self.assertIn("不是禁词", prose["connector_policy"])

    def test_machine_audit_explicitly_rejects_semantic_overclaim(self):
        data = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))
        boundary = data["machine_audit_boundary"]
        self.assertTrue(boundary["report_only_for_semantic_style_risks"])
        self.assertIn("mathematical_correctness_from_regex", boundary["must_not_claim"])
        self.assertIn("formula_source_semantic_validity_from_keywords_only", boundary["must_not_claim"])


if __name__ == "__main__":
    unittest.main()
