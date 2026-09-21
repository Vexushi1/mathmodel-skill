from __future__ import annotations

import json
import sys
import tempfile
import unittest
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
