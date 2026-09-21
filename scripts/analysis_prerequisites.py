"""Read-only analysis eligibility under the existing user-execution contract."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

import artifact_identity as ARTIFACT_IDENTITY
import stage_code as STAGE_CODE


def _file_issues(root: Path, path: Any, expected: Any, label: str) -> list[str]:
    if not isinstance(path, str) or not path.strip():
        return [f"{label}缺少工作簿/代码路径"]
    candidate = (root / path).resolve()
    if not candidate.is_relative_to(root.resolve()):
        return [f"{label}路径越出项目目录"]
    if not candidate.is_file():
        return [f"{label}文件不存在"]
    if not expected or hashlib.sha256(candidate.read_bytes()).hexdigest() != str(expected).lower():
        return [f"{label}缺少有效验收哈希或当前文件哈希不一致"]
    return []


def _hashes(entry: Mapping[str, Any]) -> tuple[dict, dict]:
    current = ARTIFACT_IDENTITY.normalize_artifact_hashes(
        entry.get("artifact_hashes"), legacy_primary_fallback=entry.get("model_hash"))
    validated = ARTIFACT_IDENTITY.normalize_artifact_hashes(
        entry.get("validated_artifact_hashes"), legacy_primary_fallback=entry.get("validated_model_hash"))
    return current, validated


def primary_issues(root: Path, state: Mapping[str, Any], entry: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    issues.extend(STAGE_CODE.validate_stage_binding(root, entry, "primary", require_validated=True))
    if entry.get("primary_execution_status") != "accepted" or entry.get("result_quality_status") != "passed":
        issues.append("主工作簿未accepted或主结果质量未passed")
    layers = set(ARTIFACT_IDENTITY.normalize_stale_layers(entry.get("stale_layers", []) or []))
    relevant = layers & {"data", "primary_code", "solution_workbook"}
    if relevant or (entry.get("artifacts_stale") is True and not layers):
        issues.append("主结果存在未关闭的数值stale层")
    try:
        current, validated = _hashes(entry)
    except ARTIFACT_IDENTITY.ArtifactIdentityError as exc:
        return [*issues, f"artifact identity alias conflict: {exc}"]
    for layer in ("data", "primary_code", "solution_workbook"):
        if layer in current and layer in validated and str(current[layer]).lower() != str(validated[layer]).lower():
            issues.append(f"主结果{layer}当前与已验收哈希不一致")
    issues.extend(_file_issues(root, entry.get("solution_workbook"),
                              validated.get("solution_workbook") or current.get("solution_workbook"), "主工作簿"))
    if entry.get("code"):
        issues.extend(_file_issues(root, entry["code"], validated.get("primary_code") or
                                  entry.get("primary_code_sha256") or current.get("primary_code"), "主求解代码"))
    if entry.get("validated_data_hash") and entry.get("data_hash") != entry["validated_data_hash"]:
        issues.append("当前data_hash与已验收主结果数据不一致")
    preprocessing = state.get("preprocessing") or {}
    if preprocessing.get("decision") == "project_level":
        if preprocessing.get("status") != "accepted" or preprocessing.get("quality_status") != "passed":
            issues.append("project_level预处理必须current且accepted/passed")
        digest = preprocessing.get("workbook_sha256")
        issues.extend(_file_issues(root, preprocessing.get("workbook"), digest, "预处理工作簿"))
        if not digest or str(entry.get("data_hash", "")).lower() != str(digest).lower():
            issues.append("主结果数据身份必须绑定已验收预处理工作簿")
    return list(dict.fromkeys(issues))


def analysis_issues(root: Path, state: Mapping[str, Any], entry: Mapping[str, Any], *,
                    for_receipt: bool = False, historical_workbook: Path | None = None,
                    data_hash: Any = None) -> list[str]:
    issues = primary_issues(root, state, entry)
    if data_hash is not None and str(data_hash).lower() != str(entry.get("data_hash", "")).lower():
        issues.append("analysis data_sha256必须继承当前主结果data_hash，不得覆盖主结果数据身份")
    if entry.get("result_analysis_status") == "not_required":
        return [*issues, "Analysis Necessity Gate=not_required，必须显式重新裁决后才能交付或验收分析"]
    # Only the identical previously accepted artifact may use historical read compatibility.
    historical_read = False
    if historical_workbook is not None and entry.get("analysis_execution_status") == "accepted" and entry.get("result_analysis_status") == "passed":
        try:
            current, validated = _hashes(entry)
            saved = entry.get("result_analysis_workbook") or entry.get("robustness_workbook")
            digest = validated.get("result_analysis_workbook") or current.get("result_analysis_workbook")
            historical_read = bool(saved) and (root / saved).resolve() == historical_workbook.resolve() and not _file_issues(root, saved, digest, "分析工作簿")
        except ARTIFACT_IDENTITY.ArtifactIdentityError:
            pass
    if not historical_read:
        reason = entry.get("result_analysis_requirement_reason")
        methods = entry.get("analysis_methods")
        if not isinstance(reason, str) or not reason.strip():
            issues.append("Analysis Necessity Gate未裁决：required计划必须有非空result_analysis_requirement_reason")
        if not isinstance(methods, list) or not methods or any(not isinstance(item, str) or not item.strip() for item in methods):
            issues.append("required计划必须有非空analysis_methods")
    if for_receipt:
        if entry.get("analysis_execution_status") not in {
            "code_delivered", "awaiting_user_execution", "workbook_received", "accepted", "rejected", "redo_required",
        }:
            issues.append("分析回执必须先有明确的代码交付/执行状态")
        issues.extend(_file_issues(root, entry.get("result_analysis_code"), entry.get("analysis_code_sha256"), "深化分析代码"))
        issues.extend(STAGE_CODE.validate_stage_binding(root, entry, "analysis"))
    return list(dict.fromkeys(issues))
