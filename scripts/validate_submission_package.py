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
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT / "scripts"))
from submission_requirements import expand_required_allowlist, reproducibility_requirements

COMPETITION_PROFILES = SKILL_ROOT / "config" / "competition_profiles.yaml"
MANIFEST_NAME = "submission_manifest.yaml"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _sha256_stream(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


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
    return {path.relative_to(root.resolve()).as_posix() for path in expand_required_allowlist(root, patterns)}


def _current_compiled_pdf(root: Path, state: Mapping[str, Any]) -> Path:
    artifacts = state.get("artifacts") or {}
    declared = artifacts.get("compiled_pdf")
    return root / str(declared or "final_latex/main.pdf")


def declared_package_path(root: Path, state: Mapping[str, Any]) -> Path:
    """Resolve the raw package without silently choosing between multiple candidates."""
    artifacts = state.get("artifacts") or {}
    declared = artifacts.get("submission_package")
    if declared:
        candidate = Path(str(declared))
        return candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()

    submission_dir = root / "submission"
    candidates = sorted(path.resolve() for path in submission_dir.glob("*.zip") if path.is_file()) if submission_dir.is_dir() else []
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        names = ", ".join(path.name for path in candidates)
        raise SystemExit(
            "multiple submission ZIPs exist but state.artifacts.submission_package is not declared: " + names
        )
    return (submission_dir / "submission.zip").resolve()


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
    state_path = root / 'state/project_state.yaml'
    state_bytes = state_path.read_bytes() if state_path.is_file() else None
    state_hash = sha256_bytes(state_bytes) if state_bytes is not None else None
    state = (yaml.safe_load(state_bytes.decode('utf-8')) or {}) if state_bytes is not None else {}

    # A direct invocation must replay the opt-in B2 gate and the formal proof
    # chain; a matching ZIP/PDF hash alone cannot certify changed claim sources.
    from claim_consumption import formal_text_gate
    from project_transaction import _check_read_set

    claim_gate = formal_text_gate(root)
    observed = claim_gate['observed_sources']
    project_read_set = dict(observed['project'])
    if project_read_set.get('state/project_state.yaml') != state_hash:
        issues.append('项目State首读与B2门读集不一致')
    project_read_set['state/project_state.yaml'] = state_hash
    package_hash: str | None = None

    def finish(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            if package_hash is not None and _sha256_stream(package) != package_hash:
                raise ValueError('提交ZIP在验证过程中发生变化')
            _check_read_set(root, project_read_set)
            _check_read_set(SKILL_ROOT, observed['skill'])
        except (OSError, ValueError, RuntimeError) as exc:
            payload['issues'] = sorted(set([*payload['issues'], '提交包验证读集冲突: ' + str(exc)]))
            payload['status'] = 'failed'
        return payload

    if claim_gate['status'] == 'failed':
        issues.append('B2正式文本门未通过: ' + '; '.join(claim_gate['issues'][:8]))
    elif claim_gate['status'] == 'passed':
        from latex_delivery import recorded_input_snapshot, source_bundle_snapshot, verify_compile_report

        latex_root = root / 'final_latex'
        skill_profile = 'core/compile_profiles.yaml'
        profile_before = _sha256_stream(SKILL_ROOT / skill_profile)
        if skill_profile in observed['skill'] and observed['skill'][skill_profile] != profile_before:
            issues.append('B2读集与编译profile版本冲突')
        observed['skill'][skill_profile] = profile_before
        compile_path = latex_root / 'compile_report.yaml'
        if not compile_path.is_file():
            issues.append('B2正式文本门要求当前compile_report.yaml证明')
        else:
            project_read_set['final_latex/compile_report.yaml'] = _sha256_stream(compile_path)
            compile_report = load_yaml(compile_path)
            if not isinstance(compile_report, Mapping):
                issues.append('B2正式文本门的compile_report.yaml结构无效')
            else:
                bound_audit = Path(str(compile_report.get('latex_audit_report') or 'latex_audit_report.yaml'))
                audit_path = bound_audit if bound_audit.is_absolute() else latex_root / bound_audit
                if audit_path.is_file():
                    if audit_path.resolve().is_relative_to(root):
                        project_read_set[audit_path.resolve().relative_to(root).as_posix()] = _sha256_stream(audit_path)
                issues.extend(verify_compile_report(
                    project=latex_root, main=latex_root / 'main.tex',
                    pdf=_current_compiled_pdf(root, state), report=compile_report,
                ))
                try:
                    source_snapshot = source_bundle_snapshot(latex_root / 'main.tex')
                    input_snapshot = recorded_input_snapshot(latex_root / 'main.tex')
                    if (source_snapshot['source_bundle_sha256'] != compile_report.get('source_bundle_sha256')
                            or input_snapshot['actual_input_files'] != compile_report.get('actual_input_files')):
                        issues.append('B2证明输入在提交包验证期间变化')
                    for field in (source_snapshot['source_files'], input_snapshot['actual_input_files']):
                        for entry in field:
                            relative = 'final_latex/' + entry['path']
                            raw_hash = _sha256_stream(root / relative)
                            if relative in project_read_set and project_read_set[relative] != raw_hash:
                                issues.append(f'B2读集与编译证明输入冲突: {relative}')
                            project_read_set[relative] = raw_hash
                    if source_bundle_snapshot(latex_root / 'main.tex') != source_snapshot:
                        issues.append('B2 LaTeX source bundle在提交包验证期间变化')
                    recorder_path = latex_root / input_snapshot['recorder']
                    if recorder_path.is_file():
                        project_read_set['final_latex/' + input_snapshot['recorder']] = _sha256_stream(recorder_path)
                    log_path = latex_root / str(compile_report.get('log') or 'main.log')
                    if log_path.is_file() and log_path.resolve().is_relative_to(root):
                        project_read_set[log_path.resolve().relative_to(root).as_posix()] = _sha256_stream(log_path)
                    if _sha256_stream(SKILL_ROOT / skill_profile) != profile_before:
                        issues.append('编译profile在提交包验证期间变化')
                except (OSError, ValueError, TypeError, KeyError) as exc:
                    issues.append('B2编译证明输入无法复核: ' + str(exc))

    try:
        package.relative_to(root)
    except ValueError:
        issues.append("正式提交包必须位于当前项目目录内")

    if not package.is_file():
        return finish({"status": "failed", "kind": None, "issues": sorted(set([*issues, f"提交包不存在: {package}"])), "warnings": []})
    try:
        package_hash = _sha256_stream(package)
        archive = zipfile.ZipFile(package)
    except Exception as exc:  # noqa: BLE001
        return finish({"status": "failed", "kind": None, "issues": sorted(set([*issues, f"无法打开提交ZIP: {exc}"])), "warnings": []})

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
            else:
                current_hash = sha256_file(current)
                if current_hash != archived_hash:
                    issues.append(f"提交包文件不是当前项目版本: {relative}")
                else:
                    if claim_gate['status'] == 'passed':
                        if relative in project_read_set and project_read_set[relative] != current_hash:
                            issues.append(f"B2读集与提交包项目文件版本冲突: {relative}")
                        project_read_set[relative] = current_hash

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
            if claim_gate['status'] == 'passed' and compiled_pdf.is_relative_to(root):
                relative_pdf = compiled_pdf.relative_to(root).as_posix()
                if relative_pdf in project_read_set and project_read_set[relative_pdf] != current_pdf_hash:
                    issues.append(f"B2读集与当前compiled_pdf版本冲突: {relative_pdf}")
                project_read_set[relative_pdf] = current_pdf_hash
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
                    try:
                        expected = expand_allowlist(root, patterns)
                    except ValueError as exc:
                        issues.append(str(exc))
                        expected = set()
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
            required, requirement_issues = reproducibility_requirements(root, state)
            issues.extend(requirement_issues)
            for relative in sorted(required - archived_payload):
                issues.append(f"完整复现包缺少当前必需文件: {relative}")

    return finish({
        "status": "passed" if not issues else "failed",
        "kind": str(manifest.get("kind", "")) if manifest else None,
        "issues": sorted(set(issues)),
        "warnings": sorted(set(warnings)),
    })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", nargs="?", default=".")
    parser.add_argument("--package", default=None, help="package path; defaults to state.artifacts.submission_package or the unique submission ZIP")
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
