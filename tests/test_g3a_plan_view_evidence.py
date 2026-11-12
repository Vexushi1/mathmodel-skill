"""G3A: compact presentation experiment must preserve current source/Gate pointers."""
from __future__ import annotations

from copy import deepcopy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g3a_plan_view_evidence as VIEW

ROOT = Path(__file__).resolve().parents[1]


def sample_plan():
    return {
        "version": "10.27.0", "intents": ["figures", "latex"],
        "modules": ["modules/04_figure_evidence.md", "modules/05_writing/latex.md"],
        "pause_state": None, "delivery_scope": "latex",
        "missing_prerequisites": ["accepted_result"],
        "terminal_outputs": ["figure_contract", "latex_source"],
        "assurance": {
            "status": "pass",
            "context": {"conflicts": [], "ambiguities": [], "question": "Q2"},
            "artifact_assurance": {"evidence": [{"artifact": "accepted_solution_workbook",
                                                 "status": "missing"}]},
            "authority_fingerprint": {"sha256": "a"*64},
        },
        "reading_plan": {
            "profile": "full", "status": "conservative_fallback",
            "reasons": ["mixed intents"],
            "read_now": [
                {"path": "core/source.md", "origin": "skill", "sha256": "b"*64,
                 "ranges": [[1, 20]], "selectors": {"headings": ["# A"]},
                 "when": None, "planned_bytes": 142}],
            "conditional": [
                {"path": "core/conditional.yaml", "origin": "skill",
                 "sha256": "c"*64, "ranges": [[5, 10]],
                 "selectors": {"yaml_paths": ["rule"]},
                 "when": "current_judgment_needs_evidence"}],
            "tool_interfaces": [{"name": "project_sync", "path": "scripts/sync_project.py"}],
        },
        "pre_delivery_gates": [
            {"name": "semantic_governance", "path": "scripts/validate_semantic_governance.py",
             "command": "python scripts/validate_semantic_governance.py --check"},
            {"name": "project_sync", "path": "scripts/sync_project.py",
             "command": "python scripts/sync_project.py --check"},
        ],
    }


class G3APlanPresentationTests(unittest.TestCase):
    def test_source_row_and_all_gates_preserved_exactly(self):
        source = sample_plan()
        pristine = deepcopy(source)
        view = VIEW.preview_from_plan(source, "d"*64)
        VIEW.prove_presentation_subset(source, view)
        self.assertEqual(source, pristine)
        self.assertEqual(len(view["pre_delivery_gates"]), 2)
        self.assertEqual(view["read"]["read_now"][0]["ranges"], [[1, 20]])
        self.assertEqual(view["read"]["conditional"][0]["when"], "current_judgment_needs_evidence")
        self.assertEqual(view["assurance"]["artifact_evidence"][0]["status"], "missing")
        self.assertFalse(view["status_boundaries"]["gate_executed_or_passed"])

    def test_candidate_cannot_hide_missing_read_row_or_gate(self):
        source = sample_plan()
        for mutator in (
            lambda view: view["read"]["read_now"].clear(),
            lambda view: view["read"]["conditional"].clear(),
            lambda view: view["pre_delivery_gates"].pop(),
            lambda view: view["tool_interfaces"].clear(),
            lambda view: view["status_boundaries"].update(gate_executed_or_passed=True),
            lambda view: view["selected_intents"].pop(),
        ):
            with self.subTest(mutator=str(mutator)):
                view = VIEW.preview_from_plan(source, "d"*64)
                mutator(view)
                with self.assertRaises(ValueError):
                    VIEW.prove_presentation_subset(source, view)

    def test_incomplete_or_invalid_machine_plan_rejected(self):
        with self.assertRaisesRegex(ValueError, "machine plan"):
            VIEW.preview_from_plan({}, "d"*64)
        source = sample_plan()
        source["reading_plan"]["read_now"][0].pop("ranges")
        with self.assertRaisesRegex(ValueError, "ranges"):
            VIEW.preview_from_plan(source, "d"*64)

    def test_comparison_uses_same_json_format(self):
        source = sample_plan()
        raw = VIEW.encoded(source)
        view = VIEW.encoded(VIEW.preview_from_plan(source, "e"*64))
        self.assertTrue(raw.startswith(b"{"))
        self.assertTrue(view.startswith(b"{"))
        self.assertIsInstance(len(view), int)

    def test_case_sources_are_prior_independent_synthetic_corpora(self):
        rows = VIEW.cases_from_existing(ROOT)
        self.assertGreaterEqual(len(rows), 20)
        self.assertEqual(len({row["id"] for row in rows}), len(rows))
        self.assertTrue(any("g1b::independent_figure_and_latex" == x["id"] for x in rows))
        self.assertTrue(all("request" in x and "intents" in x for x in rows))

    def test_candidate_remains_non_executable_even_with_full_gates(self):
        source = sample_plan()
        view = VIEW.preview_from_plan(source, "d"*64)
        self.assertTrue(view["status_boundaries"]["not_a_replacement_for_machine_plan"])
        self.assertFalse(view["status_boundaries"]["source_text_returned"])
        self.assertFalse(view["status_boundaries"]["approved_or_accepted_artifact"])
        self.assertEqual(view["assurance"]["status"], "pass")
        self.assertEqual(view["pre_delivery_gates"][0]["name"], "semantic_governance")


if __name__ == "__main__":
    unittest.main()
