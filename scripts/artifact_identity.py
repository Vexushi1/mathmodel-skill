#!/usr/bin/env python3
"""Canonical artifact-identity compatibility helpers for the staged v9 migration."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

LEGACY_PRIMARY_CODE_KEY = "model"
PRIMARY_CODE_KEY = "primary_code"
ANALYSIS_CODE_KEY = "analysis_code"


class ArtifactIdentityError(ValueError):
    """Raised when legacy and canonical artifact identities contradict each other."""


def _same_hash(left: Any, right: Any) -> bool:
    return str(left).strip().lower() == str(right).strip().lower()


def normalize_artifact_hashes(
    values: Mapping[str, Any] | None,
    *,
    legacy_primary_fallback: Any = None,
) -> dict[str, Any]:
    """Return canonical hashes, mapping legacy model -> primary_code only when safe.

    The legacy key is never returned. If both keys exist they must denote the same hash;
    otherwise migration is blocked rather than choosing one truth silently.
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
    """Map the v8 implementation layer name model -> primary_code for comparison."""
    return sorted({PRIMARY_CODE_KEY if str(item) == LEGACY_PRIMARY_CODE_KEY else str(item) for item in (values or [])})


def entry_alias_issues(entry: Mapping[str, Any], *, scope: str = "subproblem") -> list[str]:
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


def canonicalize_entry_hashes(entry: dict[str, Any]) -> None:
    """Mechanically migrate an entry in memory to canonical implementation keys."""
    current = normalize_artifact_hashes(
        entry.get("artifact_hashes"), legacy_primary_fallback=entry.get("model_hash")
    )
    validated = normalize_artifact_hashes(
        entry.get("validated_artifact_hashes"),
        legacy_primary_fallback=entry.get("validated_model_hash"),
    )
    if current or "artifact_hashes" in entry:
        entry["artifact_hashes"] = current
    if validated or "validated_artifact_hashes" in entry:
        entry["validated_artifact_hashes"] = validated
    if "stale_layers" in entry:
        entry["stale_layers"] = normalize_stale_layers(entry.get("stale_layers"))
