from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one occurrence, found {count}: {old!r}")
    return text.replace(old, new, 1)


def regex_once(text: str, pattern: str, repl: str, *, label: str, flags: int = 0) -> str:
    new, count = re.subn(pattern, repl, text, count=1, flags=flags)
    if count != 1:
        raise SystemExit(f"{label}: expected one regex match, found {count}: {pattern!r}")
    return new


# ---------------------------------------------------------------------------
# Version carriers
# ---------------------------------------------------------------------------
for path, old, new in (
    ("core/bootstrap.yaml", "skill_version: 7.11.0", "skill_version: 7.11.1"),
    ("core/workflow_router.yaml", "version: 7.11.0", "version: 7.11.1"),
    ("core/module_manifest.yaml", "version: 7.11.0", "version: 7.11.1"),
    ("core/output_contract.yaml", "version: 7.11.0", "version: 7.11.1"),
    ("README.md", "# mathmodel-skill v7.11.0", "# mathmodel-skill v7.11.1"),
    ("core/hsk_core_policy.md", "# HSK Core Policy v7.11.0", "# HSK Core Policy v7.11.1"),
):
    write(path, replace_once(read(path), old, new, label=path))

for path in ("SKILL.md", "skills/mathmodel-skill/SKILL.md"):
    text = read(path)
    text = replace_once(text, "version: 7.11.0", "version: 7.11.1", label=path)
    text = replace_once(text, "# HSK 数学建模模块化工作流 v7.11.0", "# HSK 数学建模模块化工作流 v7.11.1", label=path)
    write(path, text)

plugin_path = ROOT / ".codex-plugin/plugin.json"
plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
if plugin.get("version") != "7.11.0":
    raise SystemExit(f"plugin version drift: {plugin.get('version')}")
