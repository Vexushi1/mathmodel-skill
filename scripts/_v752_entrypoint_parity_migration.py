from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = "7.5.1"
NEW = "7.5.2"


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def write(relative: str, text: str) -> None:
    (ROOT / relative).write_text(text, encoding="utf-8", newline="\n")


def replace_once(relative: str, old: str, new: str) -> None:
    text = read(relative)
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{relative}: expected exactly one occurrence of {old!r}, found {count}")
    write(relative, text.replace(old, new, 1))


def replace_regex_once(relative: str, pattern: str, replacement: str, flags: int = 0) -> None:
    text = read(relative)
    updated, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f"{relative}: regex replacement count={count}: {pattern}")
    write(relative, updated)


RUNTIME_CONTRACT = """<!-- HSK_RUNTIME_ENTRY_CONTRACT_START -->
## 运行时入口合同（非权威摘要）

无论从根目录 `SKILL.md` 还是插件目录 `skills/mathmodel-skill/SKILL.md` 进入，运行语义都只服从同一仓库根目录权威链：

1. 先读取 `core/bootstrap.yaml`；
2. 默认全局规则由 `core/workflow_router.yaml` 的 `default_load` 指向 `core/hsk_core_policy.md`；
3. 使用 `scripts/resolve_workflow.py` 按用户当前任务解析最小 `load_order`；
4. 只加载 resolver 命中的 route-specific contracts、modules、packs 与 templates；建模/写作推理仅在对应 route 加载 `core/writing_reasoning_contract.yaml`；
5. 已有 current `模型论文框架.md` 时按 `project_memory_contract` 恢复项目语义，具体数值仍以已验收工作簿为准；
6. `legacy/` 与 V622 compatibility pointers 不进入默认执行链。

本节只声明入口委托关系，不作为模型、预处理、求解、绘图或写作规则的独立权威；详细规则以 `core/bootstrap.yaml` 指向的当前权威源为准。
<!-- HSK_RUNTIME_ENTRY_CONTRACT_END -->"""


def bump_version_carriers() -> None:
    replacements = {
        ".codex-plugin/plugin.json": ('"version": "7.5.1"', '"version": "7.5.2"'),
        "core/bootstrap.yaml": ("skill_version: 7.5.1", "skill_version: 7.5.2"),
        "core/workflow_router.yaml": ("version: 7.5.1", "version: 7.5.2"),
        "core/module_manifest.yaml": ("version: 7.5.1", "version: 7.5.2"),
        "core/output_contract.yaml": ("version: 7.5.1", "version: 7.5.2"),
        "core/hsk_core_policy.md": ("# HSK Core Policy v7.5.1", "# HSK Core Policy v7.5.2"),
        "SKILL.md": ("version: 7.5.1", "version: 7.5.2"),
        "skills/mathmodel-skill/SKILL.md": ("version: 7.5.1", "version: 7.5.2"),
        "README.md": ("# mathmodel-skill v7.5.1", "# mathmodel-skill v7.5.2"),
        "scripts/lint_skill.py": ('PACKAGE_VERSION = "7.5.1"', 'PACKAGE_VERSION = "7.5.2"'),
    }
    for path, (old, new) in replacements.items():
        replace_once(path, old, new)

    replace_once("SKILL.md", "# HSK 数学建模模块化工作流 v7.5.1", "# HSK 数学建模模块化工作流 v7.5.2")
    replace_once(
        "skills/mathmodel-skill/SKILL.md",
        "# HSK 数学建模模块化工作流 v7.5.1",
        "# HSK 数学建模模块化工作流 v7.5.2",
    )

    # Stable utility/archive docs should not be release carriers; this removes two
    # redundant version touch-points from future patch releases.
    replace_once("scripts/README.md", "# Scripts v7.5.1", "# Scripts")
    replace_once(
        "legacy/README.md",
        "本目录仅用于旧项目追溯、兼容和迁移，不属于 v7.5.1 默认运行链路。",
        "本目录仅用于旧项目追溯、兼容和迁移，不属于当前默认运行链路。",
    )
    replace_once(
        "scripts/resolve_workflow.py",
        '"""Resolve one or more user intents into an ordered HSK v7.5.1 execution plan."""',
        '"""Resolve one or more user intents into an ordered HSK execution plan."""',
    )


