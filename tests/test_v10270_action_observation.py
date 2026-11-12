"""G1B oracle semantics and observation safety; no real project writes."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v10270_action_observation as G1B

ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "tests/fixtures/v10270_action_oracle.yaml"


def sample_case():
    return {"id": "case", "request": "画图", "competition": "CUMCM",
            "category": "single_action",
            "positive_actions": [{"id": "draw", "intent": "figures"}],
            "negative_intents": ["latex"], "targets": ["结果图"]}


def sample_plan(intents=None, pause=None, gates=None):
    selected = ["figures"] if intents is None else intents
    return {"intents": selected, "pause_state": pause, "delivery_scope": "figures",
            "modules": ["modules/04_figure_evidence.md"],
            "terminal_outputs": ["approved_figures"],
            "missing_prerequisites": [],
            "pre_delivery_gates": [] if gates is None else gates,
            "assurance": {"status": "pass",
                          "intent_resolution": {"inferred_candidates": [
                              {"intent": "figures", "score": 2, "matched_keywords": ["画图"]}]}},
            "reading_plan": {"profile": "figure_design", "status": "planned", "metrics": {}}}


class G1BActionObservationTests(unittest.TestCase):
    def test_independently_authored_oracle_contains_multi_actions(self):
        cases = G1B.validate_cases(ORACLE)
        self.assertGreaterEqual(len(cases), 10)
        self.assertTrue(any(len(c["positive_actions"]) == 2 for c in cases))
        self.assertTrue(any(c["category"] == "historically_protected_carriers" for c in cases))
        self.assertTrue(any(c["category"] == "lifecycle" for c in cases))
        self.assertFalse(any("selected_intents" in c for c in cases))

    def test_missing_action_is_visible_not_called_dispatched(self):
        c = deepcopy(sample_case())
        c["positive_actions"].append({"id": "explain_in_latex", "intent": "latex"})
        c["negative_intents"] = []
        result = G1B.observed_actions(c, sample_plan())
        self.assertEqual(result["missing_action_count"], 1)
        missing = [x for x in result["actions"] if x["disposition"] == "missing_unjustified"]
        self.assertEqual(missing[0]["id"], "explain_in_latex")
        self.assertEqual(result["safety_conflicts"], [])

    def test_pause_is_deferred_not_execution_or_omission(self):
        c = sample_case()
        result = G1B.observed_actions(c, sample_plan(pause="awaiting_model_approval"))
        self.assertEqual(result["actions"][0]["disposition"], "explicitly_deferred_or_blocked")
        self.assertEqual(result["missing_action_count"], 0)

    def test_negative_intent_is_detected_independent_of_gate(self):
        c = sample_case()
        actual = G1B.observed_actions(c, sample_plan(intents=["figures", "latex"]))
        self.assertIn("forbidden_intent", {x["type"] for x in actual["safety_conflicts"]})

    def test_read_only_writer_gate_is_detected(self):
        c = sample_case()
        c["forbid_write_gates"] = True
        actual = G1B.observed_actions(c, sample_plan(gates=[{
            "name": "project_sync", "command": "python scripts/sync_project.py --write"}]))
        self.assertIn("write_capable_gate_in_read_only_plan",
                      {x["type"] for x in actual["safety_conflicts"]})

    def test_protected_carrier_is_not_auto_union(self):
        c = sample_case()
        c["positive_actions"] = [{"id": "carrier", "intent": "latex"}]
        c["negative_intents"] = []
        c["protected_assured_intents"] = ["latex"]
        before = G1B.observed_actions(c, sample_plan(intents=["latex"]))
        after = G1B.observed_actions(c, sample_plan(intents=["latex", "docx"]))
        self.assertEqual(before["safety_conflicts"], [])
        self.assertIn("protected_carrier_selection_changed",
                      {row["type"] for row in after["safety_conflicts"]})

    def test_execution_module_gate_is_not_replaced(self):
        c = sample_case()
        c["expected_pause_state"] = "awaiting_model_approval"
        c["forbid_execution_modules"] = ["modules/03_solve_validate.md"]
        p = sample_plan(pause=None)
        p["modules"].append("modules/03_solve_validate.md")
        conflicts = G1B.observed_actions(c, p)["safety_conflicts"]
        self.assertIn("execution_boundary_crossed", {x["type"] for x in conflicts})
        self.assertIn("unexpected_pause", {x["type"] for x in conflicts})

    def test_corpus_rejects_unknown_fields_and_duplicate_id(self):
        import yaml
        c = sample_case()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "oracle.yml"
            for cases in ([dict(c, observed_route=["figures"])], [c, deepcopy(c)]):
                p.write_text(yaml.safe_dump({
                    "schema_version": 1, "authored_basis": "human_independent_semantic_labels",
                    "cases": cases}, allow_unicode=True), encoding="utf-8")
                with self.assertRaises(ValueError):
                    G1B.validate_cases(p)

    def test_corpus_rejects_contradictory_positive_and_negative(self):
        import yaml
        c = sample_case()
        c["negative_intents"] = ["figures"]
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "oracle.yml"
            p.write_text(yaml.safe_dump({
                "schema_version": 1, "authored_basis": "human_independent_semantic_labels",
                "cases": [c]}, allow_unicode=True), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "positive and forbidden"):
                G1B.validate_cases(p)

    def test_timing_is_observation_not_full_user_latency(self):
        t = G1B.timed_summary([0.2, 0.1, 0.3])
        self.assertEqual(t["count"], 3)
        self.assertAlmostEqual(t["median_seconds"], 0.2)
        self.assertAlmostEqual(t["nearest_rank_p95_seconds"], 0.3)
        self.assertIn("small-N", t["note"])

    def test_sample_requires_selected_current_source(self):
        with self.assertRaisesRegex(ValueError, "uniquely selected"):
            G1B.read_first_chunk(ROOT, "a" * 40, "plan: empty", sample_plan(),
                                 "core/not_selected.yaml")

    def test_observations_do_not_elevate_gate_or_token_status(self):
        x = G1B.observed_actions(sample_case(), sample_plan())
        self.assertEqual(x["ordered_gate_names"], [])
        self.assertNotIn("gate_pass_granted", x)
        self.assertFalse(x["safety_conflicts"])


if __name__ == "__main__":
    unittest.main()
