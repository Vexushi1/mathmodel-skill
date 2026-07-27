# v6.2.6 proposition-proof 变更记录

文件名保留 V622 作为稳定兼容路径。

## 目标

本版本在 v6.2.5 当前模型论文框架与 MATLAB 图标题闭环基础上，增加论文级命题与证明工作流。目标不是让每个小问机械出现命题，而是将真正影响模型建立、约束转化、解结构、算法可行性和误差边界的理论结论纳入可审查、可失效、可同步的证据链。

## P0：全文命题上限与准入

- 全文命题数量允许为 0，最多 4 个，不按小问机械配置；
- 仅允许等价性、存在/可行性、单调/阈值、凸性/唯一性/解结构、约束或维度缩减、可行性保持、稳定性/误差界及经条件核验的标准定理进入命题规划；
- 变量定义、直接代数变形、题意复述、单个样本结果、模型准确率比较和求解器退出状态不得包装成命题；
- 每个命题必须记录前提与定义域、结论、证明等级、模型作用、失效边界和状态；
- 数值实验只作导数符号、Hessian、理论界、等价误差或约束违反量复核，不替代数学证明。

## P1：框架、状态与路由闭环

- `templates/model/model_paper_framework.md` 新增“命题与证明规划”、P1--P4 合同、逐问命题引用、数值复核和失效检查；
- `core/output_contract.yaml` 新增 `proposition_contract`，明确全文 0--4 个、必填字段、允许类型和证明等级；
- `core/project_state.schema.yaml` 增加 `paper_framework.propositions`、命题数量/状态及每问 `proposition_refs`；
- `core/module_manifest.yaml` 新增 `proposition_plan` 产物，并接入模型设计、求解、写作和终审链；
- `core/workflow_router.yaml` 新增命题证明专用路由和命题/证明变更同步触发器；
- 模型、参数、约束或定义域变化后，相关命题与证明必须重新检查；stale 命题不得与 current 框架并存。

## P2：写作与 LaTeX

- DOCX 规则增加命题就近排版、证明标题、模型作用和失效边界要求；
- LaTeX 推荐顺序统一为“模型详细推导—必要命题与证明—核心模型汇总—求解算法—结果分析”；
- CUMCM HSK 模板新增按章节编号的 `proposition` 环境和显示“证明：”的 `hskproof` 环境；
- 长证明可将技术细节移附录，但正文保留条件、关键证明链、模型作用和失效边界；
- 禁止彩色定理盒、装饰阴影和与模型脱节的“理论创新”章节。

## P3：清理、校验与测试

- AI 模板感清除新增显然命题、伪证明、循环论证、条件遗漏、局部结论扩大和旧证明残留检查；
- `scripts/validate_model_paper_framework.py` 校验命题上限、数量、P1--P4 编号、表格字段和项目状态一致性；
- `scripts/validate_project_state.py` 校验命题数量、引用、current 字段和 stale 传播；
- `scripts/lint_skill.py`、Schema 测试、路由测试、内容测试和 LaTeX 模板检查全面接入命题契约；
- 根 Skill、README、项目说明、Runtime Router、Repository Index、插件元数据、Agent prompt、交付 Pack 和检查表同步至 v6.2.6。

---

# v6.2.5 current-model-framework 变更记录

文件名保留 V622 作为稳定兼容路径。

## 目标

本版本在 v6.2.4 扁平目录与 MATLAB 实表固定列读取基础上，解决两个长期断点：一是模型设计、求解修正、结果摘要与论文写作之间缺少单一当前口径文件；二是 MATLAB 正式图标题被旧规则统一删除，影响本地筛图与答辩复用。

## P0：`模型论文框架.md` 当前口径契约

- `locked_model_spec` 形成后，在项目根目录创建 `模型论文框架.md`；
- 新增 `templates/model/model_paper_framework.md`，覆盖当前数据/模型口径、论文结构、逐问模型与结果摘要、综合检验、图表证据链和待办；
- 文件内部只保留当前有效模型、参数、约束、数据处理、算法、结果和图表映射；发生变化时删除受影响旧内容并完整替换，历史由 Git 保存；
- 每次正式交付模型、代码、工作簿、验证、MATLAB 图、DOCX 或 LaTeX 时，必须同时交付完整最新版框架；
- 每问求解后结果摘要记录模型与算法、核心数值、验证/可行性、敏感性/鲁棒性、最终结论和证据位置。