def add_runtime_contracts() -> None:
    heading = "# HSK 数学建模模块化工作流 v7.5.2\n"
    for relative in ("SKILL.md", "skills/mathmodel-skill/SKILL.md"):
        text = read(relative)
        if "HSK_RUNTIME_ENTRY_CONTRACT_START" in text:
            raise RuntimeError(f"{relative}: runtime entry contract already exists")
        if text.count(heading) != 1:
            raise RuntimeError(f"{relative}: expected one current H1")
        text = text.replace(heading, heading + "\n" + RUNTIME_CONTRACT + "\n", 1)
        write(relative, text)

    old_sentence = (
        "LaTeX 是默认论文主链，`modules/05_writing/latex.md` 的“正文表达与章节组织协议（写作权威）”统一约束 DOCX、LaTeX 与 AI-cleanup。"
        "v7.5.1 延续 v7.4.4 的中文国赛正文结构，并增加成稿 prose audit："
    )
    new_sentence = (
        "LaTeX 是默认论文主链，`modules/05_writing/latex.md` 的“正文表达与章节组织协议（写作权威）”统一约束 DOCX、LaTeX 与 AI-cleanup。"
        "v7.5.2 的入口防漂移不改变正文行为；当前写作结构继续执行 v7.4.5 的成稿 prose audit，并由 v7.5.0 reasoning contract 约束公式推理、共享基础、跨问递进与证据化表达："
    )
    for relative in ("SKILL.md", "skills/mathmodel-skill/SKILL.md"):
        text = read(relative)
        if old_sentence in text:
            write(relative, text.replace(old_sentence, new_sentence, 1))


def fix_readme_release_history() -> None:
    relative = "README.md"
    text = read(relative)
    stale_heading = "## v7.5.1：证明机器契约收口与成稿 prose audit"
    if stale_heading not in text:
        raise RuntimeError("README stale v7.5.1 heading not found")
    text = text.replace(stale_heading, "## v7.4.5：证明机器契约收口与成稿 prose audit", 1)
    anchor = "## v7.4.5：证明机器契约收口与成稿 prose audit"
    new_sections = """## v7.5.2：双 Skill 入口语义防漂移

根目录 `SKILL.md` 与 Codex 插件目录 `skills/mathmodel-skill/SKILL.md` 继续同时保留，但两者新增完全一致的“运行时入口合同”摘要：统一委托 `core/bootstrap.yaml`，再由 `core/workflow_router.yaml` / `scripts/resolve_workflow.py` 解析最小 route-specific 加载链。详细模型、预处理、求解、绘图和写作规则仍只由 bootstrap 指向的权威源定义，两个入口不再各自承担独立规则权威。

静态 lint 与 v7.5.2 回归测试同时检查两入口的合同块、版本、插件 `./skills/` 发现路径、核心 authority 指针以及 legacy/V622 默认隔离。稳定的 `scripts/README.md`、`legacy/README.md` 和 resolver docstring 改为 versionless，减少后续 patch 的无意义版本触点。数值模型、预处理、工作簿、Python/MATLAB、五文件合同、LaTeX 与 v7.5.0 writing-reasoning 能力均未改变。

## v7.5.1：读取架构瘦身与单一事实源强化

`core/bootstrap.yaml` 收回为真正的最小启动索引，只保留 authority 指针和启动不变量；详细 reasoning 继续由 `core/writing_reasoning_contract.yaml` 等权威源承担。resolver 对 taxonomy 改为按需解析，Figure、工作簿和无关 utility route 不再无需求加载 reasoning/taxonomy。

v7.5.1 同时保留 v7.5.0 的 Source→Derivation→Destination、共享基础、跨问递进、结构化简优先、数值参数证据、多方法结构一致性与本科生证据驱动学术表达，并通过读取预算与 route-isolation 回归防止后续瘦身误删能力。

## v7.5.0：跨比赛公式推理与证据驱动写作架构

建立跨比赛 `Source → Derivation → Destination` 公式推理链；共享基础按实际复用程度启用，后问只写继承与增量；高维/非线性模型先检查解析关系、单调性、消元、降维、候选域和分解，再决定是否升级算法。步长、网格、Monte Carlo/Bootstrap 数量、窗口、滞后和优化容差等数值参数必须有收敛、验证或稳定性证据。

多方法验证从单纯结果数值一致扩展到决策区间、活跃约束、策略结构、系数方向、排序、聚类或关键区域等任务相关结构一致性；正文语言采用 evidence-driven undergraduate academic prose，强调具体对象、当前数学困难、数学处理和所得信息的连续证据链。

"""
    text = text.replace(anchor, new_sections + anchor, 1)
    write(relative, text)


