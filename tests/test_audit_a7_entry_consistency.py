from __future__ import annotations

import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import lint_skill_checks as lint
import resolve_runtime as runtime


def frontmatter(path):
    return yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1])


class TestA7EntryConsistency(unittest.TestCase):
    def run_plan(self, root, **arguments):
        state = {
            "project": {"competition": "CUMCM"},
            "subproblems": {"Q1": {
                "classification": {"objective": "optimization", "structures": ["stochastic", "temporal"]},
                "capabilities": {"requires_convergence_diagnostic": True, "requires_uncertainty_quantification": True},
            }},
        }
        (root / "state").mkdir(exist_ok=True)
        (root / "state/project_state.yaml").write_text(yaml.safe_dump(state), encoding="utf-8")
        return runtime.resolve_runtime("problem_analysis", project_root=root, question="Q1", **arguments)

    def test_partial_explicit_classification_reports_conflict_and_preserves_other_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = self.run_plan(Path(tmp), objective="prediction")
        self.assertEqual(plan["classification"]["objective"], "prediction")
        self.assertEqual(set(plan["classification"]["structures"]), {"stochastic", "temporal"})
        self.assertEqual(len(plan["classification"]["capabilities"]), 2)
        self.assertEqual(plan["assurance"]["status"], "review_required")
        self.assertTrue(any("objective" in value for value in plan["assurance"]["context"]["conflicts"]))

    def test_explicit_sets_can_change_or_clear_without_dropping_unspecified_axes(self):
        with tempfile.TemporaryDirectory() as tmp:
            for arguments, field in (({"structures": ["network"]}, "structures"),
                                     ({"capabilities": []}, "capabilities"),
                                     ({"structures": []}, "structures")):
                with self.subTest(arguments=arguments):
                    plan = self.run_plan(Path(tmp), **arguments)
                    self.assertEqual(plan["classification"]["objective"], "optimization")
                    self.assertTrue(any(field in value for value in plan["assurance"]["context"]["conflicts"]))
                    actual = plan["classification"]["capabilities"] if field == "capabilities" else plan["classification"][field]
                    self.assertEqual(actual, arguments[field])

    def test_equal_sets_and_competition_alias_do_not_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = self.run_plan(Path(tmp), competition="国赛", objective="optimization",
                structures=["temporal", "stochastic"],
                capabilities=["requires_uncertainty_quantification", "requires_convergence_diagnostic"])
            self.assertEqual(plan["assurance"]["context"]["conflicts"], [])
            plan = self.run_plan(Path(tmp), competition="MCM")
            self.assertTrue(any("competition" in value for value in plan["assurance"]["context"]["conflicts"]))

    def test_legacy_labels_are_compared_after_mapping_and_keep_capabilities(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = self.run_plan(Path(tmp), primary="prediction")
            equivalent = self.run_plan(Path(tmp), primary="optimization", secondary=["prediction", "simulation"])
        self.assertEqual(plan["classification"]["objective"], "prediction")
        self.assertEqual(plan["classification"]["structures"], ["temporal"])
        self.assertEqual(len(plan["classification"]["capabilities"]), 2)
        self.assertTrue(plan["assurance"]["context"]["conflicts"])
        self.assertEqual(equivalent["assurance"]["context"]["conflicts"], [])

    def test_generators_are_consumed_once(self):
        plan = runtime.resolve_runtime("problem_analysis",
            structures=iter(["stochastic"]), capabilities=iter(["requires_convergence_diagnostic"]))
        self.assertEqual(plan["classification"]["structures"], ["stochastic"])
        self.assertEqual(plan["classification"]["capabilities"], ["requires_convergence_diagnostic"])

    def test_multi_question_scope_compares_sets_but_does_not_merge_different_classifications(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_plan(root)
            path = root / "state/project_state.yaml"
            state = yaml.safe_load(path.read_text())
            state["subproblems"]["Q2"] = copy.deepcopy(state["subproblems"]["Q1"])
            state["subproblems"]["Q2"]["classification"]["structures"].reverse()
            path.write_text(yaml.safe_dump(state))
            plan = runtime.resolve_runtime("problem_analysis", project_root=root)
            self.assertFalse(plan["assurance"]["context"]["ambiguities"])
            state["subproblems"]["Q2"]["classification"]["objective"] = "prediction"
            path.write_text(yaml.safe_dump(state))
            plan = runtime.resolve_runtime("problem_analysis", project_root=root, objective="simulation")
            self.assertEqual(plan["classification"]["objective"], "simulation")
            self.assertTrue(plan["assurance"]["context"]["ambiguities"])
            self.assertEqual(plan["assurance"]["status"], "review_required")

    def test_entrypoints_have_host_fields_and_preserved_metadata(self):
        paths = [ROOT / "SKILL.md", ROOT / "skills/mathmodel-skill/SKILL.md"]
        self.assertEqual(paths[0].read_bytes(), paths[1].read_bytes())
        data = frontmatter(paths[0])
        self.assertFalse(set(data) - {"name", "description", "license", "allowed-tools", "metadata"})
        self.assertIsInstance(data.get("description"), str)
        self.assertTrue(0 < len(data["description"].strip()) <= 1024)
        self.assertNotRegex(data["description"], r"[<>]|\[TODO:")
        self.assertTrue({"version", "summary", "triggers"}.issubset(data["metadata"]))
        self.assertIn("数学建模", data["metadata"]["triggers"])

    def test_entrypoint_shared_paths_resolve_in_the_copied_plugin_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = ("SKILL.md", "skills/mathmodel-skill/SKILL.md", ".codex-plugin/plugin.json",
                     "core/bootstrap.yaml", "scripts/resolve_runtime.py", "core/workflow_router.yaml")
            for relative in paths:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, target)
            for entry, base in ((root / "SKILL.md", root),
                                (root / "skills/mathmodel-skill/SKILL.md", root / "skills/mathmodel-skill/../..")):
                self.assertTrue(entry.is_file())
                self.assertTrue((base / ".codex-plugin/plugin.json").is_file())
                bootstrap = yaml.safe_load((base / "core/bootstrap.yaml").read_text(encoding="utf-8"))
                self.assertTrue((base / bootstrap["startup_contract"]["resolver"]).is_file())
                self.assertTrue((base / bootstrap["authoritative_sources"]["routing"]).is_file())

    def test_fallback_validation_projection_stays_aligned_with_authority(self):
        path = ROOT / "templates/code/hsk_pipeline/result_io.py"
        spec = importlib.util.spec_from_file_location("a7_result_io", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        canonical = yaml.safe_load((ROOT / "core/workbook_schema.yaml").read_text(encoding="utf-8"))
        fallback = module._FALLBACK_SCHEMA
        for kind in ("solution", "result_analysis"):
            full_required, full_sheets = module.WORKBOOK_VALIDATION._required_sheet_schemas(canonical, kind)
            copied_required, copied_sheets = module.WORKBOOK_VALIDATION._required_sheet_schemas(fallback, kind)
            self.assertEqual(full_required, copied_required)
            self.assertEqual({key: value.get("required_columns", []) for key, value in full_sheets.items()},
                             {key: value.get("required_columns", []) for key, value in copied_sheets.items()})
        for field in ("objective_profiles", "structure_profiles", "task_profiles"):
            def requirements(schema):
                return {key: value["required_any"] for key, value in schema["solution_workbook"][field].items()
                        if isinstance(value, dict) and value.get("required_any")}
            self.assertEqual(requirements(canonical), requirements(fallback))
        for field in ("allowed", "required_sheets"):
            self.assertEqual(canonical["capability_contract"][field], fallback["capability_contract"][field])
        for field in ("problem_types", "required_sheets"):
            self.assertEqual(canonical["capability_contract"]["legacy_problem_type_fallback"][field],
                             fallback["capability_contract"]["legacy_problem_type_fallback"][field])
        self.assertEqual(canonical["result_analysis_workbook"]["required_any_sheets"],
                         fallback["result_analysis_workbook"]["required_any_sheets"])

    def test_entry_lint_rejects_missing_or_placeholder_description(self):
        original = lint.read_text
        for description in (None, "", "[TODO: write description]", 123):
            with self.subTest(description=description):
                def modified(path):
                    text = original(path)
                    if Path(path).name != "SKILL.md":
                        return text
                    data = yaml.safe_load(text.split("---", 2)[1])
                    if description is None:
                        data.pop("description", None)
                    else:
                        data["description"] = description
                    return "---\n" + yaml.safe_dump(data, allow_unicode=True) + "---" + text.split("---", 2)[2]
                errors = []
                with patch.object(lint, "read_text", side_effect=modified):
                    lint.check_skill_entrypoint_parity(errors)
                self.assertTrue(any("description" in error for error in errors), errors)

    def test_prose_pointers_delegate_to_protocol(self):
        for name in ("packs/artifact/algorithm_flow.md", "templates/writing/caption_explanation.md"):
            self.assertIn("modules/05_writing/paper_writing_protocol.md", (ROOT / name).read_text(encoding="utf-8"))

    def test_standalone_support_package_matches_canonical_workbook_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = ROOT / "templates/code/hsk_pipeline"
            for name in ("result_io.py", "workbook_validation.py"):
                shutil.copy2(source / name, root / name)
            # Separate process, outside the repository with no schema environment fallback.
            probe = root / "probe.py"
            probe.write_text('''import copy, json, sys
from pathlib import Path
import result_io as io
canonical = io.load_workbook_schema(Path(sys.argv[1]))
assert io.load_workbook_schema() is io._FALLBACK_SCHEMA
def tables(kind):
    section = canonical[kind + "_workbook"]
    result = {name: [{column: (True if column == "是否通过" else "fixture") for column in spec["required_columns"]}]
              for name, spec in section["common_required_sheets"].items()}
    if kind == "result_analysis":
        result["参数敏感性"] = [{"参数": "p", "基准值": 1, "变化值": 2, "结果指标": 3}]
    return result
cases = []
for kind in ("solution", "result_analysis"):
    good = tables(kind)
    cases.append((kind, good, {}, True))
    missing = copy.deepcopy(good); missing.pop("运行配置")
    cases.append((kind, missing, {}, False))
    bad = copy.deepcopy(good); bad["运行配置"] = [{"项目": "fixture"}]
    cases.append((kind, bad, {}, False))
analysis = tables("result_analysis")
cases.append(("robustness", analysis, {}, True))
extra = copy.deepcopy(analysis); extra["unknown"] = [{"x": 1}]
cases.append(("result_analysis", extra, {}, False))
empty = copy.deepcopy(analysis); empty.pop("参数敏感性")
cases.append(("result_analysis", empty, {}, False))
for label, spec in canonical["solution_workbook"]["task_profiles"].items():
    if not isinstance(spec, dict): continue
    base = tables("solution")
    cases.append(("solution", base, {"problem_types": [label]}, False))
    sheet = spec["required_any"][0]
    columns = canonical["solution_workbook"]["common_recommended_sheets"][sheet]["required_columns"]
    base = copy.deepcopy(base); base[sheet] = [{column: "fixture" for column in columns}]
    cases.append(("solution", base, {"problem_types": [label]}, True))
outcomes = []
for index, (kind, values, options, expected) in enumerate(cases):
    outcomes_pair = []
    for mode, schema in (("canonical", Path(sys.argv[1])), ("fallback", None)):
        target = Path(str(index) + mode + ".xlsx")
        try:
            io.write_workbook(target, values, workbook_kind=kind, schema_path=schema, **options)
            io.validate_workbook_file(target, kind, schema_path=schema, **options)
            passed = True
        except ValueError:
            passed = False
        outcomes_pair.append(passed)
    assert outcomes_pair == [expected, expected], (index, kind, options, outcomes_pair, expected)
    outcomes.append(outcomes_pair)
print(json.dumps(outcomes))
''', encoding="utf-8")
            env = {key: value for key, value in os.environ.items() if key not in {"HSK_WORKBOOK_SCHEMA", "PYTHONPATH"}}
            result = subprocess.run([sys.executable, "-B", str(probe), str(ROOT / "core/workbook_schema.yaml")],
                cwd=root, env=env, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertGreaterEqual(len(json.loads(result.stdout)), 19)


if __name__ == "__main__":
    unittest.main()

