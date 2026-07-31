import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
PIPELINE_ROOT = ROOT / "templates" / "code"
if str(PIPELINE_ROOT) not in sys.path:
    sys.path.insert(0, str(PIPELINE_ROOT))

from hsk_pipeline import (  # noqa: E402
    PipelineConfig,
    ResultAnalysisResult,
    REQUIRED_CAPABILITIES,
    run_primary_pipeline,
    run_result_analysis_pipeline,
)
from hsk_pipeline.result_io import read_workbook_tables  # noqa: E402


def framework_text() -> str:
    return "# 模型论文框架\n\n> 本文件只保留当前有效版本。\n\n### Q1：测试\n"


def config(root: Path) -> PipelineConfig:
    framework = root / "模型论文框架.md"
    framework.write_text(framework_text(), encoding="utf-8")
    return PipelineConfig(
        project_root=root,
        framework_path=framework,
        framework_section="### Q1：测试",
        problem_name="问题一",
        objective="optimization",
        structures=(),
        capabilities={name: False for name in REQUIRED_CAPABILITIES},
    )


def load_data(cfg, audit):
    return {"原始数据": pd.DataFrame({"x": [1.0]})}


def preprocess(raw, cfg, audit):
    return raw


def build_features(clean, cfg):
    return {"x": 1.0}


def solve(features, cfg):
    return {
        "核心指标": pd.DataFrame({"指标": ["目标值"], "数值": [1.0]}),
        "推荐方案": pd.DataFrame({"方案": ["A"]}),
    }


def constraints(solution, cfg):
    return None


def sync_primary(primary):
    return None


def sync_analysis(primary, path, tables):
    return None


class TestSplitPipelineRuntime(unittest.TestCase):
    def test_failed_primary_quality_is_written_before_blocking(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cfg = config(root)

            def quality(context, checked):
                return pd.DataFrame(
                    {"检查项": ["收敛"], "是否通过": [False], "证据": ["迭代上限"]}
                )

            with self.assertRaisesRegex(RuntimeError, "失败证据已写入"):
                run_primary_pipeline(
                    cfg,
                    load_data_hook=load_data,
                    preprocess_hook=preprocess,
                    build_features_hook=build_features,
                    solve_hook=solve,
                    constraint_hook=constraints,
                    quality_hook=quality,
                    framework_sync_hook=sync_primary,
                )
            workbook = root / "结果数据表/问题一/问题一求解结果.xlsx"
            self.assertTrue(workbook.is_file())
            quality_table = read_workbook_tables(workbook)["主结果质量门"]
            self.assertFalse(bool(quality_table.loc[0, "是否通过"]))

    def test_redo_required_persists_analysis_and_marks_state_stale(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cfg = config(root)
            state_dir = root / "state"
            state_dir.mkdir()
            state = {
                "project": {"current_phase": "result_analysis"},
                "subproblems": {
                    "Q1": {
                        "status": "solved",
                        "result_quality_status": "passed",
                        "result_analysis_status": "pending",
                        "result_summary_status": "current",
                        "result_summary_anchor": "### Q1：测试",
                        "framework_section": "### Q1：测试",
                        "artifacts_stale": False,
                        "stale_layers": [],
                        "proposition_refs": [],
                        "artifact_hashes": {},
                        "validated_artifact_hashes": {},
                    }
                },
                "paper_framework": {"sync_status": "current"},
            }
            state_path = state_dir / "project_state.yaml"
            state_path.write_text(yaml.safe_dump(state, allow_unicode=True), encoding="utf-8")

            def quality(context, checked):
                return pd.DataFrame(
                    {"检查项": ["收敛"], "是否通过": [True], "证据": ["通过"]}
                )

            primary = run_primary_pipeline(
                cfg,
                load_data_hook=load_data,
                preprocess_hook=preprocess,
                build_features_hook=build_features,
                solve_hook=solve,
                constraint_hook=constraints,
                quality_hook=quality,
                framework_sync_hook=sync_primary,
            )

            tables = {
                "分析设计": pd.DataFrame(
                    {
                        "风险来源": ["结构"],
                        "分析问题": ["结论是否依赖模型形式"],
                        "方法": ["结构稳健性"],
                        "指标": ["方案变化"],
                        "通过标准": ["方案保持"],
                    }
                ),
                "结构稳健性": pd.DataFrame(
                    {
                        "替代结构": ["B"],
                        "核心设定": ["替代损失"],
                        "结果指标": [2.0],
                        "与主模型差异": [1.0],
                    }
                ),
                "结论稳定性汇总": pd.DataFrame(
                    {
                        "核心结论": ["方案A最优"],
                        "分析方法": ["结构稳健性"],
                        "稳定范围": ["仅主结构"],
                        "是否保持": [False],
                    }
                ),
            }

            def analyze(result):
                return ResultAnalysisResult(
                    tables=tables,
                    status="redo_required",
                    methods=("结构稳健性",),
                    reason="替代结构改变最优方案",
                    restart_phase="model_design",
                )

            with self.assertRaisesRegex(RuntimeError, "回退到 model_design"):
                run_result_analysis_pipeline(
                    primary,
                    analysis_hook=analyze,
                    framework_sync_hook=sync_analysis,
                )
            analysis_path = root / "结果数据表/问题一/问题一结果深化分析.xlsx"
            self.assertTrue(analysis_path.is_file())
            updated = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            entry = updated["subproblems"]["Q1"]
            self.assertEqual(entry["result_analysis_status"], "redo_required")
            self.assertTrue(entry["artifacts_stale"])
            self.assertIn("result_analysis_workbook", entry["stale_layers"])
            self.assertEqual(updated["project"]["current_phase"], "model_design")
            self.assertEqual(updated["paper_framework"]["sync_status"], "stale")


if __name__ == "__main__":
    unittest.main()
