from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OLD = "7.17.0"
NEW = "7.18.0"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one anchor, found {count}: {old!r}")
    return text.replace(old, new, 1)


def bump_simple_carriers() -> None:
    replacements = {
        "core/bootstrap.yaml": (f"skill_version: {OLD}\n", f"skill_version: {NEW}\n"),
        "core/module_manifest.yaml": (f"version: {OLD}\n", f"version: {NEW}\n"),
        "core/workflow_router.yaml": (f"version: {OLD}\n", f"version: {NEW}\n"),
        "core/hsk_core_policy.md": (f"# HSK Core Policy v{OLD}\n", f"# HSK Core Policy v{NEW}\n"),
    }
    for path, (old, new) in replacements.items():
        text = read(path)
        write(path, replace_once(text, old, new, label=path))


def bump_output_contract() -> None:
    path = "core/output_contract.yaml"
    text = read(path)
    text = replace_once(text, f"version: {OLD}\n", f"version: {NEW}\n", label=path)
    anchor = "  solver_justification_contract: core/writing_reasoning_contract.yaml#solver_justification\n"
    addition = anchor + "  model_solution_narrative_contract: core/writing_reasoning_contract.yaml#model_establishment_solution_narrative\n"
    if "model_solution_narrative_contract:" not in text:
        text = replace_once(text, anchor, addition, label=f"{path}:narrative-pointer")
    write(path, text)


def bump_plugin() -> None:
    path = ROOT / ".codex-plugin/plugin.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != OLD:
        raise RuntimeError(f"plugin version is not {OLD}: {data.get('version')!r}")
    data["version"] = NEW
    phrase = "continuous model-establishment/solution narrative with functional transitions, professional headings and result-adjacent interpretation"
    description = str(data.get("description", ""))
    if phrase not in description:
        marker = "optimization model expression closure, "
        if marker not in description:
            raise RuntimeError("plugin description anchor missing")
        description = description.replace(marker, marker + phrase + ", ", 1)
    data["description"] = description
    keywords = list(data.get("keywords", []))
    if "modeling-prose" not in keywords:
        insert_at = keywords.index("paper-writing") + 1 if "paper-writing" in keywords else len(keywords)
        keywords.insert(insert_at, "modeling-prose")
    data["keywords"] = keywords
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def bump_skill_entry(path: str) -> None:
    text = read(path)
    text = replace_once(text, f"version: {OLD}\n", f"version: {NEW}\n", label=f"{path}:frontmatter")
    text = replace_once(
        text,
        f"# HSK 数学建模模块化工作流 v{OLD}\n",
        f"# HSK 数学建模模块化工作流 v{NEW}\n",
        label=f"{path}:heading",
    )
    summary_old = "optimization model expression closure, adaptive Algorithm Trace"
    summary_new = (
        "optimization model expression closure, continuous model-establishment/solution narrative "
        "with functional transitions, professional heading semantics and result-adjacent interpretation, adaptive Algorithm Trace"
    )
    if summary_new not in text:
        text = replace_once(text, summary_old, summary_new, label=f"{path}:summary")

    marker = "核心模型收束按 `required / inline / not_applicable` 自适应；算法流程按 `not_needed / stepwise / pseudocode` 自适应；"
    paragraph = (
        "v7.18 进一步强化**模型建立—模型求解—结果解释的连续数学叙事**：进入具体小问后不重复问题分析、模型假设和题面；"
        "核心关系围绕“当前还缺什么量/判据 → 为什么这样建式 → 关系带来什么结构变化 → 下一步如何使用”自然推进；"
        "solver 必须由真实模型结构、计算困难或已完成的化简自然引出，而不是先写算法百科；"
        "小节标题优先对应对象与独立数学任务，不按决策变量/目标/约束等合同字段机械拆分；"
        "关键最优值、曲线和验证证据在邻近位置解释其决策含义、形成机制和设问结论。"
        "这些规则只约束写作组织，不改变已批准模型、数值事实、Model Approval、03A/03B 或 Workbook/Project State 语义。\n\n"
    )
    if paragraph.strip() not in text:
        text = replace_once(text, marker, paragraph + marker, label=f"{path}:v718-paragraph")
    write(path, text)


