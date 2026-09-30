#!/usr/bin/env python3
"""D1 corpus admission and deterministic indexing; case content is inert data.

No retrieval, project state writer, model approval or numerical qualification is
implemented here. The repository metadata generator owns the canonical index.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

from jsonschema import Draft202012Validator
import safe_yaml
import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS_ROOT = ROOT / "knowledge/case_memory"
PROTOCOL_VERSION = "1.0.0"
SUPPORTED_SCHEMA_SHA256 = "4d6a70e50fb5a238833efb672dc70734204588e0980dc5a8bd4adcdd515714b1"
HARD_LIMITS = {"file_bytes": 262144, "total_bytes": 2097152, "cases": 64,
               "sources": 64, "depth": 32, "nodes": 32768, "string_chars": 8192}


class CaseMemoryError(ValueError):
    """An admission failure with safe diagnostic fields, without private text."""

    def __init__(self, code: str, message: str, object_id: str = "corpus", field: str = ""):
        self.code, self.message = code, message
        self.object_id = object_id if re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", object_id) else "invalid_id"
        self.field = ".".join(part if re.fullmatch(r"[A-Za-z0-9_-]{1,64}", part) else "invalid_field"
                              for part in field.split("."))[:512]
        super().__init__(f"{self.code}: {self.object_id}: {self.field}: {self.message}")

    def diagnostic(self) -> dict:
        return {"object_id": self.object_id, "field": self.field, "code": self.code, "message": self.message}


def _canonical(value: Any) -> bytes:
    def normalize(item: Any) -> Any:
        if isinstance(item, str):
            return item.replace("\r\n", "\n").replace("\r", "\n")
        if isinstance(item, list):
            return [normalize(child) for child in item]
        if isinstance(item, dict):
            return {normalize(key): normalize(child) for key, child in item.items()}
        return item
    return json.dumps(normalize(value), sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def source_sha256(source: dict) -> str:
    """Bind the independent source record, including its rights, using canonical JSON."""
    return hashlib.sha256(_canonical(source)).hexdigest()


def _path(root: Path, name: str) -> Path:
    path = root / name
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise CaseMemoryError("path_violation", "symbolic links are outside the corpus protocol", field=name)
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        raise CaseMemoryError("path_violation", "resolved input must remain inside the corpus root", field=name) from None
    return path


def _read_bytes(path: Path, limit: int) -> bytes:
    if not path.is_file():
        raise CaseMemoryError("file_missing", "required corpus file is missing", field=path.name)
    if path.stat().st_size > limit:
        raise CaseMemoryError("budget_exceeded", "file byte budget exceeded", field=path.name)
    with path.open("rb") as handle:
        raw = handle.read(limit + 1)
    if len(raw) > limit:
        raise CaseMemoryError("budget_exceeded", "file byte budget exceeded", field=path.name)
    return raw


def _json(raw: bytes) -> Any:
    def unique(pairs: list) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise CaseMemoryError("schema_error", "duplicate JSON key")
            result[key] = value
        return result
    def nonfinite(_value: str) -> None:
        raise CaseMemoryError("schema_error", "non-finite JSON number")
    try:
        return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique, parse_constant=nonfinite)
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        if isinstance(exc, CaseMemoryError):
            raise
        raise CaseMemoryError("schema_error", "invalid bounded UTF-8 JSON document") from None


def _schema_document(raw: bytes) -> dict:
    text = raw.decode("utf-8-sig")
    # Preserve ordinary safe_yaml/cache semantics after rejecting ambiguous YAML.
    node = yaml.compose(text, Loader=yaml.SafeLoader)
    pending, seen = [(node, 0)], set()
    while pending:
        current, depth = pending.pop()
        if current is None or id(current) in seen:
            raise CaseMemoryError("schema_error", "aliases or cyclic Schema graphs are not permitted")
        seen.add(id(current))
        if len(seen) > HARD_LIMITS["nodes"] or depth > HARD_LIMITS["depth"]:
            raise CaseMemoryError("budget_exceeded", "Schema node or nesting budget exceeded")
        if isinstance(current, yaml.MappingNode):
            keys = set()
            for key, value in current.value:
                if not isinstance(key, yaml.ScalarNode) or key.value in keys:
                    raise CaseMemoryError("schema_error", "duplicate or non-scalar YAML Schema key")
                keys.add(key.value)
                pending.append((value, depth + 1))
        elif isinstance(current, yaml.SequenceNode):
            pending.extend((child, depth + 1) for child in current.value)
    return safe_yaml.safe_load(text)


def _local_refs(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref" and (not isinstance(child, str) or not child.startswith("#/")):
                raise CaseMemoryError("schema_error", "Schema references must be local JSON pointers")
            _local_refs(child)
    elif isinstance(value, list):
        for child in value:
            _local_refs(child)


def _tree(value: Any, limits: dict) -> int:
    stack, containers, nodes = [(value, 0)], set(), 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > limits["nodes"] or depth > limits["depth"]:
            raise CaseMemoryError("budget_exceeded", "document node or nesting budget exceeded")
        if isinstance(item, str) and len(item) > limits["string_chars"]:
            raise CaseMemoryError("budget_exceeded", "document string budget exceeded")
        if isinstance(item, float) and not math.isfinite(item):
            raise CaseMemoryError("schema_error", "non-finite document number")
        if isinstance(item, (dict, list)):
            if id(item) in containers:
                raise CaseMemoryError("schema_error", "aliases or cyclic document graphs are not permitted")
            containers.add(id(item))
            children = list(item.values()) + list(item.keys()) if isinstance(item, dict) else item
            stack.extend((child, depth + 1) for child in children)
        elif not isinstance(item, (str, int, float, bool, type(None))):
            raise CaseMemoryError("schema_error", "unsupported document value type")
    return nodes


def _screen(value: Any, patterns: list[re.Pattern], object_id: str, field: str = "") -> None:
    if isinstance(value, str):
        if any(pattern.search(value) for pattern in patterns):
            raise CaseMemoryError("privacy_violation", "publication screening found sensitive content; remove it before admission",
                                  object_id, field)
    elif isinstance(value, dict):
        for key, child in value.items():
            _screen(key, patterns, object_id, field)
            _screen(child, patterns, object_id, f"{field}.{key}".strip("."))
    elif isinstance(value, list):
        for number, child in enumerate(value):
            _screen(child, patterns, object_id, f"{field}.{number}".strip("."))


class _Snapshot:
    def __init__(self, corpus_root: Path):
        self.root = Path(corpus_root).absolute()
        self.raw: dict[str, bytes] = {}
        self.total = 0
        self.nodes = 0

    def read(self, name: str, limits: dict) -> bytes:
        raw = _read_bytes(_path(self.root, name), limits["file_bytes"])
        self.total += len(raw)
        if self.total > limits["total_bytes"]:
            raise CaseMemoryError("budget_exceeded", "corpus total byte budget exceeded")
        if name in self.raw and self.raw[name] != raw:
            raise CaseMemoryError("source_changed", "corpus source changed during the read", field=name)
        self.raw[name] = raw
        return raw

    def recheck(self, limits: dict) -> None:
        for name, previous in self.raw.items():
            if _read_bytes(_path(self.root, name), limits["file_bytes"]) != previous:
                raise CaseMemoryError("source_changed", "corpus source changed before return", field=name)

    def read_set(self) -> dict:
        return {name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(self.raw.items())}


def _load(snapshot: _Snapshot) -> tuple[dict, dict, dict, dict]:
    try:
        schema = _schema_document(snapshot.read("schema.yaml", HARD_LIMITS))
        _tree(schema, HARD_LIMITS)
        if not isinstance(schema, dict) or schema.get("version") != PROTOCOL_VERSION:
            raise CaseMemoryError("schema_error", "unsupported Case Memory Schema version")
        _local_refs(schema)
        schema_identity = deepcopy(schema)
        schema_identity["x-admission"]["limits"] = HARD_LIMITS
        if hashlib.sha256(_canonical(schema_identity)).hexdigest() != SUPPORTED_SCHEMA_SHA256:
            raise CaseMemoryError("schema_error", "unsupported admission Authority identity; review Schema and consumer together")
        policy = schema["x-admission"]
        if (policy["protocol_version"] != PROTOCOL_VERSION or policy["source_kinds"] != ["synthetic"]
                or policy["synthetic_evidence"] != ["synthetic_example", "recommended_validation"]):
            raise CaseMemoryError("schema_error", "unsupported D1 admission policy")
        limits = policy["limits"]
        if set(limits) != set(HARD_LIMITS) or any(type(value) is not int or not 0 < value <= HARD_LIMITS[key]
                                               for key, value in limits.items()):
            raise CaseMemoryError("schema_error", "invalid or excessive admission limits")
        if any(len(raw) > limits["file_bytes"] for raw in snapshot.raw.values()):
            raise CaseMemoryError("budget_exceeded", "authority file byte budget exceeded")
        sources = _json(snapshot.read("sources.json", limits))
        cases = _json(snapshot.read("cases.json", limits))
        snapshot.nodes = _tree(schema, limits) + _tree(sources, limits) + _tree(cases, limits)
        if snapshot.nodes > limits["nodes"]:
            raise CaseMemoryError("budget_exceeded", "corpus total node budget exceeded")
        for document, key in ((sources, "sources"), (cases, "cases")):
            if isinstance(document, dict) and isinstance(document.get(key), list) and len(document[key]) > limits[key]:
                raise CaseMemoryError("budget_exceeded", "case or source count budget exceeded")
        Draft202012Validator.check_schema(schema)
        error = next(Draft202012Validator(schema).iter_errors({"sources": sources, "cases": cases}), None)
        if error:
            raise CaseMemoryError("schema_error", "corpus does not match the closed admission Schema",
                                  field=".".join(map(str, error.absolute_path)))
        if len(sources["sources"]) > limits["sources"] or len(cases["cases"]) > limits["cases"]:
            raise CaseMemoryError("budget_exceeded", "case or source count budget exceeded")
        return schema, policy, sources, cases
    except CaseMemoryError:
        raise
    except Exception:
        raise CaseMemoryError("schema_error", "admission authority or document is invalid") from None


def _unique(records: list[dict], label: str) -> dict[str, dict]:
    result = {}
    for record in records:
        if record["id"] in result:
            raise CaseMemoryError("duplicate_id", "duplicate stable ID", record["id"], label)
        result[record["id"]] = record
    return result


def _admit(policy: dict, sources: dict, cases: dict) -> tuple[list[dict], dict]:
    patterns = [re.compile(pattern) for pattern in policy["privacy_patterns"]]
    source_records = _unique(sources["sources"], "sources")
    case_records = _unique(cases["cases"], "cases")
    for source in source_records.values():
        _screen(source, patterns, source["id"])
        if source["kind"] not in policy["source_kinds"]:
            raise CaseMemoryError("unsupported_source", "D1 real-source admission requires a separate authorization and factual review capability",
                                  source["id"], "kind")
        rights = source["rights"]
        if (rights["license_id"] not in policy["licenses"]
                or not set(policy["required_uses"]).issubset(rights["allowed_uses"])
                or rights["authorization_basis"] != "independently_authored_synthetic"):
            raise CaseMemoryError("rights_violation", "publication rights and synthetic authorship must be declared; a declaration is not independent proof",
                                  source["id"], "rights")
    for case in case_records.values():
        _screen(case, patterns, case["id"])
        if case.get("near_duplicates", {}).get("status") == "unresolved" and case["status"] == "reviewed":
            raise CaseMemoryError("near_duplicate_unresolved", "resolve the suspected duplicate origin before reviewed admission",
                                  case["id"], "near_duplicates")
        source = source_records.get(case["source"]["id"])
        if source is None or source_sha256(source) != case["source"]["sha256"]:
            raise CaseMemoryError("stale_source", "case source is missing or its current canonical identity differs", case["id"], "source")
        _unique(case["evidence"], "evidence")
        for item in case["evidence"]:
            if item["kind"] not in policy["synthetic_evidence"]:
                raise CaseMemoryError("unobserved_validation", "synthetic material cannot establish observed facts or execution", case["id"], "evidence")
            if item["source_anchor"] not in source["sections"]:
                raise CaseMemoryError("source_anchor_missing", "evidence must resolve to a current source section", case["id"], "evidence")
            if _canonical(item["statement"]) != _canonical(source["sections"][item["source_anchor"]]):
                raise CaseMemoryError("source_anchor_mismatch", "D1 evidence statement must match its synthetic source section",
                                      case["id"], "evidence")
        if case["validation"]["completed_checks"] or case["validation"]["outcome"] != "not_run":
            raise CaseMemoryError("unobserved_validation", "no executed validation is admitted for D1 synthetic seeds", case["id"], "validation")
    eligible = sorted((case for case in case_records.values() if case["status"] == "reviewed"), key=lambda case: case["id"])
    return eligible, source_records


def _groups(eligible: list[dict], sources: dict) -> list[dict]:
    parents = {case["id"]: case["id"] for case in eligible}
    def normalized(item: Any) -> Any:
        if isinstance(item, str):
            return " ".join(item.split()).casefold()
        if isinstance(item, list):
            return [normalized(child) for child in item]
        if isinstance(item, dict):
            return {key: normalized(child) for key, child in item.items()}
        return item
    def find(key: str) -> str:
        while key != parents[key]:
            key = parents[key]
        return key
    origins, cores = {}, {}
    for case in eligible:
        origin = sources[case["source"]["id"]]["origin_group"]
        core = {key: case[key] for key in ("structure", "decision", "validation", "transfer")}
        # Whitespace/case changes and different metadata do not manufacture an independent source.
        digest = hashlib.sha256(_canonical(normalized(core))).hexdigest()
        for mapping, identity in ((origins, origin), (cores, digest)):
            if identity in mapping:
                left, right = find(case["id"]), find(mapping[identity])
                parents[max(left, right)] = min(left, right)
            else:
                mapping[identity] = case["id"]
    groups = {}
    for case in eligible:
        groups.setdefault(find(case["id"]), []).append(case)
    result = []
    for members in groups.values():
        origin = min(sources[case["source"]["id"]]["origin_group"] for case in members)
        result.append({"origin_group": origin, "case_ids": [case["id"] for case in members], "representative": members[0]})
    return sorted(result, key=lambda group: (group["origin_group"], group["case_ids"][0]))


def _inspect(corpus_root: Path) -> tuple[dict, _Snapshot, dict]:
    snapshot = _Snapshot(corpus_root)
    schema, policy, sources, cases = _load(snapshot)
    eligible, source_records = _admit(policy, sources, cases)
    groups = _groups(eligible, source_records)
    identity = {"schema": schema, "sources": sources, "cases": cases}
    report = {"status": "corpus_valid", "protocol_version": PROTOCOL_VERSION,
              "independent_review": "not_run", "execution_authorized": False,
              "eligible_cases": eligible, "groups": groups, "errors": [],
              "counts": {"cases": len(cases["cases"]), "sources": len(source_records),
                         "reviewed_cases": len(eligible), "indexed_groups": len(groups)},
              "corpus_sha256": hashlib.sha256(_canonical(identity)).hexdigest()}
    return report, snapshot, policy["limits"]


def _failure(error: Exception) -> dict:
    problem = error if isinstance(error, CaseMemoryError) else CaseMemoryError("read_error", "corpus could not be safely read")
    return {"status": "blocked", "protocol_version": PROTOCOL_VERSION, "execution_authorized": False,
            "independent_review": "not_run", "eligible_cases": [], "groups": [], "counts": {},
            "read_set": {}, "errors": [problem.diagnostic()]}


def _index_payload(report: dict, snapshot: _Snapshot, limits: dict) -> dict:
    payload = {key: report[key] for key in ("protocol_version", "corpus_sha256", "counts", "groups")}
    size = len((json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8"))
    if size > limits["file_bytes"] or snapshot.total + size > limits["total_bytes"]:
        raise CaseMemoryError("budget_exceeded", "derived index would exceed its readable byte budget")
    if snapshot.nodes + _tree(payload, limits) > limits["nodes"]:
        raise CaseMemoryError("budget_exceeded", "corpus and derived index exceed the total node budget")
    return payload


def inspect_corpus(corpus_root: Path = DEFAULT_CORPUS_ROOT) -> dict:
    """Read-only publication/admission report; returned objects never confer project qualifications."""
    try:
        report, snapshot, limits = _inspect(corpus_root)
        snapshot.recheck(limits)
        report["read_set"] = snapshot.read_set()
        return deepcopy(report)
    except Exception as error:
        return _failure(error)


def build_index(corpus_root: Path = DEFAULT_CORPUS_ROOT) -> dict:
    """Produce a deterministic reviewed-only payload without writing any file."""
    try:
        report, snapshot, limits = _inspect(corpus_root)
        payload = _index_payload(report, snapshot, limits)
        snapshot.recheck(limits)
        return deepcopy(payload)
    except CaseMemoryError:
        raise
    except Exception:
        raise CaseMemoryError("read_error", "corpus could not be safely read") from None


def check_index(corpus_root: Path = DEFAULT_CORPUS_ROOT, index_path: Path | None = None) -> dict:
    """Read-only freshness check; a missing, changed or retired corpus never replays an old index."""
    try:
        report, snapshot, limits = _inspect(corpus_root)
        candidate = Path(index_path).absolute() if index_path is not None else snapshot.root / "index.json"
        try:
            relative = candidate.relative_to(snapshot.root).as_posix()
        except ValueError:
            raise CaseMemoryError("path_violation", "index must remain inside the corpus root") from None
        if not _path(snapshot.root, relative).is_file():
            raise CaseMemoryError("index_missing", "derived index is missing; rebuild through the repository generator")
        expected = _index_payload(report, snapshot, limits)
        actual = _json(snapshot.read(relative, limits))
        if snapshot.nodes + _tree(actual, limits) > limits["nodes"]:
            raise CaseMemoryError("budget_exceeded", "corpus and supplied index exceed the total node budget")
        if _canonical(actual) != _canonical(expected):
            raise CaseMemoryError("index_stale", "derived index differs from current admitted corpus; rebuild before consumption")
        snapshot.recheck(limits)
        return {"status": "index_current", "protocol_version": PROTOCOL_VERSION,
                "corpus_sha256": report["corpus_sha256"], "counts": report["counts"],
                "read_set": snapshot.read_set(), "errors": [], "execution_authorized": False}
    except Exception as error:
        return _failure(error)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "build-index", "check-index"))
    parser.add_argument("--corpus-root", type=Path, default=DEFAULT_CORPUS_ROOT)
    args = parser.parse_args(argv)
    try:
        result = (build_index(args.corpus_root) if args.command == "build-index" else
                  check_index(args.corpus_root) if args.command == "check-index" else inspect_corpus(args.corpus_root))
    except CaseMemoryError as error:
        result = _failure(error)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False))
    return 1 if result.get("status") == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
