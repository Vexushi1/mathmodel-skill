#!/usr/bin/env python3
"""Explicit, recoverable case provenance; references never authorize execution."""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from project_transaction import (
    JOURNAL_RELATIVE_PATH, STATE_RELATIVE_PATH, _guarded_path,
    commit_project_state, state_generation,
)
from runtime_assurance import ProjectStateSnapshot
from semantic_identity import (
    Q_HEADING_RE, _strip_yaml_fence, inspect_question_semantics, semantic_scope,
)
from validate_project_state import validate_state_payload

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS_ROOT = ROOT / "knowledge/case_memory"
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 8 * 1024 * 1024
MAX_INPUT_BYTES = 65536
MAX_NODES = 65536
MAX_DEPTH = 32
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
QUESTION_RE = re.compile(r"^Q[1-9][0-9]*$")
CONTEXT_FIELDS = ("classification", "capabilities", "depends_on", "problem_contract_status")
CURRENT_BINDINGS = (
    "corpus_sha256", "features_sha256", "authority_sha256", "taxonomy_sha256",
    "retriever_sha256", "filter_policy_sha256",
)
CASE_FIELDS = ("case_id", "case_version", "case_sha256", "source_id", "source_sha256")
SKILL_INPUTS = (
    "core/project_state.schema.yaml", "core/task_taxonomy.yaml",
    "core/state_transition_contract.yaml", "scripts/case_references.py",
    "scripts/project_transaction.py", "scripts/runtime_assurance.py",
    "scripts/semantic_identity.py", "scripts/validate_project_state.py",
    "scripts/safe_yaml.py",
)
NON_AUTHORIZATION = {
    "execution_authorized": False, "model_approval_granted": False,
    "project_condition_semantics": "not_assessed",
}


