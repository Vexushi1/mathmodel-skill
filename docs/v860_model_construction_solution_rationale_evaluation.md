# v8.6.0 Model Construction & Solution Rationale：实现与回归评估

日期：2026-09-04。

本文保存 v8.6.0 从候选分支到正式 release 的实现/验收证据，不是新的数学建模 Authority，不是论文句式模板，也不用于作者身份或 AI 使用判断。正式规则仍由 `core/writing_reasoning_contract.yaml`、`modules/02_model_design.md`、`modules/05_writing/paper_writing_protocol.md` 及其既有 consumers 承担。候选阶段的失败与待办继续保留为历史快照，但不能覆盖下述 Final Release Status。

## 0. Final Release Status

- Document role：v8.6.0 implementation/evaluation record；runtime authority = none。
- Release version：`8.6.0`。
- Merged PR：#110。
- Merge commit：`41373e1a0ce3472df2c5afc15a3f4c0b9db379fa`。
- Final PR validation：HSK Skill CI #2383 全矩阵通过后进入合并。
- Post-merge validation：`main` 上 HSK Skill CI #2384 对 merge commit 完成并 `success`；generated-metadata verification 同步完成。
- Release carriers：正式合并时已同步到 `8.6.0`。
- Current verdict for v8.6.0：`released / merged / superseded only by a later release`。
- 下文 #2348 等失败记录属于 candidate-stage historical observations，不应解释为当前仓库仍处于 Draft、pending 或未发布状态。

## 1. 基线、候选与评估范围

- 发布基线：`main@6951b8f5d7526332abc821bcb6d1ef8f6f8bc3af`（v8.5.0）。
- 候选分支：`upgrade/v8.6.0-model-construction-solution-rationale`。
- Candidate-stage PR：#110；在本评估快照形成时仍为 Draft，当时要求全量 CI 与 release-carrier synchronization 完成后才进入合并判定。
- 参考材料只用于抽象跨题型写作/建模结构；不复制 A196 的题目对象、算法、标题、章节编号或固定句式。
- 固定语义案例：`tests/fixtures/model_construction_solution_cases.yaml`，共 12 组，覆盖事件判据、局部边界定位、严格/启发式缩域、离散参数证据、solver fit/escalation、标题拆分/压缩与简单解析 anti-bloat。

本轮评估回答的不是“文字是否更像人工”，而是评委能否从当前模型建立及求解部分恢复：

```text
问题结构
→ modeling gap
→ 为什么选择当前数学结构
→ 结构化简为何成立/证据等级
→ 当前适用条件与边界
→ solver 所需前提
→ solver 为什么适配
→ 关键数值建模参数为什么这样选
→ 结果与验证范围
```

## 2. 实际实现落点

| Authority / consumer | v8.6.0 增量 | 明确不做 |
|---|---|---|
| `core/writing_reasoning_contract.yaml` | `model_construction_rationale`、local applicability、solver preconditions、Reduction Provenance 语言边界、numerical parameter rationale、Section Title Minimality、Adaptive Subsection Separation | 不建立第二套 applicability/heading contract；不按连接词、算法名、标题长度自动判断正确性 |
| `modules/02_model_design.md` | 在当前模型语义、Complexity Sanity、Model Challenge、Approval Brief 和项目记忆中暴露真正改变求解语义的 rationale/precondition/provenance 信息 | 不新增生命周期 Gate，不改变 Human Model Approval、03A/03B 或工作簿 schema |
| `modules/05_writing/paper_writing_protocol.md` | 重要模型选择局部闭合 gap → structure → applicability → downstream role；solver 前提与 fit 分离；关键离散/容差参数给出证据链；标题与小节按真实独立任务自适应 | 不固定“模型适用性分析”小节；不固定四段式标题；不把模型建立写成长篇百科 |
| `modules/05_writing/ai_cleanup.md` | Keep / Compress / Re-locate / Delete 建模理由；Heading Compression Test；Keep / Compress / Merge / Split 小节决策 | 不用标题数量、字符数、代词或“因为/因此”作质量评分 |
| `modules/06_review_delivery.md` | Model Construction & Solution Rationale Review；对非法 heuristic→strict、material solver-precondition failure 保留既有 Hard 证据边界 | 不把标题较长、三级小节较多、复杂模型保留短导航标题自动列为 Blocking |
| `core/writing_runtime_contract.yaml` | 普通问题写作阶段暴露 rationale/precondition/title-minimality 能力；新增一个按需示例读取分支 | 不增加 startup preload，不新增 stage，不改变 final assembly 顺序 |
| `templates/model/model_paper_framework.md` | 记录本题实际 modeling gap、结构选择依据、适用性、solver preconditions、参数依据和二级/三级小节规划 | 不复制跨项目写作手册 |

