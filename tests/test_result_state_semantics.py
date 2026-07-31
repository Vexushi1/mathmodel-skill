import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestResultStateSemantics(unittest.TestCase):
    def test_redo_required_allows_semantic_downstream_stale_layers(self):
        validator = load_module(
            "state_semantics_validator", ROOT / "scripts/validate_project_state.py"
        )
        digest = "a" * 64
        state = {
            "result_quality_status": "passed",
            "result_analysis_status": "redo_required",
            "artifact_hashes": {"result_analysis_workbook": digest},
            "validated_artifact_hashes": {"result_analysis_workbook": digest},
            "artifacts_stale": True,
            "stale_layers": [
                "result_analysis_workbook",
                "matlab_script",
                "figure_bundle",
                "framework",
            ],
        }
        issues = validator._validate_hashes("Q1", state, "designed")
        self.assertFalse(any("must equal changed validated layers" in issue for issue in issues), issues)
        self.assertFalse(any("must be non-empty for semantic stale" in issue for issue in issues), issues)

    def test_ordinary_hash_stale_still_requires_exact_changed_layers(self):
        validator = load_module(
            "state_hash_validator", ROOT / "scripts/validate_project_state.py"
        )
        state = {
            "result_quality_status": "pending",
            "result_analysis_status": "pending",
            "artifact_hashes": {"model": "a" * 64},
            "validated_artifact_hashes": {"model": "b" * 64},
            "artifacts_stale": True,
            "stale_layers": ["model", "framework"],
        }
        issues = validator._validate_hashes("Q1", state, "designed")
        self.assertTrue(any("must equal changed validated layers" in issue for issue in issues), issues)

    def test_formal_results_require_both_passed_states(self):
        syncer = load_module("sync_state_gate", ROOT / "scripts/sync_project.py")
        required = {"result_quality_report", "result_analysis_report"}
        state = {
            "subproblems": {
                "Q1": {
                    "result_quality_status": "passed",
                    "result_analysis_status": "failed",
                    "artifacts_stale": False,
                }
            }
        }
        issues = syncer._formal_state_issues(required, state)
        self.assertTrue(any("result_analysis_status=passed" in issue for issue in issues), issues)
        self.assertFalse(any("result_quality_status=passed" in issue for issue in issues), issues)

    def test_downstream_delivery_rejects_stale_results(self):
        syncer = load_module("sync_stale_gate", ROOT / "scripts/sync_project.py")
        required = {"approved_figures"}
        state = {
            "subproblems": {
                "Q1": {
                    "result_quality_status": "passed",
                    "result_analysis_status": "passed",
                    "artifacts_stale": True,
                }
            }
        }
        issues = syncer._formal_state_issues(required, state)
        self.assertTrue(any("禁止使用 stale 结果" in issue for issue in issues), issues)


if __name__ == "__main__":
    unittest.main()
