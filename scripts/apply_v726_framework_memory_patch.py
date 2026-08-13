#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT = "7.2.5"
TARGET = "7.2.6"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    if old not in text:
        raise RuntimeError(f"expected snippet not found in {path}: {old[:120]!r}")
    write(path, text.replace(old, new, 1))


def replace_all(path: str, old: str, new: str) -> None:
    text = read(path)
    if old not in text:
        raise RuntimeError(f"expected token not found in {path}: {old!r}")
    write(path, text.replace(old, new))


VERSION_FILES = [
    ".codex-plugin/plugin.json",
    "SKILL.md",
    "skills/mathmodel-skill/SKILL.md",
    "README.md",
    "core/bootstrap.yaml",
    "core/code_quality_contract.yaml",
    "core/global_preprocessing_contract.yaml",
    "core/hsk_core_policy.md",
    "core/module_manifest.yaml",
    "core/output_contract.yaml",
    "core/project_state.schema.yaml",
    "core/user_execution_contract.yaml",
    "core/workflow_router.yaml",
    "scripts/README.md",
    "scripts/lint_skill.py",
    "scripts/resolve_workflow.py",
    "legacy/README.md",
    "tests/test_schemas.py",
    "tests/test_v701_stage_boundary_closure.py",
]

for path in VERSION_FILES:
    replace_all(path, CURRENT, TARGET)

# Plugin metadata: surface the new project-memory role without changing interfaces.
replace_once(
    ".codex-plugin/plugin.json",
    "code-quality enforcement and LaTeX-first authoring.",
    "code-quality enforcement, assistant-readable model-paper project memory and LaTeX-first authoring.",
)
replace_once(
    ".codex-plugin/plugin.json",
    "题意冻结、条件式预处理、论文数学证据、data_process图、双阶段Python、LaTeX直写",
    "题意冻结、框架项目记忆、条件式预处理、data_process图、双阶段Python、LaTeX直写",
)

# Bootstrap: make context recovery a hard invariant.
replace_once(
    "core/bootstrap.yaml",
    "- locked_model_spec形成后维护项目根目录当前版模型论文框架.md；旧版本由Git历史保存。",
    "- locked_model_spec形成后维护项目根目录当前版模型论文框架.md；旧版本由Git历史保存。\n"
    "- 模型论文框架.md不仅是交付给用户的可读文档，也是助手跨阶段、跨聊天恢复当前项目上下文的首选语义记忆；只要框架存在且current，后续预处理、求解、深化分析、绘图、写作和终审都应在执行前按需读取相关段落，不得只依赖聊天记忆重建当前模型。\n"
    "- 模型论文框架.md保存当前有效语义、结果摘要和证据位置，但不替代数值事实源与机器状态：具体数值必须回到已验收工作簿复核，semantic revision、hash与stale以project state为准。",
)

# Core policy: authoritative project-memory semantics.
policy_marker = "## 3. 数据审计、条件式预处理与论文证据"
policy_insert = """### 2.5 项目工作记忆与上下文恢复\n\n`模型论文框架.md` 同时承担当前项目的**助手可读工作记忆**。它不是只给用户查看的交付说明，而是在模型锁定以后，把长上下文中最容易丢失的题意口径、数据角色、`preprocessing_decision`、变量/参数/假设、核心公式与约束、小问依赖、当前算法语义、结果摘要、验证边界、图表证据位置和论文组织压缩为一份可再次读取的当前态文档。\n\n执行现有项目时采用 **read-before-use / write-after-change**：\n\n1. 框架存在且 `current` 时，继续预处理、主求解、结果深化、绘图或单问修改前，优先读取“当前有效口径”、目标小问的当前模型/结果区和必要跨问依赖，不得仅凭聊天记忆恢复模型；\n2. 新聊天接续、长上下文恢复、整篇 DOCX/LaTeX 写作、跨问综合和终审时读取完整 current 框架；日常单问工作允许定向读取相关段落，避免无差别加载整份文件；\n3. 题意、数据口径、参数、假设、目标、约束、预处理、算法语义或依赖变化后，先按 semantic governance 处理 stale，再重写框架中的受影响当前内容；主结果、深化结果或图表验收后同步结果摘要和证据位置；\n4. 框架只保留当前有效版本，不保存历史流水账；历史仍由 Git 保存；\n5. 框架不是数值数据库。需要写入论文、比较算法或生成图表的具体数字必须回到已验收的标准工作簿复核；`state/project_state.yaml` 继续负责 semantic revision、hash、依赖和 stale。\n\n因此，框架的作用是“当前语义索引 + 项目记忆 + 写作骨架”，工作簿是数值事实源，project state 是机器状态源；三者职责互补而不互相替代。\n\n"""
text = read("core/hsk_core_policy.md")
if policy_marker not in text:
    raise RuntimeError("core policy insertion marker missing")
