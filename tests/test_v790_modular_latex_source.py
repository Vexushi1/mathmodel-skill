from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def load_project_audit_module():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    path = SCRIPTS / "audit_latex_project.py"
    spec = importlib.util.spec_from_file_location("audit_latex_project_v790", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestV790ModularLatexSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load_project_audit_module()

    def test_recursive_expansion_audits_cross_file_labels(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sections").mkdir()
            (root / "main.tex").write_text(
                r"""\documentclass{article}
\begin{document}
\input{sections/q1}
\input{sections/q2}
\end{document}
""",
                encoding="utf-8",
            )
            (root / "sections/q1.tex").write_text(
                r"""\section{问题一模型建立及求解}
\subsection{核心模型汇总}
\begin{equation}x=1\label{eq:q1}\end{equation}
\subsection{求解结果}
结果由统一模型得到。
""",
                encoding="utf-8",
            )
            (root / "sections/q2.tex").write_text(
                r"""\section{问题二模型建立及求解}
\subsection{核心模型汇总}
由式~\eqref{eq:q1}继承上一问关系。
\subsection{求解结果}
得到第二问结果。
""",
                encoding="utf-8",
            )
            findings = self.audit.audit_project(root / "main.tex")
            codes = {item.code for item in findings}
            self.assertNotIn("missing_ref_label", codes, findings)
            self.assertNotIn("latex_include_missing", codes, findings)
            self.assertNotIn("latex_include_cycle", codes, findings)

    def test_missing_include_is_blocking(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "main.tex").write_text(
                r"\documentclass{article}\begin{document}\input{sections/missing}\end{document}",
                encoding="utf-8",
            )
            findings = self.audit.audit_project(root / "main.tex")
            item = next((x for x in findings if x.code == "latex_include_missing"), None)
            self.assertIsNotNone(item, findings)
            self.assertEqual(item.severity, "blocking")

    def test_include_cycle_is_blocking(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sections").mkdir()
            (root / "main.tex").write_text(
                r"\documentclass{article}\begin{document}\input{sections/a}\end{document}",
                encoding="utf-8",
            )
            (root / "sections/a.tex").write_text(r"\input{sections/b}", encoding="utf-8")
            (root / "sections/b.tex").write_text(r"\input{sections/a}", encoding="utf-8")
            findings = self.audit.audit_project(root / "main.tex")
            self.assertTrue(any(x.code == "latex_include_cycle" and x.severity == "blocking" for x in findings), findings)

    def test_reincluded_fragment_requires_review(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sections").mkdir()
            (root / "main.tex").write_text(
                r"\documentclass{article}\begin{document}\input{sections/q1}\input{sections/q1}\end{document}",
                encoding="utf-8",
            )
            (root / "sections/q1.tex").write_text("重复正文。", encoding="utf-8")
            findings = self.audit.audit_project(root / "main.tex")
            item = next((x for x in findings if x.code == "latex_fragment_reincluded"), None)
            self.assertIsNotNone(item, findings)
            self.assertEqual(item.severity, "review_required")
            self.assertIn("sections/q1.tex", item.evidence)

    def test_child_document_declaration_is_blocking(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sections").mkdir()
            (root / "main.tex").write_text(
                r"\documentclass{article}\begin{document}\input{sections/q1}\end{document}",
                encoding="utf-8",
            )
            (root / "sections/q1.tex").write_text(
                r"\begin{document}非法子文档\end{document}", encoding="utf-8"
            )
            findings = self.audit.audit_project(root / "main.tex")
            self.assertTrue(any(x.code == "latex_child_declares_document" and x.severity == "blocking" for x in findings), findings)

    def test_commented_child_document_declaration_is_not_blocking(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sections").mkdir()
            (root / "main.tex").write_text(
                r"\documentclass{article}\begin{document}\input{sections/q1}\end{document}",
                encoding="utf-8",
            )
            (root / "sections/q1.tex").write_text(
                "% 示例：\\documentclass{article}\n当前正文。\n",
                encoding="utf-8",
            )
            findings = self.audit.audit_project(root / "main.tex")
            self.assertFalse(any(x.code == "latex_child_declares_document" for x in findings), findings)

    def test_verbatim_child_document_declaration_is_not_blocking(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sections").mkdir()
            (root / "main.tex").write_text(
                r"\documentclass{article}\begin{document}\input{sections/q1}\end{document}",
                encoding="utf-8",
            )
            (root / "sections/q1.tex").write_text(
                r"""\begin{verbatim}
\begin{document}
\end{document}
\end{verbatim}
当前正文。
""",
                encoding="utf-8",
            )
            findings = self.audit.audit_project(root / "main.tex")
            self.assertFalse(any(x.code == "latex_child_declares_document" for x in findings), findings)

    def test_nested_include_must_be_project_root_relative(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sections/q3").mkdir(parents=True)
            (root / "main.tex").write_text(
                r"\documentclass{article}\begin{document}\input{sections/q3/q3}\end{document}",
                encoding="utf-8",
            )
            (root / "sections/q3/q3.tex").write_text(r"\input{model}", encoding="utf-8")
            (root / "sections/q3/model.tex").write_text("当前模型。", encoding="utf-8")
            findings = self.audit.audit_project(root / "main.tex")
            item = next((x for x in findings if x.code == "latex_include_missing"), None)
            self.assertIsNotNone(item, findings)
            self.assertEqual(item.severity, "blocking")
            self.assertIn("sections/q3/q3.tex -> model", item.evidence)

    def test_nested_project_root_relative_include_resolves(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sections/q3").mkdir(parents=True)
            (root / "main.tex").write_text(
                r"\documentclass{article}\begin{document}\input{sections/q3/q3}\end{document}",
                encoding="utf-8",
            )
            (root / "sections/q3/q3.tex").write_text(
                r"\input{sections/q3/model}",
                encoding="utf-8",
            )
            (root / "sections/q3/model.tex").write_text("当前模型。", encoding="utf-8")
            findings = self.audit.audit_project(root / "main.tex")
            self.assertFalse(any(x.code == "latex_include_missing" for x in findings), findings)

    def test_orphan_content_fragment_is_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sections").mkdir()
            (root / "main.tex").write_text(
                r"\documentclass{article}\begin{document}\input{sections/q1}\end{document}",
                encoding="utf-8",
            )
            (root / "sections/q1.tex").write_text("当前正文。", encoding="utf-8")
            (root / "sections/old.tex").write_text("旧正文。", encoding="utf-8")
            findings = self.audit.audit_project(root / "main.tex")
            self.assertTrue(any(x.code == "latex_orphan_fragment" and x.severity == "warning" for x in findings), findings)

    def test_hsk_template_main_is_orchestration_only_and_inputs_exist(self):
        template = ROOT / "templates/latex/cumcm/hsk"
        main = (template / "hsk_main.tex").read_text(encoding="utf-8")
        self.assertNotIn("\\section{", main)
        self.assertNotIn("兼容旧版静态合同检查", main)
        self.assertIn("\\input{frontmatter/abstract}", main)
        self.assertIn("\\input{sections/06_question1}", main)
        self.assertTrue((template / "config/preamble.tex").is_file())
        self.assertTrue((template / "frontmatter/abstract.tex").is_file())
        self.assertTrue((template / "sections/01_problem_statement.tex").is_file())
        self.assertTrue((template / "appendices/appendices.tex").is_file())

    def test_runtime_contract_and_framework_expose_physical_fragment_mapping(self):
        output = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        policy = output["writing_policy"]
        self.assertEqual(policy["latex_source_layout_default"], "modular")
        self.assertEqual(policy["latex_project_audit_script"], "scripts/audit_latex_project.py")
        self.assertTrue(policy["legacy_single_file_latex_supported"])

        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        fragment = schema["$defs"]["paper_fragment_entry"]
        self.assertNotIn("source_file", fragment["required"])
        self.assertEqual(fragment["properties"]["source_file"]["type"], "string")

        framework = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        self.assertIn("LaTeX 源码文件（可选）", framework)
        self.assertIn("final_latex/frontmatter/abstract.tex", framework)


if __name__ == "__main__":
    unittest.main()
