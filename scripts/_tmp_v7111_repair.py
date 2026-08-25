from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    if text.count(old) != 1:
        raise SystemExit(f"{path}: expected one match, found {text.count(old)}: {old!r}")
    write(path, text.replace(old, new, 1))


# Output summary keeps the established pointer name expected by current consumers.
replace_once(
    "core/output_contract.yaml",
    "  analysis_evidence_authority: core/writing_reasoning_contract.yaml#analysis_evidence_disposition\n",
    "  result_analysis_disposition_authority: core/writing_reasoning_contract.yaml#analysis_evidence_disposition\n",
)

# Historical accepted primary results can proceed to result analysis without retroactive approval.
replace_once(
    "core/workflow_router.yaml",
    "  analysis_execution:\n    role: analysis_execution\n    canonical_route: result_analysis\n",
    "  analysis_execution:\n    role: analysis_execution\n    canonical_route: result_analysis\n    pre_delivery_gates: [semantic_governance, code_delivery]\n",
)

# Preprocessing conditionality now belongs to Router + module spec, not a manifest top-level copy.
replace_once(
    "tests/test_preprocessing_decision_contract.py",
    '    def test_manifest_makes_preprocessing_conditional(self):\n        self.assertIn("data_preprocessing", self.manifest["conditional_modules"])\n',
    '    def test_manifest_makes_preprocessing_conditional(self):\n        self.assertNotIn("conditional_modules", self.manifest)\n        self.assertIn("data_preprocessing", self.router["execution_contract"]["conditional_modules"])\n',
)

# Route-specific gate sequence replaces the duplicate execution_contract gate list.
replace_once(
    "tests/test_router_contract.py",
    '''        self.assertEqual(
            self.router["execution_contract"]["code_stage_gates"],
            ["semantic_governance", "model_approval", "code_delivery"],
        )
''',
    '''        self.assertNotIn("code_stage_gates", self.router["execution_contract"])
        self.assertEqual(
            self.router["routing"]["full_solution"]["pre_delivery_gates"],
            ["semantic_governance", "model_approval", "code_delivery"],
        )
''',
)

# Rewrite the stale changelog assertion as a current/immediate-previous invariant.
path = "tests/test_v752_entrypoint_parity.py"
text = read(path)
pattern = r"    def test_current_changelog_matches_bootstrap\(self\):\n.*?\n    def test_stable_docs_and_resolver_do_not_create_extra_release_carriers"
replacement = '''    def test_current_changelog_matches_bootstrap(self):
        current = str(yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))["skill_version"])
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        releases = re.findall(r"^## (?:Current|Previous) release: ([^\\n]+)$", changelog, flags=re.MULTILINE)
        self.assertGreaterEqual(len(releases), 2)
        self.assertEqual(releases[0], current)
        self.assertNotEqual(releases[1], current)

    def test_stable_docs_and_resolver_do_not_create_extra_release_carriers'''
updated, count = re.subn(pattern, lambda _: replacement, text, count=1, flags=re.DOTALL)
if count != 1:
    raise SystemExit(f"{path}: changelog test repair anchor drift")
write(path, updated)

# Consumer test protects delegation to the authority instead of duplicated field literals.
replace_once(
    "tests/test_v711_model_approval_gate.py",
    '''    def test_solve_module_requires_model_approval_validator(self):
        text = (ROOT / "modules" / "03_solve_validate.md").read_text(encoding="utf-8")
        self.assertIn("scripts/validate_model_approval.py", text)
        self.assertIn("model_challenge_status=passed", text)
        self.assertIn("human_model_approval_status=approved", text)
        self.assertIn("awaiting_model_approval", text)
''',
    '''    def test_solve_module_requires_model_approval_validator(self):
        text = (ROOT / "modules" / "03_solve_validate.md").read_text(encoding="utf-8")
        self.assertIn("scripts/validate_model_approval.py", text)
        self.assertIn("core/model_approval_contract.yaml", text)
        self.assertIn("不复制第二套检查清单", text)
        self.assertIn("awaiting_model_approval", text)
        self.assertNotIn("model_challenge_status=passed", text)
        self.assertNotIn("human_model_approval_status=approved", text)
''',
)

print("v7.11.1 compatibility repair complete")
