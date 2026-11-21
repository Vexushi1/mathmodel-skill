#!/usr/bin/env python3
"""Score a modeling submission using config/review_weights.json."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "review_weights.json"
REVIEW_SCHEMA_VERSION = "1.0.0"
CHECK_FAMILIES = (
    "edition_compliance",
    "anonymity_and_metadata",
    "ai_disclosure",
    "citation_entity_integrity",
    "rendered_page_surface",
    "figure_table_information_value",
    "reproducibility_and_package",
    "cross_question_dynamic_coverage",
)
COVERAGE_APPLICABILITY = {"applicable", "not_applicable"}
COVERAGE_STATUSES = {"passed", "findings_present", "unverifiable", "not_applicable"}
VERIFICATION_MODES = {"machine", "manual", "hybrid"}
FINDING_SEVERITIES = {"blocking", "review_required", "warning"}
FINDING_STATUSES = {"open", "resolved", "accepted_exception"}
RULE_VERIFICATION_STATUSES = {"verified", "unverified", "expired"}
DELIVERY_MODES = {"official", "reproducibility"}
OFFICIAL_RULE_HARD_FAIL = "verified_official_rule_violation"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def load_payload(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return yaml.safe_load(text) or {}


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (Mapping, Sequence)) and not isinstance(value, (str, bytes)):
        return bool(value)
    return True


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be a mapping")
    return value


def _require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    return value


def _hard_fail_codes(value: Any, field: str = "hard_fail") -> set[str]:
    items = _require_list(value, field)
    invalid = [item for item in items if not isinstance(item, str) or not item.strip()]
    if invalid:
        raise ValueError(f"{field} must contain non-empty string codes")
    return set(items)


def _require_fields(item: Mapping[str, Any], fields: Sequence[str], origin: str) -> None:
    missing = [field for field in fields if field not in item]
    if missing:
        raise ValueError(f"{origin} missing fields: {missing}")


def _validate_sha256(value: Any, field: str) -> None:
    if value is not None and (not isinstance(value, str) or SHA256_RE.fullmatch(value) is None):
        raise ValueError(f"{field} must be null or a lowercase SHA-256 digest")


def _page_ranges(value: Any, page_count: int, field: str) -> list[list[int]]:
    """Merge one-based inclusive intervals without expanding them into individual pages."""
    items = _require_list(value, field)
    for item in items:
        if (
            not isinstance(item, list) or len(item) != 2
            or any(type(page) is not int for page in item)
            or not 1 <= item[0] <= item[1] <= page_count
        ):
            raise ValueError(f"{field} must contain inclusive page pairs within 1..{page_count}")
    merged: list[list[int]] = []
    for start, end in sorted(items):
        if merged and start <= merged[-1][1] + 1:
            merged[-1][1] = max(end, merged[-1][1])
        else:
            merged.append([start, end])
    return merged


def _check_rendered_pages(entry: dict[str, Any], context: Mapping[str, Any], pdf_path: Path | None) -> str | None:
    compiled_hash = context["compiled_pdf_sha256"]
    record = entry.get("page_review")
    if entry["applicability"] == "not_applicable":
        if not isinstance(entry["evidence"], str) or not entry["evidence"].strip():
            return "document the reason this delivery does not require a PDF"
        if compiled_hash or pdf_path is not None or context["delivery_mode"] == "official":
            return "PDF coverage is required for the supplied PDF or official delivery"
        if record is not None and (
            not isinstance(record, Mapping) or any(value is not None and value != [] for value in record.values())
        ):
            return "a delivery without a PDF cannot claim a PDF review"
        return None
    if entry["verification_mode"] == "machine":
        return "machine checks cannot establish visual page coverage"
    if not isinstance(record, Mapping):
        return "no structured visual page review for the current PDF"
    if record.get("method") != "assistant_visual":
        return "record assistant_visual only for pages the assistant actually viewed"
    if not compiled_hash or record.get("pdf_sha256") != compiled_hash:
        return "visual review digest does not match review_context.compiled_pdf_sha256"
    if pdf_path is None:
        return "current PDF was not supplied for digest and page-count verification"
    try:
        data = pdf_path.read_bytes()
    except OSError as exc:
        return f"current PDF cannot be read: {exc}"
    if hashlib.sha256(data).hexdigest() != compiled_hash:
        return "current PDF bytes differ from the reviewed PDF"
    try:
        from pypdf import PdfReader
        from pypdf.errors import PyPdfError
    except ImportError:
        return "current PDF page count could not be verified: pypdf is unavailable"
    try:
        page_count = len(PdfReader(io.BytesIO(data), strict=True).pages)
    except (PyPdfError, ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as exc:
        return f"current PDF page count could not be verified: {exc}"
    if page_count < 1 or type(record.get("page_count")) is not int or record["page_count"] != page_count:
        return f"reviewed page_count does not match current PDF ({page_count} pages)"
    try:
        viewed = _page_ranges(record.get("viewed_ranges"), page_count, "viewed_ranges")
        uncovered = _page_ranges(record.get("uncovered_ranges"), page_count, "uncovered_ranges")
    except ValueError as exc:
        return str(exc)
    remaining = []
    next_page = 1
    for start, end in viewed:
        if next_page < start:
            remaining.append([next_page, start - 1])
        next_page = end + 1
    if next_page <= page_count:
        remaining.append([next_page, page_count])
    entry["page_review"] = dict(record, viewed_ranges=viewed, uncovered_ranges=uncovered)
    if remaining != uncovered:
        return f"uncovered_ranges disagrees with viewed_ranges; the uncovered pages are {remaining}"
    if remaining:
        return f"visual review has uncovered pages: {remaining}"
    return None


def _normalize_review_matrix(
    config: Mapping[str, Any],
    report: Mapping[str, Any],
    allowed_hard_fail: set[str],
    pdf_path: Path | None,
) -> dict[str, Any]:
    version = str(report.get("review_schema_version", ""))
    if version != REVIEW_SCHEMA_VERSION:
        raise ValueError(f"unsupported review_schema_version: {version!r}")

    context = _require_mapping(report.get("review_context"), "review_context")
    context_fields = (
        "skill_version",
        "competition_profile",
        "edition",
        "rule_verification_status",
        "rule_verified_at",
        "rule_source",
        "delivery_mode",
        "source_bundle_sha256",
        "compiled_pdf_sha256",
    )
    _require_fields(context, context_fields, "review_context")
    if not _nonempty(context.get("skill_version")):
        raise ValueError("review_context.skill_version is required")
    if not _nonempty(context.get("competition_profile")):
        raise ValueError("review_context.competition_profile is required")
    rule_status = context.get("rule_verification_status")
    if rule_status not in RULE_VERIFICATION_STATUSES:
        raise ValueError(f"unknown rule_verification_status: {rule_status!r}")
    delivery_mode = context.get("delivery_mode")
    if delivery_mode not in DELIVERY_MODES:
        raise ValueError(f"unknown delivery_mode: {delivery_mode!r}")
    _validate_sha256(context.get("source_bundle_sha256"), "review_context.source_bundle_sha256")
    _validate_sha256(context.get("compiled_pdf_sha256"), "review_context.compiled_pdf_sha256")
    if not context["source_bundle_sha256"]:
        raise ValueError("review_context.source_bundle_sha256 is required for a final review matrix")
    if rule_status == "verified" and not (
        _nonempty(context.get("rule_verified_at")) and _nonempty(context.get("rule_source"))
    ):
        raise ValueError("verified official rule context requires rule_verified_at and rule_source")

    coverage = _require_list(report.get("coverage"), "coverage")
    coverage_fields = (
        "check_family",
        "applicability",
        "verification_mode",
        "status",
        "rule_source",
        "evidence",
    )
    coverage_by_family: dict[str, dict[str, Any]] = {}
    normalized_coverage: list[dict[str, Any]] = []
    for index, raw_entry in enumerate(coverage):
        entry = _require_mapping(raw_entry, f"coverage[{index}]")
        _require_fields(entry, coverage_fields, f"coverage[{index}]")
        family = entry.get("check_family")
        if family not in CHECK_FAMILIES:
            raise ValueError(f"unknown coverage check_family: {family!r}")
        if family in coverage_by_family:
            raise ValueError(f"duplicate coverage check_family: {family}")
        applicability = entry.get("applicability")
        if applicability not in COVERAGE_APPLICABILITY:
            raise ValueError(f"unknown coverage applicability: {applicability!r}")
        verification_mode = entry.get("verification_mode")
        if verification_mode not in VERIFICATION_MODES:
            raise ValueError(f"unknown coverage verification_mode: {verification_mode!r}")
        status = entry.get("status")
        if status not in COVERAGE_STATUSES:
            raise ValueError(f"unknown coverage status: {status!r}")
        if applicability == "not_applicable" and status != "not_applicable":
            raise ValueError(f"coverage {family} marked not_applicable must use not_applicable status")
        if applicability == "applicable" and status == "not_applicable":
            raise ValueError(f"coverage {family} cannot use not_applicable status when applicable")
        if not _nonempty(entry.get("rule_source")):
            raise ValueError(f"coverage {family} rule_source is required")
        if not _nonempty(entry.get("evidence")):
            raise ValueError(f"coverage {family} evidence is required for status {status}")
        if family == "edition_compliance" and rule_status != "verified" and status == "passed":
            raise ValueError("unverified or expired edition rules cannot be marked passed")
        normalized = dict(entry)
        coverage_by_family[str(family)] = normalized
        normalized_coverage.append(normalized)
    missing_families = sorted(set(CHECK_FAMILIES) - set(coverage_by_family))
    if missing_families or len(coverage_by_family) != len(CHECK_FAMILIES):
        raise ValueError(f"coverage families must contain each stable family exactly once: {missing_families}")

    surface = coverage_by_family["rendered_page_surface"]
    if surface["status"] == "passed" and not context["compiled_pdf_sha256"]:
        raise ValueError("review_context.compiled_pdf_sha256 is required for a passed PDF review")
    surface.pop("page_review_issue", None)
    page_review_issue = _check_rendered_pages(surface, context, pdf_path)
    if page_review_issue:
        surface["page_review_issue"] = page_review_issue
        if surface["status"] == "passed":
            surface["status"] = "unverifiable"

    dimensions = set((config.get("dimensions") or {}).keys())
    findings = _require_list(report.get("findings"), "findings")
    finding_fields = (
        "check_id",
        "check_family",
        "dimension",
        "severity",
        "status",
        "hard_fail_code",
        "rule_source",
        "verification_mode",
        "location",
        "evidence",
        "action",
    )
    seen_ids: set[str] = set()
    normalized_findings: list[dict[str, Any]] = []
    open_blocking_codes: set[str] = set()
    open_severities: set[str] = set()
    finding_families: set[str] = set()
    for index, raw_finding in enumerate(findings):
        finding = _require_mapping(raw_finding, f"findings[{index}]")
        _require_fields(finding, finding_fields, f"findings[{index}]")
        check_id = finding.get("check_id")
        if not isinstance(check_id, str) or not check_id.strip():
            raise ValueError(f"findings[{index}].check_id is required")
        if check_id in seen_ids:
            raise ValueError(f"duplicate check_id: {check_id}")
        seen_ids.add(check_id)
        family = finding.get("check_family")
        if family not in CHECK_FAMILIES:
            raise ValueError(f"unknown finding check_family: {family!r}")
        dimension = finding.get("dimension")
        if dimension not in dimensions:
            raise ValueError(f"unknown finding dimension: {dimension!r}")
        severity = finding.get("severity")
        if severity not in FINDING_SEVERITIES:
            raise ValueError(f"unknown finding severity: {severity!r}")
        status = finding.get("status")
        if status not in FINDING_STATUSES:
            raise ValueError(f"unknown finding status: {status!r}")
        verification_mode = finding.get("verification_mode")
        if verification_mode not in VERIFICATION_MODES:
            raise ValueError(f"unknown finding verification_mode: {verification_mode!r}")
        if not _nonempty(finding.get("rule_source")):
            raise ValueError(f"findings[{index}].rule_source is required")
        if status != "resolved":
            for field in ("location", "evidence", "action"):
                if not _nonempty(finding.get(field)):
                    raise ValueError(f"findings[{index}].{field} is required when status={status}")
        hard_fail_code = finding.get("hard_fail_code")
        if hard_fail_code is not None and hard_fail_code not in allowed_hard_fail:
            raise ValueError(f"unknown hard-fail code in finding {check_id}: {hard_fail_code!r}")
        if hard_fail_code is not None and severity != "blocking":
            raise ValueError(f"finding {check_id} hard_fail_code is only valid for blocking severity")
        if severity == "blocking" and status == "open":
            if not _nonempty(hard_fail_code):
                raise ValueError(f"findings[{index}].hard_fail_code is required for open blocking")
            open_blocking_codes.add(str(hard_fail_code))
        if hard_fail_code == OFFICIAL_RULE_HARD_FAIL:
            if rule_status != "verified" or not (
                _nonempty(context.get("rule_verified_at")) and _nonempty(context.get("rule_source"))
            ):
                raise ValueError("verified official rule context is required for verified_official_rule_violation")
            if status == "accepted_exception":
                raise ValueError("accepted_exception cannot waive a verified official rule violation")
        if status == "open":
            open_severities.add(str(severity))
            if coverage_by_family[str(family)].get("status") != "findings_present":
                raise ValueError(f"coverage {family} must use findings_present while an open finding exists")
        finding_families.add(str(family))
        normalized_findings.append(dict(finding))

    empty_finding_coverage = sorted(
        family
        for family, entry in coverage_by_family.items()
        if entry.get("status") == "findings_present" and family not in finding_families
    )
    if empty_finding_coverage:
        raise ValueError(f"coverage marked findings_present without findings: {empty_finding_coverage}")

    dimension_evidence = _require_mapping(report.get("evidence"), "evidence")
    missing_evidence = sorted(name for name in dimensions if not _nonempty(dimension_evidence.get(name)))
    if missing_evidence:
        raise ValueError(f"missing dimension evidence: {missing_evidence}")

    declared = _hard_fail_codes(report.get("hard_fail", []))
    invalid_declared = sorted(declared - allowed_hard_fail)
    if invalid_declared:
        raise ValueError(f"unknown hard-fail codes: {invalid_declared}")
    if declared - open_blocking_codes:
        raise ValueError(
            "matrix hard_fail codes require matching open blocking findings: "
            f"{sorted(declared - open_blocking_codes)}"
        )
    hard_fail = declared | open_blocking_codes
    if hard_fail or "blocking" in open_severities:
        review_status = "blocking"
    elif page_review_issue or "review_required" in open_severities or any(
        entry.get("status") == "unverifiable" for entry in normalized_coverage
    ):
        review_status = "review_required"
    elif "warning" in open_severities:
        review_status = "warning"
    else:
        review_status = "passed"
    return {
        "review_schema_version": REVIEW_SCHEMA_VERSION,
        "review_context": dict(context),
        "review_status": review_status,
        "coverage": normalized_coverage,
        "findings": normalized_findings,
        "hard_fail": hard_fail,
    }


def score_submission(
    config: Mapping[str, Any], report: Mapping[str, Any], *, pdf_path: Path | None = None
) -> dict[str, Any]:
    dimensions = config.get("dimensions", {})
    weights = {name: float(item["weight"]) for name, item in dimensions.items()}
    if abs(sum(weights.values()) - 1.0) > 1e-9:
        raise ValueError("review weights must sum to 1")

    supplied = report.get("scores", {})
    missing = [name for name in dimensions if name not in supplied]
    unknown = [name for name in supplied if name not in dimensions]
    if missing:
        raise ValueError(f"missing dimension scores: {missing}")
    if unknown:
        raise ValueError(f"unknown dimension scores: {unknown}")

    normalized: dict[str, float] = {}
    contributions: dict[str, float] = {}
    for name, value in supplied.items():
        score = float(value)
        if not 0 <= score <= float(config.get("scale", 100)):
            raise ValueError(f"score out of range for {name}: {score}")
        normalized[name] = score
        contributions[name] = score * weights[name]

    allowed_hard_fail = set(config.get("hard_fail", []))
    declared_hard_fail = _hard_fail_codes(report.get("hard_fail", []))
    invalid_hard_fail = sorted(declared_hard_fail - allowed_hard_fail)
    if invalid_hard_fail:
        raise ValueError(f"unknown hard-fail codes: {invalid_hard_fail}")

    matrix = None
    if "review_schema_version" in report:
        matrix = _normalize_review_matrix(config, report, allowed_hard_fail, pdf_path)
        declared_hard_fail = matrix["hard_fail"]

    total = round(sum(contributions.values()), 4)
    rejected = bool(declared_hard_fail)
    result = {
        "version": config.get("version"),
        "total": total,
        "scale": config.get("scale", 100),
        "status": config.get("hard_fail_action") if rejected else "scored",
        "hard_fail": sorted(declared_hard_fail),
        "scores": normalized,
        "weighted_contributions": {name: round(value, 4) for name, value in contributions.items()},
        "evidence": report.get("evidence", {}),
    }
    if matrix is not None:
        result.update(
            review_schema_version=matrix["review_schema_version"],
            review_context=matrix["review_context"],
            review_status=matrix["review_status"],
            coverage=matrix["coverage"],
            findings=matrix["findings"],
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", help="YAML/JSON file containing scores, evidence and optional hard_fail codes")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--output")
    parser.add_argument("--pdf", type=Path, help="current compiled PDF for rendered-page review")
    args = parser.parse_args()
    result = score_submission(load_payload(Path(args.config)), load_payload(Path(args.report)), pdf_path=args.pdf)
    rendered = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")
    return 2 if result["hard_fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
