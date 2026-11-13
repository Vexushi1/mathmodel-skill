"""G6-A admission controls: blocker evidence never grants a narrow runtime action."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import g6a_blocked_diagnostic_probe as G6A


def minimal_plan(*, intent="full_solution", pause=None, approval_pause=False,
                 assurance="pass", reading_status="full",
                 reasons=(), profile="full", project_loaded=False):
    return {
        "intents": [intent],
        "pause_state": pause, "pause_for_model_approval": approval_pause,
        "assurance": {"status": assurance, "context": {
            "project_state_loaded": project_loaded}},
        "reading_plan": {
            "profile": profile, "status": reading_status,
            "reasons": list(reasons), "read_now": [],
            "metrics": {"planned_skill_read_bytes": 0}},
        "pre_delivery_gates": [],
    }


class G6ABlockedDiagnosticAdmissionTests(unittest.TestCase):
    def test_only_authority_established_model_pause_counts(self):
        p = minimal_plan(pause="awaiting_model_approval", approval_pause=True)
        yes, reason, source = G6A.diagnostic_guard("model_approval_pending", p)
        self.assertTrue(yes)
        self.assertEqual(source, G6A.MODEL_APPROVAL_AUTHORITY)
        self.assertIn("primary_code", reason)
        for change in (
            {"pause_state": None},
            {"pause_for_model_approval": False},
            {"assurance": {"status": "review_required"}},
            {"intents": ["latex"]},
        ):
            with self.subTest(change=change):
                candidate = deepcopy(p)
                candidate.update(change)
                self.assertFalse(
                    G6A.diagnostic_guard("model_approval_pending", candidate)[0])

    def test_figure_guard_requires_current_evidence_and_single_style_action(self):
        p = minimal_plan(
            intent="figures", reading_status="evidence_required",
            reasons=["current figure approval is absent"],
            profile="full", project_loaded=True,
        )
        eligible, _, source = G6A.diagnostic_guard("old_figure_approval_missing", p)
        self.assertTrue(eligible)
        self.assertEqual(source, G6A.FIGURE_AUTHORITY)
        for change in (
            {"intents": ["figures", "latex"]},
            {"assurance": {"status": "review_required"}},
            {"reading_plan": {**p["reading_plan"], "status": "planned"}},
            {"reading_plan": {**p["reading_plan"], "reasons": []}},
        ):
            with self.subTest(change=change):
                candidate = deepcopy(p)
                candidate.update(change)
                self.assertFalse(G6A.diagnostic_guard(
                    "old_figure_approval_missing", candidate)[0])
        self.assertFalse(G6A.diagnostic_guard("mixed_old_figure_and_new_design", p)[0])
        self.assertFalse(G6A.diagnostic_guard("figure_semantic_change", p)[0])

    def test_missing_or_mismatched_authority_cannot_be_eligible(self):
        p = minimal_plan(pause="awaiting_model_approval", approval_pause=True)
        observation = G6A.observe("model_approval_pending", p, ROOT, "a" * 40)
        self.assertFalse(observation["diagnostic_scope_guard_observed"])
        self.assertEqual(observation["guard_reason"],
                         "diagnostic_authority_not_uniquely_in_current_read_now")
        self.assertEqual(observation["preview_candidate_bytes"], 0)
        self.assertFalse(observation["diagnostic_scope_admitted_to_production"])
        self.assertFalse(observation["gate_execution"])

    def test_planned_source_identity_hash_is_necessary_not_an_approval(self):
        bad = {
            "path": G6A.MODEL_APPROVAL_AUTHORITY, "origin": "skill",
            "sha256": "0" * 64, "ranges": [[1, 2]], "planned_bytes": 3,
        }
        with self.assertRaisesRegex(ValueError, "drift"):
            G6A.safe_origin_identity(ROOT, "a" * 40, [bad])
        for mutation in (
            {"origin": "project"},
            {"path": "../escape.yaml"},
            {"planned_bytes": -1},
            {"ranges": None},
        ):
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    G6A.safe_origin_identity(ROOT, "a" * 40, [{**bad, **mutation}])

    def test_real_synthetic_cases_and_no_production_shortcut(self):
        report = G6A.collect(ROOT)
        self.assertEqual(len(report["cases"]), 6)
        self.assertFalse(report["production_runtime_changed"])
        result = {c["case_id"]: c for c in report["cases"]}
        self.assertTrue(result["model_approval_pending"]["diagnostic_scope_guard_observed"])
        self.assertTrue(result["old_figure_approval_missing"]["diagnostic_scope_guard_observed"])
        for name in (
            "old_figure_current", "old_figure_source_drift",
            "figure_semantic_change", "mixed_old_figure_and_new_design",
        ):
            self.assertFalse(result[name]["diagnostic_scope_guard_observed"], msg=name)
        for case in result.values():
            self.assertFalse(case["diagnostic_scope_admitted_to_production"])
            self.assertFalse(case["gate_execution"])
            self.assertFalse(case["stage_execution"])
            self.assertFalse(case["current_project_write"])
            self.assertTrue(case["complete_action_reading_preserved"])
            if case["diagnostic_scope_guard_observed"]:
                self.assertTrue(case["candidate_source_identity"])
                self.assertLessEqual(
                    case["preview_candidate_bytes"],
                    case["original_planned_skill_bytes"])

    def test_foreign_root_and_report_scope_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "candidate worktree"):
                G6A.collect(Path(tmp))


if __name__ == "__main__":
    unittest.main()
