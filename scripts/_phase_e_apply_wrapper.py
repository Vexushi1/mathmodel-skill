#!/usr/bin/env python3
"""One-shot wrapper correcting integration-only migration/test anchors."""
from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
helper = ROOT / "scripts/_phase_e_apply.py"
text = helper.read_text(encoding="utf-8")
old = '''replace_all(
    "tests/test_v711_model_approval_gate.py",
    '            self.assertIn("model", ',
    '            self.assertIn("primary_code", ',
    2,
)
'''
new = '''replace_all(
    "tests/test_v711_model_approval_gate.py",
    '            self.assertIn("model", ',
    '            self.assertIn("primary_code", ',
    1,
)
'''
if text.count(old) != 1:
    raise RuntimeError(f"Phase E helper anchor changed: {text.count(old)}")
helper.write_text(text.replace(old, new, 1), encoding="utf-8")
runpy.run_path(str(helper), run_name="__main__")

# The second v7.11 assertion has class-level indentation and is patched separately.
target = ROOT / "tests/test_v711_model_approval_gate.py"
text = target.read_text(encoding="utf-8")
old = '        self.assertIn("model", entry["stale_layers"])\n'
new = '        self.assertIn("primary_code", entry["stale_layers"])\n'
if text.count(old) != 1:
    raise RuntimeError(f"remaining legacy stale-layer assertion count={text.count(old)}")
target.write_text(text.replace(old, new, 1), encoding="utf-8")

# Keep the expected hash inside the TemporaryDirectory lifetime in the new Phase E regression.
target = ROOT / "tests/test_v900_artifact_identity.py"
text = target.read_text(encoding="utf-8")
old = '''            updated = yaml.safe_load((root / "state" / "project_state.yaml").read_text(encoding="utf-8"))
        hashes = updated["subproblems"]["Q1"]["artifact_hashes"]
        self.assertEqual(hashes["primary_code"], hashlib.sha256(script.read_bytes()).hexdigest())
        self.assertNotIn("model", hashes)
'''
new = '''            expected_hash = hashlib.sha256(script.read_bytes()).hexdigest()
            updated = yaml.safe_load((root / "state" / "project_state.yaml").read_text(encoding="utf-8"))
        hashes = updated["subproblems"]["Q1"]["artifact_hashes"]
        self.assertEqual(hashes["primary_code"], expected_hash)
        self.assertNotIn("model", hashes)
'''
if text.count(old) != 1:
    raise RuntimeError(f"Phase E temp-hash test anchor count={text.count(old)}")
target.write_text(text.replace(old, new, 1), encoding="utf-8")
