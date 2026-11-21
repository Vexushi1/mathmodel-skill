from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class TestV802EntrypointSurfaceSlimming(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.packaged_skill = (ROOT / "skills/mathmodel-skill/SKILL.md").read_text(encoding="utf-8")
        cls.instructions = (ROOT / "PROJECT_INSTRUCTIONS.md").read_text(encoding="utf-8")

    def test_root_and_packaged_entrypoints_remain_exactly_equal(self):
        self.assertEqual(self.root_skill, self.packaged_skill)

    def test_entrypoint_keeps_mandatory_delegation_and_hard_boundaries(self):
        for token in (
            "core/bootstrap.yaml",
            "core/workflow_router.yaml",
            "core/hsk_core_policy.md",
            "scripts/resolve_runtime.py",
            "scripts/resolve_workflow.py",
            "core/model_approval_contract.yaml",
            "core/numerical_verification_contract.yaml",
            "core/writing_reasoning_contract.yaml",
            "模型论文框架.md",
            "state/project_state.yaml",
            "legacy/",
            "pre_delivery_gates",
            "full_fidelity",
        ):
            self.assertIn(token, self.root_skill)

    def test_entrypoint_no_longer_copies_versioned_business_rulebooks(self):
        for token in (
            "### 数据与求解",
            "### Figure Evidence",
            "v7.16 进一步要求",
            "v7.18 进一步强化",
            "v7.19 在保持",
            "v8.0.0 将模板",
            "v8.0.1 完成",
            "问题X求解/\n├─",
            "箱线+原始散点",
            "约 3--4 个",
        ):
            self.assertNotIn(token, self.root_skill)

    def test_public_navigation_leads_to_one_copy_of_the_web_app_instructions(self):
        anchor = '<a id="web-app-start"></a>'
        self.assertEqual(self.instructions.count(anchor), 1)
        section = self.instructions.split(anchor, 1)[1].strip().split("\n## ", 1)[0]
        blocks = re.findall(r"^```text\n(.+?)\n```$", section, re.MULTILINE | re.DOTALL)
        self.assertEqual(len(blocks), 1)
        for relative in ("README.md", "RUNTIME_ROUTER.md", "REPOSITORY_INDEX.md",
                         "scripts/README.md", "docs/stage_reading_execution_refactor_plan.md"):
            with self.subTest(relative=relative):
                path = ROOT / relative
                text = path.read_text(encoding="utf-8")
                if relative.startswith("docs/"):
                    before_next = re.split(r"^### 13\.2 .+?$", text, flags=re.MULTILINE)[1]
                    text = re.split(r"^#{1,3} ", before_next, maxsplit=1, flags=re.MULTILINE)[0]
                targets = re.findall(r"\[[^\]]+\]\(([^)]+)#web-app-start\)", text)
                self.assertIn(ROOT / "PROJECT_INSTRUCTIONS.md",
                              [(path.parent / target).resolve() for target in targets])
                self.assertNotIn(blocks[0], text)

    def test_project_instructions_is_procedure_not_duplicate_contract(self):
        for required in (
            "scripts/resolve_runtime.py",
            "模型论文框架.md",
            "state/project_state.yaml",
            "full-fidelity",
            "core/numerical_verification_contract.yaml",
            "modules/03_result_analysis.md",
            "modules/04_figure_evidence.md",
            "pre_delivery_gates",
            "SKILL_CHANGE_GOVERNANCE.md",
        ):
            self.assertIn(required, self.instructions)
        for artifact in ("问题X求解.py", "问题X结果深化分析.py"):
            self.assertIn(artifact, self.instructions)
        for duplicated in (
            "├─",
            "required / inline / not_applicable",
            "命题 0--4",
            "主比较允许中高饱和",
        ):
            self.assertNotIn(duplicated, self.instructions)

    def test_current_release_carriers_match_bootstrap_version(self):
        bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))
        expected = str(bootstrap["skill_version"])
        plugin = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(str(plugin["version"]), expected)
        self.assertIn(f"version: {expected}", self.root_skill)
        self.assertTrue((ROOT / "README.md").read_text(encoding="utf-8").startswith(f"# mathmodel-skill v{expected}"))
        self.assertTrue((ROOT / "core/hsk_core_policy.md").read_text(encoding="utf-8").startswith(f"# HSK Core Policy v{expected}"))
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertTrue(changelog.startswith(f"# Changelog\n\n## {expected}"))
        for relative in (
            "core/workflow_router.yaml",
            "core/module_manifest.yaml",
            "core/output_contract.yaml",
            "core/writing_runtime_contract.yaml",
            "config/prose_audit_patterns.yaml",
        ):
            data = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))
            self.assertEqual(str(data["version"]), expected, relative)

    def test_historical_801_audit_remains_historical(self):
        audit = (ROOT / "docs/v801_chapter_capability_preservation_audit.md").read_text(encoding="utf-8")
        self.assertIn("v8.0.1", audit)
        review_test = (ROOT / "tests/test_v801_chapter_capability_preservation.py").read_text(encoding="utf-8")
        self.assertIn("v7.20/v8.0.1", review_test)


if __name__ == "__main__":
    unittest.main()
