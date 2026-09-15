# Skill 全面优化实施记录

## 已批准范围与基线

2026-09-15，用户在审阅《Mathmodel Skill 全面优化计划》后明确表示“全部都批准，考虑开始进入优化部分”。本记录落实该批准，不重新定义业务 Authority。

- 批准文稿：`mathmodel_skill_optimization_plan.md`，80,455 bytes。
- 原文 SHA-256：`05808d566177dd44b3bbf924db43fad5a239c6b5d599b5faa9cc0f65af8fd365`。
- 设计与实施起点：`8a92a7924e950939dc77b15d3bb1a88400c09979`，Skill v9.1.0。
- 实施前已重读 main 的 `core/bootstrap.yaml`、`SKILL_CHANGE_GOVERNANCE.md`、`AGENTS.md`，开放 PR 查询为空。
- 完整设计稿仍以用户批准的上述文稿为准；本文是实施登记，不声称是该 20 节文稿的全文副本。

批准覆盖基础优化、配置/回执分离、论文参考驱动绘图、条件式分析和附录方案。批准不撤销各项前提：基础设施仍需测量证据；非 MATLAB 后端仍非本轮必要前置；精度与官方 Adapter 仍独立迭代；最终版本依据实际兼容性在发布时裁决。默认不删旧 reader、不修改旧项目、不直接写 main。

## 分阶段执行

| 阶段 | 主题 | 状态 |
|---|---|---|
| P0 | 计划与范围审批 | 用户已批准 |
| P1 | 可重算的读取与行为基线 | 已合并，PR #152，`0eecaf929c83f19555402564ea0b14743d9bcf7d` |
| P2 | 读取范围、事实同步和工具调用分流 | 已合并，PR #153，`2a9cb227067d58d52471f164d317be3b4be330fe` |
| P3a | 全局政策去重与来源映射 | 已合并，PR #154，`9cb5005b780c278953463d1ebeb891928974bb1f` |
| P3b | 逐章/局部写作读取与 Cleanup/Review 职责收束 | 最终 CI 已通过，PR #155 待合并 |
| P4 | compact framework 实例化与渐进登记 | 未开始 |
| P5a/P5b | RUN_CONFIG 命名、版本化回执 | 未开始 |
| P6a/P6b | 论文图例索引、独立 MATLAB profile、真实预览 | 未开始 |
| P7 | 条件式分析与附录 | 已获范围批准，尚未实现 |
| P8 | 有测量依据的基础设施整理 | 未开始 |
| P9 | 综合回归、兼容与发布 | 未开始 |

## P1 修改简报

P1 固定代表请求并建立真实 resolver 的只读、可重算资源与行为基线。该阶段不改变业务 Authority，完整证据见 PR #152；P1 的零差值只表示基线建立成功，不是优化收益。

## P2 修改简报与结果

P2 在不删除旧 `load_order`、machine dependency closure、审批/identity/stale/gate 的前提下，新增 additive `reading_plan`，将当前必读、条件资料与工具接口分开。事实同步、纯样式返修均要求现有 file-backed evidence；缺证据、歧义、语义变更、mixed intent 均完整回退。P2 已合并，PR #153，合并提交 `2a9cb227067d58d52471f164d317be3b4be330fe`。

## P3a 修改简报与结果

P3a 收束默认必读 `core/hsk_core_policy.md`，从 20,016 bytes 降至 10,788 bytes，约减少 46%；只保留真正跨阶段 Hard，将目录、工作簿、预处理、Figure、普通写作和兼容细节回指唯一 Authority。新增 source map 和回归，旧测试由 Core Policy 文本耦合改为验证真实 Authority。最终 head CI 全绿后合并，PR #154，合并提交 `9cb5005b780c278953463d1ebeb891928974bb1f`。

## P3b 修改简报、实现与最终验收

**分支/PR：** `refactor/optimization-p3b-writing-roles`，PR #155。

