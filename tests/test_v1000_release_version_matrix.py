from pathlib import Path
import json
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load(relative):
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)


class V1000ReleaseVersionMatrixTests(unittest.TestCase):
    def test_current_skill_carriers_and_single_backend_cli(self):
        bootstrap = load("core/bootstrap.yaml")
        self.assertEqual(str(bootstrap["skill_version"]), "10.0.0")
        plugin = load(".codex-plugin/plugin.json")
        self.assertEqual(plugin["version"], "10.0.0")
        self.assertIn("one project-wide Python/MATLAB numerical backend", plugin["description"])
        for relative in (
            "core/workflow_router.yaml", "core/module_manifest.yaml",
            "core/output_contract.yaml", "core/writing_runtime_contract.yaml",
            "config/prose_audit_patterns.yaml",
        ):
            with self.subTest(relative=relative):
                self.assertEqual(str(load(relative)["version"]), "10.0.0")
        self.assertEqual(
            bootstrap["entrypoints"]["project_solver_backend"],
            "python scripts/project_solver_backend.py",
        )
        self.assertEqual(
            sum("project_solver_backend.py" in value for value in bootstrap["entrypoints"].values()), 1
        )
        root_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(root_skill, (ROOT / "skills/mathmodel-skill/SKILL.md").read_text(encoding="utf-8"))
        self.assertIn("version: 10.0.0", root_skill)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertTrue(readme.startswith("# mathmodel-skill v10.0.0"))
        self.assertIn("Draft 候选，尚未发布", readme.splitlines()[0])
        self.assertTrue(changelog.startswith("# Changelog\n\n## Current release: 10.0.0\n"))
        self.assertIn("draft branch candidate, not a released tag", changelog)
        self.assertTrue((ROOT / "core/hsk_core_policy.md").read_text(encoding="utf-8").startswith("# HSK Core Policy v10.0.0"))

    def test_independent_protocol_versions_are_not_skill_versions(self):
        bootstrap = load("core/bootstrap.yaml")
        execution = load("core/user_execution_contract.yaml")
        self.assertEqual(bootstrap["bootstrap_schema_version"], "1.1.0")
        self.assertEqual(load("core/project_state.schema.yaml")["version"], "8.0.0")
        self.assertEqual(execution["version"], "3.0.0")
        self.assertEqual(load("core/runtime_assurance_contract.yaml")["version"], "2.0.0")
        self.assertEqual(load("core/state_transition_contract.yaml")["version"], "1.2.0")
        self.assertEqual(load("core/workbook_schema.yaml")["schema_version"], "2.3.1")
        self.assertEqual(execution["code_bundle"]["protocol_version"], "1.1.0")
        self.assertEqual(execution["code_delivery"]["run_receipt_protocol"]["current_version_by_stage"],
                         {"preprocessing": "1.0.0", "primary": "1.1.0", "analysis": "1.1.0"})
        self.assertEqual(execution["code_delivery"]["primary_quality_protocol_version"], "1.0.0")
        self.assertEqual(load("core/output_contract.yaml")["model_paper_framework"]["current_template_version"],
                         "v0.8-project-memory")

    def test_renewed_applicability_preserves_each_lower_bound(self):
        governance = (ROOT / "SKILL_CHANGE_GOVERNANCE.md").read_text(encoding="utf-8")
        self.assertEqual(yaml.safe_load(governance.split("---", 2)[1])["applies_to_skill"],
                         ">=6.3.0,<11.0.0")
        expected = {
            "core/task_taxonomy.yaml": ">=6.3.1,<11.0.0",
            "core/workbook_schema.yaml": ">=6.3.2,<11.0.0",
            "core/global_preprocessing_contract.yaml": ">=7.4.2,<11.0.0",
            "core/code_quality_contract.yaml": ">=7.4.2,<11.0.0",
            "assets/figure_assets.yaml": ">=7.4.2,<11.0.0",
            "core/numerical_verification_contract.yaml": ">=7.14.0,<11.0.0",
        }
        for relative, compatibility in expected.items():
            with self.subTest(relative=relative):
                self.assertEqual(load(relative)["skill_compatibility"], compatibility)

    def test_active_solver_mapping_is_bilingual_and_python_lists_are_legacy_projections(self):
        output = load("core/output_contract.yaml")["per_question"]
        execution = load("core/user_execution_contract.yaml")["code_delivery"]
        self.assertEqual(output["solver_scripts"], {
            "python": {"primary": "问题{中文序号}求解.py", "result_analysis": "问题{中文序号}结果深化分析.py"},
            "matlab": {"primary": "q{阿拉伯序号}_solver.m", "result_analysis": "q{阿拉伯序号}_analysis.m"},
        })
        self.assertEqual(execution["stage_scripts_authority"], "core/output_contract.yaml#per_question.solver_scripts")
        self.assertEqual(output["python_scripts"], output["solver_scripts"]["python"])
        self.assertEqual(output["base_default_files"][0], output["solver_scripts"]["python"]["primary"])
        self.assertEqual(output["analysis_required_additional_files"][0],
                         output["solver_scripts"]["python"]["result_analysis"])


if __name__ == "__main__":
    unittest.main()
