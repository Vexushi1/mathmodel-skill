#!/usr/bin/env python3
"""One-shot deterministic Phase F integration patch.

This helper is intentionally removed by the temporary Phase F integration workflow
before the final implementation commit.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace(relative: str, old: str, new: str, expected: int = 1) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{relative}: expected {expected} matches, got {count}: {old[:100]!r}")
    path.write_text(text.replace(old, new, expected), encoding="utf-8")


# ---------------------------------------------------------------------------
# Schema and example: optional-on-read for v8 compatibility, canonical on write.
# ---------------------------------------------------------------------------
replace(
    "core/project_state.schema.yaml",
    """      current_phase:\n        type: string\n        enum: [problem_audit, model_design, data_preprocessing, solve_validate, result_analysis, figure_evidence, writing_docx, writing_latex, ai_cleanup, latex_compile_quality, review_delivery, completed]\n      problem_types:\n""",
    """      current_phase:\n        type: string\n        enum: [problem_audit, model_design, data_preprocessing, solve_validate, result_analysis, figure_evidence, writing_docx, writing_latex, ai_cleanup, latex_compile_quality, review_delivery, completed]\n      state_generation:\n        description: Phase F optimistic project-write generation；legacy v8 projects may omit and are read as generation 0.\n        type: integer\n        minimum: 0\n        default: 0\n      problem_types:\n""",
)
replace(
    "state/project_state.example.yaml",
    """  current_phase: model_design\n  objectives: [explanation, optimization]\n""",
    """  current_phase: model_design\n  state_generation: 0\n  objectives: [explanation, optimization]\n""",
)

# ---------------------------------------------------------------------------
# sync_project.py: framework/state/report become one recoverable transaction.
# ---------------------------------------------------------------------------
replace(
    "scripts/sync_project.py",
    """import artifact_identity as ARTIFACT_IDENTITY  # noqa: E402\nDEFAULT_SCHEMA_PATH = SKILL_ROOT / \"core\" / \"workbook_schema.yaml\"\n""",
    """import artifact_identity as ARTIFACT_IDENTITY  # noqa: E402\nimport project_transaction as PROJECT_TX  # noqa: E402\nDEFAULT_SCHEMA_PATH = SKILL_ROOT / \"core\" / \"workbook_schema.yaml\"\n""",
)
replace(
    "scripts/sync_project.py",
    """def _update_framework_header(path: Path, scope: str, stale: bool) -> None:\n    if not path.is_file():\n        return\n    lines = path.read_text(encoding=\"utf-8\").replace(\"\\r\\n\", \"\\n\").replace(\"\\r\", \"\\n\").splitlines()\n    timestamp = datetime.now(timezone.utc).isoformat()\n    lines = _replace_or_prepend(lines, \"- 最近同步：\", f\"- 最近同步：`{scope}`\")\n    lines = _replace_or_prepend(lines, \"- 最近同步时间：\", f\"- 最近同步时间：`{timestamp}`\")\n    lines = _replace_or_prepend(lines, \"- 当前状态：\", f\"- 当前状态：`{'stale' if stale else 'current'}`\")\n    path.write_text(\"\\n\".join(lines).rstrip() + \"\\n\", encoding=\"utf-8\")\n""",
    """def _framework_header_text(path: Path, scope: str, stale: bool) -> str | None:\n    \"\"\"Return the next framework text without mutating the live project.\"\"\"\n    if not path.is_file():\n        return None\n    lines = path.read_text(encoding=\"utf-8\").replace(\"\\r\\n\", \"\\n\").replace(\"\\r\", \"\\n\").splitlines()\n    timestamp = datetime.now(timezone.utc).isoformat()\n    lines = _replace_or_prepend(lines, \"- 最近同步：\", f\"- 最近同步：`{scope}`\")\n    lines = _replace_or_prepend(lines, \"- 最近同步时间：\", f\"- 最近同步时间：`{timestamp}`\")\n    lines = _replace_or_prepend(lines, \"- 当前状态：\", f\"- 当前状态：`{'stale' if stale else 'current'}`\")\n    return \"\\n\".join(lines).rstrip() + \"\\n\"\n""",
)
replace(
    "scripts/sync_project.py",
    """    state_path = root / \"state/project_state.yaml\"\n    framework_path = root / \"模型论文框架.md\"\n    state = load_yaml(state_path)\n    schema = load_yaml(Path(schema_path))\n""",
    """    state_path = root / \"state/project_state.yaml\"\n    framework_path = root / \"模型论文框架.md\"\n    if write and state_path.is_file():\n        _, state, base_generation = PROJECT_TX.load_state_for_update(root)\n    else:\n        state = load_yaml(state_path)\n        base_generation = PROJECT_TX.state_generation(state)\n    schema = load_yaml(Path(schema_path))\n""",
)
replace(
    "scripts/sync_project.py",
    """    if write and state_path.is_file():\n        any_stale = any(\n            bool(entry.get(\"artifacts_stale\"))\n            for entry in (state.get(\"subproblems\") or {}).values()\n            if isinstance(entry, Mapping)\n        )\n        framework = state.setdefault(\"paper_framework\", {})\n        if _uses_fragment_stale(framework):\n            stale_fragments = _mark_paper_fragments_stale(framework, set(stale_questions))\n            framework[\"sync_status\"] = \"current\"\n            header_stale = False\n        else:\n            framework[\"sync_status\"] = \"stale\" if any_stale else \"current\"\n            header_stale = any_stale\n        framework[\"last_sync_scope\"] = scope\n        framework[\"last_synced_at\"] = datetime.now(timezone.utc).isoformat()\n        _update_framework_header(framework_path, scope, header_stale)\n        if framework_path.is_file():\n            framework[\"sha256\"] = sha256_file(framework_path)\n        state.setdefault(\"artifacts\", {})[\"sync_report\"] = \"sync_report.yaml\"\n        state.setdefault(\"execution\", {})[\"last_sync_report\"] = \"sync_report.yaml\"\n        state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding=\"utf-8\")\n    else:\n""",
    """    framework_text_for_write: str | None = None\n    if write and state_path.is_file():\n        any_stale = any(\n            bool(entry.get(\"artifacts_stale\"))\n            for entry in (state.get(\"subproblems\") or {}).values()\n            if isinstance(entry, Mapping)\n        )\n        framework = state.setdefault(\"paper_framework\", {})\n        if _uses_fragment_stale(framework):\n            stale_fragments = _mark_paper_fragments_stale(framework, set(stale_questions))\n            framework[\"sync_status\"] = \"current\"\n            header_stale = False\n        else:\n            framework[\"sync_status\"] = \"stale\" if any_stale else \"current\"\n            header_stale = any_stale\n        framework[\"last_sync_scope\"] = scope\n        framework[\"last_synced_at\"] = datetime.now(timezone.utc).isoformat()\n        framework_text_for_write = _framework_header_text(framework_path, scope, header_stale)\n        if framework_text_for_write is not None:\n            framework[\"sha256\"] = hashlib.sha256(framework_text_for_write.encode(\"utf-8\")).hexdigest()\n        state.setdefault(\"artifacts\", {})[\"sync_report\"] = \"sync_report.yaml\"\n        state.setdefault(\"execution\", {})[\"last_sync_report\"] = \"sync_report.yaml\"\n    else:\n""",
)
replace(
    "scripts/sync_project.py",
    """        \"framework_hash\": sha256_file(framework_path) if framework_path.is_file() else None,\n""",
    """        \"framework_hash\": (\n            hashlib.sha256(framework_text_for_write.encode(\"utf-8\")).hexdigest()\n            if framework_text_for_write is not None\n            else sha256_file(framework_path) if framework_path.is_file() else None\n        ),\n""",
)
replace(
    "scripts/sync_project.py",
    """    if write:\n        report_path = root / \"sync_report.yaml\"\n        report_path.write_text(yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding=\"utf-8\")\n        if state_path.is_file() and framework_path.is_file():\n            expected = ((load_yaml(state_path).get(\"paper_framework\") or {}).get(\"sha256\"))\n            actual = sha256_file(framework_path)\n            if expected != actual:\n                report[\"issues\"].append(\"写后哈希自检失败: paper_framework.sha256不一致\")\n                report[\"status\"] = \"failed\"\n                report_path.write_text(yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding=\"utf-8\")\n    return report\n""",
    """    if write:\n        report_text = yaml.safe_dump(report, allow_unicode=True, sort_keys=False)\n        if state_path.is_file():\n            before_state = (\n                [(\"模型论文框架.md\", framework_text_for_write)]\n                if framework_text_for_write is not None\n                else []\n            )\n\n            def _validate_staged_sync(staged: Mapping[str, Path]) -> None:\n                staged_state = load_yaml(staged[PROJECT_TX.STATE_RELATIVE_PATH])\n                if framework_text_for_write is not None:\n                    staged_framework = staged[\"模型论文框架.md\"]\n                    expected = ((staged_state.get(\"paper_framework\") or {}).get(\"sha256\"))\n                    actual = sha256_file(staged_framework)\n                    if expected != actual:\n                        raise ValueError(\"staged paper_framework.sha256 self-check failed\")\n                staged_report = load_yaml(staged[\"sync_report.yaml\"])\n                if staged_report.get(\"framework_hash\") != report.get(\"framework_hash\"):\n                    raise ValueError(\"staged sync report framework hash self-check failed\")\n\n            PROJECT_TX.commit_project_state(\n                root,\n                state,\n                expected_generation=base_generation,\n                writes_before_state=before_state,\n                writes_after_state=[(\"sync_report.yaml\", report_text)],\n                validators=[_validate_staged_sync],\n            )\n        else:\n            PROJECT_TX.atomic_write_text(root / \"sync_report.yaml\", report_text)\n    return report\n""",
)

