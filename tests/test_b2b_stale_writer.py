"""B2b opt-in claim-local stale writes through the existing sync transaction."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

from tests.claim_fixture import record
from tests.test_sync_project import load_syncer, setup_project


SYNC = load_syncer()


def _raw(path: Path) -> bytes:
    return path.read_bytes() if path.exists() else b""


def _state(root: Path) -> dict:
    return yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))


def _save_state(root: Path, state: dict) -> None:
    (root / "state/project_state.yaml").write_text(
        yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8",
    )


def _fragment(identifier: str, kind: str, dependency: str, anchor: str) -> dict:
    return {"id": identifier, "kind": kind, "scope": "Q1", "depends_on": [dependency],
            "anchor": anchor, "status": "current"}


class ClaimStaleWriterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        setup_project(self.root, status="designed", phase="model_design")
        self.fragments = [
            _fragment("paper.answer", "question_result_text", "claim:gain_claim", "answer"),
            _fragment("paper.aux", "model_evaluation_claim", "claim:aux_claim", "auxiliary"),
            _fragment("paper.abstract", "abstract_claim", "paper.aux", "abstract"),
            _fragment("paper.unrelated", "paper_section", "Q1.unrelated", "background"),
        ]
        claims = record()
        auxiliary = deepcopy(claims["claims"][0])
        auxiliary.update(id="aux_claim", text="Synthetic auxiliary evaluation claim.")
        claims["claims"].append(auxiliary)
        self.state = _state(self.root)
        framework = self.state["paper_framework"]
        framework.update(version="v0.8-project-memory", claim_evidence=claims,
                         paper_fragments=self.fragments,
                         claim_consumption_policy={
                             "protocol_version": "1.1.0", "mode": "propagate",
                             "required_consumptions": [{"claim_id": "aux_claim",
                                                        "fragment_kinds": ["model_evaluation_claim"]}],
                         })
        self.state["subproblems"]["Q1"]["analysis_evidence_dispositions"] = [{
            "id": "E1", "method_or_source": "synthetic auxiliary review",
            "target_claim": "aux_claim", "disposition": "modify",
            "key_finding": "auxiliary wording too broad", "required_action": "rewrite auxiliary claim",
            "status": "current",
        }]
        base = (self.root / "模型论文框架.md").read_text(encoding="utf-8")
        rows = ["### Terminology Registry", "", "### Numeric Profile", "",
                "### Paper Fragment Dependency Map", "",
                "| Fragment ID | 类型 | 范围 | 依赖对象 | 正文/摘要锚点 | LaTeX 源码文件（可选） | 状态 |",
                "|---|---|---|---|---|---|---|"]
        for fragment in self.fragments:
            rows.append("| " + " | ".join((fragment["id"], fragment["kind"], fragment["scope"],
                                               ", ".join(fragment["depends_on"]), fragment["anchor"],
                                               "", fragment["status"])) + " |")
        self.framework = base + "\n" + "\n".join(rows) + "\n"
        (self.root / "模型论文框架.md").write_text(self.framework, encoding="utf-8")
        framework["sha256"] = SYNC.sha256_text(self.framework)
        _save_state(self.root, self.state)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _bytes(self) -> tuple[bytes, bytes, bytes]:
        return tuple(_raw(self.root / name) for name in
                     ("state/project_state.yaml", "模型论文框架.md", "sync_report.yaml"))

    def test_b12_auxiliary_disposition_stales_only_linked_fragments_atomically(self) -> None:
        before = self._bytes()
        report = SYNC.synchronize(self.root, write=True)
        self.assertTrue(report["write_performed"], report)
        self.assertEqual(report["status"], "passed", report)
        self.assertEqual(report["invalidated_claim_ids"], ["aux_claim"])
        self.assertEqual(report["claim_stale_fragments"], ["paper.abstract", "paper.aux"])
        self.assertEqual(report["stale_paper_fragments"], ["paper.abstract", "paper.aux"])
        self.assertNotEqual(self._bytes(), before)
        state = _state(self.root)
        statuses = {row["id"]: row["status"] for row in state["paper_framework"]["paper_fragments"]}
        self.assertEqual(statuses, {"paper.answer": "current", "paper.aux": "stale",
                                    "paper.abstract": "stale", "paper.unrelated": "current"})
        self.assertFalse(state["subproblems"]["Q1"]["artifacts_stale"])
        text = (self.root / "模型论文框架.md").read_text(encoding="utf-8")
        self.assertIn("| paper.aux | model_evaluation_claim | Q1 | claim:aux_claim | auxiliary |  | stale |", text)
        self.assertIn("| paper.answer | question_result_text | Q1 | claim:gain_claim | answer |  | current |", text)
        self.assertEqual(state["paper_framework"]["sha256"], SYNC.sha256_text(text))
        self.assertEqual(report["framework_hash"], SYNC.sha256_file(self.root / "模型论文框架.md"))
        self.assertFalse((self.root / SYNC.PROJECT_TX.JOURNAL_RELATIVE_PATH).exists())

    def test_readonly_and_observe_mode_leave_claim_status_current(self) -> None:
        before = self._bytes()
        report = SYNC.synchronize(self.root, write=False)
        self.assertFalse(report["write_performed"])
        self.assertEqual(self._bytes(), before)
        self.state["paper_framework"]["claim_consumption_policy"].update(
            protocol_version="1.0.0", mode="observe")
        _save_state(self.root, self.state)
        report = SYNC.synchronize(self.root, write=True)
        self.assertTrue(report["write_performed"])
        self.assertNotIn("claim_stale_fragments", report)
        self.assertEqual({row["status"] for row in _state(self.root)["paper_framework"]["paper_fragments"]},
                         {"current"})

    def test_invalid_or_text_only_target_prevents_every_write(self) -> None:
        for target in ("Synthetic auxiliary evaluation claim.", "unknown"):
            with self.subTest(target=target):
                self.state["subproblems"]["Q1"]["analysis_evidence_dispositions"][0]["target_claim"] = target
                _save_state(self.root, self.state)
                before = self._bytes()
                report = SYNC.synchronize(self.root, write=True)
                self.assertFalse(report["write_performed"], report)
                self.assertTrue(any("exact B1 claim ID" in issue for issue in report["issues"]), report)
                self.assertEqual(self._bytes(), before)
                self.assertEqual(report["framework_hash"], SYNC.sha256_file(self.root / "模型论文框架.md"))

    def test_stale_or_resolved_disposition_is_ignored(self) -> None:
        for status in ("stale", "resolved"):
            with self.subTest(status=status):
                self.state["subproblems"]["Q1"]["analysis_evidence_dispositions"][0].update(
                    status=status, target_claim="legacy prose target")
                _save_state(self.root, self.state)
                report = SYNC.synchronize(self.root, write=True)
                self.assertTrue(report["write_performed"], report)
                self.assertEqual(report["invalidated_claim_ids"], [])
                self.assertEqual(report["claim_stale_fragments"], [])
                self.assertEqual({row["status"] for row in _state(self.root)["paper_framework"]["paper_fragments"]},
                                 {"current"})
                self.state = _state(self.root)

    def test_invalid_policy_projection_and_bom_prevent_every_write(self) -> None:
        alterations = (
            lambda: self.state["paper_framework"]["claim_consumption_policy"].update(mode="observe"),
            lambda: (self.root / "模型论文框架.md").write_text(
                self.framework.replace("| paper.aux |", "| paper.missing |"), encoding="utf-8"),
            lambda: (self.root / "模型论文框架.md").write_bytes(b"\xef\xbb\xbf" + self.framework.encode("utf-8")),
        )
        for alter in alterations:
            with self.subTest(alteration=alterations.index(alter)):
                (self.root / "模型论文框架.md").write_text(self.framework, encoding="utf-8")
                self.state["paper_framework"]["claim_consumption_policy"].update(
                    protocol_version="1.1.0", mode="propagate")
                alter()
                _save_state(self.root, self.state)
                before = self._bytes()
                report = SYNC.synchronize(self.root, write=True)
                self.assertFalse(report["write_performed"], report)
                self.assertEqual(self._bytes(), before)

    def test_crlf_layout_and_unchanged_cells_survive_status_patch(self) -> None:
        path = self.root / "模型论文框架.md"
        path.write_bytes(self.framework.replace("\n", "\r\n").encode("utf-8"))
        report = SYNC.synchronize(self.root, write=True)
        self.assertTrue(report["write_performed"], report)
        raw = path.read_bytes()
        self.assertEqual(raw.count(b"\n"), raw.count(b"\r\n"))
        self.assertIn(b"| paper.answer | question_result_text | Q1 | claim:gain_claim | answer |  | current |\r\n", raw)
        self.assertEqual(_state(self.root)["paper_framework"]["sha256"],
                         SYNC.sha256_text(raw.decode("utf-8")))
        import claim_consumption
        observed = claim_consumption.inspect_project(self.root)
        self.assertFalse(any("paper_framework.sha256" in item for item in observed["errors"]), observed)

    def test_not_applicable_fragment_is_not_changed_by_claim_closure(self) -> None:
        self.state["paper_framework"]["paper_fragments"][2]["status"] = "not_applicable"
        self.framework = self.framework.replace(
            "| paper.abstract | abstract_claim | Q1 | paper.aux | abstract |  | current |",
            "| paper.abstract | abstract_claim | Q1 | paper.aux | abstract |  | not_applicable |",
        )
        (self.root / "模型论文框架.md").write_text(self.framework, encoding="utf-8")
        self.state["paper_framework"]["sha256"] = SYNC.sha256_text(self.framework)
        _save_state(self.root, self.state)
        report = SYNC.synchronize(self.root, write=True)
        self.assertTrue(report["write_performed"], report)
        self.assertEqual(report["claim_stale_fragments"], ["paper.aux"])
        statuses = {row["id"]: row["status"] for row in
                    _state(self.root)["paper_framework"]["paper_fragments"]}
        self.assertEqual(statuses["paper.abstract"], "not_applicable")
        self.assertEqual(statuses["paper.aux"], "stale")
        self.assertIn("| paper.abstract | abstract_claim | Q1 | paper.aux | abstract |  | not_applicable |",
                      (self.root / "模型论文框架.md").read_text(encoding="utf-8"))

    def test_question_level_stale_is_unioned_into_framework_status_cells(self) -> None:
        self.state["subproblems"]["Q1"]["validated_artifact_hashes"] = {"data": "0" * 64}
        _save_state(self.root, self.state)
        report = SYNC.synchronize(self.root, write=True)
        self.assertTrue(report["write_performed"], report)
        self.assertIn("Q1", report["stale_questions"])
        self.assertEqual(report["stale_paper_fragments"],
                         ["paper.abstract", "paper.answer", "paper.aux", "paper.unrelated"])
        self.assertEqual({row["status"] for row in
                          _state(self.root)["paper_framework"]["paper_fragments"]}, {"stale"})
        text = (self.root / "模型论文框架.md").read_text(encoding="utf-8")
        self.assertIn("| paper.unrelated | paper_section | Q1 | Q1.unrelated | background |  | stale |", text)
        self.assertFalse(any("sha256 does not match 模型论文框架" in issue for issue in report["issues"]), report)

    def test_observe_policy_keeps_legacy_question_stale_projection_consistent(self) -> None:
        self.state["paper_framework"]["claim_consumption_policy"].update(
            protocol_version="1.0.0", mode="observe")
        self.state["subproblems"]["Q1"]["validated_artifact_hashes"] = {"data": "0" * 64}
        _save_state(self.root, self.state)
        report = SYNC.synchronize(self.root, write=True)
        self.assertTrue(report["write_performed"], report)
        self.assertNotIn("invalidated_claim_ids", report)
        self.assertEqual(report["stale_paper_fragments"],
                         ["paper.abstract", "paper.answer", "paper.aux", "paper.unrelated"])
        text = (self.root / "模型论文框架.md").read_text(encoding="utf-8")
        state = _state(self.root)
        self.assertIn("| paper.unrelated | paper_section | Q1 | Q1.unrelated | background |  | stale |", text)
        self.assertEqual(state["paper_framework"]["sha256"], SYNC.sha256_text(text))
        import claim_consumption
        claim_consumption._check_projection(state["paper_framework"], text)

    def test_scope_mismatch_prevents_write(self) -> None:
        self.state["subproblems"]["Q2"] = deepcopy(self.state["subproblems"]["Q1"])
        self.state["subproblems"]["Q1"]["analysis_evidence_dispositions"] = []
        _save_state(self.root, self.state)
        before = self._bytes()
        report = SYNC.synchronize(self.root, write=True)
        self.assertFalse(report["write_performed"], report)
        self.assertTrue(any("scope does not match" in issue for issue in report["issues"]), report)
        self.assertEqual(self._bytes(), before)

    def test_duplicate_framework_row_is_rejected_before_transaction(self) -> None:
        row = "| paper.aux | model_evaluation_claim | Q1 | claim:aux_claim | auxiliary |  | current |\n"
        self.framework = self.framework.replace(row, row + row)
        (self.root / "模型论文框架.md").write_text(self.framework, encoding="utf-8")
        self.state["paper_framework"]["sha256"] = SYNC.sha256_text(self.framework)
        _save_state(self.root, self.state)
        before = self._bytes()
        report = SYNC.synchronize(self.root, write=True)
        self.assertFalse(report["write_performed"], report)
        self.assertTrue(any("duplicate framework fragment ID" in issue for issue in report["issues"]), report)
        self.assertEqual(self._bytes(), before)

    def test_malformed_disposition_and_duplicate_claim_ids_prevent_write(self) -> None:
        alterations = (
            lambda: self.state["subproblems"]["Q1"]["analysis_evidence_dispositions"][0].update(status="unknown"),
            lambda: self.state["subproblems"]["Q1"]["analysis_evidence_dispositions"].append(
                deepcopy(self.state["subproblems"]["Q1"]["analysis_evidence_dispositions"][0])),
            lambda: self.state["paper_framework"]["claim_evidence"]["claims"].append(
                deepcopy(self.state["paper_framework"]["claim_evidence"]["claims"][0])),
            lambda: self.state["paper_framework"]["paper_fragments"][0].update(depends_on=17),
        )
        baseline = deepcopy(self.state)
        for index, alter in enumerate(alterations):
            with self.subTest(case=index):
                self.state = deepcopy(baseline)
                alter()
                _save_state(self.root, self.state)
                before = self._bytes()
                report = SYNC.synchronize(self.root, write=True)
                self.assertFalse(report["write_performed"], report)
                self.assertTrue(report["issues"])
                self.assertEqual(self._bytes(), before)

    def test_staged_projection_failure_keeps_all_live_files_unchanged(self) -> None:
        before = self._bytes()
        with patch.object(SYNC, "_framework_fragment_status_text", side_effect=lambda text, stale_ids: text):
            with self.assertRaisesRegex(ValueError, "State and Framework fragment row differ"):
                SYNC.synchronize(self.root, write=True)
        self.assertEqual(self._bytes(), before)
        self.assertFalse((self.root / SYNC.PROJECT_TX.JOURNAL_RELATIVE_PATH).exists())

    def test_claim_closure_error_reports_only_b2_error_and_does_not_write(self) -> None:
        before = self._bytes()
        with patch.object(SYNC.STATE_TRANSITIONS, "claim_fragment_stale_closure",
                          side_effect=ValueError("invalid claim edge")):
            report = SYNC.synchronize(self.root, write=True)
        self.assertFalse(report["write_performed"])
        self.assertEqual(report["status"], "failed")
        self.assertTrue(any("invalid claim edge" in issue for issue in report["issues"]), report)
        self.assertFalse(any("sha256 does not match" in issue for issue in report["issues"]), report)
        self.assertEqual(self._bytes(), before)

    def test_framework_read_set_conflict_prevents_commit(self) -> None:
        before_state, _, before_report = self._bytes()
        original = SYNC._framework_header_preserving_layout

        def mutate(text: str, scope: str, stale: bool) -> str:
            (self.root / "模型论文框架.md").write_text(self.framework + "external change\n", encoding="utf-8")
            return original(text, scope, stale)

        with patch.object(SYNC, "_framework_header_preserving_layout", side_effect=mutate):
            with self.assertRaises(SYNC.PROJECT_TX.ReadSetConflictError):
                SYNC.synchronize(self.root, write=True)
        after_state, _, after_report = self._bytes()
        self.assertEqual((after_state, after_report), (before_state, before_report))


if __name__ == "__main__":
    unittest.main()
