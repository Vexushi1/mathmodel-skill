"""Read-only input observations for the existing 1.1 stage identity contract."""
from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from typing import Any, Mapping

from artifact_fingerprint import combined_hash, combined_hash_from_entries, embedded_parameters_hash, sha256_file
from execution_protocol import AUXILIARY_RECEIPT_VERSION, auxiliary_config_issues


class InputUnavailableError(ValueError):
    """A declared file is absent; this does not establish a bad numerical run."""

    def __init__(self, message: str, *, paths: list[Path], missing: list[str]) -> None:
        super().__init__(message)
        self.paths = paths
        self.missing = missing
        self.observation: dict[str, Any] = {}


def input_files(root: Path, declared: Any) -> list[Path]:
    """Resolve actual files without accepting escapes or filesystem aliases."""
    if not isinstance(declared, (list, tuple)) or not declared:
        raise ValueError("data_paths必须声明非空实际输入文件列表")
    root = root.resolve()
    files: list[Path] = []
    missing: list[str] = []
    seen: set[str] = set()
    for relative in declared:
        if (not isinstance(relative, str) or not relative.strip() or "\\" in relative
                or PurePosixPath(relative).is_absolute() or PureWindowsPath(relative).drive
                or any(part in {"", ".", ".."} for part in relative.split("/"))
                or "\0" in relative or ":" in relative):
            raise ValueError(f"data_paths必须使用非空项目相对POSIX文件路径: {relative!r}")
        if relative.casefold() in seen:
            raise ValueError(f"data_paths含重复或大小写别名: {relative}")
        seen.add(relative.casefold())
        path = root
        for part in PurePosixPath(relative).parts:
            if path.is_dir():
                matches = [item.name for item in path.iterdir() if item.name.casefold() == part.casefold()]
                if len(matches) > 1 or (matches and matches[0] != part):
                    raise ValueError(f"输入路径大小写不唯一或不一致: {relative}")
            path /= part
            if path.is_symlink():
                raise ValueError(f"输入文件不接受符号链接别名: {relative}")
        path = path.resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"输入文件路径越出项目根目录: {relative}")
        if not path.exists():
            missing.append(relative)
            continue
        if not path.is_file():
            raise ValueError(f"输入文件不存在或不是文件: {relative}")
        if any(path.samefile(previous) for previous in files):
            raise ValueError(f"data_paths含同一文件的硬链接别名: {relative}")
        files.append(path)
    if missing:
        raise InputUnavailableError("输入文件不存在: " + ", ".join(missing), paths=files, missing=missing)
    return files


def _embedded_parameters_identity(config: Mapping[str, Any]) -> tuple[str | None, list[str]]:
    """Validate the explicit Python-only no-external-file input mode."""
    issues: list[str] = []
    if config.get("stage") not in {"primary", "analysis"}:
        issues.append("embedded_parameters仅支持primary/analysis阶段")
    if config.get("solver_backend") != "python":
        issues.append("embedded_parameters当前仅支持Python后端")
    if config.get("run_receipt_protocol_version") not in {"1.1.0", "1.3.0", "1.4.0"}:
        issues.append("embedded_parameters仅支持RUN_RECEIPT 1.1.0/1.3.0/1.4.0")
    if config.get("data_paths") != []:
        issues.append("embedded_parameters模式要求RUN_CONFIG.data_paths=[]")
    if "auxiliary_data_paths" in config or "auxiliary_data_sha256" in config:
        issues.append("embedded_parameters不得与辅助文件输入混用")
    try:
        digest = embedded_parameters_hash(config.get("embedded_parameters"))
    except (TypeError, ValueError) as exc:
        return None, [*issues, str(exc)]
    expected = str(config.get("data_sha256", "")).lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected) or digest != expected:
        issues.append("内置参数data_sha256与规范化参数摘要不一致")
    return digest, issues


def data_input_files(root: Path, config: Mapping[str, Any]) -> list[Path]:
    """Resolve file-backed data, or validate and return no files for embedded parameters."""
    mode = config.get("data_identity_mode", "combined")
    if mode == "embedded_parameters":
        _, issues = _embedded_parameters_identity(config)
        if issues:
            raise ValueError("; ".join(issues))
        return []
    if mode not in {"combined", "preprocessing_workbook"}:
        raise ValueError(f"不支持的data_identity_mode: {mode!r}")
    return input_files(root, config.get("data_paths"))


def declared_input_files(root: Path, config: Mapping[str, Any]) -> list[Path]:
    """Resolve all real file inputs while preserving the empty embedded-parameter case."""
    configuration_issues = auxiliary_config_issues(config)
    if configuration_issues:
        raise ValueError("; ".join(configuration_issues))
    files = data_input_files(root, config)
    if config.get("run_receipt_protocol_version") == AUXILIARY_RECEIPT_VERSION:
        auxiliaries = input_files(root, config["auxiliary_data_paths"])
        if any(aux.samefile(base) for aux in auxiliaries for base in files):
            raise ValueError("auxiliary_data_paths不得重复主数据文件或其别名")
        files.extend(auxiliaries)
    return files


