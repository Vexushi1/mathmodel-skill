#!/usr/bin/env python3
"""One-shot v8.7 writing capability authority/prose integration applicator.

Temporary implementation helper. It is intentionally idempotent and must be removed
before PR #114 is ready for review.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    (ROOT / rel).write_text(text, encoding="utf-8")


def insert_before_once(text: str, marker: str, addition: str, token: str) -> str:
    if token in text:
        return text
    if marker not in text:
        raise RuntimeError(f"missing marker for insertion: {marker[:80]!r}")
    return text.replace(marker, addition + marker, 1)


def insert_after_once(text: str, marker: str, addition: str, token: str) -> str:
    if token in text:
        return text
    if marker not in text:
        raise RuntimeError(f"missing marker for insertion: {marker[:80]!r}")
    return text.replace(marker, marker + addition, 1)


def replace_once(text: str, old: str, new: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"missing replacement anchor: {old[:100]!r}")
    return text.replace(old, new, 1)


def patch_reasoning() -> None:
    rel = "core/writing_reasoning_contract.yaml"
    text = read(rel)

    role_block = """  formula_role_taxonomy:\n    field_role: paper_and_trace_recoverability\n    values:\n      - final_model_relation\n      - key_bridge_relation\n      - supporting_derivation\n      - routine_algebra\n    roles:\n      final_model_relation:\n        definition: 最终模型、solver、validator、决策规则或直接答案实际消费的关系。\n        paper_policy: preserve\n        summary_policy: include_by_default_when_summary_is_required_or_inline\n      key_bridge_relation:\n        definition: >-\n          不一定直接进入 solver，但连接机理、定义、证明、变换、判据、边界、降维与最终模型；\n          删除后会造成关键来源、充分性、候选域或推导链断裂。\n        paper_policy: preserve_near_the_derivation_or_transformation\n        summary_policy: include_only_when_needed_to_recover_final_model_or_solver_precondition\n      supporting_derivation:\n        definition: 对理解推导有帮助但不承担独立模型/判据/证明/solver 接口的关系。\n        paper_policy: compress_or_keep_by_detail_allocation\n        summary_policy: exclude_by_default\n      routine_algebra:\n        definition: 机械展开、重复代换、单位整理或可由相邻式直接恢复的普通代数步骤。\n        paper_policy: compress_or_omit\n        summary_policy: exclude\n        trace_policy: normally_not_registered\n    role_assignment_basis:\n      - downstream_mathematical_use\n      - dependency_break_if_removed\n      - solver_validator_or_answer_consumption\n      - proof_reduction_or_boundary_dependency\n    bridge_preservation_rule: >-\n      “不是最终 solver 方程”不等于“可删除中间式”。若某关系承担 Source→Derivation→Destination 的关键桥接，\n      或后续命题、缩域、边界、solver precondition 需要回指，它应登记为 key_bridge_relation 并保留可恢复表达。\n    anti_bloat_rule: >-\n      角色分类不是增加公式数量的配额；routine_algebra 不因新增 taxonomy 进入 Core Formula Trace，\n      supporting_derivation 仍可压缩，简单解析题不要求额外造桥接式。\n    machine_boundary:\n      may_check: [declared_role_value, declared_role_anchor_presence, stale_role_status_conflict]\n      must_not_claim: [mathematical_role_from_regex, bridge_necessity_from_formula_position, formula_correctness_from_role_label]\n\n"""
    text = insert_before_once(
        text,
        "  chain_quality_rules:\n",
        role_block,
        "  formula_role_taxonomy:\n",
    )
    text = replace_once(
        text,
        "    - 核心模型汇总只呈现最终可计算模型，不重复完整推导。",
        "    - 核心模型汇总以 final_model_relation 为主体，只在恢复最终模型、关键边界或 solver 前提确有需要时带入少量 key_bridge_relation；不重复 supporting_derivation 与 routine_algebra。",
    )
    text = replace_once(
        text,
        "    required_fields: [formula_id, question, source, derivation, destination, status]\n    optional_fields: [depends_on, code_anchor, workbook_evidence]",
        "    required_fields: [formula_id, question, role, source, derivation, destination, status]\n    optional_fields: [depends_on, code_anchor, workbook_evidence]",
    )

    summary_block = """  summary_content:\n    include_by_default: [final_model_relation]\n    include_when_recoverability_requires: [key_bridge_relation]\n    exclude_by_default: [supporting_derivation, routine_algebra]\n    key_bridge_admission: >-\n      只有当不带该桥接关系会使最终模型的来源、关键边界、充分性、变量消元或 solver precondition 难以恢复时，\n      才在 summary 中保留；否则留在前述推导邻近位置。\n    no_formula_dump_rule: true\n\n"""
    text = insert_before_once(
        text,
        "  rule: >-\n    目标是让评委快速恢复求解器实际消费的最终模型；不得为了章节整齐强制所有小问设置同名小节。\n\nshared_foundation:",
        summary_block,
        "  summary_content:\n",
    )

    text = replace_once(
        text,
        "    formula_semantics: formula_reasoning_chain\n    shared_foundation: shared_foundation",
        "    formula_semantics: formula_reasoning_chain\n    formula_roles: formula_reasoning_chain.formula_role_taxonomy\n    shared_foundation: shared_foundation",
    )
    text = replace_once(
        text,
        "    formula_rules:\n      core_relation: 保留必要来源、关键推导与下游作用。\n      intermediate_relation: 仅作代数传递时可合并或压缩。\n      final_model: 必须让评委恢复 solver 实际消费的目标、关系、约束、状态方程或判据。\n      standard_relation: 只说明本题适用条件与进入当前模型的方式，不展开教科书式长介绍。",
        "    formula_rules:\n      final_model_relation: 必须保留，并让评委恢复 solver/validator/决策规则实际消费的目标、关系、约束、状态方程或判据。\n      key_bridge_relation: 若删除会造成机理—判据—证明—降维—边界—最终模型之间的关键依赖断裂，则保留其必要来源、推导与下游作用，不得仅因其不是最终 solver 输入而删除。\n      supporting_derivation: 按理解需要压缩或保留；不机械进入最终模型汇总。\n      routine_algebra: 优先压缩或省略，默认不进入 Core Formula Trace。\n      standard_relation: 只说明本题适用条件与进入当前模型的方式，不展开教科书式长介绍。",
    )
    write(rel, text)


def patch_protocol() -> None:
    rel = "modules/05_writing/paper_writing_protocol.md"
    text = read(rel)

    preflight_input = """\n\n### 1.1 Per-Question Writing Capability Preflight：先判定本问需要什么，再写\n\n进入任何“问题X模型建立及求解”正文前，必须先消费 `core/writing_runtime_contract.yaml#per_question_writing_capability_preflight` 与当前 `模型论文框架.md#逐问写作能力预检`。预检至少明确本问 Formula Roles、Core Model Summary、Proposition / Proof、Algorithm Presentation，以及当前需要条件加载的 Authority / Pack。\n\n`required / planned / current / stepwise / pseudocode` 等已记录项目状态必须在用户未再次提醒“公式汇总、命题、伪代码”时仍然生效。`missing` 不能静默改成 `not_applicable / not_needed`；`stale` 不能直接写成 current。若状态尚未裁决，先完成语义裁决，再生成该问正文。Preflight 只调度已有能力，不自动创造命题、算法或额外公式。\n"""
    text = insert_after_once(
        text,
        "写模型建立与求解前，从当前模型方案、Model Construction Rationale、Formula/Algorithm Trace、已知条件和结果中恢复关键选择的依据。可由现有关系推出的理由应解释清楚；需要新增数据、实验或团队经历才能成立的理由不能补造，缺口交回语义审查或请求事实。无需新建思考日志或项目必填表。仅润色局部时保留原有范围、术语、公式和数值；理由充分且表达自然的原文可以不改。",
        preflight_input,
        "### 1.1 Per-Question Writing Capability Preflight",
    )

    role_section = """### 7.0 Formula Roles：区分最终模型、关键桥接与可压缩推导\n\nCore Formula Trace 不再只用“核心公式/普通代数”二分。正文按 Writing Reasoning Authority 中的角色判断：\n\n- **Final Model Relation** (`final_model_relation`)：最终模型、solver、validator、决策规则或直接答案实际消费，原则上保留；\n- **Key Bridge Relation** (`key_bridge_relation`)：不一定直接进入 solver，但连接机理、定义、证明、变换、判据、边界或降维。若删除会让“为什么能得到最终模型”断裂，就不能当作普通中间式压掉；\n- **Supporting Derivation** (`supporting_derivation`)：有助于理解但不承担独立接口，可按篇幅和难度压缩；\n- **Routine Algebra** (`routine_algebra`)：机械展开、重复代换等普通代数，优先省略，通常不登记进 Core Formula Trace。\n\n角色取决于**下游数学作用**，不是公式在正文中的位置。某个距离式、判别式或变换式即使最终不出现在 solver 输入中，只要后续关键判据、缩域、命题或边界依赖它，就可能是 Key Bridge Relation。反之，推导很长也不自动意味着每一步都应保留。\n\n正文推导通常保留 Final + Key Bridge + 必要 Supporting；核心模型汇总以 Final 为主体，只在缺少某个 Key Bridge 会使最终模型来源、边界或 solver 前提不可恢复时带入该桥接式。禁止把前文所有公式复制成“公式大全”。\n\n"""
    text = insert_before_once(
        text,
        "### 7.0.1 Structural Reduction：为什么可以简化必须与证据等级一致\n",
        role_section,
        "### 7.0 Formula Roles",
    )

    text = insert_after_once(
        text,
        "核心模型汇总只负责让评委快速恢复 solver 实际消费的最终模型，不能替代前面对变量、目标函数现实含义、约束来源和关键推导的说明。",
        "\n\n汇总内容以 `final_model_relation` 为主体；如果某个 `key_bridge_relation` 不出现就无法恢复关键边界、充分性、变量消元或 solver precondition，可在 recap 中保留它。`supporting_derivation` 与 `routine_algebra` 默认不重复进入汇总。这样既避免“把所有中间式再抄一遍”，也避免把真正承担逻辑桥梁的公式收束得过狠。",
        "汇总内容以 `final_model_relation` 为主体",
    )

    text = replace_once(
        text,
        "动力系统、概率、回归、网络、仿真等模型按真实结构汇总最终可计算关系，可包含状态方程、观测/概率关系、初始与边界条件、判据和输出映射，不强行套用优化模型的 `s.t.`。若只有一两个解析关系，直接在相邻正文中收束，不新增形式化总结块。",
        "动力系统、概率、回归、网络、仿真等模型按真实结构汇总最终可计算关系，可包含状态方程、观测/概率关系、初始与边界条件、判据和输出映射，不强行套用优化模型的 `s.t.`。若状态方程到观测关系、几何量到判据、转移关系到决策规则之间存在不可替代的 `key_bridge_relation`，应保留其关键来源与推导，不能因为它不是最终输出方程而跳过。若只有一两个解析关系，直接在相邻正文中收束，不新增形式化总结块。",
    )

    solve_preflight = """求解段开始前再次消费本问 Preflight 已裁决状态：`Core Model Summary=required` 时先确认最终模型已经可恢复；planned/current 命题若承担 solver 前提或缩域依据，先完成对应证明/引用；`Algorithm Presentation=stepwise/pseudocode` 时按项目状态自动加载 Algorithm Flow，而不是等待用户再次提醒。`missing/stale` 状态不得跨过此处直接进入算法叙述。\n\n"""
    text = insert_after_once(
        text,
        "## 8. 模型求解\n\n",
        solve_preflight,
        "求解段开始前再次消费本问 Preflight",
    )
    write(rel, text)


