from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = "7.4.0"
NEW = "7.4.1"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    (ROOT / rel).write_text(text, encoding="utf-8", newline="\n")


def replace_once(rel: str, old: str, new: str) -> None:
    text = read(rel)
    if text.count(old) != 1:
        raise RuntimeError(f"{rel}: expected exactly one occurrence of {old!r}, got {text.count(old)}")
    write(rel, text.replace(old, new, 1))


def replace_all(rel: str, old: str, new: str, minimum: int = 1) -> None:
    text = read(rel)
    count = text.count(old)
    if count < minimum:
        raise RuntimeError(f"{rel}: expected at least {minimum} occurrences of {old!r}, got {count}")
    write(rel, text.replace(old, new))


# Release markers and current-version authorities.
for rel, old, new in [
    ("core/bootstrap.yaml", "skill_version: 7.4.0", "skill_version: 7.4.1"),
    ("core/workflow_router.yaml", "version: 7.4.0", "version: 7.4.1"),
    ("core/module_manifest.yaml", "version: 7.4.0", "version: 7.4.1"),
    ("core/output_contract.yaml", "version: 7.4.0", "version: 7.4.1"),
    ("core/project_state.schema.yaml", "version: 7.4.0", "version: 7.4.1"),
    ("core/user_execution_contract.yaml", "skill_version: 7.4.0", "skill_version: 7.4.1"),
    ("core/code_quality_contract.yaml", "skill_version: 7.4.0", "skill_version: 7.4.1"),
    ("core/global_preprocessing_contract.yaml", "skill_version: 7.4.0", "skill_version: 7.4.1"),
    ("SKILL.md", "version: 7.4.0", "version: 7.4.1"),
    ("SKILL.md", "# HSK 数学建模模块化工作流 v7.4.0", "# HSK 数学建模模块化工作流 v7.4.1"),
    ("skills/mathmodel-skill/SKILL.md", "version: 7.4.0", "version: 7.4.1"),
    ("skills/mathmodel-skill/SKILL.md", "# HSK 数学建模模块化工作流 v7.4.0", "# HSK 数学建模模块化工作流 v7.4.1"),
    ("README.md", "# mathmodel-skill v7.4.0", "# mathmodel-skill v7.4.1"),
    ("scripts/README.md", "# Scripts v7.4.0", "# Scripts v7.4.1"),
    ("legacy/README.md", "不属于 v7.4.0 默认运行链路", "不属于 v7.4.1 默认运行链路"),
    ("core/hsk_core_policy.md", "# HSK Core Policy v7.2.6", "# HSK Core Policy v7.4.1"),
]:
    replace_once(rel, old, new)

# The template add-on is an active stable entry; avoid carrying an obsolete Skill-era version in its title.
replace_once(
    "templates/latex/cumcm/hsk/README.md",
    "# HSK CUMCM LaTeX Template Add-on v6.2.2",
    "# HSK CUMCM LaTeX Template Add-on",
)

# Plugin release marker.
plugin_path = ROOT / ".codex-plugin/plugin.json"
plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
if plugin.get("version") != OLD:
    raise RuntimeError(f"plugin version unexpected: {plugin.get('version')}")
plugin["version"] = NEW
plugin_path.write_text(json.dumps(plugin, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

# Taxonomy must explicitly support the active v7 line.
replace_once(
    "core/task_taxonomy.yaml",
    "skill_compatibility: '>=6.3.1,<7.0.0'",
    "skill_compatibility: '>=6.3.1,<8.0.0'",
)

# Model-design assumptions must agree with the v7.4 evidence-writing authority: no fixed quota, scoped by use.
replace_once(
    "modules/02_model_design.md",
    "每个模型保留 3--5 个关键假设，说明设立原因、与题意关系、结果影响、失效偏差和检验方式。假设不能替代可由数据或约束直接表达的关系。",
    "模型假设按必要性而非数量配额保留。只有会实质改变变量、约束、目标、分布、状态转移、近似误差或适用边界的条件才作为假设；题面事实、数据事实、确定性定义和单位约定不得伪装成假设。影响两个及以上小问的共享假设进入全局层，只影响单问的假设在第一次使用前就近记录；不存在实质共享假设时允许不设置独立全局假设章。每条保留假设说明依据、与题意关系、对模型/结果的影响、失效偏差和可执行检验。假设不能替代可由数据、定义或约束直接表达的关系。",
)

# Clarify that the project-state preprocessing note describes feature origin, not the active Skill version.
replace_once(
    "core/project_state.schema.yaml",
    "description: v7.2.6条件式预处理状态。旧项目可缺失；重新进入模型设计或求解时先锁定decision并按当前通用审计规则复核必要性。",
    "description: v7.2.6引入的条件式预处理状态。旧项目可缺失；重新进入模型设计或求解时先锁定decision并按当前通用审计规则复核必要性。",
)

# Resolver and tests that intentionally assert the current release marker.
replace_all("scripts/resolve_workflow.py", "v7.4.0 execution plan", "v7.4.1 execution plan")
for rel in [
    "tests/test_v730_writing_expression_protocol.py",
    "tests/test_v740_writing_evidence_architecture.py",
    "tests/test_schemas.py",
    "tests/test_v701_stage_boundary_closure.py",
]:
    replace_all(rel, '"7.4.0"', '"7.4.1"')
replace_all("tests/test_v701_stage_boundary_closure.py", "v7.4.0 execution plan", "v7.4.1 execution plan")

# Release notes: preserve v7.4.0 as historical feature release while adding a small closure patch above it.
changelog = read("CHANGELOG.md")
needle = "## Current release: 7.4.0\n"
if changelog.count(needle) != 1:
    raise RuntimeError("CHANGELOG current release anchor mismatch")
patch_notes = """## Current release: 7.4.1\n\n- Audited every active Module 01--06 stage plus bootstrap, router, manifest, contracts, templates and compatibility boundaries for read/load closure.\n- Fixed the active `core/hsk_core_policy.md` header that still advertised v7.2.6, and extended release-marker linting so current authoritative Markdown cannot silently lag the Skill version again.\n- Fixed `core/task_taxonomy.yaml` declaring `<7.0.0` compatibility even though the active Skill is v7; the taxonomy now explicitly supports the v7 line.\n- Removed the stale fixed `3--5` assumption quota from Module 02 and aligned model design with the writing authority: assumptions are impact-based, checkable and localized by cross-question or question-local scope.\n- Kept the four V622 filenames as backward-compatible pointers but removed them from the active Skill index, active MANIFEST and active-required-file set, so historical pointer names cannot be mistaken for current runtime modules.\n- Made the CUMCM HSK template add-on README versionless so a stable active template entry does not carry an obsolete Skill-era version label.\n- Hardened `lint_skill.py` with compatibility-pointer isolation, taxonomy compatibility checks, repository-relative path validation, Markdown local-link checks and all-route resolver smoke checks.\n- Added v7.4.1 regression coverage for active/compatibility separation and resolver path existence. No Problem Contract, preprocessing, numerical, workbook, MATLAB, five-file or writing-evidence interface changed.\n\n## Previous release: 7.4.0\n"""
changelog = changelog.replace(needle, patch_notes, 1)
write("CHANGELOG.md", changelog)

# This script is one-shot migration scaffolding and must not remain in the active package.
Path(__file__).unlink()
