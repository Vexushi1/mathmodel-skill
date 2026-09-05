from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "fix/v8.7.4-active-authority-hygiene"
OLD = "8.7.3"
NEW = "8.7.4"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_exact(path: str, old: str, new: str, *, count: int = 1) -> None:
    text = read(path)
    actual = text.count(old)
    if actual != count:
        raise RuntimeError(f"{path}: expected {count} occurrences of {old!r}, found {actual}")
    write(path, text.replace(old, new, count))


def replace_all_current(path: str) -> None:
    text = read(path)
    if OLD not in text:
        raise RuntimeError(f"{path}: missing current version {OLD}")
    write(path, text.replace(OLD, NEW))


def main() -> None:
    if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("GITHUB_REF_NAME") != EXPECTED_BRANCH:
        raise RuntimeError("one-time migration may run only in the intended GitHub Actions branch")

    # Release carriers: update only the explicit current-version surfaces.
    replace_exact(".codex-plugin/plugin.json", '"version": "8.7.3"', '"version": "8.7.4"')
    for path in ("SKILL.md", "skills/mathmodel-skill/SKILL.md"):
        replace_all_current(path)
    replace_exact("core/bootstrap.yaml", "skill_version: 8.7.3", "skill_version: 8.7.4")
    replace_exact("core/hsk_core_policy.md", "# HSK Core Policy v8.7.3", "# HSK Core Policy v8.7.4")
    for path in (
        "core/workflow_router.yaml",
        "core/module_manifest.yaml",
        "core/output_contract.yaml",
        "core/writing_runtime_contract.yaml",
        "config/prose_audit_patterns.yaml",
    ):
        replace_exact(path, "version: 8.7.3", "version: 8.7.4")

    # Current-release tests that intentionally follow the active release.
    replace_all_current("tests/test_current_skill_health.py")
    replace_exact(
        "tests/test_v840_author_reasoning_writing.py",
        'self.assertEqual(runtime["version"], "8.7.3")',
        'self.assertEqual(runtime["version"], "8.7.4")',
    )

    # Paper Writing Protocol is an active Authority: its title must be release-neutral.
    replace_exact(
        "modules/05_writing/paper_writing_protocol.md",
        "# Module 05A：Paper Writing Protocol（v8.7.2）",
        "# Module 05A：Paper Writing Protocol",
    )
    replace_exact(
        "tests/test_v830_editable_mechanism_diagram.py",
        '"# Module 05A：Paper Writing Protocol（v8.7.2）",\n                "# Module 05A：Paper Writing Protocol（v8.7.0）",',
        '"# Module 05A：Paper Writing Protocol",\n                "# Module 05A：Paper Writing Protocol（v8.7.0）",',
    )

    # Keep the optional DOCX branch distinct from the ordinary-writing Authority label.
    replace_exact(
        "modules/05_writing/docx.md",
        "# Module 05A：可选 DOCX 审阅分支",
        "# Module 05E：可选 DOCX 审阅分支",
    )

    # Repair v8 Template-First Authority routing residues in Artifact Packs.
    replace_exact(
        "packs/artifact/docx.md",
        "本 Pack 只负责 **Word/DOCX 载体、可编辑性交付与迁移**。正文结构与表达服从 `modules/05_writing/latex.md`，跨竞赛推理、规则等级、命题预算和 Citation Evidence 服从 `core/writing_reasoning_contract.yaml`，Word 专属排版服从 `modules/05_writing/docx.md`。",
        "本 Pack 只负责 **Word/DOCX 载体、可编辑性交付与迁移**。普通正文结构与表达服从 `modules/05_writing/paper_writing_protocol.md`，跨竞赛推理、规则等级、命题预算和 Citation Evidence 服从 `core/writing_reasoning_contract.yaml`，Word 专属排版服从 `modules/05_writing/docx.md`；`modules/05_writing/latex.md` 仅在迁移到正式 LaTeX 时作为载体 Adapter。",
    )
    replace_exact(
        "packs/artifact/docx.md",
        "用户要求 Word/DOCX 草稿、基于现有底稿修改、批注版论文或 LaTeX 前置审稿稿时加载。",
        "用户要求 Word/DOCX 草稿、基于现有底稿修改、批注版论文，或明确要求在 LaTeX 之前进行 Word 审稿时加载。",
    )
    replace_exact(
        "packs/artifact/latex.md",
        "本 Pack 只负责 **LaTeX 工程、编译和交付**。正文结构与表达服从 `modules/05_writing/latex.md`，跨竞赛推理、规则等级、命题预算和 Citation Evidence 服从 `core/writing_reasoning_contract.yaml`。本文件不得复制第二套正文规范。",
        "本 Pack 只负责 **LaTeX 工程、编译和交付**。普通正文结构与表达服从 `modules/05_writing/paper_writing_protocol.md`，跨竞赛推理、规则等级、命题预算和 Citation Evidence 服从 `core/writing_reasoning_contract.yaml`；`modules/05_writing/latex.md` 只负责 LaTeX 载体、环境、引用、审计与编译接口。本文件不得复制第二套正文规范。",
    )

    # README: current release, current Authority map, and release note.
    replace_exact("README.md", "# mathmodel-skill v8.7.3", "# mathmodel-skill v8.7.4")
    replace_exact(
        "README.md",
        "- `modules/05_writing/latex.md`：正文结构与表达；",
        "- `modules/05_writing/paper_writing_protocol.md`：普通正文结构与表达；\n- `modules/05_writing/latex.md`：LaTeX Adapter 与载体接口；",
    )
    readme = read("README.md")
    marker = "## v8.7.3：Mechanism Diagram Monochrome & Geometry Rollback\n"
    if readme.count(marker) != 1:
        raise RuntimeError("README: v8.7.3 release marker missing or duplicated")
    v874 = (
        "## v8.7.4：Active Authority / Read-Path Hygiene\n\n"
        "本补丁修复仓库级健康审计发现的活动读取与 Authority 漂移，不改变模型、求解、Schema、CLI、目录或写作规则内容。Paper Writing Protocol 的活动标题改为 release-neutral，避免后续 patch 再产生标题版本漂移；README、DOCX/LaTeX Artifact Packs 统一把普通正文结构与表达指向 `modules/05_writing/paper_writing_protocol.md`，并继续把 `modules/05_writing/latex.md` 限定为 LaTeX Adapter。\n\n"
        "MATLAB 绘图说明同步明确：高对比蓝/红/绿/橙/紫调色板只服务数据驱动结果 Figure，正式机理/推导图继续服从 Module 04 的 monochrome-first 规则；`draw_mechanism_structure.m` 只使用黑白灰结构编码。兼容 V622、legacy、旧工作簿/旧目录的只读路径保持不变。\n\n"
    )
    write("README.md", readme.replace(marker, v874 + marker, 1))

    # Changelog: preserve v8.7.3 as historical release and add the new patch.
    changelog = read("CHANGELOG.md")
    prefix = "# Changelog\n\n## Current release: 8.7.3\n\n"
    if not changelog.startswith(prefix):
        raise RuntimeError("CHANGELOG current-release prefix is not v8.7.3")
    new_prefix = (
        "# Changelog\n\n## Current release: 8.7.4\n\n"
        "- Repaired active writing Authority/read-path drift: ordinary body structure and expression now consistently point to `modules/05_writing/paper_writing_protocol.md`, while `modules/05_writing/latex.md` remains a carrier-only LaTeX Adapter.\n"
        "- Removed stale release branding from the active Paper Writing Protocol title and separated the optional DOCX branch display label from the ordinary-writing Module 05A label.\n"
        "- Clarified MATLAB figure guidance so the high-contrast scientific palette applies to data-driven result figures only; formal mechanism/derivation figures continue to use the Module 04 monochrome-first visual grammar.\n"
        "- Added focused active-authority hygiene regression coverage while preserving model mathematics, Model Approval, 03A/03B, Workbook/Project State schemas, CLI, project layout, legacy/V622 read compatibility, and the v8.7.3 mechanism rendering behavior.\n\n"
        "## Previous release: 8.7.3\n\n"
    )
    write("CHANGELOG.md", new_prefix + changelog[len(prefix):])

    # MATLAB mechanism diagrams must not inherit the result-figure color palette.
    replace_exact(
        "templates/matlab/README.md",
        "- 主结果恢复高对比、中高饱和科研主色：亮蓝 `#1478FF`、鲜红 `#F04444`、亮绿 `#16B364`、亮橙 `#F79009`、亮紫 `#7A5AF8`；强比较优先亮蓝 vs 鲜红；",
        "- 数据驱动主结果图恢复高对比、中高饱和科研主色：亮蓝 `#1478FF`、鲜红 `#F04444`、亮绿 `#16B364`、亮橙 `#F79009`、亮紫 `#7A5AF8`；强比较优先亮蓝 vs 鲜红；正式机理/推导图不继承该调色板，统一服从 Module 04 的 monochrome-first 黑白灰线稿规则；",
    )
    replace_exact(
        "templates/matlab/draw_mechanism_structure.m",
        "% 题目专属结构图骨架。调用者必须提供真实对象、关系和坐标；无通用默认节点。",
        "% 题目专属结构图骨架。正式机理图采用 monochrome-first；调用者必须提供真实对象、关系和坐标。\n% hsk_apply_scientific_style 这里只统一字体/画布，不表示继承数据结果图的彩色 palette。",
    )

    # Focused regression: active Authority pointers, version-neutral title, and MATLAB palette boundary.
    test_path = ROOT / "tests/test_v874_active_authority_hygiene.py"
    if test_path.exists():
        raise RuntimeError("v8.7.4 hygiene regression already exists")
    test_path.write_text(
        '''from __future__ import annotations\n\nimport re\nimport unittest\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\n\n\ndef read(relative: str) -> str:\n    return (ROOT / relative).read_text(encoding="utf-8")\n\n\nclass ActiveAuthorityHygieneTests(unittest.TestCase):\n    def test_paper_writing_protocol_title_is_release_neutral(self):\n        first_line = read("modules/05_writing/paper_writing_protocol.md").splitlines()[0]\n        self.assertEqual(first_line, "# Module 05A：Paper Writing Protocol")\n        self.assertIsNone(re.search(r"v\\d+\\.\\d+\\.\\d+", first_line, re.I))\n\n    def test_docx_module_has_distinct_optional_branch_label(self):\n        first_line = read("modules/05_writing/docx.md").splitlines()[0]\n        self.assertEqual(first_line, "# Module 05E：可选 DOCX 审阅分支")\n\n    def test_artifact_packs_route_body_authority_to_protocol(self):\n        for relative in ("packs/artifact/docx.md", "packs/artifact/latex.md"):\n            text = read(relative)\n            with self.subTest(relative=relative):\n                self.assertIn("modules/05_writing/paper_writing_protocol.md", text)\n                self.assertNotIn("正文结构与表达服从 `modules/05_writing/latex.md`", text)\n        self.assertIn("LaTeX Adapter", read("packs/artifact/docx.md"))\n        self.assertIn("只负责 LaTeX 载体", read("packs/artifact/latex.md"))\n\n    def test_readme_authority_map_matches_template_first_architecture(self):\n        text = read("README.md")\n        self.assertIn("`modules/05_writing/paper_writing_protocol.md`：普通正文结构与表达", text)\n        self.assertIn("`modules/05_writing/latex.md`：LaTeX Adapter 与载体接口", text)\n        self.assertNotIn("`modules/05_writing/latex.md`：正文结构与表达", text)\n\n    def test_matlab_mechanism_guidance_preserves_monochrome_boundary(self):\n        readme = read("templates/matlab/README.md")\n        mechanism = read("templates/matlab/draw_mechanism_structure.m")\n        self.assertIn("数据驱动主结果图", readme)\n        self.assertIn("正式机理/推导图不继承该调色板", readme)\n        self.assertIn("monochrome-first", mechanism)\n        for forbidden in ("#1478FF", "#F04444", "#16B364", "#F79009", "#7A5AF8"):\n            self.assertNotIn(forbidden, mechanism)\n\n\nif __name__ == "__main__":\n    unittest.main()\n''',
        encoding="utf-8",
    )

    # Restore the temporary workflow and remove this migration helper before committing.
    workflow = subprocess.check_output(
        ["git", "show", "HEAD^:.github/workflows/refresh-generated.yml"],
        cwd=ROOT,
        text=True,
    )
    write(".github/workflows/refresh-generated.yml", workflow)
    Path(__file__).unlink()

    # Generated metadata must be produced by the repository's own generator.
    subprocess.run([sys.executable, "scripts/generate_indexes.py"], cwd=ROOT, check=True)

    # Commit the complete deterministic patch from the workflow's existing write-authorized job.
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=ROOT, check=True)
    subprocess.run(
        ["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
    if not status.strip():
        raise RuntimeError("migration produced no changes")
    subprocess.run(
        ["git", "commit", "-m", "fix: repair active authority and read-path drift"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(["git", "push", "origin", f"HEAD:{EXPECTED_BRANCH}"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
