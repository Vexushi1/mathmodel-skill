# v10.27.0 Runtime 非退化优化：R1 机器验收与候选处置记录

> 本文件是 maintenance / evidence-only，不是运行时 Authority、审批记录、人工评审或版本发布声明。权威仍为 R1 计划、SKILL_CHANGE_GOVERNANCE.md、当前 Router/Resolver/Project State/Review Receipt 等活动源。

## 1. 证据身份与机器验收范围

- **冻结源版本**：main@b3388db438757576818b6f8a2aaaeb33eb9c1226，core/bootstrap.yaml 中 Skill 10.27.0；本文件在此后另起 docs PR，其最终 head/合并后 main 均需独立正式验收。
- **最终已合并实现的主分支 CI**：[HSK CI #43378504458](https://github.com/Vexushi1/mathmodel-skill/actions/runs/43378504458)，head SHA 与上述 main 完全相符，SUCCESS：20 个 success（Windows Python 3.10 和 3.14 每版本四分片及汇总、Static、Generated、MATLAB Native、Figure 3.10/3.14、三类 LaTeX、Production Attestation、Regression）；1 个条件性 targeted checks skipped，**未计作 PASS**。
- **阶段 PR 与合并后正式 CI**：[G4-B #310](https://github.com/Vexushi1/mathmodel-skill/pull/310) → [#43354696506](https://github.com/Vexushi1/mathmodel-skill/actions/runs/43354696506)；[G4-C #311](https://github.com/Vexushi1/mathmodel-skill/pull/311) → [#43364210509](https://github.com/Vexushi1/mathmodel-skill/actions/runs/43364210509)；[G5 #312](https://github.com/Vexushi1/mathmodel-skill/pull/312) → [#43370457273](https://github.com/Vexushi1/mathmodel-skill/actions/runs/43370457273)；[G6-A #313](https://github.com/Vexushi1/mathmodel-skill/pull/313) → [#43378504458](https://github.com/Vexushi1/mathmodel-skill/actions/runs/43378504458)。各列主分支正式 CI 均 SUCCESS。
- **证据归档**：[G6-A Optimization #43373665703](https://github.com/Vexushi1/mathmodel-skill/actions/runs/43373665703)，artifact 名 optimization-p2-evidence、ID 14013442875、对应实验 head e4b5ea06defad9fb6bd0c56b476ed5beec595770。下载归档 SHA-256 为 91048196767d2f09f634cced8bb3e42c3e851e731ca8f14d380d41a2c60fcb03。本记录中的数字取该归档原始 JSON；实验 SHA 与 merge commit 不应混淆。

**范围声明**：本报告验证的是指定合成样本中的机器行为、来源身份和正式 GitHub CI，**不**验证实际赛题的数学正确性、用户计算/accepted 工作簿、人工审批、PDF 逐页、真实 ChatGPT Token/完整用户延迟或真实提交结果。

## 2. L/P/N 三套基线：不混用比较器与样本

| 证据通道 | 原始报告 | 审计结果 | 限制 |
|---|---|---|---|
| L，历史 16 例 | comparison.json | 16 例，all_equal=true；PASS_MACHINE | P1 历史比较，不是当前任务体验收益 |
| P，19 例 Reading Plan | p2-comparison.json | 19 例，all_legacy_behavior_equal_except_approved_changes=true；PASS_MACHINE | 原 all_legacy_behavior_equal=false，存在合法历史版本/Authority 例外；不可称零差异 |
| N，10.27.0 的 8 例 | v10270-comparison.json | status=pass；approved_delta_count=12；unapproved_delta_count=0；PASS_MACHINE | 12 条已登记行为差异不能抹去，也不是实际项目质量评价 |
| G1B 独立动作正反例 | v10270-g1b-action-observations.json | 12 cases；无缺失动作场景、无安全冲突；PASS_MACHINE | 只覆盖合成 oracle；没有 Gate PASS、数值运行或真实工具消费证明 |

主分支 CI PASS 与 L/P/N 报告相互补充，不可取代真实业务 Gate 或人工语义评估。

## 3. G0–G6 候选的保留/拒绝/延期裁决

| 阶段 | 最终处置 | 有证据支持的边界 |
|---|---|---|
| G0 维护计划 | **保留** | R1 计划是实施/STOP 指南而非第二套 Runtime Authority |
| G1A/G1B 基线与动作 oracle | **保留** | L/P/N 分离；G1B 当前合成 12 例无漏选/安全冲突 |
| G2 正确性修复 | **保留已验收修复** | N：8 例，unapproved=0；两载体历史保护不因为优化被取消 |
| G3-A 计划展示 | **不推出新生产对象** | 20 合成场景的 JSON 投影中位大小比 0.59358，纯字节/可见展示实验，非真实 Token |
| G3-B 批量读取 | **保留只读试验，不增生产批量 API** | 原文一致；一个试点的 Git 子进程中位数 15→8，测试进程时间 1.204→0.484 s；尚缺实际宿主、触发条件和项目来源完整消费证明 |
| G4-A 预解析复用 | **暂缓生产 API** | 微基准不足以证明可变项目状态/完整来源核验下的收益 |
| G4-B selector index | **测试完成，不部署生产索引** | PR #310 的 Markdown 小幅 CPU 收益，YAML AST index 未测，不支持新增维护边界 |
| G4-C question→paper stale | **测试完成、生产公共闭包归并延期** | PR #311 双消费者差分通过；第三消费者 project_solver_backend.py 的迁移预览依赖 sync_project 原入口，lint 有函数名依赖；无完整事务链及收益证明 |
| G5 混合意图组合 | **生产不准入** | v10270-g5-composability-admission.json 两个混合场景均 NOT_ADMITTED：有跨动作依赖、Gate 次序/参数及读集覆盖缺口 |
| G6-A 阻断诊断缩读 | **测试完成，生产不准入** | v10270-g6a-diagnostic-admission.json 六个合成场景，仅模型审批缺失和旧图未批准生成候选诊断来源；计划字节 388174→12462 与 544592→44491，未证实真实 Token 与诊断充分性；另四例拒绝错误快捷路径 |
| G6-B 局部只读 Review | **DEFERRED / STOP，不实施新增生产 profile** | 现有 Module 06 已支持 Draft/Final 不同读取闭包与局部核查；暂无更窄范围仍覆盖必要 Authority 且改善真实成本的证据 |

### G6-B 的独立准入审查

- 现有 core/module_manifest.yaml 的 review_delivery.reading_sources 为 Draft = entry + content，Final = entry + content + final，已在 tests/test_reading_module06.py 等回归约束。
- modules/06_review/final_delivery.md 明确允许按 physical file/question/check family 分批，但每个 active file、current question、headline claim 和 required gate 都必须 covered；只看部分章节不能宣称整篇 PASS。
- core/review_receipt_contract.yaml 的 partial_recheck 仅覆盖已声明的 object/check IDs；局部只读意见**不能**创建或替代完整 draft_semantic_review / final_review_and_delivery PASS 与正式 review_receipt。
- 因此 G6-B 不是已有功能失效的修复。缺真实 project scope、完整所需原文、实际阅读工具成本和至少一个可安全缩读的正反例之前，不通过更高风险的生产立项；不为填阶段而另建第二套 Review Authority。

## 4. 非退化边界、成本未测项和人工保留

- **保留的机器边界**：原 Router/Assured Runtime 的选中意图、5 个执行片段、11 模块/12 工具职责、有效 Gate 顺序、项目模型批准/用户执行边界、source commit/SHA/snapshot、typed stale、claim stale 与 Project Transaction read-set/generation，不在本审计中重新赋权。
- **实际未测**：actual_read_tokens、完整 GitHub-only 工具消费成本、用户端端到端时延、生产环境跨代项目状态安全、真实模型审稿解释充分性；不得按 planned bytes 外推减重百分比。
- **必须保留为 PENDING_MANUAL/NOT_ASSESSED**：真实赛题逐字审题、公式/约束闭合、双轮 Model Challenge 与用户明确审批、原始数值与残差/收敛、accepted workbook / RUN_RECEIPT、图表人工审核、PDF 逐页核查、官方赛规与提交包验收。机器全绿不等于数学或论文质量全称保证。
- **未来重启的硬门槛**：G4-C、G5、G6 任一生产候选必须在独立新 PR 中先证明必要性、正确性、完备来源读取、兼容/事务及真实可复算收益；未证明者继续 STOP。不得更改历史已批准期望来伪造通过。

## 5. 本维护报告的关闭流程

本 docs-only 单主题 PR 不修改生产 code、Schema、CLI、Authority、项目或版本；GitHub refresh-generated 维护 SKILL_FILE_INDEX.md / MANIFEST.sha256，不得手改。只有 **报告最终 bot-generated head 的正式 HSK CI 与适用 Optimization 全绿 → 合并 → 合并后 main 同 SHA 正式 CI 全绿**，才能把 R1 维护记录判为 COMPLETED_MACHINE_CLOSEOUT。本文冻结在上述源码基线；如果后续修改 main，重新核查对应 SHA。

**总结**：R1 在所记录的机器可验收边界内可以进入文档收尾；有独立收益的证据不等于已上线，缺准入的高风险候选明确延期，科研人工边界未宣称完成。
