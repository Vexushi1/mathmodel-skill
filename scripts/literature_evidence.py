#!/usr/bin/env python3
"""Read-only structural validator for externally gathered literature evidence.

No web access, project write, user approval, source-truth attestation or
mathematical-semantic verification is performed by this module.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "core/literature_research_contract.yaml"
MAX_BYTES = 262144


class EvidenceError(ValueError):
    """A bounded diagnostic code that never repeats user-supplied source text."""


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError("duplicate_json_key")
        result[key] = value
    return result


def _no_nonfinite(_: str) -> None:
    raise EvidenceError("nonfinite_json_number")


def read_report(path: Path) -> dict[str, Any]:
    try:
        if path.stat().st_size > MAX_BYTES:
            raise EvidenceError("report_size_limit")
        raw = path.read_bytes()
        if len(raw) > MAX_BYTES:
            raise EvidenceError("report_size_limit")
        report = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_no_duplicate_keys,
            parse_constant=_no_nonfinite,
        )
    except EvidenceError:
        raise
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        raise EvidenceError("unreadable_or_invalid_json") from exc
    if not isinstance(report, dict):
        raise EvidenceError("report_root_must_be_object")
    return report


def _contract() -> dict[str, Any]:
    document = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise EvidenceError("invalid_contract")
    Draft202012Validator.check_schema(document)
    return document


def validate_report(report: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    if not isinstance(report, dict):
        issues.append("report_root_must_be_object")
    else:
        schema = _contract()
        validator = Draft202012Validator(schema)
        errors = sorted(
            validator.iter_errors(report),
            key=lambda err: (tuple(map(str, err.absolute_path)), str(err.validator)),
        )
        for err in errors:
            path = ".".join(map(str, err.absolute_path)) or "root"
            issues.append(f"schema:{path}:{err.validator}")
    if not issues:
        scope, search = report["scope"], report["search"]
        sources, methods, decision = report["sources"], report["methods"], report["decision"]

        if scope["mode"] == "model_design":
            if scope["problem_contract_status"] != "frozen" or scope["question"] == "general":
                issues.append("model_design_requires_frozen_scoped_problem_contract")
        elif scope["problem_contract_status"] != "not_applicable":
            issues.append("standalone_cannot_claim_problem_contract_freeze")

        if search["status"] in {"completed", "no_suitable_source"}:
            has_real_attempt = any(
                attempt["status"] == "success"
                and attempt["channel"] in {"web", "academic_connector"}
                for attempt in search["attempts"]
            )
            if not has_real_attempt or not search.get("searched_at"):
                issues.append("declared_search_success_requires_real_channel_and_date")
        if search["status"] == "completed" and not sources:
            issues.append("completed_search_requires_source")

        source_ids = [source["id"] for source in sources]
        if len(set(source_ids)) != len(source_ids):
            issues.append("duplicate_source_id")
        method_ids = [method["id"] for method in methods]
        if len(set(method_ids)) != len(method_ids):
            issues.append("duplicate_method_id")
        source_by_id = {source["id"]: source for source in sources}

        for source in sources:
            level, access = source["evidence_level"], source["access_level"]
            if level in {"E2", "E3"} and (
                access not in {"method", "full"} or not source.get("method_anchor")
            ):
                issues.append(f"source:{source['id']}:original_method_not_located")
            if level == "E3" and not source.get("replication_anchor"):
                issues.append(f"source:{source['id']}:independent_replication_not_located")
            if level == "E1" and access == "metadata":
                issues.append(f"source:{source['id']}:abstract_not_accessed")
            if level == "E0" and access != "metadata":
                issues.append(f"source:{source['id']}:metadata_only_level_mismatch")

        substantive = {
            "adopt_as_basis", "adapt_to_problem", "use_as_comparator", "use_for_validation",
        }
        for method in methods:
            mid = method["id"]
            source = source_by_id.get(method["source_id"])
            if source is None:
                issues.append(f"method:{mid}:missing_source")
                continue
            if method["disposition"] in substantive:
                if scope["mode"] != "model_design":
                    issues.append(f"method:{mid}:standalone_cannot_adopt")
                if source["evidence_level"] not in {"E2", "E3"}:
                    issues.append(f"method:{mid}:original_method_not_verified")
                if method["transferability"] not in {"applicable", "conditional"}:
                    issues.append(f"method:{mid}:transferability_not_supported")
                if search["status"] == "no_suitable_source":
                    issues.append(f"method:{mid}:no_suitable_source_conflict")

        if decision["evidence_status"] == "sufficient" and decision["unresolved_gaps"]:
            issues.append("sufficient_conflicts_with_unresolved_gaps")
        if decision["evidence_status"] == "not_required" and methods:
            issues.append("not_required_conflicts_with_method_assessments")

    return {
        "status": "passed" if not issues else "failed",
        "issues": issues[:80],
        "qualification": "structure_and_internal_consistency_only",
        "search_execution": "declared_not_independently_attested",
        "source_authenticity": "not_assessed",
        "semantic_applicability": "not_assessed",
        "human_model_approval": "not_granted",
        "numerical_acceptance": "not_granted",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only literature evidence validation")
    sub = parser.add_subparsers(dest="command", required=True)
    cmd = sub.add_parser("validate", help="Validate one external JSON report")
    cmd.add_argument("--report", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = validate_report(read_report(args.report))
    except EvidenceError as exc:
        result = {
            "status": "failed", "issues": [str(exc)],
            "human_model_approval": "not_granted",
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
