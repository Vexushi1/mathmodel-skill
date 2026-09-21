"""Reference-boundary follow-up and real historical receipt regression.

All executions are isolated scalar repository fixtures, not user problem models.
The narrow patched guard creates only a pre-fix accepted record for rejection.
"""
from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]
from python_source_checks import execution_reference_issues
import stage_code as STAGE
import validate_code_delivery as DELIVERY
import validate_user_execution as RECEIPT
import solver_backend_mixed_smoke as REAL


class PythonReferenceFollowupTests(unittest.TestCase):
    def test_reflective_acquisition_is_rejected_at_qualified_origin(self):
        cases = (
            'import importlib\nload = importlib.__getattribute__("import_module")',
            'from importlib import __getattribute__ as grab\nload = grab("import_module")',
            'from importlib import __dict__ as ns\nload = ns["import_module"]',
            'import importlib\nloader = importlib.__loader__',
            'import importlib\nspec = importlib.__spec__',
            'import builtins\nload = builtins.__getattribute__("__import__")',
            'import os\nlaunch = os.__getattribute__("system")',
        )
        for source in cases:
            with self.subTest(source=source):
                self.assertTrue(execution_reference_issues(ast.parse(source)))
        # Do not ban arbitrary numerical object attributes by spelling alone.
        self.assertEqual(execution_reference_issues(ast.parse('value = obj.__getattribute__("shape")')), [])

    def test_matlab_root_namespace_cannot_hide_engine_launch(self):
        for source in (
            'import matlab\nm = matlab\nlaunch = m.engine.start_matlab',
            'import matlab\nlaunch = getattr(matlab, "engine").start_matlab',
        ):
            with self.subTest(source=source):
                self.assertTrue(execution_reference_issues(ast.parse(source)))

    def test_process_constants_are_values_not_execution_capabilities(self):
        for source in (
            'import subprocess\nvalue = subprocess.PIPE',
            'from subprocess import DEVNULL, STDOUT\nvalues = [DEVNULL, STDOUT]',
            'import subprocess as process\nvalue = process.STDOUT',
        ):
            with self.subTest(source=source):
                self.assertEqual(execution_reference_issues(ast.parse(source)), [])
        for source in ('import subprocess\nf = subprocess.run',
                       'import subprocess\nsubprocess.PIPE()',
                       'from subprocess import PIPE\nPIPE()'):
            with self.subTest(source=source):
                self.assertTrue(execution_reference_issues(ast.parse(source)))

    def test_actual_old_workbooks_are_rejected_without_rebinding(self):
        for acquisition in ('importlib.import_module', 'importlib.__getattribute__("import_module")'):
            with self.subTest(acquisition=acquisition), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / "input.json").write_text('{"coefficient":2,"right_hand_side":6}', encoding="utf-8")
                REAL.python_primary(root, "问题一", False)
                code = root / "问题一求解/问题一求解.py"
                text = code.read_text(encoding="utf-8").replace("import hashlib\n", "import hashlib\nimport importlib\n", 1)
                needle = "    solution = right_hand_side / coefficient"
                self.assertIn(needle, text)
                text = text.replace(needle, '    load = ' + acquisition + '\n    right_hand_side *= load("helper").FACTOR\n' + needle, 1)
                code.write_text(text, encoding="utf-8")
                helper = code.parent / "helper.py"
                helper.write_text("FACTOR = 1.0\n", encoding="utf-8")
                REAL.register(root, "问题一", code, "python", ["input.json"])
                first = json.loads(subprocess.check_output([sys.executable, "-B", str(code)], cwd=root, text=True))
                self.assertEqual(first["answer"], 3.0)
                # Numerical execution and workbook are real. Only emulate the
                # old source gate while constructing its historical provenance.
                with patch.object(STAGE, "dependency_reference_issues", return_value=[]):
                    REAL.accept(root, "问题一", "python", 3)
                state = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
                before = deepcopy(state)
                workbook = code.parent / "问题一求解结果.xlsx"
                original = workbook.read_bytes()
                self.assertTrue(DELIVERY.validate_script(root, code)[0])
                self.assertTrue(RECEIPT.validate_one(root, workbook, state, False))
                self.assertEqual(state, before)
                self.assertTrue(RECEIPT.validate_one(root, workbook, state, True))
                self.assertEqual(state["subproblems"]["Q1"]["primary_execution_status"], "rejected")
                for field in ("solver_execution", "primary_code_sha256", "validated_artifact_hashes"):
                    self.assertEqual(state["subproblems"]["Q1"][field], before["subproblems"]["Q1"][field])
                helper.write_text("FACTOR = 2.0\n", encoding="utf-8")
                second = json.loads(subprocess.check_output([sys.executable, "-B", str(code)], cwd=root, text=True))
                self.assertEqual(second["answer"], 6.0)
                self.assertEqual(first["code_sha256"], second["code_sha256"])
                workbook.write_bytes(original)
                self.assertTrue(RECEIPT.validate_one(root, workbook, state, False))
                self.assertTrue(STAGE.validate_stage_binding(root, state["subproblems"]["Q1"], "primary", require_validated=True))


if __name__ == "__main__":
    unittest.main()
