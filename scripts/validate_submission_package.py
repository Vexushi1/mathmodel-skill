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
import os
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT / "scripts"))
from submission_requirements import current_analysis_artifacts, expand_required_allowlist, reproducibility_requirements
from safe_yaml import safe_load

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


def load_yaml(path: Path, *, observe=None) -> dict[str, Any]:
    if not path.is_file():
        return {}
    raw = path.read_bytes()
    if observe is not None:
        observe(path, raw)
    return safe_load(raw) or {}


def resolve_competition(token: str, payload: Mapping[str, Any]) -> tuple[str, Mapping[str, Any]]:
    normalized = token.strip().lower()
    profiles = payload.get("profiles") or {}
    if not isinstance(profiles, Mapping):
        raise ValueError('competition_profiles.yaml.profiles必须是映射结构')
    for name, config in profiles.items():
        if not isinstance(config, Mapping):
            raise ValueError(f'competition profile必须是映射结构: {name}')
        aliases = [name, *config.get("aliases", [])]
        if normalized in {str(item).lower() for item in aliases}:
            return str(name), config
    raise ValueError(f"unknown competition profile: {token}")


def expand_allowlist(root: Path, patterns: Iterable[str]) -> set[str]:
    return {path.relative_to(root.resolve()).as_posix() for path in expand_required_allowlist(root, patterns)}


