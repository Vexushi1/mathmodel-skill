#!/usr/bin/env python3
"""Deterministic artifact fingerprint helpers extracted mechanically from sync_project."""
from __future__ import annotations

import hashlib
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

def combined_hash(paths: Iterable[Path], root: Path) -> str | None:
    files = sorted(
        {Path(path).resolve() for path in paths if Path(path).is_file()},
        key=lambda item: item.as_posix(),
    )
    if not files:
        return None
    digest = hashlib.sha256()
    for path in files:
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            relative = path.as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()

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
