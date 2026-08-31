import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_runtime():
    path = ROOT / "scripts/resolve_runtime.py"
    spec = importlib.util.spec_from_file_location("resolve_runtime_v800_cross_chat", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.path.insert(0, str(ROOT / "scripts"))
    spec.loader.exec_module(module)
    return module


class TestV800CrossChatMinimalContext(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = load_runtime()

    def test_fresh_latex_context_uses_compact_writing_package(self):
        plan = self.runtime.resolve_runtime("latex", competition="CUMCM")
        required = {
            "core/writing_runtime_contract.yaml",
            "templates/latex/cumcm/hsk/template_manifest.yaml",
            "modules/05_writing/paper_writing_protocol.md",
            "modules/05_writing/latex.md",
        }
        self.assertTrue(required <= set(plan["load_order"]))
        self.assertNotIn("core/writing_reasoning_contract.yaml", plan["load_order"])
        for forbidden in (
            "core/numerical_verification_contract.yaml",
            "core/model_approval_contract.yaml",
            "core/user_execution_contract.yaml",
            "core/code_quality_contract.yaml",
        ):
            self.assertNotIn(forbidden, plan["load_order"], forbidden)

    def test_full_reasoning_remains_available_for_semantic_fallback(self):
        plan = self.runtime.resolve_runtime("latex", competition="CUMCM")
        runtime = plan["writing_runtime"]
        self.assertEqual(runtime["full_reasoning_authority_fallback"], "core/writing_reasoning_contract.yaml")
        self.assertTrue(runtime["fallback_triggers"])

    def test_final_review_keeps_full_authority(self):
        plan = self.runtime.resolve_runtime("review", competition="CUMCM")
        self.assertIn("core/writing_reasoning_contract.yaml", plan["load_order"])
        self.assertNotIn("writing_runtime", plan)


if __name__ == "__main__":
    unittest.main()
