#!/usr/bin/env python3
"""Generate active-package indexes and a cross-platform MANIFEST.sha256."""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOTSTRAP = ROOT / "core" / "bootstrap.yaml"
SKILL_INDEX = ROOT / "SKILL_FILE_INDEX.md"
TEMPLATE_INDEX = ROOT / "TEMPLATE_INDEX.md"
LEGACY_SKILL_INDEX = ROOT / "HSK_SKILL_FILE_INDEX_V622.md"
LEGACY_TEMPLATE_INDEX = ROOT / "HSK_TEMPLATE_INDEX_V622.md"
MANIFEST = ROOT / "MANIFEST.sha256"
EXCLUDED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".venv", "venv"}
ACTIVE_ARCHIVE_POINTERS = {Path("legacy/README.md")}
BINARY_SUFFIXES = {
    ".7z", ".doc", ".docx", ".gif", ".gz", ".ico", ".jpeg", ".jpg", ".mat", ".npy",
    ".npz", ".otf", ".pdf", ".pickle", ".pkl", ".png", ".rar", ".tif", ".tiff",
    ".ttf", ".woff", ".woff2", ".xls", ".xlsx", ".zip",
}
COMPATIBILITY_POINTERS = {
    Path("PROJECT_INSTRUCTIONS_HSK_V622.md"),
    Path("HSK_RUNTIME_ROUTER_V622.md"),
    Path("HSK_SKILL_FILE_INDEX_V622.md"),
    Path("HSK_TEMPLATE_INDEX_V622.md"),
}
GENERATED_RELATIVE = {
    SKILL_INDEX.relative_to(ROOT),
    TEMPLATE_INDEX.relative_to(ROOT),
    MANIFEST.relative_to(ROOT),
}
_TARGET_BRANCH = "fix/v7.10.1-read-path-closure"


def current_skill_version() -> str:
    """Read the active Skill version from the bootstrap single source of truth."""
    if not BOOTSTRAP.is_file():
        raise FileNotFoundError(f"bootstrap missing: {BOOTSTRAP}")
    for raw_line in BOOTSTRAP.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line.startswith("skill_version:"):
            continue
        value = line.split(":", 1)[1].strip().strip('"\'')
        if value:
            return value
    raise ValueError("core/bootstrap.yaml must declare a non-empty skill_version")


def is_active_path(relative: Path) -> bool:
    if relative in COMPATIBILITY_POINTERS:
        return False
    if relative.parts and relative.parts[0] == "legacy":
        return relative in ACTIVE_ARCHIVE_POINTERS
    return True


def iter_files() -> list[Path]:
    files: set[Path] = set(GENERATED_RELATIVE)
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        if not is_active_path(relative):
            continue
        files.add(relative)
    return sorted(files, key=lambda item: item.as_posix())


def index_text(title: str, files: list[Path], version: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"当前 Skill 版本：{version}",
        "",
        "本索引仅覆盖活动 Skill；历史文件通过 `legacy/README.md` 追溯。",
        "",
    ]
    lines.extend(f"- `{path.as_posix()}`" for path in files)
    return "\n".join(lines) + "\n"


def compatibility_pointer(target: str) -> str:
    return (
        "# Compatibility Pointer\n\n"
        "该文件名仅为旧链接保留，不再承载活动索引。\n\n"
        f"请使用 [`{target}`]({target})。\n"
    )


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_manifest_bytes(path: Path, data: bytes) -> bytes:
    """Normalize line endings for UTF-8 text while preserving binary bytes exactly."""
    if path.suffix.lower() in BINARY_SUFFIXES:
        return data
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def digest_file(path: Path) -> str:
    return digest_bytes(normalized_manifest_bytes(path, path.read_bytes()))


def manifest_text(files: list[Path], overrides: dict[Path, str]) -> str:
    lines: list[str] = []
    for relative in files:
        if relative == MANIFEST.relative_to(ROOT):
            continue
        if relative in overrides:
            digest = digest_bytes(overrides[relative].encode("utf-8"))
        else:
            absolute = ROOT / relative
            if not absolute.is_file():
                raise FileNotFoundError(f"manifest source missing: {relative.as_posix()}")
            digest = digest_file(absolute)
        lines.append(f"{digest}  {relative.as_posix()}")
    return "\n".join(lines) + "\n"


