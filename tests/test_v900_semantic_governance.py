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


def framework(payload: dict | None = None, *, prose: str = "当前模型说明。", question: str = "Q1") -> str:
    if payload is None:
        return f"""# 模型论文框架
## 各问模型与结果
### {question}：第一问
#### 当前模型口径
- 目标：min f(x)
- 说明：{prose}
#### 结果摘要
待求解。
"""
    identity_yaml = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    return f"""# 模型论文框架
## 各问模型与结果
### {question}：第一问
#### 当前模型口径
<!-- HSK_SEMANTIC_IDENTITY_BEGIN {question} -->
```yaml
{identity_yaml}```
<!-- HSK_SEMANTIC_IDENTITY_END {question} -->

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


def dependency_project(root: Path) -> Path:
    state = base_state()
    prototype = deepcopy(state["subproblems"]["Q1"])
    dependencies = {
        "Q1": [], "Q2": [("Q1", "model")], "Q3": [("Q2", "model")],
        "Q4": [], "Q5": [("Q1", "result")],
    }
    sections = []
    for question, edges in dependencies.items():
        typed = [{"question": source, "kind": kind} for source, kind in edges]
        state["subproblems"][question] = dict(deepcopy(prototype), depends_on=typed)
        identity = dict(identity_payload(), question=question, dependencies=typed)
        if question == "Q2":
            identity["dependencies"] = [dict(typed[0], selector=name) for name in ("objective", "C1")]
        section = framework(identity, question=question).split("## 各问模型与结果\n", 1)[1]
        sections.append(section)
    return write_project(root, state, "# 模型论文框架\n## 各问模型与结果\n" + "\n".join(sections))


class TestV900SemanticGovernance(unittest.TestCase):
    def test_duplicate_current_question_scope_blocks_governance_write(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = identity_payload()
            state_path = write_project(root, base_state(), framework(payload))
            self.assertEqual(SEMANTIC.validate_project(root, write=True, strict=True)["status"], "passed")
            before = state_path.read_bytes()
            changed = deepcopy(payload)
            changed["objective"]["sense"] = "maximize"
            (root / "模型论文框架.md").write_text(framework(changed) + framework(payload), encoding="utf-8")
            report = SEMANTIC.validate_project(root, write=True, strict=True)
            self.assertEqual(report["status"], "failed", report)
            self.assertTrue(any("duplicate" in item and "Q1" in item for item in report["issues"]), report)
            self.assertEqual(state_path.read_bytes(), before)
            self.assertNotIn("Q1", report["semantic_identity_hashes"])

    def test_canonical_key_collision_blocks_governance_write_without_legacy_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = identity_payload()
            payload["extensions"] = {"weights": {"1": "approved"}}
            state_path = write_project(root, base_state(), framework(payload))
            self.assertEqual(SEMANTIC.validate_project(root, write=True, strict=True)["status"], "passed")
            before = state_path.read_bytes()
            collision = deepcopy(payload)
            collision["extensions"]["weights"] = {1: "hidden", "1": "approved"}
            (root / "模型论文框架.md").write_text(framework(collision), encoding="utf-8")
            report = SEMANTIC.validate_project(root, write=True, strict=True)
            self.assertEqual(report["status"], "failed", report)
            self.assertTrue(any("key" in item and "collision" in item for item in report["issues"]), report)
            self.assertEqual(state_path.read_bytes(), before)
            self.assertNotIn("Q1", report["semantic_hashes"])
            self.assertNotIn("Q1", report["semantic_identity_hashes"])

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

    def test_dependency_conflict_names_edges_and_chain_without_advancing_baselines(self):
        for declarations, expected in (
            ([], ["Q1/model"]),
            ([{"question": "Q1", "kind": "result"}], ["Q1/model", "Q1/result"]),
            ([{"question": "Q4", "kind": "model"}], ["Q1/model", "Q4/model"]),
            (17, ["depends_on must be a list"]),
        ):
            with self.subTest(declarations=declarations), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                path = dependency_project(root)
                first = SEMANTIC.validate_project(root, write=True, strict=True)
                self.assertEqual(first["status"], "passed", first)
                self.assertEqual(first["affected_questions"], [])
                state = yaml.safe_load(path.read_bytes())
                original = state["subproblems"]["Q2"]["depends_on"]
                state["subproblems"]["Q2"]["depends_on"] = declarations
                path.write_text(yaml.safe_dump(state), encoding="utf-8")
                before = path.read_bytes()
                for write in (False, True):
                    report = SEMANTIC.validate_project(root, write=write, strict=True)
                    self.assertEqual(report["status"], "failed", report)
                    self.assertEqual(report["affected_questions"], ["Q2", "Q3"])
                    self.assertEqual(set(report["dependency_conflicts"]), {"Q2"})
                    detail = " ".join(report["dependency_conflicts"]["Q2"])
                    for label in expected:
                        self.assertIn(label, detail)
                    self.assertEqual(path.read_bytes(), before)

                # A source revision observed during disagreement must be replayable
                # once the operator reconciles State with the two selectors in the SIB.
                state["subproblems"]["Q1"]["semantic_revision"] = 2
                path.write_text(yaml.safe_dump(state), encoding="utf-8")
                conflicted = path.read_bytes()
                report = SEMANTIC.validate_project(root, write=True, strict=True)
                self.assertEqual(report["status"], "failed", report)
                self.assertEqual(path.read_bytes(), conflicted)
                state["subproblems"]["Q2"]["depends_on"] = original
                path.write_text(yaml.safe_dump(state), encoding="utf-8")
                repaired = SEMANTIC.validate_project(root, write=True, strict=True)
                self.assertEqual(repaired["status"], "passed", repaired)
                self.assertEqual(repaired["affected_questions"], ["Q1", "Q2", "Q3", "Q5"])

    def test_revision_only_change_uses_typed_propagation_and_refuses_regression(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = dependency_project(root)
            initial = SEMANTIC.validate_project(root, write=True, strict=True)
            self.assertEqual(initial["status"], "passed", initial)
            for revision, baseline, status in ((2, 2, "passed"), (1, 2, "failed")):
                state = yaml.safe_load(path.read_bytes())
                for entry in state["subproblems"].values():
                    entry.update(approved_semantic_identity_hash=entry["semantic_identity_hash"],
                                 approved_semantic_revision=entry["validated_semantic_revision"],
                                 model_challenge_status="passed", human_model_approval_status="approved")
                state["subproblems"]["Q1"]["semantic_revision"] = revision
                path.write_text(yaml.safe_dump(state), encoding="utf-8")
                before = path.read_bytes()
                preview = SEMANTIC.validate_project(root, write=False, strict=True)
                self.assertEqual(preview["changed_sources"], ["Q1"])
                self.assertEqual(path.read_bytes(), before)
                written = SEMANTIC.validate_project(root, write=True, strict=True)
                self.assertEqual(written["status"], status, written)
                self.assertEqual(written["affected_questions"], ["Q1", "Q2", "Q3", "Q5"])
                entries = yaml.safe_load(path.read_bytes())["subproblems"]
                self.assertEqual(entries["Q1"]["validated_semantic_revision"], baseline)
                for name in ("Q1", "Q2", "Q3"):
                    self.assertEqual(entries[name]["model_challenge_status"], "stale")
                    self.assertEqual(entries[name]["human_model_approval_status"], "stale")
                for name in ("Q4", "Q5"):
                    self.assertEqual(entries[name]["human_model_approval_status"], "approved")
                self.assertFalse(entries["Q4"]["artifacts_stale"])
                self.assertTrue(entries["Q5"]["artifacts_stale"])

    def test_previously_advanced_baseline_retires_old_approval_before_upstream_reapproval(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = dependency_project(root)
            self.assertEqual(SEMANTIC.validate_project(root, write=True, strict=True)["status"], "passed")
            baseline = yaml.safe_load(path.read_bytes())
            for entry in baseline["subproblems"].values():
                entry["approved_semantic_identity_hash"] = entry["semantic_identity_hash"]
            for anchor in ("revision", "identity"):
                with self.subTest(previous_approval=anchor):
                    state = deepcopy(baseline)
                    q1 = state["subproblems"]["Q1"]
                    if anchor == "revision":
                        q1.update(semantic_revision=2, validated_semantic_revision=2)
                    else:
                        q1["approved_semantic_identity_hash"] = "f" * 64
                    path.write_text(yaml.safe_dump(state), encoding="utf-8")
                    report = SEMANTIC.validate_project(root, write=True, strict=True)
                    self.assertEqual(report["status"], "passed", report)
                    self.assertEqual(report["changed_sources"], ["Q1"])
                    rows = yaml.safe_load(path.read_bytes())["subproblems"]
                    for name in ("Q1", "Q2", "Q3"):
                        self.assertEqual(rows[name]["human_model_approval_status"], "stale")
                    for name in ("Q4", "Q5"):
                        self.assertEqual(rows[name]["human_model_approval_status"], "approved")

                    # Re-binding only the upstream model cannot revive its dependents.
                    saved = yaml.safe_load(path.read_bytes())
                    q1 = saved["subproblems"]["Q1"]
                    q1.update(model_challenge_status="passed", human_model_approval_status="approved",
                              approved_semantic_revision=q1["semantic_revision"],
                              approved_semantic_identity_hash=q1["semantic_identity_hash"])
                    path.write_text(yaml.safe_dump(saved), encoding="utf-8")
                    again = SEMANTIC.validate_project(root, write=True, strict=True)
                    self.assertEqual(again["changed_sources"], [])
                    rows = yaml.safe_load(path.read_bytes())["subproblems"]
                    self.assertEqual(rows["Q1"]["human_model_approval_status"], "approved")
                    self.assertEqual(rows["Q2"]["human_model_approval_status"], "stale")

            for status, complete in (("pending", True), ("stale", True), ("approved", False)):
                with self.subTest(approval_status=status, recorded=complete):
                    state = deepcopy(baseline)
                    q1 = state["subproblems"]["Q1"]
                    q1.update(semantic_revision=2, validated_semantic_revision=2,
                              human_model_approval_status=status)
                    if not complete:
                        del q1["approved_semantic_identity_hash"]
                    path.write_text(yaml.safe_dump(state), encoding="utf-8")
                    report = SEMANTIC.validate_project(root, write=True, strict=True)
                    self.assertEqual(report["affected_questions"], [], report)

    def test_invalid_revision_cannot_preserve_approval_through_integer_equality(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = dependency_project(root)
            first = SEMANTIC.validate_project(root, write=True, strict=True)
            self.assertEqual(first["status"], "passed", first)
            previous = yaml.safe_load(path.read_bytes())
            for bad in (True, 0, None):
                with self.subTest(invalid_revision=bad):
                    state = deepcopy(previous)
                    entry = state["subproblems"]["Q1"]
                    if bad is None:
                        del entry["semantic_revision"]
                    else:
                        entry["semantic_revision"] = bad
                    path.write_text(yaml.safe_dump(state), encoding="utf-8")
                    report = SEMANTIC.validate_project(root, write=True, strict=True)
                    self.assertEqual(report["status"], "failed", report)
                    self.assertIn("Q3", report["affected_questions"])
                    rows = yaml.safe_load(path.read_bytes())["subproblems"]
                    self.assertEqual(rows["Q3"]["human_model_approval_status"], "stale")
                    self.assertEqual(rows["Q1"]["validated_semantic_revision"], 1)
                    self.assertEqual(rows["Q4"]["human_model_approval_status"], "approved")

    def test_legacy_string_and_missing_revision_baseline_keep_compatibility(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = dependency_project(root)
            state = yaml.safe_load(path.read_bytes())
            state["subproblems"]["Q2"]["depends_on"] = ["Q1"]
            path.write_text(yaml.safe_dump(state), encoding="utf-8")
            initial = SEMANTIC.validate_project(root, write=True, strict=True)
            self.assertEqual(initial["status"], "passed", initial)
            state = yaml.safe_load(path.read_bytes())
            q1 = state["subproblems"]["Q1"]
            q1.pop("validated_semantic_revision")
            q1["semantic_revision"] = 3
            path.write_text(yaml.safe_dump(state), encoding="utf-8")
            filled = SEMANTIC.validate_project(root, write=True, strict=True)
            self.assertEqual(filled["status"], "passed", filled)
            self.assertEqual(filled["affected_questions"], [])
            state = yaml.safe_load(path.read_bytes())
            self.assertNotIn("approved_semantic_identity_hash", state["subproblems"]["Q1"])
            state["subproblems"]["Q1"]["semantic_revision"] = 4
            path.write_text(yaml.safe_dump(state), encoding="utf-8")
            updated = SEMANTIC.validate_project(root, write=True, strict=True)
            self.assertEqual(updated["status"], "passed", updated)
            state = yaml.safe_load(path.read_bytes())
            self.assertEqual(state["subproblems"]["Q2"]["depends_on"], ["Q1"])
            self.assertEqual(state["subproblems"]["Q2"]["human_model_approval_status"], "stale")

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
