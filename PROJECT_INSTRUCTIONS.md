# HSK 项目调用说明

当前活动规则以 `core/bootstrap.yaml` 指向的权威文件为准。本文件只提供调用顺序和稳定摘要，不复制各合同的完整字段。

1. 首先读取 `core/bootstrap.yaml`；
2. 使用 `scripts/resolve_workflow.py` 解析一个或多个意图，只加载命中的模块、Pack 和模板；
3. 每问按 `classification.objective`、`classification.structures` 和顶层 `capabilities` 分类；
4. Module 01 先冻结 Problem Contract；Module 02 再完成模型路线选择、语义闭环、Complexity Sanity 与 `preprocessing_decision`，形成 `proposed_model_spec` 后执行相互独立的 Model Reviewer 与 Devil's Advocate。Challenge 通过后生成 Model Approval Brief，并停在 `awaiting_model_approval`；只有用户明确批准当前 `semantic_revision/hash` 后才形成 current `locked_model_spec`，不得把 Problem Contract 冻结、Challenge 通过或用户未反对等价为已锁模；
5. `proposed_model_spec` 形成后即可维护项目根目录 `模型论文框架.md`。框架只保留当前项目事实与选择，包括 Formula Trace、Algorithm Trace、Model Challenge/Human Approval 当前状态、参数证据、Terminology Registry、Numeric Profile、Title Claim、命题、Citation Evidence、Paper Fragment Dependency Map、深化证据处置、结果摘要与图表映射；历史由 Git 保存。已有 current 框架时，继续预处理、求解、深化分析、绘图和写作前优先按需读取相关段落；跨聊天/整篇写作/终审读取完整框架；具体数值回到已验收工作簿复核，semantic revision/hash、challenge/approval 与 stale 以 project state 为准；
6. 所有数据题都先做非破坏性审计，但只有 `preprocessing_decision=project_level` 时创建 `数据预处理/`；`not_needed` 直接使用原始数据，`question_local` 仅在对应小问 Python 中执行有数学来源的局部变换；
7. `project_level` 时，只有 current Model Challenge passed 且 Human Model Approval 与当前 `semantic_revision/hash` 完全一致后，才允许交付并由用户本地 full-fidelity 运行 `数据预处理/数据预处理.py`；验收 `数据预处理结果.xlsx` 后才进入依赖主求解。主求解代码同样不得绕过 `scripts/validate_semantic_governance.py` 与 `scripts/validate_model_approval.py`；`data_process.m` 在后续 Figure Evidence 阶段生成，不是主求解前置；
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
14. 默认写作链为 Figure Evidence → LaTeX → AI cleanup → prose/BibTeX/framework audit → 编译质量检查；DOCX 仅在用户明确要求 Word 审阅、批注、协作或特定提交格式时加载，不是 LaTeX 前置；
15. 写作治理以两个 Authority 收口：`core/writing_reasoning_contract.yaml` 管理 Formula Trace、Algorithm Trace 与 `not_needed / stepwise / pseudocode`、Hard / Default / Recommendation、命题预算、Terminology、Numeric Style、Title Claim、深化证据处置、Paragraph Necessity、Paper Fragment stale 与 Citation Evidence；`modules/05_writing/latex.md` 管理正文结构与表达。`packs/artifact/algorithm_flow.md` 和命题 Pack 只提供按需呈现细则，DOCX、AI cleanup、review、Artifact Packs 和检查表只消费 Authority，不得重新定义第二套正文规则；
16. Algorithm Trace 仅在 `stepwise/pseudocode` 时建立，闭合“模型结构/公式/命题/约束 → 论文算法流程 → 真实 Python 实现 → 工作簿结果或验证证据”；`not_needed` 不为版式完整生成装饰性 Algorithm 1；
17. 核心模型收束按 `required / inline / not_applicable` 自适应；命题 0--4 是默认正文阅读预算而非 Hard 上限，P5+ 可在必要性审查和 justification 后保留；优点和缺点没有强制数量关系；需要外部证据的核心 claim 通过 Citation Evidence 连接正文位置与 `references.bib`；
18. AI cleanup 后正式 LaTeX 审计统一运行 `scripts/audit_latex_project.py`；它递归展开模块化源码并委托 `audit_paper_prose.py` 做 prose/BibTeX/framework 检查。确定性 Hard 错误为 blocking，Default 偏离为 review_required，Recommendation/风格风险为 warning；机器不得从正则判断数学/算法正确性、参数最优性、术语语义等价或 citation 的语义支持关系；
19. 正式交付统一执行 resolver 当前返回的全部 `pre_delivery_gates`，并严格保持返回顺序；不得在入口文档维护第二套 gate 固定清单。`semantic_governance`、`model_approval`、`project_sync`、`submission_package_validation` 等 gate 只有在当前 plan 返回时才执行；其中 `model_approval` 只在项目级预处理或主求解等需 current 人工锁模的阶段出现，`project_sync` 按 resolved scope 重算/同步当前产物，LaTeX/提交 scope 会核对 source bundle、`compile_report` 与 PDF hash，`submission_package_validation` 对当前 submission manifest、ZIP 内容与绑定哈希做最终包级验证；
20. `project_sync` 只发现产物、校验 Schema、计算哈希和传播 stale，不生成模型语义、数值结果或 passed 状态；
21. `run_info.json`、`result_manifest.yaml`、`matlab_figure_handoff.json` 只在用户明确要求完整复现包时生成，并放在项目级内部元数据目录，不得进入 `问题X求解/` 或 `数据预处理/`；
22. 旧 `结果数据表/问题X/`、旧敏感性与鲁棒性工作簿以及 v6.6 单脚本四文件目录只作历史项目只读兼容，新项目不得按旧结构生成；
23. 命题证明 Pack 仅在明确需要证明或当前命题规划非零时加载；算法流程 Pack 通常只在明确算法流程请求或当前写作/终审需要消费 `stepwise/pseudocode` Algorithm Trace 时加载；`full_workflow` 因代表完整论文/全套成果，可保留这个小型 Pack 跨用户执行边界，避免后续论文阶段漏读，普通 `full_solution / code_and_solution` 不预加载；
24. 中文国赛终稿保留 `cumcmthesis`。

活动入口使用稳定文件名：`PROJECT_INSTRUCTIONS.md`、`RUNTIME_ROUTER.md`、`SKILL_FILE_INDEX.md` 和 `TEMPLATE_INDEX.md`。旧版本化入口只保留兼容指针，不承载活动规则，也不进入 Active Skill Index/Active MANIFEST；默认 resolver 不加载它们。