## P1：机器状态与模块闭环

- `core/output_contract.yaml` 增加框架路径、更新触发器、权威边界和正式交付同步规则；
- `core/module_manifest.yaml` 将 `model_paper_framework` 接入 model_design、solve_validate、figure_evidence、writing 和 review 生产者—消费者链；
- `core/workflow_router.yaml` 增加 `framework_sync` 路由，并要求所有改变模型、结果、图表或论文结构的正式模块同步框架；
- `core/project_state.schema.yaml` 增加 `paper_framework`、每问 `framework_section`、`result_summary_status` 和 `result_summary_anchor`；
- `scripts/validate_project_state.py` 增加框架/结果摘要 freshness、stale 和可选哈希一致性检查；
- 新增 `scripts/validate_model_paper_framework.py`，检查必需章节、逐问章节、结果摘要锚点、同步状态和可选哈希；
- `scripts/hsk_check_artifact.py` 接入框架校验，并检查每问 MATLAB 正式脚本存在 `title` 或 `sgtitle`。

## P2：MATLAB 图标题恢复

- 单图必须使用简洁 `title`，多面板必须使用一个整体 `sgtitle`；
- 标题只说明研究对象、指标关系和必要方法信息，不写完整结论；
- 标题默认保留在可见图窗和导出文件中；
- DOCX/LaTeX 图注继续置于图下，用于补充样本、时间范围、统计口径、误差和解释，不与图内标题逐字重复；
- `q1_plot.m` 新增标题占位、非空/长度检查和标题样式；
- Figure Contract、图型选择、QA、MATLAB README、DOCX/LaTeX 规则和交付 Pack 全部同步。

## P3：全面同步与优化

- 根 `SKILL.md`、插件 shim、插件元数据、Agent prompt、README、项目说明、Runtime Router、Repository Index 和 Scripts README 更新至 v6.2.5；
- 写作模块改为先读取 current 框架，再从标准工作簿复核数值，禁止从聊天记忆恢复已删除旧口径；
- 终审新增框架—状态—工作簿—图标题/图注—论文一致性检查；
- 静态 lint、Schema 测试、工具测试、内容 Pack 测试和结构测试增加框架与图标题合同；
- 保留 v6.2.4 的项目根目录 Python、扁平问题目录、同目录工作簿与 `q{x}_plot.m`、实表真实表头和固定列读取规则。

---

# v6.2.4 flat-question-layout 变更记录

文件名保留 V622 作为稳定兼容路径。

## 目标

本版本不改变六模块主工作流和 Python/MATLAB 软件职责，重点消除竞赛项目中的重复目录、路径搜索辅助文件和工作簿—绘图脚本分离问题，使每问证据链在一个目录内闭合。

## P0：项目目录统一

- 赛题 PDF、附件数据表、说明文件和具体问题 Python 脚本直接放在项目根目录；
- 不再默认创建 `数据/`、`Python求解/` 和 `MATLAB绘图/`；
- Python 统一使用 `Path(__file__).resolve().parent` 定位项目根目录；
- 旧目录结构只用于历史项目迁移，不作为新项目交付格式。

## P1：每问结果目录扁平化

旧结构：

```text
结果数据表/问题X/问题X结果数据/
```

新结构：

```text
结果数据表/问题X/
├─ 问题X求解结果.xlsx
├─ 问题X敏感性与鲁棒性结果.xlsx
├─ q{x}_plot.m
└─ 图表/
```

- 删除 `问题X结果数据/` 重复层级；
- 两类标准工作簿、可选元数据和 MATLAB 绘图入口统一位于问题目录；
- 正式结果图统一导出到同级 `图表/`，可编辑图源按需放入 `图表/可编辑源/`。

## P2：MATLAB 单文件默认入口

