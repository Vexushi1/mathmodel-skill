import importlib.util
import sys
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def load_surface_audit():
    path = ROOT / "scripts/audit_v8_writing_surface.py"
    spec = importlib.util.spec_from_file_location("audit_v8_surface_v801", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_runtime_resolver():
    scripts = ROOT / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    path = scripts / "resolve_runtime.py"
    spec = importlib.util.spec_from_file_location("resolve_runtime_v801_sequence", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestV801ChapterCapabilityPreservation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = read("modules/05_writing/paper_writing_protocol.md")
        cls.review = read("modules/06_review_delivery.md")
        cls.audit_doc = read("docs/v801_chapter_capability_preservation_audit.md")
        cls.runtime = yaml.safe_load(read("core/writing_runtime_contract.yaml"))
        cls.reasoning = yaml.safe_load(read("core/writing_reasoning_contract.yaml"))
        cls.manifest = yaml.safe_load(read("templates/latex/cumcm/hsk/template_manifest.yaml"))
        cls.surface = load_surface_audit()
        cls.resolver = load_runtime_resolver()

    def test_full_reasoning_authority_keeps_model_solution_semantic_depth(self):
        narrative = self.reasoning["model_establishment_solution_narrative"]
        required = {
            "continuous_mathematical_narrative",
            "formula_prose_rhythm",
            "transition_function_governance",
            "within_question_subsection_architecture",
            "detail_allocation_governance",
            "model_to_solver_bridge",
            "result_adjacent_interpretation",
            "figure_result_narrative",
            "question_section_narrative_closure",
            "prose_target",
        }
        self.assertTrue(required.issubset(narrative), required - set(narrative))

    def test_compact_runtime_exposes_every_chapter_family(self):
        capabilities = set(self.runtime["semantic_capabilities"]["chapter_content_from_protocol"])
        required = {
            "title_and_keywords_evidence_alignment",
            "abstract_per_question_information_closure",
            "problem_restatement_without_prompt_copying",
            "coherent_problem_analysis",
            "assumption_rationale_and_failure_impact",
            "symbol_cross_artifact_consistency",
            "data_preprocessing_and_shared_foundation_boundary",
            "model_construction_rationale_and_local_applicability",
            "model_establishment_detail_preservation",
            "solver_precondition_and_detail_preservation",
            "adaptive_subsection_separation_and_title_minimality",
            "numeric_and_terminology_consistency",
            "citation_use_boundary",
            "figure_role_specific_interpretation",
            "model_evaluation_evidence_boundary",
            "direct_answer_conclusion_boundary",
            "appendix_body_boundary",
        }
        self.assertEqual(required, capabilities)

    def test_default_writing_flow_is_template_first_and_progressive(self):
        progressive = self.runtime["template_first_progressive_authoring"]
        stages = progressive["stages"]
        stage_ids = [stage["id"] for stage in stages]
        self.assertEqual(
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
            stage_ids,
        )
        self.assertEqual([], stages[0]["write_now"])
        self.assertIn("template_manifest.yaml", " ".join(stages[0]["read_now"]))
        for stage in stages[1:]:
            self.assertIn("gate", stage, stage["id"])
        self.assertEqual(
            "core/writing_runtime_contract.yaml#template_first_progressive_authoring",
            self.manifest["authoring_execution_pointer"],
        )
        forbidden = set(self.manifest["authority_boundary"]["forbidden_template_authority"])
        self.assertIn("generate_body_during_template_inspection", forbidden)
        self.assertIn("replace_progressive_chapter_authoring_order", forbidden)

    def test_problem_restatement_and_analysis_are_separate_read_write_stages(self):
        stages = {
            stage["id"]: stage
            for stage in self.runtime["template_first_progressive_authoring"]["stages"]
        }
        restatement = stages["problem_restatement"]
        analysis = stages["problem_analysis"]
        self.assertTrue(any("#6.1-问题重述" in item for item in restatement["read_now"]))
        self.assertEqual(
            ["templates/latex/cumcm/hsk/sections/01_problem_statement.tex"],
            restatement["write_now"],
        )
        self.assertTrue(any("#6.2-问题分析" in item for item in analysis["read_now"]))
        self.assertEqual(
            ["templates/latex/cumcm/hsk/sections/02_problem_analysis.tex"],
            analysis["write_now"],
        )

    def test_question_stage_keeps_proof_and_pseudocode_conditional_branches(self):
        stages = {
            stage["id"]: stage
            for stage in self.runtime["template_first_progressive_authoring"]["stages"]
        }
        question = stages["question_model_solution_result_validation"]
        self.assertTrue(question["repeat_for_each_question_in_template_order"])
        joined = " ".join(question["read_now"])
        for section in ("#7-模型建立", "#8-模型求解", "#9-求解结果数值与术语", "#10-结果与验证的分层"):
            self.assertIn(section, joined)
        branches = question["conditional_reads_before_relevant_passage"]
        self.assertEqual(
            {
                "core/writing_reasoning_contract.yaml",
                "packs/artifact/proposition_proof.md",
            },
            set(branches["proposition_or_proof"]["read"]),
        )
        self.assertIn("packs/artifact/algorithm_flow.md", branches["stepwise_or_pseudocode"]["read"])
        self.assertIn("not_needed", branches["stepwise_or_pseudocode"]["when"])
        self.assertIn(
            "modules/05_writing/references/model_construction_solution_rationale_examples.md",
            branches["model_construction_solution_example"]["read"],
        )

    def test_review_cleanup_compile_and_final_review_order_is_locked(self):
        stage_ids = [
            stage["id"]
            for stage in self.runtime["template_first_progressive_authoring"]["stages"]
        ]
        self.assertLess(stage_ids.index("draft_semantic_review"), stage_ids.index("ai_cleanup"))
        self.assertLess(stage_ids.index("ai_cleanup"), stage_ids.index("latex_assembly_audit_and_compile"))
        self.assertLess(stage_ids.index("latex_assembly_audit_and_compile"), stage_ids.index("final_review_and_delivery"))

    def test_resolver_exposes_sequence_instead_of_hiding_it_in_resource_order(self):
        plan = self.resolver.resolve_runtime("latex", competition="CUMCM")
        writing = plan["writing_runtime"]
        self.assertEqual("template_first_progressive_authoring", writing["execution_mode"])
        self.assertIn("不表示可以在开篇一次性预读", writing["resource_order_semantics"])
        self.assertEqual(
            [
                "core/hsk_core_policy.md",
                "core/writing_runtime_contract.yaml",
                "templates/latex/cumcm/hsk/template_manifest.yaml",
                "templates/latex/cumcm/hsk/hsk_main.tex",
            ],
            writing["initial_read_order"],
        )
        self.assertEqual(
            "template_inspection",
            writing["authoring_sequence"][0]["id"],
        )

    def test_protocol_preserves_detailed_model_establishment_and_solution_inputs(self):
        for detail in (
            "决策变量/决策对象及定义域、单位和现实含义",
            "为什么优化该量就回答本问",
            "约束条件、来源和对可行域的作用",
            "不能替代前面对变量、目标函数现实含义、约束来源和关键推导的说明",
            "只有直接法确实不足时才说明其限制",
            "本题变量/状态编码、目标或适应度评价、约束处理、初始化、关键参数、精度/终止条件以及输出映射",
            "程序正常结束",
        ):
            self.assertIn(detail, self.protocol)

    def test_protocol_preserves_non_question_chapter_detail(self):
        for detail in (
            "数据说明与必要预处理",
            "共享基础与模型准备",
            "数值展示",
            "术语一致性",
            "外部经验参数、外部数据、领域事实、非显然标准定理",
            "模型评价不能替代",
            "不能把论证主体全部移入附录",
        ):
            self.assertIn(detail, self.protocol)

    def test_q1_q2_q3_are_maintained_template_examples(self):
        examples = self.manifest["cumcm_question_section"]["maintained_examples"]
        sources = {item["source"] for item in examples}
        expected = {
            "sections/06_question1.tex",
            "sections/07_question2.tex",
            "sections/08_question3.tex",
        }
        self.assertEqual(expected, sources)
        for source, number in zip(sorted(sources), ("一", "二", "三")):
            text = read(f"templates/latex/cumcm/hsk/{source}")
            self.assertIn(f"\\section{{问题{number}模型建立及求解}}", text)
            self.assertIn("模型求解", text)
            self.assertIn("求解结果", text)
            self.assertIn("结果的分析与验证", text)

    def test_explicit_stage_order_reversal_is_reported(self):
        tex = r"""
\section{问题一模型建立及求解}
\subsection{求解结果}先给结果。
\subsection{模型求解}再写求解。
"""
        findings = self.surface.audit_text(tex)
        self.assertTrue(any(item.code == "question_stage_order_risk" for item in findings), findings)

    def test_professional_headings_are_not_mechanically_failed(self):
        tex = r"""
\section{问题一模型建立及求解}
\subsection{候选边界的确定}由几何关系得到候选域。
\subsection{公共斜率的估计}利用候选域估计厚度。
\subsection{厚度结果及误差范围}给出结果和误差。
"""
        findings = self.surface.audit_text(tex)
        self.assertFalse(any(item.code == "question_stage_order_risk" for item in findings), findings)

    def test_solver_first_without_structure_is_reported(self):
        tex = r"""
\section{问题二模型建立及求解}
\subsection{模型求解}
采用遗传算法进行求解，该算法具有较强的全局搜索能力。
"""
        findings = self.surface.audit_text(tex)
        self.assertTrue(any(item.code == "solver_first_narrative" for item in findings), findings)

    def test_structure_led_solver_entry_is_not_reported(self):
        tex = r"""
\section{问题二模型建立及求解}
\subsection{模型求解}
目标函数由离散判定累计得到且不可导，搜索空间同时包含整数变量，因此采用遗传算法搜索可行方案。
"""
        findings = self.surface.audit_text(tex)
        self.assertFalse(any(item.code == "solver_first_narrative" for item in findings), findings)

    def test_consecutive_figures_without_local_explanation_are_reported(self):
        tex = r"""
\begin{figure}\includegraphics{a}\caption{图一}\end{figure}
\begin{figure}\includegraphics{b}\caption{图二}\end{figure}
"""
        findings = self.surface.audit_text(tex)
        self.assertTrue(
            any(item.code == "consecutive_figures_without_local_interpretation" for item in findings),
            findings,
        )

    def test_figures_in_different_question_sections_are_not_treated_as_consecutive(self):
        tex = r"""
\section{问题一模型建立及求解}
\begin{figure}\includegraphics{a}\caption{图一}\end{figure}
\section{问题二模型建立及求解}
\begin{figure}\includegraphics{b}\caption{图二}\end{figure}
"""
        findings = self.surface.audit_text(tex)
        self.assertFalse(
            any(item.code == "consecutive_figures_without_local_interpretation" for item in findings),
            findings,
        )

    def test_review_and_audit_matrix_close_v720_execution_layer(self):
        for detail in (
            "v7.20/v8.0.1 章节能力保全检查",
            "装饰性引号",
            "solver 入口",
            "Document Length Profile",
            "目标函数位于约束大括号外",
        ):
            self.assertIn(detail, self.review)
        self.assertIn("v7.19 章节能力迁移矩阵", self.audit_doc)
        self.assertIn("v7.20 R1 实施矩阵", self.audit_doc)

    def test_audit_matrix_accounts_for_every_legacy_writing_family(self):
        legacy_families = (
            "写作输入与事实源",
            "规则等级",
            "标题与关键词",
            "摘要",
            "中文国赛一级骨架",
            "段落必要性",
            "问题重述",
            "问题分析",
            "假设与符号",
            "数据说明/预处理",
            "共享基础/模型准备",
            "模型推导",
            "优化模型建立",
            "非优化模型建立",
            "命题与证明",
            "核心模型汇总",
            "模型求解",
            "算法呈现",
            "数值展示",
            "术语与模型命名",
            "求解结果",
            "结果验证",
            "跨问递进",
            "图结果叙事",
            "模型评价与推广",
            "逐问结论与附录",
            "Citation Evidence",
            "自然学术表达",
            "篇幅与工作量",
            "LaTeX 环境、审计和输出",
        )
        missing = [name for name in legacy_families if f"| {name} |" not in self.audit_doc]
        self.assertEqual([], missing)


if __name__ == "__main__":
    unittest.main()
