#!/usr/bin/env python3
"""One-shot v7.5.0 release finalizer.

This helper is created only on the release-prep branch. The release workflow removes it
before committing the final tree, so it is not part of the active Skill after release.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = "7.4.5"
NEW = "7.5.0"
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".py", ".tex", ".m", ".bib"}
EXCLUDED_NAMES = {
    "CHANGELOG.md",
    "MANIFEST.sha256",
    "SKILL_FILE_INDEX.md",
    "TEMPLATE_INDEX.md",
    "HSK_SKILL_FILE_INDEX_V622.md",
    "HSK_TEMPLATE_INDEX_V622.md",
    "_release_v750_once.py",
}
EXCLUDED_PATHS = {
    Path(".github/workflows/refresh-generated.yml"),
}


def iter_text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        rel = path.relative_to(ROOT)
        if path.name in EXCLUDED_NAMES or rel in EXCLUDED_PATHS:
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def replace_release_markers() -> list[str]:
    changed: list[str] = []
    for path in iter_text_files():
        text = path.read_text(encoding="utf-8-sig")
        if OLD not in text:
            continue
        updated = text.replace(OLD, NEW)
        path.write_text(updated, encoding="utf-8")
        changed.append(str(path.relative_to(ROOT)))
    return changed


def update_changelog() -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8-sig")
    marker = "## Current release: 7.4.5"
    if marker not in text:
        if "## Current release: 7.5.0" in text:
            return
        raise RuntimeError("CHANGELOG current-release marker not found")
    release = """## Current release: 7.5.0

- Added a cross-competition writing-reasoning contract centered on **Source → Derivation → Destination**: every core formula must recover its problem/definition/mechanism/theory source, preserve the modeling-relevant derivation, and state its downstream use in state definition, objectives, constraints, decisions, reduction, validation or the final answer.
- Added adaptive shared-foundation and cross-question progression rules. Shared equations/geometry/probability/network structure are defined once only when reuse is substantial; dependent questions explain inherited structure, new objects/conditions, changed difficulty and solver/model increments, while independent questions remain independent.
- Added a structure-before-algorithm gate for high-dimensional, nonlinear and combinatorial models: analytic relations, monotonicity/convexity/symmetry, elimination/dimension reduction, candidate bounds, decomposition/hierarchy and prior-question search restrictions are checked before selecting advanced metaheuristics or learning methods.
- Added evidence requirements for numerical choices such as step size, grid resolution, discretization count, Monte Carlo/Bootstrap size, lag/window, search resolution and optimization tolerance. Parameter choices now require prompt provenance or convergence/validation/stability evidence rather than a generic “accuracy versus efficiency” sentence.
- Extended multi-method validation from numerical agreement alone to task-appropriate structural agreement such as decision ranges, active constraints, strategy structure, coefficient direction, ranking, clustering or key regions.
- Distilled the writing style into **evidence-driven undergraduate academic prose**: concrete objects and current mathematical difficulties lead into the mathematical treatment and its next use. Natural connectors such as “根据/因此/进一步/从而” remain legitimate and are reviewed only when mechanically repeated or logically empty.
- Strengthened proposition governance so a proof states its downstream model/computational consequence instead of ending at “命题得证”. Paragraph-first proof organization from v7.4.5 remains unchanged.
- Extended `scripts/audit_paper_prose.py` with conservative warning-only checks for dense formula runs, repeated derivation connectors, excessive meta-navigation, background-management paragraphs and suspicious unsupported numerical assignments. The audit explicitly does **not** infer mathematical correctness, true formula provenance or parameter optimality from regex.
- Added v7.5.0 regression coverage for cross-competition applicability, route-specific loading, formula-chain closure, shared foundations, cross-question increments, numerical-parameter evidence, natural prose and machine-audit boundaries. Numerical models, preprocessing APIs, workbook schemas, Python/MATLAB ownership and per-question five-file interfaces remain unchanged.

## Previous release: 7.4.5"""
    text = text.replace(marker, release, 1)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    changed = replace_release_markers()
    update_changelog()
    print(f"Updated {len(changed)} release-marker files from {OLD} to {NEW}.")
    for item in changed:
        print(f"- {item}")
    print("- CHANGELOG.md")


if __name__ == "__main__":
    main()
