"""Validate and hash the optional, preapproved primary quality specification."""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from decimal import Decimal, DecimalException
from pathlib import Path
from typing import Any

import safe_yaml

SPECIFICATION_KEY = "primary_quality_specification"
SPECIFICATION_VERSION = "1.0.0"
CONTRACT_PATH = Path(__file__).resolve().parents[1] / "core" / "numerical_verification_contract.yaml"
REQUIRED_ITEM_FIELDS = {"id", "metric", "relation", "threshold", "threshold_source", "evidence_sheet"}


class PrimaryQualitySpecificationError(ValueError):
    """The bound quality criteria are malformed or cannot be qualified."""


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PrimaryQualitySpecificationError(f"{label} must be non-empty text")
    return value.strip()


def numeric_threshold(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise PrimaryQualitySpecificationError(f"{label} must be a finite number")
    try:
        decimal = Decimal(str(value))
        number = float(decimal)
    except (DecimalException, OverflowError, ValueError) as exc:
        raise PrimaryQualitySpecificationError(f"{label} must be a finite number") from exc
    if not math.isfinite(number) or Decimal(str(number)) != decimal:
        raise PrimaryQualitySpecificationError(f"{label} must be a finite, exactly representable workbook number")
    return number if number else 0.0


def _normalize_item(
    item: Any, question: str, seen_ids: set[str], id_pattern: str,
    sources: set[str], relations: set[str],
) -> dict[str, Any]:
    if (not isinstance(item, Mapping) or not REQUIRED_ITEM_FIELDS <= set(item)
            or set(item) - (REQUIRED_ITEM_FIELDS | {"unit"})):
        raise PrimaryQualitySpecificationError("PQS item requires id, metric, relation, threshold, "
                                               "threshold_source, evidence_sheet, and unit when numeric")

    identifier = _text(item["id"], "PQS item id")
    if not identifier.startswith(f"PQ-{question}-") or not re.fullmatch(id_pattern, identifier):
        raise PrimaryQualitySpecificationError(f"PQS id {identifier!r} does not match {question}")
    if identifier in seen_ids:
        raise PrimaryQualitySpecificationError(f"duplicate PQS id {identifier}")
    seen_ids.add(identifier)
    relation = _text(item["relation"], f"{identifier} relation")
    if relation not in relations:
        raise PrimaryQualitySpecificationError(f"{identifier} has unsupported relation {relation!r}")
    source = _text(item["threshold_source"], f"{identifier} threshold_source")
    if source not in sources:
        raise PrimaryQualitySpecificationError(f"{identifier} has unsupported threshold_source {source!r}")
    normalized = {
        "id": identifier,
        "metric": _text(item["metric"], f"{identifier} metric"),
        "relation": relation,
        "threshold_source": source,
        "evidence_sheet": _text(item["evidence_sheet"], f"{identifier} evidence_sheet"),
    }
    if relation == "bool_true":
        unit = item.get("unit")
        if item["threshold"] is not True or (unit is not None and
                                            (not isinstance(unit, str) or unit.strip())):
            raise PrimaryQualitySpecificationError(f"{identifier} bool_true requires threshold true and no unit")
        normalized["threshold"] = True
    else:
        threshold = numeric_threshold(item["threshold"], f"{identifier} threshold")
        if relation == "abs<=" and threshold < 0:
            raise PrimaryQualitySpecificationError(f"{identifier} requires a nonnegative abs<= threshold")
        normalized["threshold"] = threshold
        normalized["unit"] = _text(item.get("unit"), f"{identifier} unit")
    return normalized


def normalize_specification(value: Any, question: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != {"version", "items"}:
        raise PrimaryQualitySpecificationError("PQS requires version and items")
    if value["version"] != SPECIFICATION_VERSION:
        raise PrimaryQualitySpecificationError(f"unsupported PQS version {value['version']!r}")
    if not isinstance(value["items"], list) or not value["items"]:
        raise PrimaryQualitySpecificationError("PQS requires at least one item")

    contract = safe_yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    rules = contract[SPECIFICATION_KEY]
    sources = set(rules["threshold_sources"])
    relations = set(contract["strict_v714_trace"]["allowed_relations"])
    seen_ids: set[str] = set()
    items = [_normalize_item(item, question, seen_ids, rules["id_pattern"], sources, relations)
             for item in value["items"]]
    return {"version": SPECIFICATION_VERSION, "items": sorted(items, key=lambda item: item["id"])}


def specification_sha256(normalized: Mapping[str, Any]) -> str:
    """Hash a normalized specification, excluding unrelated model or prose data."""
    payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256((payload + "\n").encode("utf-8")).hexdigest()
