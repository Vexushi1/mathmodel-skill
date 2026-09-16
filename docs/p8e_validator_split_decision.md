# P8e 大型 validator 结构整理裁决与 P8 收尾

> 本文件是维护证据，不是新的业务 Authority。静态检查语义、错误文本、调用顺序与完整门禁仍由现有 `scripts/lint_skill_checks.py`、`scripts/lint_skill.py`、测试与 CI 共同约束。

## 1. 决策背景

P8a 先建立基础设施测量基线；P8b 将 generated-metadata bot final head 自动接回现有完整 `HSK Skill CI` 与 `Optimization baseline evidence`；P8c 收敛两处 RUN_CONFIG/FULL_* 静态解析到共享语法 helper；P8d-1 再为大型 validator 增加顶层函数数量与函数跨度测量。

截至 `main@d8fc5a9868f11d95d9c424619383d10bb89d45d6`，`scripts/lint_skill_checks.py` 仍是明显最大的维护热点。P8d 的结构测量显示其共有 25 个顶层函数，其中最长的候选包括 `check_contracts`（260 行）、`check_templates`（179 行）和 `check_router`（100 行）。这些数字证明“体量集中”，但不能单独证明可安全拆分。

## 2. 对低风险拆分准入条件的复核

本轮重新读取最新 main 的 `scripts/lint_skill.py` 与 `scripts/lint_skill_checks.py` 后，发现当前静态检查器不是简单的“独立函数集合”，而存在显式 host-adapter 耦合：

1. `scripts/lint_skill.py` 以 `import lint_skill_checks as checks` 加载检查集合，并保存 `_ORIGINAL_READ_TEXT = checks.read_text`；
2. 它随后执行 `checks.read_text = _module_aware_read_text`，使 legacy 检查在读取 CUMCM 主模板时看到由真实模块拼接出的虚拟文档，而不是直接读取单一文件；
3. 它还对 `checks.check_contracts` 等检查函数做 wrapper/rebind，以承接当前 P7 条件式分析、活动 fragment 校验和其它 current-contract 适配；
4. `check_contracts` 与 `check_templates` 本身大量依赖同一模块级 `ROOT / read_text / load_structured / load_module / active_files` 语义；若直接移动到独立模块，默认 Python 名称绑定会绕开 `lint_skill.py` 对 `checks.read_text` 的当前适配，除非额外引入依赖注入、共享 context 或新的适配协议；
5. 这类额外协议已超出“纯结构移动、公开入口/调用顺序/错误文本/失败集合保持等价”的低风险范围，也会把 P8 从维护整理扩大为 validator 架构重写。

因此，当前函数边界虽然足以识别职责热点，却**不足以证明 `check_contracts` / `check_templates` 可以作为纯搬移拆分而不改变适配语义**。

## 3. P8 对大型 validator 的裁决

P8 在该项选择 **不拆 `scripts/lint_skill_checks.py`**。

这不是放弃维护，而是执行 P8d 已批准的 fail-safe 条件：没有充分证据支持低风险职责拆分时，不为了减少文件行数而强行制造新的模块边界。后续若要重构，应作为独立维护项目，先明确一套可测试的 lint context / adapter protocol，再迁移检查族；不能把该架构设计隐藏在 P8 的“结构整理”名义下。

本裁决保持：

- `scripts/lint_skill.py` 公开入口不变；
- 现有检查调用顺序不变；
- 错误文本与失败集合不变；
- module-aware `read_text` 适配不变；
- P7 current-contract wrappers 不变；
- drift guard、Static contract lint、Generated file contract、Python 版本矩阵、LaTeX 与 production attestation 均不减少。

## 4. P8 完成范围

P8 的已批准目标是“仅基于测量证据整理基础设施/大型 validator/重复解析与 generated-metadata 工作流”。当前形成的闭环为：

- **测量**：P8a + P8d-1 建立可复算文件热点、解析调用点与顶层函数跨度证据；
- **generated metadata**：P8b-1/P8b-2 让 bot-generated final head 自动调度原有两套完整门禁，替代人工 same-tree retrigger，但没有复制、裁剪或跳过测试；
- **重复解析**：P8c 只收敛有 P5a/P5b 行为回归保护的 RUN_CONFIG/FULL_* 静态解析，不机械统一全部 YAML 读取；
- **大型 validator**：P8d-1 测量后，本轮依据真实 host-adapter 耦合裁决“不拆”，避免无证据架构扩大。

因此 P8 已完成其批准范围；release carrier、P5a/P5b 兼容窗口裁决、Changelog/版本一致性和最终综合回归进入 P9 单独处理。

## 5. 回滚

本文件只记录维护裁决，可独立删除，不影响运行时。P8a–P8d 的实际实现分别保留各自 PR 的独立回滚边界。