plugin["version"] = "7.11.1"
plugin_path.write_text(json.dumps(plugin, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

changelog = read("CHANGELOG.md")
changelog = replace_once(
    changelog,
    "## Current release: 7.11.0",
    """## Current release: 7.11.1

- Consolidated workflow authority so `core/workflow_router.yaml` owns route ordering and runtime boundary declarations, while `core/module_manifest.yaml` is limited to module/artifact/gate graph semantics.
- Removed resolver-embedded `*_GATES`, `*_OUTPUTS`, `DOWNSTREAM_MODULES`, and `MODEL_APPROVAL_REQUIRED_INTENTS` policy constants; `scripts/resolve_workflow.py` now executes declarative router segments and derives module ordering from the router authority.
- Reduced Model Approval duplication in Modules 02/03: field-level challenge/approval binding remains defined only by `core/model_approval_contract.yaml` and enforced by `scripts/validate_model_approval.py`.
- Narrowed `core/output_contract.yaml` semantic/execution/result sections to authority pointers plus delivery-integration switches instead of parallel policy copies.
- Repaired stale release/proposition fixtures and added invariant-focused tests for single authority, boundary dispatch, manifest scope, and resolver policy hygiene.
- Preserved CLI, project-state schema, Workbook Schema, per-question five-file interface, Python/MATLAB ownership, full-fidelity user execution, LaTeX attestation v3, and submission provenance.

## Previous release: 7.11.0""",
    label="CHANGELOG.md",
)
write("CHANGELOG.md", changelog)

readme = read("README.md")
needle = "## v7.11.0：Model Challenge & Human Approval Closure"
section = """## v7.11.1：Single-Authority Stabilization

本补丁不新增建模功能，重点收口 v7.11.0 之后暴露出的第二事实源和失效测试：Router 负责多意图路由、加载顺序与运行边界声明；Manifest 只保存模块/产物/Gate 图；Resolver 只解释声明并生成 plan。Model Approval 的字段级规则继续只由 `core/model_approval_contract.yaml` 定义，Output Contract 只保留交付集成所需的 authority pointer 与运行开关。CLI、项目状态 Schema、Workbook Schema、每问五文件接口、Python/MATLAB 分工、full-fidelity 用户执行和 LaTeX/submission provenance 均保持不变。

"""
readme = replace_once(readme, needle, section + needle, label="README.md")
write("README.md", readme)


# ---------------------------------------------------------------------------
# Router becomes the route/order/runtime-boundary authority.
# ---------------------------------------------------------------------------
router_path = "core/workflow_router.yaml"
router = read(router_path)
router = router.replace("  code_stage_gates: [semantic_governance, model_approval, code_delivery]\n", "", 1)
router = router.replace("  returned_workbook_gates: [semantic_governance, user_execution_receipt]\n", "", 1)

runtime_segments = r'''runtime_segments:
  model_approval_pending:
    role: model_approval
    satisfied_when:
      any: [locked_model_spec, accepted_solution_workbook]
      all_groups:
      - [solution_workbook, result_quality_report]
      - [solved_results, result_quality_report]
    stop_before_module: data_preprocessing
    required_load: [core/model_approval_contract.yaml, core/writing_reasoning_contract.yaml, modules/01_problem_audit.md, modules/02_model_design.md]
    terminal_outputs: [route_comparison, selected_models, proposed_model_spec, model_challenge, model_approval_brief, awaiting_model_approval, preprocessing_decision, formula_closure, formula_reasoning_chain, semantic_closure, complexity_sanity_check, validation_plan, model_paper_framework]
    delivery_scope: design
    pre_delivery_gates: [semantic_governance]
    formal_delivery: false
    pause_state: awaiting_model_approval

  preprocessing:
    role: preprocessing
    canonical_route: data_preprocessing
    stage_module: data_preprocessing
    stop_before_module: solve_validate
    satisfied_when:
      any: [accepted_preprocessing_workbook, preprocessing_workbook]

  primary_execution:
    role: primary_execution
    canonical_route: code_and_solution
    stage_module: solve_validate
    stop_before_module: result_analysis
    satisfied_when:
      any: [accepted_solution_workbook]
      all_groups:
      - [solution_workbook, result_quality_report]
      - [solved_results, result_quality_report]

  analysis_execution:
    role: analysis_execution
    canonical_route: result_analysis
    stage_module: result_analysis
    reset_from_module: solve_validate
    satisfied_when:
      any: [accepted_result_analysis_workbook]
      all_groups:
      - [result_analysis_workbook, validated_results]

  full_workflow_resume:
    role: full_workflow_resume
    final_load: [modules/04_figure_evidence.md, packs/artifact/figure.md, modules/05_writing/latex.md, packs/artifact/latex.md, modules/05_writing/ai_cleanup.md, modules/05_latex_compile_quality.md, modules/06_review_delivery.md, packs/artifact/review.md, packs/artifact/full_submission.md]
    terminal_outputs: [approved_figures, latex_source, latex_audit_report, compiled_pdf, compile_report, review_report, submission_package, model_paper_framework]
    delivery_scope: submission
    pre_delivery_gates: [semantic_governance, project_sync, submission_package_validation]
    formal_delivery: true

'''
router = replace_once(router, "routing:\n", runtime_segments + "routing:\n", label=router_path)

roles = {
    "new_problem_design": "[model_approval]",
    "model_selection": "[model_approval]",
    "advanced_method": "[model_approval]",
    "data_preprocessing": "[model_approval, preprocessing]",
    "full_solution": "[model_approval, preprocessing, primary_execution]",
    "full_workflow": "[model_approval, preprocessing, primary_execution, full_workflow_resume]",
    "code_and_solution": "[model_approval, preprocessing, primary_execution]",
    "result_analysis": "[model_approval, analysis_execution]",
    "validation": "[model_approval, analysis_execution]",
}
for route_name, role_list in roles.items():
    marker = f"  {route_name}:\n"
    router = replace_once(router, marker, marker + f"    boundary_roles: {role_list}\n", label=f"router role {route_name}")
write(router_path, router)


# ---------------------------------------------------------------------------
# Manifest: module/artifact/gate graph only; workflow profiles become aliases.
# ---------------------------------------------------------------------------
manifest_path = "core/module_manifest.yaml"
manifest = read(manifest_path)
manifest = regex_once(
    manifest,
    r"\Aversion: 7\.11\.1\nworkflow_order:\n(?:- .*\n)+conditional_modules:\n(?:- .*\n)+contracts:\n",
    """version: 7.11.1
routing_authority: core/workflow_router.yaml
workflow_profile_compatibility:
  authority: core/workflow_router.yaml
  runtime_consumed: false
  aliases:
    design: new_problem_design
    full_solution: full_solution
    full_workflow: full_workflow
contracts:
""",
    label=manifest_path,
)
manifest = regex_once(
    manifest,
    r"\nworkflow_profiles:\n.*?\nmodules:\n",
    "\nmodules:\n",
    label=manifest_path,
    flags=re.S,
)
write(manifest_path, manifest)


# ---------------------------------------------------------------------------
# Resolver: execution implementation only, no embedded policy constants.
# ---------------------------------------------------------------------------
resolver_path = "scripts/resolve_workflow.py"
resolver = read(resolver_path)
resolver = resolver.replace(
    "def ordered_modules(paths: Iterable[str], manifest: dict[str, Any]) -> list[str]:\n    order = manifest.get(\"workflow_order\") or manifest.get(\"workflow_profiles\", {}).get(\"full_workflow\", {}).get(\"modules\", [])\n",
    "def ordered_modules(paths: Iterable[str], manifest: dict[str, Any], workflow_order: Iterable[str]) -> list[str]:\n    order = list(workflow_order)\n",
    1,
)
resolver = resolver.replace(
    "    manifest: dict[str, Any],\n) -> list[str]:\n    \"\"\"Add unique unconditional upstream producers when current artifact state is supplied.\"\"\"",
    "    manifest: dict[str, Any],\n    workflow_order: Iterable[str],\n) -> list[str]:\n    \"\"\"Add unique unconditional upstream producers when current artifact state is supplied.\"\"\"",
    1,
)
resolver = resolver.replace("for path in ordered_modules(selected, manifest):", "for path in ordered_modules(selected, manifest, workflow_order):")
resolver = resolver.replace("return ordered_modules(selected, manifest)", "return ordered_modules(selected, manifest, workflow_order)")

helpers = r'''
def route_boundary_roles(intents: Iterable[str], router: dict[str, Any]) -> set[str]:
    roles: set[str] = set()
    for intent in intents:
        roles.update(str(item) for item in (router.get("routing", {}).get(intent, {}) or {}).get("boundary_roles", []))
    return roles


def artifact_condition_met(available: set[str], condition: dict[str, Any] | None) -> bool:
    condition = condition or {}
    if set(condition.get("any", [])) & available:
        return True
    return any(set(group).issubset(available) for group in condition.get("all_groups", []))


def module_path(manifest: dict[str, Any], module_name: str) -> str:
    spec = manifest.get("modules", {}).get(module_name)
    if not isinstance(spec, dict) or not spec.get("path"):
        raise ValueError(f"unknown module in runtime segment: {module_name}")
    return str(spec["path"])


def strip_modules_at_or_after(
    paths: Iterable[str],
    manifest: dict[str, Any],
    workflow_order: Iterable[str],
    start_module: str,
) -> list[str]:
    order = list(workflow_order)
    if start_module not in order:
        raise ValueError(f"runtime segment start module is not in workflow order: {start_module}")
    rank = {name: index for index, name in enumerate(order)}
    path_to_name = {
        str(spec.get("path")): name
        for name, spec in manifest.get("modules", {}).items()
        if isinstance(spec, dict) and spec.get("path")
    }
    start_rank = rank[start_module]
    return [
        item for item in paths
        if item not in path_to_name or rank.get(path_to_name[item], 10_000) < start_rank
    ]


def remove_named_modules(paths: Iterable[str], manifest: dict[str, Any], names: Iterable[str]) -> list[str]:
    blocked = {module_path(manifest, name) for name in names}
    return [item for item in paths if item not in blocked]


def runtime_segment(name: str, router: dict[str, Any]) -> dict[str, Any]:
    segment = dict((router.get("runtime_segments", {}) or {}).get(name, {}) or {})
    if not segment:
        raise ValueError(f"missing runtime segment: {name}")
    canonical = segment.get("canonical_route")
    if canonical:
        route = (router.get("routing", {}) or {}).get(canonical)
        if not isinstance(route, dict):
            raise ValueError(f"runtime segment canonical route missing: {name} -> {canonical}")
        for key in ("terminal_outputs", "pre_delivery_gates", "delivery_scope", "formal_delivery", "pause_for_user_execution"):
            if key not in segment and key in route:
                segment[key] = route[key]
    return segment


def segment_result(
    segment: dict[str, Any],
    paths: list[str],
) -> tuple[list[str], list[str], list[str], list[str], bool, bool]:
    scope = segment.get("delivery_scope")
    return (
        paths,
        list(segment.get("terminal_outputs", [])),
        [str(scope)] if scope else [],
        list(segment.get("pre_delivery_gates", [])),
        bool(segment.get("formal_delivery", False)),
        bool(segment.get("pause_for_user_execution", False) or segment.get("pause_state")),
    )


'''
resolver = regex_once(
    resolver,
    r"MODEL_APPROVAL_OUTPUTS = \[.*?\n\ndef apply_model_approval_boundary\(",
    helpers + "def apply_model_approval_boundary(",
    label="resolver policy constants",
    flags=re.S,
)

boundary_funcs = r'''def apply_model_approval_boundary(
    intents: list[str],
    paths: list[str],
    outputs: list[str],
    scopes: list[str],
    gates: list[str],
    formal_delivery: bool,
    pause: bool,
    available: set[str],
    router: dict[str, Any],
    manifest: dict[str, Any],
    workflow_order: Iterable[str],
) -> tuple[list[str], list[str], list[str], list[str], bool, bool, bool]:
    """Stop before task code until the declarative Model Approval segment is satisfied."""
    if "model_approval" not in route_boundary_roles(intents, router):
        return paths, outputs, scopes, gates, formal_delivery, pause, False
    segment = runtime_segment("model_approval_pending", router)
    if artifact_condition_met(available, segment.get("satisfied_when")):
        return paths, outputs, scopes, gates, formal_delivery, pause, False
    paths = strip_modules_at_or_after(
        paths, manifest, workflow_order, str(segment["stop_before_module"])
    )
    for required in segment.get("required_load", []):
        if required not in paths:
            paths.append(str(required))
    paths, outputs, scopes, gates, formal_delivery, pause = segment_result(segment, paths)
    return paths, outputs, scopes, gates, formal_delivery, pause, True


def apply_preprocessing_boundary(
    intents: list[str],
    paths: list[str],
    outputs: list[str],
    scopes: list[str],
    gates: list[str],
    formal_delivery: bool,
    pause: bool,
    available: set[str],
    decision: str | None,
    router: dict[str, Any],
    manifest: dict[str, Any],
    workflow_order: Iterable[str],
) -> tuple[list[str], list[str], list[str], list[str], bool, bool]:
    """Apply the declarative project-level preprocessing execution boundary."""
    if decision is not None and decision not in VALID_PREPROCESSING_DECISIONS:
        raise ValueError(f"unknown preprocessing decision: {decision}")
    segment = runtime_segment("preprocessing", router)
    stage_path = module_path(manifest, str(segment["stage_module"]))
    if decision in {"not_needed", "question_local"}:
        return [item for item in paths if item != stage_path], outputs, scopes, gates, formal_delivery, pause
    if decision != "project_level" or "preprocessing" not in route_boundary_roles(intents, router):
        return paths, outputs, scopes, gates, formal_delivery, pause
    if artifact_condition_met(available, segment.get("satisfied_when")):
        return [item for item in paths if item != stage_path], outputs, scopes, gates, formal_delivery, pause
    paths = strip_modules_at_or_after(
        paths, manifest, workflow_order, str(segment["stop_before_module"])
    )
    if stage_path not in paths:
        paths.append(stage_path)
    return segment_result(segment, paths)


def apply_user_execution_boundary(
    intents: list[str],
    paths: list[str],
    outputs: list[str],
    scopes: list[str],
    gates: list[str],
    formal_delivery: bool,
    pause: bool,
    available: set[str],
    router: dict[str, Any],
    manifest: dict[str, Any],
    workflow_order: Iterable[str],
) -> tuple[list[str], list[str], list[str], list[str], bool, bool]:
    """Select the next declarative user-executed segment without crossing its boundary."""
    roles = route_boundary_roles(intents, router)
    primary = runtime_segment("primary_execution", router)
    analysis = runtime_segment("analysis_execution", router)
    final = runtime_segment("full_workflow_resume", router)
    primary_accepted = artifact_condition_met(available, primary.get("satisfied_when"))
    analysis_accepted = artifact_condition_met(available, analysis.get("satisfied_when"))
    solve_path = module_path(manifest, str(primary["stage_module"]))
    analysis_path = module_path(manifest, str(analysis["stage_module"]))

    def primary_segment(current: list[str]):
        current = strip_modules_at_or_after(
            current, manifest, workflow_order, str(primary["stop_before_module"])
        )
        if solve_path not in current:
            current.append(solve_path)
        return segment_result(primary, current)

    def analysis_segment(current: list[str]):
        current = strip_modules_at_or_after(
            current, manifest, workflow_order, str(analysis["reset_from_module"])
        )
        if analysis_path not in current:
            current.append(analysis_path)
        return segment_result(analysis, current)

    if "full_workflow_resume" in roles:
        if not primary_accepted:
            return primary_segment(paths)
        if not analysis_accepted:
            return analysis_segment(paths)
        paths = strip_modules_at_or_after(paths, manifest, workflow_order, "solve_validate")
        paths.extend(str(item) for item in final.get("final_load", []))
        return segment_result(final, paths)

    if "analysis_execution" in roles:
        if not primary_accepted:
            return primary_segment(paths)
        if not analysis_accepted:
            return analysis_segment(paths)
    if "primary_execution" in roles and not primary_accepted:
        return primary_segment(paths)
    return paths, outputs, scopes, gates, formal_delivery, pause


def resolve_workflow('''
resolver = regex_once(
    resolver,
    r"def apply_model_approval_boundary\(.*?\ndef resolve_workflow\(",
    boundary_funcs,
    label="resolver boundary functions",
    flags=re.S,
)

resolver = replace_once(
    resolver,
    "    manifest = load_yaml(manifest_path)\n    taxonomy: dict[str, Any] | None = None\n",
    "    manifest = load_yaml(manifest_path)\n    workflow_order = list((router.get(\"execution_contract\", {}) or {}).get(\"workflow_order\", []))\n    if not workflow_order:\n        raise ValueError(\"router execution_contract.workflow_order is required\")\n    taxonomy: dict[str, Any] | None = None\n",
    label="resolver workflow order",
)

resolver = resolver.replace(
    "        available_set,\n    ) = apply_model_approval_boundary(",
    "        available_set,\n        router,\n        manifest,\n        workflow_order,\n    ) = apply_model_approval_boundary(",
)
# The previous replacement shape is intentionally corrected below using exact call blocks.
resolver = resolver.replace(
    "        pause_for_user_execution,\n        available_set,\n    )\n\n    preprocessing_pause = False",
    "        pause_for_user_execution,\n        available_set,\n        router,\n        manifest,\n        workflow_order,\n    )\n\n    preprocessing_pause = False",
    1,
)
resolver = resolver.replace(
    "            available_set,\n            preprocessing_decision,\n        )",
    "            available_set,\n            preprocessing_decision,\n            router,\n            manifest,\n            workflow_order,\n        )",
    1,
)
resolver = resolver.replace(
    "                pause_for_user_execution,\n                available_set,\n            )",
    "                pause_for_user_execution,\n                available_set,\n                router,\n                manifest,\n                workflow_order,\n            )",
    1,
)
resolver = resolver.replace("module_paths = ordered_modules(paths, manifest)", "module_paths = ordered_modules(paths, manifest, workflow_order)")
resolver = resolver.replace(
    "module_paths = close_module_dependencies(module_paths, available_set, manifest)",
    "module_paths = close_module_dependencies(module_paths, available_set, manifest, workflow_order)",
)
write(resolver_path, resolver)


# ---------------------------------------------------------------------------
# Output contract: delivery/output authority with delegated semantic policy.
# ---------------------------------------------------------------------------
output_path = "core/output_contract.yaml"
output = read(output_path)
scope_boundary = r'''scope_boundary:
  owns: [project_layout, delivery_attestation, project_sync_stage_requirements, per_question_delivery_layout, global_preprocessing_delivery_layout, framework_modes]
  delegates:
    semantic_governance: scripts/validate_semantic_governance.py
    project_state_and_stale: core/project_state.schema.yaml
    model_approval: core/model_approval_contract.yaml
    preprocessing_semantics: core/global_preprocessing_contract.yaml
    user_execution: core/user_execution_contract.yaml
    result_workbook_and_quality: core/workbook_schema.yaml
    code_quality: core/code_quality_contract.yaml
    writing_reasoning: core/writing_reasoning_contract.yaml
    prose_structure: modules/05_writing/latex.md
  rule: Delegated sections below are integration pointers/switches only; they must not become parallel policy authorities.
'''
output = replace_once(output, "project_root:\n", scope_boundary + "project_root:\n", label=output_path)
output = regex_once(
    output,
    r"execution_policy:\n.*?\nsemantic_governance:\n",
    """execution_policy:
  role: delivery_integration_only
  user_execution_authority: core/user_execution_contract.yaml
  preprocessing_authority: core/global_preprocessing_contract.yaml
  model_approval_authority: core/model_approval_contract.yaml
  semantic_governance_authority: scripts/validate_semantic_governance.py
  code_quality_authority: core/code_quality_contract.yaml
  default_owner: user
  default_profile: full_fidelity
  assistant_task_code_execution_allowed: false
  pause_states: [awaiting_model_approval, awaiting_user_preprocessing, awaiting_user_execution]
semantic_governance:
""",
    label="output execution policy",
    flags=re.S,
)
output = regex_once(
    output,
    r"semantic_governance:\n.*?\nresult_policy:\n",
    """semantic_governance:
  version: 1.0.0
  authority: scripts/validate_semantic_governance.py
  state_schema_authority: core/project_state.schema.yaml
  dependency_kind_authority: core/project_state.schema.yaml#/$defs/dependency_kind
  role: pre_delivery_integrity_gate_pointer_only
  report_persistence: stdout_or_chat_only
result_policy:
""",
    label="output semantic governance",
    flags=re.S,
)
output = regex_once(
    output,
    r"result_policy:\n.*?\nmodel_paper_framework:\n",
    """result_policy:
  role: delivery_admission_summary_only
  workbook_authority: core/workbook_schema.yaml
  preprocessing_authority: core/global_preprocessing_contract.yaml
  analysis_evidence_authority: core/writing_reasoning_contract.yaml#analysis_evidence_disposition
  primary_quality_gate_required: true
  failed_quality_evidence_persisted: true
  downstream_admission_requires_quality_passed: true
  result_analysis_outcomes: [passed, failed, redo_required]
  result_analysis_dispositions: [support, modify, reject]
  fixed_perturbation_forbidden: true
  feedback_loop: Deep analysis may require redo/rewrite, but the detailed disposition semantics live in writing_reasoning_contract.
model_paper_framework:
""",
    label="output result policy",
    flags=re.S,
)
write(output_path, output)


# ---------------------------------------------------------------------------
# Modules consume the approval authority instead of restating field-level rules.
# ---------------------------------------------------------------------------
module2_path = "modules/02_model_design.md"
module2 = read(module2_path)
module2 = regex_once(
    module2,
    r"## 阶段门槛\n\n进入项目级预处理或主求解前必须满足：\n\n1\..*?最终 current 设计链至少形成",
    """## 阶段门槛

进入项目级预处理或主求解前分两层闭合：

1. **设计完整性**：Problem Contract 已冻结；数据口径、三轴分类、变量/目标/约束、`preprocessing_decision`、语义闭环、核心 Formula Trace、必要 Algorithm Trace、Complexity Sanity、当前 semantic revision、命题必要性与 Citation Evidence 计划均达到本模块要求；
2. **审批完整性**：调用 `scripts/validate_model_approval.py` 检查 current Challenge/Approval。审批状态、用户显式批准、revision/hash 绑定、blocking/review_required 处置及 stale 规则只由 `core/model_approval_contract.yaml` 定义，本模块不再复制字段级判定表。

若设计完整性已经满足但 Model Approval gate 尚未通过，形成 `proposed_model_spec`、Model Approval Brief、`awaiting_model_approval` 与 current 框架后停止；不得把“用户未反对”解释为 approval。Gate 通过后才形成 current `locked_model_spec`。若 `preprocessing_decision=project_level`，下一阶段进入 Module 03P；否则直接进入主求解。

最终 current 设计链至少形成""",
    label=module2_path,
    flags=re.S,
)
write(module2_path, module2)

module3_path = "modules/03_solve_validate.md"
module3 = read(module3_path)
module3 = regex_once(
    module3,
    r"进入本模块前，当前小问必须先通过 `scripts/validate_semantic_governance\.py`，并随后通过 `scripts/validate_model_approval\.py`：\n\n(?:- .*\n)+\nProblem Contract、Semantic Closure 或 Complexity Sanity 均不能替代 Model Challenge 与 Human Approval。用户未明确批准当前 semantic revision/hash 时，必须停在 `awaiting_model_approval`，不得生成正式主求解代码。",
    """进入本模块前，当前小问必须依次通过 `scripts/validate_semantic_governance.py` 与 `scripts/validate_model_approval.py`。前者负责当前题意/语义/复杂度与 stale 一致性，后者是 Challenge/Human Approval 的唯一字段级运行门；具体批准状态、revision/hash 绑定与失效条件只服从 `core/model_approval_contract.yaml`，本模块不复制第二套检查清单。

任一 gate 未通过都不得生成正式主求解代码；Model Approval 未通过时返回 Module 02，并停在 `awaiting_model_approval`。""",
    label=module3_path,
    flags=re.S,
)
write(module3_path, module3)


# ---------------------------------------------------------------------------
# Lint follows the new authority split and rejects resolver policy constants.
# ---------------------------------------------------------------------------
lint_path = "scripts/lint_skill_checks.py"
lint = read(lint_path)
lint = lint.replace(
    "        conditional = route.get(\"conditional_stage\") or {}\n        _check_repo_reference(errors, conditional.get(\"module\"), f\"router.{route_name}.conditional_stage.module\")\n",
    "        conditional = route.get(\"conditional_stage\") or {}\n        _check_repo_reference(errors, conditional.get(\"module\"), f\"router.{route_name}.conditional_stage.module\")\n    for segment_name, segment in (router.get(\"runtime_segments\") or {}).items():\n        for field in (\"required_load\", \"final_load\"):\n            for index, value in enumerate(segment.get(field, [])):\n                _check_repo_reference(errors, value, f\"router.runtime_segments.{segment_name}.{field}[{index}]\")\n",
    1,
)
lint = lint.replace(
    "    manifest = load_structured(ROOT / \"core/module_manifest.yaml\") or {}\n    for key, value in (manifest.get(\"contracts\") or {}).items():",
    "    manifest = load_structured(ROOT / \"core/module_manifest.yaml\") or {}\n    _check_repo_reference(errors, manifest.get(\"routing_authority\"), \"manifest.routing_authority\")\n    _check_repo_reference(errors, (manifest.get(\"workflow_profile_compatibility\") or {}).get(\"authority\"), \"manifest.workflow_profile_compatibility.authority\")\n    for key, value in (manifest.get(\"contracts\") or {}).items():",
    1,
)
old_tokens = '    for token in ("pre_delivery_gates", "available_after_modules", "available_after_plan", "gate_plan", "SEMANTIC_CODE_GATES", "SEMANTIC_SYNC_GATES", "apply_preprocessing_boundary", "preprocessing_decision"):\n        if token not in resolver:\n            errors.append(f"resolver lacks gate-closure token: {token}")\n'
new_tokens = '''    for token in ("pre_delivery_gates", "available_after_modules", "available_after_plan", "gate_plan", "runtime_segment", "route_boundary_roles", "apply_preprocessing_boundary", "preprocessing_decision"):
        if token not in resolver:
            errors.append(f"resolver lacks declarative gate-closure token: {token}")
    for forbidden in (
        "PRIMARY_CODE_GATES", "ANALYSIS_CODE_GATES", "SEMANTIC_CODE_GATES", "SEMANTIC_SYNC_GATES",
        "SUBMISSION_GATES", "MODEL_APPROVAL_OUTPUTS", "PREPROCESSING_OUTPUTS", "PRIMARY_CODE_OUTPUTS",
        "ANALYSIS_CODE_OUTPUTS", "FINAL_WORKFLOW_OUTPUTS", "DOWNSTREAM_MODULES", "MODEL_APPROVAL_REQUIRED_INTENTS",
    ):
        if forbidden in resolver:
            errors.append(f"resolver must not embed workflow policy constant: {forbidden}")
'''
lint = replace_once(lint, old_tokens, new_tokens, label="lint resolver tokens")

lint = lint.replace(
    '    if execution.get("code_stage_gates") != ["semantic_governance", "model_approval", "code_delivery"]:\n        errors.append("code stages must declare semantic_governance before code_delivery")\n',
    '',
    1,
)
insert_after = '    if execution.get("task_code_execution_allowed") is not False:\n        errors.append("router must forbid assistant task-code execution")\n'
runtime_checks = '''    segments = router.get("runtime_segments", {}) or {}
    for name in ("model_approval_pending", "preprocessing", "primary_execution", "analysis_execution", "full_workflow_resume"):
        if name not in segments:
            errors.append(f"router runtime segment missing: {name}")
    expected_roles = {
        "new_problem_design": {"model_approval"},
        "model_selection": {"model_approval"},
        "advanced_method": {"model_approval"},
        "data_preprocessing": {"model_approval", "preprocessing"},
        "full_solution": {"model_approval", "preprocessing", "primary_execution"},
        "full_workflow": {"model_approval", "preprocessing", "primary_execution", "full_workflow_resume"},
        "code_and_solution": {"model_approval", "preprocessing", "primary_execution"},
        "result_analysis": {"model_approval", "analysis_execution"},
        "validation": {"model_approval", "analysis_execution"},
    }
    for route_name, expected in expected_roles.items():
        if set((routes.get(route_name, {}) or {}).get("boundary_roles", [])) != expected:
            errors.append(f"router boundary roles drifted: {route_name}")
    for segment_name in ("preprocessing", "primary_execution", "analysis_execution"):
        canonical = (segments.get(segment_name, {}) or {}).get("canonical_route")
        if canonical not in routes:
            errors.append(f"runtime segment canonical route missing: {segment_name} -> {canonical}")
'''
lint = replace_once(lint, insert_after, insert_after + runtime_checks, label="lint runtime segment checks")

old_manifest_head = '''    modules = manifest.get("modules", {})
    order = manifest.get("workflow_order", [])
    rank = {name: index for index, name in enumerate(order)}
'''
new_manifest_head = '''    modules = manifest.get("modules", {})
    router = load_structured(ROOT / "core/workflow_router.yaml") or {}
    order = (router.get("execution_contract") or {}).get("workflow_order", [])
    rank = {name: index for index, name in enumerate(order)}
    if "workflow_order" in manifest or "workflow_profiles" in manifest:
        errors.append("manifest must not duplicate router workflow order/profile semantics")
    compat = manifest.get("workflow_profile_compatibility", {}) or {}
    if compat.get("authority") != "core/workflow_router.yaml" or compat.get("runtime_consumed") is not False:
        errors.append("manifest workflow-profile compatibility must be a non-runtime router alias view")
'''
lint = replace_once(lint, old_manifest_head, new_manifest_head, label="lint manifest order")
lint = regex_once(
    lint,
    r"    profile_spec = manifest\.get\(\"workflow_profiles\", \{\}\)\.get\(\"full_workflow\", \{\}\)\n    profile = profile_spec\.get\(\"modules\", \[\]\)\n    if profile != \[\"problem_audit\", \"model_design\", \"solve_validate\"\]:\n        errors\.append\(\"full_workflow initial manifest profile must stop at solve_validate\"\)\n    if \(profile_spec\.get\(\"conditional_modules\"\) or \{\}\)\.get\(\"data_preprocessing\", \{\}\)\.get\(\"when\"\) != \"preprocessing_decision == project_level\":\n        errors\.append\(\"full_workflow manifest profile must condition data_preprocessing\"\)\n    if profile_spec\.get\(\"pre_delivery_gates\"\) != \[\"semantic_governance\", \"model_approval\", \"code_delivery\"\]:\n        errors\.append\(\"full_workflow initial manifest profile must use semantic and code delivery\"\)\n",
    "",
    label="lint remove manifest profiles",
)

lint = lint.replace(
    '    semantic = output.get("semantic_governance", {})\n    if semantic.get("script") != "scripts/validate_semantic_governance.py":\n        errors.append("output contract must declare semantic governance script")\n    if semantic.get("dependency_kinds") != ["data", "parameter", "model", "result"]:\n        errors.append("semantic governance must define typed dependency kinds")\n    execution = output.get("execution_policy", {})\n    if execution.get("semantic_governance_gate") != "scripts/validate_semantic_governance.py":\n        errors.append("execution policy must require semantic governance")\n    if execution.get("preprocessing_required_before_solve_when_decision") != "project_level":\n        errors.append("execution policy must require preprocessing only for project_level")\n    if execution.get("shared_data_alone_does_not_require_preprocessing") is not True:\n        errors.append("execution policy must not promote shared data to preprocessing automatically")\n',
    '    semantic = output.get("semantic_governance", {})\n    if semantic.get("authority") != "scripts/validate_semantic_governance.py":\n        errors.append("output contract must delegate semantic governance to its authority")\n    if semantic.get("dependency_kind_authority") != "core/project_state.schema.yaml#/$defs/dependency_kind":\n        errors.append("output contract must point dependency kinds to project-state schema")\n    execution = output.get("execution_policy", {})\n    expected_execution_authorities = {\n        "user_execution_authority": "core/user_execution_contract.yaml",\n        "preprocessing_authority": "core/global_preprocessing_contract.yaml",\n        "model_approval_authority": "core/model_approval_contract.yaml",\n        "semantic_governance_authority": "scripts/validate_semantic_governance.py",\n        "code_quality_authority": "core/code_quality_contract.yaml",\n    }\n    for key, expected in expected_execution_authorities.items():\n        if execution.get(key) != expected:\n            errors.append(f"execution policy authority mismatch: {key}")\n',
    1,
)
write(lint_path, lint)


# ---------------------------------------------------------------------------
# Freshen stale tests and move current invariants away from release snapshots.
# ---------------------------------------------------------------------------
v752 = read("tests/test_v752_entrypoint_parity.py")
v752 = regex_once(
    v752,
    r"    def test_current_changelog_matches_bootstrap\(self\):\n        current = .*?\n        self\.assertIn\(\"## Previous release: 7\.6\.0\", changelog\)\n",
    '''    def test_current_changelog_matches_bootstrap(self):
        current = str(yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))["skill_version"])
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        match = re.match(
            rf"# Changelog\\n\\n## Current release: {re.escape(current)}\\n.*?\\n\\n## Previous release: ([^\\n]+)",
            changelog,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(match)
        self.assertNotEqual(match.group(1), current)
''',
    label="v752 changelog freshness",
    flags=re.S,
)
write("tests/test_v752_entrypoint_parity.py", v752)

v631 = read("tests/test_v631_contract_closure.py")
v631 = replace_once(
    v631,
    'full = compact + "## 论文整体框架\\n### 命题与证明规划\\n全文命题上限：4\\n当前计划命题数：0\\n## 综合检验与跨问结论\\n## 同步检查\\n"',
    'full = compact + "## 论文整体框架\\n### 命题与证明规划\\n- 当前计划命题数：0\\n- 默认正文预算：0--4\\n- 超预算状态：`within_default_budget`\\n- 当前命题状态：`planned`\\n## 综合检验与跨问结论\\n## 同步检查\\n"',
    label="v631 proposition fixture",
)
write("tests/test_v631_contract_closure.py", v631)

contract_test = '''import importlib.util
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_resolver():
    path = ROOT / "scripts/resolve_workflow.py"
    spec = importlib.util.spec_from_file_location("contract_closure_resolver", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestContractClosure(unittest.TestCase):
    def setUp(self):
        self.manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8"))
        self.router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        self.resolver = load_resolver()

    def test_all_module_and_gate_artifacts_are_catalogued(self):
        known = set(self.manifest["artifact_catalog"]) | set(self.manifest["external_artifacts"])
        for name, module in self.manifest["modules"].items():
            for field in ("inputs", "outputs"):
                self.assertEqual(set(module[field]) - known, set(), f"{name}.{field}")
        for name, gate in self.manifest["utility_gates"].items():
            for field in ("inputs", "outputs"):
                self.assertEqual(set(gate[field]) - known, set(), f"gate {name}.{field}")

    def test_initial_full_workflow_closes_at_primary_user_execution_boundary(self):
        available = set(self.manifest["modules"]["model_design"]["outputs"])
        available.add("locked_model_spec")
        plan = self.resolver.resolve_workflow(
            "full_workflow",
            objective="optimization",
            structures=["stochastic"],
            available_artifacts=sorted(available),
            preprocessing_decision="not_needed",
        )
        self.assertEqual(plan["pause_state"], "awaiting_user_execution")
        self.assertIn("modules/03_solve_validate.md", plan["modules"])
        self.assertNotIn("modules/03_result_analysis.md", plan["modules"])
        self.assertEqual(
            [item["name"] for item in plan["pre_delivery_gates"]],
            ["semantic_governance", "model_approval", "code_delivery"],
        )

    def test_user_execution_receipt_produces_accepted_results(self):
        gate = self.manifest["utility_gates"]["user_execution_receipt"]
        outputs = set(gate["outputs"])
        self.assertTrue({"accepted_solution_workbook", "result_quality_report", "solved_results", "accepted_result_analysis_workbook", "validated_results"}.issubset(outputs))
        self.assertEqual(gate["path"], "scripts/validate_user_execution.py")

    def test_project_sync_is_real_producer(self):
        gate = self.manifest["utility_gates"]["project_sync"]
        self.assertEqual(gate["path"], "scripts/sync_project.py")
        self.assertTrue((ROOT / gate["path"]).is_file())
        self.assertEqual(set(gate["outputs"]), {"project_state", "sync_report"})
        self.assertIn("<delivery_scope>", gate["command"])

    def test_cleanup_precedes_compile_in_router_order(self):
        order = self.router["execution_contract"]["workflow_order"]
        self.assertLess(order.index("writing_latex"), order.index("ai_cleanup"))
        self.assertLess(order.index("ai_cleanup"), order.index("latex_compile_quality"))
        compile_inputs = set(self.manifest["modules"]["latex_compile_quality"]["inputs"])
        self.assertIn("latex_source", compile_inputs)
        self.assertNotIn("latex_source_draft", compile_inputs)


if __name__ == "__main__":
    unittest.main()
'''
write("tests/test_contract_closure.py", contract_test)

structure = read("tests/test_structure.py")
structure = replace_once(
    structure,
    '''        for order in (
            router["execution_contract"]["workflow_order"],
            manifest["workflow_order"],
        ):
            self.assertLess(order.index("solve_validate"), order.index("result_analysis"))
            self.assertLess(order.index("result_analysis"), order.index("figure_evidence"))
''',
    '''        order = router["execution_contract"]["workflow_order"]
        self.assertLess(order.index("solve_validate"), order.index("result_analysis"))
        self.assertLess(order.index("result_analysis"), order.index("figure_evidence"))
        self.assertNotIn("workflow_order", manifest)
        self.assertNotIn("workflow_profiles", manifest)
''',
    label="structure router order",
)
write("tests/test_structure.py", structure)

latex_test = read("tests/test_latex_first_versionless_docs.py")
latex_test = regex_once(
    latex_test,
    r"    def test_manifest_and_output_contract_are_latex_first\(self\):\n.*?\n    def test_versionless_active_documents_and_legacy_pointers",
    '''    def test_manifest_and_output_contract_are_latex_first(self):
        manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8"))
        router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        full = router["routing"]["full_workflow"]
        loaded = list(full.get("load", [])) + list(full.get("then", []))
        self.assertNotIn("modules/05_writing/docx.md", loaded)
        self.assertNotIn("modules/05_writing/latex.md", loaded)
        self.assertIn("writing_docx", manifest["modules"])
        self.assertIn("writing_latex", manifest["modules"])
        self.assertNotIn("workflow_profiles", manifest)
        output = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        policy = output["writing_policy"]
        self.assertEqual(policy["default_mode"], "latex_first")
        self.assertEqual(policy["docx_mode"], "explicit_only_independent")
        self.assertFalse(policy["docx_is_latex_prerequisite"])

    def test_versionless_active_documents_and_legacy_pointers''',
    label="latex first manifest test",
    flags=re.S,
)
write("tests/test_latex_first_versionless_docs.py", latex_test)

v750 = read("tests/test_v750_writing_reasoning_architecture.py")
v750 = replace_once(
    v750,
    '        self.assertIn("formula_reasoning_chain", manifest["workflow_profiles"]["design"]["terminal_outputs"])\n',
    '        router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))\n        self.assertIn("formula_reasoning_chain", router["routing"]["new_problem_design"]["terminal_outputs"])\n',
    label="v750 manifest workflow profile",
)
write("tests/test_v750_writing_reasoning_architecture.py", v750)

schemas = read("tests/test_schemas.py")
schemas = schemas.replace(
    '        self.assertEqual(contract["semantic_governance"]["script"], "scripts/validate_semantic_governance.py")\n        self.assertEqual(contract["semantic_governance"]["dependency_kinds"], ["data", "parameter", "model", "result"])\n',
    '        self.assertEqual(contract["semantic_governance"]["authority"], "scripts/validate_semantic_governance.py")\n        self.assertEqual(contract["semantic_governance"]["dependency_kind_authority"], "core/project_state.schema.yaml#/$defs/dependency_kind")\n',
    1,
)
write("tests/test_schemas.py", schemas)

authority_test = '''from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_RESOLVER_POLICY_CONSTANTS = (
    "PRIMARY_CODE_GATES", "ANALYSIS_CODE_GATES", "SEMANTIC_CODE_GATES", "SEMANTIC_SYNC_GATES",
    "SUBMISSION_GATES", "MODEL_APPROVAL_OUTPUTS", "PREPROCESSING_OUTPUTS", "PRIMARY_CODE_OUTPUTS",
    "ANALYSIS_CODE_OUTPUTS", "FINAL_WORKFLOW_OUTPUTS", "DOWNSTREAM_MODULES", "MODEL_APPROVAL_REQUIRED_INTENTS",
)


def load_resolver():
    path = ROOT / "scripts/resolve_workflow.py"
    spec = importlib.util.spec_from_file_location("authority_single_source_resolver", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestAuthoritySingleSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        cls.manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8"))
        cls.resolver = load_resolver()

    def test_router_owns_order_and_runtime_boundaries(self):
        self.assertIn("workflow_order", self.router["execution_contract"])
        self.assertIn("runtime_segments", self.router)
        self.assertNotIn("workflow_order", self.manifest)
        self.assertNotIn("workflow_profiles", self.manifest)
        compat = self.manifest["workflow_profile_compatibility"]
        self.assertEqual(compat["authority"], "core/workflow_router.yaml")
        self.assertFalse(compat["runtime_consumed"])

    def test_resolver_contains_no_embedded_policy_collections(self):
        text = (ROOT / "scripts/resolve_workflow.py").read_text(encoding="utf-8")
        for token in FORBIDDEN_RESOLVER_POLICY_CONSTANTS:
            self.assertNotIn(token, text, token)
        self.assertIn("runtime_segment", text)
        self.assertIn("route_boundary_roles", text)

    def test_route_boundary_roles_are_declarative(self):
        expected = {
            "new_problem_design": {"model_approval"},
            "model_selection": {"model_approval"},
            "advanced_method": {"model_approval"},
            "data_preprocessing": {"model_approval", "preprocessing"},
            "full_solution": {"model_approval", "preprocessing", "primary_execution"},
            "full_workflow": {"model_approval", "preprocessing", "primary_execution", "full_workflow_resume"},
            "code_and_solution": {"model_approval", "preprocessing", "primary_execution"},
            "result_analysis": {"model_approval", "analysis_execution"},
            "validation": {"model_approval", "analysis_execution"},
        }
        for route, roles in expected.items():
            self.assertEqual(set(self.router["routing"][route]["boundary_roles"]), roles, route)

    def test_model_approval_and_execution_boundaries_preserve_plan_semantics(self):
        no_approval = self.resolver.resolve_workflow(
            "full_solution", objective="optimization", structures=["stochastic"], preprocessing_decision="not_needed"
        )
        self.assertEqual(no_approval["pause_state"], "awaiting_model_approval")
        self.assertNotIn("modules/03_solve_validate.md", no_approval["modules"])

        design_outputs = set(self.manifest["modules"]["model_design"]["outputs"])
        design_outputs.add("locked_model_spec")
        primary = self.resolver.resolve_workflow(
            "full_solution",
            objective="optimization",
            structures=["stochastic"],
            available_artifacts=sorted(design_outputs),
            preprocessing_decision="not_needed",
        )
        self.assertEqual(primary["pause_state"], "awaiting_user_execution")
        self.assertIn("modules/03_solve_validate.md", primary["modules"])
        self.assertEqual([g["name"] for g in primary["pre_delivery_gates"]], ["semantic_governance", "model_approval", "code_delivery"])

    def test_full_workflow_resumes_analysis_then_submission_from_router_segments(self):
        all_artifacts = set(self.manifest["artifact_catalog"])
        analysis_pending = all_artifacts - {"accepted_result_analysis_workbook", "result_analysis_workbook", "validated_results"}
        analysis_plan = self.resolver.resolve_workflow(
            "full_workflow",
            objective="optimization",
            structures=["stochastic"],
            available_artifacts=sorted(analysis_pending),
            preprocessing_decision="not_needed",
        )
        self.assertEqual(analysis_plan["pause_state"], "awaiting_user_execution")
        self.assertIn("modules/03_result_analysis.md", analysis_plan["modules"])

        final_plan = self.resolver.resolve_workflow(
            "full_workflow",
            objective="optimization",
            structures=["stochastic"],
            available_artifacts=sorted(all_artifacts),
            preprocessing_decision="not_needed",
        )
        self.assertIsNone(final_plan["pause_state"])
        self.assertIn("modules/04_figure_evidence.md", final_plan["modules"])
        self.assertIn("modules/05_writing/latex.md", final_plan["modules"])
        self.assertIn("modules/06_review_delivery.md", final_plan["modules"])
        self.assertEqual([g["name"] for g in final_plan["pre_delivery_gates"]], ["semantic_governance", "project_sync", "submission_package_validation"])


if __name__ == "__main__":
    unittest.main()
'''
write("tests/test_authority_single_source.py", authority_test)

# Matrix is an internal change artifact; update the decision from semantic profiles to aliases.
matrix_path = "docs/architecture/authority_duplication_matrix_v7.11.1.md"
if (ROOT / matrix_path).is_file():
    matrix = read(matrix_path)
    matrix = matrix.replace(
        "| workflow_profiles | core/module_manifest.yaml | Medium | Compatibility view only | Retain for backward compatibility; prohibit new semantics |",
        "| workflow_profiles | core/module_manifest.yaml | Medium | core/workflow_router.yaml | Remove semantic profile copies; retain only a lightweight non-runtime alias map |",
    )
    write(matrix_path, matrix)

print("v7.11.1 stabilization source migration complete")
