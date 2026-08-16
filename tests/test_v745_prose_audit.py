from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_audit_module():
    path = ROOT / "scripts/audit_paper_prose.py"
    spec = importlib.util.spec_from_file_location("audit_paper_prose_v745", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestV745ProseAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load_audit_module()

    def test_clean_cumcm_fragment_passes(self):
        tex = r"""
\begin{document}
\section{问题重述}
\subsection{问题背景}
复杂介质中的定位误差会随结构和速度场变化，因此需要建立统一的分析口径。

\subsection{问题提出}
问题一：比较两类成像方法在共同观测范围内的定位差异，并给出误差变化规律。

\section{问题分析}
\subsection{问题一的分析}
该问的主要困难在于时间域记录与深度域结构之间存在不同表示，需要先统一观测范围，再比较复杂区域的定位表现。

\section{模型假设}
1. 在共同观测范围内比较两类方法。

\section{符号说明}
主要符号在首次使用处给出。

\section{问题一模型建立及求解}
\subsection{模型建立}
根据传播关系建立定位模型，并保留横向速度变化。

\subsection{核心模型汇总}
最终模型由传播方程、边界条件和定位误差指标组成。

\subsection{模型求解}
采用与模型结构一致的数值推进方式求解。

\subsection{求解结果}
图~\ref{fig:q1}给出了两种方法的定位结果。复杂区域的误差差异更明显，该现象与横向速度变化相对应。

\begin{figure}
\centering
\caption{定位结果比较}
\label{fig:q1}
\end{figure}
\end{document}
"""
        findings = self.audit.audit_text(tex)
        self.assertEqual(self.audit.overall_status(findings), "pass", findings)

    def test_structural_regressions_require_review(self):
        tex = r"""
\begin{document}
\section{问题重述}
\subsection{问题背景}
背景文字用于引出问题。
\subsection{问题要求}
问题一：求解目标量。
\section{模型假设与符号说明}
H1. 数据满足要求。
\section{问题一模型建立及求解}
\subsection{模型求解}
直接求解。
\subsection{求解结果}
得到结果。
\section{结论}
汇总全文。
\end{document}
"""
        findings = self.audit.audit_text(tex)
        codes = {item.code for item in findings if item.severity == "review_required"}
        self.assertIn("missing_problem_statement", codes)
        self.assertIn("legacy_problem_requirement", codes)
        self.assertIn("merged_assumption_symbol_section", codes)
        self.assertIn("visible_assumption_contract_id", codes)
        self.assertIn("missing_core_model_summary", codes)
        self.assertIn("standalone_conclusion", codes)
        self.assertEqual(self.audit.overall_status(findings), "review_required")

    def test_repeated_negation_is_warning_not_word_ban(self):
        ordinary = r"""
\begin{document}
\section{问题重述}
\subsection{问题背景}
该模型在复杂区域存在局部误差，但总体趋势保持一致。
\subsection{问题提出}
问题一：分析误差来源。
\end{document}
"""
        self.assertEqual(self.audit.overall_status(self.audit.audit_text(ordinary)), "pass")

        dense = r"""
\begin{document}
本文不是直接比较结果，而是先统一口径。本文不是重新构造数据，而是保留共同观测区域。

然而该区域仍有局部误差，不过整体趋势没有改变。

但是深部位置不能直接解释，只能保留为边界信息。
\end{document}
"""
        findings = self.audit.audit_text(dense)
        codes = {item.code for item in findings}
        self.assertTrue({"repeated_negation_template", "consecutive_contrast_paragraphs"} & codes, findings)
        self.assertEqual(self.audit.overall_status(findings), "warning")

    def test_unreferenced_main_figure_is_warning(self):
        tex = r"""
\begin{document}
正文给出成像结果和对应解释，但没有引用下面的图号。
\begin{figure}
\caption{结果图}
\label{fig:unref}
\end{figure}
\end{document}
"""
        findings = self.audit.audit_text(tex)
        self.assertTrue(any(item.code == "unreferenced_figure_table" for item in findings), findings)
        self.assertEqual(self.audit.overall_status(findings), "warning")

    def test_reasoning_audit_warns_on_dense_formula_run_but_does_not_claim_math_error(self):
        tex = r"""
\begin{document}
由几何定义得到第一个关系。
\begin{equation}a=b+c\end{equation}
进一步可得
\begin{equation}d=e+f\end{equation}
同理可得
\begin{equation}g=h+i\end{equation}
\end{document}
"""
        findings = self.audit.audit_text(tex)
        item = next((x for x in findings if x.code == "dense_formula_run"), None)
        self.assertIsNotNone(item, findings)
        self.assertEqual(item.severity, "warning")
        self.assertNotIn("错误", item.message)

    def test_numeric_parameter_assignment_without_nearby_evidence_is_warning_only(self):
        tex = r"""
\begin{document}
为了进行后续计算，取 n=300，并据此完成全部离散计算。
\end{document}
"""
        findings = self.audit.audit_text(tex)
        item = next((x for x in findings if x.code == "numeric_parameter_evidence"), None)
        self.assertIsNotNone(item, findings)
        self.assertEqual(item.severity, "warning")
        self.assertEqual(self.audit.overall_status(findings), "warning")

    def test_numeric_parameter_with_explicit_convergence_evidence_is_not_flagged(self):
        tex = r"""
\begin{document}
对候选离散点数进行网格收敛检验，误差在 n=300 后已经稳定，因此取 n=300 作为后续计算参数。
\end{document}
"""
        findings = self.audit.audit_text(tex)
        self.assertFalse(any(x.code == "numeric_parameter_evidence" for x in findings), findings)

    def test_second_background_paragraph_is_allowed_when_it_narrows_object(self):
        tex = r"""
\begin{document}
\section{问题重述}
\subsection{问题背景}
城市交通系统受需求波动和道路容量共同影响，拥堵状态具有明显的时空差异。

本题进一步聚焦于给定路网中的高峰时段车辆分配，需要刻画有限容量下各路径的流量变化。

\subsection{问题提出}
问题一：确定给定需求下的路径流量分配结果。
\end{document}
"""
        findings = self.audit.audit_text(tex)
        codes = {x.code for x in findings}
        self.assertNotIn("background_management_paragraph", codes)
        self.assertNotIn("long_problem_background", codes)

    def test_background_management_second_paragraph_is_warning(self):
        tex = r"""
\begin{document}
\section{问题重述}
\subsection{问题背景}
城市交通系统受需求波动和道路容量共同影响，需要建立合理的分配模型。

全文将依次研究三个问题，后文章节安排如下，并分别介绍模型和求解结果。

\subsection{问题提出}
问题一：确定路径流量分配结果。
\end{document}
"""
        findings = self.audit.audit_text(tex)
        self.assertTrue(any(x.code == "background_management_paragraph" for x in findings), findings)

    def test_strict_cli_blocks_only_review_required(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "main.tex"
            path.write_text(r"\begin{document}\section{结论}重复总结。\end{document}", encoding="utf-8")
            findings = self.audit.audit_file(path)
            self.assertEqual(self.audit.overall_status(findings), "review_required")

    def test_machine_contract_uses_paragraph_first_logical_units(self):
        contract = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        policy = contract["writing_policy"]
        proposition = contract["proposition_contract"]

        self.assertEqual(policy["proof_structure_default"], "paragraph_first")
        self.assertTrue(policy["proof_logical_units_required"])
        self.assertTrue(policy["proof_numbered_steps_when_needed"])
        self.assertNotIn("proposition_proof_segmented_steps", policy)

        self.assertEqual(proposition["main_text_default_structure"], "paragraph_first")
        self.assertTrue(proposition["logical_units_required"])
        self.assertTrue(proposition["numbered_steps_when_needed"])
        self.assertEqual(proposition["numbered_steps_min"], 2)
        self.assertEqual(proposition["numbered_steps_max"], 6)
        self.assertNotIn("segmented_steps_required", proposition)
        self.assertNotIn("main_text_key_steps_min", proposition)
        self.assertNotIn("main_text_key_steps_max", proposition)

    def test_writing_contract_exposes_prose_audit(self):
        contract = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        policy = contract["writing_policy"]
        self.assertEqual(policy["prose_audit_script"], "scripts/audit_paper_prose.py")
        self.assertEqual(policy["prose_audit_default_mode"], "report_only")
        self.assertEqual(policy["prose_audit_strict_blocks_on"], "review_required")


if __name__ == "__main__":
    unittest.main()
