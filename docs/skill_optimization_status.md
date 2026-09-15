# Skill 全面优化实施记录

## 已批准范围与基线

2026-09-15，用户审阅并批准《Mathmodel Skill 全面优化计划》全部范围，随后要求持续自动推进。批准文稿 SHA-256：`05808d566177dd44b3bbf924db43fad5a239c6b5d599b5faa9cc0f65af8fd365`。全面优化起点为 Skill v9.1.0 / `8a92a7924e950939dc77b15d3bb1a88400c09979`。

本记录是实施证据，不建立新的业务 Authority。每一阶段仍遵守 `SKILL_CHANGE_GOVERNANCE.md`：从最新 main 建独立分支、单主题 PR、真实测试全绿后合并；默认不改用户项目、不跳过审批/identity/stale、数值/工作簿和交付门。

## 分阶段执行

| 阶段 | 主题 | 状态 |
|---|---|---|
| P0 | 计划与范围审批 | 用户已批准 |
| P1 | 可重算的读取与行为基线 | 已合并，PR #152，`0eecaf929c83f19555402564ea0b14743d9bcf7d` |
| P2 | 读取范围、事实同步和工具调用分流 | 已合并，PR #153，`2a9cb227067d58d52471f164d317be3b4be330fe` |
| P3a | 全局政策去重与来源映射 | 已合并，PR #154，`9cb5005b780c278953463d1ebeb891928974bb1f` |
| P3b | 逐章/局部写作读取与 Cleanup/Review 职责收束 | 已合并，PR #155，`541cd398f5d4dfb9b0137437263747e9d55a6ca8` |
| P4 | compact framework 实例化与渐进登记 | 已合并，PR #156，`a15b0a15e45fd561a87264eae4af5b1a710d23f6` |
| P5a | 新生成阶段脚本统一 RUN_CONFIG，执行政策与任务参数分离 | 已合并，PR #157，`36c1e8e983228bbe2d8870bef05d204491273cca` |
| P5b | 版本化运行回执 RUN_RECEIPT | 已合并，PR #158，`8a7b0738db6d8f730979ea04676d0a113b504f99` |
| P6a/P6b | 论文图例索引、独立 MATLAB profile、真实预览 | P6a 实施中，PR #159；P6b 未开始 |
| P7 | 条件式分析与附录 | 已获范围批准，尚未实现 |
| P8 | 有测量依据的基础设施整理 | 未开始 |
| P9 | 综合回归、兼容与发布 | 未开始 |

## 已合并阶段摘要

### P1

建立固定代表请求、真实 assured resolver 的资源/行为基线与审批/identity 边界回归。P1 的零差值只表示基线可重算，不宣称优化收益。

### P2

新增 additive `reading_plan`，把 `read_now / conditional / tool_interfaces` 与完整兼容 `load_order` 分开。事实同步/纯样式快捷读取只在 file-backed evidence current 时启用；混合意图、歧义、语义变化和 stale 均完整回退。旧 gate、pause、machine dependency closure 与 CLI 不变。

### P3a

默认必读 `core/hsk_core_policy.md` 从 20,016 bytes 收束至 10,788 bytes，约减少 46%。目录、工作簿、预处理、绘图、普通写作及兼容细节回指现有唯一 Authority，跨阶段 Hard 保留。

### P3b

把写作链职责拆清：Runtime 管阶段/读取/Capability；Protocol 管普通正文叙事；Cleanup 只管表现层清理与必要推理保护；Review 只管检查/分级/返修/交付。局部编辑默认不扩大成全文工作。最终 head 通过 Python 3.10--3.14、Static lint、Generated contract、三类 LaTeX 和 Production attestation，并通过 Optimization baseline evidence 后合并为 `541cd398...`。

## P4：Compact Framework 实例化与渐进登记

### 修改主题与 Authority 边界

P4 修复一个已经存在但没有真正进入创建路径的闭环：`core/output_contract.yaml#model_paper_framework.default_mode` 已是 `compact`，但 canonical `templates/model/model_paper_framework.md` 是 full superset，直接复制会在 model-design 阶段过早带入题目候选、摘要、Paper Fragment、Chapter Handoff、跨问综合等 full-only 写作登记。

