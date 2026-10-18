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
    "scripts/validate_code_delivery.py": (
        (
            (
                "import hashlib\n"
                "import shutil\n"
                "import sys\n"
            ),
            (
                "import hashlib\n"
                "import sys\n"
            ),
        ),
        (
            (
                "\n"
                "def _native_delivery_analysis(\n"
                "    script: Path, matlab_command: str | None, *, require_native: bool,\n"
                ") -> dict[str, Any]:\n"
                "    \"\"\"Keep optional native coverage separate from required delivery findings.\"\"\"\n"
                "    if not require_native and not matlab_command:\n"
                "        return {\n"
                "            \"status\": \"unverified\", \"issues\": [],\n"
                "            \"warnings\": [\"未选定可用的MATLAB Code Analyzer；原生分析未核验\"],\n"
                "        }\n"
                "    native = MATLAB_CHECKS.native_code_analysis(script, matlab_command)\n"
                "    if native[\"status\"] == \"unverified\" and not require_native:\n"
                "        return {\n"
                "            **native, \"issues\": [],\n"
                "            \"warnings\": [*native.get(\"warnings\", []), *native[\"issues\"]],\n"
                "        }\n"
                "    return native\n"
                "\n"
                "\n"
                "def validate_script(\n"
            ),
            (
                "\n"
                "def validate_script(\n"
            ),
        ),
        (
            (
                ") -> tuple[list[str], dict[str, Any]]:\n"
                "    \"\"\"Check source statically; CLI discovers MATLAB, internal callers opt in explicitly.\"\"\"\n"
                "    issues: list[str] = []\n"
            ),
            (
                ") -> tuple[list[str], dict[str, Any]]:\n"
                "    issues: list[str] = []\n"
            ),
        ),
        (
            (
                "            text, config, contract=load_yaml(QUALITY_CONTRACT), filename=script.name)\n"
                "        native = _native_delivery_analysis(script, matlab_command, require_native=require_native)\n"
                "        if native_report is not None:\n"
                "            native_report.update(native)\n"
                "        quality_errors.extend(native[\"issues\"])\n"
                "        if native.get(\"source_sha256\") and native[\"source_sha256\"] != source_sha256:\n"
                "            quality_errors.append(\"MATLAB原生检查源码与本次配置/工程检查源码不一致\")\n"
                "        for item in native.get(\"complexity_metrics\", []):\n"
                "            if item[\"value\"] > load_yaml(QUALITY_CONTRACT)[\"complexity\"][\"hard_max\"]:\n"
                "                quality_errors.append(f\"MATLAB原生复杂度L{item['line']}={item['value']}超过硬上限\")\n"
                "    else:\n"
            ),
            (
                "            text, config, contract=load_yaml(QUALITY_CONTRACT), filename=script.name)\n"
                "        if require_native or matlab_command:\n"
                "            native = MATLAB_CHECKS.native_code_analysis(script, matlab_command)\n"
                "            if native_report is not None:\n"
                "                native_report.update(native)\n"
                "            quality_errors.extend(native[\"issues\"])\n"
                "            if native.get(\"source_sha256\") and native[\"source_sha256\"] != source_sha256:\n"
                "                quality_errors.append(\"MATLAB原生检查源码与本次配置/工程检查源码不一致\")\n"
                "            for item in native.get(\"complexity_metrics\", []):\n"
                "                if item[\"value\"] > load_yaml(QUALITY_CONTRACT)[\"complexity\"][\"hard_max\"]:\n"
                "                    quality_errors.append(f\"MATLAB原生复杂度L{item['line']}={item['value']}超过硬上限\")\n"
                "    else:\n"
            ),
        ),
        (
            (
                "                    helper_text, {}, contract=load_yaml(QUALITY_CONTRACT), filename=helper.name)\n"
                "                native = _native_delivery_analysis(helper, matlab_command, require_native=require_native)\n"
                "                errors.extend(native[\"issues\"])\n"
                "                warnings.extend(native.get(\"warnings\", []))\n"
                "                metrics[\"native_analysis_status\"] = native[\"status\"]\n"
                "                metrics[\"native_release\"] = native.get(\"release\")\n"
                "                metrics[\"native_source_sha256\"] = native.get(\"source_sha256\")\n"
                "                metrics[\"native_complexity\"] = native.get(\"complexity_metrics\", [])\n"
                "                if native.get(\"source_sha256\") and native[\"source_sha256\"] != record[\"sha256\"]:\n"
                "                    errors.append(\"MATLAB依赖原生检查源码与本次bundle不一致\")\n"
                "                if any(item[\"value\"] > load_yaml(QUALITY_CONTRACT)[\"complexity\"][\"hard_max\"]\n"
                "                       for item in native.get(\"complexity_metrics\", [])):\n"
                "                    errors.append(\"MATLAB依赖原生复杂度超过硬上限\")\n"
                "            else:\n"
            ),
            (
                "                    helper_text, {}, contract=load_yaml(QUALITY_CONTRACT), filename=helper.name)\n"
                "                native = None\n"
                "                if require_native or matlab_command:\n"
                "                    native = MATLAB_CHECKS.native_code_analysis(helper, matlab_command)\n"
                "                    errors.extend(native[\"issues\"])\n"
                "                    warnings.extend(native.get(\"warnings\", []))\n"
                "                    metrics[\"native_analysis_status\"] = native[\"status\"]\n"
                "                    metrics[\"native_release\"] = native.get(\"release\")\n"
                "                    metrics[\"native_source_sha256\"] = native.get(\"source_sha256\")\n"
                "                    metrics[\"native_complexity\"] = native.get(\"complexity_metrics\", [])\n"
                "                    if native.get(\"source_sha256\") and native[\"source_sha256\"] != record[\"sha256\"]:\n"
                "                        errors.append(\"MATLAB依赖原生检查源码与本次bundle不一致\")\n"
                "                    if any(item[\"value\"] > load_yaml(QUALITY_CONTRACT)[\"complexity\"][\"hard_max\"]\n"
                "                           for item in native.get(\"complexity_metrics\", [])):\n"
                "                        errors.append(\"MATLAB依赖原生复杂度超过硬上限\")\n"
                "            else:\n"
            ),
        ),
        (
            (
                "        return 1\n"
                "    matlab_command = args.matlab_command\n"
                "    if matlab_command is None and any(script.suffix.lower() == \".m\" for script in scripts):\n"
                "        matlab_command = shutil.which(\"matlab\")\n"
                "    issues: list[str] = []\n"
            ),
            (
                "        return 1\n"
                "    issues: list[str] = []\n"
            ),
        ),
        (
            (
                "        native_report: dict[str, Any] = {}\n"
                "        item_issues, config = validate_script(root, script, args.stage, matlab_command=matlab_command,\n"
                "                                             native_report=native_report)\n"
                "        issues.extend(f\"{script.name}: {item}\" for item in item_issues)\n"
            ),
            (
                "        native_report: dict[str, Any] = {}\n"
                "        item_issues, config = validate_script(root, script, args.stage, matlab_command=args.matlab_command,\n"
                "                                             require_native=args.write or args.strict, native_report=native_report)\n"
                "        issues.extend(f\"{script.name}: {item}\" for item in item_issues)\n"
            ),
        ),
        (
            (
                "            item_metrics[\"dependency_code_quality\"] = native_report[\"dependency_code_quality\"]\n"
                "            native_statuses = [item_metrics.get(\"native_analysis_status\"), *(\n"
                "                item.get(\"native_analysis_status\") for item in native_report[\"dependency_code_quality\"].values()\n"
                "            )]\n"
                "            if \"failed\" in native_statuses:\n"
                "                item_metrics[\"native_analysis_status\"] = \"failed\"\n"
                "            elif \"unverified\" in native_statuses:\n"
                "                item_metrics[\"native_analysis_status\"] = \"unverified\"\n"
            ),
            (
                "            item_metrics[\"dependency_code_quality\"] = native_report[\"dependency_code_quality\"]\n"
                "            if any(item.get(\"native_analysis_status\") == \"unverified\" for item in native_report[\"dependency_code_quality\"].values()):\n"
                "                item_metrics[\"native_analysis_status\"] = \"unverified\"\n"
            ),
        ),
        (
            (
                "    report = {\n"
                "        \"status\": \"failed\" if issues else \"passed\",\n"
                "        \"checked_scripts\": checked,\n"
            ),
            (
                "    report = {\n"
                "        \"status\": (\"failed\" if issues else \"unverified\" if any(\n"
                "            item.get(\"native_analysis_status\") == \"unverified\" for item in metrics.values()) else \"passed\"),\n"
                "        \"checked_scripts\": checked,\n"
            ),
        ),
    ),
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


