from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_measurement_module():
    path = ROOT / "scripts/measure_writing_validation.py"
    spec = importlib.util.spec_from_file_location("measure_writing_validation_w0", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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

    def test_citation_notes_and_literal_keys(self):
        tex = r"""\parencite* [see {chapter ] 2}] % annotation
            [p.~17] {known, missing}
            % \cite{comment}
            \verb|\cite{example}|
            \begin{lstlisting}
            \cite{code}
            \end{lstlisting}
            """
        rows = self.audit.audit_bibliography(tex, "@article{known,\n title = {Test}\n}")
        self.assertEqual([("missing_bib_key", "missing")],
                         [(row.code, row.evidence) for row in rows])

    def test_grouped_reference_preserves_positions_and_distinct_keys(self):
        text = r"""\cref {fig:b, fig:a} and \Cref{fig:unknown}.
            \label{fig:a}\label{fig:b}
            % \ref{fig:unseen}
            \verb|\ref{fig:unseen}| \label{fig:unseen}
            """
        findings = self.audit.audit_text(text)
        self.assertEqual({"fig:unknown"}, {f.evidence for f in findings if f.code == "missing_ref_label"})
        self.assertEqual({"fig:unseen"}, {f.evidence for f in findings if f.code == "unreferenced_label"})

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

    def test_default_structural_regressions_require_review_and_style_ids_warn(self):
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
        review_codes = {item.code for item in findings if item.severity == "review_required"}
        warning_codes = {item.code for item in findings if item.severity == "warning"}
        self.assertIn("missing_problem_statement", review_codes)
        self.assertIn("legacy_problem_requirement", review_codes)
        self.assertIn("merged_assumption_symbol_section", review_codes)
        self.assertIn("standalone_conclusion", review_codes)
        self.assertIn("visible_assumption_contract_id", warning_codes)
        self.assertNotIn("no_named_core_model_summary", warning_codes)
        self.assertEqual(self.audit.overall_status(findings), "review_required")

    def test_repeated_negation_is_not_a_mechanical_warning(self):
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
        self.assertTrue({"repeated_negation_template", "consecutive_contrast_paragraphs",
                         "dense_contrast_paragraph"}.isdisjoint(codes), findings)
        self.assertEqual(self.audit.overall_status(findings), "pass")

    def test_normal_academic_word_frequencies_are_not_diagnostic_thresholds(self):
        paragraph = (
            "本文首先建立当前对象的关系，其次进一步可得该对象的变化规律，"
            "最后由图可知结果与研究对象相对应。由表可知计算结果满足要求，见表。"
            "本节主要介绍实际过程，为了便于解释，下面将给出下一步。"
            "然而该关系并非完全独立，不能直接合并，只能按实际条件判断。"
        )
        text = r"\begin{document}" + "\n\n".join([paragraph] * 8) + r"\end{document}"
        removed = {
            "repeated_paper_subject_start", "consecutive_paper_subject_start",
            "repeated_derivation_connector", "repeated_stock_phrase",
            "repeated_negation_template", "repeated_meta_navigation",
            "consecutive_contrast_paragraphs", "dense_contrast_paragraph",
            "possible_redundant_paragraph",
        }
        self.assertTrue(removed.isdisjoint({row.code for row in self.audit.audit_text(text)}))

    def test_background_paragraph_count_is_not_a_warning(self):
        text = (
            r"\begin{document}\section{问题重述}\subsection{问题背景}"
            + "\n\n".join(["城市交通系统受到需求波动和有限道路容量的共同影响。"] * 4)
            + r"\subsection{问题提出}确定路径流量。\end{document}"
        )
        codes = {row.code for row in self.audit.audit_text(text)}
        self.assertNotIn("long_problem_background", codes)
        self.assertNotIn("missing_problem_background", codes)

    def test_long_caption_still_requires_real_references_not_character_counts(self):
        text = (
            r"\begin{document}比较结果见图~\ref{fig:real}。"
            r"\begin{figure}\caption{" + "实际研究对象的结果及其适用范围" * 8
            + r"}\label{fig:real}\end{figure}\end{document}"
        )
        codes = {row.code for row in self.audit.audit_text(text)}
        self.assertNotIn("long_caption", codes)
        self.assertNotIn("unreferenced_figure_table", codes)
        missing = text.replace(r"\ref{fig:real}", r"\ref{fig:absent}")
        findings = self.audit.audit_text(missing)
        self.assertTrue(any(row.code == "missing_ref_label" and row.severity == "blocking"
                            for row in findings), findings)

    def test_problem_analysis_uses_pure_text_and_active_math_is_reported(self):
        prefix = r"\begin{document}\section{问题分析}\subsection{问题一的分析}"
        suffix = r"\section{模型建立}后续模型使用 $x=1$。\end{document}"
        for formula in (
            r"$x=1$", r"\(x=1\)", r"\[x=1\]", r"$x=1$",
            r"\begin{equation}x=1\end{equation}",
            r"\begin{align*}x&=1\end{align*}",
            r"\begin{multline}x=1\end{multline}", r"\ensuremath{x=1}",
        ):
            with self.subTest(formula=formula):
                findings = self.audit.audit_text(prefix + formula + suffix)
                self.assertTrue(any(row.code == "formula_in_problem_analysis"
                                    and row.severity == "review_required" for row in findings))
        for plain in (
            "依据题目给定的3组数据，分析误差变化趋势。",
            r"成本为 \$3，随后比较不同方案。",
            "% 注释里的 $x=1$\n采用纯文本分析。",
            r"\verb|$x=1$| 作为字面示例。",
        ):
            with self.subTest(plain=plain):
                self.assertFalse(any(row.code == "formula_in_problem_analysis"
                                     for row in self.audit.audit_text(prefix + plain + suffix)))

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

    def test_strict_status_can_distinguish_warning_review_and_blocking(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "main.tex"
            path.write_text(r"\begin{document}\section{结论}重复总结。\end{document}", encoding="utf-8")
            findings = self.audit.audit_file(path)
            self.assertEqual(self.audit.overall_status(findings), "review_required")

            duplicate = self.audit.audit_text(
                r"\begin{document}\label{fig:x}\label{fig:x}\end{document}"
            )
            self.assertEqual(self.audit.overall_status(duplicate), "blocking")

    def test_machine_contract_delegates_proof_structure_to_reasoning_authority(self):
        output = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        proposition = output["proposition_contract"]
        reasoning = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(proposition["authority"], "core/writing_reasoning_contract.yaml#proposition_governance")
        self.assertEqual(proposition["default_budget"], [0, 4])
        self.assertFalse(proposition["automatic_rejection_over_budget"])
        self.assertIn("proof_length_recommendation", reasoning["proposition_governance"])
        self.assertIn("proof_placement_rule", reasoning["proposition_governance"])
        self.assertIn("核心证明必须留在正文", reasoning["proposition_governance"]["proof_placement_rule"])

    def test_writing_contract_exposes_tiered_prose_audit(self):
        contract = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        policy = contract["writing_policy"]
        self.assertEqual(policy["prose_audit_script"], "scripts/audit_paper_prose.py")
        self.assertEqual(policy["prose_audit_default_mode"], "report_only")
        self.assertEqual(policy["prose_audit_strict_blocks_on"], ["blocking", "review_required"])

    def test_w0_measurement_preserves_runtime_and_exposes_paired_candidates(self):
        measurement = load_measurement_module()
        report = measurement.collect(ROOT, repeats=1, warmup=0)
        self.assertEqual(report["schema_version"], "1.0.0")
        self.assertFalse(report["environment"]["timing_is_gate"])
        graph = report["call_graph"]
        self.assertTrue(graph["draft_semantic_review"]["surface_audit_direct"])
        self.assertFalse(graph["reuse_adjudication"]["same_input"])
        self.assertFalse(graph["reuse_adjudication"]["cross_stage_cache_allowed"])

        rows = {row["id"]: row for row in report["candidate_snapshots"]}
        for row in rows.values():
            self.assertTrue(row["expectation_matches"], row)
        self.assertFalse(rows["many_independent_subsections"]["observed_present"])
        self.assertEqual(
            rows["mechanical_subsection_split"]["observed_severity"],
            "warning",
        )
        self.assertEqual(
            rows["result_validation_without_bridge"]["observed_severity"],
            "review_required",
        )
        self.assertFalse(rows["result_validation_with_bridge"]["observed_present"])
        self.assertEqual(
            rows["solver_first_without_structure"]["observed_severity"],
            "review_required",
        )
        self.assertFalse(rows["solver_with_structure"]["observed_present"])
        self.assertEqual(rows["stage_order_inverted"]["observed_severity"], "review_required")
        self.assertFalse(rows["stage_order_valid"]["observed_present"])


if __name__ == "__main__":
    unittest.main()
