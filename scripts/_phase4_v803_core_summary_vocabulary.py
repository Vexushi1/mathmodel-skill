from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8", newline="\n")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one {old!r}, got {count}")
    write(path, text.replace(old, new, 1))


# Release carriers: 8.0.2 -> 8.0.3 without touching historical release prose.
for path, old, new in (
    ("core/bootstrap.yaml", "skill_version: 8.0.2", "skill_version: 8.0.3"),
    ("core/workflow_router.yaml", "version: 8.0.2", "version: 8.0.3"),
    ("core/module_manifest.yaml", "version: 8.0.2", "version: 8.0.3"),
    ("core/output_contract.yaml", "version: 8.0.2", "version: 8.0.3"),
    ("core/writing_runtime_contract.yaml", "version: 8.0.2", "version: 8.0.3"),
    ("config/prose_audit_patterns.yaml", "version: 8.0.2", "version: 8.0.3"),
    (".codex-plugin/plugin.json", '"version": "8.0.2"', '"version": "8.0.3"'),
    ("core/hsk_core_policy.md", "# HSK Core Policy v8.0.2", "# HSK Core Policy v8.0.3"),
):
    replace_once(path, old, new)

for path in ("SKILL.md", "skills/mathmodel-skill/SKILL.md"):
    replace_once(path, "version: 8.0.2", "version: 8.0.3")
    replace_once(path, "# HSK 数学建模模块化工作流 v8.0.2", "# HSK 数学建模模块化工作流 v8.0.3")

# Make semantic-summary and rendering modes explicit while preserving legacy aliases.
reasoning_path = "core/writing_reasoning_contract.yaml"
reasoning = read(reasoning_path)
old = """adaptive_core_model_summary:\n  governance_level: default\n  modes: [required, inline, not_applicable]\n  required_when_any:\n"""
new = """adaptive_core_model_summary:\n  governance_level: default\n  semantic_summary_mode:\n    values: [required, inline, not_applicable]\n    meaning: >-\n      语义层只回答当前问题是否需要独立收束最终可计算模型；required 表示需要显式收束，inline 表示在连续正文中收束，\n      not_applicable 表示当前数学结构无需额外汇总。该层不直接决定 LaTeX 小节或显示形式。\n  modes: [required, inline, not_applicable]\n  modes_status: deprecated_read_alias_for_semantic_summary_mode_until_9_0_0\n  required_when_any:\n"""
if reasoning.count(old) != 1:
    raise RuntimeError("adaptive_core_model_summary anchor drifted")
reasoning = reasoning.replace(old, new, 1)
old = """  adaptive_core_model_summary:\n    status: readable_compatibility_mapping\n    old_to_new_modes:\n      required: displayed\n      inline: inline\n      not_applicable: omitted\n    authority: templates/latex/cumcm/hsk/template_manifest.yaml#core_model_summary_rendering\n"""
new = """  adaptive_core_model_summary:\n    status: readable_compatibility_mapping\n    semantic_summary_mode:\n      values: [required, inline, not_applicable]\n      authority: core/writing_reasoning_contract.yaml#adaptive_core_model_summary\n      legacy_field_alias: modes\n    rendering_mode:\n      values: [displayed, inline, omitted]\n      authority: templates/latex/cumcm/hsk/template_manifest.yaml#core_model_summary_rendering\n      legacy_field_alias: modes\n    semantic_to_rendering_mode:\n      required: displayed\n      inline: inline\n      not_applicable: omitted\n    old_to_new_modes:\n      required: displayed\n      inline: inline\n      not_applicable: omitted\n    old_to_new_modes_status: deprecated_read_alias_for_semantic_to_rendering_mode_until_9_0_0\n    authority: templates/latex/cumcm/hsk/template_manifest.yaml#core_model_summary_rendering\n"""
if reasoning.count(old) != 1:
    raise RuntimeError("v8 compatibility mapping anchor drifted")
