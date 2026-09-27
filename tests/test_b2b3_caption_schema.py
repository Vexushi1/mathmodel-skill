"""B2b3c caption-specific precision stays optional and bounded."""
from copy import deepcopy
from pathlib import Path
import unittest

import yaml
from jsonschema import Draft202012Validator

from tests.claim_schema_reference import previous_b2b3c_schema


ROOT = Path(__file__).resolve().parents[1]


class FigureCaptionProfileSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator({
            "$ref": "#/$defs/numeric_metric_entry", "$defs": cls.schema["$defs"],
        })

    def test_optional_precision_is_distinct_and_bounded(self):
        self.assertEqual(self.schema["version"], "8.10.0")
        base = {"id": "N1", "metric": "score", "display_form": "decimal", "unit": "ratio",
                "body_decimals": 2, "table_decimals": 4, "status": "current"}
        self.assertTrue(self.validator.is_valid(base))
        for decimals in (0, 3, 30):
            with self.subTest(decimals=decimals):
                self.assertTrue(self.validator.is_valid({**base, "figure_caption_decimals": decimals}))
        for decimals in (-1, 31, 2.5, True, None, "3"):
            with self.subTest(decimals=decimals):
                self.assertFalse(self.validator.is_valid({**base, "figure_caption_decimals": decimals}))
        self.assertEqual(base["body_decimals"], 2)
        self.assertEqual(base["table_decimals"], 4)

    def test_exact_predecessor_projection(self):
        previous = previous_b2b3c_schema(deepcopy(self.schema))
        self.assertEqual(previous["version"], "8.8.0")
        self.assertNotIn("figure_caption_decimals",
                         previous["$defs"]["numeric_metric_entry"]["properties"])

    def test_contract_keeps_text_gate_and_policy_pairs(self):
        contract = yaml.safe_load((ROOT / "core/claim_consumption_contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(contract["version"], "1.6.0")
        caption = contract["figure_caption_numeric_audit"]
        self.assertEqual(caption["precision_field"], "paper_framework.numeric_profile[].figure_caption_decimals")
        self.assertEqual(caption["read_only_report"], "figure_caption_numeric_checks")
        self.assertEqual(caption["formal_gate"],
                         "observation_only_for_legacy_policies_and_current_caption_numeric_consumed_by_1.3.0_gate")
        self.assertEqual(contract["formal_text_gate"]["activation"],
                         "explicit_enforce_latex_text_protocol_1.2.0_and_explicit_latex_or_submission_scope")
        self.assertEqual([(row["protocol_version"], row["mode"])
                          for row in contract["activation"]["supported_policies"]],
                         [("1.0.0", "observe"), ("1.1.0", "propagate"),
                          ("1.2.0", "enforce_latex_text"),
                          ("1.3.0", "enforce_latex_text_and_figure_chain")])


if __name__ == "__main__":
    unittest.main()
