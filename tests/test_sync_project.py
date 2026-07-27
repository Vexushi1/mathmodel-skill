import importlib.util
import tempfile
import unittest
import sys
from pathlib import Path

import yaml
from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]


def load_syncer():
    spec = importlib.util.spec_from_file_location("sync_project", ROOT / "scripts/sync_project.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_book(path: Path, sheet: str):
    book = Workbook()
    ws = book.active
    ws.title = sheet
    ws.append(["指标", "数值"])
    ws.append(["目标值", 1.0])
    book.save(path)


class TestSyncProject(unittest.TestCase):
    def test_discovers_artifacts_and_writes_report(self):
        syncer = load_syncer()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "问题一求解.py").write_text("def main():\n    return 1\n", encoding="utf-8")
            result = root / "结果数据表" / "问题一"
            result.mkdir(parents=True)
            write_book(result / "问题一求解结果.xlsx", "核心指标")
            write_book(result / "问题一敏感性与鲁棒性结果.xlsx", "参数敏感性")
            (result / "q1_plot.m").write_text('title(gca, "结果");', encoding="utf-8")
            (root / "模型论文框架.md").write_text(
                "- 最近同步：`x`\n- 最近同步时间：`x`\n- 当前状态：`current`\n",
                encoding="utf-8",
            )
            report = syncer.synchronize(root, write=True)
            self.assertIn("Q1", report["questions"])
            self.assertTrue((root / "sync_report.yaml").is_file())
            self.assertTrue(report["questions"]["Q1"]["matlab_has_title"])

    def test_hash_change_propagates_stale_but_never_passes_validation(self):
        syncer = load_syncer()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            code = root / "问题一求解.py"
            code.write_text("VALUE = 2\n", encoding="utf-8")
            result = root / "结果数据表" / "问题一"
            result.mkdir(parents=True)
            write_book(result / "问题一求解结果.xlsx", "核心指标")
            write_book(result / "问题一敏感性与鲁棒性结果.xlsx", "参数敏感性")
            state_dir = root / "state"
            state_dir.mkdir()
            state = {
                "subproblems": {
                    "Q1": {
                        "status": "validated",
                        "validation_status": "passed",
                        "result_summary_status": "current",
                        "validated_model_hash": "0" * 64,
                        "evidence": [],
                    }
                },
                "artifacts": {"code": [], "results": [], "figures": [], "papers": []},
                "paper_framework": {"sync_status": "current"},
            }
            (state_dir / "project_state.yaml").write_text(yaml.safe_dump(state, allow_unicode=True), encoding="utf-8")
            report = syncer.synchronize(root, write=True)
            updated = yaml.safe_load((state_dir / "project_state.yaml").read_text(encoding="utf-8"))
            self.assertEqual(report["stale_questions"], ["Q1"])
            self.assertEqual(updated["subproblems"]["Q1"]["validation_status"], "pending")
            self.assertEqual(updated["subproblems"]["Q1"]["result_summary_status"], "stale")


if __name__ == "__main__":
    unittest.main()
