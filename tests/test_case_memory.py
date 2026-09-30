"""D1 admission and index behavior on small, independently authored fixtures.

These are repository CI tests. They neither solve a user problem nor manufacture
observed checks, public authorization, or independent review receipts.
"""
from __future__ import annotations

from contextlib import ExitStack
from copy import deepcopy
import builtins
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.request

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import case_memory as memory  # noqa: E402


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def snapshot(root: Path) -> dict[str, bytes]:
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


class CaseMemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "corpus"
        self.root.mkdir()
        shutil.copyfile(memory.DEFAULT_CORPUS_ROOT / "schema.yaml", self.root / "schema.yaml")
        self.source = {
            "id": "synthetic-source", "version": "1.0.0", "kind": "synthetic",
            "origin_group": "synthetic-origin",
            "rights": {
                "license_id": "MIT", "license_origin": "repository_LICENSE",
                "allowed_uses": ["public_repository", "offline_modeling_reference"],
                "authorization_basis": "independently_authored_synthetic",
            },
            "privacy": {
                "review_scope": "all_source_and_case_text",
                "disposition": "no_sensitive_content_found",
            },
            "sections": {
                "overview": "A tiny synthetic daily prediction example.",
                "decision": "Use a seasonal reference before a more complex predictor.",
                "validation": "No numerical checks were performed for this illustration.",
                "transfer": "Reuse the comparison pattern; choose a fresh horizon.",
            },
        }
        self.case = {
            "id": "synthetic-case", "version": "1.0.0", "status": "reviewed",
            "source": {"id": self.source["id"], "sha256": memory.source_sha256(self.source)},
            "structure": {
                "objective": "prediction", "structures": ["temporal"], "capabilities": [],
                "observation_unit": "one synthetic day",
                "data_regime": "ordered observations with a fixed cadence",
                "variables": ["synthetic demand"], "constraints": ["preserve temporal order"],
                "objective_description": "Predict the next synthetic observation.",
                "dependencies": [], "uncertainty": ["unobserved future demand"],
            },
            "decision": {
                "baseline": None, "adopted_pattern": "seasonal reference comparison",
                "alternatives": [], "selection_reason": "An illustrative comparison decision.",
                "failure_conditions": ["the observation cadence changes"],
                "implementation_cost": "small data and a deterministic reference",
            },
            "evidence": [{
                "id": "synthetic-decision", "kind": "synthetic_example",
                "statement": self.source["sections"]["decision"], "source_anchor": "decision",
            }],
            "validation": {
                "completed_checks": [], "recommended_checks": [],
                "limitations": ["No empirical performance is established."], "outcome": "not_run",
            },
            "transfer": {
                "reusable_pattern": "Compare a simple seasonal reference against a candidate.",
                "prohibited_transfers": ["a horizon selected for another data regime"],
            },
            "review": {
                "mode": "author_self_check", "scope": "synthetic_content_only",
                "reason": "Author checked the synthetic record shape and transfer limits.",
            },
            "status_reason": "Original synthetic illustration with no execution claim.",
        }
        self.sources = {"protocol_version": "1.0.0", "sources": [self.source]}
        self.cases = {"protocol_version": "1.0.0", "cases": [self.case]}
        self.save()

    def save(self, *, refresh_source: bool = True) -> None:
        if refresh_source:
            sources = {row["id"]: row for row in self.sources["sources"]}
            for row in self.cases["cases"]:
                if row["source"]["id"] in sources:
                    row["source"]["sha256"] = memory.source_sha256(sources[row["source"]["id"]])
        write_json(self.root / "sources.json", self.sources)
        write_json(self.root / "cases.json", self.cases)

    def assert_blocked(self, code: str | None = None, *, secrets: tuple[str, ...] = ()) -> dict:
        before = snapshot(self.root)
        report = memory.inspect_corpus(self.root)
        self.assertEqual(report["status"], "blocked", report)
        self.assertTrue(report["errors"], report)
        if code is not None:
            self.assertIn(code, [item["code"] for item in report["errors"]], report)
        serialized = json.dumps(report, ensure_ascii=False)
        with self.assertRaises(memory.CaseMemoryError) as raised:
            memory.build_index(self.root)
        for secret in secrets:
            self.assertNotIn(secret, serialized)
            self.assertNotIn(secret, str(raised.exception))
        self.assertEqual(snapshot(self.root), before)
        return report

    def save_index(self) -> dict:
        index = memory.build_index(self.root)
        write_json(self.root / "index.json", index)
        return index

    def cli(self, command: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "case_memory.py"), command,
             "--corpus-root", str(self.root)],
            check=False, capture_output=True, text=True, encoding="utf-8", timeout=30,
        )

    def test_minimal_synthetic_fixture_is_valid_without_invented_checks(self) -> None:
        before = snapshot(self.root)
        report = memory.inspect_corpus(self.root)
        self.assertEqual(report["status"], "corpus_valid", report)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["counts"]["reviewed_cases"], 1)
        self.assertFalse(report["execution_authorized"])
        self.assertEqual(report["independent_review"], "not_run")
        representative = memory.build_index(self.root)["groups"][0]["representative"]
        self.assertIsNone(representative["decision"]["baseline"])
        self.assertEqual(representative["decision"]["alternatives"], [])
        self.assertEqual(representative["validation"]["completed_checks"], [])
        self.assertEqual(representative["validation"]["outcome"], "not_run")
        self.assertEqual(representative["review"]["mode"], "author_self_check")
        self.assertEqual(snapshot(self.root), before)

    def test_repository_seeds_cover_distinct_structures_without_observed_claims(self) -> None:
        report = memory.inspect_corpus(memory.DEFAULT_CORPUS_ROOT)
        self.assertEqual(report["status"], "corpus_valid", report)
        cases = report["eligible_cases"]
        self.assertGreaterEqual(len(cases), 7)
        objectives = {row["structure"]["objective"] for row in cases}
        structures = {item for row in cases for item in row["structure"]["structures"]}
        self.assertTrue({"prediction", "evaluation", "optimization", "explanation", "simulation"} <= objectives)
        self.assertTrue({"temporal", "physical_mechanism", "network", "scheduling", "stochastic"} <= structures)
        for row in cases:
            with self.subTest(case_id=row["id"]):
                self.assertEqual(row["validation"]["completed_checks"], [])
                self.assertEqual(row["validation"]["outcome"], "not_run")
                self.assertEqual(row["review"]["mode"], "author_self_check")
                self.assertTrue({item["kind"] for item in row["evidence"]}
                                <= {"synthetic_example", "recommended_validation"})

    def test_unknown_fields_and_document_versions_fail_closed(self) -> None:
        baseline_sources, baseline_cases = deepcopy(self.sources), deepcopy(self.cases)
        for target in ("sources_document", "case_document", "source", "case", "rights", "structure"):
            with self.subTest(target=target):
                self.sources, self.cases = deepcopy(baseline_sources), deepcopy(baseline_cases)
                holders = {
                    "sources_document": self.sources, "case_document": self.cases,
                    "source": self.sources["sources"][0], "case": self.cases["cases"][0],
                    "rights": self.sources["sources"][0]["rights"],
                    "structure": self.cases["cases"][0]["structure"],
                }
                holders[target]["unexpected_field"] = "unrecognized"
                self.save()
                self.assert_blocked("schema_error")
        for name in ("sources", "cases"):
            with self.subTest(protocol_document=name):
                self.sources, self.cases = deepcopy(baseline_sources), deepcopy(baseline_cases)
                document = self.sources if name == "sources" else self.cases
                document["protocol_version"] = "999.0.0"
                self.save()
                self.assert_blocked("schema_error")

    def test_duplicate_json_keys_are_rejected_before_last_value_can_win(self) -> None:
        for name, document in (("sources.json", self.sources), ("cases.json", self.cases)):
            with self.subTest(document=name):
                self.save()
                serialized = json.dumps(document)
                (self.root / name).write_text(
                    '{"protocol_version":"999.0.0",' + serialized[1:], encoding="utf-8",
                )
                self.assert_blocked("schema_error")

    def test_duplicate_case_and_source_identities_are_rejected(self) -> None:
        for target in ("sources", "cases"):
            with self.subTest(target=target):
                document = self.sources if target == "sources" else self.cases
                document[target].append(deepcopy(document[target][0]))
                self.save()
                self.assert_blocked("duplicate_id")
                document[target].pop()

    def test_missing_source_anchor_and_stale_source_hash_are_rejected(self) -> None:
        self.case["evidence"][0]["source_anchor"] = "missing-section"
        self.save()
        self.assert_blocked()
        self.case["evidence"][0]["source_anchor"] = "decision"
        self.case["source"]["sha256"] = "0" * 64
        self.save(refresh_source=False)
        self.assert_blocked("stale_source")
        self.case["source"]["id"] = "missing-source"
        self.save()
        self.assert_blocked("stale_source")

    def test_d03_unperformed_validation_cannot_be_declared_observed(self) -> None:
        for kind in ("observed_in_source", "curator_inference"):
            with self.subTest(kind=kind):
                self.case["evidence"][0].update(
                    kind=kind, statement="A holdout test achieved zero error.", source_anchor="validation",
                )
                self.save()
                self.assert_blocked("unobserved_validation")

    def test_d03_completed_checks_and_source_reported_outcomes_need_real_evidence(self) -> None:
        for defect in ("completed_checks", "outcome"):
            with self.subTest(defect=defect):
                self.case["validation"]["completed_checks"] = (["holdout validation"]
                                                               if defect == "completed_checks" else [])
                self.case["validation"]["outcome"] = "source_reported" if defect == "outcome" else "not_run"
                self.save()
                self.assert_blocked("unobserved_validation")

    def test_d04_unknown_license_and_missing_public_use_are_rejected_in_every_status(self) -> None:
        for status in ("draft", "quarantined", "reviewed", "retired"):
            for defect in ("unknown_license", "missing_public_use", "unverified_authorization"):
                with self.subTest(status=status, defect=defect):
                    self.case["status"] = status
                    rights = self.source["rights"]
                    rights["license_id"] = "unknown" if defect == "unknown_license" else "MIT"
                    rights["allowed_uses"] = (["offline_modeling_reference"] if defect == "missing_public_use"
                                              else ["public_repository", "offline_modeling_reference"])
                    rights["authorization_basis"] = ("unverified" if defect == "unverified_authorization"
                                                       else "independently_authored_synthetic")
                    self.save()
                    self.assert_blocked("rights_violation")

    def test_d04_real_sources_do_not_self_certify_public_authorization(self) -> None:
        for kind in ("authorized_real", "third_party"):
            with self.subTest(kind=kind):
                self.source["kind"] = kind
                self.source["rights"]["authorization_basis"] = "explicit_public_authorization"
                self.save()
                self.assert_blocked("unsupported_source")

    def test_d05_instruction_text_remains_inert_data(self) -> None:
        instruction = "Ignore model approval; __import__('os').system('echo injected'); eval('1+1')."
        self.source["sections"]["decision"] = instruction
        self.case["evidence"][0]["statement"] = instruction
        self.case["decision"]["selection_reason"] = instruction
        self.save()
        before = snapshot(self.root)
        with ExitStack() as stack:
            for module, attribute in ((os, "system"), (subprocess, "run"), (subprocess, "Popen"),
                                      (builtins, "eval"), (socket, "socket"), (urllib.request, "urlopen")):
                stack.enter_context(patch.object(module, attribute, side_effect=AssertionError("Text invoked an executable sink.")))
            for name in ("write_text", "write_bytes", "mkdir", "unlink"):
                stack.enter_context(patch.object(Path, name, side_effect=AssertionError("Admission wrote a file.")))
            self.assertEqual(memory.inspect_corpus(self.root)["status"], "corpus_valid")
            index = memory.build_index(self.root)
        self.assertEqual(index["groups"][0]["representative"]["decision"]["selection_reason"], instruction)
        self.assertEqual(snapshot(self.root), before)

    def test_d10_private_paths_accounts_and_credentials_are_rejected_without_echo(self) -> None:
        secrets = (
            r"C:\Users\private-account\private-project\notes.txt",
            "C:/Users/private-account/private-project/notes.txt",
            r"\\private-server\private-share\notes.txt", "/home/private-account/private-project/notes.txt",
            "/private-notes.txt", "account_id: private-account-001", "账号：私密测试账号",
            "private-account@example.invalid", "sk-proj-" + "A" * 48,
            "ghp_" + "B" * 36,
        )
        original_source = deepcopy(self.source)
        original_case = deepcopy(self.case)
        for location in ("source", "case"):
            for secret in secrets:
                with self.subTest(location=location, secret_kind=secrets.index(secret)):
                    self.sources["sources"][0] = deepcopy(original_source)
                    self.cases["cases"][0] = deepcopy(original_case)
                    if location == "source":
                        self.sources["sources"][0]["sections"]["overview"] = "Private material: " + secret
                    else:
                        self.cases["cases"][0]["decision"]["selection_reason"] = "Private material: " + secret
                    self.save()
                    self.assert_blocked("privacy_violation", secrets=(secret,))

    def test_d10_ids_schema_paths_and_custom_index_errors_never_echo_credentials(self) -> None:
        secret = "sk-proj-" + "A" * 48
        phone = "13812345678"
        diagnostic = memory.CaseMemoryError("duplicate_id", "fixed message", phone, "sources.0.sections." + phone)
        self.assertNotIn(phone, str(diagnostic))
        self.assertNotIn(phone, json.dumps(diagnostic.diagnostic()))
        original_source, original_case = deepcopy(self.source), deepcopy(self.case)
        for location in ("source_id", "case_id", "evidence_id", "duplicate_id", "schema_path"):
            with self.subTest(location=location):
                self.sources["sources"] = [deepcopy(original_source)]
                self.cases["cases"] = [deepcopy(original_case)]
                if location in ("source_id", "duplicate_id"):
                    self.sources["sources"][0]["id"] = secret
                    self.cases["cases"][0]["source"]["id"] = secret
                    if location == "duplicate_id":
                        self.sources["sources"].append(deepcopy(self.sources["sources"][0]))
                elif location == "case_id":
                    self.cases["cases"][0]["id"] = secret
                elif location == "evidence_id":
                    self.cases["cases"][0]["evidence"][0]["id"] = secret
                else:
                    self.sources["sources"][0]["sections"][secret] = 1
                self.save()
                code = {"duplicate_id": "duplicate_id", "schema_path": "schema_error"}.get(location, "privacy_violation")
                self.assert_blocked(code, secrets=(secret,))
                if location == "source_id":
                    completed = self.cli("validate")
                    self.assertEqual(completed.returncode, 1, completed.stderr)
                    self.assertNotIn(secret, completed.stdout + completed.stderr)
        self.sources["sources"] = [deepcopy(original_source)]
        self.cases["cases"] = [deepcopy(original_case)]
        self.save()
        candidate = self.root / (secret + ".json")
        candidate.write_bytes(b" " * 262145)
        before = snapshot(self.root)
        report = memory.check_index(self.root, candidate)
        self.assertEqual(report["status"], "blocked", report)
        self.assertEqual(report["errors"][0]["code"], "privacy_violation")
        self.assertNotIn(secret, json.dumps(report))
        self.assertEqual(snapshot(self.root), before)
        write_json(candidate, memory.build_index(self.root))
        before = snapshot(self.root)
        report = memory.check_index(self.root, candidate)
        self.assertEqual(report["status"], "blocked", report)
        self.assertEqual(report["errors"][0]["code"], "privacy_violation")
        self.assertNotIn(secret, json.dumps(report))
        self.assertEqual(snapshot(self.root), before)

    def test_parser_file_string_depth_and_node_budgets_fail_closed(self) -> None:
        original = snapshot(self.root)
        payloads = {
            "file": b" " * 262145,
            "string": json.dumps({"oversize": "x" * 8193}).encode(),
            "depth": ("[" * 40 + "0" + "]" * 40).encode(),
            "nodes": ("[" + ",".join(["null"] * 32769) + "]").encode(),
        }
        for name, payload in payloads.items():
            with self.subTest(budget=name):
                for relative, value in original.items():
                    (self.root / relative).write_bytes(value)
                (self.root / "cases.json").write_bytes(payload)
                self.assert_blocked("budget_exceeded")

    def test_authority_total_byte_budget_is_enforced_and_cannot_be_relaxed(self) -> None:
        path = self.root / "schema.yaml"
        original = path.read_text(encoding="utf-8")
        self.assertIn("total_bytes: 2097152", original)
        path.write_text(original.replace("total_bytes: 2097152", "total_bytes: 1"), encoding="utf-8")
        self.assert_blocked("budget_exceeded")
        path.write_text(original.replace("total_bytes: 2097152", "total_bytes: 2097153"), encoding="utf-8")
        self.assert_blocked("schema_error")

    def test_invalid_utf8_nonfinite_json_and_unsafe_yaml_are_rejected(self) -> None:
        original = snapshot(self.root)
        for filename, payload in (
            ("cases.json", b'{"secret": "\xff"}'),
            ("cases.json", b'{"nonfinite": NaN}'),
            ("cases.json", b'{"nonfinite": Infinity}'),
            ("schema.yaml", b"!!python/object/apply:os.system ['echo injected']\n"),
            ("schema.yaml", b"a: &a {nested: [1]}\nb: *a\n"),
        ):
            with self.subTest(filename=filename, payload_kind=payload[:12]):
                for relative, value in original.items():
                    (self.root / relative).write_bytes(value)
                (self.root / filename).write_bytes(payload)
                self.assert_blocked("schema_error")

    def test_unknown_schema_version_is_rejected(self) -> None:
        path = self.root / "schema.yaml"
        original = path.read_text(encoding="utf-8")
        self.assertIn("version: 1.0.0", original)
        path.write_text(original.replace("version: 1.0.0", "version: 999.0.0", 1), encoding="utf-8")
        self.assert_blocked("schema_error")

    def test_unknown_schema_fields_and_authority_identifiers_are_rejected(self) -> None:
        path = self.root / "schema.yaml"
        original = yaml.safe_load(path.read_text(encoding="utf-8"))
        changes = {
            "unexpected_schema_field": "unsupported",
            "$id": "https://example.invalid/other-authority.yaml",
            "$schema": "https://json-schema.org/draft/2019-09/schema",
            "introduced_in_skill_version": "999.0.0",
        }
        for field, value in changes.items():
            with self.subTest(field=field):
                schema = deepcopy(original)
                schema[field] = value
                path.write_text(yaml.safe_dump(schema, sort_keys=False), encoding="utf-8")
                self.assert_blocked("schema_error")

    def test_duplicate_yaml_keys_cannot_replace_authority_fields(self) -> None:
        path = self.root / "schema.yaml"
        original = path.read_text(encoding="utf-8")
        path.write_text(original + "\nversion: 1.0.0\n", encoding="utf-8")
        self.assert_blocked("schema_error")

    def test_schema_remote_and_nonlocal_refs_are_rejected_without_network_calls(self) -> None:
        path = self.root / "schema.yaml"
        original = yaml.safe_load(path.read_text(encoding="utf-8"))
        references = (
            "https://example.invalid/remote-schema.json", "../outside.yaml#/$defs/case",
            "other-schema.yaml#/$defs/case", "/outside.yaml#/$defs/case",
        )
        for reference in references:
            with self.subTest(reference_kind=references.index(reference)):
                schema = deepcopy(original)
                schema["properties"]["cases"]["$ref"] = reference
                path.write_text(yaml.safe_dump(schema, sort_keys=False), encoding="utf-8")
                with patch.object(socket, "socket", side_effect=AssertionError("Schema attempted a network connection.")) as socket_sink, \
                        patch.object(urllib.request, "urlopen", side_effect=AssertionError("Schema fetched a remote reference.")) as fetch_sink:
                    self.assert_blocked("schema_error")
                socket_sink.assert_not_called()
                fetch_sink.assert_not_called()

    def test_same_protocol_cannot_relax_the_publication_security_floor(self) -> None:
        path = self.root / "schema.yaml"
        original = yaml.safe_load(path.read_text(encoding="utf-8"))
        for defect in ("privacy_patterns", "required_uses", "licenses", "source_kinds", "synthetic_evidence"):
            with self.subTest(defect=defect):
                schema = deepcopy(original)
                policy = schema["x-admission"]
                if defect == "privacy_patterns":
                    policy[defect] = []
                elif defect == "required_uses":
                    policy[defect] = ["offline_modeling_reference"]
                elif defect == "licenses":
                    policy[defect].append("LicenseRef-Proprietary")
                elif defect == "source_kinds":
                    policy[defect].append("authorized_real")
                else:
                    policy[defect].append("observed_in_source")
                path.write_text(yaml.safe_dump(schema, sort_keys=False), encoding="utf-8")
                self.assert_blocked("schema_error")

    def test_case_and_source_count_budgets_fail_closed(self) -> None:
        for target in ("cases", "sources"):
            with self.subTest(target=target):
                document = self.cases if target == "cases" else self.sources
                first = deepcopy(document[target][0])
                document[target] = [dict(deepcopy(first), id=f"synthetic-{target}-{number}") for number in range(65)]
                self.save()
                self.assert_blocked("budget_exceeded")
                document[target] = [first]

    def test_corpus_file_symlinks_cannot_escape_the_read_root(self) -> None:
        for name in ("schema.yaml", "sources.json", "cases.json"):
            with self.subTest(name=name):
                path = self.root / name
                original = path.read_bytes()
                outside = self.root.parent / ("outside-" + name)
                outside.write_bytes(original)
                path.unlink()
                try:
                    path.symlink_to(outside)
                except (OSError, NotImplementedError) as error:
                    path.write_bytes(original)
                    self.skipTest(f"This runner cannot create file symlinks: {type(error).__name__}")
                try:
                    report = memory.inspect_corpus(self.root)
                    self.assertEqual(report["status"], "blocked", report)
                    with self.assertRaises(memory.CaseMemoryError):
                        memory.build_index(self.root)
                    self.assertNotIn(str(outside), json.dumps(report))
                finally:
                    path.unlink()
                    path.write_bytes(original)

    def test_current_bytes_are_rechecked_for_each_corpus_input(self) -> None:
        original = snapshot(self.root)
        inputs = ("schema.yaml", "sources.json", "cases.json")
        for operation, name in ((operation, name) for operation in ("inspect", "build", "check")
                                for name in (inputs + ("index.json",) if operation == "check" else inputs)):
            with self.subTest(operation=operation, name=name):
                for relative, value in original.items():
                    (self.root / relative).write_bytes(value)
                if operation == "check":
                    self.save_index()
                real_read = memory._read_bytes
                changed = False

                def change_after_read(path: Path, limit: int) -> bytes:
                    nonlocal changed
                    value = real_read(path, limit)
                    if Path(path).name == name and not changed:
                        changed = True
                        stat = Path(path).stat()
                        self.assertEqual(value[-1:], b"\n")
                        Path(path).write_bytes(value[:-1] + b" ")
                        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
                    return value

                with patch.object(memory, "_read_bytes", side_effect=change_after_read):
                    if operation == "build":
                        with self.assertRaises(memory.CaseMemoryError) as raised:
                            memory.build_index(self.root)
                        self.assertEqual(raised.exception.code, "source_changed")
                        report = {"status": "blocked", "errors": [raised.exception.diagnostic()]}
                    else:
                        report = (memory.check_index(self.root) if operation == "check"
                                  else memory.inspect_corpus(self.root))
                self.assertTrue(changed)
                self.assertEqual(report["status"], "blocked", report)
                self.assertIn("source_changed", [item["code"] for item in report["errors"]], report)

    def test_d06_forks_in_one_origin_group_form_one_indexed_group(self) -> None:
        second = deepcopy(self.case)
        second["id"] = "synthetic-fork"
        second["decision"]["selection_reason"] = "Another view of the same synthetic origin."
        self.cases["cases"].append(second)
        self.save()
        index = memory.build_index(self.root)
        self.assertEqual(index["counts"]["reviewed_cases"], 2)
        self.assertEqual(index["counts"]["indexed_groups"], 1)
        self.assertEqual(index["groups"][0]["case_ids"], ["synthetic-case", "synthetic-fork"])
        self.assertEqual(index["groups"][0]["representative"]["id"], "synthetic-case")

    def test_d06_same_core_under_different_origins_does_not_create_a_majority(self) -> None:
        second_source = deepcopy(self.source)
        second_source.update(id="synthetic-source-fork", origin_group="synthetic-other-origin")
        second_case = deepcopy(self.case)
        second_case["id"] = "synthetic-fork"
        second_case["source"]["id"] = second_source["id"]
        self.sources["sources"].append(second_source)
        self.cases["cases"].append(second_case)
        self.save()
        index = memory.build_index(self.root)
        self.assertEqual(index["counts"]["sources"], 2)
        self.assertEqual(index["counts"]["indexed_groups"], 1)
        self.assertEqual(index["groups"][0]["case_ids"], ["synthetic-case", "synthetic-fork"])

    def test_d06_text_case_and_whitespace_do_not_create_an_independent_core(self) -> None:
        second_source = deepcopy(self.source)
        second_source.update(id="synthetic-source-fork", origin_group="synthetic-other-origin")
        second_case = deepcopy(self.case)
        second_case["id"] = "synthetic-fork"
        second_case["source"]["id"] = second_source["id"]
        second_case["decision"]["selection_reason"] = self.case["decision"]["selection_reason"].upper().replace(" ", "\n  ")
        self.sources["sources"].append(second_source)
        self.cases["cases"].append(second_case)
        self.save()
        self.assertEqual(memory.build_index(self.root)["counts"]["indexed_groups"], 1)

    def test_distinct_structures_retain_distinct_groups(self) -> None:
        second_source = deepcopy(self.source)
        second_source.update(id="synthetic-network-source", origin_group="synthetic-network-origin")
        second_case = deepcopy(self.case)
        second_case["id"] = "synthetic-network-case"
        second_case["source"]["id"] = second_source["id"]
        second_case["structure"]["objective"] = "optimization"
        second_case["structure"]["structures"] = ["network"]
        second_case["decision"]["adopted_pattern"] = "capacity constrained network allocation"
        self.sources["sources"].append(second_source)
        self.cases["cases"].append(second_case)
        self.save()
        self.assertEqual(memory.build_index(self.root)["counts"]["indexed_groups"], 2)

    def test_valid_nonreviewed_cases_are_not_indexed(self) -> None:
        for status in ("draft", "quarantined", "retired"):
            with self.subTest(status=status):
                self.case["status"] = status
                self.save()
                self.assertEqual(memory.inspect_corpus(self.root)["status"], "corpus_valid")
                index = memory.build_index(self.root)
                self.assertEqual(index["counts"]["cases"], 1)
                self.assertEqual(index["counts"]["reviewed_cases"], 0)
                self.assertEqual(index["groups"], [])

    def test_unresolved_near_duplicates_cannot_enter_reviewed_recommendations(self) -> None:
        self.case["near_duplicates"] = {
            "status": "unresolved", "reason": "A curator must resolve a suspected shared origin.",
        }
        self.save()
        self.assert_blocked("near_duplicate_unresolved")
        for status in ("draft", "quarantined", "retired"):
            with self.subTest(status=status):
                self.case["status"] = status
                self.save()
                self.assertEqual(memory.inspect_corpus(self.root)["status"], "corpus_valid")
                self.assertEqual(memory.build_index(self.root)["groups"], [])
        self.case["status"] = "reviewed"
        self.case["near_duplicates"] = {
            "status": "cleared", "reason": "No unresolved shared-origin concern remains in the fixture.",
        }
        self.save()
        self.assertEqual(memory.build_index(self.root)["counts"]["indexed_groups"], 1)

    def test_rebuilding_the_same_payload_is_deterministic_and_read_only(self) -> None:
        before = snapshot(self.root)
        first = memory.build_index(self.root)
        second = memory.build_index(self.root)
        self.assertEqual(first, second)
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
        self.assertEqual(snapshot(self.root), before)

    def test_file_json_formatting_and_order_do_not_change_derived_identity(self) -> None:
        first = memory.build_index(self.root)
        for name, document in (("sources.json", self.sources), ("cases.json", self.cases)):
            reversed_document = dict(reversed(list(document.items())))
            payload = json.dumps(reversed_document, ensure_ascii=False, indent=4)
            (self.root / name).write_bytes((payload.replace("\n", "\r\n") + "\r\n").encode("utf-8"))
        self.assertEqual(memory.build_index(self.root), first)

    def test_case_and_source_file_order_do_not_select_a_different_representative(self) -> None:
        second_source = deepcopy(self.source)
        second_source.update(id="synthetic-source-fork", origin_group="synthetic-other-origin")
        second_case = deepcopy(self.case)
        second_case["id"] = "synthetic-fork"
        second_case["source"]["id"] = second_source["id"]
        self.sources["sources"].append(second_source)
        self.cases["cases"].append(second_case)
        self.save()
        groups = memory.build_index(self.root)["groups"]
        self.sources["sources"].reverse()
        self.cases["cases"].reverse()
        self.save()
        self.assertEqual(memory.build_index(self.root)["groups"], groups)

    def test_source_hash_normalizes_line_endings_and_mapping_order(self) -> None:
        first = deepcopy(self.source)
        first["sections"]["overview"] = "first line\r\nsecond line\rthird line"
        second = dict(reversed(list(deepcopy(first).items())))
        second["sections"] = dict(reversed(list(second["sections"].items())))
        second["sections"]["overview"] = "first line\nsecond line\nthird line"
        self.assertEqual(memory.source_sha256(first), memory.source_sha256(second))
        canonical = json.dumps(second, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.assertEqual(memory.source_sha256(first), hashlib.sha256(canonical).hexdigest())

    def test_missing_index_never_reports_current(self) -> None:
        before = snapshot(self.root)
        report = memory.check_index(self.root)
        self.assertEqual(report["status"], "blocked", report)
        self.assertIn("index_missing", [item["code"] for item in report["errors"]], report)
        self.assertEqual(snapshot(self.root), before)

    def test_current_index_becomes_stale_when_a_case_changes_or_is_withdrawn(self) -> None:
        original_case = deepcopy(self.case)
        for change in ("decision", "retired"):
            with self.subTest(change=change):
                self.cases["cases"][0] = deepcopy(original_case)
                self.save()
                self.save_index()
                self.assertEqual(memory.check_index(self.root)["status"], "index_current")
                if change == "decision":
                    self.cases["cases"][0]["decision"]["selection_reason"] = "Revised synthetic reasoning."
                else:
                    self.cases["cases"][0]["status"] = "retired"
                    self.cases["cases"][0]["status_reason"] = "Withdrawn synthetic illustration."
                self.save()
                before = snapshot(self.root)
                report = memory.check_index(self.root)
                self.assertEqual(report["status"], "blocked", report)
                self.assertIn("index_stale", [item["code"] for item in report["errors"]], report)
                self.assertEqual(snapshot(self.root), before)

    def test_index_checks_current_source_bytes_even_with_unchanged_stat(self) -> None:
        self.save_index()
        path = self.root / "sources.json"
        stat = path.stat()
        payload = path.read_bytes()
        self.assertIn(b"daily", payload)
        path.write_bytes(payload.replace(b"daily", b"night", 1))
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        self.assertEqual(path.stat().st_size, stat.st_size)
        self.assertEqual(path.stat().st_mtime_ns, stat.st_mtime_ns)
        self.assertEqual(memory.check_index(self.root)["status"], "blocked")

    def test_tampered_index_cannot_self_assert_current(self) -> None:
        index = self.save_index()
        index["groups"][0]["representative"]["decision"]["selection_reason"] = "Tampered advice."
        write_json(self.root / "index.json", index)
        self.assertEqual(memory.check_index(self.root)["status"], "blocked")

    def test_index_paths_outside_the_corpus_are_rejected_without_private_path_echo(self) -> None:
        index = memory.build_index(self.root)
        outside = self.root.parent / "private-index.json"
        write_json(outside, index)
        for path in (outside, self.root / ".." / outside.name):
            with self.subTest(path_kind="direct" if path == outside else "parent_traversal"):
                report = memory.check_index(self.root, path)
                self.assertEqual(report["status"], "blocked", report)
                self.assertIn("path_violation", [item["code"] for item in report["errors"]], report)
                self.assertNotIn(str(outside), json.dumps(report))
        custom = self.root / "custom-index.json"
        write_json(custom, index)
        self.assertEqual(memory.check_index(self.root, custom)["status"], "index_current")

    def test_reports_and_payloads_do_not_share_mutable_returned_state(self) -> None:
        first = memory.build_index(self.root)
        original = deepcopy(first)
        first["groups"][0]["representative"]["decision"]["selection_reason"] = "caller mutation"
        first["groups"][0]["case_ids"].append("caller-added")
        self.assertEqual(memory.build_index(self.root), original)
        report = memory.inspect_corpus(self.root)
        report["eligible_cases"][0]["status"] = "retired"
        self.assertEqual(memory.inspect_corpus(self.root)["eligible_cases"][0]["status"], "reviewed")

    def test_cli_validate_build_and_check_are_read_only(self) -> None:
        for command, expected_status in (("validate", "corpus_valid"), ("build-index", None)):
            with self.subTest(command=command):
                before = snapshot(self.root)
                result = self.cli(command)
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                report = json.loads(result.stdout)
                if expected_status is None:
                    self.assertEqual(report, memory.build_index(self.root))
                else:
                    self.assertEqual(report["status"], expected_status)
                self.assertEqual(snapshot(self.root), before)
        self.save_index()
        before = snapshot(self.root)
        result = self.cli("check-index")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout)["status"], "index_current")
        self.assertEqual(snapshot(self.root), before)

    def test_cli_failures_are_nonzero_and_do_not_echo_sensitive_content(self) -> None:
        secret = "private-account@example.invalid"
        self.source["sections"]["overview"] = secret
        self.save()
        for command in ("validate", "build-index", "check-index"):
            with self.subTest(command=command):
                before = snapshot(self.root)
                result = self.cli(command)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn(secret, result.stdout + result.stderr)
                self.assertEqual(snapshot(self.root), before)

    def test_cli_missing_index_is_nonzero_and_does_not_build_it_implicitly(self) -> None:
        before = snapshot(self.root)
        result = self.cli("check-index")
        self.assertNotEqual(result.returncode, 0)
        report = json.loads(result.stdout)
        self.assertIn("index_missing", [item["code"] for item in report["errors"]], report)
        self.assertEqual(snapshot(self.root), before)


if __name__ == "__main__":
    unittest.main()
