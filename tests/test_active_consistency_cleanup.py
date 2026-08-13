from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class ActiveConsistencyCleanupTests(unittest.TestCase):
    def test_project_instructions_use_five_file_two_python_contract(self) -> None:
        text = read("PROJECT_INSTRUCTIONS.md")
        self.assertIn("问题X结果深化分析.py", text)
        self.assertTrue("最终默认恰好保留五个文件" in text or "最终默认恰好包含" in text)
        self.assertNotIn("不得另建结果深化分析 Python 脚本", text)
        self.assertNotIn("覆盖更新同一个 `问题X求解.py`", text)

    def test_review_and_submission_packs_use_current_contract(self) -> None:
        review = read("packs/artifact/review.md")
        submission = read("packs/artifact/full_submission.md")
        self.assertIn("五文件合同", review)
        self.assertNotIn("四文件合同", review)
        self.assertIn("问题X结果深化分析.py", submission)
        self.assertNotIn("不得创建独立结果深化脚本", submission)
        self.assertIn("internal_metadata/", submission)
        self.assertIn("不得把这些文件塞入 `问题X求解/`", submission)

    def test_active_figure_templates_do_not_generate_legacy_result_paths(self) -> None:
        for relative in (
            "templates/figure/figure_plan.md",
            "templates/figure/figure_paper_closure.md",
        ):
            text = read(relative)
            self.assertIn("问题一求解/", text, relative)
            self.assertNotIn("结果数据表/问题一/", text, relative)
            self.assertNotIn("结果数据表/问题二/", text, relative)

    def test_runtime_router_exposes_conditional_preprocessing_and_user_gates(self) -> None:
        text = read("RUNTIME_ROUTER.md")
        self.assertIn("project_level → data_preprocessing", text)
        self.assertIn("用户本地运行预处理 Python", text)
        self.assertIn("用户本地运行主求解 Python", text)
        self.assertIn("用户本地运行深化分析 Python", text)
        self.assertIn("不会跨越用户执行边界", text)

    def test_project_state_example_locks_preprocessing_decision(self) -> None:
        state = yaml.safe_load(read("state/project_state.example.yaml"))
        preprocessing = state.get("preprocessing", {})
        self.assertEqual(preprocessing.get("decision"), "not_needed")
        self.assertEqual(preprocessing.get("level"), "none")
        self.assertEqual(preprocessing.get("downstream_data_source"), "raw")
        self.assertEqual(state.get("data", {}).get("active_source_mode"), "raw")

    def test_generated_index_version_comes_from_bootstrap(self) -> None:
        generator = read("scripts/generate_indexes.py")
        bootstrap = yaml.safe_load(read("core/bootstrap.yaml"))
        self.assertIn("current_skill_version", generator)
        self.assertIn('BOOTSTRAP = ROOT / "core" / "bootstrap.yaml"', generator)
        self.assertNotIn('VERSION = "7.2.1"', generator)
        expected = str(bootstrap["skill_version"])
        for relative in ("SKILL_FILE_INDEX.md", "TEMPLATE_INDEX.md"):
            self.assertIn(f"当前 Skill 版本：{expected}", read(relative), relative)


if __name__ == "__main__":
    unittest.main()
