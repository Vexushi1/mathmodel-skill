#!/usr/bin/env python3
"""Pack a modeling project while excluding caches and temporary build files."""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

EXCLUDED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".venv", "venv"}
EXCLUDED_NAMES = {
    ".DS_Store",
    "Thumbs.db",
}
EXCLUDED_ENDINGS = (
    ".aux",
    ".bcf",
    ".bbl",
    ".blg",
    ".log",
    ".out",
    ".toc",
    ".lof",
    ".lot",
    ".run.xml",
    ".synctex.gz",
    ".fdb_latexmk",
    ".fls",
    ".xdv",
)


def should_exclude(path: Path, root: Path, output: Path) -> bool:
    if path.resolve() == output:
        return True
    relative = path.relative_to(root)
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return True
    if path.name in EXCLUDED_NAMES:
        return True
    return path.name.endswith(EXCLUDED_ENDINGS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", nargs="?", default=".")
    parser.add_argument("--output", default="hsk_submission_backup.zip")
    args = parser.parse_args()

    root = Path(args.project).resolve()
    if not root.is_dir():
        raise SystemExit(f"project directory not found: {root}")
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or should_exclude(path, root, output):
                continue
            archive.write(path, path.relative_to(root))
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