新增可选参考：`modules/05_writing/references/model_construction_solution_rationale_examples.md`。它只用于困难段落的局部示范，明确不是当前项目事实、算法推荐表或固定句式库。

## 3. 12 组固定语义案例

1. **已有轨迹但缺事件判据**：轨迹已知不能替代“成功/失败”predicate；solver 不得早于判据闭合。
2. **多区间事件边界**：`0→1→0` 只支持分段后的局部 bracket，不允许由连续性直接推成全域单调二分。
3. **proven-sufficient reduction**：有证明锚点时可说明保留所需解，但不必伪装成双向严格等价。
4. **heuristic reduction**：没有全局证书时保留弃置域风险和有限 claim scope，不得升级为全局最优。
5. **离散点数/网格选择**：选择依据来自声明精度指标与平台区间，不自动包装成现实参数鲁棒性。
6. **低维连续黑箱 solver fit**：solver 适配由目标/可行域实际结构决定，而非仅由“变量连续”或算法名称决定。
7. **跨问 solver escalation**：维度、离散分配、跨主体耦合新增后，solver 更换需要说明结构增量。
8. **复杂模型标题 profile**：独立数学任务充分时允许清晰短三级标题，不因标题数量机械合并。
9. **简单模型标题 profile**：直接关系已经闭合时优先连续组织，不强制四个子标题。
10. **Heading Compression**：删除父标题重复与“基于/视角下/研究”等包装后，若数学任务仍完整则优先短标题；无硬字符数。
11. **空泛 applicability**：“适用范围广/精度高/科学合理”等不构成本题适用性依据。
12. **直接解析 anti-bloat**：无需 solver/额外验证时不扩写 rationale、算法段或适用性小节。

测试保护的是语义边界和固定事实，不把这些案例的算法、题目对象或句式传播为默认模板。

## 4. v8.5 Author Reasoning Voice 保全

本轮没有回退 v8.5 的 Author Reasoning Voice：

- `human_reasoning_trace.subject_roles.quota = none` 继续成立；
- 不设置 `pronoun_frequency_target`；
- 不从作者声音推断 authorship / AI usage；
- Question Closure、Reasoning Necessity、Problem-Specificity 和 Claim Strength Alignment 继续有效；
- “我们认为”不能把 `HEURISTIC` 升级为全局最优；
- 简单题不强行插入第一人称、问句、算法或额外验证。

v8.6 的 Model Construction Rationale 与 v8.5 Author Reasoning Voice 的关系是：前者规定**什么重要建模理由需要可恢复**，后者规定这些理由如何在证据范围内自然表达；两者不建立代词配额或“人工感评分”。

## 5. 小节治理：同时防碎片化与过度合并

v8.6 明确修复单侧“只减少标题”的风险。

适合拆分的对象包括：独立关键判据/证明、独立结构化简、独立数值参数证据、独立 solver stage，以及后文需要明确回指的数学任务。适合连续组织的是同一论证链、每个候选标题只有很薄内容、且没有独立回指价值的段落。

因此以下两种情况同时合法：

```text
复杂优化：决策变量 / 目标函数 / 关键约束 / 模型汇总
```

在它们确实形成独立导航任务时可保留；而简单模型则可以在一个连续“模型建立”小节内完成全部闭环。没有“标题超过 N 个自动失败”或“标题超过 N 字自动失败”。

