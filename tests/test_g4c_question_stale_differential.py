"""G4-C admission only: exact question-level stale closure parity across consumers.

These tests deliberately do not replace or modify the production stale writers.
They also preserve the distinct, stricter claim-reference semantics and the
project-backend migration consumer of sync_project's compatibility entrypoint.
"""
from __future__ import annotations

from copy import deepcopy
import inspect
import random
import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import sync_project as SYNC
import validate_semantic_governance as SEMANTIC
import state_transitions as TRANSITIONS
import project_solver_backend as BACKEND


def fragment(fid: str, scope: str = "global", deps: Any = None,
             status: str = "current") -> dict[str, Any]:
    return {
        "id": fid, "kind": "paper_section", "scope": scope,
        "depends_on": [] if deps is None else deps, "anchor": fid,
        "status": status,
    }


def observation(fn: Any, fragments: Any, questions: set[str]) -> dict[str, Any]:
    payload = {
        "paper_fragments": deepcopy(fragments),
        "unrelated": {"locked_model_hash": "not_a_result_or_approval"},
    }
    before = deepcopy(payload["unrelated"])
    try:
        value = fn(payload, set(questions))
        result: dict[str, Any] = {
            "ok": True, "returned_ids": value, "error": None,
        }
    except Exception as exc:  # noqa: BLE001 - compare historical failure behavior.
        result = {
            "ok": False, "returned_ids": None,
            "error": (type(exc).__name__, str(exc)),
        }
    result["framework"] = payload
    result["unrelated_untouched"] = payload["unrelated"] == before
    return result


