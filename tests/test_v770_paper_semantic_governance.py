from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestV770PaperSemanticGovernance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reasoning = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))
        cls.output = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        cls.schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        cls.audit = load_module("audit_paper_prose_v770", "scripts/audit_paper_prose.py")
        cls.state_validator = load_module("validate_project_state_v770", "scripts/validate_project_state.py")
        cls.semantic = load_module("validate_semantic_governance_v770", "scripts/validate_semantic_governance.py")

    def test_authority_exposes_all_new_governance_objects(self):
        for key in (
            "terminology_governance",
            "numeric_style_contract",
            "title_claim_gate",
            "analysis_evidence_disposition",
            "paragraph_necessity",
            "paper_fragment_stale_governance",
        ):
            self.assertIn(key, self.reasoning)
        self.assertEqual(self.reasoning["paragraph_necessity"]["governance_level"], "recommendation")
        self.assertEqual(self.reasoning["analysis_evidence_disposition"]["statuses"], ["support", "modify", "reject"])

    def test_high_precision_scoring_contract_does_not_downround_abstract(self):
        numeric = self.reasoning["numeric_style_contract"]
        principle = numeric["principle"]
        self.assertEqual(numeric["high_precision_default"]["preferred_decimal_places_when_not_otherwise_specified"], [6, 7])
        self.assertIn("不得", principle)
        self.assertIn("粗略舍入", principle)
        self.assertIn("摘要", principle)
        self.assertIn("6--7", principle)
        self.assertIn("高精度", numeric["display_profiles"]["abstract"])
        latex = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        cleanup = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        abstract_check = (ROOT / "templates/writing/abstract_result_check.md").read_text(encoding="utf-8")
        for text in (latex, cleanup, abstract_check):
            self.assertIn("6--7", text)
        self.assertIn("核心答案的精度不得为了摘要简洁而擅自降低", latex)
        self.assertNotIn("摘要只写实际有意义的 3--4 位", latex)
        self.assertEqual(self.output["writing_policy"]["core_result_precision_priority"], "scoring_and_official_output_requirements")

    def test_framework_v08_contains_project_memory_registries(self):
        text = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        self.assertIn("框架版本：`v0.8-project-memory`", text)
        for heading in (
            "### Terminology Registry",
            "### Numeric Profile",
            "#### Title Claim Gate",
            "### Paper Fragment Dependency Map",
            "**深化证据处置**",
        ):
            self.assertIn(heading, text)
        self.assertIn("若小数后 6--7 位可能影响结果分", text)

    def test_project_state_schema_keeps_new_fields_optional_for_legacy_read(self):
        paper_props = self.schema["properties"]["paper_framework"]["properties"]
        sub_props = self.schema["properties"]["subproblems"]["additionalProperties"]["properties"]
        for field in ("terminology_registry", "numeric_profile", "title_claims", "paper_fragments"):
            self.assertIn(field, paper_props)
            self.assertNotIn(field, self.schema["properties"]["paper_framework"]["required"])
        self.assertIn("analysis_evidence_dispositions", sub_props)
        self.assertNotIn("analysis_evidence_dispositions", self.schema["properties"]["subproblems"]["additionalProperties"]["required"])

    def test_terminology_alias_collision_is_deterministic_state_issue(self):
        framework = {
            "terminology_registry": [
                {"id": "T1", "canonical_term": "有效遮蔽时长", "definition": "时间长度", "allowed_aliases": ["有效时长"], "status": "current"},
                {"id": "T2", "canonical_term": "总遮蔽时长", "definition": "总时间长度", "allowed_aliases": ["有效时长"], "status": "current"},
            ]
        }
        issues = self.state_validator._validate_terminology(framework)
        self.assertTrue(any("alias maps to multiple" in issue for issue in issues), issues)

    def test_high_precision_numeric_profile_rejects_unjustified_low_abstract_precision(self):
        good = {"numeric_profile": [{
            "id": "N1", "metric": "最优时间", "display_form": "decimal",
            "abstract_decimals": 7, "body_decimals": 7, "table_decimals": 7,
            "precision_basis": "reviewer", "status": "current",
        }]}
        bad = {"numeric_profile": [{
            "id": "N1", "metric": "最优时间", "display_form": "decimal",
            "abstract_decimals": 4, "body_decimals": 7, "table_decimals": 7,
            "precision_basis": "reviewer", "status": "current",
        }]}
        self.assertEqual(self.state_validator._validate_numeric_profile(good), [])
        self.assertTrue(self.state_validator._validate_numeric_profile(bad))

    def test_current_substantive_title_claim_requires_real_closure(self):
        incomplete = {"title_claims": [{
            "id": "TC1", "text": "鲁棒优化", "claim_type": "main_method", "status": "current",
            "related_questions": ["Q3"], "body_anchor": "", "result_evidence": [],
            "abstract_anchor": "", "keyword_link": [],
        }]}
        issues = self.state_validator._validate_title_claims(incomplete)
        self.assertGreaterEqual(len(issues), 4)

    def test_local_paper_stale_marks_only_real_dependencies(self):
        framework = {
            "paper_fragments": [
                {"id": "paper.q1.result", "kind": "question_result_text", "scope": "Q1", "depends_on": ["Q1.result_summary"], "anchor": "q1", "status": "current"},
                {"id": "paper.q3.result", "kind": "question_result_text", "scope": "Q3", "depends_on": ["Q3.result_summary"], "anchor": "q3", "status": "current"},
                {"id": "paper.abstract.q3", "kind": "abstract_claim", "scope": "Q3", "depends_on": ["paper.q3.result"], "anchor": "abs-q3", "status": "current"},
                {"id": "paper.title.tc1", "kind": "title_claim", "scope": "global", "depends_on": ["paper.abstract.q3"], "anchor": "title", "status": "current"},
                {"id": "paper.background", "kind": "paper_section", "scope": "global", "depends_on": [], "anchor": "background", "status": "current"},
            ]
        }
        stale = self.semantic._mark_paper_fragments_stale(framework, {"Q3"})
        self.assertEqual(stale, ["paper.abstract.q3", "paper.q3.result", "paper.title.tc1"])
        status = {item["id"]: item["status"] for item in framework["paper_fragments"]}
        self.assertEqual(status["paper.q1.result"], "current")
        self.assertEqual(status["paper.background"], "current")

    def test_support_modify_reject_contract_allows_auxiliary_rewrite(self):
        state = {
            "result_analysis_status": "passed",
            "analysis_evidence_dispositions": [{
                "id": "E1", "method_or_source": "压力测试", "target_claim": "模型稳定性很强",
                "disposition": "reject", "key_finding": "极端区间不稳定",
                "required_action": "重写该非核心评价句并收窄边界", "status": "resolved",
            }],
        }
        self.assertEqual(self.state_validator._validate_analysis_dispositions("Q3", state), [])

    def test_unresolved_ref_is_blocking_but_unreferenced_equation_is_warning(self):
        missing = self.audit.audit_text(r"\begin{document}见式~\eqref{eq:missing}。\end{document}")
        self.assertTrue(any(x.code == "missing_ref_label" and x.severity == "blocking" for x in missing), missing)
        unreferenced = self.audit.audit_text(r"\begin{document}\begin{equation}a=b\label{eq:x}\end{equation}\end{document}")
        self.assertTrue(any(x.code == "unreferenced_label" and x.severity == "warning" for x in unreferenced), unreferenced)
        self.assertFalse(any(x.severity == "blocking" for x in unreferenced), unreferenced)

    def test_abstract_structural_checks_do_not_guess_math(self):
        tex = r"""
\begin{document}
\begin{abstract}
结果见下式。
\[x=1\]
\end{abstract}
\keywords{模型, 优化}
\end{document}
"""
        findings = self.audit.audit_text(tex)
        codes = {x.code: x.severity for x in findings}
        self.assertEqual(codes.get("abstract_contains_display_math"), "review_required")
        self.assertEqual(codes.get("keyword_count"), "review_required")
        self.assertFalse(any("数学错误" in x.message for x in findings))

    def test_framework_terminology_audit_warns_on_registered_discouraged_alias(self):
        framework = """
### Terminology Registry
| Term ID | 标准术语 | 定义 | 量纲/单位 | 允许简称 | 不建议别名 | 易混术语 | 对应符号 | 适用范围 | 状态 |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 有效遮蔽时长 | 满足判据的累计时间 | s | | 有效时长 | 总遮蔽时长 | T_e | Q1 | current |
"""
        tex = r"\begin{document}本问得到的有效时长用于回答问题一。\end{document}"
        findings = self.audit.audit_framework_consistency(tex, framework)
        self.assertTrue(any(x.code == "discouraged_terminology_alias" for x in findings), findings)

    def test_numeric_profile_audit_warns_when_registered_answer_loses_digits(self):
        framework = """
### Numeric Profile
| Metric ID | 标准指标 | 符号 | 单位 | 展示形式 | 摘要精度 | 正文精度 | 表格精度 | 提交/决策精度 | 评分精度依据 |
|---|---|---|---|---|---|---|---|---|---|
| N1 | 最优时间 | t | s | decimal | 7 | 7 | 7 | 7 | reviewer |
"""
        tex = r"""
\begin{document}
\begin{abstract}最优时间为 1.2345 s。\end{abstract}
\end{document}
"""
        findings = self.audit.audit_framework_consistency(tex, framework)
        self.assertTrue(any(x.code == "numeric_precision_drift" for x in findings), findings)

    def test_cleanup_is_layered_not_numbered_rule_accumulation(self):
        cleanup = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        for heading in ("## A. Integrity / Hard boundary", "## B. Evidence closure", "## C. Style & Necessity", "## D. Optional machine diagnostics"):
            self.assertIn(heading, cleanup)
        self.assertIn("Skill 负责原则，脚本负责穷举", cleanup)
        self.assertNotIn("99.", cleanup)


if __name__ == "__main__":
    unittest.main()
