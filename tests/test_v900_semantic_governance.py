from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

SPEC = importlib.util.spec_from_file_location(
    "v900_semantic_governance", ROOT / "scripts/validate_semantic_governance.py"
)
SEMANTIC = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = SEMANTIC
SPEC.loader.exec_module(SEMANTIC)


def identity_payload(*, objective_expression: str = "sum_i c_i * x_i") -> dict:
    return {
        "schema_version": "1.0.0",
        "question": "Q1",
        "research_object": "城市配送车辆调度",
        "data_scope": [{"id": "D1", "source": "附件1", "role": "input"}],
        "variables": [{"id": "V1", "symbol": "x_i", "role": "decision", "domain": "binary"}],
        "parameters": [{"id": "P1", "symbol": "c_i", "unit": "CNY"}],
        "assumptions": [{"id": "A1", "statement": "单周期内需求按题面给定"}],
        "objective": {"sense": "minimize", "expression": objective_expression},
        "constraints": [{"id": "C1", "expression": "sum_i x_i <= K", "role": "capacity"}],
        "preprocessing_decision": "not_needed",
        "algorithm_semantics": {"model_family": "MILP", "solver_role": "exact_or_gap_bounded"},
        "dependencies": [],
    }


def framework(payload: dict | None = None, *, prose: str = "当前模型说明。") -> str:
    if payload is None:
        return f"""# 模型论文框架
## 各问模型与结果
### Q1：第一问
#### 当前模型口径
- 目标：min f(x)
- 说明：{prose}
#### 结果摘要
待求解。
"""
    identity_yaml = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    return f"""# 模型论文框架
## 各问模型与结果
### Q1：第一问
#### 当前模型口径
<!-- HSK_SEMANTIC_IDENTITY_BEGIN Q1 -->
```yaml
{identity_yaml}```
<!-- HSK_SEMANTIC_IDENTITY_END Q1 -->

{prose}
#### 结果摘要
待求解。
"""


def base_state() -> dict:
    legacy_hash = "a" * 64
    return {
        "semantic_governance_version": "1.0.0",
        "subproblems": {
            "Q1": {
                "status": "designed",
                "selected_model": "MILP",
                "classification": {"objective": "optimization", "structures": []},
                "capabilities": {},
                "depends_on": [],
                "problem_contract_status": "frozen",
                "semantic_closure_status": "passed",
                "complexity_sanity_status": "passed",
                "complexity_sanity_flags": [],
                "complexity_sanity_note": "复审完成。",
                "model_challenge_status": "passed",
                "human_model_approval_status": "approved",
                "approved_semantic_revision": 1,
                "approved_semantic_hash": legacy_hash,
                "semantic_revision": 1,
                "validated_semantic_revision": 1,
                "semantic_change_categories": ["initial_design"],
                "semantic_hash": legacy_hash,
                "validated_semantic_hash": legacy_hash,
                "artifact_hashes": {},
                "validated_artifact_hashes": {},
                "stale_layers": [],
                "framework_section": "### Q1：第一问",
                "result_summary_status": "current",
                "result_quality_status": "passed",
                "result_analysis_status": "passed",
                "validation_status": "passed",
                "artifacts_stale": False,
                "primary_execution_status": "accepted",
                "analysis_execution_status": "accepted",
            }
        },
        "paper_framework": {"sync_status": "current", "paper_fragments": []},
    }


