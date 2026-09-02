from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected exactly one match for {old!r}, got {count}")
    write(path, text.replace(old, new, 1))


def replace_all_checked(path: str, old: str, new: str, minimum: int = 1) -> None:
    text = read(path)
    count = text.count(old)
    if count < minimum:
        raise RuntimeError(f"{path}: expected at least {minimum} matches for {old!r}, got {count}")
    write(path, text.replace(old, new))


# 1) Explicit semantic-vs-rendering vocabulary without deleting legacy read aliases.
replace_once(
    "core/writing_reasoning_contract.yaml",
    "adaptive_core_model_summary:\n  governance_level: default\n  modes: [required, inline, not_applicable]\n",
    "adaptive_core_model_summary:\n"
    "  governance_level: default\n"
    "  semantic_summary_mode:\n"
    "    field_role: mathematical_narrative_need\n"
    "    values: [required, inline, not_applicable]\n"
    "  modes: [required, inline, not_applicable]\n"
    "  legacy_modes_field:\n"
    "    status: deprecated_read_only_alias\n"
    "    canonical_field: semantic_summary_mode.values\n"
    "    removal_not_before_skill_version: 9.0.0\n",
)
replace_once(
    "core/writing_reasoning_contract.yaml",
    "  adaptive_core_model_summary:\n"
    "    status: readable_compatibility_mapping\n"
    "    old_to_new_modes:\n"
    "      required: displayed\n"
    "      inline: inline\n"
    "      not_applicable: omitted\n"
    "    authority: templates/latex/cumcm/hsk/template_manifest.yaml#core_model_summary_rendering\n",
    "  adaptive_core_model_summary:\n"
    "    status: readable_compatibility_mapping\n"
    "    semantic_summary_mode_field: adaptive_core_model_summary.semantic_summary_mode.values\n"
    "    legacy_semantic_alias_field: adaptive_core_model_summary.modes\n"
    "    rendering_mode_field: templates/latex/cumcm/hsk/template_manifest.yaml#core_model_summary_rendering.rendering_mode.values\n"
    "    semantic_to_rendering_mode:\n"
    "      required: displayed\n"
    "      inline: inline\n"
    "      not_applicable: omitted\n"
    "    old_to_new_modes:\n"
    "      required: displayed\n"
    "      inline: inline\n"
    "      not_applicable: omitted\n"
    "    legacy_mapping_field:\n"
    "      status: deprecated_read_only_alias\n"
    "      canonical_field: semantic_to_rendering_mode\n"
    "      removal_not_before_skill_version: 9.0.0\n"
    "    authority: templates/latex/cumcm/hsk/template_manifest.yaml#core_model_summary_rendering\n",
)
replace_once(
    "templates/latex/cumcm/hsk/template_manifest.yaml",
    "core_model_summary_rendering:\n  modes:\n    - displayed\n    - inline\n    - omitted\n",
    "core_model_summary_rendering:\n"
    "  rendering_mode:\n"
    "    field_role: cumcm_presentation\n"
    "    values: [displayed, inline, omitted]\n"
    "  modes:\n"
    "    - displayed\n"
    "    - inline\n"
    "    - omitted\n"
    "  legacy_modes_field:\n"
    "    status: deprecated_read_only_alias\n"
    "    canonical_field: rendering_mode.values\n"
    "    removal_not_before_skill_version: 9.0.0\n"
    "  semantic_mapping_authority: core/writing_reasoning_contract.yaml#v8_compatibility.adaptive_core_model_summary.semantic_to_rendering_mode\n",
)
replace_once(
    "modules/05_writing/paper_writing_protocol.md",
    "核心模型汇总应当自适应而非机械必设；v7 的 `required / inline / not_applicable` 只读语义在 v8 分别迁移为 `displayed / inline / omitted`，具体载体选择由 Template Manifest 与当前项目事实确定。",
    "核心模型汇总应当自适应而非机械必设。先由 Writing Reasoning Authority 的 `semantic_summary_mode` 判断数学叙事上是 `required / inline / not_applicable`，再由 CUMCM Template Manifest 的 `rendering_mode` 决定最终呈现为 `displayed / inline / omitted`；两层只通过 Authority 中的唯一映射连接。旧 `modes` 与 `old_to_new_modes` 仅作 v8.x 只读兼容，不应被 consumer 当作新的独立规则。",
)

