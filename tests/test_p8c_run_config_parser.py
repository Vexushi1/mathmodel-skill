from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PARSER = load_module("p8c_run_config_parser", ROOT / "scripts" / "run_config_parser.py")
CODE = load_module("p8c_validate_code_delivery", ROOT / "scripts" / "validate_code_delivery.py")
RECEIPT = load_module("p8c_validate_user_execution", ROOT / "scripts" / "validate_user_execution.py")


class P8cRunConfigParserTests(unittest.TestCase):
    def config(self) -> dict:
        return {"stage": "primary", "problem_name": "问题一"}

    def test_both_validators_share_supported_names(self):
        self.assertEqual(CODE.CONFIG_NAMES, PARSER.CONFIG_NAMES)
        self.assertEqual(RECEIPT.CONFIG_NAMES, PARSER.CONFIG_NAMES)

    def test_success_behavior_is_identical(self):
        text = f"RUN_CONFIG = {self.config()!r}\n"
        expected = ("RUN_CONFIG", self.config())
        self.assertEqual(CODE.embedded_config(text), expected)
        self.assertEqual(RECEIPT._embedded_config(text), expected)

    def test_delivery_error_text_is_preserved(self):
        with self.assertRaisesRegex(ValueError, "缺少RUN_CONFIG字典常量"):
            CODE.embedded_config("x = 1\n")
        with self.assertRaisesRegex(ValueError, "RUN_CONFIG必须为字典常量"):
            CODE.embedded_config("RUN_CONFIG = []\n")
        with self.assertRaisesRegex(ValueError, "同一脚本只能定义一个受支持运行配置"):
            CODE.embedded_config("RUN_CONFIG = {}\nFULL_RUN_CONFIG = {}\n")

    def test_returned_execution_error_text_is_preserved(self):
        with self.assertRaisesRegex(ValueError, "已交付阶段代码缺少RUN_CONFIG字典常量"):
            RECEIPT._embedded_config("x = 1\n")
        with self.assertRaisesRegex(ValueError, "已交付阶段代码中的RUN_CONFIG必须为字典常量"):
            RECEIPT._embedded_config("RUN_CONFIG = []\n")
        with self.assertRaisesRegex(ValueError, "已交付阶段代码只能定义一个受支持运行配置"):
            RECEIPT._embedded_config("RUN_CONFIG = {}\nFULL_RUN_CONFIG = {}\n")

    def test_parser_remains_top_level_literal_only(self):
        with self.assertRaisesRegex(ValueError, "缺少RUN_CONFIG"):
            CODE.embedded_config("def f():\n    RUN_CONFIG = {}\n")
        with self.assertRaises((ValueError, TypeError)):
            CODE.embedded_config("RUN_CONFIG = dict(stage='primary')\n")

    def test_duplicate_literal_eval_implementations_are_removed(self):
        self.assertNotIn(
            "ast.literal_eval",
            (ROOT / "scripts" / "validate_code_delivery.py").read_text(encoding="utf-8"),
        )
        self.assertNotIn(
            "ast.literal_eval",
            (ROOT / "scripts" / "validate_user_execution.py").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "ast.literal_eval",
            (ROOT / "scripts" / "run_config_parser.py").read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
