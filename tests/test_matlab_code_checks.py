from __future__ import annotations

import json
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import matlab_code_checks as MATLAB
import run_config_parser as PARSER


def matlab_source(config: dict, extra: str = "") -> str:
    encoded = json.dumps(config, ensure_ascii=False).replace("'", "''")
    return f"function result = q1_solver()\nRUN_CONFIG = jsondecode('{encoded}');\nresult = RUN_CONFIG;\n{extra}\nend\n"


class MatlabCodeChecksTests(unittest.TestCase):
    def test_literal_round_trip_and_apostrophe(self):
        config = {"stage": "primary", "note": "文本 O'Brien % ", "code_dependencies": [],
                  "code_quality_exemption": {"enabled": False, "reason": ""}}
        self.assertEqual(MATLAB.parse_config(matlab_source(config)), ("RUN_CONFIG", config))
        self.assertEqual(PARSER.parse_embedded_config(matlab_source(config), backend="matlab",
                                                    messages=PARSER.DELIVERY_MESSAGES)[1], config)

    def test_continued_character_concatenation(self):
        text = "function q1_solver()\n% comment\nRUN_CONFIG=jsondecode([ ... % continuation\n '{\"stage\":' ...\n '\"primary\"}']);\nend\n"
        self.assertEqual(MATLAB.parse_config(text)[1], {"stage": "primary"})

    def test_comments_and_transpose_are_distinct(self):
        source = matlab_source({"stage": "primary"}, "x=[1 2]; y=x'; z=x.'; s=\"value%\"; % fake RUN_CONFIG\n")
        tokens = MATLAB.tokenize(source)
        self.assertTrue(any(item.value == "'" and item.kind == "symbol" for item in tokens))
        self.assertTrue(any(item.value == "value%" for item in tokens))
        self.assertEqual(MATLAB.parse_config(source)[1]["stage"], "primary")

    def test_block_comment_config_does_not_count(self):
        text = "%{\nRUN_CONFIG=jsondecode('{}');\n%}\n" + matlab_source({"stage": "primary"})
        self.assertEqual(MATLAB.parse_config(text)[1]["stage"], "primary")

    def test_rejects_dynamic_or_ambiguous_config_forms(self):
        bad = [
            "RUN_CONFIG=jsondecode(fileread('config.json'));",
            "RUN_CONFIG=struct('stage','primary');",
            "RUN_CONFIG=jsondecode(['{}',value]);",
            "RUN_CONFIG=jsondecode(\"{}\");",
            "if true\nRUN_CONFIG=jsondecode('{}');\nend",
            "% RUN_CONFIG=jsondecode('{}');\nx=1;",
            "RUN_CONFIG=jsondecode('{\"stage\":1,\"stage\":2}');",
            "RUN_CONFIG=jsondecode('{\"bad-key\":1}');",
            "RUN_CONFIG=jsondecode('{\"x\":NaN}');",
            "RUN_CONFIG=jsondecode('{\"x\":1e999}');",
            "RUN_CONFIG=jsondecode('{\"random_seed\":9007199254740993}');",
            "RUN_CONFIG=jsondecode('[]');",
        ]
        for body in bad:
            with self.subTest(body=body), self.assertRaises(ValueError):
                MATLAB.parse_config("function q1_solver()\n" + body + "\nend")

    def test_config_redefinition_and_mutation_rejected(self):
        for extra in ("RUN_CONFIG=jsondecode('{}');", "RUN_CONFIG.stage='analysis';", "RUN_CONFIG.('stage')='analysis';", "clear RUN_CONFIG"):
            with self.subTest(extra=extra), self.assertRaisesRegex(ValueError, "覆盖|重复|清除"):
                MATLAB.parse_config(matlab_source({}, extra))

    def test_never_executes_json_text(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "should_not_exist"
            source = matlab_source({"note": f"system('touch {target}')"})
            self.assertEqual(MATLAB.parse_config(source)[1]["note"], f"system('touch {target}')")
            self.assertFalse(target.exists())

    def findings(self, extra: str):
        contract = yaml.safe_load((ROOT / "core/code_quality_contract.yaml").read_text(encoding="utf-8"))
        return MATLAB.matlab_code_findings(matlab_source({}, extra), {}, contract=contract, filename="q1_solver.m")

    def test_native_verification_is_not_claimed_by_portable_check(self):
        errors, _, metrics = self.findings("x=[1 2]; result=x(end); ")
        self.assertEqual(errors, [])
        self.assertEqual(metrics["native_analysis_status"], "unverified")
        self.assertEqual(metrics["function_count"], 1)

    def test_invalid_structure_and_role_calls(self):
        for extra in ("if true\nx=1;", "plot(1,2);", "eval('x=1');", "mlock;", "mlock();", "addpath('old');", "try\nx=1;\ncatch\nend"):
            with self.subTest(extra=extra):
                self.assertTrue(self.findings(extra)[0])

    def test_wrong_main_function_is_blocking(self):
        contract = yaml.safe_load((ROOT / "core/code_quality_contract.yaml").read_text(encoding="utf-8"))
        issues, _, _ = MATLAB.matlab_code_findings(matlab_source({}), {}, contract=contract, filename="q2_solver.m")
        self.assertTrue(any("主函数名" in issue for issue in issues))

    def test_data_reader_literals_ignore_comments(self):
        source = "x=readtable('共享.xlsx'); y=readcell(\"真实.xlsx\"); % load('fake.xlsx')\n"
        self.assertEqual(MATLAB.literal_data_reader_paths(source), ["共享.xlsx", "真实.xlsx"])

    def test_unavailable_native_analyzer_is_unverified(self):
        with patch.object(MATLAB.shutil, "which", return_value=None):
            result = MATLAB.native_code_analysis(Path("never-read.m"))
        self.assertEqual(result["status"], "unverified")

    def test_native_launch_failure_retains_bounded_redacted_process_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "q1_solver.m"
            source.write_text(matlab_source({}), encoding="utf-8")
            output = subprocess.CompletedProcess([], 2,
                "MATHWORKS_TOKEN=example-secret\n" + "startup detail\n" * 500,
                "License checkout failed: -9\nAuthorization: Bearer example-bearer\npassword='example password'")
            with patch.object(MATLAB.subprocess, "run", return_value=output):
                result = MATLAB.native_code_analysis(source, "matlab")
        self.assertEqual(result["status"], "unverified")
        messages = "\n".join(result["issues"])
        self.assertIn("exit_code=2", messages)
        self.assertIn("License checkout failed: -9", messages)
        self.assertIn("[truncated]", messages)
        for secret in ("example-secret", "example-bearer", "example password"):
            self.assertNotIn(secret, messages)
        self.assertTrue(all(len(item) <= 2040 for item in result["issues"]))

    def test_native_timeout_retains_partial_byte_output_and_missing_report_is_distinct(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "q1_solver.m"
            source.write_text(matlab_source({}), encoding="utf-8")
            error = subprocess.TimeoutExpired("matlab", 3, output=b"Launching MATLAB", stderr=b"api_key=example-key\nLicense wait")
            with patch.object(MATLAB.subprocess, "run", side_effect=error):
                result = MATLAB.native_code_analysis(source, "matlab", timeout=3)
            messages = "\n".join(result["issues"])
            self.assertIn("TimeoutExpired after 3s", messages)
            self.assertIn("Launching MATLAB", messages)
            self.assertIn("License wait", messages)
            self.assertNotIn("example-key", messages)
            with patch.object(MATLAB.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "No analysis report produced", "")):
                result = MATLAB.native_code_analysis(source, "matlab")
            self.assertIn("report_exists=False", result["issues"][0])
            self.assertIn("No analysis report produced", "\n".join(result["issues"]))

    def test_failed_native_evidence_reaches_strict_delivery_cli(self):
        import validate_code_delivery as delivery
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "问题一求解/q1_solver.m"
            source.parent.mkdir()
            config = {"stage": "primary", "problem_name": "问题一", "solver_backend": "matlab",
                      "data_paths": ["input.json"], "data_sha256": "a" * 64, "solver": "direct", "random_seed": 2026,
                      "tolerance": 1e-8, "iteration_or_time_limit": "direct", "expected_workbook": "问题一求解结果.xlsx",
                      "run_receipt_protocol_version": "1.1.0", "primary_quality_protocol_version": "1.0.0", "code_dependencies": []}
            source.write_text(matlab_source(config), encoding="utf-8")
            failed = subprocess.CompletedProcess([], 7, "Launcher started", "License Manager Error -9")
            captured = io.StringIO()
            with patch.object(MATLAB.subprocess, "run", return_value=failed), patch.object(sys, "argv", [
                    "validate_code_delivery.py", str(root), "--script", str(source), "--strict", "--matlab-command", "matlab"]), redirect_stdout(captured):
                code = delivery.main()
            report = yaml.safe_load(captured.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(report["status"], "failed")
        self.assertFalse(report["task_code_executed"])
        self.assertTrue(any("License Manager Error -9" in item for item in report["issues"]))
        self.assertTrue(any("exit_code=7" in item for item in report["issues"]))

    def test_current_matlab_templates_have_parseable_unique_configs(self):
        for path in (ROOT / "templates/code/matlab").glob("q1_*.m"):
            with self.subTest(path=path.name):
                config = MATLAB.parse_config(path.read_text(encoding="utf-8"))[1]
                self.assertEqual(config["solver_backend"], "matlab")
                contract = yaml.safe_load((ROOT / "core/code_quality_contract.yaml").read_text(encoding="utf-8"))
                self.assertEqual(MATLAB.matlab_code_findings(path.read_text(encoding="utf-8"), config,
                                                          contract=contract, filename=path.name)[0], [])


if __name__ == "__main__":
    unittest.main()
