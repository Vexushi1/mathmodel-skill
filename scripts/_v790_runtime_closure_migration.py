#!/usr/bin/env python3
"""One-shot branch migration for v7.9.0 LaTeX runtime closure.

This file is intentionally self-removing. It is introduced only to apply exact,
asserted edits on the dedicated upgrade branch because repository modification is
performed through GitHub Actions rather than a local checkout. The final branch
must not contain this migration file or a modified refresh-generated workflow.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET_VERSION = "7.9.0"
OLD_VERSION = "7.8.1"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one exact match, found {count}: {old[:100]!r}")
    write(path, text.replace(old, new, 1))


def regex_once(path: str, pattern: str, replacement: str, *, flags: int = 0) -> None:
    text = read(path)
    updated, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f"{path}: expected one regex match, found {count}: {pattern}")
    write(path, updated)


def insert_before_once(path: str, marker: str, addition: str) -> None:
    replace_once(path, marker, addition + marker)


def write_new(path: str, text: str) -> None:
    target = ROOT / path
    if target.exists():
        raise RuntimeError(f"new file already exists: {path}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def update_versions() -> None:
    replace_once("core/bootstrap.yaml", f"skill_version: {OLD_VERSION}", f"skill_version: {TARGET_VERSION}")
    for path in ("core/workflow_router.yaml", "core/module_manifest.yaml", "core/output_contract.yaml"):
        replace_once(path, f"version: {OLD_VERSION}", f"version: {TARGET_VERSION}")
    for path in ("SKILL.md", "skills/mathmodel-skill/SKILL.md"):
        replace_once(path, f"version: {OLD_VERSION}", f"version: {TARGET_VERSION}")
        replace_once(path, f"# HSK 数学建模模块化工作流 v{OLD_VERSION}", f"# HSK 数学建模模块化工作流 v{TARGET_VERSION}")
    replace_once("core/hsk_core_policy.md", f"# HSK Core Policy v{OLD_VERSION}", f"# HSK Core Policy v{TARGET_VERSION}")
    replace_once("scripts/lint_skill_checks.py", f'PACKAGE_VERSION = "{OLD_VERSION}"', f'PACKAGE_VERSION = "{TARGET_VERSION}"')

    plugin_path = ROOT / ".codex-plugin/plugin.json"
    plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
    if plugin.get("version") != OLD_VERSION:
        raise RuntimeError(f"plugin version drift: {plugin.get('version')}")
    plugin["version"] = TARGET_VERSION
    plugin["description"] = (
        "HSK lightweight-bootstrap mathematical-modeling workflow with Problem Contract freezing, "
        "semantic closure, evidence-driven conditional preprocessing, dependency-aware stale propagation, "
        "full-fidelity user execution, separate primary/result-analysis Python stages, assistant-readable "
        "model-paper project memory, Source-Derivation-Destination formula traces, adaptive Algorithm Trace, "
        "tiered writing governance, Citation Evidence, Terminology Registry, scoring-aware Numeric Profile, "
        "Title Claim Gate, MATLAB evidence figures, modular LaTeX source delivery, recursive project audit, "
        "and source-bundle/PDF freshness verification."
    )
    plugin["interface"]["shortDescription"] = "题意冻结、算法闭环、双阶段Python、模块化LaTeX与源码-PDF新鲜度校验"
    plugin_path.write_text(json.dumps(plugin, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    replace_once("README.md", f"# mathmodel-skill v{OLD_VERSION}", f"# mathmodel-skill v{TARGET_VERSION}")
    release = """## v7.9.0：模块化 LaTeX 运行时闭环\n\n本版本把 v7.8.1 之后已经进入模板/Artifact 层的模块化 LaTeX 能力正式闭合到运行时、编译报告和项目同步层，不改变数学模型、数值求解、工作簿 Schema、Python/MATLAB 职责或每问五文件接口。\n\n- 正式 LaTeX 审计统一从 `scripts/audit_latex_project.py` 进入：模块化工程递归展开 `\\input/\\include`，兼容单文件工程退化为单文件审计；`audit_paper_prose.py` 保留为底层 prose/BibTeX/framework 审查实现，不再作为活动 LaTeX 运行时的默认入口。\n- `full_workflow` 在跨过用户执行边界后显式补齐 Figure、LaTeX 和 Review Artifact Packs，避免“直接 latex route 能读规则、完整流程反而漏读 Pack”的分流。\n- CUMCM 当前项目模板统一指向 `templates/latex/cumcm/hsk/`；`cumcmthesis/` 仅保留上游 class/基础模板资源。\n- 新增 `scripts/latex_delivery.py`，对 active `.tex` 图、参考文献、本地 class/style 和正式图片建立 source bundle hash；`render_paper.py` 自动生成 `compile_report.yaml`，记录 source/PDF hash、实际编译序列和未解析引用。\n- `sync_project.py` 在 LaTeX/提交 scope 重新计算当前 source bundle，并要求与 `compile_report.compiled_from_source_sha256` 及 PDF hash 一致；任一 active 源文件或正式图片在编译后改变都会使旧 PDF 失效。\n- Paper Fragment 的 `source_file` 在项目审计时与真实 `final_latex/` 文件和当前 main include graph 做确定性闭环检查。\n- `full_workflow` 的最终 terminal outputs 补齐 `validated_submission_package`。\n- 增加跨层回归测试，覆盖 audit 入口、Pack closure、CUMCM 模板权威、fragment 物理映射、source/PDF freshness 与 compile report。\n\n"""
    insert_before_once("README.md", "## v7.8.1：Algorithm Trace 闭环补强\n", release)

    changelog = read("CHANGELOG.md")
    marker = "## Current release: 7.8.1\n"
    if marker not in changelog:
        raise RuntimeError("CHANGELOG current release marker missing")
    section = """## Current release: 7.9.0\n\n- Closed modular-LaTeX runtime dispatch: `audit_latex_project.py` is now the public LaTeX audit entrypoint for modular and compatible single-file projects, delegating prose/BibTeX/framework checks to `audit_paper_prose.py`.\n- Closed `full_workflow` post-execution Pack loading so Figure, LaTeX and Review Artifact Packs are available after accepted primary/result-analysis workbooks, and added `validated_submission_package` to final workflow outputs.\n- Unified the current CUMCM project-template authority on `templates/latex/cumcm/hsk/`; the `cumcmthesis/` directory remains an upstream class/base-template resource rather than the active project template.\n- Added source-bundle/PDF freshness verification through deterministic compile reports. `render_paper.py` now writes `compile_report.yaml`; `sync_project.py` recomputes the current active source bundle before LaTeX/submission delivery.\n- Added deterministic Paper Fragment `source_file` checks against actual files and the active `main.tex` include graph.\n- Added regression coverage for the integration gaps above. Numerical modeling, preprocessing, Workbook Schema, Python/MATLAB ownership, user full-fidelity execution, framework `v0.8-project-memory`, semantic-governance 1.0.0 and the per-question five-file interface are unchanged.\n\n## Previous release: 7.8.1\n"""
    write("CHANGELOG.md", changelog.replace(marker, section, 1))