def fix_scripts_readme() -> None:
    relative = "scripts/README.md"
    text = read(relative)
    stale = (
        "v7.5.1 保留 v7.4.4 的自然论文流，并清理了证明机器契约的旧歧义：默认 `paragraph_first`，要求逻辑单元清晰，只有明显多阶段证明才使用 2--6 个编号步骤。"
        "新增 prose audit 检查高密度否定/转折、重复段首主语、重复固定图表句式及独立结论章、H1/A1、缺“问题提出”/“核心模型汇总”等结构回退；普通单次使用“但/然而”不判错。"
    )
    corrected = (
        "v7.5.2 新增根 `SKILL.md` 与 packaged `skills/mathmodel-skill/SKILL.md` 的运行时入口合同一致性检查；两入口都只委托 bootstrap/resolver/route authority，不各自建立第二套运行规则。"
        "版本一致性检查同时避免稳定工具说明、legacy 归档说明和 resolver docstring 成为无意义的 release carrier。\n\n"
        "v7.5.1 将 bootstrap 收回为最小启动索引，并把 taxonomy/reasoning 改为 route-specific lazy load；v7.5.0 建立跨比赛 Source→Derivation→Destination、共享基础、跨问增量、结构化简优先和数值参数证据。\n\n"
        "v7.4.5 保留 v7.4.4 的自然论文流，并清理证明机器契约歧义：默认 `paragraph_first`，要求逻辑单元清晰，只有明显多阶段证明才使用 2--6 个编号步骤。"
        "prose audit 检查高密度否定/转折、重复段首主语、重复固定图表句式及独立结论章、H1/A1、缺“问题提出”/“核心模型汇总”等结构回退；普通单次使用“但/然而”不判错。"
    )
    if stale not in text:
        raise RuntimeError("scripts/README stale release paragraph not found")
    write(relative, text.replace(stale, corrected, 1))


def update_changelog() -> None:
    relative = "CHANGELOG.md"
    text = read(relative)
    anchor = "## Current release: 7.5.1\n\n"
    if text.count(anchor) != 1:
        raise RuntimeError("CHANGELOG current release anchor mismatch")
    new = """## Current release: 7.5.2

- Added an identical non-authoritative runtime-entry contract block to root `SKILL.md` and packaged `skills/mathmodel-skill/SKILL.md`. Both entrypoints now explicitly delegate to the same `core/bootstrap.yaml` → global policy → `scripts/resolve_workflow.py` → route-specific authority chain; neither entrypoint is allowed to become an independent domain-rule source.
- Added static-lint and unit-test protection for dual-entrypoint semantic parity, bootstrap/plugin version parity, `./skills/` plugin discovery, required authority pointers and legacy/V622 default isolation. This closes the previous gap where only the two frontmatter version strings were compared.
- Removed redundant current-version coupling from stable `scripts/README.md`, `legacy/README.md` and the resolver docstring, and converted older release-version tests to derive the active version from bootstrap rather than hard-coding every patch number. `README.md` release headings were corrected so v7.5.1 again denotes architecture slimming and v7.5.0 denotes the reasoning architecture.
- No numerical model, preprocessing behavior, workbook schema, Python/MATLAB ownership, five-file question contract, LaTeX interface or v7.5.0 reasoning capability changed.

## Previous release: 7.5.1

"""
    write(relative, text.replace(anchor, new, 1))


