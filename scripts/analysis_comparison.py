"""Pure, bounded comparison-scope, frozen-plan and captured-XLSX inspection.

No task execution, source qualification, project writes or runtime imports live here.
Coordinators capture inputs and decide acceptance; this module checks declared records.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import hashlib
import json
import re
from typing import Any, Mapping

import yaml
from claim_values import EvidenceError, converted, derive, number, unit_info
from claim_workbook import Workbook
from semantic_identity import canonical_semantic_identity, semantic_identity_hash

VERSION = "1.0.0"
KINDS = {"model_comparison": "多模型检验", "algorithm_comparison": "同模型多算法检验"}
PROTOCOL_FIELD = "analysis_comparison_protocol_version"
PLAN_FIELD = "analysis_comparison_plan_sha256"
SHA = re.compile(r"^[0-9a-f]{64}$")
QUESTION = re.compile(r"^Q[1-9][0-9]*$")
PURE_ALGORITHM_KEYS = {"family", "method", "solver", "solver_role", "implementation", "backend"}
REVIEW_ROLES = {"positive_fitness_review", "adversarial_model_challenge"}
REGISTRY_FIELDS = {
    "protocol_version", "scope_ref", "scope_sha256", "baseline_semantic_identity_hash",
    "approval_binding", "checks",
}
CHECK_FIELDS = {
    "id", "kind", "requirement", "requirement_source", "question", "target_claim",
    "baseline_ref", "candidate_refs", "criterion", "evidence_refs", "disposition_ref", "retirement",
}
SELECTOR_FIELDS = {
    "sheet", "header_row", "row_key", "expected_cardinality", "value_type",
    "identity_columns", "value_column", "unit",
}


class ComparisonError(ValueError):
    """Unknown, ambiguous or internally inconsistent comparison declaration."""


class _UniqueLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        keys = [self.construct_object(key, deep=deep) for key, _ in node.value]
        if any(not isinstance(key, str) for key in keys) or len(keys) != len(set(keys)):
            raise ComparisonError("comparison YAML requires unique text mapping keys")
        return super().construct_mapping(node, deep=deep)


def _mapping(value, required, allowed=None, label="record"):
    if not isinstance(value, Mapping):
        raise ComparisonError(f"{label} must be a mapping")
    missing = set(required) - set(value)
    unknown = set(value) - set(allowed if allowed is not None else required)
    if missing or unknown:
        raise ComparisonError(f"{label}: missing {sorted(missing)}, unknown {sorted(unknown)}")
    return value


def _text(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 4096:
        raise ComparisonError(f"{label} must be bounded nonempty text")
    return value


def _strings(value, label, *, nonempty=True):
    if not isinstance(value, list) or (nonempty and not value) or len(value) > 128:
        raise ComparisonError(f"{label} must be a bounded text list")
    if any(not isinstance(item, str) or not item.strip() for item in value) or len(value) != len(set(value)):
        raise ComparisonError(f"{label} requires unique nonempty text")
    return value


def _index(rows, label):
    if not isinstance(rows, list) or len(rows) > 128:
        raise ComparisonError(f"{label} must be a bounded list")
    result = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise ComparisonError(f"{label} entries must be mappings")
        identifier = _text(row.get("id"), label + " ID")
        if identifier in result:
            raise ComparisonError(f"duplicate {label} ID: {identifier}")
        result[identifier] = row
    return result


def _hash(value):
    try:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError, RecursionError) as exc:
        raise ComparisonError("comparison identity is not finite JSON data") from exc
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def extract_specs(framework_text: str, question: str) -> dict:
    """Read one strict, independent block outside the primary semantic-text scope."""
    if not QUESTION.fullmatch(question):
        raise ComparisonError("invalid comparison question ID")
    begin = f"<!-- HSK_ANALYSIS_COMPARISON_BEGIN {question} -->"
    end = f"<!-- HSK_ANALYSIS_COMPARISON_END {question} -->"
    if framework_text.count(begin) != 1 or framework_text.count(end) != 1:
        raise ComparisonError(f"{question}: exactly one comparison marker pair is required")
    start = framework_text.index(begin)
    stop = framework_text.index(end)
    if stop < start:
        raise ComparisonError("comparison marker order is invalid")
    headings = list(re.finditer(r"(?m)^###\s+(Q[1-9][0-9]*)[:：]", framework_text))
    containing = [match for match in headings if match.start() < start]
    if not containing or containing[-1].group(1) != question:
        raise ComparisonError("comparison block is outside its question section")
    section_start = containing[-1].start()
    next_heading = next((match.start() for match in headings if match.start() > section_start), len(framework_text))
    result_start = framework_text.find("#### 结果摘要", section_start, next_heading)
    if result_start < 0 or start < result_start or stop >= next_heading:
        raise ComparisonError("comparison block must follow 结果摘要 in its own question section")
    raw = framework_text[start + len(begin):stop].strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines[0] not in {"```yaml", "```yml"} or lines[-1] != "```":
            raise ComparisonError("comparison YAML fence is incomplete")
        raw = "\n".join(lines[1:-1])
    if len(raw.encode("utf-8")) > 2097152:
        raise ComparisonError("comparison block byte budget exceeded")
    try:
        events = list(yaml.parse(raw))
        depth = 0
        for event in events:
            if isinstance(event, yaml.AliasEvent) or getattr(event, "anchor", None):
                raise ComparisonError("comparison YAML aliases/anchors are forbidden")
            if isinstance(event, (yaml.MappingStartEvent, yaml.SequenceStartEvent)):
                depth += 1
                if depth > 32:
                    raise ComparisonError("comparison YAML depth budget exceeded")
            elif isinstance(event, (yaml.MappingEndEvent, yaml.SequenceEndEvent)):
                depth -= 1
        specs = yaml.load(raw, Loader=_UniqueLoader)
    except yaml.YAMLError as exc:
        raise ComparisonError("invalid comparison YAML") from exc
    canonical_scope(specs, question=question)
    return deepcopy(specs)


def mathematical_projection(identity: Mapping[str, Any], pure_algorithm_keys=()) -> dict:
    """Keep all math/unknown extensions; only reviewed scalar implementation keys may leave."""
    canonical = canonical_semantic_identity(identity)
    keys = _strings(list(pure_algorithm_keys), "pure_algorithm_keys", nonempty=False)
    if set(keys) - PURE_ALGORITHM_KEYS:
        raise ComparisonError("unknown/mathematical algorithm keys cannot be excluded")
    algorithm = canonical["algorithm_semantics"]
    for key in keys:
        if key not in algorithm or not isinstance(algorithm[key], str):
            raise ComparisonError("excluded implementation key must be present scalar text")
    canonical["algorithm_semantics"] = {key: value for key, value in algorithm.items() if key not in keys}
    return canonical


def canonical_scope(specs: Mapping[str, Any], *, question=None) -> dict:
    _mapping(specs, {"protocol_version", "question", "baseline_semantic_identity_hash", "models", "algorithms", "questions"}, label="comparison scope")
    if specs["protocol_version"] != VERSION or not QUESTION.fullmatch(str(specs["question"])):
        raise ComparisonError("unsupported comparison scope version/question")
    if question is not None and specs["question"] != question:
        raise ComparisonError("comparison scope question mismatch")
    if not isinstance(specs["baseline_semantic_identity_hash"], str) or not SHA.fullmatch(specs["baseline_semantic_identity_hash"]):
        raise ComparisonError("comparison baseline must be a current structured identity")
    models = _index(specs["models"], "model")
    algorithms = _index(specs["algorithms"], "algorithm")
    questions = _index(specs["questions"], "comparison question")
    if not models or not questions:
        raise ComparisonError("comparison scope requires models and comparison questions")
    canonical = deepcopy(dict(specs))
    normalized_models = []
    for identifier, model in models.items():
        _mapping(model, {"id", "identity", "pure_algorithm_keys"}, label=identifier)
        if not isinstance(model["identity"], Mapping):
            raise ComparisonError("comparator identity must be a complete mathematical mapping")
        if model["identity"].get("question") != specs["question"]:
            raise ComparisonError("comparator mathematical definition has wrong question")
        mathematical_projection(model["identity"], model["pure_algorithm_keys"])
        normalized_models.append({"id": identifier, "identity": canonical_semantic_identity(model["identity"]),
                                  "pure_algorithm_keys": sorted(model["pure_algorithm_keys"])})
    matched = [model for model in models.values() if semantic_identity_hash(model["identity"]) == specs["baseline_semantic_identity_hash"]]
    if len(matched) != 1:
        raise ComparisonError("scope must contain exactly one complete current primary SIB")
    main_model = matched[0]["id"]
    for identifier, algorithm in algorithms.items():
        _mapping(algorithm, {"id", "model_ref", "definition", "implementation_anchor"}, label=identifier)
        if algorithm["model_ref"] not in models:
            raise ComparisonError("algorithm references an unknown mathematical model")
        _mapping(algorithm["definition"], {"family", "update_rule", "stop_rule"}, label="algorithm definition")
        for field in ("family", "update_rule", "stop_rule"):
            _text(algorithm["definition"][field], "algorithm " + field)
        _text(algorithm["implementation_anchor"], "algorithm implementation anchor")
    for identifier, item in questions.items():
        _mapping(item, {"id", "kind", "baseline_ref", "candidate_refs", "question", "target_claim", "evaluation"}, label=identifier)
        if item["kind"] not in KINDS:
            raise ComparisonError("unknown comparison type")
        _strings(item["candidate_refs"], "candidate_refs")
        _text(item["question"], "comparison question")
        _text(item["target_claim"], "comparison target claim")
        evaluation = _mapping(item["evaluation"], {"id", "metric", "unit", "direction", "fixed_axes", "allowed_changes"}, label="evaluation protocol")
        for field in ("id", "metric", "unit"):
            _text(evaluation[field], "evaluation " + field)
        if evaluation["direction"] not in {"higher", "lower"}:
            raise ComparisonError("evaluation metric direction is required")
        _strings(evaluation["fixed_axes"], "fixed_axes", nonempty=False)
        if any(axis in {"metric", "model", "algorithm"} or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", axis) for axis in evaluation["fixed_axes"]):
            raise ComparisonError("fixed axes must name observed noncomparison axes")
        _strings(evaluation["allowed_changes"], "allowed_changes", nonempty=False)
        objects = models if item["kind"] == "model_comparison" else algorithms
        refs = [item["baseline_ref"], *item["candidate_refs"]]
        if any(ref not in objects for ref in refs) or len(refs) != len(set(refs)):
            raise ComparisonError("comparison requires distinct known object references")
        if item["kind"] == "model_comparison":
            if item["baseline_ref"] != main_model:
                raise ComparisonError("model comparison baseline must be current primary model")
            base = mathematical_projection(models[item["baseline_ref"]]["identity"], models[item["baseline_ref"]]["pure_algorithm_keys"])
            for ref in item["candidate_refs"]:
                if set(models[ref]["pure_algorithm_keys"]) != set(models[item["baseline_ref"]]["pure_algorithm_keys"]):
                    raise ComparisonError("model comparison requires a common reviewed implementation-key partition")
                candidate = mathematical_projection(models[ref]["identity"], models[ref]["pure_algorithm_keys"])
                if _hash(base) == _hash(candidate):
                    raise ComparisonError("identical mathematical declarations cannot count as different models")
        else:
            if any(algorithms[ref]["model_ref"] != main_model for ref in refs):
                raise ComparisonError("algorithm comparison must reference the same original primary model")
            definitions = [_hash(algorithms[ref]["definition"]["update_rule"]) for ref in refs]
            if len(definitions) != len(set(definitions)):
                raise ComparisonError("duplicate algorithm definitions do not establish multiple methods")
    canonical["models"] = sorted(normalized_models, key=lambda item: item["id"])
    canonical["algorithms"] = sorted(canonical["algorithms"], key=lambda item: item["id"])
    canonical["questions"] = sorted(canonical["questions"], key=lambda item: item["id"])
    for item in canonical["questions"]:
        item["candidate_refs"] = sorted(item["candidate_refs"])
        item["evaluation"]["fixed_axes"] = sorted(item["evaluation"]["fixed_axes"])
    return canonical


def scope_sha256(specs: Mapping[str, Any]) -> str:
    return _hash(canonical_scope(specs))


def enabled(entry: Mapping[str, Any], config=None, receipt=None) -> bool:
    if "analysis_comparison" in entry:
        return True
    methods = entry.get("analysis_methods", [])
    if isinstance(methods, list) and any(item in set(KINDS) | set(KINDS.values()) for item in methods):
        return True
    return any(isinstance(record, Mapping) and (PROTOCOL_FIELD in record or PLAN_FIELD in record) for record in (config, receipt))


active = enabled


def _selector(source, label):
    _mapping(source, {"source", "selector"}, label=label)
    if source["source"] not in {"primary", "analysis"}:
        raise ComparisonError("comparison values must come from primary/analysis captured workbooks")
    selector = _mapping(source["selector"], SELECTOR_FIELDS, label=label + " selector")
    if type(selector["header_row"]) is not int or selector["header_row"] < 1 or selector["expected_cardinality"] != 1 or type(selector["expected_cardinality"]) is not int:
        raise ComparisonError("comparison selectors require one exact physical row")
    if selector["value_type"] != "scalar":
        raise ComparisonError("comparison arithmetic requires scalar numeric selectors")
    if not isinstance(selector["row_key"], Mapping) or not selector["row_key"]:
        raise ComparisonError("comparison row key must be explicit")
    if not isinstance(selector["identity_columns"], Mapping) or "metric" not in selector["identity_columns"]:
        raise ComparisonError("comparison metric must be an observed identity column")
    unit = _mapping(selector["unit"], {"kind"}, {"kind", "column"}, label="comparison unit")
    if unit["kind"] not in {"column", "header"} or (unit["kind"] == "column" and not isinstance(unit.get("column"), str)):
        raise ComparisonError("comparison unit must be explicit in workbook column/header")
    return source


def canonical_plan(plan: Mapping[str, Any], *, question: str, baseline_identity=None, scope_identity=None) -> dict:
    _mapping(plan, REGISTRY_FIELDS, label="analysis_comparison")
    if plan["protocol_version"] != VERSION or plan["scope_ref"] != question:
        raise ComparisonError("comparison registry version/scope mismatch")
    if not all(isinstance(plan[field], str) and SHA.fullmatch(plan[field]) for field in ("scope_sha256", "baseline_semantic_identity_hash")):
        raise ComparisonError("comparison registry has incomplete identity binding")
    if baseline_identity is not None and plan["baseline_semantic_identity_hash"] != baseline_identity:
        raise ComparisonError("comparison baseline identity is stale")
    if scope_identity is not None and plan["scope_sha256"] != scope_identity:
        raise ComparisonError("comparison scope identity is stale")
    checks = _index(plan["checks"], "comparison check")
    if not checks:
        raise ComparisonError("comparison registry must declare at least one check")
    normalized = []
    for identifier, check in checks.items():
        _mapping(check, CHECK_FIELDS - {"disposition_ref", "retirement"}, CHECK_FIELDS, label=identifier)
        if not re.fullmatch(r"CMP-" + re.escape(question) + r"-[0-9]{2,}", identifier):
            raise ComparisonError("comparison check ID must be question-scoped CMP-Qn-nn")
        if check["kind"] not in KINDS or check["requirement"] not in {"required", "exploratory", "retired"}:
            raise ComparisonError("unknown comparison type/requirement")
        for field in ("requirement_source", "question", "target_claim", "baseline_ref"):
            _text(check[field], "comparison " + field)
        _strings(check["candidate_refs"], "candidate_refs")
        criterion = _mapping(check["criterion"], {"id", "relation", "threshold", "unit", "source"}, {"id", "relation", "threshold", "unit", "source", "arithmetic_tolerance"}, label="comparison criterion")
        if criterion["relation"] not in {"le", "ge", "abs_le", "abs_ge"}:
            raise ComparisonError("unsupported bounded comparison relation")
        for field in ("id", "threshold", "unit", "source"):
            _text(criterion[field], "criterion " + field)
        try:
            threshold = Decimal(criterion["threshold"])
            tolerance = Decimal(criterion.get("arithmetic_tolerance", "0"))
        except (ArithmeticError, TypeError, ValueError) as exc:
            raise ComparisonError("criterion requires explicit finite decimal literals") from exc
        if not threshold.is_finite() or not tolerance.is_finite() or tolerance < 0:
            raise ComparisonError("criterion requires finite threshold/nonnegative arithmetic tolerance")
        evidence = _index(check["evidence_refs"], "comparison evidence")
        if check["requirement"] == "required" and not evidence:
            raise ComparisonError("required comparison must declare exact evidence selectors")
        for record in evidence.values():
            _mapping(record, {"id", "candidate_ref", "baseline", "candidate", "reported_baseline", "reported_difference", "operation"}, label="comparison evidence")
            if record["candidate_ref"] not in check["candidate_refs"]:
                raise ComparisonError("evidence candidate is outside declared comparison")
            for field in ("baseline", "candidate", "reported_baseline", "reported_difference"):
                _selector(record[field], field)
                if field != "baseline" and record[field]["source"] != "analysis":
                    raise ComparisonError("candidate/reported observations must come from analysis")
            op = _mapping(record["operation"], {"op", "comparison_axis"}, {"op", "comparison_axis", "direction"}, label="comparison operation")
            if op["op"] not in {"difference", "relative_change", "improvement", "percentage_points"}:
                raise ComparisonError("comparison operation is outside finite whitelist")
            axis = "model" if check["kind"] == "model_comparison" else "algorithm"
            if op["comparison_axis"] != axis or (op["op"] == "improvement" and op.get("direction") not in {"higher", "lower"}):
                raise ComparisonError("comparison operation axis/direction conflict")
        if check["requirement"] == "required" and set(record["candidate_ref"] for record in evidence.values()) != set(check["candidate_refs"]):
            raise ComparisonError("required candidates must each have predeclared evidence")
        if check["requirement"] == "retired":
            retirement = _mapping(check.get("retirement"), {"reason", "claim_action", "source_ref"}, label="comparison retirement")
            for field in retirement:
                _text(retirement[field], "retirement " + field)
            if retirement["claim_action"] not in {"removed_auxiliary_claim", "superseded_primary_semantics"}:
                raise ComparisonError("retirement requires an explicit auxiliary-claim removal or superseded primary semantics")
        row = deepcopy(dict(check))
        row.pop("disposition_ref", None)
        row.pop("retirement", None)
        row["candidate_refs"] = sorted(row["candidate_refs"])
        row["evidence_refs"] = sorted(row["evidence_refs"], key=lambda item: item["id"])
        normalized.append(row)
    return {key: deepcopy(plan[key]) for key in REGISTRY_FIELDS - {"approval_binding", "checks"}} | {"checks": sorted(normalized, key=lambda item: item["id"])}


def plan_sha256(plan: Mapping[str, Any]) -> str:
    plan = {key: value for key, value in plan.items() if key != "scope"}
    if "approval_binding" not in plan:
        plan = dict(plan) | {"approval_binding": {}}
    return _hash(canonical_plan(plan, question=str(plan.get("scope_ref", ""))))


def approval_issues(binding, scope_hash) -> list[str]:
    try:
        _mapping(binding, {"status", "owner", "statement", "source_ref", "approved_scope_sha256", "reviews"}, label="comparison approval")
        if binding["status"] != "approved" or binding["owner"] != "user" or binding["approved_scope_sha256"] != scope_hash:
            raise ComparisonError("comparison scope requires matching explicit user approval")
        _text(binding["statement"], "explicit scope approval statement")
        _text(binding["source_ref"], "scope approval source reference")
        reviews = binding["reviews"]
        if not isinstance(reviews, list) or len(reviews) != 2:
            raise ComparisonError("comparison approval requires two independent review passes")
        roles, review_ids = set(), set()
        for review in reviews:
            _mapping(review, {"review_id", "role", "scope_sha256", "verdict", "method", "conclusion", "blocking_items", "unresolved_items"}, label="comparison review")
            if review["role"] not in REVIEW_ROLES or review["role"] in roles:
                raise ComparisonError("comparison review roles must be distinct")
            roles.add(review["role"])
            identifier = _text(review["review_id"], "independent review reference")
            if identifier in review_ids:
                raise ComparisonError("two review conclusions must have distinct references")
            review_ids.add(identifier)
            if review["scope_sha256"] != scope_hash or review["verdict"] != "passed" or review["method"] not in {"separate_pass", "subagent"}:
                raise ComparisonError("comparison review is stale/incomplete")
            _text(review["conclusion"], "review boundary/independence conclusion")
            if review["blocking_items"] != [] or review["unresolved_items"] != []:
                raise ComparisonError("comparison review has unresolved/blocking findings")
        return []
    except (ComparisonError, TypeError, KeyError) as exc:
        return [str(exc)]


def inspect_plan(entry: Mapping[str, Any], *, question: str, specs, config=None, receipt=None) -> dict:
    result = {"enabled": enabled(entry, config, receipt), "issues": [], "plan": None,
              "plan_sha256": None, "scope_sha256": None, "required_ids": []}
    if not result["enabled"]:
        return result
    try:
        parsed = extract_specs(specs, question) if isinstance(specs, str) else specs
        scope = canonical_scope(parsed, question=question)
        digest = scope_sha256(scope)
        result["scope_sha256"] = digest
        baseline = entry.get("semantic_identity_hash")
        if entry.get("model_challenge_status") != "passed" or entry.get("human_model_approval_status") != "approved":
            raise ComparisonError("comparison does not replace current primary Challenge/Human Approval")
        if not isinstance(baseline, str) or not SHA.fullmatch(baseline) or any(entry.get(field) != baseline for field in ("validated_semantic_identity_hash", "approved_semantic_identity_hash")):
            raise ComparisonError("comparison requires current validated and approved primary identity")
        if scope["baseline_semantic_identity_hash"] != baseline:
            raise ComparisonError("framework comparison baseline is stale")
        registry = entry.get("analysis_comparison")
        plan = canonical_plan(registry, question=question, baseline_identity=baseline, scope_identity=digest)
        result["issues"].extend(approval_issues(registry["approval_binding"], digest))
        questions = _index(scope["questions"], "scope question")
        for check in plan["checks"]:
            scoped = questions.get(check["id"])
            if scoped is None or any(check[field] != scoped[field] for field in ("kind", "question", "target_claim", "baseline_ref")) or not set(check["candidate_refs"]).issubset(scoped["candidate_refs"]):
                raise ComparisonError("activated check is outside its approved comparison scope")
            _validate_evidence_metadata(check, scoped, scope)
        result["plan"] = deepcopy(dict(registry)) | {"scope": scope}
        result["plan_sha256"] = plan_sha256(plan)
        result["required_ids"] = [row["id"] for row in plan["checks"] if row["requirement"] == "required"]
        if result["required_ids"] and entry.get("result_analysis_status") == "not_required":
            raise ComparisonError("required comparison conflicts with Analysis Necessity Gate=not_required")
        for record in (config, receipt):
            if record is not None:
                if record.get(PROTOCOL_FIELD) != VERSION or record.get(PLAN_FIELD) != result["plan_sha256"]:
                    raise ComparisonError("comparison protocol/frozen plan digest is missing, changed or unsupported")
                if record.get("stage") not in (None, "analysis"):
                    raise ComparisonError("comparison protocol is analysis-only")
    except (ComparisonError, ValueError, TypeError, KeyError) as exc:
        result["issues"].append(str(exc))
    return result


def _validate_evidence_metadata(check, scoped, scope):
    axis = "model" if check["kind"] == "model_comparison" else "algorithm"
    evaluation = scoped["evaluation"]
    for record in check["evidence_refs"]:
        candidate = record["candidate"]["selector"]
        if candidate["sheet"] != KINDS[check["kind"]]:
            raise ComparisonError("required comparison must use its corresponding evidence table")
        expected = {"检验ID": check["id"], "记录键": record["id"], "评价协议ID": evaluation["id"],
                    "判据ID": check["criterion"]["id"], "差异类型": record["operation"]["op"]}
        if axis == "model":
            expected.update({"主模型ID": check["baseline_ref"], "对照模型ID": record["candidate_ref"]})
        else:
            expected.update({"基准算法ID": check["baseline_ref"], "对照算法ID": record["candidate_ref"]})
            expected["模型ID"] = _index(scope["algorithms"], "algorithm")[check["baseline_ref"]]["model_ref"]
        if any(candidate["row_key"].get(key) != value for key, value in expected.items()):
            raise ComparisonError("comparison selector must bind check, record, protocol and actual object IDs")
        needed_axes = {"metric", axis, *evaluation["fixed_axes"]}
        if not needed_axes.issubset(candidate["identity_columns"]):
            raise ComparisonError("comparison candidate must observe its metric, object and fixed axes")
        for field in ("reported_baseline", "reported_difference"):
            selector = record[field]["selector"]
            if selector["sheet"] != candidate["sheet"] or selector["row_key"] != candidate["row_key"]:
                raise ComparisonError("reported baseline/difference must be in the same exact comparison row")
        columns = (("对照模型数值", "主模型数值") if axis == "model" else ("对照数值", "基准数值"))
        if (candidate["value_column"] != columns[0]
                or record["reported_baseline"]["selector"]["value_column"] != columns[1]
                or record["reported_difference"]["selector"]["value_column"] != "差异"):
            raise ComparisonError("comparison selectors must use the actual declared value/difference columns")
        if record["operation"]["op"] == "improvement" and record["operation"]["direction"] != evaluation["direction"]:
            raise ComparisonError("improvement direction conflicts with approved metric direction")


def _select(source, books):
    return books[source["source"]].select(source["selector"], [])[0]


def _table_decision(book, sheet, header_row, row):
    rows = book.rows(sheet)
    columns = [column for column, cell in rows[header_row].items() if cell.kind == "text" and cell.value == "判定"]
    if len(columns) != 1:
        raise ComparisonError("comparison table requires an exact unique 判定 column")
    cell = rows[row].get(columns[0])
    if cell is None or cell.formula:
        raise ComparisonError("comparison 判定 must be a real literal, never a missing/formula value")
    if cell.kind == "boolean" and cell.value in {"0", "1"}:
        return cell.value == "1"
    if cell.kind == "text" and cell.value in {"true", "false", "True", "False"}:
        return cell.value.lower() == "true"
    raise ComparisonError("comparison 判定 must be an explicit boolean or true/false text")


def _exploratory_started(check, book, dispositions, declared_ids):
    """No result obligation until an optional check reports a row or disposition."""
    if check.get("disposition_ref") in dispositions:
        return True
    sheet = KINDS[check["kind"]]
    if sheet not in book.sheets:
        return False
    header_rows = {record["candidate"]["selector"]["header_row"] for record in check["evidence_refs"]} or {1}
    record_ids = {record["id"] for record in check["evidence_refs"]}
    rows = book.rows(sheet)
    started = False
    for header_row in header_rows:
        headers = rows.get(header_row, {})
        columns = {}
        for field in ("检验ID", "记录键"):
            matched = [column for column, cell in headers.items() if cell.kind == "text" and cell.value == field]
            if len(matched) != 1:
                raise ComparisonError("comparison table requires exact unique check/record ID columns")
            columns[field] = matched[0]
        for row_index, row in rows.items():
            if row_index <= header_row or not row:
                continue
            check_cell, record_cell = (row.get(columns[field]) for field in ("检验ID", "记录键"))
            if (check_cell is None or check_cell.formula or check_cell.kind != "text"
                    or check_cell.value not in declared_ids):
                raise ComparisonError("reported comparison row has malformed or undeclared check ID")
            if record_cell is None or record_cell.formula or record_cell.kind != "text" or not record_cell.value:
                raise ComparisonError("reported comparison row has malformed record ID")
            started |= check_cell.value == check["id"] or record_cell.value in record_ids
    return started


def inspect_evidence(plan: Mapping[str, Any], *, primary_bytes: bytes, analysis_bytes: bytes,
                     dispositions, workbook_contract=None, comparison_rules=None) -> dict:
    result = {"issues": [], "covered_ids": [], "uncovered_required_ids": [], "computed_metrics": [],
              "criterion_results": [], "disposition_impacts": []}
    if not isinstance(comparison_rules, Mapping) or "limits" not in comparison_rules or "units" not in comparison_rules:
        result["issues"].append("captured bounded claim-evidence limits/units Authority is required")
        return result
    try:
        scope = canonical_scope(plan.get("scope"), question=plan.get("scope_ref"))
        plain = {key: value for key, value in plan.items() if key != "scope"}
        plain.setdefault("approval_binding", {})
        canonical = canonical_plan(plain, question=plan["scope_ref"],
                                   baseline_identity=scope["baseline_semantic_identity_hash"],
                                   scope_identity=scope_sha256(scope))
        books = {"primary": Workbook(primary_bytes, comparison_rules), "analysis": Workbook(analysis_bytes, comparison_rules)}
        questions = _index(scope["questions"], "scope question")
        disposition_rows = _index(dispositions, "disposition")
        original_checks = _index(plan["checks"], "comparison check")
        used_observations = set()
        for check in canonical["checks"]:
            if check["requirement"] == "retired":
                continue
            identifier = check["id"]
            if check["requirement"] == "exploratory":
                if not _exploratory_started(original_checks[identifier], books["analysis"], disposition_rows, original_checks):
                    continue
                if not check["evidence_refs"]:
                    result["issues"].append(f"{identifier}: reported exploratory comparison requires predeclared exact evidence selectors")
                    continue
            scoped = questions[identifier]
            _validate_evidence_metadata(check, scoped, scope)
            evaluation = scoped["evaluation"]
            criterion = check["criterion"]
            threshold = number(criterion["threshold"], comparison_rules)
            tolerance = number(criterion.get("arithmetic_tolerance", "0"), comparison_rules)
            outcomes = []
            check_issues = []
            for record in check["evidence_refs"]:
                try:
                    baseline = _select(record["baseline"], books)
                    candidate, location = books["analysis"].select(record["candidate"]["selector"], [])
                    reported_base = _select(record["reported_baseline"], books)
                    reported_difference = _select(record["reported_difference"], books)
                    axis = record["operation"]["comparison_axis"]
                    expected_axes = {"metric", *evaluation["fixed_axes"]}
                    for value in (baseline, candidate):
                        if not expected_axes.issubset(value.identity) or value.identity["metric"] != evaluation["metric"]:
                            raise ComparisonError("selected metric/fixed axes conflict with evaluation protocol")
                        if unit_info(value.unit, comparison_rules) != unit_info(evaluation["unit"], comparison_rules):
                            raise ComparisonError("selected unit conflicts with approved common metric")
                    if candidate.identity.get(axis) != record["candidate_ref"]:
                        raise ComparisonError("candidate observation is attributed to the wrong object")
                    if record["baseline"]["source"] == "primary" and axis not in baseline.identity:
                        baseline = replace(baseline, identity=dict(baseline.identity) | {axis: check["baseline_ref"]})
                    if baseline.identity.get(axis) != check["baseline_ref"]:
                        raise ComparisonError("baseline observation is attributed to the wrong object")
                    if any(baseline.identity.get(key) != candidate.identity.get(key) for key in expected_axes):
                        raise ComparisonError("comparison observations use different metric/instance scopes")
                    if abs(converted(reported_base, baseline.unit, comparison_rules).value - baseline.value) > tolerance:
                        raise ComparisonError("analysis baseline does not reproduce its captured source")
                    if not expected_axes.issubset(reported_base.identity) or any(reported_base.identity[key] != baseline.identity[key] for key in expected_axes):
                        raise ComparisonError("reported baseline has different observation axes")
                    observed = next(iter(candidate.origins))
                    if observed in used_observations:
                        raise ComparisonError("duplicate physical candidate evidence cannot close multiple records")
                    used_observations.add(observed)
                    computed = derive(record["operation"], {"baseline": baseline, "candidate": candidate}, comparison_rules)
                    reported = converted(reported_difference, computed.unit, comparison_rules)
                    if abs(reported.value - computed.value) > tolerance:
                        raise ComparisonError("reported difference does not match bounded recomputation")
                    target = converted(computed, criterion["unit"], comparison_rules).value
                    relation = criterion["relation"]
                    operand = abs(target) if relation.startswith("abs_") else target
                    met = operand <= threshold if relation.endswith("le") else operand >= threshold
                    if _table_decision(books["analysis"], location["sheet"], record["candidate"]["selector"]["header_row"], location["row"]) != met:
                        raise ComparisonError("table 判定 disagrees with independently recomputed criterion")
                    outcomes.append(met)
                    result["computed_metrics"].append({"check_id": identifier, "record_id": record["id"], "value": str(computed.value), "unit": computed.unit})
                    result["criterion_results"].append({"check_id": identifier, "record_id": record["id"], "criterion_met": met})
                except (EvidenceError, ComparisonError, KeyError, TypeError, ValueError) as exc:
                    check_issues.append(f"{identifier}/{record['id']}: {exc}")
            disposition_ref = original_checks[identifier].get("disposition_ref")
            disposition = disposition_rows.get(disposition_ref)
            if not disposition or disposition.get("target_claim") != check["target_claim"]:
                check_issues.append(f"{identifier}: exact target-claim disposition is required")
            elif disposition.get("disposition") not in {"support", "modify", "reject"}:
                check_issues.append(f"{identifier}: invalid evidence disposition")
            elif disposition.get("status", "current") not in {"current", "resolved"}:
                check_issues.append(f"{identifier}: stale evidence disposition cannot qualify comparison")
            elif disposition.get("status", "current") == "resolved" and not (
                    disposition["disposition"] == "modify"
                    or (disposition["disposition"] == "reject" and disposition.get("impact_scope") == "auxiliary_wording")):
                check_issues.append(f"{identifier}: support/core rejection cannot be closed by a resolved label")
            elif disposition["disposition"] == "support" and not all(outcomes):
                check_issues.append(f"{identifier}: negative criterion cannot be silently disposed as support")
            else:
                try:
                    for field in ("method_or_source", "key_finding", "required_action"):
                        _text(disposition.get(field), "disposition " + field)
                    if disposition["disposition"] in {"modify", "reject"}:
                        impact = disposition.get("impact_scope")
                        if impact not in {"auxiliary_wording", "core_answer", "model_validity"}:
                            raise ComparisonError("negative comparison requires explicit impact_scope")
                        stage = disposition.get("return_stage")
                        event = None
                        if disposition["disposition"] == "reject" and impact != "auxiliary_wording":
                            expected = "model_design" if impact == "model_validity" else "solve_validate"
                            if stage != expected:
                                raise ComparisonError("core comparison rejection has incorrect return_stage")
                            event = "model_validity_rejected" if impact == "model_validity" else "core_answer_rejected"
                        elif stage is not None:
                            raise ComparisonError("modify/auxiliary rejection cannot carry return_stage")
                        result["disposition_impacts"].append({"evidence_id": disposition["id"], "check_id": identifier,
                                                              "impact_scope": impact, "return_stage": stage, "event": event})
                except ComparisonError as exc:
                    check_issues.append(f"{identifier}: {exc}")
            result["issues"].extend(check_issues)
            if not check_issues and outcomes:
                result["covered_ids"].append(identifier)
        required = {check["id"] for check in canonical["checks"] if check["requirement"] == "required"}
        result["uncovered_required_ids"] = sorted(required - set(result["covered_ids"]))
        if result["uncovered_required_ids"]:
            result["issues"].append("uncovered required comparisons: " + ", ".join(result["uncovered_required_ids"]))
    except (ComparisonError, EvidenceError, ValueError, TypeError, KeyError, OSError) as exc:
        result["issues"].append(str(exc))
    return result
