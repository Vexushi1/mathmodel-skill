#!/usr/bin/env python3
"""One-shot health-check migration for Phase D. Removed after successful integration."""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "scripts" / "lint_skill_checks.py"
text = path.read_text(encoding="utf-8")
old = '''    for token in ("problem_contract_status", "semantic_closure_status", "complexity_sanity_status", "semantic_revision", "depends_on", "_dependent_closure", "_mark_paper_fragments_stale"):
        if token not in semantic:
            errors.append(f"semantic governance validator lacks token: {token}")
'''
new = '''    for token in ("problem_contract_status", "semantic_closure_status", "complexity_sanity_status", "semantic_revision", "depends_on", "STATE_TRANSITIONS", "STATE_TRANSITION_CONTRACT", "_mark_paper_fragments_stale"):
        if token not in semantic:
            errors.append(f"semantic governance validator lacks token: {token}")
    transition_engine = read_text(ROOT / "scripts/state_transitions.py")
    for token in ("apply_transition", "apply_local_event", "dependency_cycles", "LEGACY_DEPENDENCY_KIND"):
        if token not in transition_engine:
            errors.append(f"state transition engine lacks token: {token}")
    transition_contract = load_structured(ROOT / "core/state_transition_contract.yaml") or {}
    if transition_contract.get("status") != "active":
        errors.append("state transition contract must be active")
    dependency_rules = transition_contract.get("dependency_rules", {}) or {}
    for kind in ("data", "parameter", "model", "result", "legacy_untyped"):
        if kind not in dependency_rules:
            errors.append(f"state transition contract lacks dependency rule: {kind}")
'''
if text.count(old) != 1:
    raise RuntimeError(f"expected one legacy semantic-lint token block, got {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Phase D lint migrated to shared state-transition Authority")
