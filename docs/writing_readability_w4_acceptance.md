# W4 写作可读性集成验收记录

> 本文件是 `docs/writing_readability_validation_slimming_plan.md` 的维护验收证据，不是新的 Writing / Review Authority，不进入普通写作默认读取，不新增 Gate、Project State 字段或用户必交材料。

## 1. 基线与范围

- 集成基线：`main@f3946972f246cc145796558a8c115062d435ecb3`。
- W1：Part C–G 已完成。
- W2：PR #205 完成 Consumer/Pack/Template/例文对齐；PR #206 完成长核心证明真实分页与引用/编号验收。
- W3：PR #203 只移除 W0 已批准的 count-only `question_subsection_granularity` finding。
- W4 只做既有 review 内的集成验收，不重新设计业务政策，不扩大检查减重范围。

机器检查与语义审阅分别记录。本文中的“语义审阅”是本次仓库维护对当前 Authority、Consumer、样例和正反例所做的人工式逐项阅读判断，**不是独立评委、用户或第三方人工反馈**；外部人工反馈：none。

## 2. 验收方法

- **machine**：现有 audit、validator、unit regression、真实 LaTeX CI 能确定地判定。
- **semantic**：必须阅读数学作用、术语含义、表格语义或正文完整性，不能由关键词/长度/计数自动判定。
- **hybrid**：机器先定位显式冲突，语义审阅确认含义与修复边界。

W4 不把 semantic 项改造成新的机器阈值。正例与反例用于证明边界，而不是训练新的风格分数。

## 3. T01–T18 集成矩阵

| ID | 模式 | 正例 / 必须保留 | 反例 / 必须拒绝 | 当前证据 | 结论 |
|---|---|---|---|---|---|
| T01 | semantic | 简单守恒/解析关系说明来源、代入和答案即可 | 强造 solver、敏感性、多个三级标题 | `test_v719_intra_question_writing_closure.py`；rationale examples §12 | PASS |
| T02 | semantic | 条件/规律 → 变量关系 → 控制方程 → 初边值 → 适用范围 → 下游计算 | 只列最终 PDE，把关键化简/边界移附录 | `core_derivation_body_closure`；`test_v719...` / `test_v750...` | PASS |
| T03 | hybrid | 变量、目标、非平凡约束来源和最终优化模型完整；独立任务可用三级标题 | 只留最终模型大括号，删除约束来源 | Q1/Q2 template；rationale examples Profile A/B；heading regressions | PASS |
| T04 | machine + semantic | 命题陈述后用 standalone `hskproof` 保留完整长核心证明并真实跨页 | 因框高只留摘要或“证明见附录” | PR #206 Production LaTeX attestation：AUX 证明最终公式页码晚于命题页码，引用/编号解析成功 | PASS |
| T05 | semantic | 机械代数、重复系数、完整代码/日志和非主线补充材料可压缩/外置 | 因“长”把核心推导全部塞附录，或反向把所有机械展开塞正文 | Authority appendix boundary；Protocol / Cleanup | PASS |
| T06 | semantic | `supporting_derivation` 若是恢复非显然核心推导所必需则留正文 | 仅按 role 标签删除必要桥接 | Authority / Cleanup / Review；`test_v719...` | PASS |
| T07 | semantic | 前问已完整推导的共享模型准确回指；后问只展开真实增量 | 每问复制整套推导，或用“同理”掩盖新增条件 | Authority inheritance rule；Q3 template | PASS |
| T08 | machine | 多个 `subsubsection` 正常通过，无数量上限 | 因数量强压回二级 | `test_v790_modular_latex_source.py` + W3 count-only removal | PASS |
| T09 | machine | 正式标题停在三级 | `paragraph`、`paragraph*`、`subparagraph` 承担第四层/更深层级 | `audit_latex_project.py` + `test_v790...` | PASS |
| T10 | machine | 注释、verbatim、宏定义中的深层标题文本不算活动正文标题 | 全仓字符串搜索后误判第四层 | `test_v790_modular_latex_source.py` | PASS |
| T11 | hybrid | 专业术语首次实质出现有准确邻近解释，后续 canonical term 稳定 | 裸缩写、错误口语替换、discouraged alias 漂移 | Terminology Authority / Cleanup / Review；registry regression | PASS |
| T12 | semantic | 比较表的对象、行列、单位、指标方向、baseline/条件清楚，算法与模型角色不混淆 | 内部 run id 直接作为行名，或把算法比较称为模型比较 | table readability Authority；caption template；DOCX checklist | PASS |
| T13 | hybrid | 题面指定表结构和 Numeric Profile 精度保持，只补邻近说明 | 擅自舍入、改单位、绝对/相对误差或百分比/百分点口径 | numeric precision regression；table source-precision invariant | PASS |
| T14 | hybrid | 纯标题/措辞修改不改模型 identity/审批；最终 source audit/compile 仍绑定新源码 | 复用旧 source/PDF attestation | Writing Runtime semantic boundary；`hydrated_wording_only` baseline；source-bundle tests | PASS |
| T15 | machine | 只删除已证明 count-only 误报；真实机械拆分 warning 与 Hard 检查仍在 | 无行为对照直接删检查链 | W0 baseline + PR #203；W4 integrated audit pair | PASS |
| T16 | machine + semantic | 符号、约束方向、证据等真实语义变化使相关状态/fragment/audit 失效并复验 | “已经审过”作为永久通过 | semantic invalidation / paper-fragment / source-bundle regressions | PASS |
| T17 | hybrid | MCM/ICM、电工杯、DOCX 使用完整 reasoning fallback 与自身载体骨架；最大三级语义保持 | 强套 CUMCM 一级骨架 | Writing Runtime fallback；DOCX Heading 1–3；HSK CI 的 MCM-ICM/Diangong real compile | PASS |
| T18 | machine + semantic | duplicate/missing reference、claim-scope、真实数值/术语语义错误继续按既有 Hard/Default 处理 | 所有“可读性”问题一律 warning | blocking audit regressions；Numeric/Terminology governance；Review severity | PASS |