class G4CQuestionFragmentDifferentialTests(unittest.TestCase):
    def assert_equivalent(self, label: str, fragments: Any, questions: set[str],
                          expected: list[str] | None = None) -> None:
        before = deepcopy(fragments)
        a = observation(SYNC._mark_paper_fragments_stale, fragments, questions)
        b = observation(SEMANTIC._mark_paper_fragments_stale, fragments, questions)
        self.assertEqual(a, b, msg=f"question stale consumer drift: {label}")
        self.assertEqual(fragments, before, msg=f"probe mutated its inputs: {label}")
        self.assertTrue(a["unrelated_untouched"])
        if expected is not None:
            self.assertTrue(a["ok"], msg=f"unexpected error: {a['error']}")
            self.assertEqual(a["returned_ids"], expected, msg=label)

    def test_exact_question_tokens_and_prefix_boundary(self):
        deps = [
            fragment("paper.q1.scope", "Q1"),
            fragment("paper.q10.scope", "Q10"),
            fragment("paper.q1.dot", deps=["Q1.model"]),
            fragment("paper.q1.colon", deps=["Q1:result"]),
            fragment("paper.q1.exact", deps=["Q1"]),
            fragment("paper.other", deps=["Q10.parameter"]),
        ]
        self.assert_equivalent(
            "no Q1 -> Q10 collision", deps, {"Q1"},
            ["paper.q1.colon", "paper.q1.dot", "paper.q1.exact", "paper.q1.scope"],
        )
        for token, expected in [
            ("Q1", True), ("Q1.model", True), ("Q1:result", True),
            ("Q10", False), ("Q1x", False), ("Q1_model", False),
        ]:
            with self.subTest(token=token):
                self.assertEqual(SYNC._dependency_hits_question(token, "Q1"), expected)
                self.assertEqual(SEMANTIC._dependency_hits_question(token, "Q1"), expected)

    def test_transitive_cross_question_and_cycle_boundaries(self):
        cases = [
            ("transitive", [
                fragment("paper.q2.result", "Q2"),
                fragment("paper.abstract", deps=["paper.q2.result"]),
                fragment("paper.title", deps=["paper.abstract"]),
                fragment("paper.q1", "Q1"),
            ], {"Q2"}, ["paper.abstract", "paper.q2.result", "paper.title"]),
            ("seeded_cycle", [
                fragment("paper.a", "Q1", ["paper.b"]),
                fragment("paper.b", "global", ["paper.a"]),
            ], {"Q1"}, ["paper.a", "paper.b"]),
            ("unseeded_cycle", [
                fragment("paper.a", "global", ["paper.b"]),
                fragment("paper.b", "global", ["paper.a"]),
            ], {"Q2"}, []),
            ("multiple_questions", [
                fragment("paper.a", "Q1"),
                fragment("paper.b", "Q2"),
                fragment("paper.c", "global", ["paper.a", "paper.b"]),
                fragment("paper.d", "Q3"),
            ], {"Q1", "Q2"}, ["paper.a", "paper.b", "paper.c"]),
            ("claim_is_not_question", [
                fragment("paper.a", "global", ["claim:aux_analysis"]),
                fragment("paper.b", "global", ["paper.a"]),
            ], {"Q1"}, []),
            ("unknown_paper_reference_without_seed", [
                fragment("paper.a", "global", ["paper.unknown"]),
            ], {"Q1"}, []),
            ("already_stale", [
                fragment("paper.a", "Q1", status="stale"),
                fragment("paper.b", "global", ["paper.a"], status="not_applicable"),
            ], {"Q1"}, ["paper.a", "paper.b"]),
            ("empty_affected", [
                fragment("paper.a", "Q1"),
            ], set(), []),
        ]
        for label, fragments, questions, expected in cases:
            with self.subTest(case=label):
                self.assert_equivalent(label, fragments, questions, expected)

    def test_historical_malformed_inputs_have_identical_errors_and_side_effects(self):
        cases = [
            ("absent_fragments", None),
            ("not_list", {"unexpected": "mapping"}),
            ("non_mapping_items", ["not-a-dict", None, 3]),
            ("duplicate_id_last_wins", [
                fragment("paper.same", "Q1"),
                fragment("paper.same", "Q2"),
            ]),
            ("noniterable_dependencies", [
                fragment("paper.a", "Q1", 42),
            ]),
            ("dependency_object_string_cast", [
                fragment("paper.a", "Q1", [{"suspicious": "dependency"}]),
            ]),
            ("missing_id", [
                {"scope": "Q1", "depends_on": ["Q1"], "status": "current"},
            ]),
        ]
        for label, value in cases:
            with self.subTest(case=label):
                self.assert_equivalent(label, value, {"Q1"})

    def test_unaffected_fragment_status_and_metadata_are_preserved(self):
        fragments = [
            fragment("paper.q1", "Q1", status="current"),
            fragment("paper.q2", "Q2", status="not_applicable"),
            fragment("paper.q3", "Q3", status="stale"),
        ]
        for fn in (SYNC._mark_paper_fragments_stale,
                   SEMANTIC._mark_paper_fragments_stale):
            with self.subTest(writer=fn.__module__):
                output = observation(fn, fragments, {"Q1"})
                self.assertEqual(output["returned_ids"], ["paper.q1"])
                self.assertEqual(
                    [f["status"] for f in output["framework"]["paper_fragments"]],
                    ["stale", "not_applicable", "stale"],
                )
                self.assertTrue(output["unrelated_untouched"])

    def test_seeded_graph_matrix_differential(self):
        rng = random.Random(20261113)
        for trial in range(35):
            nodes = []
            for index in range(15):
                fid = f"paper.g{index}"
                candidate = [f"paper.g{j}" for j in range(15) if j != index]
                dependencies = rng.sample(candidate, k=rng.randrange(0, 4))
                if rng.randrange(4) == 0:
                    dependencies.append(f"Q{rng.randrange(1, 5)}.result")
                nodes.append(fragment(
                    fid, f"Q{rng.randrange(1, 5)}" if rng.randrange(4) == 0 else "global",
                    dependencies, rng.choice(["current", "stale", "not_applicable"]),
                ))
            selected = {f"Q{rng.randrange(1, 5)}"}
            self.assert_equivalent(f"graph_trial_{trial}", nodes, selected)

    def test_claim_closure_is_not_interchangeable_with_question_stale(self):
        fragments = [fragment("paper.a", "Q1", ["Q1.result", "paper.unknown"])]
        self.assert_equivalent("legacy_question_semantics", fragments, {"Q1"}, ["paper.a"])
        with self.assertRaisesRegex(ValueError, "unknown paper fragment"):
            TRANSITIONS.claim_fragment_stale_closure(fragments, {"X"})

    def test_backend_migration_and_static_lint_entrypoints_remain_present(self):
        # project_solver_backend imports SYNC._mark_paper_fragments_stale inside
        # _retirement_candidate. Renaming/removing this callable breaks previews.
        self.assertTrue(callable(SYNC._mark_paper_fragments_stale))
        self.assertTrue(callable(SEMANTIC._mark_paper_fragments_stale))
        self.assertIn(
            "from sync_project import _mark_paper_fragments_stale",
            inspect.getsource(BACKEND._retirement_candidate),
        )
        self.assert_equivalent(
            "backend_compatibility_surface",
            [fragment("paper.q1", "Q1")], {"Q1"}, ["paper.q1"],
        )


if __name__ == "__main__":
    unittest.main()
