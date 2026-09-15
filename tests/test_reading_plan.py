from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import reading_plan as READING
from resolve_runtime import resolve_runtime
from reading_plan_cases import CASES, build_project


def tree_hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


class SelectorTests(unittest.TestCase):
    def describe(self, text, **selectors):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "source.md").write_bytes(text.encode("utf-8"))
            return READING.SourceReader(root).describe({"path": "source.md", **selectors})

    def test_markdown_keeps_applicability_not_siblings(self):
        text = "# Title\nGlobal applicability.\n## Parent\nOnly for scoped data.\n### Keep\n中文\n### Other\nDo not select.\n## End\nEnd.\n"
        row = self.describe(text, headings=["### Keep"])
        self.assertEqual(row["resolution"], "exact")
        selected = "".join("".join(text.splitlines(keepends=True)[a-1:b]) for a, b in row["ranges"])
        self.assertIn("Global applicability", selected)
        self.assertIn("Only for scoped data", selected)
        self.assertIn("中文", selected)
        self.assertNotIn("Do not select", selected)
        self.assertEqual(row["planned_bytes"], len(selected.encode("utf-8")))

    def test_fenced_fake_headings_do_not_break_real_selector(self):
        text = "# A\n## Target\n```text\n## Target\n```\n~~~\n## Other\n~~~\nbody\n## End\nend\n"
        row = self.describe(text, headings=["## Target"])
        self.assertEqual(row["resolution"], "exact")
        self.assertLess(row["planned_bytes"], row["source_bytes"])

    def test_missing_duplicate_or_empty_selectors_expand_whole_file(self):
        for text, selectors in (("# A\n## B\nx\n", ["## missing"]),
                                ("# A\n## B\nx\n## B\ny\n", ["## B"]),
                                ("# A\n## B\nx\n", [])):
            with self.subTest(selectors=selectors):
                row = self.describe(text, headings=selectors)
                self.assertEqual(row["resolution"], "whole_file_fallback")
                self.assertEqual(row["planned_bytes"], row["source_bytes"])

    def test_yaml_exact_subtree_and_parent_keys(self):
        text = "version: 1\nparent:\n  chosen:\n    a: 中文\n  other: 2\n"
        row = self.describe(text, yaml_paths=["parent.chosen"])
        selected = "".join("".join(text.splitlines(keepends=True)[a-1:b]) for a, b in row["ranges"])
        self.assertIn("parent:", selected)
        self.assertIn("a: 中文", selected)
        self.assertNotIn("other", selected)

    def test_yaml_alias_duplicates_and_bad_paths_expand(self):
        for text in ("a: &a {x: 1}\nb: *a\n", "a: 1\na: 2\n", "a: [1, 2]\n"):
            with self.subTest(text=text):
                row = self.describe(text, yaml_paths=["a.x"])
                self.assertEqual(row["resolution"], "whole_file_fallback")

    def test_crlf_unicode_and_overlap_count_actual_utf8_union(self):
        text = "# A\r\n## B\r\n中文\r\n### C\r\n文\r\n## D\r\nx\r\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.md").write_bytes(text.encode("utf-8"))
            reader = READING.SourceReader(root)
            rows = reader.consolidate([reader.describe({"path": "a.md", "headings": [h]})
                                       for h in ("## B", "### C", "## B")])
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["planned_bytes"], len(text.split("## D")[0].encode("utf-8")))

    def test_missing_or_escaping_sources_never_become_empty_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            outside = Path(tmp) / "outside"
            outside.write_text("not in repo")
            reader = READING.SourceReader(root)
            with self.assertRaises(FileNotFoundError):
                reader.describe({"path": "missing"})
            with self.assertRaises(ValueError):
                reader.describe({"path": "../outside"})
            (root / "link").symlink_to(outside)
            with self.assertRaises(ValueError):
                reader.describe({"path": "link"})


class ReadingPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plans = {}
        for identifier, intent, request, fixture in CASES:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                kwargs = {"competition": "CUMCM", "request": request}
                if fixture:
                    build_project(ROOT, root, fixture)
                    before = tree_hashes(root)
                    kwargs.update(project_root=root, question="Q1")
                plan = resolve_runtime(intent, **kwargs)
                if fixture and before != tree_hashes(root):
                    raise AssertionError("Resolver wrote to synthetic project")
                cls.plans[identifier] = plan

    def test_verified_facts_and_style_are_narrow(self):
        for case, profile in (("facts_current", "framework_result_sync"), ("style_current", "figure_style")):
            with self.subTest(case=case):
                reading = self.plans[case]["reading_plan"]
                self.assertEqual(reading["profile"], profile)
                self.assertEqual(reading["status"], "planned")
                self.assertGreater(reading["metrics"]["planned_project_read_bytes"], 0)

    def test_unscoped_ambiguous_changed_and_stale_never_take_shortcut(self):
        for case in ("facts_unscoped", "facts_model_change", "facts_ambiguous", "facts_stale_framework",
                     "facts_hash_drift", "facts_identity_drift", "facts_stale_dependency", "style_unscoped",
                     "style_data_change", "style_figure_drift", "style_no_approval", "mixed"):
            with self.subTest(case=case):
                self.assertEqual(self.plans[case]["reading_plan"]["profile"], "full")

    def test_machine_closure_and_gates_preserved_exactly(self):
        for identifier, plan in self.plans.items():
            with self.subTest(case=identifier):
                reading = plan["reading_plan"]
                self.assertEqual(reading["machine_dependencies"], plan["assurance"]["dependency_closure"])
                self.assertEqual(reading["authority_fingerprint"], plan["assurance"]["authority_fingerprint"])
                tools = {row["name"]: row for row in reading["tool_interfaces"]}
                for gate in plan["pre_delivery_gates"]:
                    self.assertEqual({k: tools[gate["name"]][k] for k in gate}, gate)
                self.assertIsNone(reading["metrics"]["actual_read_tokens"])
                self.assertIsNone(reading["metrics"]["actual_read_bytes"])

    def test_tool_routes_do_not_preload_implementation(self):
        for case in ("project_sync", "receipt"):
            reading = self.plans[case]["reading_plan"]
            self.assertTrue(reading["tool_interfaces"])
            self.assertFalse(any(r["path"].endswith(".py") for r in reading["read_now"]))
            self.assertTrue(any(r["path"].endswith(".py") for r in reading["conditional"]))

    def test_new_figure_keeps_selection_and_enhancement_available(self):
        reading = self.plans["new_field"]["reading_plan"]
        paths = {r["path"] for r in reading["read_now"]}
        self.assertNotIn("templates/figure/figure_enhancement_patterns.md", paths)
        for path in ("templates/figure/chart_selection.md", "templates/figure/figure_enhancement_patterns.md"):
            self.assertTrue(any(r["path"] == path and r["when"] for r in reading["conditional"]))

    def test_progressive_writing_delegates_existing_preflight(self):
        plan = self.plans["cumcm_writing"]
        self.assertEqual(plan["reading_plan"]["delegated_writing_sequence"], plan["writing_runtime"])
        self.assertEqual(plan["writing_runtime"]["execution_mode"], "template_first_progressive_authoring")

    def test_all_configured_selectors_match_current_sources(self):
        for identifier, plan in self.plans.items():
            with self.subTest(case=identifier):
                for row in plan["reading_plan"]["read_now"]:
                    self.assertEqual(row["resolution"], "exact", row["fallback_reason"])

    def test_read_projection_does_not_mutate_input_plan(self):
        plan = deepcopy(self.plans["new_field"])
        before = deepcopy(plan)
        router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text())
        manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text())
        READING.build_reading_plan(ROOT, plan, router, manifest)
        self.assertEqual(plan, before)

    def test_missing_profile_falls_back_and_unknown_schema_errors(self):
        plan = self.plans["new_field"]
        router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text())
        manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text())
        del router["reading_policy"]["profiles"]["figure_design"]
        self.assertEqual(READING.build_reading_plan(ROOT, plan, router, manifest)["profile"], "full")
        router["reading_policy"]["schema_version"] = "999"
        with self.assertRaises(ValueError):
            READING.build_reading_plan(ROOT, plan, router, manifest)

    def test_legacy_name_declarations_never_qualify_as_verified(self):
        plan = resolve_runtime("framework_sync", request="仅同步已验收结果摘要，不修改模型。",
                               available_artifacts=["locked_model_spec", "accepted_solution_workbook"])
        self.assertEqual(plan["reading_plan"]["profile"], "full")


if __name__ == "__main__":
    unittest.main()
