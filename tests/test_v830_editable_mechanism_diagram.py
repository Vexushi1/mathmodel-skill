from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

from module06_sources import historical_review_text
from writing_slimming_reference import (
    WRITING_SLIMMING_REWRITES,
    prior_writing_slimming_text as prior_w1_writing_slimming_text,
)
from w2_numeric_display_reference import (
    W2_D02_APPROVED_REWRITES, W2_D02_SOURCE_IDENTITIES,
    prior_w2_numeric_display_text,
)

def prior_writing_slimming_text(relative: str, text: str) -> str:
    """First reverse W2 D02, then W1; historical digest guards remain unchanged."""
    return prior_w1_writing_slimming_text(
        relative, prior_w2_numeric_display_text(relative, text)
    )


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


GENERATOR = load_script("hsk_generate_mechanism_drawio", "scripts/generate_mechanism_drawio.py")
VALIDATOR = load_script("hsk_validate_drawio_figure", "scripts/validate_drawio_figure.py")


def base_spec(*, layout_mode: str = "explicit") -> dict:
    nodes = [
        {
            "id": "n_target",
            "label": "观测目标 T",
            "semantic_role": "object",
            "symbol_refs": ["T"],
            "source_anchor": "模型论文框架.md#Q1-对象",
            "group_id": None,
            "shape": "rounded_rect",
            "emphasis": "primary",
            "geometry": {"x": 80, "y": 120, "width": 180, "height": 70},
        },
        {
            "id": "n_boundary",
            "label": "可见边界 g(T)=0",
            "semantic_role": "boundary",
            "symbol_refs": ["g(T)"],
            "source_anchor": "模型论文框架.md#式-6",
            "group_id": None,
            "shape": "diamond",
            "emphasis": "risk",
            "geometry": {"x": 420, "y": 120, "width": 190, "height": 90},
        },
        {
            "id": "n_state",
            "label": "临界可见状态",
            "semantic_role": "state",
            "symbol_refs": ["z=1"],
            "source_anchor": "模型论文框架.md#Q1-状态",
            "group_id": None,
            "shape": "rounded_rect",
            "emphasis": "secondary",
            "geometry": {"x": 750, "y": 120, "width": 170, "height": 70},
        },
    ]
    edges = [
        {
            "id": "e_constraint",
            "source": "n_target",
            "target": "n_boundary",
            "relation_type": "constrains",
            "direction": "forward",
            "label": "遮蔽约束",
            "source_anchor": "模型论文框架.md#式-6",
            "formula_refs": ["F6"],
            "waypoints": [],
        },
        {
            "id": "e_switch",
            "source": "n_boundary",
            "target": "n_state",
            "relation_type": "switches_to",
            "direction": "forward",
            "label": "越过临界值",
            "source_anchor": "模型论文框架.md#Q1-判定条件",
            "formula_refs": ["F7"],
            "waypoints": [],
        },
    ]
    if layout_mode != "explicit":
        for node in nodes:
            node.pop("geometry")
    return {
        "spec_version": "1.0.0",
        "figure_id": "MF-Q1-01",
        "question_id": "Q1",
        "diagram_type": "critical_state",
        "core_question": "遮蔽约束如何决定目标的临界可见状态？",
        "core_conclusion": "边界函数变号触发可见状态切换。",
        "framework_anchor": "模型论文框架.md#Q1-机理图",
        "backend": "drawio",
        "layout_mode": layout_mode,
        "semantic_anchors": {
            "model": ["模型论文框架.md#Q1-模型"],
            "formulas": ["F6", "F7"],
            "constraints": ["C1"],
            "assumptions": ["A2"],
            "code": ["问题一求解.py:is_visible"],
            "result_evidence": [],
        },
        "canvas": {
            "width": 1000,
            "height": 700,
            "orientation": "landscape",
            "target_use": "paper",
            "target_width_mm": 150,
        },
        "groups": [],
        "nodes": nodes,
        "edges": edges,
        "artifact": {
            "spec_source": "figures/source/q1_occlusion.mechanism.yaml",
            "editable_source": "figures/source/q1_occlusion.drawio",
            "preview": None,
            "final_exports": ["figures/q1_occlusion.pdf", "figures/q1_occlusion.svg"],
            "spec_sha256": None,
            "drawio_sha256": None,
            "preview_sha256": None,
            "validation_status": "pending",
            "visual_review_status": "pending",
        },
    }