def update_runtime_contracts() -> None:
    # Public audit entrypoint while preserving the lower-level prose implementation.
    replace_once(
        "core/bootstrap.yaml",
        "  audit_paper_prose: python scripts/audit_paper_prose.py\n",
        "  audit_latex_project: python scripts/audit_latex_project.py\n  audit_paper_prose: python scripts/audit_paper_prose.py\n",
    )
    replace_once(
        "core/output_contract.yaml",
        "  prose_audit_script: scripts/audit_paper_prose.py\n  latex_source_layout_default: modular\n",
        "  prose_audit_script: scripts/audit_paper_prose.py\n  latex_audit_entrypoint: scripts/audit_latex_project.py\n  latex_source_layout_default: modular\n",
    )
    replace_once(
        "core/output_contract.yaml",
        "  - 对DOCX、LaTeX与提交scope检查真实文件、编译报告、图片引用和提交ZIP内容\n",
        "  - 对DOCX、LaTeX与提交scope检查真实文件、编译报告、图片引用和提交ZIP内容\n"
        "  - LaTeX与提交scope重算当前active source bundle；必须与compile_report.compiled_from_source_sha256及PDF哈希一致，任一active .tex/.bib/.cls/.sty/正式图片变化后旧PDF均视为stale\n",
    )
    replace_once(
        "core/module_manifest.yaml",
        "  compile_report: 编译引擎、日志和警告检查\n",
        "  compile_report: 编译引擎、日志、source bundle/PDF哈希新鲜度与警告检查\n",
    )

    # Resolver: close downstream Pack availability after the user-execution boundary.
    replace_once(
        "scripts/resolve_workflow.py",
        '    "approved_figures", "latex_source", "compiled_pdf", "compile_report",\n    "review_report", "model_paper_framework",\n',
        '    "approved_figures", "latex_source", "compiled_pdf", "compile_report",\n    "review_report", "validated_submission_package", "model_paper_framework",\n',
    )
    replace_once(
        "scripts/resolve_workflow.py",
        '        paths.extend([\n            "modules/04_figure_evidence.md", "modules/05_writing/latex.md",\n            "modules/05_writing/ai_cleanup.md", "modules/05_latex_compile_quality.md",\n            "modules/06_review_delivery.md",\n        ])\n',
        '        paths.extend([\n            "modules/04_figure_evidence.md", "packs/artifact/figure.md",\n            "modules/05_writing/latex.md", "packs/artifact/latex.md",\n            "modules/05_writing/ai_cleanup.md", "modules/05_latex_compile_quality.md",\n            "modules/06_review_delivery.md", "packs/artifact/review.md",\n        ])\n',
    )

    # CUMCM project-template authority.
    replace_once(
        "config/competition_profiles.yaml",
        "      latex_template: templates/latex/cumcm/cumcmthesis/\n",
        "      latex_template: templates/latex/cumcm/hsk/\n",
    )
    replace_once(
        "packs/competition/cumcm.md",
        "- 最终中文论文默认使用 `templates/latex/cumcm/cumcmthesis/`；\n",
        "- 最终中文论文默认使用 `templates/latex/cumcm/hsk/` 模块化工程；`templates/latex/cumcm/cumcmthesis/` 仅作为上游 class/基础模板资源；\n",
    )
    replace_once(
        "modules/05_writing/latex.md",
        "论文从首个正文版本开始直接使用 LaTeX，并在源码中持续修改至终稿。中文国赛默认基于 `templates/latex/cumcm/cumcmthesis/`。DOCX 不是进入本模块的前置条件；显式 DOCX 审阅件也不得成为模型或数值事实源。\n",
        "论文从首个正文版本开始直接使用 LaTeX，并在源码中持续修改至终稿。中文国赛默认基于 `templates/latex/cumcm/hsk/` 模块化工程；`templates/latex/cumcm/cumcmthesis/` 只提供上游 class/基础模板资源。DOCX 不是进入本模块的前置条件；显式 DOCX 审阅件也不得成为模型或数值事实源。\n",
    )

    # Active writing consumers must use the project wrapper, not audit main.tex as prose directly.
    replace_once(
        "modules/05_writing/latex.md",
        "本模块输出 `latex_source_draft` 与可审查 `paper_text`。随后执行 `modules/05_writing/ai_cleanup.md`，再运行 `scripts/audit_paper_prose.py` 做非破坏性检查；清理后的 `latex_source` 才进入编译模块。\n",
        "本模块输出 `latex_source_draft` 与可审查 `paper_text`。随后执行 `modules/05_writing/ai_cleanup.md`，正式 LaTeX 审计统一运行 `scripts/audit_latex_project.py`；该入口递归覆盖模块化源码，并把展开后的完整正文委托给 `scripts/audit_paper_prose.py`。清理后的 `latex_source` 通过项目审计后才进入编译模块。\n",
    )
    replace_once(
        "modules/05_writing/ai_cleanup.md",
        "本层只确认不可被润色掩盖的事实与结构边界，具体确定性检查交给 `scripts/audit_paper_prose.py`、project-state/framework validators 和 LaTeX 编译链：\n",
        "本层只确认不可被润色掩盖的事实与结构边界。正式 LaTeX 工程的确定性检查统一从 `scripts/audit_latex_project.py` 进入；该入口再委托 `scripts/audit_paper_prose.py` 完成 prose/BibTeX/framework 检查，并与 project-state/framework validators、LaTeX 编译链共同闭环：\n",
    )
    replace_once(
        "modules/05_writing/ai_cleanup.md",
        "BibTeX key、重复条目、未使用条目等确定性结构问题交给 `scripts/audit_paper_prose.py`。\n",
        "BibTeX key、重复条目、未使用条目等确定性结构问题由 `scripts/audit_latex_project.py` 的底层 prose/BibTeX 审计处理。\n",
    )
    replace_once(
        "modules/05_writing/ai_cleanup.md",
        "python scripts/audit_paper_prose.py final_latex/main.tex \\\n  --bib final_latex/references.bib \\\n  --framework 模型论文框架.md\n",
        "python scripts/audit_latex_project.py final_latex/main.tex \\\n  --bib final_latex/references.bib \\\n  --framework 模型论文框架.md\n",
    )

    replace_once(
        "modules/05_latex_compile_quality.md",
        "本模块只编译 `ai_cleanup` 输出的已清理 `latex_source`，输出 `compiled_pdf` 与 `compile_report`。\n",
        "本模块只编译已经通过 `scripts/audit_latex_project.py` 的已清理 `latex_source`，输出 `compiled_pdf` 与机器生成的 `compile_report`。\n",
    )
    replace_once(
        "modules/05_latex_compile_quality.md",
        "- `scripts/render_paper.py --profile <name>` 必须与所用模板一致，不得手工混用引擎和文献工具。\n",
        "- `scripts/render_paper.py --profile <name>` 必须与所用模板一致，不得手工混用引擎和文献工具；成功编译后由脚本自动写入 `compile_report.yaml`，不得手工伪造 passed 状态。\n"
        "- `compile_report` 必须记录当前 active LaTeX source bundle hash、实际编译序列和 PDF hash；正式同步时重新计算 source bundle，若与编译时 hash 不一致则 PDF stale，必须重编译。\n",
    )

    # Artifact LaTeX Pack: one public entrypoint for both layouts.
    path = "packs/artifact/latex.md"
    text = read(path)
    pattern = re.compile(
        r"仍采用单文件模板的工程（包括尚未迁移的 MCM/ICM、电工杯模板与旧项目）可继续直接运行核心 prose audit：\n\n```bash\npython scripts/audit_paper_prose.py final_latex/main.tex --bib final_latex/references.bib --strict\n```\n\n模块化工程正式使用项目包装器：\n\n```bash\npython scripts/audit_latex_project.py final_latex/main.tex --bib final_latex/references.bib --framework 模型论文框架.md --strict\n```",
        flags=re.M,
    )
    replacement = """正式 LaTeX 审计无论模块化还是兼容单文件工程，都统一从项目包装器进入：\n\n```bash\npython scripts/audit_latex_project.py final_latex/main.tex --bib final_latex/references.bib --framework 模型论文框架.md --strict\n```\n\n模块化工程会递归展开项目内 `\\input` / `\\include`；兼容单文件工程会自然退化为单文件展开。`scripts/audit_paper_prose.py` 继续作为包装器内部的 prose/structure/BibTeX/framework 审查实现，可用于维护级单元测试，但不再作为活动 LaTeX route 的默认入口。"""
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise RuntimeError(f"{path}: failed to replace audit dispatch section")
    write(path, updated)

    # Stable runtime documentation.
    for path in ("SKILL.md", "skills/mathmodel-skill/SKILL.md"):
        replace_once(
            path,
            "成稿运行 `scripts/audit_paper_prose.py`，可附 `--framework 模型论文框架.md` 做登记术语与 Numeric Profile 的保守检查。确定性 Hard 错误为 blocking，Default 偏离为 review_required，Recommendation/风格风险为 warning；机器不得从正则推断数学正确性、算法正确性、术语语义等价、物理/统计准确性或 citation 的语义支持关系。\n",
            "正式 LaTeX 成稿统一运行 `scripts/audit_latex_project.py`；模块化工程递归展开全部 active fragment，兼容单文件工程自然退化为单文件审计，随后由底层 `audit_paper_prose.py` 执行 prose/BibTeX/framework 检查。确定性 Hard 错误为 blocking，Default 偏离为 review_required，Recommendation/风格风险为 warning；机器不得从正则推断数学正确性、算法正确性、术语语义等价、物理/统计准确性或 citation 的语义支持关系。\n",
        )
    replace_once(
        "PROJECT_INSTRUCTIONS.md",
        "18. AI cleanup 后运行 `scripts/audit_paper_prose.py`；确定性 Hard 错误为 blocking，Default 偏离为 review_required，Recommendation/风格风险为 warning。机器不得从正则判断数学/算法正确性、参数最优性、术语语义等价或 citation 的语义支持关系；\n",
        "18. AI cleanup 后正式 LaTeX 审计统一运行 `scripts/audit_latex_project.py`；它递归展开模块化源码并委托 `audit_paper_prose.py` 做 prose/BibTeX/framework 检查。确定性 Hard 错误为 blocking，Default 偏离为 review_required，Recommendation/风格风险为 warning；机器不得从正则判断数学/算法正确性、参数最优性、术语语义等价或 citation 的语义支持关系；\n",
    )
    replace_once(
        "RUNTIME_ROUTER.md",
        "→ prose/BibTeX/framework audit（scripts/audit_paper_prose.py + framework validator）\n",
        "→ LaTeX project/prose/BibTeX/framework audit（scripts/audit_latex_project.py + framework validator）\n",
    )
    replace_once(
        "REPOSITORY_INDEX.md",
        "- `scripts/audit_paper_prose.py`：成稿结构、引用、登记术语/Numeric Profile 的保守审查；\n",
        "- `scripts/audit_latex_project.py`：正式 LaTeX 项目审计入口，递归覆盖模块化源码并委托 prose/BibTeX/framework 检查；\n- `scripts/audit_paper_prose.py`：上述入口使用的底层成稿结构、引用、登记术语/Numeric Profile 保守审查实现；\n",
    )
    replace_once(
        "scripts/README.md",
        "- `audit_paper_prose.py`：对最终论文主文件执行非破坏性成稿审计，可结合 `--framework 模型论文框架.md` 与 `--bib references.bib`。结果分为 `blocking / review_required / warning`；默认只报告，`--strict` 阻断 `blocking` 与未处理的 `review_required`，warning 不阻断。机器不推断数学正确性、定理适用性、术语语义等价、参数最优性或 citation 是否真正支持 claim。\n",
        "- `audit_latex_project.py`：正式 LaTeX 项目审计入口。递归展开 active `\\input/\\include`、检查 fragment/source-file 工程闭环，再委托 `audit_paper_prose.py` 完成 prose/structure/BibTeX/framework 审查；兼容单文件工程自然退化为单文件模式。\n- `audit_paper_prose.py`：底层非破坏性成稿审计实现；结果分为 `blocking / review_required / warning`。它保留维护级直接调用能力，但不是活动 LaTeX route 的默认入口。机器不推断数学正确性、定理适用性、术语语义等价、参数最优性或 citation 是否真正支持 claim。\n",
    )

    # Lint inventory: new public audit and freshness helper are active required scripts.
    replace_once(
        "scripts/lint_skill_checks.py",
        '    "scripts/validate_code_delivery.py", "scripts/validate_user_execution.py", "scripts/audit_paper_prose.py",\n',
        '    "scripts/validate_code_delivery.py", "scripts/validate_user_execution.py", "scripts/audit_latex_project.py",\n    "scripts/audit_paper_prose.py", "scripts/latex_delivery.py",\n',
    )


