"""Exercise physical Figure outputs and their evidence through the normal resolver and synchronizer."""
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]
import resolve_workflow
from resolve_runtime import resolve_runtime
import sync_project
import test_runtime_consistency_repairs as fixtures


class FigureRoutingTests(unittest.TestCase):
    def test_two_outputs_share_reading_but_not_numerical_qualification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            fixtures.MechanismScopeTests().make_project(root)
            before = fixtures.file_bytes(root)
            for request in (
                "为问题一绘制机理图和误差分布图。",
                "同一份题面，请设计这张机理草图和预测误差结果图。现有材料能落到哪里就先做到哪里。",
                "绘制残差图，以及一张机理图。",
            ):
                with self.subTest(request=request):
                    plan = resolve_runtime(request=request, project_root=root, question="Q1")
                    group = plan["figure_composition"]
                    self.assertEqual(group["layout"], "separate")
                    self.assertEqual(group["gate_execution"], "not_assessed_by_router")
                    mechanism, result = group["deliveries"]
                    self.assertEqual(mechanism["delivery_scope"], "mechanism")
                    self.assertEqual(mechanism["evidence_status"], "base_inputs_verified")
                    self.assertEqual(mechanism["missing_verified_artifacts"], [])
                    self.assertEqual(result["delivery_scope"], "figures")
                    self.assertIn("accepted_solution_workbook", result["missing_verified_artifacts"])
                    self.assertIn("validated_results", result["missing_verified_artifacts"])
                    read = {row["path"] for row in plan["reading_plan"]["read_now"]}
                    self.assertTrue({"templates/figure/mechanism_contract.md",
                                     "templates/figure/result_figure_contract.md"} <= read)
            self.assertEqual(fixtures.file_bytes(root), before)

    def test_independent_editable_gates_use_both_scopes_in_execution_order(self):
        request = "绘制可编辑机理图和预测误差图。"
        for plan in (resolve_workflow.resolve_workflow(request=request), resolve_runtime(request=request)):
            with self.subTest(resolver="assurance" in plan):
                self.assertEqual(plan["figure_composition"]["layout"], "separate")
                gates = plan["pre_delivery_gates"]
                self.assertEqual([g["name"] for g in gates].count("semantic_governance"), 1)
                sync = [g for g in gates if g["name"] == "project_sync"]
                self.assertEqual([g["delivery_scope"] for g in sync], ["mechanism", "figures"])
                self.assertIn("--mechanism-spec", sync[0]["command"])
                self.assertNotIn("--write", sync[0]["command"])
                self.assertNotIn("--mechanism-spec", sync[1]["command"])

    def test_one_physical_figure_with_numerical_evidence_never_claims_a_separate_mechanism(self):
        for request in (
            "在可编辑机理图中标注预测误差值。",
            "把机理图和误差分布图合成一张图。",
            "将误差图作为机理图的子图。",
            "机理图依照工作簿数值着色。",
        ):
            with self.subTest(request=request):
                plan = resolve_runtime("editable_mechanism_diagram", request=request,
                                       available_artifacts=["locked_model_spec", "accepted_solution_workbook"])
                composition = plan["figure_composition"]
                self.assertEqual((composition["layout"], plan["delivery_scope"]), ("single_numeric", "figures"))
                self.assertEqual(len(composition["deliveries"]), 1)
                row = composition["deliveries"][0]
                self.assertEqual(row["delivery_scope"], "figures")
                self.assertIn("accepted_solution_workbook", row["missing_verified_artifacts"])
                self.assertEqual(row["evidence_status"], "not_verified")
                self.assertFalse(any(g["delivery_scope"] == "mechanism" for g in plan["pre_delivery_gates"]))

    def test_without_a_physical_pair_existing_scopes_and_review_only_intent_remain(self):
        for intents, request, scope in (
            ("editable_mechanism_diagram", "只画一张可编辑机理图。", "mechanism"),
            ("figures", "绘制一张误差分布图。", "figures"),
            (["editable_mechanism_diagram", "figures"], "", "figures"),
        ):
            plan = resolve_runtime(intents, request=request)
            self.assertNotIn("figure_composition", plan)
            self.assertEqual(plan["delivery_scope"], scope)
        semantic = resolve_runtime("figures", request="修改模型参数，再画机理图和误差图。")
        self.assertNotIn("figure_composition", semantic)
        self.assertEqual(semantic["reading_plan"]["profile"], "full")

    def test_verification_of_one_exact_spec_cannot_qualify_its_numeric_neighbor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            pure = fixtures.MechanismScopeTests().make_project(root)
            numeric = yaml.safe_load(yaml.safe_dump(pure).replace("q1_occlusion", "q1_numeric"))
            numeric["figure_id"] = "MF-Q1-02"
            numeric["semantic_anchors"]["result_evidence"] = ["问题一求解结果.xlsx#核心指标"]
            numeric["artifact"]["spec_sha256"] = fixtures.GENERATOR.canonical_spec_sha256(numeric)
            numeric_path = numeric["artifact"]["spec_source"]
            (root / numeric_path).write_text(yaml.safe_dump(numeric, allow_unicode=True), encoding="utf-8")
            before = fixtures.file_bytes(root)
            pure_path = pure["artifact"]["spec_source"]
            scoped = sync_project.synchronize(root, delivery_scope="mechanism", mechanism_spec=pure_path, write=True)
            self.assertEqual(scoped["status"], "passed", scoped["issues"])
            self.assertEqual(scoped["mechanism_spec"], pure_path)
            self.assertFalse(scoped["write"])
            self.assertNotIn(numeric_path, scoped["observed_sources"])
            for selected in (None, numeric_path):
                report = sync_project.synchronize(root, delivery_scope="mechanism", mechanism_spec=selected)
                self.assertEqual(report["status"], "failed")
                self.assertTrue(any("数值证据" in issue for issue in report["issues"]), report["issues"])
            absent = sync_project.synchronize(root, delivery_scope="mechanism",
                                               mechanism_spec="figures/source/absent.mechanism.yaml")
            self.assertEqual(absent["status"], "failed")
            for scope, path in (("figures", pure_path), ("mechanism", "../outside.mechanism.yaml")):
                with self.assertRaises(ValueError):
                    sync_project.synchronize(root, delivery_scope=scope, mechanism_spec=path, write=True)
            self.assertEqual(fixtures.file_bytes(root), before)


if __name__ == "__main__":
    unittest.main()
