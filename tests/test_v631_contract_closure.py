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
        tables = {
            "核心指标": pd.DataFrame({"指标": ["MAE"], "数值": [0.1]}),
            "数据审计": pd.DataFrame({"等级": ["Info"], "检查项": ["字段"], "信息": ["通过"], "处理方式": ["无"]}),
        }
        with self.assertRaisesRegex(ValueError, "objective:prediction"):
            self.result_io.validate_workbook_tables(tables, "solution", objective="prediction")
        tables["误差指标"] = pd.DataFrame({"指标": ["MAE"], "数值": [0.1]})
        self.result_io.validate_workbook_tables(tables, "solution", objective="prediction")

    def test_structure_profile_drives_workbook_requirement(self):
        tables = {
            "核心指标": pd.DataFrame({"指标": ["目标"], "数值": [1.0]}),
            "数据审计": pd.DataFrame({"等级": ["Info"], "检查项": ["字段"], "信息": ["通过"], "处理方式": ["无"]}),
            "推荐方案": pd.DataFrame({"方案": ["A"]}),
        }
        with self.assertRaisesRegex(ValueError, "structure:network"):
            self.result_io.validate_workbook_tables(tables, "solution", objective="optimization", structures=("network",))
        tables["节点结果"] = pd.DataFrame({"节点": ["A"], "数值": [1.0]})
        self.result_io.validate_workbook_tables(tables, "solution", objective="optimization", structures=("network",))


if __name__ == "__main__":
    unittest.main()