class CaseReferenceError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _lf(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _canonical(value: Any) -> bytes:
    remaining = [MAX_NODES]

    def normalize(item, depth=0):
        remaining[0] -= 1
        if remaining[0] < 0 or depth > MAX_DEPTH:
            raise CaseReferenceError("input_budget_exceeded")
        if isinstance(item, str):
            if len(item.encode("utf-8")) > 32768:
                raise CaseReferenceError("input_budget_exceeded")
            return _lf(item)
        if item is None or type(item) in (bool, int):
            return item
        if type(item) is float and math.isfinite(item):
            return item
        if isinstance(item, list):
            return [normalize(child, depth + 1) for child in item]
        if isinstance(item, dict) and all(isinstance(key, str) for key in item):
            return {key: normalize(child, depth + 1) for key, child in item.items()}
        raise CaseReferenceError("invalid_input")

    return json.dumps(normalize(value), sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def state_field_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def framework_anchor_sha256(anchor: str) -> str:
    return hashlib.sha256(_lf(anchor).encode("utf-8")).hexdigest()


def _read(path: Path, limit=MAX_FILE_BYTES) -> bytes:
    with path.open("rb") as handle:
        raw = handle.read(limit + 1)
    if len(raw) > limit:
        raise CaseReferenceError("input_budget_exceeded")
    return raw


_LOADED_SCRIPT_SHA256 = hashlib.sha256(_read(Path(__file__))).hexdigest()


class _StateLoader(yaml.SafeLoader):
    def __init__(self, stream):
        super().__init__(stream)
        self.depth = self.nodes = 0

    def compose_node(self, parent, index):
        if self.check_event(yaml.AliasEvent):
            raise CaseReferenceError("invalid_project_state")
        self.depth += 1
        self.nodes += 1
        try:
            if self.depth > MAX_DEPTH or self.nodes > MAX_NODES:
                raise CaseReferenceError("input_budget_exceeded")
            return super().compose_node(parent, index)
        finally:
            self.depth -= 1

    def construct_mapping(self, node, deep=False):
        keys = [self.construct_object(key, deep=deep) for key, _ in node.value]
        if any(not isinstance(key, str) for key in keys) or len(set(keys)) != len(keys):
            raise CaseReferenceError("invalid_project_state")
        return super().construct_mapping(node, deep=deep)


def _state(raw: bytes) -> dict:
    payload = yaml.load(raw.decode("utf-8"), Loader=_StateLoader)
    if not isinstance(payload, dict):
        raise CaseReferenceError("invalid_project_state")
    _canonical(payload)
    return payload


class _BoundedStateSnapshot(ProjectStateSnapshot):
    """Reuse snapshot payload/identity while bounding every State re-observation."""

    def assert_current(self, project_root=None):
        if project_root is not None and Path(project_root).expanduser().resolve() != self.root:
            raise CaseReferenceError("snapshot_project_mismatch")
        journal = self.root / JOURNAL_RELATIVE_PATH
        if journal.exists() or journal.is_symlink():
            raise CaseReferenceError("recovery_required")
        raw = _read(_guarded_path(self.root, STATE_RELATIVE_PATH))
        if journal.exists() or journal.is_symlink():
            raise CaseReferenceError("recovery_required")
        if raw != self.raw:
            raise CaseReferenceError("project_state_changed")


def _assert_reads(root, expected):
    total = 0
    for relative, digest in expected.items():
        raw = _read(_guarded_path(root, relative))
        total += len(raw)
        if total > MAX_TOTAL_BYTES:
            raise CaseReferenceError("input_budget_exceeded")
        if hashlib.sha256(raw).hexdigest() != digest:
            raise CaseReferenceError("read_set_changed")


def _problem_contract_body(scope: str, marker: str) -> str:
    body = scope.split(marker, 1)[1]
    boundary = re.search(r"(?m)^\s*(?:\*\*[^*\n]+\*\*\s*$|#{1,6}\s|<!--\s*HSK_SEMANTIC_IDENTITY_)", body)
    if boundary:
        body = body[:boundary.start()]
    body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL).strip()
    if not body or re.search(r"__[^\s]+__|填写|待填写", body):
        raise CaseReferenceError("frozen_problem_contract_content_required")
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    substantive = False
    for index, line in enumerate(lines):
        if line.startswith("|"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if all(not cell or re.fullmatch(r"[-: ]+", cell) for cell in cells):
                continue
            if index + 1 < len(lines) and re.fullmatch(r"[|\s:-]+", lines[index + 1]):
                continue  # A Markdown table header is not frozen contract content.
            substantive |= any(cell and cell not in {"待定", "待确认", "pending"} for cell in cells[1:])
        else:
            substantive |= bool(re.search(r"[\w\u4e00-\u9fff]", line))
    if not substantive:
        raise CaseReferenceError("frozen_problem_contract_content_required")
    return body


@dataclass
class _Context:
    root: Path
    question: str
    snapshot: ProjectStateSnapshot
    state: dict
    scope: str
    context_sha256: str
    project_reads: dict
    skill_reads: dict
    schema: dict
    bytes_read: int

    def assert_current(self):
        self.snapshot.assert_current()
        _assert_reads(self.root, self.project_reads)
        _assert_reads(ROOT, self.skill_reads)

    def evidence(self, references: list):
        for reference in references:
            kind = reference["kind"]
            if kind == "state_field":
                prefix = f"/subproblems/{self.question}/"
                pointer = reference["pointer"]
                field = pointer.removeprefix(prefix)
                entry = self.state["subproblems"][self.question]
                if not pointer.startswith(prefix) or field not in CONTEXT_FIELDS or field not in entry:
                    raise CaseReferenceError("evidence_outside_question")
                actual = state_field_sha256(entry[field])
            elif kind == "framework_anchor":
                anchor = _lf(reference["anchor"])
                if not anchor.strip() or self.scope.count(anchor) != 1:
                    raise CaseReferenceError("evidence_anchor_not_unique")
                actual = framework_anchor_sha256(anchor)
            else:
                relative = reference["path"]
                if relative in (STATE_RELATIVE_PATH, JOURNAL_RELATIVE_PATH,
                                "state/.project_transaction.lock"):
                    raise CaseReferenceError("evidence_control_file_forbidden")
                path = _guarded_path(self.root, relative)
                raw = _read(path)
                self.bytes_read += len(raw)
                if self.bytes_read > MAX_TOTAL_BYTES:
                    raise CaseReferenceError("input_budget_exceeded")
                actual = hashlib.sha256(raw).hexdigest()
                self.project_reads[relative] = actual
            if actual != reference["sha256"]:
                raise CaseReferenceError("evidence_hash_mismatch")


def _capture(root, question: str) -> _Context:
    if not isinstance(question, str) or not QUESTION_RE.fullmatch(question):
        raise CaseReferenceError("invalid_question")
    root = Path(root).expanduser().resolve()
    journal = root / JOURNAL_RELATIVE_PATH
    if journal.exists() or journal.is_symlink():
        raise CaseReferenceError("recovery_required")
    raw = _read(_guarded_path(root, STATE_RELATIVE_PATH))
    state = _state(raw)
    snapshot = _BoundedStateSnapshot(root, raw)
    snapshot.assert_current()
    skill_reads = {name: hashlib.sha256(_read(_guarded_path(ROOT, name))).hexdigest()
                   for name in SKILL_INPUTS}
    if skill_reads["scripts/case_references.py"] != _LOADED_SCRIPT_SHA256:
        raise CaseReferenceError("source_changed")
    schema = yaml.safe_load(_read(ROOT / "core/project_state.schema.yaml"))
    if schema.get("version") != "8.15.0":
        raise CaseReferenceError("unsupported_state_schema")
    if any(Draft202012Validator(schema).iter_errors(state)):
        raise CaseReferenceError("invalid_project_state")
    entry = state.get("subproblems", {}).get(question)
    decision = state.get("decisions", {}).get(question)
    if not isinstance(entry, dict) or not isinstance(decision, dict):
        raise CaseReferenceError("existing_question_decision_required")
    classification, capabilities = entry.get("classification"), entry.get("capabilities")
    if not isinstance(classification, dict) or not isinstance(capabilities, dict):
        raise CaseReferenceError("modern_classification_required")
    if any(type(value) is not bool for value in capabilities.values()):
        raise CaseReferenceError("strict_capabilities_required")
    alias = classification.get("capabilities")
    if alias is not None and _canonical(alias) != _canonical(capabilities):
        raise CaseReferenceError("capability_alias_mismatch")
    if entry.get("problem_contract_status") != "frozen":
        raise CaseReferenceError("frozen_problem_contract_required")
    relative = state.get("paper_framework", {}).get("path")
    if not isinstance(relative, str) or not relative:
        raise CaseReferenceError("registered_framework_required")
    framework_raw = _read(_guarded_path(root, relative))
    text = _lf(framework_raw.decode("utf-8"))
    headings = list(Q_HEADING_RE.finditer(text))
    selected = [index for index, heading in enumerate(headings) if heading.group(1) == question]
    if len(selected) != 1:
        raise CaseReferenceError("framework_question_not_unique")
    index = selected[0]
    heading = headings[index]
    if _lf(entry.get("framework_section", "")) != heading.group(0):
        raise CaseReferenceError("framework_question_binding_mismatch")
    end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
    section = text[heading.start():end]
    scope = semantic_scope(section)
    marker = "**题意口径（Problem Contract）**"
    if not scope or section.count("#### 当前模型口径") != 1 or scope.count(marker) != 1:
        raise CaseReferenceError("frozen_problem_contract_content_required")
    if len(scope.encode("utf-8")) > 32768:
        raise CaseReferenceError("input_budget_exceeded")
    _problem_contract_body(scope, marker)
    if "HSK_SEMANTIC_IDENTITY_" in scope:
        begin = f"<!-- HSK_SEMANTIC_IDENTITY_BEGIN {question} -->"
        end_marker = f"<!-- HSK_SEMANTIC_IDENTITY_END {question} -->"
        if scope.count(begin) != 1 or scope.count(end_marker) != 1:
            raise CaseReferenceError("invalid_semantic_identity")
        start, stop = scope.find(begin) + len(begin), scope.find(end_marker)
        if stop < start:
            raise CaseReferenceError("invalid_semantic_identity")
        # Preflight bounds, aliases and duplicate keys before the existing identity parser.
        _state(_strip_yaml_fence(scope[start:stop]).encode("utf-8"))
    semantics = inspect_question_semantics(section, question)
    for name in ("semantic_identity_hash", "semantic_text_hash", "semantic_identity_schema_version"):
        declared = entry.get(name)
        if declared and declared != semantics[name]:
            raise CaseReferenceError("current_semantic_identity_mismatch")
    if validate_state_payload(state, project_root=root, framework_text_override=text):
        raise CaseReferenceError("invalid_project_state")
    project_reads = {STATE_RELATIVE_PATH: hashlib.sha256(raw).hexdigest(),
                     relative: hashlib.sha256(framework_raw).hexdigest()}
    context_sha = state_field_sha256({
        "question": question, "state_fields": {name: entry.get(name) for name in CONTEXT_FIELDS},
        "framework_path": relative, "framework_heading": heading.group(0),
        "framework_scope": scope,
    })
    context = _Context(root, question, snapshot, state, scope, context_sha,
                       project_reads, skill_reads, schema, len(raw) + len(framework_raw))
    context.assert_current()
    return context


def _validate_record(record, schema):
    shape = {"$schema": schema["$schema"], "$defs": schema["$defs"],
             "$ref": "#/$defs/case_reference_record"}
    if len(_canonical(record)) > MAX_INPUT_BYTES or any(Draft202012Validator(shape).iter_errors(record)):
        raise CaseReferenceError("invalid_reference")


def _prepare(root, question, query, selection, corpus_root):
    # Query shape belongs solely to the independent retrieval Authority.
    from case_memory_retrieve import capture_query

    if len(_canonical(query)) > MAX_INPUT_BYTES or len(_canonical(selection)) > MAX_INPUT_BYTES:
        raise CaseReferenceError("input_budget_exceeded")
    fields = {"case_id", "disposition", "adopted_parts", "rejected_parts", "current_evidence", "reason"}
    if not isinstance(selection, dict) or set(selection) != fields:
        raise CaseReferenceError("invalid_selection")
    context = _capture(root, question)
    retrieval = capture_query(query, corpus_root=corpus_root)
    if retrieval.report.get("status") != "matches":
        raise CaseReferenceError("current_retrieval_match_required")
    match = next((item for item in retrieval.report["matches"]
                  if item.get("case_id") == selection["case_id"]), None)
    if match is None:
        raise CaseReferenceError("selected_case_not_current_match")
    entry = context.state["subproblems"][question]
    if (query["objective"] != entry["classification"]["objective"]
            or set(query["structures"]) != set(entry["classification"]["structures"])
            or set(query["capabilities"]) != {key for key, value in entry["capabilities"].items() if value is True}):
        raise CaseReferenceError("query_project_classification_mismatch")
    case = retrieval.case(selection["case_id"])
    record = {name: case[name] for name in CASE_FIELDS}
    record.update(retrieval.bindings)
    record["project_context_sha256"] = context.context_sha256
    record.update({name: deepcopy(selection[name]) for name in fields if name != "case_id"})
    _validate_record(record, context.schema)
    context.evidence(record["current_evidence"])
    decision = context.state["decisions"][question]
    records = decision.get("case_references", {}).get("records", [])
    unchanged = any(_canonical(existing) == _canonical(record) for existing in records)
    candidate = deepcopy(context.state)
    if not unchanged:
        if len(records) >= 64:
            raise CaseReferenceError("reference_budget_exceeded")
        candidate["decisions"][question]["case_references"] = {
            "protocol_version": "1.0.0", "records": [*deepcopy(records), record],
        }
    context.assert_current()
    retrieval.assert_current()
    report = {"status": "unchanged" if unchanged else "preview", "record": record,
              "state_snapshot": context.snapshot.describe(),
              "retrieval_bindings": deepcopy(retrieval.bindings),
              "project_context_sha256": context.context_sha256, "errors": [],
              "compatibility": match.get("compatibility"), **NON_AUTHORIZATION}
    return context, retrieval, candidate, report


def _blocked(root, error):
    code = getattr(error, "code", "reference_operation_failed")
    # Codes are fixed implementation identifiers; never expose input, paths or exception text.
    if not isinstance(code, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,80}", code):
        code = "reference_operation_failed"
    journal = Path(root).expanduser().resolve() / JOURNAL_RELATIVE_PATH
    return {"status": "blocked", "errors": [code],
            "recovery_required": journal.exists() or journal.is_symlink(), **NON_AUTHORIZATION}


def preview_reference(root, question, query, selection, *, corpus_root=DEFAULT_CORPUS_ROOT):
    try:
        return _prepare(root, question, query, selection, corpus_root)[3]
    except (ValueError, TypeError, KeyError, OSError, RuntimeError, ImportError, yaml.YAMLError, RecursionError) as error:
        return _blocked(root, error)


def record_reference(root, question, query, selection, *, expected_generation,
                     expected_state_sha256, expected_retrieval_corpus_sha256,
                     write=False, failure_hook=None, corpus_root=DEFAULT_CORPUS_ROOT):
    try:
        context, retrieval, candidate, report = _prepare(root, question, query, selection, corpus_root)
        if type(expected_generation) is not int or expected_generation != state_generation(context.state):
            raise CaseReferenceError("generation_conflict")
        for value in (expected_state_sha256, expected_retrieval_corpus_sha256):
            if not isinstance(value, str) or not HASH_RE.fullmatch(value):
                raise CaseReferenceError("invalid_expected_hash")
        if expected_state_sha256 != context.snapshot.describe()["sha256"]:
            raise CaseReferenceError("state_snapshot_conflict")
        if expected_retrieval_corpus_sha256 != retrieval.bindings["corpus_sha256"]:
            raise CaseReferenceError("retrieval_snapshot_conflict")
        if type(write) is not bool:
            raise CaseReferenceError("invalid_write_flag")
        if not write or report["status"] == "unchanged":
            return report
        expected = deepcopy(candidate)
        expected["project"]["state_generation"] = expected_generation + 1
        expected_encoded = _canonical(expected)
        preserved = deepcopy(context.state)
        preserved["project"].pop("state_generation", None)
        preserved["decisions"][question].pop("case_references", None)
        preserved_encoded = _canonical(preserved)

        def guard():
            context.assert_current()
            retrieval.assert_current()

        def validate(staged):
            guard()
            actual = _state(_read(staged[STATE_RELATIVE_PATH]))
            if _canonical(actual) != expected_encoded:
                raise CaseReferenceError("candidate_delta_forbidden")
            unchanged_fields = deepcopy(actual)
            unchanged_fields["project"].pop("state_generation", None)
            unchanged_fields["decisions"][question].pop("case_references", None)
            if _canonical(unchanged_fields) != preserved_encoded:
                raise CaseReferenceError("candidate_delta_forbidden")
            if validate_state_payload(actual, project_root=context.root):
                raise CaseReferenceError("invalid_project_state")
            guard()

        def hook(point):
            if failure_hook is not None:
                failure_hook(point)
            if point in ("after_validation", "after_generation_check"):
                guard()

        transaction = commit_project_state(
            context.root, candidate, expected_generation=expected_generation,
            expected_file_hashes=context.project_reads, validators=(validate,), failure_hook=hook,
        )
        return {**report, "status": "committed", "transaction": transaction}
    except (ValueError, TypeError, KeyError, OSError, RuntimeError, ImportError, yaml.YAMLError, RecursionError) as error:
        return _blocked(root, error)


def inspect_references(root, *, corpus_root=DEFAULT_CORPUS_ROOT):
    try:
        from case_memory_retrieve import capture_current

        root = Path(root).expanduser().resolve()
        snapshot = _BoundedStateSnapshot(root, _read(_guarded_path(root, STATE_RELATIVE_PATH)))
        state = _state(snapshot.raw)
        snapshot.assert_current()
        schema_raw = _read(_guarded_path(ROOT, "core/project_state.schema.yaml"))
        schema = yaml.safe_load(schema_raw)
        if schema.get("version") != "8.15.0" or any(Draft202012Validator(schema).iter_errors(state)):
            raise CaseReferenceError("invalid_project_state")
        retrieval = capture_current(corpus_root=corpus_root)
        records = []
        contexts = []
        for question, decision in state.get("decisions", {}).items():
            if not isinstance(decision, dict) or "case_references" not in decision:
                continue
            context = None
            try:
                context = _capture(root, question)
                if context.snapshot.raw != snapshot.raw:
                    raise CaseReferenceError("state_snapshot_conflict")
                contexts.append(context)
            except (ValueError, TypeError, KeyError, OSError, RuntimeError, yaml.YAMLError) as error:
                context_error = getattr(error, "code", "project_context_unavailable")
            container = decision["case_references"]
            if not isinstance(container, dict) or container.get("protocol_version") != "1.0.0" or not isinstance(container.get("records"), list):
                raise CaseReferenceError("invalid_reference")
            for record in container["records"]:
                _validate_record(record, schema)
                reasons = []
                if context is None:
                    reasons.append(context_error)
                else:
                    _validate_record(record, context.schema)
                    if record["project_context_sha256"] != context.context_sha256:
                        reasons.append("project_context_changed")
                    try:
                        context.evidence(record["current_evidence"])
                    except (ValueError, TypeError, KeyError, OSError, RuntimeError) as error:
                        reasons.append(getattr(error, "code", "project_evidence_unavailable"))
                if retrieval.report.get("status") != "current":
                    reasons.append("retrieval_unavailable")
                else:
                    try:
                        case = retrieval.case(record["case_id"])
                        if any(record[name] != case[name] for name in CASE_FIELDS):
                            reasons.append("case_or_source_changed")
                    except (ValueError, KeyError, RuntimeError):
                        reasons.append("case_unavailable")
                    reasons.extend(name.removesuffix("_sha256") + "_changed"
                                   for name in CURRENT_BINDINGS
                                   if record[name] != retrieval.bindings[name])
                records.append({"question": question, "case_id": record["case_id"],
                                "status": "needs_review" if reasons else "current",
                                "reasons": sorted(set(reasons)),
                                "ranking_not_recomputed": True, "original_query_not_available": True})
        snapshot.assert_current()
        if _read(_guarded_path(ROOT, "core/project_state.schema.yaml")) != schema_raw:
            raise CaseReferenceError("state_schema_changed")
        for context in contexts:
            context.assert_current()
        retrieval.assert_current()
        return {"status": "inspected", "records": records, "errors": [],
                "ranking_not_recomputed": True, "original_query_not_available": True,
                "numerical_acceptance_revoked": False, **NON_AUTHORIZATION}
    except (ValueError, TypeError, KeyError, OSError, RuntimeError, ImportError, yaml.YAMLError, RecursionError) as error:
        return {**_blocked(root, error), "ranking_not_recomputed": True,
                "original_query_not_available": True, "numerical_acceptance_revoked": False}


def _json_file(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise CaseReferenceError("invalid_input")
            result[key] = value
        return result

    value = json.loads(_read(Path(path), MAX_INPUT_BYTES).decode("utf-8"), object_pairs_hook=pairs,
                       parse_constant=lambda _: (_ for _ in ()).throw(CaseReferenceError("invalid_input")))
    _canonical(value)
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("preview", "record", "inspect"))
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--corpus-root", type=Path, default=DEFAULT_CORPUS_ROOT)
    parser.add_argument("--question")
    parser.add_argument("--query", type=Path)
    parser.add_argument("--selection", type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--expected-generation", type=int)
    parser.add_argument("--expected-state-sha256")
    parser.add_argument("--expected-retrieval-corpus-sha256")
    args = parser.parse_args(argv)
    try:
        if args.operation == "inspect":
            if args.write:
                raise CaseReferenceError("invalid_write_flag")
            report = inspect_references(args.project_root, corpus_root=args.corpus_root)
        else:
            if args.question is None or args.query is None or args.selection is None:
                raise CaseReferenceError("query_selection_question_required")
            inputs = (args.project_root, args.question, _json_file(args.query), _json_file(args.selection))
            if args.operation == "preview":
                if args.write:
                    raise CaseReferenceError("invalid_write_flag")
                report = preview_reference(*inputs, corpus_root=args.corpus_root)
            else:
                report = record_reference(*inputs, corpus_root=args.corpus_root, write=args.write,
                    expected_generation=args.expected_generation,
                    expected_state_sha256=args.expected_state_sha256,
                    expected_retrieval_corpus_sha256=args.expected_retrieval_corpus_sha256)
    except (ValueError, TypeError, OSError, RuntimeError, RecursionError) as error:
        report = _blocked(args.project_root, error)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return int(report["status"] == "blocked")


if __name__ == "__main__":
    raise SystemExit(main())