def add_fragment_source_validation() -> None:
    path = "scripts/audit_latex_project.py"
    marker = "\ndef audit_project(\n"
    addition = r'''

def audit_fragment_source_files(
    main_file: Path,
    framework_path: Path,
    visited: set[Path],
) -> list[Finding]:
    """Validate declared current Paper Fragment -> physical LaTeX source mappings.

    The framework stores project-root-relative paths such as
    ``final_latex/sections/06_question1.tex``. A declared current mapping is only
    useful when the file exists and is part of the active ``main.tex`` include
    graph. Missing mappings remain allowed for legacy/single-file projects.
    """
    text = framework_path.read_text(encoding="utf-8-sig", errors="strict")
    heading = "### Paper Fragment Dependency Map"
    start = text.find(heading)
    if start < 0:
        return []
    tail = text[start + len(heading):]
    next_heading = re.search(r"\n#{1,3}\s+", tail)
    section = tail[:next_heading.start()] if next_heading else tail
    project_root = framework_path.parent.resolve()
    final_root = main_file.parent.resolve()
    findings: list[Finding] = []

    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line.startswith("| paper."):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 7:
            continue
        fragment_id, source_file, status = cells[0], cells[5].strip("` "), cells[6].strip("` ")
        if not source_file or status != "current":
            continue
        candidate = (project_root / source_file).resolve()
        try:
            candidate.relative_to(project_root)
            candidate.relative_to(final_root)
        except ValueError:
            findings.append(
                Finding(
                    "blocking",
                    "paper_fragment_source_outside_latex",
                    "current Paper Fragment 的 source_file 必须位于当前 final_latex 工程内。",
                    f"{fragment_id}: {source_file}",
                )
            )
            continue
        if not candidate.is_file():
            findings.append(
                Finding(
                    "blocking",
                    "paper_fragment_source_missing",
                    "current Paper Fragment 声明的 LaTeX source_file 不存在。",
                    f"{fragment_id}: {source_file}",
                )
            )
            continue
        if candidate not in visited:
            findings.append(
                Finding(
                    "blocking",
                    "paper_fragment_source_not_in_active_graph",
                    "current Paper Fragment 的 source_file 未进入 main.tex 当前 input/include 图。",
                    f"{fragment_id}: {source_file}",
                )
            )
    return findings
'''
    insert_before_once(path, marker, addition)
    replace_once(
        path,
        "    combined, project_findings, _ = expand_project(main_file)\n",
        "    combined, project_findings, visited = expand_project(main_file)\n",
    )
    replace_once(
        path,
        "    if framework_path is not None and framework_path.is_file():\n        framework_text = framework_path.read_text(encoding=\"utf-8-sig\", errors=\"strict\")\n    findings.extend(audit_framework_consistency(combined, framework_text))\n",
        "    if framework_path is not None and framework_path.is_file():\n        framework_text = framework_path.read_text(encoding=\"utf-8-sig\", errors=\"strict\")\n        findings.extend(audit_fragment_source_files(main_file, framework_path, visited))\n    findings.extend(audit_framework_consistency(combined, framework_text))\n",
    )


