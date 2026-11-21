#!/usr/bin/env python3
"""Deterministic semantic-identity parsing and hashing for model framework sections.

This module is an implementation utility, not a rule Authority. The authoritative
behavior remains in the project-state/model-approval/runtime contracts that consume it.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from primary_quality_specification import (
    PrimaryQualitySpecificationError,
    SPECIFICATION_KEY,
    normalize_specification,
)

SEMANTIC_IDENTITY_SCHEMA_VERSION = "1.0.0"
Q_HEADING_RE = re.compile(r"^###[ \t]+(Q\d+)[:：].*$", re.MULTILINE)
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
QUESTION_RE = re.compile(r"^Q[1-9][0-9]*$")
PLACEHOLDER_RE = re.compile(r"__[^\s]+__")
PREPROCESSING_DECISIONS = {"not_needed", "question_local", "project_level"}
DEPENDENCY_KINDS = {"data", "parameter", "model", "result"}

REQUIRED_ROOT_FIELDS = {
    "schema_version",
    "question",
    "research_object",
    "data_scope",
    "variables",
    "parameters",
    "assumptions",
    "objective",
    "constraints",
    "preprocessing_decision",
    "algorithm_semantics",
    "dependencies",
}
ALLOWED_ROOT_FIELDS = REQUIRED_ROOT_FIELDS | {"extensions"}
SET_LIKE_ID_FIELDS = {"data_scope", "variables", "parameters", "assumptions", "constraints"}


class SemanticIdentityError(ValueError):
    """Raised when an embedded Semantic Identity Block is malformed or incomplete."""


def is_semantic_revision(value: Any) -> bool:
    """Implement the State Schema's positive-integer revision, excluding booleans."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def semantic_revision_issues(entry: Mapping[str, Any], *, required: tuple[str, ...] = ()) -> list[str]:
    """Validate declared revision endpoints before equality or ordering comparisons."""
    fields = ("semantic_revision", "approved_semantic_revision", "validated_semantic_revision")
    return [f"{field} must be a positive integer (not bool, float or string)"
            for field in fields if (field in entry or field in required)
            and not is_semantic_revision(entry.get(field))]


def sha256_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip() + "\n"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def question_sections(text: str) -> dict[str, str]:
    """Find unique real Qn scopes, preserving section bytes and ignoring fenced examples."""
    matches: list[tuple[str, int]] = []
    first_lines: dict[str, int] = {}
    fence_character: str | None = None
    fence_length = 0
    offset = 0
    for line_number, raw_line in enumerate(text.splitlines(keepends=True), 1):
        line = raw_line.rstrip("\r\n")
        fence = FENCE_RE.fullmatch(line)
        if fence_character is not None:
            if (fence and fence.group(1)[0] == fence_character
                    and len(fence.group(1)) >= fence_length and re.fullmatch(r"[ \t]*", fence.group(2))):
                fence_character = None
        elif fence and (fence.group(1)[0] != "`" or "`" not in fence.group(2)):
            fence_character = fence.group(1)[0]
            fence_length = len(fence.group(1))
        else:
            heading = Q_HEADING_RE.fullmatch(line)
            if heading:
                question = heading.group(1)
                if question in first_lines:
                    raise SemanticIdentityError(
                        f"{question}: duplicate question section headings at lines "
                        f"{first_lines[question]} and {line_number}"
                    )
                first_lines[question] = line_number
                matches.append((question, offset))
        offset += len(raw_line)
    sections: dict[str, str] = {}
    for index, (question, start) in enumerate(matches):
        end = matches[index + 1][1] if index + 1 < len(matches) else len(text)
        sections[question] = text[start:end]
    return sections


def semantic_scope(section: str) -> str | None:
    marker = "#### 当前模型口径"
    start = section.find(marker)
    if start < 0:
        return None
    end = section.find("#### 结果摘要", start + len(marker))
    if end < 0:
        end = len(section)
    return section[start:end].strip()


