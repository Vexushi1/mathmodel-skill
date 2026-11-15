# v10.32.0 — 文献辅助建模链正式发布
**发布日期：** 2026-11-15（以 GitHub Release 实际发布时间为准）
**发布级别：** v10.27.1 后的兼容性功能版本；当前 Skill 版本载体已在 v10.32.0，发布不再人为加号。

## 核心变化：审题 → 学术检索 → 自主模型设计

- **P1 / v10.28.0**：只读研究证据合同、E0–E3 来源等级、方法卡与有限有效性校验。
- **P2 / v10.29.0**：已冻结的逐问 Problem Contract 与独立结构评估之后、正式模型设计之前，执行有条件的真实学术研究、方法迁移分析；仍经原 Model Challenge 和 Human Approval。
- **P3 / v10.30.0**：显式授权的 Crossref/OpenAlex 限量元数据检索适配器；其检索记录最高是 E0 书目候选，**不自动获取全文、不能据此断言已验证论文公式**。如会话拥有已授权的网页/论文工具，模型设计可进一步阅读全文方法、假设和适用性。无工具/无匹配按合同诚实降级。
- **P4 / v10.31.0**：可选、须显式执行的研究证据来源快照与当前性核验，默认不修改项目状态、已批准模型或 accepted 数值。
- **v10.32.0**：包含独立仓库维护用 P6-A 历史题评价工具及来源目录；**它不进入正式建模路由或任何模型审批 / 发布门禁**。

## P5/P6 结案决议

- **P5**：不新增独立文献机器 Gate；已有 Model Challenge 中的来源与条件核验继续有效。
- **P6**：用户于 2026-11-15 明确停止三道 COMAP 历史题的双条件收益实验；[Issue #323](https://github.com/Vexushi1/mathmodel-skill/issues/323) 以 **Closed / not_planned** 结案，**不是完成真实盲评或证明收益**。P6-A CLI 及前期材料保留为独立、未激活的维护资料。
- 过时的旧版 docs-only 分阶段计划 [PR #317](https://github.com/Vexushi1/mathmodel-skill/pull/317) 已关闭而非合并，防止旧生成索引覆盖当前 main。

## 兼容性与权限

不更改 Project State、SIB/语义身份、独立两轮模型质询、用户明确锁模、用户本地 full-fidelity 数值执行、accepted 工作簿、Figure、LaTeX 或正式交付门禁。新模型路线检索按题目需要和当时授权工具决定，不设强制论文篇数，不要求对照收益实验来获得模型设计资格。真实外部论文的引用和数学迁移性仍须核验。

## 机器验收与发布范围

- 已合并 v10.32.0 及 docs-only 发布口径修复后的 **最终 Git Tag 所指 SHA**，应与该提交的 main HSK Skill CI、生成文件检查、相应 Optimization baseline 已验收证据一致；GitHub 正式对象可回查精确 commit。
- 之前完整主分支 HSK CI [#43681981722](https://github.com/Vexushi1/mathmodel-skill/actions/runs/43681981722)（v10.32.0 @ `483dc7aeb736c8264f94708ea8bbbc1deef7a950`）为 **Success**：Windows Python 3.10/3.14 各四分片与汇总、MATLAB R2024b Native、Python Figure、CUMCM/电工杯/MCM-ICM LaTeX、Static、Generated、Production Attestation 均通过。可选 Targeted Job 被按条件跳过。
- P6-A 的 [Optimization baseline #43609883271](https://github.com/Vexushi1/mathmodel-skill/actions/runs/43609883271) 为 **Success**；docs-only 发布说明修订应重新经最终 PR head 和合并后 main CI 验收。
- **机器 CI 不能证明任意论文真实、任意文献模型适配或具体赛题的数学/数值结论。** 实际检索 E0 与原文 E2 仍须使用当前可用、获授权工具，并记录来源与失效限制。

## 安装/回退

正式发布采用固定 Tag `v10.32.0`，不得把 GitHub main 的后续动态移动解释为已发布包。使用完整 Skill 仓库同一 tag 的源码，而不是仅拷贝 SKILL.md。升级不自动批准旧模型，既有项目零强制迁移。

仓库代码许可证及第三方素材依照现行 `LICENSE`、`THIRD_PARTY_NOTICES.md` 处理。GitHub Release 只使用 GitHub 自带源码归档，不附带 COMAP 原始 PDF/ZIP、用户项目数据或实验产物。
