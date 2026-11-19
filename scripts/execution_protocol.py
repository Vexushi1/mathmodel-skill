"""Shared implementation of User Execution receipt-version and auxiliary-field rules.

No project I/O, qualification, state changes or numerical execution occur here.
The Authority remains core/user_execution_contract.yaml.
"""
from __future__ import annotations

import json
import re
from typing import Any, Mapping

PQS_RECEIPT_VERSION = "1.3.0"
PQS_PROTOCOL_VERSION = "1.1.0"
PQS_DIGEST_FIELD = "primary_quality_spec_sha256"
SOURCE_RECEIPT_VERSIONS = frozenset({"1.1.0", "1.2.0", PQS_RECEIPT_VERSION})
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
    if config.get("run_receipt_protocol_version") not in ("1.1.0", "1.2.0"):
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


def primary_quality_config_issues(config: Mapping[str, Any], *, required: bool = False) -> list[str]:
    """Enforce the primary-only, backward-incompatible receipt boundary when opted in."""
    receipt_version = config.get("run_receipt_protocol_version")
    quality_version = config.get("primary_quality_protocol_version")
    if (not required and receipt_version != PQS_RECEIPT_VERSION
            and quality_version != PQS_PROTOCOL_VERSION and PQS_DIGEST_FIELD not in config):
        if config.get("stage") == "primary":
            return ([] if quality_version in (None, "", "1.0.0") else
                    ["primary_quality_protocol_version必须为1.0.0"])
        return ([] if quality_version in (None, "") else
                ["primary_quality_protocol_version只允许出现在primary阶段运行配置"])
    issues = []
    if config.get("stage") != "primary" or receipt_version != PQS_RECEIPT_VERSION:
        issues.append("approved primary quality requires primary RUN_RECEIPT 1.3.0")
    if quality_version != PQS_PROTOCOL_VERSION:
        issues.append("approved primary quality requires primary_quality_protocol_version=1.1.0")
    digest = config.get(PQS_DIGEST_FIELD)
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
        issues.append(f"approved primary quality requires a valid {PQS_DIGEST_FIELD}")
    return issues


def primary_quality_receipt_issues(receipt: Mapping[str, Any], config: Mapping[str, Any], *,
                                   required: bool = False) -> list[str]:
    """Verify the selected PQS receipt echoes the delivered identity."""
    if (not required and config.get("run_receipt_protocol_version") != PQS_RECEIPT_VERSION
            and config.get("primary_quality_protocol_version") != PQS_PROTOCOL_VERSION
            and PQS_DIGEST_FIELD not in config
            and receipt.get("run_receipt_version") != PQS_RECEIPT_VERSION
            and receipt.get("primary_quality_protocol_version") != PQS_PROTOCOL_VERSION
            and PQS_DIGEST_FIELD not in receipt):
        return []
    issues = primary_quality_config_issues(config, required=True)
    if receipt.get("stage") != "primary" or receipt.get("run_receipt_version") != PQS_RECEIPT_VERSION:
        issues.append("approved primary quality must return primary RUN_RECEIPT 1.3.0")
    if receipt.get("primary_quality_protocol_version") != PQS_PROTOCOL_VERSION:
        issues.append("RUN_RECEIPT must echo primary_quality_protocol_version=1.1.0")
    paths = receipt.get("data_paths")
    if isinstance(paths, str):
        try:
            paths = json.loads(paths)
        except json.JSONDecodeError:
            paths = None
    if not isinstance(paths, list) or paths != config.get("data_paths"):
        issues.append("RUN_RECEIPT.data_paths differs from delivered approved primary inputs")
    if receipt.get("data_identity_mode") != config.get("data_identity_mode", "combined"):
        issues.append("RUN_RECEIPT.data_identity_mode differs from delivered approved primary inputs")
    expected = config.get(PQS_DIGEST_FIELD)
    returned = receipt.get(PQS_DIGEST_FIELD)
    if (not isinstance(expected, str) or not isinstance(returned, str)
            or expected.lower() != returned.lower()):
        issues.append(f"RUN_RECEIPT.{PQS_DIGEST_FIELD} differs from delivered approved PQS")
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
