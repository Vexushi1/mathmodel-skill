# v10.27.1 — 双动作路由修复与 R1 非退化验收

这是基于既有 v10.27.0 正式 Release 的**兼容性补丁版本**。重点修复明确双任务请求中的动作遗漏，并将随后完成的非退化对照、来源安全和性能准入研究纳入正式发布证据；**没有默认启用未获准入的性能快捷路径**。

## 主要修复

- **G2：有界双动作识别**。当用户未提供显式 intent，且请求明确包含两个非否定的正向动作分句时，Resolver 能在以下两类组合中保留两个动作：**图表修改/制作 + LaTeX 论文调整**、**模型检验 + LaTeX 论文编写**。两个分句必须分别有唯一最优 Router 命中；不采用对所有命中关键词的广泛合并。
- **安全回退**。显式 intent 的优先级、审稿只读语义、Word/LaTeX 载体消歧、否定与歧义条件、full_workflow 优先、原业务步骤、Gate 和暂停边界保持不变。仅识别两个动作**不代表**可并行执行、免除批准或缩减原文读取。
- **证据性修复**。独立动作 oracle、拒绝误分派的负例、历史路由投影和精确 G2 approved delta 对照构成回归依据。

## 运行时非退化与性能准入

完成 R1 的分阶段审计与回归，不把微基准自动转为用户端性能承诺。

- **G1**：保留三个分开的对照通道：历史 L（16 例）、Reading Plan P（19 例）和 v10.27 新版 N（8 例）。N 报告有 12 项明确批准差异、0 项未经批准差异；G1B 12 个独立标注动作样本未发现漏分派或安全冲突。
- **G3–G4**：记录计划呈现、批量原文读取、预解析和选择器索引的成本及差分结果。无充分实际收益或完整安全证明的缓存/批量 API 未推入生产；G4-C 的问题级 paper-fragment stale 双消费者差分已增加测试，生产公共闭包归并仍延期。
- **G5**：两组混合动作的有效执行计划存在上下游依赖，未达到安全组合准入，继续保守完整读取。
- **G6**：缺模型批准/旧图无当前批准的诊断候选经过合成检查，但实际解释充分性与消费端 Token 收益未证明；生产诊断缩读未开启。G6-B 局部只读 Review 已有部分能力，未创建新的 Review Authority/回执快捷路径。

## 兼容性与升级

本次为 **patch 版本（v10.27.0 → v10.27.1）**，不变更项目状态 Schema、公开 CLI、项目目录、accepted 工作簿格式、数值/绘图后端选择、用户数值执行职责和独立协议版本。Model Challenge、Human Model Approval、来源身份、typed stale、正式 Figure/Review/LaTeX/交付 Gate 继续按原 Authority 执行。

升级时使用完整仓库的 v10.27.1 Tag/源码而非仅复制嵌套 SKILL 子目录。重新核对 core/bootstrap.yaml、根与嵌套 SKILL.md、插件 metadata 的版本；旧读取计划遇到来源 SHA/Authority/commit 变化时，需重新运行 resolve_runtime.py 获取有效计划。**下载最新版本本身不会批准旧模型或重新验收旧数值结果。**

## 验收与适用范围

本版发布候选的前置基线为 main@21357bb301d057c98fc172b576eed72e69538e90，其 [HSK CI #43409330115](https://github.com/Vexushi1/mathmodel-skill/actions/runs/43409330115) 为 SUCCESS：Windows Python 3.10/3.14 各四分片及汇总、Static、Generated、MATLAB R2024b Native、Python Figure 3.10/3.14、CUMCM/Diangong/MCM-ICM LaTeX、Production LaTeX Attestation 全部通过；1 项条件性 targeted checks 为 skipped，不计作 PASS。

**发布门**：仍须以 v10.27.1 版本载体 PR 的最终 bot-generated head 完整 GitHub CI、合并后实际 main SHA 的正式 CI 为准。创建 Release 时 Tag 必须指向该已验收的合并后 main SHA；不得重用或移动旧 v10.27.0 Tag。

[完整非退化验收与候选处置](https://github.com/Vexushi1/mathmodel-skill/blob/main/docs/v10_27_runtime_nonregression_closeout.md)；[自 v10.27.0 起的完整变更](https://github.com/Vexushi1/mathmodel-skill/compare/v10.27.0...v10.27.1)（此链接在 v10.27.1 Tag 正式创建后生效）。

**验收限制**：上述 CI 和合成实验属于软件/契约机器证据；真实赛题模型、数值复演、Figure 人工核验、最终论文逐页和官方赛规验证仍需在具体项目内单独完成。actual_read_tokens 与真实端到端用户延迟仍未测量。

本仓库自有代码按 MIT 许可分发；第三方材料按仓库 THIRD_PARTY_NOTICES.md 及其原许可适用。GitHub Release 使用 GitHub 自动生成的 source code ZIP / tar.gz，不附带未经核验的竞赛数值产物。