def bump_readme() -> None:
    path = "README.md"
    text = read(path)
    text = replace_once(text, f"# mathmodel-skill v{OLD}\n", f"# mathmodel-skill v{NEW}\n", label=f"{path}:heading")
    pipeline_old = "LaTeX 终稿（优化模型表达/算法理由/小节颗粒度/Claim Strength）"
    pipeline_new = "LaTeX 终稿（优化模型表达/连续模型建立与求解叙事/专业标题/结果邻接解释/算法理由/小节颗粒度/Claim Strength）"
    text = replace_once(text, pipeline_old, pipeline_new, label=f"{path}:pipeline")
    section_anchor = f"## v{OLD}：Mechanism Structural Validity Hardening\n"
    new_section = f"""## v{NEW}：Model Establishment & Solution Writing Style Hardening

本版本只强化“模型建立—模型求解—结果解释”的论文叙事和表达，不改变模型数学语义、求解所有权、Model Approval、03A/03B、Workbook Schema、Project State 或运行时 Gate。

- 新增 **Continuous Mathematical Narrative**：模型建立围绕当前对象、下一数学需要、建式依据、关系后果和下游用途连续推进，避免“建立 A 模型—建立 B 模型—采用 C 算法”的报告式拼接。
- 新增 **Formula Prose Rhythm**：核心公式正文按 `Need / Basis / Formula / Meaning / Consequence` 的信息功能闭合，但不要求固定五句话；已定义符号后优先解释公式带来的判据、可行域、目标或计算结构变化。
- 新增 **Transition Function Governance**：衔接句按 `inherit / gap / introduce / transform / solve_entry / result_entry / interpret / increment` 的逻辑功能判断，不维护“首先—其次—因此”连接词模板。
- 新增 **Professional Heading Semantics**：标题按独立数学任务组织，优先恢复“处理哪个对象、完成什么关系/计算动作”；不强制“XX 的 XX”语法，也不把决策变量、目标函数、约束和模型汇总机械拆成多个小节。
- 新增 **Model-to-Solver Bridge**：solver 首次出现前先说明真实模型结构、计算困难、已完成化简或搜索对象，再写本题编码、约束处理、参数/精度/终止条件；算法通用优点不能替代本题理由。
- 新增 **Result-adjacent Interpretation**：单点最优、曲线/图像、算法/精度验证分别使用自适应解释功能，关键结果出现后就近说明决策含义、形成机制、可行性和对设问的回答，不把图表集中堆放后统一“由图可知”。
- 明确模型建立部分默认不重新完整复述问题分析、模型假设或题面，后问只恢复真实继承与新增结构；AI Cleanup 只审计表现风险，不成为第二写作 Authority。
- 规则来源主要抽象自优秀国赛论文的连续论证方法，但 runtime 不包含参考论文名称、固定句式、具体算法、题目专属对象或章节模板。

"""
    if f"## v{NEW}：" not in text:
        text = replace_once(text, section_anchor, new_section + section_anchor, label=f"{path}:section")
    write(path, text)


def bump_changelog() -> None:
    path = "CHANGELOG.md"
    text = read(path)
    anchor = f"## Current release: {OLD}\n\n"
    new_block = f"""## Current release: {NEW}

- Added a single `model_establishment_solution_narrative` writing authority for continuous model-establishment, solution and result-interpretation prose without changing modeling, solver, validator or numerical semantics.
- Added **Continuous Mathematical Narrative** and **Formula Prose Rhythm** so core relations are introduced from the current mathematical need, connected to their basis, and followed by the structural or downstream consequence instead of being presented as disconnected formula blocks.
- Added **Transition Function Governance** based on logical roles (`inherit / gap / introduce / transform / solve_entry / result_entry / interpret / increment`) rather than a connector-word phrase bank.
- Added **Professional Heading Semantics** so question subsections are organized by independent mathematical tasks; generic headings are review risks, while no hard “XX 的 XX” or heading-grammar template is introduced.
- Added **Model-to-Solver Bridge** rules requiring solver choice to emerge from actual model structure, computational difficulty or completed simplification, with problem-specific encoding, constraints, accuracy and termination stated before generic algorithm exposition.
- Added adaptive **Result-adjacent Interpretation** profiles for point optima/parameter sets, curves/figures and algorithm/accuracy/validation evidence; key results should be interpreted near the evidence rather than detached into a final generic paragraph.
- Clarified that model-establishment sections do not repeat full problem analysis, model-assumption lists or prompt restatement, and that later questions write inherited structure plus genuine mathematical/solver increments only.
- Extended AI Cleanup to review report-like model listing, formula-without-purpose, solver-first narrative, generic-heading density, management-only transitions and detached result interpretation while explicitly forbidding keyword-only judgments of mathematical correctness or narrative quality.
- Added v7.18 regression coverage and six-family human prose smoke for mechanism/geometry, continuous optimization, statistics/regression, simple analytic, multi-question progression and result-dense writing.
- Preserved Model Challenge/Human Approval, Numerical Verification/PQS, 03A/03B, Workbook Schema, Project State, runtime routing, user-owned full-fidelity execution and all existing numerical/figure/LaTeX provenance semantics.

## Previous release: {OLD}

"""
    text = replace_once(text, anchor, new_block, label=f"{path}:current-release")
    write(path, text)


def bump_health_test() -> None:
    path = "tests/test_v7141_skill_health.py"
    text = read(path)
    if OLD not in text:
        raise RuntimeError(f"{path}: old release assertions missing")
    text = text.replace(OLD, NEW)
    marker = '        self.assertIn("Claim Strength Calibration", root_skill)\n'
    addition = marker + '        self.assertIn("continuous model-establishment/solution narrative", root_skill)\n'
    if "continuous model-establishment/solution narrative" not in text:
        text = replace_once(text, marker, addition, label=f"{path}:skill-capability")
    marker2 = '        self.assertEqual(\n            writing.get("claim_strength_contract"),\n            "core/writing_reasoning_contract.yaml#claim_strength_calibration",\n        )\n'
    addition2 = marker2 + '        self.assertEqual(\n            writing.get("model_solution_narrative_contract"),\n            "core/writing_reasoning_contract.yaml#model_establishment_solution_narrative",\n        )\n'
    if "model_solution_narrative_contract" not in text:
        text = replace_once(text, marker2, addition2, label=f"{path}:output-pointer")
    write(path, text)


def assert_skill_pair_equal() -> None:
    root = read("SKILL.md")
    packaged = read("skills/mathmodel-skill/SKILL.md")
    if root != packaged:
        raise RuntimeError("root/package SKILL mismatch after release transform")


def main() -> None:
    bump_simple_carriers()
    bump_output_contract()
    bump_plugin()
    bump_skill_entry("SKILL.md")
    bump_skill_entry("skills/mathmodel-skill/SKILL.md")
    bump_readme()
    bump_changelog()
    bump_health_test()
    assert_skill_pair_equal()
    print(f"staged deterministic release transform: {OLD} -> {NEW}")


if __name__ == "__main__":
    main()