write("core/hsk_core_policy.md", text.replace(policy_marker, policy_insert + policy_marker, 1))

# Workflow router: single machine-readable project-memory contract.
router_marker = "- core/global_preprocessing_contract.yaml\nclassification_contract:"
router_block = """- core/global_preprocessing_contract.yaml\nproject_memory_contract:\n  artifact: model_paper_framework\n  project_file: 模型论文框架.md\n  activation: locked_model_spec exists and current framework is available\n  purpose: assistant-readable current project semantic memory for context recovery across stages and chats\n  read_before_modules: [data_preprocessing, solve_validate, result_analysis, figure_evidence, writing_docx, writing_latex, review_delivery]\n  targeted_read_sections: [当前有效口径, relevant_subproblem, required_dependencies, relevant_result_summary, 待办与缺口]\n  full_read_when: [cross_chat_handoff, long_context_recovery, full_paper_writing, cross_question_synthesis, final_review]\n  numeric_fact_source: accepted_standard_workbooks\n  machine_state_source: state/project_state.yaml\n  rules:\n  - Prefer the current framework over reconstructing current model semantics from chat memory.\n  - Use targeted section reads for ordinary single-question continuation; do not preload the whole framework without need.\n  - Use the full current framework for full-paper writing, cross-question synthesis, handoff and final review.\n  - Verify concrete numerical claims against accepted workbooks; framework result summaries are a navigation and context layer, not the numerical source of truth.\n  - If the framework is stale or conflicts with project state/workbooks, repair the upstream semantic/result state before downstream use.\n  - Synchronize affected framework sections after semantic changes and after accepted primary results, result analysis or figure evidence.\nclassification_contract:"""
replace_once("core/workflow_router.yaml", router_marker, router_block)
replace_once(
    "core/workflow_router.yaml",
    "  - Reuse current project state, framework and artifacts before recomputing.",
    "  - Reuse current project state, framework and artifacts before recomputing; when a current 模型论文框架.md exists, apply project_memory_contract and read the relevant sections before downstream work.",
)

# Module manifest: clarify artifact role without duplicating the router rules.
replace_once(
    "core/module_manifest.yaml",
    "  model_paper_framework: 当前有效模型语义、Problem Contract、预处理判定与论文证据、论文组织、逐问结果摘要和图表映射",
    "  model_paper_framework: 助手可再次读取的当前项目语义记忆与论文骨架；保存Problem Contract、预处理判定、模型语义、逐问结果摘要和图表映射，具体数值仍以已验收工作簿为准，读取策略以core/workflow_router.yaml#project_memory_contract为准",
)

