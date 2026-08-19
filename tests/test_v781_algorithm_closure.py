from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TestV781AlgorithmClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = load_module(
            "v781_framework_validator", ROOT / "scripts/validate_model_paper_framework.py"
        )
        cls.router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        cls.full_submission = (ROOT / "packs/artifact/full_submission.md").read_text(encoding="utf-8")
        cls.review_module = (ROOT / "modules/06_review_delivery.md").read_text(encoding="utf-8")
        cls.review_pack = (ROOT / "packs/artifact/review.md").read_text(encoding="utf-8")

    @staticmethod
    def framework(mode: str, linked: str = "", trace_mode: str | None = None, *, python_anchor: str = "solve_q1()", trace_status: str = "current", blank_role: bool = False) -> str:
        rows = ""
        if trace_mode is not None:
            role = "" if blank_role else "求解测试问题"
            rows = (
                "### Algorithm Trace\n\n"
                "| Algorithm ID | 小问 | 作用 | 输入/状态 | 核心操作 | 循环/分支/阶段 | Formula/Proposition/Constraint 锚点 | 终止条件 | 输出 | Python 锚点 | 呈现模式 | 状态 |\n"
                "|---|---|---|---|---|---|---|---|---|---|---|---|\n"
                f"| A1 | Q1 | {role} | x | 更新 x | 阶段转换 | F1 | 收敛 | y | {python_anchor} | {trace_mode} | {trace_status} |\n\n"
            )
        linked_line = f"- 关联 Algorithm ID：`{linked}`\n" if linked else "- 关联 Algorithm ID：\n"
        return (
            "# 模型论文框架\n\n"
            "> 本文件只保留当前有效项目事实。\n\n"
            "## 当前有效口径\n\n"
            f"{rows}"
            "## 各问模型与结果\n\n"
            "### Q1：测试\n\n"
            f"- 算法流程呈现：`{mode}`\n"
            f"{linked_line}\n"
            "#### 结果摘要\n\n"
            "Q1.result.current\n\n"
            "## 图表证据链\n\n"
            "## 待办与缺口\n"
        )

    def test_stepwise_requires_linked_current_trace(self):
        issues = self.validator.validate_framework_text(self.framework("stepwise"))
        self.assertTrue(any("has no 关联 Algorithm ID" in issue for issue in issues))

        issues = self.validator.validate_framework_text(
            self.framework("stepwise", "A1", "pseudocode")
        )
        self.assertTrue(any("does not match A1 mode" in issue for issue in issues))

        issues = self.validator.validate_framework_text(
            self.framework("stepwise", "A1", "stepwise", trace_status="stale")
        )
        self.assertTrue(any("non-current Algorithm Trace" in issue for issue in issues))

    def test_current_trace_requires_structural_fields(self):
        issues = self.validator.validate_framework_text(
            self.framework("pseudocode", "A1", "pseudocode", blank_role=True)
        )
        self.assertTrue(any("missing required fields" in issue for issue in issues))

    def test_not_needed_does_not_require_algorithm_trace(self):
        issues = self.validator.validate_framework_text(self.framework("not_needed"))
        self.assertFalse(any("Algorithm" in issue or "算法流程呈现" in issue for issue in issues), issues)

    def test_not_needed_rejects_stale_link(self):
        issues = self.validator.validate_framework_text(
            self.framework("not_needed", "A1", "stepwise")
        )
        self.assertTrue(any("not_needed but still links" in issue for issue in issues))

    def test_solved_trace_requires_python_anchor(self):
        text = self.framework("stepwise", "A1", "stepwise", python_anchor="")
        state = {
            "paper_framework": {"mode": "compact"},
            "subproblems": {
                "Q1": {
                    "status": "solved",
                    "framework_section": "### Q1：测试",
                    "result_summary_status": "current",
                    "result_summary_anchor": "#### 结果摘要",
                    "proposition_refs": [],
                    "artifacts_stale": False,
                }
            },
        }
        issues = self.validator.validate_framework_text(text, state=state)
        self.assertTrue(any("requires a Python code anchor" in issue for issue in issues))

    def test_analyzed_status_requires_current_result_summary(self):
        text = self.framework("not_needed")
        state = {
            "paper_framework": {"mode": "compact"},
            "subproblems": {
                "Q1": {
                    "status": "analyzed",
                    "framework_section": "### Q1：测试",
                    "result_summary_status": "stale",
                    "result_summary_anchor": "#### 结果摘要",
                    "proposition_refs": [],
                    "artifacts_stale": True,
                }
            },
        }
        issues = self.validator.validate_framework_text(text, state=state)
        self.assertTrue(any("result_summary_status must be current when status is analyzed" in issue for issue in issues))

    def test_writing_and_review_routes_load_algorithm_pack_and_authority(self):
        routing = self.router["routing"]
        for name in ("latex", "docx", "review", "full_submission"):
            self.assertIn("packs/artifact/algorithm_flow.md", routing[name]["load"], name)
        self.assertNotIn(
            "packs/artifact/algorithm_flow.md",
            routing["full_workflow"]["load"],
            "full_workflow must stop at the initial code/user-execution boundary without preloading a writing-only pack",
        )
        for name in ("review", "full_submission"):
            self.assertIn("core/writing_reasoning_contract.yaml", routing[name]["load"], name)

    def test_submission_no_longer_restores_hard_proposition_cap(self):
        self.assertNotIn("命题数量允许为 0 且最多 4 个", self.full_submission)
        self.assertIn("0--4 仅是默认正文阅读预算", self.full_submission)
        self.assertIn("P5+", self.full_submission)

    def test_final_review_explicitly_consumes_algorithm_trace(self):
        for text in (self.review_module, self.review_pack):
            self.assertIn("Algorithm Trace", text)
            self.assertIn("stepwise", text)
            self.assertIn("pseudocode", text)
        self.assertIn("真实 Python 实现", self.review_module)
        self.assertIn("工作簿结果", self.review_module)


if __name__ == "__main__":
    unittest.main()
