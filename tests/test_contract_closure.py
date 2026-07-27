import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class TestContractClosure(unittest.TestCase):
    def setUp(self):
        self.manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8"))

    def test_all_module_and_gate_artifacts_are_catalogued(self):
        known = set(self.manifest["artifact_catalog"]) | set(self.manifest["external_artifacts"])
        for name, module in self.manifest["modules"].items():
            for field in ("inputs", "outputs"):
                self.assertEqual(set(module[field]) - known, set(), f"{name}.{field}")
        for name, gate in self.manifest["utility_gates"].items():
            for field in ("inputs", "outputs"):
                self.assertEqual(set(gate[field]) - known, set(), f"gate {name}.{field}")

    def test_full_workflow_closes_after_utility_gate(self):
        available = set(self.manifest["external_artifacts"])
        modules = self.manifest["modules"]
        profile = self.manifest["workflow_profiles"]["full_workflow"]
        for name in profile["modules"]:
            missing = set(modules[name]["inputs"]) - available
            self.assertEqual(missing, set(), name)
            available.update(modules[name]["outputs"])
        self.assertNotIn("sync_report", available)
        for gate_name in profile["pre_delivery_gates"]:
            gate = self.manifest["utility_gates"][gate_name]
            self.assertEqual(set(gate["inputs"]) - available - set(self.manifest["external_artifacts"]), set())
            available.update(gate["outputs"])
        self.assertTrue(set(profile["terminal_outputs"]).issubset(available))
        self.assertIn("sync_report", available)

    def test_project_sync_is_real_producer(self):
        gate = self.manifest["utility_gates"]["project_sync"]
        self.assertEqual(gate["path"], "scripts/sync_project.py")
        self.assertTrue((ROOT / gate["path"]).is_file())
        self.assertEqual(set(gate["outputs"]), {"project_state", "sync_report"})
        self.assertIn("<delivery_scope>", gate["command"])

    def test_cleanup_precedes_compile(self):
        modules = self.manifest["workflow_profiles"]["full_workflow"]["modules"]
        self.assertLess(modules.index("ai_cleanup"), modules.index("latex_compile_quality"))
        compile_inputs = set(self.manifest["modules"]["latex_compile_quality"]["inputs"])
        self.assertIn("latex_source", compile_inputs)
        self.assertNotIn("latex_source_draft", compile_inputs)


if __name__ == "__main__":
    unittest.main()