# ---------------------------------------------------------------------------
# Semantic governance: recover before reading, then generation-checked state commit.
# ---------------------------------------------------------------------------
replace(
    "scripts/validate_semantic_governance.py",
    """import state_transitions as STATE_TRANSITIONS  # noqa: E402\n\nSEMANTIC_GOVERNANCE_VERSION = \"1.0.0\"\n""",
    """import state_transitions as STATE_TRANSITIONS  # noqa: E402\nimport project_transaction as PROJECT_TX  # noqa: E402\n\nSEMANTIC_GOVERNANCE_VERSION = \"1.0.0\"\n""",
)
replace(
    "scripts/validate_semantic_governance.py",
    """    state_path = root / \"state\" / \"project_state.yaml\"\n    framework_path = root / \"模型论文框架.md\"\n    state = load_yaml(state_path)\n    issues: list[str] = []\n""",
    """    state_path = root / \"state\" / \"project_state.yaml\"\n    framework_path = root / \"模型论文框架.md\"\n    if write and state_path.is_file():\n        _, state, base_generation = PROJECT_TX.load_state_for_update(root)\n    else:\n        state = load_yaml(state_path)\n        base_generation = PROJECT_TX.state_generation(state)\n    issues: list[str] = []\n""",
)
replace(
    "scripts/validate_semantic_governance.py",
    """        if state_path.is_file():\n            state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding=\"utf-8\")\n\n    return {\n""",
    """        if state_path.is_file():\n            PROJECT_TX.commit_project_state(\n                root, state, expected_generation=base_generation\n            )\n\n    return {\n""",
)