def patch_output_contract() -> None:
    rel = "core/output_contract.yaml"
    text = read(rel)
    text = insert_before_once(
        text,
        "  core_model_summary_policy: adaptive_required_inline_not_applicable\n",
        "  formula_role_contract: core/writing_reasoning_contract.yaml#formula_reasoning_chain.formula_role_taxonomy\n  core_model_summary_contract: core/writing_reasoning_contract.yaml#adaptive_core_model_summary\n  per_question_writing_preflight_contract: core/writing_runtime_contract.yaml#per_question_writing_capability_preflight\n",
        "  per_question_writing_preflight_contract:",
    )
    write(rel, text)


def patch_cleanup() -> None:
    rel = "modules/05_writing/ai_cleanup.md"
    text = read(rel)
    addition = """\n\n先读取本问 Formula Role 与 Writing Capability Preflight：\n\n- `final_model_relation`：原则上 **Keep**；清理不得让最终 solver/validator/决策规则失去可恢复模型；\n- `key_bridge_relation`：若删除会断开机理、证明、判据、边界、降维或 solver precondition，必须 **Keep / Compress without breaking the bridge**；不能仅因“不是最终模型公式”删除；\n- `supporting_derivation`：可按 Detail Allocation **Compress / Re-locate**，但若当前读者无法恢复关键跳步则不能过度压缩；\n- `routine_algebra`：优先 **Compress / Delete**，默认不因 v8.7 新角色增加正文公式数量；\n- Preflight 已裁决 `Core Model Summary=required`、Proposition `planned/current`、Algorithm `stepwise/pseudocode` 时，Cleanup 只能优化表达与载体，不能因为用户本轮没有再次提到这些能力就删掉；\n- `missing/stale/review_required` 必须回到裁决或修复，不能通过润色伪装成 current。\n"""
    text = insert_after_once(
        text,
        "按 reasoning contract 检查表现层风险：",
        addition,
        "先读取本问 Formula Role 与 Writing Capability Preflight",
    )
    write(rel, text)