def observe_preprocessing_inputs(root: Path, config: Mapping[str, Any]) -> tuple[str, dict[str, str]]:
    """Observe 1.0 raw inputs once; historical single-file and combined identities are valid."""
    root = root.resolve()
    files = input_files(root, config.get("data_paths"))
    hashes = {path.relative_to(root).as_posix(): sha256_file(path) for path in files}
    combined = combined_hash_from_entries(sorted(hashes.items()))
    if len(hashes) == 1 and combined != str(config.get("data_sha256", "")).lower():
        return next(iter(hashes.values())), hashes
    assert combined is not None  # input_files requires a nonempty declaration.
    return combined, hashes


def observe_inputs(root: Path, config: Mapping[str, Any], state: Mapping[str, Any]) -> dict[str, Any]:
    """Observe file-backed or embedded inputs without replacing delivered hashes."""
    root = root.resolve()
    configuration_issues = auxiliary_config_issues(config)
    if configuration_issues:
        raise ValueError("; ".join(configuration_issues))

    mode = config.get("data_identity_mode", "combined")
    preprocessing = state.get("preprocessing") or {}
    issues: list[str] = []
    embedded_digest: str | None = None

    if mode == "embedded_parameters":
        embedded_digest, embedded_issues = _embedded_parameters_identity(config)
        issues.extend(embedded_issues)
        if preprocessing.get("decision") == "project_level":
            raise ValueError("embedded_parameters不得绕过project_level已验收预处理工作簿")
        files: list[Path] = []
        digest = embedded_digest
    else:
        try:
            files = input_files(root, config.get("data_paths"))
        except InputUnavailableError as exc:
            exc.observation = {"paths": [path.relative_to(root).as_posix() for path in exc.paths], "issues": []}
            raise
        if mode == "preprocessing_workbook":
            if (preprocessing.get("decision") != "project_level" or preprocessing.get("status") != "accepted"
                    or preprocessing.get("quality_status") != "passed"):
                raise ValueError("preprocessing_workbook输入必须绑定accepted/passed项目级预处理")
            accepted = input_files(root, [preprocessing.get("workbook") or "数据预处理/数据预处理结果.xlsx"])
            if len(files) != 1 or files != accepted or files[0].suffix.lower() != ".xlsx":
                raise ValueError("preprocessing_workbook的data_paths必须恰含唯一已登记预处理XLSX")
            digest = sha256_file(files[0])
            if digest != str(preprocessing.get("workbook_sha256", "")).lower():
                issues.append("预处理工作簿当前文件SHA-256与已验收身份不一致")
        elif mode == "combined":
            if preprocessing.get("decision") == "project_level":
                raise ValueError("新1.1 project_level阶段必须显式data_identity_mode=preprocessing_workbook")
            digest = combined_hash(files, root)
        else:
            raise ValueError(f"不支持的data_identity_mode: {mode!r}")

        expected = str(config.get("data_sha256", "")).lower()
        if not re.fullmatch(r"[0-9a-f]{64}", expected) or digest != expected:
            issues.append("当前实际输入data_sha256与已交付RUN_CONFIG不一致")

    result = {
        "paths": [path.relative_to(root).as_posix() for path in files],
        "data_sha256": digest,
        "data_identity_mode": mode,
        "issues": issues,
    }
    if embedded_digest is not None:
        result["embedded_parameters_sha256"] = embedded_digest

    if config.get("run_receipt_protocol_version") == AUXILIARY_RECEIPT_VERSION:
        try:
            auxiliaries = input_files(root, config["auxiliary_data_paths"])
        except InputUnavailableError as exc:
            exc.observation = {**result, "auxiliary_data_paths": [
                path.relative_to(root).as_posix() for path in exc.paths]}
            raise
        if any(aux.samefile(base) for aux in auxiliaries for base in files):
            raise ValueError("auxiliary_data_paths不得重复主数据文件或其别名")
        covered = preprocessing.get("covered_raw_sources")
        if not isinstance(covered, list) or not covered or any(not isinstance(item, str) or not item.strip() for item in covered):
            raise ValueError("辅助输入核验需要有效covered_raw_sources")
        for relative in covered:
            if (PurePosixPath(relative).is_absolute() or PureWindowsPath(relative).drive
                    or "\\" in relative or any(part in {"", ".", ".."} for part in relative.split("/"))):
                raise ValueError("covered_raw_sources路径必须为规范项目相对路径")
            covered_path = (root / relative).resolve()
            if not covered_path.is_relative_to(root):
                raise ValueError("covered_raw_sources路径越出项目根目录")
            for aux in auxiliaries:
                same_name = aux.relative_to(root).as_posix().casefold() == relative.casefold()
                same_file = covered_path.is_file() and aux.samefile(covered_path)
                if same_name or same_file:
                    raise ValueError("auxiliary_data_paths不得重读covered_raw_sources已覆盖原始源")
        auxiliary_digest = combined_hash(auxiliaries, root)
        if auxiliary_digest != config["auxiliary_data_sha256"].lower():
            issues.append("当前实际auxiliary_data_sha256与已交付RUN_CONFIG不一致")
        result.update(
            auxiliary_data_paths=[path.relative_to(root).as_posix() for path in auxiliaries],
            auxiliary_data_sha256=auxiliary_digest,
        )
        result["paths"].extend(result["auxiliary_data_paths"])
    return result
