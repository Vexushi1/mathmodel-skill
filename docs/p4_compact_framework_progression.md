# P4 Compact Framework 实例化与渐进登记实施边界

> 维护证据，不是新的业务 Authority。Framework mode、项目状态、写作语义仍分别服从现有 Authority。

## 基线与问题

- P4 基线：main `541cd398f5d4dfb9b0137437263747e9d55a6ca8`，Skill v9.1.0。
- `core/output_contract.yaml#model_paper_framework` 已声明 `default_mode: compact`，日常迭代/单问交付/普通聊天续作使用 compact；跨聊天交接、完整复现、DOCX/LaTeX 终稿与终审使用 full。
- 当前 canonical `templates/model/model_paper_framework.md` 是 full superset，头部却直接写死 `框架模式: full`。如果直接复制模板创建 live framework，会绕过 default compact，并过早登记标题、摘要、Paper Fragment、Chapter Handoff 等 full-only 写作信息。

P4 只修复“声明的 compact mode 没有真正进入实例化路径”这一闭环，不重新设计项目记忆语义。

## Authority 边界

| 职责 | 唯一事实源 / consumer |
|---|---|
| framework modes、何时 compact/full、正式交付模式 | `core/output_contract.yaml#model_paper_framework` |
| canonical 可用结构 | `templates/model/model_paper_framework.md`（superset，不是 live project 实例） |
| live framework 结构确定性校验 | `scripts/validate_model_paper_framework.py` |
| mode/hash/sync/stale 等机器状态 | `state/project_state.yaml` + `core/project_state.schema.yaml` |
| SIB / semantic identity | 现有 Semantic Identity Authority，不由 P4 复制 |
| model-design 阶段何时创建/更新 framework | `modules/02_model_design.md` consumer |
| 项目同步及 framework hash | `scripts/sync_project.py` consumer |

不得让 instantiator 成为第二套 Framework Authority：它只读取上述 contract/template，投影出 compact/full 文本并执行 fail-closed 结构检查。

## 目标行为

### 新建

- `compact`：只实例化 canonical template 中的 common header + compact 顶层块：`当前有效口径 / 各问模型与结果 / 图表证据链 / 待办与缺口`。
- `full`：实例化 canonical superset 全部顶层块。
- canonical template 使用显式 mode placeholder，禁止把 raw template 当 live framework 直接交付；live strict validation 继续拒绝未解析 placeholder。

### compact → full

扩展是**无损增加**：

1. 保留现有 compact common 顶层块原文；
2. 只从 canonical superset 插入缺失的 full-only 顶层块，并按 canonical 顺序定位；
3. 只把 header 的 mode 从 compact 改为 full；
4. 现有 SIB、当前模型、结果摘要、证据位置等 common 内容不得被 template 默认值覆盖；
5. 重复执行必须幂等。

### full → compact

默认拒绝自动转换。该操作可能删除 title/abstract/proposition/paper fragment/handoff/cross-question 等现有项目事实，属于有损操作；P4 不提供静默 shrink 快捷方式。

## 渐进登记矩阵

| 项目阶段 / 操作 | 默认 mode | 允许/要求登记 | 不应为了“完整”提前登记 |
|---|---|---|---|
| `proposed_model_spec` / model design | compact | 当前有效口径、Q 级当前模型/SIB/Challenge/Approval、必要 Formula/Algorithm/PQS、当前证据与待办 | 论文题目候选、摘要组织、全篇 Paper Fragment/Chapter Handoff |
| accepted primary / analysis result | compact | 更新对应 Q 结果摘要、证据位置、claim evidence/boundary、待办 | 无关小问写作规划、全文 title/abstract |
| figure evidence | compact | 当前 Figure evidence/map 与入文锚点 | 全文写作 registry，除非已有独立 full trigger |
| 普通单问续作 / 局部修改 | 保持 compact | 只更新目标 Q/common 依赖 | 因局部操作自动升级 full |
| 跨聊天完整交接、整篇 DOCX/LaTeX、跨问综合、终审 | full | 先 compact→full，再按当前事实填充 overall/title/abstract/preflight/fragments/handoff/cross-question/sync | 从空模板重新复制覆盖现有 common facts |

可从既有 current facts 派生的写作视图应在进入 full 时再生成/登记，不在 compact 阶段重复手填同一事实。

## 不变量

- 不修改 Model Approval、semantic revision、SIB canonicalization、typed stale 规则。
- 不修改 accepted workbook、PQS、03A/03B、五文件、RUN_CONFIG 或 MATLAB Figure Skill。
- 不改变 CUMCM 一级骨架和官方竞赛规则。
- compact 不是“少验证”：其现有字段仍必须通过 current validator；需要完整交付时先扩展 full 再执行完整写作/终审链。
- 旧 full/compact project 继续可读；没有强制迁移。

## 计划实现

1. canonical template 将 mode 改为 `__FRAMEWORK_MODE__`，明确它是 superset source。
2. 新增 `scripts/instantiate_model_paper_framework.py`：`new compact|full`、`expand compact→full`、`--check`/stdout 或显式 output；默认不写 state。
3. Output Contract 增加 canonical superset、instantiator、default creation mode、lossless expansion 与 progressive registration 指针。
4. Module 02 改为“默认调用 compact instantiator”，禁止 raw-copy full template；full trigger 仍由 Output Contract 决定。
5. 测试 compact/full 投影、common-section byte preservation、幂等、未知/重复顶层 heading fail-closed、full→compact 拒绝、旧 live frameworks 兼容。

## 验收与回滚

P4 合并前必须完成：

- `python scripts/lint_skill.py`
- `python -m unittest discover -s tests`
- `python scripts/generate_indexes.py --check`
- compact/full 生成结果通过 `validate_model_paper_framework.py`
- compact→full common-section 原文保持；re-expand 无变化；full→compact 失败
- 完整 GitHub Python 3.10--3.14、Static contract lint、Generated file contract、CUMCM/MCM-ICM/Diangong LaTeX、Production LaTeX attestation 全绿

回滚只撤销 P4 helper、contract/template/Module 02 的 P4 增量及测试/维护证据，再重新生成索引；不得触及用户 project state、SIB、审批或数值 artifact。