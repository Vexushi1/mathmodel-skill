from __future__ import annotations

import ast
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "tests/fixtures/v900_phase_i_writer_retirement_inventory.yaml"
READINESS_PATH = ROOT / "docs/phase_i_legacy_writer_retirement_readiness.md"
SEMANTIC_GOVERNANCE_PATH = ROOT / "scripts/validate_semantic_governance.py"
MODEL_APPROVAL_PATH = ROOT / "scripts/validate_model_approval.py"
SCHEMA_PATH = ROOT / "core/project_state.schema.yaml"
BOOTSTRAP_PATH = ROOT / "core/bootstrap.yaml"

INVENTORY = yaml.safe_load(INVENTORY_PATH.read_text(encoding="utf-8"))
READINESS = READINESS_PATH.read_text(encoding="utf-8")

LEGACY_FIELDS = {
    "semantic_hash",
    "validated_semantic_hash",
    "approved_semantic_hash",
    "model_hash",
    "validated_model_hash",
}


def _literal_subscript_key(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Subscript):
        return None
    key = node.slice
    if isinstance(key, ast.Constant) and isinstance(key.value, str):
        return key.value
    return None


def _direct_subscript_assignments(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    assigned: set[str] = set()
    for node in ast.walk(tree):
        targets: list[ast.AST] = []
        if isinstance(node, ast.Assign):
            targets.extend(node.targets)
        elif isinstance(node, ast.AnnAssign):
            targets.append(node.target)
        elif isinstance(node, ast.AugAssign):
            targets.append(node.target)
        for target in targets:
            key = _literal_subscript_key(target)
            if key is not None:
                assigned.add(key)
    return assigned


class PhaseII2WriterRetirementReadinessTests(unittest.TestCase):
    def test_inventory_is_bound_to_current_stable_release_and_non_destructive_scope(self):
        bootstrap = yaml.safe_load(BOOTSTRAP_PATH.read_text(encoding="utf-8"))
        self.assertEqual(INVENTORY["baseline_skill_version"], bootstrap["skill_version"])
        self.assertEqual(bootstrap["skill_version"], "8.9.0")

        scope = INVENTORY["scope"]
        self.assertEqual(scope["phase"], "I2_readiness")
        self.assertFalse(scope["runtime_change_authorized"])
        self.assertFalse(scope["destructive_compatibility_removal_authorized"])
        self.assertTrue(scope["gate5_explicit_user_confirmation_required"])

        gates = INVENTORY["phase_i_gates_after_readiness"]
        self.assertTrue(gates["stable_compatibility_window_closed"])
        self.assertTrue(gates["migration_fixture_baseline_present"])
        self.assertFalse(gates["all_legacy_writers_stopped"])
        self.assertFalse(gates["code_search_old_refs_only_readers_docs"])
        self.assertFalse(gates["user_approved_end_v8_write_compatibility"])
        self.assertFalse(gates["final_migration_document_complete"])

    def test_only_confirmed_direct_legacy_semantic_writes_are_in_semantic_governance(self):
        direct_writes: set[tuple[str, str]] = set()
        for path in sorted((ROOT / "scripts").glob("*.py")):
            for field in _direct_subscript_assignments(path) & LEGACY_FIELDS:
                direct_writes.add((path.name, field))

        self.assertEqual(
            direct_writes,
            {
                ("validate_semantic_governance.py", "semantic_hash"),
                ("validate_semantic_governance.py", "validated_semantic_hash"),
            },
        )

        semantic_fields = INVENTORY["legacy_semantic_fields"]
        self.assertTrue(semantic_fields["semantic_hash"]["active_writer"])
        self.assertTrue(semantic_fields["validated_semantic_hash"]["active_writer"])
        self.assertFalse(semantic_fields["approved_semantic_hash"]["active_writer"])

        artifact_fields = INVENTORY["legacy_artifact_fields"]
        self.assertFalse(artifact_fields["model_hash"]["active_writer"])
        self.assertFalse(artifact_fields["validated_model_hash"]["active_writer"])

    def test_structured_identity_writer_surface_is_distinct_and_must_not_be_retired(self):
        assigned = _direct_subscript_assignments(SEMANTIC_GOVERNANCE_PATH)
        for field in (
            "semantic_identity_schema_version",
            "semantic_identity_hash",
            "semantic_text_hash",
            "validated_semantic_identity_hash",
        ):
            self.assertIn(field, assigned)

        self.assertIn(
            "structured SIB 分支写的是 `semantic_identity_hash / validated_semantic_identity_hash / semantic_text_hash`",
            READINESS,
        )
        self.assertIn("不应被 I2 retirement 误伤", READINESS)

    def test_schema_and_historical_reader_boundaries_match_inventory(self):
        schema_text = SCHEMA_PATH.read_text(encoding="utf-8")
        schema_contract = INVENTORY["current_schema_contract"]
        for key in (
            "semantic_hash_description_contains",
            "validated_semantic_hash_description_contains",
            "approved_semantic_hash_description_contains",
            "model_hash_description_contains",
            "validated_model_hash_description_contains",
        ):
            self.assertIn(schema_contract[key], schema_text)

        approval_text = MODEL_APPROVAL_PATH.read_text(encoding="utf-8")
        self.assertIn("allow_legacy_read_only", approval_text)
        self.assertIn("legacy semantic_hash approval is read-only compatibility", approval_text)

        readers = INVENTORY["historical_readers_to_preserve_through_initial_v9"]
        approval_reader = next(
            item for item in readers if item["file"] == "scripts/validate_model_approval.py"
        )
        self.assertEqual(approval_reader["guard"], "allow_legacy_read_only")
        self.assertFalse(approval_reader["active_code_authorization"])

    def test_readiness_pr_forbids_behavior_change_and_does_not_satisfy_gate5(self):
        forbidden = set(INVENTORY["forbidden_in_readiness_pr"])
        for item in (
            "modify_scripts",
            "modify_core_authority",
            "modify_project_state_schema",
            "stop_legacy_writer",
            "delete_legacy_field",
            "remove_historical_reader",
            "modify_compatibility_range",
            "infer_gate5_from_continue_instruction",
            "bump_skill_version",
        ):
            self.assertIn(item, forbidden)

        self.assertIn("runtime_authority: false", READINESS)
        self.assertIn("legacy_writer_retirement_authorized: false", READINESS)
        self.assertIn("当前“继续修改”不等于 destructive-boundary approval", READINESS)
        self.assertIn("I2-readiness 合并不会改变上述 Gate 3–6", READINESS)


if __name__ == "__main__":
    unittest.main()
