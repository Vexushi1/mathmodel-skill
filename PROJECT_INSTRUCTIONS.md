# HSK 项目调用说明

当前活动规则以 `core/bootstrap.yaml` 指向的权威文件为准。本文件只提供调用顺序和稳定摘要，不复制各合同的完整字段。

1. 首先读取 `core/bootstrap.yaml`；
2. 使用 `scripts/resolve_workflow.py` 解析一个或多个意图，只加载命中的模块、Pack 和模板；
3. 每问按 `classification.objective`、`classification.structures` 和顶层 `capabilities` 分类；
4. Module 01 先冻结 Problem Contract，Module 02 再锁定模型语义、复杂度复审和 `preprocessing_decision`；
5. `locked_model_spec` 形成后维护项目根目录 `模型论文框架.md`，只保留当前有效语义，历史由 Git 保存；该文件同时是助手的项目级工作记忆：已有 current 框架时，继续预处理、求解、深化分析、绘图和写作前优先按需读取相关段落，跨聊天/整篇写作/终审时读取完整框架，不得只依赖聊天记忆重建当前模型；具体数值仍回到已验收工作簿复核，hash/stale 仍以 project state 为准；
6. 所有数据题都先做非破坏性审计，但只有 `preprocessing_decision=project_level` 时创建 `数据预处理/`；`not_needed` 直接使用原始数据，`question_local` 仅在对应小问 Python 中执行有数学来源的局部变换；
7. `project_level` 时先交付并由用户本地 full-fidelity 运行 `数据预处理/数据预处理.py`，验收 `数据预处理结果.xlsx` 后才进入依赖主求解；`data_process.m` 在后续 Figure Evidence 阶段生成，不是主求解前置；
8. 每问数值阶段最终默认恰好保留五个文件：

```text
问题X求解/
├─ 问题X求解.py
├─ 问题X求解结果.xlsx
├─ 问题X结果深化分析.py
├─ 问题X结果深化分析.xlsx
└─ qX_plot.m
```

9. `问题X求解.py` 只负责主求解；用户返回的主工作簿 accepted 后冻结该脚本；
10. 主工作簿通过质量门后，单独生成 `问题X结果深化分析.py`，读取当前数据事实源和已验收主结果，输出 `问题X结果深化分析.xlsx`；不得为了深化分析覆盖改写主求解脚本；
11. 实际赛题的预处理、主求解和深化分析 Python 默认由用户本地 full-fidelity 运行；助手只生成、静态检查并验收返回工作簿，不自动降采样、粗网格、缩短时域、减少重复、放宽容差或静默切换求解器；
12. Python 不生成论文结果图；MATLAB 在 Figure Evidence 阶段读取真实工作簿和精确表头绘图，不重新预处理或求解；
13. `project_level` 的公共预处理证据图脚本固定为 `数据预处理/data_process.m`；各问结果图脚本固定为同目录 `qX_plot.m`；默认只保留可见图窗，不自动创建图表子目录或批量导出；
14. 默认写作链为 Figure Evidence → LaTeX → AI cleanup → prose audit → 编译质量检查；DOCX 仅在用户明确要求 Word 审阅、批注、协作或特定提交格式时加载，不是 LaTeX 前置；
15. DOCX、LaTeX 和 AI cleanup 的正文表达统一读取 `modules/05_writing/latex.md` 中“正文表达与章节组织协议（写作权威）”。中文国赛问题重述默认采用“问题背景 + 问题提出”，问题提出按“问题一：”“问题二：”逐问转述；问题分析逐问说明难点、对象关系、跨问依赖和建模抓手且不写公式/结果；每问详细推导后设置“核心模型汇总”，主结果放在本问“求解结果”小节，深化证据按真实方法命名，默认不再设置固定“小问结论”或全文独立“结论”章；正文核心图表必须有邻近编号引用和解释；短证明默认自然分段，仅多阶段证明使用 2--6 个编号步骤；语言以正向连续叙述为主，不把科研初学者式写成频繁否定、自我辩护或免责声明；完成清理后运行 `scripts/audit_paper_prose.py`，warning 供人工复查，最终编译前 `--strict` 不得保留结构性 `review_required`；
16. 正式模型、代码、返回工作簿和下游交付先执行 `scripts/validate_semantic_governance.py`；正式产物交付再按解析器返回的 scope 执行 `scripts/sync_project.py <project_root> --write --strict --delivery-scope <scope>`；
17. `project_sync` 只发现产物、校验 Schema、计算哈希和传播 stale，不生成模型语义、数值结果或 passed 状态；
18. `run_info.json`、`result_manifest.yaml`、`matlab_figure_handoff.json` 只在用户明确要求完整复现包时生成，并放在项目级内部元数据目录，不得进入 `问题X求解/` 或 `数据预处理/`；
19. 旧 `结果数据表/问题X/`、旧敏感性与鲁棒性工作簿以及 v6.6 单脚本四文件目录只作历史项目只读兼容，新项目不得按旧结构生成；
20. 命题证明详细 Pack 仅在明确需要证明或当前命题规划非零时加载；
21. 中文国赛终稿保留 `cumcmthesis`。

活动入口使用稳定文件名：`PROJECT_INSTRUCTIONS.md`、`RUNTIME_ROUTER.md`、`SKILL_FILE_INDEX.md` 和 `TEMPLATE_INDEX.md`。旧版本化入口只保留兼容指针，不承载活动规则，也不进入 Active Skill Index/Active MANIFEST；默认 resolver 不加载它们。