# AUD-02 协议裁决：辅助输入使用可选 RUN_RECEIPT 1.2

日期：2026-09-25。属于 `docs/v1010_audit_closure_remediation_plan.md` 的 S1 裁决，先于功能实现提交。本文件修正主计划第 6 节中“在 1.1 上增加可选字段”的初步设想；主计划其余边界不变。尚未实现，不是当前正式规则。

## 为什么不能把辅助字段直接加进 1.1

原 1.1 reader 不一定拒绝未知字段，特别是上轮已定位的 runtime 输入资格缺口。把新路径/摘要直接放入 1.1，旧检查器可能忽略辅助文件而仍声称 current。因此仅靠 Skill 版本、文档或一个未知 feature 字段不足以形成协议隔离。

## 冻结方案

- 无辅助输入：继续使用主/深化回执 1.1.0；旧 1.0/P5a/FULL 按原只读兼容。
- project_level 的主/深化计算需要未被统一工作簿覆盖的辅助附件：使用配置 `run_receipt_protocol_version: 1.2.0` 与返回回执 `run_receipt_version: 1.2.0`。
- 1.2 必须具有 `data_identity_mode: preprocessing_workbook` 以及完整的 `auxiliary_data_paths`、`auxiliary_data_sha256`；主 `data_paths` 仍为唯一 accepted 预处理 XLSX，主 `data_sha256` 不变。
- 1.2 不允许没有辅助输入，不用于项目级预处理（后者仍为 1.0）；1.1/1.0 不得携带辅助输入扩展。
- 辅助摘要沿用现有 combined_hash 的路径/原始字节身份，不改变 source bundle 1.1 算法，不新增 State Schema 数值事实副本。
- auxiliary 路径列表在回执中使用 JSON 文本表示以适配 XLSX 单元格；比较时解析为严格字符串列表，集合身份与已交付配置一致；辅助摘要按 SHA-256 大小写等价核对。
- helper 解析、交付、验收、runtime、sync、复现包和迁移预览必须同时识别 1.1/1.2 的共享源码绑定，而不是只改一个 validator 的版本白名单。
- 实际输入观察始终检查辅助字节，不能从状态或回执自报值推导“当前输入未变”。正式生成入口在运行前后均核对源码/主数据/辅助数据。
- 旧版本遇到 1.2 必须保留原来的 unsupported-version 拒绝；不为兼容而篡改旧实例版本。回退 Skill 前，应保留新实例并用支持 1.2 的工具只读核验，或明确重新交付/运行 1.1 无辅助实例，不能去掉字段伪装旧格式。

## 不变量

模型批准、项目唯一 Python/MATLAB 后端、PQS、Analysis Necessity Gate、当前 accepted 主结果绑定、covered_raw_sources 禁止重读、所有路径边界、数值精度与原始文件保护不变。新增 input 扩展不会自动迁移任何用户项目。

## 验收补充

1. 旧 1.1 合法无辅助实例继续通过。
2. 1.1 携带辅助字段、新 1.2 缺字段/半字段/错模式均拒绝。
3. 配置 1.2 + 回执 1.1（或反向）拒绝，不降级。
4. 旧固定基线的 stage binding 与 receipt 检查对 1.2 拒绝；不能称旧 reader 支持完整新输入。
5. 辅助文件替换、缺失、覆盖原始源、与主文件/另一辅助文件别名或重复时拒绝。
6. 回执路径 JSON 错误、字段缺失、摘要冲突和未登记新增输入均拒绝。
7. Python/MATLAB 原生合成样例与 sync/package 输入收集闭环验证。

实施时在主计划回填本裁决与真实测试结果；不能只更新本文件状态就宣称 AUD-02 修复。
