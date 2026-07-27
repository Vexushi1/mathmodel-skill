import importlib.util
import sys
import tempfile
import unittest
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


def append_sheet(book: Workbook, title: str, headers, row):
    if len(book.sheetnames) == 1 and book.active.max_row == 1 and book.active["A1"].value is None:
        ws = book.active
        ws.title = title
    else:
        ws = book.create_sheet(title)
    ws.append(list(headers))
    ws.append(list(row))


def write_solution(path: Path, *, constraint=False, out_of_sample=False):
    book = Workbook()
    append_sheet(book, "核心指标", ["指标", "数值"], ["目标值", 1.0])
    append_sheet(book, "数据审计", ["等级", "检查项", "信息", "处理方式"], ["Info", "完整性", "通过", "无需处理"])
    if constraint:
        append_sheet(book, "约束违反检查", ["约束编号", "约束含义", "违反量", "容差", "是否满足"], ["C1", "容量", 0.0, 1e-8, "是"])
    if out_of_sample:
        append_sheet(book, "外样本验证", ["划分或窗口", "指标", "数值"], ["测试集", "MAE", 0.1])
    book.save(path)


def write_robustness(path: Path):
    book = Workbook()
    append_sheet(book, "参数敏感性", ["参数", "基准值", "扰动值", "目标指标"], ["a", 1.0, 1.1, 2.0])
    book.save(path)


def capabilities(**overrides):
    values = {
        "has_explicit_constraints": False,
        "requires_feasibility_check": False,
        "requires_equilibrium_residual": False,
        "requires_conservation_residual": False,
        "requires_discretization_check": False,
        "requires_convergence_diagnostic": False,
        "requires_out_of_sample_validation": False,
        "requires_uncertainty_quantification": False,
        "requires_leakage_check": False,
        "requires_calibration_check": False,
        "requires_identifiability_check": False,
    }
    values.update(overrides)
    return values


def write_state(root: Path, status="designed", caps=None, phase="model_design", validated=None):
    state_dir = root / "state"
    state_dir.mkdir(exist_ok=True)
    payload = {
        "project": {"current_phase": phase},
        "subproblems": {
            "Q1": {
                "status": status,
                "classification": {"objective": "optimization", "structures": []},
                "capabilities": caps or capabilities(),
                "validation_status": "passed" if status == "validated" else "pending",
                "result_summary_status": "current" if status in {"solved", "validated"} else "pending",
                "result_summary_anchor": "### Q1" if status in {"solved", "validated"} else "",
                "artifacts_stale": False,
                "evidence": [],
                "validated_artifact_hashes": validated or {},
            }
        },
        "artifacts": {"code": [], "results": [], "figures": [], "papers": []},
        "paper_framework": {"path": "模型论文框架.md", "sync_status": "current", "mode": "compact"},
    }
    (state_dir / "project_state.yaml").write_text(yaml.safe_dump(payload, allow_unicode=True), encoding="utf-8")


def setup_valid_project(root: Path, status="designed", caps=None, phase="model_design"):
    (root / "问题一求解.py").write_text("def main():\n    return 1\n", encoding="utf-8")
    result = root / "结果数据表" / "问题一"
    result.mkdir(parents=True)
    write_solution(result / "问题一求解结果.xlsx", constraint=bool((caps or {}).get("has_explicit_constraints")), out_of_sample=bool((caps or {}).get("requires_out_of_sample_validation")))
    write_robustness(result / "问题一敏感性与鲁棒性结果.xlsx")
    (root / "模型论文框架.md").write_text(
        "- 最近同步：`x`\n- 最近同步时间：`x`\n- 当前状态：`current`\n### Q1\n",
        encoding="utf-8",
    )
    write_state(root, status=status, caps=caps, phase=phase)
    return result


class TestSyncProject(unittest.TestCase):
    def test_discovers_artifacts_writes_report_and_final_framework_hash(self):
        syncer = load_syncer()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = setup_valid_project(root)
            (result / "q1_plot.m").write_text('title(gca, "结果");', encoding="utf-8")
            report = syncer.synchronize(root, write=True)
            self.assertIn("Q1", report["questions"])
            self.assertTrue((root / "sync_report.yaml").is_file())
            updated = yaml.safe_load((root / "state" / "project_state.yaml").read_text(encoding="utf-8"))
            actual_hash = syncer.sha256_file(root / "模型论文框架.md")
            self.assertEqual(updated["paper_framework"]["sha256"], actual_hash)
            self.assertEqual(report["framework_hash"], actual_hash)

    def test_designed_project_does_not_require_workbooks(self):
        syncer = load_syncer()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "问题一求解.py").write_text("VALUE = 1\n", encoding="utf-8")
            write_state(root, status="designed", phase="model_design")
            report = syncer.synchronize(root, write=False)
            self.assertFalse(any("缺少标准" in issue for issue in report["issues"]))

    def test_solved_project_requires_both_workbooks(self):
        syncer = load_syncer()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "问题一求解.py").write_text("VALUE = 1\n", encoding="utf-8")
            write_state(root, status="solved", phase="solve_validate")
            report = syncer.synchronize(root, write=False)
            self.assertTrue(any("缺少标准求解结果工作簿" in issue for issue in report["issues"]))
            self.assertTrue(any("缺少标准敏感性与鲁棒性工作簿" in issue for issue in report["issues"]))

    def test_capability_required_sheet_is_enforced(self):
        syncer = load_syncer()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            caps = capabilities(requires_out_of_sample_validation=True)
            result = setup_valid_project(root, status="solved", caps=caps, phase="solve_validate")
            write_solution(result / "问题一求解结果.xlsx", out_of_sample=False)
            report = syncer.synchronize(root, write=False)
            self.assertTrue(any("requires_out_of_sample_validation" in issue for issue in report["issues"]))

    def test_workbook_hash_change_propagates_stale(self):
        syncer = load_syncer()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = setup_valid_project(root, status="validated", phase="solve_validate")
            initial = syncer.synchronize(root, write=False)
            current = initial["questions"]["Q1"]["artifact_hashes"]
            state_path = root / "state" / "project_state.yaml"
            state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            state["subproblems"]["Q1"]["validated_artifact_hashes"] = current
            state_path.write_text(yaml.safe_dump(state, allow_unicode=True), encoding="utf-8")
            book_path = result / "问题一求解结果.xlsx"
            book = Workbook()
            append_sheet(book, "核心指标", ["指标", "数值"], ["目标值", 2.0])
            append_sheet(book, "数据审计", ["等级", "检查项", "信息", "处理方式"], ["Info", "完整性", "通过", "无需处理"])
            book.save(book_path)
            report = syncer.synchronize(root, write=True)
            updated = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            self.assertEqual(report["stale_questions"], ["Q1"])
            self.assertIn("solution_workbook", updated["subproblems"]["Q1"]["stale_layers"])
            self.assertEqual(updated["subproblems"]["Q1"]["validation_status"], "pending")

    def test_figure_scope_checks_declared_export(self):
        syncer = load_syncer()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = setup_valid_project(root, status="solved", phase="figure_evidence")
            (result / "q1_plot.m").write_text(
                'title(gca, "结果"); exportgraphics(gca, "图表/missing.png");',
                encoding="utf-8",
            )
            report = syncer.synchronize(root, write=False, delivery_scope="figures")
            self.assertTrue(any("声明导出的图不存在" in issue for issue in report["issues"]))


if __name__ == "__main__":
    unittest.main()
