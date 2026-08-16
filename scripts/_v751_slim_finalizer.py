from pathlib import Path
import json
import re
import textwrap

ROOT = Path(__file__).resolve().parent.parent


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_heading_block(path: str, start_phrase: str, end_phrase: str, replacement: str) -> None:
    text = read(path)
    start_pos = text.find(start_phrase)
    if start_pos < 0:
        raise SystemExit(f"missing start phrase in {path}: {start_phrase}")
    start = text.rfind("\n###", 0, start_pos)
    if start < 0:
        if text.startswith("###"):
            start = 0
        else:
            raise SystemExit(f"cannot locate heading start in {path}: {start_phrase}")
    else:
        start += 1
    end_pos = text.find(end_phrase, start_pos + len(start_phrase))
    if end_pos < 0:
        raise SystemExit(f"missing end phrase in {path}: {end_phrase}")
    end = text.rfind("\n###", 0, end_pos)
    if end < 0:
        raise SystemExit(f"cannot locate heading end in {path}: {end_phrase}")
    end += 1
    write(path, text[:start] + textwrap.dedent(replacement).strip() + "\n\n" + text[end:])


BOOTSTRAP = """
skill_version: 7.5.1
bootstrap_schema_version: 1.1.0
purpose: >-
  Minimal startup index for the HSK mathematical-modeling workflow. Read this
  file first, load the global policy through workflow_router.default_load, then
  use scripts/resolve_workflow.py for the task-specific plan. Do not preload the
  repository or duplicate domain contracts here.
authoritative_sources:
  global_policy: core/hsk_core_policy.md
  routing: core/workflow_router.yaml
  artifact_graph: core/module_manifest.yaml
  task_taxonomy: core/task_taxonomy.yaml
  project_state: core/project_state.schema.yaml
  workbook: core/workbook_schema.yaml
  output: core/output_contract.yaml
  preprocessing: core/global_preprocessing_contract.yaml
  user_execution: core/user_execution_contract.yaml
  code_quality: core/code_quality_contract.yaml
  writing_reasoning: core/writing_reasoning_contract.yaml
  semantic_governance: scripts/validate_semantic_governance.py
startup_contract:
  principle: minimal_route_specific
  default_policy_source: core/hsk_core_policy.md
  resolver: scripts/resolve_workflow.py
  rules:
    - Bootstrap stores pointers and startup invariants only; global domain rules live in core/hsk_core_policy.md.
    - Route-specific contracts are loaded only when the resolved task needs them.
    - Resolver-internal manifests and taxonomies are not user-facing preload unless the route needs their content.
    - Current project semantics are restored from current 模型论文框架.md when available; numerical facts still come from accepted workbooks and machine state from project_state.
hard_invariants:
  - Global modeling, preprocessing, solving, figure, writing and review rules are governed by their authoritative sources above; bootstrap must not restate those contracts in detail.
  - Resolve the smallest task-specific load order and stop after the user-requested deliverable; do not preload unrelated contracts or modules.
  - Formal model/code/downstream delivery must still pass the existing semantic-governance and project-sync gates required by the resolved route.
  - Current 模型论文框架.md is the assistant-readable semantic memory; accepted workbooks are numerical fact sources and project state is the machine-state source.
  - Task-specific preprocessing, solve and result-analysis code remains user-executed; the assistant generates, statically checks and validates returned artifacts under the existing execution contracts.
  - legacy/ remains outside default execution; compatibility pointers are read-only bridges and may not become active dependencies.
entrypoints:
  resolve: python scripts/resolve_workflow.py
  semantic_governance: python scripts/validate_semantic_governance.py
  sync: python scripts/sync_project.py
  validate_state: python scripts/validate_project_state.py
  validate_framework: python scripts/validate_model_paper_framework.py
  review: python scripts/score_submission.py
  validate_code_delivery: python scripts/validate_code_delivery.py
  validate_user_execution: python scripts/validate_user_execution.py
  audit_paper_prose: python scripts/audit_paper_prose.py
repository_maintenance:
  governance: SKILL_CHANGE_GOVERNANCE.md
  mandatory_before_write: true
  read_from_ref: main
  branch_required: true
  pull_request_required: true
  direct_main_write_allowed: false
  generated_files_managed_by: scripts/generate_indexes.py
compatibility:
  legacy_task_labels_supported: true
  legacy_router_single_intent_supported: true
  deprecated_classification_capabilities_supported: true
  deprecated_problem_types_supported: true
  legacy_robustness_workbook_read_supported: true
  v7_2_0_preprocessing_without_decision_read_supported: true
  v7_0_semantic_governance_fields_optional_for_read: true
  v6_6_single_script_question_folders_read_supported: true
  versionless_active_documents:
    - PROJECT_INSTRUCTIONS.md
    - RUNTIME_ROUTER.md
    - SKILL_FILE_INDEX.md
    - TEMPLATE_INDEX.md
  legacy_document_pointers_supported: true
"""

