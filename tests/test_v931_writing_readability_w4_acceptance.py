from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
EVIDENCE = ROOT / "docs/writing_readability_w4_acceptance.md"


def load_module(name: str, relative: str):
    path = ROOT / relative
    parent = str(path.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PROSE = load_module("w4_audit_paper_prose", "scripts/audit_paper_prose.py")
LATEX = load_module("w4_audit_latex_project", "scripts/audit_latex_project.py")


class TestWritingReadabilityW4Acceptance(unittest.TestCase):
    def test_t01_t18_are_explicitly_adjudicated_without_fake_human_feedback(self):
        text = EVIDENCE.read_text(encoding="utf-8")
        for index in range(1, 19):
            self.assertIn(f"| T{index:02d} |", text)
        self.assertIn("外部人工反馈：none", text)
        self.assertIn("不是独立评委、用户或第三方人工反馈", text)

    def test_w4_does_not_create_a_new_gate_state_or_coverage_family(self):
        matrix = yaml.safe_load(
            (ROOT / "templates/review/final_review_matrix.yaml").read_text(encoding="utf-8")
        )
        families = [item["check_family"] for item in matrix["coverage"]]
        self.assertEqual(
            families,
            [
                "edition_compliance",
                "anonymity_and_metadata",
                "ai_disclosure",
                "citation_entity_integrity",
                "rendered_page_surface",
                "figure_table_information_value",
                "reproducibility_and_package",
                "cross_question_dynamic_coverage",
            ],
        )
        runtime = (ROOT / "core/writing_runtime_contract.yaml").read_text(encoding="utf-8")
        project_state = (ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8")
        review = (ROOT / "modules/06_review_delivery.md").read_text(encoding="utf-8")
        self.assertNotIn("readability_status", runtime)
        self.assertNotIn("readability_status", project_state)
        self.assertIn("不新增新的可读性检查族", review)
        self.assertIn("machine / manual / hybrid", review)

    def test_t08_t10_heading_depth_positive_negative_and_exclusions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = root / "main.tex"
            main.write_text(
                r"""\documentclass{article}
\newcommand{\exampledeep}{\paragraph{宏定义中的示例}}
\begin{document}
% \paragraph{注释示例}
\begin{verbatim}
\paragraph{代码示例}
\end{verbatim}
\section{问题一}
\subsection{模型建立}
\subsubsection{状态变量}
\subsubsection{控制方程}
\subsubsection{边界条件}
\subsubsection{参数依据}
\subsubsection{数值离散}
\subsubsection{模型收束}
正文。
\end{document}
""",
                encoding="utf-8",
            )
            findings = LATEX.audit_project(main)
            self.assertFalse(
                any(item.code == "formal_heading_depth_exceeds_three" for item in findings),
                findings,
            )

            for command in (
                r"\paragraph{第四层}",
                r"\paragraph*{未编号第四层}",
                r"\subparagraph{第五层}",
            ):
                main.write_text(
                    "\\documentclass{article}\n\\begin{document}\n"
                    "\\section{问题一}\n\\subsection{模型建立}\n"
                    "\\subsubsection{核心关系}\n"
                    + command
                    + "\n正文。\n\\end{document}\n",
                    encoding="utf-8",
                )
                findings = LATEX.audit_project(main)
                item = next(
                    (x for x in findings if x.code == "formal_heading_depth_exceeds_three"),
                    None,
                )
                self.assertIsNotNone(item, findings)
                self.assertEqual(item.severity, "blocking")

    def test_t15_count_only_finding_is_gone_but_specific_fragmentation_remains(self):
        independent = r"""
\begin{document}
\section{问题一模型建立及求解}
\subsection{状态变量定义}定义状态和量纲。
\subsection{边界条件构造}给出独立边界条件。
\subsection{控制方程}推导控制方程。
\subsection{数值求解}依据当前结构说明数值求解。
\subsection{求解结果}给出结果并回答设问。
\end{document}
"""
        findings = PROSE.audit_text(independent)
        self.assertFalse(
            any(x.code == "question_subsection_granularity" for x in findings),
            findings,
        )

        mechanical = r"""
\begin{document}
\section{问题一模型建立及求解}
\subsection{决策变量}定义变量。
\subsection{目标函数}给出目标。
\subsection{约束条件}给出约束。
\subsection{核心模型汇总}重复汇总。
\subsection{求解结果}给出结果。
\end{document}
"""
        findings = PROSE.audit_text(mechanical)
        item = next(
            (x for x in findings if x.code == "possible_mechanical_model_subsection_split"),
            None,
        )
        self.assertIsNotNone(item, findings)
        self.assertEqual(item.severity, "warning")
        self.assertFalse(
            any(x.code == "question_subsection_granularity" for x in findings),
            findings,
        )

    def test_t11_t13_terminology_and_numeric_drift_are_still_detected(self):
        framework = """
### Terminology Registry
| Term ID | 标准术语 | 定义 | 量纲/单位 | 允许简称 | 不建议别名 | 易混术语 | 对应符号 | 适用范围 | 状态 |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 有效遮蔽时长 | 满足判据的累计时间 | s | | 有效时长 | 总遮蔽时长 | T_e | Q1 | current |

### Numeric Profile
| Metric ID | 标准指标 | 符号 | 单位 | 展示形式 | 摘要精度 | 正文精度 | 表格精度 | 提交/决策精度 | 评分精度依据 |
|---|---|---|---|---|---|---|---|---|---|
| N1 | 最优时间 | t | s | decimal | 7 | 7 | 7 | 7 | reviewer |
"""
        tex = r"""
\begin{document}
\begin{abstract}最优时间为 1.2345 s，本问得到的有效时长用于回答问题一。\end{abstract}
\end{document}
"""
        findings = PROSE.audit_framework_consistency(tex, framework)
        codes = {item.code: item.severity for item in findings}
        self.assertEqual(codes.get("discouraged_terminology_alias"), "warning")
        self.assertEqual(codes.get("numeric_precision_drift"), "warning")

    def test_t14_t16_wording_and_semantic_change_boundaries_remain_distinct(self):
        runtime = (ROOT / "core/writing_runtime_contract.yaml").read_text(encoding="utf-8")
        baseline_test = (ROOT / "tests/test_optimization_baseline.py").read_text(encoding="utf-8")
        semantic_test = (ROOT / "tests/test_v711_model_approval_gate.py").read_text(encoding="utf-8")
        source_test = (ROOT / "tests/test_v790_runtime_closure.py").read_text(encoding="utf-8")

        for token in (
            "writing_only: true",
            "included_in_model_semantic_hash: false",
            "invalidates_locked_model_spec: false",
            "triggers_model_approval: false",
            "triggers_primary_solve: false",
        ):
            self.assertIn(token, runtime)
        self.assertIn("hydrated_wording_only", baseline_test)
        self.assertIn(
            "test_structured_semantic_change_marks_challenge_and_human_approval_stale",
            semantic_test,
        )
        self.assertIn("test_source_bundle_hash_changes_with_child_tex_and_graphic", source_test)

    def test_t17_cross_carrier_fallback_preserves_each_carrier_boundary(self):
        runtime = yaml.safe_load(
            (ROOT / "core/writing_runtime_contract.yaml").read_text(encoding="utf-8")
        )
        applicability = runtime["applicability"]
        self.assertEqual(
            applicability["fallback_for_other_competitions"],
            "core/writing_reasoning_contract.yaml",
        )
        rule = applicability["rule"]
        for token in ("DOCX", "MCM/ICM", "电工杯", "不得错误套用 CUMCM 一级骨架"):
            self.assertIn(token, rule)

        docx = (ROOT / "modules/05_writing/docx.md").read_text(encoding="utf-8")
        self.assertIn("Heading 1 / Heading 2 / Heading 3", docx)
        self.assertIn("禁止 Heading 4 及以上", docx)

        ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        for token in ("name: CUMCM", "name: MCM-ICM", "name: Diangong"):
            self.assertIn(token, ci)

    def test_t18_hard_structural_errors_remain_blocking(self):
        tex = r"""
\begin{document}
\section{问题一}
\label{dup:key}
\label{dup:key}
参见式~\eqref{eq:missing}。
\end{document}
"""
        findings = PROSE.audit_text(tex)
        severities = {item.code: item.severity for item in findings}
        self.assertEqual(severities.get("duplicate_label"), "blocking")
        self.assertEqual(severities.get("missing_ref_label"), "blocking")

        review = (ROOT / "modules/06_review_delivery.md").read_text(encoding="utf-8")
        self.assertIn("blocking → review_required → warning", review)
        self.assertIn("必要模型/公式/约束、非显然核心推导或证明逻辑断裂", review)


if __name__ == "__main__":
    unittest.main()
