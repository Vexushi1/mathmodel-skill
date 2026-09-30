"""Explicit synthetic provenance writes do not change model or numerical authority."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import case_memory_retrieve as RETRIEVAL  # noqa: E402
import case_references as REFERENCES  # noqa: E402
import project_transaction as TX  # noqa: E402
import validate_project_state as STATE  # noqa: E402
from case_memory_fixtures import (  # noqa: E402
    add_synthetic_sib, copy_corpus, make_project, query_for, read_json,
    refresh_corpus, tree_bytes, write_json, write_state,
)


def change_same_stat(path: Path) -> None:
    original = path.read_bytes()
    stat = path.stat()
    path.write_bytes(original[:-1] + (b" " if original[-1:] != b" " else b"\n"))
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))


class CaseReferenceBehaviorTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.temp = Path(temporary.name)
        self.root = self.temp / "project"
        self.state = make_project(self.root)
        self.state_path = self.root / TX.STATE_RELATIVE_PATH
        self.framework = self.root / "模型论文框架.md"
        self.corpus = copy_corpus(self.temp / "corpus")
        self.query = query_for(self.corpus, 3)
        self.selection = {
            "case_id": "CM-SYN-003", "disposition": "reference",
            "adopted_parts": [], "rejected_parts": [],
            "current_evidence": [{"kind": "state_field", "pointer": "/subproblems/Q1/classification",
                                  "sha256": REFERENCES.state_field_sha256(self.state["subproblems"]["Q1"]["classification"])}],
            "reason": "Independently authored synthetic control-plane reference; no numerical or approval evidence.",
        }

    def current(self):
        return yaml.safe_load(self.state_path.read_text(encoding="utf-8"))

    def preview(self, *, question="Q1", query=None, selection=None):
        return REFERENCES.preview_reference(self.root, question,
            self.query if query is None else query,
            self.selection if selection is None else selection, corpus_root=self.corpus)

    def record(self, *, preview=None, selection=None, query=None, **kwargs):
        selection = self.selection if selection is None else selection
        query = self.query if query is None else query
        preview = self.preview(query=query, selection=selection) if preview is None else preview
        options = {"expected_generation": preview["state_snapshot"]["state_generation"],
                   "expected_state_sha256": preview["state_snapshot"]["sha256"],
                   "expected_retrieval_corpus_sha256": preview["retrieval_bindings"]["corpus_sha256"]}
        options.update(kwargs)
        return REFERENCES.record_reference(self.root, "Q1", query, selection,
                                           corpus_root=self.corpus, **options)

    def inspect(self):
        return REFERENCES.inspect_references(self.root, corpus_root=self.corpus)

    def assert_non_authorizing(self, report):
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["model_approval_granted"])
        self.assertEqual(report["project_condition_semantics"], "not_assessed")

    def assert_blocked(self, report):
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(report["errors"])
        self.assert_non_authorizing(report)

    def test_old_state_without_optional_references_is_still_valid(self):
        self.assertNotIn("case_references", self.state["decisions"]["Q1"])
        self.assertEqual(STATE.validate_state_payload(self.state, project_root=self.root), [])
        before = tree_bytes(self.root)
        report = self.inspect()
        self.assertEqual(report["status"], "inspected")
        self.assertEqual(report["records"], [])
        self.assertEqual(tree_bytes(self.root), before)

    def test_preview_and_default_record_leave_project_and_corpus_untouched(self):
        before = tree_bytes(self.root), tree_bytes(self.corpus)
        preview = self.preview()
        self.assertEqual(preview["status"], "preview")
        self.assertEqual(self.record(preview=preview)["status"], "preview")
        self.assert_non_authorizing(preview)
        self.assertEqual((tree_bytes(self.root), tree_bytes(self.corpus)), before)
        self.assertFalse((self.root / TX.JOURNAL_RELATIVE_PATH).exists())

    def test_explicit_write_changes_only_references_and_generation(self):
        before = deepcopy(self.state)
        framework = self.framework.read_bytes()
        numerical = self.root / "synthetic-results.txt"
        numerical.write_text("Synthetic sentinel, not a numerical result.\n", encoding="utf-8")
        sentinel = numerical.read_bytes()
        report = self.record(write=True)
        self.assertEqual(report["status"], "committed")
        self.assert_non_authorizing(report)
        state = self.current()
        references = state["decisions"]["Q1"].pop("case_references")
        self.assertEqual(references["protocol_version"], "1.0.0")
        self.assertEqual(references["records"], [report["record"]])
        self.assertEqual(state["project"]["state_generation"], 1)
        state["project"]["state_generation"] = 0
        self.assertEqual(state, before)
        self.assertEqual(self.framework.read_bytes(), framework)
        self.assertEqual(numerical.read_bytes(), sentinel)
        self.assertFalse((self.root / TX.JOURNAL_RELATIVE_PATH).exists())

    def test_identical_record_is_readonly_without_a_new_generation(self):
        self.assertEqual(self.record(write=True)["status"], "committed")
        before = self.state_path.read_bytes(), self.framework.read_bytes()
        report = self.record(write=True)
        self.assertEqual(report["status"], "unchanged")
        self.assertEqual(self.current()["project"]["state_generation"], 1)
        self.assertEqual((self.state_path.read_bytes(), self.framework.read_bytes()), before)

    def test_reference_adopt_and_reject_are_explicit_user_dispositions(self):
        for disposition in ("reference", "adopt", "reject"):
            with self.subTest(disposition=disposition):
                selection = deepcopy(self.selection)
                selection.update(disposition=disposition,
                                 adopted_parts=["Synthetic structural pattern only."] if disposition == "adopt" else [],
                                 rejected_parts=["Continuous allocation absent in target."] if disposition == "reject" else [])
                report = self.preview(selection=selection)
                self.assertEqual(report["status"], "preview")
                self.assertEqual(report["record"]["disposition"], disposition)
                self.assert_non_authorizing(report)
        selection = deepcopy(self.selection)
        selection["disposition"] = "adopt"
        self.assert_blocked(self.preview(selection=selection))

    def test_adoption_needs_current_question_evidence_while_reference_can_be_unassessed(self):
        selection = deepcopy(self.selection)
        selection.update(disposition="adopt", adopted_parts=["Synthetic structural pattern."], current_evidence=[])
        report = self.preview(selection=selection)
        self.assert_blocked(report)
        self.assertIn("invalid_reference", report["errors"])
        for disposition in ("reference", "reject"):
            with self.subTest(disposition=disposition):
                selection.update(disposition=disposition, adopted_parts=[])
                report = self.preview(selection=selection)
                self.assertEqual(report["status"], "preview")
                self.assert_non_authorizing(report)

    def test_missing_question_decision_cannot_be_created_by_preview(self):
        del self.state["decisions"]["Q1"]
        write_state(self.root, self.state)
        before = tree_bytes(self.root)
        self.assert_blocked(self.preview())
        self.assertEqual(tree_bytes(self.root), before)

    def test_missing_unfrozen_contract_and_placeholder_framework_block(self):
        original = self.framework.read_bytes()
        for status in ("pending", "draft"):
            with self.subTest(status=status):
                state = deepcopy(self.state)
                state["subproblems"]["Q1"]["problem_contract_status"] = status
                write_state(self.root, state)
                self.assert_blocked(self.preview())
        write_state(self.root, self.state)
        text = original.decode("utf-8")
        self.framework.write_text(text.replace("本题是独立合成结构", "__QUESTION_NAME__"), encoding="utf-8")
        self.assert_blocked(self.preview())

    def test_duplicate_or_unbound_question_framework_is_rejected(self):
        text = self.framework.read_text(encoding="utf-8")
        self.framework.write_text(text + "\n### Q1：重复合成标题\n", encoding="utf-8")
        self.assert_blocked(self.preview())
        self.framework.write_text(text, encoding="utf-8")
        self.state["subproblems"]["Q1"]["framework_section"] = "### Q1：另一个标题"
        write_state(self.root, self.state)
        self.assert_blocked(self.preview())

    def test_empty_problem_contract_cannot_borrow_the_variables_paragraph(self):
        text = self.framework.read_text(encoding="utf-8")
        start = text.index("**题意口径（Problem Contract）**") + len("**题意口径（Problem Contract）**")
        end = text.index("**变量、假设与模型**", start)
        self.framework.write_text(text[:start] + "\n\n" + text[end:], encoding="utf-8")
        before = tree_bytes(self.root)
        report = self.preview()
        self.assert_blocked(report)
        self.assertIn("frozen_problem_contract_content_required", report["errors"])
        self.assertEqual(tree_bytes(self.root), before)

    def test_classification_and_strict_capability_scope_must_match_current_query(self):
        for mutation in ("objective", "capability", "non_bool", "alias"):
            with self.subTest(mutation=mutation):
                state = deepcopy(self.state)
                entry = state["subproblems"]["Q1"]
                if mutation == "objective":
                    entry["classification"]["objective"] = "prediction"
                elif mutation == "capability":
                    entry["capabilities"]["requires_convergence_diagnostic"] = True
                elif mutation == "non_bool":
                    entry["capabilities"]["has_explicit_constraints"] = "true"
                else:
                    entry["classification"]["capabilities"] = {"has_explicit_constraints": False}
                write_state(self.root, state)
                self.assert_blocked(self.preview())

    def test_selection_cannot_forge_source_identity_or_select_an_unranked_case(self):
        selection = deepcopy(self.selection)
        selection["source_sha256"] = "0" * 64
        self.assert_blocked(self.preview(selection=selection))
        selection = deepcopy(self.selection)
        selection["case_id"] = "CM-SYN-001"
        self.assert_blocked(self.preview(selection=selection))

    def test_empty_or_unknown_selection_fields_are_rejected(self):
        for field, value in (("reason", ""), ("disposition", "approved"), ("unexpected", True)):
            with self.subTest(field=field):
                selection = deepcopy(self.selection)
                selection[field] = value
                self.assert_blocked(self.preview(selection=selection))

    def test_current_evidence_accepts_real_question_anchor_and_relative_file(self):
        path = self.root / "synthetic-evidence.txt"
        path.write_text("Synthetic description only; no checks performed.\n", encoding="utf-8")
        anchor = "**题意口径（Problem Contract）**"
        selection = deepcopy(self.selection)
        selection["current_evidence"] += [
            {"kind": "framework_anchor", "anchor": anchor,
             "sha256": REFERENCES.framework_anchor_sha256(anchor)},
            {"kind": "project_file", "path": path.name,
             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()},
        ]
        self.assertEqual(self.preview(selection=selection)["status"], "preview")

    def test_wrong_scope_missing_anchor_and_wrong_evidence_hash_block(self):
        for evidence in (
            {"kind": "state_field", "pointer": "/subproblems/Q2/classification", "sha256": "0" * 64},
            {"kind": "framework_anchor", "anchor": "Missing synthetic anchor", "sha256": "0" * 64},
            {"kind": "state_field", "pointer": "/subproblems/Q1/classification", "sha256": "0" * 64},
            {"kind": "project_file", "path": "missing.txt", "sha256": "0" * 64},
            {"kind": "project_file", "path": TX.STATE_RELATIVE_PATH,
             "sha256": hashlib.sha256(self.state_path.read_bytes()).hexdigest()},
        ):
            with self.subTest(kind=evidence["kind"], pointer=evidence.get("pointer")):
                selection = deepcopy(self.selection)
                selection["current_evidence"] = [evidence]
                self.assert_blocked(self.preview(selection=selection))

    def test_duplicate_framework_anchor_is_not_current_evidence(self):
        anchor = "仅声明模型设计条件"
        self.framework.write_text(self.framework.read_text(encoding="utf-8").replace(
            anchor, anchor + "；" + anchor), encoding="utf-8")
        selection = deepcopy(self.selection)
        selection["current_evidence"] = [{"kind": "framework_anchor", "anchor": anchor,
                                         "sha256": REFERENCES.framework_anchor_sha256(anchor)}]
        self.assert_blocked(self.preview(selection=selection))

    def test_absolute_escape_and_private_path_diagnostics_do_not_echo_inputs(self):
        secrets = (r"C:\Users\private-account\secret.txt", r"\\private-server\share\secret.txt",
                   "/private-account/secret.txt", "../private-account.txt")
        for secret in secrets:
            with self.subTest(path=secret):
                selection = deepcopy(self.selection)
                selection["current_evidence"] = [{"kind": "project_file", "path": secret, "sha256": "0" * 64}]
                report = self.preview(selection=selection)
                self.assert_blocked(report)
                serialized = json.dumps(report)
                self.assertNotIn("private-account", serialized)
                self.assertNotIn("private-server", serialized)

    def test_stale_generation_state_and_retrieval_hashes_block_write(self):
        preview = self.preview()
        before = self.state_path.read_bytes()
        for options in ({"expected_generation": 1}, {"expected_generation": True},
                        {"expected_state_sha256": "0" * 64},
                        {"expected_retrieval_corpus_sha256": "0" * 64}, {"write": "yes"}):
            with self.subTest(options=options):
                report = self.record(preview=preview, **{"write": True, **options})
                self.assert_blocked(report)
                self.assertEqual(self.state_path.read_bytes(), before)

    def test_raw_state_drift_with_same_generation_size_and_timestamp_blocks(self):
        preview = self.preview()
        change_same_stat(self.state_path)
        changed = self.state_path.read_bytes()
        self.assert_blocked(self.record(preview=preview, write=True))
        self.assertEqual(self.state_path.read_bytes(), changed)

    def test_existing_current_sib_does_not_require_model_approval(self):
        add_synthetic_sib(self.root, self.state)
        self.assertEqual(self.preview()["status"], "preview")
        self.assertEqual(self.state["subproblems"]["Q1"]["human_model_approval_status"], "pending")

    def test_plausible_old_hash_cannot_replace_current_sib_identity(self):
        add_synthetic_sib(self.root, self.state)
        self.state["subproblems"]["Q1"].update(semantic_identity_hash="f" * 64,
                                                approved_semantic_identity_hash="f" * 64,
                                                validated_semantic_identity_hash="f" * 64)
        write_state(self.root, self.state)
        before = self.state_path.read_bytes()
        self.assert_blocked(self.preview())
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_synthetic_approval_declarations_are_preserved_by_reference_write(self):
        add_synthetic_sib(self.root, self.state, declared_approved=True)
        before = deepcopy(self.state["subproblems"])
        report = self.record(write=True)
        self.assertEqual(report["status"], "committed")
        self.assertEqual(self.current()["subproblems"], before)
        self.assert_non_authorizing(report)

    def test_authority_stale_profile_is_preserved_by_reference_write(self):
        entry = self.state["subproblems"]["Q1"]
        entry.update(artifacts_stale=True, result_summary_status="stale",
                     stale_layers=["primary_code", "solution_workbook", "result_analysis_workbook",
                                   "matlab_script", "figure_bundle", "framework"])
        self.state["paper_framework"]["sync_status"] = "stale"
        write_state(self.root, self.state)
        self.assertEqual(STATE.validate_state_payload(self.state, project_root=self.root), [])
        before = deepcopy(self.state)
        self.assertEqual(self.record(write=True)["status"], "committed")
        current = self.current()
        self.assertEqual(current["subproblems"], before["subproblems"])
        self.assertEqual(current["paper_framework"], before["paper_framework"])

    def test_unqualified_synthetic_acceptance_declaration_cannot_be_repaired_by_reference(self):
        # Deliberately invalid control declaration: no real execution/receipt is invented.
        self.state["subproblems"]["Q1"].update(status="solved", primary_execution_status="accepted",
                                                result_quality_status="passed")
        write_state(self.root, self.state)
        before = tree_bytes(self.root)
        self.assert_blocked(self.preview())
        self.assertEqual(tree_bytes(self.root), before)

    def test_precommit_project_scope_and_evidence_changes_block_without_journal(self):
        for target_kind in ("framework", "state", "evidence"):
            with self.subTest(target=target_kind):
                original_state = self.state_path.read_bytes()
                original_framework = self.framework.read_bytes()
                evidence = self.root / "synthetic-evidence.txt"
                evidence.write_bytes(b"Synthetic description.\n")
                selection = deepcopy(self.selection)
                selection["current_evidence"].append({"kind": "project_file", "path": evidence.name,
                    "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest()})
                target = {"framework": self.framework, "state": self.state_path, "evidence": evidence}[target_kind]
                def hook(point):
                    if point == "after_validation":
                        change_same_stat(target)
                report = self.record(selection=selection, write=True, failure_hook=hook)
                self.assert_blocked(report)
                self.assertFalse((self.root / TX.JOURNAL_RELATIVE_PATH).exists())
                self.assertNotIn("case_references", self.current()["decisions"]["Q1"])
                self.state_path.write_bytes(original_state)
                self.framework.write_bytes(original_framework)

    def test_precommit_corpus_source_schema_and_features_changes_block(self):
        for filename, point in (("sources.json", "after_validation"), ("schema.yaml", "after_generation_check"),
                                ("retrieval_features.json", "after_generation_check")):
            with self.subTest(filename=filename):
                path = self.corpus / filename
                original = path.read_bytes()
                before = self.state_path.read_bytes()
                def hook(current_point):
                    if current_point == point:
                        change_same_stat(path)
                report = self.record(write=True, failure_hook=hook)
                self.assert_blocked(report)
                self.assertEqual(self.state_path.read_bytes(), before)
                self.assertFalse((self.root / TX.JOURNAL_RELATIVE_PATH).exists())
                path.write_bytes(original)

    def test_precommit_external_authority_change_is_checked_on_its_actual_path(self):
        path = self.temp / "isolated-retrieval-authority.yaml"
        shutil.copyfile(RETRIEVAL.AUTHORITY_PATH, path)
        before = self.state_path.read_bytes()
        with mock.patch.object(RETRIEVAL, "AUTHORITY_PATH", path):
            def hook(point):
                if point == "after_generation_check":
                    change_same_stat(path)
            report = self.record(write=True, failure_hook=hook)
        self.assert_blocked(report)
        self.assertEqual(self.state_path.read_bytes(), before)
        self.assertFalse((self.root / TX.JOURNAL_RELATIVE_PATH).exists())

    def isolated_writer_skill(self):
        skill = self.temp / "isolated-writer-skill"
        skill.mkdir()
        for relative in REFERENCES.SKILL_INPUTS:
            target = skill / relative
            target.parent.mkdir(exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        return skill

    def test_changed_writer_bytes_cannot_be_bound_to_an_old_loaded_module(self):
        skill = self.isolated_writer_skill()
        path = skill / "scripts/case_references.py"
        before = tree_bytes(self.root)
        with mock.patch.object(REFERENCES, "ROOT", skill):
            self.assertEqual(self.preview()["status"], "preview")
            change_same_stat(path)
            report = self.preview()
        self.assert_blocked(report)
        self.assertIn("source_changed", report["errors"])
        self.assertEqual(tree_bytes(self.root), before)

    def test_precommit_state_schema_change_cannot_commit_an_old_validation(self):
        skill = self.isolated_writer_skill()
        schema = skill / "core/project_state.schema.yaml"
        before = self.state_path.read_bytes()
        with mock.patch.object(REFERENCES, "ROOT", skill):
            def hook(point):
                if point == "after_validation":
                    change_same_stat(schema)
            report = self.record(write=True, failure_hook=hook)
        self.assert_blocked(report)
        self.assertEqual(self.state_path.read_bytes(), before)
        self.assertFalse((self.root / TX.JOURNAL_RELATIVE_PATH).exists())

    def test_prepared_fault_requires_explicit_rollforward_and_keeps_generation_bound(self):
        before = self.state_path.read_bytes()
        def fail(point):
            if point == "after_journal_prepared":
                raise RuntimeError("Synthetic prepared-stage fault.")
        report = self.record(write=True, failure_hook=fail)
        self.assert_blocked(report)
        self.assertTrue(report["recovery_required"])
        self.assertEqual(self.state_path.read_bytes(), before)
        self.assertTrue((self.root / TX.JOURNAL_RELATIVE_PATH).exists())
        self.assert_blocked(self.preview())
        self.assertEqual(self.state_path.read_bytes(), before)
        recovered = TX.recover_project_transaction(self.root)
        self.assertTrue(recovered["recovered"])
        self.assertEqual(recovered["status"], "rolled_forward")
        self.assertEqual(self.current()["project"]["state_generation"], 1)
        self.assertEqual(self.current()["subproblems"], self.state["subproblems"])
        self.assertEqual(self.record(write=True)["status"], "unchanged")

    def test_currentness_inspection_does_not_replay_query_or_change_generation(self):
        self.assertEqual(self.record(write=True)["status"], "committed")
        before = tree_bytes(self.root)
        report = self.inspect()
        self.assertEqual(report["status"], "inspected")
        self.assertEqual(report["records"][0]["status"], "current")
        self.assertTrue(report["ranking_not_recomputed"])
        self.assertTrue(report["original_query_not_available"])
        self.assertFalse(report["numerical_acceptance_revoked"])
        self.assertEqual(tree_bytes(self.root), before)

    def test_historical_query_filter_hashes_are_provenance_not_replayed_currentness(self):
        self.record(write=True)
        state = self.current()
        record = state["decisions"]["Q1"]["case_references"]["records"][0]
        record.update(query_sha256="a" * 64, filter_sha256="b" * 64)
        write_state(self.root, state)
        report = self.inspect()
        self.assertEqual(report["status"], "inspected")
        self.assertEqual(report["records"][0]["status"], "current")
        self.assertTrue(report["original_query_not_available"])

    def test_wrong_persistent_source_identity_requires_review(self):
        self.record(write=True)
        state = self.current()
        state["decisions"]["Q1"]["case_references"]["records"][0]["source_sha256"] = "0" * 64
        write_state(self.root, state)
        before = self.state_path.read_bytes()
        report = self.inspect()
        self.assertEqual(report["records"][0]["status"], "needs_review")
        self.assertIn("case_or_source_changed", report["records"][0]["reasons"])
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_unknown_reference_protocol_and_closed_record_fields_block_consumption(self):
        self.record(write=True)
        original = self.current()
        for mutation in ("protocol", "field"):
            with self.subTest(mutation=mutation):
                state = deepcopy(original)
                container = state["decisions"]["Q1"]["case_references"]
                if mutation == "protocol":
                    container["protocol_version"] = "9.0.0"
                else:
                    container["records"][0]["numerical_evidence_qualified"] = True
                write_state(self.root, state)
                before = self.state_path.read_bytes()
                self.assert_blocked(self.inspect())
                self.assertEqual(self.state_path.read_bytes(), before)

    def test_context_or_current_evidence_drift_requires_review_without_model_changes(self):
        self.record(write=True)
        state = self.current()
        self.framework.write_text(self.framework.read_text(encoding="utf-8").replace(
            "允许连续分配且关系为线性", "当前仍允许连续分配且关系为线性"), encoding="utf-8")
        before = self.state_path.read_bytes()
        report = self.inspect()
        self.assertEqual(report["records"][0]["status"], "needs_review")
        self.assertIn("project_context_changed", report["records"][0]["reasons"])
        self.assertEqual(self.current()["subproblems"], state["subproblems"])
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_withdrawn_case_requires_review_and_does_not_revoke_numerical_acceptance(self):
        self.record(write=True)
        cases = read_json(self.corpus / "cases.json")
        case = next(row for row in cases["cases"] if row["id"] == "CM-SYN-003")
        case.update(status="retired", status_reason="Synthetic reference withdrawn.")
        write_json(self.corpus / "cases.json", cases)
        refresh_corpus(self.corpus)
        before = self.state_path.read_bytes()
        report = self.inspect()
        self.assertEqual(report["records"][0]["status"], "needs_review")
        self.assertIn("case_unavailable", report["records"][0]["reasons"])
        self.assertFalse(report["numerical_acceptance_revoked"])
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_missing_or_stale_retrieval_never_writes_a_reference(self):
        preview = self.preview()
        (self.corpus / "index.json").unlink()
        before = tree_bytes(self.root)
        self.assert_blocked(self.record(preview=preview, write=True))
        self.assertEqual(tree_bytes(self.root), before)
        self.assertFalse((self.corpus / "index.json").exists())

    def test_input_budget_blocks_without_echoing_large_text(self):
        selection = deepcopy(self.selection)
        selection["reason"] = "Synthetic private marker " * 4000
        report = self.preview(selection=selection)
        self.assert_blocked(report)
        self.assertNotIn("Synthetic private marker", json.dumps(report))

    def test_cli_preview_is_readonly_and_invalid_scope_is_nonzero(self):
        query_path, selection_path = self.temp / "query.json", self.temp / "selection.json"
        write_json(query_path, self.query)
        write_json(selection_path, self.selection)
        arguments = ["preview", "--project-root", str(self.root), "--corpus-root", str(self.corpus),
                     "--question", "Q1", "--query", str(query_path), "--selection", str(selection_path)]
        before = tree_bytes(self.root)
        output = io.StringIO()
        with mock.patch.object(sys, "stdout", output):
            self.assertEqual(REFERENCES.main(arguments), 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "preview")
        arguments[arguments.index("Q1")] = "Q99"
        with mock.patch.object(sys, "stdout", io.StringIO()):
            self.assertNotEqual(REFERENCES.main(arguments), 0)
        self.assertEqual(tree_bytes(self.root), before)


if __name__ == "__main__":
    unittest.main()
