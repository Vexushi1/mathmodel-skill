---
name: mathmodel-skill
version: 7.5.0
summary: HSK mathematical-modeling workflow with Problem Contract freezing, semantic closure, generalized evidence-driven conditional preprocessing, substantive preprocessing paper evidence, dedicated data_process MATLAB figures, dynamic evidence-driven MATLAB layouts and high-contrast scientific palettes, dependency-aware stale propagation, full-fidelity solving, separate primary/result-analysis Python stages, affirmative evidence-driven CUMCM writing, paragraph-first proposition proofs, final prose audit and LaTeX-first writing.
triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 数据预处理, Python求解, MATLAB绘图, LaTeX, DOCX]
---

# HSK 数学建模模块化工作流 v7.5.0

1. 从本目录定位仓库根目录 `../..`，读取 `../../core/bootstrap.yaml`；
2. 使用 `../../scripts/resolve_workflow.py` 获取任务执行计划；
3. 正式模型与代码前先完成 Problem Contract、当前附件的非破坏性通用数据审计、`preprocessing_decision`、题面—数学—代码语义闭环和 Complexity Sanity Check，并运行 `../../scripts/validate_semantic_governance.py`；

### `模型论文框架.md` 是项目工作记忆

`locked_model_spec` 形成后，项目根目录 `模型论文框架.md` 不只是交付给用户查看的框架文件，也是助手跨阶段、跨聊天恢复当前项目语义的首选入口。已有 current 框架时，后续预处理、求解、深化分析、绘图和写作应先按需读取相关段落；单问继续优先读取当前有效口径、对应小问和必要依赖，整篇论文、跨问综合、长上下文恢复与终审读取完整框架。不得仅依赖聊天记忆重新拼接已锁定模型。

框架负责当前语义、结果摘要和证据导航；具体数值必须回到已验收工作簿复核，semantic revision、hash 和 stale 继续由 `state/project_state.yaml` 管理。模型/参数/约束/预处理/算法语义变化后，以及主结果、深化结果、图表验收后，都要同步受影响的当前框架内容。

### 数据阶段硬规则

4. `preprocessing_decision` 只有三种：`not_needed`、`question_local`、`project_level`。共享同一原始数据源、检测到缺失值或某类赛题过去常见处理本身都不是 `project_level` 的充分条件；
5. 只有 `project_level` 才创建 `数据预处理/`；最终标准文件为 `数据预处理.py`、`数据预处理结果.xlsx` 和 `data_process.m`。`not_needed` 直接使用原始数据，`question_local` 只在本问脚本内做有数学来源的局部变换；
6. 判定必须检查当前数据的完整性、一致性、有效性、重复身份、采样与覆盖、测量质量、模型输入要求以及时间因果/信息泄漏；缺失值不等于必须插值，插值、统计填补、模型填补和预测填补都必须按变量语义、缺失结构与可验证性选择；
7. 预测填补只可用于恢复后续模型确实需要的缺测输入，并须独立验证且禁止未来信息/标签泄漏；赛题本身要求预测的未来值、类别、需求、风险等属于核心模型，不得包装为数据预处理；
8. 只要实际预处理改变后续模型输入，论文必须给出数据问题、数学公式或映射、参数依据、方法验证、处理前后证据和后续模型接口；经验型处理不得编造形式证明；
9. `project_level` 的 `data_process.m` 是项目级预处理证据固定 MATLAB 脚本；文件归属 `数据预处理/`，但仅在 Figure Evidence 阶段、主求解与结果深化分析完成后生成。它只读取 `数据预处理结果.xlsx` 中 Python 已持久化的处理前后、诊断和验证数据绘图，不重新清洗、插值、滤波、重采样或估计参数；正式导出基名使用 `data_process` 或 `data_process_<evidence>`；
10. 模型语义或数据处理判定变化时递增 semantic revision，并按 data / parameter / model / result 依赖递归传播 stale；
11. 每问最终维护两个题目专属 Python：`问题X求解.py` 和 `问题X结果深化分析.py`，并保留两个标准工作簿与一个 `qX_plot.m`；主求解脚本 accepted 后冻结，结果深化分析使用独立脚本；
12. 实际生成的 `preprocessing / primary / analysis` 代码阶段都必须通过 `../../core/code_quality_contract.yaml` 与 `../../scripts/validate_code_delivery.py`；
13. 用户完整运行后，由 `validate_user_execution.py` 按当前数据事实源验收工作簿、对应阶段代码/数据哈希和质量门；project_level 工作簿同时必须保存论文方法、处理前后和绘图底层证据；
14. 深化分析不稳定时按原因回退模型、条件式预处理或主求解并传播 stale；只改深化脚本不得污染已通过的主结果质量状态；
15. MATLAB只读真实工作簿证据绘图。正式绘图前根据 Core conclusion、Evidence level 和 Primary question 动态选择单图、1×2、2×1、1×3、2×2或拆图；不存在固定默认版式。主比较允许中高饱和、高对比颜色，亮蓝/鲜红等主色用于快速建立视觉差异，辅助元素降权；完整规则以 `../../modules/04_figure_evidence.md` 为准；
16. LaTeX为默认论文主链，DOCX仅显式按需；正文写作统一遵循 `../../modules/05_writing/latex.md` 的“正文表达与章节组织协议（写作权威）”。中文国赛问题重述默认采用“问题背景 + 问题提出”，问题提出逐问写“问题X：”；问题分析逐问且不写公式/结果；模型假设与符号说明分章；各问使用“问题X模型建立及求解”，详细推导后设置核心模型汇总，主结果放在“求解结果”；默认不设固定“小问结论”和全文独立“结论”章；命题短证明分段优先、多阶段才分点；核心图表必须有正文编号引用和解释；AI-cleanup 后执行略朴素、生涩但规范且以正向连续叙述为主的科研初学者式学术重写；最终 LaTeX 运行 `../../scripts/audit_paper_prose.py` 做非破坏性成稿审计，warning 人工复查、`--strict` 只阻断结构性 `review_required`。

详细规则以 `../../core/` 下权威合同为准。v7.2.0--v7.2.2 项目重新进入设计、预处理、绘图或写作时沿用三态 `preprocessing_decision` 并按当前通用审计与论文证据框架复核；历史只读交付不强制反向补 `data_process.m`，更早项目与 `legacy/` 按既有只读兼容规则处理。