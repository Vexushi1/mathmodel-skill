"""Regression tests for source identities that previously missed real code changes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_config_parser as CONFIG
import stage_code as STAGE
import validate_code_delivery as DELIVERY


class SolverBackendSourceClosureTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.folder = self.root / "问题一求解"
        self.folder.mkdir()
        self.write("state/project_state.yaml", yaml.safe_dump({"preprocessing": {"decision": "not_needed"}}))

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def source(self, backend, body, dependencies=()):
        state_path = self.root / "state/project_state.yaml"
        state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        state["execution"] = {"solver_backend": backend,
                              "solver_backend_selection_reason": "Synthetic whole-project source-closure fixture"}
        state_path.write_text(yaml.safe_dump(state, allow_unicode=True), encoding="utf-8")
        from artifact_fingerprint import combined_hash
        data = self.root / "input.json"
        if not data.exists():
            data.write_text("{}", encoding="utf-8")
        config = {"stage": "primary", "problem_name": "问题一", "solver_backend": backend,
                  "data_paths": ["input.json"], "data_sha256": combined_hash([data], self.root), "solver": "direct",
                  "random_seed": 2026, "tolerance": 1e-8, "iteration_or_time_limit": "direct",
                  "expected_workbook": "问题一求解结果.xlsx", "run_receipt_protocol_version": "1.1.0",
                  "primary_quality_protocol_version": "1.0.0",
                  "code_dependencies": [{"path": path.relative_to(self.root).as_posix(),
                                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                                        for path in dependencies]}
        if backend == "python":
            text = f"RUN_CONFIG = {config!r}\n{body}\ndef main():\n    return 0\nif __name__ == '__main__':\n    main()\n"
            name = "问题一求解.py"
        else:
            literal = json.dumps(config, ensure_ascii=False).replace("'", "''")
            text = "function q1_solver()\nRUN_CONFIG = jsondecode('" + literal + "');\n" + body
            name = "q1_solver.m"
        return self.write("问题一求解/" + name, text), config

    def binding(self, source, config):
        fingerprint = STAGE.stage_code_fingerprint(self.root, source, config["code_dependencies"])
        return {"code": source.relative_to(self.root).as_posix(), "primary_code_sha256": fingerprint["entry_sha256"],
                "solver_execution": {"primary": {"bundle_sha256": fingerprint["bundle_sha256"],
                                                 "validated_bundle_sha256": fingerprint["bundle_sha256"]}}}

    def references(self, source, config):
        return STAGE.dependency_reference_issues(self.root, source, config)

    def package(self, calculation="from ..constants import VALUE\nvalue = VALUE\n"):
        paths = [self.write("问题一求解/pkg/__init__.py", ""),
                 self.write("问题一求解/pkg/sub/__init__.py", ""),
                 self.write("问题一求解/pkg/sub/calculation.py", calculation)]
        constants = self.write("问题一求解/pkg/constants.py", "VALUE = 1\n")
        return paths, constants

    def test_parent_relative_import_changes_real_output_and_is_rejected_until_declared(self):
        declared, constants = self.package()
        source, config = self.source("python", "from pkg.sub.calculation import value\nprint(value)", declared)
        self.assertIn("项目Python依赖未声明: 问题一求解/pkg/constants.py", self.references(source, config))
        self.assertTrue(DELIVERY.validate_script(self.root, source)[0])
        source, config = self.source("python", "from pkg.sub.calculation import value\nprint(value)", [*declared, constants])
        self.assertEqual(DELIVERY.validate_script(self.root, source)[0], [])
        entry = self.binding(source, config)
        command = [sys.executable, "-B", str(source)]
        self.assertEqual(subprocess.check_output(command, text=True).strip(), "1")
        constants.write_text("VALUE = 999\n", encoding="utf-8")
        self.assertEqual(subprocess.check_output(command, text=True).strip(), "999")
        self.assertTrue(STAGE.validate_stage_binding(self.root, entry, "primary", require_validated=True,
                                                     project_backend="python"))

    def test_single_level_relative_import_and_from_dot_alias_are_resolved(self):
        for statement in ("from .constants import VALUE", "from . import constants"):
            with self.subTest(statement=statement):
                init = self.write("问题一求解/pkg/__init__.py", "")
                helper = self.write("问题一求解/pkg/helper.py", statement + "\n")
                constants = self.write("问题一求解/pkg/constants.py", "VALUE = 1\n")
                source, config = self.source("python", "import pkg.helper", [init, helper])
                self.assertTrue(any("pkg/constants.py" in issue for issue in self.references(source, config)))
                source, config = self.source("python", "import pkg.helper", [init, helper, constants])
                self.assertEqual(self.references(source, config), [])

    def test_multilevel_relative_module_requires_each_package_initializer(self):
        declared, constants = self.package("from ...shared.values import VALUE\n")
        deep = self.write("问题一求解/pkg/sub/deep/__init__.py", "")
        calculation = self.write("问题一求解/pkg/sub/deep/calculation.py", "from ...shared.values import VALUE\n")
        shared = self.write("问题一求解/pkg/shared/__init__.py", "")
        values = self.write("问题一求解/pkg/shared/values.py", "VALUE = 1\n")
        dependencies = [declared[0], declared[1], deep, calculation, values]
        source, config = self.source("python", "import pkg.sub.deep.calculation", dependencies)
        self.assertTrue(any("pkg/shared/__init__.py" in issue for issue in self.references(source, config)))
        source, config = self.source("python", "import pkg.sub.deep.calculation", [*dependencies, shared])
        self.assertEqual(self.references(source, config), [])

    def test_relative_import_cannot_escape_its_top_level_package(self):
        declared, _ = self.package("from ...outside import VALUE\n")
        source, config = self.source("python", "import pkg.sub.calculation", declared)
        self.assertTrue(any("越出已知包" in issue for issue in self.references(source, config)))
        source, config = self.source("python", "from . import helper")
        self.assertTrue(any("越出已知包" in issue for issue in self.references(source, config)))

    def test_relative_import_from_package_initializer_includes_current_package(self):
        init = self.write("问题一求解/pkg/__init__.py", "from . import constants\n")
        constants = self.write("问题一求解/pkg/constants.py", "VALUE = 1\n")
        source, config = self.source("python", "import pkg", [init])
        self.assertTrue(any("constants.py" in issue for issue in self.references(source, config)))
        source, config = self.source("python", "import pkg", [init, constants])
        self.assertEqual(self.references(source, config), [])

    def test_installed_absolute_import_does_not_resolve_to_unrelated_helper_sibling(self):
        declared, _ = self.package("from collections import Counter\nimport math\n")
        self.write("问题一求解/pkg/sub/collections.py", "raise RuntimeError('not imported')\n")
        self.write("问题一求解/pkg/sub/math.py", "raise RuntimeError('not imported')\n")
        source, config = self.source("python", "import pkg.sub.calculation", declared)
        self.assertEqual(self.references(source, config), [])
        self.assertEqual(subprocess.run([sys.executable, "-B", str(source)], capture_output=True).returncode, 0)

    def test_absolute_project_import_in_nested_helper_uses_entry_directory(self):
        declared, _ = self.package("import shared\n")
        shared = self.write("问题一求解/shared.py", "VALUE = 1\n")
        source, config = self.source("python", "import pkg.sub.calculation", declared)
        self.assertTrue(any("求解/shared.py" in issue for issue in self.references(source, config)))
        source, config = self.source("python", "import pkg.sub.calculation", [*declared, shared])
        self.assertEqual(self.references(source, config), [])

    def test_matlab_bare_parenthesized_and_handle_references_require_helper(self):
        helper = self.write("问题一求解/helper.m", "function y = helper()\ny = 1;\nend\n")
        for body in ("value = helper;", "value = helper();", "f = @helper; value = f();", "helper;"):
            with self.subTest(body=body):
                source, config = self.source("matlab", body + "\nend\n")
                self.assertTrue(any("helper.m" in issue for issue in self.references(source, config)))
                self.assertTrue(DELIVERY.validate_script(self.root, source)[0])
                source, config = self.source("matlab", body + "\nend\n", [helper])
                self.assertEqual(DELIVERY.validate_script(self.root, source)[0], [])

    def test_matlab_declared_bare_call_helper_change_invalidates_binding(self):
        helper = self.write("问题一求解/helper.m", "function y = helper()\ny = 1;\nend\n")
        source, config = self.source("matlab", "value = helper;\nend\n", [helper])
        entry = self.binding(source, config)
        self.assertEqual(STAGE.validate_stage_binding(self.root, entry, "primary", require_validated=True,
                                                      project_backend="matlab"), [])
        helper.write_text("function y = helper()\ny = 999;\nend\n", encoding="utf-8")
        self.assertTrue(STAGE.validate_stage_binding(self.root, entry, "primary", require_validated=True,
                                                     project_backend="matlab"))

    def test_matlab_local_function_and_variable_precedence_do_not_capture_unrelated_file(self):
        self.write("问题一求解/helper.m", "function y = helper()\ny = 999;\nend\n")
        bodies = ("value = helper;\nend\nfunction value = helper()\nvalue = 1;\nend\n",
                  "helper = 1; value = helper;\nend\n",
                  "helper = [1,2]; value = helper(1);\nend\n",
                  "object.helper = 1; value = object.helper;\nend\n",
                  "f = @(helper) helper(1); value = f(1);\nend\n",
                  "value = local(1);\nend\nfunction value = local(helper)\nvalue = helper;\nend\n")
        for body in bodies:
            with self.subTest(body=body):
                source, config = self.source("matlab", body)
                self.assertEqual(self.references(source, config), [])

    def test_matlab_function_variable_scope_does_not_hide_another_function_reference(self):
        self.write("问题一求解/helper.m", "function y = helper()\ny = 1;\nend\n")
        body = "helper = 1; value = local();\nend\nfunction value = local()\nvalue = helper;\nend\n"
        source, config = self.source("matlab", body)
        self.assertTrue(any("helper.m" in issue for issue in self.references(source, config)))
        source, config = self.source("matlab", "helper = 1; f = @helper;\nend\n")
        self.assertTrue(any("helper.m" in issue for issue in self.references(source, config)))

    def test_matlab_bare_reference_before_assignment_is_not_hidden(self):
        self.write("问题一求解/helper.m", "function y = helper()\ny = 1;\nend\n")
        source, config = self.source("matlab", "value = helper; helper = 1;\nend\n")
        self.assertTrue(any("helper.m" in issue for issue in self.references(source, config)))

    def test_matlab_conditional_variable_and_anonymous_parameter_do_not_hide_outer_calls(self):
        self.write("问题一求解/helper.m", "function y = helper()\ny = 1;\nend\n")
        bodies = ("if false\nhelper = 1;\nend\nvalue = helper;\nend\n",
                  "values = {helper, @(helper) helper};\nend\n",
                  "values = {@(helper) helper, helper};\nend\n")
        for body in bodies:
            with self.subTest(body=body):
                source, config = self.source("matlab", body)
                self.assertTrue(any("helper.m" in issue for issue in self.references(source, config)))
        source, config = self.source("matlab", "if true\nhelper = 1; value = helper;\nend\nend\n")
        self.assertEqual(self.references(source, config), [])

    def test_matlab_project_package_and_private_are_explicitly_unverified(self):
        packaged = self.write("问题一求解/+pkg/helper.m", "function y = helper()\ny = 1;\nend\n")
        private = self.write("问题一求解/private/private_helper.m", "function y = private_helper()\ny = 1;\nend\n")
        for body, path in (("value = pkg.helper();", packaged), ("f = @pkg.helper;", packaged),
                           ("value = private_helper;", private)):
            for declared in ([], [path]):
                with self.subTest(body=body, declared=bool(declared)):
                    source, config = self.source("matlab", body + "\nend\n", declared)
                    self.assertTrue(any("尚未验证" in issue for issue in self.references(source, config)))

    def test_matlab_struct_field_with_package_name_is_not_a_package_call(self):
        self.write("问题一求解/+pkg/helper.m", "function y = helper()\ny = 1;\nend\n")
        source, config = self.source("matlab", "pkg = struct('helper',1); value = pkg.helper;\nend\n")
        self.assertEqual(self.references(source, config), [])

    def test_matlab_implicit_function_ends_are_flat_and_do_not_share_main_variables(self):
        helper = self.write("问题一求解/helper.m", "function y = helper()\ny = 999;\nend\n")
        body = "helper = 1;\nvalue = local();\nfunction y = local()\ny = helper;\n"
        source, config = self.source("matlab", body)
        entry = self.binding(source, config)
        self.assertTrue(any("helper.m" in issue for issue in self.references(source, config)))
        self.assertTrue(any("helper.m" in issue for issue in STAGE.validate_stage_binding(
            self.root, entry, "primary", require_validated=True, project_backend="matlab")))
        source, config = self.source("matlab", body, [helper])
        self.assertEqual(self.references(source, config), [])
        # Explicit nesting has different semantics: the nested function captures
        # the main function variable and does not call the same-named disk file.
        nested = "helper = 1;\nvalue = local();\nfunction y = local()\ny = helper;\nend\nend\n"
        source, config = self.source("matlab", nested)
        self.assertEqual(self.references(source, config), [])

    def test_matlab_command_arguments_are_literals_but_command_target_is_a_dependency(self):
        helper = self.write("问题一求解/helper.m", "function y = helper(varargin)\ny = 999;\nend\n")
        for command in ("disp helper", "disp 'helper'", 'disp "helper"', "disp helper.txt"):
            with self.subTest(command=command):
                source, config = self.source("matlab", command + "\nvalue = 1;\nend\n")
                self.assertEqual(self.references(source, config), [])
                self.assertEqual(STAGE.validate_stage_binding(self.root, self.binding(source, config),
                                                             "primary", require_validated=True,
                                                             project_backend="matlab"), [])
        source, config = self.source("matlab", "helper text\nend\n")
        self.assertTrue(any("helper.m" in issue for issue in self.references(source, config)))
        source, config = self.source("matlab", "helper text\nend\n", [helper])
        self.assertEqual(self.references(source, config), [])
        source, config = self.source("matlab", "disp(helper)\nend\n")
        self.assertTrue(any("helper.m" in issue for issue in self.references(source, config)))

    def test_matlab_persistent_and_global_declarations_establish_variables(self):
        self.write("问题一求解/helper.m", "function y = helper()\ny = 999;\nend\n")
        for declaration in ("persistent helper", "global helper", "persistent helper another"):
            with self.subTest(declaration=declaration):
                body = declaration + "\nif isempty(helper)\nhelper = 1;\nend\nvalue = helper;\nend\n"
                source, config = self.source("matlab", body)
                self.assertEqual(self.references(source, config), [])
                self.assertEqual(STAGE.validate_stage_binding(self.root, self.binding(source, config),
                                                             "primary", require_validated=True,
                                                             project_backend="matlab"), [])

    def test_new_config_incremental_assignment_and_deletion_are_rejected_in_all_scopes(self):
        for operation in ("RUN_CONFIG |= {'tolerance': 0.5}", "del RUN_CONFIG", "del RUN_CONFIG, unrelated"):
            for prefix in ("", "def change():\n    global RUN_CONFIG\n    "):
                with self.subTest(operation=operation, nested=bool(prefix)):
                    text = "RUN_CONFIG = {'run_receipt_protocol_version': '1.1.0', 'tolerance': 1e-8}\n" + prefix + operation + "\n"
                    with self.assertRaisesRegex(ValueError, "RUN_CONFIG禁止"):
                        CONFIG.parse_embedded_config(text, messages=CONFIG.DELIVERY_MESSAGES)

    def test_read_only_config_and_old_protocol_keep_existing_semantics(self):
        text = "RUN_CONFIG = {'run_receipt_protocol_version': '1.1.0', 'tolerance': 1e-8}\nvalue = RUN_CONFIG['tolerance']\n"
        self.assertEqual(CONFIG.parse_embedded_config(text, messages=CONFIG.DELIVERY_MESSAGES)[1]["tolerance"], 1e-8)
        for operation in ("RUN_CONFIG |= {'tolerance': 0.5}", "del RUN_CONFIG"):
            legacy = text.replace("1.1.0", "1.0.0") + operation + "\n"
            self.assertEqual(CONFIG.parse_embedded_config(legacy, messages=CONFIG.DELIVERY_MESSAGES)[1]["tolerance"], 1e-8)


if __name__ == "__main__":
    unittest.main()