## 6. 机器审计边界

新增风险仍以保守 semantic review 为主。机器可以检查已登记字段、Authority 指针、确定性 claim/evidence 冲突和明确结构，但不得声称：

- 从“因为/因此”等连接词判断 rationale 完整；
- 从模型名/形容词判断 applicability；
- 从算法名判断 solver precondition 已满足；
- 从标题字符数或标题数量判断小节质量；
- 从表面顺序判断局部数学依赖；
- 从第一人称、问号或固定短语判断作者身份或“像不像人”。

如果 solver 前提实际不成立并导致主计算无效，或 heuristic 缩域被当成严格等价并改变答案，Blocking 仍来自既有数学/证据错误本身，而不是文风触发器。

## 7. Candidate-stage CI 历史观察

在候选 head `94f42f2136fa7d6eb96ea5d08d108bde4e4bf955` 的 GitHub Actions `HSK Skill CI` run #2348 中：

- Static contract lint：通过；
- LaTeX MCM-ICM：通过；
- LaTeX Diangong：通过；
- Production LaTeX attestation：通过；
- Generated file contract：在该 head 上因生成元数据 stale 失败；随后 `refresh-generated` 工作流已生成 bot commit，属于预期生成文件同步流程；
- Python 3.12：执行 703 项测试，仅剩 2 项失败；两项均为 **release version carrier 不同步**：`core/writing_runtime_contract.yaml=8.6.0`，而 `core/bootstrap.yaml=8.5.0`。未出现新的模型/写作语义断言失败。
- Python 3.10/3.11/3.13/3.14 在该 run 的 unit-test job 同样处于 failure；正式 release 前仍须以同步版本载体后的新 head 重新跑完整矩阵，不能用本记录替代最终绿色 CI。

因此在该候选 head 当时的状态是：**v8.6 语义/回归问题已从前一轮 16 个失败收敛到 release-carrier synchronization；当时尚不能宣称 full CI green。** 该结论只描述 #2348 候选快照；最终 release 状态以第 0 节为准。

## 8. Candidate-stage 当时未完成项

在该候选阶段，把 PR #110 从 Draft 推到 Ready for Review 前当时仍需：

1. 将 current Skill release carriers 统一同步到 `8.6.0`，包括 bootstrap、plugin、双份 Skill 入口、README/CHANGELOG、Core Policy 以及现有 release-version contracts；
2. 重新生成 `SKILL_FILE_INDEX.md` / `TEMPLATE_INDEX.md` / `MANIFEST.sha256` 等 generated metadata；
3. 在最终非 bot head 上重跑 Python 3.10--3.14、Static Contract、三套 LaTeX、Production LaTeX Attestation 和 Generated File Contract；
4. 所有 required CI 为 green 后更新本评估记录的最终 CI head/result；
5. 最后再更新 PR 描述并决定是否转 Ready for Review；在此之前不合并。

## 9. Candidate-stage 当时结论与最终收口

就 v8.6 本轮目标而言，已经形成了单一 Authority 下的完整能力链：

```text
current problem structure
→ modeling gap
→ model construction rationale
→ reduction provenance / applicability
→ solver preconditions + fit
→ numerical parameter rationale
→ adaptive subsection navigation
→ result / validation boundary
```

并且目前回归结果没有显示 v8.5 Author Reasoning Voice、Claim Strength、Model Approval、03A/03B、Workbook、Figure Evidence 或 LaTeX 载体被本轮语义扩展破坏。

但在该候选快照形成时，release-carrier synchronization 与最终全绿 CI 尚未完成，所以**当时的 candidate verdict** 只能是：

```text
implementation_semantics = ready_for_release_sync
release_status = pending
pr_status = draft
merge_status = forbidden_until_final_green_ci
```

该历史 verdict 后续已被第 0 节记录的最终事实闭合。v8.6.0 的 release closure 为：

```text
implementation_semantics = released
release_status = released
pr_status = merged
merge_commit = 41373e1a0ce3472df2c5afc15a3f4c0b9db379fa
post_merge_ci = HSK Skill CI #2384 success
```