write(reasoning_path, reasoning.replace(old, new, 1))

manifest_path = "templates/latex/cumcm/hsk/template_manifest.yaml"
manifest = read(manifest_path)
old = """core_model_summary_rendering:\n  modes:\n    - displayed\n    - inline\n    - omitted\n"""
new = """core_model_summary_rendering:\n  rendering_mode:\n    values:\n      - displayed\n      - inline\n      - omitted\n    semantic_source: core/writing_reasoning_contract.yaml#adaptive_core_model_summary.semantic_summary_mode\n    mapping_authority: core/writing_reasoning_contract.yaml#v8_compatibility.adaptive_core_model_summary.semantic_to_rendering_mode\n  modes:\n    - displayed\n    - inline\n    - omitted\n  modes_status: compatibility_alias_for_rendering_mode_values\n"""
if manifest.count(old) != 1:
    raise RuntimeError("template rendering anchor drifted")
write(manifest_path, manifest.replace(old, new, 1))

protocol_path = "modules/05_writing/paper_writing_protocol.md"
protocol = read(protocol_path)
old = "核心模型汇总应当自适应而非机械必设；v7 的 `required / inline / not_applicable` 只读语义在 v8 分别迁移为 `displayed / inline / omitted`，具体载体选择由 Template Manifest 与当前项目事实确定。"
new = "核心模型汇总先在语义层判定 `semantic_summary_mode = required / inline / not_applicable`：它只回答是否需要独立收束最终可计算模型；随后由 Template Manifest 把语义状态映射为 `rendering_mode = displayed / inline / omitted`。两层中的 `inline` 名称相同但职责不同；v7 的 `modes` 与 `old_to_new_modes` 仅保留只读兼容，具体载体仍由 Template Manifest 与当前项目事实确定。"
if protocol.count(old) != 1:
    raise RuntimeError("paper protocol summary wording anchor drifted")
write(protocol_path, protocol.replace(old, new, 1))

output_path = "core/output_contract.yaml"
output = read(output_path)
old = """  core_model_summary_policy: adaptive_required_inline_not_applicable\n  core_model_summary_policy_status: deprecated_v7_read_compatibility\n  core_model_summary_rendering_authority: templates/latex/cumcm/hsk/template_manifest.yaml#core_model_summary_rendering\n"""
new = """  core_model_summary_semantic_authority: core/writing_reasoning_contract.yaml#adaptive_core_model_summary\n  core_model_summary_semantic_field: semantic_summary_mode\n  core_model_summary_rendering_authority: templates/latex/cumcm/hsk/template_manifest.yaml#core_model_summary_rendering\n  core_model_summary_rendering_field: rendering_mode\n  core_model_summary_mapping_authority: core/writing_reasoning_contract.yaml#v8_compatibility.adaptive_core_model_summary.semantic_to_rendering_mode\n  core_model_summary_policy: adaptive_required_inline_not_applicable\n  core_model_summary_policy_status: deprecated_v7_read_compatibility\n"""
if output.count(old) != 1:
    raise RuntimeError("output contract summary pointer anchor drifted")
write(output_path, output.replace(old, new, 1))

# Update existing regression expectations without removing compatibility aliases.
path = "tests/test_v743_writing_structure_style.py"
text = read(path)
old = '        self.assertEqual(reasoning["adaptive_core_model_summary"]["modes"], ["required", "inline", "not_applicable"])\n'
new = (
    '        summary = reasoning["adaptive_core_model_summary"]\n'
    '        self.assertEqual(summary["semantic_summary_mode"]["values"], ["required", "inline", "not_applicable"])\n'
    '        self.assertEqual(summary["modes"], ["required", "inline", "not_applicable"])\n'
)
if text.count(old) != 1:
    raise RuntimeError("v743 summary assertion drifted")
write(path, text.replace(old, new, 1))

