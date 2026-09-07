#!/usr/bin/env python3
"""Canonical artifact-identity compatibility helpers for the staged v9 migration."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

LEGACY_PRIMARY_CODE_KEY = "model"
PRIMARY_CODE_KEY = "primary_code"
ANALYSIS_CODE_KEY = "analysis_code"


class ArtifactIdentityError(ValueError):
    """Raised when legacy and canonical artifact identities cannot be used safely."""


def _same_hash(left: Any, right: Any) -> bool:
    return str(left).strip().lower() == str(right).strip().lower()


def normalize_artifact_hashes(
    values: Mapping[str, Any] | None,
    *,
    legacy_primary_fallback: Any = None,
) -> dict[str, Any]:
    """Return canonical hashes for read-only audit/migration compatibility.

    The legacy key is never returned. If both keys exist they must denote the same hash;
    otherwise migration is blocked rather than choosing one truth silently. Active project
    writers must call ``canonicalize_entry_hashes`` and therefore cannot rely on these
    read-only aliases.
    """
    normalized = dict(values or {})
    legacy = normalized.get(LEGACY_PRIMARY_CODE_KEY)
    primary = normalized.get(PRIMARY_CODE_KEY)
    if legacy not in (None, "") and primary not in (None, "") and not _same_hash(legacy, primary):
        raise ArtifactIdentityError(
            "artifact_hashes.model conflicts with artifact_hashes.primary_code; "
            "legacy/new implementation identities must agree before migration"
        )
    if primary in (None, ""):
        if legacy not in (None, ""):
            normalized[PRIMARY_CODE_KEY] = legacy
        elif legacy_primary_fallback not in (None, ""):
            normalized[PRIMARY_CODE_KEY] = legacy_primary_fallback
    normalized.pop(LEGACY_PRIMARY_CODE_KEY, None)
    return normalized


def normalize_stale_layers(values: Any) -> list[str]:
    """Map the v8 implementation layer name model -> primary_code for read-only comparison."""
    return sorted({PRIMARY_CODE_KEY if str(item) == LEGACY_PRIMARY_CODE_KEY else str(item) for item in (values or [])})


def entry_alias_issues(entry: Mapping[str, Any], *, scope: str = "subproblem") -> list[str]:
    """Report contradictory legacy/canonical identities without treating aliases as current."""
    issues: list[str] = []
    for field, fallback in (
        ("artifact_hashes", entry.get("model_hash")),
        ("validated_artifact_hashes", entry.get("validated_model_hash")),
    ):
        try:
            normalize_artifact_hashes(entry.get(field), legacy_primary_fallback=fallback)
        except ArtifactIdentityError as exc:
            issues.append(f"{scope}.{field}: {exc}")
    return issues


def active_alias_issues(entry: Mapping[str, Any], *, scope: str = "subproblem") -> list[str]:
    """Return legacy implementation aliases that block an active project-state write."""
    issues = list(entry_alias_issues(entry, scope=scope))
    for field, canonical in (
        ("artifact_hashes", "artifact_hashes.primary_code"),
        ("validated_artifact_hashes", "validated_artifact_hashes.primary_code"),
    ):
        values = entry.get(field)
        if isinstance(values, Mapping) and values.get(LEGACY_PRIMARY_CODE_KEY) not in (None, ""):
            issues.append(
                f"{scope}.{field}.model is historical read-only compatibility; "
                f"migrate to {canonical} before active project writes"
            )
    for field, canonical in (
        ("model_hash", "artifact_hashes.primary_code"),
        ("validated_model_hash", "validated_artifact_hashes.primary_code"),
    ):
        if entry.get(field) not in (None, ""):
            issues.append(
                f"{scope}.{field} is historical read-only compatibility; "
                f"migrate to {canonical} before active project writes"
            )
    if LEGACY_PRIMARY_CODE_KEY in {str(item) for item in (entry.get("stale_layers", []) or [])}:
        issues.append(
            f"{scope}.stale_layers contains historical layer 'model'; "
            "migrate it to 'primary_code' before active project writes"
        )
    return list(dict.fromkeys(issues))


def canonicalize_entry_hashes(entry: dict[str, Any]) -> None:
    """Require canonical implementation identity before mutating active project state.

    Phase I I3a retires the old behavior that silently migrated artifact aliases inside
    active writers. Historical readers may still use ``normalize_artifact_hashes`` and
    ``normalize_stale_layers`` for audit/migration diagnostics, but any active write must
    begin from canonical ``primary_code`` state.
    """
    issues = active_alias_issues(entry)
    if issues:
        raise ArtifactIdentityError("active project write requires canonical artifact identity: " + "; ".join(issues))

    current = normalize_artifact_hashes(entry.get("artifact_hashes"))
    validated = normalize_artifact_hashes(entry.get("validated_artifact_hashes"))
    if current or "artifact_hashes" in entry:
        entry["artifact_hashes"] = current
    if validated or "validated_artifact_hashes" in entry:
        entry["validated_artifact_hashes"] = validated
    if "stale_layers" in entry:
        entry["stale_layers"] = normalize_stale_layers(entry.get("stale_layers"))