def write_spec(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


# v10.18 comparison extensions are an exact inverse projection, not a new body
# baseline. Every authorized literal must occur once; the historical blob hashes
# below still reject any unrelated change, including primary execution semantics.
# Exact v10.29.0 literature checks are projected away before testing the
# immutable historical approval authority. Any unrelated change still fails
# against the original pinned Git blob SHA-1.
LITERATURE_APPROVAL_V10290_RULES = """    literature_method_transfer_when_used: >-
      If the current proposed model consumes outside research, independently verify
      the original paper's object, assumptions, variables, constraints, data needs
      and the current problem's transfer conditions. Presence of a citation or a
      structurally valid literature JSON report does not prove applicability.
      Without externally dependent model relations, this check is not_applicable.
    literature_source_qualification_when_used: >-
      For critical outside methods, empirical parameters and nontrivial theories,
      retain actual source access and original-method anchors or explicit unresolved
      evidence. E0/E1 summaries cannot establish a verified formula; where a
      critical external premise remains unsupported, require repair before PASS.
    literature_recency_anchor_and_novelty_bias_when_used: >-
      Independently challenge recentness bias, inaccessible original methods,
      incompatible boundary/data regimes, omitted counterexamples and unsupported
      claims of first invention; do not demand a fixed number of citations.
"""

LITERATURE_APPROVAL_V10290_LIST_ITEMS = (
    "    - literature_method_transfer_when_used\n",
    "    - literature_source_qualification_when_used\n",
    "    - literature_recency_anchor_and_novelty_bias_when_used\n",
)

COMPARISON_AUTHORITY_REWRITES = {
    "core/model_approval_contract.yaml": (
        ("version: 1.2.0\n", "version: 1.1.0\n"),
        ("""analysis_comparison_approval:
  activation: current_analysis_comparison_1.0.0_only
  same_gate: model_approval
  scope_authority: modules/03_result_analysis.md
  scope_shape: core/project_state.schema.yaml#/$defs/analysis_comparison
  implementation: scripts/analysis_comparison.py
  framework_marker: HSK_ANALYSIS_COMPARISON_BEGIN_END_Qn_after_result_summary
  primary_identity: unchanged_full_current_validated_approved_SIB
  scope_digest:
    includes: [protocol_version, question, baseline_semantic_identity_hash, complete_model_specs, algorithm_definitions, comparison_questions, common_evaluation_protocols]
    excludes: [future_primary_workbook_hash, actual_results, final_evidence_row_positions, approval_records]
  mathematical_projection:
    purpose: declared_model_comparison_only_not_a_new_global_identity
    retain: all_model_fields_all_extensions_and_unknown_algorithm_content
    removable_scalar_implementation_keys: [family, method, solver, solver_role, implementation, backend]
    removal_requires: explicit_pure_algorithm_keys_and_scope_bound_two_pass_boundary_review
    comparison_partition: identical_pure_algorithm_key_sets_for_compared_model_specs
    nonremovable_examples: [domain_reduction, discretization_approximation, exact_predicate, event_topology, update_rule, stop_rule, original_model_reevaluation]
    qualification_boundary: string_or_hash_equality_does_not_prove_mathematical_equivalence_or_independence
  independent_review:
    roles: [positive_fitness_review, adversarial_model_challenge]
    same_independence_rule_as_primary: true
    each_record_requires: [distinct_review_reference, matching_scope_sha256, passed_verdict, actual_method, concrete_boundary_and_independence_conclusion, no_blocking_items, no_unresolved_items]
    checks: [mathematical_closure, material_difference_or_same_original_model, common_evaluation_fit, full_fidelity_feasibility, shared_defects_and_independent_information, legitimate_parameter_and_algorithm_scope]
  human_approval:
    explicit_only: true
    binding: current_scope_sha256
    recorded_provenance: user_statement_and_source_reference
    may_share_primary_brief: true
    no_synthesized_approval: true
  concrete_plan:
    create_only_after_primary_accepted: true
    criteria_and_selectors_frozen_before_analysis_delivery: true
    must_stay_within_approved_scope: true
  out_of_scope_change: supplemental_two_pass_review_and_explicit_scope_approval_in_existing_gate
  scope_only_change: invalidate_scope_approval_and_analysis_chain_preserve_unchanged_primary_lock_and_acceptance
  actual_primary_change: original_semantic_revision_and_identity_stale_policy
  c_review_policy: consume_comparison_scope_objects_when_explicitly_declared_never_reuse_main_only_receipts_as_comparison_review
  compatibility: absent_new_scope_preserves_existing_primary_and_legacy_analysis_rules

""", ""),
    ),
    "core/workbook_schema.yaml": (
        ("schema_version: 2.4.0\n", "schema_version: 2.3.1\n"),
        ("      optional_columns: [输入, 论文作用, 选择理由, 检验ID, 评价协议ID, 判据ID]\n",
         "      optional_columns: [输入, 论文作用, 选择理由]\n"),
        ("      optional_columns: [失效边界, 证据工作表, 论文位置, 说明, 检验ID, 证据处置ID]\n",
         "      optional_columns: [失效边界, 证据工作表, 论文位置, 说明]\n"),
        ("""  - 多模型检验
  - 同模型多算法检验
  comparison_method_sheets:
    model_comparison: 多模型检验
    多模型检验: 多模型检验
    algorithm_comparison: 同模型多算法检验
    同模型多算法检验: 同模型多算法检验
""", ""),
        ("""    多模型检验:
      required_columns: [检验ID, 记录键, 主模型ID, 对照模型ID, 评价协议ID, 实例或场景, 指标, 单位, 主模型数值, 对照模型数值, 差异类型, 差异, 判据ID, 判定]
      optional_columns: [模型族, 对照角色, 结构差异, 数据划分, 重复编号, 随机种子, 可行性, 残差, gap, 运行时间, 求解器及版本, 停止原因, 子运行ID, 源码位置, 证据位置, 差异单位]
    同模型多算法检验:
      required_columns: [检验ID, 记录键, 模型ID, 基准算法ID, 对照算法ID, 评价协议ID, 实例或场景, 重复编号, 指标, 单位, 基准数值, 对照数值, 差异类型, 差异, 判据ID, 判定]
      optional_columns: [随机种子, 初值, 计算预算, 可行性, 残差, gap, 决策差异, 运行时间, 求解器版本, 停止原因, 子运行ID, 源码位置, 证据位置, 差异单位]
""", ""),
    ),
    "core/writing_reasoning_contract.yaml": (
        ("schema_version: 1.11.0\n", "schema_version: 1.10.0\n"),
        ("""  comparison_scope:
    authority: modules/03_result_analysis.md
    rules:
    - Distinguish different mathematical models from different algorithms for one model; cite current accepted comparison evidence.
    - Agreement corroborates only the declared evaluation scope; a disagreement can support a model-selection or boundary claim.
    - Required comparisons need exact current evidence and disposition; sensitivity evidence cannot replace missing comparison evidence.
    - Do not put inspection IDs, hashes, protocol markers or machine statuses into ordinary paper prose.
""", ""),
    ),
    "modules/03_result_analysis.md": (
        ("""## 三、按需多模型检验与同模型多算法检验

两类新检验沿用本模块的 Analysis Necessity Gate、独立 analysis 入口、项目唯一 backend 和现有处置，不要求每问两个模型。

| 类型 | 保持与改变的对象 | 专项证据表 |
|---|---|---|
| `model_comparison` | 保持题目对象、合法数据事实源和共同评价问题；比较至少一个有实质数学差异的合理模型 | `多模型检验` |
| `algorithm_comparison` | 保持原始数学模型、现实参数、目标和硬约束；比较至少两个不同真实求解方法 | `同模型多算法检验` |

同算法换 seed、初值、容差或函数名不单独计为多算法；不同模型名字不证明模型不同。同一方程改变离散或积分算法通常属于求解方法变化，增加物理机制才可能属于模型变化。等价 reformulation 必须保留原模型映射与回算。两模型一致只提供指定范围内的交叉佐证；不同模型产生差异也不自动否决主模型。

Module 02 的 Comparator 按具体比较问题关联稳定检验 ID。数学／算法比较规范置于框架 `#### 结果摘要` 之后的独立 `HSK_ANALYSIS_COMPARISON_BEGIN/END Qn` marker，不能混入主 SIB 或主语义哈希区。规范、范围审查和批准服从 `core/model_approval_contract.yaml`；当前主身份仍须 current = validated = approved。比较范围变化只失效该范围及 analysis 链，主模型真正变化才按原语义治理使主批准和结果失效。

主工作簿 accepted 后，在现有 `analysis_comparison.checks` 中冻结本次具体检验、对象引用、共同评价、判据和预期证据选择器。`required` 项必须逐项执行并形成真实非空证据及 disposition；敏感性或另一张实质表不能替代它。`exploratory` 未完成不阻塞当前必要答案，但不得写成已验证。仍有 current required 项时不得整体 `not_required`；明确题目／用户要求和未关闭核心风险不能因计算失败撤销。

配置与回执扩展仅按 `core/user_execution_contract.yaml` 激活；计划摘要排除实际结果和运行后处置，主簿和源码身份继续使用现有绑定。机器能核对规范一致性、有限指标算术、覆盖和来源，不能从名称自动证明数学等价、算法独立性或模型正确性。

每次真实子运行保留模型／算法、实例或重复、指标、单位、实际设置、停止原因及必要可行性／残差／时间；表列与 MATLAB 交接只由 `core/workbook_schema.yaml` 定义。共同评价须声明输出映射、因果合法划分、单位、方向和判据；不同目标函数不能直接相减。性能主张还需要适用预算、硬件和重复记录。只写固定比较数字或“通过”不构成执行证据。

`单位` 标记基准与对照指标；相对变化、改进比例或百分点等差异单位与指标单位不同时，必须在同一行明确填写 `差异单位`，并由该差异 selector 显式引用。非空 `差异单位` 不能被普通单位 selector 忽略；空可选列不触发单位推断。机器只对该字面单位作有限转换，不从运算名称补造单位，也不放宽其他指标的单位冲突规则。

有效的负比较结果属于实验发现。技术失败、缺行、不可比数据或身份不符不能冒充 `reject` 或已完成。`modify` 或附加 claim 的 `reject` 可完成检验，但关联正文保持 stale，直到具体动作完成；核心答案／模型有效性 `reject` 按现有核心否证规则 `redo_required` 并回退。

""", ""),
        ("## 四、Analysis Evidence Disposition\n", "## 三、Analysis Evidence Disposition\n"),
        ("## 五、Analysis Evidence Capture：深化分析必须保留可复查的底层结果\n", "## 四、Analysis Evidence Capture：深化分析必须保留可复查的底层结果\n"),
        ("## 六、数据与模型边界\n", "## 五、数据与模型边界\n"),
    ),
    "scripts/validate_code_delivery.py": (
        ("import analysis_comparison_gate as COMPARISON  # noqa: E402\n", ""),
        ("from execution_protocol import SOURCE_RECEIPT_VERSIONS, is_source_receipt, auxiliary_config_issues, comparison_config_issues\n",
         "from execution_protocol import SOURCE_RECEIPT_VERSIONS, is_source_receipt, auxiliary_config_issues\n"),
        ("    issues.extend(comparison_config_issues(config))\n", ""),
        ("""        comparison = COMPARISON.inspect_gate(
            project_root, state, _question_key(problem), config=config, code_path=script)
        issues.extend(comparison["issues"])
""", ""),
        ("    configuration_issues.extend(comparison_config_issues(config))\n", ""),
        ("""    guarded = any(CONFORMANCE.present(entry) or COMPARISON.present(entry, config=config)
                  for entry in (observed_state.get("subproblems") or {}).values())
    if guarded:
""", "    if any(CONFORMANCE.present(entry) for entry in (observed_state.get(\"subproblems\") or {}).values()):\n"),
        ("""    comparison = COMPARISON.inspect_gate(
        project_root, state, key, config=config, code_path=script) if stage == "analysis" else {
            "enabled": False, "issues": [], "observed_sources": {"project": {}, "skill": {}}}
    if comparison["issues"]:
        raise ValueError("; ".join(comparison["issues"]))
""", ""),
        ("    CONFORMANCE.merge_read_sets(observed, comparison[\"observed_sources\"])\n", ""),
        ("        validators=[CONFORMANCE.skill_validator(observed)] if conformance[\"enabled\"] or comparison[\"enabled\"] else (),\n",
         "        validators=[CONFORMANCE.skill_validator(observed)] if conformance[\"enabled\"] else (),\n"),
    ),
}


# Invert only the approved v10.19.3 handoff additions before applying the
# historical projections. Each literal is required exactly once; unchanged
# protected hashes still reject unrelated edits to these writing authorities.
HANDOFF_AUTHORITY_REWRITES = {
    "modules/05_writing/paper_writing_protocol.md": (
        # Restore the three v11 chapter-read/registration changes before the older handoff inverse.
        ("正式启动与跨会话恢复沿用固定提交的启动合同。已选择全文启动时，先取得规范全文。开始或切换小问、章节时仍须重新取得当前动作适用的规则原文、当前框架及相应证据。前一问尚缺的结果继续留待核验。已有规范正文只提供规则依据，正式写入仍须满足当前项目的模型、结果与写作门。\n\n新论文或结构性重写先确定实际骨架、目标位置与本轮范围。采用 Template-First 的项目按 `core/writing_runtime_contract.yaml#template_first_progressive_authoring` 读活动模板和主文件，再按“读取当前章节规则 → 写当前章节 → 通过当前 gate → 再读取下一章节规则”推进。其他赛事及明确选择的 Word 载体沿用其实际骨架；缺赛事专属模板时，根据题目和已有项目材料组织当前章节。", "本文件是普通正文内容 Authority，但**不是开篇一次性预读的长提示词**。每次新论文或结构性重写必须服从 `core/writing_runtime_contract.yaml#template_first_progressive_authoring`：先读 Template Manifest 与主文件，只确定骨架和目标槽；随后按“读取当前章节规则 → 写当前章节 → 通过当前 gate → 再读取下一章节规则”推进。"),
        ("一并查看用户本轮提供的章节交接材料；其中的预留标识可帮助定位对象，结果仍须回到已验收的来源核实。", ""),
        ("LaTeX 按生效的源文件和 label/ref 核对，Word 按实际标题、题注或交叉引用核对。仅交付提纲时登记拟放位置，正文形成后再回填实际锚点。", ""),
        ("前期图表预登记是后续写作的输入。每问开始前按 §13.0 盘点相关登记并安排用途，不能只凭图型或聊天记忆临时找图。\n\n", ""),
        ("""**预登记到写作的交接。** 图表可以先于论文制作；前期在现有“论文位置”／Paper location 中登记“所属小问或共享范围＋预期论证功能”，例如“问题二／结果与分析，具体小节写作时确定”。尚无正文时，“正文引用位置”留空，不预写物理行号、页码，不提前锁死三级标题；归属未定时在原位置或既有待办中说明。Figure role 保持原有证据用途定义，不改成章节槽位。

1. **该问开始先盘点。** 结合当前模板、active 骨架和标题规划，读取本问全部相关登记，包括仅在全局证据链出现、跨问共享、位置空缺或待定的对象，复用同一 Figure ID／已有表标识及来源。不能先按“结果节图”筛选而漏掉未定项。全论文或跨聊天恢复仍按现行要求读取完整框架；随后再按本问与功能节定向读取。
2. **安排后分节消费。** 按真实支撑判断和 current 证据确定主要展示位置及解释任务，再按标识检索必要登记行、表头、合同和证据。当前 resolver 不自动筛选图表行；这是现有项目文本的读取动作。未运行、未导出、未确认或缺相应 accepted 证据的对象只能保留待办或舍弃，不能因排好位置自动变成可入文。机理图沿用自身来源与审阅要求，不补造工作簿。
3. **该问完成核对去向。** 对本范围拟入文对象明确采用、合并、拆分、移位、省略、弃用或仍待完成的实际处置；在现有映射、当前写作选择或待办中记必要理由，不新增记录表或状态枚举。采用后将“论文位置”更新为真实章节／小节标题路径，并回填实际 caption 与正文引用锚点；数字编号只作辅助。合并或拆分保留新旧对象及来源关系，其他章节回指主要展示位置，不重复计作新证据。省略时确认必要答案与证据仍有适当表达，不强迫全部图表入文；只写一问不宣称全文已闭合。

普通表格沿用已有表标识、caption/label 或唯一名称，在现有标题规划／写作选择中承接用途和位置，不插入 Figure 九列表，不强制图片文件、MATLAB 绘图脚本或 B2 Figure 绑定。已启用 B2 的图片被替换或移除时，原绑定、Paper Fragment 和 policy 要求仍按原规则处理；文字处置或改成表格不等于原 Figure 门已通过，不自动关闭 policy。协议不能表达的替代保留为原流程未闭合项。

旧项目不补造历史预登记，也不批量迁移；本次触及的写作范围按现有证据补充即可。归属裁决不增加逐图用户审批；图片本身的既有人工确认要求保持。上述交接适用于当前实际论文骨架，非 CUMCM 不强套本节列举的 CUMCM 字面标题。

""", ""),
    ),
    "core/writing_reasoning_contract.yaml": (
        ("        预登记到正文的盘点、落位和实际引用回填统一消费 modules/05_writing/paper_writing_protocol.md#13.0-CUMCM-图表的正文落点先论证职责后图型，非 CUMCM 使用自身实际骨架。\n", ""),
    ),
    "modules/06_review_delivery.md": (
        ("- 按 Protocol §13.0 核对预登记与入文；\n", ""),
    ),
}


# Batch A adds only two evidence-preserving prose rules. Invert these exact
# paragraphs before the unchanged historical authority projections; the old
# protected hashes continue to reject every unrelated byte change.
DEFENSIVE_WRITING_AUTHORITY_REWRITES = {
    "modules/05_writing/paper_writing_protocol.md": (
        ("表达结果、比较与局限时，优先直接写明研究对象、适用条件、比较基准、实际结果及其影响范围。对于“遗憾的是”等不承载事实的道歉或自我辩解前缀，可以省去；若其后内容涉及真实负向结果、失败检验、数据缺口或适用限制，应保留相应事实。“仅”“尚未”“未显著”“局部”“可能”“在当前样本/测试范围内”“受限于”等表达按事实功能判断，不作通用禁词；它们承载数学条件、范围、统计状态、证据等级或适用边界时必须保留。不得为突出优势而改换题目指定指标、删去必要比较或把局部结果推广为整体结论，也不得把未开展的验证写成已完成。\n\n", ""),
    ),
    "modules/05_writing/ai_cleanup.md": (
        ("对无信息价值的自我削弱包装，只允许移除包装，不得顺带改写其后的事实。例如，“遗憾的是，该方法在测试集 B 上的 MAE 比基线高 12%”可以去掉“遗憾的是”，但必须保留测试集、指标、基线、差异方向与数值；“遗憾的是，该方法仅取得一定效果”最多去掉道歉前缀，“仅取得一定效果”仍须保留，不得补造量化指标。\n“仅”“尚未”“未通过/未观察到显著差异”“局部”“可能”“在当前样本/测试范围内”“受限于”等词不是禁词。它们承载数学前提、比较范围、统计状态、未完成事项、适用条件或证据等级时必须保留其限定作用；不得改写成更强或更弱的主张。真实负面结果、失败实验、题目要求的指标比较、模型适用边界与失效范围不得删除、淡化、换指标或移出必要论证位置。若去除措辞后会改变事实、比较或限定，Keep 并报告；需要改变评价目标、解释原因或调整结论时返回上游，不由 Cleanup 决定。\n\n", ""),
    ),
}


# v10.20.4 assigns the existing PDF visual review to the assistant. Project
# only this compact delivery paragraph, preserving the existing byte budget,
# back to v10.20.3; keep every historical PROTECTED hash unchanged.
PDF_REVIEW_OWNER_REWRITES = {
    "modules/06_review_delivery.md": (
        (
            "交付须用最新 LaTeX audit、compile report、PDF、project sync、submission package validation。每问条件 3+2 文件及目录/包边界依 `core/output_contract.yaml#per_question` 与 Artifact Packs，不复列；stale source bundle、未解析引用、编译错误、manifest/hash 不一致依既有 gate。PDF 逐页检查由助手按 Module 05D 执行。",
            "正式交付消费最新 LaTeX audit、compile report、PDF、project sync 和 submission package validation。每问条件 3+2 文件及目录/包边界只核对 `core/output_contract.yaml#per_question` 和 Artifact Packs；Review 不复制清单。任何 stale source bundle、未解析引用、编译错误、manifest/hash 不一致按既有 gate 处理。",
        ),
    ),
}


# v10.20.3 reopens only optional MATLAB native coverage and explicit checker
# ownership. Invert these exact blocks to c2181e8 before the older projections;
# the unchanged PROTECTED hashes still reject every unrelated byte change.
USER_CHECKER_AUTHORITY_REWRITES = {
    "modules/03_solve_validate.md": (
        (
            (
                "\n"
                "进入本模块前，助手为当前小问依次执行 `scripts/validate_semantic_governance.py` 与 `scripts/validate_model_approval.py`。前者负责当前题意/语义/复杂度与 stale 一致性，后者是 Challenge/Human Approval 的唯一字段级运行门；具体批准状态、revision/structured identity 绑定与失效条件只服从 `core/model_approval_contract.yaml`，本模块不复制第二套检查清单。\n"
                "\n"
            ),
            (
                "\n"
                "进入本模块前，当前小问必须依次通过 `scripts/validate_semantic_governance.py` 与 `scripts/validate_model_approval.py`。前者负责当前题意/语义/复杂度与 stale 一致性，后者是 Challenge/Human Approval 的唯一字段级运行门；具体批准状态、revision/structured identity 绑定与失效条件只服从 `core/model_approval_contract.yaml`，本模块不复制第二套检查清单。\n"
                "\n"
            ),
        ),
        (
            (
                "\n"
                "正式交付前必须从项目根恢复并核验唯一求解后端；缺失、冲突或 `auto` 均不得交付，也不得为本问另选语言。按 resolver 的后端资源映射读取该语言模板，不同时生成两份求解器。配置、1.1 回执、主入口 SHA 与源码 bundle 的绑定只服从 `core/user_execution_contract.yaml`；助手按 `core/code_quality_contract.yaml` 完成必需工程检查，并如实报告 MATLAB 原生分析的实际覆盖。\n"
                "\n"
            ),
            (
                "\n"
                "正式交付前必须从项目根恢复并核验唯一求解后端；缺失、冲突或 `auto` 均不得交付，也不得为本问另选语言。按 resolver 的后端资源映射读取该语言模板，不同时生成两份求解器。配置、1.1 回执、主入口 SHA 与源码 bundle 的绑定只服从 `core/user_execution_contract.yaml`；工程检查按 `core/code_quality_contract.yaml` 分流。MATLAB 无原生分析器时明确未核验项，不把静态字符串检查当作正式工程验收。\n"
                "\n"
            ),
        ),
        (
            (
                "\n"
                "用户返回工作簿后，助手通过 `scripts/validate_user_execution.py` 核验执行所有权、full-fidelity 配置和代码/数据哈希，并由其调用 `scripts/validate_numerical_evidence.py` 独立复核适用主数值证据；工作簿自行写出的“是否通过”不能替代机器可重算的证据一致性。v7.13 历史工作簿保持只读兼容；旧项目重新进入当前主求解时应按 v7.14 轨迹生成本问新工作簿。\n"
                "\n"
            ),
            (
                "\n"
                "返回工作簿时 `scripts/validate_user_execution.py` 先核验执行所有权、full-fidelity 配置和代码/数据哈希，再调用 `scripts/validate_numerical_evidence.py` 独立复核适用主数值证据；工作簿自行写出的“是否通过”不能替代机器可重算的证据一致性。v7.13 历史工作簿保持只读兼容；旧项目重新进入当前主求解时应按 v7.14 轨迹生成本问新工作簿。\n"
                "\n"
            ),
        ),
        (
            (
                "→ 生成所选主求解入口前锁定 Primary Evidence Capture 项\n"
                "→ 助手执行代码交付检查：执行配置 + 代码工程质量门\n"
                "→ 用户本地full_fidelity运行，同时保存最终答案 + 真实状态/过程/结构证据\n"
                "→ 用户返回问题X求解结果.xlsx\n"
                "→ 助手验收：运行配置/哈希 + 主结果质量门 + numerical evidence独立复核\n"
                "→ accepted后冻结所选主求解入口及其声明源码依赖\n"
            ),
            (
                "→ 生成所选主求解入口前锁定 Primary Evidence Capture 项\n"
                "→ validate_code_delivery.py：执行配置 + 代码工程质量门\n"
                "→ 用户本地full_fidelity运行，同时保存最终答案 + 真实状态/过程/结构证据\n"
                "→ 问题X求解结果.xlsx\n"
                "→ validate_user_execution.py：运行配置/哈希 + 主结果质量门 + numerical evidence独立复核\n"
                "→ accepted后冻结所选主求解入口及其声明源码依赖\n"
            ),
        ),
    ),
    "modules/03_result_analysis.md": (
        (
            (
                "→ 读取当前数据事实源 + 已验收问题X求解结果.xlsx + 必要前问标准工作簿\n"
                "→ 助手静态验收analysis阶段代码\n"
                "→ 用户本地full_fidelity运行\n"
                "→ 用户返回同目录问题X结果深化分析.xlsx\n"
                "→ 助手按执行Authority验收返回工作簿\n"
                "→ 对每项证据给出support / modify / reject\n"
            ),
            (
                "→ 读取当前数据事实源 + 已验收问题X求解结果.xlsx + 必要前问标准工作簿\n"
                "→ validate_code_delivery.py静态验收analysis阶段代码\n"
                "→ 用户本地full_fidelity运行\n"
                "→ 同目录问题X结果深化分析.xlsx\n"
                "→ validate_user_execution.py验收\n"
                "→ 对每项证据给出support / modify / reject\n"
            ),
        ),
    ),
}


# Reconstruct the exact predecessors of the v10.34.0 PQS changes.
# Each tuple binds a unique changed range by its first line, size and digest.
# Bytes elsewhere stay visible to the pre-existing historical checks.
PRIMARY_QUALITY_BINDING_BLOCKS = {
    "core/model_approval_contract.yaml": (
        (
            "  approval_brief_field_semantics:", 6,
            "21c5dbfb0396c138461e986af2a7e4539c7e20671e5be0ba161fcb95158cb536",
            (
                "  approval_brief_field_semantics:\n"
                "    next_stage_implementation_scope: >-\n"
            ),
        ),
        (
            "    purpose: declared_model_comparison_only_not_a_new_global_identity", 5,
            "c832bff2d01709ce465b0c97291dcde90cc67773b873610bc567371dc02b80ff",
            (
                "    purpose: declared_model_comparison_only_not_a_new_global_identity\n"
                "    retain: all_model_fields_all_extensions_and_unknown_algorithm_content\n"
                "    removable_scalar_implementation_keys: [family, method, solver, solver_role, implementation, backend]\n"
            ),
        ),
    ),
    "core/numerical_verification_contract.yaml": (
        (
            "", 15,
            "dc4837096f273aa7bf347cb1c6d59d1d4d0f49224402ea8325a5f9fe892f7af3",
            (
                "\n"
                "strict_v714_trace:\n"
            ),
        ),
    ),
    "core/workbook_schema.yaml": (
        (
            "      required_columns: [检查项, 是否通过, 证据]", 3,
            "4d1208f3239ea57af87ee9fb7c3619fc43819530047fc0d0c0b1f36e36ff4f10",
            (
                "      required_columns: [检查项, 是否通过, 证据]\n"
                "      optional_columns: [Verification ID, 判定关系, 阈值或容差, 实际值, 证据工作表, 阈值来源, 说明]\n"
                "  common_recommended_sheets:\n"
            ),
        ),
    ),
    "scripts/validate_code_delivery.py": (
        (
            "import run_config_parser as RUN_CONFIG_PARSER  # noqa: E402", 3,
            "6e925d87ce6663d85fbf936c57ff6397d728473513e0fdad2036f26569515ac2",
            (
                "import run_config_parser as RUN_CONFIG_PARSER  # noqa: E402\n"
                "import analysis_prerequisites as ANALYSIS_PREREQUISITES  # noqa: E402\n"
            ),
        ),
        (
            "import analysis_comparison_gate as COMPARISON  # noqa: E402", 6,
            "c5a91bb6f15680553c2d3c90a3d1762b0219314dac9b36d27fc37b670491df16",
            (
                "import analysis_comparison_gate as COMPARISON  # noqa: E402\n"
                "from execution_protocol import SOURCE_RECEIPT_VERSIONS, is_source_receipt, auxiliary_config_issues, comparison_config_issues\n"
                "from stage_inputs import InputUnavailableError, input_files, observe_inputs, observe_preprocessing_inputs\n"
            ),
        ),
        (
            "}", 2,
            "ae9875969ebd12ee08892dd52ec6ae54d549c9629a948c4c3467f5814fcf8320",
            (
                "}\n"
                "PRIMARY_QUALITY_PROTOCOL_VERSION = \"1.0.0\"\n"
                "PRIMARY_REQUIRED_FIELDS = {\"primary_quality_protocol_version\"}\n"
            ),
        ),
        (
            "                issues.append(f\"primary嵌入运行配置缺少字段: {field}\")", 7,
            "9513aef5df2b7dabee7df3531c821cfad359b151526d4bfbd4775718971927f3",
            (
                "                issues.append(f\"primary嵌入运行配置缺少字段: {field}\")\n"
                "        if config.get(\"primary_quality_protocol_version\") not in (None, \"\", PRIMARY_QUALITY_PROTOCOL_VERSION):\n"
                "            issues.append(f\"primary_quality_protocol_version必须为{PRIMARY_QUALITY_PROTOCOL_VERSION}\")\n"
                "    elif config.get(\"primary_quality_protocol_version\") not in (None, \"\"):\n"
                "        issues.append(\"primary_quality_protocol_version只允许出现在primary阶段运行配置\")\n"
                "    if stage and stage != filename_stage:\n"
            ),
        ),
        (
            "    observed_state = load_yaml(state_path)", 10,
            "4307f8398ede56a5bb971b98332796ad7897fdba705ff4505b5bffd48791283f",
            (
                "    observed_state = load_yaml(state_path)\n"
                "    guarded = any(CONFORMANCE.present(entry) or COMPARISON.present(entry, config=config)\n"
                "                  for entry in (observed_state.get(\"subproblems\") or {}).values())\n"
                "    stage = str(config[\"stage\"])\n"
                "    if not guarded:\n"
            ),
        ),
        (
            "    entry = state.setdefault(\"subproblems\", {}).setdefault(key, {})", 14,
            "572a657ac42a12e42917e2af7d16092c71afafdca18d408aa5d0d24e103ae8a9",
            (
                "    entry = state.setdefault(\"subproblems\", {}).setdefault(key, {})\n"
                "    conformance = CONFORMANCE.inspect_gate(\n"
            ),
        ),
        (
            "    CONFORMANCE.merge_read_sets(observed, preprocessing_observed)", 3,
            "a4ed8a3d796392cd7d2b640f8b8f8b775076ec118ca02e5801b282b600247563",
            (
                "    CONFORMANCE.merge_read_sets(observed, preprocessing_observed)\n"
                "    CONFORMANCE.assert_observed(project_root, observed)\n"
            ),
        ),
    ),
}


# Reconstruct only the exact scoped v10.35.0 execution scale edits.
EXECUTION_SCALE_BINDING_BLOCKS = {
    "core/workbook_schema.yaml": (
        (
            "      optional_columns: [用于主判定, 容差, 说明]", 4,
            "62e89517bfe04c7e10b07cf7b8e0f49b474ea73ffecf019286a8a67098709e21",
            (
                "      optional_columns: [用于主判定, 容差, 说明]\n"
                "    外样本验证:\n"
            ),
        ),
    ),
    "scripts/validate_code_delivery.py": (
        (
            ")", 3,
            "4ea62d8d4e0e752e740da6da52e5c6316c3da51bdc8815c116b3e3f4b7faef0d",
            (
                ")\n"
                "from stage_inputs import InputUnavailableError, input_files, observe_inputs, observe_preprocessing_inputs\n"
            ),
        ),
        (
            "    issues.extend(comparison_config_issues(config))", 4,
            "3b3c0149ebca5197a0c6b7d4eefe2f879de2cee3c9434a89456329f01198ebfc",
            (
                "    issues.extend(comparison_config_issues(config))\n"
                "    source_fingerprint = None\n"
            ),
        ),
        (
            "                issues.append(f\"primary嵌入运行配置缺少字段: {field}\")", 3,
            "4e58e943802b71898209e2ec625598dcb9436b80a5e7d50fc07394f3d9c9372b",
            (
                "                issues.append(f\"primary嵌入运行配置缺少字段: {field}\")\n"
                "        _, quality_issues, _ = PRIMARY_QUALITY.inspect_gate(\n"
                "            project_root, state, _question_key(problem), config, enforce_current_sib=True,\n"
            ),
        ),
        (
            "        issues.extend(quality_issues)", 4,
            "09945c58cad52a3511b2f45c3680c73bfaa571bd7d6669cec33f3cf95beb4f38",
            (
                "        issues.extend(quality_issues)\n"
                "    issues.extend(primary_quality_config_issues(config))\n"
            ),
        ),
        (
            "    configuration_issues.extend(comparison_config_issues(config))", 4,
            "74e30ad75c91f2ec3af7d4accc0c613f6c23523ecaf8facf4c2a3ba9602bb573",
            (
                "    configuration_issues.extend(comparison_config_issues(config))\n"
                "    if configuration_issues:\n"
            ),
        ),
        (
            "    observed_state = load_yaml(state_path)", 3,
            "949581c67d440608b1a6d7050ac9073ba6cb615fb8e1b8927f2dad96c8bc0c0f",
            (
                "    observed_state = load_yaml(state_path)\n"
                "    guarded = PRIMARY_QUALITY.binding_present(config) or any(\n"
                "        CONFORMANCE.present(entry) or COMPARISON.present(entry, config=config)\n"
            ),
        ),
        (
            "    quality_observed = {\"project\": {}, \"skill\": {}}", 3,
            "0ba55625591ad2048ae3531f8b349a06e134b48851579892e717666be3fc7aad",
            (
                "    quality_observed = {\"project\": {}, \"skill\": {}}\n"
                "    if stage == \"primary\":\n"
            ),
        ),
        (
            "        )", 11,
            "a4603adb2d0aee6dd7d24bc86fdb27626f889f36d37331d9c96ca66ed263120e",
            (
                "        )\n"
                "        if quality_issues:\n"
                "            raise ValueError(\"; \".join(quality_issues))\n"
                "        if specification is not None:\n"
                "            _, actual_config = STAGE_CODE.parse_stage_config(script)\n"
                "            if actual_config != config:\n"
                "                raise ValueError(\"PQS: delivery configuration differs from the actual primary source\")\n"
                "            quality_observed[\"project\"][relative] = new_hash\n"
                "    conformance = CONFORMANCE.inspect_gate(\n"
            ),
        ),
    ),
}


def _prior_reviewed_blocks(relative: str, text: str, blocks, label: str) -> str:
    lines = text.splitlines(keepends=True)
    for first, count, digest, previous in blocks.get(relative, ()):
        matches = [
            start for start, line in enumerate(lines)
            if line == first + "\n"
            and hashlib.sha256("".join(lines[start:start + count]).encode("utf-8")).hexdigest() == digest
        ]
        if len(matches) != 1:
            raise ValueError(f"{relative}: approved {label} block missing or duplicated: {first.strip()}")
        start, = matches
        lines[start:start + count] = previous.splitlines(keepends=True)
    return "".join(lines)


# Exact candidate changes relative to the P4a source. Older projections run on its recovered bytes.
ORDINARY_EXPERIMENT_BLOCKS = {
    "core/workbook_schema.yaml": (
        (
            '  - 同模型多算法检验', 16,
            "3521050ad239dcc7d67c3c5346af8f37d7434c830b318d4610092c7664c86277",
            (
                '  - 同模型多算法检验\n'
                '  # Each recognized ordinary method in the current plan requires its own substantive table.\n'
            ),
        ),
    ),
    "modules/03_result_analysis.md": (
        (
            '独立深化入口 是独立可复现程序，不复制主求解主链，不通过改写 主求解入口 实现深化分析。新生成脚本必须只定义一个按执行 Authority 可静态读取的 `RUN_CONFIG`，其中 `stage="analysis"` 并锁定当前数据事实源的 `data_sha256`；user/full-fidelity/no-degradation 政策由 `core/user_execution_contract.yaml` 继承，不在脚本中重复自报。工作簿中的 `code_sha256` 必须对应该深化分析脚本，并继续完整记录 solver/version、stop、platform、fallback 与 no-degradation 等实际运行事实。旧 `FULL_FIDELITY_CONFIG/FULL_RUN_CONFIG` 仅作只读兼容。', 8,
            "fa6e15591e01d3fdd896e1635f89d36e470da906a64be3bfaa6239da9a1d1414",
            (
                '独立深化入口 是独立可复现程序，不复制主求解主链，不通过改写 主求解入口 实现深化分析。新生成脚本必须只定义一个按执行 Authority 可静态读取的 `RUN_CONFIG`，其中 `stage="analysis"` 并锁定当前数据事实源的 `data_sha256`；user/full-fidelity/no-degradation 政策由 `core/user_execution_contract.yaml` 继承，不在脚本中重复自报。工作簿中的 `code_sha256` 必须对应该深化分析脚本，并继续完整记录 solver/version、stop、platform、fallback 与 no-degradation 等实际运行事实。旧 `FULL_FIDELITY_CONFIG/FULL_RUN_CONFIG` 仅作只读兼容。\n'
                '\n'
            ),
        ),
    ),
    "scripts/validate_code_delivery.py": (
        (
            '    SOURCE_RECEIPT_VERSIONS, is_source_receipt, auxiliary_config_issues, comparison_config_issues,', 3,
            "fae3b548190ec1b4b2b9dcab519639504fd8365e1cc4e67ebaa3bdd909088eb4",
            (
                '    SOURCE_RECEIPT_VERSIONS, is_source_receipt, auxiliary_config_issues, comparison_config_issues,\n'
                '    primary_quality_config_issues,\n'
                ')\n'
            ),
        ),
        (
            '    modern = is_source_receipt(receipt_protocol)', 3,
            "8071d9cb68cf93d4fab86f720a177d27e74a39733d5c7b03a296834942253e5e",
            (
                '    modern = is_source_receipt(receipt_protocol)\n'
                '    issues.extend(auxiliary_config_issues(config))\n'
            ),
        ),
        (
            '            issues.append(str(exc))', 9,
            "c9c09cb7342b88c367ec22187f5dade3b08cc2e319b74173234d82c614783ca4",
            (
                '            issues.append(str(exc))\n'
                '    if stage == "primary":\n'
            ),
        ),
        (
            '    configuration_issues.extend(scale_issues)', 3,
            "25f1db8dacfa218e69b452152e25fb9e9b6a675b7473e6695df3f08f9dd41131",
            (
                '    configuration_issues.extend(scale_issues)\n'
                '    if configuration_issues:\n'
            ),
        ),
        (
            '    observed_state = load_yaml(state_path)', 3,
            "e0b58ac9849fc3a0080ad6c59d9655882b5561ecb1a28a7e944a99c487bb8272",
            (
                '    observed_state = load_yaml(state_path)\n'
                '    guarded = scale_plan is not None or PRIMARY_QUALITY.binding_present(config) or any(\n'
                '        CONFORMANCE.present(entry) or COMPARISON.present(entry, config=config)\n'
            ),
        ),
        (
            '    quality_observed = {"project": {}, "skill": {}}', 21,
            "37666265bd014848c15edc98b1506bf906e6dc32bb36a0d91ce19bb9dd3ce164",
            (
                '    quality_observed = {"project": {}, "skill": {}}\n'
                '    specification = None\n'
            ),
        ),
        (
            '        expected_file_hashes=observed["project"] or None,', 3,
            "05eda83d002ac46c25eedfa65a4a9901f91aaef51c952dff40e12feba6019e59",
            (
                '        expected_file_hashes=observed["project"] or None,\n'
                '        validators=[CONFORMANCE.skill_validator(observed)] if conformance["enabled"] or comparison["enabled"] else (),\n'
                '    )\n'
            ),
        ),
    ),
}


# Reverse the exact P4d workbook and numerical contract edits for older byte-level checks.
WORKBOOK_ACCEPTANCE_BLOCKS = {
    "core/workbook_schema.yaml": (
        (
            '  key_policy: 显式记录键或样本键必须非空且唯一', 3,
            "17ea9cb5e5edbeb887d0c935fbe0e2420978a839ba3f18016fb689d82185b0f8",
            (
                '  key_policy: 显式记录键或样本键必须非空且唯一\n'
                '  numeric_policy: 数值字段不得包含正负无穷；有依据的缺失值必须在数据审计中说明\n'
                '  constraint_judgement_policy: 违反量、容差和是否满足必须逻辑一致\n'
            ),
        ),
        (
            '      required_columns: [指标, 数值]', 8,
            "abb9e712d55cc85b3175e4adc2c217de16e2506d24e96b322b3de36d22c393c5",
            (
                '      required_columns: [指标, 数值]\n'
                '      optional_columns: [单位, 统计口径, 说明]\n'
                '    数据审计:\n'
            ),
        ),
        (
            '      required_columns: [主体或均衡, 残差, 容差, 是否满足]', 6,
            "2717aa8b0b8a3d8cd7ba0e5d8b33d7fe898864b17e6535786f12d0d55993ee79",
            (
                '      required_columns: [主体或均衡, 残差, 容差, 是否满足]\n'
                '    守恒残差:\n'
                '      required_columns: [守恒量, 残差, 容差, 是否满足]\n'
                '    离散精度:\n'
            ),
        ),
        (
            '      required_columns: [指标, 下界, 上界]', 7,
            "8556d5a081afb5e0479334ead3a78d52ef3f89d49cd8a71cc4de559fa2f4cce3",
            (
                '      required_columns: [指标, 下界, 上界]\n'
                '      optional_columns: [置信水平, 分位数口径, 样本数, 单位]\n'
                '    泄漏检查:\n'
            ),
        ),
    ),
    "core/numerical_verification_contract.yaml": (
        (
            '    evidence_sheet: 不确定性区间', 3,
            "8db50dcb9ce1d4828c9149a27abfa60e9edc9344f6cb700151aadc19f97c6ea8",
            (
                '    evidence_sheet: 不确定性区间\n'
                '    recheck_mode: summary_criterion\n'
            ),
        ),
        (
            '    source_columns: [残差, 容差, 是否满足]', 12,
            "3ea95af15688372a370898d4287f01cdadf126f9b62fba53520b9830ed6f6b1c",
            (
                '    source_columns: [残差, 容差, 是否满足]\n'
                '    computed_metric: max_abs_value\n'
            ),
        ),
    ),
}


# P5 extended two applicability windows (9f23163) and clarified when legacy
# workbook IDs select strict validation (d525b06). Recover only those lines.
P5_COMPATIBILITY_BLOCKS = {
    "core/workbook_schema.yaml": (
        ("skill_compatibility: '>=6.3.2,<12.0.0'", 1,
         "fe75013e74f69d8e89b4566e226eb562b4aa6a1d09d6ca0186318af626cfe867",
         "skill_compatibility: '>=6.3.2,<11.0.0'\n"),
    ),
    "core/numerical_verification_contract.yaml": (
        ("skill_compatibility: '>=7.14.0,<12.0.0'", 1,
         "1a49db9812496e2cdd76b25d40e8d682754b9c0478fc8aeec9426257f6964632",
         "skill_compatibility: '>=7.14.0,<11.0.0'\n"),
        ("    - 主结果质量门 contains a Verification ID other than an absent cell, an empty cell, or whitespace-only text", 1,
         "c1ea648035fc1e445c04f947beb9b7aca93b7f25c6548826e8f08d1d46816177",
         "    - 主结果质量门 contains a non-empty Verification ID\n"),
    ),
}


# M3 adds current question-scoped dependency checks to the code-delivery
# consumer. The v10.27/v11 historical inverse still compares the unchanged
# predecessor exactly: recover ONLY these four reviewed M3 hunks after checking
# the complete current source SHA-256, then authenticate recovered old bytes.
# No absent, altered, duplicated or extra hunk may masquerade as old evidence.
M3_CODE_DELIVERY_SHA256 = "b62361eb21b0c47aa5fbf5b5508dbec41f9b18f7a385fbf039762e43c4474b0b"
PRE_M3_CODE_DELIVERY_SHA256 = "f02ec4ca63fa426b953aa75469d651d66e7bbf50c50bfd80444aa1c8b7087ccc"
M3_CODE_DELIVERY_HUNKS = (
    (
        "import question_dependency_gate as QUESTION_DEPENDENCIES  # noqa: E402\n",
        "",
    ),
    (
        '    # M3 is a real code-delivery prerequisite, not a read-only Resolver\n'
        '    # diagnostic. Do not inspect unrelated Qn; the helper observes only the\n'
        '    # current target\'s typed input sources against the shared State snapshot.\n'
        '    if stage in {"primary", "analysis"} and state_path.is_file():\n'
        '        try:\n'
        '            prerequisites = QUESTION_DEPENDENCIES.inspect(\n'
        '                project_root, _question_key(problem), config=config,\n'
        '            )\n'
        '            issues.extend(prerequisites["issues"])\n'
        '        except (OSError, ValueError, TypeError) as exc:\n'
        '            issues.append(f"{_question_key(problem)}: upstream dependency qualification failed: {exc}")\n',
        "",
    ),
    (
        '    # Typed prerequisites contribute a file-backed read-set even for an\n'
        '    # ordinary, formerly unguarded numerical delivery. Always bind the original\n'
        '    # State bytes as the transaction\'s write target before adding those sources.\n'
        '    if guarded or stage in {"preprocessing", "primary", "analysis"} or preprocessing_batch:\n',
        '    if guarded or stage == "preprocessing" or preprocessing_batch:\n',
    ),
    (
        '    dependencies = QUESTION_DEPENDENCIES.inspect(\n'
        '        project_root, key, config=config, snapshot=snapshot,\n'
        '    )\n'
        '    if dependencies["issues"]:\n'
        '        raise ValueError("; ".join(dependencies["issues"]))\n'
        '    # Bind exactly observed upstream files to the existing atomic delivery read\n'
        '    # set. Any concurrent change before commit must fail, never re-qualify.\n'
        '    CONFORMANCE.merge_read_sets(preprocessing_observed, dependencies["observed_sources"])\n',
        "",
    ),
)


def m3_predecessor_code_delivery(relative: str, text: str) -> str:
    if relative != "scripts/validate_code_delivery.py":
        return text
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != M3_CODE_DELIVERY_SHA256:
        raise ValueError("M3 code-delivery current source identity drift")
    for after, prior in M3_CODE_DELIVERY_HUNKS:
        if text.count(after) != 1:
            raise ValueError("M3 code-delivery approved hunk missing or duplicated")
        text = text.replace(after, prior, 1)
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != PRE_M3_CODE_DELIVERY_SHA256:
        raise ValueError("M3 predecessor does not match exact pre-M3 source")
    return text


def p4a_authority_text(relative: str) -> str:
    text = (ROOT / relative).read_text(encoding="utf-8")
    text = m3_predecessor_code_delivery(relative, text)
    text = _prior_reviewed_blocks(relative, text, P5_COMPATIBILITY_BLOCKS, "P5 compatibility")
    text = _prior_reviewed_blocks(relative, text, WORKBOOK_ACCEPTANCE_BLOCKS, "workbook acceptance")
    return _prior_reviewed_blocks(relative, text, ORDINARY_EXPERIMENT_BLOCKS, "ordinary experiment")


# Reconstruct only the approved v10.35.1 ordinary-method schema additions.
ORDINARY_ANALYSIS_COVERAGE_BLOCKS = {
    "core/workbook_schema.yaml": (
        (
            "  - 同模型多算法检验", 17,
            "7e5586ce8755032825ac417bcf111f8eddfcc244c3b3103432283c7046f6ffc0",
            (
                "  - 同模型多算法检验\n"
                "  comparison_method_sheets:\n"
            ),
        ),
    ),
}


def prior_ordinary_analysis_coverage(relative: str, text: str) -> str:
    return _prior_reviewed_blocks(relative, text, ORDINARY_ANALYSIS_COVERAGE_BLOCKS, "ordinary analysis")


def prior_execution_scale_binding(relative: str, text: str) -> str:
    predecessor = prior_ordinary_analysis_coverage(relative, text)
    return _prior_reviewed_blocks(relative, predecessor, EXECUTION_SCALE_BINDING_BLOCKS, "execution scale")


def prior_primary_quality_binding(relative: str, text: str) -> str:
    return _prior_reviewed_blocks(relative, text, PRIMARY_QUALITY_BINDING_BLOCKS, "PQS")


# PR #327 changes only these regions of validate_code_delivery.py. Each tuple
# identifies one reviewed block by its first line, length and SHA-256, followed
# by its exact v10.32.0 predecessor. Positions outside those blocks remain live.
PREPROCESSING_REDELIVERY_BLOCKS = (
    (
        "from stage_inputs import InputUnavailableError, input_files, observe_inputs, observe_preprocessing_inputs", 1,
        "68a96abb3254264c9f1f957ef879ebca45070b97121ef0c0d9b913637c7d338e",
        "from stage_inputs import observe_inputs\n",
    ),
    (
        "def _preprocessing_registration(state: Mapping[str, Any]) -> tuple:", 71,
        "b89af571ccf9607ad29b21515c2f781d05b47cc0534441e34a5d68d8dd170a69",
        (
            "def update_state(project_root: Path, config: dict[str, Any], script: Path, *,\n"
            "                 expected_source_sha256: str | None = None,\n"
            "                 expected_bundle_sha256: str | None = None) -> list[dict[str, Any]]:\n"
        ),
    ),
    (
        "    stage = str(config[\"stage\"])", 16,
        "63d9ee73e72a4d33904f77dd1d84e63d78df2ef5c92cf6ad087d55714a919fb4",
        (
            "    if guarded:\n"
            "        from runtime_assurance import ProjectStateSnapshot\n"
            "        snapshot = ProjectStateSnapshot.capture(project_root)\n"
            "        state = snapshot.payload()\n"
            "        base_generation = PROJECT_TX.state_generation(state)\n"
            "    else:\n"
            "        _, state, base_generation = PROJECT_TX.load_state_for_update(project_root)\n"
            "    problem = str(config[\"problem_name\"])\n"
            "    stage = str(config[\"stage\"])\n"
        ),
    ),
    (
        "        preprocessing_observed[\"project\"][relative] = new_hash", 19,
        "b153f527c6b0e59f2b2a374a8999c383bbc33d0a4dbb1752f869922246f08467",
        "        old_hash = preprocessing.get(\"code_sha256\")\n",
    ),
    (
        "        if change:", 1,
        "65784959f2af75b1ed4045fb247e523ab2033e33d31a7b9d41dd888a85eafcb0",
        "        if old_hash and old_hash != new_hash:\n",
    ),
    (
        "                        \"reason\": change,", 6,
        "56143a6a50e98ab65bee46133dc514c8ad057a64405ded73f206a11569f46500",
        (
            "                        \"reason\": \"project-level preprocessing code changed\",\n"
            "                    }],\n"
            "                })\n"
            "        PROJECT_TX.commit_project_state(\n"
            "            project_root, state, expected_generation=base_generation\n"
        ),
    ),
    (
        "    CONFORMANCE.merge_read_sets(observed, preprocessing_observed)", 5,
        "c235bf0565c87d811baf427e59cdc102ca148b50172d09d9c335d51235688f6e",
        "    CONFORMANCE.assert_observed(project_root, observed)\n",
    ),
    (
        "    source = root / \"数据预处理/数据预处理.py\"", 5,
        "79bf698c733eb14c4c81438d883bb6a2bc569e3467d6621b5f9782ac9d2c28d2",
        "    scripts = [root / \"数据预处理/数据预处理.py\"] if (root / \"数据预处理/数据预处理.py\").is_file() else []\n",
    ),
    (
        "def _main() -> int:", 1,
        "13b487cf9bbbda556930bf186edbd80718bd379256a49758131efc9db3960539",
        "def main() -> int:\n",
    ),
    (
        "    preprocessing_batch = {} if args.write and not args.script else None", 1,
        "1b60ecbcfdb948c8d28449b70b7a8a2ad646793f5d2ddf8383ae192c018316bb",
        "",
    ),
    (
        "                                                       expected_bundle_sha256=native_report.get(\"validated_bundle_sha256\"),", 6,
        "3c61a6f6c3bb55871d979b26f1ee8dd053dc28c78c5f3c66125fd742219296b2",
        (
            "                                                       expected_bundle_sha256=native_report.get(\"validated_bundle_sha256\")))\n"
            "            except ValueError as exc:\n"
            "                issues.append(f\"{script.name}: {exc}\")\n"
        ),
    ),
    (
        "def main() -> int:", 11,
        "aa4cc4a77d0ce2844b75042b509a8a39561bbc6f6f33a6432f2916aeb603a4b5",
        "",
    ),
)


def prior_preprocessing_delivery(text: str) -> str:
    lines = text.splitlines(keepends=True)
    for first, line_count, digest, previous in PREPROCESSING_REDELIVERY_BLOCKS:
        matches = [
            start for start, line in enumerate(lines)
            if line == first + "\n"
            and hashlib.sha256("".join(lines[start:start + line_count]).encode("utf-8")).hexdigest() == digest
        ]
        if len(matches) != 1:
            raise ValueError(f"preprocessing re-delivery block missing or duplicated: {first.strip()}")
        start, = matches
        lines[start:start + line_count] = previous.splitlines(keepends=True)
    return "".join(lines)


# PR #279 (P6) is an authorized, narrowly scoped source-provenance refactor.
# Undo only its exact changed blocks before the older protected-blob projections.
# A different or duplicated block must fail; unrelated changes remain visible
# to the historical pinned Git blob digest.
P6_SOURCE_PROVENANCE_REWRITES = {
    "scripts/validate_code_delivery.py": (
        ("import stage_code as STAGE_CODE  # noqa: E402\nimport execution_provenance as EXECUTION_PROVENANCE  # noqa: E402\nimport conformance_gate as CONFORMANCE  # noqa: E402", "import stage_code as STAGE_CODE  # noqa: E402\nimport conformance_gate as CONFORMANCE  # noqa: E402"),
        ("        state = load_yaml(state_path) if state_path.is_file() else {}\n        conformance = CONFORMANCE.inspect_gate(\n            project_root, state, _question_key(problem), stage, boundary=\"delivery\",\n        )\n        issues.extend(conformance[\"issues\"])", "        state = load_yaml(state_path) if state_path.is_file() else {}\n        conformance = CONFORMANCE.inspect_gate(project_root, state, _question_key(problem), stage)\n        issues.extend(conformance[\"issues\"])"),
        ("    entry = state.setdefault(\"subproblems\", {}).setdefault(key, {})\n    conformance = CONFORMANCE.inspect_gate(\n        project_root, state, key, stage, boundary=\"delivery\",\n    )\n    if conformance[\"issues\"]:", "    entry = state.setdefault(\"subproblems\", {}).setdefault(key, {})\n    conformance = CONFORMANCE.inspect_gate(project_root, state, key, stage)\n    if conformance[\"issues\"]:"),
        ("        raise ValueError(f\"artifact identity alias conflict: {exc}\") from exc\n    phase = str((state.get(\"project\") or {}).get(\"current_phase\", \"\"))\n    cleanup_only = False\n    if stage == \"primary\":", "        raise ValueError(f\"artifact identity alias conflict: {exc}\") from exc\n    if stage == \"primary\":"),
        ("    if stage == \"primary\":\n        old_hash = entry.get(\"primary_code_sha256\")", "    if stage == \"primary\":\n        entry[\"data_hash\"] = str(config[\"data_sha256\"]).lower()\n        old_hash = entry.get(\"primary_code_sha256\")"),
        ("            and (selection.get(CONFORMANCE.ACCEPTANCE) or {}).get(\"applicability\") == \"current\")\n        source_changed = bool(old_hash != new_hash or binding_changed)\n        validated_hashes = entry.get(\"validated_artifact_hashes\") or {}\n        accepted_data_hash = str(\n            entry.get(\"validated_data_hash\") or validated_hashes.get(\"data\") or entry.get(\"data_hash\") or \"\"\n        ).lower()\n        accepted_issues, _ = (\n            EXECUTION_PROVENANCE.accepted_result_issues(project_root, state, entry, \"primary\")\n            if accepted else ([\"no accepted primary result\"], [])\n        )\n        old_conformance = selection.get(CONFORMANCE.DELIVERY) or {}\n        same_conformance_declaration = (\n            not conformance_binding\n            or (\n                isinstance(old_conformance, Mapping)\n                and old_conformance.get(\"declaration_sha256\") == conformance_binding.get(\"declaration_sha256\")\n            )\n        )\n        cleanup_only = bool(\n            accepted and entry.get(\"result_quality_status\") == \"passed\"\n            and (source_changed or conformance_changed) and same_conformance_declaration\n            and EXECUTION_PROVENANCE.is_cleanup_phase(phase)\n            and phase not in {\"review_delivery\", \"completed\"}\n            and EXECUTION_PROVENANCE.semantic_identity_is_fully_verified(entry)\n            and not accepted_issues\n            and accepted_data_hash\n            and str(config.get(\"data_sha256\") or \"\").lower() == accepted_data_hash\n        )\n        unchanged_accepted = accepted and not source_changed and unchanged_conformance\n        if accepted and source_changed and phase != \"solve_validate\" and not cleanup_only:\n            raise ValueError(\n                \"主求解脚本已accepted并冻结；仅在已验收结果、数据身份和模型语义仍有效的整理阶段\"\n                \"允许保留旧结果，否则必须先回到solve_validate\"\n            )\n        entry[\"data_hash\"] = str(config[\"data_sha256\"]).lower()\n        entry[\"code\"] = relative", "            and (selection.get(CONFORMANCE.ACCEPTANCE) or {}).get(\"applicability\") == \"current\")\n        unchanged_accepted = accepted and old_hash == new_hash and not binding_changed and unchanged_conformance\n        phase = str((state.get(\"project\") or {}).get(\"current_phase\", \"\"))\n        if accepted and old_hash and (old_hash != new_hash or binding_changed) and phase != \"solve_validate\":\n            raise ValueError(\"主求解脚本已accepted并冻结；如需修改必须先显式回退solve_validate\")\n        entry[\"code\"] = relative"),
        ("            entry[\"primary_execution_status\"] = \"awaiting_user_execution\"\n        if cleanup_only:\n            # Current delivery identity advances; validated_bundle_sha256 and the\n            # accepted workbook remain bound to the previous real execution.\n            pass\n        elif source_changed:\n            transition_reports.append(", "            entry[\"primary_execution_status\"] = \"awaiting_user_execution\"\n        if old_hash and (old_hash != new_hash or binding_changed):\n            transition_reports.append("),
        ("    else:\n        # analysis_issues() already verifies that the accepted primary workbook,\n        # not the current primary source bytes, is the required upstream artifact.\n        old_hash = entry.get(\"analysis_code_sha256\")", "    else:\n        if entry.get(\"primary_execution_status\") != \"accepted\":\n            raise ValueError(\"主工作簿未accepted，禁止交付最终结果深化分析脚本\")\n        old_hash = entry.get(\"analysis_code_sha256\")"),
        ("        old_hash = entry.get(\"analysis_code_sha256\")\n        source_changed = bool(old_hash != new_hash or binding_changed)\n        accepted_analysis = entry.get(\"analysis_execution_status\") == \"accepted\"\n        accepted_issues, _ = (\n            EXECUTION_PROVENANCE.accepted_result_issues(project_root, state, entry, \"analysis\")\n            if accepted_analysis else ([\"no accepted analysis result\"], [])\n        )\n        old_conformance = selection.get(CONFORMANCE.DELIVERY) or {}\n        same_conformance_declaration = (\n            not conformance_binding\n            or (\n                isinstance(old_conformance, Mapping)\n                and old_conformance.get(\"declaration_sha256\") == conformance_binding.get(\"declaration_sha256\")\n            )\n        )\n        validated_hashes = entry.get(\"validated_artifact_hashes\") or {}\n        accepted_data_hash = str(\n            entry.get(\"validated_data_hash\") or validated_hashes.get(\"data\") or entry.get(\"data_hash\") or \"\"\n        ).lower()\n        cleanup_only = bool(\n            accepted_analysis and entry.get(\"result_analysis_status\") == \"passed\"\n            and (source_changed or conformance_changed) and same_conformance_declaration\n            and EXECUTION_PROVENANCE.is_cleanup_phase(phase)\n            and phase not in {\"review_delivery\", \"completed\"}\n            and EXECUTION_PROVENANCE.semantic_identity_is_fully_verified(entry)\n            and not accepted_issues\n            and accepted_data_hash\n            and str(config.get(\"data_sha256\") or \"\").lower() == accepted_data_hash\n        )\n        entry[\"result_analysis_code\"] = relative", "        old_hash = entry.get(\"analysis_code_sha256\")\n        entry[\"result_analysis_code\"] = relative"),
        ("        entry.setdefault(\"artifact_hashes\", {})[\"analysis_code\"] = new_hash\n        if source_changed and not cleanup_only:\n            transition_reports.append(", "        entry.setdefault(\"artifact_hashes\", {})[\"analysis_code\"] = new_hash\n        if old_hash != new_hash or binding_changed:\n            transition_reports.append("),
        ("            state.setdefault(\"project\", {})[\"current_phase\"] = \"result_analysis\"\n        elif conformance_changed and not cleanup_only:\n            transition_reports.append(STATE_TRANSITIONS.apply_transition(", "            state.setdefault(\"project\", {})[\"current_phase\"] = \"result_analysis\"\n        elif conformance_changed:\n            transition_reports.append(STATE_TRANSITIONS.apply_transition("),
        ("        target[\"bundle_sha256\"] = fingerprint[\"bundle_sha256\"]\n        # This is immutable provenance for the last successful real execution.\n        # Only validate_user_execution may replace it after a matching receipt and\n        # numerical acceptance; source delivery must never erase that history.\n", "        target[\"bundle_sha256\"] = fingerprint[\"bundle_sha256\"]\n        if str(target.get(\"validated_bundle_sha256\", \"\")).lower() != fingerprint[\"bundle_sha256\"]:\n            target.pop(\"validated_bundle_sha256\", None)\n"),
        ("            raise ValueError(\"; \".join(final_input_issues))\n    if conformance_binding and cleanup_only:\n        # Retain the delivery/acceptance pair for the original accepted run.\n        # The new bundle is not authorized for execution until a strict delivery\n        # and a matching user-run receipt are completed in solve_validate.\n        pass\n    elif conformance_binding:\n        target = entry[\"solver_execution\"][stage]", "            raise ValueError(\"; \".join(final_input_issues))\n    if conformance_binding:\n        target = entry[\"solver_execution\"][stage]"),
    ),
}

def inverse_user_checker_changes(relative: str, text: str) -> str:
    """Accept exactly one occurrence of each approved replacement, without masking drift."""
    for current, baseline in P6_SOURCE_PROVENANCE_REWRITES.get(relative, ()):
        if text.count(current) != 1:
            raise ValueError(f"{relative}: P6 source-provenance delta is missing or duplicated")
        text = text.replace(current, baseline, 1)
    # The P6 source is pinned to the entire pre-P6 main blob in PROTECTED.
    # Reversing older historical checker deltas again would undo valid main changes.
    if relative == "scripts/validate_code_delivery.py":
        return text
    for index, (current, baseline) in enumerate(USER_CHECKER_AUTHORITY_REWRITES.get(relative, ())):
        matches = text.count(current)
        if matches != 1:
            raise ValueError(
                f"{relative}: authorized checker delta #{index + 1} is missing or duplicated "
                f"(matches={matches}; anchor={current[:80]!r})"
            )
        text = text.replace(current, baseline, 1)
    return text


def inverse_defensive_writing_changes(relative: str, text: str) -> str:
    """Project only the exact Batch A prose additions back to the pinned predecessor."""
    for index, (current, baseline) in enumerate(
        DEFENSIVE_WRITING_AUTHORITY_REWRITES.get(relative, ())
    ):
        matches = text.count(current)
        if matches != 1:
            raise ValueError(
                f"{relative}: Batch A authority delta #{index + 1} is missing or duplicated "
                f"(matches={matches}; anchor={current[:80]!r})"
            )
        text = text.replace(current, baseline, 1)
    return text


class MechanismSpecTests(unittest.TestCase):
    def test_template_is_problem_specific_and_machine_readable(self):
        path = ROOT / "templates/figure/mechanism_drawio_spec.yaml"
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["spec_version"], "1.0.0")
        self.assertEqual(payload["backend"], "drawio")
        self.assertEqual(payload["nodes"], [])
        with self.assertRaises(GENERATOR.SpecError):
            GENERATOR.validate_spec(payload)
        self.assertNotIn("输入", path.read_text(encoding="utf-8"))
        self.assertNotIn("输出", path.read_text(encoding="utf-8"))
        self.assertNotIn("遮蔽", path.read_text(encoding="utf-8"))

    def test_all_supported_layout_modes_generate_valid_xml(self):
        for layout_mode in ("explicit", "layered_lr", "layered_tb"):
            with self.subTest(layout_mode=layout_mode):
                xml_bytes = GENERATOR.generate_drawio(base_spec(layout_mode=layout_mode))
                root = ET.fromstring(xml_bytes)
                self.assertEqual(root.tag, "mxfile")
                self.assertEqual(len(root.findall("diagram/mxGraphModel")), 1)

    def test_all_supported_diagram_types_are_expressible(self):
        for diagram_type in sorted(GENERATOR.DIAGRAM_TYPES):
            with self.subTest(diagram_type=diagram_type):
                payload = base_spec()
                payload["diagram_type"] = diagram_type
                self.assertTrue(GENERATOR.generate_drawio(payload).startswith(b"<?xml"))

    def test_node_order_does_not_change_output(self):
        first = base_spec()
        second = copy.deepcopy(first)
        second["nodes"].reverse()
        second["edges"].reverse()
        self.assertEqual(GENERATOR.generate_drawio(first), GENERATOR.generate_drawio(second))

    def test_chinese_and_formula_labels_round_trip(self):
        xml_bytes = GENERATOR.generate_drawio(base_spec())
        root = ET.fromstring(xml_bytes)
        cells = {cell.attrib["id"]: cell for cell in root.iter("mxCell")}
        self.assertEqual(cells["n_boundary"].attrib["value"], "可见边界 g(T)=0")
        self.assertEqual(cells["e_constraint"].attrib["hskFormulaRefs"], "F6")

    def test_invalid_spec_cases_fail_closed(self):
        cases = []
        duplicate = base_spec()
        duplicate["nodes"].append(copy.deepcopy(duplicate["nodes"][0]))
        cases.append(duplicate)
        bad_enum = base_spec()
        bad_enum["diagram_type"] = "generic_pipeline"
        cases.append(bad_enum)
        missing_anchor = base_spec()
        missing_anchor["nodes"][0]["source_anchor"] = ""
        cases.append(missing_anchor)
        bad_endpoint = base_spec()
        bad_endpoint["edges"][0]["target"] = "missing"
        cases.append(bad_endpoint)
        custom_without_label = base_spec()
        custom_without_label["edges"][0]["relation_type"] = "custom"
        custom_without_label["edges"][0]["label"] = ""
        cases.append(custom_without_label)
        negative_size = base_spec()
        negative_size["nodes"][0]["geometry"]["width"] = -1
        cases.append(negative_size)
        for payload in cases:
            with self.subTest(case=len(cases)):
                with self.assertRaises(GENERATOR.SpecError):
                    GENERATOR.validate_spec(payload)

    def test_declared_spec_hash_uses_non_circular_normalization(self):
        payload = base_spec()
        expected = GENERATOR.canonical_spec_sha256(payload)
        payload["artifact"]["spec_sha256"] = expected
        GENERATOR.validate_spec(payload)
        payload["core_conclusion"] = "被篡改的结论"
        with self.assertRaises(GENERATOR.SpecError):
            GENERATOR.validate_spec(payload)


