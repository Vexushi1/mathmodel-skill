import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


class TestSchemas(unittest.TestCase):
    def test_project_state_example_validates(self):
        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        example = yaml.safe_load((ROOT / "state/project_state.example.yaml").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        validator.check_schema(schema)
        self.assertEqual(list(validator.iter_errors(example)), [])

    def test_workbook_schema_forbids_empty_sheets(self):
        schema = yaml.safe_load((ROOT / "core/workbook_schema.yaml").read_text(encoding="utf-8"))
        self.assertFalse(schema["global_rules"]["empty_worksheet_allowed"])
        robust = schema["sensitivity_robustness_workbook"]
        self.assertIn("适用性说明", robust["required_any_sheets"])
        self.assertIn("required_columns", robust["sheet_schemas"]["适用性说明"])

    def test_workbook_schema_requires_composite_figure_metadata(self):
        schema = yaml.safe_load((ROOT / "core/workbook_schema.yaml").read_text(encoding="utf-8"))
        handoff = schema["matlab_handoff"]
        self.assertEqual(
            handoff["allowed_composition_levels"],
            ["single", "layered", "multi-panel", "hybrid"],
        )
        for field in (
            "composition_level",
            "layer_map",
            "axis_contract",
            "panel_map",
            "shared_color_mapping",
            "rendering_transforms",
        ):
            self.assertIn(field, handoff["required_mapping_fields"])

    def test_output_contract_references_workbook_schema(self):
        contract = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(contract["schema"], "core/workbook_schema.yaml")
        self.assertEqual(contract["version"], "6.2.2")
        self.assertEqual(
            contract["figure_system"]["composition_levels"],
            ["single", "layered", "multi-panel", "hybrid"],
        )


if __name__ == "__main__":
    unittest.main()
