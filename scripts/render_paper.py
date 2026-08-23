#!/usr/bin/env python3
"""Compile an existing LaTeX project using repository compile profiles.

Formal compilation first creates a strict project audit attestation, then compiles with
the selected profile and binds the resulting PDF to the audit, source bundle and profile
fingerprint in compile_report.yaml. Template smoke mode is explicit and cannot satisfy
formal delivery verification.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Mapping

import yaml

from audit_latex_project import audit_project, write_audit_report
from audit_paper_prose import overall_status
from latex_delivery import write_compile_report
from prepare_cumcm_class import patch_cumcm_class

ROOT = Path(__file__).resolve().parent.parent
PROFILE_FILE = ROOT / "core" / "compile_profiles.yaml"
CUMCM_CLASS_SOURCE = ROOT / "templates" / "latex" / "cumcm" / "cumcmthesis" / "cumcmthesis.cls"
AUX_SUFFIXES = (
    ".aux", ".bcf", ".bbl", ".blg", ".run.xml", ".out", ".toc",
    ".lof", ".lot", ".log", ".synctex.gz", ".fdb_latexmk", ".fls",
)


def run(command: list[str], cwd: Path) -> None:
    executable = command[0]
    if not shutil.which(executable):
        raise SystemExit(f"required executable not found: {executable}")
    print("$", " ".join(command))
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout)
    if result.returncode:
        if result.stderr:
            print(result.stderr)
        raise SystemExit(result.returncode)


def load_profiles() -> dict[str, dict[str, Any]]:
    if not PROFILE_FILE.is_file():
        raise SystemExit(f"compile profile file not found: {PROFILE_FILE}")
    payload = yaml.safe_load(PROFILE_FILE.read_text(encoding="utf-8")) or {}
    profiles = payload.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise SystemExit("compile_profiles.yaml does not define profiles")
    return profiles


def resolve_profile_name(requested: str | None, profiles: dict[str, dict[str, Any]]) -> str | None:
    if requested is None:
        return None
    token = requested.strip().lower()
    for name, config in profiles.items():
        aliases = [str(item).lower() for item in config.get("aliases", [])]
        if token == name.lower() or token in aliases:
            return name
    valid = ", ".join(sorted(profiles))
    raise SystemExit(f"unknown compile profile: {requested}; choose one of {valid}")


def resolve_main(
    project: Path,
    main_name: str | None,
    profile: Mapping[str, Any] | None = None,
) -> Path:
    if main_name:
        main = project / main_name
        if not main.is_file():
            raise SystemExit(f"main tex not found: {main}")
        return main

    candidates: list[Path] = []
    if profile:
        for key in ("project_main", "template_main"):
            value = profile.get(key)
            if value:
                candidates.append(project / str(value))
        candidates.extend(project / str(name) for name in profile.get("main_aliases", []))
    candidates.extend(project / name for name in ("main.tex", "paper.tex", "hsk_main.tex"))
    detected = [path for path in dict.fromkeys(candidates) if path.is_file()]
    if detected:
        return detected[0]
    tex_files = sorted(project.glob("*.tex"))
    if len(tex_files) != 1:
        raise SystemExit("cannot uniquely identify main .tex; use --main")
    return tex_files[0]


def _strip_tex_comments(text: str) -> str:
    return "\n".join(re.sub(r"(?<!\\)%.*$", "", line) for line in text.splitlines())


def detect_tex_requirements(main: Path) -> dict[str, bool]:
    text = _strip_tex_comments(main.read_text(encoding="utf-8", errors="ignore"))
    lowered = text.lower()
    return {
        "cumcm": "cumcmthesis" in lowered,
        "mcm": "mcmthesis" in lowered or "mcm/summary" in lowered,
        "needs_xetex": any(token in lowered for token in ("fontspec", "xecjk", "ctexart", "ctexrep", "ctexbook")),
        "uses_biber": "addbibresource" in lowered or "usepackage{biblatex}" in lowered,
        "uses_bibtex": "\\bibliography{" in lowered or "usepackage{natbib}" in lowered,
    }


def infer_profile(main: Path, profiles: dict[str, dict[str, Any]]) -> str:
    requirements = detect_tex_requirements(main)
    lowered_path = main.as_posix().lower()
    if requirements["cumcm"] or "cumcm" in lowered_path:
        candidate = "cumcm"
    elif requirements["mcm"] or re.search(r"(^|[/_-])(mcm|icm)([/_.-]|$)", lowered_path):
        candidate = "mcm_icm"
    elif "diangong" in lowered_path or "电工" in main.as_posix():
        candidate = "diangong"
    else:
        raise SystemExit(
            "cannot safely infer compile profile; specify --profile. "
            "Unknown LaTeX projects must not default to MCM/ICM."
        )

    if candidate not in profiles:
        raise SystemExit(f"inferred profile is unavailable: {candidate}")
    config = profiles[candidate]
    engine = str(config.get("engine", "")).lower()
    bibliography = str(config.get("bibliography", "none")).lower()
    if requirements["needs_xetex"] and engine not in {"xelatex", "lualatex"}:
        raise SystemExit(f"profile {candidate} uses {engine}, but the document requires a Unicode/CJK engine")
    if requirements["uses_biber"] and bibliography != "biber":
        raise SystemExit(f"profile {candidate} uses {bibliography}, but the document loads biblatex/Biber")
    if requirements["uses_bibtex"] and not requirements["uses_biber"] and bibliography == "biber":
        raise SystemExit(f"profile {candidate} uses Biber, but the document declares a BibTeX-style bibliography")
    return candidate


def prepare_profile_files(project: Path, profile_name: str) -> None:
    """Materialize audited local template dependencies and apply narrow patches."""
    if profile_name != "cumcm":
        return
    class_file = project / "cumcmthesis.cls"
    if not class_file.is_file():
        if not CUMCM_CLASS_SOURCE.is_file():
            raise SystemExit(f"CUMCM class source missing: {CUMCM_CLASS_SOURCE}")
        shutil.copyfile(CUMCM_CLASS_SOURCE, class_file)
        print(f"materialized CUMCM class: {class_file}")
    changed = patch_cumcm_class(class_file)
    if changed:
        print(f"patched CUMCM font fallback: {class_file}")


def clean_auxiliary(project: Path, stem: str) -> None:
    for path in project.iterdir():
        if not path.is_file() or not path.name.startswith(stem):
            continue
        if any(path.name.endswith(suffix) for suffix in AUX_SUFFIXES):
            path.unlink()


def engine_command(engine: str, main_name: str) -> list[str]:
    return [engine, "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", main_name]


def compile_project(
    project: Path,
    main: Path,
    config: dict[str, Any],
    engine_override: str | None,
    bibliography_override: str | None,
    runs_override: int | None,
) -> list[str]:
    engine = engine_override or str(config.get("engine", "xelatex"))
    bibliography = bibliography_override or str(config.get("bibliography", "none"))
    sequence = [str(step) for step in config.get("sequence", [])]
    if engine_override or bibliography_override:
        sequence = [engine]
        if bibliography != "none":
            sequence.append(bibliography)
        sequence.extend([engine, engine])
    if runs_override is not None:
        if runs_override < 1:
            raise SystemExit("--runs must be at least 1")
        sequence = [engine] * runs_override
        if bibliography != "none" and runs_override >= 2:
            sequence.insert(1, bibliography)
    if not sequence:
        raise SystemExit("selected compile profile has an empty sequence")

    for step in sequence:
        if step in {"xelatex", "pdflatex", "lualatex"}:
            run(engine_command(step, main.name), project)
        elif step == "biber":
            run(["biber", main.stem], project)
        elif step == "bibtex":
            run(["bibtex", main.stem], project)
        else:
            raise SystemExit(f"unsupported compile step: {step}")

    pdf = project / f"{main.stem}.pdf"
    if not pdf.is_file():
        raise SystemExit("compile sequence finished but PDF is missing")
    print(pdf)
    return sequence


def create_audit_attestation(project: Path, main_tex: Path, *, template_smoke: bool) -> Path:
    framework = None if template_smoke else project.parent / "模型论文框架.md"
    if not template_smoke and not framework.is_file():
        raise SystemExit(f"formal LaTeX compile requires current framework: {framework}")
    findings = audit_project(
        main_tex,
        framework_path=framework,
        require_framework=not template_smoke,
    )
    status = overall_status(findings)
    report_path = project / "latex_audit_report.yaml"
    write_audit_report(
        main_file=main_tex,
        findings=findings,
        framework_path=framework,
        report_path=report_path,
        mode="template_smoke" if template_smoke else "formal",
    )
    if status == "blocking" or (not template_smoke and status == "review_required"):
        raise SystemExit(f"LaTeX project audit failed with status={status}; see {report_path}")
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", nargs="?", default="final_latex")
    parser.add_argument("--main", default=None, help="main tex filename; profile-driven autodetection if omitted")
    parser.add_argument("--profile", default=None, help="compile profile name")
    parser.add_argument("--competition", default=None, help="compatibility alias for --profile")
    parser.add_argument("--engine", choices=["xelatex", "pdflatex", "lualatex"], default=None)
    parser.add_argument("--bibliography", choices=["biber", "bibtex", "none"], default=None)
    parser.add_argument("--bibtex", action="store_true", help="compatibility flag; use BibTeX")
    parser.add_argument("--runs", type=int, default=None, help="override with repeated engine runs")
    parser.add_argument("--clean", action="store_true", help="remove auxiliary files before compiling")
    parser.add_argument(
        "--template-smoke",
        action="store_true",
        help="repository template CI mode; does not produce a formal-delivery attestation",
    )
    parser.add_argument(
        "--attest-existing",
        action="store_true",
        help="template-smoke only: attest PDF/log produced by an external compile action",
    )
    args = parser.parse_args()

    if args.attest_existing and not args.template_smoke:
        raise SystemExit("--attest-existing is restricted to --template-smoke and cannot certify formal delivery")

    project = Path(args.project).resolve()
    if not project.is_dir():
        raise SystemExit(f"project directory not found: {project}")
    profiles = load_profiles()
    requested = args.profile or args.competition
    profile_name = resolve_profile_name(requested, profiles)
    main_tex = resolve_main(project, args.main, profiles.get(profile_name) if profile_name else None)
    profile_name = profile_name or infer_profile(main_tex, profiles)
    profile_config = profiles[profile_name]
    prepare_profile_files(project, profile_name)
    if args.clean and not args.attest_existing:
        clean_auxiliary(project, main_tex.stem)

    audit_report = create_audit_attestation(project, main_tex, template_smoke=args.template_smoke)
    bibliography = "bibtex" if args.bibtex else args.bibliography
    effective_engine = args.engine or str(profile_config.get("engine", "xelatex"))
    effective_bibliography = bibliography or str(profile_config.get("bibliography", "none"))
    print(f"compile profile: {profile_name}")
    print(f"main tex: {main_tex.name}")

    if args.attest_existing:
        sequence = [str(step) for step in profile_config.get("sequence", [])]
    else:
        sequence = compile_project(project, main_tex, profile_config, args.engine, bibliography, args.runs)

    report = write_compile_report(
        project=project,
        main=main_tex,
        profile=profile_name,
        engine=effective_engine,
        bibliography=effective_bibliography,
        sequence=sequence,
        profile_config=profile_config,
        audit_report_path=audit_report,
        attestation_mode="template_smoke" if args.template_smoke else "formal",
    )
    print(f"compile report: {project / 'compile_report.yaml'}")
    if report["status"] != "passed":
        raise SystemExit("compile attestation failed; see compile_report.yaml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