path = "tests/test_v800_template_authority.py"
text = read(path)
old = '        self.assertEqual(rendering["modes"], ["displayed", "inline", "omitted"])\n'
new = (
    '        self.assertEqual(rendering["rendering_mode"]["values"], ["displayed", "inline", "omitted"])\n'
    '        self.assertEqual(rendering["modes"], ["displayed", "inline", "omitted"])\n'
)
if text.count(old) != 1:
    raise RuntimeError("v800 template rendering assertion drifted")
write(path, text.replace(old, new, 1))

# Current-version tests follow bootstrap; historical v8.0.1/v8.0.2 prose remains historical.
path = "tests/test_v7141_skill_health.py"
text = read(path)
if text.count("8.0.2") < 4:
    raise RuntimeError("current health version literals drifted")
write(path, text.replace("8.0.2", "8.0.3"))

path = "tests/test_v800_writing_runtime.py"
text = read(path)
if text.count('"8.0.2"') != 1:
    raise RuntimeError("writing runtime current version assertion drifted")
write(path, text.replace('"8.0.2"', '"8.0.3"', 1))

path = "tests/test_v802_entrypoint_surface_slimming.py"
text = read(path)
for old_lit, new_lit in (
    ('self.assertEqual(str(bootstrap["skill_version"]), "8.0.2")', 'self.assertEqual(str(bootstrap["skill_version"]), "8.0.3")'),
    ('self.assertEqual(str(plugin["version"]), "8.0.2")', 'self.assertEqual(str(plugin["version"]), "8.0.3")'),
    ('self.assertIn("version: 8.0.2", self.root_skill)', 'self.assertIn("version: 8.0.3", self.root_skill)'),
    ('startswith("# mathmodel-skill v8.0.2")', 'startswith("# mathmodel-skill v8.0.3")'),
    ('startswith("# HSK Core Policy v8.0.2")', 'startswith("# HSK Core Policy v8.0.3")'),
    ('startswith("# Changelog\\n\\n## Current release: 8.0.2")', 'startswith("# Changelog\\n\\n## Current release: 8.0.3")'),
    ('self.assertEqual(str(data["version"]), "8.0.2", relative)', 'self.assertEqual(str(data["version"]), "8.0.3", relative)'),
):
    if text.count(old_lit) != 1:
        raise RuntimeError(f"v802 current-carrier assertion drifted: {old_lit}")
    text = text.replace(old_lit, new_lit, 1)
write(path, text)

new_test = '''from __future__ import annotations\n\nimport unittest\nfrom pathlib import Path\n\nimport yaml\n\nROOT = Path(__file__).resolve().parents[1]\n\n\nclass TestV803CoreModelSummaryVocabulary(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.reasoning = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))\n        cls.manifest = yaml.safe_load((ROOT / "templates/latex/cumcm/hsk/template_manifest.yaml").read_text(encoding="utf-8"))\n        cls.output = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))\n        cls.protocol = (ROOT / "modules/05_writing/paper_writing_protocol.md").read_text(encoding="utf-8")\n\n    def test_semantic_and_rendering_modes_are_explicitly_distinct(self):\n        semantic = self.reasoning["adaptive_core_model_summary"]\n        rendering = self.manifest["core_model_summary_rendering"]\n        self.assertEqual(semantic["semantic_summary_mode"]["values"], ["required", "inline", "not_applicable"])\n        self.assertEqual(rendering["rendering_mode"]["values"], ["displayed", "inline", "omitted"])\n        self.assertIn("语义层", semantic["semantic_summary_mode"]["meaning"])\n\n    def test_compatibility_aliases_remain_readable(self):\n        semantic = self.reasoning["adaptive_core_model_summary"]\n        compat = self.reasoning["v8_compatibility"]["adaptive_core_model_summary"]\n        rendering = self.manifest["core_model_summary_rendering"]\n        self.assertEqual(semantic["modes"], ["required", "inline", "not_applicable"])\n        self.assertEqual(rendering["modes"], ["displayed", "inline", "omitted"])\n        self.assertEqual(compat["old_to_new_modes"], {"required": "displayed", "inline": "inline", "not_applicable": "omitted"})\n        self.assertEqual(compat["semantic_to_rendering_mode"], compat["old_to_new_modes"])\n\n    def test_output_contract_points_to_both_layers_and_mapping(self):\n        writing = self.output["writing_policy"]\n        self.assertEqual(writing["core_model_summary_semantic_field"], "semantic_summary_mode")\n        self.assertEqual(writing["core_model_summary_rendering_field"], "rendering_mode")\n        self.assertIn("semantic_to_rendering_mode", writing["core_model_summary_mapping_authority"])\n\n    def test_protocol_explains_two_layer_decision_without_changing_rendering(self):\n        self.assertIn("semantic_summary_mode = required / inline / not_applicable", self.protocol)\n        self.assertIn("rendering_mode = displayed / inline / omitted", self.protocol)\n        self.assertIn("两层中的 `inline` 名称相同但职责不同", self.protocol)\n\n\nif __name__ == "__main__":\n    unittest.main()\n'''
write("tests/test_v803_core_model_summary_vocabulary.py", new_test)