def _current_compiled_pdf(root: Path, state: Mapping[str, Any]) -> Path:
    artifacts = state.get("artifacts") or {}
    framework = state.get("paper_framework")
    policy = framework.get("claim_consumption_policy") if isinstance(framework, Mapping) else None
    pair = ((policy.get("protocol_version"), policy.get("mode"))
            if isinstance(policy, Mapping) else None)
    source = policy.get("paper_source") if isinstance(policy, Mapping) else None
    if (pair == ("1.5.0", "enforce_selected_paper_claim_chain")
            and isinstance(source, Mapping) and source.get("format") == "latex"
            and isinstance(source.get("entrypoint"), str)):
        return (root / source["entrypoint"]).with_suffix(".pdf")
    declared = artifacts.get("compiled_pdf")
    if declared:
        return root / str(declared)
    return root / "final_latex/main.pdf"


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
    from project_transaction import _check_read_set, _guarded_path

    project_read_set: dict[str, str | None] = {}
    skill_read_set: dict[str, str | None] = {}
    observed = {'project': project_read_set, 'skill': skill_read_set}
    identities: dict[str, tuple[str, str]] = {}
    package_hash: str | None = None

    def remember(path: Path, digest: str | None, *, domain: str | None = None) -> None:
        """Keep the first byte observation, including observations from other gates."""
        try:
            if domain is not None and domain not in observed:
                raise ValueError('unknown observed source domain: ' + domain)
            candidate = Path(path)
            bases = ((domain, root if domain == 'project' else SKILL_ROOT.resolve()),) if domain else (
                ('project', root), ('skill', SKILL_ROOT.resolve()),
            )
            for source_domain, base in bases:
                absolute = candidate.absolute() if candidate.is_absolute() else base / candidate
                if absolute.is_relative_to(base):
                    relative = absolute.relative_to(base).as_posix()
                    canonical = _guarded_path(base, relative)
                    identity = os.path.normcase(str(canonical))
                    source_domain, relative = identities.setdefault(identity, (source_domain, relative))
                    destination = observed[source_domain]
                    if relative in destination and destination[relative] != digest:
                        issues.append('提交包验证首次观察与后续读集冲突: ' + relative)
                    else:
                        destination.setdefault(relative, digest)
                    return
            raise ValueError('observed source is outside the project and Skill roots: ' + str(path))
        except (OSError, ValueError, RuntimeError) as exc:
            issues.append('提交包验证读集路径无效: ' + str(exc))

    def observe(path: Path, raw: bytes) -> None:
        remember(path, sha256_bytes(raw))

    def observe_file(path: Path) -> bytes | None:
        raw = path.read_bytes() if path.is_file() else None
        remember(path, sha256_bytes(raw) if raw is not None else None)
        return raw

    def finish(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            if package_hash is not None and _sha256_stream(package) != package_hash:
                raise ValueError('提交ZIP在验证过程中发生变化')
            _check_read_set(root, project_read_set)
            _check_read_set(SKILL_ROOT.resolve(), skill_read_set)
        except (OSError, ValueError, RuntimeError) as exc:
            payload['issues'] = sorted(set([*payload['issues'], '提交包验证读集冲突: ' + str(exc)]))
        payload['issues'] = sorted(set([*payload['issues'], *issues]))
        if payload['issues']:
            payload['status'] = 'failed'
        return payload

    state_path = root / 'state/project_state.yaml'
    try:
        state_bytes = state_path.read_bytes() if state_path.is_file() else None
        state_hash = sha256_bytes(state_bytes) if state_bytes is not None else None
        remember(state_path, state_hash)
        state = (safe_load(state_bytes) or {}) if state_bytes is not None else {}
        if not isinstance(state, Mapping):
            raise ValueError('project_state.yaml必须是映射结构')
        if not isinstance(state.get('artifacts') or {}, Mapping):
            raise ValueError('project_state.yaml.artifacts必须是映射结构')
    except (OSError, ValueError, TypeError, UnicodeError, yaml.YAMLError) as exc:
        return finish({'status': 'failed', 'kind': None,
                       'issues': [*issues, '无法读取当前项目State: ' + str(exc)], 'warnings': []})

    # A direct invocation must replay the opt-in B2 gate and the formal proof
    # chain; a matching ZIP/PDF hash alone cannot certify changed claim sources.
    from claim_consumption import formal_figure_gate, formal_text_gate

    framework = state.get('paper_framework') if isinstance(state, Mapping) else None
    policy = framework.get('claim_consumption_policy') if isinstance(framework, Mapping) else None
    pair = ((policy.get('protocol_version'), policy.get('mode'))
            if isinstance(policy, Mapping) else None)
    selected_policy = pair == ('1.5.0', 'enforce_selected_paper_claim_chain')
    paper_source = policy.get('paper_source') if isinstance(policy, Mapping) else None
    carrier_format = (paper_source.get('format')
                      if selected_policy and isinstance(paper_source, Mapping) else 'latex')
    figure_policy = isinstance(policy, Mapping) and (
        policy.get('protocol_version') in {'1.3.0', '1.4.0'}
        or policy.get('mode') == 'enforce_latex_text_and_figure_chain'
        or (selected_policy and carrier_format == 'latex')
    )
    if selected_policy:
        from claim_consumption import formal_paper_gate
        claim_gate = formal_paper_gate(root)
    else:
        claim_gate = formal_figure_gate(root) if figure_policy else formal_text_gate(root)
    gate_label = '选定论文链' if selected_policy else 'Figure链' if figure_policy else '文本'
    gate_sources = claim_gate['observed_sources']
    if gate_sources['project'].get('state/project_state.yaml') != state_hash:
        issues.append('项目State首读与B2门读集不一致')
    for domain, rows in gate_sources.items():
        for relative, digest in rows.items():
            remember(Path(relative), digest, domain=domain)
    if isinstance(state, Mapping) and 'review_receipt_policy' in state:
        from review_receipt_consumption import evaluate_gate

        review_gate = evaluate_gate(root, gate='final_review_and_delivery')
        for domain, observed_rows in review_gate['observed_sources'].items():
            for relative, digest in observed_rows.items():
                remember(Path(relative), digest, domain=domain)
        if review_gate['status'] == 'failed':
            issues.extend('C2 final review receipt: ' + str(item)
                          for item in (review_gate['issues'] or [review_gate['status']]))
    if claim_gate['status'] == 'failed':
        issues.append(f'B2正式{gate_label}门未通过: ' + '; '.join(claim_gate['issues'][:8]))
    elif claim_gate['status'] == 'passed' and selected_policy and carrier_format == 'docx':
        issues.append(
            'B2 1.5.0选定DOCX载体缺少可验证的DOCX到正式PDF编译证明；submission失败关闭'
        )
    elif claim_gate['status'] == 'passed':
        from latex_delivery import recorded_input_snapshot, source_bundle_snapshot, verify_compile_report

        try:
            if selected_policy:
                latex_main = (root / str(paper_source['entrypoint'])).resolve()
            else:
                latex_main = (root / 'final_latex/main.tex').resolve()
            latex_root = latex_main.parent
            snapshot_options = ({
                'project_root': root,
                'allowed_external_graphics': {
                    row['image_token']: root / row['image_path']
                    for row in claim_gate['figure_graphic_bindings']
                },
            } if figure_policy else {})
            skill_profile = 'core/compile_profiles.yaml'
            profile_bytes = observe_file(SKILL_ROOT / skill_profile)
            profile_before = sha256_bytes(profile_bytes) if profile_bytes is not None else None
            if skill_profile in observed['skill'] and observed['skill'][skill_profile] != profile_before:
                issues.append('B2读集与编译profile版本冲突')
            compile_path = latex_root / 'compile_report.yaml'
            if not compile_path.is_file():
                issues.append('B2正式文本门要求当前compile_report.yaml证明')
            else:
                compile_report = load_yaml(compile_path, observe=observe)
                if not isinstance(compile_report, Mapping):
                    raise ValueError('B2正式文本门的compile_report.yaml结构无效')
                bound_audit = Path(str(compile_report.get('latex_audit_report') or 'latex_audit_report.yaml'))
                observe_file(bound_audit if bound_audit.is_absolute() else latex_root / bound_audit)
                for field in ('source_files', 'actual_input_files'):
                    entries = compile_report.get(field) or []
                    if not isinstance(entries, list):
                        raise ValueError('compile_report.' + field + '必须是列表')
                    for entry in entries:
                        if isinstance(entry, Mapping) and isinstance(entry.get('path'), str):
                            observe_file((root if figure_policy else latex_root) / entry['path'])
                for field, fallback in (('recorder', latex_main.with_suffix('.fls').name),
                                        ('log', latex_main.with_suffix('.log').name)):
                    observe_file(latex_root / str(compile_report.get(field) or fallback))
                observe_file(_current_compiled_pdf(root, state))
                issues.extend(verify_compile_report(
                    project=latex_root, main=latex_main,
                    pdf=_current_compiled_pdf(root, state), report=compile_report,
                ))
                source_snapshot = source_bundle_snapshot(latex_main, **snapshot_options)
                input_snapshot = recorded_input_snapshot(latex_main, **snapshot_options)
                if (source_snapshot['source_bundle_sha256'] != compile_report.get('source_bundle_sha256')
                        or input_snapshot['actual_input_files'] != compile_report.get('actual_input_files')):
                    issues.append('B2证明输入在提交包验证期间变化')
                for field in (source_snapshot['source_files'], input_snapshot['actual_input_files']):
                    for entry in field:
                        observe_file((root if figure_policy else latex_root) / entry['path'])
                if source_bundle_snapshot(latex_main, **snapshot_options) != source_snapshot:
                    issues.append('B2 LaTeX source bundle在提交包验证期间变化')
                recorder_path = latex_root / input_snapshot['recorder']
                observe_file(recorder_path)
                log_path = latex_root / str(
                    compile_report.get('log') or latex_main.with_suffix('.log').name
                )
                observe_file(log_path)
                if _sha256_stream(SKILL_ROOT / skill_profile) != profile_before:
                    issues.append('编译profile在提交包验证期间变化')
        except (OSError, ValueError, TypeError, KeyError, AttributeError, UnicodeError, yaml.YAMLError) as exc:
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
        archived_hashes: dict[str, str] = {}
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
            try:
                archived_hash = sha256_bytes(archive.read(relative))
            except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
                issues.append(f"无法读取ZIP声明文件: {relative}: {exc}")
                continue
            archived_hashes[relative] = archived_hash
            if archived_hash != recorded_hash:
                issues.append(f"ZIP中文件哈希与manifest不一致: {relative}")
            try:
                current = _guarded_path(root, relative)
            except (ValueError, RuntimeError):
                issues.append(f"manifest路径无效或越出项目根目录: {relative}")
                continue
            if not current.is_file():
                issues.append(f"manifest声明的项目文件当前不存在: {relative}")
            else:
                try:
                    current_bytes = observe_file(root / relative)
                except OSError as exc:
                    issues.append(f"无法读取manifest声明的项目文件: {relative}: {exc}")
                    continue
                if current_bytes is None:
                    issues.append(f"manifest声明的项目文件当前不存在: {relative}")
                    continue
                current_hash = sha256_bytes(current_bytes)
                if current_hash != archived_hash:
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
            try:
                current_pdf_bytes = observe_file(compiled_pdf)
                current_pdf_hash = sha256_bytes(current_pdf_bytes) if current_pdf_bytes is not None else None
            except OSError as exc:
                current_pdf_hash = None
                issues.append(f"无法读取当前正式编译PDF: {exc}")
            matching_pdf = [
                path for path in declared_paths
                if path.lower().endswith(".pdf")
                and path in names
                and current_pdf_hash is not None
                and archived_hashes.get(path) == current_pdf_hash
            ]
            if not matching_pdf:
                issues.append("提交包未包含与当前compiled_pdf哈希一致的PDF")

        if kind == "official":
            try:
                profile_payload = load_yaml(COMPETITION_PROFILES, observe=observe)
                if not isinstance(profile_payload, Mapping):
                    raise ValueError('competition_profiles.yaml必须是映射结构')
            except (OSError, ValueError, TypeError, UnicodeError, yaml.YAMLError) as exc:
                issues.append(f"无法读取当前competition profile: {exc}")
                profile_payload = {}
            token = competition or str(manifest.get("competition_profile") or (state.get("project") or {}).get("competition") or "")
            if not token:
                issues.append("official提交包缺少competition profile")
            else:
                try:
                    profile_name, profile = resolve_competition(token, profile_payload)
                except (ValueError, TypeError) as exc:
                    issues.append(str(exc))
                else:
                    rules = profile.get("edition_rules") or {}
                    if not isinstance(rules, Mapping):
                        issues.append(f"{profile_name} edition_rules必须是映射结构")
                        rules = {}
                    if rules.get("verification_status") != "verified":
                        issues.append(f"{profile_name}当届提交规则尚未verified，不能验证official package")
                    if not rules.get("verified_at") or not rules.get("source"):
                        issues.append(f"{profile_name} verified规则缺少verified_at/source证据")
                    raw_patterns = rules.get("submission_files") or []
                    if not isinstance(raw_patterns, list):
                        issues.append(f"{profile_name} submission_files必须是列表")
                        raw_patterns = []
                    patterns = [str(item) for item in raw_patterns]
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
            try:
                required, requirement_issues = reproducibility_requirements(root, state, observe=observe)
                issues.extend(requirement_issues)
                excluded, selection_issues = current_analysis_artifacts(
                    root, state, required_files=required, observe=observe,
                )
                issues.extend(selection_issues)
                for relative in sorted(archived_payload & excluded):
                    issues.append(f"复现包夹带当前State未启用的03B旧产物: {relative}")
                for relative in sorted(required - archived_payload):
                    issues.append(f"完整复现包缺少当前必需文件: {relative}")
            except (OSError, ValueError, TypeError, KeyError, AttributeError, UnicodeError, yaml.YAMLError) as exc:
                issues.append('无法读取当前完整复现包要求: ' + str(exc))

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
    if args.package:
        raw_package = Path(args.package)
        package = raw_package.resolve() if raw_package.is_absolute() else (root / raw_package).resolve()
    else:
        state = load_yaml(root / "state/project_state.yaml")
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
