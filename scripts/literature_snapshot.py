#!/usr/bin/env python3
"""Explicit, source-bound, per-question literature research snapshots.

Snapshots preserve a bounded research report across chats; currentness means
the report and frozen Problem Contract source *bytes* still match. It does not
certify a paper, a mathematical model, an approval, or real search execution.
No Project State or official submission file is modified.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import sys
from typing import Any

from literature_evidence import EvidenceError, read_report, validate_report

QUESTION = re.compile(r"^Q[1-9][0-9]*$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
STORAGE = "research_evidence"
MAX_CONTRACT_BYTES = 131072
MAX_REPORT_BYTES = 262144
MAX_SNAPSHOT_BYTES = 524288


class SnapshotError(ValueError):
    """Non-sensitive failure reason for a source-bound research snapshot."""


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _json_unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise SnapshotError("duplicate_snapshot_json_key")
        obj[key] = value
    return obj


def _parse_json(data: bytes) -> dict[str, Any]:
    def reject(_: str) -> Any:
        raise SnapshotError("invalid_json_number")
    try:
        result = json.loads(
            data.decode("utf-8"), object_pairs_hook=_json_unique,
            parse_constant=reject,
        )
    except SnapshotError:
        raise
    except (UnicodeError, ValueError, TypeError) as exc:
        raise SnapshotError("invalid_snapshot_json") from exc
    if not isinstance(result, dict):
        raise SnapshotError("snapshot_not_object")
    return result


def _root(value: str | Path) -> Path:
    path = Path(value)
    if path.is_symlink() or not path.is_dir():
        raise SnapshotError("project_root_not_real_directory")
    return path.resolve(strict=True)


def _relative(value: str, *, allow_evidence: bool = False) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise SnapshotError("source_path_invalid")
    path = PurePosixPath(value)
    if (path.is_absolute() or PureWindowsPath(value).is_absolute()
            or not path.parts or any(part in {"..", "."} for part in path.parts)
            or ":" in value):
        raise SnapshotError("source_path_outside_project")
    if not allow_evidence and path.parts[0] == STORAGE:
        raise SnapshotError("snapshot_cannot_be_its_own_source")
    return path


def _guarded(root: Path, name: str, *, allow_evidence: bool = False) -> Path:
    parts = _relative(name, allow_evidence=allow_evidence).parts
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise SnapshotError("source_symlink_forbidden")
    try:
        if not current.resolve(strict=False).is_relative_to(root):
            raise SnapshotError("source_path_outside_project")
    except (ValueError, OSError) as exc:
        raise SnapshotError("source_path_outside_project") from exc
    return current


def _read_file(path: Path, *, limit: int) -> bytes:
    try:
        meta = path.lstat()
        if not stat.S_ISREG(meta.st_mode) or meta.st_size > limit:
            raise SnapshotError("source_missing_or_oversized")
        data = path.read_bytes()
    except SnapshotError:
        raise
    except OSError as exc:
        raise SnapshotError("source_unreadable") from exc
    if not data or len(data) > limit:
        raise SnapshotError("source_missing_or_oversized")
    return data


def _question(value: str) -> str:
    if not QUESTION.fullmatch(value):
        raise SnapshotError("question_invalid")
    return value


def _source_input(root: Path, question: str, contract: str,
                  report: str) -> dict[str, Any]:
    _question(question)
    p_contract = _guarded(root, contract)
    p_report = _guarded(root, report)
    contract_bytes = _read_file(p_contract, limit=MAX_CONTRACT_BYTES)
    report_bytes = _read_file(p_report, limit=MAX_REPORT_BYTES)
    if contract == report:
        raise SnapshotError("source_paths_must_be_distinct")
    try:
        record = read_report(p_report)
        verdict = validate_report(record)
    except EvidenceError as exc:
        raise SnapshotError("report_invalid") from exc
    if verdict["status"] != "passed":
        raise SnapshotError("report_invalid")
    scope = record["scope"]
    if (scope["mode"] != "model_design"
            or scope["problem_contract_status"] != "frozen"
            or scope["question"] != question
            or not scope.get("problem_contract_anchor")):
        raise SnapshotError("research_scope_or_freeze_not_bound")
    # Validate that bytes used for the JSON decode did not move while reading.
    if _read_file(p_report, limit=MAX_REPORT_BYTES) != report_bytes:
        raise SnapshotError("report_changed_during_read")
    return {
        "question": question,
        "contract": {"path": contract, "sha256": sha(contract_bytes),
                     "bytes": len(contract_bytes)},
        "report_source": {"path": report, "sha256": sha(report_bytes),
                          "bytes": len(report_bytes)},
        "research": record,
        "research_sha256": sha(canonical(record)),
        "target": f"{STORAGE}/{question}.snapshot.json",
    }


def preview(root: str | Path, question: str,
            contract: str, report: str) -> dict[str, Any]:
    project = _root(root)
    data = _source_input(project, question, contract, report)
    target = _guarded(project, data["target"], allow_evidence=True)
    return {
        "status": "preview",
        "question": question, "target": data["target"],
        "target_exists": target.exists() or target.is_symlink(),
        "contract": data["contract"],
        "report_source": data["report_source"],
        "source_authenticity": "not_assessed",
        "search_execution": "declared_not_independently_attested",
        "model_approval": "not_granted",
        "project_write": False,
    }


def record(root: str | Path, question: str, contract: str,
           report: str, *, expected_contract_sha256: str,
           expected_report_sha256: str, write: bool) -> dict[str, Any]:
    if not write:
        raise SnapshotError("explicit_write_flag_required")
    if not DIGEST.fullmatch(expected_contract_sha256) or not DIGEST.fullmatch(expected_report_sha256):
        raise SnapshotError("expected_source_digest_invalid")
    project = _root(root)
    data = _source_input(project, question, contract, report)
    if (data["contract"]["sha256"] != expected_contract_sha256
            or data["report_source"]["sha256"] != expected_report_sha256):
        raise SnapshotError("source_read_set_changed")
    parent = project / STORAGE
    if parent.is_symlink():
        raise SnapshotError("snapshot_parent_symlink_forbidden")
    if not parent.exists():
        try:
            parent.mkdir(mode=0o700)
        except OSError as exc:
            raise SnapshotError("cannot_create_snapshot_parent") from exc
    if not parent.is_dir() or parent.is_symlink() or parent.resolve() != project / STORAGE:
        raise SnapshotError("snapshot_parent_invalid")
    dest = _guarded(project, data["target"], allow_evidence=True)
    # Recheck source identity immediately before the create; callers can
    # re-preview after concurrent writes. Never overwrite a previous snapshot.
    for item, limit in ((data["contract"], MAX_CONTRACT_BYTES),
                        (data["report_source"], MAX_REPORT_BYTES)):
        current = _read_file(_guarded(project, item["path"]), limit=limit)
        if sha(current) != item["sha256"]:
            raise SnapshotError("source_read_set_changed")
    snapshot = {
        "snapshot_version": "1.0.0",
        "question": question,
        "contract": data["contract"],
        "report_source": data["report_source"],
        "research_sha256": data["research_sha256"],
        "research": data["research"],
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    raw = canonical(snapshot) + b"\n"
    if len(raw) > MAX_SNAPSHOT_BYTES:
        raise SnapshotError("snapshot_size_limit")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(dest, flags, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise SnapshotError("snapshot_already_exists") from exc
    except OSError as exc:
        raise SnapshotError("snapshot_create_failed") from exc
    return {
        "status": "recorded", "path": data["target"],
        "snapshot_sha256": sha(raw),
        "question": question, "model_approval": "not_granted",
        "state_write": False,
    }


def inspect(root: str | Path, question: str) -> dict[str, Any]:
    project = _root(root)
    _question(question)
    rel = f"{STORAGE}/{question}.snapshot.json"
    path = _guarded(project, rel, allow_evidence=True)
    data = _parse_json(_read_file(path, limit=MAX_SNAPSHOT_BYTES))
    fields = {"snapshot_version", "question", "contract", "report_source",
              "research_sha256", "research", "created_at"}
    if set(data) != fields or data["snapshot_version"] != "1.0.0" or data["question"] != question:
        raise SnapshotError("snapshot_protocol_or_scope_invalid")
    issues = []
    for item_name, limit in (("contract", MAX_CONTRACT_BYTES),
                             ("report_source", MAX_REPORT_BYTES)):
        item = data[item_name]
        if (not isinstance(item, dict) or set(item) != {"path", "sha256", "bytes"}
                or not isinstance(item["sha256"], str) or not DIGEST.fullmatch(item["sha256"])
                or type(item["bytes"]) is not int):
            raise SnapshotError("snapshot_source_binding_invalid")
        try:
            raw = _read_file(_guarded(project, item["path"]), limit=limit)
            if sha(raw) != item["sha256"] or len(raw) != item["bytes"]:
                issues.append(f"{item_name}_changed")
        except SnapshotError:
            issues.append(f"{item_name}_missing_or_invalid")
    payload = data["research"]
    if (not isinstance(payload, dict) or not isinstance(data["research_sha256"], str)
            or not DIGEST.fullmatch(data["research_sha256"])):
        raise SnapshotError("snapshot_payload_invalid")
    if sha(canonical(payload)) != data["research_sha256"]:
        issues.append("embedded_report_digest_mismatch")
    validity = validate_report(payload)
    if validity["status"] != "passed":
        issues.append("embedded_report_invalid")
    scope = payload.get("scope")
    if (not isinstance(scope, dict)
            or scope.get("question") != question
            or scope.get("problem_contract_status") != "frozen"):
        issues.append("current_problem_scope_mismatch")
    citations = []
    if not issues and validity["status"] == "passed":
        source_map = {row["id"]: row for row in payload["sources"]}
        for method in payload["methods"]:
            src = source_map.get(method["source_id"])
            if (src and src.get("evidence_level") in {"E2", "E3"}
                    and method.get("disposition") in {"adopt_as_basis", "adapt_to_problem",
                                                      "use_as_comparator", "use_for_validation"}):
                citations.append({"method_id": method["id"], "source_id": src["id"],
                                  "doi": src.get("doi"), "source_url": src["source_url"],
                                  "declared_anchor": src.get("method_anchor"),
                                  "citation_key": None})
    return {
        "status": "current" if not issues else "stale",
        "question": question,
        "path": rel,
        "issues": issues,
        "contract_sha256": data["contract"]["sha256"],
        "report_source_sha256": data["report_source"]["sha256"],
        "snapshot_sha256": sha(_read_file(path, limit=MAX_SNAPSHOT_BYTES)),
        "citation_candidates": citations if not issues else [],
        "source_authenticity": "not_assessed",
        "external_source_currentness": "not_assessed",
        "search_execution": "declared_not_independently_attested",
        "mathematical_applicability": "not_assessed",
        "model_approval": "not_granted",
        "numerical_acceptance": "not_granted",
        "state_write": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for mode in ("preview", "record", "inspect"):
        command = sub.add_parser(mode)
        command.add_argument("--project-root", type=Path, required=True)
        command.add_argument("--question", required=True)
        if mode != "inspect":
            command.add_argument("--problem-contract", required=True)
            command.add_argument("--report", required=True)
        if mode == "record":
            command.add_argument("--expected-contract-sha256", required=True)
            command.add_argument("--expected-report-sha256", required=True)
            command.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect":
            result = inspect(args.project_root, args.question)
        elif args.command == "preview":
            result = preview(args.project_root, args.question,
                             args.problem_contract, args.report)
        else:
            result = record(args.project_root, args.question,
                            args.problem_contract, args.report,
                            expected_contract_sha256=args.expected_contract_sha256,
                            expected_report_sha256=args.expected_report_sha256,
                            write=args.write)
    except (SnapshotError, EvidenceError, ValueError, TypeError, KeyError) as exc:
        reason = str(exc) if isinstance(exc, SnapshotError) else "snapshot_invalid"
        result = {"status": "failed", "issues": [reason],
                  "model_approval": "not_granted", "state_write": False}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] in {"preview", "recorded", "current"} else 1


if __name__ == "__main__":
    sys.exit(main())
