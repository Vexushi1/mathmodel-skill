#!/usr/bin/env python3
"""Generate active-package indexes and a cross-platform MANIFEST.sha256 for HSK v6.3.2."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "6.3.2"
# Public filenames remain V622 for compatibility; generated titles carry the active Skill version.
SKILL_INDEX = ROOT / "HSK_SKILL_FILE_INDEX_V622.md"
TEMPLATE_INDEX = ROOT / "HSK_TEMPLATE_INDEX_V622.md"
MANIFEST = ROOT / "MANIFEST.sha256"
EXCLUDED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".venv", "venv"}
ACTIVE_ARCHIVE_POINTERS = {Path("legacy/README.md")}
BINARY_SUFFIXES = {
    ".7z", ".doc", ".docx", ".gif", ".gz", ".ico", ".jpeg", ".jpg", ".mat", ".npy",
    ".npz", ".otf", ".pdf", ".pickle", ".pkl", ".png", ".rar", ".tif", ".tiff",
    ".ttf", ".woff", ".woff2", ".xls", ".xlsx", ".zip",
}
GENERATED_RELATIVE = {
    SKILL_INDEX.relative_to(ROOT),
    TEMPLATE_INDEX.relative_to(ROOT),
    MANIFEST.relative_to(ROOT),
}


def is_active_path(relative: Path) -> bool:
    if relative.parts and relative.parts[0] == "legacy":
        return relative in ACTIVE_ARCHIVE_POINTERS
    return True


def iter_files() -> list[Path]:
    files: set[Path] = set(GENERATED_RELATIVE)
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        if not is_active_path(relative):
            continue
        files.add(relative)
    return sorted(files, key=lambda item: item.as_posix())


def index_text(title: str, files: list[Path]) -> str:
    lines = [f"# {title} v{VERSION}", "", "本索引仅覆盖活动 Skill；历史文件通过 `legacy/README.md` 追溯。", ""]
    lines.extend(f"- `{path.as_posix()}`" for path in files)
    return "\n".join(lines) + "\n"


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_manifest_bytes(path: Path, data: bytes) -> bytes:
    """Normalize line endings for UTF-8 text while preserving binary bytes exactly."""
    if path.suffix.lower() in BINARY_SUFFIXES:
        return data
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def digest_file(path: Path) -> str:
    return digest_bytes(normalized_manifest_bytes(path, path.read_bytes()))


def manifest_text(files: list[Path], overrides: dict[Path, str]) -> str:
    lines: list[str] = []
    for relative in files:
        if relative == MANIFEST.relative_to(ROOT):
            continue
        if relative in overrides:
            digest = digest_bytes(overrides[relative].encode("utf-8"))
        else:
            absolute = ROOT / relative
            if not absolute.is_file():
                raise FileNotFoundError(f"manifest source missing: {relative.as_posix()}")
            digest = digest_file(absolute)
        lines.append(f"{digest}  {relative.as_posix()}")
    return "\n".join(lines) + "\n"


def generated_payloads() -> dict[Path, str]:
    files = iter_files()
    template_files = [path for path in files if path.parts and path.parts[0] == "templates"]
    skill_payload = index_text("HSK Active Skill File Index", files)
    template_payload = index_text("HSK Active Template Index", template_files)
    overrides = {
        SKILL_INDEX.relative_to(ROOT): skill_payload,
        TEMPLATE_INDEX.relative_to(ROOT): template_payload,
    }
    return {
        SKILL_INDEX: skill_payload,
        TEMPLATE_INDEX: template_payload,
        MANIFEST: manifest_text(files, overrides),
    }


def write_lf_text(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when generated files differ from repository state")
    args = parser.parse_args()
    payloads = generated_payloads()
    if args.check:
        differences = []
        for path, expected in payloads.items():
            actual = path.read_text(encoding="utf-8") if path.is_file() else None
            if actual != expected:
                differences.append(path.relative_to(ROOT).as_posix())
        if differences:
            print("generated indexes are stale:")
            for item in differences:
                print("-", item)
            return 1
        print("generated indexes are current")
        return 0
    for path, text in payloads.items():
        write_lf_text(path, text)
        print(path.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
