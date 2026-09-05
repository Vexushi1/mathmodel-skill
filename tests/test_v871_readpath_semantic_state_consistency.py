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
FINAL_REVIEW_TEMPLATE = ROOT / "templates" / "review" / "final_review_matrix.yaml"


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


if __name__ == "__main__":
    unittest.main()
