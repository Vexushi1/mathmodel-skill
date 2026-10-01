from __future__ import annotations

import hashlib
import io
import importlib.util
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

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
ARTIFACTS = load_module("user_execution_artifacts", ROOT / "scripts" / "artifact_fingerprint.py")


class UserExecutionContractTests(unittest.TestCase):
    def make_project(self, root: Path) -> Path:
        (root / "state").mkdir()
        data = root / "data.csv"
        data.write_text("value\n1\n", encoding="utf-8")
        self.data_hash = ARTIFACTS.combined_hash([data], root)
        folder = root / "问题一求解"
        folder.mkdir()
        code = folder / "问题一求解.py"
        config = self.config("primary", "问题一求解结果.xlsx")
        self.write_code(code, config)
        state = {
            "project": {"competition": "test", "problem": "A", "current_phase": "solve_validate", "version": "7.2.1"},
            "execution": {"solver_backend": "python",
                          "solver_backend_selection_reason": "全题维护微例及用户执行环境已审视"},
            "data": {"active_source_mode": "raw"},
            "preprocessing": {
                "decision": "not_needed", "level": "none", "status": "not_applicable",
                "evidence": ["fixture raw data is directly usable"], "operations": [],
                "forbidden_operations": [], "downstream_data_source": "raw",
                "quality_status": "not_applicable",
            },
            "requirements": {"total": 0, "completed": [], "pending": []}, "decisions": {},
            "subproblems": {"Q1": {"status": "designed", "selected_model": "m", "capabilities": {},
                "result_quality_status": "pending", "result_analysis_status": "pending",
                "framework_section": "Q1", "result_summary_status": "pending"}},
            "variables": {"locked": [], "source": {}},
            "paper_framework": {"path": "模型论文框架.md", "version": "1", "sync_status": "stale",
                "last_sync_scope": "design", "proposition_limit": 4, "proposition_count": 0,
                "proposition_status": "not_assessed", "propositions": []},
            "artifacts": {"code": [], "results": [], "figures": [], "papers": []},
            "risks": [], "next_gate": {"module": "solve_validate", "condition": "code"},
        }
        self.write_state(root, state)
        return code

    def config(self, stage: str, workbook: str) -> dict:
        config = {
            "execution_owner": "user", "execution_profile": "full_fidelity", "stage": stage,
            "problem_name": "问题一", "data_paths": ["data.csv"],
            "data_sha256": getattr(self, "data_hash", "a" * 64),
            "solver": "test", "solver_version": "1", "random_seed": 2026, "tolerance": 1e-8,
            "iteration_or_time_limit": "full", "expected_workbook": workbook,
            "solver_backend": "python", "run_receipt_protocol_version": "1.1.0",
            "code_dependencies": [],
            **{flag: False for flag in FALSE_FLAGS},
        }
        if stage == "primary":
            config["primary_quality_protocol_version"] = "1.0.0"
        elif stage == "analysis":
            config["primary_workbook_sha256"] = getattr(self, "primary_workbook_sha", "b" * 64)
        return config

    def write_code(self, path: Path, config: dict, marker: int = 0) -> None:
        path.write_text(
            "RUN_CONFIG = " + repr(config)
            + f"\n\ndef main():\n    return {marker}\n\nif __name__ == \"__main__\":\n    raise SystemExit(main())\n",
            encoding="utf-8",
        )

    def write_state(self, root: Path, state: dict) -> None:
        (root / "state" / "project_state.yaml").write_text(
            yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )

    def read_state(self, root: Path) -> dict:
        return yaml.safe_load((root / "state" / "project_state.yaml").read_text(encoding="utf-8"))

    def make_primary_workbook(self, root: Path, code: Path, data_hash: str | None = None) -> Path:
        workbook = root / "问题一求解" / "问题一求解结果.xlsx"
        book = openpyxl.Workbook()
        sheet = book.active
        sheet.title = "运行配置"
        sheet.append(["项目", "值"])
        items = self.runtime_items("primary", code, data_hash or self.data_hash)
        for key, value in items.items():
            sheet.append([key, value])
        quality = book.create_sheet("主结果质量门")
        quality.append([
            "Verification ID", "检查项", "是否通过", "证据", "判定关系",
            "阈值或容差", "实际值", "证据工作表", "阈值来源",
        ])
        quality.append([
            "PQ-Q1-01", "完整主计算", True, "基础证据", "bool_true",
            True, True, "基础数值证据", "solver_tolerance",
        ])
        evidence = book.create_sheet("基础数值证据")
        evidence.append(["检查项", "数值"])
        evidence.append(["full_fidelity", 1])
        metrics = book.create_sheet("核心指标")
        metrics.append(["指标", "数值"])
        metrics.append(["输入value汇总", 1])
        audit = book.create_sheet("数据审计")
        audit.append(["等级", "检查项", "信息", "处理方式"])
        audit.append(["Info", "data.csv/value", "单条有限输入value=1，无缺失", "保持原值"])
        book.save(workbook)
        return workbook

    def make_analysis_workbook(self, root: Path, code: Path) -> Path:
        workbook = root / "问题一求解" / "问题一结果深化分析.xlsx"
        book = openpyxl.Workbook()
        runtime = book.active
        runtime.title = "运行配置"
        runtime.append(["项目", "值"])
        for key, value in self.runtime_items("analysis", code, self.data_hash).items():
            runtime.append([key, value])
        design = book.create_sheet("分析设计")
        design.append(["风险来源", "分析问题", "方法", "指标", "通过标准"])
        design.append(["参数", "稳定性", "敏感性", "目标值", "结论保持"])
        sensitivity = book.create_sheet("参数敏感性")
        sensitivity.append(["参数", "基准值", "变化值", "结果指标"])
        sensitivity.append(["p", 1.0, 1.1, 2.0])
        summary = book.create_sheet("结论稳定性汇总")
        summary.append(["核心结论", "分析方法", "稳定范围", "是否保持"])
        summary.append(["方案A", "敏感性", "0.9--1.1", True])
        book.save(workbook)
        return workbook

    def runtime_items(self, stage: str, code: Path, data_hash: str) -> dict:
        items = {
            "execution_owner": "user", "execution_profile": "full_fidelity", "stage": stage,
            "problem_name": "问题一", "code_sha256": hashlib.sha256(code.read_bytes()).hexdigest(),
            "data_sha256": data_hash, "solver": "test", "solver_version": "1", "tolerance": 1e-8,
            "iteration_or_time_limit": "full", "actual_stop_reason": "optimal", "random_seed": 2026,
            "repetitions_or_scenarios": 100, "grid_or_time_range": "full", "fallback_used": False,
            "platform": "test", **{flag: False for flag in FALSE_FLAGS},
            "run_receipt_version": "1.1.0", "solver_backend": "python",
            "code_bundle_sha256": CODE.STAGE_CODE.stage_code_fingerprint(code.parents[1], code)["bundle_sha256"],
        }
        if stage == "primary":
            items["primary_quality_protocol_version"] = "1.0.0"
        elif stage == "analysis":
            items["primary_workbook_sha256"] = self.primary_workbook_sha
        return items

    def accept_primary(self, root: Path, code: Path) -> dict:
        issues, config = CODE.validate_script(root, code, "primary")
        self.assertEqual(issues, [])
        CODE.update_state(root, config, code)
        workbook = self.make_primary_workbook(root, code)
        self.primary_workbook_sha = hashlib.sha256(workbook.read_bytes()).hexdigest()
        state = self.read_state(root)
        issues = RECEIPT.validate_one(root, workbook, state, True)
        self.assertEqual(issues, [])
        self.write_state(root, state)
        return state

    def make_analysis_code(self, root: Path, marker: int = 0) -> Path:
        code = root / "问题一求解" / "问题一结果深化分析.py"
        self.write_code(code, self.config("analysis", "问题一结果深化分析.xlsx"), marker)
        return code

    def activate_analysis(self, root: Path) -> None:
        state = self.read_state(root)
        state["subproblems"]["Q1"].update(
            result_analysis_requirement_reason="Current answer has a material parameter risk",
            analysis_methods=["参数敏感性"],
        )
        self.write_state(root, state)

    def test_code_delivery_does_not_mark_solved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            code = self.make_project(root)
            issues, config = CODE.validate_script(root, code, "primary")
            self.assertEqual(issues, [])
            CODE.update_state(root, config, code)
            state = self.read_state(root)
            self.assertEqual(state["subproblems"]["Q1"]["status"], "designed")
            self.assertEqual(state["subproblems"]["Q1"]["primary_execution_status"], "awaiting_user_execution")
            self.assertEqual(state["subproblems"]["Q1"]["data_hash"], self.data_hash)

    def test_reduced_flag_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            code = self.make_project(root)
            text = code.read_text(encoding="utf-8").replace("'allow_reduced_data': False", "'allow_reduced_data': True")
            code.write_text(text, encoding="utf-8")
            issues, _ = CODE.validate_script(root, code, "primary")
            self.assertTrue(any("allow_reduced_data" in item for item in issues))

    def test_primary_protocol_marker_is_required_only_for_primary(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            primary = self.make_project(root)
            text = primary.read_text(encoding="utf-8").replace(
                ", 'primary_quality_protocol_version': '1.0.0'", ""
            )
            primary.write_text(text, encoding="utf-8")
            issues, _ = CODE.validate_script(root, primary, "primary")
            self.assertTrue(any("primary_quality_protocol_version" in item for item in issues))
            analysis = self.make_analysis_code(root)
            analysis_issues, _ = CODE.validate_script(root, analysis, "analysis")
            self.assertFalse(any("primary_quality_protocol_version" in item for item in analysis_issues))

    def test_primary_workbook_acceptance_marks_solved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            code = self.make_project(root)
            state = self.accept_primary(root, code)
            self.assertEqual(state["subproblems"]["Q1"]["status"], "solved")
            self.assertEqual(state["subproblems"]["Q1"]["result_quality_status"], "passed")

    def test_primary_schema_failures_never_acquire_validated_workbook_hash(self):
        for missing in ("核心指标", "数据审计", None):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                code = self.make_project(root)
                _, config = CODE.validate_script(root, code, "primary")
                CODE.update_state(root, config, code)
                workbook = self.make_primary_workbook(root, code)
                book = openpyxl.load_workbook(workbook)
                if missing:
                    del book[missing]
                else:
                    quality = book["主结果质量门"]
                    quality.delete_rows(2)
                    quality.append(["PQ-Q1-01", "均衡", True, "rows", "<=", 1e-6, 0,
                                    "均衡残差", "locked_model_tolerance"])
                    evidence = book.create_sheet("均衡残差")
                    evidence.append(["主体或均衡", "残差", "容差", "是否满足", "残差 "])
                    evidence.append(["单主体", 0.01, 1e-6, True, 0])
                book.save(workbook)
                book.close()
                state = self.read_state(root)
                if missing is None:
                    state["subproblems"]["Q1"]["capabilities"] = {"requires_equilibrium_residual": True}
                issues = RECEIPT.validate_one(root, workbook, state, True)
                self.assertTrue(any("结构Schema" in issue for issue in issues), issues)
                entry = state["subproblems"]["Q1"]
                self.assertEqual(entry["primary_execution_status"], "rejected")
                self.assertEqual(entry["result_quality_status"], "failed")
                self.assertNotIn("solution_workbook", entry.get("validated_artifact_hashes", {}))

    def test_analysis_structure_failure_does_not_become_accepted_or_core_rejection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            primary = self.make_project(root)
            self.accept_primary(root, primary)
            self.activate_analysis(root)
            analysis = self.make_analysis_code(root)
            _, config = CODE.validate_script(root, analysis, "analysis")
            CODE.update_state(root, config, analysis)
            workbook = self.make_analysis_workbook(root, analysis)
            book = openpyxl.load_workbook(workbook)
            book["分析设计"].cell(1, 1, "旧风险字段")
            book.save(workbook)
            book.close()
            state = self.read_state(root)
            primary_hash = state["subproblems"]["Q1"]["validated_artifact_hashes"]["solution_workbook"]
            issues = RECEIPT.validate_one(root, workbook, state, True)
            entry = state["subproblems"]["Q1"]
            self.assertTrue(any("结构Schema" in issue for issue in issues), issues)
            self.assertEqual(entry["analysis_execution_status"], "rejected")
            self.assertEqual(entry["result_analysis_status"], "failed")
            self.assertNotIn("result_analysis_workbook", entry["validated_artifact_hashes"])
            self.assertEqual(entry["validated_artifact_hashes"]["solution_workbook"], primary_hash)
            self.assertEqual(entry["primary_execution_status"], "accepted")

    def test_malformed_schema_context_returns_issues_without_qualification(self):
        for field in ("classification", "problem_types", "capabilities"):
            for invalid in ([], ["unexpected"], "unexpected"):
                with self.subTest(field=field, invalid=invalid), tempfile.TemporaryDirectory() as temp:
                    root = Path(temp)
                    code = self.make_project(root)
                    _, config = CODE.validate_script(root, code, "primary")
                    CODE.update_state(root, config, code)
                    workbook = self.make_primary_workbook(root, code)
                    state = self.read_state(root)
                    entry = state["subproblems"]["Q1"]
                    entry[field] = invalid
                    issues = RECEIPT.validate_one(root, workbook, state, True)
                    self.assertTrue(any(field in issue and "Schema" in issue for issue in issues), issues)
                    self.assertNotEqual(entry["primary_execution_status"], "accepted")
                    self.assertNotIn("solution_workbook", entry.get("validated_artifact_hashes", {}))

    def test_active_comparison_retains_budget_before_unbounded_candidate_read(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            code = self.make_project(root)
            _, config = CODE.validate_script(root, code, "primary")
            CODE.update_state(root, config, code)
            workbook = self.make_primary_workbook(root, code)
            with workbook.open("r+b") as handle:
                handle.truncate(32 * 1024 * 1024 + 1)
            state = self.read_state(root)
            state["subproblems"]["Q1"]["analysis_comparison"] = {"protocol_version": "1.0.0"}
            with mock.patch.object(Path, "read_bytes", side_effect=AssertionError("unbounded candidate read")):
                with self.assertRaisesRegex(ValueError, "byte budget"):
                    RECEIPT.validate_one(root, workbook, state, True)
            self.assertNotEqual(state["subproblems"]["Q1"]["primary_execution_status"], "accepted")

    def test_primary_recomputed_threshold_is_required_even_with_close_reported_actual(self):
        for threshold, reported, expected in ((1e-12, 9e-13, False), (1e-9, 1.5e-12, True)):
            with self.subTest(threshold=threshold), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                code = self.make_project(root)
                _, config = CODE.validate_script(root, code, "primary")
                CODE.update_state(root, config, code)
                workbook = self.make_primary_workbook(root, code)
                book = openpyxl.load_workbook(workbook)
                book["主结果质量门"].delete_rows(2)
                book["主结果质量门"].append([
                    "PQ-Q1-01", "均衡", True, "重算残差", "<=", threshold,
                    reported, "均衡残差", "locked_model_tolerance",
                ])
                evidence = book.create_sheet("均衡残差")
                evidence.append(["主体或均衡", "残差", "容差", "是否满足"])
                evidence.append(["单主体均衡", 1.5e-12, 1e-9, True])
                book.save(workbook)
                book.close()
                state = self.read_state(root)
                state["subproblems"]["Q1"]["capabilities"] = {"requires_equilibrium_residual": True}
                issues = RECEIPT.validate_one(root, workbook, state, True)
                entry = state["subproblems"]["Q1"]
                self.assertEqual(not issues, expected, issues)
                self.assertEqual(entry["primary_execution_status"], "accepted" if expected else "rejected")
                self.assertEqual("solution_workbook" in entry.get("validated_artifact_hashes", {}), expected)

    def test_workbook_changed_after_capture_cannot_acquire_qualification(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            code = self.make_project(root)
            _, config = CODE.validate_script(root, code, "primary")
            CODE.update_state(root, config, code)
            workbook = self.make_primary_workbook(root, code)
            state = self.read_state(root)
            original_quality = RECEIPT.quality_passed

            def change_after_capture(raw):
                self.assertIsInstance(raw, bytes)
                result = original_quality(raw)
                workbook.write_bytes(workbook.read_bytes() + b"changed-after-capture")
                return result

            with mock.patch.object(RECEIPT, "quality_passed", side_effect=change_after_capture):
                with self.assertRaises((RuntimeError, ValueError)):
                    RECEIPT.validate_one(root, workbook, state, True)
            entry = state["subproblems"]["Q1"]
            self.assertNotEqual(entry["primary_execution_status"], "accepted")
            self.assertNotIn("solution_workbook", entry.get("validated_artifact_hashes", {}))

    def test_no_workbooks_reports_failure_without_empty_receipt_transaction(self):
        for strict in (False, True):
            with self.subTest(strict=strict), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                self.make_project(root)
                before = (root / "state/project_state.yaml").read_bytes()
                args = ["validate_user_execution.py", str(root), "--write", *( ["--strict"] if strict else [])]
                output = io.StringIO()
                with mock.patch("sys.argv", args), redirect_stdout(output), mock.patch.object(
                    RECEIPT.PROJECT_TX, "commit_project_state") as commit:
                    code = RECEIPT.main()
                self.assertEqual(code, 1 if strict else 0)
                self.assertIn("status: failed", output.getvalue())
                self.assertIn("no_workbooks: true", output.getvalue())
                self.assertIn("未发现待验收工作簿", output.getvalue())
                commit.assert_not_called()
                self.assertEqual((root / "state/project_state.yaml").read_bytes(), before)

    def test_primary_receipt_cli_commits_captured_state_and_workbook(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            code = self.make_project(root)
            _, config = CODE.validate_script(root, code, "primary")
            CODE.update_state(root, config, code)
            workbook = self.make_primary_workbook(root, code)
            generation = RECEIPT.PROJECT_TX.state_generation(self.read_state(root))
            output = io.StringIO()
            with mock.patch("sys.argv", ["validate_user_execution.py", str(root), "--write", "--strict"]), redirect_stdout(output):
                self.assertEqual(RECEIPT.main(), 0)
            report = yaml.safe_load(output.getvalue())
            self.assertEqual(report["status"], "passed")
            self.assertFalse(report["no_workbooks"])
            state = self.read_state(root)
            self.assertEqual(RECEIPT.PROJECT_TX.state_generation(state), generation + 1)
            self.assertEqual(state["subproblems"]["Q1"]["validated_artifact_hashes"]["solution_workbook"],
                             hashlib.sha256(workbook.read_bytes()).hexdigest())

    def test_data_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            code = self.make_project(root)
            _, config = CODE.validate_script(root, code, "primary")
            CODE.update_state(root, config, code)
            workbook = self.make_primary_workbook(root, code, data_hash="b" * 64)
            state = self.read_state(root)
            issues = RECEIPT.validate_one(root, workbook, state, True)
            self.assertTrue(any("data_sha256" in item for item in issues))

    def test_analysis_filename_and_stage_must_match(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_project(root)
            code = root / "问题一求解" / "问题一结果深化分析.py"
            self.write_code(code, self.config("primary", "问题一求解结果.xlsx"))
            issues, _ = CODE.validate_script(root, code)
            self.assertTrue(any("文件名对应analysis阶段" in item for item in issues))

    def test_analysis_requires_accepted_primary(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_project(root)
            analysis = self.make_analysis_code(root)
            issues, config = CODE.validate_script(root, analysis, "analysis")
            self.assertTrue(any("主工作簿未accepted" in item for item in issues), issues)
            with self.assertRaisesRegex(ValueError, "主工作簿未accepted"):
                CODE.update_state(root, config, analysis)

    def test_analysis_delivery_keeps_primary_path_and_hash_frozen(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            primary = self.make_project(root)
            state = self.accept_primary(root, primary)
            self.activate_analysis(root)
            primary_hash = state["subproblems"]["Q1"]["primary_code_sha256"]
            analysis = self.make_analysis_code(root)
            issues, config = CODE.validate_script(root, analysis, "analysis")
            self.assertEqual(issues, [])
            CODE.update_state(root, config, analysis)
            state = self.read_state(root)
            entry = state["subproblems"]["Q1"]
            self.assertEqual(entry["code"], "问题一求解/问题一求解.py")
            self.assertEqual(entry["result_analysis_code"], "问题一求解/问题一结果深化分析.py")
            self.assertEqual(entry["primary_code_sha256"], primary_hash)
            self.assertEqual(entry["analysis_code_sha256"], hashlib.sha256(analysis.read_bytes()).hexdigest())

    def test_analysis_change_does_not_invalidate_primary_quality(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            primary = self.make_project(root)
            self.accept_primary(root, primary)
            self.activate_analysis(root)
            analysis = self.make_analysis_code(root)
            _, config = CODE.validate_script(root, analysis, "analysis")
            CODE.update_state(root, config, analysis)
            state = self.read_state(root)
            state["subproblems"]["Q1"]["result_quality_status"] = "passed"
            self.write_state(root, state)
            self.write_code(analysis, self.config("analysis", "问题一结果深化分析.xlsx"), marker=1)
            _, config = CODE.validate_script(root, analysis, "analysis")
            CODE.update_state(root, config, analysis)
            entry = self.read_state(root)["subproblems"]["Q1"]
            self.assertEqual(entry["result_quality_status"], "passed")
            self.assertEqual(entry["result_analysis_status"], "pending")
            self.assertIn("result_analysis_workbook", entry["stale_layers"])
            self.assertNotIn("solution_workbook", entry["stale_layers"])

    def test_failed_analysis_conclusion_uses_core_answer_rejection_return(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            primary = self.make_project(root)
            self.accept_primary(root, primary)
            self.activate_analysis(root)
            analysis = self.make_analysis_code(root)
            issues, config = CODE.validate_script(root, analysis, "analysis")
            self.assertEqual(issues, [])
            CODE.update_state(root, config, analysis)
            workbook = self.make_analysis_workbook(root, analysis)
            book = openpyxl.load_workbook(workbook)
            book["结论稳定性汇总"]["D2"] = False
            book.save(workbook)
            book.close()
            state = self.read_state(root)
            state["project"]["current_phase"] = "result_analysis"
            state["next_gate"] = {"module": "result_analysis", "condition": "review"}
            state["paper_framework"]["claim_consumption_policy"] = {
                "protocol_version": "1.4.0",
                "mode": "enforce_latex_text_and_figure_chain",
            }
            state["subproblems"]["Q1"].update(
                model_challenge_status="passed", human_model_approval_status="approved",
            )
            issues = RECEIPT.validate_one(root, workbook, state, True)
            self.assertIn("存在核心结论未保持", issues)
            entry = state["subproblems"]["Q1"]
            self.assertEqual(state["project"]["current_phase"], "solve_validate")
            self.assertEqual(state["next_gate"]["module"], "solve_validate")
            self.assertEqual(entry["status"], "designed")
            self.assertEqual(entry["result_analysis_status"], "redo_required")
            self.assertEqual(entry["analysis_execution_status"], "redo_required")
            self.assertIn("solution_workbook", entry["stale_layers"])
            self.assertEqual(entry["human_model_approval_status"], "approved")

    def test_failed_analysis_conclusion_preserves_legacy_return_behavior(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            primary = self.make_project(root)
            self.accept_primary(root, primary)
            self.activate_analysis(root)
            analysis = self.make_analysis_code(root)
            issues, config = CODE.validate_script(root, analysis, "analysis")
            self.assertEqual(issues, [])
            CODE.update_state(root, config, analysis)
            workbook = self.make_analysis_workbook(root, analysis)
            book = openpyxl.load_workbook(workbook)
            book["结论稳定性汇总"]["D2"] = False
            book.save(workbook)
            book.close()
            state = self.read_state(root)
            state["project"]["current_phase"] = "result_analysis"
            state["next_gate"] = {"module": "result_analysis", "condition": "legacy review"}
            state["paper_framework"]["claim_consumption_policy"] = {
                "protocol_version": "1.3.0",
                "mode": "enforce_latex_text_and_figure_chain",
            }
            prior_status = state["subproblems"]["Q1"]["status"]
            issues = RECEIPT.validate_one(root, workbook, state, True)
            self.assertIn("存在核心结论未保持", issues)
            entry = state["subproblems"]["Q1"]
            self.assertEqual(state["project"]["current_phase"], "solve_validate")
            self.assertEqual(state["next_gate"]["module"], "result_analysis")
            self.assertEqual(entry["status"], prior_status)
            self.assertEqual(entry["result_analysis_status"], "redo_required")
            self.assertEqual(entry["analysis_execution_status"], "redo_required")
            self.assertEqual(
                entry["stale_layers"],
                ["result_analysis_workbook", "matlab_script", "figure_bundle", "framework"],
            )
            self.assertNotIn("solution_workbook", entry["stale_layers"])

    def test_accepted_primary_is_frozen_outside_solve_validate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            primary = self.make_project(root)
            self.accept_primary(root, primary)
            state = self.read_state(root)
            state["project"]["current_phase"] = "result_analysis"
            self.write_state(root, state)
            self.write_code(primary, self.config("primary", "问题一求解结果.xlsx"), marker=2)
            issues, config = CODE.validate_script(root, primary, "primary")
            self.assertEqual(issues, [])
            with self.assertRaisesRegex(ValueError, "已accepted并冻结"):
                CODE.update_state(root, config, primary)


if __name__ == "__main__":
    unittest.main()
