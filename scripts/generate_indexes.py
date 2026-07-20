#!/usr/bin/env python3
"""Generate repository file indexes and MANIFEST.sha256 for HSK v6.2.2."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "6.2.2"
SKILL_INDEX = ROOT / "HSK_SKILL_FILE_INDEX_V622.md"
TEMPLATE_INDEX = ROOT / "HSK_TEMPLATE_INDEX_V622.md"
MANIFEST = ROOT / "MANIFEST.sha256"
EXCLUDED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".venv", "venv"}
EXCLUDED_FILES = {MANIFEST.name}


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        files.append(relative)
    return sorted(files, key=lambda item: item.as_posix())


def index_text(title: str, files: list[Path]) -> str:
    lines = [f"# {title} v{VERSION}", ""]
    lines.extend(f"- `{path.as_posix()}`" for path in files)
    return "\n".join(lines) + "\n"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest_text(files: list[Path]) -> str:
    lines: list[str] = []
    for relative in files:
        if relative.name in EXCLUDED_FILES:
            continue
        lines.append(f"{sha256(ROOT / relative)}  {relative.as_posix()}")
    return "\n".join(lines) + "\n"


def generated_payloads() -> dict[Path, str]:
    current_files = iter_files()
    skill_files = sorted(set(current_files + [SKILL_INDEX.relative_to(ROOT), TEMPLATE_INDEX.relative_to(ROOT), MANIFEST.relative_to(ROOT)]), key=lambda item: item.as_posix())
    template_files = [path for path in skill_files if path.parts and path.parts[0] == "templates"]
    skill_payload = index_text("HSK Skill File Index", skill_files)
    template_payload = index_text("HSK Template Index", template_files)

    # Manifest must hash the newly generated index contents, not stale versions.
    SKILL_INDEX.write_text(skill_payload, encoding="utf-8")
    TEMPLATE_INDEX.write_text(template_payload, encoding="utf-8")
    refreshed_files = iter_files()
    return {
        SKILL_INDEX: skill_payload,
        TEMPLATE_INDEX: template_payload,
        MANIFEST: manifest_text(refreshed_files),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when generated files differ from repository state")
    args = parser.parse_args()

    before = {
        path: path.read_text(encoding="utf-8") if path.is_file() else None
        for path in (SKILL_INDEX, TEMPLATE_INDEX, MANIFEST)
    }
    payloads = generated_payloads()
    if args.check:
        differences = [path.relative_to(ROOT).as_posix() for path, text in payloads.items() if before[path] != text]
        if differences:
            print("generated indexes are stale:")
            for item in differences:
                print("-", item)
            return 1
        print("generated indexes are current")
        return 0

    for path, text in payloads.items():
        path.write_text(text, encoding="utf-8")
        print(path.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
