"""B2b3a Figure identity declarations: closed shape and claim/fragment references only."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_project_state as state_validator
from tests.claim_fixture import record


def framework():
    return {
        "claim_evidence": record(),
        "claim_consumption_policy": {
            "protocol_version": "1.0.0", "mode": "observe",
            "required_consumptions": [
                {"claim_id": "gain_claim", "fragment_kinds": ["figure_or_table_claim"]},
            ],
            "figure_bindings": [
                {"figure_id": "Q1_F01", "fragment_id": "paper.figure.q1",
                 "latex_label": "fig:q1-cost", "image_path": "figures/Q1_F01.png"},
            ],
        },
        "paper_fragments": [
            {"id": "paper.figure.q1", "kind": "figure_or_table_claim", "scope": "Q1",
             "depends_on": ["claim:gain_claim"], "anchor": "cost", "status": "current"},
        ],
    }


class FigureBindingsSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        cls.schema = schema
        cls.validator = Draft202012Validator({
            "$ref": "#/$defs/claim_consumption_policy", "$defs": schema["$defs"],
        })

    def test_optional_closed_identity_rows_preserve_existing_policy_modes(self):
        self.assertEqual(self.schema["version"], "8.7.0")
        base = framework()["claim_consumption_policy"]
        for version, mode in (("1.0.0", "observe"), ("1.1.0", "propagate"),
                              ("1.2.0", "enforce_latex_text")):
            with self.subTest(version=version):
                policy = {**base, "protocol_version": version, "mode": mode}
                self.assertTrue(self.validator.is_valid(policy))
                self.assertTrue(self.validator.is_valid({key: value for key, value in policy.items()
                                                         if key != "figure_bindings"}))
        self.assertFalse(self.validator.is_valid({**base, "mode": "propagate"}))
        self.assertFalse(self.validator.is_valid({**base, "figure_bindings": [
            {**base["figure_bindings"][0], "approved": True}]}))
        self.assertFalse(self.validator.is_valid({**base, "figure_bindings": [
            {"figure_id": "Q1_F01", "fragment_id": "paper.figure.q1", "image_path": "figures/Q1_F01.png"}]}))
        self.assertFalse(self.validator.is_valid({**base, "figure_bindings": base["figure_bindings"] * 129}))

    def test_literal_ids_labels_and_normalized_figure_paths(self):
        base = framework()["claim_consumption_policy"]
        row = base["figure_bindings"][0]
        for key, invalid in (
            ("figure_id", ""), ("figure_id", "  "), ("figure_id", "Q1|F01"),
            ("figure_id", "Q1`F01"), ("figure_id", "Q1\nF01"), ("figure_id", "F" * 129),
            ("fragment_id", "q1.figure"), ("latex_label", "fig:{q1}"),
            ("latex_label", "\\label{fig:q1}"), ("latex_label", "fig:q1 cost"),
            ("image_path", "../figures/Q1_F01.png"),
            ("image_path", "figures/../Q1_F01.png"),
            ("image_path", "问题一求解/./Q1_F01.png"),
            ("image_path", "figures//Q1_F01.png"),
            ("image_path", "/figures/Q1_F01.png"),
            ("image_path", "C:/figures/Q1_F01.png"),
            ("image_path", "figures\\Q1_F01.png"),
            ("image_path", "问题一求解/Q1\x00F01.png"),
            ("image_path", "问题一求解/Q1\x7fF01.png"),
            ("image_path", "figures/Q1_F01.jpg"),
            ("image_path", "figures/Q1_F01.PNG"),
        ):
            with self.subTest(key=key, invalid=invalid):
                changed = {**base, "figure_bindings": [{**row, key: invalid}]}
                self.assertFalse(self.validator.is_valid(changed))
                if key == "image_path":
                    state = framework()
                    state["claim_consumption_policy"] = changed
                    self.assertTrue(any("normalized project-relative" in issue for issue in
                                        state_validator._validate_claim_consumption_policy(state)))
        for path in ("figures/Q1_F01.pdf", "figures/panels/Q1_F01.svg",
                     "问题一求解/当前图.pdf", "图一.png"):
            policy = {**base, "figure_bindings": [{**row, "image_path": path}]}
            self.assertTrue(self.validator.is_valid(policy))
            state = framework()
            state["claim_consumption_policy"] = policy
            self.assertEqual(state_validator._validate_claim_consumption_policy(state), [])

    def test_bound_fragment_requires_registered_current_figure_claim_obligation(self):
        good = framework()
        self.assertEqual(state_validator._validate_claim_consumption_policy(good), [])
        cases = (
            (lambda item: item["paper_fragments"][0].update(id="paper.other"), "unknown paper fragment"),
            (lambda item: item["paper_fragments"][0].update(kind="question_result_text"),
             "figure_or_table_claim fragment"),
            (lambda item: item["paper_fragments"][0].update(status="stale"), "current fragment"),
            (lambda item: item["paper_fragments"][0].update(depends_on=[]), "Figure obligation edge"),
            (lambda item: item["paper_fragments"][0].update(depends_on=["claim:unknown"]),
             "Figure obligation edge"),
            (lambda item: item["claim_consumption_policy"]["required_consumptions"][0].update(
                fragment_kinds=["abstract_claim"]), "Figure obligation edge"),
        )
        for change, marker in cases:
            with self.subTest(marker=marker):
                item = deepcopy(good)
                change(item)
                self.assertTrue(any(marker in issue for issue in
                                    state_validator._validate_claim_consumption_policy(item)))

    def test_each_of_four_identity_keys_is_unique_without_file_approval(self):
        base = framework()
        first = base["claim_consumption_policy"]["figure_bindings"][0]
        for key in ("figure_id", "fragment_id", "latex_label", "image_path"):
            with self.subTest(key=key):
                item = deepcopy(base)
                second = {"figure_id": "Q1_F02", "fragment_id": "paper.figure.q2",
                          "latex_label": "fig:q1-alt", "image_path": "figures/missing_image.svg"}
                second[key] = first[key]
                item["claim_consumption_policy"]["figure_bindings"].append(second)
                self.assertTrue(any(f".{key} duplicates" in issue for issue in
                                    state_validator._validate_claim_consumption_policy(item)))
        # A declaration is valid even before an image exists; approval belongs to the live audit.
        self.assertEqual(state_validator._validate_claim_consumption_policy(base), [])

    def test_missing_policy_and_malformed_opt_in_fail_closed(self):
        state = framework()
        state.pop("claim_consumption_policy")
        self.assertEqual(state_validator._validate_claim_consumption_policy(state), [])
        state = framework()
        state["claim_consumption_policy"]["figure_bindings"] = None
        self.assertTrue(any("must be an array" in issue for issue in
                            state_validator._validate_claim_consumption_policy(state)))
        state["claim_consumption_policy"]["figure_bindings"] = [{"figure_id": "Q1_F01"}]
        self.assertTrue(state_validator._validate_claim_consumption_policy(state))
        self.assertFalse(self.validator.is_valid(state["claim_consumption_policy"]))

    def test_project_state_accepts_identity_before_image_exists(self):
        state = yaml.safe_load((ROOT / "state/project_state.example.yaml").read_text(encoding="utf-8"))
        state["paper_framework"].update(framework())
        state["paper_framework"]["claim_consumption_policy"]["figure_bindings"][0][
            "image_path"] = "问题一求解/当前图.pdf"
        self.assertEqual(state_validator.validate_state_payload(state, project_root=ROOT), [])
        state["paper_framework"]["paper_fragments"][0]["status"] = "stale"
        self.assertTrue(any("requires a current fragment" in issue for issue in
                            state_validator.validate_state_payload(state, project_root=ROOT)))


if __name__ == "__main__":
    unittest.main()
