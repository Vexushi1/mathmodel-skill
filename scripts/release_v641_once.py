#!/usr/bin/env python3
"""One-time coordinated 6.4.1 patch release migration for PR #23."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = "6.4.0"
NEW = "6.4.1"
GENERATED = {
    "SKILL_FILE_INDEX.md",
    "TEMPLATE_INDEX.md",
    "HSK_SKILL_FILE_INDEX_V622.md",
    "HSK_TEMPLATE_INDEX_V622.md",
    "MANIFEST.sha256",
}
SKIP_NAMES = {"CHANGELOG.md", "release_v641_once.py"}
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".py"}


def is_active(relative: Path) -> bool:
    if relative.as_posix() in GENERATED:
        return False
    if relative.name in SKIP_NAMES or relative.name.startswith("CHANGELOG_V"):
        return False
    if relative.parts and relative.parts[0] == "legacy":
        return relative == Path("legacy/README.md")
    return relative.suffix.lower() in TEXT_SUFFIXES


def replace_active_versions() -> list[str]:
    changed: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if not is_active(relative):
            continue
        text = path.read_text(encoding="utf-8")
        if OLD not in text:
            continue
        path.write_text(text.replace(OLD, NEW), encoding="utf-8", newline="\n")
        changed.append(relative.as_posix())
    return changed


def update_changelog() -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "## Unreleased: 6.4.1 active-residue cleanup",
        "## Current release: 6.4.1",
        1,
    )
    pending_note = (
        "\nThe package version remains 6.4.0 while this draft patch is under review. "
        "The coordinated 6.4.1 version bump is applied only after the cleanup diff and "
        "generated files pass CI.\n"
    )
    text = text.replace(pending_note, "\n", 1)
    text = text.replace("## Current release: 6.4.0", "## Previous release: 6.4.0", 1)
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    changed = replace_active_versions()
    update_changelog()
    print(f"updated {len(changed)} active files to {NEW}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