# Stable runtime / agent entrypoints.
replace_once(
    "AGENTS.md",
    "4. Create or update project-root `模型论文框架.md` after the model is locked; keep only current semantics.",
    "4. Create or update project-root `模型论文框架.md` after the model is locked; keep only current semantics. Treat it as assistant-readable project memory, not merely a user-facing deliverable: when it exists and is current, read the relevant current-scope/subproblem/dependency/result/figure sections before downstream work instead of reconstructing the model from chat memory; read the full framework for cross-chat recovery, full-paper writing and final review. Concrete numerical claims still require accepted-workbook verification, while project state owns hashes and stale status.",
)
replace_once(
    "PROJECT_INSTRUCTIONS.md",
    "5. `locked_model_spec` 形成后维护项目根目录 `模型论文框架.md`，只保留当前有效语义，历史由 Git 保存；",
    "5. `locked_model_spec` 形成后维护项目根目录 `模型论文框架.md`，只保留当前有效语义，历史由 Git 保存；该文件同时是助手的项目级工作记忆：已有 current 框架时，继续预处理、求解、深化分析、绘图和写作前优先按需读取相关段落，跨聊天/整篇写作/终审时读取完整框架，不得只依赖聊天记忆重建当前模型；具体数值仍回到已验收工作簿复核，hash/stale 仍以 project state 为准；",
)
runtime_marker = "## 概念上的完整工作流"
runtime_insert = """## 项目工作记忆\n\n`模型论文框架.md` 不是只给用户查看的输出文件。模型锁定后，它是助手恢复当前项目上下文的首选入口：保存当前题意口径、数据与预处理决策、变量/参数/假设、模型与约束、小问依赖、结果摘要、验证边界、图表映射和论文组织。\n\n- 普通单问继续：读取“当前有效口径”+对应 Q 区+必要依赖/结果摘要；\n- 参数、约束、模型、预处理或算法口径修改：先读当前相关段落，再修改并同步受影响内容；\n- 结果验收/深化分析/绘图完成：把 current 结果摘要与证据位置写回框架；\n- 新聊天接续、长上下文恢复、整篇论文写作和终审：读取完整 current 框架；\n- 具体数值必须再核对标准工作簿；semantic revision、hash 和 stale 以 `state/project_state.yaml` 为准。\n\n框架 stale 或与工作簿/状态冲突时，不得把聊天记忆当作仲裁依据，应回到对应上游阶段修正。\n\n"""
text = read("RUNTIME_ROUTER.md")
if runtime_marker not in text:
    raise RuntimeError("runtime router marker missing")
write("RUNTIME_ROUTER.md", text.replace(runtime_marker, runtime_insert + runtime_marker, 1))

# Skill entry: make the behavior visible to every routed task.
skill_insert_marker = "### 数据阶段硬规则"
skill_memory = """### `模型论文框架.md` 是项目工作记忆\n\n`locked_model_spec` 形成后，项目根目录 `模型论文框架.md` 不只是交付给用户查看的框架文件，也是助手跨阶段、跨聊天恢复当前项目语义的首选入口。已有 current 框架时，后续预处理、求解、深化分析、绘图和写作应先按需读取相关段落；单问继续优先读取当前有效口径、对应小问和必要依赖，整篇论文、跨问综合、长上下文恢复与终审读取完整框架。不得仅依赖聊天记忆重新拼接已锁定模型。\n\n框架负责当前语义、结果摘要和证据导航；具体数值必须回到已验收工作簿复核，semantic revision、hash 和 stale 继续由 `state/project_state.yaml` 管理。模型/参数/约束/预处理/算法语义变化后，以及主结果、深化结果、图表验收后，都要同步受影响的当前框架内容。\n\n"""
for path in ("SKILL.md", "skills/mathmodel-skill/SKILL.md"):
    text = read(path)
    if skill_insert_marker not in text:
        raise RuntimeError(f"skill marker missing: {path}")
    write(path, text.replace(skill_insert_marker, skill_memory + skill_insert_marker, 1))

