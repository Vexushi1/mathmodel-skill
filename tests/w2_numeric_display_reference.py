"""Exact D02 W2 display-only inverse for historical writing snapshot tests.

Only the approved text hunks are inverted. Historic W1 hashes and negative
guards remain unchanged. No runtime or document delivery code imports this.
"""
W2_D02_SOURCE_IDENTITIES = {
    "core/writing_reasoning_contract.yaml": [
        "d34d95e774c3f61bbff8cd5c56e22e5acfe42a8202f7530c292413d5415d1b98",
        "b25bb618385b3d6da148b5cbf11ec9183044218956d2b0a25b1491d3da91f08f"
    ],
    "modules/05_writing/paper_writing_protocol.md": [
        "ec5e1b95336dd6fc72114a2e2a62c5c96f2f2bbec48533c353adec158693e2a8",
        "a2f82d2f9caf391594b4083950a8b9899caefd491f9fe48571be156bbee631b1"
    ],
    "modules/05_writing/ai_cleanup.md": [
        "10f5e9b6c8a315bb888893eca03fecb9a772a0f4397cedbee669e8b2014fecf6",
        "8e4b4772d6f2afbb70a6b2e27f12b81a6e41f7bf7a02aafa8a218c19d274cf22"
    ]
}
W2_D02_APPROVED_REWRITES = {
    "core/writing_reasoning_contract.yaml": (
        ("numeric_style_contract:\n  governance_level: default\n  principle: >-\n    题目明确规定论文数值精度时服从题目及已核验的官方输出格式；未明确要求时，\n    论文数值默认保留小数点后两位。这是摘要、正文、表格和关键标注的展示规则，\n    不改变 accepted 工作簿原始数值、计算精度、求解容差或提交数据。\n  ordinary_display_default:\n    governance_level: default\n    decimal_places: 2\n    applies_when_all:\n      - paper_numeric_display\n      - no_explicit_prompt_or_verified_official_precision\n    exceptions:\n      - prompt_or_verified_official_precision\n      - integer_counts_or_nonnumeric_identifiers\n      - scientific_notation_to_preserve_order_of_magnitude\n    rules:\n      - 题目有明确精度时按要求显示；否则摘要、正文、表格和关键标注默认两位小数。\n      - 两位小数仅改变显示字符串，不对已验收数据进行舍入后再计算或覆盖原值。\n      - 极小量与极大量可采用科学计数法，整数计数保持整数；显示不得伪造零值或改变数量级。\n      - Numeric Profile 的特殊展示精度须有明确题目或官方依据，不得仅凭推测评分敏感而默认六七位。\n  consistency:\n    - 摘要、正文直接答案、核心结果表与提交结果文件的同一指标必须来自同一已验收数值事实源。\n    - 论文显示的舍入值与工作簿的完整原值职责不同；不得用显示值回写或重新计算。\n    - 百分比与百分点必须区分；例如从 90% 升至 92% 是增加 2 个百分点，而不是增加 2%。\n    - 单位必须与数值间距、量纲和符号含义一致，避免 10m、10 m、10.00m 混用。\n    - 均值±标准差、置信区间和上下界必须说明统计含义，不把区间端点误写成点估计。\n  display_profiles:\n    abstract: 题目明确要求时遵守题目；其余数值默认两位小数，并与正文相同指标口径一致。\n    body: 连续数值默认两位小数；有明确题面或官方精度要求时按该要求显示。\n    table: 列内通常统一小数位；默认两位小数，特殊精度按有来源的 Numeric Profile 执行。\n    figure_axis: 坐标刻度可按可读性表达；关键标注依题面要求或默认两位小数，避免数量级误读。\n    optimization_variable: 决策变量、坐标、时间、目标值的论文展示采用题面指定精度，否则默认两位小数。\n  machine_audit_scope:\n    may_check:\n      - declared_metric_format_consistency\n      - unit_spacing_for_registered_units\n      - decimal_place_drift_for_registered_metrics\n      - ratio_percent_mixing_for_registered_metrics\n      - percentage_point_wording_pattern\n    must_not_claim:\n      - a_specific_precision_is_correct_without_profile_or_prompt_evidence\n      - statistical_significance_from_decimal_places\n      - physical_accuracy_from_display_precision\n", "numeric_style_contract:\n  governance_level: default\n  principle: >-\n    数学建模竞赛中的核心答案数值必须按题目、官方格式、评分粒度和结果敏感性保持足够高的展示精度；\n    不得为了版面简洁或“可读性”擅自把已验收结果粗略舍入。若精确到小数后 6--7 位可能影响结果分，\n    摘要、正文直接答案和关键结果表必须保留相应高精度，并与标准工作簿同源。\n  ordinary_display_default:\n    governance_level: recommendation\n    decimal_places: 2\n    applies_when_all:\n      - explanatory_continuous_value\n      - not_scoring_sensitive_or_decision_critical\n      - no_prompt_official_or_metric_numeric_profile_override\n    exceptions:\n      - core_answers_or_submission_values\n      - objectives_decision_variables_coordinates_or_times\n      - probability_threshold_error_or_tiny_values\n      - confidence_intervals_or_uncertainty_sensitive_values\n      - integer_counts_or_values_requiring_scientific_notation\n    rules:\n      - 两位小数只影响合法正文展示，不改变 accepted workbook 原值、后续计算、容差或提交答案。\n      - 题目、官方、指标级 Numeric Profile、测量分辨率和统计不确定性优先；不得舍掉真实差别。\n      - 百分数/百分点分别按含义和必要分辨率表达，不机械把所有比例格式固定两位小数。\n  high_precision_default:\n    applies_when_any:\n      - exact_numeric_answer_is_scored\n      - judging_may_compare_late_decimal_digits\n      - optimization_or_geometry_answer_requires_precise_coordinates_times_or_objective\n      - competition_or_user_requires_fixed_decimal_places\n    preferred_decimal_places_when_not_otherwise_specified: [6, 7]\n    rule: >-\n      6--7 位是高精度结果展示的常用默认区间而非无条件硬编码；若题目、模板、物理分辨率、统计不确定性或官方要求给出其他精度，以其为准。\n  consistency:\n    - 摘要、正文直接答案、核心结果表与提交结果文件的同一指标必须来自同一已验收数值事实源。\n    - 同一指标可因百分比/比例、科学计数法等表现形式不同而改变字符串，但不得改变数值含义或有效精度。\n    - 百分比与百分点必须区分；例如从 90% 升至 92% 是增加 2 个百分点，而不是增加 2%。\n    - 单位必须与数值间距、量纲和符号含义一致，避免 10m、10 m、10.00m 混用。\n    - 均值±标准差、置信区间和上下界必须说明统计含义，不把区间端点误写成点估计。\n  display_profiles:\n    abstract: 核心答案和决定性数值优先保留可评分的高精度；不得以摘要为理由强行降到 3--4 位。\n    body: 与工作簿和题目要求保持精度闭合；可在解释性非核心数字上按项目 profile 统一。\n    table: 核心结果列保留足以复核和评分的精度；同列通常统一小数位或科学计数法。\n    figure_axis: 坐标刻度以可读性为主，但关键点/阈值/标注数值不得因坐标轴格式丢失必要精度。\n    optimization_variable: 决策变量、坐标、时间、目标值按题目输出要求和评分敏感度保留高精度。\n  machine_audit_scope:\n    may_check:\n      - declared_metric_format_consistency\n      - unit_spacing_for_registered_units\n      - decimal_place_drift_for_registered_metrics\n      - ratio_percent_mixing_for_registered_metrics\n      - percentage_point_wording_pattern\n    must_not_claim:\n      - a_specific_precision_is_correct_without_profile_or_prompt_evidence\n      - statistical_significance_from_decimal_places\n      - physical_accuracy_from_display_precision\n"),
    ),
    "modules/05_writing/paper_writing_protocol.md": (
        ("### 9.1 数值展示\n\n题目对数值精度有明确要求时，按题目及已核验的官方输出格式执行；未明确要求时，**论文数值默认保留小数点后两位**，适用于摘要、正文、表格及关键标注。整数计数保持整数；极小量或极大量可用科学计数法避免显示为零或失去数量级。该规则只调整论文展示，不修改 accepted 工作簿原始数值、计算精度、求解容差或提交数据。\n\n同一指标的单位、比例与百分比、百分点、均值 ± 标准差和置信区间必须保持含义一致。Numeric Profile 记录题目或已核验官方要求的特殊精度及来源；不能仅凭猜测评分可能检查后续小数位，就自动把核心答案提升至 6–7 位。\n", "### 9.1 数值展示\n\n一般非关键、非评分敏感的说明性连续数值，在没有更具体的项目展示要求时**建议显示两位小数**；这是阅读层级的展示默认，不是 accepted 数值精度、计算容差或正式提交口径。核心答案、目标值/决策变量、坐标与时间、概率与阈值、误差和极小量、统计区间、评分敏感值及题目规定精度优先由当前 Numeric Profile 决定；计数保持整数，极小值使用科学计数法，不能用两位小数抹掉有效差异。\n\n核心答案精度服从题目、官方输出、评分口径、物理分辨率、统计不确定性和项目 Numeric Profile，不为摘要简洁或版面整齐擅自截断。摘要、正文直接答案、关键表格和提交结果文件必须回到同一 current 数值事实源；同一指标的单位、比例/百分比、百分点、科学计数法、均值 ± 标准差、置信区间以及坐标/时间/优化变量精度保持一致。图轴可为可读性简化刻度，但作为答案证据的关键标注不得丢失评分所需位数。\n"),
        ("→ 核心结果/方案\n", "→ 高精度核心结果/方案\n"),
        ("优化类还要让读者知道主要决策对象和“优化什么”；非优化类用主要前提、输入条件、作用机制或评价准则替代“目标函数/约束”。优化类摘要如果只列决策变量和算法，却没有说明目标函数含义，模型信息仍不闭合。不要把算法数量当作模型贡献。**摘要中的数值精度服从题目明确要求；未明确要求时默认保留小数点后两位**。不能为摘要排版改变 accepted 原始数值，特殊精度必须有题面或官方来源。\n", "优化类还要让读者知道主要决策对象和“优化什么”；非优化类用主要前提、输入条件、作用机制或评价准则替代“目标函数/约束”。优化类摘要如果只列决策变量和算法，却没有说明目标函数含义，模型信息仍不闭合。不要把算法数量当作模型贡献。**核心答案的精度不得为了摘要简洁而擅自降低**；高精度评分场景常见为小数后 6--7 位，但最终服从题目、物理分辨率与 Numeric Profile。\n"),
    ),
    "modules/05_writing/ai_cleanup.md": (
        ("- **核心数值与全部数字**：包括非关键说明数字、目标值、阈值、比较基准、baseline、`accepted 数值`、单位、`绝对/相对误差`、百分比/百分点、`Numeric Profile` 和答题精度，均不舍入、不重写、不改变显示格式、计算或工作簿。具体展示精度由前置写作阶段按题目要求或默认两位小数确定；Cleanup 只读，不改 accepted 工作簿。\n", "- **核心数值与全部数字**：包括非关键说明数字、目标值、阈值、比较基准、baseline、`accepted 数值`、单位、`绝对/相对误差`、百分比/百分点、`Numeric Profile` 和答题精度，均不舍入、不重写、不改变显示格式、计算或工作簿。此前已定的普通数字两位小数与关键精度 6--7 位规范仍由前置写作阶段决定；Cleanup 只读，不改 accepted 工作簿。\n"),
    ),
}


def prior_w2_numeric_display_text(relative: str, text: str) -> str:
    """Undo only D02 edits; do not normalize unrelated or duplicate bytes."""
    for current, prior in W2_D02_APPROVED_REWRITES.get(relative, ()):
        if text.count(current) != 1:
            raise ValueError(
                f"{relative}: D02 hunk missing or duplicated: {current[:80]!r}"
            )
        text = text.replace(current, prior, 1)
    return text