# 2) Tests: preserve old aliases while locking the new canonical two-layer names.
replace_once(
    "tests/test_v743_writing_structure_style.py",
    "        self.assertEqual(reasoning[\"adaptive_core_model_summary\"][\"modes\"], [\"required\", \"inline\", \"not_applicable\"])\n",
    "        summary = reasoning[\"adaptive_core_model_summary\"]\n"
    "        self.assertEqual(summary[\"semantic_summary_mode\"][\"values\"], [\"required\", \"inline\", \"not_applicable\"])\n"
    "        self.assertEqual(summary[\"modes\"], [\"required\", \"inline\", \"not_applicable\"])\n"
    "        self.assertEqual(summary[\"legacy_modes_field\"][\"canonical_field\"], \"semantic_summary_mode.values\")\n",
)
replace_once(
    "tests/test_v800_template_authority.py",
    "        self.assertEqual(rendering[\"modes\"], [\"displayed\", \"inline\", \"omitted\"])\n",
    "        self.assertEqual(rendering[\"rendering_mode\"][\"values\"], [\"displayed\", \"inline\", \"omitted\"])\n"
    "        self.assertEqual(rendering[\"modes\"], [\"displayed\", \"inline\", \"omitted\"])\n"
    "        self.assertEqual(rendering[\"legacy_modes_field\"][\"canonical_field\"], \"rendering_mode.values\")\n",
)

new_test = '''from pathlib import Path\nimport unittest\n\nimport yaml\n\nROOT = Path(__file__).resolve().parents[1]\n\n\nclass TestV803CoreModelSummaryVocabulary(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.reasoning = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))\n        cls.manifest = yaml.safe_load((ROOT / "templates/latex/cumcm/hsk/template_manifest.yaml").read_text(encoding="utf-8"))\n        cls.protocol = (ROOT / "modules/05_writing/paper_writing_protocol.md").read_text(encoding="utf-8")\n\n    def test_semantic_and_rendering_modes_are_explicitly_distinct(self):\n        summary = self.reasoning["adaptive_core_model_summary"]\n        rendering = self.manifest["core_model_summary_rendering"]\n        self.assertEqual(summary["semantic_summary_mode"]["field_role"], "mathematical_narrative_need")\n        self.assertEqual(summary["semantic_summary_mode"]["values"], ["required", "inline", "not_applicable"])\n        self.assertEqual(rendering["rendering_mode"]["field_role"], "cumcm_presentation")\n        self.assertEqual(rendering["rendering_mode"]["values"], ["displayed", "inline", "omitted"])\n\n    def test_single_authoritative_mapping_is_preserved_with_read_aliases(self):\n        compat = self.reasoning["v8_compatibility"]["adaptive_core_model_summary"]\n        expected = {"required": "displayed", "inline": "inline", "not_applicable": "omitted"}\n        self.assertEqual(compat["semantic_to_rendering_mode"], expected)\n        self.assertEqual(compat["old_to_new_modes"], expected)\n        self.assertEqual(compat["legacy_mapping_field"]["canonical_field"], "semantic_to_rendering_mode")\n        self.assertEqual(self.manifest["core_model_summary_rendering"]["semantic_mapping_authority"], "core/writing_reasoning_contract.yaml#v8_compatibility.adaptive_core_model_summary.semantic_to_rendering_mode")\n\n    def test_legacy_aliases_remain_readable_until_v9(self):\n        summary = self.reasoning["adaptive_core_model_summary"]\n        rendering = self.manifest["core_model_summary_rendering"]\n        self.assertEqual(summary["modes"], summary["semantic_summary_mode"]["values"])\n        self.assertEqual(rendering["modes"], rendering["rendering_mode"]["values"])\n        self.assertEqual(str(summary["legacy_modes_field"]["removal_not_before_skill_version"]), "9.0.0")\n        self.assertEqual(str(rendering["legacy_modes_field"]["removal_not_before_skill_version"]), "9.0.0")\n\n    def test_protocol_describes_two_layers_without_creating_second_mapping(self):\n        self.assertIn("semantic_summary_mode", self.protocol)\n        self.assertIn("rendering_mode", self.protocol)\n        self.assertIn("唯一映射", self.protocol)\n        self.assertNotIn("semantic_to_rendering_mode:", self.protocol)\n\n    def test_rendering_behavior_and_simple_problem_boundary_are_unchanged(self):\n        rendering = self.manifest["core_model_summary_rendering"]\n        self.assertFalse(rendering["independent_named_subsection_default"])\n        self.assertTrue(rendering["simple_problem_anti_bloat"])\n        question = (ROOT / "templates/latex/cumcm/hsk/sections/06_question1.tex").read_text(encoding="utf-8")\n        self.assertNotIn(r"\\subsection{核心模型汇总}", question)\n\n\nif __name__ == "__main__":\n    unittest.main()\n'''
write("tests/test_v803_core_model_summary_vocabulary.py", new_test)

