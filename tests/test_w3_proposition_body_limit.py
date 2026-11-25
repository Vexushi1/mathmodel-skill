"""W3 I01/I02: full-paper body proposition limit, no justification bypass.

Only the existing State/Framework validators are invoked. The tests do not
simulate numerical execution, model approval, or infer a PDF review PASS.
"""
from pathlib import Path
from copy import deepcopy
import importlib.util
import sys
import unittest
import yaml

from tests.claim_schema_reference import previous_w3_proposition_schema

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


STATE = load("w3_state_validator", "scripts/validate_project_state.py")
FRAMEWORK = load("w3_framework_validator", "scripts/validate_model_paper_framework.py")


def entries(count, ids=None):
    ids = ids or [f"P{i}" for i in range(1, count + 1)]
    return [{"id": prop_id, "status": "candidate"} for prop_id in ids]


def plan(count, *, legacy_exception=False):
    lines = ["### 命题与证明规划", f"- 当前计划命题数：{count}"]
    if legacy_exception:
        lines += ["- 超预算状态：justified", "- 超预算说明（若适用）：旧项目曾说明原因"]
    lines += [
        "| 命题ID | 对应小问 | 名称与类型 | 前提/定义域 | 核心结论 | 证明等级 | 下游模型/计算作用 | 失效边界 | 状态 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for i in range(1, count + 1):
        lines.append(
            f"| P{i} | Q1 | 性质{i} | 域 | 结论 | B | 简化 | 边界 | candidate |"
        )
    lines.append("### 正文章节与交付映射")
    return "\n".join(lines)


class W3PropositionBodyLimitTests(unittest.TestCase):
    def test_authority_and_consumers_require_no_overlimit_exception(self):
        reasoning = yaml.safe_load(
            (ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8")
        )["proposition_governance"]
        self.assertEqual(reasoning["governance_level"], "hard")
        self.assertEqual(reasoning["maximum_body_propositions"], 4)
        self.assertTrue(reasoning["automatic_rejection_over_budget"])
        self.assertIn("不设超额豁免", reasoning["rule"])

        output = yaml.safe_load(
            (ROOT / "core/output_contract.yaml").read_text(encoding="utf-8")
        )["proposition_contract"]
        self.assertEqual(output["count_scope"], "full_paper_body")
        self.assertTrue(output["automatic_rejection_over_budget"])
        self.assertIn("正文正式命题最多 4 个", (ROOT / "packs/artifact/proposition_proof.md").read_text(encoding="utf-8"))
        self.assertIn("核心证明", reasoning["proof_placement_rule"])

    def test_word_and_latex_consumers_follow_the_current_body_limit(self):
        for relative in (
            "modules/05_writing/docx.md",
            "packs/artifact/docx.md",
            "packs/artifact/latex.md",
        ):
            with self.subTest(relative=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn("core/writing_reasoning_contract.yaml", text)
                self.assertNotIn("超过默认预算时已有必要性说明", text)
                self.assertNotIn("超过默认 0--4 预算", text)
                self.assertNotIn("超过预算时按实际数学作用说明必要性，不自动否决", text)
        checklist = (ROOT / "templates/writing/docx_check.md").read_text(encoding="utf-8")
        self.assertIn("全文正文正式命题总数是否不超过 4 个", checklist)
        self.assertIn("核心证明是否未因篇幅、难度或分页需要被移附录", checklist)
        preamble = (ROOT / "templates/latex/cumcm/hsk/config/preamble.tex").read_text(encoding="utf-8")
        self.assertIn("全文正文正式命题总数不超过 4 个", preamble)
        manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8"))
        plan = manifest["artifact_catalog"]["proposition_plan"]
        self.assertIn("正文正式命题总数不超过4个", plan)
        self.assertIn("core/writing_reasoning_contract.yaml#proposition_governance", plan)

    def test_state_count_rejects_five_even_with_legacy_justification(self):
        for count in (0, 1, 4):
            with self.subTest(count=count):
                st = "planned" if count else "not_assessed"
                framework = {
                    "proposition_count": count, "proposition_status": st,
                    "propositions": entries(count), "proposition_budget_status": "within_default_budget",
                }
                issues, _, _ = STATE._validate_propositions(framework, framework_sync="current")
                self.assertFalse(issues, issues)
        five = {
            "proposition_count": 5, "proposition_status": "planned",
            "propositions": entries(5),
            "proposition_budget_status": "justified",
            "proposition_budget_reason": "历史上认为不可替代",
        }
        issues, _, _ = STATE._validate_propositions(five, framework_sync="current")
        self.assertTrue(any("exceeding the full-paper body limit" in issue for issue in issues), issues)

    def test_state_schema_rejects_five_but_keeps_historical_identifiers(self):
        schema = yaml.safe_load(
            (ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8")
        )
        props = schema["properties"]["paper_framework"]["properties"]
        self.assertEqual(props["proposition_count"]["maximum"], 4)
        self.assertEqual(props["propositions"]["maxItems"], 4)
        self.assertEqual(
            schema["$defs"]["proposition_entry"]["properties"]["id"]["pattern"],
            "^P[1-9][0-9]*$",
        )
        historical = {
            "proposition_count": 3, "proposition_status": "planned",
            "propositions": entries(3, ["P3", "P5", "P9"]),
        }
        issues, ids, _ = STATE._validate_propositions(historical, framework_sync="current")
        self.assertEqual(issues, [])
        self.assertEqual(ids, {"P3", "P5", "P9"})

    def test_w3_schema_inverse_is_exact_and_rejects_unapproved_mutations(self):
        schema = yaml.safe_load(
            (ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8")
        )
        previous = previous_w3_proposition_schema(schema)
        before = previous["properties"]["paper_framework"]["properties"]
        self.assertNotIn("maximum", before["proposition_count"])
        self.assertNotIn("maxItems", before["propositions"])
        self.assertNotIn("description", before["proposition_budget_status"])
        self.assertNotIn("description", before["proposition_budget_reason"])
        self.assertEqual(
            schema["properties"]["paper_framework"]["properties"]["proposition_count"]["maximum"],
            4,
        )
        for field, patch in (
            ("proposition_count", {"maximum": 5}),
            ("propositions", {"maxItems": 5}),
            ("proposition_budget_status", {"description": "changed"}),
            ("proposition_budget_reason", {"description": "changed"}),
        ):
            with self.subTest(field=field):
                changed = deepcopy(schema)
                changed["properties"]["paper_framework"]["properties"][field].update(patch)
                with self.assertRaisesRegex(AssertionError, "W3 proposition schema inverse rejected"):
                    previous_w3_proposition_schema(changed)

    def test_framework_plans_have_hard_limit_in_lenient_and_strict_modes(self):
        for strict in (False, True):
            for count in (0, 4):
                with self.subTest(strict=strict, count=count):
                    issues, observed, ids = FRAMEWORK._validate_proposition_plan(
                        plan(count), strict=strict
                    )
                    self.assertEqual(issues, [])
                    self.assertEqual(observed, count)
                    self.assertEqual(len(ids), count)
            issues, observed, _ = FRAMEWORK._validate_proposition_plan(
                plan(5, legacy_exception=True), strict=strict
            )
            self.assertEqual(observed, 5)
            self.assertTrue(any("exceeds full-paper body limit" in s for s in issues), issues)


if __name__ == "__main__":
    unittest.main()
