#!/usr/bin/env python3
"""One-shot fixture correction for the Phase D characterization conversion."""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "tests" / "test_v900_refactor_characterization.py"
text = path.read_text(encoding="utf-8")
old = '''        "depends_on": [],
        "result_quality_status": "passed",
'''
new = '''        "depends_on": [],
        "model_challenge_status": "passed",
        "human_model_approval_status": "approved",
        "result_quality_status": "passed",
'''
if text.count(old) != 1:
    raise RuntimeError(f"expected one semantic_subproblem fixture insertion point, got {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Phase D approval-preservation fixture repaired")