def harden_lint() -> None:
    relative = "scripts/lint_skill.py"
    text = read(relative)
    old_docs = 'VERSION_DOCS = ["SKILL.md", "README.md", "CHANGELOG.md", "scripts/README.md", "legacy/README.md", "core/hsk_core_policy.md"]'
    new_docs = (
        '# Stable utility/archive docs are intentionally versionless; only active release carriers are checked here.\n'
        'VERSION_DOCS = ["SKILL.md", "README.md", "CHANGELOG.md", "core/hsk_core_policy.md"]'
    )
    if text.count(old_docs) != 1:
        raise RuntimeError("lint VERSION_DOCS anchor mismatch")
    text = text.replace(old_docs, new_docs, 1)

    function_anchor = "\ndef check_repository_references(errors: list[str]) -> None:\n"
    if text.count(function_anchor) != 1:
        raise RuntimeError("lint function insertion anchor mismatch")
    parity_function = r'''

def check_skill_entrypoint_parity(errors: list[str]) -> None:
    """Keep repository and packaged Skill entrypoints on one runtime authority chain."""
    root_skill_path = ROOT / "SKILL.md"
    packaged_skill_path = ROOT / "skills/mathmodel-skill/SKILL.md"
    plugin_path = ROOT / ".codex-plugin/plugin.json"
    bootstrap = load_structured(ROOT / "core/bootstrap.yaml") or {}
    current = str(bootstrap.get("skill_version", ""))
    start = "<!-- HSK_RUNTIME_ENTRY_CONTRACT_START -->"
    end = "<!-- HSK_RUNTIME_ENTRY_CONTRACT_END -->"

    def frontmatter_version(text: str, origin: str) -> str | None:
        match = re.search(r"^version:\s*([^\s]+)", text, flags=re.MULTILINE)
        if not match:
            errors.append(f"skill entrypoint version missing: {origin}")
            return None
        return match.group(1)

    def contract_block(text: str, origin: str) -> str | None:
        if text.count(start) != 1 or text.count(end) != 1:
            errors.append(f"skill entrypoint runtime contract markers invalid: {origin}")
            return None
        return text.split(start, 1)[1].split(end, 1)[0].strip()

    texts = {
        "SKILL.md": read_text(root_skill_path),
        "skills/mathmodel-skill/SKILL.md": read_text(packaged_skill_path),
    }
    blocks: dict[str, str | None] = {}
    required_tokens = (
        "core/bootstrap.yaml",
        "core/workflow_router.yaml",
        "core/hsk_core_policy.md",
        "scripts/resolve_workflow.py",
        "core/writing_reasoning_contract.yaml",
        "模型论文框架.md",
        "legacy/",
    )
    forbidden_tokens = (
        "HSK_RUNTIME_ROUTER_V622.md",
        "HSK_SKILL_FILE_INDEX_V622.md",
        "HSK_TEMPLATE_INDEX_V622.md",
        "PROJECT_INSTRUCTIONS_HSK_V622.md",
    )
    for origin, text_value in texts.items():
        version = frontmatter_version(text_value, origin)
        if version is not None and version != current:
            errors.append(f"skill entrypoint version mismatch: {origin} -> {version}, bootstrap -> {current}")
        block = contract_block(text_value, origin)
        blocks[origin] = block
        if block is None:
            continue
        for token in required_tokens:
            if token not in block:
                errors.append(f"skill entrypoint authority token missing: {origin} -> {token}")
        for token in forbidden_tokens:
            if token in block:
                errors.append(f"skill entrypoint must not depend on compatibility pointer: {origin} -> {token}")

    root_block = blocks.get("SKILL.md")
    packaged_block = blocks.get("skills/mathmodel-skill/SKILL.md")
    if root_block is not None and packaged_block is not None and root_block != packaged_block:
        errors.append("root and packaged SKILL runtime-entry contracts drifted")

    plugin = load_structured(plugin_path) or {}
    if plugin.get("version") != current:
        errors.append(f"plugin/bootstrap version mismatch: plugin -> {plugin.get('version')}, bootstrap -> {current}")
    if plugin.get("skills") != "./skills/":
        errors.append("plugin skill discovery path must remain ./skills/")
'''
    text = text.replace(function_anchor, parity_function + function_anchor, 1)

    checks_old = "check_required, check_compatibility_pointers, check_root_release_note_hygiene, check_versions, check_bootstrap_and_governance,"
    checks_new = "check_required, check_compatibility_pointers, check_skill_entrypoint_parity, check_root_release_note_hygiene, check_versions, check_bootstrap_and_governance,"
    if text.count(checks_old) != 1:
        raise RuntimeError("lint checks tuple anchor mismatch")
    text = text.replace(checks_old, checks_new, 1)
    write(relative, text)


