from pathlib import Path
import json
import unittest

import yaml

ROOT = Path(__file__).resolve().parent.parent


class WritingExpressionProtocolV730Tests(unittest.TestCase):
    def test_latex_module_owns_shared_expression_protocol(self):
        latex = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        self.assertIn("正文表达与章节组织协议（写作权威）", latex)
        self.assertIn("问题重述：压缩任务，不复制题面", latex)
        self.assertIn("问题分析：写“为什么这样建模”，不是方法目录", latex)
        self.assertIn("模型推导：从本题对象出发，避免教科书腔", latex)
        self.assertIn("结果段：形成“数值—机制—结论”闭环", latex)
        self.assertIn("模型评价：评价当前模型，不写万能优缺点", latex)
        self.assertIn("不同题型的推荐章节组织", latex)

    def test_docx_and_cleanup_reference_shared_authority(self):
        docx = (ROOT / "modules/05_writing/docx.md").read_text(encoding="utf-8")
        cleanup = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        marker = "正文表达与章节组织协议（写作权威）"
        self.assertIn(marker, docx)
        self.assertIn(marker, cleanup)
        self.assertIn("问题重述去复制化", cleanup)
        self.assertIn("问题分析去流程图化", cleanup)
        self.assertIn("假设去万能化", cleanup)
        self.assertIn("推导去教科书化", cleanup)
        self.assertIn("结果去报表化", cleanup)
        self.assertIn("评价去万能化", cleanup)
        self.assertIn("章节去同构化", cleanup)

    def test_latex_pack_enforces_non_template_writing(self):
        pack = (ROOT / "packs/artifact/latex.md").read_text(encoding="utf-8")
        self.assertIn("问题重述压缩为研究对象、关键条件和逐问输入/输出", pack)
        self.assertIn("问题分析必须说明本问难点、对象关系、跨问依赖和建模抓手", pack)
        self.assertIn("关键数值/现象—比较基准—机制—题目结论—必要边界", pack)
        self.assertIn("不强制“优点三条、缺点两条、推广一段”", pack)

    def test_framework_records_project_specific_writing_strategy(self):
        framework = (ROOT / "templates/model/model_paper_framework.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("### 写作组织策略", framework)
        self.assertIn("主写作类型", framework)
        self.assertIn("问题分析安排", framework)
        self.assertIn("全局共享内容", framework)
        self.assertIn("结果解释链", framework)
        self.assertIn("模型评价安排", framework)
        self.assertIn("写作组织策略已按当前题型和证据链确定", framework)

    def test_output_contract_points_to_shared_authority(self):
        output = yaml.safe_load(
            (ROOT / "core/output_contract.yaml").read_text(encoding="utf-8")
        )
        policy = output["writing_policy"]
        self.assertIn("modules/05_writing/latex.md", policy["expression_authority"])
        self.assertTrue(policy["adaptive_sectioning_by_task_type"])
        self.assertTrue(policy["problem_restatement_copy_forbidden"])
        self.assertTrue(policy["problem_analysis_pipeline_listing_forbidden"])
        self.assertTrue(policy["generic_textbook_derivation_forbidden"])
        self.assertTrue(policy["generic_model_evaluation_forbidden"])

    def test_release_versions_are_consistent(self):
        bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))
        manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8"))
        output = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        plugin = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(bootstrap["skill_version"], "7.4.0")
        self.assertEqual(manifest["version"], "7.4.0")
        self.assertEqual(output["version"], "7.4.0")
        self.assertEqual(plugin["version"], "7.4.0")
        self.assertIn("version: 7.4.0", (ROOT / "SKILL.md").read_text(encoding="utf-8"))
        self.assertIn(
            "version: 7.4.0",
            (ROOT / "skills/mathmodel-skill/SKILL.md").read_text(encoding="utf-8"),
        )
        self.assertTrue((ROOT / "README.md").read_text(encoding="utf-8").startswith("# mathmodel-skill v7.4.0"))
        self.assertIn("## Current release: 7.4.0", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
