#!/usr/bin/env python3
"""Create attested official or reproducibility packages for a modeling project.

Official packages use only a verified competition-profile allowlist. Reproducibility
packages preserve the historical broad backup behavior, but now include a deterministic
manifest with per-file SHA-256 hashes. Neither mode may silently masquerade as the other.
"""
from __future__ import annotations

import argparse
import hashlib
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parent.parent
COMPETITION_PROFILES = ROOT / "config" / "competition_profiles.yaml"
EXCLUDED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".venv", "venv", "submission"}
EXCLUDED_NAMES = {".DS_Store", "Thumbs.db"}
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


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def should_exclude(path: Path, root: Path, output: Path) -> bool:
    if path.resolve() == output:
        return True
    relative = path.relative_to(root)
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return True
    if path.name in EXCLUDED_NAMES:
        return True
    return path.name.endswith(EXCLUDED_ENDINGS)


def load_competition_profiles() -> dict[str, Any]:
    if not COMPETITION_PROFILES.is_file():
        raise SystemExit(f"competition profiles missing: {COMPETITION_PROFILES}")
    return yaml.safe_load(COMPETITION_PROFILES.read_text(encoding="utf-8")) or {}


def resolve_competition(token: str, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    normalized = token.strip().lower()
    for name, config in (payload.get("profiles") or {}).items():
        aliases = [name, *config.get("aliases", [])]
        if normalized in {str(item).lower() for item in aliases}:
            return name, config
    raise SystemExit(f"unknown competition profile: {token}")


def _expand_allowlist(root: Path, patterns: Iterable[str]) -> list[Path]:
    files: set[Path] = set()
    for raw in patterns:
        pattern = str(raw).strip()
        if not pattern:
            continue
        for candidate in root.glob(pattern):
            if candidate.is_file():
                resolved = candidate.resolve()
                try:
                    resolved.relative_to(root)
                except ValueError:
                    continue
                files.add(resolved)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def official_files(root: Path, competition: str) -> tuple[list[Path], dict[str, Any]]:
    payload = load_competition_profiles()
    name, config = resolve_competition(competition, payload)
    rules = config.get("edition_rules") or {}
    if rules.get("verification_status") != "verified":
        raise SystemExit(
            f"official package refused: {name} edition rules are not verified; "
            "verify the current competition rules before packaging"
        )
    patterns = rules.get("submission_files") or []
    if not patterns:
        raise SystemExit(f"official package refused: {name} submission_files allowlist is empty")
    files = _expand_allowlist(root, patterns)
    if not files:
        raise SystemExit(f"official package refused: verified allowlist resolved to no project files: {patterns}")
    metadata = {
        "competition_profile": name,
        "rule_verification_status": rules.get("verification_status"),
        "rule_verified_at": rules.get("verified_at"),
        "rule_source": rules.get("source"),
        "submission_files_allowlist": [str(item) for item in patterns],
    }
    return files, metadata


def reproducibility_files(root: Path, output: Path) -> list[Path]:
    return [
        path.resolve()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not should_exclude(path, root, output)
    ]


def build_manifest(root: Path, files: Iterable[Path], *, kind: str, metadata: dict[str, Any]) -> dict[str, Any]:
    records = [
        {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)}
        for path in files
    ]
    return {
        "package_schema_version": "1.0.0",
        "kind": kind,
        **metadata,
        "files": records,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", nargs="?", default=".")
    parser.add_argument("--mode", choices=["official", "reproducibility"], default="reproducibility")
    parser.add_argument("--competition", help="required for official mode; profile name or alias")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    root = Path(args.project).resolve()
    if not root.is_dir():
        raise SystemExit(f"project directory not found: {root}")
    default_name = "official_submission.zip" if args.mode == "official" else "hsk_submission_backup.zip"
    output = Path(args.output or default_name).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    if args.mode == "official":
        if not args.competition:
            raise SystemExit("--competition is required for --mode official")
        files, metadata = official_files(root, args.competition)
    else:
        files = reproducibility_files(root, output)
        metadata = {
            "competition_profile": None,
            "rule_verification_status": None,
            "rule_verified_at": None,
            "rule_source": None,
            "submission_files_allowlist": None,
        }

    manifest = build_manifest(root, files, kind=args.mode, metadata=metadata)
    manifest_bytes = yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False).encode("utf-8")
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(root).as_posix())
        archive.writestr("submission_manifest.yaml", manifest_bytes)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
