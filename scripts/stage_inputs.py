"""Read-only input observations for the existing 1.1 stage identity contract."""
from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from typing import Any, Mapping

from artifact_fingerprint import combined_hash, sha256_file


def input_files(root: Path, declared: Any) -> list[Path]:
    """Resolve actual files without accepting escapes or filesystem aliases."""
    if not isinstance(declared, (list, tuple)) or not declared:
        raise ValueError("data_paths必须声明非空实际输入文件列表")
    root = root.resolve()
    files: list[Path] = []
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
        if not path.is_file():
            raise ValueError(f"输入文件不存在或不是文件: {relative}")
        files.append(path)
    return files


def observe_inputs(root: Path, config: Mapping[str, Any], state: Mapping[str, Any]) -> dict[str, Any]:
    """Return current input bytes and issues, never replacing delivered hashes."""
    root = root.resolve()
    files = input_files(root, config.get("data_paths"))
    mode = config.get("data_identity_mode", "combined")
    preprocessing = state.get("preprocessing") or {}
    issues: list[str] = []
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
    return {"paths": [path.relative_to(root).as_posix() for path in files],
            "data_sha256": digest, "data_identity_mode": mode, "issues": issues}
