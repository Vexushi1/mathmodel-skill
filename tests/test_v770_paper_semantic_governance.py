from __future__ import annotations

import importlib.util
import sys
import tempfile
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


FRAMEWORK = load_module("framework_v770", ROOT / "scripts/validate_model_paper_framework.py")
AUDIT = load_module("audit_v770", ROOT / "scripts/audit_paper_prose.py")
SEMANTIC = load_module("semantic_v770", ROOT / "scripts/validate_semantic_governance.py")
STATE = load_module("state_v770", ROOT / "scripts/validate_project_state.py")


FULL_FRAMEWORK_BASE = r"""# 模型论文框架

> 本文件只保留当前有效项目事实、选择、状态与证据位置。
- 框架版本：`v0.8-project-memory`
- 框架模式: full
- 当前状态：current

## 当前有效口径

### Terminology Registry

| Term ID | 标准术语 | 定义 | 量纲/单位 | 允许简称 | 不推荐别名 | 易混术语 | 对应符号 | 适用范围 |
|---|---|---|---|---|---|---|---|---|

### Numeric Profile

| Metric ID | 标准指标 | 符号 | 单位 | 展示形式 | 必要小数位 | 工作簿精度 | 正文精度 | 摘要精度 | 精度/评分依据 |
|---|---|---|---|---|---|---|---|---|---|

## 论文整体框架

### Title Claim Gate

| Claim ID | 标题核心主张 | 类型 | 对应小问 | 正文锚点 | 结果证据 | 摘要位置 | 关键词 | 状态 |
|---|---|---|---|---|---|---|---|---|

### 命题与证明规划
- 当前计划命题数：0
- 默认正文预算：0--4
- 超预算状态：`not_applicable`
- 当前命题状态：`not_assessed`

| 命题ID | 对应小问 | 名称与类型 | 前提/定义域 | 核心结论 | 证明等级 | 下游模型/计算作用 | 失效边界 | 状态 |
|---|---|---|---|---|---|---|---|---|

### 正文局部状态映射

| Fragment ID | 类型 | 对应小问/来源 | depends_on | 正文锚点 | 状态 | stale 原因/修复动作 |
|---|---|---|---|---|---|---|

## 各问模型与结果

### Q1：测试
#### 当前模型口径
模型
#### 结果摘要
结果

## 综合检验与跨问判断

## 图表证据链

## 待办与缺口

## 同步检查
"""


SEMANTIC_FRAMEWORK = """# 模型论文框架
## 当前有效口径
## 各问模型与结果
### Q1：第一问
#### 当前模型口径
- 目标：min f(x)
#### 结果摘要
结果一
### Q2：第二问
#### 当前模型口径
- 目标：min g(y)
#### 结果摘要
结果二
### Q3：第三问
#### 当前模型口径
- 目标：min h(z)
#### 结果摘要
结果三
### Q4：第四问
#### 当前模型口径
- 目标：min k(w)
#### 结果摘要
结果四
## 图表证据链
## 待办与缺口
"""


def semantic_subproblem(*, depends_on=None):
    return {
        "status": "designed",
        "problem_contract_status": "frozen",
        "semantic_closure_status": "passed",
        "complexity_sanity_status": "passed",
        "complexity_sanity_flags": [],
        "complexity_sanity_note": "复审完成",
        "semantic_revision": 1,
        "semantic_change_categories": ["initial_design"],
        "depends_on": depends_on or [],
        "result_quality_status": "passed",
        "result_analysis_status": "passed",
        "validation_status": "passed",
        "result_summary_status": "current",
        "artifacts_stale": False,
        "stale_layers": [],
    }


