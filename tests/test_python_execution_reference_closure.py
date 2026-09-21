"""A13/A14 regressions: reference rejection and old false-acceptance quarantine.

Snapshot/workbook fixtures below deliberately model a pre-fix accepted record;
constructing one is not a successful acceptance by the current checker.
"""
from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from python_source_checks import execution_reference_issues
import stage_code as STAGE
import validate_code_delivery as DELIVERY
import validate_user_execution as RECEIPT
import sync_project as SYNC
from resolve_runtime import resolve_runtime
from submission_requirements import reproducibility_requirements
from tests import test_solver_backend_source_closure as source_fixtures
from tests import test_solver_backends as workbook_fixtures
from tests.test_solver_backend_downstream_identity import project_fixture, package_fixture, stage_fixture
from tests.test_solver_backend_runtime_resume import legacy_primary_project
from tests.test_solver_backend_end_to_end import save_state, file_hash
from tests.test_audit_package_completeness import archive, VALIDATOR


class PythonExecutionReferenceTests(unittest.TestCase):
    def check(self, text):
        return execution_reference_issues(ast.parse(text))

    def test_assignment_and_chained_callable_aliases(self):
        cases = [
            'import importlib\nload = importlib.import_module\nload("helper")',
            'from importlib import import_module\nload = import_module\nload("helper")',
            'from importlib import import_module as im\na = im\nb = a\nb("helper")',
            'import importlib as il\nload: object = il.import_module',
            'import importlib\n(load := importlib.import_module)("helper")',
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertIn("新源码闭包不支持动态Python代码加载", self.check(text))

    def test_callback_container_and_default_argument_references(self):
        cases = [
            'import importlib\ncallbacks = [importlib.import_module]',
            'import importlib\ncallbacks = {"load": importlib.import_module}',
            'import importlib\nobj.loader = importlib.import_module',
            'from importlib import import_module as load\nf(load)',
            'import importlib\ndef f(load=importlib.import_module):\n    return load("helper")',
            'import importlib\ndef f():\n    return importlib.import_module',
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertTrue(self.check(text))

    def test_namespace_aliases_and_reflection_fail_closed(self):
        cases = [
            'import importlib\nil = importlib\ngetattr(il, "import_module")("helper")',
            'import importlib\ngetattr(importlib, name)("helper")',
            'import importlib\nimportlib.__dict__["import_module"]("helper")',
            'import builtins\nvars(builtins)["__import__"]("helper")',
            '__builtins__["__import__"]("helper")',
            'import os\nmodule = os\nmodule.system("echo synthetic")',
            'from os import *\nf = system',
            'from subprocess import *\nf = run',
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertTrue(self.check(text))

    def test_alternative_loaders_and_builtins_are_not_proven_sources(self):
        cases = [
            'f = __import__', 'f = eval', 'f = exec',
            'import runpy\nf = runpy.run_path',
            'from runpy import run_module as runner\nf = runner',
            'import importlib.util\nf = importlib.util.spec_from_file_location',
            'from importlib.machinery import SourceFileLoader as Loader\nf = Loader',
            'import importlib\nf = importlib.reload',
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertTrue(self.check(text))

    def test_process_launch_references_are_rejected_before_aliasing(self):
        for text in ('import subprocess\nf = subprocess.run',
                     'from subprocess import run as launch\nf = launch',
                     'import os\nf = os.system', 'import os as fs\nf = fs.popen',
                     'import matlab.engine\nf = matlab.engine.start_matlab'):
            with self.subTest(text=text):
                self.assertIn("求解阶段不支持shell/跨后端进程启动", self.check(text))

    def test_sibling_import_cannot_erase_an_unsafe_origin(self):
        text = ('def unsafe():\n    from subprocess import run as action\n    f = action\n'
                'def safe():\n    from math import sin as action\n    return action(0)\n')
        self.assertTrue(self.check(text))

    def test_static_imports_numerical_aliases_and_text_are_preserved(self):
        text = ('import os.path\nfrom math import sin as wave\nimport importlib.metadata as metadata\n'
                'f = wave\nvalues = list(map(f, [0.0]))\np = os.path.join("a", "b")\n'
                'version = metadata.version("numpy")\n'
                '# load = importlib.import_module\nmessage = "eval exec import_module"\n')
        self.assertEqual(self.check(text), [])

    def test_declared_helper_and_entry_both_use_the_shared_gate(self):
        fixture = source_fixtures.SolverBackendSourceClosureTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        helper = fixture.write("问题一求解/helper.py", 'import importlib\nload = importlib.import_module\n')
        source, config = fixture.source("python", "import helper", [helper])
        self.assertTrue(STAGE.dependency_reference_issues(fixture.root, source, config))
        self.assertTrue(DELIVERY.validate_script(fixture.root, source)[0])
        self.assertTrue(STAGE.validate_stage_binding(fixture.root, fixture.binding(source, config),
                                                    "primary", require_validated=True))
        helper.write_text("from math import sqrt\ncalculate = sqrt\n", encoding="utf-8")
        source, config = fixture.source("python", "import helper", [helper])
        self.assertEqual(DELIVERY.validate_script(fixture.root, source)[0], [])
        self.assertEqual(STAGE.validate_stage_binding(fixture.root, fixture.binding(source, config),
                                                      "primary", require_validated=True), [])

    def test_original_delivery_and_historical_workbook_reject_even_with_matching_hashes(self):
        fixture = workbook_fixtures.SolverBackendTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        config = fixture.config()
        source = fixture.source(config, 'import importlib\nload = importlib.import_module\n')
        entry = fixture.entry(source, config, accepted=True)
        state = fixture.state(entry)
        book = fixture.primary_workbook(source, config, entry["solver_execution"]["primary"]["bundle_sha256"])
        before = deepcopy(state)
        self.assertTrue(DELIVERY.validate_script(fixture.root, source)[0])
        for validated in (False, True):
            self.assertTrue(STAGE.validate_stage_binding(fixture.root, entry, "primary", require_validated=validated))
        self.assertTrue(any("动态Python" in row for row in RECEIPT.validate_one(fixture.root, book, state, False)))
        self.assertEqual(before, state)

    def test_old_protocol_binding_is_not_silently_migrated(self):
        fixture = workbook_fixtures.SolverBackendTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        config = fixture.config(run_receipt_protocol_version="1.0.0")
        source = fixture.source(config, "import importlib\nload = importlib.import_module\n")
        entry = {"code": source.relative_to(fixture.root).as_posix(), "primary_code_sha256": file_hash(source)}
        self.assertEqual(STAGE.validate_stage_binding(fixture.root, entry, "primary"), [])


class PythonExecutionDownstreamTests(unittest.TestCase):
    def rebind_historical_fixture(self, root, state, stage="primary", *, unsafe=True):
        """Record bytes as an old checker could; never call it a new acceptance."""
        entry = state["subproblems"]["Q1"]
        field = "code" if stage == "primary" else "result_analysis_code"
        code = root / entry[field]
        text = code.read_text(encoding="utf-8")
        if unsafe:
            text += '\nimport importlib\nload = importlib.import_module\n'
        code.write_text(text, encoding="utf-8")
        _, config = STAGE.parse_stage_config(code)
        fingerprint = STAGE.stage_code_fingerprint(root, code, config.get("code_dependencies", []))
        entry[f"{stage}_code_sha256"] = fingerprint["entry_sha256"]
        for name in ("artifact_hashes", "validated_artifact_hashes"):
            entry.setdefault(name, {})[f"{stage}_code"] = fingerprint["entry_sha256"]
        entry["solver_execution"][stage].update(bundle_sha256=fingerprint["bundle_sha256"],
                                               validated_bundle_sha256=fingerprint["bundle_sha256"])
        save_state(root, state)
        return code, config

    def test_sync_read_and_write_invalidate_without_rebinding(self):
        for stage in ("primary", "analysis"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                state = project_fixture(root, ("python",), analysis=True)
                if stage == "analysis":
                    stage_fixture(root, state["subproblems"]["Q1"], "Q1", "python", "analysis", ["input.json"])
                self.rebind_historical_fixture(root, state, stage)
                expected = deepcopy(state["subproblems"]["Q1"])
                before = (root / "state/project_state.yaml").read_bytes()
                report = SYNC.synchronize(root)
                self.assertEqual(before, (root / "state/project_state.yaml").read_bytes())
                self.assertIn(stage + "_code_changed", [row["event"] for row in report["state_transitions"]])
                SYNC.synchronize(root, write=True)
                after = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))["subproblems"]["Q1"]
                # Execution is historical evidence; quality + typed stale govern
                # current consumability under the existing transition Authority.
                quality = "result_quality_status" if stage == "primary" else "result_analysis_status"
                self.assertEqual(after[quality], "pending")
                layer = "solution_workbook" if stage == "primary" else "result_analysis_workbook"
                self.assertIn(layer, after["stale_layers"])
                for field in ("solver_execution", "primary_code_sha256", "analysis_code_sha256", "validated_artifact_hashes"):
                    self.assertEqual(after[field], expected[field])
                if stage == "analysis":
                    self.assertEqual(after["primary_execution_status"], "accepted")
                else:
                    self.assertNotEqual(after["analysis_execution_status"], "accepted")

    def test_reproducibility_package_rejects_old_unsafe_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = project_fixture(root, ("python",))
            self.rebind_historical_fixture(root, state)
            package_fixture(root, state)
            self.assertTrue(any("动态Python" in row for row in reproducibility_requirements(root, state)[1]))
            report = VALIDATOR.validate_package(root, archive(root))
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any("动态Python" in row for row in report["issues"]))

    def test_static_helper_complete_package_passes_but_missing_helper_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = project_fixture(root, ("python",))
            entry = state["subproblems"]["Q1"]
            code = root / entry["code"]
            _, config = STAGE.parse_stage_config(code)
            helper = code.parent / "helper.py"
            helper.write_text("FACTOR = 1.0\n", encoding="utf-8")
            relative = helper.relative_to(root).as_posix()
            config["code_dependencies"] = [{"path": relative, "sha256": file_hash(helper)}]
            code.write_text("RUN_CONFIG = " + repr(config) + "\nimport helper\ndef solve_fixture():\n    return 3 * helper.FACTOR\n", encoding="utf-8")
            self.rebind_historical_fixture(root, state, unsafe=False)
            package_fixture(root, state)
            required, issues = reproducibility_requirements(root, state)
            self.assertEqual(issues, [])
            self.assertIn(relative, required)
            self.assertEqual(VALIDATOR.validate_package(root, archive(root))["status"], "passed")
            report = VALIDATOR.validate_package(root, archive(root, omit=[relative]))
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any("helper.py" in row for row in report["issues"]))
            helper.write_text("FACTOR = 2.0\n", encoding="utf-8")
            self.assertTrue(STAGE.validate_stage_binding(root, entry, "primary", require_validated=True))

    def test_runtime_does_not_promote_old_unsafe_primary_to_analysis(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            legacy_primary_project(root, analysis_backend="python")
            state = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
            fixture = workbook_fixtures.SolverBackendTests()
            fixture.root = root
            config = fixture.config()
            fixture.source(config, "import importlib\nload = importlib.import_module\n")
            entry = state["subproblems"]["Q1"]
            entry["solver_execution"]["primary"] = {"backend": "python", "selection_reason": "historical fixture"}
            self.rebind_historical_fixture(root, state, unsafe=False)
            before = (root / "state/project_state.yaml").read_bytes()
            plan = resolve_runtime("result_analysis", project_root=root, question="Q1", solver_backend="auto")
            self.assertNotIn("modules/03_result_analysis.md", plan["modules"])
            self.assertIn("modules/03_solve_validate.md", plan["modules"])
            self.assertIn("动态Python", json.dumps(plan, ensure_ascii=False))
            self.assertEqual(before, (root / "state/project_state.yaml").read_bytes())


if __name__ == "__main__":
    unittest.main()
