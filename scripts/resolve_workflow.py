#!/usr/bin/env python3
"""Resolve one user intent into an ordered, deduplicated HSK load plan."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parent.parent
ROUTER_PATH = ROOT / "core" / "workflow_router.yaml"
COMPETITION_PATH = ROOT / "config" / "competition_profiles.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def unique(items: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(str(item) for item in items if str(item).strip()))


def resolve_competition_pack(token: str | None, profiles: dict[str, Any]) -> str | None:
    if not token:
        return None
    normalized = token.strip().lower()
    for name, config in profiles.get("profiles", {}).items():
        aliases = [name, *config.get("aliases", [])]
        if normalized in {str(item).lower() for item in aliases}:
            return config.get("stable", {}).get("competition_pack")
    raise ValueError(f"unknown competition: {token}")


def resolve_workflow(
    intent: str,
    *,
    primary: str | None = None,
    secondary: Iterable[str] = (),
    competition: str | None = None,
    router_path: Path = ROUTER_PATH,
    competition_path: Path = COMPETITION_PATH,
) -> dict[str, Any]:
    router = load_yaml(router_path)
    route = router.get("routing", {}).get(intent)
    if not isinstance(route, dict):
        valid = ", ".join(sorted(router.get("routing", {})))
        raise ValueError(f"unknown intent: {intent}; choose one of {valid}")

    classifier = router.get("classifier_contract", {})
    allowed = set(classifier.get("allowed_labels", []))
    labels = unique(([primary] if primary else []) + list(secondary))
    if len(labels) > 3:
        raise ValueError("one request may load at most one primary and two secondary task packs")
    unknown = [label for label in labels if label not in allowed]
    if unknown:
        raise ValueError(f"unknown task labels: {unknown}")
    if route.get("load_classified_task_packs") and not primary:
        raise ValueError(f"intent {intent} requires a primary task label")

    paths = [*router.get("default_load", []), *route.get("load", [])]
    if route.get("load_competition_pack"):
        pack = resolve_competition_pack(competition, load_yaml(competition_path))
        paths.append(pack or "packs/competition/auto.md")
    if route.get("load_classified_task_packs"):
        paths.extend(f"packs/task/{label}.md" for label in labels)
    paths.extend(route.get("then", []))

    ordered = unique(paths)
    return {
        "version": router.get("version"),
        "intent": intent,
        "primary": primary,
        "secondary": [label for label in labels if label != primary],
        "modules": [item for item in ordered if item.startswith("modules/")],
        "packs": [item for item in ordered if item.startswith("packs/")],
        "templates": [item for item in ordered if item.startswith("templates/")],
        "contracts": [item for item in ordered if item.startswith("core/")],
        "load_order": ordered,
        "terminal_outputs": route.get("terminal_outputs", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("intent")
    parser.add_argument("--primary")
    parser.add_argument("--secondary", nargs="*", default=[])
    parser.add_argument("--competition")
    args = parser.parse_args()
    try:
        plan = resolve_workflow(
            args.intent,
            primary=args.primary,
            secondary=args.secondary,
            competition=args.competition,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
