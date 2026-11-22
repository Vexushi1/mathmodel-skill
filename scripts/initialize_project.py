#!/usr/bin/env python3
"""Create the first project State and canonical framework from authored model evidence.

This is an orchestration entrypoint, not a Model Approval, State, or transaction
authority. It must be invoked only after a real Problem Contract and a proposed
model with a complete SIB have been authored. It cannot reconstruct lost projects.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Mapping

import yaml

import instantiate_model_paper_framework as FRAMEWORK_TEMPLATE
import project_transaction as TX
import validate_model_paper_framework as FRAMEWORK_VALIDATOR
import validate_project_state as STATE_VALIDATOR
from semantic_identity import (
    SemanticIdentityError,
    inspect_question_semantics,
    question_sections,
    validate_semantic_identity,
)

FRAMEWORK_PATH = "模型论文框架.md"
STATE_PATH = TX.STATE_RELATIVE_PATH
QUESTION = re.compile(r"^Q[1-9][0-9]*$")
MODEL_STATUS = "- 当前模型状态：`proposed_model_spec / locked_model_spec / stale`"
SLOT = "#### 当前模型口径\n\n"


class InitializationError(ValueError):
    """An authored candidate is incomplete or incompatible with current Authority."""


class RecoveryRequired(InitializationError):
    """Existing project evidence cannot be overwritten or guessed from new inputs."""


def _nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or "__" in value:
        raise InitializationError(f"{label} needs actual, non-placeholder text")
    return value.strip()


def _single_line(value: Any, label: str) -> str:
    result = _nonempty(value, label)
    if "\n" in result or "\r" in result or "|" in result:
        raise InitializationError(f"{label} must be one safe Markdown line")
    return result


def _source(root: Path, path: Path) -> tuple[str, dict[str, Any], str]:
    root = root.resolve()
    raw_path = Path(path)
    target = (root / raw_path).resolve() if not raw_path.is_absolute() else raw_path.resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise InitializationError("authored specification must be a regular file inside the project")
    if raw_path.is_symlink() or any(parent.is_symlink() for parent in target.parents if parent != root):
        raise InitializationError("authored specification must not use a symlink")
    if target.as_posix() in {(root / STATE_PATH).as_posix(), (root / FRAMEWORK_PATH).as_posix()}:
        raise InitializationError("authored specification cannot be a project output")
    relative = target.relative_to(root).as_posix()
    source_bytes = target.read_bytes()
    try:
        parsed = yaml.safe_load(source_bytes.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise InitializationError("authored specification is not valid UTF-8 YAML") from exc
    if not isinstance(parsed, dict):
        raise InitializationError("authored specification must be a mapping")
    return relative, parsed, hashlib.sha256(source_bytes).hexdigest()


def _questions(spec: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
    questions = spec.get("questions")
    if not isinstance(questions, dict) or not questions:
        raise InitializationError("questions must register every known Qn")
    ordered = []
    for name, item in questions.items():
        if not isinstance(name, str) or not QUESTION.fullmatch(name) or not isinstance(item, dict):
            raise InitializationError("each question requires a Qn key and a mapping")
        _single_line(item.get("title"), f"{name}.title")
        _nonempty(item.get("problem_contract"), f"{name}.problem_contract")
        if not isinstance(item.get("classification"), dict):
            raise InitializationError(f"{name}.classification is required")
        if not isinstance(item.get("capabilities", {}), dict):
            raise InitializationError(f"{name}.capabilities must be a mapping")
        dependencies = item.get("depends_on", [])
        if not isinstance(dependencies, list):
            raise InitializationError(f"{name}.depends_on must be a typed list")
        for edge in dependencies:
            if not isinstance(edge, dict) or not QUESTION.fullmatch(str(edge.get("question", ""))):
                raise InitializationError(f"{name} has an invalid typed dependency")
            if edge.get("kind") not in {"data", "parameter", "model", "result"}:
                raise InitializationError(f"{name} dependency has unknown kind")
            if edge["question"] not in questions:
                raise InitializationError(f"{name} depends on an unregistered question")
        ordered.append((name, item))
    ordered.sort(key=lambda item: int(item[0][1:]))
    proposed = [name for name, item in ordered if "proposed_model" in item]
    if len(proposed) != 1:
        raise InitializationError("first initialization requires exactly one authored proposed_model")
    return ordered


def build_candidates(spec: Mapping[str, Any], *, mode: str = "compact") -> tuple[dict[str, Any], str]:
    """Deterministically project the canonical template; never invent model semantics."""
    project = spec.get("project")
    if not isinstance(project, dict):
        raise InitializationError("project metadata is required")
    title = _single_line(project.get("name"), "project.name")
    competition = _single_line(project.get("competition"), "project.competition")
    problem = _single_line(project.get("problem"), "project.problem")
    questions = _questions(spec)
    preprocess = spec.get("preprocessing")
    if not isinstance(preprocess, dict) or preprocess.get("decision") not in {
        "not_needed", "question_local", "project_level",
    }:
        raise InitializationError("an audited preprocessing decision is required")
    if not isinstance(preprocess.get("evidence"), list) or not any(
        isinstance(x, str) and x.strip() for x in preprocess["evidence"]
    ):
        raise InitializationError("preprocessing must have substantive audit evidence")
    status = "pending" if preprocess["decision"] == "project_level" else "not_applicable"
    preprocessing = {
        "decision": preprocess["decision"],
        "status": status,
        "evidence": list(preprocess["evidence"]),
        "operations": [],
    }

    blueprint = FRAMEWORK_TEMPLATE.instantiate(mode)
    parts = FRAMEWORK_TEMPLATE.split_top_level(blueprint)
    question_area = parts.sections["各问模型与结果"]
    marker = "### Q1：__QUESTION_NAME__"
    if question_area.count(marker) != 1:
        raise InitializationError("canonical framework has an unexpected question skeleton")
    intro, original = question_area.split(marker, 1)
    original = marker + original
    rows = []
    section_texts = []
    subproblems: dict[str, dict[str, Any]] = {}
    decisions: dict[str, dict[str, Any]] = {}

    for name, entry in questions:
        subtitle = _single_line(entry["title"], f"{name}.title")
        proposed = entry.get("proposed_model")
        text = original.replace("Q1", name).replace("__QUESTION_NAME__", subtitle)
        problem_contract = _nonempty(entry["problem_contract"], f"{name}.problem_contract")
        if re.search(r"(?m)^#{1,3}[ \t]+", problem_contract):
            raise InitializationError(f"{name}.problem_contract must not add framework headings")
        source_note = "\n".join("> " + line for line in problem_contract.splitlines())
        text = text.replace(SLOT, SLOT + "**本问已审计 Problem Contract 原文**\n\n" + source_note + "\n\n", 1)
        if isinstance(proposed, dict):
            model_name = _single_line(proposed.get("name"), f"{name}.proposed_model.name")
            reason = _nonempty(proposed.get("reason"), f"{name}.proposed_model.reason")
            model_text = _nonempty(proposed.get("model_text"), f"{name}.proposed_model.model_text")
            if re.search(r"(?m)^#{1,3}[ \t]+", model_text):
                raise InitializationError(f"{name}.model_text must not redefine framework headings")
            identity = proposed.get("semantic_identity")
            if not isinstance(identity, dict):
                raise InitializationError(f"{name}: authored SIB mapping is required")
            try:
                validate_semantic_identity(identity, expected_question=name)
            except SemanticIdentityError as exc:
                raise InitializationError(f"{name}: invalid proposed SIB: {exc}") from exc
            if identity["preprocessing_decision"] != preprocess["decision"]:
                raise InitializationError(f"{name}: SIB preprocessing decision conflicts with project")
            declared = {(d["question"], d["kind"]) for d in entry.get("depends_on", [])}
            from_sib = {(d["question"], d["kind"]) for d in identity["dependencies"]}
            if declared != from_sib:
                raise InitializationError(f"{name}: State and SIB dependencies differ")
            if proposed.get("semantic_closure") != "passed" or proposed.get("complexity_sanity") != "passed":
                raise InitializationError(f"{name}: explicit prior semantic and complexity review is required")
            marker_text = (
                f"<!-- HSK_SEMANTIC_IDENTITY_BEGIN {name} -->\n"
                "```yaml\n"
                + yaml.safe_dump(identity, allow_unicode=True, sort_keys=False)
                + "```\n"
                + f"<!-- HSK_SEMANTIC_IDENTITY_END {name} -->\n\n"
                + model_text + "\n\n"
            )
            # SIB sits in the live model scope, not in the canonical placeholder comment.
            text = text.replace(SLOT, SLOT + marker_text, 1)
            text = text.replace(MODEL_STATUS, "- 当前模型状态：proposed_model_spec", 1)
            text = text.replace(
                "- 当前状态：`audited / designed / solved / analyzed / validated / written / completed`",
                "- 当前状态：designed", 1,
            )
            decisions[name] = {
                "selected_model": model_name, "rejected_models": [],
                "key_reason": reason,
            }
            current_status, selected = "designed", model_name
        elif proposed is None:
            text = text.replace(
                "- 当前状态：`audited / designed / solved / analyzed / validated / written / completed`",
                "- 当前状态：audited", 1,
            )
            current_status, selected = "audited", ""
        else:
            raise InitializationError(f"{name}.proposed_model must be a mapping")
        # The template's approval alternatives are not affirmative approval records.
        text = text.replace("- Model Challenge：`pending / passed / revision_required / stale`",
                            "- Model Challenge：pending", 1)
        text = text.replace("- Human Model Approval：`pending / approved / revision_required / stale`",
                            "- Human Model Approval：pending", 1)
        section_texts.append(text.rstrip("\n") + "\n\n")
        dependencies = deepcopy(entry.get("depends_on", []))
        sub = {
            "status": current_status,
            "selected_model": selected,
            "classification": deepcopy(entry["classification"]),
            "capabilities": deepcopy(entry.get("capabilities", {})),
            "depends_on": dependencies,
            "framework_section": f"### {name}：{subtitle}",
            "problem_contract_status": "frozen",
            "semantic_closure_status": "passed" if proposed is not None else "pending",
            "complexity_sanity_status": "passed" if proposed is not None else "pending",
            "complexity_sanity_flags": [],
            "model_challenge_status": "pending",
            "human_model_approval_status": "pending",
            "result_summary_status": "pending",
            "result_quality_status": "pending",
            "result_analysis_status": "pending",
            "primary_execution_status": "pending",
            "analysis_execution_status": "pending",
            "validation_status": "pending",
            "artifact_hashes": {}, "validated_artifact_hashes": {},
            "stale_layers": [], "artifacts_stale": False,
        }
        if proposed is not None:
            sub.update(semantic_revision=1, semantic_change_categories=["initial_design"],
                       complexity_sanity_note=_nonempty(
                           proposed.get("complexity_sanity_note"),
                           f"{name}.complexity_sanity_note",
                       ))
        subproblems[name] = sub
        kinds = ", ".join(d["kind"] for d in dependencies) if dependencies else "independent"
        upstream = ", ".join(d["question"] for d in dependencies) if dependencies else "无"
        rows.append(f"| {name} | {subtitle} | 待逐问细化 | {upstream} | {kinds} | 待评估 | not_applicable | 待求解 | {current_status} |")

    sections = dict(parts.sections)
    sections["各问模型与结果"] = intro + "".join(section_texts)
    initial_framework = FRAMEWORK_TEMPLATE._assemble(parts.header, parts.order, sections)
    replacements = {
        "__PROJECT__": title,
        "__COMPETITION_AND_PROBLEM__": f"{competition} {problem}",
        "__LAST_SYNC_SCOPE__": "first proposed model and all audited questions",
        "__ISO_DATETIME__": "not_recorded",
    }
    for old, new in replacements.items():
        initial_framework = initial_framework.replace(old, new)
    dependency_example = "| Q1 |  |  |  | data / parameter / model / result / independent |  | not_applicable / remains_sufficient / becomes_insufficient |  |  |"
    if dependency_example not in initial_framework:
        raise InitializationError("canonical dependency roster anchor was not found")
    initial_framework = initial_framework.replace(dependency_example, "\n".join(rows), 1)
    if "__" in initial_framework:
        raise InitializationError("unresolved canonical template placeholder")
    frame_hash = hashlib.sha256(initial_framework.encode("utf-8")).hexdigest()
    project_entry = {
        "competition": competition, "problem": problem,
        "current_phase": "model_design", "state_generation": 0,
    }
    objectives = sorted({str(entry["classification"].get("objective", ""))
                         for _, entry in questions})
    if all(objectives):
        project_entry["objectives"] = objectives
    payload = {
        "semantic_governance_version": "1.0.0",
        "project": project_entry,
        "requirements": {
            "total": len(questions), "completed": [],
            "pending": [name for name, _ in questions],
        },
        "preprocessing": preprocessing,
        "decisions": decisions,
        "subproblems": subproblems,
        "variables": {"locked": [], "source": {}},
        "paper_framework": {
            "path": FRAMEWORK_PATH, "version": "v0.8-project-memory",
            "mode": mode, "sync_status": "current",
            "last_sync_scope": "first proposed model and all audited questions",
            "sha256": frame_hash,
            "proposition_count": 0, "proposition_status": "not_assessed", "propositions": [],
            "paper_fragments": [],
        },
        "artifacts": {"code": [], "results": [], "figures": [], "papers": [FRAMEWORK_PATH]},
        "risks": [], "next_gate": {
            "module": "model_design",
            "condition": "Await current model challenge and explicit human approval",
        },
    }
    return payload, initial_framework


def _candidate_issues(root: Path, state: Mapping[str, Any], framework: str) -> list[str]:
    issues = STATE_VALIDATOR.validate_state_payload(
        state, project_root=root, framework_text_override=framework,
    )
    issues.extend(FRAMEWORK_VALIDATOR.validate_framework_text(
        framework, state=state, mode=state["paper_framework"]["mode"],
        strict=True, project_root=root,
    ))
    sections = question_sections(framework)
    if set(sections) != set(state["subproblems"]):
        issues.append("framework question scopes do not match registered Qn")
    for name, entry in state["subproblems"].items():
        if entry["status"] != "designed":
            continue
        try:
            inspection = inspect_question_semantics(sections[name], name)
            if inspection.get("mode") != "semantic_identity_v1":
                issues.append(f"{name}: proposed model has no current structured SIB")
        except SemanticIdentityError as exc:
            issues.append(f"{name}: {exc}")
    return issues


def _historical_project_outputs(root: Path) -> list[str]:
    found = []
    for path in root.iterdir():
        if path.name in {"final_latex", "draft_docx", "sync_report.yaml"}:
            found.append(path.name)
        if path.is_dir() and path.name.startswith("问题") and path.name.endswith("求解"):
            found.append(path.name)
    state_dir = root / "state"
    if state_dir.is_dir():
        found.extend("state/" + x.name for x in state_dir.iterdir()
                     if x.name not in {".project_transaction.lock"})
    return sorted(set(found))


def initialize_project(
    project_root: Path,
    spec_file: Path,
    *,
    mode: str = "compact",
    write: bool = False,
    failure_hook: TX.FailureHook | None = None,
) -> dict[str, Any]:
    """Preflight or atomically create both project files; no implicit recovery."""
    root = Path(project_root).resolve()
    if not root.is_dir():
        raise InitializationError("project root must already be a directory")
    state_path, framework_path = root / STATE_PATH, root / FRAMEWORK_PATH
    if os.path.lexists(root / TX.JOURNAL_RELATIVE_PATH):
        raise RecoveryRequired("pending transaction journal: explicit recovery is required")
    if os.path.lexists(state_path) != os.path.lexists(framework_path):
        raise RecoveryRequired("partial project: recover original State/framework, do not rebuild")
    relative, source, spec_hash = _source(root, Path(spec_file))
    candidate, framework = build_candidates(source, mode=mode)
    issues = _candidate_issues(root, candidate, framework)
    if issues:
        raise InitializationError("candidate validation failed: " + "; ".join(issues))
    if os.path.lexists(state_path):
        if not state_path.is_file() or not framework_path.is_file():
            raise RecoveryRequired("existing project paths are not regular files")
        try:
            existing = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            if not isinstance(existing, dict):
                raise ValueError("existing State is not a mapping")
            existing_issues = _candidate_issues(root, existing, framework_path.read_text(encoding="utf-8"))
            if existing_issues:
                raise RecoveryRequired("existing project fails validation: " + "; ".join(existing_issues))
            expected = deepcopy(candidate)
            expected["project"]["state_generation"] = existing["project"].get("state_generation")
            if existing != expected or framework_path.read_text(encoding="utf-8") != framework:
                raise RecoveryRequired("existing current project differs from proposed initialization")
        except (UnicodeError, yaml.YAMLError, OSError, ValueError) as exc:
            if isinstance(exc, RecoveryRequired):
                raise
            raise RecoveryRequired("existing State/framework cannot be safely resumed") from exc
        return {"status": "already_initialized", "generation": existing["project"]["state_generation"],
                "questions": list(candidate["subproblems"]), "source_sha256": spec_hash}
    historical = _historical_project_outputs(root)
    if historical:
        raise RecoveryRequired("historical project artifacts require recovery: " + ", ".join(historical))
    if not write:
        return {"status": "ready_for_initialization", "generation": 0,
                "questions": list(candidate["subproblems"]), "source_sha256": spec_hash}

    def staged_validator(files: Mapping[str, Path]) -> None:
        staged_state = yaml.safe_load(files[STATE_PATH].read_text(encoding="utf-8"))
        staged_framework = files[FRAMEWORK_PATH].read_text(encoding="utf-8")
        violations = _candidate_issues(root, staged_state, staged_framework)
        if violations:
            raise InitializationError("staged initialization failed: " + "; ".join(violations))

    TX.commit_project_state(
        root, candidate, expected_generation=0,
        expected_file_hashes={
            STATE_PATH: None, FRAMEWORK_PATH: None, relative: spec_hash,
        },
        writes_before_state=[(FRAMEWORK_PATH, framework)],
        validators=[staged_validator], failure_hook=failure_hook,
    )
    persisted = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    if (persisted["project"].get("state_generation") != 1
            or framework_path.read_text(encoding="utf-8") != framework
            or _candidate_issues(root, persisted, framework)):
        raise InitializationError("post-commit verification failed; preserve current files for recovery")
    return {"status": "initialized", "generation": 1,
            "questions": list(candidate["subproblems"]), "source_sha256": spec_hash}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--spec", type=Path, required=True, help="authored project-local Problem Contract + first proposed model SIB YAML")
    parser.add_argument("--mode", choices=("compact", "full"), default="compact")
    parser.add_argument("--write", action="store_true", help="atomically create State and framework after preflight")
    args = parser.parse_args()
    try:
        result = initialize_project(args.project_root, args.spec, mode=args.mode, write=args.write)
    except (InitializationError, TX.ProjectTransactionError, OSError) as exc:
        print(json.dumps({"status": "recovery_required" if isinstance(exc, RecoveryRequired) else "failed",
                          "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
