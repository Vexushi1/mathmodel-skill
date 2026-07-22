# 竞赛自动选择

从用户明确名称、题面抬头、模板或附件识别 CUMCM、MCM/ICM、电工杯、认证杯。无法识别时使用通用规则，不凭空套用某竞赛格式。竞赛适配器只负责格式与评审侧重点，不覆盖核心建模规则。

机器入口为 `config/competition_profiles.yaml`：

1. `stable` 只保存相对稳定的模板、编译 Profile、语言和 Pack 路径；
2. `edition_rules` 保存页数、匿名、提交文件、AI 披露等时效性规则；
3. `verification_status` 不是 `verified` 时，不得把默认值表述为当届官方要求；
4. 当届规则必须记录 `verified_at` 和官方来源；旧年度规则到期后标记 `expired`，不得静默复用。

竞赛识别与题型分类相互独立：竞赛决定格式和交付约束，题型决定变量、模型、验证和结果表结构。
