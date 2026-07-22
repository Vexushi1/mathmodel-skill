#!/usr/bin/env python3
"""Resolve normalized internal review weights from a base profile and optional overlay."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
BASE_PATH = ROOT / "config" / "review_weights.json"
OVERLAY_PATH = ROOT / "config" / "review_overlays.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_weights(overlay_name: str | None = None) -> dict[str, float]:
    base = load_json(BASE_PATH)
    weights = {
        key: float(config["weight"])
        for key, config in base["dimensions"].items()
    }
    if overlay_name is None:
        return weights

    overlays = load_json(OVERLAY_PATH)["overlays"]
    if overlay_name not in overlays:
        valid = ", ".join(sorted(overlays))
        raise KeyError(f"unknown review overlay: {overlay_name}; choose one of {valid}")
    multipliers = overlays[overlay_name]["multipliers"]
    if set(multipliers) != set(weights):
        missing = sorted(set(weights) - set(multipliers))
        extra = sorted(set(multipliers) - set(weights))
        raise ValueError(f"overlay dimensions mismatch; missing={missing}, extra={extra}")

    adjusted = {key: weights[key] * float(multipliers[key]) for key in weights}
    total = sum(adjusted.values())
    if total <= 0:
        raise ValueError("review overlay produces non-positive total weight")
    return {key: value / total for key, value in adjusted.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overlay", default=None)
    args = parser.parse_args()
    print(json.dumps(resolve_weights(args.overlay), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
