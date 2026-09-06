"""Characterize v8.7.4 boundaries before the staged v9.0.0 runtime/state refactor.

Tests that still describe known deficiencies remain characterization coverage; fixed
boundaries are converted in place to regression expectations as each phase lands.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative_path: str):
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


RUNTIME_ASSURANCE = load_module(
    "v900_runtime_assurance_characterization", "scripts/runtime_assurance.py"
)
SEMANTIC = load_module(
    "v900_semantic_governance_characterization",
    "scripts/validate_semantic_governance.py",
)
SYNC = load_module("v900_sync_project_characterization", "scripts/sync_project.py")
CODE_DELIVERY = load_module(
    "v900_code_delivery_characterization", "scripts/validate_code_delivery.py"
)
STATE_TRANSITIONS = load_module(
    "v900_state_transitions_characterization", "scripts/state_transitions.py"
)
STATE_TRANSITION_CONTRACT = yaml.safe_load(
    (ROOT / "core/state_transition_contract.yaml").read_text(encoding="utf-8")
)


FRAMEWORK = """# 模型论文框架
## 当前有效口径
## 各问模型与结果
### Q1：第一问
#### 当前模型口径
**题意口径合同（Problem Contract）**
- 原始对象：A
- 目标：min f(x)
**题面—数学—代码语义闭环**
|题面|数学|Python|输出|状态|
|A|x|x|核心指标|closed|
**复杂度合理性复审**
- 复审结论：passed
#### 结果摘要
待求解。
## 图表证据链
## 待办与缺口
"""


def semantic_subproblem() -> dict:
    return {
        "status": "designed",
        "problem_contract_status": "frozen",
        "semantic_closure_status": "passed",
        "complexity_sanity_status": "passed",
        "complexity_sanity_flags": [],
        "complexity_sanity_note": "复审完成。",
        "semantic_revision": 1,
        "semantic_change_categories": ["initial_design"],
        "depends_on": [],
        "model_challenge_status": "passed",
        "human_model_approval_status": "approved",
        "result_quality_status": "passed",
        "result_analysis_status": "passed",
        "validation_status": "passed",
        "result_summary_status": "current",
        "artifacts_stale": False,
        "stale_layers": [],
        "primary_execution_status": "accepted",
        "analysis_execution_status": "accepted",
    }


class TestV900RefactorCharacterization(unittest.TestCase):
    """Track v8.7.4 boundaries as the staged v9 refactor replaces them."""

    def test_locked_model_assurance_rejects_state_only_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "state").mkdir()
            state_hash = "a" * 64
            state = {
                "project": {
                    "competition": "CUMCM",
                    "problem": "A",
                    "current_phase": "solve_validate",
                },
                "preprocessing": {
                    "decision": "not_needed",
                    "status": "not_applicable",
                },
                "subproblems": {
                    "Q1": {
                        "classification": {
                            "objective": "optimization",
                            "structures": [],
                        },
                        "capabilities": {},
                        "model_challenge_status": "passed",
                        "human_model_approval_status": "approved",
                        "semantic_revision": 3,
                        "semantic_hash": state_hash,
                        "approved_semantic_revision": 3,
                        "approved_semantic_hash": state_hash,
                        "primary_execution_status": "pending",
                        "analysis_execution_status": "pending",
                        "result_quality_status": "pending",
                        "result_analysis_status": "pending",
                    }
                },
            }
            (root / "state" / "project_state.yaml").write_text(
                yaml.safe_dump(state, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            # Deliberately write current framework semantics that cannot hash to state_hash.
            (root / "模型论文框架.md").write_text(FRAMEWORK, encoding="utf-8")

            hydrated = RUNTIME_ASSURANCE.hydrate_project_context(root, "Q1")
            row = next(
                item
                for item in hydrated["artifact_evidence"]
                if item["artifact"] == "locked_model_spec"
            )

        self.assertNotIn("locked_model_spec", hydrated["verified_artifacts"])
        self.assertEqual(row["status"], "stale")
        self.assertEqual(row["source"], "framework+project_state")
        self.assertEqual(row["path"], "模型论文框架.md")
        self.assertEqual(row["expected_sha256"], state_hash)
        self.assertIsNotNone(row["actual_sha256"])
        self.assertNotEqual(row["actual_sha256"], state_hash)

    def test_wording_only_framework_edit_currently_changes_semantic_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "state").mkdir()
            (root / "模型论文框架.md").write_text(FRAMEWORK, encoding="utf-8")
            state = {
                "semantic_governance_version": "1.0.0",
                "subproblems": {"Q1": semantic_subproblem()},
            }
            state_path = root / "state" / "project_state.yaml"
            state_path.write_text(
                yaml.safe_dump(state, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )

            first = SEMANTIC.validate_project(root, write=True, strict=True)
            self.assertEqual(first["status"], "passed", first)
            before = yaml.safe_load(state_path.read_text(encoding="utf-8"))["subproblems"]["Q1"][
                "validated_semantic_hash"
            ]

            # Punctuation-only prose change inside the current semantic scope.
            changed = (root / "模型论文框架.md").read_text(encoding="utf-8").replace(
                "- 复审结论：passed", "- 复审结论：passed。"
            )
            (root / "模型论文框架.md").write_text(changed, encoding="utf-8")
            report = SEMANTIC.validate_project(root, write=False, strict=True)
            section = SEMANTIC._semantic_scope(
                SEMANTIC._question_sections(changed)["Q1"]
            )
            assert section is not None
            after = SEMANTIC.sha256_text(section)

        self.assertNotEqual(before, after)
        self.assertEqual(report["changed_sources"], ["Q1"])
        self.assertEqual(report["status"], "failed")
        self.assertTrue(
            any("semantic_revision未递增" in item for item in report["issues"]),
            report,
        )

    def test_dependency_kind_now_controls_transition_propagation(self):
        state = {
            "subproblems": {
                "Q1": semantic_subproblem(),
                "Q2": {**semantic_subproblem(), "depends_on": [{"question": "Q1", "kind": "result"}]},
                "Q3": {**semantic_subproblem(), "depends_on": [{"question": "Q1", "kind": "model"}]},
                "Q4": {**semantic_subproblem(), "depends_on": [{"question": "Q2", "kind": "data"}]},
            }
        }
        report = STATE_TRANSITIONS.apply_transition(
            state,
            event="semantic_identity_changed",
            source_question="Q1",
            contract=STATE_TRANSITION_CONTRACT,
            context={"semantic_change_categories": ["objective"]},
        )
        self.assertEqual(report["affected_questions"], ["Q1", "Q2", "Q3"])
        self.assertNotIn("Q4", report["affected_questions"])
        self.assertEqual(state["subproblems"]["Q2"]["human_model_approval_status"], "approved")
        self.assertEqual(state["subproblems"]["Q3"]["human_model_approval_status"], "stale")

    def test_stale_rules_now_have_one_shared_engine(self):
        for module in (SEMANTIC, SYNC, CODE_DELIVERY):
            self.assertFalse(hasattr(module, "PRIMARY_STALE_LAYERS"))
            self.assertFalse(hasattr(module, "ANALYSIS_STALE_LAYERS"))
        for relative in (
            "scripts/validate_semantic_governance.py",
            "scripts/sync_project.py",
            "scripts/validate_code_delivery.py",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("STATE_TRANSITIONS", text)
        contract = (ROOT / "core/state_transition_contract.yaml").read_text(encoding="utf-8")
        self.assertIn("semantic_identity_changed", contract)
        self.assertIn("legacy_untyped", contract)

    def test_artifact_hash_primary_code_now_has_explicit_implementation_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result_dir = root / "问题一求解"
            result_dir.mkdir(parents=True)
            primary = result_dir / "问题一求解.py"
            primary.write_text(
                "def main():\n    return 1\n\nif __name__ == '__main__':\n    main()\n",
                encoding="utf-8",
            )
            (root / "模型论文框架.md").write_text(
                "# 模型论文框架\n\n### Q1\n",
                encoding="utf-8",
            )
            schema = SYNC.load_yaml(SYNC.DEFAULT_SCHEMA_PATH)
            snapshot = SYNC._snapshot_question(
                root,
                "问题一",
                {"status": "designed", "framework_section": "### Q1"},
                schema,
                None,
                None,
            )

        self.assertEqual(
            snapshot["artifact_hashes"]["primary_code"], snapshot["primary_code_sha256"]
        )
        self.assertNotIn("model", snapshot["artifact_hashes"])


if __name__ == "__main__":
    unittest.main()
