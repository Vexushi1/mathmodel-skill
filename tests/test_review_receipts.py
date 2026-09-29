"""C1 receipt regressions on synthetic inputs; no actual review is asserted."""
from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import review_receipts as REVIEW
import claim_tex as TEX


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_bytes(root: Path) -> dict[str, bytes]:
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


class ReviewReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "project"
        self.skill = Path(temp.name) / "skill"
        (self.root / "state").mkdir(parents=True)
        (self.skill / "core").mkdir(parents=True)
        contract = yaml.safe_load((ROOT / "core/review_receipt_contract.yaml").read_text(encoding="utf-8"))
        authority_paths = {"core/project_state.schema.yaml", "core/review_receipt_contract.yaml",
                           "core/model_approval_contract.yaml"}
        for gate in contract["gate_authorities"].values():
            authority_paths.update(gate.get("required_paths", []))
            authority_paths.update(gate.get("latex_required_paths", []))
        for relative in sorted(authority_paths):
            destination = self.skill / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        paper_root = self.root / "final_latex"
        paper_root.mkdir()
        (paper_root / "main.tex").write_text(
            "\\documentclass{article}\n\\begin{document}\n"
            "\\input{body}\n\\end{document}\n", encoding="utf-8")
        (paper_root / "body.tex").write_text(
            "\\section{Synthetic result}\nA small fixture result.\n", encoding="utf-8")
        (paper_root / "decoy.tex").write_text(
            "\\documentclass{article}\n\\begin{document}\nDecoy.\\end{document}\n",
            encoding="utf-8")
        (paper_root / "main.pdf").write_bytes(b"synthetic compiled-PDF identity only\n")
        scanned = TEX.scan_static_latex(self.root, paper_root / "main.tex", selected_carrier=True)
        self.assertEqual(scanned["status"], "scanned", scanned)
        self.assertEqual(set(scanned["files"]), {"final_latex/main.tex", "final_latex/body.tex"})
        (self.root / "模型论文框架.md").write_text(
            "# Synthetic model\nQ1: x = 2. This fixture is not mathematical approval.\n",
            encoding="utf-8",
        )
        self.state = {
            "project": {"state_generation": 3, "competition": "synthetic"},
            "subproblems": {"Q1": {"semantic_revision": 3,
                                   "semantic_identity_hash": "a" * 64}},
            "paper_framework": {"claim_consumption_policy": {
                "protocol_version": "1.5.0", "mode": "enforce_selected_paper_claim_chain",
                "paper_source": {"format": "latex", "entrypoint": "final_latex/main.tex"}}},
            "artifacts": {"compiled_pdf": "final_latex/main.pdf", "approved_figures": []},
        }
        self.state_path = self.root / "state/project_state.yaml"
        self.save()

    def save(self) -> None:
        self.state_path.write_text(
            yaml.safe_dump(self.state, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )

    def snapshot(self, *, gate: str, role: str, scope: dict,
                 criteria_version: str) -> dict:
        if gate == "model_challenge":
            state_fields = [
                {"pointer": f"/subproblems/Q1/{key}",
                 "sha256": REVIEW.state_field_sha256(self.state["subproblems"]["Q1"][key])}
                for key in ("semantic_revision", "semantic_identity_hash")]
            project_paths = ["模型论文框架.md"]
        else:
            source = self.state["paper_framework"]["claim_consumption_policy"]["paper_source"]
            state_fields = [{"pointer": "/paper_framework/claim_consumption_policy/paper_source",
                             "sha256": REVIEW.state_field_sha256(source)}]
            selected = source["entrypoint"]
            if source["format"] == "latex":
                graph = TEX.scan_static_latex(self.root, self.root / selected, selected_carrier=True)
                self.assertEqual(graph["status"], "scanned", graph)
                project_paths = sorted(graph["files"])
            else:
                project_paths = [selected]
            if gate == "final_review_and_delivery":
                state_fields.append({"pointer": "/artifacts/compiled_pdf",
                                     "sha256": REVIEW.state_field_sha256(
                                         self.state["artifacts"]["compiled_pdf"])})
                project_paths.append(self.state["artifacts"]["compiled_pdf"])
        project_files = [{"path": path, "sha256": sha256(self.root / path)}
                         for path in project_paths]
        contract = yaml.safe_load((self.skill / "core/review_receipt_contract.yaml").read_text(encoding="utf-8"))
        spec = contract["gate_authorities"][gate]
        authority_paths = set(spec["required_paths"])
        if gate != "model_challenge" and source["format"] == "latex":
            authority_paths.update(spec.get("latex_required_paths", []))
        authority_paths.add("core/review_receipt_contract.yaml")
        authorities = [
            {"path": relative, "sha256": sha256(self.skill / relative)}
            for relative in sorted(authority_paths)
        ]
        return {
            "state_generation": self.state["project"]["state_generation"],
            "state_fields": state_fields,
            "project_files": project_files,
            "authorities": authorities,
            "fingerprint_sha256": REVIEW.snapshot_fingerprint(
                state_fields, project_files, authorities,
                gate=gate, role=role, scope=scope, criteria_version=criteria_version),
        }

    def receipt(self, review_id: str = "R1", *, role: str = "positive_fitness_review",
                method: str = "separated_passes", pass_id: str = "pass-1",
                gate: str = "model_challenge",
                object_ids: tuple[str, ...] = ("Q1:model",)) -> dict:
        criteria_version = "1.1.0" if gate == "model_challenge" else "1.0.0"
        scope = {"questions": ["Q1"], "object_ids": list(object_ids)}
        if gate == "model_challenge":
            contract = yaml.safe_load((self.skill / "core/model_approval_contract.yaml").read_text(encoding="utf-8"))
            role_key = ("reviewer_pass" if role == "positive_fitness_review"
                        else "devils_advocate_pass")
            check_ids = contract["model_challenge"][role_key]["must_check"]
        else:
            check_ids = ["fit"]
        return {
            "review_id": review_id,
            "gate": gate,
            "role": role,
            "criteria_version": criteria_version,
            "scope": scope,
            "snapshot": self.snapshot(gate=gate, role=role, scope=scope,
                                      criteria_version=criteria_version),
            "execution": {"method": method, "source_kind": "assistant_record",
                          "source_locator": pass_id, "pass_id": pass_id},
            "checks": [{"id": check_id, "object_ids": list(object_ids), "result": "pass",
                        "evidence_locator": f"synthetic-review/{pass_id}#{check_id}"}
                       for check_id in check_ids],
            "findings": [],
            "uncovered": [],
            "verdict": "pass",
        }

    def install(self, *records: dict) -> None:
        self.state["review_receipts"] = {"protocol_version": "1.0.0",
                                         "records": list(records)}
        self.save()

    @staticmethod
    def rebind(record: dict) -> None:
        snapshot = record["snapshot"]
        snapshot["fingerprint_sha256"] = REVIEW.snapshot_fingerprint(
            snapshot["state_fields"], snapshot["project_files"], snapshot["authorities"],
            gate=record["gate"], role=record["role"], scope=record["scope"],
            criteria_version=record["criteria_version"])

    def inspect(self, review_id: str | None = None, host_evidence: dict | None = None) -> dict:
        with patch.object(REVIEW, "ROOT", self.skill):
            return REVIEW.inspect_project(self.root, review_id=review_id,
                                          host_evidence=host_evidence)

    @staticmethod
    def row(report: dict, review_id: str) -> dict:
        return next(row for row in report["receipts"] if row["review_id"] == review_id)

    def test_c01_self_assertion_and_fake_run_id_do_not_prove_independence(self):
        self_check = self.receipt(method="author_self_check")
        self_check["execution"]["source_kind"] = "self_report"
        self_check["independent"] = True  # A forged legacy-style assertion is not evidence.
        self.install(self_check)
        report = self.inspect()
        if report["receipts"]:
            self.assertNotEqual(self.row(report, "R1").get("independence"), "verified_independent")
        else:
            self.assertEqual(report["status"], "blocked")

        native = self.receipt(method="native_isolated")
        native["execution"].update(source_kind="host_record", source_locator="hand-typed-run-id")
        self.install(native)
        report = self.inspect()
        self.assertEqual(self.row(report, "R1")["independence"], "unverified")
        fake_host = {"R1": {"method": "native_isolated", "source_kind": "host_record",
                            "source_locator": "hand-typed-run-id", "pass_id": "pass-1"}}
        report = self.inspect(host_evidence=fake_host)
        self.assertEqual(self.row(report, "R1")["independence"], "unverified")

    def test_c02_old_pass_is_stale_after_bound_input_changes(self):
        self.install(self.receipt())
        self.assertEqual(self.row(self.inspect(), "R1")["applicability"], "current")
        (self.root / "模型论文框架.md").write_text("# Changed model\n", encoding="utf-8")
        self.assertEqual(self.row(self.inspect(), "R1")["applicability"], "stale")

    def test_c03_applicable_authority_changes_only_affected_receipt(self):
        self.install(self.receipt())
        self.assertEqual(self.row(self.inspect(), "R1")["applicability"], "current")
        unrelated = self.skill / "core/unrelated.yaml"
        unrelated.write_text("version: changed\n", encoding="utf-8")
        self.assertEqual(self.row(self.inspect(), "R1")["applicability"], "current")
        criterion = self.skill / "core/model_approval_contract.yaml"
        original_bytes = criterion.read_bytes()
        criterion.write_bytes(criterion.read_bytes() + b"\n# changed criterion\n")
        self.assertEqual(self.row(self.inspect(), "R1")["applicability"], "stale")
        criterion.write_bytes(original_bytes)
        self.state["review_receipts"]["records"][0]["criteria_version"] = "1.2.0"
        self.save()
        self.assertNotEqual(self.inspect()["status"], "current")

    def test_paper_review_tracks_delegated_module06_authority(self):
        record = self.receipt(gate="draft_semantic_review", role="semantic_reviewer")
        self.install(record)
        self.assertEqual(self.inspect()["status"], "current")
        delegated = self.skill / "modules/05_writing/paper_writing_protocol.md"
        delegated.write_bytes(delegated.read_bytes() + b"\n<!-- changed writing Authority -->\n")
        report = self.inspect()
        self.assertEqual(self.row(report, "R1")["applicability"], "stale", report)

    def test_paper_review_binds_selected_main_not_a_decoy(self):
        record = self.receipt(gate="draft_semantic_review", role="semantic_reviewer")
        self.install(record)
        self.assertEqual(self.inspect()["status"], "current")
        decoy = self.root / "final_latex/decoy.tex"
        decoy.write_bytes(decoy.read_bytes() + b"\n% irrelevant decoy change\n")
        self.assertEqual(self.row(self.inspect(), "R1")["applicability"], "current")
        record = self.receipt(gate="draft_semantic_review", role="semantic_reviewer")
        main_row = next(row for row in record["snapshot"]["project_files"]
                        if row["path"] == "final_latex/main.tex")
        main_row.update(path="final_latex/decoy.tex", sha256=sha256(decoy))
        self.rebind(record)
        self.install(record)
        self.assertNotEqual(self.inspect()["status"], "current")

    def test_paper_main_path_guard_failure_returns_blocked_report(self):
        self.install(self.receipt(gate="draft_semantic_review", role="semantic_reviewer"))
        original_guard = REVIEW.PROJECT_TX._guarded_path

        def reject_selected_main(root: Path, relative: str) -> Path:
            if relative == "final_latex/main.tex":
                raise REVIEW.PROJECT_TX.ProjectTransactionError("synthetic paper path alias")
            return original_guard(root, relative)

        with patch.object(REVIEW.PROJECT_TX, "_guarded_path", side_effect=reject_selected_main):
            report = self.inspect()
        self.assertEqual(report["status"], "blocked", report)

    def test_paper_review_binds_active_child_tex(self):
        record = self.receipt(gate="draft_semantic_review", role="semantic_reviewer")
        self.install(record)
        self.assertEqual(self.inspect()["status"], "current")
        child = self.root / "final_latex/body.tex"
        original = child.read_bytes()
        child.write_bytes(original + b"\nChanged active child.\n")
        self.assertEqual(self.row(self.inspect(), "R1")["applicability"], "stale")
        child.write_bytes(original)
        record = self.receipt(gate="draft_semantic_review", role="semantic_reviewer")
        record["snapshot"]["project_files"] = [
            row for row in record["snapshot"]["project_files"]
            if row["path"] != "final_latex/body.tex"]
        self.rebind(record)
        self.install(record)
        self.assertNotEqual(self.inspect()["status"], "current")

    def test_paper_review_binds_approved_active_figure_image(self):
        image = self.root / "figures/q1.png"
        image.parent.mkdir()
        image.write_bytes(b"synthetic image identity")
        (self.root / "final_latex/body.tex").write_text(
            "\\begin{figure}\\includegraphics{../figures/q1.png}"
            "\\caption{Result}\\label{fig:q1}\\end{figure}\n"
            "See \\ref{fig:q1}.\n", encoding="utf-8")
        self.state["artifacts"]["approved_figures"] = ["figures/q1.png"]
        self.save()
        record = self.receipt(gate="draft_semantic_review", role="semantic_reviewer")
        record["snapshot"]["state_fields"].append(
            {"pointer": "/artifacts/approved_figures",
             "sha256": REVIEW.state_field_sha256(self.state["artifacts"]["approved_figures"])})
        record["snapshot"]["project_files"].append(
            {"path": "figures/q1.png", "sha256": sha256(image)})
        self.rebind(record)
        self.install(record)
        self.assertEqual(self.row(self.inspect(), "R1")["applicability"], "current")
        original = image.read_bytes()
        image.write_bytes(b"changed image identity")
        self.assertEqual(self.row(self.inspect(), "R1")["applicability"], "stale")
        image.write_bytes(original)
        record["snapshot"]["project_files"] = [
            row for row in record["snapshot"]["project_files"]
            if row["path"] != "figures/q1.png"]
        self.rebind(record)
        self.install(record)
        self.assertNotEqual(self.inspect()["status"], "current")

    def test_c04_copied_pass_cannot_establish_two_separate_reviews(self):
        first = self.receipt()
        copied = self.receipt("R2", role="adversarial_model_challenge", pass_id="pass-1")
        copied["verdict"] = first["verdict"]
        self.install(first, copied)
        report = self.inspect()
        self.assertNotEqual(report["status"], "current", report)
        self.assertTrue(report["issues"] or any(row["issues"] for row in report["receipts"]))

    def test_c05_distinct_separated_passes_remain_available(self):
        first = self.receipt()
        second = self.receipt("R2", role="adversarial_model_challenge", pass_id="pass-2")
        self.install(first, second)
        report = self.inspect()
        self.assertEqual(report["status"], "current", report)
        self.assertEqual({row["independence"] for row in report["receipts"]},
                         {"separated_passes"})

    def test_c05_separated_passes_need_traceable_source_and_pass_ids(self):
        first = self.receipt()
        second = self.receipt("R2", role="adversarial_model_challenge", pass_id="pass-2")
        for record in (first, second):
            record["execution"].pop("source_locator")
            record["execution"].pop("pass_id")
        self.install(first, second)
        report = self.inspect()
        self.assertEqual(report["status"], "needs_review", report)
        self.assertEqual({row["applicability"] for row in report["receipts"]},
                         {"unverified"})

    def test_c06_corrected_blocker_without_recheck_is_not_closed(self):
        record = self.receipt()
        record["findings"] = [{"id": "F1", "severity": "blocking",
                               "evidence_locator": "synthetic-review/pass-1#F1",
                               "closure": "corrected"}]
        self.install(record)
        report = self.inspect()
        self.assertNotEqual(report["status"], "current", report)

    def test_c06_other_gate_cannot_reverify_model_finding(self):
        original = self.receipt()
        original["findings"] = [{"id": "F1", "severity": "blocking",
                                 "evidence_locator": "synthetic-review/pass-1#F1",
                                 "closure": "reverified"}]
        other_gate = self.receipt("R2", gate="draft_semantic_review",
                                  role="semantic_reviewer", pass_id="pass-2")
        other_gate["checks"] = [
            {**check, "evidence_locator": f"synthetic-review/pass-2#{check['id']}"}
            for check in original["checks"]]
        other_gate["rechecks"] = [{"review_id": "R1", "finding_ids": ["F1"],
                                   "object_ids": ["Q1:model"],
                                   "check_ids": [check["id"] for check in original["checks"]]}]
        self.install(original, other_gate)
        report = self.inspect()
        self.assertNotEqual(report["status"], "current", report)

    def test_c06_local_finding_recheck_keeps_full_review_scope_explicit(self):
        original = self.receipt(role="semantic_reviewer", gate="draft_semantic_review",
                                object_ids=("Q1:A", "Q1:B"))
        original["checks"] = [
            {"id": "A", "object_ids": ["Q1:A"], "result": "fail",
             "evidence_locator": "synthetic-review/pass-1#A"},
            {"id": "B", "object_ids": ["Q1:B"], "result": "pass",
             "evidence_locator": "synthetic-review/pass-1#B"},
        ]
        original["findings"] = [{"id": "F1", "severity": "blocking",
                                 "evidence_locator": "synthetic-review/pass-1#A",
                                 "closure": "reverified", "object_ids": ["Q1:A"],
                                 "check_ids": ["A"]}]
        original["verdict"] = "fail"
        local = self.receipt("R2", role="semantic_reviewer", gate="draft_semantic_review",
                             pass_id="pass-2", object_ids=("Q1:A",))
        local["checks"] = [{"id": "A", "object_ids": ["Q1:A"], "result": "pass",
                            "evidence_locator": "synthetic-review/pass-2#A"}]
        local["rechecks"] = [{"review_id": "R1", "finding_ids": ["F1"],
                              "object_ids": ["Q1:A"], "check_ids": ["A"]}]
        self.install(original, local)
        report = self.inspect()
        self.assertEqual(self.row(report, "R1")["applicability"], "current", report)
        self.assertEqual(self.row(report, "R2")["applicability"], "current", report)
        self.assertEqual(report["status"], "needs_review", report)
        self.assertNotIn("supersedes", local)

    def test_c06_full_new_pass_can_recheck_only_affected_finding(self):
        original = self.receipt(role="semantic_reviewer", gate="draft_semantic_review",
                                object_ids=("Q1:A", "Q1:B"))
        original["checks"][0].update(id="A", object_ids=["Q1:A"], result="fail")
        original["checks"].append({"id": "B", "object_ids": ["Q1:B"], "result": "pass",
                                   "evidence_locator": "synthetic-review/pass-1#B"})
        original["findings"] = [{"id": "F1", "severity": "blocking",
                                 "evidence_locator": "synthetic-review/pass-1#A",
                                 "closure": "reverified", "object_ids": ["Q1:A"],
                                 "check_ids": ["A"]}]
        original["verdict"] = "fail"
        successor = self.receipt("R2", role="semantic_reviewer", gate="draft_semantic_review",
                                 pass_id="pass-2", object_ids=("Q1:A", "Q1:B"))
        successor["checks"] = [
            {"id": check_id, "object_ids": [object_id], "result": "pass",
             "evidence_locator": f"synthetic-review/pass-2#{check_id}"}
            for check_id, object_id in (("A", "Q1:A"), ("B", "Q1:B"))]
        successor["rechecks"] = [{"review_id": "R1", "finding_ids": ["F1"],
                                  "object_ids": ["Q1:A"], "check_ids": ["A"]}]
        self.install(original, successor)
        report = self.inspect()
        self.assertEqual(self.row(report, "R1")["applicability"], "current", report)
        self.assertEqual(self.row(report, "R2")["applicability"], "current", report)
        self.assertEqual(report["status"], "needs_review", report)
        self.assertNotIn("supersedes", successor)

    def test_c07_partial_recheck_cannot_claim_full_scope(self):
        original = self.receipt(role="semantic_reviewer", gate="draft_semantic_review",
                                object_ids=("Q1:A", "Q1:B"))
        original["checks"] = [
            {"id": "A", "object_ids": ["Q1:A"], "result": "fail",
             "evidence_locator": "synthetic-review/pass-1#A"},
            {"id": "B", "object_ids": ["Q1:B"], "result": "pass",
             "evidence_locator": "synthetic-review/pass-1#B"},
        ]
        original["findings"] = [{"id": "F1", "severity": "blocking",
                                 "evidence_locator": "synthetic-review/pass-1#A", "closure": "open"}]
        original["verdict"] = "fail"
        partial = self.receipt("R2", role="semantic_reviewer", gate="draft_semantic_review",
                               pass_id="pass-2", object_ids=("Q1:A", "Q1:B"))
        partial["checks"] = [{"id": "A", "object_ids": ["Q1:A"], "result": "pass",
                              "evidence_locator": "synthetic-review/pass-2#A"}]
        partial["supersedes"] = ["R1"]
        partial["rechecks"] = [{"review_id": "R1", "finding_ids": ["F1"],
                                "object_ids": ["Q1:A"], "check_ids": ["A"]}]
        self.install(original, partial)
        report = self.inspect()
        self.assertNotEqual(report["status"], "current", report)
        issues = " ".join(self.row(report, "R2")["issues"])
        self.assertIn("PASS omits declared review objects", issues, report)
        self.assertIn("supersede full review", issues, report)

    def test_c07_finding_scope_must_match_original_check_objects(self):
        original = self.receipt(role="semantic_reviewer", gate="draft_semantic_review",
                                object_ids=("Q1:A", "Q1:B"))
        original["checks"] = [
            {"id": "A", "object_ids": ["Q1:A"], "result": "fail",
             "evidence_locator": "synthetic-review/pass-1#A"},
            {"id": "B", "object_ids": ["Q1:B"], "result": "pass",
             "evidence_locator": "synthetic-review/pass-1#B"},
        ]
        original["findings"] = [{"id": "F1", "severity": "blocking",
                                 "evidence_locator": "synthetic-review/pass-1#A",
                                 "closure": "reverified", "object_ids": ["Q1:A"],
                                 "check_ids": ["B"]}]
        original["verdict"] = "fail"
        unrelated = self.receipt("R2", role="semantic_reviewer",
                                 gate="draft_semantic_review", pass_id="pass-2",
                                 object_ids=("Q1:A",))
        unrelated["checks"] = [{"id": "B", "object_ids": ["Q1:A"], "result": "pass",
                                "evidence_locator": "synthetic-review/pass-2#B"}]
        unrelated["rechecks"] = [{"review_id": "R1", "finding_ids": ["F1"],
                                   "object_ids": ["Q1:A"], "check_ids": ["B"]}]
        self.install(original, unrelated)
        report = self.inspect()
        self.assertEqual(self.row(report, "R1")["applicability"], "unverified", report)
        self.assertIn("not linked", " ".join(self.row(report, "R1")["issues"]), report)

    def test_c07_pass_requires_union_coverage_of_declared_objects(self):
        record = self.receipt(object_ids=("Q1:A", "Q1:B"))
        for check in record["checks"]:
            check["object_ids"] = ["Q1:A"]
        self.install(record)
        report = self.inspect()
        self.assertNotEqual(report["status"], "current", report)

    def test_c08_receipt_write_and_unrelated_generation_do_not_self_invalidate(self):
        self.install(self.receipt())
        self.assertEqual(self.row(self.inspect(), "R1")["applicability"], "current")
        self.state["review_receipts"]["records"][0]["snapshot"]["state_fields"].reverse()
        self.state["review_receipts"]["records"][0]["snapshot"]["authorities"].reverse()
        self.save()
        self.assertEqual(self.row(self.inspect(), "R1")["applicability"], "current")
        self.state["project"]["state_generation"] += 1
        self.state["review_receipts"]["records"][0]["execution"]["source_locator"] = "pass-1-updated"
        self.save()
        self.assertEqual(self.row(self.inspect(), "R1")["applicability"], "current")
        self.state["subproblems"]["Q1"]["semantic_identity_hash"] = "b" * 64
        self.save()
        self.assertEqual(self.row(self.inspect(), "R1")["applicability"], "stale")

    def test_c08_raw_state_file_cannot_be_a_review_input(self):
        record = self.receipt()
        record["snapshot"]["project_files"].append(
            {"path": "state/project_state.yaml", "sha256": sha256(self.state_path)})
        record["snapshot"]["fingerprint_sha256"] = REVIEW.snapshot_fingerprint(
            record["snapshot"]["state_fields"], record["snapshot"]["project_files"],
            record["snapshot"]["authorities"], gate=record["gate"], role=record["role"],
            scope=record["scope"], criteria_version=record["criteria_version"])
        self.install(record)
        report = self.inspect()
        self.assertEqual(report["status"], "blocked", report)

    def test_array_json_pointer_tracks_exact_element(self):
        self.state["subproblems"]["Q1"]["review_inputs"] = [
            {"id": "A", "value": 1}, {"id": "B", "value": 2}]
        record = self.receipt()
        record["snapshot"]["state_fields"].append(
            {"pointer": "/subproblems/Q1/review_inputs/1/value",
             "sha256": REVIEW.state_field_sha256(2)})
        self.rebind(record)
        self.install(record)
        self.assertEqual(self.row(self.inspect(), "R1")["applicability"], "current")
        self.state["subproblems"]["Q1"]["review_inputs"][1]["value"] = 3
        self.save()
        self.assertEqual(self.row(self.inspect(), "R1")["applicability"], "stale")

    def test_model_receipt_requires_actual_semantic_identity_references(self):
        record = self.receipt()
        record["snapshot"]["state_fields"] = [
            {"pointer": "/project/competition",
             "sha256": REVIEW.state_field_sha256(self.state["project"]["competition"])}]
        record["snapshot"]["fingerprint_sha256"] = REVIEW.snapshot_fingerprint(
            record["snapshot"]["state_fields"], record["snapshot"]["project_files"],
            record["snapshot"]["authorities"], gate=record["gate"], role=record["role"],
            scope=record["scope"], criteria_version=record["criteria_version"])
        self.install(record)
        self.assertNotEqual(self.inspect()["status"], "current")

    def test_model_pass_with_no_checks_cannot_be_current(self):
        record = self.receipt()
        record["checks"] = []
        self.install(record)
        self.assertNotEqual(self.inspect()["status"], "current")

    def test_c09_object_change_during_inspection_cannot_return_current(self):
        self.install(self.receipt())
        original = REVIEW._gate_authority_issues

        def interleave(*args, **kwargs):
            result = original(*args, **kwargs)
            (self.root / "模型论文框架.md").write_text("# Changed during inspection\n", encoding="utf-8")
            return result

        with patch.object(REVIEW, "_gate_authority_issues", side_effect=interleave):
            report = self.inspect()
        self.assertEqual(report["status"], "blocked", report)
        if report["receipts"]:
            self.assertNotEqual(self.row(report, "R1")["applicability"], "current", report)

    def test_inspection_is_read_only_and_missing_or_unknown_protocol_is_explicit(self):
        before = tree_bytes(self.root)
        self.assertEqual(self.inspect()["status"], "not_assessed")
        self.assertEqual(before, tree_bytes(self.root))
        self.install(self.receipt())
        before = tree_bytes(self.root)
        self.assertEqual(self.inspect()["status"], "current")
        self.assertEqual(before, tree_bytes(self.root))
        self.state["review_receipts"]["protocol_version"] = "999.0.0"
        self.save()
        before = tree_bytes(self.root)
        self.assertEqual(self.inspect()["status"], "blocked")
        self.assertEqual(before, tree_bytes(self.root))


if __name__ == "__main__":
    unittest.main()
