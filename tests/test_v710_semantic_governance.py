from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_semantic_governance.py"
SPEC = importlib.util.spec_from_file_location("semantic_governance", MODULE_PATH)
SEMANTIC = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SEMANTIC)


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
### Q2：第二问
#### 当前模型口径
**题意口径合同（Problem Contract）**
- 原始对象：B
- 目标：min g(y)
**题面—数学—代码语义闭环**
|题面|数学|Python|输出|状态|
|B|y|y|核心指标|closed|
**复杂度合理性复审**
- 复审结论：passed
#### 结果摘要
待求解。
### Q3：第三问
#### 当前模型口径
**题意口径合同（Problem Contract）**
- 原始对象：C
- 目标：min h(z)
**题面—数学—代码语义闭环**
|题面|数学|Python|输出|状态|
|C|z|z|核心指标|closed|
**复杂度合理性复审**
- 复审结论：passed
#### 结果摘要
待求解。
## 图表证据链
## 待办与缺口
"""


def subproblem(*, depends_on=None, complexity="passed", revision=1, category="initial_design"):
    return {
        "status": "designed",
        "problem_contract_status": "frozen",
        "semantic_closure_status": "passed",
        "complexity_sanity_status": complexity,
        "complexity_sanity_flags": [],
        "complexity_sanity_note": "复审完成。",
        "semantic_revision": revision,
        "semantic_change_categories": [category],
        "depends_on": depends_on or [],
        "result_quality_status": "passed",
        "result_analysis_status": "passed",
        "validation_status": "passed",
        "result_summary_status": "current",
        "artifacts_stale": False,
        "stale_layers": [],
        "primary_execution_status": "accepted",
        "analysis_execution_status": "accepted",
    }


class SemanticGovernanceTests(unittest.TestCase):
    def make_project(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / "state").mkdir()
        (root / "模型论文框架.md").write_text(FRAMEWORK, encoding="utf-8")
        state = {
            "semantic_governance_version": "1.0.0",
            "subproblems": {
                "Q1": subproblem(),
                "Q2": subproblem(depends_on=[{"question": "Q1", "kind": "model", "note": "继承Q1模型"}]),
                "Q3": subproblem(depends_on=[{"question": "Q2", "kind": "result", "note": "使用Q2结果"}]),
            },
        }
        (root / "state" / "project_state.yaml").write_text(
            yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        return temp, root

    def read_state(self, root: Path):
        return yaml.safe_load((root / "state" / "project_state.yaml").read_text(encoding="utf-8"))

    def test_missing_problem_freeze_blocks_gate(self):
        temp, root = self.make_project()
        self.addCleanup(temp.cleanup)
        state = self.read_state(root)
        state["subproblems"]["Q1"]["problem_contract_status"] = "pending"
        (root / "state" / "project_state.yaml").write_text(
            yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        report = SEMANTIC.validate_project(root, write=False, strict=True)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(any("problem_contract_status" in item for item in report["issues"]))

    def test_complexity_review_required_blocks_gate(self):
        temp, root = self.make_project()
        self.addCleanup(temp.cleanup)
        state = self.read_state(root)
        state["subproblems"]["Q1"]["complexity_sanity_status"] = "review_required"
        state["subproblems"]["Q1"]["complexity_sanity_flags"] = ["implausibly_easy_computation"]
        (root / "state" / "project_state.yaml").write_text(
            yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        report = SEMANTIC.validate_project(root, write=False, strict=True)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(any("complexity_sanity_status" in item for item in report["issues"]))

    def test_first_valid_run_accepts_semantic_hashes(self):
        temp, root = self.make_project()
        self.addCleanup(temp.cleanup)
        report = SEMANTIC.validate_project(root, write=True, strict=True)
        self.assertEqual(report["status"], "passed")
        state = self.read_state(root)
        for key in ("Q1", "Q2", "Q3"):
            self.assertEqual(len(state["subproblems"][key]["validated_semantic_hash"]), 64)
            self.assertEqual(state["subproblems"][key]["validated_semantic_revision"], 1)

    def test_semantic_change_propagates_stale_through_dependency_chain(self):
        temp, root = self.make_project()
        self.addCleanup(temp.cleanup)
        first = SEMANTIC.validate_project(root, write=True, strict=True)
        self.assertEqual(first["status"], "passed")

        framework = (root / "模型论文框架.md").read_text(encoding="utf-8")
        framework = framework.replace("- 目标：min f(x)", "- 目标：min f(x)+lambda*r(x)")
        (root / "模型论文框架.md").write_text(framework, encoding="utf-8")
        state = self.read_state(root)
        state["subproblems"]["Q1"]["semantic_revision"] = 2
        state["subproblems"]["Q1"]["semantic_change_categories"] = ["objective"]
        (root / "state" / "project_state.yaml").write_text(
            yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )

        report = SEMANTIC.validate_project(root, write=True, strict=True)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["changed_sources"], ["Q1"])
        self.assertEqual(report["affected_questions"], ["Q1", "Q2", "Q3"])

        state = self.read_state(root)
        for key in ("Q1", "Q2", "Q3"):
            entry = state["subproblems"][key]
            self.assertTrue(entry["artifacts_stale"])
            self.assertEqual(entry["result_quality_status"], "pending")
            self.assertEqual(entry["result_analysis_status"], "pending")
            self.assertEqual(entry["result_summary_status"], "stale")
        self.assertEqual(state["subproblems"]["Q1"]["validated_semantic_revision"], 2)

    def test_semantic_change_without_revision_increment_fails(self):
        temp, root = self.make_project()
        self.addCleanup(temp.cleanup)
        self.assertEqual(SEMANTIC.validate_project(root, write=True, strict=True)["status"], "passed")
        framework = (root / "模型论文框架.md").read_text(encoding="utf-8")
        framework = framework.replace("- 目标：min f(x)", "- 目标：max f(x)")
        (root / "模型论文框架.md").write_text(framework, encoding="utf-8")
        state = self.read_state(root)
        state["subproblems"]["Q1"]["semantic_change_categories"] = ["objective"]
        (root / "state" / "project_state.yaml").write_text(
            yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        report = SEMANTIC.validate_project(root, write=False, strict=True)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(any("semantic_revision未递增" in item for item in report["issues"]))


if __name__ == "__main__":
    unittest.main()
