from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = "7.4.0"
NEW = "7.4.1"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    (ROOT / rel).write_text(text, encoding="utf-8", newline="\n")


def replace_once(rel: str, old: str, new: str) -> None:
    text = read(rel)
    if text.count(old) != 1:
        raise RuntimeError(f"{rel}: expected exactly one occurrence of {old!r}, got {text.count(old)}")
    write(rel, text.replace(old, new, 1))


def replace_all(rel: str, old: str, new: str, minimum: int = 1) -> None:
    text = read(rel)
    count = text.count(old)
    if count < minimum:
        raise RuntimeError(f"{rel}: expected at least {minimum} occurrences of {old!r}, got {count}")
    write(rel, text.replace(old, new))


# Release markers and current-version authorities.
for rel, old, new in [
    ("core/bootstrap.yaml", "skill_version: 7.4.0", "skill_version: 7.4.1"),
    ("core/workflow_router.yaml", "version: 7.4.0", "version: 7.4.1"),
    ("core/module_manifest.yaml", "version: 7.4.0", "version: 7.4.1"),
    ("core/output_contract.yaml", "version: 7.4.0", "version: 7.4.1"),
    ("core/project_state.schema.yaml", "version: 7.4.0", "version: 7.4.1"),
    ("core/user_execution_contract.yaml", "skill_version: 7.4.0", "skill_version: 7.4.1"),
    ("core/code_quality_contract.yaml", "skill_version: 7.4.0", "skill_version: 7.4.1"),
    ("core/global_preprocessing_contract.yaml", "skill_version: 7.4.0", "skill_version: 7.4.1"),
    ("SKILL.md", "version: 7.4.0", "version: 7.4.1"),
    ("SKILL.md", "# HSK 数学建模模块化工作流 v7.4.0", "# HSK 数学建模模块化工作流 v7.4.1"),
    ("skills/mathmodel-skill/SKILL.md", "version: 7.4.0", "version: 7.4.1"),
    ("skills/mathmodel-skill/SKILL.md", "# HSK 数学建模模块化工作流 v7.4.0", "# HSK 数学建模模块化工作流 v7.4.1"),
    ("README.md", "# mathmodel-skill v7.4.0", "# mathmodel-skill v7.4.1"),
    ("scripts/README.md", "# Scripts v7.4.0", "# Scripts v7.4.1"),
    ("legacy/README.md", "不属于 v7.4.0 默认运行链路", "不属于 v7.4.1 默认运行链路"),
    ("core/hsk_core_policy.md", "# HSK Core Policy v7.2.6", "# HSK Core Policy v7.4.1"),
]:
    replace_once(rel, old, new)

# Active stable template docs should not carry an obsolete Skill-era version in their title.
replace_once(
    "templates/latex/cumcm/hsk/README.md",
    "# HSK CUMCM LaTeX Template Add-on v6.2.2",
    "# HSK CUMCM LaTeX Template Add-on",
)

# Plugin release marker.
plugin_path = ROOT / ".codex-plugin/plugin.json"
plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
if plugin.get("version") != OLD:
    raise RuntimeError(f"plugin version unexpected: {plugin.get('version')}")