class TestV770PaperSemanticGovernance(unittest.TestCase):
    def test_reasoning_authority_exposes_all_v770_governance(self):
        contract = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(contract["schema_version"], "1.2.0")
        for key in (
            "terminology_governance",
            "numeric_style_contract",
            "title_claim_gate",
            "analysis_evidence_disposition",
            "paragraph_necessity",
            "paper_fragment_stale",
        ):
            self.assertIn(key, contract)
        numeric = contract["numeric_style_contract"]["scoring_result_precision"]
        self.assertEqual(numeric["default_continuous_decimal_digits"], [6, 7])
        self.assertTrue(numeric["verified_requirement_precedence"])
        self.assertIn("6--7", contract["numeric_style_contract"]["summary_policy"])
        self.assertEqual(
            set(contract["analysis_evidence_disposition"]["values"]),
            {"support", "modify", "reject"},
        )

    def test_framework_template_exposes_project_semantic_registries(self):
        text = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        self.assertIn("v0.8-project-memory", text)
        for token in (
            "### Terminology Registry",
            "### Numeric Profile",
            "### Title Claim Gate",
            "### 正文局部状态映射",
            "**深化证据处置**",
            "小数点后6--7位",
        ):
            self.assertIn(token, text)

    def test_framework_validator_rejects_alias_collision(self):
        text = FULL_FRAMEWORK_BASE.replace(
            "|---|---|---|---|---|---|---|---|---|\n\n### Numeric Profile",
            "|---|---|---|---|---|---|---|---|---|\n"
            "| T1 | 有效遮蔽时长 | 有效判据累计时间 | s | 有效时长 |  | 总遮蔽时长 | T_e | 全文 |\n"
            "| T2 | 总遮蔽时长 | 任意遮蔽累计时间 | s | 有效时长 |  | 有效遮蔽时长 | T | 全文 |\n\n"
            "### Numeric Profile",
        )
        issues = FRAMEWORK.validate_framework_text(text, strict=False, mode="full")
        self.assertTrue(any("maps to multiple canonical terms" in item for item in issues), issues)

    def test_framework_validator_requires_current_title_claim_closure_in_strict_mode(self):
        text = FULL_FRAMEWORK_BASE.replace(
            "|---|---|---|---|---|---|---|---|---|\n\n### 命题与证明规划",
            "|---|---|---|---|---|---|---|---|---|\n"
            "| TC1 | 鲁棒优化 | main_method | Q1 |  | 图8 | 摘要Q1 | 鲁棒优化 | current |\n\n"
            "### 命题与证明规划",
        )
        issues = FRAMEWORK.validate_framework_text(text, strict=True, mode="full")
        self.assertTrue(any("current title claim has empty closure fields" in item for item in issues), issues)

    def test_legacy_v07_full_framework_does_not_require_v08_headings(self):
        legacy = """# 模型论文框架
只保留当前有效项目事实
- 框架版本：`v0.7-project-memory`
- 框架模式: full
## 当前有效口径
## 论文整体框架
### 命题与证明规划
- 当前计划命题数：0
## 各问模型与结果
## 综合检验与跨问判断
## 图表证据链
## 待办与缺口
## 同步检查
"""
        self.assertEqual(FRAMEWORK.validate_framework_text(legacy, mode="full"), [])

    def test_semantic_v10_is_read_compatible(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            (root / "state").mkdir()
            (root / "模型论文框架.md").write_text(SEMANTIC_FRAMEWORK, encoding="utf-8")
            state = {
                "semantic_governance_version": "1.0.0",
                "subproblems": {
                    "Q1": semantic_subproblem(),
                    "Q2": semantic_subproblem(),
                    "Q3": semantic_subproblem(),
                    "Q4": semantic_subproblem(),
                },
            }
            (root / "state/project_state.yaml").write_text(
                yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            report = SEMANTIC.validate_project(root, write=False, strict=True)
            self.assertEqual(report["status"], "passed")
            self.assertTrue(any("兼容读取版本" in item for item in report["warnings"]))

    def test_q3_change_stales_only_explicitly_dependent_paper_fragments(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            (root / "state").mkdir()
            (root / "模型论文框架.md").write_text(SEMANTIC_FRAMEWORK, encoding="utf-8")
            state = {
                "semantic_governance_version": "1.1.0",
                "paper_framework": {
                    "sync_status": "current",
                    "paper_fragments": [
                        {"id": "PF1", "kind": "other", "status": "current", "anchor": "问题背景"},
                        {"id": "PF2", "kind": "question_result", "source_questions": ["Q1"], "status": "current", "anchor": "Q1结果"},
                        {"id": "PF3", "kind": "abstract_claim", "source_questions": ["Q3"], "status": "current", "anchor": "摘要Q3"},
                        {"id": "PF4", "kind": "title_claim", "depends_on": ["Q4.result"], "status": "current", "anchor": "标题"},
                    ],
                },
                "subproblems": {
                    "Q1": semantic_subproblem(),
                    "Q2": semantic_subproblem(),
                    "Q3": semantic_subproblem(),
                    "Q4": semantic_subproblem(depends_on=[{"question": "Q3", "kind": "result"}]),
                },
            }
            state_path = root / "state/project_state.yaml"
            state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
            self.assertEqual(SEMANTIC.validate_project(root, write=True, strict=True)["status"], "passed")

            changed = (root / "模型论文框架.md").read_text(encoding="utf-8").replace(
                "- 目标：min h(z)", "- 目标：min h(z)+lambda*r(z)"
            )
            (root / "模型论文框架.md").write_text(changed, encoding="utf-8")
            state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            state["subproblems"]["Q3"]["semantic_revision"] = 2
            state["subproblems"]["Q3"]["semantic_change_categories"] = ["objective"]
            state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")

            report = SEMANTIC.validate_project(root, write=True, strict=True)
            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["changed_sources"], ["Q3"])
            self.assertEqual(report["affected_questions"], ["Q3", "Q4"])
            self.assertEqual(report["affected_paper_fragments"], ["PF3", "PF4"])

            state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            fragments = {item["id"]: item for item in state["paper_framework"]["paper_fragments"]}
            self.assertEqual(fragments["PF1"]["status"], "current")
            self.assertEqual(fragments["PF2"]["status"], "current")
            self.assertEqual(fragments["PF3"]["status"], "stale")
            self.assertEqual(fragments["PF4"]["status"], "stale")
            self.assertEqual(state["paper_framework"]["sync_status"], "stale")

    def test_analysis_evidence_core_reject_requires_redo_but_peripheral_reject_does_not(self):
        base = {
            "analysis_evidence": [
                {
                    "id": "E1",
                    "target_claim": "推荐方案全域稳定",
                    "disposition": "reject",
                    "required_action": "删除全域稳定表述",
                    "rejects_core_answer": False,
                    "status": "current",
                }
            ],
            "result_analysis_status": "passed",
        }
        self.assertEqual(STATE._validate_analysis_evidence("Q1", base), [])

        core = {
            "analysis_evidence": [
                {
                    "id": "E2",
                    "target_claim": "最优方案为A",
                    "disposition": "reject",
                    "required_action": "回退主求解重新认证",
                    "rejects_core_answer": True,
                    "status": "current",
                }
            ],
            "result_analysis_status": "passed",
        }
        issues = STATE._validate_analysis_evidence("Q1", core)
        self.assertTrue(any("redo_required" in item for item in issues), issues)

    def test_audit_blocks_missing_ref_target_but_unused_label_is_warning(self):
        tex = r"""\documentclass{article}
\begin{document}
\section{测试}\label{sec:used-never}
参见式\eqref{eq:missing}。
\end{document}
"""
        findings = AUDIT.audit_text(tex)
        by_code = {item.code: item.severity for item in findings}
        self.assertEqual(by_code["missing_ref_target"], "blocking")
        self.assertEqual(by_code["unused_label"], "warning")

    def test_audit_checks_caption_abstract_and_keywords_without_math_inference(self):
        tex = r"""\documentclass{article}
\begin{document}
\begin{abstract}
摘要中不应放展示公式：\[x=1\]
\end{abstract}
\keywords{优化，仿真}
\begin{figure}
\caption{结果图}
\includegraphics{a.pdf}
\end{figure}
\begin{table}
\begin{tabular}{c}1\end{tabular}
\caption{结果表}
\end{table}
\end{document}
"""
        findings = AUDIT.audit_text(tex)
        by_code = {item.code: item.severity for item in findings}
        self.assertEqual(by_code["abstract_contains_float_or_display_formula"], "review_required")
        self.assertEqual(by_code["keyword_count"], "review_required")
        self.assertEqual(by_code["figure_caption_before_graphic"], "review_required")
        self.assertEqual(by_code["table_caption_after_table"], "review_required")

    def test_registered_terminology_drift_is_warning(self):
        tex = r"""\documentclass{article}
\begin{document}
本文的有效时长用于后续比较。
\end{document}
"""
        framework = """### Terminology Registry
| Term ID | 标准术语 | 定义 | 量纲/单位 | 允许简称 | 不推荐别名 | 易混术语 | 对应符号 | 适用范围 |
|---|---|---|---|---|---|---|---|---|
| T1 | 有效遮蔽时长 | 满足判据的累计时间 | s |  | 有效时长 | 总遮蔽时长 | T_e | 全文 |
### Numeric Profile
"""
        findings = AUDIT.audit_framework_semantics(tex, framework)
        by_code = {item.code: item.severity for item in findings}
        self.assertEqual(by_code["registered_terminology_drift"], "warning")

    def test_verified_numeric_precision_loss_blocks_and_six_digits_pass(self):
        framework = """### Numeric Profile
| Metric ID | 标准指标 | 符号 | 单位 | 展示形式 | 必要小数位 | 工作簿精度 | 正文精度 | 摘要精度 | 精度/评分依据 |
|---|---|---|---|---|---|---|---|---|---|
| N1 | 最优时间 | t^* | s | decimal | 6 | 8 | 6 | 6 | 已核验评分口径 |
### 各问依赖关系
"""
        low = r"""\documentclass{article}\begin{document}最优时间 10.1234 s。\end{document}"""
        findings = AUDIT.audit_framework_semantics(low, framework)
        by_code = {item.code: item.severity for item in findings}
        self.assertEqual(by_code["scoring_result_precision_loss"], "blocking")

        precise = r"""\documentclass{article}\begin{document}最优时间 10.123456 s。\end{document}"""
        findings = AUDIT.audit_framework_semantics(precise, framework)
        self.assertNotIn("scoring_result_precision_loss", {item.code for item in findings})

    def test_unverified_numeric_profile_shortfall_is_warning_not_blocking(self):
        framework = """### Numeric Profile
| Metric ID | 标准指标 | 符号 | 单位 | 展示形式 | 必要小数位 | 工作簿精度 | 正文精度 | 摘要精度 | 精度/评分依据 |
|---|---|---|---|---|---|---|---|---|---|
| N1 | 最优时间 | t^* | s | decimal | 6 | 8 | 6 | 6 | 默认高精度 |
### 各问依赖关系
"""
        tex = r"""\documentclass{article}\begin{document}最优时间 10.1234 s。\end{document}"""
        findings = AUDIT.audit_framework_semantics(tex, framework)
        by_code = {item.code: item.severity for item in findings}
        self.assertEqual(by_code["numeric_precision_anomaly"], "warning")


if __name__ == "__main__":
    unittest.main()
