#!/usr/bin/env python3
"""One-shot post-audit correction for Phase D. Removed after successful commit."""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(relative: str, old: str, new: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"{relative}: expected exactly one match, got {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def git_blob_sha(relative: str) -> str:
    data = (ROOT / relative).read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


replace_once(
    "scripts/validate_code_delivery.py",
    "    if not state_path.is_file():\n        return\n",
    "    if not state_path.is_file():\n        return []\n",
)

# Durable regression: an optional/missing project state must preserve the list-return contract.
path = ROOT / "tests" / "test_v900_state_transitions.py"
text = path.read_text(encoding="utf-8")
old = '''TRANSITIONS = load_module("v900_state_transitions", "scripts/state_transitions.py")
CONTRACT = yaml.safe_load((ROOT / "core/state_transition_contract.yaml").read_text(encoding="utf-8"))
'''
new = '''TRANSITIONS = load_module("v900_state_transitions", "scripts/state_transitions.py")
CODE_DELIVERY = load_module("v900_code_delivery_transition_contract", "scripts/validate_code_delivery.py")
CONTRACT = yaml.safe_load((ROOT / "core/state_transition_contract.yaml").read_text(encoding="utf-8"))
'''
if text.count(old) != 1:
    raise RuntimeError("state-transition test import insertion point changed")
text = text.replace(old, new, 1)
old = '''class StateTransitionAuthorityTests(unittest.TestCase):
'''
new = '''class CodeDeliveryTransitionContractTests(unittest.TestCase):
    def test_missing_project_state_returns_empty_transition_list(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "问题一求解.py"
            script.write_text("print('placeholder')\\n", encoding="utf-8")
            result = CODE_DELIVERY.update_state(
                root,
                {"stage": "primary", "problem": "问题一"},
                script,
            )
        self.assertEqual(result, [])


class StateTransitionAuthorityTests(unittest.TestCase):
'''
if text.count(old) != 1:
    raise RuntimeError("state-transition test class insertion point changed")
path.write_text(text.replace(old, new, 1), encoding="utf-8")

# Refresh only the legally changed protected baseline.
protected = ROOT / "tests" / "test_v830_editable_mechanism_diagram.py"
text = protected.read_text(encoding="utf-8")
lines = text.splitlines()
needle = '        "scripts/validate_code_delivery.py": "'
matched = [index for index, line in enumerate(lines) if line.startswith(needle)]
if len(matched) != 1:
    raise RuntimeError(f"protected validate_code_delivery baseline match count={len(matched)}")
index = matched[0]
lines[index] = f'        "scripts/validate_code_delivery.py": "{git_blob_sha("scripts/validate_code_delivery.py")}",'
protected.write_text("\n".join(lines) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")

print("Phase D post-audit return contract fixed")
