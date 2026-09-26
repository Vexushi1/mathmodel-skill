"""B2b2 formal text gate stays explicit and shares the sync read set."""
from __future__ import annotations

import unittest
from unittest.mock import patch

import tests.test_b2b_stale_writer as fixture
import claim_consumption


SYNC = fixture.SYNC


def _gate(status="passed", *, locations=(), project=None, skill=None, issues=()):
    return {"status": status, "issues": list(issues),
            "observed_sources": {"project": project or {}, "skill": skill or {}},
            "fragment_locations": list(locations)}


class SyncFormalTextGateTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.ClaimStaleWriterTests("test_b12_auxiliary_disposition_stales_only_linked_fragments_atomically")
        self.fixture.setUp()
        self.root = self.fixture.root
        self.fixture.state["paper_framework"]["claim_consumption_policy"].update(
            protocol_version="1.2.0", mode="enforce_latex_text")
        fixture._save_state(self.root, self.fixture.state)

    def tearDown(self):
        self.fixture.tearDown()

    def test_explicit_latex_read_only_gate_failure_blocks_without_writes(self):
        before = self.fixture._bytes()
        with patch.object(claim_consumption, "formal_text_gate",
                          return_value=_gate("failed", issues=["abstract value conflicts"])) as gate:
            report = SYNC.synchronize(self.root, write=False, delivery_scope="latex")
        gate.assert_called_once_with(self.root)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["claim_text_gate"]["status"], "failed")
        self.assertTrue(any("abstract value conflicts" in issue for issue in report["issues"]))
        self.assertEqual(self.fixture._bytes(), before)

    def test_legacy_policy_and_implicit_scope_never_insert_formal_gate(self):
        self.fixture.state["paper_framework"]["claim_consumption_policy"].update(
            protocol_version="1.1.0", mode="propagate")
        fixture._save_state(self.root, self.fixture.state)
        with patch.object(claim_consumption, "formal_text_gate", side_effect=AssertionError("unexpected gate")):
            old = SYNC.synchronize(self.root, write=False, delivery_scope="latex")
        self.assertNotIn("claim_text_gate", old)
        self.fixture.state["paper_framework"]["claim_consumption_policy"].update(
            protocol_version="1.2.0", mode="enforce_latex_text")
        fixture._save_state(self.root, self.fixture.state)
        with patch.object(claim_consumption, "formal_text_gate", side_effect=AssertionError("unexpected gate")):
            implicit = SYNC.synchronize(self.root, write=False)
        self.assertNotIn("claim_text_gate", implicit)

    def test_unknown_or_partial_policy_fails_formal_dry_run(self):
        for version, mode in (("1.9.0", "propagate"), ("1.2.0", "propagate"),
                              ("1.1.0", "enforce_latex_text")):
            with self.subTest(version=version, mode=mode):
                self.fixture.state["paper_framework"]["claim_consumption_policy"].update(
                    protocol_version=version, mode=mode)
                fixture._save_state(self.root, self.fixture.state)
                before = self.fixture._bytes()
                with patch.object(claim_consumption, "formal_text_gate",
                                  return_value=_gate("failed", issues=["unsupported pair"])):
                    report = SYNC.synchronize(self.root, write=False, delivery_scope="latex")
                self.assertEqual(report["status"], "failed")
                self.assertTrue(any("claim consumption policy" in issue for issue in report["issues"]))
                self.assertEqual(self.fixture._bytes(), before)

    def test_new_policy_inherits_claim_stale_writer_without_formal_scope(self):
        with patch.object(claim_consumption, "formal_text_gate", side_effect=AssertionError("unexpected gate")):
            report = SYNC.synchronize(self.root, write=True)
        self.assertTrue(report["write_performed"], report)
        self.assertEqual(report["claim_stale_fragments"], ["paper.abstract", "paper.aux"])

    def test_candidate_stale_fragment_fails_formal_gate_but_persists_stale(self):
        before = self.fixture._bytes()
        located = [{"id": "paper.aux", "status": "located"},
                   {"id": "paper.abstract", "status": "located"}]
        with patch.object(claim_consumption, "formal_text_gate", return_value=_gate(locations=located)):
            report = SYNC.synchronize(self.root, write=True, delivery_scope="latex")
        self.assertTrue(report["write_performed"], report)
        self.assertTrue(report["state_write_performed"], report)
        self.assertEqual(report["claim_text_gate"]["status"], "failed")
        self.assertTrue(any("candidate State has non-current" in issue for issue in report["issues"]))
        self.assertNotEqual(self.fixture._bytes(), before)
        self.assertEqual(report["claim_stale_fragments"], ["paper.abstract", "paper.aux"])
        state = fixture._state(self.root)
        statuses = {row["id"]: row["status"] for row in state["paper_framework"]["paper_fragments"]}
        self.assertEqual(statuses["paper.abstract"], "stale")
        self.assertEqual(statuses["paper.aux"], "stale")

    def test_malformed_tex_discovery_still_allows_safe_stale_commit(self):
        tex = self.root / "final_latex/main.tex"
        tex.parent.mkdir()
        tex.write_text("\\input{bad", encoding="utf-8")
        with patch.object(SYNC.LATEX_DELIVERY, "source_bundle_files",
                          side_effect=ValueError("unsupported TeX graph")):
            with patch.object(claim_consumption, "formal_text_gate",
                              return_value=_gate("failed", issues=["unsupported TeX graph"])):
                report = SYNC.synchronize(self.root, write=True, delivery_scope="latex")
        self.assertEqual(report["status"], "failed")
        self.assertTrue(report["write_performed"], report)
        self.assertEqual(report["claim_stale_fragments"], ["paper.abstract", "paper.aux"])

    def test_formal_pass_writes_only_report_and_preserves_proof_sources(self):
        self.fixture.state["subproblems"]["Q1"]["analysis_evidence_dispositions"][0]["status"] = "resolved"
        fixture._save_state(self.root, self.fixture.state)
        SYNC.synchronize(self.root, write=True)  # Materialize ordinary project observations first.
        before_state, before_framework, before_report = self.fixture._bytes()
        with patch.object(claim_consumption, "formal_text_gate", return_value=_gate(
                locations=[{"id": "paper.aux", "status": "located"}])):
            report = SYNC.synchronize(self.root, write=True, delivery_scope="latex")
        self.assertEqual(report["claim_text_gate"]["status"], "passed")
        self.assertTrue(report["write_performed"], report)
        self.assertFalse(report["state_write_performed"], report)
        after_state, after_framework, after_report = self.fixture._bytes()
        self.assertEqual((after_state, after_framework), (before_state, before_framework))
        self.assertNotEqual(after_report, before_report)

    def test_gate_project_and_skill_sources_are_rechecked(self):
        tex = self.root / "final_latex/main.tex"
        tex.parent.mkdir()
        tex.write_text("original", encoding="utf-8")
        project_digest = SYNC.sha256_file(tex)
        skill_digest = "0" * 64
        sources = {"project": {"final_latex/main.tex": project_digest},
                   "skill": {"core/claim_consumption_contract.yaml": skill_digest}}
        self.fixture.state["subproblems"]["Q1"]["analysis_evidence_dispositions"][0]["status"] = "resolved"
        fixture._save_state(self.root, self.fixture.state)
        before = self.fixture._bytes()
        with patch.object(claim_consumption, "formal_text_gate", return_value=_gate(
                locations=[{"id": "paper.aux", "status": "located"}], **sources)):
            with self.assertRaises(SYNC.PROJECT_TX.ReadSetConflictError):
                SYNC.synchronize(self.root, write=True, delivery_scope="latex")
        self.assertEqual(self.fixture._bytes(), before)

        def changed_project(_root):
            tex.write_text("changed after observation", encoding="utf-8")
            return _gate(locations=[{"id": "paper.aux", "status": "located"}],
                         project={"final_latex/main.tex": project_digest})

        with patch.object(claim_consumption, "formal_text_gate", side_effect=changed_project):
            with self.assertRaises(SYNC.PROJECT_TX.ReadSetConflictError):
                SYNC.synchronize(self.root, write=True, delivery_scope="latex")
        self.assertEqual(self.fixture._bytes(), before)


if __name__ == "__main__":
    unittest.main()
