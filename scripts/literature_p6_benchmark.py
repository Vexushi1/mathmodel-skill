#!/usr/bin/env python3
"""P6 paired historical-problem model-design study, strictly local and read-only.

This tool verifies pinned source/artifact bytes and reports descriptive human
scorecards. It does NOT generate model designs, retrieve publications, judge
mathematical validity, prove blinding, or claim treatment effects.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "docs/literature_p6_historical_case_catalog.json"
MAX_CATALOG_BYTES = 32768
MAX_STUDY_BYTES = 262144
MAX_INPUT_BYTES = 25 * 1024 * 1024
SHA = re.compile(r"^[0-9a-f]{64}$")
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,79}$")
REVIEWER_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{1,79}$")
AXES = (
    "requirements_coverage",
    "mathematical_sufficiency",
    "method_transfer_and_assumptions",
    "comparison_and_validation",
    "source_verifiability",
    "solver_feasibility",
    "challenge_resolution",
)
EXPECTED_CASES = ("COMAP-2024-MCM-A", "COMAP-2024-MCM-C", "COMAP-2024-ICM-D")


class BenchmarkError(ValueError):
    """Non-sensitive diagnostic, without original task or solution text."""


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, val in pairs:
        if key in out:
            raise BenchmarkError("duplicate_json_key")
        out[key] = val
    return out


def _nonfinite(_: str) -> None:
    raise BenchmarkError("nonfinite_json_number")


def load_json(path: Path, max_bytes: int) -> dict[str, Any]:
    try:
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > max_bytes:
            raise BenchmarkError("input_missing_or_oversize")
        raw = path.read_bytes()
        if len(raw) > max_bytes:
            raise BenchmarkError("input_oversize")
        parsed = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique,
                            parse_constant=_nonfinite)
    except BenchmarkError:
        raise
    except (ValueError, UnicodeError, OSError, TypeError) as exc:
        raise BenchmarkError("invalid_json_input") from exc
    if not isinstance(parsed, dict):
        raise BenchmarkError("json_root_not_object")
    return parsed


def require_keys(obj: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(obj, dict) or set(obj) != fields:
        raise BenchmarkError(f"{label}_fields_invalid")
    return obj


def _string(value: Any, limit: int, name: str) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= limit or not value.strip():
        raise BenchmarkError(f"{name}_invalid")
    return value


def _positive(value: Any, maximum: int, name: str, *, zero: bool = True) -> int:
    if type(value) is not int or not (0 if zero else 1) <= value <= maximum:
        raise BenchmarkError(f"{name}_invalid")
    return value


def _duration(value: Any, maximum: float, name: str) -> float:
    if type(value) not in (int, float) or not 0 <= value <= maximum:
        raise BenchmarkError(f"{name}_invalid")
    return float(value)


def catalog_cases(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    require_keys(catalog, {"catalog_version", "purpose", "authoritative_problem_text_embedded",
                           "source_policy", "cases"}, "catalog")
    if (catalog["catalog_version"] != "1.0.0"
            or catalog["purpose"] != "historical_real_problem_paired_model_design_evaluation"
            or catalog["authoritative_problem_text_embedded"] is not False
            or not isinstance(catalog["cases"], list)):
        raise BenchmarkError("catalog_protocol_invalid")
    found = {}
    for case in catalog["cases"]:
        require_keys(case, {"id", "year", "competition", "problem_letter", "title",
                            "task_family", "official_page_url", "official_problem_pdf_url",
                            "required_attachment_kinds", "caveat"}, "catalog_case")
        cid = _string(case["id"], 80, "case_id")
        if cid in found:
            raise BenchmarkError("catalog_duplicate_case_id")
        if (case["year"] != 2024 or case["competition"] not in {"MCM", "ICM"}
                or case["problem_letter"] not in {"A", "C", "D"}
                or not case["official_page_url"].startswith("https://www.comap.org/")
                or not case["official_problem_pdf_url"].startswith("https://www.comap.org/")
                or not isinstance(case["required_attachment_kinds"], list)
                or any(not isinstance(kind, str) or not ID.fullmatch(kind)
                       for kind in case["required_attachment_kinds"])
                or len(set(case["required_attachment_kinds"])) != len(case["required_attachment_kinds"])):
            raise BenchmarkError("catalog_case_source_invalid")
        found[cid] = case
    if tuple(found) != EXPECTED_CASES:
        raise BenchmarkError("catalog_case_set_changed")
    return found


def guarded_file(root: Path, relative: Any, expected_digest: Any, *, pdf: bool = False) -> int:
    rel = _string(relative, 512, "path")
    if "\\" in rel or "\x00" in rel or ":" in rel:
        raise BenchmarkError("unsafe_relative_path")
    pure = PurePosixPath(rel)
    if (pure.is_absolute() or PureWindowsPath(rel).is_absolute()
            or any(part in {"..", "."} for part in pure.parts)):
        raise BenchmarkError("unsafe_relative_path")
    if not isinstance(expected_digest, str) or not SHA.fullmatch(expected_digest):
        raise BenchmarkError("invalid_source_digest")
    path = root
    for part in pure.parts:
        path = path / part
        if path.is_symlink():
            raise BenchmarkError("symlink_source_forbidden")
    if not path.resolve(strict=False).is_relative_to(root):
        raise BenchmarkError("unsafe_relative_path")
    try:
        meta = path.lstat()
        if not stat.S_ISREG(meta.st_mode) or meta.st_size > MAX_INPUT_BYTES or meta.st_size == 0:
            raise BenchmarkError("source_missing_or_oversize")
        hasher = hashlib.sha256()
        size = 0
        first = b""
        with path.open("rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                if not size:
                    first = chunk[:5]
                size += len(chunk)
                if size > MAX_INPUT_BYTES:
                    raise BenchmarkError("source_oversize")
                hasher.update(chunk)
    except BenchmarkError:
        raise
    except OSError as exc:
        raise BenchmarkError("source_unreadable") from exc
    if hasher.hexdigest() != expected_digest:
        raise BenchmarkError("source_sha256_mismatch")
    if pdf and (not rel.lower().endswith(".pdf") or first != b"%PDF-"):
        raise BenchmarkError("task_not_pdf")
    return size


def _scores(scores: Any, label: str) -> dict[str, int]:
    require_keys(scores, set(AXES), label)
    return {key: _positive(scores[key], 4, label + "_score") for key in AXES}


def _review(review: Any) -> dict[str, Any]:
    require_keys(review, {"reviewer_id", "scored_before_unblinding", "scores",
                          "blocking_issues", "unsupported_assumptions", "review_evidence"},
                 "review")
    if not REVIEWER_ID.fullmatch(_string(review["reviewer_id"], 80, "reviewer_id")):
        raise BenchmarkError("reviewer_id_invalid")
    if review["scored_before_unblinding"] is not True:
        raise BenchmarkError("review_must_precede_unblinding")
    scores = require_keys(review["scores"], {"X", "Y"}, "scores")
    _scores(scores["X"], "X")
    _scores(scores["Y"], "Y")
    for field in ("blocking_issues", "unsupported_assumptions"):
        values = require_keys(review[field], {"X", "Y"}, field)
        for val in values.values():
            _positive(val, 100, field)
    notes = require_keys(review["review_evidence"], {"X", "Y"}, "review_evidence")
    for val in notes.values():
        if not isinstance(val, str) or not 12 <= len(val) <= 4096:
            raise BenchmarkError("review_evidence_missing")
    return review


def _arm(arm: Any, root: Path, budget: int) -> dict[str, Any]:
    require_keys(arm, {"model_runtime", "prompt_sha256", "design_path", "design_sha256",
                       "elapsed_minutes", "research_read_minutes", "external_queries",
                       "design_tokens"}, "arm")
    if not ID.fullmatch(_string(arm["model_runtime"], 80, "model_runtime")):
        raise BenchmarkError("model_runtime_invalid")
    if not isinstance(arm["prompt_sha256"], str) or not SHA.fullmatch(arm["prompt_sha256"]):
        raise BenchmarkError("prompt_hash_invalid")
    guarded_file(root, arm["design_path"], arm["design_sha256"])
    _duration(arm["elapsed_minutes"], budget, "elapsed_minutes")
    _duration(arm["research_read_minutes"], budget, "research_read_minutes")
    if arm["research_read_minutes"] > arm["elapsed_minutes"]:
        raise BenchmarkError("reading_time_exceeds_elapsed")
    _positive(arm["external_queries"], 60, "external_queries")
    _positive(arm["design_tokens"], 200000, "design_tokens")
    return arm


def evaluate(study: dict[str, Any], catalog: dict[str, Any], root: Path) -> dict[str, Any]:
    case_catalog = catalog_cases(catalog)
    require_keys(study, {"protocol_version", "study_id", "catalog_version",
                         "protocol_pre_registered", "cases"}, "study")
    if (study["protocol_version"] != "1.0.0" or study["catalog_version"] != "1.0.0"
            or study["protocol_pre_registered"] is not True
            or not ID.fullmatch(_string(study["study_id"], 80, "study_id"))
            or not isinstance(study["cases"], list)):
        raise BenchmarkError("study_protocol_invalid")
    if not root.is_dir() or root.is_symlink():
        raise BenchmarkError("study_root_invalid")
    root = root.resolve(strict=True)
    case_ids = []
    for item in study["cases"]:
        if not isinstance(item, dict) or "case_id" not in item:
            raise BenchmarkError("study_case_invalid")
        cid = item["case_id"]
        if cid not in case_catalog or cid in case_ids:
            raise BenchmarkError("study_case_unknown_or_duplicate")
        case_ids.append(cid)
    missing = [cid for cid in case_catalog if cid not in case_ids]
    if missing:
        return {
            "status": "not_ready", "case_count": len(case_ids),
            "missing_case_ids": missing, "measured_quality_improvement": "not_assessed",
            "source_truth": "not_attested", "no_automatic_model_approval": True,
        }
    case_deltas = []
    for case in study["cases"]:
        require_keys(case, {"case_id", "official_page_url", "task", "attachments",
                            "budget_minutes", "controls", "arms", "unblinding", "reviews"},
                     "study_case")
        origin = case_catalog[case["case_id"]]
        if case["official_page_url"] != origin["official_page_url"]:
            raise BenchmarkError("official_source_identity_drift")
        task = require_keys(case["task"], {"path", "sha256"}, "task")
        guarded_file(root, task["path"], task["sha256"], pdf=True)
        if not isinstance(case["attachments"], list):
            raise BenchmarkError("attachments_invalid")
        seen_kinds = []
        for item in case["attachments"]:
            require_keys(item, {"kind", "path", "sha256"}, "attachment")
            kind = _string(item["kind"], 80, "attachment_kind")
            if kind in seen_kinds:
                raise BenchmarkError("attachment_duplicate_kind")
            seen_kinds.append(kind)
            guarded_file(root, item["path"], item["sha256"])
        if set(seen_kinds) != set(origin["required_attachment_kinds"]):
            raise BenchmarkError("required_attachments_incomplete")
        budget = _positive(case["budget_minutes"], 720, "budget", zero=False)
        controls = require_keys(case["controls"], {
            "same_question_and_attachments", "separate_run_contexts",
            "same_resource_budget", "reviewers_blinded_before_scoring",
        }, "controls")
        if any(value is not True for value in controls.values()):
            raise BenchmarkError("paired_conditions_not_declared")
        arms = require_keys(case["arms"], {"X", "Y"}, "arms")
        left = _arm(arms["X"], root, budget)
        right = _arm(arms["Y"], root, budget)
        if left["model_runtime"] != right["model_runtime"]:
            raise BenchmarkError("different_model_runtime")
        if left["prompt_sha256"] != right["prompt_sha256"]:
            raise BenchmarkError("unequal_prompt_template")
        mapping = require_keys(case["unblinding"], {"X", "Y"}, "unblinding")
        if set(mapping.values()) != {"baseline", "literature_enhanced"}:
            raise BenchmarkError("arm_mapping_invalid")
        baseline = left if mapping["X"] == "baseline" else right
        candidate = right if mapping["Y"] == "literature_enhanced" else left
        if baseline["external_queries"] != 0:
            raise BenchmarkError("baseline_search_not_disabled")
        if not isinstance(case["reviews"], list) or len(case["reviews"]) < 2:
            raise BenchmarkError("insufficient_independent_reviewers")
        reviewers = set()
        diffs = {key: [] for key in AXES}
        counts = {"blocking_issues": [], "unsupported_assumptions": []}
        for review in case["reviews"]:
            _review(review)
            rid = review["reviewer_id"]
            if rid in reviewers:
                raise BenchmarkError("duplicate_reviewer")
            reviewers.add(rid)
            label_base = "X" if mapping["X"] == "baseline" else "Y"
            label_candidate = "Y" if label_base == "X" else "X"
            for key in AXES:
                diffs[key].append(review["scores"][label_candidate][key]
                                  - review["scores"][label_base][key])
            for key in counts:
                counts[key].append(review[key][label_candidate] - review[key][label_base])
        case_deltas.append({
            "case_id": case["case_id"],
            "reviewer_count": len(reviewers),
            "criteria_delta": {key: round(sum(values) / len(values), 3)
                               for key, values in diffs.items()},
            "blocking_delta": round(sum(counts["blocking_issues"]) / len(reviewers), 3),
            "unsupported_assumptions_delta": round(
                sum(counts["unsupported_assumptions"]) / len(reviewers), 3),
            "elapsed_minutes_delta": round(
                candidate["elapsed_minutes"] - baseline["elapsed_minutes"], 3),
            "research_read_minutes_delta": round(
                candidate["research_read_minutes"] - baseline["research_read_minutes"], 3),
            "external_query_delta": candidate["external_queries"] - baseline["external_queries"],
        })
    aggregate = {
        key: round(sum(c["criteria_delta"][key] for c in case_deltas) / len(case_deltas), 3)
        for key in AXES
    }
    return {
        "status": "descriptive_only", "case_count": len(case_deltas),
        "studied_source_kind": "user_supplied_hash_pinned_original_problems_and_outputs",
        "criteria_delta_mean": aggregate, "case_deltas": case_deltas,
        "quality_judgments": "reviewer_declared_not_machine_attested",
        "blinding": "declared_not_independently_attested",
        "causal_inference": "not_established",
        "statistical_significance": "not_assessed",
        "source_authenticity": "not_independently_attested",
        "model_approval": "not_granted",
        "no_automatic_winner_or_release_gate": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    catalog_parser = sub.add_parser("catalog")
    catalog_parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    run = sub.add_parser("evaluate")
    run.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    run.add_argument("--study", required=True, type=Path)
    run.add_argument("--study-root", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        catalog = load_json(args.catalog, MAX_CATALOG_BYTES)
        verified = catalog_cases(catalog)
        if args.action == "catalog":
            result = {
                "status": "catalog_metadata_only", "cases": [
                    {"case_id": x, "title": info["title"], "official_page_url": info["official_page_url"],
                     "requires_original_task_file": True,
                     "required_attachment_kinds": info["required_attachment_kinds"]}
                    for x, info in verified.items()
                ],
                "paired_designs_evaluated": 0,
                "model_quality_gain": "not_assessed",
            }
        else:
            study = load_json(args.study, MAX_STUDY_BYTES)
            result = evaluate(study, catalog, args.study_root)
    except BenchmarkError as exc:
        result = {"status": "invalid", "issues": [str(exc)],
                  "model_quality_gain": "not_assessed",
                  "model_approval": "not_granted"}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] in {"catalog_metadata_only", "descriptive_only"} else 1


if __name__ == "__main__":
    sys.exit(main())
