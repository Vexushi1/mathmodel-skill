import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class TestContractClosure(unittest.TestCase):
    def setUp(self):
        self.manifest = yaml.safe_load(
            (ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8")
        )

    def test_all_module_artifacts_are_catalogued(self):
        known = set(self.manifest["artifact_catalog"]) | set(self.manifest["external_artifacts"])
        for name, module in self.manifest["modules"].items():
            for field in ("inputs", "outputs"):
                self.assertEqual(set(module[field]) - known, set(), f"{name}.{field}")

    def test_full_workflow_inputs_have_upstream_producers(self):
        available = set(self.manifest["external_artifacts"])
        modules = self.manifest["modules"]
        profile = self.manifest["workflow_profiles"]["full_workflow"]
        for name in profile["modules"]:
            missing = set(modules[name]["inputs"]) - available
            self.assertEqual(missing, set(), name)
            available.update(modules[name]["outputs"])
        self.assertTrue(set(profile["terminal_outputs"]).issubset(available))

    def test_cleanup_precedes_compile(self):
        modules = self.manifest["workflow_profiles"]["full_workflow"]["modules"]
        self.assertLess(modules.index("ai_cleanup"), modules.index("latex_compile_quality"))
        compile_inputs = set(self.manifest["modules"]["latex_compile_quality"]["inputs"])
        self.assertIn("latex_source", compile_inputs)
        self.assertNotIn("latex_source_draft", compile_inputs)


if __name__ == "__main__":
    unittest.main()