def modernize_version_tests() -> None:
    # v7.3 regression: keep release parity strong without hard-coding every patch number.
    relative = "tests/test_v730_writing_expression_protocol.py"
    text = read(relative)
    pattern = r"    def test_release_versions_are_consistent\(self\):\n.*?(?=\n\n\nif __name__)"
    replacement = '''    def test_release_versions_are_consistent(self):
        bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))
        current = str(bootstrap["skill_version"])
        manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8"))
        output = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        plugin = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(str(manifest["version"]), current)
        self.assertEqual(str(output["version"]), current)
        self.assertEqual(str(plugin["version"]), current)
        self.assertIn(f"version: {current}", (ROOT / "SKILL.md").read_text(encoding="utf-8"))
        self.assertIn(
            f"version: {current}",
            (ROOT / "skills/mathmodel-skill/SKILL.md").read_text(encoding="utf-8"),
        )
        self.assertTrue((ROOT / "README.md").read_text(encoding="utf-8").startswith(f"# mathmodel-skill v{current}"))
        self.assertIn(f"## Current release: {current}", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))'''
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError("v730 release parity test replacement failed")
    write(relative, updated)

    relative = "tests/test_v741_skill_closure_hygiene.py"
    text = read(relative)
    old = '''        self.assertEqual(bootstrap["skill_version"], "7.5.1")
        self.assertEqual((ROOT / "core/hsk_core_policy.md").read_text(encoding="utf-8").splitlines()[0], "# HSK Core Policy v7.5.1")'''
    new = '''        current = str(bootstrap["skill_version"])
        self.assertIn(f"version: {current}", (ROOT / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual((ROOT / "core/hsk_core_policy.md").read_text(encoding="utf-8").splitlines()[0], f"# HSK Core Policy v{current}")'''
    if text.count(old) != 1:
        raise RuntimeError("v741 version assertions anchor mismatch")
    write(relative, text.replace(old, new, 1))

    for relative in (
        "tests/test_schemas.py",
        "tests/test_v740_writing_evidence_architecture.py",
        "tests/test_v744_natural_paper_flow.py",
    ):
        text = read(relative)
        old = 'self.assertEqual(data["version"], "7.5.1")' if relative != "tests/test_schemas.py" else 'self.assertEqual(contract["version"], "7.5.1")'
        if old not in text:
            raise RuntimeError(f"{relative}: hard-coded output-contract version anchor missing")
        var = "data" if relative != "tests/test_schemas.py" else "contract"
        indent = "        "
        new = (
            f'{indent}current = str(yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))["skill_version"])\n'
            f'{indent}self.assertEqual(str({var}["version"]), current)'
        )
        write(relative, text.replace(indent + old, new, 1))

    relative = "tests/test_v661_code_quality_closure.py"
    text = read(relative)
    old = '''        current = str(yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))["skill_version"])
        # v7.5.1 is a writing-only patch. The code-quality domain contract did not
        # change behavior, so it intentionally retains its v7.4.2 release marker.
        self.assertEqual(current, "7.5.1")
        self.assertEqual(str(data["skill_version"]), "7.4.2")'''
    new = '''        # The code-quality domain contract keeps its own behavior/schema marker
        # until that domain changes; release parity is checked by the global carriers.
        self.assertEqual(str(data["skill_version"]), "7.4.2")'''
    if text.count(old) != 1:
        raise RuntimeError("v661 current-release assertion anchor mismatch")
    write(relative, text.replace(old, new, 1))

    relative = "tests/test_v701_stage_boundary_closure.py"
    text = read(relative)
    old = '''    def test_resolver_docstring_uses_current_release(self):
        text = (ROOT / "scripts/resolve_workflow.py").read_text(encoding="utf-8")
        self.assertNotIn("v6.6.0 execution plan", text)
        self.assertNotIn("v7.0.1 execution plan", text)
        self.assertNotIn("v7.1.0 execution plan", text)
        self.assertNotIn("v7.2.2 execution plan", text)
        self.assertNotIn("v7.4.2 execution plan", text)
        self.assertNotIn("v7.4.3 execution plan", text)
        self.assertNotIn("v7.4.4 execution plan", text)
        self.assertIn("v7.5.1 execution plan", text)'''
    new = '''    def test_resolver_docstring_is_versionless_to_avoid_release_drift(self):
        text = (ROOT / "scripts/resolve_workflow.py").read_text(encoding="utf-8")
        self.assertIn("ordered HSK execution plan", text)
        self.assertIsNone(re.search(r"HSK v\\d+\\.\\d+\\.\\d+ execution plan", text))'''
    if text.count(old) != 1:
        raise RuntimeError("v701 resolver-docstring anchor mismatch")
    text = text.replace("import hashlib\n", "import hashlib\nimport re\n", 1)
    write(relative, text.replace(old, new, 1))


