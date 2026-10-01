"""Shared implementation of User Execution receipt-version and auxiliary-field rules.

No project I/O, qualification, state changes or numerical execution occur here.
The Authority remains core/user_execution_contract.yaml.
"""
from __future__ import annotations

import json
import re
from typing import Any, Mapping

SOURCE_RECEIPT_VERSIONS = frozenset({"1.1.0", "1.2.0"})
AUXILIARY_RECEIPT_VERSION = "1.2.0"
AUXILIARY_FIELDS = ("auxiliary_data_paths", "auxiliary_data_sha256")
COMPARISON_PROTOCOL_VERSION = "1.0.0"
COMPARISON_FIELDS = ("analysis_comparison_protocol_version", "analysis_comparison_plan_sha256")


def comparison_config_issues(config: Mapping[str, Any], *, required: bool = False) -> list[str]:
    """Validate the analysis-only overlay without changing receipt 1.1/1.2."""
    if not required and not any(field in config for field in COMPARISON_FIELDS):
        return []
    issues = []
    if config.get("stage") != "analysis":
        issues.append("analysis comparison fields only support the analysis stage")
    if config.get("run_receipt_protocol_version") not in SOURCE_RECEIPT_VERSIONS:
        issues.append("analysis comparison requires RUN_RECEIPT 1.1.0/1.2.0")
    if config.get(COMPARISON_FIELDS[0]) != COMPARISON_PROTOCOL_VERSION:
        issues.append("analysis_comparison_protocol_version must be 1.0.0")
    digest = config.get(COMPARISON_FIELDS[1])
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
        issues.append("analysis comparison requires a frozen analysis_comparison_plan_sha256")
    return issues


def comparison_receipt_issues(receipt: Mapping[str, Any], config: Mapping[str, Any], *,
                              required: bool = False) -> list[str]:
    active = required or any(field in value for value in (receipt, config) for field in COMPARISON_FIELDS)
    if not active:
        return []
    issues = comparison_config_issues(config, required=True)
    if receipt.get("stage") != "analysis" or not is_source_receipt(receipt.get("run_receipt_version")):
        issues.append("analysis comparison receipt must retain analysis RUN_RECEIPT 1.1.0/1.2.0")
    for field in COMPARISON_FIELDS:
        expected, actual = config.get(field), receipt.get(field)
        if not isinstance(expected, str) or not isinstance(actual, str) or (
                expected.lower() != actual.lower() if field.endswith("sha256") else expected != actual):
            issues.append(f"RUN_RECEIPT.{field} differs from delivered comparison plan")
    return issues


def is_source_receipt(value: Any) -> bool:
    return isinstance(value, str) and value in SOURCE_RECEIPT_VERSIONS


def auxiliary_config_issues(config: Mapping[str, Any]) -> list[str]:
    """Fail closed on partial or unsupported auxiliary-input declarations."""
    present = [field in config for field in AUXILIARY_FIELDS]
    modern_auxiliary = config.get("run_receipt_protocol_version") == AUXILIARY_RECEIPT_VERSION
    if not modern_auxiliary:
        return ["auxiliary inputs require RUN_RECEIPT 1.2.0"] if any(present) else []
    issues = []
    if config.get("stage") not in {"primary", "analysis"}:
        issues.append("RUN_RECEIPT 1.2.0 only supports primary/analysis")
    if config.get("data_identity_mode") != "preprocessing_workbook":
        issues.append("RUN_RECEIPT 1.2.0 requires preprocessing_workbook input mode")
    paths = config.get("auxiliary_data_paths")
    if not isinstance(paths, list) or not paths or any(not isinstance(path, str) or not path.strip() for path in paths):
        issues.append("RUN_RECEIPT 1.2.0 requires non-empty auxiliary_data_paths")
    digest = config.get("auxiliary_data_sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
        issues.append("RUN_RECEIPT 1.2.0 requires auxiliary_data_sha256")
    return issues


def declared_input_paths(config: Mapping[str, Any]) -> list[str]:
    """Inventory explicit source paths; malformed auxiliary fields never disappear."""
    issues = auxiliary_config_issues(config)
    values = []
    for field in ("data_paths", "auxiliary_data_paths"):
        paths = config.get(field, [])
        if not isinstance(paths, (list, tuple)) or any(not isinstance(path, str) for path in paths):
            issues.append(f"{field} must be a string path list")
        else:
            values.extend(paths)
    if issues:
        raise ValueError("; ".join(issues))
    return values


def auxiliary_receipt_issues(receipt: Mapping[str, Any], config: Mapping[str, Any]) -> list[str]:
    """Bind scalar workbook receipt fields to the delivered auxiliary input spec."""
    issues = auxiliary_config_issues(config)
    auxiliary = config.get("run_receipt_protocol_version") == AUXILIARY_RECEIPT_VERSION
    if not auxiliary:
        return issues + (["unexpected auxiliary receipt fields"] if any(field in receipt for field in AUXILIARY_FIELDS) else [])
    if receipt.get("data_identity_mode") != "preprocessing_workbook":
        issues.append("RUN_RECEIPT 1.2.0 requires preprocessing_workbook input mode")
    try:
        paths = json.loads(receipt.get("auxiliary_data_paths", ""))
    except (TypeError, ValueError):
        paths = None
    if (not isinstance(paths, list) or not paths or any(not isinstance(path, str) for path in paths)
            or paths != config.get("auxiliary_data_paths")):
        issues.append("RUN_RECEIPT.auxiliary_data_paths must match delivered paths as a JSON list")
    if str(receipt.get("auxiliary_data_sha256", "")).lower() != str(config.get("auxiliary_data_sha256", "")).lower():
        issues.append("RUN_RECEIPT.auxiliary_data_sha256 differs from delivered config")
    return issues
