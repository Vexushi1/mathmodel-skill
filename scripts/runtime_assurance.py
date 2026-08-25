#!/usr/bin/env python3
"""Runtime context hydration and assurance helpers for the HSK resolver."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Iterable

import yaml


def _unique(items: Iterable[str | None]) -> list[str]:
    return list(dict.fromkeys(str(item) for item in items if item and str(item).strip()))


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_intent_assurance(
    explicit_intents: Iterable[str],
    request: str,
    router: dict[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    explicit = _unique(explicit_intents)
    text = request.strip().lower()
    candidates: list[dict[str, Any]] = []
    if text:
        for name, route in (router.get("routing", {}) or {}).items():
            keywords = route.get("infer_keywords", route.get("triggers", []))
            matched = _unique(
                str(word) for word in keywords if str(word).lower() in text
            )
            if matched:
                candidates.append(
                    {
                        "intent": str(name),
                        "score": sum(max(1, len(word.strip())) for word in matched),
                        "matched_keyword_count": len(matched),
                        "matched_keywords": matched,
                    }
                )
    candidates.sort(key=lambda item: (-int(item["score"]), str(item["intent"])))
    top_score = int(candidates[0]["score"]) if candidates else 0
    top = [item for item in candidates if int(item["score"]) == top_score]
    inferred = [str(item["intent"]) for item in top]
    if "full_workflow" in inferred:
        inferred = ["full_workflow"]

    selected = explicit if explicit else inferred
    ambiguity = bool(not explicit and len(inferred) > 1)

    if explicit:
        confidence_band = "high"
        confidence_score = 1.0
        mode = "mixed" if candidates else "explicit"
        reason = "explicit intent is authoritative; keyword matches are provenance only"
    elif not candidates:
        confidence_band = "low"
        confidence_score = 0.0
        mode = "unresolved"
        reason = "no explicit intent and no configured keyword matched"
    elif ambiguity:
        confidence_band = "low"
        confidence_score = 0.35
        mode = "inferred"
        reason = "multiple inferred intents share the top deterministic specificity score"
    elif int(top[0].get("matched_keyword_count", 0)) >= 2:
        confidence_band = "high"
        confidence_score = 0.8
        mode = "inferred"
        reason = "the selected route has multiple deterministic keyword matches"
    else:
        confidence_band = "medium"
        confidence_score = 0.6
        mode = "inferred"
        reason = "the selected route has the highest deterministic keyword-specificity score"

    return selected, {
        "mode": mode,
        "explicit_intents": explicit,
        "inferred_candidates": candidates,
        "selected_intents": selected,
        "confidence_band": confidence_band,
        "confidence_score": confidence_score,
        "ambiguity": ambiguity,
        "selection_reason": reason,
    }


def _scope_questions(state: dict[str, Any], question: str | None) -> tuple[list[str], list[str]]:
    subproblems = state.get("subproblems", {}) or {}
    if question:
        if question not in subproblems:
            return [], [f"question {question} is not present in project state"]
        return [question], []
    return sorted(str(name) for name in subproblems), []


def _classification_for_scope(
    state: dict[str, Any], questions: list[str]
) -> tuple[dict[str, Any], list[str]]:
    if not questions:
        return {}, []
    subproblems = state.get("subproblems", {}) or {}
    rows: list[tuple[str | None, tuple[str, ...], tuple[str, ...]]] = []
    for question in questions:
        item = subproblems.get(question, {}) or {}
        classification = item.get("classification", {}) or {}
        objective = classification.get("objective")
        structures = tuple(classification.get("structures", []) or [])
        capabilities = item.get("capabilities", {}) or classification.get("capabilities", {}) or {}
        enabled = tuple(sorted(str(name) for name, value in capabilities.items() if value is True))
        if objective or structures or enabled:
            rows.append((str(objective) if objective else None, structures, enabled))
    if not rows:
        return {}, []
    if len(set(rows)) != 1:
        return {}, [
            "scoped subproblems do not share one objective/structures/capabilities classification"
        ]
    objective, structures, capabilities = rows[0]
    return {
        "objective": objective,
        "structures": list(structures),
        "capabilities": list(capabilities),
    }, []


def _semantic_lock_evidence(question: str, item: dict[str, Any]) -> dict[str, Any]:
    revision = item.get("semantic_revision")
    semantic_hash = item.get("semantic_hash")
    approved_revision = item.get("approved_semantic_revision")
    approved_hash = item.get("approved_semantic_hash")
    ok = (
        item.get("model_challenge_status") == "passed"
        and item.get("human_model_approval_status") == "approved"
        and revision is not None
        and semantic_hash
        and approved_revision == revision
        and approved_hash == semantic_hash
    )
    return {
        "artifact": "locked_model_spec",
        "source": "project_state",
        "scope": question,
        "status": "verified" if ok else "stale_or_unapproved",
        "reason": (
            "challenge and explicit approval bind to the current semantic revision/hash"
            if ok
            else "challenge/approval is missing, stale, or not bound to the current semantic revision/hash"
        ),
        "path": None,
        "expected_sha256": semantic_hash if ok else None,
        "actual_sha256": semantic_hash if ok else None,
    }


def _project_artifact_path(
    project_root: Path, relative_path: str | None
) -> tuple[Path | None, str | None]:
    if not relative_path:
        return None, None
    root = project_root.resolve()
    raw = Path(relative_path).expanduser()
    candidate = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None, "artifact path resolves outside project root"
    return candidate, None


def _file_evidence(
    project_root: Path,
    *,
    artifact: str,
    scope: str,
    relative_path: str | None,
    expected_sha256: str | None,
    accepted: bool,
    accepted_reason: str,
) -> dict[str, Any]:
    path, path_error = _project_artifact_path(project_root, relative_path)
    actual = sha256_file(path) if path else None
    if not accepted:
        status = "not_accepted"
        reason = accepted_reason
    elif not relative_path:
        status = "missing"
        reason = "accepted state has no artifact path"
    elif path_error:
        status = "outside_project_root"
        reason = path_error
    elif not path or not path.is_file():
        status = "missing"
        reason = "artifact path does not exist"
    elif not expected_sha256:
        status = "unverified"
        reason = "accepted state has no expected sha256"
    elif actual != expected_sha256:
        status = "hash_mismatch"
        reason = "actual sha256 does not match current project-state evidence"
    else:
        status = "verified"
        reason = accepted_reason
    return {
        "artifact": artifact,
        "source": "project_state",
        "scope": scope,
        "status": status,
        "reason": reason,
        "path": relative_path,
        "expected_sha256": expected_sha256,
        "actual_sha256": actual,
    }


def _expected_hash(item: dict[str, Any], layer: str) -> str | None:
    validated = item.get("validated_artifact_hashes", {}) or {}
    current = item.get("artifact_hashes", {}) or {}
    return validated.get(layer) or current.get(layer)


def hydrate_project_context(project_root: str | Path, question: str | None = None) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    state_path = root / "state" / "project_state.yaml"
    state = _load_yaml(state_path)
    if not state:
        return {
            "loaded": False,
            "project_root": str(root),
            "state_path": str(state_path),
            "question": question,
            "competition": None,
            "preprocessing_decision": None,
            "classification": {},
            "verified_artifacts": [],
            "artifact_evidence": [],
            "conflicts": [],
            "ambiguities": ["project state is unavailable"],
        }

    questions, ambiguities = _scope_questions(state, question)
    classification, classification_ambiguities = _classification_for_scope(state, questions)
    ambiguities.extend(classification_ambiguities)
    project = state.get("project", {}) or {}
    preprocessing = state.get("preprocessing", {}) or {}
    evidence: list[dict[str, Any]] = []
    verified: set[str] = set()

    semantic_rows = [
        _semantic_lock_evidence(q, (state.get("subproblems", {}) or {}).get(q, {}) or {})
        for q in questions
    ]
    evidence.extend(semantic_rows)
    if semantic_rows and all(item["status"] == "verified" for item in semantic_rows):
        verified.add("locked_model_spec")

    preprocessing_status = preprocessing.get("status") == "accepted"
    pre = _file_evidence(
        root,
        artifact="preprocessing_workbook",
        scope="project",
        relative_path=preprocessing.get("workbook"),
        expected_sha256=preprocessing.get("workbook_sha256"),
        accepted=preprocessing_status,
        accepted_reason=(
            "project-level preprocessing workbook is accepted"
            if preprocessing_status
            else "project-level preprocessing workbook is not accepted"
        ),
    )
    if preprocessing.get("decision") == "project_level" or preprocessing.get("workbook"):
        evidence.append(pre)
        if pre["status"] == "verified":
            verified.update({"preprocessing_workbook", "accepted_preprocessing_workbook"})

    primary_rows: list[dict[str, Any]] = []
    analysis_rows: list[dict[str, Any]] = []
    subproblems = state.get("subproblems", {}) or {}
    for q in questions:
        item = subproblems.get(q, {}) or {}
        primary_ok = (
            item.get("primary_execution_status") == "accepted"
            and item.get("result_quality_status") == "passed"
        )
        primary_rows.append(
            _file_evidence(
                root,
                artifact="accepted_solution_workbook",
                scope=q,
                relative_path=item.get("solution_workbook"),
                expected_sha256=_expected_hash(item, "solution_workbook"),
                accepted=primary_ok,
                accepted_reason=(
                    "primary execution and result quality are accepted"
                    if primary_ok
                    else "primary execution or result quality is not accepted"
                ),
            )
        )
        analysis_ok = (
            item.get("analysis_execution_status") == "accepted"
            and item.get("result_analysis_status") == "passed"
        )
        analysis_rows.append(
            _file_evidence(
                root,
                artifact="accepted_result_analysis_workbook",
                scope=q,
                relative_path=item.get("result_analysis_workbook"),
                expected_sha256=_expected_hash(item, "result_analysis_workbook"),
                accepted=analysis_ok,
                accepted_reason=(
                    "result-analysis execution and stability status are accepted"
                    if analysis_ok
                    else "result-analysis execution or stability status is not accepted"
                ),
            )
        )
    evidence.extend(primary_rows)
    evidence.extend(analysis_rows)
    if primary_rows and all(item["status"] == "verified" for item in primary_rows):
        verified.update({"accepted_solution_workbook", "solution_workbook", "result_quality_report"})
    if analysis_rows and all(item["status"] == "verified" for item in analysis_rows):
        verified.update({"accepted_result_analysis_workbook", "result_analysis_workbook", "validated_results"})

    return {
        "loaded": True,
        "project_root": str(root),
        "state_path": str(state_path),
        "question": question,
        "project": {
            "competition": project.get("competition"),
            "problem": project.get("problem"),
            "version": project.get("version"),
            "current_phase": project.get("current_phase"),
        },
        "competition": project.get("competition"),
        "preprocessing_decision": preprocessing.get("decision"),
        "classification": classification,
        "verified_artifacts": sorted(verified),
        "artifact_evidence": evidence,
        "conflicts": [],
        "ambiguities": ambiguities,
    }


def reconcile_legacy_artifacts(
    declared: Iterable[str], hydration: dict[str, Any]
) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    declared_set = set(_unique(declared))
    verified = set(hydration.get("verified_artifacts", []) or [])
    evidence = list(hydration.get("artifact_evidence", []) or [])
    conflicts: list[str] = []
    known_invalid = {
        str(item.get("artifact"))
        for item in evidence
        if item.get("status") not in {"verified"}
    }
    effective = set(verified)
    for artifact in sorted(declared_set):
        if hydration.get("loaded") and artifact in known_invalid:
            conflicts.append(
                f"legacy artifact declaration {artifact} conflicts with current project-state assurance"
            )
            continue
        effective.add(artifact)
        evidence.append(
            {
                "artifact": artifact,
                "source": "legacy_available_artifacts",
                "scope": hydration.get("question") or "unspecified",
                "status": "declared_unverified",
                "reason": "legacy name-only compatibility input",
                "path": None,
                "expected_sha256": None,
                "actual_sha256": None,
            }
        )
    return sorted(effective), evidence, conflicts


def apply_contract_dependency_closure(
    plan: dict[str, Any],
    manifest: dict[str, Any],
    assurance_contract: dict[str, Any],
) -> dict[str, Any]:
    dependency_spec = (
        assurance_contract.get("contract_dependency_closure", {}) or {}
    ).get("contract_dependencies", {}) or {}
    aliases = manifest.get("contracts", {}) or {}
    required_aliases: list[str] = []
    for module in plan.get("modules", []) or []:
        required_aliases.extend(dependency_spec.get(str(module), []) or [])
    for gate in plan.get("pre_delivery_gates", []) or []:
        required_aliases.extend(
            dependency_spec.get(f"gate:{gate.get('name')}", []) or []
        )
    required_aliases = _unique(required_aliases)
    missing_aliases = [alias for alias in required_aliases if alias not in aliases]
    if missing_aliases:
        raise ValueError(f"runtime contract dependency aliases are undefined: {missing_aliases}")
    required_paths = _unique(aliases.get(alias) for alias in required_aliases)
    load_order = list(plan.get("load_order", []) or [])
    additions = [path for path in required_paths if path not in load_order]
    if additions:
        first_module = next(
            (index for index, item in enumerate(load_order) if str(item).startswith("modules/")),
            len(load_order),
        )
        load_order[first_module:first_module] = additions
    plan["load_order"] = load_order
    plan["contracts"] = _unique(
        [*(plan.get("contracts", []) or []), *required_paths]
    )
    return {
        "required_aliases": required_aliases,
        "required_paths": required_paths,
        "added_paths": additions,
        "missing_aliases": [],
    }


def authority_fingerprint(root: Path, sources: Iterable[str]) -> dict[str, Any]:
    rows: list[dict[str, str | None]] = []
    aggregate = hashlib.sha256()
    for relative in sources:
        path = root / relative
        digest = sha256_file(path)
        rows.append({"path": relative, "sha256": digest})
        aggregate.update(relative.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update((digest or "missing").encode("ascii"))
        aggregate.update(b"\n")
    return {"algorithm": "sha256", "sources": rows, "sha256": aggregate.hexdigest()}