def patch_review() -> None:
    rel = "modules/06_review_delivery.md"
    text = read(rel)
    review = """### Question Writing Capability Activation Review\n\n本检查消费 `core/writing_runtime_contract.yaml#per_question_writing_capability_preflight`、当前 `模型论文框架.md#逐问写作能力预检` 与既有 Writing Reasoning Authority，不建立第二套数学写作规则。其目标不是判断“有没有提到关键词”，而是验证**项目状态是否在该出现时真的激活了相应能力**。\n\n逐问检查：\n\n1. **Formula Roles**：`final_model_relation`、`key_bridge_relation`、`supporting_derivation` 是否按下游作用登记；关键桥接式不能仅因不直接进入 solver 被删除，routine algebra 也不能因新 taxonomy 被机械扩写。\n2. **Core Model Summary Activation**：`required` 是否在模型建立结束前形成可恢复的最终模型；`inline/not_applicable` 是否来自显式裁决而非遗漏。summary 以 Final 为主体，Key Bridge 只在恢复边界/充分性/precondition 真正需要时进入。\n3. **Proposition / Proof Activation**：planned/current 命题是否自动进入对应写作分支；candidate/high-signal 只触发必要性审查，不自动造命题；stale 命题不能写成 current。\n4. **Algorithm Presentation Activation**：`stepwise/pseudocode` 是否即使用户 prompt 未出现“伪代码/算法流程”也自动读取 Algorithm Flow 并消费 current Algorithm Trace；`not_needed` 不产生装饰算法框。\n5. **Missing / Stale Gate**：Preflight 关键状态缺失时是否进入 `needs_adjudication`，而不是静默设为 `not_applicable/not_needed`；stale 是否阻止旧命题、旧算法或旧公式角色直接进入正文。\n6. **Compact Runtime Boundary**：完整 reasoning Authority、Proposition Pack、Algorithm Pack 仍按状态条件加载，不得因为本轮增强恢复开篇全量 preload。\n\n上述 activation 缺口默认属于 `review_required`；只有其同时造成既有 Hard 事实/数学/证据错误时才 blocking，例如 stale 证明支撑 current claim、必要 solver 前提被遗漏导致主计算无效、或数值实验冒充严格证明。机器可以核对 declared state→resource mapping 和锚点存在，不能由公式位置、关键词、算法名或命题标题判断数学必要性和正确性。\n\n"""
    text = insert_before_once(
        text,
        "### Author Reasoning Semantic Review\n",
        review,
        "### Question Writing Capability Activation Review",
    )
    write(rel, text)


def main() -> None:
    patch_reasoning()
    patch_protocol()
    patch_output_contract()
    patch_cleanup()
    patch_review()
    print("v8.7 phase-2 writing authority/prose integration applied")


if __name__ == "__main__":
    main()
