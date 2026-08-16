from pathlib import Path
import json
import unittest

import yaml

ROOT = Path(__file__).resolve().parent.parent


class WritingExpressionProtocolV730Tests(unittest.TestCase):
    def test_latex_module_owns_shared_expression_protocol(self):
        latex = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        self.assertIn("正文表达与章节组织协议（写作权威）", latex)
        self.assertIn("问题重述：问题背景 + 问题提出", latex)
        self.assertIn("问题分析：国赛式逐问分析，不写公式和结果", latex)
        self.assertIn("模型推导：核心公式必须有来源、推导和去向", latex)
        for token in ("（Source）", "（Derivation）", "（Destination）"):
            self.assertIn(token, latex)
        self.assertIn("共享基础模型：按需单列，后问写增量", latex)
        self.assertIn("结构化简优先于算法升级", latex)
        self.assertIn("数值参数必须有选择证据", latex)
        self.assertIn("核心模型汇总：推导后、求解前必须出现", latex)
        self.assertIn("求解结果：图表、数值、机制和题目回答就近闭环", latex)
        self.assertIn("模型的评价与推广", latex)
        self.assertIn("证据驱动的本科生学术表达", latex)
        self.assertIn("分段优先，分点按需", latex)

    def test_docx_and_cleanup_reference_shared_authority(self):
        docx = (ROOT / "modules/05_writing/docx.md").read_text(encoding="utf-8")
        cleanup = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        marker = "正文表达与章节组织协议（写作权威）"
        self.assertIn(marker, docx)
        self.assertIn(marker, cleanup)
        self.assertIn("问题重述去复制化", cleanup)
        self.assertIn("问题提出逐问化", cleanup)
        self.assertIn("问题分析去流程图化", cleanup)
        self.assertIn("问题分析禁公式结果", cleanup)
        self.assertIn("假设去万能化", cleanup)
        self.assertIn("推导去教科书化", cleanup)
        self.assertIn("核心公式 Source 检查", cleanup)
        self.assertIn("公式链检查", cleanup)
        self.assertIn("数值参数依据检查", cleanup)
        self.assertIn("结果去报表化", cleanup)
        self.assertIn("评价去万能化", cleanup)
        self.assertIn("正向叙述优先", cleanup)
        self.assertIn("证据驱动的本科生学术表达", cleanup)
        self.assertIn("成稿机器审计", cleanup)
        self.assertIn("audit_paper_prose.py", cleanup)

    def test_latex_pack_enforces_non_template_writing(self):
        pack = (ROOT / "packs/artifact/latex.md").read_text(encoding="utf-8")
        self.assertIn("问题重述默认采用“问题背景 + 问题提出”", pack)
        self.assertIn("问题分析必须说明本问难点、对象关系、跨问依赖和建模抓手", pack)
        self.assertIn("核心图表/关键数值引用—比较基准—机制—题目回答—必要边界", pack)
        self.assertIn("不强制“优点三条、缺点两条、推广一段”", pack)
        self.assertIn("B 级短证明默认自然分段", pack)

    def test_framework_records_project_specific_writing_strategy(self):
        framework = (ROOT / "templates/model/model_paper_framework.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("### 写作组织策略", framework)
        self.assertIn("主写作类型", framework)
        self.assertIn("问题重述口径", framework)
        self.assertIn("问题分析安排", framework)
        self.assertIn("共享基础模型", framework)
        self.assertIn("跨问模型增量", framework)
        self.assertIn("核心公式链索引", framework)
        self.assertIn("数值参数依据", framework)
        self.assertIn("结果解释链", framework)
        self.assertIn("模型评价安排", framework)
        self.assertIn("正向叙述策略", framework)
        self.assertIn("写作组织策略已按当前题型和证据链确定", framework)

    def test_writing_reasoning_contract_is_cross_competition_and_adaptive(self):
        contract = yaml.safe_load(
            (ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(contract["scope"]["competitions"], "all")
        self.assertEqual(contract["formula_reasoning_chain"]["chain"], ["source", "derivation", "destination"])
        self.assertEqual(contract["shared_foundation"]["default"], "adaptive")
        self.assertEqual(
            contract["cross_question_progression"]["activate_when"],
            "actual_dependency_exists",
        )
        self.assertTrue(contract["proposition_downstream_consequence"]["required_when_proposition_is_used_for_computation"])
        self.assertEqual(contract["prose_style"]["name"], "evidence_driven_undergraduate_academic")
        self.assertTrue(contract["machine_audit_boundary"]["report_only_for_semantic_style_risks"])

    def test_output_contract_points_to_shared_authority(self):
        output = yaml.safe_load(
            (ROOT / "core/output_contract.yaml").read_text(encoding="utf-8")
        )
        policy = output["writing_policy"]
        self.assertIn("modules/05_writing/latex.md", policy["expression_authority"])
        self.assertTrue(policy["adaptive_sectioning_by_task_type"])
        self.assertTrue(policy["problem_restatement_copy_forbidden"])
        self.assertEqual(policy["problem_restatement_second_section"], "问题提出")
        self.assertTrue(policy["problem_statement_per_question_required"])
        self.assertTrue(policy["problem_analysis_pipeline_listing_forbidden"])
        self.assertTrue(policy["problem_analysis_formula_result_forbidden"])
        self.assertTrue(policy["assumptions_symbols_separate_sections"])
        self.assertTrue(policy["core_model_summary_before_solve_required"])
        self.assertEqual(policy["question_result_section_default"], "求解结果")
        self.assertFalse(policy["standalone_paper_conclusion_default"])
        self.assertTrue(policy["generic_textbook_derivation_forbidden"])
        self.assertTrue(policy["generic_model_evaluation_forbidden"])
        self.assertTrue(policy["affirmative_statement_preferred"])
        self.assertTrue(policy["novice_academic_rewrite_after_cleanup"])
        self.assertEqual(policy["proof_structure_default"], "paragraph_first")
        self.assertTrue(policy["proof_numbered_steps_when_needed"])
        self.assertNotIn("proposition_proof_segmented_steps", policy)
        self.assertEqual(policy["prose_audit_script"], "scripts/audit_paper_prose.py")

    def test_bootstrap_registers_reasoning_authority_without_global_preload(self):
        bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))
        self.assertEqual(
            bootstrap["authoritative_sources"]["writing_reasoning"],
            "core/writing_reasoning_contract.yaml",
        )
        self.assertIn("Source—Derivation—Destination", "\n".join(bootstrap["hard_invariants"]))

    def test_release_versions_are_consistent(self):
        bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))
        manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8"))
        output = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        plugin = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(bootstrap["skill_version"], "7.4.5")
        self.assertEqual(manifest["version"], "7.4.5")
        self.assertEqual(output["version"], "7.4.5")
        self.assertEqual(plugin["version"], "7.4.5")
        self.assertIn("version: 7.4.5", (ROOT / "SKILL.md").read_text(encoding="utf-8"))
        self.assertIn(
            "version: 7.4.5",
            (ROOT / "skills/mathmodel-skill/SKILL.md").read_text(encoding="utf-8"),
        )
        self.assertTrue((ROOT / "README.md").read_text(encoding="utf-8").startswith("# mathmodel-skill v7.4.5"))
        self.assertIn("## Current release: 7.4.5", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