def add_v752_tests() -> None:
    relative = "tests/test_v752_entrypoint_parity.py"
    if (ROOT / relative).exists():
        raise RuntimeError(f"{relative} already exists")
    test_text = r'''from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ROOT_SKILL = ROOT / "SKILL.md"
PACKAGED_SKILL = ROOT / "skills/mathmodel-skill/SKILL.md"
START = "<!-- HSK_RUNTIME_ENTRY_CONTRACT_START -->"
END = "<!-- HSK_RUNTIME_ENTRY_CONTRACT_END -->"


def extract_contract(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if text.count(START) != 1 or text.count(END) != 1:
        raise AssertionError(f"runtime contract markers invalid: {path}")
    return text.split(START, 1)[1].split(END, 1)[0].strip()


def frontmatter_version(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^version:\s*([^\s]+)", text, flags=re.MULTILINE)
    if not match:
        raise AssertionError(f"frontmatter version missing: {path}")
    return match.group(1)


class EntrypointParityV752Tests(unittest.TestCase):
    def test_root_and_packaged_runtime_contracts_are_identical(self):
        self.assertEqual(extract_contract(ROOT_SKILL), extract_contract(PACKAGED_SKILL))

    def test_runtime_contract_delegates_to_single_authority_chain(self):
        block = extract_contract(ROOT_SKILL)
        for token in (
            "core/bootstrap.yaml",
            "core/workflow_router.yaml",
            "core/hsk_core_policy.md",
            "scripts/resolve_workflow.py",
            "core/writing_reasoning_contract.yaml",
            "模型论文框架.md",
            "legacy/",
        ):
            self.assertIn(token, block)
        for stale in (
            "HSK_RUNTIME_ROUTER_V622.md",
            "HSK_SKILL_FILE_INDEX_V622.md",
            "HSK_TEMPLATE_INDEX_V622.md",
            "PROJECT_INSTRUCTIONS_HSK_V622.md",
        ):
            self.assertNotIn(stale, block)
        self.assertIn("不作为模型、预处理、求解、绘图或写作规则的独立权威", block)

    def test_skill_and_plugin_versions_follow_bootstrap(self):
        bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))
        current = str(bootstrap["skill_version"])
        plugin = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(frontmatter_version(ROOT_SKILL), current)
        self.assertEqual(frontmatter_version(PACKAGED_SKILL), current)
        self.assertEqual(str(plugin["version"]), current)
        self.assertEqual(plugin["skills"], "./skills/")

    def test_stable_docs_and_resolver_do_not_create_extra_release_carriers(self):
        self.assertEqual((ROOT / "scripts/README.md").read_text(encoding="utf-8").splitlines()[0], "# Scripts")
        legacy = (ROOT / "legacy/README.md").read_text(encoding="utf-8")
        self.assertIn("不属于当前默认运行链路", legacy)
        resolver = (ROOT / "scripts/resolve_workflow.py").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"HSK v\d+\.\d+\.\d+ execution plan", resolver))

    def test_readme_release_history_matches_current_architecture(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertTrue(readme.startswith("# mathmodel-skill v7.5.2"))
        self.assertIn("## v7.5.2：双 Skill 入口语义防漂移", readme)
        self.assertIn("## v7.5.1：读取架构瘦身与单一事实源强化", readme)
        self.assertIn("## v7.5.0：跨比赛公式推理与证据驱动写作架构", readme)
        self.assertIn("## v7.4.5：证明机器契约收口与成稿 prose audit", readme)
        self.assertNotIn("## v7.5.1：证明机器契约收口与成稿 prose audit", readme)

    def test_one_shot_v752_migration_files_are_absent(self):
        paths = (
            "scripts/_v752_entrypoint_parity_migration.py",
            ".github/workflows/v752-entrypoint-parity-migration.yml",
        )
        manifest = (ROOT / "MANIFEST.sha256").read_text(encoding="utf-8")
        for relative in paths:
            self.assertFalse((ROOT / relative).exists(), relative)
            self.assertNotIn(relative, manifest)


if __name__ == "__main__":
    unittest.main()
'''
    write(relative, test_text)


def main() -> int:
    bump_version_carriers()
    add_runtime_contracts()
    fix_readme_release_history()
    fix_scripts_readme()
    update_changelog()
    harden_lint()
    modernize_version_tests()
    add_v752_tests()

    print("v7.5.2 entrypoint parity migration applied")
    print("remaining active 7.5.1 references for review:")
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or "legacy" in path.parts or path.name in {"CHANGELOG.md", "MANIFEST.sha256"}:
            continue
        if path.suffix.lower() not in {".md", ".py", ".yaml", ".yml", ".json"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if "7.5.1" in text:
            print("-", path.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