## 4. 机器侧集成断言

W4 聚焦测试覆盖以下跨阶段不变量：

1. 多个三级标题通过；明确四级标题 blocking；注释/verbatim/宏定义不误报。
2. W3 后五个独立二级任务不再触发 count-only finding，但机械拆分仍产生 `possible_mechanical_model_subsection_split`。
3. Terminology Registry 的 discouraged alias 与 Numeric Profile 精度漂移仍能被定位。
4. duplicate label / missing ref 等 Hard 路径仍为 blocking。
5. CUMCM compact runtime 不扩散到 MCM/ICM、电工杯、DOCX；DOCX 保持 Heading 1–3 / 禁止 Heading 4+。
6. final review matrix 仍恰好八类 coverage，`readability_status` 不进入 Runtime/Project State。
7. CI 保留 CUMCM、MCM-ICM、电工杯真实 LaTeX 与 Production LaTeX attestation；PR #206 的长证明真实渲染继续作为 Production attestation 子步骤。

## 5. 语义审阅记录

本轮语义审阅逐项核对 T01–T18 的“必须通过/禁止伪通过”与当前 Authority、Protocol、Cleanup、Review、Pack、Template 和例文。结论：

- T01/T05：anti-bloat 与正文完整性没有冲突；简单题可短，机械重复可压缩。
- T02/T06/T07：核心非显然推导、必要 supporting derivation、共享模型增量边界可以从正文规则恢复；没有以角色名、篇幅或“代码可复现”授权删核心链。
- T03/T08：三级标题由独立数学任务决定，不由数量决定；紧凑型与导航型两种组织均被保留。
- T11–T13：可读显示层与 canonical term / Numeric Profile / accepted 数值事实层分离，未授权重命名真实变量含义或改变精度口径。
- T14/T16：纯 wording 与真实语义变化分开；前者不污染模型审批，后者仍触发真实依赖复验。
- T17：跨载体只共享写作语义，不共享 CUMCM 一级骨架。
- T18：没有把数学、事实、数值、引用或 stale 错误归并成“风格 warning”。

未记录任何“评委已验证”“用户已人工验收”之类不存在的反馈。

## 6. W4 完成判据

只有下列条件同时满足才可把 W4 标记为 COMPLETED：

- 本矩阵 T01–T18 全部有正/反边界与真实证据；
- W4 聚焦测试、全量 Python matrix、Static contract lint、Generated file contract 全绿；
- CUMCM / MCM-ICM / 电工杯 LaTeX 与 Production LaTeX attestation 全绿；
- Optimization baseline 全绿；
- final head 与 merge 后 main 均通过；
- 没有新增 Gate、required state、coverage family、readability score 或跨运行信任缓存。

W4 不作版本发布裁决；版本、CHANGELOG 与 release carrier 只在 W5 处理。
