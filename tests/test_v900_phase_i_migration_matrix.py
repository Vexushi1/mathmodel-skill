from __future__ import annotations

import importlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def load_module(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SEMANTIC = load_module("v900_phase_i_semantic_identity", "scripts/semantic_identity.py")
APPROVAL = load_module("v900_phase_i_model_approval", "scripts/validate_model_approval.py")
ASSURANCE = load_module("v900_phase_i_runtime_assurance", "scripts/runtime_assurance.py")
RESOLVER = load_module("v900_phase_i_resolver", "scripts/resolve_runtime.py")
ARTIFACT_IDENTITY = importlib.import_module("artifact_identity")

MATRIX = yaml.safe_load(
    (ROOT / "tests/fixtures/v900_phase_i_migration_matrix.yaml").read_text(encoding="utf-8")
)
MIGRATION_CONTRACT = (ROOT / MATRIX["migration_contract_document"]).read_text(encoding="utf-8")


def capabilities() -> dict:
    return {
        "has_explicit_constraints": True,
        "requires_feasibility_check": True,
        "requires_equilibrium_residual": False,
        "requires_conservation_residual": False,
        "requires_discretization_check": False,
        "requires_convergence_diagnostic": True,
    }


def identity_payload() -> dict:
    return {
        "schema_version": "1.0.0",
        "question": "Q1",
        "research_object": "城市配送车辆调度",
        "data_scope": [{"id": "D1", "source": "附件1", "role": "输入"}],
        "variables": [
            {"id": "V1", "symbol": "x_i", "role": "decision", "domain": "binary"},
        ],
        "parameters": [{"id": "P1", "symbol": "c_i", "unit": "CNY"}],
        "assumptions": [{"id": "A1", "statement": "需求在决策周期内保持给定"}],
        "objective": {"sense": "minimize", "expression": "C(x)"},
        "constraints": [{"id": "C1", "expression": "x_i in {0,1}"}],
        "preprocessing_decision": "not_needed",
        "algorithm_semantics": {"model_family": "MILP", "solver_role": "exact_or_gap_bounded"},
        "dependencies": [],
    }


def legacy_framework() -> str:
    return (
        "# 模型论文框架\n\n"
        "### Q1：第一问\n"
        "#### 当前模型口径\n"
        "- 目标：min f(x)\n"
        "- 约束：x >= 0\n"
        "#### 结果摘要\n"
        "历史结果。\n"
    )


def structured_framework(payload: dict) -> str:
    yaml_text = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    return (
        "# 模型论文框架\n\n"
        "### Q1：第一问\n"
        "#### 当前模型口径\n"
        "<!-- HSK_SEMANTIC_IDENTITY_BEGIN Q1 -->\n"
        "```yaml\n"
        f"{yaml_text}"
        "```\n"
        "<!-- HSK_SEMANTIC_IDENTITY_END Q1 -->\n\n"
        "当前说明文字。\n"
        "#### 结果摘要\n"
        "待求解。\n"
    )


def common_question() -> dict:
    return {
        "classification": {
            "objective": "optimization",
            "structures": ["stochastic"],
        },
        "capabilities": capabilities(),
        "model_challenge_status": "passed",
        "human_model_approval_status": "approved",
        "semantic_revision": 2,
        "approved_semantic_revision": 2,
        "primary_execution_status": "pending",
        "analysis_execution_status": "pending",
        "result_quality_status": "pending",
        "result_analysis_status": "pending",
    }


def legacy_question(framework_text: str) -> dict:
    section = SEMANTIC.question_sections(framework_text)["Q1"]
    digest = SEMANTIC.inspect_question_semantics(section, "Q1")["semantic_text_hash"]
    question = common_question()
    question.update(
        {
            "semantic_hash": digest,
            "validated_semantic_hash": digest,
            "approved_semantic_hash": digest,
        }
    )
    return question


def structured_question(payload: dict, framework_text: str) -> dict:
    inspected = SEMANTIC.inspect_question_semantics(
        SEMANTIC.question_sections(framework_text)["Q1"], "Q1"
    )
    digest = SEMANTIC.semantic_identity_hash(payload)
    question = common_question()
    question.update(
        {
            "semantic_identity_schema_version": "1.0.0",
            "semantic_identity_hash": digest,
            "validated_semantic_identity_hash": digest,
            "approved_semantic_identity_hash": digest,
            "semantic_text_hash": inspected["semantic_text_hash"],
        }
    )
    return question


def write_project(root: Path, question: dict, framework_text: str) -> None:
    (root / "state").mkdir(parents=True, exist_ok=True)
    state = {
        "project": {
            "competition": "CUMCM",
            "problem": "A",
            "current_phase": "solve_validate",
            "version": "current",
        },
        "preprocessing": {"decision": "not_needed", "status": "not_applicable"},
        "subproblems": {"Q1": question},
    }
    (root / "state" / "project_state.yaml").write_text(
        yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    (root / "模型论文框架.md").write_text(framework_text, encoding="utf-8")


def locked_row(hydration: dict) -> dict:
    return next(
        item
        for item in hydration["artifact_evidence"]
        if item["artifact"] == "locked_model_spec" and item["scope"] == "Q1"
    )


class PhaseIPlanBindingTests(unittest.TestCase):
    def test_fixture_remains_bound_to_v890_staging_baseline_after_v9_release(self):
        bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))
        self.assertEqual(MATRIX["baseline_skill_version"], "8.9.0")
        self.assertEqual(bootstrap["skill_version"], "9.0.0")
        self.assertNotEqual(MATRIX["baseline_skill_version"], bootstrap["skill_version"])
        self.assertEqual(
            MATRIX["baseline_main_commit"],
            "e7a5f45fe5bbd96db03b49c6e993b26af10f55ae",
        )

        plan = (ROOT / "docs/semantic_state_runtime_refactor_plan.md").read_text(encoding="utf-8")
        self.assertIn("## Phase I — v9.0.0 Compatibility Removal", plan)
        for token in (
            "artifact_hashes.model",
            "semantic_hash",
            "model_hash / validated_model_hash",
            "用户确认可以结束 v8 project write compatibility",
        ):
            self.assertIn(token, plan)

        gates = MATRIX["phase_i_gates"]
        self.assertTrue(gates["stable_compatibility_window_closed"])
        self.assertTrue(gates["migration_fixture_baseline_present"])
        self.assertTrue(gates["migration_fixtures_green_on_v890_baseline"])
        self.assertTrue(gates["all_legacy_writers_stopped"])
        self.assertTrue(gates["user_approved_end_v8_write_compatibility"])
        self.assertTrue(gates["artifact_active_schema_aliases_removed"])
        self.assertTrue(gates["final_migration_document_complete"])
        self.assertTrue(gates["release_carrier_v900_active"])
        self.assertTrue(gates["i5_release_closure_documented"])

    def test_final_contract_closes_release_without_becoming_runtime_authority(self):
        self.assertIn("runtime_authority: false", MIGRATION_CONTRACT)
        self.assertIn("destructive_compatibility_removal_authorized: true", MIGRATION_CONTRACT)
        self.assertIn("current_skill_version: 9.0.0", MIGRATION_CONTRACT)
        self.assertIn("phase_i_release_documentation_complete: true", MIGRATION_CONTRACT)
        self.assertIn("I5 本身不执行真实用户项目的批量迁移", MIGRATION_CONTRACT)


