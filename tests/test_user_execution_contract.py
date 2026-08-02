from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

import openpyxl
import yaml

ROOT = Path(__file__).resolve().parents[1]
FALSE_FLAGS = (
    "allow_reduced_data", "allow_coarser_grid", "allow_shorter_horizon",
    "allow_fewer_repetitions", "allow_relaxed_tolerance",
    "allow_silent_solver_fallback",
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


CODE = load_module("validate_code_delivery", ROOT / "scripts" / "validate_code_delivery.py")
RECEIPT = load_module("validate_user_execution", ROOT / "scripts" / "validate_user_execution.py")


class UserExecutionContractTests(unittest.TestCase):
    def make_project(self, root: Path) -> tuple[Path, Path]:
        (root / "state").mkdir()
        code = root / "问题一求解.py"
        code.write_text(
            'def main():\n    return 0\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n',
            encoding="utf-8",
        )
        digest = hashlib.sha256(code.read_bytes()).hexdigest()
        config = root / "问题一完整运行配置.yaml"
        payload = {
            "execution_owner": "user",
            "execution_profile": "full_fidelity",
            "stage": "primary",
            "problem_name": "问题一",
            "code_path": code.name,
            "code_sha256": digest,
            "data_paths": ["data.csv"],
            "data_sha256": "a" * 64,
            "solver": "test",
            "solver_version": "1",
            "random_seed": 2026,
            "tolerance": 1e-8,
            "iteration_or_time_limit": "full",
            "repetitions_or_scenarios": 100,
            "grid_or_time_range": "full",
            "expected_workbook": "结果数据表/问题一/问题一求解结果.xlsx",
            **{flag: False for flag in FALSE_FLAGS},
        }
        config.write_text(
            yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        (root / "问题一本地运行说明.md").write_text("full run", encoding="utf-8")
        state = {
            "project": {
                "competition": "test",
                "problem": "A",
                "current_phase": "solve_validate",
            },
            "requirements": {"total": 0, "completed": [], "pending": []},
            "decisions": {},
            "subproblems": {
                "Q1": {
                    "status": "designed",
                    "selected_model": "m",
                    "capabilities": {},
                    "result_quality_status": "pending",
                    "result_analysis_status": "pending",
                    "framework_section": "Q1",
                    "result_summary_status": "pending",
                }
            },
            "variables": {"locked": [], "source": {}},
            "paper_framework": {
                "path": "模型论文框架.md",
                "version": "1",
                "sync_status": "stale",
                "last_sync_scope": "design",
                "proposition_limit": 4,
                "proposition_count": 0,
                "proposition_status": "not_assessed",
                "propositions": [],
            },
            "artifacts": {"code": [], "results": [], "figures": [], "papers": []},
            "risks": [],
            "next_gate": {"module": "solve_validate", "condition": "code"},
        }
        (root / "state" / "project_state.yaml").write_text(
            yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        return config, code

    def make_primary_workbook(self, root: Path, code: Path, data_hash: str = "a" * 64) -> Path:
        result_dir = root / "结果数据表" / "问题一"
        result_dir.mkdir(parents=True)
        workbook = result_dir / "问题一求解结果.xlsx"
        book = openpyxl.Workbook()
        sheet = book.active
        sheet.title = "运行配置"
        sheet.append(["项目", "值"])
        items = {
            "execution_owner": "user",
            "execution_profile": "full_fidelity",
            "stage": "primary",
            "problem_name": "问题一",
            "code_sha256": hashlib.sha256(code.read_bytes()).hexdigest(),
            "data_sha256": data_hash,
            "solver": "test",
            "solver_version": "1",
            "tolerance": 1e-8,
            "iteration_or_time_limit": "full",
            "actual_stop_reason": "optimal",
            "random_seed": 2026,
            "repetitions_or_scenarios": 100,
            "grid_or_time_range": "full",
            "fallback_used": False,
            "platform": "test",
            **{flag: False for flag in FALSE_FLAGS},
        }
        for key, value in items.items():
            sheet.append([key, value])
        quality = book.create_sheet("主结果质量门")
        quality.append(["检查项", "是否通过", "证据"])
        quality.append(["完整运行", True, "ok"])
        book.save(workbook)
        return workbook

    def test_code_delivery_does_not_mark_solved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config, _ = self.make_project(root)
            issues, payload, path = CODE.validate_config(root, config)
            self.assertEqual(issues, [])
            CODE.update_state(root, payload, path)
            state = yaml.safe_load(
                (root / "state" / "project_state.yaml").read_text(encoding="utf-8")
            )
            self.assertEqual(state["subproblems"]["Q1"]["status"], "designed")
            self.assertEqual(
                state["subproblems"]["Q1"]["primary_execution_status"],
                "awaiting_user_execution",
            )
            self.assertEqual(state["subproblems"]["Q1"]["data_hash"], "a" * 64)

    def test_reduced_flag_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config, _ = self.make_project(root)
            payload = yaml.safe_load(config.read_text(encoding="utf-8"))
            payload["allow_reduced_data"] = True
            config.write_text(
                yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            issues, _, _ = CODE.validate_config(root, config)
            self.assertTrue(any("allow_reduced_data" in item for item in issues))

    def test_primary_workbook_acceptance_marks_solved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config, code = self.make_project(root)
            _, payload, path = CODE.validate_config(root, config)
            CODE.update_state(root, payload, path)
            workbook = self.make_primary_workbook(root, code)
            state = yaml.safe_load(
                (root / "state" / "project_state.yaml").read_text(encoding="utf-8")
            )
            issues = RECEIPT.validate_one(root, workbook, state, True)
            self.assertEqual(issues, [])
            self.assertEqual(state["subproblems"]["Q1"]["status"], "solved")
            self.assertEqual(
                state["subproblems"]["Q1"]["primary_execution_status"], "accepted"
            )

    def test_data_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config, code = self.make_project(root)
            _, payload, path = CODE.validate_config(root, config)
            CODE.update_state(root, payload, path)
            workbook = self.make_primary_workbook(root, code, data_hash="b" * 64)
            state = yaml.safe_load(
                (root / "state" / "project_state.yaml").read_text(encoding="utf-8")
            )
            issues = RECEIPT.validate_one(root, workbook, state, True)
            self.assertTrue(any("data_sha256" in item for item in issues))
            self.assertEqual(
                state["subproblems"]["Q1"]["primary_execution_status"], "rejected"
            )


if __name__ == "__main__":
    unittest.main()
