#!/usr/bin/env python3
"""One-shot wrapper correcting integration-only migration/test anchors."""
from __future__ import annotations

import hashlib
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git_blob_sha(relative: str) -> str:
    data = (ROOT / relative).read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


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

# Normalize the audit record so staged git diff --check remains strict.
inventory = ROOT / "docs/phase_e_artifact_identity_inventory.md"
text = inventory.read_text(encoding="utf-8")
old = "Baseline: `main@5ec9974bfcf87075d509da9fcced69541013877d`  \n"
new = "Baseline: `main@5ec9974bfcf87075d509da9fcced69541013877d`\n"
if text.count(old) != 1:
    raise RuntimeError(f"Phase E inventory whitespace anchor count={text.count(old)}")
inventory.write_text(text.replace(old, new, 1), encoding="utf-8")

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

# Active sync characterization must now assert the canonical primary implementation name.
target = ROOT / "tests/test_sync_project.py"
text = target.read_text(encoding="utf-8")
old = '            self.assertEqual(report["questions"]["Q1"]["artifact_hashes"]["model"], snapshot["artifact_hashes"]["model"])\n'
new = '            self.assertEqual(report["questions"]["Q1"]["artifact_hashes"]["primary_code"], snapshot["artifact_hashes"]["primary_code"])\n'
if text.count(old) != 1:
    raise RuntimeError(f"active sync legacy model assertion count={text.count(old)}")
target.write_text(text.replace(old, new, 1), encoding="utf-8")

# project_state.schema.yaml is a protected authority and is intentionally modified by Phase E.
protected = ROOT / "tests/test_v830_editable_mechanism_diagram.py"
text = protected.read_text(encoding="utf-8")
lines = text.splitlines()
needle = '        "core/project_state.schema.yaml": "'
matched = [index for index, line in enumerate(lines) if line.startswith(needle)]
if len(matched) != 1:
    raise RuntimeError(f"protected project_state schema baseline matches={len(matched)}")
index = matched[0]
lines[index] = f'        "core/project_state.schema.yaml": "{git_blob_sha("core/project_state.schema.yaml")}",'
protected.write_text("\n".join(lines) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