class MigrationContractPolicyTests(unittest.TestCase):
    def test_only_mechanical_implementation_aliases_are_auto_migratable(self):
        policy = MATRIX["migration_contract"]
        automatic = policy["automatic_migrations"]
        for key in (
            "artifact_hashes_model_to_primary_code",
            "validated_artifact_hashes_model_to_primary_code",
            "model_hash_to_primary_code_fallback",
            "validated_model_hash_to_primary_code_fallback",
            "stale_model_layer_to_primary_code",
        ):
            self.assertIn(key, automatic)
            self.assertNotEqual(automatic[key], "forbidden")

        self.assertEqual(
            policy["automatic_migration_scope"],
            "pre_schema_historical_adapter_only",
        )
        self.assertEqual(
            MATRIX["artifact_compatibility"]["alias_conflict_policy"], "blocking"
        )
        self.assertIn("blocking inconsistency", MIGRATION_CONTRACT)
        self.assertIn("禁止", MIGRATION_CONTRACT)
        self.assertIn("静默覆盖", MIGRATION_CONTRACT)

    def test_semantic_identity_and_human_approval_are_never_synthesized(self):
        policy = MATRIX["migration_contract"]
        forbidden = policy["forbidden_automatic_migrations"]
        for key in (
            "semantic_hash_to_semantic_identity_hash",
            "validated_semantic_hash_to_validated_semantic_identity_hash",
            "approved_semantic_hash_to_approved_semantic_identity_hash",
            "synthesize_verified_sib_from_legacy_prose",
            "synthesize_human_approval",
            "legacy_fallback_when_structured_identity_partial",
        ):
            self.assertTrue(forbidden[key], key)

        self.assertTrue(policy["legacy_reentry_requires_structured_identity"])
        self.assertTrue(policy["legacy_reentry_requires_explicit_human_approval"])
        self.assertTrue(policy["destructive_legacy_write_retirement_authorized"])
        self.assertIn("必须显式 Human Approval", MIGRATION_CONTRACT)
        self.assertIn("partial structured state 必须 fail closed", MIGRATION_CONTRACT)

    def test_initial_v9_keeps_narrow_historical_read_only_adapter(self):
        policy = MATRIX["migration_contract"]
        self.assertTrue(policy["historical_read_only_supported"])
        self.assertEqual(
            policy["initial_v9_historical_reader_policy"], "narrow_read_only_adapter"
        )
        self.assertIn("L0 — Historical read-only legacy project", MIGRATION_CONTRACT)
        self.assertIn("L1 — Legacy project re-entering active modeling / code workflow", MIGRATION_CONTRACT)
        self.assertIn("初始 v9.0.0 不要求", MIGRATION_CONTRACT)
        self.assertIn("historical reader 的彻底删除", MIGRATION_CONTRACT)


