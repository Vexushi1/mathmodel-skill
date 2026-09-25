#!/usr/bin/env python3
"""Opt-in, read-only structural conformance under the current model/source authorities.

Neither a declaration nor a successful structural inspection proves that an
arbitrary program implements a mathematical model. This command never grants
Model Approval, execution permission, numerical acceptance or independent review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

import yaml
from jsonschema import Draft202012Validator
from yaml.events import AliasEvent, CollectionStartEvent, CollectionEndEvent

import conformance_source as source
import execution_protocol
import runtime_assurance as runtime
import run_config_parser
import semantic_identity as semantic
import stage_code

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = "core/model_code_conformance_contract.yaml"
SCHEMA = "core/project_state.schema.yaml"
POLICY_SOURCES = (
    CONTRACT, SCHEMA, "core/model_approval_contract.yaml", "core/user_execution_contract.yaml",
    "core/output_contract.yaml", "scripts/model_code_conformance.py", "scripts/conformance_source.py",
    "scripts/semantic_identity.py", "scripts/runtime_assurance.py", "scripts/project_transaction.py",
    "scripts/stage_code.py", "scripts/run_config_parser.py", "scripts/python_source_checks.py",
    "scripts/matlab_code_checks.py", "scripts/execution_protocol.py",
)


class ConformanceError(ValueError):
    """A bounded read could not establish current structural evidence."""


class UniqueLoader(yaml.SafeLoader):
    """Reject ambiguous keys; never construct arbitrary Python objects."""


def _unique_mapping(loader: UniqueLoader, node: yaml.MappingNode, deep: bool = False) -> dict:
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, (str, int, float, bool, type(None))):
            raise ConformanceError("unsupported YAML mapping key")
        if key in result:
            raise ConformanceError("duplicate YAML mapping key")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def _yaml(text: str, depth_limit: int) -> Any:
    depth = 0
    for event in yaml.parse(text):
        if isinstance(event, AliasEvent):
            raise ConformanceError("YAML aliases are outside the bounded declaration protocol")
        if isinstance(event, CollectionStartEvent):
            depth += 1
            if depth > depth_limit:
                raise ConformanceError("declaration nesting budget exceeded")
        elif isinstance(event, CollectionEndEvent):
            depth -= 1
    return yaml.load(text, Loader=UniqueLoader)


def _read(root: Path, relative: str, limit: int, read_set: dict[str, str]) -> bytes:
    path = stage_code._relative_path(root, relative)
    if not path.is_file() or path.stat().st_size > limit:
        raise ConformanceError(f"missing file or byte budget exceeded: {relative}")
    with path.open("rb") as handle:
        raw = handle.read(limit + 1)
    if len(raw) > limit:
        raise ConformanceError(f"byte budget exceeded: {relative}")
    digest = hashlib.sha256(raw).hexdigest()
    if relative in read_set and read_set[relative] != digest:
        raise ConformanceError(f"source changed while reading: {relative}")
    read_set[relative] = digest
    return raw


def _recheck(root: Path, observed: Mapping[str, str]) -> None:
    # Reuse the existing read-set observer, not a second transaction or writer.
    from project_transaction import _check_read_set
    _check_read_set(root, observed)


def _model_items(identity: dict, contract: dict) -> dict[tuple[str, str | None], Any]:
    result = {}
    for field in contract["coverage"]["stable_id_fields"]:
        for item in identity[field]:
            result[field, str(item["id"])] = item
    for field in contract["coverage"]["singleton_fields"]:
        result[field, None] = identity[field]
    for name, value in identity.get("extensions", {}).items():
        result["extensions", str(name)] = value
    if len(result) > contract["limits"]["model_items"]:
        raise ConformanceError("model object budget exceeded")
    return result


def _selector(ref: Mapping[str, Any]) -> tuple[str, str | None]:
    return ref["field"], ref.get("id")


def _model_snapshot(root: Path, question: str, contract: dict, read_set: dict) -> tuple[Any, dict, dict, dict]:
    limits = contract["limits"]
    raw = _read(root, "state/project_state.yaml", limits["state_bytes"], read_set)
    _yaml(raw.decode("utf-8"), limits["record_depth"])
    snapshot = runtime.ProjectStateSnapshot.capture(root)
    if snapshot.raw != raw:
        raise ConformanceError("project state changed during capture")
    state = snapshot.payload()
    entry = (state.get("subproblems") or {}).get(question)
    if not isinstance(entry, dict):
        raise ConformanceError("requested question is missing or malformed")
    text = _read(root, "模型论文框架.md", limits["framework_bytes"], read_set).decode("utf-8")
    headings = [match.group(1) for match in semantic.Q_HEADING_RE.finditer(text)]
    if len(headings) != len(set(headings)):
        raise ConformanceError("ambiguous duplicate question scopes in current framework")
    section = semantic.question_sections(text).get(question)
    if section is None:
        raise ConformanceError("current framework has no requested question scope")
    begin, end = f"<!-- HSK_SEMANTIC_IDENTITY_BEGIN {question} -->", f"<!-- HSK_SEMANTIC_IDENTITY_END {question} -->"
    if section.count(begin) == 1 and section.count(end) == 1:
        block = section.split(begin, 1)[1].split(end, 1)[0].strip()
        _yaml(semantic._strip_yaml_fence(block), limits["record_depth"])
    inspection = semantic.inspect_question_semantics(section, question)
    lock = runtime._semantic_lock_evidence(question, entry, current_semantics=inspection, framework_error=None)
    if lock["status"] != "verified":
        raise ConformanceError("current model lock is not verified: " + lock["reason"])
    return snapshot, state, entry, inspection


def _source_snapshot(root: Path, question: str, stage: str, state: dict, entry: dict,
                     contract: dict, read_set: dict) -> tuple[dict, dict, dict, list, list]:
    limits = contract["limits"]
    backend = stage_code.current_project_backend(state, required=True)
    code = stage_code.resolve_stage_code(root, question, stage, entry=entry, project_backend=backend)
    if code is None:
        raise ConformanceError("selected stage has no source")
    relative = code.path.relative_to(root).as_posix()
    entry_raw = _read(root, relative, limits["source_file_bytes"], read_set)
    _, config = run_config_parser.parse_embedded_config(
        entry_raw.decode("utf-8-sig"), messages=run_config_parser.DELIVERY_MESSAGES, backend=backend)
    if (config.get("solver_backend") != backend or config.get("stage") != stage
            or config.get("problem_name") != code.problem_name
            or not execution_protocol.is_source_receipt(config.get("run_receipt_protocol_version"))):
        raise ConformanceError("stage/source/config backend, question or protocol mismatch")
    if execution_protocol.auxiliary_config_issues(config):
        raise ConformanceError("incomplete auxiliary input protocol in source declaration")
    dependencies = config.get("code_dependencies", [])
    if not isinstance(dependencies, list) or len(dependencies) + 1 > limits["source_files"]:
        raise ConformanceError("source dependency count is invalid or exceeds budget")
    paths = [relative]
    for dependency in dependencies:
        if not isinstance(dependency, dict) or set(dependency) != {"path", "sha256"}:
            raise ConformanceError("source dependency must contain exactly path and sha256")
        paths.append(dependency["path"])
    raw_sources, total = {}, 0
    for path in paths:
        raw = _read(root, path, limits["source_file_bytes"], read_set)
        total += len(raw)
        if total > limits["total_source_bytes"]:
            raise ConformanceError("total source byte budget exceeded")
        raw_sources[path] = raw
    fingerprint = stage_code.stage_code_fingerprint(root, code.path, dependencies)
    if any(read_set[item["path"]] != item["sha256"] for item in fingerprint["files"]):
        raise ConformanceError("source bytes changed during bundle binding")
    symbols, candidates, limitations = {}, [], []
    for path, raw in raw_sources.items():
        try:
            rows, reverse, unknown = source.inspect_source(path, raw.decode("utf-8-sig"), contract)
            symbols[path] = rows
            candidates.extend(reverse)
            limitations.extend(f"{path}: {value}" for value in unknown)
        except (ValueError, SyntaxError, RecursionError) as exc:
            raise ConformanceError(f"{path}: unsupported or invalid source: {type(exc).__name__}") from None
    if len(candidates) > limits["reverse_operations"]:
        raise ConformanceError("reverse candidate budget exceeded")
    if len({item["operation_id"] for item in candidates}) != len(candidates):
        raise ConformanceError("ambiguous reverse candidate identity")
    limitations.extend(stage_code.dependency_reference_issues(root, code.path, config))
    actual = {"solver_backend": backend, "entrypoint": relative, "source_bundle_sha256": fingerprint["bundle_sha256"]}
    return actual, fingerprint, symbols, candidates, list(dict.fromkeys(limitations))


def _mapping_issues(record: dict, items: dict, symbols: dict, candidates: list, backend: str,
                    contract: dict) -> tuple[list[str], list[str], list[dict]]:
    errors, review, checks, seen, coverage = [], [], [], set(), set()
    for mapping in record["mappings"]:
        mid, selector = mapping["id"], _selector(mapping["model_ref"])
        if mid in seen:
            errors.append(f"duplicate mapping id: {mid}")
        seen.add(mid)
        if selector not in items:
            errors.append(f"{mid}: model selector is not in current approved SIB")
            continue
        coverage.add(selector)
        if not mapping["rationale"].strip():
            errors.append(f"{mid}: empty rationale")
        if mapping["relation"] == "non_executable":
            review.append(f"{mid}: non-executable disposition needs mathematical review")
        if mapping["relation"] in {"equivalent_transform", "approved_approximation", "numerical_choice"}:
            review.append(f"{mid}: transformation/approximation applicability is not proved by source structure")
        for anchor in mapping["anchors"]:
            matches = [row for row in symbols.get(anchor["path"], []) if row.name == anchor["symbol"]]
            if len(matches) != 1:
                errors.append(f"{mid}: source symbol is missing, outside bundle or ambiguous")
                continue
            actual = matches[0]
            if actual.summary()["sha256"] != anchor["sha256"].lower():
                errors.append(f"{mid}: source symbol digest differs")
                continue
            if anchor.get("check_expression"):
                item = items[selector]
                expression = (item.get("implementation_expression", {}).get(backend)
                              if isinstance(item, dict) and isinstance(item.get("implementation_expression", {}), dict) else None)
                if not isinstance(expression, str) or not expression.strip():
                    review.append(f"{mid}: no approved implementation expression for this language")
                    continue
                status, reason = source.compare_expression(actual, expression, backend, anchor, contract["limits"])
                checks.append({"mapping_id": mid, "status": status, "reason": reason})
                if status == "different":
                    # A mismatch is not a proof that a declared equivalent transform is wrong.
                    target = errors if mapping["relation"] == "direct" else review
                    target.append(f"{mid}: {reason}")
                elif status == "needs_review":
                    review.append(f"{mid}: {reason}")
    for field, identity in sorted(set(items) - coverage, key=lambda item: (item[0], str(item[1]))):
        errors.append(f"unmapped current model object: {field}" + (f"/{identity}" if identity else ""))
    observed = {row["operation_id"] for row in candidates}
    reviewed = set()
    for row in record["reverse_review"]:
        operation = row["operation_id"]
        if operation in reviewed or operation not in observed or _selector(row["model_ref"]) not in items or not row["rationale"].strip():
            errors.append("reverse declaration is duplicate, orphaned or has no current model/rationale")
        reviewed.add(operation)
    for operation in sorted(observed - reviewed):
        review.append(f"{operation}: unregistered lexical operation needs model-level adjudication")
    return errors, review, checks


def inspect_project(project_root: str | Path, question: str, stage: str, *, inventory: bool = False) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    policy_read_set: dict[str, str] = {}
    project_read_set: dict[str, str] = {}
    report: dict[str, Any] = {"protocol_version": "1.0.0", "question": question, "stage": stage,
        "status": "blocked", "errors": [], "review_required": [], "mathematical_equivalence": "not_established",
        "constraint_activation": "not_proved", "numerical_acceptance": "not_assessed", "native_execution": "not_run",
        "independent_review": "not_run", "execution_authorized": False, "declaration_role": "author_supplied_not_proof"}
    snapshot = None
    try:
        if not re.fullmatch(r"Q[1-9][0-9]*", question) or stage not in {"primary", "analysis"}:
            raise ConformanceError("question/stage is invalid")
        for path in POLICY_SOURCES:
            _read(ROOT, path, 8 * 1024 * 1024, policy_read_set)
        contract = yaml.safe_load((ROOT / CONTRACT).read_text(encoding="utf-8"))
        schema = yaml.safe_load((ROOT / SCHEMA).read_text(encoding="utf-8"))
        if contract.get("version") != "1.1.0":
            raise ConformanceError("unsupported conformance Authority version")
        snapshot, state, entry, model = _model_snapshot(root, question, contract, project_read_set)
        items = _model_items(model["identity"], contract)
        actual, fingerprint, symbols, candidates, limitations = _source_snapshot(root, question, stage, state, entry, contract, project_read_set)
        actual.update(semantic_revision=entry["semantic_revision"], semantic_identity_hash=model["semantic_identity_hash"])
        report.update(binding=actual, model_selectors=[{"field": f, **({"id": i} if i is not None else {})} for f, i in items],
                      source_symbols=[{"path": path, **symbol.summary()} for path, rows in symbols.items() for symbol in rows],
                      reverse_candidates=candidates, review_required=limitations, source_files=fingerprint["files"])
        declarations = entry.get("implementation_conformance")
        if "implementation_conformance" in entry:
            validator = Draft202012Validator({"$ref": "#/$defs/implementation_conformance", "$defs": schema["$defs"]})
            errors = list(validator.iter_errors(declarations))
            if errors:
                raise ConformanceError("malformed conformance declaration at " + ", ".join(
                    "/".join(str(value) for value in error.path) or "record" for error in errors[:12]))
        record = declarations.get(stage) if declarations is not None else None
        if record is None or inventory:
            report["status"] = "not_assessed"
            report["reason"] = "observed inventory is not a verified mapping" if inventory else "no conformance record for this stage"
        else:
            if not semantic.is_semantic_revision(record["semantic_revision"]):
                raise ConformanceError("record semantic_revision must be a true positive integer")
            if record["question"] != question or record["stage"] != stage:
                raise ConformanceError("record question or stage differs from selected source")
            for field, value in actual.items():
                recorded = record[field]
                if field.endswith("sha256") or field.endswith("_hash"):
                    recorded = recorded.lower()
                if recorded != value:
                    raise ConformanceError(f"record binding is stale or inconsistent: {field}")
            errors, review, checks = _mapping_issues(record, items, symbols, candidates, actual["solver_backend"], contract)
            report["errors"].extend(errors)
            report["review_required"].extend(review)
            report["expression_checks"] = checks
            report["status"] = "blocked" if errors else "needs_review" if report["review_required"] else "structure_verified"
    except (OSError, ValueError, TypeError, KeyError, AttributeError, SyntaxError, RecursionError, yaml.YAMLError) as exc:
        report["errors"].append(str(exc).replace(str(root), "<project>"))
        report["status"] = "blocked"
    finally:
        try:
            if snapshot is not None:
                snapshot.assert_current()
            _recheck(root, project_read_set)
            _recheck(ROOT, policy_read_set)
        except (OSError, ValueError, RuntimeError) as exc:
            report["errors"].append("read snapshot changed or became unavailable: " + str(exc).replace(str(root), "<project>"))
            report["status"] = "blocked"
    report["observed_sources"] = {"project": project_read_set, "skill": policy_read_set}
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root")
    parser.add_argument("--question", required=True)
    parser.add_argument("--stage", choices=("primary", "analysis"), required=True)
    parser.add_argument("--inventory", action="store_true", help="Only report observed selectors and symbols, without creating a mapping")
    args = parser.parse_args()
    report = inspect_project(args.project_root, args.question, args.stage, inventory=args.inventory)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return {"structure_verified": 0, "blocked": 1, "needs_review": 2, "not_assessed": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
