import importlib.util
import sys
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_resolver():
    path = ROOT / "scripts/resolve_workflow.py"
    spec = importlib.util.spec_from_file_location("read_path_resolver", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestReadPathSemanticClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resolver = load_resolver()
        manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8"))
        cls.available = sorted(
            set(manifest.get("external_artifacts", []))
            | set(manifest.get("artifact_catalog", {}))
        )

    def resolve(self, intent, **kwargs):
        return self.resolver.resolve_workflow(
            intent,
            available_artifacts=self.available,
            preprocessing_decision=kwargs.pop("preprocessing_decision", "not_needed"),
            **kwargs,
        )

    def test_default_load_is_minimal(self):
        router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        self.assertEqual(router["default_load"], ["core/hsk_core_policy.md"])
        self.assertEqual(router["load_policy"]["principle"], "minimal_route_specific")
        self.assertIn("core/module_manifest.yaml", router["load_policy"]["resolver_internal_only"])
        self.assertNotIn("core/writing_reasoning_contract.yaml", router["default_load"])

    def test_figure_route_does_not_preload_unrelated_core_contracts(self):
        plan = self.resolve("figures")
        contracts = set(plan["contracts"])
        self.assertIn("core/hsk_core_policy.md", contracts)
        for path in (
            "core/module_manifest.yaml",
            "core/task_taxonomy.yaml",
            "core/user_execution_contract.yaml",
            "core/global_preprocessing_contract.yaml",
            "core/code_quality_contract.yaml",
            "core/writing_reasoning_contract.yaml",
        ):
            self.assertNotIn(path, contracts)
        self.assertIn("modules/04_figure_evidence.md", plan["modules"])
        self.assertIn("packs/artifact/figure.md", plan["packs"])

    def test_latex_route_loads_reasoning_but_not_code_or_preprocessing_contracts(self):
        plan = self.resolve("latex")
        contracts = set(plan["contracts"])
        self.assertEqual(
            contracts,
            {
                "core/bootstrap.yaml",
                "core/hsk_core_policy.md",
                "core/writing_reasoning_contract.yaml",
            },
        )
        self.assertNotIn("core/user_execution_contract.yaml", contracts)
        self.assertNotIn("core/global_preprocessing_contract.yaml", contracts)
        self.assertNotIn("core/task_taxonomy.yaml", contracts)

    def test_model_selection_loads_reasoning_contract(self):
        plan = self.resolve(
            "model_selection",
            objective="optimization",
            structures=["stochastic"],
        )
        self.assertIn("core/writing_reasoning_contract.yaml", set(plan["contracts"]))
        self.assertIn("modules/02_model_design.md", plan["modules"])

    def test_problem_analysis_loads_taxonomy_but_not_execution_or_reasoning_contracts(self):
        plan = self.resolve("problem_analysis")
        contracts = set(plan["contracts"])
        self.assertIn("core/task_taxonomy.yaml", contracts)
        self.assertNotIn("core/user_execution_contract.yaml", contracts)
        self.assertNotIn("core/code_quality_contract.yaml", contracts)
        self.assertNotIn("core/global_preprocessing_contract.yaml", contracts)
        self.assertNotIn("core/writing_reasoning_contract.yaml", contracts)

    def test_code_route_loads_required_contracts(self):
        plan = self.resolve(
            "code_and_solution",
            objective="optimization",
            structures=["stochastic"],
        )
        contracts = set(plan["contracts"])
        for path in (
            "core/task_taxonomy.yaml",
            "core/global_preprocessing_contract.yaml",
            "core/user_execution_contract.yaml",
            "core/code_quality_contract.yaml",
        ):
            self.assertIn(path, contracts)

    def test_result_analysis_loads_required_contracts(self):
        plan = self.resolve(
            "result_analysis",
            objective="evaluation",
            structures=["stochastic"],
        )
        contracts = set(plan["contracts"])
        for path in (
            "core/task_taxonomy.yaml",
            "core/global_preprocessing_contract.yaml",
            "core/user_execution_contract.yaml",
            "core/code_quality_contract.yaml",
        ):
            self.assertIn(path, contracts)

    def test_returned_workbook_validation_loads_execution_only(self):
        plan = self.resolve("returned_workbook_validation")
        contracts = set(plan["contracts"])
        self.assertIn("core/user_execution_contract.yaml", contracts)
        self.assertNotIn("core/task_taxonomy.yaml", contracts)
        self.assertNotIn("core/global_preprocessing_contract.yaml", contracts)
        self.assertNotIn("core/code_quality_contract.yaml", contracts)
        self.assertNotIn("core/writing_reasoning_contract.yaml", contracts)

    def test_figure_pack_cannot_reverse_authoritative_rules(self):
        text = (ROOT / "packs/artifact/figure.md").read_text(encoding="utf-8")
        self.assertIn("唯一权威为 `modules/04_figure_evidence.md`", text)
        self.assertIn("preprocessing_decision", text)
        self.assertIn("中高饱和、高对比", text)
        self.assertNotIn("默认白底、细轴、低饱和深色", text)
        self.assertNotIn("正式结果图只读取本问", text)

    def test_code_pack_inherits_preprocessing_source(self):
        text = (ROOT / "packs/artifact/code.md").read_text(encoding="utf-8")
        self.assertIn("数据读取必须继承 current `preprocessing_decision`", text)
        self.assertIn("禁止再次直接读取对应共享原始数据", text)
        self.assertNotIn("已验收主工作簿和必要原始数据", text)

    def test_active_matlab_templates_do_not_reintroduce_old_palette(self):
        q1 = (ROOT / "templates/matlab/q1_plot.m").read_text(encoding="utf-8")
        process = (ROOT / "templates/matlab/data_process.m").read_text(encoding="utf-8")
        style = (ROOT / "templates/matlab/hsk_apply_scientific_style.m").read_text(encoding="utf-8")
        self.assertIn("[20, 120, 255] / 255", q1)
        self.assertIn("[240, 68, 68] / 255", process)
        for token in ("brightBlue", "vividRed", "brightGreen", "brightOrange", "brightPurple"):
            self.assertIn(token, style)
        self.assertNotIn("[23, 59, 94] / 255", q1)
        self.assertNotIn("[23, 59, 94] / 255", process)
        self.assertNotIn("唯一Python脚本", q1)

    def test_figure_assets_cover_active_v7_line(self):
        assets = yaml.safe_load((ROOT / "assets/figure_assets.yaml").read_text(encoding="utf-8"))
        self.assertEqual(assets["skill_compatibility"], ">=7.4.2,<8.0.0")
        self.assertFalse(assets["default_load"])
        self.assertIn("不得改变模型结果", "".join(assets["rules"]))


if __name__ == "__main__":
    unittest.main()
