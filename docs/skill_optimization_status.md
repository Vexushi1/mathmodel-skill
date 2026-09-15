# Skill 全面优化实施记录

## 已批准范围与基线

2026-09-15，用户已批准《Mathmodel Skill 全面优化计划》全部范围并要求连续自动推进。本记录只登记实施状态，不建立新的业务 Authority。活动 release 仍由 `core/bootstrap.yaml` 等 release carriers 声明，阶段性优化在 P9 之前不提前发布新版本。

## 阶段状态

| 阶段 | 状态 | 说明 |
|---|---|---|
| P1 | 已合并 | resolver 基线、固定案例、审批/identity 回归 |
| P2 | 已合并 | 按任务 reading_plan、条件读取与工具接口 |
| P3a | 已合并 | Core Policy 去重、唯一 Authority 来源映射 |
| P3b | 已完成、待合并 | 写作运行时 / Cleanup / Review 职责收束；最终 head CI 全绿 |
| P4 | 未开始 | compact framework 实例化与渐进登记 |
| P5 | 未开始 | RUN_CONFIG / RUN_RECEIPT |
| P6 | 未开始 | 论文参考驱动 Figure Skill |
| P7 | 未开始 | 条件式分析与附录 |
| P8 | 未开始 | 基础设施整理，包括 generated metadata workflow 根因治理 |
| P9 | 未开始 | 综合回归、兼容与发布 |

## P3b 实施结论

P3b 分支 `refactor/optimization-p3b-writing-roles`、PR #155，从 P3a 合并后的 main `9cb5005b780c278953463d1ebeb891928974bb1f` 开始。

本阶段收束写作链职责：

- `core/writing_runtime_contract.yaml` 只负责阶段顺序、逐问 capability activation、条件读取和 fallback；
- `modules/05_writing/paper_writing_protocol.md` 继续拥有普通正文数学叙事与章节衔接；
- `modules/05_writing/ai_cleanup.md` 只做表现层 Keep / Compress / Re-subject / Delete，并保护 Formula bridge、Algorithm/Proposition、Claim Strength、Citation、Numeric、Title 与 stale 边界；
- `modules/06_review_delivery.md` 只负责检查、分级、返修排序和最终交付判定；
- 复杂数学语义继续由 `core/writing_reasoning_contract.yaml` 唯一拥有；Template Manifest 继续决定 CUMCM 固定骨架。

局部 Cleanup 默认只读目标 fragment、真实依赖和 Terminology/Numeric/Claim anchors；跨问依赖、Title/Abstract、assembled seam、全篇术语/数值冲突或 final review 明确需要时才扩大范围。Final review 保持全篇覆盖，不允许以抽样章节替代完整交付审查。

### 回归与首轮修复

首轮 CI 暴露三类历史实现耦合：

1. editable-mechanism 回归固定哈希保护本轮明确要改的 writing consumers；已改为继续固定保护 figure/model/numerical/state 等禁止触碰 Authority，而 writing Authority 由 P3b 专项测试保护。
2. Static lint 要求 Review Authority 保留 final-review matrix 的稳定 family/enum token；精简 Review 时一度删掉，已恢复稳定机器锚点但没有把普通正文规则复制回来。
3. 少量旧测试把 AI Cleanup 长篇措辞当 Authority；已保留真正的语义断言，例如 bridge relation 不得删、stepwise/pseudocode 按状态激活、final review matrix 不泄漏到写作 Authority，而去掉对旧段落全文的实现耦合。

未通过删除测试、降低模型/数值/figure 约束或跳过 gate 来解决失败。

### 最终验收

最终 head `f2d8baa796d590c2aa05ca0a9e23e46becf37695` 的 `HSK Skill CI` run `34939238023` 已 `completed / success`：Python 3.10、3.11、3.12、3.13、3.14、Static contract lint、Generated file contract、CUMCM/MCM-ICM/Diangong LaTeX 与 Production LaTeX attestation 全部通过。

生成器 bot 提交后使用 same-tree 用户身份空提交重新触发完整 CI；没有修改文件内容、没有跳过测试、没有绕过任何 gate。

P3b 合并后，P4 必须从最新 main 建独立分支，不能在本 PR 继续叠加 framework compact 实例化。