class LegacyMigrationAcceptanceTests(unittest.TestCase):
    def test_l0_historical_legacy_is_readable_but_never_verified(self):
        case = MATRIX["cases"]["L0_historical_read_only"]
        text = legacy_framework()
        question = legacy_question(text)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root, question, text)
            hydration = ASSURANCE.hydrate_project_context(root, "Q1")

        row = locked_row(hydration)
        self.assertEqual(row["identity_mode"], case["identity_mode"])
        self.assertEqual(row["status"], case["runtime_locked_model_status"])
        self.assertEqual("locked_model_spec" in hydration["verified_artifacts"], case["locked_model_promoted"])

        strict_errors = APPROVAL.validate_question("Q1", question)
        self.assertTrue(any("read-only compatibility" in item for item in strict_errors))
        self.assertEqual(
            APPROVAL.validate_question("Q1", question, allow_legacy_read_only=True),
            [],
        )

    def test_l1_legacy_reentry_returns_to_model_approval_before_primary_solve(self):
        case = MATRIX["cases"]["L1_legacy_reenter_full_solution"]
        text = legacy_framework()
        question = legacy_question(text)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root, question, text)
            plan = RESOLVER.resolve_runtime(
                case["intent"], project_root=root, question="Q1"
            )

        self.assertEqual(plan["pause_state"], case["expected_pause_state"])
        self.assertEqual(
            plan["pause_for_model_approval"], case["expected_pause_for_model_approval"]
        )
        self.assertIn(case["required_module"], plan["modules"])
        self.assertNotIn(case["forbidden_module"], plan["modules"])
        effective = plan["assurance"]["artifact_assurance"]["effective_artifacts"]
        self.assertEqual("locked_model_spec" in effective, case["locked_model_promoted"])

    def test_l2_current_structured_identity_verifies(self):
        case = MATRIX["cases"]["L2_structured_current"]
        payload = identity_payload()
        text = structured_framework(payload)
        question = structured_question(payload, text)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root, question, text)
            hydration = ASSURANCE.hydrate_project_context(root, "Q1")

        row = locked_row(hydration)
        self.assertEqual(row["identity_mode"], case["identity_mode"])
        self.assertEqual(row["status"], case["runtime_locked_model_status"])
        self.assertEqual("locked_model_spec" in hydration["verified_artifacts"], case["locked_model_promoted"])
        self.assertEqual(
            len(APPROVAL.validate_question("Q1", question)),
            case["structured_approval_error_count"],
        )


class ArtifactCompatibilityAcceptanceTests(unittest.TestCase):
    def test_legacy_artifact_names_are_pre_schema_read_only_aliases(self):
        config = MATRIX["artifact_compatibility"]
        digest = "a" * 64

        self.assertFalse(config["active_state_schema_accepts_legacy_aliases"])
        self.assertTrue(config["historical_adapter_supported"])
        self.assertEqual(config["historical_adapter"], "scripts/artifact_identity.py")

        normalized = ARTIFACT_IDENTITY.normalize_artifact_hashes(
            {config["legacy_artifact_key"]: digest}
        )
        self.assertEqual(normalized[config["canonical_artifact_key"]], digest)
        self.assertNotIn(config["legacy_artifact_key"], normalized)

        fallback = ARTIFACT_IDENTITY.normalize_artifact_hashes(
            {}, legacy_primary_fallback=digest
        )
        self.assertEqual(fallback[config["canonical_artifact_key"]], digest)

        with self.assertRaises(ARTIFACT_IDENTITY.ArtifactIdentityError):
            ARTIFACT_IDENTITY.normalize_artifact_hashes(
                {
                    config["legacy_artifact_key"]: "a" * 64,
                    config["canonical_artifact_key"]: "b" * 64,
                }
            )

    def test_state_transition_authority_retires_stale_model_alias(self):
        contract = yaml.safe_load(
            (ROOT / "core/state_transition_contract.yaml").read_text(encoding="utf-8")
        )
        compatibility = contract["compatibility"]
        self.assertFalse(
            compatibility["obsolete_implementation_artifact_aliases_in_active_state_supported"]
        )
        self.assertEqual(
            compatibility["historical_implementation_alias_adapter"],
            MATRIX["artifact_compatibility"]["historical_adapter"],
        )
        self.assertEqual(
            compatibility["historical_implementation_alias_adapter_scope"],
            "read_only_audit_or_pre_schema_migration",
        )
        self.assertNotIn("legacy_model_artifact_layer_read_supported", compatibility)
        self.assertNotIn("legacy_model_artifact_layer_maps_to", compatibility)
        self.assertNotIn("legacy_model_artifact_layer_write_supported", compatibility)

        schema = yaml.safe_load(
            (ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8")
        )
        self.assertNotIn("model", schema["$defs"]["artifact_layer"]["enum"])
        self.assertIn("model", schema["$defs"]["dependency_kind"]["enum"])


if __name__ == "__main__":
    unittest.main()
