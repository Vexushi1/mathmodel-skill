import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


class TestSchemas(unittest.TestCase):
    def test_project_state_example_validates(self):
        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        example = yaml.safe_load((ROOT / "state/project_state.example.yaml").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(example)), [])

    def test_v63_classification_is_supported(self):
        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        defs = schema["$defs"]
        self.assertIn("classification", defs)
        self.assertIn("objective", defs)
        self.assertIn("structure", defs)
        capabilities = defs["capabilities"]["properties"]
        self.assertIn("requires_out_of_sample_validation", capabilities)
        self.assertIn("requires_leakage_check", capabilities)

    def test_workbook_schema_has_independent_version_and_new_capabilities(self):
        schema = yaml.safe_load((ROOT / "core/workbook_schema.yaml").read_text(encoding="utf-8"))
        self.assertEqual(schema["schema_version"], "2.0.0")
        self.assertIn("skill_compatibility", schema)
        allowed = schema["capability_contract"]["allowed"]
        self.assertIn("requires_calibration_check", allowed)
        self.assertEqual(schema["matlab_handoff"]["field_resolution"]["method"], "exact_header_unique_match")

    def test_output_contract_defines_sync_and_framework_modes(self):
        contract = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(contract["version"], "6.3.0")
        self.assertEqual(contract["project_sync"]["script"], "scripts/sync_project.py")
        self.assertEqual(set(contract["model_paper_framework"]["modes"]), {"compact", "full"})
        self.assertEqual(contract["matlab_figure_contract"]["field_resolution"], "exact_header_unique_match")


if __name__ == "__main__":
    unittest.main()