def _marker(question: str, edge: str) -> str:
    return f"<!-- HSK_SEMANTIC_IDENTITY_{edge} {question} -->"


def _strip_yaml_fence(block: str) -> str:
    stripped = block.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if not lines or lines[0].strip().lower() not in {"```yaml", "```yml"}:
        raise SemanticIdentityError("Semantic Identity Block fenced content must use ```yaml or ```yml")
    if len(lines) < 2 or lines[-1].strip() != "```":
        raise SemanticIdentityError("Semantic Identity Block YAML fence is not closed")
    return "\n".join(lines[1:-1]).strip()


class _SemanticIdentityLoader(yaml.SafeLoader):
    """Record duplicate YAML keys and aliases for the new bound PQS form."""

    def __init__(self, stream):
        super().__init__(stream)
        self.quality_declared = False
        self.duplicate_keys = False
        self.aliases = False

    def compose_node(self, parent, index):
        if self.check_event(yaml.AliasEvent):
            self.aliases = True
        return super().compose_node(parent, index)

    def construct_mapping(self, node, deep=False):
        mapping = super().construct_mapping(node, deep=deep)
        self.quality_declared = self.quality_declared or SPECIFICATION_KEY in mapping
        self.duplicate_keys = self.duplicate_keys or len(mapping) != len(node.value)
        return mapping


def extract_semantic_identity(section: str, question: str) -> dict[str, Any] | None:
    """Parse one embedded SIB. Return None only when no identity marker exists at all."""
    begin = _marker(question, "BEGIN")
    end = _marker(question, "END")
    has_any_marker = "HSK_SEMANTIC_IDENTITY_BEGIN" in section or "HSK_SEMANTIC_IDENTITY_END" in section
    if not has_any_marker:
        return None
    if section.count(begin) != 1 or section.count(end) != 1:
        raise SemanticIdentityError(
            f"{question}: Semantic Identity Block must contain exactly one matching BEGIN/END marker pair"
        )
    start = section.find(begin) + len(begin)
    stop = section.find(end, start)
    if stop < start:
        raise SemanticIdentityError(f"{question}: Semantic Identity Block END marker precedes BEGIN marker")
    raw = _strip_yaml_fence(section[start:stop])
    if not raw:
        raise SemanticIdentityError(f"{question}: Semantic Identity Block is empty")
    loader = _SemanticIdentityLoader(raw)
    try:
        payload = loader.get_single_data()
        if loader.quality_declared and (loader.duplicate_keys or loader.aliases):
            raise SemanticIdentityError(
                f"{question}: Semantic Identity Block with PQS requires unique YAML keys and no aliases"
            )
    except yaml.YAMLError as exc:
        raise SemanticIdentityError(f"{question}: Semantic Identity Block YAML is invalid: {exc}") from exc
    finally:
        loader.dispose()
    if not isinstance(payload, dict):
        raise SemanticIdentityError(f"{question}: Semantic Identity Block root must be a mapping")
    validate_semantic_identity(payload, expected_question=question)
    return payload


