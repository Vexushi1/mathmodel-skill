from __future__ import annotations

import ast
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "tests/fixtures/v900_phase_i_writer_retirement_inventory.yaml"
READINESS_PATH = ROOT / "docs/phase_i_legacy_writer_retirement_readiness.md"
IMPLEMENTATION_PATH = ROOT / "docs/phase_i_legacy_writer_retirement.md"
SEMANTIC_GOVERNANCE_PATH = ROOT / "scripts/validate_semantic_governance.py"
MODEL_APPROVAL_PATH = ROOT / "scripts/validate_model_approval.py"
RUNTIME_ASSURANCE_PATH = ROOT / "scripts/runtime_assurance.py"
SCHEMA_PATH = ROOT / "core/project_state.schema.yaml"
BOOTSTRAP_PATH = ROOT / "core/bootstrap.yaml"

INVENTORY = yaml.safe_load(INVENTORY_PATH.read_text(encoding="utf-8"))
READINESS = READINESS_PATH.read_text(encoding="utf-8")
IMPLEMENTATION = IMPLEMENTATION_PATH.read_text(encoding="utf-8")

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


class PhaseII2WriterRetirementTests(unittest.TestCase):
    def test_inventory_remains_bound_to_v890_stable_checkpoint_after_v9_release(self):
        bootstrap = yaml.safe_load(BOOTSTRAP_PATH.read_text(encoding="utf-8"))
        self.assertEqual(INVENTORY["baseline_skill_version"], "8.9.0")
        self.assertEqual(bootstrap["skill_version"], "9.0.0")
        self.assertNotEqual(INVENTORY["baseline_skill_version"], bootstrap["skill_version"])

        scope = INVENTORY["scope"]
        self.assertEqual(scope["phase"], "I2_writer_retirement")
        self.assertTrue(scope["runtime_change_authorized"])
        self.assertTrue(scope["legacy_writer_retirement_authorized"])
        self.assertTrue(scope["gate5_explicit_user_confirmation_required"])
        self.assertTrue(scope["gate5_explicit_user_confirmation_recorded"])
        self.assertFalse(scope["delete_legacy_fields"])
        self.assertFalse(scope["artifact_alias_cleanup_in_scope"])
        self.assertFalse(scope["bump_skill_version"])

        gates = INVENTORY["phase_i_gates_after_i2"]
        self.assertTrue(gates["stable_compatibility_window_closed"])
        self.assertTrue(gates["migration_fixture_baseline_present"])
        self.assertTrue(gates["all_targeted_legacy_semantic_writers_stopped"])
        self.assertTrue(gates["code_search_old_refs_only_intended_readers_validators_tests_docs"])
        self.assertTrue(gates["user_approved_end_v8_write_compatibility"])
        self.assertFalse(gates["final_migration_document_complete"])

    def test_no_active_script_directly_assigns_legacy_identity_candidates(self):
        direct_writes: set[tuple[str, str]] = set()
        for path in sorted((ROOT / "scripts").glob("*.py")):
            for field in _direct_subscript_assignments(path) & LEGACY_FIELDS:
                direct_writes.add((path.name, field))

        self.assertEqual(direct_writes, set())

        semantic_fields = INVENTORY["legacy_semantic_fields"]
        self.assertFalse(semantic_fields["semantic_hash"]["active_writer"])
        self.assertFalse(semantic_fields["validated_semantic_hash"]["active_writer"])
        self.assertFalse(semantic_fields["approved_semantic_hash"]["active_writer"])
        self.assertTrue(semantic_fields["semantic_hash"]["historical_read"])
        self.assertTrue(semantic_fields["validated_semantic_hash"]["historical_read"])

        artifact_fields = INVENTORY["legacy_artifact_fields"]
        self.assertFalse(artifact_fields["model_hash"]["active_writer"])
        self.assertFalse(artifact_fields["validated_model_hash"]["active_writer"])

    def test_structured_identity_writer_surface_is_distinct_and_remains_active(self):
        assigned = _direct_subscript_assignments(SEMANTIC_GOVERNANCE_PATH)
        for field in (
            "semantic_identity_schema_version",
            "semantic_identity_hash",
            "semantic_text_hash",
            "validated_semantic_identity_hash",
        ):
            self.assertIn(field, assigned)

        self.assertNotIn("semantic_hash", assigned)
        self.assertNotIn("validated_semantic_hash", assigned)
        semantic_text = SEMANTIC_GOVERNANCE_PATH.read_text(encoding="utf-8")
        self.assertIn("legacy_write_blocked_sources", semantic_text)
        self.assertIn("write_allowed = write and not legacy_write_blocked_sources", semantic_text)
        self.assertIn("historical provenance only", semantic_text)

    def test_schema_and_historical_reader_boundaries_match_post_i2_inventory(self):
        schema_text = SCHEMA_PATH.read_text(encoding="utf-8")
        schema = yaml.safe_load(schema_text)
        schema_contract = INVENTORY["current_schema_contract"]
        for key in (
            "semantic_hash_description_contains",
            "validated_semantic_hash_description_contains",
            "semantic_hash_description_forbids_active_writer",
            "validated_semantic_hash_description_forbids_active_writer",
            "approved_semantic_hash_description_contains",
        ):
            self.assertIn(schema_contract[key], schema_text)

        subproblem_fields = schema["properties"]["subproblems"]["additionalProperties"]["properties"]
        self.assertNotIn("model_hash", subproblem_fields)
        self.assertNotIn("validated_model_hash", subproblem_fields)

        approval_text = MODEL_APPROVAL_PATH.read_text(encoding="utf-8")
        self.assertIn("allow_legacy_read_only", approval_text)
        self.assertIn("legacy semantic_hash approval is read-only compatibility", approval_text)

        runtime_text = RUNTIME_ASSURANCE_PATH.read_text(encoding="utf-8")
        self.assertIn("legacy_review_required", runtime_text)

        readers = INVENTORY["historical_readers_to_preserve_through_initial_v9"]
        approval_reader = next(
            item for item in readers if item["file"] == "scripts/validate_model_approval.py"
        )
        self.assertEqual(approval_reader["guard"], "allow_legacy_read_only")
        self.assertFalse(approval_reader["active_code_authorization"])

    def test_readiness_record_remains_historical_and_implementation_records_gate5(self):
        self.assertIn("runtime_authority: false", READINESS)
        self.assertIn("legacy_writer_retirement_authorized: false", READINESS)
        self.assertIn("当前“继续修改”不等于 destructive-boundary approval", READINESS)

        self.assertIn("gate5_explicit_user_approval_recorded: true", IMPLEMENTATION)
        self.assertIn("legacy_writer_retirement_authorized: true", IMPLEMENTATION)
        self.assertIn("artifact_alias_removal_in_scope: false", IMPLEMENTATION)
        self.assertIn("legacy_field_deletion_in_scope: false", IMPLEMENTATION)
        self.assertIn("entire semantic-governance state commit = blocked", IMPLEMENTATION)

    def test_i2_forbidden_scope_remains_outside_writer_retirement(self):
        forbidden = set(INVENTORY["forbidden_in_i2_implementation_pr"])
        for item in (
            "delete_legacy_field",
            "remove_historical_reader",
            "delete_model_hash_aliases",
            "delete_artifact_hashes_model",
            "delete_stale_model_alias",
            "modify_compatibility_range",
            "bump_skill_version",
            "auto_create_sib",
            "auto_inherit_human_approval",
        ):
            self.assertIn(item, forbidden)


if __name__ == "__main__":
    unittest.main()