plugin["version"] = NEW
plugin_path.write_text(json.dumps(plugin, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

# Taxonomy must support the active v7 line.
replace_once(
    "core/task_taxonomy.yaml",
    "skill_compatibility: '>=6.3.1,<7.0.0'",
    "skill_compatibility: '>=6.3.1,<8.0.0'",
)

# Model-design assumptions must agree with the evidence-writing authority: no fixed quota, scoped by use.
replace_once(
    "modules/02_model_design.md",
    "每个模型保留 3--5 个关键假设，说明设立原因、与题意关系、结果影响、失效偏差和检验方式。假设不能替代可由数据或约束直接表达的关系。",
    "模型假设按必要性而非数量配额保留。只有会实质改变变量、约束、目标、分布、状态转移、近似误差或适用边界的条件才作为假设；题面事实、数据事实、确定性定义和单位约定不得伪装成假设。影响两个及以上小问的共享假设进入全局层，只影响单问的假设在第一次使用前就近记录；不存在实质共享假设时允许不设置独立全局假设章。每条保留假设说明依据、与题意关系、对模型/结果的影响、失效偏差和可执行检验。假设不能替代可由数据、定义或约束直接表达的关系。",
)

# Clarify historical feature-origin wording in project-state schema.
replace_once(
    "core/project_state.schema.yaml",
    "description: v7.2.6条件式预处理状态。旧项目可缺失；重新进入模型设计或求解时先锁定decision并按当前通用审计规则复核必要性。",
    "description: v7.2.6引入的条件式预处理状态。旧项目可缺失；重新进入模型设计或求解时先锁定decision并按当前通用审计规则复核必要性。",
)

# Compatibility pointers remain generated/backward-readable, but are no longer part of the active index/manifest surface.
generator = read("scripts/generate_indexes.py")
old_block = '''GENERATED_RELATIVE = {\n    SKILL_INDEX.relative_to(ROOT),\n    TEMPLATE_INDEX.relative_to(ROOT),\n    LEGACY_SKILL_INDEX.relative_to(ROOT),\n    LEGACY_TEMPLATE_INDEX.relative_to(ROOT),\n    MANIFEST.relative_to(ROOT),\n}\n'''
new_block = '''COMPATIBILITY_POINTERS = {\n    Path("PROJECT_INSTRUCTIONS_HSK_V622.md"),\n    Path("HSK_RUNTIME_ROUTER_V622.md"),\n    Path("HSK_SKILL_FILE_INDEX_V622.md"),\n    Path("HSK_TEMPLATE_INDEX_V622.md"),\n}\nGENERATED_RELATIVE = {\n    SKILL_INDEX.relative_to(ROOT),\n    TEMPLATE_INDEX.relative_to(ROOT),\n    MANIFEST.relative_to(ROOT),\n}\n'''
if generator.count(old_block) != 1:
    raise RuntimeError("generate_indexes GENERATED_RELATIVE anchor mismatch")
generator = generator.replace(old_block, new_block, 1)
old_active = '''def is_active_path(relative: Path) -> bool:\n    if relative.parts and relative.parts[0] == "legacy":\n        return relative in ACTIVE_ARCHIVE_POINTERS\n    return True\n'''
new_active = '''def is_active_path(relative: Path) -> bool:\n    if relative in COMPATIBILITY_POINTERS:\n        return False\n    if relative.parts and relative.parts[0] == "legacy":\n        return relative in ACTIVE_ARCHIVE_POINTERS\n    return True\n'''
if generator.count(old_active) != 1:
    raise RuntimeError("generate_indexes is_active_path anchor mismatch")
generator = generator.replace(old_active, new_active, 1)
write("scripts/generate_indexes.py", generator)

# Harden repository lint: current-version authorities, compatibility isolation, path checks and resolver smoke.
lint = read("scripts/lint_skill.py")
lint = lint.replace("import json\nimport subprocess", "import json\nimport re\nimport subprocess", 1)
lint = lint.replace('PACKAGE_VERSION = "7.4.0"', 'PACKAGE_VERSION = "7.4.1"', 1)
lint = lint.replace(
    '    "PROJECT_INSTRUCTIONS_HSK_V622.md", "HSK_RUNTIME_ROUTER_V622.md",\n    "HSK_SKILL_FILE_INDEX_V622.md", "HSK_TEMPLATE_INDEX_V622.md",\n',
    "",
    1,
)
lint = lint.replace(
    'VERSION_DOCS = ["SKILL.md", "README.md", "CHANGELOG.md"]',
    'VERSION_DOCS = ["SKILL.md", "README.md", "CHANGELOG.md", "scripts/README.md", "legacy/README.md", "core/hsk_core_policy.md"]',
    1,
)
insert_after = 'TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".py", ".m", ".tex", ".bib"}\n'
compat_block = '''COMPATIBILITY_POINTERS = {\n    "PROJECT_INSTRUCTIONS_HSK_V622.md": "PROJECT_INSTRUCTIONS.md",\n    "HSK_RUNTIME_ROUTER_V622.md": "RUNTIME_ROUTER.md",\n    "HSK_SKILL_FILE_INDEX_V622.md": "SKILL_FILE_INDEX.md",\n    "HSK_TEMPLATE_INDEX_V622.md": "TEMPLATE_INDEX.md",\n}\nREPO_PATH_PREFIXES = ("core/", "modules/", "packs/", "templates/", "scripts/", "config/", "state/", "assets/", "agents/", "skills/", ".github/", ".codex-plugin/")\nMARKDOWN_LINK_RE = re.compile(r"\\[[^\\]]+\\]\\(([^)]+)\\)")\n'''
if insert_after not in lint:
    raise RuntimeError("lint constants anchor mismatch")
lint = lint.replace(insert_after, insert_after + compat_block, 1)

required_anchor = '''def check_root_release_note_hygiene(errors: list[str]) -> None:\n'''
new_checks = r'''def check_compatibility_pointers(errors: list[str]) -> None:
    bootstrap = load_structured(ROOT / "core/bootstrap.yaml") or {}
    if bootstrap.get("compatibility", {}).get("legacy_document_pointers_supported") is not True:
        errors.append("bootstrap must explicitly declare legacy document-pointer compatibility")
    for legacy, active in COMPATIBILITY_POINTERS.items():
        legacy_path = ROOT / legacy
        active_path = ROOT / active
        if not active_path.is_file():
            errors.append(f"compatibility pointer target missing: {legacy} -> {active}")
            continue
        if not legacy_path.is_file():
            errors.append(f"compatibility pointer missing: {legacy}")
            continue
        text = read_text(legacy_path)
        if "Compatibility Pointer" not in text or active not in text:
            errors.append(f"invalid compatibility pointer: {legacy} -> {active}")
    active_index = read_text(ROOT / "SKILL_FILE_INDEX.md") if (ROOT / "SKILL_FILE_INDEX.md").is_file() else ""
    manifest = read_text(ROOT / "MANIFEST.sha256") if (ROOT / "MANIFEST.sha256").is_file() else ""
    for legacy in COMPATIBILITY_POINTERS:
        if f"`{legacy}`" in active_index:
            errors.append(f"compatibility pointer leaked into active index: {legacy}")
        if any(line.endswith(f"  {legacy}") for line in manifest.splitlines()):
            errors.append(f"compatibility pointer leaked into active manifest: {legacy}")


def _check_repo_reference(errors: list[str], value: object, origin: str, *, base: Path | None = None) -> None:
    if not isinstance(value, str):
        return
    token = value.strip().strip("`<>")
    if not token or token.startswith(("http://", "https://", "mailto:", "#", "plugin://")):
        return
    token = token.split("#", 1)[0].strip()
    if not token or any(marker in token for marker in ("{", "}", "<", ">", "*")):
        return
    candidate = (base / token).resolve() if base is not None and not token.startswith(REPO_PATH_PREFIXES) else (ROOT / token)
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return
    if not candidate.exists():
        errors.append(f"repository reference missing: {origin} -> {token}")


def check_repository_references(errors: list[str]) -> None:
    bootstrap = load_structured(ROOT / "core/bootstrap.yaml") or {}
    for key, value in (bootstrap.get("authoritative_sources") or {}).items():
        _check_repo_reference(errors, value, f"bootstrap.authoritative_sources.{key}")
    for key, command in (bootstrap.get("entrypoints") or {}).items():
        if isinstance(command, str):
            parts = command.split()
            if len(parts) >= 2 and parts[0].lower().startswith("python"):
                _check_repo_reference(errors, parts[1], f"bootstrap.entrypoints.{key}")
    maintenance = bootstrap.get("repository_maintenance") or {}
    _check_repo_reference(errors, maintenance.get("governance"), "bootstrap.repository_maintenance.governance")

    router = load_structured(ROOT / "core/workflow_router.yaml") or {}
    _check_repo_reference(errors, router.get("bootstrap"), "router.bootstrap")
    for index, value in enumerate(router.get("default_load", [])):
        _check_repo_reference(errors, value, f"router.default_load[{index}]")
    for route_name, route in (router.get("routing") or {}).items():
        for field in ("load", "then"):
            for index, value in enumerate(route.get(field, [])):
                _check_repo_reference(errors, value, f"router.{route_name}.{field}[{index}]")
        conditional = route.get("conditional_stage") or {}
        _check_repo_reference(errors, conditional.get("module"), f"router.{route_name}.conditional_stage.module")

    manifest = load_structured(ROOT / "core/module_manifest.yaml") or {}
    for key, value in (manifest.get("contracts") or {}).items():
        _check_repo_reference(errors, value, f"manifest.contracts.{key}")
    for name, spec in (manifest.get("modules") or {}).items():
        _check_repo_reference(errors, spec.get("path"), f"manifest.modules.{name}.path")
    for name, spec in (manifest.get("utility_gates") or {}).items():
        _check_repo_reference(errors, spec.get("path"), f"manifest.utility_gates.{name}.path")

    taxonomy = load_structured(ROOT / "core/task_taxonomy.yaml") or {}
    for objective, spec in (taxonomy.get("objectives") or {}).items():
        pack = spec.get("legacy_pack")
        if pack:
            _check_repo_reference(errors, f"packs/task/{pack}.md", f"taxonomy.objectives.{objective}.legacy_pack")
    for structure, spec in (taxonomy.get("structures") or {}).items():
        pack = spec.get("supplemental_pack")
        if pack:
            _check_repo_reference(errors, f"packs/task/{pack}.md", f"taxonomy.structures.{structure}.supplemental_pack")

    competitions = load_structured(ROOT / "config/competition_profiles.yaml") or {}
    compile_profiles = load_structured(ROOT / "core/compile_profiles.yaml") or {}
    known_compile_profiles = set((compile_profiles.get("profiles") or {}).keys())
    for name, spec in (competitions.get("profiles") or {}).items():
        stable = spec.get("stable") or {}
        _check_repo_reference(errors, stable.get("competition_pack"), f"competition.{name}.competition_pack")
        _check_repo_reference(errors, stable.get("latex_template"), f"competition.{name}.latex_template")
        profile = stable.get("compile_profile")
        if profile is not None and profile not in known_compile_profiles:
            errors.append(f"competition compile profile missing: {name} -> {profile}")
    for name, spec in (compile_profiles.get("profiles") or {}).items():
        directory = spec.get("template_directory")
        _check_repo_reference(errors, directory, f"compile_profiles.{name}.template_directory")
        if directory and spec.get("template_main"):
            _check_repo_reference(errors, f"{str(directory).rstrip('/')}/{spec['template_main']}", f"compile_profiles.{name}.template_main")

    root_docs = [
        ROOT / "SKILL.md", ROOT / "README.md", ROOT / "PROJECT_INSTRUCTIONS.md",
        ROOT / "RUNTIME_ROUTER.md", ROOT / "REPOSITORY_INDEX.md", ROOT / "SKILL_CHANGE_GOVERNANCE.md",
    ]
    markdown_files = set(path for path in active_files() if path.suffix.lower() == ".md") | set(root_docs)
    for path in sorted(markdown_files):
        if not path.is_file():
            continue
        for match in MARKDOWN_LINK_RE.finditer(read_text(path)):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:", "#", "plugin://")):
                continue
            target = target.split()[0].strip("<>")
            _check_repo_reference(errors, target, f"markdown:{path.relative_to(ROOT)}", base=path.parent)


def check_resolver_smoke(errors: list[str]) -> None:
    resolver = load_module("lint_resolver_smoke", ROOT / "scripts/resolve_workflow.py")
    router = load_structured(ROOT / "core/workflow_router.yaml") or {}
    manifest = load_structured(ROOT / "core/module_manifest.yaml") or {}
    available = set(manifest.get("external_artifacts", [])) | set(manifest.get("artifact_catalog", {}))
    for gate in (manifest.get("utility_gates") or {}).values():
        available.update(gate.get("outputs", []))

    def validate_plan(label: str, plan: dict[str, Any]) -> None:
        for field in ("modules", "packs", "templates", "contracts", "load_order"):
            for value in plan.get(field, []):
                if isinstance(value, str) and value.startswith(REPO_PATH_PREFIXES):
                    _check_repo_reference(errors, value, f"resolver:{label}:{field}")
        for gate in plan.get("pre_delivery_gates", []):
            _check_repo_reference(errors, gate.get("path"), f"resolver:{label}:gate:{gate.get('name')}")
        if plan.get("missing_prerequisites"):
            errors.append(f"resolver smoke has missing prerequisites for {label}: {plan['missing_prerequisites']}")

    for route_name in (router.get("routing") or {}):
        decision = "project_level" if route_name == "data_preprocessing" else "not_needed"
        try:
            plan = resolver.resolve_workflow(
                route_name,
                objective="optimization",
                structures=["stochastic"],
                available_artifacts=sorted(available),
                preprocessing_decision=decision,
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"resolver route failed: {route_name}: {exc}")
            continue
        validate_plan(route_name, plan)

    competitions = load_structured(ROOT / "config/competition_profiles.yaml") or {}
    for name in (competitions.get("profiles") or {}):
        try:
            plan = resolver.resolve_workflow(
                "model_selection",
                objective="optimization",
                competition=name,
                available_artifacts=sorted(available),
                preprocessing_decision="not_needed",
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"resolver competition failed: {name}: {exc}")
            continue
        validate_plan(f"competition:{name}", plan)


'''
if required_anchor not in lint:
    raise RuntimeError("lint function insertion anchor mismatch")
lint = lint.replace(required_anchor, new_checks + required_anchor, 1)

# Add exact current-authority version and taxonomy compatibility checks.
version_anchor = '''    if plugin.get("version") != PACKAGE_VERSION:\n        errors.append("plugin version mismatch")\n'''
version_extra = '''    if read_text(ROOT / "core/hsk_core_policy.md").splitlines()[0].strip() != f"# HSK Core Policy v{PACKAGE_VERSION}":\n        errors.append("core policy current-version header mismatch")\n'''
if version_anchor not in lint:
    raise RuntimeError("lint version anchor mismatch")
lint = lint.replace(version_anchor, version_anchor + version_extra, 1)

taxonomy_anchor = '''    if data.get("classification_contract", {}).get("authoritative_locations", {}).get("capabilities") != "subproblem.capabilities":\n        errors.append("taxonomy must declare top-level capabilities as authoritative")\n'''
taxonomy_extra = '''    compatibility = str(data.get("skill_compatibility", ""))\n    if ">=6.3.1" not in compatibility or "<8.0.0" not in compatibility:\n        errors.append("task taxonomy compatibility must cover the active v7 line")\n'''
if taxonomy_anchor not in lint:
    raise RuntimeError("lint taxonomy anchor mismatch")
lint = lint.replace(taxonomy_anchor, taxonomy_anchor + taxonomy_extra, 1)

# Prevent the old assumption quota from reappearing in Module 02.
template_anchor = '''    for token in ("题面—数学—代码三层语义闭环", "Complexity Sanity Check", "semantic_revision", "review_required", "preprocessing_decision"):\n        if token not in design:\n            errors.append(f"model design lacks semantic/preprocessing governance token: {token}")\n'''
template_extra = '''    if "3--5 个关键假设" in design or "3—5 个关键假设" in design:\n        errors.append("model design must not restore a fixed assumption quota")\n    for token in ("按必要性而非数量配额", "共享假设", "单问"):\n        if token not in design:\n            errors.append(f"model design lacks scoped assumption token: {token}")\n'''
if template_anchor not in lint:
    raise RuntimeError("lint model-design anchor mismatch")
lint = lint.replace(template_anchor, template_anchor + template_extra, 1)

main_anchor = '''        check_required, check_root_release_note_hygiene, check_versions, check_bootstrap_and_governance,\n        check_taxonomy, check_router, check_manifest, check_contracts, check_project_state_and_framework,\n        check_templates, check_syntax,\n'''
main_new = '''        check_required, check_compatibility_pointers, check_root_release_note_hygiene, check_versions, check_bootstrap_and_governance,\n        check_taxonomy, check_repository_references, check_router, check_manifest, check_resolver_smoke,\n        check_contracts, check_project_state_and_framework, check_templates, check_syntax,\n'''
if main_anchor not in lint:
    raise RuntimeError("lint main checks anchor mismatch")
lint = lint.replace(main_anchor, main_new, 1)
write("scripts/lint_skill.py", lint)

# Stable docs explicitly state compatibility pointers are outside the active load surface.
replace_once(
    "REPOSITORY_INDEX.md",
    "旧 `V622` 文件只保留兼容指针，不再承载活动规则。",
    "旧 `V622` 文件只保留兼容指针，不再承载活动规则，也不计入 Active Skill Index、Active MANIFEST 或活动 REQUIRED 集合；默认 resolver 不加载这些文件。",
)
replace_once(
    "PROJECT_INSTRUCTIONS.md",
    "旧版本化入口只保留兼容指针，不承载活动规则。",
    "旧版本化入口只保留兼容指针，不承载活动规则，也不进入 Active Skill Index/Active MANIFEST；默认 resolver 不加载它们。",
)
replace_once(
    "scripts/README.md",
    "- `lint_skill.py`：检查活动版本、路由、语义治理、通用判定式条件数据预处理、产物闭环、五文件合同、代码质量合同、Schema、旧结构残留、Python 语法和生成文件；",
    "- `lint_skill.py`：检查活动版本、路由、语义治理、通用判定式条件数据预处理、产物闭环、五文件合同、代码质量合同、Schema、兼容层隔离、仓库引用路径、本地 Markdown 链接、全路由 resolver smoke、旧结构残留、Python 语法和生成文件；",
)

# Current-release assertions in existing regression tests.
replace_all("scripts/resolve_workflow.py", "v7.4.0 execution plan", "v7.4.1 execution plan")
for rel in [
    "tests/test_v730_writing_expression_protocol.py",
    "tests/test_v740_writing_evidence_architecture.py",
    "tests/test_schemas.py",
    "tests/test_v701_stage_boundary_closure.py",
]:
    replace_all(rel, "7.4.0", "7.4.1")

# Add focused v7.4.1 closure regression coverage.
test_path = ROOT / "tests/test_v741_skill_closure_hygiene.py"
if test_path.exists():
    raise RuntimeError("v7.4.1 closure regression already exists")
test_path.write_text(r'''import importlib.util
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
POINTERS = {
    "PROJECT_INSTRUCTIONS_HSK_V622.md": "PROJECT_INSTRUCTIONS.md",
    "HSK_RUNTIME_ROUTER_V622.md": "RUNTIME_ROUTER.md",
    "HSK_SKILL_FILE_INDEX_V622.md": "SKILL_FILE_INDEX.md",
    "HSK_TEMPLATE_INDEX_V622.md": "TEMPLATE_INDEX.md",
}


def load_resolver():
    spec = importlib.util.spec_from_file_location("resolve_workflow_v741", ROOT / "scripts/resolve_workflow.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestV741SkillClosureHygiene(unittest.TestCase):
    def test_current_authorities_are_release_aligned(self):
        bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))
        taxonomy = yaml.safe_load((ROOT / "core/task_taxonomy.yaml").read_text(encoding="utf-8"))
        self.assertEqual(bootstrap["skill_version"], "7.4.1")
        self.assertEqual((ROOT / "core/hsk_core_policy.md").read_text(encoding="utf-8").splitlines()[0], "# HSK Core Policy v7.4.1")
        self.assertIn(">=6.3.1", taxonomy["skill_compatibility"])
        self.assertIn("<8.0.0", taxonomy["skill_compatibility"])

    def test_model_design_has_no_fixed_assumption_quota(self):
        design = (ROOT / "modules/02_model_design.md").read_text(encoding="utf-8")
        self.assertNotIn("3--5 个关键假设", design)
        self.assertNotIn("3—5 个关键假设", design)
        self.assertIn("按必要性而非数量配额", design)
        self.assertIn("共享假设", design)
        self.assertIn("第一次使用前就近记录", design)

    def test_compatibility_pointers_are_preserved_but_not_active(self):
        index = (ROOT / "SKILL_FILE_INDEX.md").read_text(encoding="utf-8")
        manifest = (ROOT / "MANIFEST.sha256").read_text(encoding="utf-8")
        for legacy, active in POINTERS.items():
            pointer = (ROOT / legacy).read_text(encoding="utf-8")
            self.assertIn("Compatibility Pointer", pointer)
            self.assertIn(active, pointer)
            self.assertNotIn(f"`{legacy}`", index)
            self.assertFalse(any(line.endswith(f"  {legacy}") for line in manifest.splitlines()))

    def test_every_router_route_resolves_to_existing_paths(self):
        resolver = load_resolver()
        router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8"))
        available = set(manifest["external_artifacts"]) | set(manifest["artifact_catalog"])
        for gate in manifest.get("utility_gates", {}).values():
            available.update(gate.get("outputs", []))
        prefixes = ("core/", "modules/", "packs/", "templates/", "scripts/", "config/", "state/", "assets/", "agents/", "skills/", ".github/", ".codex-plugin/")
        for route_name in router["routing"]:
            decision = "project_level" if route_name == "data_preprocessing" else "not_needed"
            plan = resolver.resolve_workflow(
                route_name,
                objective="optimization",
                structures=["stochastic"],
                available_artifacts=sorted(available),
                preprocessing_decision=decision,
            )
            self.assertEqual(plan["missing_prerequisites"], [], route_name)
            paths = []
            for field in ("modules", "packs", "templates", "contracts", "load_order"):
                paths.extend(plan.get(field, []))
            paths.extend(gate.get("path") for gate in plan.get("pre_delivery_gates", []))
            for value in paths:
                if isinstance(value, str) and value.startswith(prefixes):
                    self.assertTrue((ROOT / value.split("#", 1)[0]).exists(), f"{route_name}: {value}")


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8", newline="\n")

# Release notes: preserve v7.4.0 as historical feature release while adding a closure patch above it.
changelog = read("CHANGELOG.md")
needle = "## Current release: 7.4.0\n"
if changelog.count(needle) != 1:
    raise RuntimeError("CHANGELOG current release anchor mismatch")
patch_notes = """## Current release: 7.4.1\n\n- Audited every active Module 01--06 stage plus bootstrap, router, manifest, contracts, templates and compatibility boundaries for read/load closure.\n- Fixed the active `core/hsk_core_policy.md` header that still advertised v7.2.6, and extended release-marker linting so current authoritative Markdown cannot silently lag the Skill version again.\n- Fixed `core/task_taxonomy.yaml` declaring `<7.0.0` compatibility even though the active Skill is v7; the taxonomy now explicitly supports the v7 line.\n- Removed the stale fixed `3--5` assumption quota from Module 02 and aligned model design with the writing authority: assumptions are impact-based, checkable and localized by cross-question or question-local scope.\n- Kept the four V622 filenames as backward-compatible pointers but removed them from the active Skill index, active MANIFEST and active-required-file set, so historical pointer names cannot be mistaken for current runtime modules.\n- Made the CUMCM HSK template add-on README versionless so a stable active template entry does not carry an obsolete Skill-era version label.\n- Hardened `lint_skill.py` with compatibility-pointer isolation, taxonomy compatibility checks, repository-relative path validation, Markdown local-link checks and all-route resolver smoke checks.\n- Added v7.4.1 regression coverage for active/compatibility separation and resolver path existence. No Problem Contract, preprocessing, numerical, workbook, MATLAB, five-file or writing-evidence interface changed.\n\n## Previous release: 7.4.0\n"""
changelog = changelog.replace(needle, patch_notes, 1)
write("CHANGELOG.md", changelog)

# One-shot migration scaffolding must not remain in the active package.
Path(__file__).unlink()