def inverse_user_checker_changes(relative: str, text: str) -> str:
    """Accept exactly one occurrence of each approved replacement, without masking drift."""
    for current, baseline in USER_CHECKER_AUTHORITY_REWRITES.get(relative, ()):
        if text.count(current) != 1:
            raise ValueError(f"{relative}: authorized checker delta is missing or duplicated")
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
        "core/writing_reasoning_contract.yaml": "b17c4f5f9555a3be873761f46e94cdf77e86d40e",
        "modules/03_solve_validate.md": "cfbe8091f0434b8531ec97cbccde013895e18228",
        "modules/03_result_analysis.md": "d63db5f2acdba56d006cff5de6de2f76df02364a",
        "modules/05_writing/paper_writing_protocol.md": "5c8bca56733cd0feabf82ba0daa3aea780a79a0c",
        "modules/05_writing/ai_cleanup.md": "3e6249d17a0a91091bf7c61c49aeb9245ccc41e1",
        # C1 distinguishes optional receipt metadata from the internal review matrix.
        "modules/06_review_delivery.md": "4d2bc78193c14f2ee72983db7d58b1870e9ca59f",
        "config/competition_profiles.yaml": "0cfe08e2edac99f07f2e527643499b8bc73c0479",
        "scripts/validate_semantic_governance.py": "3a91083546ce0bd0cc20ca3e1c5593611f00f77d",
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
        # Delivery checks the root policy again against the state being committed.
        "scripts/validate_code_delivery.py": "2877ba23d4b52cedafb8508e47a5afe0b2ece975",
    }

    def prior_handoff_text(self, relative):
        text = (ROOT / relative).read_text(encoding="utf-8")
        for current, baseline in PDF_REVIEW_OWNER_REWRITES.get(relative, ()):
            self.assertEqual(text.count(current), 1, (relative, current))
            text = text.replace(current, baseline, 1)
        text = inverse_user_checker_changes(relative, text)
        for current, baseline in HANDOFF_AUTHORITY_REWRITES.get(relative, ()):
            self.assertEqual(text.count(current), 1, (relative, current))
            text = text.replace(current, baseline, 1)
        return text

    def test_protected_authorities_have_not_drifted(self):
        # W1 proof-body preservation, judge-readable heading/terminology, Part D table/figure
        # readability, Part C derivation closure, Part E narrative, and approved Part F heading-depth changes
        # intentionally re-pin only the touched writing authorities; unrelated drift still fails closed.
        protocol = "modules/05_writing/paper_writing_protocol.md"
        competition_profiles = "config/competition_profiles.yaml"
        protocol_rewrites = (
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
                    self.assertEqual(text.count(competition_lineage_comment), 1)
                    data = text.replace(competition_lineage_comment, "", 1).encode("utf-8")
                    actual = hashlib.sha1(
                        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
                    ).hexdigest()
                elif relative in COMPARISON_AUTHORITY_REWRITES:
                    text = self.prior_handoff_text(relative)
                    for current, baseline in COMPARISON_AUTHORITY_REWRITES[relative]:
                        self.assertEqual(text.count(current), 1, (relative, current))
                        text = text.replace(current, baseline, 1)
                    data = text.encode("utf-8")
                    actual = hashlib.sha1(
                        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
                    ).hexdigest()
                elif relative in HANDOFF_AUTHORITY_REWRITES or relative in USER_CHECKER_AUTHORITY_REWRITES:
                    data = self.prior_handoff_text(relative).encode("utf-8")
                    actual = hashlib.sha1(
                        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
                    ).hexdigest()
                elif relative == "core/project_state.schema.yaml":
                    from claim_schema_reference import previous_d2_schema

                    text = path.read_text(encoding="utf-8")
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
                else:
                    actual = git_blob_sha(path)
                self.assertEqual(actual, expected)

    def test_checker_inverse_projection_rejects_missing_or_duplicate_authorized_blocks(self):
        for relative, replacements in USER_CHECKER_AUTHORITY_REWRITES.items():
            text = (ROOT / relative).read_text(encoding="utf-8")
            for current, _ in replacements:
                for changed in (text.replace(current, "unauthorized replacement\n", 1), text + current):
                    with self.subTest(relative=relative, current=current[:80]):
                        with self.assertRaises(ValueError):
                            inverse_user_checker_changes(relative, changed)

    def test_checker_inverse_projection_does_not_erase_unrelated_changes(self):
        for relative in USER_CHECKER_AUTHORITY_REWRITES:
            text = (ROOT / relative).read_text(encoding="utf-8")
            changed = text + "\nunauthorized unrelated change\n"
            projected = inverse_user_checker_changes(relative, text)
            self.assertEqual(
                inverse_user_checker_changes(relative, changed),
                projected + "\nunauthorized unrelated change\n",
            )
            self.assertEqual((ROOT / relative).read_text(encoding="utf-8"), text)

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
