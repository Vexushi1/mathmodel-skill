# AUD-02 协议裁决：辅助输入使用可选 RUN_RECEIPT 1.2

日期：2026-09-25。属于 `docs/v1010_audit_closure_remediation_plan.md` 的 S1 裁决，先于功能实现提交。本文件保留设计取舍记录，不是第二套运行时 Authority；字段与行为的当前权威为 `core/user_execution_contract.yaml`。

**实施记录：** 本轮分支已经实现下述协议，本地完整1724项测试无失败；Python合成主/深化实际运行、旧固定基线reader拒绝1.2、同步/打包/迁移和来源变化反例均已验证。MATLAB原生与最终多平台结果以 [PR #236](https://github.com/Vexushi1/mathmodel-skill/pull/236) 精确最终head的CI为准；这不代表已发布Release或已迁移用户项目。

## 为什么不能把辅助字段直接加进 1.1

原1.1 reader不一定拒绝未知字段，特别是已定位的runtime输入资格缺口。直接塞入辅助路径/摘要可能被旧检查器忽略。因此先于实现否决初稿的1.1扩展，冻结可选1.2；仅靠Skill版本或未知feature字段不足以隔离。

## 冻结方案

- 无辅助输入：继续主/深化回执1.1；旧1.0/P5a/FULL按原只读兼容。
- project_level主/深化确需独立附件时：配置 `run_receipt_protocol_version: 1.2.0`，回执 `run_receipt_version: 1.2.0`。
- 1.2必须为 `data_identity_mode: preprocessing_workbook`，主 `data_paths` 为唯一accepted预处理XLSX，主 `data_sha256` 仍普通文件SHA。
- 必须完整提供 `auxiliary_data_paths` 和 `auxiliary_data_sha256`；没有辅助输入不得使用1.2，项目级预处理仍1.0，旧协议不得携带辅助扩展。
- 辅助集合摘要复用现有combined_hash；source bundle算法仍1.1，不新增State Schema数值事实副本。
- 回执辅助路径采用JSON文本，严格解析并与已交付配置逐项匹配；摘要大小写等价。
- 解析、交付、验收、runtime、sync、复现包与迁移预览一起识别1.1/1.2共享源码绑定，不只放宽一个版本白名单。
- 实际输入观察核对当前辅助字节；正式运行入口在前后核对源码、主数据和辅助数据。
- 辅助路径不能越界、缺失、别名/重复、与主输入相同或重读covered_raw_sources；运行回执不是覆盖原始数据边界的授权。
- 旧版本遇1.2保持unknown-version拒绝，不改旧实例版本以求通过。回退不能删字段伪装1.1；应保留新实例并使用支持1.2的工具核验，或重新交付运行新的合法实例。

## 不变量

模型批准、项目统一Python/MATLAB后端、PQS、Analysis Necessity Gate、accepted主结果绑定、原始源保护和数值精度不变。新协议不自动迁移任何项目，不自动形成批准或accepted结果。

## 必须持续保留的回归

1. 合法无辅助1.1仍通过；旧1.0控制不受无关扩展影响。
2. 旧协议携带辅助字段、新1.2缺字段/半字段/错模式均拒绝。
3. 配置和回执版本不一致拒绝，不降级。
4. 原固定基线stage binding和receipt reader对1.2拒绝，不冒充完整支持。
5. 辅助文件改动/删除、覆盖原源、主/辅助别名与重复拒绝。
6. 回执JSON错误、摘要冲突、路径不符拒绝。
7. Python/MATLAB原生合成运行，sync/package/迁移完整收集来源。
8. 回执验收期间来源改变不得写入新的accepted身份。

计划进度、失败与修复历史见主计划和PR实际记录，不能仅修改状态文字就宣称验收完成。