def _contains_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return bool(PLACEHOLDER_RE.search(value))
    if isinstance(value, Mapping):
        return any(_contains_placeholder(key) or _contains_placeholder(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_placeholder(item) for item in value)
    return False


def _validate_id_list(name: str, value: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{name} must be a list")
        return
    ids: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            errors.append(f"{name}[{index}] must be a mapping with an id")
            continue
        identity = str(item.get("id", "")).strip()
        if not identity:
            errors.append(f"{name}[{index}].id is required")
        else:
            ids.append(identity)
    duplicates = sorted({identity for identity in ids if ids.count(identity) > 1})
    if duplicates:
        errors.append(f"{name} contains duplicate ids: {duplicates}")


def _check_canonical_mapping_keys(value: Any, *, path: str = "identity") -> None:
    """Reject lossy key normalization without changing valid canonical representations."""
    if isinstance(value, Mapping):
        keys: dict[str, Any] = {}
        for key, item in value.items():
            normalized = str(key)
            if normalized in keys:
                raise SemanticIdentityError(
                    f"{path}: canonical mapping key collision between "
                    f"{keys[normalized]!r} and {key!r} after normalization to {normalized!r}"
                )
            keys[normalized] = key
            _check_canonical_mapping_keys(item, path=f"{path}[{normalized!r}]")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _check_canonical_mapping_keys(item, path=f"{path}[{index}]")


def primary_quality_specification(identity: Mapping[str, Any]) -> dict[str, Any] | None:
    extensions = identity.get("extensions")
    if not isinstance(extensions, Mapping) or SPECIFICATION_KEY not in extensions:
        return None
    try:
        return normalize_specification(extensions[SPECIFICATION_KEY], str(identity.get("question", "")).strip())
    except PrimaryQualitySpecificationError as exc:
        raise SemanticIdentityError(f"{identity.get('question', '<unknown>')}: {exc}") from exc


def validate_semantic_identity(identity: Mapping[str, Any], *, expected_question: str | None = None) -> None:
    _check_canonical_mapping_keys(identity)
    errors: list[str] = []
    fields = set(identity)
    missing = sorted(REQUIRED_ROOT_FIELDS - fields)
    unknown = sorted(fields - ALLOWED_ROOT_FIELDS, key=str)
    if missing:
        errors.append(f"missing required fields: {missing}")
    if unknown:
        errors.append(f"unknown root fields: {unknown}; use extensions for model-specific semantics")

    if str(identity.get("schema_version", "")).strip() != SEMANTIC_IDENTITY_SCHEMA_VERSION:
        errors.append(
            f"schema_version must be {SEMANTIC_IDENTITY_SCHEMA_VERSION}, got {identity.get('schema_version')!r}"
        )
    question = str(identity.get("question", "")).strip()
    if not QUESTION_RE.fullmatch(question):
        errors.append("question must match Q1, Q2, ...")
    if expected_question and question != expected_question:
        errors.append(f"question {question!r} does not match enclosing framework section {expected_question!r}")

    research_object = identity.get("research_object")
    if not isinstance(research_object, str) or not research_object.strip():
        errors.append("research_object must be a non-empty string")

    for name in SET_LIKE_ID_FIELDS:
        _validate_id_list(name, identity.get(name), errors)

    objective = identity.get("objective")
    if not isinstance(objective, Mapping) or not objective:
        errors.append("objective must be a non-empty mapping")
    algorithm = identity.get("algorithm_semantics")
    if not isinstance(algorithm, Mapping) or not algorithm:
        errors.append("algorithm_semantics must be a non-empty mapping")

    preprocessing = identity.get("preprocessing_decision")
    if preprocessing not in PREPROCESSING_DECISIONS:
        errors.append(f"preprocessing_decision must be one of {sorted(PREPROCESSING_DECISIONS)}")

    dependencies = identity.get("dependencies")
    if not isinstance(dependencies, list):
        errors.append("dependencies must be a list")
    else:
        seen: set[tuple[str, str, str]] = set()
        for index, item in enumerate(dependencies):
            if not isinstance(item, Mapping):
                errors.append(f"dependencies[{index}] must be a mapping")
                continue
            dep_question = str(item.get("question", "")).strip()
            kind = str(item.get("kind", "")).strip()
            selector = str(item.get("selector", "")).strip()
            if not QUESTION_RE.fullmatch(dep_question):
                errors.append(f"dependencies[{index}].question must match Q1, Q2, ...")
            if dep_question == question:
                errors.append(f"dependencies[{index}] cannot depend on the same question {question}")
            if kind not in DEPENDENCY_KINDS:
                errors.append(f"dependencies[{index}].kind must be one of {sorted(DEPENDENCY_KINDS)}")
            key = (dep_question, kind, selector)
            if key in seen:
                errors.append(f"dependencies[{index}] duplicates dependency {key}")
            seen.add(key)

    if "extensions" in identity and not isinstance(identity.get("extensions"), Mapping):
        errors.append("extensions must be a mapping when present")
    try:
        primary_quality_specification(identity)
    except SemanticIdentityError as exc:
        errors.append(str(exc))
    if _contains_placeholder(identity):
        errors.append("Semantic Identity Block still contains __PLACEHOLDER__ tokens")

    if errors:
        raise SemanticIdentityError("; ".join(errors))


def _canonical_scalar(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    return value


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonical_value(value[key]) for key in sorted(value, key=lambda item: str(item))}
    if isinstance(value, list):
        return [_canonical_value(item) for item in value]
    return _canonical_scalar(value)


def canonical_semantic_identity(identity: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deterministic representation; only declared set-like collections are reordered."""
    validate_semantic_identity(identity)
    canonical = _canonical_value(dict(identity))
    for name in SET_LIKE_ID_FIELDS:
        canonical[name] = sorted(
            canonical[name],
            key=lambda item: (str(item.get("id", "")), json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))),
        )
    canonical["dependencies"] = sorted(
        canonical["dependencies"],
        key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
    )
    specification = primary_quality_specification(identity)
    if specification is not None:
        canonical["extensions"][SPECIFICATION_KEY] = specification
    return canonical


def canonical_semantic_identity_text(identity: Mapping[str, Any]) -> str:
    canonical = canonical_semantic_identity(identity)
    return json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def semantic_identity_hash(identity: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_semantic_identity_text(identity).encode("utf-8")).hexdigest()


def inspect_question_semantics(section: str, question: str) -> dict[str, Any]:
    """Return current text provenance plus optional structured semantic identity evidence."""
    scope = semantic_scope(section)
    if scope is None:
        raise SemanticIdentityError(f"{question}: framework section has no #### 当前模型口径 semantic scope")
    text_hash = sha256_text(scope)
    identity = extract_semantic_identity(scope, question)
    if identity is None:
        return {
            "mode": "legacy_text_hash",
            "semantic_text_hash": text_hash,
            "semantic_identity_hash": None,
            "semantic_identity_schema_version": None,
            "identity": None,
        }
    return {
        "mode": "semantic_identity_v1",
        "semantic_text_hash": text_hash,
        "semantic_identity_hash": semantic_identity_hash(identity),
        "semantic_identity_schema_version": str(identity["schema_version"]),
        "identity": identity,
    }


def read_framework_semantic_evidence(
    framework_path: Path,
) -> tuple[dict[str, dict[str, Any]], str | None]:
    """Parse current per-question semantic evidence using the shared canonical implementation."""
    if not framework_path.is_file():
        return {}, "current model framework is missing"
    return framework_semantic_evidence(framework_path.read_text(encoding="utf-8"))


def framework_semantic_evidence(text: str) -> tuple[dict[str, dict[str, Any]], str | None]:
    """Inspect captured framework text without reading the file again."""
    rows: dict[str, dict[str, Any]] = {}
    try:
        sections = question_sections(text)
    except SemanticIdentityError as exc:
        return {}, f"current model framework is malformed: {exc}"
    for question, section in sections.items():
        try:
            rows[question] = inspect_question_semantics(section, question)
        except SemanticIdentityError as exc:
            rows[question] = {
                "mode": "malformed",
                "error": str(exc),
                "semantic_text_hash": None,
                "semantic_identity_hash": None,
                "semantic_identity_schema_version": None,
            }
    return rows, None


def validated_semantic_changes(entry: Mapping[str, Any], inspection: Mapping[str, Any]) -> tuple[bool, bool]:
    """Compare an established structured identity and its validated revision independently."""
    previous_hash = str(entry.get("validated_semantic_identity_hash", "")).strip()
    if inspection.get("mode") != "semantic_identity_v1" or not previous_hash:
        return False, False
    revision = entry.get("semantic_revision")
    previous_revision = entry.get("validated_semantic_revision")
    # An absent historical revision can be initialized. Once recorded, an invalid
    # endpoint (including True == 1 in Python) cannot verify a downstream approval.
    revision_changed = "validated_semantic_revision" in entry and (
        not is_semantic_revision(previous_revision) or not is_semantic_revision(revision)
        or revision != previous_revision
    )
    return previous_hash != inspection["semantic_identity_hash"], revision_changed


def past_approval_conflict(entry: Mapping[str, Any], inspection: Mapping[str, Any]) -> bool:
    """Detect a recorded approval that an older writer failed to retire before advancing its baseline."""
    if inspection.get("mode") != "semantic_identity_v1" or entry.get("human_model_approval_status") != "approved":
        return False
    identity = inspection["semantic_identity_hash"]
    revision = entry.get("semantic_revision")
    validated_revision = entry.get("validated_semantic_revision")
    if (identity != entry.get("semantic_identity_hash") or identity != entry.get("validated_semantic_identity_hash")
            or not is_semantic_revision(revision) or not is_semantic_revision(validated_revision)
            or revision != validated_revision):
        return False
    approved_hash = entry.get("approved_semantic_identity_hash")
    approved_revision = entry.get("approved_semantic_revision")
    if (not isinstance(approved_hash, str) or re.fullmatch(r"[0-9a-fA-F]{64}", approved_hash) is None
            or not is_semantic_revision(approved_revision)):
        return False
    return approved_hash != identity or approved_revision != revision


def dependency_alignment_issues(
    subproblems: Mapping[str, Any], inspections: Mapping[str, Mapping[str, Any]]
) -> dict[str, list[str]]:
    """Compare typed endpoints, retaining selectors in identity and historical string edges in State."""
    conflicts: dict[str, list[str]] = {}
    for question, entry in subproblems.items():
        if not isinstance(entry, Mapping):
            continue
        dependencies = entry.get("depends_on", [])
        if not isinstance(dependencies, list):
            conflicts[question] = [f"{question}: State depends_on must be a list"]
            continue
        inspection = inspections.get(question, {})
        if inspection.get("mode") != "semantic_identity_v1":
            continue
        expected = {(str(dep["question"]).strip(), str(dep["kind"]).strip())
                    for dep in inspection["identity"]["dependencies"]}
        typed: set[tuple[str, str]] = set()
        legacy: set[str] = set()
        issues: list[str] = []
        for index, dep in enumerate(dependencies):
            if isinstance(dep, str) and QUESTION_RE.fullmatch(dep):
                legacy.add(dep)
            elif isinstance(dep, Mapping):
                source = dep.get("question")
                kind = dep.get("kind")
                if (isinstance(source, str) and QUESTION_RE.fullmatch(source)
                        and isinstance(kind, str) and kind in DEPENDENCY_KINDS):
                    typed.add((source, kind))
                else:
                    issues.append(f"{question}: invalid State depends_on[{index}] ({source!r}, {kind!r})")
            else:
                issues.append(f"{question}: invalid State depends_on[{index}]")
        for source, kind in sorted(expected - typed):
            if source not in legacy:
                issues.append(f"{question}: SIB dependency {source}/{kind} missing from State depends_on")
        for source, kind in sorted(typed - expected):
            issues.append(f"{question}: State dependency {source}/{kind} missing from SIB dependencies")
        for source, kind in sorted(expected):
            # Missing execution inputs do not revoke approval for the mathematical model.
            if kind == "model" and source not in subproblems:
                issues.append(f"{question}: SIB dependency {source}/{kind} refers to an unknown State question")
        if issues:
            conflicts[question] = issues
    return conflicts
