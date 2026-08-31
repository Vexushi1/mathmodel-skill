from __future__ import annotations

import argparse
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _resolve_manifest_path(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    return candidate.resolve()


def _tex_path(template_root: Path, source: str) -> Path:
    path = template_root / source
    if path.suffix:
        return path
    return path.with_suffix(".tex")


def validate_template_manifest(path: str | Path) -> list[str]:
    manifest_path = _resolve_manifest_path(path)
    errors: list[str] = []

    if not manifest_path.exists():
        return [f"manifest not found: {manifest_path}"]

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    template_root = manifest_path.parent

    if manifest.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0 for v8 Phase 1")

    canonical = manifest.get("canonical_template", {})
    entry = canonical.get("entry")
    if not entry:
        errors.append("canonical_template.entry is required")
    else:
        entry_path = template_root / entry
        if not entry_path.exists():
            errors.append(f"canonical template entry missing: {entry}")

    skeleton = manifest.get("paper_skeleton", {}).get("ordered_slots", [])
    for slot in skeleton:
        if not slot.get("required"):
            continue
        source = slot.get("source")
        if not source:
            continue
        source_path = template_root / source
        if source_path.suffix == ".bib":
            resolved = source_path
        else:
            resolved = _tex_path(template_root, source)
        if not resolved.exists():
            errors.append(f"required template source missing: {source}")

    checks = manifest.get("fixed_template_checks", {})
    example = checks.get("question_example")
    if not example:
        errors.append("fixed_template_checks.question_example is required")
        return errors

    question_path = template_root / example
    if not question_path.exists():
        errors.append(f"question example missing: {example}")
        return errors

    text = question_path.read_text(encoding="utf-8")
    for token in checks.get("required_question_tokens", []):
        if token not in text:
            errors.append(f"required question token missing: {token}")

    for token in checks.get("forbidden_question_tokens", []):
        if token in text:
            errors.append(f"forbidden question token present: {token}")

    if checks.get("objective_before_constraints"):
        objective = text.find(r"\min_{\mathbf{x}}")
        constraints = text.find(r"\text{s.t.}\quad")
        if objective < 0 or constraints < 0 or objective >= constraints:
            errors.append("objective must appear before constraints in the question template")

    if checks.get("objective_outside_constraint_brace"):
        objective = text.find(r"\min_{\mathbf{x}}")
        constraints = text.find(r"\text{s.t.}\quad")
        brace = text.find(r"\left\{", constraints if constraints >= 0 else 0)
        if objective < 0 or constraints < 0 or brace < 0:
            errors.append("objective/constraints/brace structure is incomplete")
        elif not (objective < constraints < brace):
            errors.append("objective must remain outside the constraints brace")

    title_pattern = manifest.get("cumcm_question_section", {}).get("title_pattern")
    if title_pattern != "问题{N}模型建立及求解":
        errors.append("CUMCM question title pattern drifted from 问题{N}模型建立及求解")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate deterministic synchronization between the HSK CUMCM Template Manifest and template files."
    )
    parser.add_argument(
        "manifest",
        nargs="?",
        default="templates/latex/cumcm/hsk/template_manifest.yaml",
    )
    args = parser.parse_args()

    errors = validate_template_manifest(args.manifest)
    if errors:
        print("Template manifest validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Template manifest validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