MODEL_BLOCK = """
### 4.1 核心公式推理链

`Source–Derivation–Destination` 的语义定义、允许来源/去向与删除边界由 `core/writing_reasoning_contract.yaml` 的 `formula_reasoning_chain` 唯一负责。本阶段只把已经选定模型的核心关系逐式登记并判定是否闭合：

| 核心关系 | Source：题意/定义/机制/理论依据 | Derivation：关键推理 | Destination：后续用途 | 状态 |
|---|---|---|---|---|
|  |  |  |  | closed / gap |

`closed` 要求三列均能由当前题意与 locked model 实际恢复；存在 gap 时不得用代码实现或论文润色补洞。这张表是内部模型/写作记忆，不原样进入正文。

### 4.2 共享基础与跨问模型增量

是否启用共享基础层、允许/禁止内容及关系图准入以 `writing_reasoning_contract.shared_foundation` 和 `cross_question_progression` 为准。本阶段只记录本题实际选择；没有真实依赖的小问明确标记 `independent`。

| 小问 | 继承结构 | 新增对象/条件 | 新增数学结构 | 困难变化 | 求解变化 |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

### 4.3 数值参数证据计划

数值参数的适用范围、题型证据族和禁止口径由 `writing_reasoning_contract.numerical_parameter_evidence` 唯一负责。本阶段只登记会影响结论的参数及其待验证证据；题面固定参数注明来源即可。

| 参数 | 数学作用 | 候选范围 | 证据方法 | 通过标准 | 最终值状态 |
|---|---|---|---|---|---|
|  |  |  |  |  | pending |
"""

LATEX_BLOCK = """
### 6. 模型推导：核心公式必须有来源、推导和去向

跨竞赛语义以 `core/writing_reasoning_contract.yaml` 为唯一权威；本节只规定终稿如何把该合同自然写出来，不复制内部枚举表。

- **（Source）** 在公式前说明当前对象为什么需要这个关系，并指出题面、定义、机制、数据或已核验理论依据；不能只写“根据相关理论可得”。
- **（Derivation）** 保留会改变建模含义的关键推理，纯代数展开可以压缩；连续多式必须说明前后关系，不能靠“进一步可得/同理可得”替代推理。
- **（Destination）** 公式后立即说明得到什么以及下一步用于哪个状态、目标、约束、判定、降维、算法、验证或题目回答；没有实际去向的式子应删除、压缩或移附录。

正文因此应形成“为什么现在需要这个式子 → 怎样由当前条件得到 → 得到了什么 → 下一步在哪里使用”的连续链，而不是把 `formula_reasoning_chain` 内部合同表复制进论文。共享基础、跨问递进、**结构化简优先于算法升级**和**数值参数必须有选择证据**同样直接消费该合同：正文只写当前题实际启用的内容，不罗列未使用的候选机制或证据方法。
"""

