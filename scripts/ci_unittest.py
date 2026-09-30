#!/usr/bin/env python3
"""Time and shard standard unittest discovery; verify complete remote coverage.

Every worker discovers the entire suite in the standard order before selecting
whole files. The collector accepts only successful, disjoint full-suite shards
from the same checkout, source commit, event commit and Python version.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
import traceback
from typing import Any, Iterable
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "1.0.0"
TIMINGS_PATH = ROOT / "tests/fixtures/windows_unittest_timings.json"
_DEFAULT_PROFILE = object()


class EvidenceError(ValueError):
    """Discovery or shard evidence cannot establish full-suite coverage."""


@dataclass(frozen=True)
class TimingProfile:
    weights: dict[str, float]
    case_count: int
    sha256: str
    identity: dict[str, Any]


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError(f"duplicate timing profile key: {key}")
        result[key] = value
    return result


def load_timing_profile(path: Path = TIMINGS_PATH) -> TimingProfile | None:
    if not path.exists():
        return None
    try:
        raw = path.read_bytes()
        if len(raw) > 2 * 1024 * 1024:
            raise EvidenceError("timing profile exceeds 2 MiB")
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_json_object)
        if not isinstance(payload, dict) or type(payload.get("schema_version")) is not int or payload["schema_version"] != 1:
            raise EvidenceError("timing profile schema_version must be 1")
        if not re.fullmatch(r"[0-9a-f]{40}", str(payload.get("profile_source_sha", ""))):
            raise EvidenceError("timing profile source SHA is invalid")
        if type(payload.get("profile_run_id")) is not int or payload["profile_run_id"] < 1:
            raise EvidenceError("timing profile run ID is invalid")
        if payload.get("python_version") not in ("3.10", "3.14"):
            raise EvidenceError("timing profile Python version is outside the formal matrix")
        if type(payload.get("profile_case_count")) is not int or payload["profile_case_count"] < 1:
            raise EvidenceError("timing profile case count is invalid")
        if payload.get("status") not in ("timing_only_failed_gate_not_acceptance", "timing_only_successful_gate_not_acceptance"):
            raise EvidenceError("timing profile must explicitly describe timing-only evidence")
        evidence = payload.get("evidence")
        if not isinstance(evidence, list) or not evidence or any(not isinstance(row, (dict, str)) or not row for row in evidence):
            raise EvidenceError("timing profile evidence is missing or invalid")
        weights = payload.get("weights")
        if not isinstance(weights, dict) or not weights:
            raise EvidenceError("timing profile weights must be a nonempty mapping")
        if payload["profile_case_count"] < len(weights):
            raise EvidenceError("timing profile case count is smaller than its file count")
        for filename, seconds in weights.items():
            if not isinstance(filename, str):
                raise EvidenceError("timing profile path is not text")
            parts = filename.split("/")
            if (len(parts) < 2 or parts[0] != "tests" or "\\" in filename
                    or any(not part or part in (".", "..") for part in parts)
                    or not parts[-1].startswith("test_") or not parts[-1].endswith(".py")
                    or not parts[-1][:-3].isidentifier()
                    or any(not part.isidentifier() for part in parts[1:-1])):
                raise EvidenceError(f"timing profile path is not a relative discovery file: {filename}")
            if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds <= 0:
                raise EvidenceError(f"timing profile weight must be finite and positive: {filename}")
        if not math.isfinite(sum(weights.values())):
            raise EvidenceError("timing profile total weight is not finite")
        identity = {key: payload[key] for key in ("profile_source_sha", "profile_run_id", "python_version",
                                                "profile_case_count", "status")}
        return TimingProfile(weights, payload["profile_case_count"], hashlib.sha256(raw).hexdigest(), identity)
    except (OSError, ValueError, UnicodeError) as exc:
        raise EvidenceError(f"cannot load timing profile {path}: {exc}") from exc


def file_weights(entries: list[dict[str, Any]], profile: TimingProfile | None = None) -> tuple[dict[str, float], dict[str, Any]]:
    counts = Counter(entry["file"] for entry in entries)
    matched = set(counts) & set(profile.weights) if profile else set()
    average = sum(profile.weights.values()) / profile.case_count if profile and matched else None
    weights = {path: profile.weights.get(path, average * count) if average is not None else count
               for path, count in counts.items()}
    manifest = {"mode": "measured_file_seconds" if matched else "case_count",
                "weights_sha256": profile.sha256 if profile else None,
                "profile": profile.identity if profile else None,
                "fallback_seconds_per_case": average, "matched_file_count": len(matched),
                "fallback_files": sorted(set(counts) - matched) if matched else []}
    return weights, manifest


def iter_cases(suite: unittest.TestSuite) -> Iterable[unittest.TestCase]:
    if isinstance(suite, unittest.TestSuite):
        for item in suite:
            yield from iter_cases(item)
    elif isinstance(suite, unittest.TestCase):
        yield suite
    else:
        raise EvidenceError(f"unsupported discovered test object: {type(suite).__name__}")


class RecordingLoader(unittest.TestLoader):
    """Use the standard loader, recording the file that collected each case."""

    def __init__(self, root: Path):
        super().__init__()
        self.root = root.resolve()
        self.case_files: dict[int, str] = {}

    def loadTestsFromModule(self, module, *, pattern=None):
        suite = super().loadTestsFromModule(module, pattern=pattern)
        path = Path(module.__file__).resolve().relative_to(self.root).as_posix()
        for case in iter_cases(suite):
            # A load_tests hook may itself discover modules. Preserve the deeper
            # loader's attribution rather than replacing it with its package.
            self.case_files.setdefault(id(case), path)
        return suite


@dataclass
class Collection:
    suite: unittest.TestSuite
    entries: list[dict[str, Any]]
    seconds: float
    loader_errors: list[str]


def discover_tests(root: Path = ROOT, start_directory: Path | None = None) -> Collection:
    start = (start_directory or root / "tests").resolve()
    loader = RecordingLoader(root)
    began = time.perf_counter()
    # Do not supply top_level_dir: this exactly follows discover -s tests.
    suite = loader.discover(str(start), pattern="test_*.py")
    entries = []
    for case in iter_cases(suite):
        path = loader.case_files.get(id(case))
        if path is None and isinstance(case, unittest.loader._FailedTest):
            # Standard discovery represents an import failure as a real failing
            # test without calling loadTestsFromModule.
            failed = start / (case._testMethodName.replace(".", "/") + ".py")
            path = failed.relative_to(root.resolve()).as_posix()
        if path is None:
            raise EvidenceError(f"discovered case has no collection file: {case.id()}")
        entries.append({"id": case.id(), "file": path, "case": case})
    return Collection(suite, entries, time.perf_counter() - began, list(loader.errors))


def assign_files(entries: list[dict[str, Any]], shard_count: int,
                 profile: TimingProfile | None = None) -> dict[str, int]:
    if shard_count < 1:
        raise EvidenceError("shard count must be positive")
    weights, _ = file_weights(entries, profile)
    loads = [0] * shard_count
    assignments = {}
    # Measured file seconds when available; otherwise collected case counts.
    # New files use the profile's average seconds/case. No test result is reused.
    for path in sorted(weights, key=lambda name: (-weights[name], name)):
        index = min(range(shard_count), key=lambda value: (loads[value], value))
        assignments[path] = index
        loads[index] += weights[path]
    return assignments


def parse_modules(value: str) -> list[str]:
    modules = value.split(",")
    if not modules or any(not re.fullmatch(r"test_[A-Za-z0-9_]+", name) for name in modules):
        raise EvidenceError("--modules requires comma-separated test_ module names")
    if len(set(modules)) != len(modules):
        raise EvidenceError("--modules contains duplicates")
    return modules


class TimedSuite(unittest.TestSuite):
    """Standard TestSuite fixture handling with clocks around its own hooks."""

    timing_file: str | None = None

    def run(self, result, debug=False):
        began = time.perf_counter()
        try:
            return super().run(result, debug)
        finally:
            if self.timing_file:
                result.file_seconds[self.timing_file] += time.perf_counter() - began

    def _fixture(self, result, kind, scope, callback):
        began = time.perf_counter()
        prior = result.fixture_seconds
        try:
            return callback()
        finally:
            elapsed = time.perf_counter() - began
            # _handleModuleFixture also invokes module teardown. Record its own
            # exclusive time, so that nested fixture clocks are never added twice.
            exclusive = max(0.0, elapsed - (result.fixture_seconds - prior))
            result.record_fixture(kind, scope, exclusive, elapsed)

    def _handleClassSetUp(self, test, result):
        if test.__class__ == getattr(result, "_previousTestClass", None):
            return super()._handleClassSetUp(test, result)
        scope = f"{test.__class__.__module__}.{test.__class__.__qualname__}"
        return self._fixture(result, "class_setup", scope,
                             lambda: super(TimedSuite, self)._handleClassSetUp(test, result))

    def _tearDownPreviousClass(self, test, result):
        previous = getattr(result, "_previousTestClass", None)
        if previous is None or (test is not None and previous == test.__class__):
            return super()._tearDownPreviousClass(test, result)
        scope = f"{previous.__module__}.{previous.__qualname__}"
        return self._fixture(result, "class_teardown", scope,
                             lambda: super(TimedSuite, self)._tearDownPreviousClass(test, result))

    def _handleModuleFixture(self, test, result):
        module = test.__class__.__module__
        previous = getattr(result, "_previousTestClass", None)
        if previous is not None and module == previous.__module__:
            return super()._handleModuleFixture(test, result)
        return self._fixture(result, "module_setup", module,
                             lambda: super(TimedSuite, self)._handleModuleFixture(test, result))

    def _handleModuleTearDown(self, result):
        previous = getattr(result, "_previousTestClass", None)
        if previous is None:
            return super()._handleModuleTearDown(result)
        return self._fixture(result, "module_teardown", previous.__module__,
                             lambda: super(TimedSuite, self)._handleModuleTearDown(result))


def select_suite(suite, selected: set[int], case_files: dict[int, str], *, timed=True):
    """Retain discovery order and nesting; never flatten away fixture boundaries."""
    if isinstance(suite, unittest.TestCase):
        return suite if id(suite) in selected else None
    if type(suite) is not unittest.TestSuite:
        raise EvidenceError(f"custom suite cannot be safely sharded: {type(suite).__name__}")
    all_cases = list(iter_cases(suite))
    files = {case_files[id(case)] for case in all_cases if id(case) in selected}
    owns_clock = timed and len(files) == 1
    children = [select_suite(child, selected, case_files, timed=timed and not owns_clock)
                for child in suite]
    chosen = TimedSuite(child for child in children if child is not None)
    if owns_clock:
        chosen.timing_file = next(iter(files))
    return chosen if chosen.countTestCases() else None


class TimingResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.entries: dict[str, dict[str, Any]] = {}
        self.case_rows: list[dict[str, Any]] = []
        self.executed_ids: list[str] = []
        self.fixture_skipped_ids: list[str] = []
        self.fixture_events: list[dict[str, str]] = []
        self.fixtures: list[dict[str, Any]] = []
        self.file_seconds: Counter = Counter()
        self.fixture_seconds = 0.0
        self.active: dict[str, float] = {}
        self.outcomes: dict[str, str] = {}
        self.integrity_errors: list[str] = []

    def startTest(self, test):
        self.active[test.id()] = time.perf_counter()
        self.executed_ids.append(test.id())
        super().startTest(test)

    def stopTest(self, test):
        case_id = test.id()
        self.case_rows.append({"id": case_id, "file": self.entries[case_id]["file"],
                               "seconds": time.perf_counter() - self.active.pop(case_id),
                               "outcome": self.outcomes.get(case_id, "unknown")})
        super().stopTest(test)

    def _outcome(self, test, status, detail=""):
        if test.id() in self.active:
            self.outcomes[test.id()] = status
        else:
            self.fixture_events.append({"id": test.id(), "outcome": status, "detail": detail})

    def addSuccess(self, test):
        self._outcome(test, "success")
        super().addSuccess(test)

    def addError(self, test, err):
        self._outcome(test, "error", str(err[1]))
        super().addError(test, err)

    def addFailure(self, test, err):
        self._outcome(test, "failure", str(err[1]))
        super().addFailure(test, err)

    def addSkip(self, test, reason):
        self._outcome(test, "skip", reason)
        if test.id() not in self.active:
            match = re.fullmatch(r"(setUpClass|setUpModule) \((.+)\)", test.id())
            if not match:
                self.integrity_errors.append(f"unknown fixture skip scope: {test.id()}")
            else:
                kind, scope = match.groups()
                for case_id, entry in self.entries.items():
                    case = entry["case"]
                    target = case.__class__.__module__
                    if kind == "setUpClass":
                        target += "." + case.__class__.__qualname__
                    if target == scope:
                        self.fixture_skipped_ids.append(case_id)
        super().addSkip(test, reason)

    def addExpectedFailure(self, test, err):
        self._outcome(test, "expected_failure")
        super().addExpectedFailure(test, err)

    def addUnexpectedSuccess(self, test):
        self._outcome(test, "unexpected_success")
        super().addUnexpectedSuccess(test)

    def addSubTest(self, test, subtest, err):
        if err is not None:
            self._outcome(test, "failure" if issubclass(err[0], test.failureException) else "error")
        super().addSubTest(test, subtest, err)

    def record_fixture(self, kind, scope, seconds, wall_seconds):
        path = next((entry["file"] for entry in self.entries.values()
                     if (entry["case"].__class__.__module__ if kind.startswith("module_") else
                         f"{entry['case'].__class__.__module__}.{entry['case'].__class__.__qualname__}")
                     == scope), None)
        self.fixtures.append({"kind": kind, "scope": scope, "file": path,
                              "seconds": seconds, "wall_seconds": wall_seconds})
        self.fixture_seconds += seconds


def dependency_info() -> dict[str, Any]:
    versions = {}
    for name in ("PyYAML", "openpyxl", "numpy", "scipy", "matplotlib"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    import yaml
    import safe_yaml
    return {"dependencies": versions, "pyyaml_libyaml_available": bool(yaml.__with_libyaml__),
            "yaml_loader": safe_yaml.loader_name(),
            "yaml_pure_python_requested": os.getenv("HSK_YAML_PURE_PYTHON", ""),
            "yaml_disable_cache_requested": os.getenv("HSK_YAML_DISABLE_CACHE", ""),
            "unittest_loader": "standard unittest.TestLoader discovery with collection metadata",
            "python_implementation": platform.python_implementation(), "platform": platform.platform(),
            "executable": sys.executable}


def runtime_metadata(root: Path = ROOT) -> dict[str, Any]:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True,
                            capture_output=True, check=True)
    checkout = result.stdout.strip()
    return {"github_sha": os.getenv("GITHUB_SHA", checkout), "checkout_sha": checkout,
            "source_sha": os.getenv("HSK_SOURCE_SHA", checkout),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
            "python_full_version": platform.python_version(), "runtime": dependency_info()}


def execute_collection(collection: Collection, *, metadata: dict[str, Any], shard_index=0,
                       shard_count=1, modules: list[str] | None = None, stream=None,
                       profile=_DEFAULT_PROFILE) -> dict[str, Any]:
    began = time.perf_counter()
    report = {"schema_version": SCHEMA_VERSION, **metadata, "status": "error",
              "mode": "targeted" if modules else "full", "modules": modules or [],
              "shard": {"index": shard_index, "count": shard_count},
              "collection_seconds": collection.seconds, "loader_errors": collection.loader_errors,
              "full_ids": [entry["id"] for entry in collection.entries], "assigned_ids": [],
              "full_files": {entry["id"]: entry["file"] for entry in collection.entries},
              "executed_ids": [], "fixture_skipped_ids": [], "cases": [], "fixtures": [],
              "file_timings": [], "counts": {}, "integrity_errors": []}
    try:
        if not 0 <= shard_index < shard_count:
            raise EvidenceError("shard index must be between zero and shard count minus one")
        duplicates = [key for key, count in Counter(report["full_ids"]).items() if count > 1]
        if duplicates:
            raise EvidenceError("duplicate discovery IDs: " + ", ".join(duplicates))
        if not collection.entries:
            raise EvidenceError("discovery collected no tests")
        if profile is _DEFAULT_PROFILE:
            profile = load_timing_profile()
        weights, manifest = file_weights(collection.entries, profile)
        report["file_weights"] = weights
        report["weight_profile"] = manifest
        report["weights_sha256"] = manifest["weights_sha256"]
        assignments = assign_files(collection.entries, shard_count, profile)
        report["file_assignments"] = assignments
        selected_files = {path for path, index in assignments.items() if index == shard_index}
        if modules:
            if shard_count != 1:
                raise EvidenceError("targeted mode requires one shard")
            discovered = {Path(path).stem: path for path in assignments}
            if len(discovered) != len(assignments):
                raise EvidenceError("targeted modules are ambiguous across test directories")
            missing = sorted(set(modules) - set(discovered))
            if missing:
                raise EvidenceError("unknown targeted modules: " + ", ".join(missing))
            selected_files = {discovered[name] for name in modules}
        chosen = [entry for entry in collection.entries if entry["file"] in selected_files]
        report["assigned_ids"] = [entry["id"] for entry in chosen]
        cases = {id(entry["case"]): entry["file"] for entry in collection.entries}
        suite = select_suite(collection.suite, {id(entry["case"]) for entry in chosen}, cases)
        runner = unittest.TextTestRunner(stream=stream or sys.stderr, verbosity=2,
                                         resultclass=TimingResult)
        # TextTestRunner owns start/stopTestRun; attach metadata before fixtures.
        original_make_result = runner._makeResult
        def make_result():
            result = original_make_result()
            result.entries = {entry["id"]: entry for entry in chosen}
            return result
        runner._makeResult = make_result
        result = runner.run(suite or TimedSuite())
        report.update(executed_ids=result.executed_ids, fixture_skipped_ids=result.fixture_skipped_ids,
                      cases=result.case_rows, fixtures=result.fixtures, fixture_events=result.fixture_events)
        report["counts"] = {"assigned": len(chosen), "run": result.testsRun,
                            "failures": len(result.failures), "errors": len(result.errors),
                            "skips": len(result.skipped), "expected_failures": len(result.expectedFailures),
                            "unexpected_successes": len(result.unexpectedSuccesses),
                            "fixture_skipped": len(result.fixture_skipped_ids)}
        for path in sorted(selected_files):
            case_seconds = sum(row["seconds"] for row in result.case_rows if row["file"] == path)
            fixture_seconds = sum(row["seconds"] for row in result.fixtures if row["file"] == path)
            block = result.file_seconds[path]
            # A module's final teardown happens at the following module boundary
            # or at the outer suite's end. Attributable time is cases + fixtures;
            # keep the raw suite block clock separately instead of double counting.
            report["file_timings"].append({"file": path, "seconds": case_seconds + fixture_seconds,
                                           "suite_block_seconds": block,
                                           "case_seconds": case_seconds, "fixture_seconds": fixture_seconds,
                                           "other_seconds": max(0.0, block - case_seconds - fixture_seconds)})
        accounted = Counter(result.executed_ids + result.fixture_skipped_ids)
        if accounted != Counter(report["assigned_ids"]):
            result.integrity_errors.append("execution and fixture skips do not cover assigned cases exactly")
        report["integrity_errors"] = result.integrity_errors
        report["status"] = "success" if (result.wasSuccessful() and not result.integrity_errors
                                        and not collection.loader_errors) else "failure"
    except Exception:
        report["integrity_errors"].append(traceback.format_exc())
    finally:
        report["wall_seconds"] = time.perf_counter() - began + collection.seconds
    return report


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_report_structure(report: dict[str, Any]) -> None:
    for field in ("schema_version", "mode", "status", "github_sha", "checkout_sha", "source_sha",
                  "python_version"):
        if not isinstance(report.get(field), str):
            raise EvidenceError(f"missing or invalid {field}")
    for field in ("full_ids", "assigned_ids", "executed_ids", "fixture_skipped_ids", "loader_errors",
                  "integrity_errors"):
        value = report.get(field)
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise EvidenceError(f"missing or invalid {field}")
    for field in ("full_files", "file_assignments", "file_weights"):
        value = report.get(field)
        if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
            raise EvidenceError(f"missing or invalid {field}")
    if any(not isinstance(value, str) for value in report["full_files"].values()):
        raise EvidenceError("invalid full file mapping")
    if any(type(value) is not int for value in report["file_assignments"].values()):
        raise EvidenceError("invalid file assignment")
    if any(type(value) not in (int, float) or not math.isfinite(value) or value <= 0
           for value in report["file_weights"].values()):
        raise EvidenceError("invalid file weights")
    if not isinstance(report.get("weight_profile"), dict):
        raise EvidenceError("missing weight profile identity")
    shard = report.get("shard")
    if not isinstance(shard, dict) or any(type(shard.get(key)) is not int for key in ("index", "count")):
        raise EvidenceError("missing or invalid shard")
    counts = report.get("counts")
    keys = ("assigned", "run", "failures", "errors", "skips", "expected_failures",
            "unexpected_successes", "fixture_skipped")
    if not isinstance(counts, dict) or any(type(counts.get(key)) is not int or counts[key] < 0 for key in keys):
        raise EvidenceError("missing or invalid result counts")
    for field in ("collection_seconds", "wall_seconds"):
        seconds = report.get(field)
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
            raise EvidenceError(f"missing or invalid {field}")
    for field, name in (("cases", "id"), ("file_timings", "file")):
        rows = report.get(field)
        if not isinstance(rows, list):
            raise EvidenceError(f"missing or invalid {field}")
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get(name), str):
                raise EvidenceError(f"invalid {field} row")
            seconds = row.get("seconds")
            if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
                raise EvidenceError(f"invalid {field} timing")


def verify_reports(paths: list[Path], *, shard_count: int, python_version: str,
                   github_sha: str, source_sha: str | None = None,
                   profile=_DEFAULT_PROFILE) -> dict[str, Any]:
    errors, reports = [], []
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise EvidenceError("report is not an object")
            validate_report_structure(payload)
            reports.append(payload)
        except (ValueError, OSError) as exc:
            errors.append(f"unreadable report {path}: {exc}")
    if shard_count < 1 or len(paths) != shard_count or len(reports) != shard_count:
        errors.append(f"expected {shard_count} reports; found {len(paths)}, readable {len(reports)}")
    if not re.fullmatch(r"[0-9a-f]{40}", github_sha):
        errors.append("expected GitHub event SHA is missing or invalid")
    if profile is _DEFAULT_PROFILE:
        try:
            profile = load_timing_profile()
        except EvidenceError as exc:
            errors.append(str(exc))
            profile = None
    baseline = reports[0] if reports else {}
    seen_indices, all_assigned = [], []
    full = baseline.get("full_ids", [])
    if not full or len(full) != len(set(full)):
        errors.append("full discovery IDs are missing or duplicated")
    expected_plan = baseline.get("file_assignments", {})
    full_files = baseline.get("full_files", {})
    entries = [{"file": path} for path in full_files.values()]
    weights, manifest = file_weights(entries, profile)
    if set(full_files) != set(full):
        errors.append("full discovery file mapping is incomplete")
    if full_files and shard_count > 0:
        calculated = assign_files(entries, shard_count, profile)
        if expected_plan != calculated:
            errors.append("file assignment is not the deterministic plan")
    for report in reports:
        shard = report.get("shard", {})
        index = shard.get("index")
        seen_indices.append(index)
        label = f"shard {index}"
        if report.get("schema_version") != SCHEMA_VERSION or report.get("mode") != "full":
            errors.append(f"{label}: wrong schema or targeted report cannot establish full coverage")
        if report.get("status") != "success" or report.get("integrity_errors") or report.get("loader_errors"):
            errors.append(f"{label}: unsuccessful execution or discovery")
        if shard.get("count") != shard_count:
            errors.append(f"{label}: shard count mismatch")
        if report.get("python_version") != python_version:
            errors.append(f"{label}: Python version mismatch")
        if report.get("github_sha") != github_sha:
            errors.append(f"{label}: GitHub event commit mismatch")
        for field in ("checkout_sha", "source_sha"):
            if not re.fullmatch(r"[0-9a-f]{40}", str(report.get(field, ""))):
                errors.append(f"{label}: {field} is missing or invalid")
            if report.get(field) != baseline.get(field):
                errors.append(f"{label}: {field} differs across shards")
        if source_sha is not None and report.get("source_sha") != source_sha:
            errors.append(f"{label}: source commit mismatch")
        if source_sha is not None and report.get("checkout_sha") != source_sha:
            errors.append(f"{label}: checkout is not the expected source commit")
        if (report.get("full_ids") != full or report.get("file_assignments") != expected_plan
                or report.get("full_files") != full_files):
            errors.append(f"{label}: full discovery or assignment plan differs")
        if (report.get("weight_profile") != manifest or report.get("file_weights") != weights
                or report.get("weights_sha256") != manifest["weights_sha256"]):
            errors.append(f"{label}: weights or profile hash differ from the current checkout")
        assigned = report.get("assigned_ids", [])
        expected_assigned = [case_id for case_id in full
                             if expected_plan.get(full_files.get(case_id)) == index]
        if assigned != expected_assigned:
            errors.append(f"{label}: assigned cases differ from its file plan")
        accounted = report.get("executed_ids", []) + report.get("fixture_skipped_ids", [])
        if Counter(assigned) != Counter(accounted):
            errors.append(f"{label}: assigned cases were not all executed or fixture-skipped")
        counts = report.get("counts", {})
        if any(counts.get(field, 0) != 0 for field in ("failures", "errors", "unexpected_successes")):
            errors.append(f"{label}: test failure counts are nonzero")
        if counts.get("assigned") != len(assigned) or counts.get("run") != len(report.get("executed_ids", [])):
            errors.append(f"{label}: test counts do not match IDs")
        if counts.get("fixture_skipped") != len(report.get("fixture_skipped_ids", [])):
            errors.append(f"{label}: fixture skip counts do not match IDs")
        rows = report.get("cases", [])
        if [row["id"] for row in rows] != report.get("executed_ids"):
            errors.append(f"{label}: case timing rows do not match executed IDs")
        if any(row.get("outcome") not in ("success", "skip", "expected_failure") for row in rows):
            errors.append(f"{label}: case outcome is unsuccessful or unknown")
        all_assigned.extend(assigned)
    if Counter(seen_indices) != Counter(range(shard_count)):
        errors.append("shard indices are missing, repeated or invalid")
    if Counter(all_assigned) != Counter(full):
        errors.append("shard union duplicates or omits full discovery IDs")
    return {"schema_version": SCHEMA_VERSION, "status": "failure" if errors else "success",
            "errors": errors, "python_version": python_version, "github_sha": github_sha,
            "source_sha": baseline.get("source_sha"), "checkout_sha": baseline.get("checkout_sha"),
            "weight_profile": manifest, "weights_sha256": manifest["weights_sha256"],
            "shards": len(reports), "full_count": len(full),
            "wall_seconds": max((report.get("wall_seconds", 0) for report in reports), default=0),
            "runner_seconds": sum(report.get("wall_seconds", 0) for report in reports),
            "slowest_cases": sorted((row for report in reports for row in report.get("cases", [])),
                                    key=lambda row: row["seconds"], reverse=True)[:20],
            "slowest_files": sorted((row for report in reports for row in report.get("file_timings", [])),
                                    key=lambda row: row["seconds"], reverse=True)[:20]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--shard-index", type=int, default=0)
    run.add_argument("--shard-count", type=int, default=1)
    run.add_argument("--modules", help="comma-separated validated test_ module names for targeted runs")
    run.add_argument("--report", required=True, type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("--reports", required=True, type=Path)
    verify.add_argument("--shard-count", required=True, type=int)
    verify.add_argument("--python-version", required=True)
    verify.add_argument("--output", type=Path, help="save the machine-readable coverage summary")
    args = parser.parse_args(argv)
    if args.command == "verify":
        summary = verify_reports(sorted(args.reports.rglob("*.json")), shard_count=args.shard_count,
                                 python_version=args.python_version, github_sha=os.getenv("GITHUB_SHA", ""),
                                 source_sha=os.getenv("HSK_SOURCE_SHA"))
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if args.output:
            write_report(args.output, summary)
        if os.getenv("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
                stream.write(f"Python {args.python_version}: {summary['status']}; "
                             f"{summary['full_count']} full discovery cases, {summary['shards']} shards; "
                             f"worker wall {summary['wall_seconds']:.1f}s, "
                             f"total runner {summary['runner_seconds']:.1f}s.\n")
                for title, key, name in (("Slowest cases", "slowest_cases", "id"),
                                         ("Slowest files (cases + fixtures)", "slowest_files", "file")):
                    stream.write(f"\n{title}\n\n| Item | Seconds |\n|---|---:|\n")
                    for row in summary[key]:
                        label = row[name].replace("|", "\\|").replace("\n", " ")
                        stream.write(f"| {label} | {row['seconds']:.3f} |\n")
        return 0 if summary["status"] == "success" else 1
    report = {"schema_version": SCHEMA_VERSION, "status": "error", "integrity_errors": []}
    try:
        metadata = runtime_metadata()
        report = execute_collection(discover_tests(), metadata=metadata, shard_index=args.shard_index,
                                    shard_count=args.shard_count,
                                    modules=parse_modules(args.modules) if args.modules is not None else None)
    except BaseException:
        report["integrity_errors"].append(traceback.format_exc())
    finally:
        write_report(args.report, report)
    print(f"Shard result: {report['status']}; evidence: {args.report}")
    return 0 if report["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
