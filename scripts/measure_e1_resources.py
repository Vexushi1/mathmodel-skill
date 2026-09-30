#!/usr/bin/env python3
"""GitHub maintenance measurements of ordinary routing and explicit retrieval.

These are bounded synthetic operations, not contest solvers, quality scores or
time-based gates. Initial driver imports, identity capture and resource enumeration are
outside the measured operation. Python allocation peaks are not process RSS.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import platform
import re
from statistics import median
import subprocess
from time import perf_counter_ns
import tracemalloc
from unittest.mock import patch
import argparse

import case_memory_retrieve as retrieval
from resolve_runtime import resolve_runtime
import safe_yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = ROOT / "knowledge/case_memory"
FIXTURE_VERSION = "1.0.0"
ROUTE_INPUT = {"intents": "model_selection", "objective": "optimization", "structures": []}
QUERY = {
    "protocol_version": "1.0.0", "objective": "optimization", "structures": [],
    "capabilities": ["has_explicit_constraints", "requires_feasibility_check"],
    "summary": "Synthetic continuous allocation under a common resource budget.",
    "traits": {"observation_regime": "shared_resource_tasks", "variable_domain": "continuous",
               "information_boundary": "unknown", "conditions": {
                   "same_decision_period": "satisfied", "shared_resource_feasibility": "satisfied",
                   "linear_relations": "satisfied", "divisible_allocation": "satisfied"}},
}
SOURCE_FILES = (
    "core/bootstrap.yaml", "core/project_state.schema.yaml", "core/workflow_router.yaml",
    "core/runtime_assurance_contract.yaml", "core/case_memory_retrieval_contract.yaml",
    "core/task_taxonomy.yaml", "scripts/resolve_runtime.py", "scripts/runtime_assurance.py",
    "scripts/case_memory.py", "scripts/case_memory_retrieve.py", "scripts/safe_yaml.py",
    "scripts/measure_e1_resources.py",
)
CORPUS_FILES = ("schema.yaml", "sources.json", "cases.json", "index.json", "retrieval_features.json")


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


_LOADED_DRIVER_SHA256 = digest(Path(__file__).read_bytes())


def head_identity() -> dict:
    values = {}
    for name, expression in (("checkout_commit", "HEAD"), ("checkout_tree", "HEAD^{tree}")):
        completed = subprocess.run(["git", "rev-parse", expression], cwd=ROOT, check=True,
                                   capture_output=True, text=True)
        value = completed.stdout.strip()
        if re.fullmatch(r"[0-9a-f]{40}", value) is None:
            raise ValueError("Git did not return an exact source identity")
        values[name] = value
    source = os.environ.get("HSK_SOURCE_SHA", values["checkout_commit"])
    if source != values["checkout_commit"]:
        raise ValueError("Source head differs from the measured checkout")
    event = os.environ.get("GITHUB_SHA")
    if event is not None and re.fullmatch(r"[0-9a-f]{40}", event) is None:
        raise ValueError("GitHub event identity is malformed")
    return {**values, "source_head": source, "github_event_sha": event}


def source_snapshot(corpus: Path, extra_paths=()) -> tuple[dict, dict[str, bytes]]:
    raw = {name: (ROOT / name).read_bytes() for name in SOURCE_FILES}
    for path in extra_paths:
        path = Path(path).resolve()
        if not path.is_relative_to(ROOT.resolve()):
            raise ValueError("Measured route source is outside the Skill checkout")
        name = path.relative_to(ROOT.resolve()).as_posix()
        raw[name] = path.read_bytes()
    raw.update({"corpus/" + name: (corpus / name).read_bytes() for name in CORPUS_FILES})
    if digest(raw["scripts/measure_e1_resources.py"]) != _LOADED_DRIVER_SHA256:
        raise ValueError("Loaded measurement driver differs from the current source bytes")
    bootstrap = safe_yaml.safe_load(raw["core/bootstrap.yaml"], cache=False)
    return {"skill_version": str(bootstrap["skill_version"]),
            "files": {name: {"sha256": digest(data), "bytes": len(data)}
                      for name, data in sorted(raw.items())}}, raw


def assert_frozen_files(corpus: Path, raw: dict[str, bytes]) -> None:
    for name, previous in raw.items():
        path = corpus / name[len("corpus/"):] if name.startswith("corpus/") else ROOT / name
        if path.read_bytes() != previous:
            raise ValueError("Measured source or corpus bytes changed before evidence was finalized")


def _read_alias(path: Path, corpus: Path) -> str:
    if path.is_relative_to(corpus.resolve()):
        return "corpus/" + path.relative_to(corpus.resolve()).as_posix()
    if path.is_relative_to(ROOT.resolve()):
        return path.relative_to(ROOT.resolve()).as_posix()
    raise ValueError("Measured operation read outside its frozen package and corpus")


@contextmanager
def observe_reads(corpus: Path, *, forbid_corpus: bool):
    """Observe real Path.open calls without reading files to obtain the metric.

    Calls are operations, not distinct files or physical disk reads. Binary and
    text reads remain unchanged; no inferred byte count is presented as I/O.
    """
    original = Path.open
    observed = {"paths": [], "write_attempted": False, "corpus_read_attempted": False}
    corpus = corpus.resolve()
    corpus_roots = {corpus, DEFAULT_CORPUS.resolve()}

    def open_path(path, *args, **kwargs):
        mode = args[0] if args else kwargs.get("mode", "r")
        if any(character in mode for character in "wax+"):
            observed["write_attempted"] = True
            raise ValueError("A measured read-only operation attempted a write")
        current = path.resolve()
        if forbid_corpus and any(current.is_relative_to(root) for root in corpus_roots):
            observed["corpus_read_attempted"] = True
            raise ValueError("An extension-off operation read the case corpus")
        observed["paths"].append(current)
        return original(path, *args, **kwargs)

    with patch.object(Path, "open", open_path):
        yield observed


def sample(operation, corpus: Path, *, forbid_corpus: bool, expected_status: str | None = None) -> dict:
    if tracemalloc.is_tracing():
        raise ValueError("An existing allocation trace cannot be used as a fresh operation peak")
    safe_yaml.clear_cache()
    try:
        with observe_reads(corpus, forbid_corpus=forbid_corpus) as observed:
            tracemalloc.start()
            start = perf_counter_ns()
            value = operation()
            if isinstance(value, retrieval.RetrievalSnapshot):
                value.assert_current()
                value = value.report
            encoded = canonical(value)
            elapsed = perf_counter_ns() - start
            _, peak = tracemalloc.get_traced_memory()
        # Consumers may turn a read error into a diagnostic or even catch it;
        # neither can erase an observed forbidden operation.
        if observed["write_attempted"]:
            raise ValueError("A measured read-only operation attempted a write")
        if observed["corpus_read_attempted"]:
            raise ValueError("An extension-off operation read the case corpus")
        paths = observed["paths"]
        if expected_status is None:
            if value.get("task_code_execution_allowed") is not False:
                raise ValueError("The synthetic ordinary route unexpectedly authorized task execution")
        elif value.get("status") != expected_status or value.get("execution_authorized") is not False:
            raise ValueError("The synthetic retrieval operation failed or claimed execution authority")
        return {"elapsed_ns": elapsed, "python_allocation_peak_bytes": peak,
                "returned_utf8_bytes": len(encoded), "returned_sha256": digest(encoded),
                "observed_path_open_calls": len(paths), "observed_unique_paths": len(set(paths)),
                "observed_corpus_open_calls": sum(any(path.is_relative_to(root) for root in
                                                     {corpus.resolve(), DEFAULT_CORPUS.resolve()}) for path in paths),
                "status": value.get("status", "ordinary_route"), "execution_authorized": False,
                "value": value, "_observed_paths": paths}
    finally:
        tracemalloc.stop()
        safe_yaml.clear_cache()


def declared_resources(plan: dict) -> list[dict]:
    rows = []
    for name in dict.fromkeys(path.split("#", 1)[0] for path in plan["load_order"]):
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT.resolve()) or path.is_relative_to(DEFAULT_CORPUS.resolve()):
            raise ValueError("Ordinary route declares an unexpected resource")
        raw = path.read_bytes()
        rows.append({"path": name, "bytes": len(raw), "sha256": digest(raw)})
    return rows


def measure(*, repeats: int = 1, corpus_root: Path = DEFAULT_CORPUS) -> dict:
    if type(repeats) is not int or not 1 <= repeats <= 5:
        raise ValueError("repeats must be an integer between 1 and 5")
    corpus = Path(corpus_root).resolve()
    identity = head_identity()
    # A real, unmeasured preflight discovers this route's dependencies. Freeze
    # those exact files before the timed invocation, including resources outside
    # SOURCE_FILES; a report cannot combine values from different read sets.
    with observe_reads(corpus, forbid_corpus=True) as preflight_reads:
        preflight = resolve_runtime(**deepcopy(ROUTE_INPUT))
    if preflight_reads["write_attempted"] or preflight_reads["corpus_read_attempted"]:
        raise ValueError("Ordinary preflight attempted a forbidden operation")
    resources = declared_resources(preflight)
    extra_paths = [*preflight_reads["paths"], *(ROOT / row["path"] for row in resources)]
    snapshot, raw = source_snapshot(corpus, extra_paths)
    preflight_sha256 = digest(canonical(preflight))
    inputs = {"fixture_version": FIXTURE_VERSION, "scope": "synthetic_development_cost_only",
              "ordinary_route": deepcopy(ROUTE_INPUT), "retrieval_query": deepcopy(QUERY),
              "retrieval_options": {"top_k": 1, "mode": "structural", "excluded_origins": []},
              "expected_case_ids": ["CM-SYN-003"]}
    rows = []
    for name, operation, forbidden, status in (
        ("ordinary_route_extensions_off", lambda: resolve_runtime(**deepcopy(inputs["ordinary_route"])), True, None),
        ("explicit_retrieval_off", lambda: retrieval.capture_query(deepcopy(inputs["retrieval_query"]), corpus,
                                                                  enabled=False, top_k=1), True, "off"),
        ("explicit_retrieval_on", lambda: retrieval.capture_query(deepcopy(inputs["retrieval_query"]), corpus,
                                                                 top_k=1), False, "matches"),
    ):
        samples = []
        resources = []
        read_set = {}
        bindings = {}
        for _ in range(repeats):
            observed = sample(operation, corpus, forbid_corpus=forbidden, expected_status=status)
            value = observed.pop("value")
            paths = observed.pop("_observed_paths")
            if any(_read_alias(path, corpus) not in raw for path in paths):
                raise ValueError("A measured operation read an input outside its frozen read set")
            if name == "ordinary_route_extensions_off":
                if observed["returned_sha256"] != preflight_sha256:
                    raise ValueError("Ordinary route changed after its dependency preflight")
                current_resources = declared_resources(value)
                if any(row["sha256"] != digest(raw[row["path"]]) for row in current_resources):
                    raise ValueError("Declared route resources changed after identity capture")
                if resources and current_resources != resources:
                    raise ValueError("Ordinary route resources changed during measurement")
                resources = current_resources
            elif name == "explicit_retrieval_on":
                if value["bindings"].get("query_sha256") != digest(canonical(inputs["retrieval_query"])):
                    raise ValueError("Retrieval result is not bound to the frozen query")
                if [match["case_id"] for match in value["matches"]] != inputs["expected_case_ids"]:
                    raise ValueError("The frozen synthetic fixture did not return its declared case")
                if read_set and (read_set != value["read_set"] or bindings != value["bindings"]):
                    raise ValueError("Retrieval input identities changed between samples")
                read_set, bindings = value["read_set"], value["bindings"]
            if samples and observed["returned_sha256"] != samples[0]["returned_sha256"]:
                raise ValueError("An operation returned inconsistent results for fixed inputs")
            samples.append(observed)
        rows.append({"id": name, "samples": samples,
                     "median_elapsed_ns": median(row["elapsed_ns"] for row in samples),
                     "max_python_allocation_peak_bytes": max(row["python_allocation_peak_bytes"] for row in samples),
                     "declared_skill_resources": resources,
                     "declared_skill_resource_bytes": sum(row["bytes"] for row in resources),
                     "retrieval_read_set": read_set, "retrieval_bindings": bindings})
    if head_identity() != identity:
        raise ValueError("Measured checkout changed before evidence was finalized")
    assert_frozen_files(corpus, raw)
    return {"schema_version": 1, "measurement": "e1_bounded_extension_resource_observation",
            **identity, **snapshot, "environment": {
                "python": platform.python_version(), "platform": platform.platform(),
                "yaml_loader": safe_yaml.loader_name(), "initial_driver_imports_excluded": True,
                "ordinary_dependency_preflight_excluded": True,
                "parse_cache_cleared_before_each_operation": True},
            "repeats": repeats, "inputs": inputs, "inputs_sha256": digest(canonical(inputs)),
            "driver_sha256": snapshot["files"]["scripts/measure_e1_resources.py"]["sha256"],
            "rows": rows, "performance_gate": "not_assessed_no_prefrozen_time_or_memory_threshold",
            "independent_modeling_quality": "not_assessed", "solver_performance": "not_assessed",
            "interpretation": {
                "elapsed": "Observed operation including serialization, allocation tracing, read instrumentation and any remaining lazy imports; excludes initial driver imports, ordinary dependency preflight, source identity capture, cache clearing, declared-resource enumeration, queue and setup.",
                "memory": "Fresh tracemalloc peak of Python allocations during each operation; excludes existing imports and native allocations; not total process RSS.",
                "reads": "Real Path.open call counts within each operation. Declared resource bytes describe unique load_order files, not actual context tokens or physical disk I/O; identity capture reads the corpus outside off-operation measurements.",
                "comparison": "Different bounded operations in one current checkout; no historic-baseline speedup, full-regression cost reduction, contest-solver timing or quality claim.",
                "scope": "No project root, project writer, model approval, accepted workbook, numerical run or public case import is involved."}}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args(argv)
    report = measure(repeats=arguments.repeats)
    text = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if arguments.output is not None:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
