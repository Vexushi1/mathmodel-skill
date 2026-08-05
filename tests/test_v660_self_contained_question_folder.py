import importlib.util
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_sync():
    spec = importlib.util.spec_from_file_location("sync_project_v660", ROOT / "scripts/sync_project.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestV660SelfContainedQuestionFolder(unittest.TestCase):
    def test_output_contract_has_exact_four_default_files(self):
        data = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        per_question = data["per_question"]
        self.assertEqual(per_question["question_directory"], "问题{中文序号}求解/")
        self.assertEqual(len(per_question["exact_default_files"]), 4)
        self.assertTrue(per_question["no_auxiliary_files_by_default"])

    def test_user_contract_forbids_standalone_auxiliary_files(self):
        data = yaml.safe_load((ROOT / "core/user_execution_contract.yaml").read_text(encoding="utf-8"))
        forbidden = set(data["code_delivery"]["standalone_files_forbidden_by_default"])
        self.assertIn("问题X结果深化分析.py", forbidden)
        self.assertEqual(data["filenames"]["python_code"], "问题X求解/问题X求解.py")

    def test_sync_python_discovery_is_question_specific(self):
        sync = load_sync()
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for problem in ("问题一", "问题二"):
                folder = root / f"{problem}求解"
                folder.mkdir()
                (folder / f"{problem}求解.py").write_text("", encoding="utf-8")
            files = sync._python_files(root, "问题一")
            self.assertEqual([path.name for path in files], ["问题一求解.py"])

    def test_nested_plugin_paths_resolve(self):
        skill_dir = ROOT / "skills/mathmodel-skill"
        self.assertTrue((skill_dir / "../../core/bootstrap.yaml").resolve().is_file())
        self.assertTrue((skill_dir / "../../scripts/resolve_workflow.py").resolve().is_file())


if __name__ == "__main__":
    unittest.main()
