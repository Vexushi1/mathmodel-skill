#!/usr/bin/env python3
"""Read-only shape, provenance, and current-input inspection for C1 review receipts.

This inspector does not create a review, authenticate a reviewer, or grant an
existing model, numerical, writing, or delivery gate. In particular, a caller
supplied host observation is useful for finding contradictions, not a trust root.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml
from jsonschema import Draft202012Validator

import claim_figure
import claim_tex
import latex_delivery
import project_transaction as PROJECT_TX
import runtime_assurance as RUNTIME

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "core/project_state.schema.yaml"
CONTRACT = "core/review_receipt_contract.yaml"
PROTOCOL_VERSION = "1.0.0"
STATE_FIELD_DOMAIN = "hsk.review_receipt.state_field.v1"
INPUT_SNAPSHOT_DOMAIN = "hsk.review_receipt.input_snapshot.v1"
MAX_STATE_BYTES = 2 * 1024 * 1024
MAX_SOURCE_BYTES = 64 * 1024 * 1024
MAX_TOTAL_SOURCE_BYTES = 256 * 1024 * 1024
MAX_OBSERVED_FILES = 256


class ReceiptInspectionError(ValueError):
    """A malformed record or unsafe read cannot be treated as review evidence."""


class _ReadBudget:
    def __init__(self) -> None:
        self.bytes = 0

    def add(self, size: int) -> None:
        if self.bytes + size > MAX_TOTAL_SOURCE_BYTES:
            raise ReceiptInspectionError("total review source byte budget exceeded")
        self.bytes += size


class _ObservedFiles(dict[str, str | None]):
    def __init__(self, budget: _ReadBudget) -> None:
        super().__init__()
        self.budget = budget


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def _digest(domain: str, value: Any) -> str:
    return hashlib.sha256(domain.encode("ascii") + b"\0" + _canonical(value)).hexdigest()


def state_field_sha256(value: Any) -> str:
    """Hash a selected state value, excluding receipt-bearing state file bytes."""
    return _digest(STATE_FIELD_DOMAIN, value)


def _sorted_rows(rows: Sequence[Mapping[str, str]], key: str) -> list[dict[str, str]]:
    return [dict(row) for row in sorted(rows, key=lambda row: row[key])]


def snapshot_fingerprint(
    state_fields: Sequence[Mapping[str, str]],
    project_files: Sequence[Mapping[str, str]],
    authorities: Sequence[Mapping[str, str]],
    *, gate: str, role: str, scope: Mapping[str, Sequence[str]], criteria_version: str,
) -> str:
    """Bind review meaning and its selected inputs in one stable snapshot."""
    return _digest(INPUT_SNAPSHOT_DOMAIN, {
        "gate": gate,
        "role": role,
        "criteria_version": criteria_version,
        "scope": {
            "questions": sorted(scope["questions"]),
            "object_ids": sorted(scope["object_ids"]),
        },
        "state_fields": _sorted_rows(state_fields, "pointer"),
        "project_files": _sorted_rows(project_files, "path"),
        "authorities": _sorted_rows(authorities, "path"),
    })


def _recorded_rows(rows: Any, key: str, location: str) -> list[dict[str, str]]:
    if not isinstance(rows, list):
        raise ReceiptInspectionError(f"{location} must be a list")
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping) or set(row) != {key, "sha256"}:
            raise ReceiptInspectionError(f"{location}[{index}] must contain exactly {key} and sha256")
        name, digest = row[key], row["sha256"]
        if not isinstance(name, str) or not name or name != name.strip():
            raise ReceiptInspectionError(f"{location}[{index}].{key} is invalid")
        if name in seen:
            raise ReceiptInspectionError(f"{location} has a duplicate {key}: {name}")
        seen.add(name)
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ReceiptInspectionError(f"{location}[{index}].sha256 must be lowercase SHA-256")
        result.append({key: name, "sha256": digest})
    return result


def _state_value(state: Mapping[str, Any], pointer: str) -> Any:
    if not pointer.startswith("/") or pointer == "/":
        raise ReceiptInspectionError(f"invalid state pointer: {pointer}")
    if pointer == "/review_receipts" or pointer.startswith("/review_receipts/"):
        raise ReceiptInspectionError("review receipts cannot depend on their own state subtree")
    if pointer in {"/project", "/project/state_generation"}:
        raise ReceiptInspectionError("state generation is context, not a reviewed input")
    value: Any = state
    for token in pointer[1:].split("/"):
        if "~" in token:
            index = 0
            while index < len(token):
                if token[index] == "~" and (index + 1 >= len(token) or token[index + 1] not in "01"):
                    raise ReceiptInspectionError(f"invalid JSON Pointer escape: {pointer}")
                index += 2 if token[index] == "~" else 1
        key = token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, Mapping):
            if key not in value:
                raise KeyError(pointer)
            value = value[key]
        elif isinstance(value, list):
            if re.fullmatch(r"(?:0|[1-9][0-9]*)", key) is None:
                raise ReceiptInspectionError(f"invalid JSON Pointer array index: {pointer}")
            index = int(key)
            if index >= len(value):
                raise KeyError(pointer)
            value = value[index]
        else:
            raise KeyError(pointer)
    return value


def _observe_file(root: Path, relative: str, read_set: dict[str, str | None]) -> str | None:
    if relative in read_set:
        return read_set[relative]
    if len(read_set) >= MAX_OBSERVED_FILES and relative not in read_set:
        raise ReceiptInspectionError("review source count exceeds budget")
    try:
        path = PROJECT_TX._guarded_path(root, relative)
    except PROJECT_TX.ProjectTransactionError as exc:
        raise ReceiptInspectionError(f"unsafe review source path: {relative}") from exc
    if not path.is_file():
        digest = None
    else:
        size = path.stat().st_size
        if size > MAX_SOURCE_BYTES:
            raise ReceiptInspectionError(f"review source byte budget exceeded: {relative}")
        hash_state = hashlib.sha256()
        actual_size = 0
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                actual_size += len(chunk)
                if actual_size > MAX_SOURCE_BYTES:
                    raise ReceiptInspectionError(f"review source byte budget exceeded: {relative}")
                hash_state.update(chunk)
        if isinstance(read_set, _ObservedFiles):
            read_set.budget.add(actual_size)
        digest = hash_state.hexdigest()
    if relative in read_set and read_set[relative] != digest:
        raise ReceiptInspectionError(f"review source changed during inspection: {relative}")
    read_set[relative] = digest
    return digest


def _observe_bytes(root: Path, relative: str, read_set: dict[str, str | None]) -> bytes:
    """Parse and fingerprint policy from the same exact byte observation."""
    if len(read_set) >= MAX_OBSERVED_FILES and relative not in read_set:
        raise ReceiptInspectionError("review source count exceeds budget")
    try:
        path = PROJECT_TX._guarded_path(root, relative)
    except PROJECT_TX.ProjectTransactionError as exc:
        raise ReceiptInspectionError(f"unsafe review source path: {relative}") from exc
    if not path.is_file() or path.stat().st_size > MAX_STATE_BYTES:
        raise ReceiptInspectionError(f"missing policy file or byte budget exceeded: {relative}")
    if relative not in read_set and isinstance(read_set, _ObservedFiles):
        read_set.budget.add(path.stat().st_size)
    with path.open("rb") as source:
        raw = source.read(MAX_STATE_BYTES + 1)
    if len(raw) > MAX_STATE_BYTES:
        raise ReceiptInspectionError(f"policy byte budget exceeded: {relative}")
    digest = hashlib.sha256(raw).hexdigest()
    if relative in read_set and read_set[relative] != digest:
        raise ReceiptInspectionError(f"review policy changed during inspection: {relative}")
    read_set[relative] = digest
    return raw


def _shape_issues(block: Any, schema: Mapping[str, Any]) -> list[str]:
    properties = schema.get("properties") or {}
    receipt_schema = properties.get("review_receipts")
    if not isinstance(receipt_schema, Mapping):
        return ["current Project State Schema has no review_receipts definition"]
    local_schema = {"$schema": schema.get("$schema"), "$defs": schema.get("$defs", {}), **receipt_schema}
    validator = Draft202012Validator(local_schema)
    return [
        "schema review_receipts/" + "/".join(map(str, error.path)) + ": " + error.message
        for error in sorted(validator.iter_errors(block), key=lambda item: list(map(str, item.path)))[:32]
    ]


def _gate_authority_issues(
    record: Mapping[str, Any], state: Mapping[str, Any], contract: Mapping[str, Any],
    skill_read_set: dict[str, str | None],
) -> list[str]:
    issues: list[str] = []
    gate = record["gate"]
    authority_paths = {row["path"] for row in record["snapshot"]["authorities"]}
    spec = (contract.get("gate_authorities") or {}).get(gate, {})
    if not isinstance(spec, Mapping):
        raise ReceiptInspectionError(f"invalid gate authority contract for {gate}")
    required = list(spec.get("required_paths") or [])
    source = _selected_paper_source(state)
    if source is not None and source[0] == "latex":
        required.extend(spec.get("latex_required_paths") or [])
    for path in required:
        if path not in authority_paths:
            issues.append(f"required review Authority omitted: {path}")
    version_path = spec.get("version_source")
    if version_path and version_path in authority_paths:
        try:
            raw = _observe_bytes(ROOT, version_path, skill_read_set)
            current = yaml.safe_load(raw.decode("utf-8")) or {}
            if str(current.get("version", "")) != record["criteria_version"]:
                issues.append("review criteria version differs from current Authority")
            if gate == "model_challenge":
                challenge = current.get("model_challenge") or {}
                role_to_pass = {
                    "positive_fitness_review": "reviewer_pass",
                    "adversarial_model_challenge": "devils_advocate_pass",
                }
                pass_name = role_to_pass.get(record["role"])
                if pass_name is None:
                    issues.append("model challenge has an unknown review role")
                elif record["verdict"] == "pass":
                    required_checks = set((challenge.get(pass_name) or {}).get("must_check") or [])
                    observed_checks = {item["id"] for item in record["checks"]}
                    if not required_checks or not required_checks.issubset(observed_checks):
                        issues.append("model challenge PASS omits required role-specific checks")
        except (OSError, yaml.YAMLError, AttributeError, PROJECT_TX.ProjectTransactionError) as exc:
            issues.append(f"review criteria version could not be checked: {exc}")
    return issues


def _review_payload(record: Mapping[str, Any]) -> str:
    """Compare substantive passes without counting their role labels as evidence."""
    return _digest("hsk.review_receipt.substantive_pass.v1", {
        "checks": record["checks"], "findings": record["findings"],
        "uncovered": record["uncovered"], "verdict": record["verdict"],
    })


def _selected_paper_source(state: Mapping[str, Any]) -> tuple[str, str] | None:
    framework = state.get("paper_framework") or {}
    policy = framework.get("claim_consumption_policy") or {} if isinstance(framework, Mapping) else {}
    if not isinstance(policy, Mapping) or (policy.get("protocol_version"), policy.get("mode")) != (
        "1.5.0", "enforce_selected_paper_claim_chain",
    ):
        return None
    source = policy.get("paper_source")
    if not isinstance(source, Mapping):
        return None
    paper_format, entrypoint = source.get("format"), source.get("entrypoint")
    if paper_format == "latex" and isinstance(entrypoint, str) and re.fullmatch(r"final_latex/[^/]+\.tex", entrypoint):
        return paper_format, entrypoint
    if paper_format == "docx" and isinstance(entrypoint, str) and re.fullmatch(r"draft_docx/[^/]+\.docx", entrypoint):
        return paper_format, entrypoint
    return None


def _latex_closure_issues(
    root: Path, state: Mapping[str, Any], entrypoint: str, pointers: set[str], paths: set[str],
    project_read_set: dict[str, str | None],
) -> list[str]:
    issues: list[str] = []
    try:
        main = PROJECT_TX._guarded_path(root, entrypoint)
    except PROJECT_TX.ProjectTransactionError as exc:
        raise ReceiptInspectionError(f"unsafe selected paper entrypoint: {entrypoint}") from exc
    scan = claim_tex.scan_static_latex(root, main, selected_carrier=True)
    if scan.get("status") != "scanned":
        return ["selected LaTeX source graph is not statically closed"]
    for relative, item in (scan.get("files") or {}).items():
        if relative not in paths:
            issues.append(f"active LaTeX source omitted from review snapshot: {relative}")
        if _observe_file(root, relative, project_read_set) != item.get("sha256"):
            issues.append(f"active LaTeX source changed during closure scan: {relative}")
    figures = claim_figure.inspect_static_figures(scan)
    if figures.get("status") != "scanned":
        return issues + ["selected LaTeX Figure source is not statically closed"]
    approved = (state.get("artifacts") or {}).get("approved_figures") or []
    if not isinstance(approved, list):
        return issues + ["approved Figure list is malformed"]
    approved_paths = set(approved)
    allowed_external: dict[str, Path] = {}
    for figure in figures.get("figures", []):
        token = figure.get("image")
        if not isinstance(token, str) or not token:
            issues.append("active Figure has no literal image path")
            continue
        if token.startswith("../figures/"):
            resolved = (main.parent / token).resolve()
            if not resolved.is_relative_to(root):
                issues.append("active Figure image escapes the project")
                continue
            relative = resolved.relative_to(root).as_posix()
            if relative not in approved_paths:
                issues.append(f"active Figure image lacks current project approval: {relative}")
                continue
            if "/artifacts/approved_figures" not in pointers:
                issues.append("approved Figure identities are absent from the review state snapshot")
            allowed_external[token] = resolved
    try:
        bundle = latex_delivery.source_bundle_files(
            main, project_root=root, allowed_external_graphics=allowed_external,
        )
    except (OSError, ValueError, UnicodeError) as exc:
        return issues + ["selected LaTeX source/image closure is unresolved: " + str(exc)[:256]]
    for path in bundle:
        relative = path.relative_to(root).as_posix()
        if relative not in paths:
            issues.append(f"LaTeX source or image omitted from review snapshot: {relative}")
        _observe_file(root, relative, project_read_set)
    return issues


def _gate_input_issues(
    root: Path, record: Mapping[str, Any], state: Mapping[str, Any], contract: Mapping[str, Any],
    state_fields: Sequence[Mapping[str, str]], project_files: Sequence[Mapping[str, str]],
    project_read_set: dict[str, str | None],
) -> list[str]:
    profiles = contract.get("gate_inputs") or {}
    profile = profiles.get(record["gate"])
    if not isinstance(profile, Mapping):
        return ["unknown review gate has no C1 input profile"]
    issues: list[str] = []
    pointers = {row["pointer"] for row in state_fields}
    paths = {row["path"] for row in project_files}
    for template in profile.get("required_state_pointers_per_question", []):
        for question in record["scope"]["questions"]:
            pointer = template.replace("{question}", question)
            if pointer not in pointers:
                issues.append(f"required review state input omitted: {pointer}")
    if profile.get("required_state_pointers_per_question") and not record["scope"]["questions"]:
        issues.append("question-scoped review has no question")
    for pointer in profile.get("required_state_pointers", []):
        if pointer not in pointers:
            issues.append(f"required review state input omitted: {pointer}")
    for path in profile.get("required_project_files", []):
        if path not in paths:
            issues.append(f"required review project input omitted: {path}")
    selected_pointer = profile.get("selected_paper_source_pointer")
    if selected_pointer:
        if selected_pointer not in pointers:
            issues.append("selected paper source is absent from the review state snapshot")
        selected = _selected_paper_source(state)
        if selected is None:
            issues.append("no current selected paper source is declared in project state")
        else:
            paper_format, entrypoint = selected
            if entrypoint not in paths:
                issues.append(f"selected paper entrypoint is absent from the review snapshot: {entrypoint}")
            if paper_format == "latex" and profile.get("requires_static_latex_closure"):
                issues.extend(_latex_closure_issues(
                    root, state, entrypoint, pointers, paths, project_read_set,
                ))
    patterns = profile.get("paper_carrier_patterns") or []
    if patterns and not any(re.fullmatch(pattern, path) for pattern in patterns for path in paths):
        issues.append("review snapshot omits an actual paper source carrier")
    registered_pointer = profile.get("required_project_file_from_state_pointer")
    if registered_pointer:
        try:
            registered = _state_value(state, registered_pointer)
        except KeyError:
            registered = None
        if not isinstance(registered, str) or not registered.endswith(".pdf") or registered not in paths:
            issues.append("review snapshot omits the registered compiled PDF")
    return issues


def _independence(record: Mapping[str, Any], host_evidence: Mapping[str, Any] | None) -> tuple[str, list[str]]:
    method = record["execution"]["method"]
    source_kind = record["execution"]["source_kind"]
    issues: list[str] = []
    if method != "unverified" and not record["execution"].get("source_locator"):
        issues.append("review execution source has no locator")
    if method == "separated_passes" and not record["execution"].get("pass_id"):
        issues.append("separated review pass has no pass ID")
    if method == "author_self_check":
        if source_kind not in {"author_self_report", "self_report"}:
            issues.append("author self-check has contradictory execution source")
        return "not_independent", issues
    if method == "separated_passes":
        if source_kind not in {"assistant_record", "self_report"}:
            issues.append("separated passes have contradictory execution source")
        return "separated_passes", issues
    if method == "native_isolated":
        if source_kind != "host_record":
            issues.append("native isolated method lacks a host-record source")
    elif method == "human_review":
        if source_kind != "human_record":
            issues.append("human review method lacks a human-record source")
    else:
        return "unverified", issues
    # C1 has no trusted host attestation adapter. A caller's dict can expose a
    # contradiction, but it must never turn a self-declaration into verification.
    if host_evidence is not None and record["review_id"] in host_evidence:
        observed = host_evidence[record["review_id"]]
        if not isinstance(observed, Mapping) or any(
            observed.get(key) != record["execution"].get(key)
            for key in ("method", "source_kind", "source_locator", "pass_id")
            if key in observed
        ):
            issues.append("host observation contradicts declared execution")
    return "unverified", issues


def _inspect_record(
    root: Path, state: Mapping[str, Any], record: Mapping[str, Any], contract: Mapping[str, Any],
    project_read_set: dict[str, str | None], skill_read_set: dict[str, str | None],
    host_evidence: Mapping[str, Any] | None,
) -> dict[str, Any]:
    receipt_id = record["review_id"]
    result: dict[str, Any] = {"review_id": receipt_id, "verdict": record["verdict"],
                              "applicability": "current", "independence": "unverified",
                              "qualification": "not_granted", "coverage_boundary": "declared_scope_only", "issues": []}
    snapshot = record["snapshot"]
    state_fields = _recorded_rows(snapshot["state_fields"], "pointer", f"{receipt_id}.state_fields")
    project_files = _recorded_rows(snapshot["project_files"], "path", f"{receipt_id}.project_files")
    authorities = _recorded_rows(snapshot["authorities"], "path", f"{receipt_id}.authorities")
    if any(row["path"] == PROJECT_TX.STATE_RELATIVE_PATH for row in project_files):
        raise ReceiptInspectionError("review snapshot cannot bind its containing state file")
    if not (state_fields or project_files) or not authorities:
        raise ReceiptInspectionError(f"{receipt_id} has no reviewed input or Authority")
    result["issues"].extend(_gate_input_issues(
        root, record, state, contract, state_fields, project_files, project_read_set,
    ))
    expected = snapshot_fingerprint(
        state_fields, project_files, authorities,
        gate=record["gate"], role=record["role"], scope=record["scope"],
        criteria_version=record["criteria_version"],
    )
    if expected != snapshot["fingerprint_sha256"]:
        raise ReceiptInspectionError(f"{receipt_id} input snapshot fingerprint is invalid")
    if snapshot["state_generation"] > RUNTIME.state_generation(state):
        raise ReceiptInspectionError(f"{receipt_id} claims a future state generation")

    stale = False
    for row in state_fields:
        try:
            actual = state_field_sha256(_state_value(state, row["pointer"]))
        except KeyError:
            actual = None
        if actual != row["sha256"]:
            stale = True
            result["issues"].append(f"reviewed state field changed: {row['pointer']}")
    for rows, source_root, read_set, label in (
        (project_files, root, project_read_set, "project input"),
        (authorities, ROOT, skill_read_set, "review Authority"),
    ):
        for row in rows:
            actual = _observe_file(source_root, row["path"], read_set)
            if actual != row["sha256"]:
                stale = True
                result["issues"].append(f"{label} changed: {row['path']}")
    result["issues"].extend(_gate_authority_issues(record, state, contract, skill_read_set))
    independence, provenance_issues = _independence(record, host_evidence)
    result["independence"] = independence
    result["issues"].extend(provenance_issues)
    if stale:
        result["applicability"] = "stale"
    elif provenance_issues or result["issues"] or independence in {"unverified", "not_independent"}:
        result["applicability"] = "unverified"

    check_ids = [item["id"] for item in record["checks"]]
    finding_ids = [item["id"] for item in record["findings"]]
    if not check_ids:
        result["issues"].append("review has no declared checks")
    if len(check_ids) != len(set(check_ids)) or len(finding_ids) != len(set(finding_ids)):
        raise ReceiptInspectionError(f"{receipt_id} has duplicate check or finding IDs")
    objects = set(record["scope"]["object_ids"])
    if len(objects) != len(record["scope"]["object_ids"]):
        raise ReceiptInspectionError(f"{receipt_id} has duplicate scope objects")
    if any(not set(check["object_ids"]).issubset(objects) for check in record["checks"]):
        raise ReceiptInspectionError(f"{receipt_id} check exceeds declared object scope")
    if not set(record["uncovered"]).issubset(objects):
        raise ReceiptInspectionError(f"{receipt_id} uncovered objects exceed declared scope")
    if record["verdict"] == "pass":
        if record["uncovered"] or any(check["result"] != "pass" for check in record["checks"]):
            result["issues"].append("PASS does not cover every declared check and object")
        checked_objects = {object_id for check in record["checks"] for object_id in check["object_ids"]}
        if objects - checked_objects:
            result["issues"].append("PASS omits declared review objects")
        if any(item["closure"] in {"open", "corrected"} and item["severity"] in {"blocking", "review_required"}
               for item in record["findings"]):
            result["issues"].append("PASS cannot close a material finding by correction alone")
    if result["issues"] and result["applicability"] == "current":
        result["applicability"] = "unverified"
    return result


def _cross_record_issues(records: list[Mapping[str, Any]], reports: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    by_id = {record["review_id"]: record for record in records}
    if len(by_id) != len(records):
        issues.append("duplicate review_id")
        return issues
    by_report = {item["review_id"]: item for item in reports}
    for record in records:
        review_id = record["review_id"]
        for predecessor in record.get("supersedes", []):
            if predecessor not in by_id or predecessor == review_id:
                issues.append(f"{review_id} supersedes unknown or self receipt: {predecessor}")
            else:
                old = by_id[predecessor]
                same_review = record["gate"] == old["gate"] and record["role"] == old["role"]
                old_objects = set(old["scope"]["object_ids"])
                old_checks = {item["id"] for item in old["checks"]}
                old_findings = {item["id"] for item in old["findings"]}
                covers_old = (set(old["scope"]["questions"]).issubset(record["scope"]["questions"])
                              and old_objects.issubset(record["scope"]["object_ids"])
                              and old_checks.issubset({item["id"] for item in record["checks"]}))
                linked = any(
                    item["review_id"] == predecessor
                    and old_objects.issubset(item["object_ids"])
                    and old_checks.issubset(item["check_ids"])
                    and old_findings.issubset(item["finding_ids"])
                    for item in record.get("rechecks", [])
                )
                if (not same_review or not covers_old or not linked or record["verdict"] != "pass"
                        or by_report[review_id]["applicability"] != "current"):
                    by_report[review_id]["issues"].append("partial or inapplicable receipt cannot supersede full review")
                    by_report[review_id]["applicability"] = "unverified"
                else:
                    by_report[predecessor]["applicability"] = "superseded"
        for recheck in record.get("rechecks", []):
            old_id = recheck["review_id"]
            if old_id not in by_id or old_id == review_id:
                issues.append(f"{review_id} rechecks unknown or self receipt: {old_id}")
                continue
            old = by_id[old_id]
            if (record["gate"], record["role"], record["criteria_version"]) != (
                old["gate"], old["role"], old["criteria_version"],
            ):
                issues.append(f"{review_id} recheck uses a different gate, role, or criteria version")
            if not set(recheck["finding_ids"]).issubset({f["id"] for f in old["findings"]}):
                issues.append(f"{review_id} rechecks unknown finding IDs")
            if not set(recheck["object_ids"]).issubset(set(old["scope"]["object_ids"])):
                issues.append(f"{review_id} rechecks objects outside predecessor scope")
            if not set(recheck["check_ids"]).issubset({c["id"] for c in old["checks"]}):
                issues.append(f"{review_id} rechecks checks outside predecessor scope")
    pairs: dict[str, list[Mapping[str, Any]]] = {}
    for record in records:
        if record["execution"]["method"] != "separated_passes":
            continue
        snapshot = record["snapshot"]
        key = _digest("hsk.review_receipt.shared_input.v1", {
            "gate": record["gate"], "criteria_version": record["criteria_version"],
            "scope": {"questions": sorted(record["scope"]["questions"]),
                      "object_ids": sorted(record["scope"]["object_ids"])},
            "state_fields": _sorted_rows(snapshot["state_fields"], "pointer"),
            "project_files": _sorted_rows(snapshot["project_files"], "path"),
            "authorities": _sorted_rows(snapshot["authorities"], "path"),
        })
        pairs.setdefault(key, []).append(record)
    for grouped in pairs.values():
        for index, first in enumerate(grouped):
            for second in grouped[index + 1:]:
                same_pass = first["execution"].get("pass_id") and first["execution"].get("pass_id") == second["execution"].get("pass_id")
                copied = _review_payload(first) == _review_payload(second)
                if first["role"] != second["role"] and (same_pass or copied):
                    for record in (first, second):
                        report = by_report[record["review_id"]]
                        report["independence"] = "unverified"
                        report["applicability"] = "unverified"
                        report["issues"].append("two roles share a pass ID or copied substantive verdict")
    for old in records:
        old_id = old["review_id"]
        old_report = by_report[old_id]
        old_objects = set(old["scope"]["object_ids"])
        old_checks = {check["id"] for check in old["checks"]}
        for finding in old["findings"]:
            if finding["closure"] != "reverified":
                continue
            scoped_objects = finding.get("object_ids")
            scoped_checks = finding.get("check_ids")
            if scoped_objects is None or scoped_checks is None:
                old_report["issues"].append("reverified finding lacks its affected object/check scope")
                old_report["applicability"] = "unverified"
                continue
            affected_objects = set(scoped_objects)
            affected_checks = set(scoped_checks)
            if not affected_objects.issubset(old_objects) or not affected_checks.issubset(old_checks):
                old_report["issues"].append("reverified finding exceeds its original review scope")
                old_report["applicability"] = "unverified"
                continue
            valid_recheck = False
            for successor in records:
                if successor["review_id"] == old_id:
                    continue
                if (successor["gate"], successor["role"], successor["criteria_version"]) != (
                    old["gate"], old["role"], old["criteria_version"],
                ):
                    continue
                successor_report = by_report[successor["review_id"]]
                if successor_report["applicability"] != "current" or successor["verdict"] != "pass":
                    continue
                old_pass = old["execution"].get("pass_id")
                new_pass = successor["execution"].get("pass_id")
                if not old_pass or not new_pass or old_pass == new_pass:
                    continue
                if successor["execution"]["method"] in {"author_self_check", "unverified"}:
                    continue
                if not any(
                    item["review_id"] == old_id and finding["id"] in item["finding_ids"]
                    and affected_objects.issubset(item["object_ids"])
                    and affected_checks.issubset(item["check_ids"])
                    and set(item["object_ids"]).issubset(successor["scope"]["object_ids"])
                    and set(item["check_ids"]).issubset({check["id"] for check in successor["checks"]})
                    and affected_objects.issubset({
                        object_id for check in successor["checks"] if check["id"] in affected_checks
                        for object_id in check["object_ids"]
                    })
                    for item in successor.get("rechecks", [])
                ):
                    continue
                valid_recheck = True
                break
            if not valid_recheck:
                old_report["issues"].append("reverified finding lacks a current separate affected-scope recheck")
                old_report["applicability"] = "unverified"
    return issues


def inspect_project(
    project_root: str | Path, review_id: str | None = None,
    host_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Inspect declared receipts without writing, accepting, or retroactively filling them."""
    root = Path(project_root).expanduser().resolve()
    report: dict[str, Any] = {"protocol_version": PROTOCOL_VERSION, "status": "blocked",
                              "qualification": "not_granted", "coverage_boundary": "declared_scope_only",
                              "receipts": [], "issues": [],
                              "observed_sources": {"project": {}, "skill": {}}}
    budget = _ReadBudget()
    report["observed_sources"]["project"] = _ObservedFiles(budget)
    report["observed_sources"]["skill"] = _ObservedFiles(budget)
    project_read_set: dict[str, str | None] = report["observed_sources"]["project"]
    skill_read_set: dict[str, str | None] = report["observed_sources"]["skill"]
    state_snapshot = None
    try:
        state_snapshot = RUNTIME.ProjectStateSnapshot.capture(root)
        if state_snapshot.raw is not None and len(state_snapshot.raw) > MAX_STATE_BYTES:
            raise ReceiptInspectionError("project state byte budget exceeded")
        budget.add(len(state_snapshot.raw or b""))
        project_read_set[PROJECT_TX.STATE_RELATIVE_PATH] = state_snapshot.describe()["sha256"]
        state = state_snapshot.payload()
        if "review_receipts" not in state:
            report["status"] = "not_assessed"
        else:
            schema = yaml.safe_load(_observe_bytes(ROOT, SCHEMA, skill_read_set).decode("utf-8")) or {}
            contract = yaml.safe_load(_observe_bytes(ROOT, CONTRACT, skill_read_set).decode("utf-8")) or {}
            if not isinstance(schema, Mapping) or not isinstance(contract, Mapping):
                raise ReceiptInspectionError("review Schema or Authority is not a mapping")
            if contract.get("version") != PROTOCOL_VERSION:
                raise ReceiptInspectionError("unsupported review receipt Authority version")
            block = state["review_receipts"]
            shape_issues = _shape_issues(block, schema)
            if shape_issues:
                raise ReceiptInspectionError("; ".join(shape_issues))
            if block["protocol_version"] != PROTOCOL_VERSION:
                raise ReceiptInspectionError("unsupported review receipt protocol version")
            records = block["records"]
            if review_id is not None and review_id not in {item["review_id"] for item in records}:
                raise ReceiptInspectionError(f"unknown review_id: {review_id}")
            all_reports = [
                _inspect_record(root, state, record, contract, project_read_set, skill_read_set, host_evidence)
                for record in records
            ]
            report["issues"].extend(_cross_record_issues(records, all_reports))
            report["receipts"] = ([row for row in all_reports if row["review_id"] == review_id]
                                  if review_id is not None else all_reports)
            if not records:
                report["status"] = "not_assessed"
            elif report["issues"] or any(row["issues"] or row["applicability"] != "current" or row["verdict"] != "pass"
                                         for row in all_reports):
                report["status"] = "needs_review"
            else:
                report["status"] = "current"
    except (OSError, ValueError, TypeError, KeyError, AttributeError, yaml.YAMLError) as exc:
        report["issues"].append(str(exc).replace(str(root), "<project>"))
        report["status"] = "blocked"
    finally:
        try:
            if state_snapshot is not None:
                state_snapshot.assert_current()
            PROJECT_TX._check_read_set(root, project_read_set)
            PROJECT_TX._check_read_set(ROOT, skill_read_set)
        except (OSError, ValueError, RuntimeError) as exc:
            report["issues"].append("read snapshot changed or became unavailable: " + str(exc).replace(str(root), "<project>"))
            report["status"] = "blocked"
    if report["status"] == "blocked":
        for receipt in report["receipts"]:
            receipt["applicability"] = "unverified"
            receipt["issues"].append("inspection did not complete on a stable read snapshot")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect optional C1 review receipts without writing project state")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--review-id")
    args = parser.parse_args()
    report = inspect_project(args.project_root, review_id=args.review_id)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return {"current": 0, "blocked": 1, "needs_review": 2, "not_assessed": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
