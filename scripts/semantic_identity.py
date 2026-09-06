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
from typing import Any

import yaml

SEMANTIC_IDENTITY_SCHEMA_VERSION = "1.0.0"
Q_HEADING_RE = re.compile(r"^###\s+(Q\d+)[:：].*$", re.MULTILINE)
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


def sha256_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip() + "\n"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def question_sections(text: str) -> dict[str, str]:
    matches = list(Q_HEADING_RE.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[match.group(1)] = text[match.start():end]
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
    try:
        payload = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise SemanticIdentityError(f"{question}: Semantic Identity Block YAML is invalid: {exc}") from exc
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


def validate_semantic_identity(identity: Mapping[str, Any], *, expected_question: str | None = None) -> None:
    errors: list[str] = []
    fields = set(identity)
    missing = sorted(REQUIRED_ROOT_FIELDS - fields)
    unknown = sorted(fields - ALLOWED_ROOT_FIELDS)
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