**等级/版本：** minor-compatible / semantic-preserving refactor；Skill release carrier 保持 9.1.0，本阶段不发布新版本。

**直接目标：** 把普通写作链明确拆成：Runtime 调度读取与 capability；Protocol 管普通正文数学叙事；Cleanup 只做表现层清理与必要推理保护；Review 只做检查、分级、返修和交付。局部写作/清理默认保持局部，不因为“完整”机械读取或重写全文。

**唯一 Authority：** `core/writing_reasoning_contract.yaml` 继续负责复杂数学语义，`paper_writing_protocol.md` 负责正文组织，`writing_runtime_contract.yaml` 负责写作时序/Preflight/activation，Template Manifest 负责一级骨架。Cleanup/Review 是 consumer，不建立平行正文规则。

**保护边界：** 不修改 Model Approval、structured identity、typed stale、工作簿、数值验证、03A/03B、五文件、赛题 Python/MATLAB、CUMCM 一级骨架、赛事规则或 release carriers；无用户项目迁移。

### P3b 实施

- Runtime 增加 explicit operation scope / expansion triggers，继续保留 Template-First progressive authoring、per-question capability preflight、MCM/DOCX full-authority fallback。
- Paper Protocol 继续作为普通正文 Authority，并明确 local-edit boundary：局部编辑只读取目标 fragment 和真实依赖；Title/Abstract、跨问依赖、assembled seam、全篇术语/数值冲突等才扩大范围。
- `ai_cleanup.md` 从约 33 KB 收束为约 13 KB 级别的 consumer：保留 Integrity、Formula/bridge protection、Terminology/Numeric/Citation/Claim、Keep/Compress/Re-subject/Delete、Paragraph Necessity、Figure Result Narrative、Heading Compression、machine diagnostic boundary；删除对上游 Authority 的大段复述。
- `modules/06_review_delivery.md` 从约 39 KB 收束为约 15 KB 级别的 review consumer：保留 draft/final 两时机、full coverage、check families、blocking/review_required/warning、machine/manual boundary、final submission evidence sweep；不复制正文写作手册。
- 新增 `docs/p3b_writing_role_source_map.md`、fixture/test，保护 FW05--FW09 能力和边界，确保必要 bridge derivation 不被 Cleanup 破坏，full-paper review 不能抽样代替完整覆盖。

### P3b CI 诊断与修复

第一次真实 CI 暴露两类维护耦合：旧保护测试把 `paper_writing_protocol.md`、`ai_cleanup.md`、`review_delivery.md` 的历史 blob SHA 固定为不可变；`lint_skill_checks.py` 又要求 Review 文件继续重复完整 final-review token/family 定义。修复时没有删除规则，而是把保护改为：复杂数学 Authority 继续锁定，Cleanup/Review/Protocol 的职责能力由 P3b source-map + behavior tests 守护；final-review stable families 继续由 `templates/review/final_review_matrix.yaml` 和 scorer 验证，Review module 只需消费/覆盖而不复制完整矩阵。

最终业务修复 head 经过生成器刷新，再使用 same-tree 用户身份空提交触发完整 CI；该动作不改变文件内容，不跳过任何检查。

### P3b 最终验收

最终 head：`6aea56326d6d78cfdf9a7ea399331ba5c1cd82e3`。

- HSK Skill CI run `34979879324`：completed / success；Python 3.10、3.11、3.12、3.13、3.14，Static contract lint，Generated file contract，CUMCM/MCM-ICM/Diangong LaTeX 与 Production LaTeX attestation 全部通过。
- Optimization baseline evidence run `34979879072`：completed / success。
- 最终生成文件已 current；没有通过删测试、降断言、绕过 gate 或关闭 CI 达成全绿。

P3b 合并后，P4 必须从新的 `main` 独立建分支，处理 compact framework 的真实实例化、渐进登记与可派生视图，不能在 P3b 分支继续叠加。