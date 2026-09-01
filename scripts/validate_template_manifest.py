from __future__ import annotations

import argparse
import hashlib
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _strip_tex_comments(text: str) -> str:
    active_lines: list[str] = []
    for line in text.splitlines():
        out: list[str] = []
        escaped = False
        for char in line:
            if char == "%" and not escaped:
                break
            out.append(char)
            if char == "\\":
                escaped = not escaped
            else:
                escaped = False
        active_lines.append("".join(out))
    return "\n".join(active_lines)


def validate_template_manifest(path: str | Path) -> list[str]:
    manifest_path = _resolve_manifest_path(path)
    errors: list[str] = []

    if not manifest_path.exists():
        return [f"manifest not found: {manifest_path}"]

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    template_root = manifest_path.parent

    if manifest.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0 for v8")
    if manifest.get("authoring_execution_pointer") != (
        "core/writing_runtime_contract.yaml#template_first_progressive_authoring"
    ):
        errors.append("template must delegate authoring timing to template_first_progressive_authoring")
    forbidden_template_authority = set(
        (manifest.get("authority_boundary", {}) or {}).get("forbidden_template_authority", [])
    )
    for forbidden in (
        "generate_body_during_template_inspection",
        "replace_progressive_chapter_authoring_order",
    ):
        if forbidden not in forbidden_template_authority:
            errors.append(f"template authority boundary missing: {forbidden}")

    canonical = manifest.get("canonical_template", {})
    entry = canonical.get("entry")
    entry_path: Path | None = None
    if not entry:
        errors.append("canonical_template.entry is required")
    else:
        entry_path = template_root / entry
        if not entry_path.exists():
            errors.append(f"canonical template entry missing: {entry}")

    for key in ("external_reference_exemplar", "framework_reference"):
        reference = canonical.get(key)
        status = canonical.get(key.replace("exemplar", "status")) if key == "external_reference_exemplar" else canonical.get("framework_reference_status")
        if status in {"imported_verified", "adapted_verified"}:
            if not reference:
                errors.append(f"{key} must be declared when status is {status}")
            elif not (template_root / reference).exists():
                errors.append(f"verified reference missing: {reference}")

    provenance = manifest.get("reference_provenance", {}) or {}
    for record_name, path_key in (
        ("user_template_source", "stored_adaptation"),
        ("framework_source", "stored_notes"),
    ):
        record = provenance.get(record_name, {}) or {}
        relative = record.get(path_key)
        expected = str(record.get("stored_sha256", "")).lower()
        if not relative or not expected:
            errors.append(f"reference_provenance.{record_name} requires {path_key} and stored_sha256")
            continue
        stored = template_root / relative
        if not stored.is_file():
            errors.append(f"stored reference missing: {relative}")
        elif _sha256(stored) != expected:
            errors.append(f"stored reference sha256 mismatch: {relative}")

    skeleton = manifest.get("paper_skeleton", {}).get("ordered_slots", [])
    for slot in skeleton:
        pattern = slot.get("source_pattern")
        if pattern:
            matches = sorted(template_root.glob(pattern))
            if slot.get("required") and not matches:
                errors.append(f"required repeatable template source missing: {pattern}")
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
            errors.append(f"declared template source missing: {source}")

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

    for example_spec in checks.get("optimization_examples", []):
        source = example_spec.get("source")
        token = example_spec.get("objective_token")
        example_path = template_root / str(source or "")
        if not source or not example_path.is_file():
            errors.append(f"optimization example missing: {source}")
            continue
        example_text = example_path.read_text(encoding="utf-8")
        objective = example_text.find(str(token or ""))
        constraints = example_text.find(r"\text{s.t.}\quad")
        brace = example_text.find(r"\left\{", constraints if constraints >= 0 else 0)
        if objective < 0 or constraints < 0 or objective >= constraints:
            errors.append(f"objective must appear before constraints: {source}")
        if brace < 0 or not (objective < constraints < brace):
            errors.append(f"objective must remain outside the constraints brace: {source}")

    question_contract = manifest.get("cumcm_question_section", {}) or {}
    maintained_examples = question_contract.get("maintained_examples", []) or []
    if len(maintained_examples) < 3:
        errors.append("cumcm_question_section must maintain Q1/Q2/Q3 examples")
    for example_spec in maintained_examples:
        source = str(example_spec.get("source", ""))
        number = str(example_spec.get("question_number", ""))
        example_path = template_root / source
        if not source or not example_path.is_file():
            errors.append(f"maintained question example missing: {source}")
            continue
        example_text = example_path.read_text(encoding="utf-8")
        expected_title = rf"\section{{问题{number}模型建立及求解}}"
        if not number or expected_title not in example_text:
            errors.append(f"maintained question title drifted: {source}")
        for functional_token in ("模型建立", "模型求解", "求解结果", "结果的分析与验证"):
            if functional_token not in example_text:
                errors.append(f"maintained question capability missing {functional_token}: {source}")

    if entry_path and entry_path.exists():
        main_text = entry_path.read_text(encoding="utf-8")
        for token in checks.get("required_main_tokens", []):
            if token not in main_text:
                errors.append(f"required main template token missing: {token}")
        active_main = _strip_tex_comments(main_text)
        for token in checks.get("optional_default_inactive_tokens", []):
            if token in active_main:
                errors.append(f"optional template slot must be inactive by default: {token}")
        last_position = -1
        for token in checks.get("active_main_order", []):
            position = active_main.find(token)
            if position < 0:
                errors.append(f"active main template token missing: {token}")
            elif position <= last_position:
                errors.append(f"active main template order drifted at: {token}")
            else:
                last_position = position

    evaluation_slot = next(
        (slot for slot in skeleton if slot.get("id") == "evaluation" and slot.get("source")),
        None,
    )
    required_evaluation_token = checks.get("required_evaluation_token")
    if evaluation_slot and required_evaluation_token:
        evaluation_path = _tex_path(template_root, evaluation_slot["source"])
        if not evaluation_path.exists():
            errors.append(f"evaluation source missing: {evaluation_slot['source']}")
        elif required_evaluation_token not in evaluation_path.read_text(encoding="utf-8"):
            errors.append(f"required evaluation token missing: {required_evaluation_token}")

    title_pattern = question_contract.get("title_pattern")
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
