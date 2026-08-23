#!/usr/bin/env python3
"""Validate official or reproducibility ZIP packages against the current project.

The validator consumes ``submission_manifest.yaml`` embedded by
``hsk_pack_submission.py``. It verifies archive hashes, compares archived project files
to the current project, binds the packaged PDF to the current compiled PDF, and enforces
verified competition allowlists for official submissions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

SKILL_ROOT = Path(__file__).resolve().parent.parent
COMPETITION_PROFILES = SKILL_ROOT / "config" / "competition_profiles.yaml"
MANIFEST_NAME = "submission_manifest.yaml"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def resolve_competition(token: str, payload: Mapping[str, Any]) -> tuple[str, Mapping[str, Any]]:
    normalized = token.strip().lower()
    for name, config in (payload.get("profiles") or {}).items():
        aliases = [name, *config.get("aliases", [])]
        if normalized in {str(item).lower() for item in aliases}:
            return str(name), config
    raise ValueError(f"unknown competition profile: {token}")


def expand_allowlist(root: Path, patterns: Iterable[str]) -> set[str]:
    names: set[str] = set()
    for raw in patterns:
        pattern = str(raw).strip()
        if not pattern:
            continue
        for candidate in root.glob(pattern):
            if not candidate.is_file():
                continue
            resolved = candidate.resolve()
            try:
                names.add(resolved.relative_to(root).as_posix())
            except ValueError:
                continue
    return names


def _current_compiled_pdf(root: Path, state: Mapping[str, Any]) -> Path:
    artifacts = state.get("artifacts") or {}
    declared = artifacts.get("compiled_pdf")
    return root / str(declared or "final_latex/main.pdf")


def declared_package_path(root: Path, state: Mapping[str, Any]) -> Path:
    artifacts = state.get("artifacts") or {}
    declared = str(artifacts.get("submission_package") or "submission/submission.zip")
    candidate = Path(declared)
    return candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()


def _manifest_from_archive(archive: zipfile.ZipFile) -> tuple[dict[str, Any], list[str]]:
    names = archive.namelist()
    if names.count(MANIFEST_NAME) != 1:
        return {}, ["提交包必须且只能包含一个submission_manifest.yaml"]
    try:
        payload = yaml.safe_load(archive.read(MANIFEST_NAME).decode("utf-8")) or {}
    except Exception as exc:  # noqa: BLE001
        return {}, [f"无法解析submission_manifest.yaml: {exc}"]
    if not isinstance(payload, dict):
        return {}, ["submission_manifest.yaml必须是映射结构"]
    return payload, []


def validate_package(
    project_root: Path,
    package_path: Path,
    *,
    competition: str | None = None,
) -> dict[str, Any]:
    root = project_root.resolve()
    package = package_path.resolve()
    issues: list[str] = []
    warnings: list[str] = []
    state = load_yaml(root / "state/project_state.yaml")

    try:
        package.relative_to(root)
    except ValueError:
        issues.append("正式提交包必须位于当前项目目录内")

    if not package.is_file():
        return {"status": "failed", "kind": None, "issues": sorted(set([*issues, f"提交包不存在: {package}"])), "warnings": []}
    try:
        archive = zipfile.ZipFile(package)
    except Exception as exc:  # noqa: BLE001
        return {"status": "failed", "kind": None, "issues": sorted(set([*issues, f"无法打开提交ZIP: {exc}"])), "warnings": []}

    manifest: dict[str, Any] = {}
    with archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            issues.append(f"提交ZIP存在重复文件名: {duplicates}")
        manifest, manifest_issues = _manifest_from_archive(archive)
        issues.extend(manifest_issues)
        if str(manifest.get("package_schema_version", "")) != "1.0.0":
            issues.append("submission_manifest缺少v1 package schema")
        kind = str(manifest.get("kind", ""))
        if kind not in {"official", "reproducibility"}:
            issues.append(f"未知package kind: {kind or '<missing>'}")

        records = manifest.get("files") or []
        if not isinstance(records, list):
            issues.append("submission_manifest.files必须是列表")
            records = []
        declared_paths: list[str] = []
        for record in records:
            if not isinstance(record, Mapping):
                issues.append("submission_manifest.files存在非法记录")
                continue
            relative = str(record.get("path", "")).strip()
            recorded_hash = str(record.get("sha256", "")).strip()
            if not relative or not recorded_hash:
                issues.append("submission_manifest文件记录缺少path或sha256")
                continue
            if relative == MANIFEST_NAME:
                issues.append("submission_manifest不得把自身列入files")
                continue
            if relative in declared_paths:
                issues.append(f"submission_manifest重复声明文件: {relative}")
            declared_paths.append(relative)
            if relative not in names:
                issues.append(f"manifest声明文件未进入ZIP: {relative}")
                continue
            archived_hash = sha256_bytes(archive.read(relative))
            if archived_hash != recorded_hash:
                issues.append(f"ZIP中文件哈希与manifest不一致: {relative}")
            current = (root / relative).resolve()
            try:
                current.relative_to(root)
            except ValueError:
                issues.append(f"manifest路径越出项目根目录: {relative}")
                continue
            if not current.is_file():
                issues.append(f"manifest声明的项目文件当前不存在: {relative}")
            elif sha256_file(current) != archived_hash:
                issues.append(f"提交包文件不是当前项目版本: {relative}")

        archived_payload = set(names) - {MANIFEST_NAME}
        if archived_payload != set(declared_paths):
            undeclared = sorted(archived_payload - set(declared_paths))
            missing = sorted(set(declared_paths) - archived_payload)
            if undeclared:
                issues.append(f"ZIP包含manifest未声明文件: {undeclared}")
            if missing:
                issues.append(f"manifest声明但ZIP缺失文件: {missing}")

        compiled_pdf = _current_compiled_pdf(root, state)
        if not compiled_pdf.is_file():
            issues.append(f"当前项目缺少正式编译PDF: {compiled_pdf}")
        else:
            current_pdf_hash = sha256_file(compiled_pdf)
            matching_pdf = [
                path for path in declared_paths
                if path.lower().endswith(".pdf")
                and path in names
                and sha256_bytes(archive.read(path)) == current_pdf_hash
            ]
            if not matching_pdf:
                issues.append("提交包未包含与当前compiled_pdf哈希一致的PDF")

        if kind == "official":
            profile_payload = load_yaml(COMPETITION_PROFILES)
            token = competition or str(manifest.get("competition_profile") or (state.get("project") or {}).get("competition") or "")
            if not token:
                issues.append("official提交包缺少competition profile")
            else:
                try:
                    profile_name, profile = resolve_competition(token, profile_payload)
                except ValueError as exc:
                    issues.append(str(exc))
                else:
                    rules = profile.get("edition_rules") or {}
                    if rules.get("verification_status") != "verified":
                        issues.append(f"{profile_name}当届提交规则尚未verified，不能验证official package")
                    if not rules.get("verified_at") or not rules.get("source"):
                        issues.append(f"{profile_name} verified规则缺少verified_at/source证据")
                    patterns = [str(item) for item in (rules.get("submission_files") or [])]
                    if not patterns:
                        issues.append(f"{profile_name} verified submission_files allowlist为空")
                    expected = expand_allowlist(root, patterns)
                    if patterns and not expected:
                        issues.append(f"{profile_name} submission_files allowlist未解析到任何当前项目文件")
                    if archived_payload != expected:
                        issues.append(
                            "official package内容与当前verified submission_files allowlist不一致: "
                            f"expected={sorted(expected)}, actual={sorted(archived_payload)}"
                        )
                    if manifest.get("competition_profile") != profile_name:
                        issues.append("official package manifest的competition_profile与当前profile不一致")
                    if manifest.get("rule_verification_status") != "verified":
                        issues.append("official package manifest未记录verified规则状态")
                    if manifest.get("rule_verified_at") != rules.get("verified_at"):
                        issues.append("official package manifest的rule_verified_at与当前规则不一致")
                    if manifest.get("rule_source") != rules.get("source"):
                        issues.append("official package manifest的rule_source与当前规则来源不一致")
                    if manifest.get("submission_files_allowlist") != patterns:
                        issues.append("official package manifest记录的submission_files allowlist与当前规则不一致")
        elif kind == "reproducibility":
            lowered = [name.lower() for name in archived_payload]
            for suffix, label in ((".pdf", "PDF"), (".py", "Python代码"), (".xlsx", "结果工作簿"), (".m", "MATLAB脚本")):
                if not any(name.endswith(suffix) for name in lowered):
                    issues.append(f"完整复现包缺少{label}")
            if "模型论文框架.md" not in archived_payload:
                warnings.append("完整复现包未包含模型论文框架.md")

    return {
        "status": "passed" if not issues else "failed",
        "kind": str(manifest.get("kind", "")) if manifest else None,
        "issues": sorted(set(issues)),
        "warnings": sorted(set(warnings)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", nargs="?", default=".")
    parser.add_argument("--package", default=None, help="package path; defaults to state.artifacts.submission_package")
    parser.add_argument("--competition")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.project).resolve()
    state = load_yaml(root / "state/project_state.yaml")
    if args.package:
        raw_package = Path(args.package)
        package = raw_package.resolve() if raw_package.is_absolute() else (root / raw_package).resolve()
    else:
        package = declared_package_path(root, state)
    report = validate_package(root, package, competition=args.competition)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for item in report["issues"]:
            print("-", item)
        for item in report["warnings"]:
            print("warning:", item)
        print(f"submission package validation: {report['status']}")
    return 1 if args.strict and report["status"] != "passed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