def write_project(root: Path, state: dict, framework_text: str) -> Path:
    (root / "state").mkdir(parents=True, exist_ok=True)
    state_path = root / "state" / "project_state.yaml"
    state_path.write_text(
        yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    (root / "模型论文框架.md").write_text(framework_text, encoding="utf-8")
    return state_path


class TestV900SemanticGovernance(unittest.TestCase):
    def test_schema_accepts_complete_identity_state_and_rejects_partial_identity_state(self):
        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        fields = schema["properties"]["subproblems"]["additionalProperties"]["properties"]
        for name in (
            "semantic_identity_schema_version",
            "semantic_identity_hash",
            "validated_semantic_identity_hash",
            "approved_semantic_identity_hash",
            "semantic_text_hash",
        ):
            self.assertIn(name, fields)

        example = yaml.safe_load((ROOT / "state/project_state.example.yaml").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        self.assertEqual(list(validator.iter_errors(example)), [])

        migrated = deepcopy(example)
        q1 = migrated["subproblems"]["Q1"]
        q1["semantic_identity_schema_version"] = "1.0.0"
        q1["semantic_identity_hash"] = "b" * 64
        q1["validated_semantic_identity_hash"] = "b" * 64
        q1["semantic_text_hash"] = "c" * 64
        self.assertEqual(list(validator.iter_errors(migrated)), [])

        partial = deepcopy(example)
        partial["subproblems"]["Q1"]["semantic_identity_hash"] = "b" * 64
        self.assertTrue(list(validator.iter_errors(partial)))

    def test_legacy_framework_is_read_only_and_write_requires_sib(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = base_state()
            q1 = state["subproblems"]["Q1"]
            for name in (
                "semantic_hash",
                "validated_semantic_hash",
                "approved_semantic_hash",
                "approved_semantic_revision",
                "validated_semantic_revision",
            ):
                q1.pop(name, None)
            state_path = write_project(root, state, framework(None))
            before_text = state_path.read_text(encoding="utf-8")

            historical = SEMANTIC.validate_project(root, write=False, strict=True)
            report = SEMANTIC.validate_project(root, write=True, strict=True)
            after_text = state_path.read_text(encoding="utf-8")
            saved = yaml.safe_load(after_text)["subproblems"]["Q1"]

        self.assertEqual(historical["identity_modes"], {"Q1": "legacy_text_hash"})
        self.assertEqual(historical["status"], "passed", historical)
        self.assertEqual(report["status"], "failed", report)
        self.assertEqual(report["identity_modes"], {"Q1": "legacy_text_hash"})
        self.assertEqual(report["migration_sources"], ["Q1"])
        self.assertEqual(report["legacy_write_blocked_sources"], ["Q1"])
        self.assertTrue(any("历史只读兼容" in item and "有效SIB" in item for item in report["issues"]), report)
        self.assertEqual(before_text, after_text)
        self.assertNotIn("semantic_hash", saved)
        self.assertNotIn("validated_semantic_hash", saved)
        self.assertNotIn("semantic_identity_hash", saved)
        self.assertNotIn("semantic_text_hash", saved)

    def test_sib_requires_baseline_on_strict_read_then_write_initializes_new_fields_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = base_state()
            legacy_hash = state["subproblems"]["Q1"]["semantic_hash"]
            state_path = write_project(root, state, framework(identity_payload()))

            before = SEMANTIC.validate_project(root, write=False, strict=True)
            self.assertEqual(before["status"], "failed", before)
            self.assertEqual(before["migration_sources"], ["Q1"])

            migrated = SEMANTIC.validate_project(root, write=True, strict=True)
            saved = yaml.safe_load(state_path.read_text(encoding="utf-8"))["subproblems"]["Q1"]

        self.assertEqual(migrated["status"], "passed", migrated)
        self.assertEqual(migrated["identity_modes"], {"Q1": "semantic_identity_v1"})
        self.assertEqual(migrated["legacy_write_blocked_sources"], [])
        self.assertEqual(saved["semantic_identity_schema_version"], "1.0.0")
        self.assertEqual(saved["semantic_identity_hash"], saved["validated_semantic_identity_hash"])
        self.assertEqual(saved["semantic_identity_hash"], migrated["semantic_identity_hashes"]["Q1"])
        self.assertEqual(saved["semantic_text_hash"], migrated["semantic_text_hashes"]["Q1"])
        self.assertEqual(saved["semantic_hash"], legacy_hash)
        self.assertEqual(saved["validated_semantic_hash"], legacy_hash)
        self.assertNotIn("approved_semantic_identity_hash", saved)
        self.assertFalse(saved["artifacts_stale"])

    def test_wording_only_change_updates_text_hash_without_semantic_stale(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path = write_project(root, base_state(), framework(identity_payload(), prose="模型说明A。"))
            first = SEMANTIC.validate_project(root, write=True, strict=True)
            self.assertEqual(first["status"], "passed", first)
            first_state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            before_identity = first_state["subproblems"]["Q1"]["semantic_identity_hash"]
            before_text = first_state["subproblems"]["Q1"]["semantic_text_hash"]
            before_revision = first_state["subproblems"]["Q1"]["semantic_revision"]

            (root / "模型论文框架.md").write_text(
                framework(identity_payload(), prose="换一种表达，但数学语义没有变化。"), encoding="utf-8"
            )
            report = SEMANTIC.validate_project(root, write=False, strict=True)
            self.assertEqual(report["status"], "passed", report)
            self.assertEqual(report["changed_sources"], [])
            self.assertEqual(report["text_changed_sources"], ["Q1"])

            written = SEMANTIC.validate_project(root, write=True, strict=True)
            saved = yaml.safe_load(state_path.read_text(encoding="utf-8"))["subproblems"]["Q1"]

        self.assertEqual(written["status"], "passed", written)
        self.assertEqual(saved["semantic_identity_hash"], before_identity)
        self.assertNotEqual(saved["semantic_text_hash"], before_text)
        self.assertEqual(saved["semantic_revision"], before_revision)
        self.assertFalse(saved["artifacts_stale"])
        self.assertEqual(saved["human_model_approval_status"], "approved")

    def test_identity_change_without_revision_bump_fails_and_with_bump_stales(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path = write_project(root, base_state(), framework(identity_payload()))
            first = SEMANTIC.validate_project(root, write=True, strict=True)
            self.assertEqual(first["status"], "passed", first)

            (root / "模型论文框架.md").write_text(
                framework(identity_payload(objective_expression="sum_i (c_i + 1) * x_i")), encoding="utf-8"
            )
            failed = SEMANTIC.validate_project(root, write=False, strict=True)
            self.assertEqual(failed["status"], "failed", failed)
            self.assertEqual(failed["changed_sources"], ["Q1"])
            self.assertTrue(any("semantic_revision未递增" in item for item in failed["issues"]), failed)

            state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            state["subproblems"]["Q1"]["semantic_revision"] = 2
            state["subproblems"]["Q1"]["semantic_change_categories"] = ["objective"]
            state_path.write_text(
                yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            passed = SEMANTIC.validate_project(root, write=True, strict=True)
            saved = yaml.safe_load(state_path.read_text(encoding="utf-8"))["subproblems"]["Q1"]

        self.assertEqual(passed["status"], "passed", passed)
        self.assertEqual(passed["changed_sources"], ["Q1"])
        self.assertEqual(saved["validated_semantic_identity_hash"], saved["semantic_identity_hash"])
        self.assertEqual(saved["validated_semantic_revision"], 2)
        self.assertTrue(saved["artifacts_stale"])
        self.assertEqual(saved["human_model_approval_status"], "stale")
        self.assertEqual(saved["model_challenge_status"], "stale")

    def test_malformed_sib_markers_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            malformed = """# 模型论文框架
### Q1：第一问
#### 当前模型口径
<!-- HSK_SEMANTIC_IDENTITY_BEGIN Q1 -->
```yaml
question: Q1
```
#### 结果摘要
待求解。
"""
            write_project(root, base_state(), malformed)
            report = SEMANTIC.validate_project(root, write=False, strict=True)

        self.assertEqual(report["status"], "failed", report)
        self.assertTrue(any("Semantic Identity Block" in item for item in report["issues"]), report)
        self.assertNotIn("Q1", report["semantic_hashes"])
        self.assertNotIn("Q1", report["semantic_identity_hashes"])


if __name__ == "__main__":
    unittest.main()