# ---------------------------------------------------------------------------
# Code delivery: every control-plane state mutation uses the shared generation gate.
# ---------------------------------------------------------------------------
replace(
    "scripts/validate_code_delivery.py",
    """import state_transitions as STATE_TRANSITIONS  # noqa: E402\nimport artifact_identity as ARTIFACT_IDENTITY  # noqa: E402\n""",
    """import state_transitions as STATE_TRANSITIONS  # noqa: E402\nimport artifact_identity as ARTIFACT_IDENTITY  # noqa: E402\nimport project_transaction as PROJECT_TX  # noqa: E402\n""",
)
replace(
    "scripts/validate_code_delivery.py",
    """    if not state_path.is_file():\n        return []\n    state = load_yaml(state_path)\n    problem = str(config[\"problem_name\"])\n""",
    """    if not state_path.is_file():\n        return []\n    _, state, base_generation = PROJECT_TX.load_state_for_update(project_root)\n    problem = str(config[\"problem_name\"])\n""",
)
replace(
    "scripts/validate_code_delivery.py",
    """        state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding=\"utf-8\")\n        return transition_reports\n\n    key = _question_key(problem)\n""",
    """        PROJECT_TX.commit_project_state(\n            project_root, state, expected_generation=base_generation\n        )\n        return transition_reports\n\n    key = _question_key(problem)\n""",
)
replace(
    "scripts/validate_code_delivery.py",
    """    state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding=\"utf-8\")\n    return transition_reports\n\n\ndef discover_scripts""",
    """    PROJECT_TX.commit_project_state(\n        project_root, state, expected_generation=base_generation\n    )\n    return transition_reports\n\n\ndef discover_scripts""",
)

# ---------------------------------------------------------------------------
# Returned-workbook acceptance: mutate in memory, then one generation-checked commit.
# ---------------------------------------------------------------------------
replace(
    "scripts/validate_user_execution.py",
    """import artifact_identity as ARTIFACT_IDENTITY  # noqa: E402\n\nFALSE_FLAGS = (\n""",
    """import artifact_identity as ARTIFACT_IDENTITY  # noqa: E402\nimport project_transaction as PROJECT_TX  # noqa: E402\n\nFALSE_FLAGS = (\n""",
)
replace(
    "scripts/validate_user_execution.py",
    """    if not state_path.is_file():\n        raise SystemExit(\"缺少state/project_state.yaml\")\n    state = load_yaml(state_path)\n    workbooks = (\n""",
    """    if not state_path.is_file():\n        raise SystemExit(\"缺少state/project_state.yaml\")\n    if args.write:\n        _, state, base_generation = PROJECT_TX.load_state_for_update(root)\n    else:\n        state = load_yaml(state_path)\n        base_generation = PROJECT_TX.state_generation(state)\n    workbooks = (\n""",
)
replace(
    "scripts/validate_user_execution.py",
    """    if args.write:\n        state_path.write_text(\n            yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding=\"utf-8\"\n        )\n    report = {\n""",
    """    if args.write:\n        PROJECT_TX.commit_project_state(\n            root, state, expected_generation=base_generation\n        )\n    report = {\n""",
)

print("Phase F transactional writer integration applied")
