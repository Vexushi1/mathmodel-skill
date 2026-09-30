"""C2 scoped receipt eligibility on synthetic projects, not actual review evidence."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import review_receipts as REVIEW
import review_receipt_consumption as CONSUMPTION


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReviewReceiptConsumptionTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "state").mkdir()
        (self.root / "final_latex").mkdir()
        (self.root / "模型论文框架.md").write_text("# Synthetic Q1 model\n", encoding="utf-8")
        (self.root / "final_latex/main.tex").write_text(
            "\\documentclass{article}\n\\begin{document}\n"
            "\\input{body}\n\\end{document}\n", encoding="utf-8",
        )
        (self.root / "final_latex/body.tex").write_text(
            "\\section{Result}\nSynthetic text.\n", encoding="utf-8",
        )
        (self.root / "final_latex/main.pdf").write_bytes(b"synthetic PDF identity\n")
        self.state = {
            "project": {"state_generation": 1},
            "subproblems": {"Q1": {
                "semantic_revision": 1, "semantic_identity_hash": "a" * 64,
                "model_challenge_status": "passed",
                "human_model_approval_status": "pending",
            }},
            "paper_framework": {"claim_consumption_policy": {
                "protocol_version": "1.5.0", "mode": "enforce_selected_paper_claim_chain",
                "paper_source": {"format": "latex", "entrypoint": "final_latex/main.tex"},
            }},
            "artifacts": {"compiled_pdf": "final_latex/main.pdf", "approved_figures": []},
        }
        self.model = yaml.safe_load((ROOT / "core/model_approval_contract.yaml").read_text(encoding="utf-8"))
        self.final_matrix = yaml.safe_load((ROOT / "templates/review/final_review_matrix.yaml").read_text(encoding="utf-8"))
        self.c1_contract = yaml.safe_load((ROOT / "core/review_receipt_contract.yaml").read_text(encoding="utf-8"))
        self.save()

    def save(self) -> None:
        (self.root / "state/project_state.yaml").write_text(
            yaml.safe_dump(self.state, allow_unicode=True, sort_keys=False), encoding="utf-8",
        )

    def requirement(self, gate: str) -> dict:
        if gate == "model_challenge":
            roles = [
                {"role": role, "check_ids": list(self.model["model_challenge"][pass_name]["must_check"])}
                for role, pass_name in CONSUMPTION.MODEL_ROLES.items()
            ]
            objects = ["Q1:model"]
        else:
            families = [row["check_family"] for row in self.final_matrix["coverage"]]
            roles = [
                {"role": role, "check_ids": families}
                for role in ("semantic_reviewer", "final_reviewer")
            ]
            objects = [
                "paper_source:final_latex/main.tex",
                "source:final_latex/main.tex",
                "source:final_latex/body.tex",
                "rendered:final_latex/main.pdf",
            ]
        return {"gate": gate, "questions": ["Q1"], "object_ids": objects, "roles": roles}

    def activate(self, gate: str) -> dict:
        requirement = self.requirement(gate)
        self.state["review_receipt_policy"] = {
            "protocol_version": "1.0.0", "mode": "enforce_scoped",
            "requirements": [requirement],
        }
        self.save()
        return requirement

    def receipt(self, gate: str, role_spec: dict, pass_id: str, objects: list[str]) -> dict:
        role = role_spec["role"]
        scope = {"questions": ["Q1"], "object_ids": list(objects)}
        fields = [
            {"pointer": "/review_receipt_policy",
             "sha256": REVIEW.state_field_sha256(self.state["review_receipt_policy"])},
        ]
        if gate == "model_challenge":
            fields.extend([
                {"pointer": f"/subproblems/Q1/{key}",
                 "sha256": REVIEW.state_field_sha256(self.state["subproblems"]["Q1"][key])}
                for key in ("semantic_revision", "semantic_identity_hash")
            ])
            project_paths = ["模型论文框架.md"]
            criteria_version = self.model["version"]
        else:
            fields.extend([
                {"pointer": "/paper_framework/claim_consumption_policy/paper_source",
                 "sha256": REVIEW.state_field_sha256(
                     self.state["paper_framework"]["claim_consumption_policy"]["paper_source"])},
                {"pointer": "/artifacts/compiled_pdf",
                 "sha256": REVIEW.state_field_sha256(self.state["artifacts"]["compiled_pdf"])},
            ])
            project_paths = ["final_latex/main.tex", "final_latex/body.tex",
                             "final_latex/main.pdf"]
            if (self.root / "final_latex/sections/figure.tex").is_file():
                project_paths.append("final_latex/sections/figure.tex")
            approved = self.state["artifacts"]["approved_figures"]
            if approved:
                fields.append({
                    "pointer": "/artifacts/approved_figures",
                    "sha256": REVIEW.state_field_sha256(approved),
                })
                project_paths.extend(approved)
            criteria_version = "1.0.0"
        project_files = [
            {"path": path, "sha256": sha256(self.root / path)}
            for path in project_paths
        ]
        gate_spec = self.c1_contract["gate_authorities"][gate]
        authority_paths = set(self.c1_contract["required_authority_paths"])
        authority_paths.update(gate_spec["required_paths"])
        authority_paths.update(gate_spec.get("latex_required_paths", []))
        authority_paths.add("core/review_receipt_consumption_contract.yaml")
        authorities = [
            {"path": path, "sha256": sha256(ROOT / path)}
            for path in sorted(authority_paths)
        ]
        snapshot = {
            "state_generation": self.state["project"]["state_generation"],
            "state_fields": fields, "project_files": project_files,
            "authorities": authorities,
            "fingerprint_sha256": REVIEW.snapshot_fingerprint(
                fields, project_files, authorities,
                gate=gate, role=role, scope=scope, criteria_version=criteria_version,
            ),
        }
        return {
            "review_id": f"R-{pass_id}", "gate": gate, "role": role,
            "criteria_version": criteria_version, "scope": scope, "snapshot": snapshot,
            "execution": {"method": "separated_passes", "source_kind": "assistant_record",
                          "source_locator": f"synthetic/{pass_id}", "pass_id": pass_id},
            "checks": [
                {"id": check_id, "object_ids": list(objects), "result": "pass",
                 "evidence_locator": f"synthetic/{pass_id}#{check_id}"}
                for check_id in role_spec["check_ids"]
            ],
            "findings": [], "uncovered": [], "verdict": "pass",
        }

    def install_pair(self, gate: str) -> tuple[dict, dict]:
        requirement = self.activate(gate)
        first, second = [
            self.receipt(gate, role, f"pass-{index}", requirement["object_ids"])
            for index, role in enumerate(requirement["roles"], start=1)
        ]
        self.state["review_receipts"] = {
            "protocol_version": "1.0.0", "records": [first, second],
        }
        self.save()
        return first, second

    def inspect(self, gate: str, questions: list[str] | None = None) -> dict:
        return CONSUMPTION.evaluate_gate(self.root, gate, questions=questions)

    def test_optional_policy_is_closed_and_legacy_state_is_unchanged(self) -> None:
        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        self.assertEqual(schema["version"], "8.14.0")
        policy_schema = schema["$defs"]["review_receipt_policy"]
        self.assertEqual(self.inspect("model_challenge")["status"], "not_assessed")
        good = self.activate("model_challenge")
        self.assertFalse(list(Draft202012Validator(policy_schema).iter_errors(
            self.state["review_receipt_policy"])))
        bad = dict(self.state["review_receipt_policy"])
        bad["mode"] = "observe"
        self.assertTrue(list(Draft202012Validator(policy_schema).iter_errors(bad)))
        self.assertEqual(good["questions"], ["Q1"])
        self.assertEqual(self.inspect("model_challenge")["status"], "failed")

    def test_model_pair_passes_only_scoped_receipt_eligibility(self) -> None:
        self.install_pair("model_challenge")
        result = self.inspect("model_challenge", ["Q1"])
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["qualification"], "scoped_receipt_eligible")
        self.assertEqual(len(result["receipt_ids"]), 2)
        self.assertEqual(len(result["selected_snapshots"]), 2)
        self.assertTrue(result["observed_sources"]["project"])
        self.assertTrue(result["observed_sources"]["skill"])
        # C11/C12: a review never provides numerical reproduction or human approval.
        self.assertEqual(result["numerical_reproduction"], "not_granted")
        self.assertEqual(result["accepted_workbook"], "not_granted")
        self.assertEqual(result["human_model_approval"], "not_granted")
        self.assertEqual(result["final_delivery"], "not_granted")
        self.assertEqual(self.state["subproblems"]["Q1"]["human_model_approval_status"], "pending")

    def test_policy_or_input_change_and_partial_policy_fail_closed(self) -> None:
        first, second = self.install_pair("model_challenge")
        self.state["review_receipt_policy"]["requirements"][0]["object_ids"] = ["Q1:one-constraint"]
        self.save()
        self.assertEqual(self.inspect("model_challenge")["status"], "failed")
        self.state["review_receipt_policy"]["requirements"][0]["object_ids"] = ["Q1:model"]
        self.state["review_receipt_policy"]["requirements"][0]["roles"][0]["check_ids"] = ["problem_contract_fit"]
        self.save()
        self.assertEqual(self.inspect("model_challenge")["status"], "failed")
        self.state["review_receipt_policy"]["requirements"][0]["roles"][0]["check_ids"] = [
            check["id"] for check in first["checks"]
        ]
        self.save()
        self.assertEqual(self.inspect("model_challenge")["status"], "passed")
        self.state["subproblems"]["Q1"]["semantic_identity_hash"] = "b" * 64
        self.save()
        self.assertEqual(self.inspect("model_challenge")["status"], "failed")

    def test_c10_failed_or_unknown_command_and_untrusted_native_claim_fail(self) -> None:
        _, second = self.install_pair("model_challenge")
        second["execution"].update(command="synthetic-check", exit_code=1)
        self.save()
        self.assertEqual(self.inspect("model_challenge")["status"], "failed")
        second["execution"].pop("exit_code")
        self.save()
        self.assertEqual(self.inspect("model_challenge")["status"], "failed")
        second["execution"].pop("command")
        observed_failure = {second["review_id"]: {"command": "synthetic-check", "exit_code": 1}}
        self.assertEqual(CONSUMPTION.evaluate_gate(
            self.root, "model_challenge", host_evidence=observed_failure,
        )["status"], "failed")
        second["execution"].update(method="native_isolated", source_kind="host_record")
        self.save()
        self.assertEqual(self.inspect("model_challenge")["status"], "failed")

    def test_final_review_requires_active_source_and_all_matrix_families(self) -> None:
        self.install_pair("final_review_and_delivery")
        result = self.inspect("final_review_and_delivery")
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["final_delivery"], "not_granted")
        requirement = self.state["review_receipt_policy"]["requirements"][0]
        requirement["object_ids"] = ["paper_source:final_latex/main.tex"]
        self.save()
        self.assertEqual(self.inspect("final_review_and_delivery")["status"], "failed")
        requirement["object_ids"] = self.requirement("final_review_and_delivery")["object_ids"]
        requirement["roles"][0]["check_ids"] = ["edition_compliance"]
        self.save()
        self.assertEqual(self.inspect("final_review_and_delivery")["status"], "failed")

    def test_active_approved_figure_requires_both_role_object_coverage(self) -> None:
        image = self.root / "figures/q1.png"
        image.parent.mkdir()
        image.write_bytes(b"synthetic approved Figure identity")
        nested = self.root / "final_latex/sections/figure.tex"
        nested.parent.mkdir()
        nested.write_text(
            "\\begin{figure}\\includegraphics{../figures/q1.png}"
            "\\caption{Result}\\label{fig:q1}\\end{figure}\n"
            "See \\ref{fig:q1}.\n", encoding="utf-8",
        )
        (self.root / "final_latex/main.tex").write_text(
            "\\documentclass{article}\n\\begin{document}\n"
            "\\input{sections/figure}\n\\end{document}\n", encoding="utf-8",
        )
        self.state["artifacts"]["approved_figures"] = ["figures/q1.png"]
        self.install_pair("final_review_and_delivery")
        missing = self.inspect("final_review_and_delivery")
        self.assertEqual(missing["status"], "failed")
        self.assertTrue(any("figure:figures/q1.png" in issue for issue in missing["issues"]))
        nested_object_id = "source:final_latex/sections/figure.tex"
        object_id = "figure:figures/q1.png"
        self.state["review_receipt_policy"]["requirements"][0]["object_ids"].extend(
            [nested_object_id, object_id]
        )
        policy_digest = REVIEW.state_field_sha256(self.state["review_receipt_policy"])
        for record in self.state["review_receipts"]["records"]:
            record["scope"]["object_ids"].extend([nested_object_id, object_id])
            for check in record["checks"]:
                check["object_ids"].extend([nested_object_id, object_id])
            for field in record["snapshot"]["state_fields"]:
                if field["pointer"] == "/review_receipt_policy":
                    field["sha256"] = policy_digest
            snapshot = record["snapshot"]
            snapshot["fingerprint_sha256"] = REVIEW.snapshot_fingerprint(
                snapshot["state_fields"], snapshot["project_files"],
                snapshot["authorities"], gate=record["gate"], role=record["role"],
                scope=record["scope"], criteria_version=record["criteria_version"],
            )
        self.save()
        self.assertEqual(self.inspect("final_review_and_delivery")["status"], "passed")
        first = self.state["review_receipts"]["records"][0]
        first["scope"]["object_ids"].remove(object_id)
        for check in first["checks"]:
            check["object_ids"].remove(object_id)
        snapshot = first["snapshot"]
        snapshot["fingerprint_sha256"] = REVIEW.snapshot_fingerprint(
            snapshot["state_fields"], snapshot["project_files"], snapshot["authorities"],
            gate=first["gate"], role=first["role"], scope=first["scope"],
            criteria_version=first["criteria_version"],
        )
        self.save()
        self.assertEqual(self.inspect("final_review_and_delivery")["status"], "failed")
        first["scope"]["object_ids"].append(object_id)
        for check in first["checks"]:
            check["object_ids"].append(object_id)
        snapshot["project_files"] = [
            item for item in snapshot["project_files"]
            if item["path"] != "figures/q1.png"
        ]
        snapshot["fingerprint_sha256"] = REVIEW.snapshot_fingerprint(
            snapshot["state_fields"], snapshot["project_files"], snapshot["authorities"],
            gate=first["gate"], role=first["role"], scope=first["scope"],
            criteria_version=first["criteria_version"],
        )
        self.save()
        missing_snapshot = self.inspect("final_review_and_delivery")
        self.assertEqual(missing_snapshot["status"], "failed")

    def test_local_recheck_cannot_replace_full_review(self) -> None:
        first, _ = self.install_pair("final_review_and_delivery")
        full_objects = self.state["review_receipt_policy"]["requirements"][0]["object_ids"]
        first["verdict"] = "fail"
        first["checks"][0]["result"] = "fail"
        first["findings"] = [{
            "id": "F1", "severity": "blocking", "closure": "corrected",
            "evidence_locator": "synthetic/pass-1#F1",
        }]
        local = self.receipt(
            "final_review_and_delivery",
            self.state["review_receipt_policy"]["requirements"][0]["roles"][0],
            "local-recheck", [full_objects[0]],
        )
        local["supersedes"] = [first["review_id"]]
        local["rechecks"] = [{
            "review_id": first["review_id"], "finding_ids": ["F1"],
            "object_ids": [full_objects[0]], "check_ids": [first["checks"][0]["id"]],
        }]
        self.state["review_receipts"]["records"].append(local)
        self.save()
        self.assertEqual(self.inspect("final_review_and_delivery")["status"], "failed")

    def test_scoped_activation_and_candidate_state_mismatch(self) -> None:
        self.install_pair("model_challenge")
        self.assertEqual(self.inspect("final_review_and_delivery")["status"], "not_assessed")
        self.assertEqual(self.inspect("model_challenge", ["Q2"])["status"], "not_assessed")
        self.assertEqual(self.inspect("model_challenge", ["Q1", "Q2"])["status"], "failed")
        candidate = dict(self.state)
        candidate["subproblems"] = {"Q1": dict(self.state["subproblems"]["Q1"])}
        candidate["subproblems"]["Q1"]["semantic_identity_hash"] = "b" * 64
        self.assertEqual(CONSUMPTION.evaluate_gate(
            self.root, "model_challenge", questions=["Q1"], state=candidate,
        )["status"], "failed")

    def test_policy_cannot_declare_a_question_absent_from_current_state(self) -> None:
        self.install_pair("final_review_and_delivery")
        self.state["review_receipt_policy"]["requirements"][0]["questions"] = ["Q99"]
        self.save()
        result = self.inspect("final_review_and_delivery")
        self.assertEqual(result["status"], "failed")
        self.assertTrue(any("Q99" in issue for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()