# Model design: define read-before-use/write-after-change behavior at framework creation point.
replace_once(
    "modules/02_model_design.md",
    "`locked_model_spec` 形成后，以 `templates/model/model_paper_framework.md` 为骨架在项目根目录创建 `模型论文框架.md`。它承担当前模型语义、Problem Contract、三层闭环、复杂度复审、论文组织、命题规划、逐问结果摘要和图表映射，不承担历史日志。",
    "`locked_model_spec` 形成后，以 `templates/model/model_paper_framework.md` 为骨架在项目根目录创建 `模型论文框架.md`。它承担当前模型语义、Problem Contract、三层闭环、复杂度复审、论文组织、命题规划、逐问结果摘要和图表映射，不承担历史日志。除此之外，它还是助手的**项目级长期工作记忆**：把长上下文中最容易遗失、但后续求解与写作必须保持一致的当前信息压缩在一处，供后续阶段和新聊天再次读取。",
)
replace_once(
    "modules/02_model_design.md",
    "- `full`：跨聊天交接、DOCX/LaTeX、终审和提交，增加论文整体框架、命题与证明规划、综合检验与跨问结论、同步检查。\n\n写入规则：",
    "- `full`：跨聊天交接、DOCX/LaTeX、终审和提交，增加论文整体框架、命题与证明规划、综合检验与跨问结论、同步检查。\n\n读取规则：\n\n1. 已有项目且框架为 `current` 时，继续某一问前优先读取“当前有效口径”、该问的“当前模型口径/结果摘要”和必要 `data / parameter / model / result` 依赖；不得只凭聊天记忆复原当前模型；\n2. 普通单问迭代采用定向读取，不要求每次把整份大框架全部载入上下文；\n3. 新聊天接续、上下文过长需要恢复、跨问综合、DOCX/LaTeX 整篇写作和终审时读取完整 current 框架；\n4. 框架若为 `stale`，先依据 project state 与已验收产物修正，不能把 stale 内容继续当作当前语义；\n5. 具体数值回到标准工作簿核验，框架结果摘要用于上下文恢复、导航和写作组织，不替代数值事实源。\n\n写入规则：",
)

# Downstream modules explicitly consume the current framework before acting.
replace_once(
    "modules/03_data_preprocessing.md",
    "> 本模块只执行已经判定为 `project_level` 的公共数据处理。是否需要预处理、缺失如何处理、是否允许插值/预测填补，以及论文证据和预处理图证据的详细要求，以 `core/global_preprocessing_contract.yaml` 为唯一权威事实源。",
    "> 本模块只执行已经判定为 `project_level` 的公共数据处理。是否需要预处理、缺失如何处理、是否允许插值/预测填补，以及论文证据和预处理图证据的详细要求，以 `core/global_preprocessing_contract.yaml` 为唯一权威事实源。\n> 若项目根目录已有 current `模型论文框架.md`，进入本模块前先读取全局数据协议、`preprocessing_decision`、相关小问依赖和当前模型输入要求；不得脱离框架重新凭聊天记忆定义公共数据口径。",
)
replace_once(
    "modules/03_solve_validate.md",
    "本模块在 `问题X求解/` 中生成 `问题X求解.py`。助手只生成和静态检查，不运行赛题代码。\n\n进入本模块前，当前小问必须先通过 `scripts/validate_semantic_governance.py`：",
    "本模块在 `问题X求解/` 中生成 `问题X求解.py`。助手只生成和静态检查，不运行赛题代码。\n\n若项目根目录已有 current `模型论文框架.md`，正式生成本问代码前必须先读取“当前有效口径”、本问“当前模型口径/求解与验证方案”以及必要前问依赖，用它恢复当前模型语义；不得仅凭聊天记忆重建变量、参数、目标或约束。具体输入数值和已验收结果仍回到当前数据事实源/标准工作簿核验。\n\n进入本模块前，当前小问必须先通过 `scripts/validate_semantic_governance.py`：",
)
replace_once(
    "modules/03_result_analysis.md",
    "本模块只接受已验收的主工作簿。根据真实主结果选择参数敏感性、场景压力、多算法/多初值、结构稳健性、阈值、异质性、误差分解或外样本稳定性。",
    "本模块只接受已验收的主工作簿。根据真实主结果选择参数敏感性、场景压力、多算法/多初值、结构稳健性、阈值、异质性、误差分解或外样本稳定性。若 current `模型论文框架.md` 已存在，制定分析计划前先读取本问当前模型、验证方案、主结果摘要、适用/失效边界和跨问依赖，再用已验收主工作簿复核具体数值；不得脱离框架按聊天印象选择分析对象。",
)
replace_once(
    "modules/04_figure_evidence.md",
    "## 正确顺序\n\n1. 继承已经锁定的 `preprocessing_decision`；",
    "## 正确顺序\n\n进入本模块时先读取 current `模型论文框架.md` 中的当前有效口径、相关小问结果摘要、待办缺口和既有图表映射，用于确定“哪些结论需要图证据”；随后再从真实工作簿读取具体数值和底层序列。不得仅凭聊天记忆或框架摘要数字反推图数据。\n\n1. 继承已经锁定的 `preprocessing_decision`；",
)
replace_once(
    "modules/05_writing/latex.md",
    "写作前读取框架中的当前模型、`preprocessing_decision`、预处理方法与证据、主结果、分析方法选择理由、稳定范围、失效边界和图表映射，再从实际工作簿复核数值。不得根据聊天记忆恢复框架已删除的旧模型、旧预处理、旧结果或旧分析。",
    "整篇 LaTeX 写作前必须读取完整 current `模型论文框架.md`，以其中的当前模型、`preprocessing_decision`、预处理方法与证据、主结果摘要、分析方法选择理由、稳定范围、失效边界、跨问关系和图表映射恢复项目上下文，再从实际工作簿复核具体数值。不得根据聊天记忆恢复框架已删除的旧模型、旧预处理、旧结果或旧分析，也不得把框架中的摘要数字当作免复核的数值事实。",
)