FRAMEWORK_BLOCK = """
### 写作组织策略

> 本节只记录当前项目的写作选择；规则定义分别来自 `modules/05_writing/latex.md` 与 `core/writing_reasoning_contract.yaml`，不得在框架中再复制一套规范。

- 主写作类型：`物理机理/几何工程 / 统计回归 / 机器学习 / 优化调度/图网络 / 动态仿真 / 空间计量 / 多问混合`
- 问题重述口径：当前采用的背景/问题提出组织与必要对象图：
- 问题分析安排：各问难点、对象关系和真实跨问依赖如何组织：
- 共享基础模型：`不需要 / 首次使用处定义 / 独立共享基础章节`；当前选择、涉及小问与章节名：
- 问题关系/模型递进图：`不需要 / 需要`；若需要，必须表达的真实继承与增量：
- 各问正文主线：当前题实际采用的“继承/新增 → 推导 → 核心模型汇总 → 求解 → 结果/深化 → 回答设问”裁剪方式：
- 公式推导口径：重点展示的 Source → Derivation → Destination 链及需要压缩的普通代数：
- 结构化简策略：高级算法前本题实际检查/使用的解析关系、降维、界、分解或前问信息：
- 数值参数证据：需要给出来源、收敛、验证或稳定性依据的参数：
- 结果解释链：核心图表/关键数值如何连接比较基准、机制和题目回答：
- 多方法验证：除主数值外需要比较的结构结论：
- 模型评价安排：`模型的评价与推广 / 模型的改进、评价与推广 / 当届模板指定 / 不单列`；当前选择：
- 独立“结论”一级章：`不设置 / 设置`；依据：
- 语言风格：证据驱动的本科生学术表达；本题需要保留的自然推理痕迹：
- 正向叙述策略：需要避免的重复否定/转折和真正需要保留的冲突、异常、边界：
- 正文篇幅重点：详细推导与短说明分别放在哪里：
- 完成标记：写作组织策略已按当前题型和证据链确定。
"""

NEW_TEST = r'''
from pathlib import Path
import importlib.util
import sys
import unittest
import yaml

ROOT = Path(__file__).resolve().parent.parent
REASONING = "core/writing_reasoning_contract.yaml"


def load_resolver():
    path = ROOT / "scripts/resolve_workflow.py"
    spec = importlib.util.spec_from_file_location("v751_resolver", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ArchitectureSlimmingV751Tests(unittest.TestCase):
    def test_bootstrap_is_pointer_only_and_startup_budget_is_smaller(self):
        bootstrap_path = ROOT / "core/bootstrap.yaml"
        policy_path = ROOT / "core/hsk_core_policy.md"
        bootstrap = yaml.safe_load(bootstrap_path.read_text(encoding="utf-8"))
        self.assertEqual(bootstrap["authoritative_sources"]["writing_reasoning"], REASONING)
        hard = "\n".join(bootstrap["hard_invariants"])
        for duplicated_detail in (
            "Source—Derivation—Destination",
            "GA、PSO、DE",
            "Monte Carlo",
            "问题背景通常",
        ):
            self.assertNotIn(duplicated_detail, hard)
        self.assertLessEqual(bootstrap_path.stat().st_size, 6500)
        self.assertLessEqual(bootstrap_path.stat().st_size + policy_path.stat().st_size, 22000)

    def test_reasoning_contract_keeps_v750_capabilities(self):
        contract = yaml.safe_load((ROOT / REASONING).read_text(encoding="utf-8"))
        self.assertEqual(contract["formula_reasoning_chain"]["chain"], ["source", "derivation", "destination"])
        self.assertEqual(contract["shared_foundation"]["default"], "adaptive")
        self.assertEqual(contract["cross_question_progression"]["activate_when"], "actual_dependency_exists")
        self.assertIn("final_solver_selection", contract["structure_before_algorithm"]["check_order"])
        self.assertIn("optimization_tolerance", contract["numerical_parameter_evidence"]["applies_to"])
        self.assertIn("structural_consistency", contract["multi_method_validation"]["two_levels"])
        self.assertEqual(contract["prose_style"]["name"], "evidence_driven_undergraduate_academic")

    def test_route_specific_reasoning_load_is_preserved(self):
        router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        routes = router["routing"]
        for name in ("new_problem_design", "framework_sync", "proposition_proof", "model_selection", "advanced_method", "docx", "latex"):
            self.assertIn(REASONING, routes[name].get("load", []), name)
        for name in ("problem_analysis", "data_preprocessing", "code_and_solution", "result_analysis", "returned_workbook_validation", "validation", "figures", "full_submission", "review"):
            self.assertNotIn(REASONING, routes[name].get("load", []), name)

    def test_consumers_reference_authority_instead_of_losing_semantics(self):
        for relative in (
            "modules/02_model_design.md",
            "modules/05_writing/latex.md",
            "modules/05_writing/ai_cleanup.md",
            "templates/model/model_paper_framework.md",
            "packs/artifact/proposition_proof.md",
        ):
            self.assertIn(REASONING, (ROOT / relative).read_text(encoding="utf-8"), relative)
        latex = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        for marker in ("（Source）", "（Derivation）", "（Destination）", "结构化简优先于算法升级", "数值参数必须有选择证据"):
            self.assertIn(marker, latex)

    def test_taxonomy_is_lazy_for_nonclassification_routes(self):
        resolver = load_resolver()
        original = resolver.load_yaml
        calls = []

        def traced(path):
            calls.append(path)
            return original(path)

        resolver.load_yaml = traced
        plan = resolver.resolve_workflow("figures")
        self.assertNotIn(resolver.TAXONOMY_PATH, calls)
        self.assertNotIn(REASONING, plan["load_order"])
        self.assertIn("modules/04_figure_evidence.md", plan["load_order"])

        calls.clear()
        taxonomy = yaml.safe_load(resolver.TAXONOMY_PATH.read_text(encoding="utf-8"))
        objective = next(iter(taxonomy["objectives"]))
        plan = resolver.resolve_workflow("model_selection", objective=objective)
        self.assertIn(resolver.TAXONOMY_PATH, calls)
        self.assertIn(REASONING, plan["load_order"])

    def test_minimal_router_default_load_remains_single_policy(self):
        router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        self.assertEqual(router["default_load"], ["core/hsk_core_policy.md"])
        self.assertEqual(router["load_policy"]["principle"], "minimal_route_specific")


if __name__ == "__main__":
    unittest.main()
'''