P4 不创建第二套 framework Authority：

- mode/use_when/required_sections 仍由 `core/output_contract.yaml#model_paper_framework` 定义；
- canonical template 仍是唯一结构 superset；
- `scripts/validate_model_paper_framework.py` 仍是确定性 live framework validator；
- `state/project_state.yaml` 仍保存 mode/hash/sync/stale；
- SIB、Model Approval、semantic revision/identity 和 typed stale 完全不由 P4 helper 改写。

### 实现

新增 `scripts/instantiate_model_paper_framework.py`：

1. `new` 默认直接读取 Output Contract 的 `default_mode`，因此新 scaffold 真正以 compact 投影创建；也可显式 `--mode full`。
2. compact 只保留 canonical template 中 `当前有效口径 / 各问模型与结果 / 图表证据链 / 待办与缺口` 四个顶层块，不复制 full-only 顶层内容。
3. `expand` 允许 compact → full 无损扩展：已有 common 顶层块逐字节保留，只按 canonical 顺序插入缺失 full-only 顶层块，并把 mode header 改为 full。
4. full → compact 自动转换直接拒绝，避免静默删除已有 title/abstract/proposition/paper-fragment/handoff 等项目事实。
5. 重复/未知顶层标题、compact 中已混入 full-only 顶层块、路径越界/缺失 template 等均 fail closed。
6. helper 不写 project state、不创建 approval、不修改 SIB/工作簿/数值 artifact；同 mode transition 幂等。
7. `core/bootstrap.yaml` 增加稳定 `instantiate_framework` 入口并明确 raw full-superset template 不是 live-project 默认复制路径；Framework mode 语义仍回指 Output Contract。

未修改 `core/output_contract.yaml` 的既有 mode 定义，也未重写 canonical 大模板：当前 Authority 已足够，P4 只补缺失的执行投影层，避免为了“实现计划”重复新增字段。

### 渐进登记

- `proposed_model_spec` / 日常单问设计：compact；记录 current scope、Q 级模型/SIB/Challenge/Approval、必要 Formula/Algorithm/PQS、结果/证据与待办。
- accepted primary/result analysis：继续 compact，只更新对应 Q 结果摘要、证据、claim/boundary。
- figure evidence：继续 compact，只更新 Figure evidence/map。
- 跨聊天完整交接、整篇 DOCX/LaTeX、跨问综合、终审：先 lossless compact → full，再登记 overall/title/abstract/preflight/fragments/handoff/cross-question/sync。
- 局部修改本身不触发 full；可由现有 current facts 派生的写作视图延迟到 full 阶段生成，不在 compact 阶段重复手填。

详见非 Authority 维护证据 `docs/p4_compact_framework_progression.md`。

### 测量与测试

在完整 candidate source snapshot 上实测 canonical projection：

- full scaffold：32,941 UTF-8 bytes；
- compact scaffold：15,425 UTF-8 bytes；
- 初始 project-memory scaffold 减少 17,516 bytes，约 **53.2%**。

这只是 framework scaffold 体量差，不是实际 token 或整任务耗时节省。

P4 新增 10 个专项测试，覆盖：default compact、compact 顶层精确投影、full validator 闭环、compact→full common sections byte-for-byte 保留、幂等、full→compact 拒绝、未知/重复/full-only 混入 fail-closed、fenced fake heading、防止 project state 隐式写入、Bootstrap entrypoint。

业务实现 head `e7b733fb464773a52380707c59aa39bf2130b031` 的完整 HSK Skill CI 与 Optimization baseline evidence 均通过；随后状态记录进入同样的 generated-metadata/final-head 复验流程，PR #156 最终按治理门全绿合并至 `main`，merge commit 为 `a15b0a15e45fd561a87264eae4af5b1a710d23f6`。

## P5a：RUN_CONFIG 任务参数与执行政策分离

### 边界

P5a 只改**运行前代码交付配置**，不改 returned workbook 的运行事实回执 schema，也不在本阶段引入版本化 `RUN_RECEIPT`。后者留给独立 P5b。Skill release carriers 仍保持 v9.1.0，统一版本发布留给 P9。

