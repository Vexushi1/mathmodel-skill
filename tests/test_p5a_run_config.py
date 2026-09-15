from __future__ import annotations

import ast
import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
FALSE_FLAGS = (
    "allow_reduced_data", "allow_coarser_grid", "allow_shorter_horizon",
    "allow_fewer_repetitions", "allow_relaxed_tolerance",
    "allow_silent_solver_fallback",
)
POLICY_FIELDS = {"execution_owner", "execution_profile", *FALSE_FLAGS}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


CODE = load_module("p5a_validate_code_delivery", ROOT / "scripts" / "validate_code_delivery.py")
RECEIPT = load_module("p5a_validate_user_execution", ROOT / "scripts" / "validate_user_execution.py")


class P5aRunConfigTests(unittest.TestCase):
    def run_config(self) -> dict:
        return {
            "stage": "primary",
            "problem_name": "问题一",
            "data_paths": ["附件1.xlsx"],
            "data_sha256": "a" * 64,
            "solver": "test-solver",
            "random_seed": 2026,
            "tolerance": 1e-8,
            "iteration_or_time_limit": "full",
            "expected_workbook": "问题一求解/问题一求解结果.xlsx",
            "primary_quality_protocol_version": "1.0.0",
        }

    def legacy_config(self) -> dict:
        config = {
            **self.run_config(),
            "execution_owner": "user",
            "execution_profile": "full_fidelity",
            "solver_version": "1.0",
        }
        config.update({flag: False for flag in FALSE_FLAGS})
        return config

    def write_script(self, root: Path, name: str, config: dict, *, extra: str = "") -> Path:
        folder = root / "问题一求解"
        folder.mkdir(parents=True, exist_ok=True)
        script = folder / "问题一求解.py"
        script.write_text(
            f"{name} = {config!r}\n{extra}\n"
            "def main():\n    return 0\n\n"
            "if __name__ == '__main__':\n    raise SystemExit(main())\n",
            encoding="utf-8",
        )
        return script

    def test_canonical_run_config_omits_inherited_policy_and_solver_version(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            script = self.write_script(root, "RUN_CONFIG", self.run_config())
            issues, config = CODE.validate_script(root, script, "primary")
            self.assertEqual(issues, [])
            self.assertNotIn("execution_owner", config)
            self.assertNotIn("execution_profile", config)
            self.assertNotIn("solver_version", config)
            for flag in FALSE_FLAGS:
                self.assertNotIn(flag, config)

    def test_canonical_run_config_still_requires_pre_run_data_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = self.run_config()
            config.pop("data_sha256")
            script = self.write_script(root, "RUN_CONFIG", config)
            issues, _ = CODE.validate_script(root, script, "primary")
            self.assertTrue(any("data_sha256" in issue for issue in issues))

    def test_canonical_run_config_rejects_illegal_policy_override(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = self.run_config()
            config["allow_reduced_data"] = True
            script = self.write_script(root, "RUN_CONFIG", config)
            issues, _ = CODE.validate_script(root, script, "primary")
            self.assertTrue(any("不得覆盖全局执行政策" in issue for issue in issues))

    def test_canonical_run_config_accepts_matching_redundant_policy_override(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = self.run_config()
            config.update({"execution_owner": "user", "execution_profile": "full_fidelity"})
            config.update({flag: False for flag in FALSE_FLAGS})
            config["solver_version"] = "redundant-runtime-hint"
            script = self.write_script(root, "RUN_CONFIG", config)
            issues, _ = CODE.validate_script(root, script, "primary")
            self.assertEqual(issues, [])

    def test_legacy_config_keeps_old_required_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = self.legacy_config()
            config.pop("solver_version")
            config.pop("allow_coarser_grid")
            script = self.write_script(root, "FULL_FIDELITY_CONFIG", config)
            issues, _ = CODE.validate_script(root, script, "primary")
            self.assertTrue(any("solver_version" in issue for issue in issues))
            self.assertTrue(any("allow_coarser_grid" in issue for issue in issues))

    def test_delivery_multiple_supported_configs_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            script = self.write_script(
                root,
                "RUN_CONFIG",
                self.run_config(),
                extra=f"FULL_RUN_CONFIG = {self.legacy_config()!r}",
            )
            issues, _ = CODE.validate_script(root, script, "primary")
            self.assertTrue(any("只能定义一个受支持运行配置" in issue for issue in issues))

    def test_receipt_static_reader_multiple_supported_configs_fail_closed(self):
        text = (
            f"RUN_CONFIG = {self.run_config()!r}\n"
            f"FULL_FIDELITY_CONFIG = {self.legacy_config()!r}\n"
        )
        with self.assertRaisesRegex(ValueError, "只能定义一个受支持运行配置"):
            RECEIPT._embedded_config(text)

    def test_contract_separates_canonical_task_fields_from_inherited_policy(self):
        contract = yaml.safe_load(
            (ROOT / "core" / "user_execution_contract.yaml").read_text(encoding="utf-8")
        )
        delivery = contract["code_delivery"]
        self.assertEqual(delivery["canonical_config_name"], "RUN_CONFIG")
        canonical = set(delivery["canonical_required_config_fields"])
        self.assertFalse(canonical & POLICY_FIELDS)
        self.assertNotIn("solver_version", canonical)
        self.assertIn("data_sha256", canonical)
        self.assertEqual(set(delivery["legacy_config_names"]), {"FULL_FIDELITY_CONFIG", "FULL_RUN_CONFIG"})
        legacy = set(delivery["legacy_required_config_fields"])
        self.assertTrue(POLICY_FIELDS <= legacy)
        self.assertIn("solver_version", legacy)

    def test_pipeline_config_does_not_repeat_execution_policy_fields(self):
        tree = ast.parse(
            (ROOT / "templates" / "code" / "hsk_pipeline" / "main_pipeline.py").read_text(encoding="utf-8")
        )
        pipeline = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "PipelineConfig"
        )
        fields = {
            node.target.id
            for node in pipeline.body
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
        }
        self.assertFalse(fields & POLICY_FIELDS)


if __name__ == "__main__":
    unittest.main()
