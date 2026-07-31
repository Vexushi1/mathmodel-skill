import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_state_validator():
    spec = importlib.util.spec_from_file_location(
        "state_semantics_validator", ROOT / "scripts/validate_project_state.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestResultStateSemantics(unittest.TestCase):
    def test_redo_required_allows_semantic_downstream_stale_layers(self):
        validator = load_state_validator()
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
        validator = load_state_validator()
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


if __name__ == "__main__":
    unittest.main()