# Framework template itself: state its assistant-memory purpose and repair the last active legacy path.
replace_once(
    "templates/model/model_paper_framework.md",
    "> 本文件只保留当前有效口径。题意解释、模型、参数、约束、数据处理、算法、命题、证明、结果或图表发生变化时，直接替换受影响内容并删除旧版本；历史由 Git 保存。",
    "> 本文件只保留当前有效口径。题意解释、模型、参数、约束、数据处理、算法、命题、证明、结果或图表发生变化时，直接替换受影响内容并删除旧版本；历史由 Git 保存。\n> 本文件同时是助手的项目级长期工作记忆：后续预处理、求解、结果深化、绘图和单问修改可按需读取相关段落，新聊天接续、长上下文恢复、整篇论文写作和终审应读取完整 current 框架。\n> 事实源边界：框架保存当前语义、结果摘要和证据位置；具体数值必须回到已验收标准工作簿复核，semantic revision、hash 与 stale 以 `state/project_state.yaml` 为准。",
)
replace_all(
    "templates/model/model_paper_framework.md",
    "敏感性与鲁棒性工作簿",
    "结果深化分析工作簿",
)
replace_all(
    "templates/model/model_paper_framework.md",
    "`结果数据表/问题一/q1_plot.m`",
    "`问题一求解/q1_plot.m`",
)

# Changelog: preserve 7.2.5 history and add the new current release.
changelog_old = "# Changelog\n\n## Current release: 7.2.5\n"
changelog_new = """# Changelog\n\n## Current release: 7.2.6\n\n- Repositioned project-root `模型论文框架.md` as assistant-readable project memory in addition to a user-visible modeling/paper artifact, so current semantics can be recovered across long contexts and new chats without reconstructing the model from conversation history.\n- Added a router-level `project_memory_contract` with targeted reads for ordinary single-question continuation and full reads for cross-chat recovery, full-paper writing, cross-question synthesis and final review.\n- Added explicit read-before-use rules to project-level preprocessing, primary solving, result analysis, Figure Evidence and LaTeX writing; downstream stages must consult the current framework before acting when it exists.\n- Kept source-of-truth boundaries strict: accepted workbooks remain the numerical fact source and project state remains the semantic-revision/hash/stale source; framework summaries are context, navigation and writing memory rather than a replacement database.\n- Added write-after-change synchronization requirements for semantic changes, accepted primary/results-analysis outputs and locked figure evidence, while continuing to keep only the current framework version and using Git for history.\n- Removed the remaining active legacy `结果数据表/问题一/q1_plot.m` path from the framework template and renamed its generic sensitivity/robustness evidence row to the current result-analysis workbook terminology.\n- Added regression coverage for the framework project-memory contract without changing the existing three-state preprocessing API or per-question five-file interface.\n\n## Previous release: 7.2.5\n"""
replace_once("CHANGELOG.md", changelog_old, changelog_new)

