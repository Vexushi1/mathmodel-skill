#!/usr/bin/env python3
"""One-shot deterministic Phase E artifact naming migration. Removed after integration."""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(relative: str, old: str, new: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{relative}: expected exactly one match, got {count}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_all(relative: str, old: str, new: str, expected: int) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{relative}: expected {expected} matches, got {count}: {old[:80]!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def write(relative: str, content: str) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def git_blob_sha(relative: str) -> str:
    data = (ROOT / relative).read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


# ---------------------------------------------------------------------------
# Shared compatibility helper. Policy remains in project_state schema + plan;
# this module only canonicalizes the migration alias deterministically.
# ---------------------------------------------------------------------------
write(
    "scripts/artifact_identity.py",
    '''#!/usr/bin/env python3
"""Canonical artifact-identity compatibility helpers for the staged v9 migration."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

LEGACY_PRIMARY_CODE_KEY = "model"
PRIMARY_CODE_KEY = "primary_code"
ANALYSIS_CODE_KEY = "analysis_code"


class ArtifactIdentityError(ValueError):
    """Raised when legacy and canonical artifact identities contradict each other."""


def _same_hash(left: Any, right: Any) -> bool:
    return str(left).strip().lower() == str(right).strip().lower()


def normalize_artifact_hashes(
    values: Mapping[str, Any] | None,
    *,
    legacy_primary_fallback: Any = None,
) -> dict[str, Any]:
    """Return canonical hashes, mapping legacy model -> primary_code only when safe.

    The legacy key is never returned. If both keys exist they must denote the same hash;
    otherwise migration is blocked rather than choosing one truth silently.
    """
    normalized = dict(values or {})
    legacy = normalized.get(LEGACY_PRIMARY_CODE_KEY)
    primary = normalized.get(PRIMARY_CODE_KEY)
    if legacy not in (None, "") and primary not in (None, "") and not _same_hash(legacy, primary):
        raise ArtifactIdentityError(
            "artifact_hashes.model conflicts with artifact_hashes.primary_code; "
            "legacy/new implementation identities must agree before migration"
        )
    if primary in (None, ""):
        if legacy not in (None, ""):
            normalized[PRIMARY_CODE_KEY] = legacy
        elif legacy_primary_fallback not in (None, ""):
            normalized[PRIMARY_CODE_KEY] = legacy_primary_fallback
    normalized.pop(LEGACY_PRIMARY_CODE_KEY, None)
    return normalized


def normalize_stale_layers(values: Any) -> list[str]:
    """Map the v8 implementation layer name model -> primary_code for comparison."""
    return sorted({PRIMARY_CODE_KEY if str(item) == LEGACY_PRIMARY_CODE_KEY else str(item) for item in (values or [])})


def entry_alias_issues(entry: Mapping[str, Any], *, scope: str = "subproblem") -> list[str]:
    issues: list[str] = []
    for field, fallback in (
        ("artifact_hashes", entry.get("model_hash")),
        ("validated_artifact_hashes", entry.get("validated_model_hash")),
    ):
        try:
            normalize_artifact_hashes(entry.get(field), legacy_primary_fallback=fallback)
        except ArtifactIdentityError as exc:
            issues.append(f"{scope}.{field}: {exc}")
    return issues


def canonicalize_entry_hashes(entry: dict[str, Any]) -> None:
    """Mechanically migrate an entry in memory to canonical implementation keys."""
    current = normalize_artifact_hashes(
        entry.get("artifact_hashes"), legacy_primary_fallback=entry.get("model_hash")
    )
    validated = normalize_artifact_hashes(
        entry.get("validated_artifact_hashes"),
        legacy_primary_fallback=entry.get("validated_model_hash"),
    )
    if current or "artifact_hashes" in entry:
        entry["artifact_hashes"] = current
    if validated or "validated_artifact_hashes" in entry:
        entry["validated_artifact_hashes"] = validated
    if "stale_layers" in entry:
        entry["stale_layers"] = normalize_stale_layers(entry.get("stale_layers"))
''',
)

# ---------------------------------------------------------------------------
# Project State Schema: additive canonical keys + explicit legacy semantics.
# ---------------------------------------------------------------------------
replace_once(
    "core/project_state.schema.yaml",
    "      model: {type: string, pattern: '^[0-9a-fA-F]{64}$'}\n      solution_workbook: {type: string, pattern: '^[0-9a-fA-F]{64}$'}\n",
    "      model:\n        description: v8 legacy primary-code artifact hash alias；Phase E仅兼容读取，新写入必须使用primary_code。\n        type: string\n        pattern: '^[0-9a-fA-F]{64}$'\n      primary_code: {type: string, pattern: '^[0-9a-fA-F]{64}$'}\n      analysis_code: {type: string, pattern: '^[0-9a-fA-F]{64}$'}\n      solution_workbook: {type: string, pattern: '^[0-9a-fA-F]{64}$'}\n",
)
replace_once(
    "core/project_state.schema.yaml",
    "    enum: [data, model, solution_workbook, result_analysis_workbook, robustness_workbook, matlab_script, figure_bundle, framework]\n",
    "    enum: [data, model, primary_code, analysis_code, solution_workbook, result_analysis_workbook, robustness_workbook, matlab_script, figure_bundle, framework]\n",
)
replace_once(
    "core/project_state.schema.yaml",
    "        model_hash: {type: string, pattern: '^[0-9a-fA-F]{64}$'}\n        validated_model_hash: {type: string, pattern: '^[0-9a-fA-F]{64}$'}\n",
    "        model_hash:\n          description: v8 legacy primary-code hash fallback；活动代码无writer，Phase E保留只读兼容并映射到artifact_hashes.primary_code。\n          type: string\n          pattern: '^[0-9a-fA-F]{64}$'\n        validated_model_hash:\n          description: v8 legacy validated primary-code hash fallback；活动代码无writer，Phase E保留只读兼容并映射到validated_artifact_hashes.primary_code。\n          type: string\n          pattern: '^[0-9a-fA-F]{64}$'\n",
)

# ---------------------------------------------------------------------------
# Transition Authority: canonical implementation layer names. Preserve event
# semantics; only make code-identity mismatches representable as stale layers.
# ---------------------------------------------------------------------------
replace_once("core/state_transition_contract.yaml", "version: 1.0.0\n", "version: 1.1.0\n")
replace_once(
    "core/state_transition_contract.yaml",
    '''compatibility:
  current_artifact_layer_names_are_v8_compatible: true
  model_layer_note: >-
    During Phase D, stale layer `model` remains the existing v8 artifact-layer name.
    Phase E owns migration to explicit primary_code/analysis_code identity names.
  legacy_string_dependency_read_supported: true
''',
    '''compatibility:
  canonical_artifact_layer_names_use_explicit_implementation_identity: true
  legacy_model_artifact_layer_read_supported: true
  legacy_model_artifact_layer_maps_to: primary_code
  legacy_model_artifact_layer_write_supported: false
  model_layer_note: >-
    Phase E canonicalizes the v8 implementation layer `model` to `primary_code`.
    The legacy name remains read-compatible only; mathematical model identity is owned by
    semantic_identity_hash and must never be inferred from an implementation artifact hash.
  legacy_string_dependency_read_supported: true
''',
)
replace_once(
    "core/state_transition_contract.yaml",
    "    stale_layers: [model, solution_workbook, result_analysis_workbook, matlab_script, figure_bundle, framework]\n",
    "    stale_layers: [primary_code, solution_workbook, result_analysis_workbook, matlab_script, figure_bundle, framework]\n",
)
replace_once(
    "core/state_transition_contract.yaml",
    "  primary_result:\n    stale_layers: [solution_workbook, result_analysis_workbook, matlab_script, figure_bundle, framework]\n",
    "  primary_result:\n    stale_layers: [primary_code, solution_workbook, result_analysis_workbook, matlab_script, figure_bundle, framework]\n",
)
replace_once(
    "core/state_transition_contract.yaml",
    "  analysis_result:\n    stale_layers: [result_analysis_workbook, matlab_script, figure_bundle, framework]\n",
    "  analysis_result:\n    stale_layers: [analysis_code, result_analysis_workbook, matlab_script, figure_bundle, framework]\n",
)
replace_once(
    "core/state_transition_contract.yaml",
    "- The three active stale-producing entrypoints must consume this Authority through scripts/state_transitions.py rather than maintain private stale-layer sets.\n",
    "- The three active stale-producing entrypoints must consume this Authority through scripts/state_transitions.py rather than maintain private stale-layer sets.\n- New transitions must never emit the legacy `model` artifact layer; Phase E canonical implementation layers are `primary_code` and `analysis_code`.\n",
)

# ---------------------------------------------------------------------------
# Output Contract + health lint use canonical implementation artifact names.
# ---------------------------------------------------------------------------
replace_once(
    "core/output_contract.yaml",
    "  - model\n  - solution_workbook\n",
    "  - primary_code\n  - analysis_code\n  - solution_workbook\n",
)
replace_once(
    "scripts/lint_skill_checks.py",
    '        "preprocessing_matlab_script", "model", "solution_workbook", "result_analysis_workbook", "matlab_script", "figure_bundle", "framework",\n',
    '        "preprocessing_matlab_script", "primary_code", "analysis_code", "solution_workbook", "result_analysis_workbook", "matlab_script", "figure_bundle", "framework",\n',
)

# ---------------------------------------------------------------------------
# sync_project: canonical snapshot/write and legacy-normalized comparison.
# ---------------------------------------------------------------------------
replace_once(
    "scripts/sync_project.py",
    "SKILL_ROOT = Path(__file__).resolve().parent.parent\nDEFAULT_SCHEMA_PATH",
    "SKILL_ROOT = Path(__file__).resolve().parent.parent\nSCRIPT_DIR = str(SKILL_ROOT / \"scripts\")\nif SCRIPT_DIR not in sys.path:\n    sys.path.insert(0, SCRIPT_DIR)\nimport artifact_identity as ARTIFACT_IDENTITY  # noqa: E402\nDEFAULT_SCHEMA_PATH",
)
replace_once(
    "scripts/sync_project.py",
    '''HASH_KEYS = (
    "data", "model", "solution_workbook", "result_analysis_workbook",
    "matlab_script", "figure_bundle", "framework",
)
''',
    '''HASH_KEYS = (
    "data", "primary_code", "analysis_code", "solution_workbook", "result_analysis_workbook",
    "matlab_script", "figure_bundle", "framework",
)
''',
)
replace_once(
    "scripts/sync_project.py",
    '''    hashes = {
        "data": data_hash,
        "model": sha256_file(primary_code) if primary_code else None,
        "solution_workbook": sha256_file(solution) if solution.is_file() else None,
''',
    '''    hashes = {
        "data": data_hash,
        "primary_code": sha256_file(primary_code) if primary_code else None,
        "analysis_code": sha256_file(analysis_code) if analysis_code else None,
        "solution_workbook": sha256_file(solution) if solution.is_file() else None,
''',
)
replace_once(
    "scripts/sync_project.py",
    '''def _normalized_validated_hashes(entry: Mapping[str, Any]) -> dict[str, str]:
    validated = dict(entry.get("validated_artifact_hashes", {}) or {})
    if "result_analysis_workbook" not in validated and "robustness_workbook" in validated:
        validated["result_analysis_workbook"] = validated["robustness_workbook"]
    return {key: value for key, value in validated.items() if key in HASH_KEYS}
''',
    '''def _normalized_validated_hashes(entry: Mapping[str, Any]) -> dict[str, str]:
    validated = ARTIFACT_IDENTITY.normalize_artifact_hashes(
        entry.get("validated_artifact_hashes"),
        legacy_primary_fallback=entry.get("validated_model_hash"),
    )
    if "result_analysis_workbook" not in validated and "robustness_workbook" in validated:
        validated["result_analysis_workbook"] = validated["robustness_workbook"]
    return {key: value for key, value in validated.items() if key in HASH_KEYS}
''',
)
replace_once(
    "scripts/sync_project.py",
    '''LAYER_TRANSITION_EVENTS = {
    "data": "data_changed",
    "model": "primary_code_changed",
    "solution_workbook": "solution_workbook_changed",
''',
    '''LAYER_TRANSITION_EVENTS = {
    "data": "data_changed",
    "primary_code": "primary_code_changed",
    "analysis_code": "analysis_code_changed",
    "solution_workbook": "solution_workbook_changed",
''',
)
replace_once(
    "scripts/sync_project.py",
    '''    entry = state.setdefault("subproblems", {}).setdefault(key, {})
    current = dict(snapshot.get("artifact_hashes", {}))
    transition_reports: list[dict[str, Any]] = []
''',
    '''    entry = state.setdefault("subproblems", {}).setdefault(key, {})
    ARTIFACT_IDENTITY.canonicalize_entry_hashes(entry)
    current = dict(snapshot.get("artifact_hashes", {}))
    transition_reports: list[dict[str, Any]] = []
''',
)

# ---------------------------------------------------------------------------
# State validation: canonical comparison, legacy alias/fallback reads, conflict
# blocking, solved requirement uses primary_code rather than ambiguous model.
# ---------------------------------------------------------------------------
replace_once(
    "scripts/validate_project_state.py",
    "import yaml\nfrom jsonschema import Draft202012Validator\n",
    "import yaml\nfrom jsonschema import Draft202012Validator\n\nimport artifact_identity as ARTIFACT_IDENTITY\n",
)
replace_once(
    "scripts/validate_project_state.py",
    '''ARTIFACT_LAYERS = {
    "data", "model", "solution_workbook", "result_analysis_workbook",
    "robustness_workbook", "matlab_script", "figure_bundle", "framework",
}
''',
    '''ARTIFACT_LAYERS = {
    "data", "model", "primary_code", "analysis_code", "solution_workbook",
    "result_analysis_workbook", "robustness_workbook", "matlab_script",
    "figure_bundle", "framework",
}
''',
)
replace_once(
    "scripts/validate_project_state.py",
    '''def _normalized_hashes(state: Mapping[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    current = dict(state.get("artifact_hashes", {}) or {})
    validated = dict(state.get("validated_artifact_hashes", {}) or {})
    if "result_analysis_workbook" not in current and "robustness_workbook" in current:
        current["result_analysis_workbook"] = current["robustness_workbook"]
    if "result_analysis_workbook" not in validated and "robustness_workbook" in validated:
        validated["result_analysis_workbook"] = validated["robustness_workbook"]
    if not current:
        if state.get("data_hash"):
            current["data"] = state["data_hash"]
        if state.get("model_hash"):
            current["model"] = state["model_hash"]
    if not validated:
        if state.get("validated_data_hash"):
            validated["data"] = state["validated_data_hash"]
        if state.get("validated_model_hash"):
            validated["model"] = state["validated_model_hash"]
    return current, validated
''',
    '''def _normalized_hashes(state: Mapping[str, Any]) -> tuple[dict[str, str], dict[str, str], list[str]]:
    issues = ARTIFACT_IDENTITY.entry_alias_issues(state)
    try:
        current = ARTIFACT_IDENTITY.normalize_artifact_hashes(
            state.get("artifact_hashes"), legacy_primary_fallback=state.get("model_hash")
        )
        validated = ARTIFACT_IDENTITY.normalize_artifact_hashes(
            state.get("validated_artifact_hashes"),
            legacy_primary_fallback=state.get("validated_model_hash"),
        )
    except ARTIFACT_IDENTITY.ArtifactIdentityError:
        # The detailed issue is already recorded. Keep deterministic partial maps so the
        # caller can report other state problems without silently selecting a winner.
        current = {key: value for key, value in dict(state.get("artifact_hashes", {}) or {}).items() if key != "model"}
        validated = {key: value for key, value in dict(state.get("validated_artifact_hashes", {}) or {}).items() if key != "model"}
    if "result_analysis_workbook" not in current and "robustness_workbook" in current:
        current["result_analysis_workbook"] = current["robustness_workbook"]
    if "result_analysis_workbook" not in validated and "robustness_workbook" in validated:
        validated["result_analysis_workbook"] = validated["robustness_workbook"]
    if "data" not in current and state.get("data_hash"):
        current["data"] = state["data_hash"]
    if "data" not in validated and state.get("validated_data_hash"):
        validated["data"] = state["validated_data_hash"]
    return current, validated, issues
''',
)
replace_once(
    "scripts/validate_project_state.py",
    '''    current, validated = _normalized_hashes(state)
    stale_layers = set(state.get("stale_layers", []) or [])
    invalid_layers = stale_layers - ARTIFACT_LAYERS
''',
    '''    current, validated, alias_issues = _normalized_hashes(state)
    issues.extend(f"{name}.{item}" for item in alias_issues)
    raw_stale_layers = set(state.get("stale_layers", []) or [])
    invalid_layers = raw_stale_layers - ARTIFACT_LAYERS
    stale_layers = set(ARTIFACT_IDENTITY.normalize_stale_layers(raw_stale_layers))
''',
)
replace_once(
    "scripts/validate_project_state.py",
    '        required = {"data", "model", "solution_workbook", "framework"}\n',
    '        required = {"data", "primary_code", "solution_workbook", "framework"}\n',
)

# ---------------------------------------------------------------------------
# Code delivery: publish canonical implementation identity on every new write.
# ---------------------------------------------------------------------------
replace_once(
    "scripts/validate_code_delivery.py",
    "import state_transitions as STATE_TRANSITIONS  # noqa: E402\n",
    "import state_transitions as STATE_TRANSITIONS  # noqa: E402\nimport artifact_identity as ARTIFACT_IDENTITY  # noqa: E402\n",
)
replace_once(
    "scripts/validate_code_delivery.py",
    '''    key = _question_key(problem)
    entry = state.setdefault("subproblems", {}).setdefault(key, {})
    entry["data_hash"] = str(config["data_sha256"]).lower()
''',
    '''    key = _question_key(problem)
    entry = state.setdefault("subproblems", {}).setdefault(key, {})
    try:
        ARTIFACT_IDENTITY.canonicalize_entry_hashes(entry)
    except ARTIFACT_IDENTITY.ArtifactIdentityError as exc:
        raise ValueError(f"artifact identity alias conflict: {exc}") from exc
    entry["data_hash"] = str(config["data_sha256"]).lower()
''',
)
replace_once(
    "scripts/validate_code_delivery.py",
    '''        entry["code"] = relative
        entry["primary_code_sha256"] = new_hash
        entry.setdefault("analysis_execution_status", "pending")
''',
    '''        entry["code"] = relative
        entry["primary_code_sha256"] = new_hash
        entry.setdefault("artifact_hashes", {})["primary_code"] = new_hash
        entry.setdefault("analysis_execution_status", "pending")
''',
)
replace_once(
    "scripts/validate_code_delivery.py",
    '''        entry["result_analysis_code"] = relative
        entry["analysis_code_sha256"] = new_hash
        if old_hash != new_hash:
''',
    '''        entry["result_analysis_code"] = relative
        entry["analysis_code_sha256"] = new_hash
        entry.setdefault("artifact_hashes", {})["analysis_code"] = new_hash
        if old_hash != new_hash:
''',
)

# ---------------------------------------------------------------------------
# User execution: migrate alias in memory and bind accepted workbook evidence to
# the exact canonical implementation identity that produced it.
# ---------------------------------------------------------------------------
replace_once(
    "scripts/validate_user_execution.py",
    "import openpyxl\nimport yaml\n\nFALSE_FLAGS",
    "import openpyxl\nimport yaml\n\nSCRIPT_DIR = str(Path(__file__).resolve().parent)\nif SCRIPT_DIR not in sys.path:\n    sys.path.insert(0, SCRIPT_DIR)\nimport artifact_identity as ARTIFACT_IDENTITY  # noqa: E402\n\nFALSE_FLAGS",
)
replace_once(
    "scripts/validate_user_execution.py",
    '''    key = question_key(problem)
    entry = {} if stage == "preprocessing" else (state.get("subproblems") or {}).get(key, {})
    issues.extend(validate_execution_evidence(config, state, entry, stage))
''',
    '''    key = question_key(problem)
    entry = {} if stage == "preprocessing" else (state.get("subproblems") or {}).get(key, {})
    if stage != "preprocessing":
        try:
            ARTIFACT_IDENTITY.canonicalize_entry_hashes(entry)
        except ARTIFACT_IDENTITY.ArtifactIdentityError as exc:
            issues.append(f"artifact identity alias conflict: {exc}")
    issues.extend(validate_execution_evidence(config, state, entry, stage))
''',
)
replace_once(
    "scripts/validate_user_execution.py",
    '''            if not issues and passed:
                entry.setdefault("validated_artifact_hashes", {})["solution_workbook"] = file_hash(workbook)
                entry["status"] = "solved"
''',
    '''            if not issues and passed:
                validated_hashes = entry.setdefault("validated_artifact_hashes", {})
                validated_hashes["primary_code"] = str(entry.get("primary_code_sha256", "")).lower()
                validated_hashes["solution_workbook"] = file_hash(workbook)
                entry["status"] = "solved"
''',
)
replace_once(
    "scripts/validate_user_execution.py",
    '''            if not issues and passed:
                entry.setdefault("validated_artifact_hashes", {})["result_analysis_workbook"] = file_hash(workbook)
                entry["status"] = "analyzed"
''',
    '''            if not issues and passed:
                validated_hashes = entry.setdefault("validated_artifact_hashes", {})
                validated_hashes["analysis_code"] = str(entry.get("analysis_code_sha256", "")).lower()
                validated_hashes["result_analysis_workbook"] = file_hash(workbook)
                entry["status"] = "analyzed"
''',
)

# ---------------------------------------------------------------------------
# Runtime Assurance: alias-aware expected hash and explicit blocking conflicts.
# ---------------------------------------------------------------------------
replace_once(
    "scripts/runtime_assurance.py",
    '''from semantic_identity import (
    SEMANTIC_IDENTITY_SCHEMA_VERSION,
    SemanticIdentityError,
    inspect_question_semantics,
    question_sections,
)
''',
    '''from semantic_identity import (
    SEMANTIC_IDENTITY_SCHEMA_VERSION,
    SemanticIdentityError,
    inspect_question_semantics,
    question_sections,
)
import artifact_identity as ARTIFACT_IDENTITY
''',
)
replace_once(
    "scripts/runtime_assurance.py",
    '''def _expected_hash(item: dict[str, Any], layer: str) -> str | None:
    validated = item.get("validated_artifact_hashes", {}) or {}
    current = item.get("artifact_hashes", {}) or {}
    return validated.get(layer) or current.get(layer)
''',
    '''def _expected_hash(item: dict[str, Any], layer: str) -> str | None:
    try:
        validated = ARTIFACT_IDENTITY.normalize_artifact_hashes(
            item.get("validated_artifact_hashes"),
            legacy_primary_fallback=item.get("validated_model_hash"),
        )
        current = ARTIFACT_IDENTITY.normalize_artifact_hashes(
            item.get("artifact_hashes"), legacy_primary_fallback=item.get("model_hash")
        )
    except ARTIFACT_IDENTITY.ArtifactIdentityError:
        return None
    return validated.get(layer) or current.get(layer)
''',
)
replace_once(
    "scripts/runtime_assurance.py",
    '''    evidence: list[dict[str, Any]] = []
    verified: set[str] = set()

    framework_path = root / FRAMEWORK_RELATIVE_PATH
''',
    '''    evidence: list[dict[str, Any]] = []
    verified: set[str] = set()
    conflicts: list[str] = []

    framework_path = root / FRAMEWORK_RELATIVE_PATH
''',
)
replace_once(
    "scripts/runtime_assurance.py",
    '''    subproblems = state.get("subproblems", {}) or {}
    for q in questions:
        item = subproblems.get(q, {}) or {}
        primary_ok = (
''',
    '''    subproblems = state.get("subproblems", {}) or {}
    for q in questions:
        item = subproblems.get(q, {}) or {}
        conflicts.extend(ARTIFACT_IDENTITY.entry_alias_issues(item, scope=q))
        primary_ok = (
''',
)
replace_once(
    "scripts/runtime_assurance.py",
    '''        "artifact_evidence": evidence,
        "conflicts": [],
        "ambiguities": ambiguities,
''',
    '''        "artifact_evidence": evidence,
        "conflicts": conflicts,
        "ambiguities": ambiguities,
''',
)

# ---------------------------------------------------------------------------
# Tests: convert Phase A characterization into Phase E regression, update layer
# expectations, and add dedicated alias/migration coverage.
# ---------------------------------------------------------------------------
replace_once(
    "tests/test_v900_refactor_characterization.py",
    '''    def test_artifact_hash_model_currently_means_primary_python_code(self):
''',
    '''    def test_artifact_hash_primary_code_now_has_explicit_implementation_identity(self):
''',
)
replace_once(
    "tests/test_v900_refactor_characterization.py",
    '''        self.assertEqual(
            snapshot["artifact_hashes"]["model"], snapshot["primary_code_sha256"]
        )
        self.assertNotIn("primary_code", snapshot["artifact_hashes"])
''',
    '''        self.assertEqual(
            snapshot["artifact_hashes"]["primary_code"], snapshot["primary_code_sha256"]
        )
        self.assertNotIn("model", snapshot["artifact_hashes"])
''',
)
replace_once(
    "tests/test_v900_state_transitions.py",
    '        self.assertEqual(CONTRACT["version"], "1.0.0")\n',
    '        self.assertEqual(CONTRACT["version"], "1.1.0")\n',
)
replace_once(
    "tests/test_v900_state_transitions.py",
    '        self.assertIn("model", q2["stale_layers"])\n',
    '        self.assertIn("primary_code", q2["stale_layers"])\n        self.assertNotIn("model", q2["stale_layers"])\n',
)
replace_all(
    "tests/test_v711_model_approval_gate.py",
    '            self.assertIn("model", ',
    '            self.assertIn("primary_code", ',
    2,
)
replace_once(
    "tests/test_schemas.py",
    '        self.assertIn("result_analysis_workbook", defs["artifact_hashes"]["properties"])\n',
    '        self.assertIn("result_analysis_workbook", defs["artifact_hashes"]["properties"])\n        self.assertIn("primary_code", defs["artifact_hashes"]["properties"])\n        self.assertIn("analysis_code", defs["artifact_hashes"]["properties"])\n        self.assertIn("model", defs["artifact_hashes"]["properties"])  # v8 read compatibility\n',
)
replace_once(
    "tests/test_schemas.py",
    '''                "raw_data", "preprocessing_decision", "preprocessing_code", "preprocessing_workbook",
                "preprocessing_matlab_script", "model", "solution_workbook", "result_analysis_workbook",
                "matlab_script", "figure_bundle", "framework",
''',
    '''                "raw_data", "preprocessing_decision", "preprocessing_code", "preprocessing_workbook",
                "preprocessing_matlab_script", "primary_code", "analysis_code", "solution_workbook",
                "result_analysis_workbook", "matlab_script", "figure_bundle", "framework",
''',
)

write(
    "tests/test_v900_artifact_identity.py",
    '''from __future__ import annotations

import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import artifact_identity as ARTIFACT_IDENTITY


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SYNC = load_module("v900_phase_e_sync", "scripts/sync_project.py")
STATE_VALIDATION = load_module("v900_phase_e_state_validation", "scripts/validate_project_state.py")
RUNTIME = load_module("v900_phase_e_runtime", "scripts/runtime_assurance.py")
CODE = load_module("v900_phase_e_code_delivery", "scripts/validate_code_delivery.py")
TRANSITIONS = load_module("v900_phase_e_transitions", "scripts/state_transitions.py")
CONTRACT = yaml.safe_load((ROOT / "core/state_transition_contract.yaml").read_text(encoding="utf-8"))


class ArtifactAliasTests(unittest.TestCase):
    def test_legacy_model_alias_reads_as_primary_code(self):
        digest = "a" * 64
        normalized = ARTIFACT_IDENTITY.normalize_artifact_hashes({"model": digest})
        self.assertEqual(normalized["primary_code"], digest)
        self.assertNotIn("model", normalized)

    def test_equal_old_and_new_alias_is_readable_but_canonicalized(self):
        digest = "a" * 64
        normalized = ARTIFACT_IDENTITY.normalize_artifact_hashes(
            {"model": digest.upper(), "primary_code": digest}
        )
        self.assertEqual(normalized["primary_code"], digest)
        self.assertNotIn("model", normalized)

    def test_conflicting_old_and_new_alias_blocks(self):
        with self.assertRaisesRegex(ARTIFACT_IDENTITY.ArtifactIdentityError, "conflicts"):
            ARTIFACT_IDENTITY.normalize_artifact_hashes(
                {"model": "a" * 64, "primary_code": "b" * 64}
            )

    def test_model_hash_is_read_only_primary_code_fallback(self):
        digest = "c" * 64
        current, validated, issues = STATE_VALIDATION._normalized_hashes(
            {"model_hash": digest, "validated_model_hash": digest}
        )
        self.assertEqual(issues, [])
        self.assertEqual(current["primary_code"], digest)
        self.assertEqual(validated["primary_code"], digest)
        self.assertNotIn("model", current)


class CanonicalWriteTests(unittest.TestCase):
    def test_sync_snapshot_writes_primary_and_analysis_code_not_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "问题一求解"
            folder.mkdir(parents=True)
            primary = folder / "问题一求解.py"
            analysis = folder / "问题一结果深化分析.py"
            primary.write_text("print('primary')\\n", encoding="utf-8")
            analysis.write_text("print('analysis')\\n", encoding="utf-8")
            (root / "模型论文框架.md").write_text("# 模型论文框架\\n\\n### Q1\\n", encoding="utf-8")
            schema = SYNC.load_yaml(SYNC.DEFAULT_SCHEMA_PATH)
            snapshot = SYNC._snapshot_question(
                root,
                "问题一",
                {
                    "status": "designed",
                    "framework_section": "### Q1",
                    "analysis_code_sha256": hashlib.sha256(analysis.read_bytes()).hexdigest(),
                },
                schema,
                None,
                None,
            )
        self.assertEqual(snapshot["artifact_hashes"]["primary_code"], snapshot["primary_code_sha256"])
        self.assertEqual(snapshot["artifact_hashes"]["analysis_code"], snapshot["analysis_code_sha256"])
        self.assertNotIn("model", snapshot["artifact_hashes"])

    def test_code_delivery_primary_write_uses_only_primary_code_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "state").mkdir()
            folder = root / "问题一求解"
            folder.mkdir()
            script = folder / "问题一求解.py"
            script.write_text("print('primary')\\n", encoding="utf-8")
            state = {
                "project": {"current_phase": "solve_validate"},
                "subproblems": {"Q1": {"status": "designed"}},
            }
            (root / "state" / "project_state.yaml").write_text(
                yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            CODE.update_state(
                root,
                {"problem_name": "问题一", "stage": "primary", "data_sha256": "a" * 64},
                script,
            )
            updated = yaml.safe_load((root / "state" / "project_state.yaml").read_text(encoding="utf-8"))
        hashes = updated["subproblems"]["Q1"]["artifact_hashes"]
        self.assertEqual(hashes["primary_code"], hashlib.sha256(script.read_bytes()).hexdigest())
        self.assertNotIn("model", hashes)


class TransitionAndRuntimeTests(unittest.TestCase):
    def _entry(self):
        return {
            "status": "validated",
            "depends_on": [],
            "model_challenge_status": "passed",
            "human_model_approval_status": "approved",
            "primary_execution_status": "accepted",
            "analysis_execution_status": "accepted",
            "result_quality_status": "passed",
            "result_analysis_status": "passed",
            "validation_status": "passed",
            "result_summary_status": "current",
            "artifacts_stale": False,
            "stale_layers": [],
        }

    def test_primary_change_does_not_invalidate_mathematical_approval(self):
        state = {"subproblems": {"Q1": self._entry()}}
        TRANSITIONS.apply_transition(
            state, event="primary_code_changed", source_question="Q1", contract=CONTRACT
        )
        q1 = state["subproblems"]["Q1"]
        self.assertEqual(q1["model_challenge_status"], "passed")
        self.assertEqual(q1["human_model_approval_status"], "approved")
        self.assertIn("primary_code", q1["stale_layers"])

    def test_analysis_change_does_not_stale_primary_result(self):
        state = {"subproblems": {"Q1": self._entry()}}
        TRANSITIONS.apply_transition(
            state, event="analysis_code_changed", source_question="Q1", contract=CONTRACT
        )
        q1 = state["subproblems"]["Q1"]
        self.assertEqual(q1["result_quality_status"], "passed")
        self.assertNotIn("solution_workbook", q1["stale_layers"])
        self.assertIn("analysis_code", q1["stale_layers"])

    def test_runtime_reports_alias_conflict_instead_of_selecting_a_hash(self):
        item = {
            "artifact_hashes": {"model": "a" * 64, "primary_code": "b" * 64},
            "validated_artifact_hashes": {},
        }
        issues = ARTIFACT_IDENTITY.entry_alias_issues(item, scope="Q1")
        self.assertTrue(any("conflicts" in issue for issue in issues))
        self.assertIsNone(RUNTIME._expected_hash(item, "primary_code"))


if __name__ == "__main__":
    unittest.main()
''',
)

# ---------------------------------------------------------------------------
# Required audit record from the Phase E plan.
# ---------------------------------------------------------------------------
write(
    "docs/phase_e_artifact_identity_inventory.md",
    '''# Phase E Artifact Identity Reference Inventory

Baseline: `main@5ec9974bfcf87075d509da9fcced69541013877d`  
Scope: Phase E additive naming migration only. No Phase F transactional writes, Phase G resolver policy, Phase H mechanical split, or Phase I compatibility deletion.

| Field | Active readers before E | Active writers before E | Proven semantic meaning | Phase E action |
|---|---|---|---|---|
| `artifact_hashes.model` | `validate_project_state.py`, `sync_project.py` stale comparison/fixtures | `sync_project.py::_snapshot_question()` | SHA-256 of the primary Python implementation, not mathematical model semantics | Read as legacy alias only when `primary_code` is absent; block conflicting dual presence; stop all new writes |
| `artifact_hashes.primary_code` | none before E | none before E | Canonical primary implementation identity | Add to Schema; canonical write/read key in sync and delivery flows |
| `artifact_hashes.analysis_code` | none before E | none before E | Canonical result-analysis implementation identity | Add to Schema; canonical write/read key in sync and analysis delivery flows |
| `primary_code_sha256` | `validate_user_execution.py`, `sync_project.py`, delivery/runtime tests | `validate_code_delivery.py` | Exact delivered primary Python hash used by workbook receipt binding | Keep; it is already unambiguous stage-specific delivery provenance and must equal canonical `artifact_hashes.primary_code` on new writes |
| `analysis_code_sha256` | `validate_user_execution.py`, `sync_project.py`, delivery/runtime tests | `validate_code_delivery.py` | Exact delivered analysis Python hash used by workbook receipt binding | Keep; bind new writes to canonical `artifact_hashes.analysis_code` |
| `model_hash` | `validate_project_state.py` only | no active writer found | Legacy fallback for primary implementation hash | Keep read-only compatibility; map to `primary_code` only when canonical artifact hash is absent; deletion deferred to Phase I |
| `validated_model_hash` | `validate_project_state.py` only | no active writer found | Legacy validated fallback for primary implementation hash | Keep read-only compatibility; map to validated `primary_code`; deletion deferred to Phase I |
| `semantic_identity_hash` | semantic governance, Model Approval, Runtime Assurance | semantic governance | Mathematical semantic identity from the Framework SIB | Unchanged; explicitly separate from implementation identity |
| `semantic_hash` | legacy semantic compatibility readers | legacy migration path only | Legacy Markdown semantic-scope provenance | Unchanged by E; Phase C/Phase I compatibility policy continues to govern it |

## Migration invariants

1. `artifact_hashes.model -> artifact_hashes.primary_code` is mechanical compatibility mapping only.
2. `model` and `primary_code` may be read together only when their values are equal; disagreement is blocking.
3. New writes never persist `artifact_hashes.model` or the legacy stale layer `model`.
4. Primary-code freshness never substitutes for `semantic_identity_hash` and never invalidates Human Model Approval by itself.
5. Analysis-code changes do not invalidate the accepted primary result.
6. `model_hash / validated_model_hash` are not deleted in Phase E because the repository audit proves they still participate in legacy reads.
''',
)

# Changelog staged record.
replace_once(
    "CHANGELOG.md",
    "\n## Previous release: 8.7.3\n",
    '''
### Unreleased v9.0.0 staged refactor — Phase E

- Migrated implementation artifact identity from ambiguous `artifact_hashes.model` to explicit `artifact_hashes.primary_code` and `artifact_hashes.analysis_code` while retaining v8 read compatibility only.
- Added deterministic alias handling: legacy `model` maps to `primary_code` only when the canonical field is absent or equal; conflicting old/new values are blocking and no active writer dual-writes the two names.
- Aligned Project State Schema, State Transition Authority, project sync, code delivery, user-execution receipts, Runtime Assurance integration pointers, Output Contract and health lint around the canonical implementation names without changing mathematical Semantic Identity or Model Approval semantics.
- Audited `model_hash / validated_model_hash` across the active repository and confirmed they have no active writer and only serve legacy primary-code fallback reads; they remain compatibility fields until the Phase I v9 removal gate.
- Added Phase E migration/alias regressions and retained the 8.7.4 release carrier. Phase F transactional writes and all later staged phases remain out of scope.

## Previous release: 8.7.3
''',
)

# Protected baseline: only validate_code_delivery.py is intentionally changed among protected files.
protected = ROOT / "tests/test_v830_editable_mechanism_diagram.py"
text = protected.read_text(encoding="utf-8")
old_prefix = '        "scripts/validate_code_delivery.py": "'
indices = [i for i, line in enumerate(text.splitlines()) if line.startswith(old_prefix)]
if len(indices) != 1:
    raise RuntimeError(f"protected validate_code_delivery baseline matches={len(indices)}")
lines = text.splitlines()
lines[indices[0]] = f'        "scripts/validate_code_delivery.py": "{git_blob_sha("scripts/validate_code_delivery.py")}",'
protected.write_text("\n".join(lines) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")

print("Phase E artifact identity migration applied")