def add_latex_delivery_helper() -> None:
    helper = r'''#!/usr/bin/env python3
"""Deterministic LaTeX source-bundle and compile-report utilities.

The source bundle contains the active project-root-relative TeX include graph plus
project-local bibliography, document class/style files and graphics referenced by
that graph. It deliberately ignores system TeX packages and unrelated orphan files.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

INCLUDE_RE = re.compile(r"\\(?:input|include)\s*\{([^{}]+)\}")
DOCUMENTCLASS_RE = re.compile(r"\\documentclass(?:\[[^\]]*\])?\{([^{}]+)\}")
USEPACKAGE_RE = re.compile(r"\\usepackage(?:\[[^\]]*\])?\{([^{}]+)\}")
ADDBIB_RE = re.compile(r"\\addbibresource(?:\[[^\]]*\])?\{([^{}]+)\}")
BIBLIOGRAPHY_RE = re.compile(r"\\bibliography\{([^{}]+)\}")
GRAPHICS_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^{}]+)\}")
GRAPHICSPATH_RE = re.compile(r"\\graphicspath\s*\{((?:\{[^{}]*\}\s*)+)\}")
GRAPHIC_DIR_RE = re.compile(r"\{([^{}]*)\}")
TEXT_SUFFIXES = {".tex", ".bib", ".cls", ".sty", ".cfg", ".def"}
GRAPHIC_SUFFIXES = (".pdf", ".png", ".jpg", ".jpeg", ".eps", ".svg", ".tif", ".tiff")


def _split_code_comment(line: str) -> str:
    backslashes = 0
    for index, char in enumerate(line):
        if char == "\\":
            backslashes += 1
            continue
        if char == "%" and backslashes % 2 == 0:
            return line[:index]
        backslashes = 0
    return line


def executable_tex(text: str) -> str:
    return "".join(_split_code_comment(line) for line in text.splitlines(keepends=True))


def _safe_project_path(root: Path, token: str, suffix: str | None = None) -> Path | None:
    raw = Path(token.strip())
    if suffix and raw.suffix == "":
        raw = raw.with_suffix(suffix)
    if raw.is_absolute():
        return None
    candidate = (root / raw).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def _discover_tex_graph(main: Path) -> tuple[set[Path], str]:
    root = main.parent.resolve()
    visited: set[Path] = set()
    stack: list[Path] = []
    texts: list[str] = []

    def walk(path: Path) -> None:
        resolved = path.resolve()
        if resolved in stack:
            cycle = " -> ".join(item.relative_to(root).as_posix() for item in [*stack, resolved])
            raise ValueError(f"LaTeX include cycle: {cycle}")
        if resolved in visited:
            return
        if not resolved.is_file():
            raise ValueError(f"LaTeX source missing: {resolved}")
        visited.add(resolved)
        stack.append(resolved)
        text = resolved.read_text(encoding="utf-8-sig", errors="strict")
        code = executable_tex(text)
        texts.append(code)
        for target in INCLUDE_RE.findall(code):
            child = _safe_project_path(root, target, ".tex")
            if child is None or not child.is_file():
                relative = resolved.relative_to(root).as_posix()
                raise ValueError(f"LaTeX include missing or outside project: {relative} -> {target}")
            walk(child)
        stack.pop()

    walk(main)
    return visited, "\n".join(texts)


def _graphic_dirs(root: Path, combined: str) -> list[Path]:
    directories = [root]
    for block in GRAPHICSPATH_RE.findall(combined):
        for token in GRAPHIC_DIR_RE.findall(block):
            candidate = _safe_project_path(root, token)
            if candidate is not None and candidate.is_dir() and candidate not in directories:
                directories.append(candidate)
    return directories


def _resolve_graphic(root: Path, token: str, directories: Iterable[Path]) -> Path | None:
    raw = Path(token.strip())
    search: list[Path] = []
    for directory in directories:
        if raw.suffix:
            search.append((directory / raw).resolve())
        else:
            search.extend((directory / raw).with_suffix(suffix).resolve() for suffix in GRAPHIC_SUFFIXES)
    for candidate in search:
        try:
            candidate.relative_to(root)
        except ValueError:
            continue
        if candidate.is_file():
            return candidate
    return None


def source_bundle_files(main: Path, bib_path: Path | None = None) -> list[Path]:
    main = main.resolve()
    root = main.parent.resolve()
    visited, combined = _discover_tex_graph(main)
    files = set(visited)

    for raw_name in DOCUMENTCLASS_RE.findall(combined):
        for name in raw_name.split(","):
            candidate = _safe_project_path(root, name.strip(), ".cls")
            if candidate is not None and candidate.is_file():
                files.add(candidate)
    for raw_names in USEPACKAGE_RE.findall(combined):
        for name in raw_names.split(","):
            candidate = _safe_project_path(root, name.strip(), ".sty")
            if candidate is not None and candidate.is_file():
                files.add(candidate)

    bib_candidates: list[Path] = []
    if bib_path is not None:
        bib_candidates.append(bib_path.resolve())
    for token in ADDBIB_RE.findall(combined):
        candidate = _safe_project_path(root, token, ".bib")
        if candidate is not None:
            bib_candidates.append(candidate)
    for block in BIBLIOGRAPHY_RE.findall(combined):
        for token in block.split(","):
            candidate = _safe_project_path(root, token.strip(), ".bib")
            if candidate is not None:
                bib_candidates.append(candidate)
    default_bib = root / "references.bib"
    if default_bib.is_file():
        bib_candidates.append(default_bib)
    for candidate in bib_candidates:
        try:
            candidate.relative_to(root)
        except ValueError:
            continue
        if candidate.is_file():
            files.add(candidate)

    directories = _graphic_dirs(root, combined)
    for token in GRAPHICS_RE.findall(combined):
        graphic = _resolve_graphic(root, token, directories)
        if graphic is not None:
            files.add(graphic)

    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def sha256_file(path: Path) -> str:
    path = path.resolve()
    if path.suffix.lower() in TEXT_SUFFIXES:
        text = path.read_text(encoding="utf-8-sig", errors="strict").replace("\r\n", "\n").replace("\r", "\n")
        payload = text.encode("utf-8")
    else:
        payload = path.read_bytes()
    return hashlib.sha256(payload).hexdigest()


def source_bundle_snapshot(main: Path, bib_path: Path | None = None) -> dict[str, Any]:
    main = main.resolve()
    root = main.parent.resolve()
    files = source_bundle_files(main, bib_path=bib_path)
    digest = hashlib.sha256()
    records: list[dict[str, str]] = []
    for path in files:
        relative = path.relative_to(root).as_posix()
        file_hash = sha256_file(path)
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(file_hash))
        records.append({"path": relative, "sha256": file_hash})
    return {
        "source_bundle_sha256": digest.hexdigest(),
        "source_files": records,
        "source_file_count": len(records),
    }


def inspect_log(log_path: Path) -> dict[str, int]:
    if not log_path.is_file():
        return {"unresolved_references": 0, "unresolved_citations": 0, "overfull_boxes": 0}
    text = log_path.read_text(encoding="utf-8", errors="ignore")
    ref_count = len(re.findall(r"LaTeX Warning: Reference .*? undefined", text))
    cite_count = len(re.findall(r"LaTeX Warning: Citation .*? undefined", text))
    if ref_count == 0 and "There were undefined references." in text:
        ref_count = 1
    if cite_count == 0 and "There were undefined citations." in text:
        cite_count = 1
    overfull = len(re.findall(r"Overfull \\[hv]box", text))
    return {
        "unresolved_references": ref_count,
        "unresolved_citations": cite_count,
        "overfull_boxes": overfull,
    }


def write_compile_report(
    *,
    project: Path,
    main: Path,
    profile: str,
    engine: str,
    bibliography: str,
    sequence: Iterable[str],
    bib_path: Path | None = None,
) -> dict[str, Any]:
    project = project.resolve()
    main = main.resolve()
    pdf = project / f"{main.stem}.pdf"
    if not pdf.is_file():
        raise FileNotFoundError(pdf)
    snapshot = source_bundle_snapshot(main, bib_path=bib_path)
    log_status = inspect_log(project / f"{main.stem}.log")
    status = "passed" if not (log_status["unresolved_references"] or log_status["unresolved_citations"]) else "failed"
    report = {
        "report_schema_version": "2.0.0",
        "status": status,
        "profile": profile,
        "engine": engine,
        "bibliography": bibliography,
        "sequence": list(sequence),
        "main": main.relative_to(project).as_posix(),
        **snapshot,
        "compiled_from_source_sha256": snapshot["source_bundle_sha256"],
        "pdf": pdf.relative_to(project).as_posix(),
        "pdf_sha256": sha256_file(pdf),
        **log_status,
        "compiled_at": datetime.now(timezone.utc).isoformat(),
    }
    (project / "compile_report.yaml").write_text(
        yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    return report


def verify_compile_report(
    *,
    project: Path,
    main: Path,
    pdf: Path,
    report: Mapping[str, Any],
) -> list[str]:
    issues: list[str] = []
    if str(report.get("report_schema_version", "")) != "2.0.0":
        issues.append("compile_report缺少v2源码新鲜度Schema；请用当前render_paper.py重新编译")
        return issues
    try:
        snapshot = source_bundle_snapshot(main)
    except Exception as exc:  # noqa: BLE001
        return [f"LaTeX source bundle无法重建: {exc}"]
    current_source = snapshot["source_bundle_sha256"]
    recorded_source = str(report.get("source_bundle_sha256", ""))
    compiled_source = str(report.get("compiled_from_source_sha256", ""))
    if not recorded_source or not compiled_source:
        issues.append("compile_report缺少source_bundle_sha256/compiled_from_source_sha256")
    elif current_source != recorded_source or current_source != compiled_source:
        issues.append("LaTeX source bundle已在编译后变化；当前PDF stale，必须重新编译")
    if not pdf.is_file():
        issues.append(f"编译PDF不存在: {pdf}")
    else:
        current_pdf = sha256_file(pdf)
        recorded_pdf = str(report.get("pdf_sha256", ""))
        if not recorded_pdf:
            issues.append("compile_report缺少pdf_sha256")
        elif current_pdf != recorded_pdf:
            issues.append("当前PDF哈希与compile_report不一致")
    return issues
'''
    write_new("scripts/latex_delivery.py", helper)