class GeneratorCliTests(unittest.TestCase):
    def test_check_mode_validates_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = root / "figure.yaml"
            output = root / "figure.drawio"
            write_spec(spec_path, base_spec())
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/generate_mechanism_drawio.py"), "--spec", str(spec_path), "--output", str(output), "--check"],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(output.exists())

    def test_generate_cli_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = root / "figure.yaml"
            first = root / "first.drawio"
            second = root / "second.drawio"
            write_spec(spec_path, base_spec())
            for output in (first, second):
                result = subprocess.run(
                    [sys.executable, str(ROOT / "scripts/generate_mechanism_drawio.py"), "--spec", str(spec_path), "--output", str(output)],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            text = first.read_text(encoding="utf-8")
            for forbidden in ("http://", "https://", "data:image", "javascript:"):
                self.assertNotIn(forbidden, text.lower())


class DrawioValidatorTests(unittest.TestCase):
    def validate(self, payload: dict) -> list:
        xml_bytes = GENERATOR.generate_drawio(payload)
        return VALIDATOR.validate_drawio_bytes(xml_bytes, spec=payload)

    def test_clean_generated_diagram_has_no_blocking_findings(self):
        findings = self.validate(base_spec())
        self.assertFalse([item for item in findings if item.severity == "blocking"])
        self.assertTrue(any(item.code == "preview_not_reviewed" for item in findings))

    def test_group_container_is_not_misclassified_as_entity_overlap(self):
        payload = base_spec()
        payload["groups"] = [{
            "id": "g_observation",
            "label": "观测域",
            "source_anchor": "模型论文框架.md#Q1-对象域",
            "geometry": {"x": 50, "y": 75, "width": 590, "height": 180},
        }]
        payload["nodes"][0]["group_id"] = "g_observation"
        payload["nodes"][1]["group_id"] = "g_observation"
        findings = self.validate(payload)
        self.assertFalse(any(item.code == "entity_overlap" for item in findings))

    def test_overlap_is_blocking(self):
        payload = base_spec()
        payload["nodes"][1]["geometry"] = copy.deepcopy(payload["nodes"][0]["geometry"])
        findings = self.validate(payload)
        self.assertTrue(any(item.code == "entity_overlap" and item.severity == "blocking" for item in findings))

    def test_out_of_bounds_is_rejected_by_spec_validation(self):
        payload = base_spec()
        payload["nodes"][2]["geometry"]["x"] = 950
        with self.assertRaises(GENERATOR.SpecError):
            GENERATOR.validate_spec(payload)

    def test_external_resource_is_blocking(self):
        xml_bytes = GENERATOR.generate_drawio(base_spec()).replace(
            b"rounded=1;",
            b"rounded=1;image=https://example.invalid/a.svg;",
            1,
        )
        findings = VALIDATOR.validate_drawio_bytes(xml_bytes, spec=base_spec())
        self.assertTrue(any(item.code == "external_resource" for item in findings))

    def test_missing_spec_cell_is_blocking(self):
        root = ET.fromstring(GENERATOR.generate_drawio(base_spec()))
        target = next(cell for cell in root.iter("mxCell") if cell.attrib.get("id") == "n_state")
        parent = next(parent for parent in root.iter() if target in list(parent))
        parent.remove(target)
        findings = VALIDATOR.validate_drawio_bytes(ET.tostring(root, encoding="utf-8"), spec=base_spec())
        self.assertTrue(any(item.code == "spec_cell_missing" for item in findings))

    def test_explicit_connector_through_unrelated_entity_is_blocking(self):
        payload = base_spec()
        payload["edges"].append({
            "id": "e_direct",
            "source": "n_target",
            "target": "n_state",
            "relation_type": "feedback",
            "direction": "forward",
            "label": "状态反馈",
            "source_anchor": "模型论文框架.md#Q1-反馈",
            "formula_refs": [],
            "waypoints": [{"x": 500, "y": 155}],
        })
        findings = self.validate(payload)
        self.assertTrue(any(item.code == "connector_crosses_entity" for item in findings))

    def test_approved_status_requires_preview_and_hash(self):
        payload = base_spec()
        payload["artifact"]["validation_status"] = "passed"
        payload["artifact"]["visual_review_status"] = "approved_for_paper"
        with self.assertRaises(GENERATOR.SpecError):
            GENERATOR.validate_spec(payload)

    def test_json_cli_and_strict_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = root / "figure.yaml"
            drawio_path = root / "figure.drawio"
            payload = base_spec()
            write_spec(spec_path, payload)
            drawio_path.write_bytes(GENERATOR.generate_drawio(payload))
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/validate_drawio_figure.py"), str(drawio_path), "--spec", str(spec_path), "--json", "--strict"],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 2)
            report = json.loads(result.stdout)
            self.assertEqual(report["claim"], "structure_and_geometry_only")
            self.assertGreaterEqual(report["counts"]["review_required"], 1)

    def test_current_preview_and_manual_approval_can_close_the_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            source_dir = project / "figures/source"
            preview_dir = project / "figures/preview"
            source_dir.mkdir(parents=True)
            preview_dir.mkdir(parents=True)
            payload = base_spec()
            xml_bytes = GENERATOR.generate_drawio(payload)
            preview_bytes = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>'
            (preview_dir / "q1_occlusion.svg").write_bytes(preview_bytes)
            payload["artifact"].update({
                "preview": "figures/preview/q1_occlusion.svg",
                "spec_sha256": GENERATOR.canonical_spec_sha256(payload),
                "drawio_sha256": hashlib.sha256(xml_bytes).hexdigest(),
                "preview_sha256": hashlib.sha256(preview_bytes).hexdigest(),
                "validation_status": "passed",
                "visual_review_status": "approved_for_paper",
            })
            spec_path = source_dir / "q1_occlusion.mechanism.yaml"
            write_spec(spec_path, payload)
            self.assertEqual(GENERATOR.generate_drawio(payload), xml_bytes)
            findings = VALIDATOR.validate_drawio_bytes(xml_bytes, spec=payload, spec_path=spec_path)
            self.assertEqual(findings, [])

    def test_fake_preview_surface_cannot_close_the_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            source_dir = project / "figures/source"
            preview_dir = project / "figures/preview"
            source_dir.mkdir(parents=True)
            preview_dir.mkdir(parents=True)
            payload = base_spec()
            xml_bytes = GENERATOR.generate_drawio(payload)
            preview_bytes = b"not-a-png"
            (preview_dir / "q1_occlusion.png").write_bytes(preview_bytes)
            payload["artifact"].update({
                "preview": "figures/preview/q1_occlusion.png",
                "spec_sha256": GENERATOR.canonical_spec_sha256(payload),
                "drawio_sha256": hashlib.sha256(xml_bytes).hexdigest(),
                "preview_sha256": hashlib.sha256(preview_bytes).hexdigest(),
                "validation_status": "passed",
                "visual_review_status": "approved_for_paper",
            })
            spec_path = source_dir / "q1_occlusion.mechanism.yaml"
            write_spec(spec_path, payload)
            findings = VALIDATOR.validate_drawio_bytes(xml_bytes, spec=payload, spec_path=spec_path)
            self.assertTrue(any(item.code == "preview_format_invalid" for item in findings))


class ContractAndDriftTests(unittest.TestCase):
    # v8.7.0 established the body baseline below. v8.7.2 intentionally reopens only
    # two Paper Writing Protocol seam sentences plus its release header, and one
    # competition-profile lineage comment. Normalize exactly those approved deltas so
    # the older protected hashes continue to guard every unrelated semantic byte.
    # v9.1.0 deliberately rebaselines only q1_plot/chart_selection/figure patterns because
    # those three Figure implementation surfaces are explicit scope of publication rendering.
    # P3b intentionally rebaselines only AI Cleanup and Review Delivery because those two
    # consumer surfaces are the explicit scope of the approved writing-role consolidation.
    # P5a intentionally rebaselines only the two 03 execution docs and code-delivery validator
    # because RUN_CONFIG migration explicitly changes those three protected execution surfaces.
    # P5b intentionally rebaselines only code-delivery validation because the versioned
    # RUN_RECEIPT protocol marker is a planned execution-interface extension.
    # P7 intentionally rebaselines project-state result-analysis semantics, the 03B module,
    # and q1_plot because conditional Analysis Necessity Gate behavior explicitly changes them.
    # P8c intentionally rebaselines only code-delivery validation because the measured
    # duplicate RUN_CONFIG parser is consolidated without changing its field policy or errors.
    # v9.3.1 PR B intentionally rebaselines only project-state classification compatibility
    # metadata: the deprecated legacy_task_packs alias no longer duplicates Router's pack budget.
    # v9.3.1 PR C intentionally rebaselines only Model Approval semantic-surface wording:
    # field/state identities remain unchanged while v9.3 minimal-sufficient/comparator meanings are made explicit.
    # F1 re-pins only approved figure-selection prose; numerical MATLAB lines are unchanged.
    # F2 re-pins the approved configurable entry style and palette guidance only.
    # F3 re-pins only the two approved figure technique reference documents.
    # v9.7.0 re-pins the approved backend execution interfaces and their consumer
    # wording only. Numerical rules, drawing code, approval roles, writing semantics
    # and every unrelated protected authority retain their previous guards.
    # The v10 candidate re-pins only the project-root backend schema and the
    # corresponding code-delivery consumer; the other authority guards remain fixed.
    # v10.1 AUD-01/03 intentionally re-pin input qualification and strict revision
    # checks; behavioral regressions live in test_audit_closure_regressions.
    # v10.26.0 B intentionally re-pins only Writing Reasoning, Paper Writing
    # Protocol and AI Cleanup after inspecting the exact authorized diff.
    # The original historical inverse projections and every other PROTECTED
    # digest remain unchanged; future unrelated edits still fail this guard.
    # v10.18.3 approved CUMCM writing clarification and documented follow-up
    # pin only the two touched writing Authority projections below. The exact
    # projected Git blob SHA-1 values were recomputed from final GitHub source
    # using the unchanged protocol and comparison inverse rewrites and matched
    # the failing CI's actual digests. All unrelated protected authorities,
    # historical baseline projection rules, and negative checks remain intact.
    # v10.18.1 approved audit closure re-pins only the recomputed numeric relation
    # (G2), ambiguous-semantic write rejection (G3), installed font fallback (G6),
    # and current conditional-file/input protocol wording (G7). Every other
    # protected hash and the exact historical inverse projections remain fixed.
    PROTECTED = {
        "core/model_approval_contract.yaml": "7cf530468a9a740a4123d64dec85b257d48e0892",
        "core/numerical_verification_contract.yaml": "37e111469a3d97a0f0acb89cbf78bb219dd47645",
        # P0-A intentionally aligns the title handoff with the existing output Authority;
        # test_schemas covers the new declaration and unchanged caption ownership.
        "core/workbook_schema.yaml": "e0479f5e74063151a515d11e140b7c4e8b8db077",
        # C2 adds only the opt-in reviewer receipt policy after C1; the
        # predecessor policy shapes remain protected by dedicated regressions.
        "core/project_state.schema.yaml": "9be39d30d5acf7e88d67bf2ccee89031e5135568",
        "core/writing_reasoning_contract.yaml": "2c84fd56b6444301bcdafb931d0fa8cfb8d9cf71",
        "modules/03_solve_validate.md": "cfbe8091f0434b8531ec97cbccde013895e18228",
        "modules/03_result_analysis.md": "d63db5f2acdba56d006cff5de6de2f76df02364a",
        "modules/05_writing/paper_writing_protocol.md": "80337757bab0a3e2a0d26442f4d4b6120001fe87",
        # v10.26.2 re-pins only the separately audited prose-only 05C consumer.
        "modules/05_writing/ai_cleanup.md": "1f6ce51c26a891db1a94a875550bfeba629ad2de",
        # C1 distinguishes optional receipt metadata from the internal review matrix.
        "modules/06_review_delivery.md": "4d2bc78193c14f2ee72983db7d58b1870e9ca59f",
        "config/competition_profiles.yaml": "0cfe08e2edac99f07f2e527643499b8bc73c0479",
        # P4c historical Git blob: 769eb05089111a11624db7da880a1402ecfec853.
        # M3 explicitly adds question-scoped semantic validation while retaining
        # the original unscoped writer guard; exact current blob remains pinned.
        "scripts/validate_semantic_governance.py": "9ba8c2b996c447fa77af9406f5e54ae6d422b544",
        # A5 requires current per-question files and exact official allowlist entries.
        # B2c additionally binds the selected LaTeX entrypoint and blocks
        # DOCX submission until a supported rendered proof exists. C2 adds
        # only an explicit opt-in final-review receipt recheck at this gate.
        # v10.18.2 R2/R3 re-pins this planned consumer only: current-analysis
        # selection and consumed-source read-set closure, including Windows
        # short-path identities. All unrelated protected hashes stay fixed.
        "scripts/validate_submission_package.py": "bac6b567cf2cd7272a21dce02bbe7c9c9eb9fe2f",
        # P0-B replaces silent filtering/fixed ordering with explicit evidence-preserving reads.
        # v10.0.1 removes unsupported ColorBar.FontUnits in the standalone fallback;
        # MATLAB syntax is parsed separately; source checks do not claim runtime execution.
        "templates/matlab/q1_plot.m": "3958dd613ec23d7f43b493757f3d3cc287b8b1ec",
        "templates/matlab/draw_mechanism_structure.m": "65ba4a3b3462a565f86880c49af0959edd21f9a4",
        # v9.7.1 A02 changes only Evidence Capture's producer from Python to the selected solver.
        "templates/figure/chart_selection.md": "8b87b79d55e23f1b581c1ceca9e4d609fd11ba26",
        "templates/figure/figure_enhancement_patterns.md": "fa9db83323c4dcbe430e8afdca82df806e3db9de",
        # P6 replays only its approved source changes onto the exact pre-P6 main blob.
        # This pins every earlier approved checker change, without repeating its old inverse maps.
        "scripts/validate_code_delivery.py": "6dafe830b6d1ab20b680200d7648b61c14454c8c",
    }

    def prior_handoff_text(self, relative):
        # P3 moves the same business sections to canonical leaves. Reconstruct
        # those live bytes before applying the unchanged historical projections;
        # neither the old protected blob hash nor its inverse rules are waived.
        text = (historical_review_text(ROOT) if relative == "modules/06_review_delivery.md"
                else p4a_authority_text(relative))
        text = prior_writing_slimming_text(relative, text)
        text = prior_primary_quality_binding(relative, prior_execution_scale_binding(relative, text))
        if relative == "core/workbook_schema.yaml":
            # Renderer-neutral handoff wording does not change the workbook
            # format. Reverse only these exact leaves before the old projections.
            for current, baseline in (
                ("和Python/MATLAB绘图交接", "和MATLAB交接"),
                ("当前选定Python/MATLAB绘图代码生成前", "MATLAB绘图代码生成前"),
            ):
                self.assertEqual(text.count(current), 1, (relative, current))
                text = text.replace(current, baseline, 1)
        for current, baseline in PDF_REVIEW_OWNER_REWRITES.get(relative, ()):
            self.assertEqual(text.count(current), 1, (relative, current))
            text = text.replace(current, baseline, 1)
        if relative == "scripts/validate_code_delivery.py":
            text = prior_preprocessing_delivery(text)
        text = inverse_user_checker_changes(relative, text)
        for current, baseline in HANDOFF_AUTHORITY_REWRITES.get(relative, ()):
            self.assertEqual(text.count(current), 1, (relative, current))
            text = text.replace(current, baseline, 1)
        text = inverse_defensive_writing_changes(relative, text)
        return text

    def test_protected_authorities_have_not_drifted(self):
        # W1 proof-body preservation, judge-readable heading/terminology, Part D table/figure
        # readability, Part C derivation closure, Part E narrative, and approved Part F heading-depth changes
        # intentionally re-pin only the touched writing authorities; unrelated drift still fails closed.
        protocol = "modules/05_writing/paper_writing_protocol.md"
        competition_profiles = "config/competition_profiles.yaml"
        protocol_rewrites = (
            # Phase C reopens Protocol §5A only. Reverse the two authorized
            # changes before the unchanged historical SHA-1 projection.
            ("只对真实跨文件依赖、尚未闭合的语义冲突或必须跨阶段恢复的数学/证据承接登记 Chapter Handoff Map。普通 `narrative`、`frontmatter_consistency` 与 `structural_terminal` 邻接依据当前相邻正文和既有锚点直接审阅，不为每条物理边界持久填表。需要登记时，项目记录只保留推动衔接所需的事实：", "每个 actual seam 的项目记录只保留推动相邻文件衔接所需的事实："),
            ("写当前文件前先读取当前项目事实与必要的 fragment/result anchors；仅在相关 handoff 记录已存在时消费，普通叙事 seam 没有记录不构成写作阻断。依赖、对象、符号或证据不清以及记录冲突时，定点回读 source 文件尾部与 target 文件开头，不预载整篇论文。写完后只更新确需追踪的 incoming/outgoing seam 与已有依赖锚点；**全部 actual active seam 仍在 draft/final review 接受 assembled seam sweep**。真实依赖缺口、引用 stale 或未闭合争议不得借“可选记录”逃避修复。", "写当前文件前，优先读取 relevant assembled predecessor handoff、当前项目事实及必要的 fragment/result anchors；信息不足或冲突时，定点回读 source 文件尾部与 target 文件开头，不预载整篇论文。写完后更新 incoming seam 状态和面向 assembled successor 的 outgoing handoff；若上游真实模型、结果或依赖变化，只标记实际受影响的 handoff/fragment stale。"),
            # v10.23.3 explicitly adds these two Manifest pointers. Remove only
            # the exact approved additions before checking the historical blob.
            (
                "CUMCM HSK 的逐问二级标题遵循 `templates/latex/cumcm/hsk/template_manifest.yaml#paper_skeleton`，按当前 Problem Contract 的实际小问数量和顺序命名；固定标题不改变下述连续数学分析的内容要求。\n\n",
                "",
            ),
            (
                "CUMCM 附录的总标题与逐项二级标题以 `templates/latex/cumcm/hsk/template_manifest.yaml#paper_skeleton` 为准；未激活附录时不补空标题，启用后仅为真实支持材料设置子节。\n\n",
                "",
            ),
            (
                "# Module 05A：Paper Writing Protocol",
                "# Module 05A：Paper Writing Protocol（v8.7.0）",
            ),
            (
                "默认作者执行顺序为：问题重述 → 问题分析 → 假设/符号/条件式数据与共享基础 → 按问题顺序逐问完成模型建立、模型求解、结果与验证 → 模型评价、按适用规则处理条件式披露、引用、结论与附录 → 最后根据 current 结果写摘要、标题和关键词 → draft semantic review → AI Cleanup → LaTeX 装配/审计/编译 → final review。成品中的摘要仍位于正文前部，但写作时不得早于 current 逐问答案和验证边界稳定。",
                "默认作者执行顺序为：问题重述 → 问题分析 → 假设/符号/条件式数据与共享基础 → 按问题顺序逐问完成模型建立、模型求解、结果与验证 → 模型评价、引用、结论与附录 → 最后根据 current 结果写摘要、标题和关键词 → draft semantic review → AI Cleanup → LaTeX 装配/审计/编译 → final review。成品中的摘要仍位于正文前部，但写作时不得早于 current 逐问答案和验证边界稳定。",
            ),
            (
                "- `structural_terminal`：用于最终结构尾部边界；AI disclosure 不启用时检查模型评价→参考文献→附录，启用时检查模型评价→AI工具使用声明→参考文献→附录。这里只检查结构、披露/引用和附录边界，不制造语义桥。",
                "- `structural_terminal`：用于模型评价→参考文献、参考文献→附录，只检查结构、引用和附录边界，不制造语义桥。",
            ),
        )
        competition_lineage_comment = (
            "# 该 version 是 competition-profile 配置格式沿革，不是当前 Skill release；当前 Skill 版本由 core/bootstrap.yaml 等 release carriers 声明。\n"
        )
        for relative, expected in self.PROTECTED.items():
            with self.subTest(relative=relative):
                path = ROOT / relative
                if relative == protocol:
                    text = self.prior_handoff_text(relative)
                    for current, baseline in protocol_rewrites:
                        self.assertEqual(text.count(current), 1, current)
                        text = text.replace(current, baseline, 1)
                    data = text.encode("utf-8")
                    actual = hashlib.sha1(
                        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
                    ).hexdigest()
                elif relative == competition_profiles:
                    text = path.read_text(encoding="utf-8")
                    current_2026_rules = (
                        "    edition_rules:\n"
                        "      edition: \"2026\"\n"
                        "      verification_status: verified\n"
                        "      verified_at: \"2026-11-03\"\n"
                        "      source: https://dxs.moe.gov.cn/zx/a/hd_sxjm_gsyw/260702/2046411.shtml\n"
                        "      ai_rule_source: https://dxs.moe.gov.cn/zx/a/hd_sxjm_gsyw/260807/2051819.shtml\n"
                        "      page_limit: 30\n"
                        "      anonymity: true\n"
                        "      # A2 will define official external exports. Keep the legacy internal-ZIP\n"
                        "      # allowlist empty in A1 so hsk_pack_submission.py refuses unsafe PASS.\n"
                        "      submission_files: []\n"
                        "      ai_disclosure: required_used_or_not_used_before_references\n"
                        "      paper:\n"
                        "        electronic_first_page: abstract\n"
                        "        electronic_forbidden_frontmatter: [promise_page, team_number_page, table_of_contents]\n"
                        "        electronic_single_file_formats: [pdf, docx]\n"
                        "        max_paper_mb: 20\n"
                        "        max_support_mb: 20\n"
                        "        appendix_required: true\n"
                        "        appendix_complete_runnable_programs: true\n"
                        "        no_program_statement: 本论文没有用到程序\n"
                        "        no_support_statement: 本论文没有支撑材料\n"
                        "        ai_detail_file_when_used: AI工具使用详情.pdf\n"
                        "        print_promise_and_number_pages: required\n"
                        "        body_max_pages: 30"
                    )
                    legacy_rules = (
                        "    edition_rules:\n"
                        "      edition: current\n"
                        "      verification_status: unverified\n"
                        "      verified_at: null\n"
                        "      source: null\n"
                        "      page_limit: null\n"
                        "      anonymity: null\n"
                        "      submission_files: []\n"
                        "      ai_disclosure: null"
                    )
                    self.assertEqual(text.count(current_2026_rules), 1)
                    text = text.replace(current_2026_rules, legacy_rules, 1)
                    self.assertEqual(text.count(competition_lineage_comment), 1)
                    data = text.replace(competition_lineage_comment, "", 1).encode("utf-8")
                    actual = hashlib.sha1(
                        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
                    ).hexdigest()
                elif relative in P6_SOURCE_PROVENANCE_REWRITES:
                    # P6 is pinned to the exact pre-P6 main blob. Do not replay
                    # earlier comparison/checker inverse maps a second time.
                    data = self.prior_handoff_text(relative).encode("utf-8")
                    actual = hashlib.sha1(
                        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
                    ).hexdigest()
                elif relative in COMPARISON_AUTHORITY_REWRITES:
                    text = self.prior_handoff_text(relative)
                    if relative == "core/model_approval_contract.yaml":
                        self.assertEqual(text.count("version: 1.3.0\n"), 1)
                        text = text.replace("version: 1.3.0\n", "version: 1.2.0\n", 1)
                        for item in LITERATURE_APPROVAL_V10290_LIST_ITEMS:
                            self.assertEqual(text.count(item), 1, (relative, item))
                            text = text.replace(item, "", 1)
                        self.assertEqual(text.count(LITERATURE_APPROVAL_V10290_RULES), 1)
                        text = text.replace(LITERATURE_APPROVAL_V10290_RULES, "", 1)
                    for current, baseline in COMPARISON_AUTHORITY_REWRITES[relative]:
                        self.assertEqual(text.count(current), 1, (relative, current))
                        text = text.replace(current, baseline, 1)
                    data = text.encode("utf-8")
                    actual = hashlib.sha1(
                        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
                    ).hexdigest()
                elif (relative in HANDOFF_AUTHORITY_REWRITES
                      or relative in USER_CHECKER_AUTHORITY_REWRITES
                      or relative in P6_SOURCE_PROVENANCE_REWRITES
                      or relative in DEFENSIVE_WRITING_AUTHORITY_REWRITES):
                    data = self.prior_handoff_text(relative).encode("utf-8")
                    actual = hashlib.sha1(
                        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
                    ).hexdigest()
                elif relative == "core/project_state.schema.yaml":
                    from claim_schema_reference import previous_d2_schema

                    text = path.read_text(encoding="utf-8")
                    # Revert only the optional Figure schema extension, byte-for-byte.
                    # Keep every original pinned predecessor hash and assertion.
                    edition_addition = (
                        "      competition_edition:\n"
                        "        type: string\n"
                        "        pattern: \"^[0-9]{4}$\"\n"
                        "        description: Optional four-digit contest year; historical projects may omit it.\n"
                    )
                    self.assertEqual(text.count(edition_addition), 1)
                    text = text.replace(edition_addition, "", 1)
                    if "  plotting:\n" in text:
                        additions = (
                            "  plotting:\n"
                            "    description: Project-wide Figure rendering backend; absent in older MATLAB projects.\n"
                            "    type: object\n"
                            "    additionalProperties: false\n"
                            "    required: [backend, selection_reason]\n"
                            "    properties:\n"
                            "      backend: {type: string, enum: [python, matlab]}\n"
                            "      selection_reason: {type: string, minLength: 1, pattern: '\\S'}\n",
                            "      plot_script: {type: string, pattern: '^[0-9a-fA-F]{64}$'}\n",
                            "        plot_script: {type: string, description: New Python Figure entry; MATLAB retains matlab_script}\n",
                        )
                        for addition in additions:
                            self.assertEqual(text.count(addition), 1, addition)
                            text = text.replace(addition, "", 1)
                        extended = "robustness_workbook, matlab_script, plot_script, figure_bundle, framework]"
                        self.assertEqual(text.count(extended), 1)
                        text = text.replace(
                            extended,
                            "robustness_workbook, matlab_script, figure_bundle, framework]",
                            1,
                        )
                    schema = yaml.safe_load(text)
                    if schema["version"] == "8.16.0":
                        from claim_schema_reference import previous_comparison_schema
                        schema = previous_comparison_schema(schema)
                        begin = "# analysis comparison definitions BEGIN\n"
                        end = "# analysis comparison definitions END\n"
                        self.assertEqual(text.count(begin), 1)
                        self.assertEqual(text.count(end), 1)
                        start = text.rfind("\n", 0, text.index(begin)) + 1
                        stop = text.index(end, start) + len(end)
                        text = text[:start] + text[stop:]
                        reference = "        analysis_comparison: {$ref: '#/$defs/analysis_comparison'}\n"
                        self.assertEqual(text.count(reference), 1)
                        self.assertEqual(text.count("version: 8.16.0\n"), 1)
                        text = text.replace(reference, "", 1).replace("version: 8.16.0\n", "version: 8.15.0\n", 1)
                    if schema["version"] == "8.15.0":
                        # Only the pinned D2 additions may project back to the frozen C2 bytes.
                        previous_d2_schema(schema)
                        start = text.index("  case_references:\n")
                        end = text.index("  review_receipt_policy:\n", start)
                        text = text[:start] + text[end:]
                        reference = "        case_references: {$ref: '#/$defs/case_references'}\n"
                        self.assertEqual(text.count(reference), 1)
                        self.assertEqual(text.count("version: 8.15.0\n"), 1)
                        text = text.replace(reference, "", 1).replace("version: 8.15.0\n", "version: 8.14.0\n", 1)
                    data = text.encode("utf-8")
                    actual = hashlib.sha1(
                        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
                    ).hexdigest()
                elif relative in PRIMARY_QUALITY_BINDING_BLOCKS:
                    predecessor = prior_execution_scale_binding(relative, p4a_authority_text(relative))
                    text = prior_primary_quality_binding(relative, predecessor)
                    data = text.encode("utf-8")
                    actual = hashlib.sha1(
                        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
                    ).hexdigest()
                else:
                    actual = git_blob_sha(path)
                self.assertEqual(actual, expected)

    def test_writing_slimming_projection_preserves_existing_authority_guards(self):
        for relative, replacements in WRITING_SLIMMING_REWRITES.items():
            source = (ROOT / relative).read_text(encoding="utf-8")
            predecessor = prior_writing_slimming_text(relative, source)
            extra = "\nunauthorized unrelated authority change\n"
            self.assertEqual(
                prior_writing_slimming_text(relative, source + extra), predecessor + extra,
            )
            for current, _ in replacements:
                for changed in (source.replace(current, "", 1), source + current):
                    with self.subTest(relative=relative, current=current[:80]):
                        with self.assertRaisesRegex(ValueError, "missing or duplicated"):
                            prior_writing_slimming_text(relative, changed)

    def test_w2_d02_authority_inverse_retains_historical_hash_guards(self):
        for relative, digests in W2_D02_SOURCE_IDENTITIES.items():
            with self.subTest(relative=relative):
                actual = (ROOT / relative).read_text(encoding="utf-8")
                self.assertEqual(hashlib.sha256(actual.encode("utf-8")).hexdigest(), digests[0])
                predecessor = prior_w2_numeric_display_text(relative, actual)
                self.assertEqual(hashlib.sha256(predecessor.encode("utf-8")).hexdigest(), digests[1])
                extra = "\n# unauthorized unrelated source change\n"
                self.assertEqual(
                    prior_w2_numeric_display_text(relative, actual + extra),
                    predecessor + extra,
                )
                for current, _ in W2_D02_APPROVED_REWRITES[relative]:
                    for modified in (actual.replace(current, "", 1), actual + current):
                        with self.subTest(hunk=current[:52]):
                            with self.assertRaisesRegex(ValueError, "D02 hunk missing or duplicated"):
                                prior_w2_numeric_display_text(relative, modified)

    def test_defensive_writing_inverse_projection_rejects_missing_or_duplicate_blocks(self):
        for relative, replacements in DEFENSIVE_WRITING_AUTHORITY_REWRITES.items():
            source = p4a_authority_text(relative)
            for current, _ in replacements:
                for changed in (
                    source.replace(current, "", 1),
                    source + current,
                ):
                    with self.subTest(relative=relative, current=current[:80]):
                        with self.assertRaises(ValueError):
                            inverse_defensive_writing_changes(relative, changed)

    def test_defensive_writing_inverse_projection_preserves_unrelated_changes(self):
        for relative in DEFENSIVE_WRITING_AUTHORITY_REWRITES:
            source = p4a_authority_text(relative)
            projected = inverse_defensive_writing_changes(relative, source)
            unrelated = "\nunauthorized unrelated authority change\n"
            self.assertEqual(
                inverse_defensive_writing_changes(relative, source + unrelated),
                projected + unrelated,
            )

    def test_p5_compatibility_projection_accepts_only_the_reviewed_lines(self):
        for relative, blocks in P5_COMPATIBILITY_BLOCKS.items():
            source = (ROOT / relative).read_text(encoding="utf-8")
            expected = source
            for first, _, _, previous in blocks:
                line = first + "\n"
                expected = expected.replace(line, previous, 1)
                with self.subTest(relative=relative, line=first):
                    for altered in (source + line, source.replace(line, first + " changed\n", 1)):
                        with self.assertRaisesRegex(ValueError, "missing or duplicated"):
                            _prior_reviewed_blocks(relative, altered, P5_COMPATIBILITY_BLOCKS, "P5 compatibility")
            extra = "# unrelated change must remain visible\n"
            projected = _prior_reviewed_blocks(relative, source + extra, P5_COMPATIBILITY_BLOCKS, "P5 compatibility")
            self.assertEqual(projected, expected + extra)

    def test_ordinary_analysis_coverage_inverse_restores_exact_scale_source(self):
        relative = "core/workbook_schema.yaml"
        text = p4a_authority_text(relative)
        prior = prior_ordinary_analysis_coverage(relative, text)
        self.assertEqual(hashlib.sha256(prior.encode("utf-8")).hexdigest(),
                         "568d2fa949b04748acf512a9883d7a5bd6c958221675d3548cee2fc88cded095")
        extra = "\n# unauthorized separate change\n"
        self.assertEqual(prior_ordinary_analysis_coverage(relative, text + extra), prior + extra)

        first, count, digest, _ = ORDINARY_ANALYSIS_COVERAGE_BLOCKS[relative][0]
        lines = text.splitlines(keepends=True)
        block, = (chunk for offset, line in enumerate(lines) if line == first + "\n"
                  for chunk in ["".join(lines[offset:offset + count])]
                  if hashlib.sha256(chunk.encode("utf-8")).hexdigest() == digest)
        for changed in (text.replace(block, extra, 1), text + block):
            with self.assertRaisesRegex(ValueError, "missing or duplicated"):
                prior_ordinary_analysis_coverage(relative, changed)

    def test_execution_scale_binding_inverse_is_exact(self):
        source_hashes = {
            "core/workbook_schema.yaml": "1d535ce535a4166907808144db7b54a4573ae73a694c1eba5c5608a58f11ce75",
            "scripts/validate_code_delivery.py": "50381540e0900f499713b4aedd6477917128beaeffde410bbfdaae2938b756ae",
        }
        for relative, expected in source_hashes.items():
            with self.subTest(relative=relative):
                current = p4a_authority_text(relative)
                prior = prior_execution_scale_binding(relative, current)
                self.assertEqual(hashlib.sha256(prior.encode("utf-8")).hexdigest(), expected)
                extra = "\n# unauthorized separate change\n"
                self.assertEqual(prior_execution_scale_binding(relative, current + extra), prior + extra)

                first, count, digest, _ = EXECUTION_SCALE_BINDING_BLOCKS[relative][0]
                lines = current.splitlines(keepends=True)
                block, = (chunk for offset, line in enumerate(lines) if line == first + "\n"
                          for chunk in ["".join(lines[offset:offset + count])]
                          if hashlib.sha256(chunk.encode("utf-8")).hexdigest() == digest)
                for changed in (current.replace(block, extra, 1), current + block):
                    with self.assertRaisesRegex(ValueError, "missing or duplicated"):
                        prior_execution_scale_binding(relative, changed)

    def test_primary_quality_binding_inverse_is_exact(self):
        source_hashes = {
            "core/model_approval_contract.yaml": "40aa80daf77bfc0ba1092fa8767a1b97df331d44e76b1e23875ccbf7410653ec",
            "core/numerical_verification_contract.yaml": "1172bc1abc7c905203fb6d5af254f85dd75467a423b4189082f5e3e259c4ac4a",
            "core/workbook_schema.yaml": "d2433f32204cbba294cc8ce0565c850b8c7bf823857cd19e4e6823d2e60526eb",
            "scripts/validate_code_delivery.py": "4a6f846c22480cd2c4553681d9243dfc211599e39d67b151a3fbc46f3a855d91",
        }
        for relative, expected in source_hashes.items():
            with self.subTest(relative=relative):
                current = p4a_authority_text(relative)
                current = prior_execution_scale_binding(relative, current)
                prior = prior_primary_quality_binding(relative, current)
                self.assertEqual(hashlib.sha256(prior.encode("utf-8")).hexdigest(), expected)
                extra = "\n# unauthorized separate change\n"
                self.assertEqual(prior_primary_quality_binding(relative, current + extra), prior + extra)

                first, count, digest, _ = PRIMARY_QUALITY_BINDING_BLOCKS[relative][0]
                lines = current.splitlines(keepends=True)
                block, = (chunk for offset, line in enumerate(lines) if line == first + "\n"
                          for chunk in ["".join(lines[offset:offset + count])]
                          if hashlib.sha256(chunk.encode("utf-8")).hexdigest() == digest)
                for changed in (current.replace(block, extra, 1), current + block):
                    with self.assertRaisesRegex(ValueError, "missing or duplicated"):
                        prior_primary_quality_binding(relative, changed)

    def test_preprocessing_redelivery_inverse_is_exact(self):
        relative = "scripts/validate_code_delivery.py"
        current = p4a_authority_text(relative)
        source = prior_primary_quality_binding(relative, prior_execution_scale_binding(relative, current))
        predecessor = prior_preprocessing_delivery(source)
        data = predecessor.encode("utf-8")
        self.assertEqual(hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest(),
                         "6a721c2620b4f1fc8023e641ae1a5b7b666f9fcc")
        extra = "\n# unrelated change\n"
        self.assertEqual(prior_preprocessing_delivery(source + extra), predecessor + extra)
        first = PREPROCESSING_REDELIVERY_BLOCKS[0][0] + "\n"
        for changed in (source.replace(first, extra, 1), source + first):
            with self.assertRaisesRegex(ValueError, "missing or duplicated"):
                prior_preprocessing_delivery(changed)

    def test_checker_inverse_projection_rejects_missing_or_duplicate_authorized_blocks(self):
        # P6 and older documentation deltas both reject a missing or duplicate
        # authorized segment. Source bytes outside those segments are hash-pinned.
        for relative, replacements in (
            *P6_SOURCE_PROVENANCE_REWRITES.items(),
            *USER_CHECKER_AUTHORITY_REWRITES.items(),
        ):
            live = p4a_authority_text(relative)
            text = prior_primary_quality_binding(relative, prior_execution_scale_binding(relative, live))
            for current, _ in replacements:
                for changed in (text.replace(current, "unauthorized replacement\n", 1), text + current):
                    with self.subTest(relative=relative, current=current[:80]):
                        with self.assertRaises(ValueError):
                            inverse_user_checker_changes(relative, changed)

    def test_checker_inverse_projection_does_not_erase_unrelated_changes(self):
        for relative in set(USER_CHECKER_AUTHORITY_REWRITES) | set(P6_SOURCE_PROVENANCE_REWRITES):
            current = p4a_authority_text(relative)
            text = prior_primary_quality_binding(relative, prior_execution_scale_binding(relative, current))
            changed = text + "\nunauthorized unrelated change\n"
            projected = inverse_user_checker_changes(relative, text)
            self.assertEqual(
                inverse_user_checker_changes(relative, changed),
                projected + "\nunauthorized unrelated change\n",
            )
            self.assertEqual(p4a_authority_text(relative), current)

    def test_matlab_ownership_and_conditional_per_question_layout_are_explicit(self):
        output = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        self.assertIn("draw.io", output["ownership"]["other_figure_tools"])
        per_question = output["per_question"]
        base = per_question["base_default_files"]
        analysis = per_question["analysis_required_additional_files"]
        self.assertEqual(len(base), 3)
        self.assertEqual(len(analysis), 2)
        self.assertTrue(set(base).isdisjoint(analysis))
        self.assertEqual(len(set(base + analysis)), 5)
        self.assertIn("q{阿拉伯序号}_plot.m", base)
        self.assertNotIn("问题{中文序号}结果深化分析.py", base)
        self.assertIn("问题{中文序号}结果深化分析.py", analysis)
        self.assertNotIn("matplotlib", (ROOT / "templates/code").read_text(encoding="utf-8") if (ROOT / "templates/code").is_file() else "")

    def test_figure_authority_and_adapter_boundaries_are_explicit(self):
        module = (ROOT / "modules/04_figure_evidence.md").read_text(encoding="utf-8")
        pack = (ROOT / "packs/artifact/figure.md").read_text(encoding="utf-8")
        for token in ("Mechanism Diagram Backend Selection Gate", "structure_checked", "approved_for_paper", "不判断箭头方向是否符合真实机制"):
            self.assertIn(token, module)
        self.assertIn("templates/figure/mechanism_drawio_spec.yaml", pack)
        self.assertIn("modules/04_figure_evidence.md", pack)

    def test_route_loads_drawio_resources_only_for_precise_trigger(self):
        router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        general = router["routing"]["figures"]
        precise = router["routing"]["editable_mechanism_diagram"]
        self.assertNotIn("templates/figure/mechanism_drawio_patterns.md", general["load"])
        self.assertIn("可编辑机理图", precise["triggers"])
        self.assertIn("templates/figure/mechanism_drawio_patterns.md", precise["load"])

    def test_natural_language_routing_keeps_drawio_resources_conditional(self):
        def resolve(request: str) -> dict:
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/resolve_workflow.py"), "--request", request],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return yaml.safe_load(result.stdout)

        editable = resolve("请用 draw.io 生成一张可编辑机理图")
        ordinary = resolve("请根据结果工作簿生成结果图")
        resource = "templates/figure/mechanism_drawio_patterns.md"
        self.assertIn(resource, editable["load_order"])
        self.assertNotIn(resource, ordinary["load_order"])

    def test_current_release_carriers_and_skill_entrypoints_match(self):
        bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))
        plugin = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        root_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        packaged = (ROOT / "skills/mathmodel-skill/SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(str(plugin["version"]), str(bootstrap["skill_version"]))
        self.assertEqual(root_skill, packaged)
        self.assertIn("Editable Mechanism Diagram", root_skill)


if __name__ == "__main__":
    unittest.main()
