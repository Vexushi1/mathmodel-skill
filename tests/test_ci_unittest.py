"""Runner contracts use tiny synthetic suites, never rediscover the real suite."""
from __future__ import annotations

from contextlib import contextmanager
import copy
import io
from pathlib import Path
import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
import ci_unittest as CI


META = {"github_sha": "a" * 40, "checkout_sha": "b" * 40, "source_sha": "b" * 40,
        "python_version": "3.10", "python_full_version": "3.10.99", "runtime": {}}
PREFIX = "test_ci_fixture_"


@contextmanager
def synthetic_suite(sources):
    prior_path = list(sys.path)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        start = root / "tests"
        start.mkdir()
        for name, text in sources.items():
            (start / f"{PREFIX}{name}.py").write_text(textwrap.dedent(text), encoding="utf-8")
        try:
            yield root, start
        finally:
            sys.path[:] = prior_path
            for name in list(sys.modules):
                if name.startswith(PREFIX):
                    del sys.modules[name]


def run_synthetic(root, start, **kwargs):
    return CI.execute_collection(CI.discover_tests(root, start), metadata=META,
                                 stream=io.StringIO(), **kwargs)


def simple_module(count):
    methods = "\n".join(f"    def test_{number:02d}(self): self.assertEqual(1 + 1, 2)"
                        for number in range(count))
    return "import unittest\nclass Case(unittest.TestCase):\n" + methods + "\n"


