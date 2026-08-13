from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class TestActiveConsistencyCleanup:
    def test_project_instructions_use_five_file_two_python_contract(self) -> None:
        text = read("PROJECT_INSTRUCTIONS.md")
        assert "问题X结果深化分析.py" in text
        assert "最终默认恰好保留五个文件" in text or "最终默认恰好包含" in text
        assert "不得另建结果深化分析 Python 脚本" not in text
        assert "覆盖更新同一个 `问题X求解.py`" not in text

    def test_review_and_submission_packs_use_current_contract(self) -> None:
        review = read("packs/artifact/review.md")
        submission = read("packs/artifact/full_submission.md")
        assert "五文件合同" in review
        assert "四文件合同" not in review
        assert "问题X结果深化分析.py" in submission
        assert "不得创建独立结果深化脚本" not in submission
        assert "internal_metadata/" in submission
        assert "不得把这些文件塞入 `问题X求解/`" in submission

    def test_active_figure_templates_do_not_generate_legacy_result_paths(self) -> None:
        for relative in (
            "templates/figure/figure_plan.md",
            "templates/figure/figure_paper_closure.md",
        ):
            text = read(relative)
            assert "问题一求解/" in text, relative
            assert "结果数据表/问题一/" not in text, relative
            assert "结果数据表/问题二/" not in text, relative

    def test_runtime_router_exposes_conditional_preprocessing_and_user_gates(self) -> None:
        text = read("RUNTIME_ROUTER.md")
        assert "project_level → data_preprocessing" in text
        assert "用户本地运行预处理 Python" in text
        assert "用户本地运行主求解 Python" in text
        assert "用户本地运行深化分析 Python" in text
        assert "不会跨越用户执行边界" in text

    def test_project_state_example_locks_preprocessing_decision(self) -> None:
        state = yaml.safe_load(read("state/project_state.example.yaml"))
        preprocessing = state.get("preprocessing", {})
        assert preprocessing.get("decision") == "not_needed"
        assert preprocessing.get("level") == "none"
        assert preprocessing.get("downstream_data_source") == "raw"
        assert state.get("data", {}).get("active_source_mode") == "raw"

    def test_generated_index_version_comes_from_bootstrap(self) -> None:
        generator = read("scripts/generate_indexes.py")
        bootstrap = yaml.safe_load(read("core/bootstrap.yaml"))
        assert "current_skill_version" in generator
        assert "BOOTSTRAP = ROOT / \"core\" / \"bootstrap.yaml\"" in generator
        assert "VERSION = \"7.2.1\"" not in generator
        expected = str(bootstrap["skill_version"])
        for relative in ("SKILL_FILE_INDEX.md", "TEMPLATE_INDEX.md"):
            assert f"当前 Skill 版本：{expected}" in read(relative), relative
