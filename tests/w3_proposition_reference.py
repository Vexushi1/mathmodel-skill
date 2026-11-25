"""W3 I01/I02 test-only inverse for exact historical source snapshots.

The source is not a new business authority and never authorizes a result or
model change. Historical W1/W2 and older protected digests remain immutable.
"""
W3_SOURCE_IDENTITIES = {
    "core/writing_reasoning_contract.yaml": [
        "56246364a74bb8a5ec014d1882e9ae2ad12f13d183815a0f5ee6f6a9a029c2e6",
        "d34d95e774c3f61bbff8cd5c56e22e5acfe42a8202f7530c292413d5415d1b98"
    ],
    "packs/artifact/proposition_proof.md": [
        "4ec2ee9345a254ebae2a2b489d3df80563ba172cc46349b7669cddccf1c8e7dd",
        "4cd57dad8303750c99b0e2e53c06f3ef8dde2432e431120fefa5ebf3fe90a91a"
    ],
    "modules/02_model_design.md": [
        "ca5c299e4cbeea9caff80fbbaba2e3711262081ffe258ef5ca51e0ee7fcaf306",
        "4deb0db4d7ff06c6cfc6cda0344fc25212e7cb9bbe8155b11d516c1f3c2107f4"
    ],
    "modules/05_writing/paper_writing_protocol.md": [
        "09994c876bc02cacd320d6898429eb95e4e2c095cb2900739dc815ab8deb0094",
        "ec5e1b95336dd6fc72114a2e2a62c5c96f2f2bbec48533c353adec158693e2a8"
    ],
    "core/output_contract.yaml": [
        "11a647712355a29de942062fa26c09d21baa5bfe3360c79df90d34021a78be05",
        "e78a4092760319cee25c94d3eb4a4fe41ea814a85395ef16d15b25d3cd15e7c9"
    ],
    "core/project_state.schema.yaml": [
        "5ab0e1b5897e70e2ce04d1de7f684a6003d9a97ad1e45201e734ae5360c722c1",
        "348e981de6a66f028f742e56f9e0cd872567baf685b4f507ff62cfff435ccd73"
    ]
}
W3_APPROVED_REWRITES = {
    "core/writing_reasoning_contract.yaml": (
        ("proposition_governance:\n  default_budget: [0, 4]\n  governance_level: hard\n  maximum_body_propositions: 4\n  count_scope: full_paper_body\n  over_budget_action: revise_body_plan_required\n  automatic_rejection_over_budget: true\n  admission_effects:\n    - reduce_dimension\n    - reduce_constraints\n    - restrict_candidate_region\n    - guarantee_feasibility\n    - justify_transformation\n    - provide_threshold_or_bound\n    - justify_model_necessity\n    - establish_solution_structure\n  rule: >-\n    全文正文正式命题总数不得超过 4 个，全部小问共同计数，不设超额豁免。\n    超过上限时先调整命题规划：合并可共享证明的性质，把普通推导改为连续数学论证；\n    只有不承担正文主论证闭环的技术引理、重复展开或扩展证明可移入附录。\n    不能以数量限制为由删除核心证明或改变数学结论；承担模型成立、关键变换合法性、\n    核心结论、边界/可行性/唯一性或下游计算前提的必要证明必须在正文完整可恢复，\n    即使其不再单列为正式编号命题。\n  proof_length_recommendation: 正文连续短证明通常用自然分段和必要公式；篇幅只影响呈现方式，不决定正文/附录位置，也不作为数学有效性的判断。\n  proof_placement_rule: >-\n    证明位置由其对当前模型与结论的数学作用决定，而不是由长度决定。核心证明必须留在正文并完整可恢复；\n    非核心技术引理、重复展开或不影响主论证闭环的扩展证明可以放入附录，但正文应明确其引用位置和支持作用。\n", "proposition_governance:\n  default_budget: [0, 4]\n  governance_level: recommendation\n  over_budget_action: justification_required\n  automatic_rejection_over_budget: false\n  admission_effects:\n    - reduce_dimension\n    - reduce_constraints\n    - restrict_candidate_region\n    - guarantee_feasibility\n    - justify_transformation\n    - provide_threshold_or_bound\n    - justify_model_necessity\n    - establish_solution_structure\n  rule: >-\n    命题数量由实际数学作用决定，不按小问分配。0--4 是正文阅读预算而非数学硬上限；\n    超出默认预算时先合并同质命题。只有不承担正文主论证闭环的技术引理、重复细节或扩展证明才可考虑移入附录；\n    承担模型成立、关键变换合法性、核心结论、关键边界/可行性/唯一性或下游计算前提的核心命题与证明，应在正文完整可恢复，\n    不得仅因数量预算、篇幅、难度或版式限制外移，并说明额外命题的不可替代作用。\n  proof_length_recommendation: 正文连续短证明通常用自然分段和必要公式；篇幅只影响呈现方式，不决定正文/附录位置，也不作为数学有效性的判断。\n  proof_placement_rule: >-\n    证明位置由其对当前模型与结论的数学作用决定，而不是由长度决定。核心证明必须留在正文并完整可恢复；\n    非核心技术引理、重复展开或不影响主论证闭环的扩展证明可以放入附录，但正文应明确其引用位置和支持作用。\n"),
    ),
    "packs/artifact/proposition_proof.md": (
        ("命题数量按 `core/writing_reasoning_contract.yaml#proposition_governance` 执行：**全文正文正式命题最多 4 个，不设超额例外**。先合并可以共用证明的同质命题，非核心技术细节可放入附录；核心证明和关键推导必须保持正文数学闭环，不因压缩正式命题数量而删除。\n", "命题治理权威来自 `core/writing_reasoning_contract.yaml`：**0--4 是默认正文阅读预算，不是绝对上限**。超过预算时先检查是否可合并同质命题；只有不承担正文主论证闭环的技术引理、重复细节或扩展证明才考虑放入附录。核心命题及其必要证明无论长短都按数学作用保留在正文；仍需超过预算时记录额外命题的不可替代作用，不自动否决。\n"),
        ("旧项目若保留 `budget_exception_reason`，仅作历史说明，不构成正文超过 4 个命题的豁免；新正文超限时必须调整命题安排，而不能用理由字段直接放行。\n", "超过默认 4 个预算时，额外记录 `budget_exception_reason`，说明为什么不能合并，以及额外命题在正文主论证中的不可替代作用；不能用“可移附录”反向要求外移核心证明。\n"),
    ),
    "modules/02_model_design.md": (
        ("**全文正文正式命题最多 4 个，不设超额豁免。** 先筛选真正需要单列命题的性质；如果规划超限，合并同质命题或将普通性质改为连续推导，只有不影响正文主论证闭环的技术细节才考虑进入附录。核心命题及其必要证明不能因预算外移或被删掉；旧 `proposition_budget_status` / `proposition_budget_reason` 仅为历史记录，不能替代调整正文规划。\n\n命题 ID 使用 `P1, P2, ...` 作内部稳定追踪编号，历史编号无需因删改重排为 P1--P4，但正文正式命题总数仍不得超过 4 个。正式论文按章节显示“命题 4.1、命题 6.2”等。", "**0--4 是默认正文阅读预算，不是绝对上限。** 先收集真正需要证明的对象，再筛选：\n\n- 预算内：正常规划；\n- 超过 4 个：先合并同质命题；只有不承担正文主论证闭环的技术引理、重复细节或扩展证明才考虑移附录，核心命题及其必要证明不能因预算外移；\n- 仍需超过预算：记录 `proposition_budget_status=justified` 与 `proposition_budget_reason`，说明额外命题的不可替代建模作用和正文保留理由。\n\n命题 ID 使用 `P1, P2, ...` 作为内部稳定追踪编号，不限制为 P1--P4。正式论文仍按章节显示“命题 4.1、命题 6.2”等。"),
    ),
    "modules/05_writing/paper_writing_protocol.md": (
        ("非优化模型仅在等价变换、单调性、可行性、唯一性、降维或边界判定等性质确实影响当前模型时使用正式命题；全文正文数量、准入、证明等级与位置服从 `core/writing_reasoning_contract.yaml#proposition_governance` 和按需加载的命题 Pack。证明后应交代该性质怎样实际改变后续变量、约束、候选域、solver、阈值或解释边界；数值实验与 solver 退出状态不能替代数学证明，简单关系可以连续推导而不必单列命题。", "命题只在承担等价转化、单调性、可行性、唯一性、降维或边界判定等真实作用时进入正文。命题或证明之后必须说明它怎样改变后续变量、约束、候选域、solver、阈值或解释边界；数值实验、求解器状态、有限样本准确率和交叉验证不能替代数学证明。复杂命题与证明的格式和证据等级再按需读取完整 reasoning Authority。\n\n证明位置服从数学作用而不是长度。若某证明承担模型成立、关键变换合法性、核心结论、关键边界/可行性/唯一性或后续计算前提，即使较长也应在正文完整可恢复；可以通过分段、分情况、分页或“命题陈述框 + 框外正文证明”改善阅读，但不能仅因篇幅或命题框高度把它移入附录。只有不影响主论证闭环的技术引理、重复展开或扩展证明才适合附录，并在正文保留明确引用与作用。\n\n命题前可以说明尚需确认的性质，证明后把性质落到实际动作，例如单调性为何允许舍弃某一候选区间。动机段不代替证明，反求问题也不自动需要正式命题；简单关系能直接闭合时保持简洁。"),
    ),
    "core/output_contract.yaml": (
        ("proposition_contract:\n  optional: true\n  authority: core/writing_reasoning_contract.yaml#proposition_governance\n  default_budget: [0, 4]\n  over_budget_action: revise_body_plan_required\n  automatic_rejection_over_budget: true\n  count_scope: full_paper_body\n  detail_pack: packs/artifact/proposition_proof.md\n  lazy_load_when: [explicit_proof_request, proposition_count_greater_than_zero]\n  latex_outer_environment: hskproposition\n  latex_proof_environment: hskproof\n  display_numbering: arabic_section_dot_arabic_proposition\n  state_fields: [proposition_default_budget, proposition_budget_status, proposition_budget_reason, proposition_count, proposition_status, propositions]\n  compatibility:\n    proposition_limit: 旧项目只读兼容；不能豁免当前正文最多4个正式命题的硬上限\n    proposition_budget_status: 旧项目只读兼容；justified 不再授权超限\n    proposition_budget_reason: 旧项目只读兼容；说明不替代正文命题调整", "proposition_contract:\n  optional: true\n  authority: core/writing_reasoning_contract.yaml#proposition_governance\n  default_budget: [0, 4]\n  over_budget_action: justification_required\n  automatic_rejection_over_budget: false\n  detail_pack: packs/artifact/proposition_proof.md\n  lazy_load_when: [explicit_proof_request, proposition_count_greater_than_zero]\n  latex_outer_environment: hskproposition\n  latex_proof_environment: hskproof\n  display_numbering: arabic_section_dot_arabic_proposition\n  state_fields: [proposition_default_budget, proposition_budget_status, proposition_budget_reason, proposition_count, proposition_status, propositions]\n  compatibility:\n    proposition_limit: 旧项目只读兼容；不再作为Hard上限"),
    ),
    "core/project_state.schema.yaml": (
        ("      proposition_default_budget: {type: integer, const: 4, default: 4}\n      proposition_budget_status:\n        description: 旧项目预算状态只读兼容，justified 不再豁免当前正文上限\n        type: string\n        enum: [within_default_budget, justification_required, justified]\n      proposition_budget_reason:\n        description: 旧项目预算说明只读兼容，不得用于当前正文超限放行\n        type: string\n      proposition_count: {type: integer, minimum: 0, maximum: 4}\n      proposition_status: {type: string, enum: [not_assessed, planned, current, stale]}\n      propositions:\n        type: array\n        maxItems: 4\n        items: {$ref: '#/$defs/proposition_entry'}", "      proposition_default_budget: {type: integer, const: 4, default: 4}\n      proposition_budget_status:\n        type: string\n        enum: [within_default_budget, justification_required, justified]\n      proposition_budget_reason: {type: string}\n      proposition_count: {type: integer, minimum: 0}\n      proposition_status: {type: string, enum: [not_assessed, planned, current, stale]}\n      propositions:\n        type: array\n        items: {$ref: '#/$defs/proposition_entry'}"),
    ),
}


def prior_w3_proposition_text(relative: str, text: str) -> str:
    """Project only the exact I01/I02 text; preserve any unrelated suffix."""
    for current, prior in W3_APPROVED_REWRITES.get(relative, ()):
        if text.count(current) != 1:
            raise ValueError(
                f"{relative}: I01/I02 hunk missing or duplicated: {current[:80]!r}"
            )
        text = text.replace(current, prior, 1)
    return text
