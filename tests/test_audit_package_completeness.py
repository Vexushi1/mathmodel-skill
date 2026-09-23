from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
import warnings
from unittest.mock import patch
import zipfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import artifact_fingerprint
import stage_code


def load_script(name):
    spec = importlib.util.spec_from_file_location("audit_" + name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


PACK = load_script("hsk_pack_submission")
VALIDATOR = load_script("validate_submission_package")


def save_state(root, state):
    (root / "state").mkdir(exist_ok=True)
    (root / "state/project_state.yaml").write_text(yaml.safe_dump(state, allow_unicode=True), encoding="utf-8")


def complete_project(root, *, analysis="not_required", preprocessing=False, questions=2,
                     preprocessing_workbook="数据预处理/数据预处理结果.xlsx"):
    state = {"project": {"competition": "DEMO"}, "subproblems": {},
             "artifacts": {"compiled_pdf": "final_latex/main.pdf", "latex_source": "final_latex/main.tex"},
             "execution": {"solver_backend": "python", "solver_backend_selection_reason":
                           "Synthetic whole-project packaging requirements reviewed"},
             "preprocessing": {"decision": "project_level" if preprocessing else "not_needed"}}
    names = ["模型论文框架.md", "final_latex/main.pdf", "final_latex/main.tex", "附件/附件1.xlsx"]
    for index, chinese in enumerate(("一", "二")[:questions], 1):
        directory = f"问题{chinese}求解"
        entry = {"code": f"{directory}/问题{chinese}求解.py",
                 "solution_workbook": f"{directory}/问题{chinese}求解结果.xlsx",
                 "matlab_script": f"{directory}/q{index}_plot.m",
                 "result_analysis_status": analysis}
        names.extend(entry[field] for field in ("code", "solution_workbook", "matlab_script"))
        if analysis == "not_required":
            entry["result_analysis_requirement_reason"] = "当前结论不需要额外世界证据"
        elif analysis == "passed":
            entry["result_analysis_code"] = f"{directory}/问题{chinese}结果深化分析.py"
            entry["result_analysis_workbook"] = f"{directory}/问题{chinese}结果深化分析.xlsx"
            names.extend([entry["result_analysis_code"], entry["result_analysis_workbook"]])
        state["subproblems"][f"Q{index}"] = entry
    if preprocessing:
        names.extend(["数据预处理/数据预处理.py", preprocessing_workbook, "数据预处理/data_process.m"])
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(("synthetic packaging fixture: " + name).encode())
    raw = root / "附件/附件1.xlsx"
    data_path = preprocessing_workbook if preprocessing else "附件/附件1.xlsx"
    data_hash = (hashlib.sha256((root / data_path).read_bytes()).hexdigest() if preprocessing
                 else artifact_fingerprint.combined_hash([raw], root))
    if preprocessing:
        state["preprocessing"].update({
            "status": "accepted", "quality_status": "passed", "workbook": preprocessing_workbook,
            "workbook_sha256": data_hash,
        })
    for index, chinese in enumerate(("一", "二")[:questions], 1):
        entry = state["subproblems"][f"Q{index}"]
        problem = f"问题{chinese}"
        workbook = root / entry["solution_workbook"]
        workbook_hash = hashlib.sha256(workbook.read_bytes()).hexdigest()
        entry.update(primary_execution_status="accepted", result_quality_status="passed",
                     data_hash=data_hash, validated_data_hash=data_hash)
        current = {"data": data_hash, "solution_workbook": workbook_hash}
        for stage, field, workbook_field in (("primary", "code", "solution_workbook"),
                                              ("analysis", "result_analysis_code", "result_analysis_workbook")):
            if field not in entry:
                continue
            code = root / entry[field]
            config = {"stage": stage, "problem_name": problem, "solver_backend": "python",
                      "run_receipt_protocol_version": "1.1.0", "data_paths": [data_path],
                      "data_sha256": data_hash,
                      "data_identity_mode": "preprocessing_workbook" if preprocessing else "combined",
                      "code_dependencies": [], "expected_workbook": entry[workbook_field]}
            if stage == "analysis":
                config["primary_workbook_sha256"] = workbook_hash
            code.write_text(f"RUN_CONFIG = {config!r}\n\ndef main():\n    return 0\n", encoding="utf-8")
            identity = stage_code.stage_code_fingerprint(root, code)
            entry[f"{stage}_code_sha256"] = identity["entry_sha256"]
            entry.setdefault("solver_execution", {})[stage] = {
                "bundle_sha256": identity["bundle_sha256"],
                "validated_bundle_sha256": identity["bundle_sha256"],
            }
            current[f"{stage}_code"] = identity["entry_sha256"]
            if stage == "analysis":
                entry["analysis_execution_status"] = "accepted"
                current["result_analysis_workbook"] = hashlib.sha256(
                    (root / entry["result_analysis_workbook"]).read_bytes()).hexdigest()
        entry["artifact_hashes"] = dict(current)
        entry["validated_artifact_hashes"] = dict(current)
    save_state(root, state)
    return state


def archive(root, *, omit=(), files=None, kind="reproducibility", metadata=None):
    package = root / "submission/fixture.zip"
    package.parent.mkdir(exist_ok=True)
    files = files if files is not None else PACK.reproducibility_files(root, package)
    files = [path for path in files if path.resolve().relative_to(root.resolve()).as_posix() not in omit]
    manifest = PACK.build_manifest(root, files, kind=kind, metadata=metadata or {})
    with zipfile.ZipFile(package, "w") as bundle:
        for path in files:
            bundle.write(path, path.resolve().relative_to(root.resolve()).as_posix())
        bundle.writestr(VALIDATOR.MANIFEST_NAME, yaml.safe_dump(manifest, allow_unicode=True))
    return package


def profile(root, patterns):
    path = root / "fixture-profiles.yaml"
    path.write_text(yaml.safe_dump({"profiles": {"DEMO": {"edition_rules": {
        "verification_status": "verified", "verified_at": "2026-09-20", "source": "synthetic fixture",
        "submission_files": patterns,
    }}}}), encoding="utf-8")
    return path


def compile_fixture(root, state):
    state["artifacts"]["compile_report"] = "final_latex/compile_report.yaml"
    save_state(root, state)
    for name in ("main.fls", "main.log", "unused.fls", "unused.log", "latex_audit_report.yaml", "values.cfg"):
        (root / "final_latex" / name).write_bytes(name.encode())
    report = {"report_schema_version": "4.0.0", "main": "main.tex", "status": "passed",
              "recorder": "main.fls", "recorder_sha256": hashlib.sha256(b"main.fls").hexdigest(),
              "log": "main.log", "log_sha256": hashlib.sha256(b"main.log").hexdigest(),
              "latex_audit_report": "latex_audit_report.yaml",
              "source_files": [{"path": "main.tex"}], "actual_input_files": [{"path": "values.cfg"}]}
    path = root / state["artifacts"]["compile_report"]
    path.write_text(yaml.safe_dump(report), encoding="utf-8")
    return path, report


class PackageCompletenessTests(unittest.TestCase):
    def test_two_question_required_analysis_package_rejects_omitted_question_and_stage(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = complete_project(root, analysis="passed")
            good = archive(root)
            self.assertEqual(VALIDATOR.validate_package(root, good)["status"], "passed")
            omitted = [value for key, entry in state["subproblems"].items() for field, value in entry.items()
                       if field in {"code", "solution_workbook", "matlab_script", "result_analysis_code", "result_analysis_workbook"}
                       and (key == "Q2" or field.startswith("result_analysis"))]
            report = VALIDATOR.validate_package(root, archive(root, omit=omitted))
            self.assertEqual(report["status"], "failed")
            for name in omitted:
                self.assertTrue(any(name in issue for issue in report["issues"]), report)

    def test_each_question_and_preprocessing_required_file_is_checked_independently(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = complete_project(root, analysis="passed", preprocessing=True)
            required = [state["subproblems"]["Q2"][field] for field in (
                "code", "solution_workbook", "matlab_script", "result_analysis_code", "result_analysis_workbook",
            )]
            required += ["数据预处理/" + name for name in ("数据预处理.py", "数据预处理结果.xlsx", "data_process.m")]
            for name in required:
                with self.subTest(name=name):
                    report = VALIDATOR.validate_package(root, archive(root, omit=[name]))
                    self.assertEqual(report["status"], "failed")
                    self.assertTrue(any(name in issue for issue in report["issues"]), report)

    def test_not_required_does_not_demand_analysis_and_nested_attachment_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            complete_project(root)
            package = archive(root)
            report = VALIDATOR.validate_package(root, package)
            self.assertEqual(report["status"], "passed", report)
            with zipfile.ZipFile(package) as bundle:
                self.assertIn("附件/附件1.xlsx", bundle.namelist())
                self.assertFalse(any("结果深化分析" in name for name in bundle.namelist()))

    def test_undecided_or_reasonless_analysis_and_missing_question_state_cannot_claim_complete(self):
        for disposition in ("pending", "reasonless", "missing_questions", "missing_preprocessing"):
            with self.subTest(disposition=disposition), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                state = complete_project(root)
                if disposition == "missing_questions":
                    state.pop("subproblems")
                elif disposition == "missing_preprocessing":
                    state.pop("preprocessing")
                elif disposition == "reasonless":
                    state["subproblems"]["Q1"].pop("result_analysis_requirement_reason")
                else:
                    state["subproblems"]["Q1"]["result_analysis_status"] = "pending"
                save_state(root, state)
                self.assertEqual(VALIDATOR.validate_package(root, archive(root))["status"], "failed")

    def test_explicit_current_paths_are_required_not_same_suffix_substitutes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = complete_project(root)
            current = state["subproblems"]["Q2"]["solution_workbook"]
            substitute = "已登记材料/精确主结果.xlsx"
            target = root / substitute
            target.parent.mkdir()
            target.write_bytes((root / current).read_bytes())
            result = VALIDATOR.validate_package(root, archive(root))
            self.assertEqual(result["status"], "passed", result)
            report = VALIDATOR.validate_package(root, archive(root, omit=[current]))
            self.assertTrue(any(current in issue for issue in report["issues"]), report)
            state["subproblems"]["Q2"]["solution_workbook"] = substitute
            save_state(root, state)
            report = VALIDATOR.validate_package(root, archive(root))
            self.assertTrue(any("不是当前标准工作簿" in issue for issue in report["issues"]), report)

    def test_official_missing_exact_file_is_rejected_by_generator_and_independent_validator(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            complete_project(root)
            patterns = ["final_latex/main.pdf", "required-disclosure.txt"]
            profiles = profile(root, patterns)
            metadata = {"competition_profile": "DEMO", "rule_verification_status": "verified",
                        "rule_verified_at": "2026-09-20", "rule_source": "synthetic fixture",
                        "submission_files_allowlist": patterns}
            with patch.object(PACK, "COMPETITION_PROFILES", profiles), patch.object(VALIDATOR, "COMPETITION_PROFILES", profiles):
                with self.assertRaisesRegex(SystemExit, "required-disclosure"):
                    PACK.official_files(root, "DEMO")
                package = archive(root, files=[root / "final_latex/main.pdf"], kind="official", metadata=metadata)
                report = VALIDATOR.validate_package(root, package)
                self.assertEqual(report["status"], "failed")
                self.assertTrue(any("required-disclosure" in issue for issue in report["issues"]), report)
                (root / "required-disclosure.txt").write_text("synthetic required disclosure")
                files, metadata = PACK.official_files(root, "DEMO")
                self.assertEqual(VALIDATOR.validate_package(root, archive(root, files=files, kind="official", metadata=metadata))["status"], "passed")

    def test_official_pdf_only_and_optional_wildcard_keep_their_existing_meaning(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            complete_project(root)
            profiles = profile(root, ["final_latex/main.pdf", "optional/*.txt"])
            with patch.object(PACK, "COMPETITION_PROFILES", profiles), patch.object(VALIDATOR, "COMPETITION_PROFILES", profiles):
                for add_optional in (False, True):
                    if add_optional:
                        (root / "optional").mkdir()
                        (root / "optional/item.txt").write_text("fixture")
                    files, metadata = PACK.official_files(root, "DEMO")
                    package = archive(root, files=files, kind="official", metadata=metadata)
                    self.assertEqual(VALIDATOR.validate_package(root, package)["status"], "passed")
                    self.assertEqual(len(files), 2 if add_optional else 1)

    def test_v4_bound_recorder_and_log_are_collected_and_required_but_other_auxiliaries_are_not(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = complete_project(root)
            compile_fixture(root, state)
            package = archive(root)
            with zipfile.ZipFile(package) as bundle:
                self.assertIn("final_latex/main.fls", bundle.namelist())
                self.assertIn("final_latex/main.log", bundle.namelist())
                self.assertNotIn("final_latex/unused.fls", bundle.namelist())
                self.assertNotIn("final_latex/unused.log", bundle.namelist())
            self.assertEqual(VALIDATOR.validate_package(root, package)["status"], "passed")
            for missing in ("final_latex/main.fls", "final_latex/main.log", "final_latex/compile_report.yaml",
                            "final_latex/latex_audit_report.yaml", "final_latex/values.cfg", "final_latex/main.tex",
                            "state/project_state.yaml", "模型论文框架.md"):
                result = VALIDATOR.validate_package(root, archive(root, omit=[missing]))
                self.assertTrue(any(missing in issue for issue in result["issues"]), result)

    def test_legacy_v3_does_not_synthesize_a_recorder_requirement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = complete_project(root)
            state["artifacts"]["compile_report"] = "final_latex/compile_report.yaml"
            save_state(root, state)
            (root / state["artifacts"]["compile_report"]).write_text("report_schema_version: 3.0.0\n", encoding="utf-8")
            report = VALIDATOR.validate_package(root, archive(root))
            self.assertFalse(any("fls" in issue for issue in report["issues"]), report)

    def test_contract_defaults_and_declared_inputs_figures_are_required(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = complete_project(root, analysis="passed", preprocessing=True)
            omitted = state["subproblems"]["Q2"]["result_analysis_workbook"]
            for entry in state["subproblems"].values():
                entry.pop("matlab_script")
            state["data"] = {"sources": [{"path": "附件/附件1.xlsx"}]}
            state["artifacts"]["approved_figures"] = ["figures/正式图.svg"]
            (root / "figures").mkdir()
            (root / "figures/正式图.svg").write_text("synthetic figure")
            save_state(root, state)
            result = VALIDATOR.validate_package(root, archive(root))
            self.assertEqual(result["status"], "passed", result)
            for name in (omitted, "附件/附件1.xlsx", "figures/正式图.svg"):
                report = VALIDATOR.validate_package(root, archive(root, omit=[name]))
                self.assertTrue(any(name in item for item in report["issues"]), report)

    def test_registered_preprocessing_paths_and_activated_pending_analysis_are_not_omitted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            current = "已登记预处理.xlsx"
            state = complete_project(root, analysis="passed", preprocessing=True,
                                     preprocessing_workbook=current)
            entry = state["subproblems"]["Q2"]
            entry.update(result_analysis_status="pending", result_analysis_requirement_reason="planned evidence",
                         analysis_methods=["declared method"])
            save_state(root, state)
            result = VALIDATOR.validate_package(root, archive(root))
            self.assertEqual(result["status"], "passed", result)
            for name in (entry["result_analysis_code"], entry["result_analysis_workbook"], current):
                report = VALIDATOR.validate_package(root, archive(root, omit=[name]))
                self.assertTrue(any(name in issue for issue in report["issues"]), report)

    def test_directory_data_sources_require_each_real_member_not_a_directory_entry(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = complete_project(root)
            nested = root / "附件/嵌套/第二附件.csv"
            nested.parent.mkdir()
            nested.write_text("synthetic input")
            state["data"] = {"sources": [{"path": "附件"}]}
            save_state(root, state)
            package = archive(root)
            with zipfile.ZipFile(package) as bundle:
                self.assertNotIn("附件", bundle.namelist())
                self.assertNotIn("附件/", bundle.namelist())
            result = VALIDATOR.validate_package(root, package)
            self.assertEqual(result["status"], "passed", result)
            name = "附件/嵌套/第二附件.csv"
            result = VALIDATOR.validate_package(root, archive(root, omit=[name]))
            self.assertEqual(result["status"], "failed", result)
            self.assertTrue(any(name in item for item in result["issues"]), result)
            state["data"]["sources"] = [{"path": "不存在的数据目录"}]
            save_state(root, state)
            result = VALIDATOR.validate_package(root, archive(root))
            self.assertEqual(result["status"], "failed", result)
            self.assertTrue(any("不存在的数据目录" in item for item in result["issues"]), result)

    def test_v4_changed_or_wrong_binding_and_escaping_recorded_inputs_are_rejected(self):
        cases = ("changed_recorder", "wrong_recorder", "outside_log", "outside_source", "outside_actual", "outside_audit", "wrong_main")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                state = complete_project(root)
                path, report = compile_fixture(root, state)
                if case == "changed_recorder":
                    (root / "final_latex/main.fls").write_bytes(b"changed")
                elif case == "wrong_recorder":
                    report["recorder"] = "unused.fls"
                elif case == "outside_log":
                    report["log"] = "../outside.log"
                elif case == "outside_audit":
                    report["latex_audit_report"] = "../outside.yaml"
                elif case == "wrong_main":
                    report["main"] = "other.tex"
                else:
                    field = "source_files" if case == "outside_source" else "actual_input_files"
                    report[field] = [{"path": "../outside.tex"}]
                path.write_text(yaml.safe_dump(report), encoding="utf-8")
                result = VALIDATOR.validate_package(root, archive(root))
                self.assertEqual(result["status"], "failed", result)
                self.assertTrue(any("编译" in item for item in result["issues"]), result)

    def test_archive_integrity_rejections_survive_complete_required_set(self):
        for case, diagnostic in (("hash", "哈希"), ("duplicate", "重复文件名"), ("outside", "越出项目根目录"), ("undeclared", "未声明")):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                complete_project(root)
                package = archive(root)
                with zipfile.ZipFile(package) as bundle:
                    entries = {name: bundle.read(name) for name in bundle.namelist()}
                if case == "hash":
                    entries["final_latex/main.pdf"] = b"tampered"
                elif case == "outside":
                    payload = b"outside fixture member"
                    manifest = yaml.safe_load(entries[VALIDATOR.MANIFEST_NAME])
                    manifest["files"].append({"path": "../outside.txt", "sha256": hashlib.sha256(payload).hexdigest()})
                    entries[VALIDATOR.MANIFEST_NAME] = yaml.safe_dump(manifest)
                    entries["../outside.txt"] = payload
                elif case == "undeclared":
                    entries["undeclared.txt"] = b"undeclared"
                with warnings.catch_warnings(), zipfile.ZipFile(package, "w") as bundle:
                    warnings.simplefilter("ignore", UserWarning)
                    for name, payload in entries.items():
                        bundle.writestr(name, payload)
                    if case == "duplicate":
                        bundle.writestr("final_latex/main.pdf", entries["final_latex/main.pdf"])
                report = VALIDATOR.validate_package(root, package)
                self.assertTrue(any(diagnostic in item for item in report["issues"]), report)

    def test_official_exact_directory_or_escape_fails_and_multiple_wildcard_matches_work(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            complete_project(root)
            for pattern in ("final_latex", "../outside.pdf", ""):
                with self.subTest(pattern=pattern), self.assertRaises(SystemExit):
                    PACK._expand_allowlist(root, ["final_latex/main.pdf", pattern])
                with self.subTest(pattern=pattern), self.assertRaises(ValueError):
                    VALIDATOR.expand_allowlist(root, ["final_latex/main.pdf", pattern])
            folder = root / "optional"
            folder.mkdir()
            for name in ("one.txt", "two.txt"):
                (folder / name).write_text("fixture")
            files = PACK._expand_allowlist(root, ["final_latex/main.pdf", "optional/*.txt"])
            self.assertEqual(len(files), 3)
            self.assertEqual(VALIDATOR.expand_allowlist(root, ["final_latex/main.pdf", "optional/*.txt"]),
                             {path.relative_to(root.resolve()).as_posix() for path in files})


if __name__ == "__main__":
    unittest.main()
