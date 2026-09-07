from __future__ import annotations

import ast
import importlib.util
import inspect
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def load_module(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SYNC = load_module("phase_h_sync", "scripts/sync_project.py")
FINGERPRINT = load_module("phase_h_fingerprint", "scripts/artifact_fingerprint.py")
SNAPSHOT = load_module("phase_h_snapshot", "scripts/project_snapshot.py")
MOVED = ['sha256_file', 'sha256_text', 'combined_hash', 'framework_section_text', 'framework_section_hash', 'question_key', 'chinese_question_name', 'question_number', 'preprocessing_decision', 'data_source_files', 'active_data_hash', '_classification', '_question_dir', '_question_names', '_stage_code_paths', '_python_files', '_analysis_path', '_figure_files', '_validate_workbook', '_has_sheets', '_matlab_executable_text', '_parse_matlab', '_snapshot_question']


class PhaseHMechanicalSplitTests(unittest.TestCase):
    def test_sync_project_no_longer_defines_extracted_functions(self):
        tree = ast.parse((ROOT / "scripts/sync_project.py").read_text(encoding="utf-8"))
        defined = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.assertTrue(set(MOVED).isdisjoint(defined))

    def test_compatibility_aliases_preserve_existing_surface(self):
        for name in ['sha256_file', 'sha256_text', 'combined_hash', 'framework_section_text', 'framework_section_hash']:
            self.assertIs(getattr(SYNC, name), getattr(SYNC.ARTIFACT_FINGERPRINT, name))
        for name in ['question_key', 'chinese_question_name', 'question_number', 'preprocessing_decision', 'data_source_files', 'active_data_hash', '_classification', '_question_dir', '_question_names', '_stage_code_paths', '_python_files', '_analysis_path', '_figure_files', '_validate_workbook', '_has_sheets', '_matlab_executable_text', '_parse_matlab', '_snapshot_question']:
            self.assertIs(getattr(SYNC, name), getattr(SYNC.PROJECT_SNAPSHOT, name))

    def test_synchronize_signature_is_unchanged(self):
        parameters = list(inspect.signature(SYNC.synchronize).parameters)
        self.assertEqual(
            parameters,
            ["project_root", "write", "strict", "delivery_scope", "schema_path", "output_contract_path"],
        )

    def test_empty_project_sync_report_matches_pre_split_golden(self):
        expected = yaml.safe_load((ROOT / "tests/fixtures/v900_phase_h_empty_sync_golden.yaml").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            actual = SYNC.synchronize(Path(tmp), write=False, strict=False)
        actual = dict(actual)
        actual.pop("generated_at", None)
        self.assertEqual(actual, expected)

    def test_fingerprint_helpers_remain_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "a.txt"
            second = root / "b.txt"
            first.write_text("alpha\n", encoding="utf-8")
            second.write_text("beta\n", encoding="utf-8")
            self.assertEqual(FINGERPRINT.sha256_file(first), SYNC.sha256_file(first))
            self.assertEqual(
                FINGERPRINT.combined_hash([second, first], root),
                FINGERPRINT.combined_hash([first, second], root),
            )


if __name__ == "__main__":
    unittest.main()
