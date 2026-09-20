# v9.4.0 写作可读性与审查减重 Release Closeout

> 本文件是 W5 发布/验收记录，不建立新的 Writing、Review、Runtime、Modeling、Numerical 或 Project State Authority。业务语义仍由 Bootstrap 指向的 current Authority 拥有。

## 修改简报

- **修改主题：** W5——对写作可读性与检查减重计划 P0 / W0–W4 / Part C–G 做综合回归、版本裁决和 release carrier 收尾。
- **当前版本：** 9.3.1；release 起点 `main@e8fd923e6273b9fe644d506ecc8c3b3372d7e4a6`。
- **目标版本：** 9.4.0。
- **变更等级：** minor。
- **直接目标：** 统一活动 release carriers；发布已经在主干验收的写作/审查行为；保留 W3 的证据化最小减重；完成 release regression、CHANGELOG/README 与状态记录。
- **明确不做：** 不重新修改 W1–W4 业务实现；不新增 Gate、required Project State、Schema、CLI、目录、readability score、跨运行缓存或 trust token；不改模型、数值、Workbook、03A/03B、MATLAB 数值事实链和 Human Model Approval。
- **权威事实源：** `core/bootstrap.yaml`、`SKILL_CHANGE_GOVERNANCE.md`、Writing/Review Authorities 与 `docs/writing_readability_validation_slimming_plan.md`。
- **预计修改文件：** 活动 release carriers、README、CHANGELOG、维护状态、release regression、计划状态与 generated metadata。
- **禁止触碰：** 历史 release/PR provenance、legacy 基线、已批准模型/数值合同及 W0 不准入的检查候选。
- **兼容性要求：** 公共 CLI/report shape、Project State、Model Approval、Workbook/output、用户执行与旧项目读取保持；非 CUMCM/DOCX 继续使用既有 fallback。
- **迁移要求：** 无强制用户迁移。
- **验收测试：** 完整 HSK Skill CI、Optimization baseline、Python 3.10–3.14、Static contract lint、Generated file contract、CUMCM/MCM-ICM/Diangong LaTeX、Production LaTeX attestation。
- **回滚方式：** 整体回滚 W5 release-carrier/doc/test 更新即可；W0–W4 已合并能力仍可在 9.3.1 carrier 下运行。

## 版本裁决

### 为什么不是 9.3.2 patch

本轮已经超出“修复一个错误但保持现有能力集合”的 patch 范围。W1–W4 新增并验收了向后兼容的写作/审查能力：

- 非显然核心推导与核心证明按数学作用保留在正文；
- 评委可读的标题/首次术语解释；
- 结果表 display layer 与 accepted 数值/单位/精度事实层分离；
- 公式密集段落按推理单元组织；
- 正式论文一级至三级标题正常可用、明确四级及以上活动 LaTeX 标题阻止正式交付；
- 长核心证明真实跨页、编号和引用的 CI 验收；
- T01–T18 的机器/语义/hybrid 综合行为验收。

这些属于新增的向后兼容能力，因此按治理规则使用 minor。

### 为什么不是 major

没有破坏性目录、Schema、CLI、required state、报告 shape 或生命周期迁移；Model Approval、Semantic Identity、typed stale、Workbook/numerical、03A/03B、用户执行和旧项目读取边界保持。因此不存在 major migration 条件。

## 检查减重边界

W0 的证据化裁决仍是唯一减重依据。W3 只移除了 count-only `question_subsection_granularity` review finding；以下内容保持：

- `possible_mechanical_model_subsection_split`；
- `framework_subsection_granularity_pending`；
- result→validation、solver-first、question-stage-order 等 surface review；
- draft 与 Cleanup/assembly 后 formal surface 复验；
- duplicate label、missing ref/BibTeX、claim-scope、stale/包级等 Hard 路径。

没有引入跨阶段缓存、持久信任 token 或“检查更少即更正确”的结论。

## W4 前置验收

W4 PR #207：
- final head：`06ace7b99bd7977b74c34fc9f7e554b16f576318`；
- HSK Skill CI workflow_dispatch #3838：success；
- Optimization baseline #355：success；
- merge：`e8fd923e6273b9fe644d506ecc8c3b3372d7e4a6`；
- merge 后 main HSK Skill CI #3840：success；
- metadata refresh #2527：success。

T01–T18 细节见 `docs/writing_readability_w4_acceptance.md`。

## 活动 release carrier 范围

W5 仅同步当前 release identity：

- `core/bootstrap.yaml#skill_version`；
- `.codex-plugin/plugin.json#version`；
- 根与 packaged `SKILL.md`；
- `README.md` 当前标题与 v9.4.0 摘要；
- `core/hsk_core_policy.md` 当前版本标题；
- `core/workflow_router.yaml#version`；
- `core/module_manifest.yaml#version`；
- `core/output_contract.yaml#version`；
- `core/writing_runtime_contract.yaml#version`；
- `config/prose_audit_patterns.yaml#version`；
- `CHANGELOG.md` 当前 release；
- generator 管理的 indexes / MANIFEST。

Subordinate schema/version、historical plan/provenance 与 legacy 记录不做全仓替换。

## 最终验收

Release PR #208 的最终 generated head 为 `81492db887439a6afffa4f9e36702f4b686c5f67`。该 SHA 的正式验收结果：

- HSK Skill CI workflow_dispatch #3843：success；
- Optimization baseline #356：success；
- Python 3.10 / 3.11 / 3.12 / 3.13 / 3.14：全部 success；
- Static contract lint：success；
- Generated file contract：success；
- LaTeX CUMCM / MCM-ICM / Diangong：全部 success；
- Production LaTeX attestation：success，其中长核心证明真实分页与命题/公式引用编号 fixture 继续 success。

PR #208 squash merge 为 `551054e695a11a8f49399619b833635577b7215e`。合并后 main 后验：

- HSK Skill CI #3845：success；
- Refresh generated repository metadata #2529：success。

## 发布结论

**v9.4.0 release closeout：COMPLETED。**

本次发布没有新增破坏性迁移，没有降低 Hard/Default 数学、数值、引用、stale 或交付标准，也没有引入新的 Readability Gate / Project State required 字段 / coverage family / persistent trust cache。当前仓库治理未要求额外 GitHub tag/release object；活动 release carriers、CHANGELOG、PR 历史及上述真实 CI 作为发布证据。
