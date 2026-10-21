from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import read_stage
from reading_plan import SourceReader, canonical_rolepaths, describe_resources, validate_review_rows

COMMIT = "a" * 40
ENTRY = "modules/06_review_delivery.md"
CONTENT = "modules/06_review/content_review.md"
FINAL = "modules/06_review/final_delivery.md"
MANIFEST = "core/module_manifest.yaml"


class ModularReviewReadingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest = {"modules": {"review_delivery": {
            "path": ENTRY,
            "reading_sources": {
                "entry": ENTRY, "content": CONTENT, "final": FINAL,
                "entry_headings": ["## 一、评审分级", "## 十、返修优先级", "## 十一、Blocking 条件"],
                "stages": {
                    "draft_semantic_review": ["entry", "content"],
                    "final_review_and_delivery": ["entry", "content", "final"],
                },
            },
        }}}
        self.write(ENTRY,
                   "# Module 06\nGlobal review applicability.\n"
                   "## 一、评审分级\nREAL-SEVERITY.\n"
                   "## 二、题意、框架与局部 stale 审查\nCompatibility link only.\n"
                   "### Cross-File Assembled Seam Sweep\nCompatibility link only.\n"
                   "## 三、公式、模型角色、算法、命题与数值证据审查\nCompatibility link only.\n"
                   "## 八、编译、复现与提交包\nCompatibility link only.\n"
                   "## 九、Final Submission Compliance & Evidence Sweep\nCompatibility link only.\n"
                   "## 十、返修优先级\nREAL-REPAIR.\n"
                   "## 十一、Blocking 条件\nREAL-BLOCKING.\n")
        self.write(CONTENT,
                   "# Common content review\nCommon applicability.\n"
                   "## 二、题意、框架与局部 stale 审查\nREAL-COMMON scope.\n"
                   "### Cross-File Assembled Seam Sweep\nREAL-SEAM.\n"
                   "## 三、公式、模型角色、算法、命题与数值证据审查\nREAL-MATH.\n")
        self.write(FINAL,
                   "# Final delivery review\nFinal applicability.\n"
                   "## 八、编译、复现与提交包\nREAL-COMPILE.\n"
                   "## 九、Final Submission Compliance & Evidence Sweep\nREAL-FINAL.\n")
        self.write_manifest()
        self.write("core/bootstrap.yaml", yaml.safe_dump({"authoritative_sources": {
            "review_content": CONTENT, "review_final": FINAL,
        }}, allow_unicode=True))

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))

    def write_manifest(self):
        self.write(MANIFEST, yaml.safe_dump(self.manifest, allow_unicode=True, sort_keys=False))

    def selected_text(self, row):
        lines = (self.root / row["path"]).read_bytes().decode("utf-8").splitlines(keepends=True)
        return "".join("".join(lines[start - 1:end]) for start, end in row["ranges"])

    def source_rows(self, **kwargs):
        return describe_resources(SourceReader(self.root), {"path": ENTRY}, **kwargs)

    def stage_plan(self, identifier, entries=None):
        return {"reading_plan": {}, "writing_runtime": {"authoring_sequence": [{
            "id": identifier, "read_now": entries or [ENTRY],
        }]}}

    def committed_sources(self):
        return {path: (self.root / path).read_bytes() for path in (MANIFEST, ENTRY, CONTENT, FINAL)}

    def git_show(self, committed):
        def result(arguments, **_kwargs):
            path = arguments[-1].partition(":")[2]
            return mock.Mock(returncode=0 if path in committed else 128,
                             stdout=committed.get(path, b""), stderr=b"")
        return result

    def test_legacy_whole_file_returns_real_complete_closure_with_source_identity(self):
        rows = self.source_rows()
        self.assertEqual([row["path"] for row in rows], [ENTRY, CONTENT, FINAL])
        self.assertEqual(canonical_rolepaths(self.root), {
            "entry": ENTRY, "content": CONTENT, "final": FINAL,
        })
        selected = "".join(self.selected_text(row) for row in rows)
        for evidence in ("REAL-SEVERITY", "REAL-COMMON", "REAL-MATH", "REAL-FINAL", "REAL-BLOCKING"):
            self.assertIn(evidence, selected)
        expected_manifest = hashlib.sha256((self.root / MANIFEST).read_bytes()).hexdigest()
        for row in rows:
            self.assertEqual(row["reading_source_manifest"], {"path": MANIFEST, "sha256": expected_manifest})
            self.assertEqual(row["review_source_closure"], [ENTRY, CONTENT, FINAL])
        # Raw metadata remains one file; only actual resource consumption expands.
        self.assertIsInstance(SourceReader(self.root).describe({"path": ENTRY}), dict)

    def test_declared_stages_read_distinct_complete_sets_without_compatibility_stubs(self):
        result = {}
        for identifier in ("draft_semantic_review", "final_review_and_delivery"):
            rows, symbolic = read_stage.select_sources(
                self.stage_plan(identifier), self.root, "writing_stage", stage_id=identifier,
            )
            self.assertFalse(symbolic)
            result[identifier] = rows
            entry = next(row for row in rows if row["path"] == ENTRY)
            text = self.selected_text(entry)
            for evidence in ("Global review applicability", "REAL-SEVERITY", "REAL-REPAIR", "REAL-BLOCKING"):
                self.assertIn(evidence, text)
            self.assertNotIn("Compatibility link only", text)
            self.assertLess(entry["planned_bytes"], entry["source_bytes"])
        self.assertEqual([row["path"] for row in result["draft_semantic_review"]], [ENTRY, CONTENT])
        self.assertEqual([row["path"] for row in result["final_review_and_delivery"]], [ENTRY, CONTENT, FINAL])
        self.assertLess(sum(row["planned_bytes"] for row in result["draft_semantic_review"]),
                        sum(row["planned_bytes"] for row in result["final_review_and_delivery"]))

    def test_legacy_heading_fetches_canonical_rules_and_parent_context(self):
        plan = self.stage_plan("draft_semantic_review", [ENTRY + "#Cross-File-Assembled-Seam-Sweep"])
        rows, _ = read_stage.select_sources(plan, self.root, "writing_stage", stage_id="draft_semantic_review")
        self.assertEqual([row["path"] for row in rows], [ENTRY, CONTENT])
        content = next(row for row in rows if row["path"] == CONTENT)
        text = self.selected_text(content)
        self.assertIn("Common applicability", text)
        self.assertIn("REAL-COMMON", text)
        self.assertIn("REAL-SEAM", text)
        self.assertNotIn("REAL-MATH", text)

    def test_legacy_final_heading_keeps_common_checks(self):
        rows = describe_resources(SourceReader(self.root), {
            "path": ENTRY, "headings": ["## 九、Final Submission Compliance & Evidence Sweep"],
        })
        self.assertEqual([row["path"] for row in rows], [ENTRY, CONTENT, FINAL])
        self.assertIn("REAL-COMMON", self.selected_text(rows[1]))
        self.assertIn("REAL-FINAL", self.selected_text(rows[2]))
        validate_review_rows(self.root, rows)

    def test_unknown_legacy_heading_fallback_respects_known_stage_scope(self):
        for heading in ("missing legacy anchor", "## 一、评审分级"):
            with self.subTest(heading=heading):
                spec = {"path": ENTRY, "headings": [heading]}
                draft = describe_resources(SourceReader(self.root), spec, stage_id="draft_semantic_review")
                self.assertEqual([row["path"] for row in draft], [ENTRY, CONTENT])
                self.assertTrue(all(row["resolution"] == "whole_file_fallback" for row in draft))
                complete = describe_resources(SourceReader(self.root), spec)
                self.assertEqual([row["path"] for row in complete], [ENTRY, CONTENT, FINAL])

    def test_final_heading_cannot_escape_draft_scope(self):
        with self.assertRaisesRegex(ValueError, "outside declared stage"):
            describe_resources(SourceReader(self.root), {
                "path": ENTRY, "headings": ["## 九、Final Submission Compliance & Evidence Sweep"],
            }, stage_id="draft_semantic_review")

    def test_missing_leaf_ambiguous_heading_and_role_cycle_fail_closed(self):
        (self.root / FINAL).unlink()
        with self.assertRaises(FileNotFoundError):
            self.source_rows(stage_id="draft_semantic_review")
        self.write(FINAL, "# Final\n### Cross-File Assembled Seam Sweep\nAnother target.\n")
        with self.assertRaisesRegex(ValueError, "ambiguous canonical review heading"):
            describe_resources(SourceReader(self.root), {
                "path": ENTRY, "headings": ["### Cross-File Assembled Seam Sweep"],
            })
        self.manifest["modules"]["review_delivery"]["reading_sources"]["content"] = ENTRY
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "alias or cycle"):
            self.source_rows()

    def test_invalid_entry_boundaries_and_removed_registered_declaration_fail_closed(self):
        declaration = self.manifest["modules"]["review_delivery"]["reading_sources"]
        declaration["entry_headings"] = ["## Missing entry boundary"]
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "entry boundary"):
            self.source_rows(stage_id="draft_semantic_review")
        del self.manifest["modules"]["review_delivery"]["reading_sources"]
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "no reading_sources declaration"):
            self.source_rows()

    def test_different_role_strings_cannot_alias_one_resolved_file(self):
        declaration = self.manifest["modules"]["review_delivery"]["reading_sources"]
        declaration["content"] = "modules/./06_review_delivery.md"
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "same file or cycle"):
            self.source_rows()

    def test_legacy_isolated_roots_without_new_declarations_stay_readable(self):
        self.write("core/bootstrap.yaml", "authoritative_sources: {}\n")
        self.write(MANIFEST, "modules: {}\n")
        rows = self.source_rows()
        self.assertEqual([row["path"] for row in rows], [ENTRY])
        self.assertIsNone(canonical_rolepaths(self.root))
        self.assertNotIn("reading_source_manifest", rows[0])

    def test_old_plan_or_missing_leaf_row_must_resolve_again(self):
        raw = SourceReader(self.root).describe({"path": ENTRY})
        for rows in ([raw], self.source_rows()[:1]):
            with self.subTest(rows=len(rows)):
                plan = {"reading_plan": {"read_now": rows}}
                with self.assertRaisesRegex(ValueError, "rerun resolver"):
                    read_stage.select_sources(plan, self.root, "read_now")

    def test_planned_manifest_binding_cannot_be_bypassed_by_repointing_all_roles(self):
        rows = self.source_rows()
        declaration = self.manifest["modules"]["review_delivery"]["reading_sources"]
        for role in ("entry", "content", "final"):
            new_path = f"modules/repointed_{role}.md"
            self.write(new_path, (self.root / declaration[role]).read_text(encoding="utf-8"))
            declaration[role] = new_path
        self.manifest["modules"]["review_delivery"]["path"] = declaration["entry"]
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "rerun resolver"):
            read_stage.select_sources({"reading_plan": {"read_now": rows}}, self.root, "read_now")

    def test_bound_plan_cannot_downgrade_when_manifest_and_bootstrap_registration_disappear(self):
        rows = self.source_rows()
        self.write("core/bootstrap.yaml", "authoritative_sources: {}\n")
        del self.manifest["modules"]["review_delivery"]["reading_sources"]
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "lost its source declaration"):
            read_stage.select_sources({"reading_plan": {"read_now": rows}}, self.root, "read_now")

    def test_pinned_writing_reads_reject_dirty_mapping_and_unrequested_leaf(self):
        committed = self.committed_sources()
        plan = self.stage_plan("final_review_and_delivery")
        with mock.patch.object(read_stage, "verify_checkout", return_value=COMMIT), \
                mock.patch.object(read_stage.subprocess, "run", side_effect=self.git_show(committed)):
            out = read_stage.extract(plan, self.root, COMMIT, "writing_stage", ENTRY,
                                     stage_id="final_review_and_delivery")
            self.assertEqual(out["gate_status"], "not_executed_by_reader")
            self.write(FINAL, committed[FINAL].decode("utf-8") + "Dirty final source.\n")
            with self.assertRaisesRegex(ValueError, "differs from selected commit"):
                read_stage.extract(plan, self.root, COMMIT, "writing_stage", ENTRY,
                                   stage_id="final_review_and_delivery")
            self.write(FINAL, committed[FINAL].decode("utf-8"))
            self.write(MANIFEST, committed[MANIFEST].decode("utf-8") + "# Dirty map bytes.\n")
            with self.assertRaisesRegex(ValueError, "differs from selected commit"):
                read_stage.extract(plan, self.root, COMMIT, "writing_stage", ENTRY,
                                   stage_id="final_review_and_delivery")

    def test_read_now_rejects_changed_unrequested_leaf_instead_of_refreshing_plan_hashes(self):
        committed = self.committed_sources()
        plan = {"reading_plan": {"read_now": self.source_rows()}}
        self.write(CONTENT, committed[CONTENT].decode("utf-8") + "Dirty common rules.\n")
        with mock.patch.object(read_stage, "verify_checkout", return_value=COMMIT), \
                mock.patch.object(read_stage.subprocess, "run", side_effect=self.git_show(committed)):
            with self.assertRaisesRegex(ValueError, "differs from reading plan"):
                read_stage.extract(plan, self.root, COMMIT, "read_now", ENTRY)

    def test_conditional_expansion_preserves_trigger_and_original_input(self):
        spec = {"path": ENTRY, "when": "actual_final_review_requested"}
        before = deepcopy(spec)
        rows = describe_resources(SourceReader(self.root), spec)
        self.assertEqual(spec, before)
        self.assertTrue(all(row["when"] == spec["when"] for row in rows))
        plan = {"reading_plan": {"conditional": rows}}
        selected, unresolved = read_stage.select_sources(plan, self.root, "conditional")
        self.assertFalse(selected)
        self.assertTrue(unresolved)
        selected, _ = read_stage.select_sources(plan, self.root, "conditional", condition=spec["when"])
        self.assertEqual([row["path"] for row in selected], [ENTRY, CONTENT, FINAL])


if __name__ == "__main__":
    unittest.main()