# New regression test: behavior, source-of-truth boundaries and template path hygiene.
test_path = ROOT / "tests" / "test_framework_project_memory_contract.py"
test_path.write_text(
    '''from __future__ import annotations\n\nimport unittest\nfrom pathlib import Path\n\nimport yaml\n\nROOT = Path(__file__).resolve().parents[1]\n\n\ndef read(relative: str) -> str:\n    return (ROOT / relative).read_text(encoding="utf-8")\n\n\nclass FrameworkProjectMemoryContractTests(unittest.TestCase):\n    def test_router_declares_project_memory_contract(self) -> None:\n        router = yaml.safe_load(read("core/workflow_router.yaml"))\n        contract = router.get("project_memory_contract", {})\n        self.assertEqual(contract.get("artifact"), "model_paper_framework")\n        self.assertEqual(contract.get("project_file"), "模型论文框架.md")\n        self.assertEqual(contract.get("numeric_fact_source"), "accepted_standard_workbooks")\n        self.assertEqual(contract.get("machine_state_source"), "state/project_state.yaml")\n        modules = set(contract.get("read_before_modules", []))\n        for required in {"data_preprocessing", "solve_validate", "result_analysis", "figure_evidence", "writing_latex", "review_delivery"}:\n            self.assertIn(required, modules)\n        self.assertIn("cross_chat_handoff", contract.get("full_read_when", []))\n        self.assertIn("full_paper_writing", contract.get("full_read_when", []))\n\n    def test_downstream_modules_explicitly_read_framework(self) -> None:\n        checks = {\n            "modules/03_data_preprocessing.md": "先读取全局数据协议",\n            "modules/03_solve_validate.md": "正式生成本问代码前必须先读取",\n            "modules/03_result_analysis.md": "制定分析计划前先读取",\n            "modules/04_figure_evidence.md": "进入本模块时先读取 current `模型论文框架.md`",\n            "modules/05_writing/latex.md": "必须读取完整 current `模型论文框架.md`",\n        }\n        for relative, marker in checks.items():\n            self.assertIn(marker, read(relative), relative)\n\n    def test_framework_is_memory_not_numeric_database(self) -> None:\n        for relative in ("core/bootstrap.yaml", "core/hsk_core_policy.md", "PROJECT_INSTRUCTIONS.md", "SKILL.md"):\n            text = read(relative)\n            self.assertIn("模型论文框架.md", text, relative)\n        policy = read("core/hsk_core_policy.md")\n        self.assertIn("read-before-use / write-after-change", policy)\n        self.assertIn("工作簿是数值事实源", policy)\n        self.assertIn("project state 是机器状态源", policy)\n\n    def test_framework_template_declares_memory_role_and_current_paths(self) -> None:\n        template = read("templates/model/model_paper_framework.md")\n        self.assertIn("助手的项目级长期工作记忆", template)\n        self.assertIn("`问题一求解/q1_plot.m`", template)\n        self.assertNotIn("`结果数据表/问题一/q1_plot.m`", template)\n        self.assertIn("结果深化分析工作簿", template)\n\n    def test_agent_entry_uses_framework_for_context_recovery(self) -> None:\n        text = read("AGENTS.md")\n        self.assertIn("assistant-readable project memory", text)\n        self.assertIn("instead of reconstructing the model from chat memory", text)\n\n\nif __name__ == "__main__":\n    unittest.main()\n''',
    encoding="utf-8",
)

print("v7.2.6 framework project-memory patch applied")