# README / CHANGELOG release notes.
readme = read("README.md")
if not readme.startswith("# mathmodel-skill v8.0.2\n"):
    raise RuntimeError("README current heading drifted")
readme = readme.replace("# mathmodel-skill v8.0.2\n", "# mathmodel-skill v8.0.3\n", 1)
marker = "## v8.0.2：Entrypoint Surface Slimming\n"
if readme.count(marker) != 1:
    raise RuntimeError("README v8.0.2 history marker drifted")
release = (
    "## v8.0.3：Core Model Summary Vocabulary Clarification\n\n"
    "本补丁把核心模型汇总明确分为两层：`semantic_summary_mode = required / inline / not_applicable` 只决定数学叙事是否需要独立收束，"
    "`rendering_mode = displayed / inline / omitted` 只决定 CUMCM 模板呈现；唯一映射仍为 required→displayed、inline→inline、not_applicable→omitted。"
    "旧 `modes` 与 `old_to_new_modes` 保留只读兼容，不自动重排历史论文，也不改变 simple-problem anti-bloat。\n\n"
)
write("README.md", readme.replace(marker, release + marker, 1))

changelog = read("CHANGELOG.md")
old_heading = "## Current release: 8.0.2\n"
if changelog.count(old_heading) != 1:
    raise RuntimeError("CHANGELOG current heading drifted")
new_top = (
    "## Current release: 8.0.3\n\n"
    "- Split adaptive core-model-summary terminology into explicit semantic `semantic_summary_mode` and CUMCM `rendering_mode` layers without changing actual rendering outcomes.\n"
    "- Preserved `modes` and `old_to_new_modes` as deprecated read aliases through the v8 compatibility window; existing v7/v8 projects remain readable and are not automatically rewritten.\n"
    "- Added single mapping authority and output-contract pointers so consumers no longer need to infer whether `required/displayed` belong to the same enum.\n\n"
    "## Previous release: 8.0.2\n"
)
write("CHANGELOG.md", changelog.replace(old_heading, new_top, 1))

status_path = "docs/v801_skill_health_remediation_status.md"
status = read(status_path)
status = status.replace("| Phase 3 | in_progress | Active Entrypoint Surface Slimming；目标 patch `8.0.2` |", "| Phase 3 | complete | Active Entrypoint Surface Slimming 已发布为 `8.0.2` |")
status = status.replace("| Phase 4 | pending | Core Model Summary Vocabulary Clarification |", "| Phase 4 | in_progress | Core Model Summary Vocabulary Clarification；目标 patch `8.0.3` |")
write(status_path, status)

print("v8.0.3 core-model-summary vocabulary migration applied")