- `q{x}_plot.m` 使用 `fileparts(mfilename("fullpath"))` 获取自身目录；
- 直接读取同目录两类固定工作簿，不再搜索项目根目录；
- 简单问题默认自包含文件、工作表、字段、空表和非法值检查，以及基础科研样式；
- 不再强制生成 `hsk_find_project_root.m`、`hsk_read_result_workbooks.m` 等辅助文件；
- 共享辅助函数仍保留为多问题复杂项目的兼容选项，但不进入默认入口。

## P3：机器契约和测试同步

- `core/output_contract.yaml`、`core/hsk_core_policy.md`、Module 03/04 和 Artifact Pack 同步新路径；
- `result_io.py` 改为直接写入 `结果数据表/问题X/`，新增问题图表目录和 MATLAB 入口路径函数；
- `hsk_check_artifact.py` 改为检查项目根目录 Python 脚本、扁平问题目录、同目录 `q{x}_plot.m` 和 `图表/`；
- `config.yaml`、`matlab_handoff.py`、Figure Contract、结果 Manifest 和提交包说明同步；
- 单元测试新增扁平路径、首次运行项目根目录、同目录 MATLAB 入口和图表目录检查。

---

# v6.2.3 contract-closure 变更记录

## 目标

本版本不增加题型 Pack，不恢复旧 Stage。重点将 v6.2.2 已有规则落实为可执行、逐问、可失效、可评分的机器契约，并减少活动包中的历史噪声。

## P0：契约闭环

- `core/module_manifest.yaml` 增加 artifact catalog、外部产物和完整生产者—消费者链；
- LaTeX 流程改为“草稿 → AI 模板感清除 → 最终编译”，避免清理结果未进入 PDF；
- `scripts/lint_skill.py` 新增模块输入无生产者、未登记产物、终点产物缺失和逆序依赖检查；
- `scripts/resolve_workflow.py` 将意图、主/次题型与竞赛解析为确定性的去重加载计划。

## P1：逐问状态与共享校验

- `core/project_state.schema.yaml` 按小问记录主/次题型、能力标志、数据/模型哈希、验证哈希、最优性措辞和失效状态；
- 新增 `scripts/validate_project_state.py`，检查阶段状态、需求计数、产物路径、证据、容差、最优性和 stale 状态；
- `core/workbook_schema.yaml` 将题型标签与验证能力分离；
- 约束、均衡、守恒、离散和收敛工作表由 capability 标志决定；
- `result_io.py` 与 `hsk_check_artifact.py` 复用同一工作簿校验函数；
- 增加重复主键、缺失值审计、非有限数值和“残差/违反量—容差—是否满足”一致性检查；
- Python 总管线移除导入阶段目录创建、全局随机种子和全局审计列表等副作用。

## P2：编译、评分和资产接入

- `core/compile_profiles.yaml` 区分仓库 `template_main` 与最终工程 `project_main`；
- `render_paper.py` 按 Profile 解析主文件，不再把硬编码候选当成唯一事实源；
- 新增 `scripts/score_submission.py`，正式消费 `config/review_weights.json`；
- 新增 `assets/figure_assets.yaml`，将 Nature 图集作为按需视觉参考接入图型选择；
- 图集不作为数据、结论或固定配色模板。

## P3：活动包与 CI

- `scripts/generate_indexes.py` 只为活动 Skill 生成索引和 Manifest；`legacy/` 仅保留 `legacy/README.md` 指针；
- 历史文件继续留在 Git 仓库，但不进入默认读取和活动完整性哈希；
- CI 将静态 lint 与 Python 3.10–3.14 单元测试矩阵拆分，减少重复工作；
- 自动生成元数据在功能分支完成后收敛为主分支维护，避免机器人提交反复触发 PR 检查。

## v6.2.2 基线

v6.2.2 完成六模块架构、十类题型 Pack、高级方法准入、两个标准工作簿、MATLAB 证据图、三套 LaTeX 冒烟编译、Python 3.10–3.14 CI、自动索引和跨平台 Manifest。v6.2.3 在该基线上完成契约闭环，v6.2.4 进一步统一项目与证据目录，v6.2.5 增加当前模型论文框架和 MATLAB 图标题闭环，v6.2.6 增加全文命题与证明的可选上限、状态和审查闭环。