`core/user_execution_contract.yaml` 继续是 user/full-fidelity/no-degradation 的唯一 Authority。新生成脚本不再重复自报这些全局不变量；工作簿 `运行配置` 继续完整记录真实 owner/profile、solver/version、停止原因、platform、fallback 与六个 no-degradation 标志，并由 `scripts/validate_user_execution.py` 验收。

### 实现

- 新生成 primary/analysis/preprocessing Python 阶段脚本统一使用唯一顶层 `RUN_CONFIG`；
- canonical RUN_CONFIG 只要求 `stage/problem_name/data_paths/data_sha256/solver/random_seed/tolerance/iteration_or_time_limit/expected_workbook`，primary 继续要求 `primary_quality_protocol_version`；
- `solver_version` 不再是运行前任务参数硬要求，仍允许冗余兼容并在工作簿中作为实际运行事实验收；
- `execution_owner/user`、`execution_profile/full_fidelity` 与六个 `allow_*=false` 从 User Execution Authority 继承；若新 RUN_CONFIG 显式覆盖这些字段，只允许与 Authority 完全一致，非法覆盖 fail closed；
- 旧 `FULL_FIDELITY_CONFIG` / `FULL_RUN_CONFIG` 保持只读兼容，并继续执行旧完整字段要求，不因迁移降低约束；
- 同一脚本若同时定义多个受支持配置名，静态交付与 receipt-side delivered-code reader 均 fail closed，避免 source-order 选择；
- `data_sha256` 仍是运行前严格 64 位 SHA-256 绑定，project-level 隔离、accepted primary code freeze、PQS/03A/03B 和 state hash 语义不变；
- `PipelineConfig` 删除重复 owner/profile/no-degradation 字段，避免模板内产生第二份全局政策来源；
- 03A/03B 与 starter/pipeline README 同步使用 canonical RUN_CONFIG 口径；
- 旧 editable-mechanism drift guard 仅对本阶段明确触碰的 `modules/03_solve_validate.md`、`modules/03_result_analysis.md`、`scripts/validate_code_delivery.py` 做受控 hash rebaseline，没有删除或放宽 drift assertion。

专项回归位于 `tests/test_p5a_run_config.py`，覆盖 canonical/legacy schema、data hash、非法 invariant override、multiple-config ambiguity、Authority 字段分离与 PipelineConfig 去重；最终 head `1cdcb307bcdc4c6aa007f71afb4951db80af6250` 的 HSK Skill CI 与 Optimization baseline evidence 均通过，PR #157 合并至 main，merge commit 为 `36c1e8e983228bbe2d8870bef05d204491273cca`。

详见非 Authority 迁移证据 `docs/p5a_run_config_migration.md`。

## P5b：版本化 RUN_RECEIPT 与 RUN_CONFIG 绑定

### 边界

P5b 不新建第二张回执表，也不新增独立运行 YAML/JSON。逻辑 `RUN_RECEIPT` 继续序列化到既有 `运行配置(项目, 值)` 工作表；`core/workbook_schema.yaml` 的物理表结构因此无需改写，运行协议语义仍由唯一 `core/user_execution_contract.yaml` 拥有。

新生成 RUN_CONFIG 通过 `run_receipt_protocol_version="1.0.0"` 声明期望协议；实际工作簿通过 `run_receipt_version="1.0.0"` 声明回执版本。P5a 过渡 RUN_CONFIG 与旧 `FULL_*` 的无版本历史回执保留只读兼容到 P9，但显式未知/不匹配版本 fail closed。

### 实现