class CiUnittestRunnerTests(unittest.TestCase):
    def test_lpt_plan_is_deterministic_and_keeps_whole_files(self):
        with synthetic_suite({"a": simple_module(7), "b": simple_module(5),
                              "c": simple_module(3), "d": simple_module(1)}) as (root, start):
            collection = CI.discover_tests(root, start)
            first = CI.assign_files(collection.entries, 4)
            second = CI.assign_files(list(reversed(collection.entries)), 4)
            self.assertEqual(first, second)
            self.assertEqual(set(first.values()), {0, 1, 2, 3})
            self.assertEqual(first["tests/test_ci_fixture_a.py"], 0)

    def test_shards_form_the_full_discovery_union_without_overlap(self):
        with synthetic_suite({name: simple_module(count) for name, count in
                              (("a", 7), ("b", 5), ("c", 3), ("d", 1), ("e", 2))}) as (root, start):
            reports = [run_synthetic(root, start, shard_index=index, shard_count=4)
                       for index in range(4)]
            full = reports[0]["full_ids"]
            union = [case_id for report in reports for case_id in report["executed_ids"]]
            self.assertEqual(sorted(full), sorted(union))
            self.assertEqual(len(union), len(set(union)))
            self.assertTrue(all(report["status"] == "success" for report in reports))
            self.assertTrue(all(report["full_ids"] == full for report in reports))

    def test_module_class_and_cleanup_order_match_standard_unittest(self):
        source = """
            import unittest
            events = []
            def setUpModule(): events.append('module setup')
            def tearDownModule(): events.append('module teardown')
            class First(unittest.TestCase):
                @classmethod
                def setUpClass(cls):
                    events.append('class setup')
                    cls.addClassCleanup(events.append, 'class cleanup')
                @classmethod
                def tearDownClass(cls): events.append('class teardown')
                def setUp(self):
                    events.append('case setup')
                    self.addCleanup(events.append, 'case cleanup')
                def tearDown(self): events.append('case teardown')
                def test_one(self): events.append('case one')
                def test_two(self): events.append('case two')
            class Second(unittest.TestCase):
                def test_three(self): events.append('case three')
        """
        with synthetic_suite({"a": source}) as (root, start):
            ordinary = CI.discover_tests(root, start)
            unittest.TextTestRunner(stream=io.StringIO()).run(ordinary.suite)
            module = sys.modules[PREFIX + "a"]
            expected = list(module.events)
            module.events.clear()
            report = run_synthetic(root, start)
            self.assertEqual(report["status"], "success", report)
            self.assertEqual(module.events, expected)
            kinds = {row["kind"] for row in report["fixtures"]}
            self.assertEqual(kinds, {"module_setup", "module_teardown", "class_setup", "class_teardown"})
            self.assertTrue(all(row["file"] == "tests/test_ci_fixture_a.py" for row in report["fixtures"]))

    def test_module_transition_fixtures_run_once_in_discovery_order(self):
        source = """
            import unittest
            events = []
            def setUpModule(): events.append('setup')
            def tearDownModule(): events.append('teardown')
            class Case(unittest.TestCase):
                def test_one(self): events.append('test')
        """
        with synthetic_suite({"a": source, "b": source}) as (root, start):
            report = run_synthetic(root, start)
            self.assertEqual(report["status"], "success", report)
            for name in ("a", "b"):
                self.assertEqual(sys.modules[PREFIX + name].events, ["setup", "test", "teardown"])
            self.assertEqual([case["file"] for case in report["cases"]],
                             ["tests/test_ci_fixture_a.py", "tests/test_ci_fixture_b.py"])

    def test_load_tests_order_is_preserved(self):
        source = """
            import unittest
            class Case(unittest.TestCase):
                def test_a(self): pass
                def test_z(self): pass
            def load_tests(loader, tests, pattern):
                return unittest.TestSuite([Case('test_z'), Case('test_a')])
        """
        with synthetic_suite({"a": source}) as (root, start):
            report = run_synthetic(root, start)
            self.assertEqual(report["status"], "success", report)
            self.assertEqual([value.rsplit('.', 1)[1] for value in report["executed_ids"]],
                             ["test_z", "test_a"])

    def test_case_timing_includes_setup_teardown_and_cleanup(self):
        source = """
            import time
            import unittest
            class Case(unittest.TestCase):
                @classmethod
                def setUpClass(cls): time.sleep(0.003)
                def setUp(self):
                    time.sleep(0.003)
                    self.addCleanup(time.sleep, 0.003)
                def tearDown(self): time.sleep(0.003)
                def test_one(self): time.sleep(0.003)
        """
        with synthetic_suite({"a": source}) as (root, start):
            report = run_synthetic(root, start)
            self.assertEqual(report["status"], "success", report)
            self.assertGreaterEqual(report["cases"][0]["seconds"], 0.01)
            row = report["file_timings"][0]
            self.assertGreater(row["fixture_seconds"], 0)
            self.assertAlmostEqual(row["seconds"], row["case_seconds"] + row["fixture_seconds"])
            self.assertGreaterEqual(report["wall_seconds"], report["collection_seconds"])

    def test_case_skip_expected_failure_and_subtest_failures_are_distinct(self):
        source = """
            import unittest
            class Case(unittest.TestCase):
                @unittest.skip('intentional fixture skip')
                def test_skip(self): self.fail('must not run')
                @unittest.expectedFailure
                def test_expected(self): self.assertEqual(1, 2)
                def test_bad_subtest(self):
                    with self.subTest(value=1): self.assertEqual(1, 2)
        """
        with synthetic_suite({"a": source}) as (root, start):
            report = run_synthetic(root, start)
            self.assertEqual(report["status"], "failure")
            self.assertEqual(report["counts"]["run"], 3)
            self.assertEqual(report["counts"]["failures"], 1)
            self.assertEqual(report["counts"]["expected_failures"], 1)
            self.assertEqual(report["counts"]["skips"], 1)
            self.assertEqual({row["outcome"] for row in report["cases"]},
                             {"failure", "skip", "expected_failure"})

    def test_fixture_skips_account_for_unstarted_assigned_cases(self):
        for fixture in ("class", "module"):
            with self.subTest(fixture=fixture):
                source = "import unittest\n"
                if fixture == "module":
                    source += "def setUpModule(): raise unittest.SkipTest('optional fixture')\n"
                    source += simple_module(2).replace("import unittest\n", "")
                else:
                    source += "class Case(unittest.TestCase):\n"
                    source += "    @classmethod\n    def setUpClass(cls): raise unittest.SkipTest('optional fixture')\n"
                    source += "    def test_one(self): self.fail('must not run')\n"
                    source += "    def test_two(self): self.fail('must not run')\n"
                with synthetic_suite({"a": source}) as (root, start):
                    report = run_synthetic(root, start)
                    self.assertEqual(report["status"], "success", report)
                    self.assertEqual(report["executed_ids"], [])
                    self.assertEqual(report["fixture_skipped_ids"], report["assigned_ids"])
                    self.assertEqual(report["counts"]["fixture_skipped"], 2)

    def test_fixture_error_is_failure_without_claiming_unstarted_cases(self):
        source = """
            import unittest
            class Case(unittest.TestCase):
                @classmethod
                def setUpClass(cls): raise RuntimeError('synthetic setup failure')
                def test_one(self): self.fail('must not run')
        """
        with synthetic_suite({"a": source}) as (root, start):
            report = run_synthetic(root, start)
            self.assertEqual(report["status"], "failure")
            self.assertEqual(report["counts"]["errors"], 1)
            self.assertEqual(report["executed_ids"], [])
            self.assertEqual(report["fixture_events"][0]["outcome"], "error")
            self.assertTrue(report["integrity_errors"])

    def test_import_failure_remains_a_reported_standard_unittest_error(self):
        with synthetic_suite({"a": "raise RuntimeError('synthetic import failure')\n"}) as (root, start):
            report = run_synthetic(root, start)
            self.assertEqual(report["status"], "failure", report)
            self.assertEqual(report["counts"]["errors"], 1)
            self.assertTrue(report["loader_errors"])
            self.assertEqual(report["assigned_ids"], report["executed_ids"])

    def test_duplicate_imported_testcase_is_rejected_before_execution(self):
        with synthetic_suite({"a": simple_module(1),
                              "b": "from test_ci_fixture_a import Case\n"}) as (root, start):
            report = run_synthetic(root, start)
            self.assertEqual(report["status"], "error")
            self.assertIn("duplicate discovery IDs", report["integrity_errors"][0])
            self.assertEqual(report["executed_ids"], [])

    def test_unknown_custom_suite_is_rejected_instead_of_flattened(self):
        source = """
            import unittest
            class Case(unittest.TestCase):
                def test_one(self): pass
            class SpecialSuite(unittest.TestSuite): pass
            def load_tests(loader, tests, pattern):
                return SpecialSuite([Case('test_one')])
        """
        with synthetic_suite({"a": source}) as (root, start):
            report = run_synthetic(root, start)
            self.assertEqual(report["status"], "error")
            self.assertIn("custom suite cannot be safely sharded", report["integrity_errors"][0])
            self.assertEqual(len(report["full_ids"]), 1)

    def test_targeted_modules_are_validated_and_keep_full_discovery_inventory(self):
        with synthetic_suite({"a": simple_module(1), "b": simple_module(2)}) as (root, start):
            report = run_synthetic(root, start, modules=[PREFIX + "b"])
            self.assertEqual(report["status"], "success", report)
            self.assertEqual(report["mode"], "targeted")
            self.assertEqual(len(report["full_ids"]), 3)
            self.assertEqual(len(report["assigned_ids"]), 2)
            missing = run_synthetic(root, start, modules=[PREFIX + "missing"])
            self.assertEqual(missing["status"], "error")
        for value in ("", "test_a,", "../test_a", "test_a,test_a", "tests.test_a"):
            with self.subTest(value=value), self.assertRaises(CI.EvidenceError):
                CI.parse_modules(value)

    def test_cli_writes_error_evidence_even_if_discovery_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            with patch.object(CI, "runtime_metadata", return_value=META), \
                    patch.object(CI, "discover_tests", side_effect=RuntimeError("synthetic discovery failure")), \
                    patch("sys.stdout", new=io.StringIO()):
                code = CI.main(["run", "--report", str(path)])
            self.assertEqual(code, 1)
            self.assertTrue(path.is_file())
            self.assertIn("synthetic discovery failure", path.read_text(encoding="utf-8"))


class CiUnittestCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.reports_root = Path(self.temp.name)

    def successful_reports(self):
        with synthetic_suite({name: simple_module(number) for name, number in
                              (("a", 4), ("b", 3), ("c", 2), ("d", 1))}) as (root, start):
            return [run_synthetic(root, start, shard_index=index, shard_count=4) for index in range(4)]

    def verify(self, reports):
        paths = []
        for index, report in enumerate(reports):
            path = self.reports_root / f"shard-{index}" / "timings.json"
            CI.write_report(path, report)
            paths.append(path)
        return CI.verify_reports(paths, shard_count=4, python_version="3.10",
                                 github_sha=META["github_sha"], source_sha=META["source_sha"])

    def test_valid_same_head_shards_pass_with_file_and_case_rankings(self):
        summary = self.verify(self.successful_reports())
        self.assertEqual(summary["status"], "success", summary)
        self.assertEqual(summary["full_count"], 10)
        self.assertEqual(summary["shards"], 4)
        self.assertEqual(len(summary["slowest_cases"]), 10)
        self.assertEqual(len(summary["slowest_files"]), 4)
        self.assertGreaterEqual(summary["runner_seconds"], summary["wall_seconds"])

    def test_missing_or_unreadable_report_fails(self):
        reports = self.successful_reports()
        self.assertEqual(self.verify(reports[:-1])["status"], "failure")
        self.verify(reports)
        path = self.reports_root / "shard-3" / "timings.json"
        path.write_text("not JSON", encoding="utf-8")
        summary = CI.verify_reports(sorted(self.reports_root.rglob("*.json")), shard_count=4,
                                    python_version="3.10", github_sha=META["github_sha"])
        self.assertEqual(summary["status"], "failure")
        self.assertTrue(any("unreadable report" in message for message in summary["errors"]))

    def test_failures_commit_version_plan_and_coverage_mismatches_fail_closed(self):
        original = self.successful_reports()
        changes = (
            lambda report: report.update(status="failure"),
            lambda report: report.update(source_sha="c" * 40),
            lambda report: report.update(checkout_sha="c" * 40),
            lambda report: report.update(github_sha="c" * 40),
            lambda report: report.update(python_version="3.14"),
            lambda report: report["shard"].update(index=1),
            lambda report: report["shard"].update(count=3),
            lambda report: report.update(mode="targeted"),
            lambda report: report["executed_ids"].clear(),
            lambda report: report["assigned_ids"].append(report["assigned_ids"][0]),
            lambda report: report["full_ids"].pop(),
            lambda report: report["counts"].update(errors=1),
            lambda report: report["file_assignments"].update({"tests/test_ci_fixture_a.py": 1}),
            lambda report: report["cases"].clear(),
            lambda report: report["cases"][0].update(outcome="unknown"),
            lambda report: report.update(full_ids=None),
            lambda report: report.update(wall_seconds=float("nan")),
        )
        for index, change in enumerate(changes):
            with self.subTest(change=index):
                reports = copy.deepcopy(original)
                change(reports[0])
                self.assertEqual(self.verify(reports)["status"], "failure")


if __name__ == "__main__":
    unittest.main()
