from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import validate_semantic_governance as SEMANTIC
from tests.test_v900_semantic_governance import identity_payload


def subproblem() -> dict:
    return {
        "status": "designed",
        "problem_contract_status": "frozen",
        "semantic_closure_status": "passed",
        "complexity_sanity_status": "passed",
        "complexity_sanity_flags": [],
        "complexity_sanity_note": "review complete",
        "semantic_revision": 1,
        "semantic_change_categories": ["initial_design"],
        "depends_on": [],
        "result_quality_status": "pending",
        "result_analysis_status": "pending",
        "result_summary_status": "pending",
        "artifacts_stale": False,
        "stale_layers": [],
    }


def mixed_framework() -> str:
    payload = identity_payload()
    payload["question"] = "Q1"
    identity_yaml = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    return f"""# 模型论文框架
## 各问模型与结果
### Q1：structured
#### 当前模型口径
<!-- HSK_SEMANTIC_IDENTITY_BEGIN Q1 -->
```yaml
{identity_yaml}```
<!-- HSK_SEMANTIC_IDENTITY_END Q1 -->
structured prose
#### 结果摘要
pending
### Q2：legacy
#### 当前模型口径
- 目标：min g(y)
- 说明：legacy historical model
#### 结果摘要
pending
"""


class PhaseII2LegacyWriterRetirementBehaviorTests(unittest.TestCase):
    def test_mixed_project_blocks_entire_semantic_write_transaction(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "state").mkdir()
            state_path = root / "state/project_state.yaml"
            state = {
                "semantic_governance_version": "1.0.0",
                "project": {
                    "competition": "test",
                    "problem": "A",
                    "current_phase": "model_design",
                    "state_generation": 7,
                },
                "subproblems": {
                    "Q1": subproblem(),
                    "Q2": subproblem(),
                },
                "paper_framework": {"paper_fragments": [], "sync_status": "current"},
            }
            state_path.write_text(
                yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            (root / "模型论文框架.md").write_text(mixed_framework(), encoding="utf-8")
            before = state_path.read_text(encoding="utf-8")

            report = SEMANTIC.validate_project(root, write=True, strict=True)
            after = state_path.read_text(encoding="utf-8")
            saved = yaml.safe_load(after)

        self.assertEqual(report["status"], "failed", report)
        self.assertEqual(
            report["identity_modes"],
            {"Q1": "semantic_identity_v1", "Q2": "legacy_text_hash"},
        )
        self.assertEqual(report["legacy_write_blocked_sources"], ["Q2"])
        self.assertEqual(report["migration_sources"], ["Q1", "Q2"])
        self.assertEqual(before, after)
        self.assertEqual(saved["project"]["state_generation"], 7)
        self.assertNotIn("semantic_identity_hash", saved["subproblems"]["Q1"])
        self.assertNotIn("semantic_text_hash", saved["subproblems"]["Q1"])
        self.assertNotIn("semantic_hash", saved["subproblems"]["Q2"])
        self.assertNotIn("validated_semantic_hash", saved["subproblems"]["Q2"])


if __name__ == "__main__":
    unittest.main()