def main() -> None:
    write("core/bootstrap.yaml", textwrap.dedent(BOOTSTRAP).lstrip())

    replace_heading_block(
        "modules/02_model_design.md",
        "核心公式推理链",
        "复杂度合理性复审",
        MODEL_BLOCK,
    )
    replace_heading_block(
        "modules/05_writing/latex.md",
        "模型推导：核心公式必须有来源、推导和去向",
        "核心模型汇总：推导后、求解前必须出现",
        LATEX_BLOCK,
    )
    replace_heading_block(
        "templates/model/model_paper_framework.md",
        "写作组织策略",
        "推理结构合同",
        FRAMEWORK_BLOCK,
    )

    cleanup_path = "modules/05_writing/ai_cleanup.md"
    cleanup = read(cleanup_path)
    pattern = re.compile(
        r"^25\. \*\*共享基础去重复\*\*.*?^34\. \*\*求解去软件化\*\*.*?$",
        re.M | re.S,
    )
    replacement = """25. **共享基础去重复**：按 `writing_reasoning_contract.shared_foundation` 检查共享内容是否只定义一次；正文只保留本题实际共享部分，单问结果/算法/专属约束不得提前进入共享层；
26. **推导去教科书化**：删除与本题无直接关系的模型史、算法百科和通用优点介绍；
27. **核心公式 Source 检查**：按权威合同复核来源是否真实可追溯；“根据相关理论可得”不能独立充当来源；
28. **核心公式 Derivation 检查**：复核公式前是否存在当前对象到该关系的关键推理；纯代数可压缩，推理不能省略；
29. **核心公式 Destination 检查**：复核公式后是否明确实际下游用途；无用途的公式删除、压缩或移附录；
30. **公式链检查**：连续多式必须形成 Source → Derivation → Destination 的真实推进，不能只靠“进一步可得/同理可得”串联；
31. **核心模型汇总检查**：详细推导结束、求解开始前集中给出最终变量、目标/方程、约束和边界，不重复中间推导；
32. **结构化简优先检查**：按 `writing_reasoning_contract.structure_before_algorithm` 复核高级算法前是否真正检查过可利用结构；
33. **数值参数依据检查**：按 `writing_reasoning_contract.numerical_parameter_evidence` 复核会影响结论的参数是否有来源或收敛/验证/稳定性证据；
34. **求解去软件化**：主要算法说明写模型对应的算法、约束处理、关键参数和终止口径，软件只作为实现环境。"""
    cleanup2, count = pattern.subn(replacement, cleanup, count=1)
    if count != 1:
        raise SystemExit("failed to compact AI-cleanup reasoning block")
    write(cleanup_path, cleanup2)

    resolver_path = "scripts/resolve_workflow.py"
    resolver = read(resolver_path)
    resolver = resolver.replace("HSK v7.5.0 execution plan", "HSK v7.5.1 execution plan", 1)
    old = """    bootstrap = load_yaml(BOOTSTRAP_PATH)\n    router = load_yaml(router_path)\n    manifest = load_yaml(manifest_path)\n    taxonomy = load_yaml(taxonomy_path)\n\n    explicit_intents = [intents] if isinstance(intents, str) else list(intents or [])"""
    new = """    bootstrap = load_yaml(BOOTSTRAP_PATH)\n    router = load_yaml(router_path)\n    manifest = load_yaml(manifest_path)\n    taxonomy: dict[str, Any] | None = None\n\n    def get_taxonomy() -> dict[str, Any]:\n        nonlocal taxonomy\n        if taxonomy is None:\n            taxonomy = load_yaml(taxonomy_path)\n        return taxonomy\n\n    explicit_intents = [intents] if isinstance(intents, str) else list(intents or [])"""
    if old not in resolver:
        raise SystemExit("resolver bootstrap/taxonomy block changed unexpectedly")
    resolver = resolver.replace(old, new, 1)

    old = """    legacy_objective, legacy_structures, legacy_packs = legacy_to_axes(primary, secondary, taxonomy)\n    objective = objective or legacy_objective\n    structures = unique([*legacy_structures, *structures])\n    max_structures = int(taxonomy.get(\"classification_contract\", {}).get(\"structures_max_items\", 3))\n    if len(structures) > max_structures:\n        raise ValueError(f\"at most {max_structures} structures are allowed\")\n    allowed_capabilities = set(taxonomy.get(\"capabilities\", {}))\n    capability_list = unique(capabilities)\n    unknown_capabilities = sorted(set(capability_list) - allowed_capabilities)\n    if unknown_capabilities:\n        raise ValueError(f\"unknown capabilities: {unknown_capabilities}\")\n    task_packs = unique([*legacy_packs, *axes_to_packs(objective, structures, taxonomy)])\n    if len(task_packs) > 3:\n        raise ValueError(\"resolved task packs exceed the one-primary/two-secondary loading budget\")"""
    new = """    secondary_list = list(secondary)\n    structure_inputs = list(structures)\n    capability_inputs = list(capabilities)\n    classification_requested = bool(primary or secondary_list or objective or structure_inputs or capability_inputs)\n    if classification_requested:\n        taxonomy_data = get_taxonomy()\n        legacy_objective, legacy_structures, legacy_packs = legacy_to_axes(primary, secondary_list, taxonomy_data)\n        objective = objective or legacy_objective\n        structures = unique([*legacy_structures, *structure_inputs])\n        max_structures = int(taxonomy_data.get(\"classification_contract\", {}).get(\"structures_max_items\", 3))\n        if len(structures) > max_structures:\n            raise ValueError(f\"at most {max_structures} structures are allowed\")\n        allowed_capabilities = set(taxonomy_data.get(\"capabilities\", {}))\n        capability_list = unique(capability_inputs)\n        unknown_capabilities = sorted(set(capability_list) - allowed_capabilities)\n        if unknown_capabilities:\n            raise ValueError(f\"unknown capabilities: {unknown_capabilities}\")\n        task_packs = unique([*legacy_packs, *axes_to_packs(objective, structures, taxonomy_data)])\n        if len(task_packs) > 3:\n            raise ValueError(\"resolved task packs exceed the one-primary/two-secondary loading budget\")\n    else:\n        structures = []\n        capability_list = []\n        task_packs = []"""
    if old not in resolver:
        raise SystemExit("resolver classification block changed unexpectedly")
    resolver = resolver.replace(old, new, 1)
    write(resolver_path, resolver)

    test730 = "tests/test_v730_writing_expression_protocol.py"
    text = read(test730)
    old = """        self.assertEqual(\n            bootstrap[\"authoritative_sources\"][\"writing_reasoning\"],\n            \"core/writing_reasoning_contract.yaml\",\n        )\n        self.assertIn(\"Source—Derivation—Destination\", \"\\n\".join(bootstrap[\"hard_invariants\"]))"""
    new = """        self.assertEqual(\n            bootstrap[\"authoritative_sources\"][\"writing_reasoning\"],\n            \"core/writing_reasoning_contract.yaml\",\n        )\n        hard = \"\\n\".join(bootstrap[\"hard_invariants\"])\n        self.assertNotIn(\"Source—Derivation—Destination\", hard)\n        self.assertIn(\"authoritative sources\", hard)"""
    if old not in text:
        raise SystemExit("bootstrap writing regression block changed unexpectedly")
    write(test730, text.replace(old, new, 1))
    write("tests/test_v751_architecture_slimming.py", textwrap.dedent(NEW_TEST).lstrip())

    version_paths = [
        "SKILL.md",
        "skills/mathmodel-skill/SKILL.md",
        "README.md",
        "scripts/README.md",
        "legacy/README.md",
        "core/hsk_core_policy.md",
        "core/workflow_router.yaml",
        "core/module_manifest.yaml",
        "core/output_contract.yaml",
        "scripts/lint_skill.py",
    ]
    for path in version_paths:
        text = read(path)
        if "7.5.0" not in text:
            raise SystemExit(f"expected current version marker missing in {path}")
        write(path, text.replace("7.5.0", "7.5.1"))

    plugin_path = ROOT / ".codex-plugin/plugin.json"
    plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
    if plugin.get("version") != "7.5.0":
        raise SystemExit("unexpected plugin version")
    plugin["version"] = "7.5.1"
    plugin_path.write_text(json.dumps(plugin, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for path in (ROOT / "tests").glob("test_*.py"):
        text = path.read_text(encoding="utf-8")
        if "7.5.0" in text:
            path.write_text(text.replace("7.5.0", "7.5.1"), encoding="utf-8")

    changelog = read("CHANGELOG.md")
    marker = "## Current release: 7.5.0\n"
    if marker not in changelog:
        raise SystemExit("current changelog marker missing")
    entry = """## Current release: 7.5.1

- Slimmed `core/bootstrap.yaml` back to a true startup index: it now stores authority pointers and startup invariants rather than duplicating modeling, preprocessing, writing and validation contracts. The detailed v7.5.0 reasoning capabilities remain in `core/writing_reasoning_contract.yaml` and the global policy.
- Kept model-design, LaTeX, AI-cleanup and framework consumers executable while removing duplicated semantic enumerations. Consumers now record/apply the current stage decision and explicitly defer cross-competition Source–Derivation–Destination, shared-foundation, progression, structure-before-algorithm and numerical-evidence definitions to the reasoning authority.
- Made `scripts/resolve_workflow.py` load `core/task_taxonomy.yaml` internally only when classification axes must actually be interpreted or validated. Routes that need the taxonomy as downstream content still return it in `load_order`; figure/writing/workbook utilities no longer parse it internally without need.
- Added v7.5.1 anti-regression tests for startup byte budget, exact route isolation, preserved v7.5.0 reasoning capabilities, consumer-authority linkage and taxonomy lazy loading. Numerical models, preprocessing semantics, workbook schemas, Python/MATLAB ownership, five-file question delivery and LaTeX output interfaces are unchanged.

## Previous release: 7.5.0
"""
    write("CHANGELOG.md", changelog.replace(marker, entry, 1))


if __name__ == "__main__":
    main()