- User Execution Contract 升至 `2.5.0`，登记 RUN_RECEIPT 逻辑名、传输载体、当前协议、兼容窗口、echo 字段与 runtime-only facts；
- `scripts/validate_code_delivery.py` 对显式 `run_receipt_protocol_version` 做静态版本校验，同时保留 P5a transitional absence；
- `scripts/validate_user_execution.py` 可按 preprocessing/primary/analysis 三阶段静态读取已交付代码，核对对应代码哈希，再执行协议握手；
- v1 回执核对 `stage/problem_name/data_sha256/solver/random_seed/tolerance/iteration_or_time_limit` 与已交付 RUN_CONFIG 一致；数值字段允许 Excel 常见数值表示等价，不把格式差异误判为语义漂移；
- `solver_version/actual_stop_reason/repetitions_or_scenarios/grid_or_time_range/platform/fallback/owner/profile/allow_*` 继续只作为运行后事实验收，不能由 RUN_CONFIG 自报替代；
- Primary Quality Protocol 保持独立：primary 可同时携带 receipt protocol 与 `primary_quality_protocol_version`，P5b 不改数值验证 Authority；
- starter 与 hsk_pipeline README 已切换为 P5b 新 writer 口径；不生成独立 RUN_RECEIPT 文件；
- 旧 editable-mechanism drift guard 只对本阶段明确触碰的 `scripts/validate_code_delivery.py` 做受控 hash rebaseline，未移除或放宽断言。

专项回归位于 `tests/test_p5b_run_receipt.py`，覆盖 v1 握手、缺版本降级拒绝、未知版本、P5a transitional read compatibility、无已交付代码绑定、echo mismatch、Excel 数值等价与 code-delivery marker 校验。最终 head `65dce8b23fc77482f568d80d11a66aeeda24837b` 的 HSK Skill CI 与 Optimization baseline evidence 均通过；PR #158 已合并至 main，merge commit 为 `8a7b0738db6d8f730979ea04676d0a113b504f99`。

详见非 Authority 设计证据 `docs/p5b_run_receipt_versioning.md`。

## P6a：论文图例索引与 MATLAB publication profile 分离

### 边界

P6a 只整理既有论文 Figure 视觉参考资产的检索索引，并把 MATLAB publication profile 从样式应用函数中拆成独立纯数据 registry；不新增外部论文图片，不把视觉参考升级为第二 Figure Authority，也不在本阶段宣称真实 MATLAB preview 已完成。真实渲染/预览验证保留给 P6b。

`modules/04_figure_evidence.md` 继续拥有图型、legend、layout 与 Figure evidence 决策；`assets/figure_assets.yaml` 仅提供 Evidence Structure / publication pattern / layout need 到既有 asset key 的候选 lookup。`templates/matlab/hsk_publication_profile.m` 只拥有 deterministic palette/typography/frame profile 数据，`hsk_apply_scientific_style.m` 只负责把已选择 profile 应用到 figure。

### 实现

- `assets/figure_assets.yaml` 升至 additive 1.1.0 索引，保留旧 `assets[].path(s)/use_for` 结构，新增 `reference_index`，默认只加载本次 lookup 命中的少量资产；
- `hsk_publication_profile.m` 独立保存 `competition_high_contrast / journal_balanced / monochrome_print` 三种 profile 的 palette、typography 与普通 Cartesian frame 参数；
- `hsk_apply_scientific_style(fig[, profile])` API 不变，改为消费 profile registry，不再复制 profile switch；release-era palette aliases 继续兼容；
- 视觉参考索引明确不提供数据、结论、固定颜色、固定面板数、legend 或 annotation 决策；
- MATLAB README、Nature figure asset README 与专项测试同步；不改正式 qX 绘图脚本的项目五文件接口，也不碰数值/工作簿/state/approval/LaTeX/release carrier 业务语义；
- generated `SKILL_FILE_INDEX.md` / `TEMPLATE_INDEX.md` / `MANIFEST.sha256` 继续由既有生成流程管理。

专项回归位于 `tests/test_p6a_figure_reference_profile.py`，并重跑 v9.1 publication rendering 与既有 scientific-figure 回归。当前候选 head 已通过完整 HSK Skill CI；本状态记录进入同一 PR 后将触发 Optimization baseline evidence，最终合并仍以 final head 的 HSK Skill CI、Optimization baseline evidence、generated contract、scope review 与 mergeability 全部通过为门。

详见非 Authority 设计证据 `docs/p6a_figure_reference_profile_split.md`。
