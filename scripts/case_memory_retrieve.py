#!/usr/bin/env python3
"""Bounded offline retrieval of current synthetic case patterns; no project writes."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from typing import Any

from jsonschema import Draft202012Validator
import case_memory as memory

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS_ROOT = memory.DEFAULT_CORPUS_ROOT
AUTHORITY_PATH = ROOT / "core/case_memory_retrieval_contract.yaml"
TAXONOMY_PATH = ROOT / "core/task_taxonomy.yaml"
SCRIPT_PATH = Path(__file__).resolve()
D1_SCRIPT_PATH = ROOT / "scripts/case_memory.py"
HELPER_PATH = ROOT / "scripts/safe_yaml.py"
PROTOCOL_VERSION = "1.0.0"
SUPPORTED_CONTRACT_SHA256 = "f5156422cba89433934515693cba3de6d7047eca3252d9659b8388d10ca8c615"
HARD_LIMITS = {"file_bytes": 262144, "total_bytes": 2097152, "depth": 32,
               "nodes": 32768, "string_chars": 8192, "query_bytes": 16384,
               "report_bytes": 16384, "evaluation_bytes": 65536, "top_k": 5, "features": 64, "queries": 32}


class RetrievalError(ValueError):
    """Fixed diagnostics never include supplied text, identifiers or filesystem paths."""

    def __init__(self, code: str, message: str):
        self.code, self.message = code, message
        super().__init__(f"{code}: {message}")

    def diagnostic(self) -> dict:
        return {"code": self.code, "message": self.message}


def _hash(value: Any) -> str:
    return hashlib.sha256(memory._canonical(value)).hexdigest()


def _report_size(value: Any) -> int:
    return len((json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                           allow_nan=False) + "\n").encode("utf-8"))


def case_sha256(case: dict) -> str:
    """Canonical current case identity used by projections and explicit references."""
    return _hash(case)


def _read_bytes(path: Path, limit: int) -> bytes:
    return memory._read_bytes(path, limit)


# Fingerprint the implementations actually imported by this process. A changed
# file must not be reported as the implementation of an older cached module.
_LOADED_IMPLEMENTATIONS = {alias: memory._read_bytes(path, HARD_LIMITS["file_bytes"])
                          for alias, path in (("scripts/case_memory_retrieve.py", SCRIPT_PATH),
                                              ("scripts/case_memory.py", D1_SCRIPT_PATH),
                                              ("scripts/safe_yaml.py", HELPER_PATH))}


class _SkillReads:
    def __init__(self):
        self.raw: dict[str, tuple[Path, bytes]] = {}

    def read(self, alias: str, path: Path, limits: dict) -> bytes:
        path = Path(path).absolute()
        raw = _read_bytes(memory._path(path.parent, path.name), limits["file_bytes"])
        if alias in self.raw and self.raw[alias] != (path, raw):
            raise RetrievalError("source_changed", "a retrieval resource changed during capture")
        self.raw[alias] = (path, raw)
        return raw

    def recheck(self, limits: dict) -> None:
        for path, previous in self.raw.values():
            if _read_bytes(memory._path(path.parent, path.name), limits["file_bytes"]) != previous:
                raise RetrievalError("source_changed", "a retrieval resource changed before consumption")

    def hashes(self) -> dict:
        # Aliases describe resource roles. Exact roots and paths remain in this snapshot.
        return {name: hashlib.sha256(raw).hexdigest() for name, (_, raw) in sorted(self.raw.items())}


class RetrievalSnapshot:
    """One protected read set; assert_current checks actual corpus and package paths.

    Public read_set is scoped by corpus/package resource aliases, including when
    a caller supplies a corpus outside the installed Skill root. It is not an
    instruction to resolve corpus aliases against the Skill root.
    """

    def __init__(self, report: dict, *, corpus=None, skill=None, limits=None,
                 records=None, bindings=None):
        self._report = deepcopy(report)
        self._corpus, self._skill = corpus, skill
        self._limits = limits or HARD_LIMITS
        self._records = deepcopy(records or {})
        self._bindings = deepcopy(bindings or {})

    @property
    def report(self) -> dict:
        return deepcopy(self._report)

    @property
    def bindings(self) -> dict:
        return deepcopy(self._bindings)

    @property
    def read_set(self) -> dict:
        return {"corpus": self._corpus.read_set() if self._corpus else {},
                "skill": self._skill.hashes() if self._skill else {}}

    def assert_current(self) -> None:
        try:
            if self._corpus:
                self._corpus.recheck(self._limits)
            if self._skill:
                self._skill.recheck(self._limits)
        except Exception:
            raise RetrievalError("source_changed", "retrieval inputs changed; capture a fresh snapshot") from None

    def case(self, case_id: str) -> dict:
        if not isinstance(case_id, str) or case_id not in self._records:
            raise RetrievalError("case_unavailable", "the referenced case is not currently admitted and reviewed")
        return deepcopy(self._records[case_id])


def _base(status: str) -> dict:
    return {"status": status, "protocol_version": PROTOCOL_VERSION, "matches": [],
            "errors": [], "excluded": [], "bindings": {}, "read_set": {"corpus": {}, "skill": {}},
            "execution_authorized": False, "independent_performance": "not_assessed"}


def _failed(error: Exception, status: str) -> RetrievalSnapshot:
    if isinstance(error, (RetrievalError, memory.CaseMemoryError)):
        code = error.code
    else:
        code = "read_error"
    messages = {
        "query_invalid": "query does not match the bounded current retrieval protocol",
        "options_invalid": "retrieval options are outside the supported protocol",
        "authority_invalid": "retrieval Authority is invalid or unsupported",
        "taxonomy_invalid": "current taxonomy is invalid or unsupported",
        "features_invalid": "retrieval projection does not match its closed contract",
        "features_stale": "retrieval projection is not bound to current admitted source and case bytes",
        "feature_anchor_missing": "retrieval projection requires a current source section",
        "feature_anchor_mismatch": "a retrieval term is not supported by its current source section",
        "feature_missing": "an admitted case has no current applicability projection",
        "source_changed": "retrieval inputs changed; capture a fresh snapshot",
        "index_missing": "current derived index is missing; use the repository generator",
        "index_stale": "derived index is stale; rebuild before retrieval",
        "budget_exceeded": "bounded retrieval input or output budget exceeded",
        "privacy_violation": "retrieval material contains sensitive publication content",
    }
    report = _base(status)
    report["errors"] = [{"code": code, "message": messages.get(code, "retrieval resources could not be safely consumed")}]
    return RetrievalSnapshot(report)


def _authority(skill: _SkillReads) -> tuple[dict, dict, dict]:
    try:
        contract = memory._schema_document(skill.read("core/case_memory_retrieval_contract.yaml", AUTHORITY_PATH, HARD_LIMITS))
        memory._tree(contract, HARD_LIMITS)
        memory._local_refs(contract)
        identity = deepcopy(contract)
        identity["x-retrieval"]["limits"] = HARD_LIMITS
        if _hash(identity) != SUPPORTED_CONTRACT_SHA256:
            raise RetrievalError("authority_invalid", "unsupported retrieval Authority identity")
        policy = contract["x-retrieval"]
        limits = policy["limits"]
        if set(limits) != set(HARD_LIMITS) or any(type(value) is not int or not 0 < value <= HARD_LIMITS[key]
                                               for key, value in limits.items()):
            raise RetrievalError("authority_invalid", "invalid retrieval limits")
        if any(len(raw) > limits["file_bytes"] for _, raw in skill.raw.values()):
            raise RetrievalError("budget_exceeded", "authority byte budget exceeded")
        Draft202012Validator.check_schema(contract)
        taxonomy = memory._schema_document(skill.read("core/task_taxonomy.yaml", TAXONOMY_PATH, limits))
        if taxonomy.get("taxonomy_version") != policy["taxonomy_version"] or any(
                not isinstance(taxonomy.get(axis), dict) for axis in ("objectives", "structures", "capabilities")):
            raise RetrievalError("taxonomy_invalid", "unsupported taxonomy")
        return contract, policy, taxonomy
    except (RetrievalError, memory.CaseMemoryError):
        raise
    except Exception:
        raise RetrievalError("authority_invalid", "invalid retrieval Authority") from None


def _validate(contract: dict, key: str, value: Any, limits: dict, code: str) -> None:
    try:
        memory._tree(value, limits)
        if next(Draft202012Validator(contract).iter_errors({key: value}), None):
            raise RetrievalError(code, "document does not match the closed retrieval contract")
    except (RetrievalError, memory.CaseMemoryError):
        raise
    except Exception:
        raise RetrievalError(code, "invalid retrieval document") from None


def _query(contract: dict, taxonomy: dict, query: Any, limits: dict) -> None:
    _validate(contract, "query", query, limits, "query_invalid")
    if (query["objective"] not in taxonomy["objectives"]
            or not set(query["structures"]).issubset(taxonomy["structures"])
            or not set(query["capabilities"]).issubset(taxonomy["capabilities"])):
        raise RetrievalError("query_invalid", "query taxonomy is unsupported")
    if len(memory._canonical(query)) > limits["query_bytes"]:
        raise RetrievalError("budget_exceeded", "query byte budget exceeded")


def _resources(corpus_root: Path, skill: _SkillReads, contract: dict, policy: dict, taxonomy: dict):
    limits = policy["limits"]
    report, corpus, admission = memory._inspect(corpus_root)
    memory._consume_index(report, corpus, admission)
    if any(len(raw) > limits["file_bytes"] for raw in corpus.raw.values()):
        raise RetrievalError("budget_exceeded", "admission inputs exceed the retrieval byte budget")
    sources = {row["id"]: row for row in memory._json(corpus.raw["sources.json"])["sources"]}
    cases = {row["id"]: row for row in report["eligible_cases"]}
    all_cases = {row["id"]: row for row in memory._json(corpus.raw["cases.json"])["cases"]}
    features = memory._json(corpus.read("retrieval_features.json", limits))
    _validate(contract, "features", features, limits, "features_invalid")
    if len(features["features"]) > limits["features"]:
        raise RetrievalError("budget_exceeded", "projection count budget exceeded")
    patterns = [re.compile(pattern) for pattern in admission["privacy_patterns"]]
    memory._screen(features, patterns, "corpus")
    projected = {}
    for feature in features["features"]:
        key = feature["case_id"]
        if key in projected:
            raise RetrievalError("features_invalid", "duplicate projection identity")
        projected[key] = feature
        # Withdrawn/draft cards may keep a projection, but it never enables them.
        if key not in cases:
            if key not in all_cases:
                raise RetrievalError("features_stale", "projection names a missing case")
            continue
        case, source = cases[key], sources[cases[key]["source"]["id"]]
        if (feature["case_version"] != case["version"] or feature["case_sha256"] != case_sha256(case)
                or feature["source_sha256"] != case["source"]["sha256"]):
            raise RetrievalError("features_stale", "projection source or case binding is stale")
        anchors = [item["source_anchor"] for item in feature["traits"].values()]
        anchors += [item["source_anchor"] for item in feature["required_conditions"] + feature["terms"]]
        if any(anchor not in source["sections"] for anchor in anchors):
            raise RetrievalError("feature_anchor_missing", "projection anchor is missing")
        if any(item["term"].casefold() not in source["sections"][item["source_anchor"]].casefold()
               for item in feature["terms"]):
            raise RetrievalError("feature_anchor_mismatch", "term has no support in its source section")
        conditions = [item["condition"] for item in feature["required_conditions"]]
        terms = [item["term"].casefold() for item in feature["terms"]]
        if len(set(conditions)) != len(conditions) or len(set(terms)) != len(terms):
            raise RetrievalError("features_invalid", "projection entries must be unique")
    if set(cases) - set(projected):
        raise RetrievalError("feature_missing", "current projection is missing")
    for alias, path in (("scripts/case_memory_retrieve.py", SCRIPT_PATH),
                        ("scripts/case_memory.py", D1_SCRIPT_PATH), ("scripts/safe_yaml.py", HELPER_PATH)):
        if skill.read(alias, path, limits) != _LOADED_IMPLEMENTATIONS[alias]:
            raise RetrievalError("source_changed", "loaded retrieval implementation differs from current bytes")
    total = corpus.total + sum(len(raw) for _, raw in skill.raw.values())
    nodes = sum(memory._tree(memory._json(corpus.raw[name]), limits) for name in
                ("sources.json", "cases.json", "index.json", "retrieval_features.json"))
    nodes += memory._tree(memory._schema_document(corpus.raw["schema.yaml"]), limits)
    nodes += memory._tree(contract, limits) + memory._tree(taxonomy, limits)
    if total > limits["total_bytes"] or nodes > limits["nodes"]:
        raise RetrievalError("budget_exceeded", "retrieval total budget exceeded")
    bindings = {"corpus_sha256": report["corpus_sha256"], "features_sha256": _hash(features),
                "authority_sha256": _hash(contract), "taxonomy_sha256": _hash(taxonomy),
                "retriever_sha256": _hash({name: sha for name, sha in skill.hashes().items() if name.startswith("scripts/")}),
                "filter_policy_sha256": _hash({"admission": memory.SUPPORTED_SCHEMA_SHA256,
                                               "retrieval": SUPPORTED_CONTRACT_SHA256}),
                "query_sha256": None, "filter_sha256": None}
    records = {}
    for group in report["groups"]:
        origins = sorted({sources[cases[key]["source"]["id"]]["origin_group"] for key in group["case_ids"]})
        for key in group["case_ids"]:
            case = cases[key]
            records[key] = {"case_id": key, "case_version": case["version"], "case_sha256": case_sha256(case),
                            "source_id": case["source"]["id"], "source_sha256": case["source"]["sha256"],
                            "origins": origins, "evidence_kind": "synthetic_example"}
    return report, corpus, projected, cases, records, bindings


def _options(enabled, top_k, excluded_origins, mode, policy) -> list[str]:
    if (type(enabled) is not bool or type(top_k) is not int or not 1 <= top_k <= policy["limits"]["top_k"]
            or mode not in policy["modes"] or not isinstance(excluded_origins, (list, tuple, set, frozenset))
            or len(excluded_origins) > 64 or any(not isinstance(origin, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", origin)
                                              for origin in excluded_origins)):
        raise RetrievalError("options_invalid", "unsupported retrieval options")
    return sorted(set(excluded_origins))


def _candidate(query: dict, case: dict, feature: dict, weights: dict, mode: str):
    if query["objective"] != case["structure"]["objective"]:
        return None, "objective_conflict"
    missing, matched, differences = [], [], []
    for name, projection in feature["traits"].items():
        actual, required = query["traits"][name], projection["value"]
        if actual != "unknown" and required != "unknown" and actual != required:
            return None, "typed_conflict"
        if actual == "unknown":
            missing.append(name)
        elif actual == required and required != "unknown":
            matched.append(name)
        elif required == "unknown":
            missing.append("case." + name)
            differences.append(name + ": case does not establish a variable or information assumption")
    for item in feature["required_conditions"]:
        condition = item["condition"]
        state = query["traits"]["conditions"].get(condition, "unknown")
        if state == "violated":
            return None, "condition_conflict"
        if state == "satisfied":
            matched.append(condition)
        else:
            missing.append(condition)
    q_structures, c_structures = set(query["structures"]), set(case["structure"]["structures"])
    if q_structures and c_structures and not q_structures.intersection(c_structures):
        return None, "structure_conflict"
    differences += ["structure:" + value for value in sorted(q_structures.symmetric_difference(c_structures))]
    q_caps, c_caps = set(query["capabilities"]), set(case["structure"]["capabilities"])
    differences += ["capability:" + value for value in sorted(q_caps.symmetric_difference(c_caps))]
    matched += ["objective:" + query["objective"]]
    matched += ["structure:" + value for value in sorted(q_structures & c_structures)]
    matched += ["capability:" + value for value in sorted(q_caps & c_caps)]
    terms = [item["term"].casefold() for item in feature["terms"]]
    lexical = sum(term in query["summary"].casefold() for term in terms)
    components = {"objective": weights["objective"], "structures": len(q_structures & c_structures) * weights["structures"],
                  "capabilities": len(q_caps & c_caps) * weights["capabilities"],
                  "typed": sum(name in matched for name in feature["traits"]) * weights["typed"],
                  "conditions": sum(item["condition"] in matched for item in feature["required_conditions"]) * weights["conditions"],
                  "lexical": lexical * weights["lexical"]}
    if mode == "lexical":
        components = {key: value if key == "lexical" else 0 for key, value in components.items()}
        if not lexical:
            return None, "no_lexical_overlap"
    return {"score": sum(components.values()), "score_components": components,
            "compatibility": "conditional" if missing else "compatible", "matched_features": sorted(matched),
            "differences": differences, "missing_conditions": sorted(missing),
            "forbidden_transfers": deepcopy(case["transfer"]["prohibited_transfers"]),
            "rationale": "Synthetic applicability pattern; verify missing conditions and current model design before transfer."}, None


def _finish(snapshot: RetrievalSnapshot) -> RetrievalSnapshot:
    snapshot.assert_current()
    report = snapshot._report
    report["bindings"], report["read_set"] = snapshot.bindings, snapshot.read_set
    if _report_size(report) > snapshot._limits["report_bytes"]:
        raise RetrievalError("budget_exceeded", "retrieval report byte budget exceeded")
    return snapshot


def capture_current(corpus_root: Path = DEFAULT_CORPUS_ROOT) -> RetrievalSnapshot:
    """Capture current case bindings without inventing or replaying a query."""
    try:
        skill = _SkillReads()
        contract, policy, taxonomy = _authority(skill)
        _, corpus, _, _, records, bindings = _resources(corpus_root, skill, contract, policy, taxonomy)
        return _finish(RetrievalSnapshot(_base("current"), corpus=corpus, skill=skill,
                                        limits=policy["limits"], records=records, bindings=bindings))
    except Exception as error:
        return _failed(error, "unavailable")


def capture_query(query: dict, corpus_root: Path = DEFAULT_CORPUS_ROOT, *, enabled: bool = True,
                  top_k: int = 3, excluded_origins=(), mode: str = "structural") -> RetrievalSnapshot:
    """Capture, filter and rank once. Disabled retrieval performs no resource reads."""
    if enabled is False:
        return RetrievalSnapshot(_base("off"))
    stage = "blocked"
    try:
        skill = _SkillReads()
        contract, policy, taxonomy = _authority(skill)
        exclusions = _options(enabled, top_k, excluded_origins, mode, policy)
        _query(contract, taxonomy, query, policy["limits"])
        query = deepcopy(query)
        _query(contract, taxonomy, query, policy["limits"])
        stage = "unavailable"
        admission, corpus, features, cases, records, bindings = _resources(corpus_root, skill, contract, policy, taxonomy)
        bindings["query_sha256"] = _hash(query)
        bindings["filter_sha256"] = _hash({"filter_policy_sha256": bindings["filter_policy_sha256"],
                                         "excluded_origins": exclusions, "mode": mode, "top_k": top_k})
        result = _base("no_match")
        for group in admission["groups"]:
            key = group["case_ids"][0]
            if set(records[key]["origins"]) & set(exclusions):
                result["excluded"].append({"case_id": key, "reason": "origin_excluded"})
                continue
            candidates, reasons = [], []
            for member in group["case_ids"]:
                candidate, reason = _candidate(query, cases[member], features[member], policy["weights"], mode)
                if candidate is not None:
                    candidates.append({**records[member], **candidate})
                else:
                    reasons.append(reason)
            if not candidates:
                result["excluded"].append({"case_id": key, "reason": sorted(set(reasons))[0]})
            else:
                result["matches"].append(sorted(candidates, key=lambda item: (-item["score"], item["case_id"]))[0])
        result["matches"] = sorted(result["matches"], key=lambda item: (-item["score"], item["case_id"]))[:top_k]
        result["status"] = "matches" if result["matches"] else "no_match"
        result["mode"] = mode
        return _finish(RetrievalSnapshot(result, corpus=corpus, skill=skill, limits=policy["limits"],
                                        records=records, bindings=bindings))
    except Exception as error:
        return _failed(error, stage)


def query_cases(query: dict, corpus_root: Path = DEFAULT_CORPUS_ROOT, *, enabled: bool = True,
                top_k: int = 3, excluded_origins=(), mode: str = "structural") -> dict:
    return capture_query(query, corpus_root, enabled=enabled, top_k=top_k,
                         excluded_origins=excluded_origins, mode=mode).report


def evaluate(corpus_root: Path = DEFAULT_CORPUS_ROOT) -> dict:
    """Measure the declared development suite; no independent performance claim."""
    try:
        baseline = capture_current(corpus_root)
        if baseline.report["status"] != "current":
            return baseline.report
        suite_path = memory._path(Path(corpus_root).absolute(), "development_queries.json")
        suite_raw = _read_bytes(suite_path, HARD_LIMITS["file_bytes"])
        skill = _SkillReads()
        contract, policy, taxonomy = _authority(skill)
        suite = memory._json(suite_raw)
        _validate(contract, "development", suite, policy["limits"], "query_invalid")
        total = baseline._corpus.total + sum(len(raw) for _, raw in baseline._skill.raw.values()) + len(suite_raw)
        nodes = sum(memory._tree(memory._json(baseline._corpus.raw[name]), policy["limits"]) for name in
                    ("sources.json", "cases.json", "index.json", "retrieval_features.json"))
        admission_schema = memory._schema_document(baseline._corpus.raw["schema.yaml"])
        nodes += sum(memory._tree(value, policy["limits"]) for value in (admission_schema, contract, taxonomy, suite))
        if (len(suite_raw) > policy["limits"]["file_bytes"] or total > policy["limits"]["total_bytes"]
                or nodes > policy["limits"]["nodes"]):
            raise RetrievalError("budget_exceeded", "development input total budget exceeded")
        memory._screen(suite, [re.compile(pattern) for pattern in admission_schema["x-admission"]["privacy_patterns"]], "corpus")
        ids = [entry["id"] for entry in suite["queries"]]
        if len(ids) != len(set(ids)):
            raise RetrievalError("query_invalid", "development query identities must be unique")
        if len(suite["queries"]) > policy["limits"]["queries"]:
            raise RetrievalError("budget_exceeded", "development query budget exceeded")
        rows = []
        known_origins = {origin for record in baseline._records.values() for origin in record["origins"]}
        for entry in suite["queries"]:
            _query(contract, taxonomy, entry["query"], policy["limits"])
            declared_origins = set(entry["derived_origins"])
            expected_origins = {origin for key in entry["expected_case_ids"]
                                for origin in baseline.case(key)["origins"]}
            if not expected_origins.issubset(declared_origins) or not declared_origins.issubset(known_origins):
                raise RetrievalError("query_invalid", "development expectations and origins are not bound to the current library")
            for mode in ("off", "lexical", "structural"):
                start = time.perf_counter_ns()
                snapshot = capture_query(entry["query"], corpus_root, enabled=mode != "off",
                                         mode="structural" if mode == "off" else mode)
                elapsed = time.perf_counter_ns() - start
                report = snapshot.report
                if mode != "off" and report["status"] not in ("matches", "no_match"):
                    return report
                if mode != "off" and any(snapshot.bindings[key] != baseline.bindings[key] for key in
                        ("corpus_sha256", "features_sha256", "authority_sha256", "taxonomy_sha256", "retriever_sha256")):
                    raise RetrievalError("source_changed", "development capture changed")
                ids = [item["case_id"] for item in report["matches"]]
                expected = entry["expected_case_ids"]
                rows.append({"query_id": entry["id"], "mode": mode, "status": report["status"],
                             "returned_case_ids": ids, "expected_recalled": bool(set(ids) & set(expected)) if expected else None,
                             "unexpected_recommendations": len(set(ids) - set(expected)),
                             "missing_condition_count": sum(len(item["missing_conditions"]) for item in report["matches"]),
                             "context_utf8_bytes": _report_size(report), "elapsed_ns": elapsed,
                             "derived_origins": entry["derived_origins"], "independent_eligible": False})
        baseline.assert_current()
        skill.recheck(policy["limits"])
        if _read_bytes(memory._path(Path(corpus_root).absolute(), "development_queries.json"),
                       policy["limits"]["file_bytes"]) != suite_raw:
            raise RetrievalError("source_changed", "development suite changed")
        result = {"status": "development_evaluated", "protocol_version": PROTOCOL_VERSION,
                "evaluation_scope": "seed_derived_development_only", "rows": rows,
                "independent_performance": {"status": "not_assessed", "recall": None, "error_rate": None},
                "execution_authorized": False, "bindings": baseline.bindings,
                "suite_sha256": _hash(suite), "errors": []}
        if _report_size(result) > policy["limits"]["evaluation_bytes"]:
            raise RetrievalError("budget_exceeded", "development report byte budget exceeded")
        return result
    except Exception as error:
        return _failed(error, "unavailable").report


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("query", "evaluate"))
    parser.add_argument("--query", type=Path)
    parser.add_argument("--corpus-root", type=Path, default=DEFAULT_CORPUS_ROOT)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--exclude-origin", action="append", default=[])
    parser.add_argument("--mode", choices=("structural", "lexical"), default="structural")
    parser.add_argument("--disabled", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "evaluate":
            result = evaluate(args.corpus_root)
        elif args.disabled:
            result = query_cases({}, enabled=False)
        elif args.query is None:
            raise RetrievalError("query_invalid", "query file is required")
        else:
            path = args.query.absolute()
            query = memory._json(_read_bytes(memory._path(path.parent, path.name), HARD_LIMITS["query_bytes"]))
            result = query_cases(query, args.corpus_root, top_k=args.top_k,
                                 excluded_origins=args.exclude_origin, mode=args.mode)
    except Exception as error:
        result = _failed(error, "blocked").report
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False))
    return 1 if result["status"] in ("blocked", "unavailable") else 0


if __name__ == "__main__":
    raise SystemExit(main())
