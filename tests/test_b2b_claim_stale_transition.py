from __future__ import annotations

import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from state_transitions import claim_fragment_stale_closure  # noqa: E402


def fragment(fragment_id: str, *dependencies: str) -> dict:
    return {"id": fragment_id, "depends_on": list(dependencies), "status": "current"}


class ClaimFragmentStaleClosureTests(unittest.TestCase):
    def test_b12_auxiliary_disposition_reaches_only_linked_fragments(self):
        fragments = [
            fragment("paper.core", "claim:core_answer", "Q1.result_summary"),
            fragment("paper.abstract", "paper.core"),
            fragment("paper.aux", "claim:aux_analysis"),
            fragment("paper.aux.table", "paper.aux"),
            fragment("paper.background"),
        ]
        original = deepcopy(fragments)
        self.assertEqual(
            claim_fragment_stale_closure(fragments, {"aux_analysis"}),
            ["paper.aux", "paper.aux.table"],
        )
        self.assertEqual(fragments, original)
        self.assertTrue(all(row["status"] == "current" for row in fragments))

    def test_fragment_fanout_and_cycle_are_deterministic_and_bounded(self):
        fragments = [
            fragment("paper.z", "paper.root"),
            fragment("paper.root", "claim:changed", "paper.loop"),
            fragment("paper.loop", "paper.z"),
            fragment("paper.a", "paper.root"),
            fragment("paper.other", "claim:unchanged"),
        ]
        expected = ["paper.a", "paper.loop", "paper.root", "paper.z"]
        self.assertEqual(claim_fragment_stale_closure(fragments, ["changed"]), expected)
        self.assertEqual(claim_fragment_stale_closure(list(reversed(fragments)), ["changed"]), expected)

    def test_no_exact_claim_match_does_not_stale_legacy_question_dependencies(self):
        fragments = [
            fragment("paper.q1", "Q1.result_summary"),
            fragment("paper.q2", "claim:changed_extra"),
            fragment("paper.abstract", "paper.q1"),
        ]
        self.assertEqual(claim_fragment_stale_closure(fragments, ["changed"]), [])
        self.assertEqual(claim_fragment_stale_closure(fragments, []), [])

    def test_malformed_or_duplicate_fragment_ids_are_rejected(self):
        for rows in (
            [{"depends_on": []}],
            [fragment("not-a-paper-id")],
            [fragment("paper.")],
            [fragment("paper.dup"), fragment("paper.dup")],
            ["paper.row"],
        ):
            with self.subTest(rows=rows), self.assertRaisesRegex(ValueError, "fragment"):
                claim_fragment_stale_closure(rows, ["changed"])

    def test_ambiguous_or_malformed_dependencies_are_rejected(self):
        for dependencies in (
            ["paper.missing"],
            ["paper."],
            ["claim:"],
            ["claim:bad id"],
            ["claim:changed", "claim:changed"],
            [" paper.root"],
            [23],
        ):
            rows = [fragment("paper.root", *dependencies)]
            with self.subTest(dependencies=dependencies), self.assertRaisesRegex(ValueError, "depends_on"):
                claim_fragment_stale_closure(rows, ["changed"])
        with self.assertRaisesRegex(ValueError, "depends_on"):
            claim_fragment_stale_closure([{"id": "paper.root"}], ["changed"])

    def test_invalid_claim_inputs_and_size_budgets_are_rejected(self):
        for claim_ids in ("changed", ["bad id"], [17]):
            with self.subTest(claim_ids=claim_ids), self.assertRaisesRegex(ValueError, "claim ID"):
                claim_fragment_stale_closure([], claim_ids)
        with self.assertRaisesRegex(ValueError, "512"):
            claim_fragment_stale_closure([fragment(f"paper.f{i}") for i in range(513)], [])
        with self.assertRaisesRegex(ValueError, "2048"):
            claim_fragment_stale_closure(
                [fragment("paper.root", *(f"Q1.result_{i}" for i in range(2049)))], []
            )


if __name__ == "__main__":
    unittest.main()