# 3) Patch release carriers, explicitly enumerated.
replace_once("SKILL.md", "version: 8.0.2", "version: 8.0.3")
replace_once("SKILL.md", "# HSK 数学建模模块化工作流 v8.0.2", "# HSK 数学建模模块化工作流 v8.0.3")
replace_once("skills/mathmodel-skill/SKILL.md", "version: 8.0.2", "version: 8.0.3")
replace_once("skills/mathmodel-skill/SKILL.md", "# HSK 数学建模模块化工作流 v8.0.2", "# HSK 数学建模模块化工作流 v8.0.3")
replace_once(".codex-plugin/plugin.json", '"version": "8.0.2"', '"version": "8.0.3"')
replace_once("core/bootstrap.yaml", "skill_version: 8.0.2", "skill_version: 8.0.3")
replace_once("core/hsk_core_policy.md", "# HSK Core Policy v8.0.2", "# HSK Core Policy v8.0.3")
for path in (
    "core/workflow_router.yaml",
    "core/module_manifest.yaml",
    "core/output_contract.yaml",
    "core/writing_runtime_contract.yaml",
    "config/prose_audit_patterns.yaml",
):
    replace_once(path, "version: 8.0.2", "version: 8.0.3")
replace_once("README.md", "# mathmodel-skill v8.0.2", "# mathmodel-skill v8.0.3")

# Version assertions that are intentionally current-health rather than historical migration evidence.
replace_all_checked("tests/test_v7141_skill_health.py", "8.0.2", "8.0.3", minimum=4)
replace_once("tests/test_v800_writing_runtime.py", 'self.assertEqual(self.contract["version"], "8.0.2")', 'self.assertEqual(self.contract["version"], "8.0.3")')
replace_all_checked("tests/test_v802_entrypoint_surface_slimming.py", "8.0.2", "8.0.3", minimum=8)
replace_once("tests/test_v802_entrypoint_surface_slimming.py", "def test_current_release_carriers_are_802(self):", "def test_current_release_carriers_match_current_patch(self):")

# Changelog: retain the full 8.0.2 notes as history.
replace_once(
    "CHANGELOG.md",
    "## Current release: 8.0.2\n",
    "## Current release: 8.0.3\n\n"
    "- Clarified Core Model Summary as two explicit concepts: `semantic_summary_mode` (`required / inline / not_applicable`) for mathematical narrative need, and CUMCM `rendering_mode` (`displayed / inline / omitted`) for presentation.\n"
    "- Kept the former `modes` and `old_to_new_modes` fields as deprecated read-only aliases through v8.x, with a single canonical semantic-to-rendering mapping in `core/writing_reasoning_contract.yaml`.\n"
    "- Preserved CUMCM rendering, simple-problem anti-bloat, historical-paper ordering, Template-First authoring, Model Approval, numerical verification, user execution and all project schemas unchanged.\n"
    "- Added regression coverage for the two-layer vocabulary and compatibility aliases.\n\n"
    "## Previous release: 8.0.2\n",
)

# Program status: correct the already-stale Phase 3 record and record this patch target.
status = read("docs/v801_skill_health_remediation_status.md")
status = status.replace("> 当前 Skill：`8.0.1`", "> 当前 Skill：`8.0.3`")
status = status.replace("> 当前实施基线 `main`：`de8c7d152b8cc4bbe31fe2558dd4b00981a56823`", "> 当前实施基线：Phase 4 merge 后以对应 `main` merge commit 为准；本文件不作为 SHA Authority")
status = status.replace("| Phase 3 | in_progress | Active Entrypoint Surface Slimming；目标 patch `8.0.2` |", "| Phase 3 | complete | PR #94 已发布 `8.0.2`，入口已收缩为最小导航/硬边界/Authority pointers |")
status = status.replace("| Phase 4 | pending | Core Model Summary Vocabulary Clarification |", "| Phase 4 | complete | `8.0.3` 明确 semantic_summary_mode / rendering_mode 两层并保留 v8.x 只读兼容 alias |")
write("docs/v801_skill_health_remediation_status.md", status)

# Root/package entrypoints must remain byte-identical after a release bump.
if read("SKILL.md") != read("skills/mathmodel-skill/SKILL.md"):
    raise RuntimeError("root/package SKILL parity broken")

print("Phase 4 v8.0.3 vocabulary migration applied")
