#!/usr/bin/env python3
"""Finalize the validated v6.5.0 repair and remove temporary migration assets."""
from __future__ import annotations

from pathlib import Path

import fix_v650_structure_once as repair

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    repair.fix_pipeline()
    repair.write_router()
    repair.write_manifest()
    repair.validate()
    repair.WORKFLOW.write_text(repair.ORIGINAL_WORKFLOW, encoding="utf-8", newline="\n")
    for relative in (
        "scripts/fix_v650_structure_once.py",
        "scripts/finalize_v650_structure.py",
        "legacy/.v650-structure-repair-trigger",
    ):
        path = ROOT / relative
        if path.exists():
            path.unlink()
    print("v6.5.0 structural repair finalized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
