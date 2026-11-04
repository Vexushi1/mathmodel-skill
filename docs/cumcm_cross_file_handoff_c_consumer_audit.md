# Phase C：Cross-File Handoff 消费者核查与最小改造记录

> 2026-11-04；基线 main@de9d032b7db50d96f4dd9ce5cc48806241a63708 / v10.26.0。此文是维护决策记录，不是新的 Writing/Runtime Authority，未运行的测试不标记 PASS。

## C1｜真实生产者、消费者、失效防护

| 对象 | 真实生产者 | 消费者及触发时机 | 去留裁决 |
|---|---|---|---|
| Active physical-file 邻接 | CUMCM Template Manifest ordered_slots + activation | Runtime template_inspection、Protocol §5A、draft/final assembled seam sweep | 保留，禁止以写作顺序替代装配顺序 |
| 单段与相邻段落承接 | 当前正文、项目事实 | Protocol §4/§5，draft/final Review | 当前上下文即时润色；不另建项目 seam 记录 |
| 普通 narrative seam | 实际相邻 active source files | Protocol §5A 六项检查、Review | 仍全部审阅；默认无需持久行 |
| 摘要→问题重述 | 真实结果、Claim、Terminology/Numeric | frontmatter_consistency、最终全文审查 | 保留真实一致性；不预登记普通行 |
| 评价→AI 声明→参考文献→附录 | 当前 active 槽位和赛事事实 | structural_terminal、正式合规审查 | 只检结构/引用/披露，不强制桥接段及登记 |
| 跨问真实模型、Formula/Result/Claim 依赖 | Framework、Formula/Algorithm Trace、Paper Fragment Dependency Map、accepted Workbook | 写作、cross_question_increment、State stale 与 draft/final Review | 真实依赖和冲突必须追踪；保留 current 锚点/必要 seam 行 |
| Chapter Handoff Map | 当前 Framework 的 writing-only 区 | Runtime/Protocol/Review，旧项目可能携带历史行 | 空表合法；仅增量记录需持续追踪的 seam；历史行可读 |
| 缺 Manifest / 非 CUMCM | Runtime activation.non_cumcm_or_missing_manifest | scripts/resolve_runtime.py | 保留 full_reasoning_fallback，不改 resolver |
| Reading Plan / 历史测试投影 | writing stages 的 read_now/run_now/write_now/gate | reading_plan.py、tests/reading_plan_evidence.py、Phase G golden | stage 输入输出与门禁数量保持；只登记精确 release carrier |
| Framework 实例化及校验 | Framework 模板与既有 State | instantiate/validate_model_paper_framework.py、Project State Schema | map 非 required，且不属于模型语义哈希；无需新字段或重算 |

## C2｜最小实现决定

1. **保留** 五类 seam profile、六项语义检查、最终 active adjacency、draft/final 的 assembled seam sweep、数学/结果/Claim 的真实依赖与 stale 传播。
2. **去除**“所有物理文件相邻边界必须先持久填表”的义务；普通 narrative、frontmatter_consistency、structural_terminal 可以只看当前片段与既有锚点。
3. **需要时才持久登记**：有真实跨文件继承、未解决语义冲突或必须跨阶段恢复的数学与证据链；empty map 并非规避真实缺口的许可证。
4. **兼容** 旧 Framework Map 行，新增仅在实际需要时进行；单文件为 not_applicable，缺模板继续 full_reasoning_fallback。
5. **不新增** IntraQuestionHandoffMap、ResultAnalysisBridgeState、机器自然度评分、项目 State、Schema、检查器、用户本地 gate 或 Model Approval。
6. **不声明耗时收益**：未进行受控的调用次数/耗时实测。本阶段目标是业务动作去冗，而非虚构性能收益。

## 文件决策

| 文件 | 处理 |
|---|---|
| modules/05_writing/paper_writing_protocol.md | §5A 两处局部语义修订，普通相邻免持久记录但全审查不撤 |
| core/writing_runtime_contract.yaml | 仅 cross_file_chapter_handoff 下读写/记录/阶段门的适用范围收束；保留 stage IDs/read_now/write_now 及 fallback |
| templates/model/model_paper_framework.md | 可选 map 无默认无意义样例行；旧行可读 |
| modules/06_review/content_review.md | 原 assembled seam sweep 继续执行；空 map 不视为机械缺项；真实依赖必须闭合 |
| tests/test_v810_cross_file_chapter_handoff.py | 新旧边界的结构回归，普通 seam 与真依赖不可混同 |
| tests/test_v840_author_reasoning_writing.py、test_v830_editable_mechanism_diagram.py | 对 Protocol §5A 恰好两处授权修订做逆投影，保留原历史 SHA/Snapshot 及全部其他来源哈希 |
| tests/reading_plan_evidence.py、test_v900_phase_g_competition_runtime.py | 仅放行真实 v10.26.1 release carrier，未登记的 route/read-set/gate 变化继续失败 |
| core/writing_reasoning_contract.yaml、Template Manifest、scripts/resolve_runtime.py、reading_plan.py、Framework 校验器、State、数值/绘图、LaTeX Adapter、AI Cleanup | 已检查；无需本阶段业务变更；AI Cleanup 另行规划并在所有阶段修正结束后实施 |

## 审核边界与回滚

- 全部 active adjacency 必须复查；未闭合真实数学依赖、证据冲突或 claim 越界不可借可选 map 放行。
- 数学语义与 accepted 数值未改；纯 handoff wording 不触发 semantic_revision、locked-model stale、模型重新批准或 03A/03B 重算。
- Github Actions 按最终 head 执行 Static/Generated、Windows Python 3.10/3.14、LaTeX、MATLAB、Python Figure、适用 Optimization baseline；本文件不作为 CI PASS 证据。
- 回滚按 Phase C 单主题 PR 原子 revert，受管索引仅由 GitHub 生成；不回写旧用户论文，也不撤销 B 阶段成果。