def patch_render_and_sync() -> None:
    # render_paper.py: return actual sequence and automatically persist the report.
    replace_once(
        "scripts/render_paper.py",
        "from prepare_cumcm_class import patch_cumcm_class\n",
        "from prepare_cumcm_class import patch_cumcm_class\nfrom latex_delivery import write_compile_report\n",
    )
    regex_once(
        "scripts/render_paper.py",
        r"(def compile_project\([\s\S]*?\n\)) -> None:\n",
        r"\1 -> list[str]:\n",
    )
    replace_once(
        "scripts/render_paper.py",
        "    print(pdf)\n\n\ndef main() -> int:\n",
        "    print(pdf)\n    return sequence\n\n\ndef main() -> int:\n",
    )
    replace_once(
        "scripts/render_paper.py",
        "    compile_project(project, main_tex, profiles[profile_name], args.engine, bibliography, args.runs)\n    return 0\n",
        "    sequence = compile_project(project, main_tex, profiles[profile_name], args.engine, bibliography, args.runs)\n"
        "    effective_engine = args.engine or str(profiles[profile_name].get(\"engine\", \"xelatex\"))\n"
        "    effective_bibliography = bibliography or str(profiles[profile_name].get(\"bibliography\", \"none\"))\n"
        "    report = write_compile_report(\n"
        "        project=project, main=main_tex, profile=profile_name, engine=effective_engine,\n"
        "        bibliography=effective_bibliography, sequence=sequence,\n"
        "    )\n"
        "    print(f\"compile report: {project / 'compile_report.yaml'}\")\n"
        "    if report[\"status\"] != \"passed\":\n"
        "        raise SystemExit(\"compile finished but unresolved references/citations remain; see compile_report.yaml\")\n"
        "    return 0\n",
    )

    # sync_project.py: load the freshness helper with the same safe dynamic-loader pattern.
    replace_once(
        "scripts/sync_project.py",
        "FRAMEWORK_VALIDATION = _load_module(\n    \"hsk_framework_validation\", SKILL_ROOT / \"scripts\" / \"validate_model_paper_framework.py\"\n)\n",
        "FRAMEWORK_VALIDATION = _load_module(\n    \"hsk_framework_validation\", SKILL_ROOT / \"scripts\" / \"validate_model_paper_framework.py\"\n)\nLATEX_DELIVERY = _load_module(\n    \"hsk_latex_delivery\", SKILL_ROOT / \"scripts\" / \"latex_delivery.py\"\n)\n",
    )
    replace_once(
        "scripts/sync_project.py",
        "        if int(report.get(\"unresolved_references\", 0) or 0) != 0:\n            issues.append(\"compile_report 存在未解析引用\")\n    return issues\n",
        "        if int(report.get(\"unresolved_references\", 0) or 0) != 0:\n            issues.append(\"compile_report 存在未解析引用\")\n"
        "        if int(report.get(\"unresolved_citations\", 0) or 0) != 0:\n            issues.append(\"compile_report 存在未解析文献引用\")\n"
        "        issues.extend(\n"
        "            LATEX_DELIVERY.verify_compile_report(\n"
        "                project=root, main=source, pdf=pdf, report=report\n"
        "            )\n"
        "        )\n"
        "    return issues\n",
    )


