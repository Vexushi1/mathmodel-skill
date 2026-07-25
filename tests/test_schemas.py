import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def load_state_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_project_state", ROOT / "scripts/validate_project_state.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestSchemas(unittest.TestCase):
    def test_project_state_example_validates(self):
        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        example = yaml.safe_load((ROOT / "state/project_state.example.yaml").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        validator.check_schema(schema)
        self.assertEqual(list(validator.iter_errors(example)), [])

    def test_project_state_requirement_counts_are_consistent(self):
        example = yaml.safe_load((ROOT / "state/project_state.example.yaml").read_text(encoding="utf-8"))
        requirements = example["requirements"]
        completed = set(requirements["completed"])
        pending = set(requirements["pending"])
        self.assertTrue(completed.isdisjoint(pending))
        self.assertEqual(requirements["total"], len(completed | pending))

    def test_project_state_tracks_framework_and_per_subproblem_contract(self):
        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        self.assertIn("paper_framework", schema["required"])
        framework = schema["properties"]["paper_framework"]
        for key in ("path", "version", "sync_status", "last_sync_scope"):
            self.assertIn(key, framework["required"])

        subproblem = schema["properties"]["subproblems"]["additionalProperties"]
        self.assertIn("problem_types", subproblem["required"])
        self.assertIn("capabilities", subproblem["required"])
        self.assertIn("framework_section", subproblem["required"])
        self.assertIn("result_summary_status", subproblem["required"])
        properties = subproblem["properties"]
        for key in (
            "data_hash",
            "validated_data_hash",
            "model_hash",
            "validated_model_hash",
            "artifacts_stale",
            "random_seed",
            "tolerance",
            "optimality_gap",
            "max_constraint_violation",
            "validation_status",
            "evidence",
            "framework_section",
            "result_summary_status",
            "result_summary_anchor",
        ):
            self.assertIn(key, properties)

    def test_semantic_validator_rejects_stale_validated_state(self):
        module = load_state_validator()
        payload = yaml.safe_load((ROOT / "state/project_state.example.yaml").read_text(encoding="utf-8"))
        state = payload["subproblems"]["Q1"]
        state.update(
            status="validated",
            validation_status="passed",
            artifacts_stale=True,
            solution_workbook="result.xlsx",
            robustness_workbook="robust.xlsx",
            evidence=["table"],
            result_summary_status="current",
            result_summary_anchor="#### 结果摘要",
            max_constraint_violation=0.0,
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "result.xlsx").write_bytes(b"x")
            (root / "robust.xlsx").write_bytes(b"x")
            issues = module.validate_state_payload(payload, project_root=root)
        self.assertTrue(any("artifacts_stale" in issue for issue in issues), issues)
        self.assertTrue(any("paper_framework.sync_status" in issue for issue in issues), issues)

    def test_workbook_schema_uses_capabilities_and_title_handoff(self):
        schema = yaml.safe_load((ROOT / "core/workbook_schema.yaml").read_text(encoding="utf-8"))
        self.assertFalse(schema["global_rules"]["empty_worksheet_allowed"])
        contract = schema["capability_contract"]
        self.assertIn("requires_equilibrium_residual", contract["allowed"])
        self.assertEqual(contract["required_sheets"]["requires_conservation_residual"], ["守恒残差"])
        handoff = schema["matlab_handoff"]
        for key in ("matlab_title", "paper_caption", "framework_registry"):
            self.assertIn(key, handoff["required_mapping_fields"])
        self.assertTrue(handoff["title_contract"]["keep_in_export"])

    def test_output_contract_references_framework_workbooks_and_flat_layout(self):
        contract = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(contract["schema"], "core/workbook_schema.yaml")
        self.assertEqual(contract["version"], "6.2.5")
        self.assertEqual(contract["project_root"]["model_paper_framework"], "模型论文框架.md")
        self.assertTrue(contract["model_paper_framework"]["formal_delivery_sync"])
        self.assertEqual(contract["per_question"]["question_directory"], "结果数据表/问题{中文序号}/")
        self.assertEqual(contract["per_question"]["matlab_script"], "q{阿拉伯序号}_plot.m")
        self.assertEqual(contract["per_question"]["figure_directory"], "图表/")
        self.assertTrue(contract["matlab_figure_contract"]["title_required"])
        self.assertEqual(contract["matlab_figure_contract"]["multi_panel_title"], "sgtitle")


if __name__ == "__main__":
    unittest.main()