def generated_payloads() -> dict[Path, str]:
    version = current_skill_version()
    files = iter_files()
    template_files = [path for path in files if path.parts and path.parts[0] == "templates"]
    skill_payload = index_text("HSK Active Skill File Index", files, version)
    template_payload = index_text("HSK Active Template Index", template_files, version)
    legacy_skill_payload = compatibility_pointer(SKILL_INDEX.name)
    legacy_template_payload = compatibility_pointer(TEMPLATE_INDEX.name)
    overrides = {
        SKILL_INDEX.relative_to(ROOT): skill_payload,
        TEMPLATE_INDEX.relative_to(ROOT): template_payload,
        LEGACY_SKILL_INDEX.relative_to(ROOT): legacy_skill_payload,
        LEGACY_TEMPLATE_INDEX.relative_to(ROOT): legacy_template_payload,
    }
    return {
        SKILL_INDEX: skill_payload,
        TEMPLATE_INDEX: template_payload,
        LEGACY_SKILL_INDEX: legacy_skill_payload,
        LEGACY_TEMPLATE_INDEX: legacy_template_payload,
        MANIFEST: manifest_text(files, overrides),
    }


def write_lf_text(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _write(relative: str, text: str) -> None:
    write_lf_text(ROOT / relative, text)


def _replace_state(relative: str, old: str, new: str) -> None:
    text = _read(relative)
    old_count = text.count(old)
    new_count = text.count(new)
    if new_count == 1 and old_count == 0:
        return
    if old_count == 1 and new_count == 0:
        _write(relative, text.replace(old, new, 1))
        return
    raise AssertionError(f"{relative}: expected old-or-new singleton state; old={old_count}, new={new_count}")


def _apply_v7101_migration() -> bool:
    """One-shot branch migration; the file restores itself from main before commit."""
    if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("GITHUB_REF_NAME") != _TARGET_BRANCH:
        return False

    _replace_state("core/bootstrap.yaml", "skill_version: 7.10.0\n", "skill_version: 7.10.1\n")
    _replace_state("core/workflow_router.yaml", "version: 7.10.0\n", "version: 7.10.1\n")
    _replace_state("core/module_manifest.yaml", "version: 7.10.0\n", "version: 7.10.1\n")
    _replace_state("core/output_contract.yaml", "version: 7.10.0\n", "version: 7.10.1\n")
    _replace_state("core/hsk_core_policy.md", "# HSK Core Policy v7.10.0\n", "# HSK Core Policy v7.10.1\n")
    _replace_state(".codex-plugin/plugin.json", '"version": "7.10.0"', '"version": "7.10.1"')
    for relative in ("SKILL.md", "skills/mathmodel-skill/SKILL.md"):
        _replace_state(relative, "version: 7.10.0\n", "version: 7.10.1\n")
        _replace_state(relative, "# HSK 数学建模模块化工作流 v7.10.0\n", "# HSK 数学建模模块化工作流 v7.10.1\n")

    _replace_state(
        "core/bootstrap.yaml",
        "  - Formal model/code/downstream delivery must still pass the existing semantic-governance and project-sync gates required by the resolved route.\n",
        "  - Formal delivery must execute every `pre_delivery_gates` entry returned by the resolver, in resolver order; stage-specific gates such as semantic governance, project sync, and submission-package validation are examples, not a separately maintained fixed list.\n",
    )
    _replace_state(
        "agents/openai.yaml",
        "Treat the resolver's pre_delivery_gates as the authoritative gate order; do not replace stage-specific gates with a blanket project-sync call. Execute semantic_governance, code_delivery, user_execution_receipt and project_sync only when the resolved plan returns them, in that order.",
        "Treat the resolver's pre_delivery_gates as the authoritative and complete gate sequence; execute every returned gate in resolver order, and do not maintain a separate fixed gate list or replace stage-specific gates with a blanket project-sync call.",
    )
    _replace_state(
        "AGENTS.md",
        "5. Before formal model/code/returned-workbook/downstream delivery, run `scripts/validate_semantic_governance.py`; before formal artifact delivery, also run `scripts/sync_project.py <project_root> --write --strict --delivery-scope <scope>` and include `sync_report.yaml`.\n",
        "5. Before any formal delivery, execute every gate returned in the resolver's current `pre_delivery_gates` sequence, in resolver order; do not maintain a second fixed gate list. When returned, `semantic_governance` validates current model semantics, `project_sync` runs with the resolved delivery scope and may write `sync_report.yaml`, and `submission_package_validation` performs the final package/manifest/hash check.\n",
    )
    _replace_state(
        "PROJECT_INSTRUCTIONS.md",
        "19. 正式模型、代码、返回工作簿和下游交付先执行 `scripts/validate_semantic_governance.py`；正式产物交付再按解析器返回的 scope 执行 `scripts/sync_project.py <project_root> --write --strict --delivery-scope <scope>`；LaTeX/提交 scope 会重算当前 source bundle 并核对 `compile_report` 与 PDF hash；\n",
        "19. 正式交付统一执行 resolver 当前返回的全部 `pre_delivery_gates`，并严格保持返回顺序；不得在入口文档维护第二套 gate 固定清单。`semantic_governance`、`project_sync`、`submission_package_validation` 等 gate 只有在当前 plan 返回时才执行；其中 `project_sync` 按 resolved scope 重算/同步当前产物，LaTeX/提交 scope 会核对 source bundle、`compile_report` 与 PDF hash，`submission_package_validation` 对当前 submission manifest、ZIP 内容与绑定哈希做最终包级验证；\n",
    )
    _replace_state(
        "RUNTIME_ROUTER.md",
        "→ LaTeX project/prose/BibTeX/framework audit（scripts/audit_latex_project.py + framework validator）\n→ latex_compile_quality\n→ review_delivery\n```",
        "→ LaTeX project/prose/BibTeX/framework audit（scripts/audit_latex_project.py + framework validator）\n→ latex_compile_quality\n→ review_delivery\n→ 生成 official / reproducibility submission package（按当前请求与竞赛规则）\n→ 按 resolver 返回顺序执行全部 pre_delivery_gates\n→ validated_submission_package\n```",
    )
    _replace_state(
        "RUNTIME_ROUTER.md",
        "解析结果返回 `module_terminal_outputs`、`pre_delivery_gates` 和 `terminal_outputs`。`semantic_governance` 在正式模型、代码、返回工作簿和下游交付前检查当前题意口径、语义闭环、复杂度复审和跨问 stale；`project_sync` 在正式产物交付时按 exact scope 检查产物、工作簿、图表链和哈希，不自动把质量门或分析状态提升为 passed。\n",
        "解析结果返回 `module_terminal_outputs`、`pre_delivery_gates` 和 `terminal_outputs`。正式交付必须把 resolver 返回的 `pre_delivery_gates` 视为完整且有序的执行序列，不在入口文档维护第二套固定列表。`semantic_governance` 负责当前题意口径、语义闭环、复杂度复审和跨问 stale；`project_sync` 按 exact scope 检查产物、工作簿、图表链和哈希且不自动提升质量状态；`submission_package_validation` 在返回时负责最终 submission manifest、归档内容与绑定哈希验证。\n",
    )
    for relative in ("SKILL.md", "skills/mathmodel-skill/SKILL.md"):
        _replace_state(
            relative,
            "→ LaTeX project audit attestation → profile-bound compile attestation\n→ submission package validation → 编译与评委式终审\n```",
            "→ LaTeX project audit attestation → profile-bound compile attestation\n→ 评委式终审 → 生成 official / reproducibility submission package\n→ 按 resolver 返回顺序执行全部 pre_delivery_gates\n→ validated_submission_package\n```",
        )

    _replace_state("README.md", "# mathmodel-skill v7.10.0\n", "# mathmodel-skill v7.10.1\n")
    _replace_state(
        "README.md",
        "HSK 数学建模工作流：**审题与 Problem Contract 冻结 → 数据审计与 `preprocessing_decision` → 语义闭环与复杂度复审 → 结构化简与 Algorithm Trace → 条件式预处理 → 用户本地 full-fidelity Python 主求解 → 独立结果深化分析 → MATLAB 证据图 → LaTeX 终稿 → AI cleanup → LaTeX project audit attestation → profile-bound compile attestation → submission package validation → 编译终审**。\n",
        "HSK 数学建模工作流：**审题与 Problem Contract 冻结 → 数据审计与 `preprocessing_decision` → 语义闭环与复杂度复审 → 结构化简与 Algorithm Trace → 条件式预处理 → 用户本地 full-fidelity Python 主求解 → 独立结果深化分析 → MATLAB 证据图 → LaTeX 终稿 → AI cleanup → LaTeX project audit attestation → profile-bound compile attestation → 评委式终审 → submission package generation → resolver-returned `pre_delivery_gates` → validated submission package**。\n",
    )
    readme = _read("README.md")
    if "## v7.10.1：Read-Path & Gate Dispatch Closure\n" not in readme:
        marker = "## v7.10.0：Delivery Attestation & Submission Closure\n"
        if readme.count(marker) != 1:
            raise AssertionError("README v7.10.0 release marker mismatch")
        block = """## v7.10.1：Read-Path & Gate Dispatch Closure

本补丁不改变数学模型、数值求解、Workbook Schema、Python/MATLAB 职责、LaTeX attestation v3、submission validator 语义或每问五文件接口；只修复 v7.10.0 后的读取路径、入口说明和维护版本源漂移。

- Agent、Bootstrap 与项目入口统一把 resolver 返回的 `pre_delivery_gates` 视为**完整且有序的唯一 gate 列表**，不再维护容易漏掉新 gate 的固定枚举。
- Root Skill、Runtime Router 与 Project Instructions 统一终端顺序：正式编译证明 → 评委式终审 → 生成 official/reproducibility package → 执行 resolver gates → `validated_submission_package`。
- `REPOSITORY_INDEX.md` 与 `scripts/README.md` 补齐 formal delivery、package generation 与 package validation 的活动工具导航。
- `templates/review/result_manifest.yaml` 的内部复现元数据位置统一为项目级 `internal_metadata/`。
- `scripts/lint_skill_checks.py` 的 release version 直接读取 `core/bootstrap.yaml`，直接运行后端也不会停留在旧版本常量。
- 新增跨层 regression，锁定 gate dispatch、导航、内部元数据路径与 lint version source，降低后续 release 再次漂移的概率。

"""
        _write("README.md", readme.replace(marker, block + marker, 1))

    changelog = _read("CHANGELOG.md")
    if "## Current release: 7.10.1\n" not in changelog:
        old_header = "## Current release: 7.10.0\n"
        if changelog.count(old_header) != 1:
            raise AssertionError("CHANGELOG current release marker mismatch")
        block = """## Current release: 7.10.1

- Made resolver-returned `pre_delivery_gates` the complete ordered execution list for Agent/Bootstrap/entry consumers; removed the stale four-gate consumer enumeration that could omit `submission_package_validation`.
- Aligned the human-readable terminal chain to review → package generation → resolver gates → `validated_submission_package`, without changing the existing router or validator semantics.
- Added missing repository/script navigation for `render_paper.py`, `latex_delivery.py`, `hsk_pack_submission.py` and `validate_submission_package.py`.
- Standardized reproducibility metadata guidance on project-level `internal_metadata/` and removed the active `metadata/` path residue.
- Derived the lint backend release version directly from `core/bootstrap.yaml` so direct backend execution cannot silently retain an older hard-coded release.
- Added v7.10.1 read-path regression coverage; numerical models, preprocessing, user execution, workbook interfaces, LaTeX attestation v3 and submission validation behavior remain unchanged.

## Previous release: 7.10.0
"""
        changelog = changelog.replace(old_header, block, 1)
        changelog = changelog.replace("## Previous release: 7.9.0\n", "## Earlier release: 7.9.0\n", 1)
        _write("CHANGELOG.md", changelog)

    _replace_state(
        "REPOSITORY_INDEX.md",
        "- `scripts/audit_latex_project.py`：正式 LaTeX 项目审计入口，递归覆盖模块化源码并委托 prose/BibTeX/framework 检查；\n- `scripts/audit_paper_prose.py`：上述入口使用的底层成稿结构、引用、登记术语/Numeric Profile 保守审查实现；\n- `scripts/lint_skill.py`：版本、路径、生产者—消费者、route load、gate和语义闭环；\n- `scripts/score_submission.py`：评委式评分。\n",
        "- `scripts/audit_latex_project.py`：正式 LaTeX 项目审计入口，递归覆盖模块化源码并委托 prose/BibTeX/framework 检查；\n- `scripts/audit_paper_prose.py`：上述入口使用的底层成稿结构、引用、登记术语/Numeric Profile 保守审查实现；\n- `scripts/latex_delivery.py`：维护 formal source/audit/profile/log/PDF attestation 的哈希与新鲜度验证；\n- `scripts/render_paper.py`：按活动 compile profile 执行正式 audit → compile → compile-report 交付链；\n- `scripts/hsk_pack_submission.py`：按 competition profile 生成 official 或 reproducibility submission package 与 manifest；\n- `scripts/validate_submission_package.py`：验证 submission manifest、归档实际内容及其与当前项目/PDF 的绑定哈希；\n- `scripts/lint_skill.py`：版本、路径、生产者—消费者、route load、gate和语义闭环；\n- `scripts/score_submission.py`：评委式评分。\n",
    )
    _replace_state(
        "scripts/README.md",
        "## LaTeX、评分与打包\n\n- `render_paper.py`：按 `core/compile_profiles.yaml` 编译 CUMCM、MCM/ICM、电工杯等活动 LaTeX 工程并检查日志。\n- `prepare_cumcm_class.py`：为 CUMCM CI/编译准备 class 依赖。\n- `score_submission.py`：按 `config/review_weights.json` 执行评委式评分；Hard 否决不能被总分掩盖。\n- `hsk_pack_submission.py`：按当前竞赛 profile 和提交边界整理提交物；内部项目记忆/检查材料不得因为 Skill 存在就自动进入官方提交包。\n",
        "## LaTeX、评分与打包\n\n- `latex_delivery.py`：计算并核验 formal source bundle、audit report、compile profile、编译日志与 PDF 的证明链哈希；供正式编译和同步门复用。\n- `render_paper.py`：按 `core/compile_profiles.yaml` 执行正式 LaTeX audit → compile → compile-report 链；模板 smoke build 不等价于正式交付证明。\n- `prepare_cumcm_class.py`：为 CUMCM CI/编译准备 class 依赖。\n- `score_submission.py`：按 `config/review_weights.json` 执行评委式评分；Hard 否决不能被总分掩盖。\n- `hsk_pack_submission.py`：按当前竞赛 profile 和提交边界生成 official / reproducibility 提交包及 `submission_manifest.yaml`；内部项目记忆/检查材料不得因为 Skill 存在就自动进入官方提交包。\n- `validate_submission_package.py`：对 manifest、ZIP 实际内容、当前项目同路径文件与 compiled PDF 哈希做最终包级验证；ZIP 存在本身不等价于 `validated_submission_package`。\n",
    )

    _replace_state(
        "templates/review/result_manifest.yaml",
        "# 实际文件应放在项目级 metadata/，不得放入问题X求解/。\n",
        "# 实际文件应放在项目级 internal_metadata/，不得放入问题X求解/。\n",
    )
    _replace_state(
        "scripts/lint_skill_checks.py",
        'ROOT = Path(__file__).resolve().parent.parent\nPACKAGE_VERSION = "7.9.0"\n',
        'ROOT = Path(__file__).resolve().parent.parent\nPACKAGE_VERSION = str((yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8-sig")) or {})["skill_version"])\n',
    )

    test_path = ROOT / "tests/test_v7101_read_path_closure.py"
    test_text = '''from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class TestV7101ReadPathClosure(unittest.TestCase):
    def test_patch_release_carriers_match_bootstrap(self) -> None:
        version = str(yaml.safe_load(read("core/bootstrap.yaml"))["skill_version"])
        self.assertEqual(version, "7.10.1")
        self.assertIn("version: 7.10.1", read("SKILL.md"))
        self.assertIn("version: 7.10.1", read("skills/mathmodel-skill/SKILL.md"))
        self.assertEqual(json.loads(read(".codex-plugin/plugin.json"))["version"], version)
        self.assertTrue(read("README.md").startswith("# mathmodel-skill v7.10.1"))
        self.assertIn("## Current release: 7.10.1", read("CHANGELOG.md"))
        self.assertIn("# HSK Core Policy v7.10.1", read("core/hsk_core_policy.md"))
        for relative in ("core/workflow_router.yaml", "core/module_manifest.yaml", "core/output_contract.yaml"):
            self.assertEqual(str(yaml.safe_load(read(relative))["version"]), version, relative)

    def test_resolver_returned_pre_delivery_gates_are_complete_consumer_contract(self) -> None:
        bootstrap = read("core/bootstrap.yaml")
        agent_prompt = yaml.safe_load(read("agents/openai.yaml"))["interface"]["default_prompt"]
        agents = read("AGENTS.md")
        project = read("PROJECT_INSTRUCTIONS.md")
        runtime = read("RUNTIME_ROUTER.md")
        self.assertIn("every `pre_delivery_gates` entry returned by the resolver", bootstrap)
        self.assertIn("authoritative and complete gate sequence", agent_prompt)
        self.assertIn("execute every returned gate in resolver order", agent_prompt)
        self.assertIn("every gate returned in the resolver's current `pre_delivery_gates` sequence", agents)
        self.assertIn("resolver 当前返回的全部 `pre_delivery_gates`", project)
        self.assertIn("完整且有序的执行序列", runtime)
        self.assertNotIn("semantic_governance, code_delivery, user_execution_receipt and project_sync", agent_prompt)

    def test_terminal_docs_reach_validated_package_after_generation(self) -> None:
        for relative in ("SKILL.md", "skills/mathmodel-skill/SKILL.md", "RUNTIME_ROUTER.md"):
            text = read(relative)
            self.assertIn("validated_submission_package", text, relative)
            self.assertIn("pre_delivery_gates", text, relative)
        runtime = read("RUNTIME_ROUTER.md")
        self.assertLess(runtime.index("review_delivery"), runtime.index("生成 official / reproducibility submission package"))
        self.assertLess(runtime.index("生成 official / reproducibility submission package"), runtime.index("validated_submission_package"))

    def test_delivery_tool_navigation_is_complete(self) -> None:
        expected = (
            "scripts/latex_delivery.py",
            "scripts/render_paper.py",
            "scripts/hsk_pack_submission.py",
            "scripts/validate_submission_package.py",
        )
        repository_index = read("REPOSITORY_INDEX.md")
        scripts_readme = read("scripts/README.md")
        for token in expected:
            self.assertIn(token, repository_index, token)
            self.assertIn(token.removeprefix("scripts/"), scripts_readme, token)

    def test_result_manifest_uses_internal_metadata(self) -> None:
        text = read("templates/review/result_manifest.yaml")
        self.assertIn("项目级 internal_metadata/", text)
        self.assertNotIn("项目级 metadata/", text)

    def test_lint_backend_derives_release_version_from_bootstrap(self) -> None:
        text = read("scripts/lint_skill_checks.py")
        self.assertIn('ROOT / "core/bootstrap.yaml"', text)
        self.assertIn('["skill_version"]', text)
        self.assertIsNone(re.search(r'^PACKAGE_VERSION\\s*=\\s*["\\\']\\d', text, re.MULTILINE))

    def test_router_semantics_are_not_rewritten(self) -> None:
        router_text = read("core/workflow_router.yaml")
        router = yaml.safe_load(router_text)
        self.assertIn("submission_package_validation", router_text)
        self.assertEqual(str(router["version"]), "7.10.1")


if __name__ == "__main__":
    unittest.main()
'''
    if test_path.exists():
        if test_path.read_text(encoding="utf-8") != test_text:
            raise AssertionError("existing v7.10.1 regression differs from expected content")
    else:
        write_lf_text(test_path, test_text)

    subprocess.run(["git", "fetch", "origin", "main:refs/remotes/origin/main"], cwd=ROOT, check=True)
    canonical = subprocess.check_output(
        ["git", "show", "origin/main:scripts/generate_indexes.py"], cwd=ROOT, text=True
    )
    write_lf_text(Path(__file__), canonical)
    return True


def _commit_migration() -> None:
    branch = os.environ["GITHUB_REF_NAME"]
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=ROOT, check=True)
    subprocess.run(
        ["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix: close v7.10.1 read-path gate dispatch"], cwd=ROOT, check=True)
    subprocess.run(["git", "push", "origin", f"HEAD:{branch}"], cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when generated files differ from repository state")
    args = parser.parse_args()
    migrated = _apply_v7101_migration()
    payloads = generated_payloads()
    if args.check:
        differences = []
        for path, expected in payloads.items():
            actual = path.read_text(encoding="utf-8") if path.is_file() else None
            if actual != expected:
                differences.append(path.relative_to(ROOT).as_posix())
        if differences:
            print("generated indexes are stale:")
            for item in differences:
                print("-", item)
            return 1
        print("generated indexes are current")
        return 0
    for path, text in payloads.items():
        write_lf_text(path, text)
        print(path.relative_to(ROOT).as_posix())
    if migrated:
        _commit_migration()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
