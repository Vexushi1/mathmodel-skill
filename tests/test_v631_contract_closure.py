import copy
import importlib.util
import sys
import unittest
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TestV631ContractClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.framework = load_module("v631_framework", "scripts/validate_model_paper_framework.py")
        cls.state_validator = load_module("v631_state", "scripts/validate_project_state.py")
        cls.result_io = load_module("v631_result_io", "templates/code/hsk_pipeline/result_io.py")
        cls.example = yaml.safe_load((ROOT / "state/project_state.example.yaml").read_text(encoding="utf-8"))

    def base_solution_tables(self):
        return {
            "核心指标": pd.DataFrame({"指标": ["MAE"], "数值": [0.1]}),
            "数据审计": pd.DataFrame(
                {"等级": ["Info"], "检查项": ["字段"], "信息": ["通过"], "处理方式": ["无"]}
            ),
            "主结果质量门": pd.DataFrame(
                {"检查项": ["基础精度"], "是否通过": [True], "证据": ["达到门槛"]}
            ),
        }

    def test_compact_and_full_framework_modes(self):
        compact = "# 模型论文框架\n只保留当前有效版本\n## 当前有效口径\n## 各问模型与结果\n## 图表证据链\n## 待办与缺口\n"
        full = compact + "## 论文整体框架\n### 命题与证明规划\n全文命题上限：4\n当前计划命题数：0\n## 综合检验与跨问结论\n## 同步检查\n"
        self.assertEqual(self.framework.validate_framework_text(compact, mode="compact"), [])
        self.assertTrue(self.framework.validate_framework_text(compact, mode="full"))
        self.assertEqual(self.framework.validate_framework_text(full, mode="full"), [])

    def test_capability_alias_must_match_authoritative_top_level(self):
        payload = copy.deepcopy(self.example)
        top = payload["subproblems"]["Q1"]["capabilities"]
        payload["subproblems"]["Q1"]["classification"]["capabilities"] = copy.deepcopy(top)
        self.assertFalse(any("classification.capabilities" in issue for issue in self.state_validator.validate_state_payload(payload, project_root=ROOT)))
        payload["subproblems"]["Q1"]["classification"]["capabilities"]["requires_leakage_check"] = True
        issues = self.state_validator.validate_state_payload(payload, project_root=ROOT)
        self.assertTrue(any("classification.capabilities" in issue for issue in issues), issues)

    def test_objective_profile_drives_workbook_requirement(self):
        tables = self.base_solution_tables()
        with self.assertRaisesRegex(ValueError, "objective:prediction"):
            self.result_io.validate_workbook_tables(tables, "solution", objective="prediction")
        tables["误差指标"] = pd.DataFrame({"指标": ["MAE"], "数值": [0.1]})
        self.result_io.validate_workbook_tables(tables, "solution", objective="prediction")

    def test_structure_profile_drives_workbook_requirement(self):
        tables = self.base_solution_tables()
        tables["推荐方案"] = pd.DataFrame({"方案": ["A"]})
        with self.assertRaisesRegex(ValueError, "structure:network"):
            self.result_io.validate_workbook_tables(
                tables, "solution", objective="optimization", structures=("network",)
            )
        tables["节点结果"] = pd.DataFrame({"节点": ["A"], "数值": [1.0]})
        self.result_io.validate_workbook_tables(
            tables, "solution", objective="optimization", structures=("network",)
        )

    def test_result_analysis_requires_real_method_and_summary(self):
        tables = {
            "分析设计": pd.DataFrame(
                {"风险来源": ["结构"], "分析问题": ["结论依赖性"], "方法": ["结构稳健性"], "指标": ["差异"], "通过标准": ["小于5%"]}
            ),
            "结构稳健性": pd.DataFrame(
                {"替代结构": ["B"], "核心设定": ["替代损失"], "结果指标": [1.0], "与主模型差异": [0.01]}
            ),
            "结论稳定性汇总": pd.DataFrame(
                {"核心结论": ["保持"], "分析方法": ["结构稳健性"], "稳定范围": ["两种结构"], "是否保持": [True]}
            ),
        }
        self.result_io.validate_workbook_tables(tables, "result_analysis")


if __name__ == "__main__":
    unittest.main()
