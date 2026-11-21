#!/usr/bin/env python3
"""Deterministic artifact fingerprint helpers extracted mechanically from sync_project."""
from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Iterable

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def sha256_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def embedded_parameters_hash(parameters: Mapping[str, object]) -> str:
    """Hash JSON-compatible parameters with a versioned, domain-separated prefix."""
    if not isinstance(parameters, Mapping) or not parameters:
        raise ValueError("embedded_parameters必须是非空JSON对象")

    def normalize(value: object, location: str) -> object:
        if value is None or isinstance(value, (str, bool, int)):
            return value
        if isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError(f"embedded_parameters含非有限数值: {location}")
            return value
        if isinstance(value, list):
            return [normalize(item, f"{location}[{index}]") for index, item in enumerate(value)]
        if isinstance(value, Mapping):
            if any(not isinstance(key, str) or not key for key in value):
                raise ValueError(f"embedded_parameters对象键必须为非空字符串: {location}")
            return {key: normalize(value[key], f"{location}.{key}") for key in sorted(value)}
        raise ValueError(f"embedded_parameters包含非JSON类型: {location}")

    normalized = normalize(parameters, "embedded_parameters")
    payload = json.dumps(
        normalized, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(b"HSK-EMBEDDED-PARAMETERS-V1\0" + payload).hexdigest()

def combined_hash_from_entries(entries: Iterable[tuple[str, str]]) -> str | None:
    """Apply the bundle format to unique, ordered path/hash pairs from one read set."""
    entries = list(entries)
    if not entries:
        return None
    digest = hashlib.sha256()
    for relative, file_sha256 in entries:
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(file_sha256))
    return digest.hexdigest()


def combined_hash(paths: Iterable[Path], root: Path) -> str | None:
    root = root.resolve()
    files = sorted(
        {Path(path).resolve() for path in paths if Path(path).is_file()},
        key=lambda item: item.as_posix(),
    )
    entries = []
    for path in files:
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            relative = path.as_posix()
        entries.append((relative, sha256_file(path)))
    return combined_hash_from_entries(entries)

def framework_section_text(path: Path, anchor: str) -> str | None:
    if not path.is_file() or not anchor.strip():
        return None
    lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n").splitlines()
    target = anchor.strip()
    start = next((index for index, line in enumerate(lines) if line.strip() == target), None)
    if start is None:
        start = next(
            (index for index, line in enumerate(lines) if line.lstrip().startswith("#") and target in line.strip()),
            None,
        )
    if start is None:
        return None
    heading = lines[start].lstrip()
    level = len(heading) - len(heading.lstrip("#"))
    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].lstrip()
        if stripped.startswith("#"):
            next_level = len(stripped) - len(stripped.lstrip("#"))
            if next_level <= level:
                end = index
                break
    return "\n".join(lines[start:end]).strip() + "\n"

def framework_section_hash(path: Path, anchor: str) -> str | None:
    text = framework_section_text(path, anchor)
    return sha256_text(text) if text else None
