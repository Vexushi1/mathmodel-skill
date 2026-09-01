import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class TestV718ModelSolutionWritingStyle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract_path = ROOT / "core/writing_reasoning_contract.yaml"
        cls.contract_text = cls.contract_path.read_text(encoding="utf-8")
        cls.contract = yaml.safe_load(cls.contract_text)
        cls.protocol = (ROOT / "modules/05_writing/paper_writing_protocol.md").read_text(encoding="utf-8")
        cls.cleanup = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        cls.module02 = (ROOT / "modules/02_model_design.md").read_text(encoding="utf-8")
        cls.taxonomy = (ROOT / "core/task_taxonomy.yaml").read_text(encoding="utf-8")
        cls.numerical = (ROOT / "core/numerical_verification_contract.yaml").read_text(encoding="utf-8")
        cls.approval = (ROOT / "core/model_approval_contract.yaml").read_text(encoding="utf-8")
        cls.workbook = (ROOT / "core/workbook_schema.yaml").read_text(encoding="utf-8")
        cls.project_state = (ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8")
        cls.router = (ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8")

    def test_single_narrative_authority_exists(self):
        self.assertEqual(self.contract["schema_version"], "1.6.0")
        self.assertIn("model_establishment_solution_narrative", self.contract)
        self.assertEqual(
            self.contract["model_establishment_solution_narrative"]["governance_level"],
            "default",
        )
        self.assertIn("core/writing_reasoning_contract.yaml", self.protocol)
        self.assertIn("model_establishment_solution_narrative", self.cleanup)
        for relative in (
            "core/model_solution_writing_contract.yaml",
            "core/model_establishment_writing_contract.yaml",
            "packs/artifact/model_solution_prose.md",
            "modules/model_solution_writing.md",
        ):
            self.assertFalse((ROOT / relative).exists(), relative)

    def test_continuous_mathematical_narrative_is_functional_not_report_like(self):
        rule = self.contract["model_establishment_solution_narrative"]
        progression = rule["continuous_mathematical_narrative"]["preferred_progression"]
        self.assertEqual(
            progression,
            [
                "inherit_current_object_or_relation",
                "identify_next_mathematical_need",
                "introduce_only_needed_object_or_quantity",
                "derive_define_or_transform_relation",
                "state_structural_or_problem_consequence",
                "continue_to_next_relation_final_model_or_solution",
            ],
        )
        combined_rules = "\n".join(rule["continuous_mathematical_narrative"]["rules"])
        self.assertIn("报告式罗列", combined_rules)
        self.assertIn("承接当前对象或上一关系", self.protocol)
        self.assertIn("为什么此时出现", self.protocol)
        self.assertIn("出现后下一步怎样变化", self.protocol)

    def test_formula_prose_rhythm_consumes_existing_formula_authority(self):
        narrative = self.contract["model_establishment_solution_narrative"]
        formula = narrative["formula_prose_rhythm"]
        self.assertEqual(formula["consumes"], "formula_reasoning_chain")
        self.assertEqual(
            formula["functional_sequence"],
            ["need", "basis", "formula", "meaning", "consequence"],
        )
        self.assertIn("符号已经定义后", formula["meaning_priority"])
        self.assertIn("公式后优先说明它如何改变判据、可行域、目标、候选域或计算结构", self.protocol)
        self.assertNotIn("Need：", self.protocol)
        self.assertNotIn("Basis：", self.protocol)

    def test_model_section_does_not_repeat_problem_analysis_or_assumption_lists(self):
        separation = self.contract["model_establishment_solution_narrative"]["stage_separation"]
        self.assertIn("不重新完整复述问题分析", separation["rule"])
        self.assertIn("repeated_problem_analysis_in_model_section", separation["review_risks"])
        self.assertIn("repeated_assumption_list_in_model_section", separation["review_risks"])
        self.assertIn("默认不重新写一遍问题分析、模型假设和题目要求", self.protocol)
        self.assertIn("模型建立开头重新完整复述题目、问题分析或模型假设", self.cleanup)

    def test_transition_functions_are_roles_not_phrase_bank(self):
        transitions = self.contract["model_establishment_solution_narrative"][
            "transition_function_governance"
        ]
        self.assertEqual(
            transitions["functional_roles"],
            [
                "inherit",
                "gap",
                "introduce",
                "transform",
                "solve_entry",
                "result_entry",
                "interpret",
                "increment",
            ],
        )
        self.assertTrue(transitions["phrase_bank_forbidden"])
        self.assertIn("不建立推荐连接词词库", self.protocol)
        self.assertIn("判断标准是逻辑功能，不是连接词词表", self.cleanup)

    def test_heading_semantics_use_independent_mathematical_tasks(self):
        headings = self.contract["model_establishment_solution_narrative"][
            "professional_heading_semantics"
        ]
        self.assertEqual(headings["preferred_pattern"], "object_plus_mathematical_task")
        self.assertFalse(headings["hard_grammar_rule"])
        self.assertIn("模型处理", headings["generic_heading_review_examples"])
        self.assertIn("结果说明", headings["generic_heading_review_examples"])
        self.assertIn("标题应对应**独立数学任务**", self.protocol)
        self.assertIn("不强制所有标题使用“XX 的 XX”", self.protocol)
        self.assertIn("泛化标题", self.cleanup)

    def test_solver_narrative_is_structure_before_algorithm(self):
        bridge = self.contract["model_establishment_solution_narrative"]["model_to_solver_bridge"]
        self.assertEqual(
            bridge["consumes"],
            ["structure_before_algorithm", "solver_justification", "model_solver_validator_roles"],
        )
        order = bridge["first_use_progression"]
        self.assertLess(order.index("current_model_structure_or_computational_difficulty"), order.index("solver_family_fit"))
        self.assertLess(order.index("exploitable_property_or_completed_simplification"), order.index("solver_family_fit"))
        self.assertTrue(bridge["generic_algorithm_praise_is_insufficient"])
        self.assertIn("不用“下面进行模型求解”作为唯一过渡", self.protocol)
        self.assertIn("求解段一开始就是算法名或算法优点", self.cleanup)

    def test_result_adjacent_interpretation_has_three_adaptive_profiles(self):
        result_rule = self.contract["model_establishment_solution_narrative"][
            "result_adjacent_interpretation"
        ]
        self.assertEqual(
            set(result_rule["profiles"]),
            {"point_optimum_or_parameter", "curve_or_figure", "algorithm_accuracy_or_validation"},
        )
        self.assertIn("support_modify_or_reject_target_claim", result_rule["profiles"]["algorithm_accuracy_or_validation"]["preferred_progression"])
        self.assertIn("关键结果出现后要在邻近位置完成", self.protocol)
        self.assertIn("核心结果远离所有解释", self.cleanup)
        self.assertIn("不要求每张图固定使用相同句数、句序和词语", self.cleanup)

    def test_cross_question_language_keeps_incremental_writing(self):
        rule = self.contract["model_establishment_solution_narrative"]["cross_question_language"]
        self.assertEqual(rule["consumes"], "cross_question_progression")
        self.assertIn("只展开新增数学关系与求解变化", rule["rule"])
        self.assertIn("共同轨迹、共同概率关系或共同网络结构不从头复制", self.protocol)
        self.assertIn("同理", self.protocol)

    def test_cleanup_risks_are_review_or_warning_not_new_blocking_semantics(self):
        audit = self.contract["machine_audit_boundary"]
        narrative_risks = {
            "report_like_model_listing",
            "formula_without_need_or_consequence",
            "solver_first_narrative",
            "generic_heading_density",
            "management_transition",
            "detached_result_interpretation",
            "repeated_problem_analysis_in_model_section",
        }
        review_or_warn = set(audit["may_review"]) | set(audit["may_warn"])
        self.assertTrue(narrative_risks <= review_or_warn)
        self.assertTrue(narrative_risks.isdisjoint(set(audit["may_block"])))
        self.assertIn("不得仅凭连接词、标题语法、算法名、段落距离、小节数量、字数、公式数、图引用关键词或表面顺序判断叙事/详略质量", self.cleanup)
        self.assertIn("narrative_quality_from_connector_words_only", audit["must_not_claim"])

    def test_reference_papers_do_not_become_runtime_templates(self):
        anti_template = "\n".join(
            self.contract["model_establishment_solution_narrative"]["anti_template_boundary"]
        )
        for token in ("PSO", "GA", "DE", "二分法", "坐标搜索"):
            self.assertIn(token, anti_template)
        self.assertIn("不复制任何优秀论文的固定句子", anti_template)
        combined = self.contract_text + "\n" + self.protocol + "\n" + self.cleanup
        self.assertNotIn("A066", combined)
        self.assertNotIn("A196", combined)

    def test_no_modeling_or_runtime_gate_schema_expansion(self):
        forbidden_tokens = (
            "model_solution_narrative_gate",
            "requires_model_solution_narrative",
            "requires_professional_heading_semantics",
            "requires_result_adjacent_interpretation",
        )
        protected = "\n".join(
            [
                self.taxonomy,
                self.numerical,
                self.approval,
                self.workbook,
                self.project_state,
                self.router,
                self.module02,
            ]
        )
        for token in forbidden_tokens:
            self.assertNotIn(token, protected)
        self.assertIn("Human Model Approval", self.module02)
        self.assertIn("semantic_closure_status=passed", self.module02)
        self.assertNotIn("model_establishment_solution_narrative", self.module02)


if __name__ == "__main__":
    unittest.main()
