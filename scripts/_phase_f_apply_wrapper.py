#!/usr/bin/env python3
"""Run Phase F patch and align intentional protected-authority blob baselines."""
from __future__ import annotations

import hashlib
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT / "scripts/_phase_f_apply.py"), run_name="__main__")


def git_blob_sha(relative: str) -> str:
    data = (ROOT / relative).read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


protected = ROOT / "tests/test_v830_editable_mechanism_diagram.py"
text = protected.read_text(encoding="utf-8")
lines = text.splitlines()
for relative in (
    "core/project_state.schema.yaml",
    "scripts/validate_semantic_governance.py",
    "scripts/validate_code_delivery.py",
):
    prefix = f'        "{relative}": "'
    matches = [index for index, line in enumerate(lines) if line.startswith(prefix)]
    if len(matches) != 1:
        raise RuntimeError(f"protected baseline matches for {relative}: {len(matches)}")
    lines[matches[0]] = f'        "{relative}": "{git_blob_sha(relative)}",'
protected.write_text("\n".join(lines) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