def add_regression_tests() -> None:
    tests = r'''from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def load_module(name: str, path: Path):
    parent = str(path.parent)
    added = parent not in sys.path
    if added:
        sys.path.insert(0, parent)
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        if added:
            sys.path.remove(parent)


class TestV790RuntimeClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resolver = load_module("resolver_v790_runtime", SCRIPTS / "resolve_workflow.py")
        cls.audit = load_module("audit_v790_runtime", SCRIPTS / "audit_latex_project.py")
        cls.delivery = load_module("latex_delivery_v790", SCRIPTS / "latex_delivery.py")
        cls.sync = load_module("sync_v790_runtime", SCRIPTS / "sync_project.py")

    def test_full_workflow_loads_downstream_artifact_packs_and_final_package(self):
        plan = self.resolver.resolve_workflow(
            "full_workflow",
            objective="optimization",
            competition="CUMCM",
            available_artifacts=[
                "solution_workbook", "accepted_solution_workbook", "result_quality_report",
                "result_analysis_workbook", "accepted_result_analysis_workbook", "validated_results",
            ],
        )
        for pack in ("packs/artifact/figure.md", "packs/artifact/latex.md", "packs/artifact/review.md"):
            self.assertIn(pack, plan["packs"])
        self.assertIn("validated_submission_package", plan["terminal_outputs"])

    def test_cumcm_current_project_template_authority_is_hsk(self):
        compile_profiles = yaml.safe_load((ROOT / "core/compile_profiles.yaml").read_text(encoding="utf-8"))
        competition = yaml.safe_load((ROOT / "config/competition_profiles.yaml").read_text(encoding="utf-8"))
        self.assertEqual(compile_profiles["profiles"]["cumcm"]["template_directory"], "templates/latex/cumcm/hsk")
        self.assertEqual(competition["profiles"]["cumcm"]["stable"]["latex_template"], "templates/latex/cumcm/hsk/")
        pack = (ROOT / "packs/competition/cumcm.md").read_text(encoding="utf-8")
        module = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        self.assertIn("templates/latex/cumcm/hsk/", pack)
        self.assertIn("templates/latex/cumcm/hsk/", module)

    def test_public_latex_audit_entrypoint_is_project_wrapper(self):
        output = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(output["writing_policy"]["latex_audit_entrypoint"], "scripts/audit_latex_project.py")
        for relative in (
            "SKILL.md", "PROJECT_INSTRUCTIONS.md", "RUNTIME_ROUTER.md",
            "modules/05_writing/latex.md", "modules/05_writing/ai_cleanup.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("audit_latex_project.py", text, relative)
            self.assertNotIn("python scripts/audit_paper_prose.py final_latex/main.tex", text, relative)

    def test_current_paper_fragment_source_must_be_in_active_include_graph(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            final = project / "final_latex"
            (final / "sections").mkdir(parents=True)
            main = final / "main.tex"
            active = final / "sections/q1.tex"
            orphan = final / "sections/orphan.tex"
            main.write_text(r"\documentclass{article}\begin{document}\input{sections/q1}\end{document}", encoding="utf-8")
            active.write_text("active", encoding="utf-8")
            orphan.write_text("orphan", encoding="utf-8")
            framework = project / "模型论文框架.md"
            framework.write_text(
                "### Paper Fragment Dependency Map\n\n"
                "| Fragment ID | 类型 | 范围 | 依赖对象 | 正文/摘要锚点 | LaTeX 源码文件（可选） | 状态 |\n"
                "|---|---|---|---|---|---|---|\n"
                "| paper.q1 | question_model_text | Q1 | Q1.model | x | `final_latex/sections/q1.tex` | current |\n",
                encoding="utf-8",
            )
            findings = self.audit.audit_project(main, framework_path=framework)
            self.assertFalse(any(item.code.startswith("paper_fragment_source_") for item in findings), findings)
            framework.write_text(
                framework.read_text(encoding="utf-8").replace("q1.tex", "orphan.tex"), encoding="utf-8"
            )
            findings = self.audit.audit_project(main, framework_path=framework)
            self.assertTrue(
                any(item.code == "paper_fragment_source_not_in_active_graph" and item.severity == "blocking" for item in findings),
                findings,
            )

    def test_source_bundle_hash_changes_with_child_tex_and_graphic(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sections").mkdir()
            (root / "figures").mkdir()
            main = root / "main.tex"
            child = root / "sections/q1.tex"
            image = root / "figures/a.png"
            main.write_text(
                r"\documentclass{article}\begin{document}\input{sections/q1}\end{document}", encoding="utf-8"
            )
            child.write_text(r"value\includegraphics{figures/a.png}", encoding="utf-8")
            image.write_bytes(b"image-a")
            first = self.delivery.source_bundle_snapshot(main)["source_bundle_sha256"]
            child.write_text(r"value2\includegraphics{figures/a.png}", encoding="utf-8")
            second = self.delivery.source_bundle_snapshot(main)["source_bundle_sha256"]
            self.assertNotEqual(first, second)
            image.write_bytes(b"image-b")
            third = self.delivery.source_bundle_snapshot(main)["source_bundle_sha256"]
            self.assertNotEqual(second, third)

    def test_compile_report_and_sync_detect_post_compile_source_change(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            final = project / "final_latex"
            (final / "sections").mkdir(parents=True)
            main = final / "main.tex"
            child = final / "sections/q1.tex"
            pdf = final / "main.pdf"
            main.write_text(r"\documentclass{article}\begin{document}\input{sections/q1}\end{document}", encoding="utf-8")
            child.write_text("v1", encoding="utf-8")
            pdf.write_bytes(b"pdf-v1")
            report = self.delivery.write_compile_report(
                project=final, main=main, profile="test", engine="xelatex",
                bibliography="none", sequence=["xelatex"],
            )
            self.assertEqual(report["status"], "passed")
            state = {
                "artifacts": {
                    "latex_source": "final_latex/main.tex",
                    "compiled_pdf": "final_latex/main.pdf",
                    "compile_report": "final_latex/compile_report.yaml",
                }
            }
            self.assertEqual(self.sync._compile_artifact_issues(project, state), [])
            child.write_text("v2", encoding="utf-8")
            issues = self.sync._compile_artifact_issues(project, state)
            self.assertTrue(any("source bundle" in item and "stale" in item for item in issues), issues)

    def test_render_paper_is_the_compile_report_producer(self):
        text = (ROOT / "scripts/render_paper.py").read_text(encoding="utf-8")
        self.assertIn("write_compile_report", text)
        self.assertIn("compile_report.yaml", text)


if __name__ == "__main__":
    unittest.main()
'''
    write_new("tests/test_v790_runtime_closure.py", tests)


