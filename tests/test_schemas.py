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

    def test_v631_classification_has_single_capability_source(self):
        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        defs = schema["$defs"]
        self.assertEqual(schema["version"], "6.3.1")
        self.assertEqual(set(defs["classification"]["required"]), {"objective", "structures"})
        sub_required = set(schema["properties"]["subproblems"]["additionalProperties"]["required"])
        self.assertIn("capabilities", sub_required)
        self.assertIn("capabilities", defs["classification"]["properties"])
        self.assertIn("artifact_hashes", defs)

    def test_workbook_schema_has_three_axis_profiles(self):
        schema = yaml.safe_load((ROOT / "core/workbook_schema.yaml").read_text(encoding="utf-8"))
        self.assertEqual(schema["schema_version"], "2.1.0")
        self.assertIn(">=6.3.1", schema["skill_compatibility"])
        self.assertEqual(schema["classification_contract"]["capabilities_source"], "subproblem.capabilities")
        self.assertIn("objective_profiles", schema["solution_workbook"])
        self.assertIn("structure_profiles", schema["solution_workbook"])
        self.assertEqual(schema["solution_workbook"]["task_profiles"]["status"], "deprecated_compatibility_only")
        self.assertEqual(schema["matlab_handoff"]["field_resolution"]["method"], "exact_header_unique_match")

    def test_output_contract_defines_stage_sync_and_framework_modes(self):
        contract = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(contract["version"], "6.3.1")
        self.assertEqual(contract["project_sync"]["role"], "formal_pre_delivery_gate")
        self.assertEqual(set(contract["model_paper_framework"]["modes"]), {"compact", "full"})
        self.assertEqual(contract["classification_contract"]["authoritative_locations"]["capabilities"], "subproblem.capabilities")
        self.assertEqual(
            set(contract["project_sync"]["artifact_hash_layers"]),
            {"data", "model", "solution_workbook", "robustness_workbook", "matlab_script", "figure_bundle", "framework"},
        )
        self.assertEqual(contract["matlab_figure_contract"]["field_resolution"], "exact_header_unique_match")


if __name__ == "__main__":
    unittest.main()
