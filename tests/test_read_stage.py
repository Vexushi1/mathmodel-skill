from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import read_stage as READER
from reading_plan import SourceReader, validate_chunk_coverage

COMMIT = "a" * 40


class StageTextExtractionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / "core" / "source.md"
        self.path.parent.mkdir()
        self.text = "# Title\nPreamble\n## Parent\nScope\n### Evidence\n一\n二\n三\n四\n### Other\nNot selected\n"
        self.path.write_text(self.text, encoding="utf-8")
        self.committed_bytes = self.path.read_bytes()
        self.reader = SourceReader(self.root)
        self.row = self.reader.describe({"path": "core/source.md", "headings": ["### Evidence"]})
        self.plan = {"reading_plan": {"read_now": [self.row], "conditional": []}}

    def _extract(self, *, index=0, length=2, plan=None):
        committed = mock.Mock(returncode=0, stdout=self.committed_bytes)
        with mock.patch.object(READER, "verify_checkout", return_value=COMMIT), \
                mock.patch.object(READER.subprocess, "run", return_value=committed):
            return READER.extract(
                plan or self.plan, self.root, COMMIT, "read_now",
                "core/source.md", chunk_lines=length, chunk_index=index,
            )

    def test_chunk_returns_original_source_and_parent_scope(self):
        out = self._extract()
        self.assertEqual(out["source_identity"]["sha256"], hashlib.sha256(self.path.read_bytes()).hexdigest())
        self.assertEqual(out["source_identity"]["selected_commit"], COMMIT)
        self.assertEqual(out["gate_status"], "not_executed_by_reader")
        self.assertIn("# Title", out["returned_chunk"]["text"])
        self.assertGreater(out["chunk_count"], 1)
        self.assertFalse(out["all_required_ranges_returned_in_this_response"])
        self.assertTrue(out["remaining_ranges"])

    def test_all_chunks_reconstruct_exact_selected_source_without_gaps(self):
        first = self._extract()
        chunks = [self._extract(index=i)["returned_chunk"] for i in range(first["chunk_count"])]
        coverage = validate_chunk_coverage(self.row["ranges"], chunks)
        self.assertTrue(coverage["complete"], coverage)
        # Preserve the exact on-disk newline bytes. Path.read_text() performs
        # universal-newline translation on Windows and would test normalized text,
        # not the original source returned by the reader.
        raw = self.path.read_bytes().decode("utf-8").splitlines(keepends=True)
        expected = "".join("".join(raw[a - 1:b]) for a, b in self.row["ranges"])
        self.assertEqual("".join(chunk["text"] for chunk in chunks), expected)
        self.assertIn("Scope", expected)
        self.assertNotIn("Not selected", expected)

    def test_missing_or_repeated_chunk_and_identity_mix_are_detected(self):
        first = self._extract()
        chunks = [self._extract(index=i)["returned_chunk"] for i in range(first["chunk_count"])]
        self.assertFalse(validate_chunk_coverage(self.row["ranges"], chunks[:-1])["complete"])
        repeated = chunks[:2] + [chunks[1]] + chunks[2:]
        self.assertFalse(validate_chunk_coverage(self.row["ranges"], repeated)["complete"])
        mixed = [dict(c) for c in chunks]
        mixed[-1]["source_commit"] = "b" * 40
        self.assertFalse(validate_chunk_coverage(self.row["ranges"], mixed)["complete"])

    def test_utf8_bom_and_crlf_keep_byte_identity_with_safe_heading_fallback(self):
        raw = b"\xef\xbb\xbf# Title\r\n## Evidence\r\nbody\r\n"
        self.path.write_bytes(raw)
        reader = SourceReader(self.root)
        row = reader.describe({"path": "core/source.md", "headings": ["# Title"]})
        expected_sha = hashlib.sha256(raw).hexdigest()
        self.assertEqual(row["resolution"], "whole_file_fallback")
        self.assertTrue(row["fallback_reason"])
        self.assertEqual(row["sha256"], expected_sha)

        chunks = READER.source_chunks(self.root, row, COMMIT, chunk_lines=2)
        coverage = validate_chunk_coverage(row["ranges"], chunks)
        self.assertTrue(coverage["complete"], coverage)
        self.assertEqual("".join(chunk["text"] for chunk in chunks), raw.decode("utf-8"))
        self.assertTrue(all(chunk["source_sha256"] == expected_sha for chunk in chunks))

    def test_source_changed_after_plan_is_blocked_even_for_same_commit_claim(self):
        self.path.write_text(self.text.replace("四", "改"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "SHA-256 differs"):
            self._extract()

    def test_plan_cannot_select_unlisted_source_or_unguarded_condition(self):
        conditional = dict(self.row, when="candidate_visual_structure_is_being_selected")
        plan = {"reading_plan": {"read_now": [], "conditional": [conditional]}}
        rows, unresolved = READER.select_sources(plan, self.root, "conditional")
        self.assertFalse(rows)
        self.assertEqual(unresolved[0]["status"], "unresolved_condition")
        committed = mock.Mock(returncode=0, stdout=self.committed_bytes)
        with mock.patch.object(READER, "verify_checkout", return_value=COMMIT), \
                mock.patch.object(READER.subprocess, "run", return_value=committed):
            with self.assertRaisesRegex(ValueError, "not uniquely selected"):
                READER.extract(plan, self.root, COMMIT, "conditional", "core/source.md")
            chosen = READER.extract(
                plan, self.root, COMMIT, "conditional", "core/source.md",
                condition="candidate_visual_structure_is_being_selected",
            )
        self.assertEqual(chosen["condition"], "candidate_visual_structure_is_being_selected")

    def test_checkout_mismatch_is_not_reported_as_a_valid_source(self):
        with mock.patch.object(READER.subprocess, "run") as process:
            process.return_value.returncode = 0
            process.return_value.stdout = "b" * 40 + "\n"
            with self.assertRaisesRegex(ValueError, "source checkout changed"):
                READER.verify_checkout(self.root, COMMIT)
        with self.assertRaisesRegex(ValueError, "40-character"):
            READER.verify_checkout(self.root, "main")


class PinnedReadingSurfaceTests(unittest.TestCase):
    """Exercise real Git identity instead of trusting a current-tree digest."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / "core" / "source.md"
        self.path.parent.mkdir()
        self.committed_bytes = "# Source\nFixed applicability.\n## Evidence\n原文。\n".encode("utf-8")
        self.path.write_bytes(self.committed_bytes)
        self.git("init", "--quiet")
        self.git("config", "core.autocrlf", "false")
        self.git("add", "core/source.md")
        self.git(
            "-c", "user.name=Stage reader test",
            "-c", "user.email=stage-reader@example.invalid",
            "-c", "commit.gpgsign=false",
            "-c", "core.hooksPath=.git/no-hooks",
            "commit", "--quiet", "-m", "Freeze source fixture",
        )
        self.commit = self.git("rev-parse", "HEAD").stdout.strip()

    def git(self, *arguments):
        return subprocess.run(
            ["git", "-C", str(self.root), *arguments],
            capture_output=True, text=True, encoding="utf-8", check=True,
        )

    def extract(self, surface, *, path="core/source.md"):
        row = SourceReader(self.root).describe({"path": path})
        condition = "current_scope_requires_source" if surface == "conditional" else None
        if condition:
            row["when"] = condition
        plan = {"reading_plan": {surface: [row]}}
        return READER.extract(
            plan, self.root, self.commit, surface, path,
            condition=condition, chunk_lines=200,
        )

    def test_committed_bytes_are_accepted_on_each_nonwriting_surface(self):
        for surface in ("read_now", "conditional"):
            with self.subTest(surface=surface):
                out = self.extract(surface)
                self.assertEqual(out["source_identity"]["selected_commit"], self.commit)
                self.assertEqual(
                    out["source_identity"]["sha256"],
                    hashlib.sha256(self.committed_bytes).hexdigest(),
                )
                self.assertEqual(out["returned_chunk"]["text"].encode("utf-8"),
                                 self.committed_bytes)
                self.assertTrue(out["all_required_ranges_returned_in_this_response"])
                self.assertEqual(out["gate_status"], "not_executed_by_reader")
                self.assertEqual(out["status"], "source_text_returned_not_stage_or_gate_passed")

    def test_dirty_source_before_plan_cannot_impersonate_the_selected_commit(self):
        self.path.write_bytes(self.committed_bytes + b"Uncommitted rule.\n")
        for surface in ("read_now", "conditional"):
            with self.subTest(surface=surface):
                # extract() builds the plan from the already-dirty bytes. Its
                # fresh digest must not authorize the unchanged Git HEAD.
                with self.assertRaisesRegex(ValueError, "differs from selected commit"):
                    self.extract(surface)
        self.assertEqual(self.git("rev-parse", "HEAD").stdout.strip(), self.commit)

    def test_existing_source_missing_from_selected_commit_fails_closed(self):
        (self.root / "core" / "untracked.md").write_bytes(b"# Untracked source\nRule.\n")
        for surface in ("read_now", "conditional"):
            with self.subTest(surface=surface):
                with self.assertRaisesRegex(ValueError, "could not be verified"):
                    self.extract(surface, path="core/untracked.md")


class WritingStageSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        file = self.root / "modules" / "05_writing" / "paper_writing_protocol.md"
        file.parent.mkdir(parents=True)
        file.write_text(
            "# Protocol\nApplies to writing.\n## 6. 前置章节\nContext.\n"
            "### 6.1 问题重述\nSelected.\n### 6.2 问题分析\nOther.\n", encoding="utf-8"
        )
        proof = self.root / "packs" / "artifact" / "proposition_proof.md"
        proof.parent.mkdir(parents=True)
        proof.write_text("# Proof\nNecessary proof rules.\n", encoding="utf-8")

    def test_restatement_stage_resolves_exact_heading_and_symbolic_project_sources(self):
        plan = {"reading_plan": {}, "writing_runtime": {"authoring_sequence": [{
            "id": "problem_restatement", "read_now": [
                "modules/05_writing/paper_writing_protocol.md#6.1-问题重述",
                "current_problem_contract", "original_problem_text",
            ],
        }]}}
        rows, unknown = READER.select_sources(plan, self.root, "writing_stage", stage_id="problem_restatement")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["resolution"], "exact")
        self.assertEqual([x["source"] for x in unknown], ["current_problem_contract", "original_problem_text"])
        source = SourceReader(self.root)
        raw = (self.root / rows[0]["path"]).read_text(encoding="utf-8").splitlines(keepends=True)
        selected = "".join("".join(raw[a-1:b]) for a,b in rows[0]["ranges"])
        self.assertIn("Context.", selected)
        self.assertIn("Selected.", selected)
        self.assertNotIn("Other.", selected)

    def test_preflight_before_question_body_and_unknown_proof_branch(self):
        plan = {"reading_plan": {}, "writing_runtime": {"authoring_sequence": [{
            "id": "question_model_solution_result_validation",
            "before_write_preflight": {"read_now": ["current_question_evidence_bundle"]},
            "read_now": ["current_question_model_formula_algorithm_result_and_figure_evidence"],
            "conditional_reads_before_relevant_passage": {
                "proposition_or_proof": {
                    "when": "project proof state is current",
                    "read": ["packs/artifact/proposition_proof.md"],
                },
            },
        }]}}
        rows, pending = READER.select_sources(
            plan, self.root, "writing_stage", stage_id="question_model_solution_result_validation"
        )
        self.assertEqual(rows, [])
        self.assertTrue(any(x["status"] == "unresolved_condition" for x in pending))
        rows, activated = READER.select_sources(
            plan, self.root, "writing_stage",
            stage_id="question_model_solution_result_validation", condition="proposition_or_proof",
        )
        self.assertEqual([x["path"] for x in rows], ["packs/artifact/proposition_proof.md"])
        self.assertTrue(any(x["status"] == "requires_current_project_fact_adjudication" for x in activated))


    def test_draft_review_stage_resolves_named_and_chinese_heading_anchors(self):
        file = self.root / "modules" / "06_review_delivery.md"
        file.write_text(
            "# Final Review\nGlobal context.\n"
            "## 二、题意、框架与局部 stale 审查\nScope.\n"
            "### Cross-File Assembled Seam Sweep\nSeam review.\n"
            "## 三、公式、模型角色、算法、命题与数值证据审查\nMath review.\n"
            "## 五、Title Claim、正文结构与 Paragraph Necessity\nStructure.\n"
            "### v7.20/v8.0.1 章节能力保全检查\nPreservation.\n",
            encoding="utf-8",
        )
        anchors = [
            "modules/06_review_delivery.md#三-公式模型角色算法命题与数值证据审查",
            "modules/06_review_delivery.md#Cross-File-Assembled-Seam-Sweep",
            "modules/06_review_delivery.md#五-Title-Claim-正文结构与-Paragraph-Necessity",
            "modules/06_review_delivery.md#v7.20-v8.0.1-章节能力保全检查",
        ]
        plan = {"reading_plan": {}, "writing_runtime": {"authoring_sequence": [{
            "id": "draft_semantic_review", "read_now": anchors,
        }]}}
        rows, unresolved = READER.select_sources(
            plan, self.root, "writing_stage", stage_id="draft_semantic_review"
        )
        self.assertFalse(unresolved)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["path"], "modules/06_review_delivery.md")
        self.assertEqual(rows[0]["resolution"], "exact", rows[0]["fallback_reason"])
        raw = file.read_text(encoding="utf-8").splitlines(keepends=True)
        selected = "".join("".join(raw[a - 1:b]) for a, b in rows[0]["ranges"])
        for phrase in ("Seam review.", "Math review.", "Structure.", "Preservation."):
            self.assertIn(phrase, selected)

        # Ambiguous equivalent headings must fail into the explicit full-file
        # fallback, not silently choose a sibling heading or a symbolic alias.
        file.write_text(file.read_text(encoding="utf-8") +
                        "### Cross File Assembled Seam Sweep\nDuplicate.\n",
                        encoding="utf-8")
        rows, unresolved = READER.select_sources(
            plan, self.root, "writing_stage", stage_id="draft_semantic_review"
        )
        self.assertFalse(unresolved)
        self.assertEqual(rows[0]["resolution"], "whole_file_fallback")
        self.assertIn("Heading not unique", rows[0]["fallback_reason"])

    def test_writing_stage_bytes_are_verified_against_selected_git_commit(self):
        file = self.root / "modules" / "05_writing" / "paper_writing_protocol.md"
        baseline = file.read_bytes()
        plan = {"reading_plan": {}, "writing_runtime": {"authoring_sequence": [{
            "id": "problem_restatement",
            "read_now": ["modules/05_writing/paper_writing_protocol.md#6.1-问题重述"],
        }]}}
        committed = mock.Mock(returncode=0, stdout=baseline)
        with mock.patch.object(READER, "verify_checkout", return_value=COMMIT), \
                mock.patch.object(READER.subprocess, "run", return_value=committed) as git:
            result = READER.extract(
                plan, self.root, COMMIT, "writing_stage",
                "modules/05_writing/paper_writing_protocol.md",
                stage_id="problem_restatement",
            )
        self.assertEqual(result["source_identity"]["sha256"],
                         hashlib.sha256(baseline).hexdigest())
        self.assertEqual(result["resolution"], "exact")
        self.assertEqual(git.call_args.args[0][-1],
                         f"{COMMIT}:modules/05_writing/paper_writing_protocol.md")

        # HEAD may be unchanged while the source in the working tree is dirty.
        # A fresh dynamically computed row digest must not approve those bytes.
        file.write_bytes(baseline.replace(b"Selected.", b"Tampered."))
        with mock.patch.object(READER, "verify_checkout", return_value=COMMIT), \
                mock.patch.object(READER.subprocess, "run", return_value=committed):
            with self.assertRaisesRegex(ValueError, "differs from selected commit"):
                READER.extract(
                    plan, self.root, COMMIT, "writing_stage",
                    "modules/05_writing/paper_writing_protocol.md",
                    stage_id="problem_restatement",
                )

    def test_writing_stage_unavailable_committed_blob_fails_closed(self):
        plan = {"reading_plan": {}, "writing_runtime": {"authoring_sequence": [{
            "id": "problem_restatement",
            "read_now": ["modules/05_writing/paper_writing_protocol.md#6.1-问题重述"],
        }]}}
        missing = mock.Mock(returncode=128, stdout=b"", stderr=b"missing")
        with mock.patch.object(READER, "verify_checkout", return_value=COMMIT), \
                mock.patch.object(READER.subprocess, "run", return_value=missing):
            with self.assertRaisesRegex(ValueError, "could not be verified"):
                READER.extract(
                    plan, self.root, COMMIT, "writing_stage",
                    "modules/05_writing/paper_writing_protocol.md",
                    stage_id="problem_restatement",
                )


class GeneratedStageNavigationTests(unittest.TestCase):
    def test_guide_uses_existing_router_and_writing_stages(self):
        import generate_indexes
        guide = generate_indexes.stage_reading_guide_text()
        self.assertIn("### figure_design", guide)
        self.assertIn("### figure_style", guide)
        self.assertIn("### problem_restatement", guide)
        self.assertIn("### problem_analysis", guide)
        self.assertIn("### question_model_solution_result_validation", guide)
        self.assertIn("### abstract_title_and_keywords", guide)
        self.assertIn("candidate_visual_structure_is_being_selected", guide)
        self.assertIn("proposition_or_proof", guide)
        self.assertIn("stepwise_or_pseudocode", guide)
        self.assertIn("not source text", guide)
        self.assertNotIn("\\`", guide)
        self.assertIn(
            generate_indexes.STAGE_GUIDE,
            generate_indexes.generated_payloads(),
        )


if __name__ == "__main__":
    unittest.main()
