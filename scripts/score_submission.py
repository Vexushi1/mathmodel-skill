#!/usr/bin/env python3
"""Score a modeling submission using config/review_weights.json."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "review_weights.json"


def load_payload(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return yaml.safe_load(text) or {}


def score_submission(config: Mapping[str, Any], report: Mapping[str, Any]) -> dict[str, Any]:
    dimensions = config.get("dimensions", {})
    weights = {name: float(item["weight"]) for name, item in dimensions.items()}
    if abs(sum(weights.values()) - 1.0) > 1e-9:
        raise ValueError("review weights must sum to 1")

    supplied = report.get("scores", {})
    missing = [name for name in dimensions if name not in supplied]
    unknown = [name for name in supplied if name not in dimensions]
    if missing:
        raise ValueError(f"missing dimension scores: {missing}")
    if unknown:
        raise ValueError(f"unknown dimension scores: {unknown}")

    normalized: dict[str, float] = {}
    contributions: dict[str, float] = {}
    for name, value in supplied.items():
        score = float(value)
        if not 0 <= score <= float(config.get("scale", 100)):
            raise ValueError(f"score out of range for {name}: {score}")
        normalized[name] = score
        contributions[name] = score * weights[name]

    declared_hard_fail = set(report.get("hard_fail", []))
    allowed_hard_fail = set(config.get("hard_fail", []))
    invalid_hard_fail = sorted(declared_hard_fail - allowed_hard_fail)
    if invalid_hard_fail:
        raise ValueError(f"unknown hard-fail codes: {invalid_hard_fail}")

    total = round(sum(contributions.values()), 4)
    rejected = bool(declared_hard_fail)
    return {
        "version": config.get("version"),
        "total": total,
        "scale": config.get("scale", 100),
        "status": config.get("hard_fail_action") if rejected else "scored",
        "hard_fail": sorted(declared_hard_fail),
        "scores": normalized,
        "weighted_contributions": {name: round(value, 4) for name, value in contributions.items()},
        "evidence": report.get("evidence", {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", help="YAML/JSON file containing scores, evidence and optional hard_fail codes")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--output")
    args = parser.parse_args()
    result = score_submission(load_payload(Path(args.config)), load_payload(Path(args.report)))
    rendered = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")
    return 2 if result["hard_fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
