"""Current project approval and execution binding for an opt-in primary quality specification."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

from execution_protocol import (
    PQS_DIGEST_FIELD, PQS_PROTOCOL_VERSION, PQS_RECEIPT_VERSION,
    primary_quality_config_issues, primary_quality_receipt_issues,
)
from primary_quality_specification import SPECIFICATION_KEY, specification_sha256
from semantic_identity import inspect_question_semantics, primary_quality_specification, question_sections


FRAMEWORK_PATH = "模型论文框架.md"


def binding_present(config: Mapping[str, Any]) -> bool:
    return (
        PQS_DIGEST_FIELD in config
        or config.get("primary_quality_protocol_version") == PQS_PROTOCOL_VERSION
        or config.get("run_receipt_protocol_version") == PQS_RECEIPT_VERSION
        or config.get("run_receipt_version") == PQS_RECEIPT_VERSION
    )


def inspect_gate(
    root: Path, state: Mapping[str, Any], question: str, config: Mapping[str, Any], *,
    receipt: Mapping[str, Any] | None = None, accepted_receipt: bool = False,
    enforce_current_sib: bool = False,
) -> tuple[dict[str, Any] | None, list[str], dict[str, Any]]:
    """Read one question's approved spec, returning exact project bytes for the transaction."""
    required = binding_present(config) or (receipt is not None and binding_present(receipt))
    observed: dict[str, Any] = {"project": {}, "skill": {}}
    root = root.resolve()
    path = root / FRAMEWORK_PATH
    section = ""
    try:
        if not path.resolve().is_relative_to(root):
            raise ValueError("model framework path escapes project root")
        raw = path.read_bytes()
        section = question_sections(raw.decode("utf-8")).get(question, "")
        semantics = inspect_question_semantics(section, question)
        identity = semantics.get("identity")
        specification = primary_quality_specification(identity) if identity is not None else None
    except (OSError, ValueError, RuntimeError) as exc:
        if required or SPECIFICATION_KEY in section:
            return None, [f"{question} PQS: current approved framework cannot be read: {exc}"], observed
        return None, [], observed

    entry = (state.get("subproblems") or {}).get(question) or {}
    if isinstance(entry, Mapping):
        approved_hash = entry.get("approved_semantic_identity_hash")
    else:
        approved_hash = None
    if specification is None:
        if required:
            return None, [f"{question} PQS: current framework does not contain an approved specification"], observed
        if (enforce_current_sib and approved_hash
                and semantics["semantic_identity_hash"] != approved_hash):
            return None, [f"{question} PQS: current framework SIB differs from the approved identity"], observed
        return None, [], observed

    from runtime_assurance import _semantic_lock_evidence

    if not isinstance(entry, Mapping):
        return None, [f"{question} PQS: current subproblem entry is not a mapping"], observed
    lock = _semantic_lock_evidence(question, dict(entry), current_semantics=semantics, framework_error=None)
    if lock["status"] != "verified":
        return None, [f"{question} PQS: {lock['reason']}"], observed
    observed["project"][FRAMEWORK_PATH] = hashlib.sha256(raw).hexdigest()
    config_view = dict(config)
    if accepted_receipt:
        config_view["run_receipt_protocol_version"] = config.get("run_receipt_version")
    issues = primary_quality_config_issues(config_view, required=True)
    if receipt is not None:
        issues.extend(primary_quality_receipt_issues(receipt, config_view, required=True))
    if str(config_view.get(PQS_DIGEST_FIELD, "")).lower() != specification_sha256(specification):
        issues.append(f"{PQS_DIGEST_FIELD} differs from the approved current SIB")
    return specification, [f"{question} PQS: {issue}" for issue in dict.fromkeys(issues)], observed