def final_consistency_edits() -> None:
    # Active docs should describe the automatic report/freshness chain.
    replace_once(
        "packs/artifact/latex.md",
        "- 编译日志无 Error、未定义引用、缺失文献、缺图、字体错误和不可接受的 Overfull box；\n",
        "- `scripts/render_paper.py` 自动生成的 `compile_report.yaml` 为 passed，当前 source bundle/PDF hash 与编译时记录一致；\n- 编译日志无 Error、未定义引用、缺失文献、缺图、字体错误和不可接受的 Overfull box；\n",
    )
    replace_once(
        "PROJECT_INSTRUCTIONS.md",
        "19. 正式模型、代码、返回工作簿和下游交付先执行 `scripts/validate_semantic_governance.py`；正式产物交付再按解析器返回的 scope 执行 `scripts/sync_project.py <project_root> --write --strict --delivery-scope <scope>`；\n",
        "19. 正式模型、代码、返回工作簿和下游交付先执行 `scripts/validate_semantic_governance.py`；正式产物交付再按解析器返回的 scope 执行 `scripts/sync_project.py <project_root> --write --strict --delivery-scope <scope>`；LaTeX/提交 scope 会重算当前 source bundle 并核对 `compile_report` 与 PDF hash；\n",
    )


def restore_temporary_workflow_and_self_remove() -> None:
    workflow = ROOT / ".github/workflows/refresh-generated.yml"
    original = subprocess.check_output(
        ["git", "show", "HEAD^:.github/workflows/refresh-generated.yml"],
        cwd=ROOT,
        text=True,
    )
    workflow.write_text(original, encoding="utf-8")
    Path(__file__).unlink()


def main() -> int:
    update_versions()
    update_runtime_contracts()
    add_fragment_source_validation()
    add_latex_delivery_helper()
    patch_render_and_sync()
    add_regression_tests()
    final_consistency_edits()
    restore_temporary_workflow_and_self_remove()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
