from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "core" / "bootstrap.yaml"
REASONING = ROOT / "core" / "writing_reasoning_contract.yaml"
RUNTIME = ROOT / "core" / "writing_runtime_contract.yaml"
MODEL_DESIGN = ROOT / "modules" / "02_model_design.md"
FRAMEWORK = ROOT / "templates" / "model" / "model_paper_framework.md"
FINAL_REVIEW_TEMPLATE = ROOT / "templates" / "review" / "final_review_matrix.yaml"
FORMULA_TRACE_HEADER = (
    "| Formula ID | 对应小问 | Role | Source | Depends on | Derivation | "
    "Destination | 代码/证据锚点 | 状态 |"
)


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TestV871ReadPathSemanticStateConsistency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bootstrap = load_yaml(BOOTSTRAP)
        cls.reasoning = load_yaml(REASONING)
        cls.runtime = load_yaml(RUNTIME)
        cls.model_design = read(MODEL_DESIGN)
        cls.framework = read(FRAMEWORK)
        cls.review_template = load_yaml(FINAL_REVIEW_TEMPLATE)
        cls.scorer = load_module("score_submission_v871", ROOT / "scripts" / "score_submission.py")
        cls.review_config = json.loads((ROOT / "config" / "review_weights.json").read_text(encoding="utf-8"))

    def _hydrated_review_report(self) -> dict:
        report = copy.deepcopy(self.review_template)
        context = report["review_context"]
        context.update(
            skill_version=str(self.bootstrap["skill_version"]),
            competition_profile="demo",
            edition="2026",
            rule_verification_status="verified",
            rule_verified_at="2026-09-05",
            rule_source="https://example.invalid/official-rules",
            delivery_mode="reproducibility",
            source_bundle_sha256="a" * 64,
            compiled_pdf_sha256="b" * 64,
        )
        for entry in report["coverage"]:
            entry["status"] = "passed"
            entry["evidence"] = f"review evidence for {entry['check_family']}"
        report["scores"] = {name: 80 for name in self.review_config["dimensions"]}
        report["evidence"] = {name: f"evidence:{name}" for name in self.review_config["dimensions"]}
        return report

    def test_active_review_template_does_not_pin_historical_skill_release(self):
        self.assertIsNone(self.review_template["review_context"]["skill_version"])
        text = read(FINAL_REVIEW_TEMPLATE)
        self.assertNotIn("skill_version: 8.3.0", text)

    def test_unhydrated_review_template_cannot_be_scored_as_final(self):
        report = self._hydrated_review_report()
        report["review_context"]["skill_version"] = None
        with self.assertRaisesRegex(ValueError, "review_context.skill_version is required"):
            self.scorer.score_submission(self.review_config, report)

    def test_review_template_hydrates_from_current_bootstrap_and_scores(self):
        report = self._hydrated_review_report()
        result = self.scorer.score_submission(self.review_config, report)
        self.assertEqual(report["review_context"]["skill_version"], str(self.bootstrap["skill_version"]))
        self.assertEqual(result["review_status"], "passed")

    def test_module02_formula_trace_producer_matches_current_framework_columns(self):
        self.assertIn(FORMULA_TRACE_HEADER, self.model_design)
        self.assertIn(FORMULA_TRACE_HEADER, self.framework)
        self.assertIn("不得把缺失角色拖到写作阶段再凭上下文猜测", self.model_design)

    def test_module02_formula_trace_covers_reasoning_required_fields(self):
        required = set(self.reasoning["formula_reasoning_chain"]["internal_trace"]["required_fields"])
        field_map = {
            "formula_id": "Formula ID",
            "question": "对应小问",
            "role": "Role",
            "source": "Source",
            "derivation": "Derivation",
            "destination": "Destination",
            "status": "状态",
        }
        self.assertTrue(required.issubset(field_map))
        for field in required:
            self.assertIn(field_map[field], FORMULA_TRACE_HEADER)

    def test_formula_role_semantics_remain_single_sourced(self):
        taxonomy = self.reasoning["formula_reasoning_chain"]["formula_role_taxonomy"]
        self.assertEqual(
            [
                "final_model_relation",
                "key_bridge_relation",
                "supporting_derivation",
                "routine_algebra",
            ],
            taxonomy["values"],
        )
        section = self.model_design.split("### 4.1 核心 Formula Trace", 1)[1].split("### 4.2", 1)[0]
        self.assertIn("唯一定义", section)
        self.assertIn("routine_algebra", section)
        self.assertNotIn("final_model_relation =", section)
        self.assertNotIn("key_bridge_relation =", section)

    def test_proposition_preflight_has_question_scoped_derivation_sources(self):
        proposition = self.runtime["per_question_writing_capability_preflight"]["activation"]["proposition_proof"]
        self.assertEqual("derived_current_question_proposition_state", proposition["state_source"])
        derivation = proposition["state_derivation"]
        self.assertIn("paper_framework.proposition_status", derivation["global_plan_source"])
        self.assertIn("related_question=current_question", derivation["item_source"])
        self.assertIn("逐问写作能力预检", derivation["framework_projection_source"])
        self.assertEqual("current_question_proposition_plan", derivation["output"])

    def test_proposition_state_derivation_preserves_missing_stale_and_question_scope(self):
        proposition = self.runtime["per_question_writing_capability_preflight"]["activation"]["proposition_proof"]
        derivation = proposition["state_derivation"]
        rules = "\n".join(derivation["rules"])
        self.assertIn("派生为 missing", rules)
        self.assertIn("related_question", rules)
        self.assertIn("其他小问", rules)
        self.assertIn("存在 stale 命题项", rules)
        self.assertIn("存在 current 命题项", rules)
        self.assertIn("仅有 candidate", rules)
        self.assertIn("显式 removed", rules)
        self.assertIn("review_required", rules)
        self.assertIn("不能覆盖 stale/missing/review_required", rules)
        self.assertEqual("needs_adjudication", proposition["rules"]["missing"]["status"])
        self.assertEqual("review_required", proposition["rules"]["stale"]["status"])

    def test_proposition_state_vocabularies_are_explicitly_separated(self):
        derivation = self.runtime["per_question_writing_capability_preflight"]["activation"]["proposition_proof"]["state_derivation"]
        self.assertEqual(
            ["candidate", "current", "stale", "removed"],
            derivation["item_status_values"],
        )
        self.assertEqual(
            ["not_assessed", "planned", "current", "stale"],
            derivation["global_plan_status_values"],
        )
        self.assertIn("planned", derivation["projection_status_values"])
        self.assertIn("removed", derivation["projection_status_values"])
        self.assertIn("missing", derivation["projection_status_values"])


if __name__ == "__main__":
    unittest.main()
