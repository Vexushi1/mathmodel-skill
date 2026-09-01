import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name="audit_v8_writing_surface_test", script="audit_v8_writing_surface.py"):
    path = ROOT / "scripts" / script
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestV800SurfaceAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load_module()

    def test_internal_workflow_vocabulary_warns_only(self):
        findings = self.audit.audit_text("主工作簿 accepted 后进入深化分析，并记录 support。")
        self.assertTrue(any(item.code == "workflow_vocabulary_leak" for item in findings))
        self.assertEqual(self.audit.overall_status(findings), "warning")

    def test_code_block_does_not_trigger_workflow_leak(self):
        tex = r"""
\begin{lstlisting}
status = "accepted"
\end{lstlisting}
正文只说明对参数进行扰动检验。
"""
        findings = self.audit.audit_text(tex)
        self.assertFalse(any(item.code == "workflow_vocabulary_leak" for item in findings), findings)

    def test_decorative_quotes_and_concept_chain_warn(self):
        tex = "采用“对象层”“机制层”“决策层”三个普通标签，并构造需求-资源-约束-决策链。"
        codes = {item.code for item in self.audit.audit_text(tex)}
        self.assertIn("decorative_quote_density", codes)
        self.assertIn("concept_chain_density", codes)

    def test_result_validation_jump_requires_review_not_blocking(self):
        tex = r"""
\subsection{求解结果}
得到最优方案与目标值。
\subsection{敏感性分析}
改变参数并重新计算。
"""
        findings = self.audit.audit_text(tex)
        item = next((x for x in findings if x.code == "result_validation_bridge_risk"), None)
        self.assertIsNotNone(item, findings)
        self.assertEqual(item.severity, "review_required")
        self.assertEqual(self.audit.overall_status(findings), "review_required")

    def test_explicit_risk_bridge_is_not_flagged(self):
        tex = r"""
\subsection{求解结果}
得到最优方案与目标值。该结果已回答主问题，但推荐方案仍可能受到边界参数扰动影响，因此进一步检验关键参数变化下方案排序是否保持稳定。
\subsection{敏感性分析}
改变参数并重新计算。
"""
        findings = self.audit.audit_text(tex)
        self.assertFalse(any(x.code == "result_validation_bridge_risk" for x in findings), findings)

    def test_surface_findings_are_integrated_into_formal_prose_audit(self):
        formal = load_module("audit_paper_prose_v800_integration", "audit_paper_prose.py")
        findings = formal.audit_text("主工作簿 accepted 后进入深化分析，并记录 support。")
        item = next((x for x in findings if x.code == "workflow_vocabulary_leak"), None)
        self.assertIsNotNone(item, findings)
        self.assertEqual(item.severity, "warning")


if __name__ == "__main__":
    unittest.main()
