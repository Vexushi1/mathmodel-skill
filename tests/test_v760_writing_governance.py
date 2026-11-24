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


FRAMEWORK = load_module("framework_v760", ROOT / "scripts/validate_model_paper_framework.py")
AUDIT = load_module("audit_v760", ROOT / "scripts/audit_paper_prose.py")


class TestV760WritingGovernance(unittest.TestCase):
    def test_reasoning_contract_has_tiered_governance_and_citation_evidence(self):
        contract = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(set(contract["rule_governance"]["levels"]), {"hard", "default", "recommendation"})
        rule = contract["proposition_governance"]
        self.assertTrue(rule["automatic_rejection_over_budget"])
        self.assertEqual(rule["default_budget"], [0, 4])
        self.assertEqual(rule["maximum_body_propositions"], 4)
        self.assertEqual(rule["count_scope"], "full_paper_body")
        self.assertEqual(rule["governance_level"], "hard")
        self.assertIn("citation_evidence", contract)
        self.assertEqual(contract["model_evaluation"], {"authority": "modules/05_writing/paper_writing_protocol.md#15-模型评价逐问结论与附录"})
        self.assertEqual(
            set(contract["adaptive_core_model_summary"]["modes"]),
            {"required", "inline", "not_applicable"},
        )

    def test_consumers_do_not_restore_removed_mechanical_hard_rules(self):
        files = [
            ROOT / "modules/05_writing/latex.md",
            ROOT / "modules/05_writing/docx.md",
            ROOT / "modules/05_writing/ai_cleanup.md",
            ROOT / "modules/06_review_delivery.md",
            ROOT / "modules/06_review/content_review.md",
            ROOT / "modules/06_review/final_delivery.md",
            ROOT / "packs/artifact/latex.md",
            ROOT / "packs/artifact/docx.md",
            ROOT / "packs/artifact/proposition_proof.md",
            ROOT / "templates/writing/docx_check.md",
            ROOT / "templates/latex/cumcm/hsk/hsk_main.tex",
            ROOT / "templates/latex/diangong/main.tex",
        ]
        combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
        self.assertNotIn("优点数必须大于缺点数", combined)
        self.assertNotIn("优点数量必须大于缺点数量", combined)
        self.assertIn("全文正文正式命题最多 4 个", combined)
        self.assertNotIn("超出预算仍可保留额外命题", combined)
        self.assertIn("required / inline / not_applicable", combined)

        protocol = (ROOT / "modules/05_writing/paper_writing_protocol.md").read_text(encoding="utf-8")
        self.assertIn("简要说明模型自身的优点与不足，通常列3项优点、1–2项不足。", protocol)
        self.assertIn("模型评价不能替代误差、残差、可行性", protocol)
        self.assertNotIn("优点和缺点的数量按模型实际决定", protocol)
        self.assertNotIn("优点数必须大于缺点数", protocol)
        self.assertNotIn("优点数量必须大于缺点数量", protocol)

    def test_framework_template_is_project_memory_with_formula_and_citation_trace(self):
        text = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        self.assertIn("只保留**当前有效项目事实、选择、状态与证据位置**", text)
        self.assertIn("### 核心公式 Trace", text)
        self.assertIn("### Citation Evidence", text)
        self.assertIn("核心模型收束：`required / inline / not_applicable`", text)
        self.assertNotIn("命题准入检查：", text)

    def test_framework_validator_allows_five_propositions_when_justified(self):
        rows = "\n".join(
            f"| P{i} | Q1 | 命题{i} | 条件 | 结论 | B | 降维 | 边界 | current |"
            for i in range(1, 6)
        )
        text = f"""# 模型论文框架

> 本文件只保留当前有效项目事实。
- 框架模式: full
- 当前状态: current

## 当前有效口径

## 论文整体框架

### 命题与证明规划
- 当前计划命题数：5
- 默认正文预算：0--4
- 超预算状态：`justified`
- 超预算说明（若适用）：五个命题分别承担不可合并的等价、可行性、单调、边界和解结构作用。
- 当前命题状态：`current`

| 命题ID | 对应小问 | 名称与类型 | 前提/定义域 | 核心结论 | 证明等级 | 下游模型/计算作用 | 失效边界 | 状态 |
|---|---|---|---|---|---|---|---|---|
{rows}

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
        issues = FRAMEWORK.validate_framework_text(text, strict=True, mode="full")
        self.assertEqual(issues, [])

    def test_bib_audit_blocks_missing_and_duplicate_keys_but_only_warns_unused(self):
        tex = r"""\documentclass{article}
\begin{document}
已有研究见 \cite{used,missing}。
\end{document}
"""
        bib = """@article{used, title={A}}
@article{used, title={B}}
@article{unused, title={C}}
"""
        findings = AUDIT.audit_bibliography(tex, bib)
        by_code = {item.code: item.severity for item in findings}
        self.assertEqual(by_code["duplicate_bib_key"], "blocking")
        self.assertEqual(by_code["missing_bib_key"], "blocking")
        self.assertEqual(by_code["unused_bib_entries"], "warning")

    def test_project_state_keeps_stable_p5_ids_but_blocks_body_count_over_four(self):
        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        proposition_id = schema["$defs"]["proposition_entry"]["properties"]["id"]["pattern"]
        self.assertEqual(proposition_id, "^P[1-9][0-9]*$")
        framework = schema["properties"]["paper_framework"]["properties"]
        self.assertEqual(framework["proposition_count"]["maximum"], 4)
        self.assertEqual(framework["propositions"]["maxItems"], 4)
        self.assertIn("proposition_budget_status", framework)
        self.assertIn("proposition_budget_reason", framework)
        refs = schema["properties"]["subproblems"]["additionalProperties"]["properties"]["proposition_refs"]
        self.assertNotIn("maxItems", refs)


if __name__ == "__main__":
    unittest.main()
