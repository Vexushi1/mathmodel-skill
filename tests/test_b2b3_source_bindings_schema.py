"""B2b3b typed Figure source declarations and bounded B1 evidence references."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_project_state as state_validator
from tests.claim_fixture import source
from tests.test_b2b3_figure_bindings_schema import framework


def with_sources():
    state = framework()
    state["claim_consumption_policy"]["figure_bindings"][0]["source_bindings"] = [
        {"source_id": "baseline", "sheet": "measurements", "required_headers": ["metric", "value"]},
        {"source_id": "candidate", "sheet": "measurements", "required_headers": ["metric", "scenario"]},
    ]
    return state


class FigureSourceBindingsSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        cls.schema = schema
        cls.validator = Draft202012Validator({
            "$ref": "#/$defs/claim_consumption_policy", "$defs": schema["$defs"],
        })

    def test_opt_in_typed_rows_keep_older_figures_and_policy_pairs_valid(self):
        self.assertEqual(self.schema["version"], "8.8.0")
        base = with_sources()["claim_consumption_policy"]
        for version, mode in (("1.0.0", "observe"), ("1.1.0", "propagate"),
                              ("1.2.0", "enforce_latex_text")):
            with self.subTest(version=version):
                policy = {**base, "protocol_version": version, "mode": mode}
                self.assertTrue(self.validator.is_valid(policy))
                old = deepcopy(policy)
                old["figure_bindings"][0].pop("source_bindings")
                self.assertTrue(self.validator.is_valid(old))
        self.assertEqual(state_validator._validate_claim_consumption_policy(with_sources()), [])
        self.assertEqual(state_validator._validate_claim_consumption_policy(framework()), [])

    def test_source_rows_are_closed_bounded_and_exact_literal_headers(self):
        base = with_sources()["claim_consumption_policy"]
        row = base["figure_bindings"][0]
        for invalid in (None, [], [row["source_bindings"][0]] * 9,
                        [{**row["source_bindings"][0], "approved": True}],
                        [{"source_id": "baseline", "sheet": "measurements"}],
                        [{**row["source_bindings"][0], "source_id": "bad:id"}],
                        [{**row["source_bindings"][0], "sheet": "  "}],
                        [{**row["source_bindings"][0], "sheet": " measurements"}],
                        [{**row["source_bindings"][0], "sheet": "measure\nments"}],
                        [{**row["source_bindings"][0], "required_headers": []}],
                        [{**row["source_bindings"][0], "required_headers": ["metric"] * 2}],
                        [{**row["source_bindings"][0], "required_headers": ["metric"] * 65}],
                        [{**row["source_bindings"][0], "required_headers": [" "]}],
                        [{**row["source_bindings"][0], "required_headers": ["met\x00ric"]}]):
            with self.subTest(invalid=invalid):
                policy = {**base, "figure_bindings": [{**row, "source_bindings": invalid}]}
                self.assertFalse(self.validator.is_valid(policy))
        # Header spaces are preserved as literal workbook header characters.
        spaced = deepcopy(base)
        spaced["figure_bindings"][0]["source_bindings"][0]["required_headers"] = [" metric "]
        self.assertTrue(self.validator.is_valid(spaced))

    def test_source_ids_follow_linked_claims_transitive_derivation_graph(self):
        good = with_sources()
        self.assertEqual(state_validator._validate_claim_consumption_policy(good), [])
        cases = (
            (lambda item: item["claim_consumption_policy"]["figure_bindings"][0]["source_bindings"].append(
                deepcopy(item["claim_consumption_policy"]["figure_bindings"][0]["source_bindings"][0])),
             "duplicates a source"),
            (lambda item: item["claim_consumption_policy"]["figure_bindings"][0]["source_bindings"][0].update(
                source_id="missing"), "unknown B1 source"),
            (lambda item: item["claim_consumption_policy"]["figure_bindings"][0]["source_bindings"][0].update(
                sheet="other"), "differs from B1 source.selector.sheet"),
            (lambda item: item["claim_evidence"]["sources"].append(source("unlinked", "extra")) or
                item["claim_consumption_policy"]["figure_bindings"][0]["source_bindings"][0].update(
                    source_id="unlinked"), "outside linked claim source evidence"),
            (lambda item: item["claim_evidence"]["sources"][0].update(question="Q2"),
             "question conflicts with Figure claim scope"),
            (lambda item: item["claim_evidence"]["derivations"][0]["inputs"].update(
                baseline="source:missing"), "dangling B1 source reference"),
            (lambda item: item["claim_evidence"]["claims"][0]["evidence"][0].update(
                ref="derivation:missing"), "dangling B1 derivation reference"),
            (lambda item: item["claim_evidence"]["claims"][0]["evidence"][0].update(
                relation="contradicts"), "outside linked claim source evidence"),
            (lambda item: item["claim_evidence"]["sources"].append(
                deepcopy(item["claim_evidence"]["sources"][0])), "unique B1 source and derivation IDs"),
            (lambda item: item["claim_evidence"]["derivations"].append(
                deepcopy(item["claim_evidence"]["derivations"][0])), "unique B1 source and derivation IDs"),
        )
        for change, marker in cases:
            with self.subTest(marker=marker):
                state = deepcopy(good)
                change(state)
                issues = state_validator._validate_claim_consumption_policy(state)
                self.assertTrue(any(marker in issue for issue in issues), issues)

    def test_question_scope_and_full_project_state(self):
        state = with_sources()
        state["paper_fragments"][0]["scope"] = "global"
        self.assertEqual(state_validator._validate_claim_consumption_policy(state), [])
        state["claim_evidence"]["claims"][0]["scope"] = "project"
        self.assertTrue(any("question conflicts" in issue for issue in
                            state_validator._validate_claim_consumption_policy(state)))
        project = yaml.safe_load((ROOT / "state/project_state.example.yaml").read_text(encoding="utf-8"))
        project["paper_framework"].update(with_sources())
        self.assertEqual(state_validator.validate_state_payload(project, project_root=ROOT), [])


if __name__ == "__main__":
    unittest.main()
