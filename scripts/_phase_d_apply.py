#!/usr/bin/env python3
"""One-shot deterministic Phase D patcher. Removed by its runner after success."""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def write(relative: str, text: str) -> None:
    (ROOT / relative).write_text(text, encoding="utf-8")


def replace_once(relative: str, old: str, new: str) -> None:
    text = read(relative)
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{relative}: expected exactly one match, got {count}: {old[:120]!r}")
    write(relative, text.replace(old, new, 1))


def git_blob_sha(relative: str) -> str:
    data = (ROOT / relative).read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


# Authority pointers / dependency closure.
replace_once(
    "core/bootstrap.yaml",
    "  project_state: core/project_state.schema.yaml\n  workbook: core/workbook_schema.yaml\n",
    "  project_state: core/project_state.schema.yaml\n  state_transitions: core/state_transition_contract.yaml\n  workbook: core/workbook_schema.yaml\n",
)
replace_once(
    "SKILL_CHANGE_GOVERNANCE.md",
    "| 项目状态、哈希与 stale | `core/project_state.schema.yaml` |\n| 竞赛差异 |",
    "| 项目状态、哈希与 stale | `core/project_state.schema.yaml` |\n| 项目状态转换、stale 传播与依赖失效 | `core/state_transition_contract.yaml` |\n| 竞赛差异 |",
)
replace_once(
    "core/module_manifest.yaml",
    "  project_state: core/project_state.schema.yaml\n  user_execution: core/user_execution_contract.yaml\n",
    "  project_state: core/project_state.schema.yaml\n  state_transition: core/state_transition_contract.yaml\n  user_execution: core/user_execution_contract.yaml\n",
)
replace_once(
    "core/module_manifest.yaml",
    "    - Propagates stale recursively through typed cross-question dependencies before accepting a new semantic identity.\n",
    "    - Propagates stale recursively through typed cross-question dependencies using the single Authority `core/state_transition_contract.yaml` before accepting a new semantic identity.\n",
)
replace_once(
    "core/runtime_assurance_contract.yaml",
    "    gate:semantic_governance: [project_state]\n    gate:model_approval: [project_state, model_approval]\n    gate:code_delivery: [code_quality]\n    gate:user_execution_receipt: [user_execution, workbook, numerical_verification]\n    gate:project_sync: [project_state, output]\n",
    "    gate:semantic_governance: [project_state, state_transition]\n    gate:model_approval: [project_state, model_approval]\n    gate:code_delivery: [code_quality, state_transition]\n    gate:user_execution_receipt: [user_execution, workbook, numerical_verification]\n    gate:project_sync: [project_state, output, state_transition]\n",
)

# Semantic governance: remove local stale/dependency policy and call the shared engine.
replace_once(
    "scripts/validate_semantic_governance.py",
    "import argparse\nimport sys\n",
    "import argparse\nfrom copy import deepcopy\nimport sys\n",
)
replace_once(
    "scripts/validate_semantic_governance.py",
    "    sha256_text,\n)\n\nSEMANTIC_GOVERNANCE_VERSION = \"1.0.0\"\nPRIMARY_STALE_LAYERS = {\n    \"model\",\n    \"solution_workbook\",\n    \"result_analysis_workbook\",\n    \"matlab_script\",\n    \"figure_bundle\",\n    \"framework\",\n}\n",
    "    sha256_text,\n)\nimport state_transitions as STATE_TRANSITIONS  # noqa: E402\n\nSEMANTIC_GOVERNANCE_VERSION = \"1.0.0\"\nSTATE_TRANSITION_CONTRACT_PATH = Path(__file__).resolve().parents[1] / \"core\" / \"state_transition_contract.yaml\"\n",
)
replace_once(
    "scripts/validate_semantic_governance.py",
    "def load_yaml(path: Path) -> dict[str, Any]:\n    if not path.is_file():\n        return {}\n    return yaml.safe_load(path.read_text(encoding=\"utf-8\")) or {}\n\n\ndef _dependency_questions(entry: Mapping[str, Any]) -> set[str]:\n    values: set[str] = set()\n    for item in entry.get(\"depends_on\", []) or []:\n        if isinstance(item, str):\n            values.add(item)\n        elif isinstance(item, Mapping) and item.get(\"question\"):\n            values.add(str(item[\"question\"]))\n    return values\n\n\ndef _dependent_closure(subproblems: Mapping[str, Any], sources: set[str]) -> set[str]:\n    affected = set(sources)\n    changed = True\n    while changed:\n        changed = False\n        for key, entry in subproblems.items():\n            if key in affected or not isinstance(entry, Mapping):\n                continue\n            if _dependency_questions(entry) & affected:\n                affected.add(str(key))\n                changed = True\n    return affected\n\n\ndef _mark_stale(entry: dict[str, Any]) -> None:\n    entry[\"artifacts_stale\"] = True\n    entry[\"stale_layers\"] = sorted(set(entry.get(\"stale_layers\", []) or []) | PRIMARY_STALE_LAYERS)\n    entry[\"result_quality_status\"] = \"pending\"\n    entry[\"result_analysis_status\"] = \"pending\"\n    entry[\"validation_status\"] = \"pending\"\n    entry[\"result_summary_status\"] = \"stale\"\n    if \"primary_execution_status\" in entry:\n        entry[\"primary_execution_status\"] = \"pending\"\n    if \"analysis_execution_status\" in entry:\n        entry[\"analysis_execution_status\"] = \"pending\"\n    # v7.11+: a semantic dependency change invalidates any approval that was\n    # bound to the previous model semantics. Keep the historical approved\n    # revision/hash for provenance, but make the current challenge/approval\n    # unusable until the affected question is challenged and explicitly\n    # approved again. Old projects that never had approval fields remain\n    # read-only compatible and are not backfilled here.\n    if \"model_challenge_status\" in entry:\n        entry[\"model_challenge_status\"] = \"stale\"\n    if \"human_model_approval_status\" in entry:\n        entry[\"human_model_approval_status\"] = \"stale\"\n\n\n",
    "def load_yaml(path: Path) -> dict[str, Any]:\n    if not path.is_file():\n        return {}\n    return yaml.safe_load(path.read_text(encoding=\"utf-8\")) or {}\n\n\nSTATE_TRANSITION_CONTRACT = load_yaml(STATE_TRANSITION_CONTRACT_PATH)\n\n\ndef _mark_stale(entry: dict[str, Any]) -> None:\n    \"\"\"Compatibility helper; the transition policy itself lives in the shared Authority.\"\"\"\n    STATE_TRANSITIONS.apply_local_event(\n        entry, \"semantic_identity_changed\", STATE_TRANSITION_CONTRACT\n    )\n\n\n",
)
replace_once(
    "scripts/validate_semantic_governance.py",
    "    affected = _dependent_closure(subproblems, changed_sources)\n    stale_fragments: list[str] = []\n    if write and changed_sources:\n        for key in affected:\n            entry = subproblems.get(key)\n            if isinstance(entry, dict):\n                _mark_stale(entry)\n        paper_framework = state.setdefault(\"paper_framework\", {})\n        stale_fragments = _mark_paper_fragments_stale(paper_framework, affected)\n        # sync_status means the framework/state record is synchronized, not that every fragment is current.\n        paper_framework[\"sync_status\"] = \"current\"\n",
    "    transition_state = state if write else deepcopy(state)\n    transition_reports: list[dict[str, Any]] = []\n    for key in sorted(changed_sources):\n        transition_entry = ((transition_state.get(\"subproblems\") or {}).get(key) or {})\n        transition_reports.append(\n            STATE_TRANSITIONS.apply_transition(\n                transition_state,\n                event=\"semantic_identity_changed\",\n                source_question=key,\n                contract=STATE_TRANSITION_CONTRACT,\n                context={\n                    \"semantic_change_categories\": list(\n                        transition_entry.get(\"semantic_change_categories\", []) or []\n                    )\n                },\n            )\n        )\n    merged_transitions = STATE_TRANSITIONS.merge_transition_reports(transition_reports)\n    affected = set(merged_transitions[\"affected_questions\"])\n    dependency_cycles = (\n        merged_transitions[\"dependency_cycles\"]\n        or STATE_TRANSITIONS.dependency_cycles(subproblems)\n    )\n    if dependency_cycles:\n        warnings.append(\"检测到跨问依赖环: \" + \"; \".join(dependency_cycles))\n\n    stale_fragments: list[str] = []\n    if write and changed_sources:\n        paper_framework = state.setdefault(\"paper_framework\", {})\n        stale_fragments = _mark_paper_fragments_stale(paper_framework, affected)\n        # sync_status means the framework/state record is synchronized, not that every fragment is current.\n        paper_framework[\"sync_status\"] = \"current\"\n",
)
replace_once(
    "scripts/validate_semantic_governance.py",
    "        \"affected_questions\": sorted(affected),\n        \"stale_paper_fragments\": stale_fragments,\n        \"issues\": sorted(set(issues)),\n",
    "        \"affected_questions\": sorted(affected),\n        \"stale_paper_fragments\": stale_fragments,\n        \"state_transitions\": transition_reports,\n        \"dependency_cycles\": dependency_cycles,\n        \"issues\": sorted(set(issues)),\n",
)

# Sync: route every detected artifact/code freshness event through the shared engine.
replace_once(
    "scripts/sync_project.py",
    "import argparse\nimport hashlib\n",
    "import argparse\nfrom copy import deepcopy\nimport hashlib\n",
)
replace_once(
    "scripts/sync_project.py",
    "ANALYZED_STATUSES = {\"analyzed\", \"validated\", \"written\", \"completed\"}\nPRIMARY_STALE_LAYERS = {\n    \"model\", \"solution_workbook\", \"result_analysis_workbook\",\n    \"matlab_script\", \"figure_bundle\", \"framework\",\n}\nANALYSIS_STALE_LAYERS = {\n    \"result_analysis_workbook\", \"matlab_script\", \"figure_bundle\", \"framework\",\n}\nVALID_PREPROCESSING_DECISIONS",
    "ANALYZED_STATUSES = {\"analyzed\", \"validated\", \"written\", \"completed\"}\nVALID_PREPROCESSING_DECISIONS",
)
replace_once(
    "scripts/sync_project.py",
    "LATEX_DELIVERY = _load_module(\n    \"hsk_latex_delivery\", SKILL_ROOT / \"scripts\" / \"latex_delivery.py\"\n)\n\n\ndef load_yaml",
    "LATEX_DELIVERY = _load_module(\n    \"hsk_latex_delivery\", SKILL_ROOT / \"scripts\" / \"latex_delivery.py\"\n)\nSTATE_TRANSITIONS = _load_module(\n    \"hsk_state_transitions\", SKILL_ROOT / \"scripts\" / \"state_transitions.py\"\n)\nSTATE_TRANSITION_CONTRACT = yaml.safe_load(\n    (SKILL_ROOT / \"core\" / \"state_transition_contract.yaml\").read_text(encoding=\"utf-8\")\n) or {}\n\n\ndef load_yaml",
)
replace_once(
    "scripts/sync_project.py",
    "def _code_hash_mismatches(entry: Mapping[str, Any], snapshot: Mapping[str, Any]) -> tuple[bool, bool]:\n    expected_primary = entry.get(\"primary_code_sha256\")\n    expected_analysis = entry.get(\"analysis_code_sha256\")\n    current_primary = snapshot.get(\"primary_code_sha256\")\n    current_analysis = snapshot.get(\"analysis_code_sha256\")\n    primary_changed = bool(expected_primary and current_primary != expected_primary)\n    analysis_changed = bool(expected_analysis and current_analysis != expected_analysis)\n    return primary_changed, analysis_changed\n\n\ndef _apply_snapshot_to_state(root: Path, state: dict[str, Any], snapshot: Mapping[str, Any]) -> set[str]:\n    entry = state.setdefault(\"subproblems\", {}).setdefault(str(snapshot[\"key\"]), {})\n    current = dict(snapshot.get(\"artifact_hashes\", {}))\n    mismatched = _mismatched_layers(entry, current)\n    primary_changed, analysis_changed = _code_hash_mismatches(entry, snapshot)\n    stale_layers = set(entry.get(\"stale_layers\", []) or []) | mismatched\n\n    if primary_changed:\n        stale_layers |= PRIMARY_STALE_LAYERS\n        entry[\"result_quality_status\"] = \"pending\"\n        entry[\"result_analysis_status\"] = \"pending\"\n        entry[\"analysis_execution_status\"] = \"pending\"\n        entry[\"result_summary_status\"] = \"stale\"\n    elif analysis_changed:\n        stale_layers |= ANALYSIS_STALE_LAYERS\n        entry[\"result_analysis_status\"] = \"pending\"\n        entry[\"analysis_execution_status\"] = \"pending\"\n        entry[\"result_summary_status\"] = \"stale\"\n\n    if mismatched.intersection({\"data\", \"model\", \"solution_workbook\"}):\n        entry[\"result_quality_status\"] = \"pending\"\n        entry[\"result_analysis_status\"] = \"pending\"\n    elif \"result_analysis_workbook\" in mismatched:\n        entry[\"result_analysis_status\"] = \"pending\"\n\n    entry[\"artifact_hashes\"] = current\n",
    "def _code_hash_mismatches(entry: Mapping[str, Any], snapshot: Mapping[str, Any]) -> tuple[bool, bool]:\n    expected_primary = entry.get(\"primary_code_sha256\")\n    expected_analysis = entry.get(\"analysis_code_sha256\")\n    current_primary = snapshot.get(\"primary_code_sha256\")\n    current_analysis = snapshot.get(\"analysis_code_sha256\")\n    primary_changed = bool(expected_primary and current_primary != expected_primary)\n    analysis_changed = bool(expected_analysis and current_analysis != expected_analysis)\n    return primary_changed, analysis_changed\n\n\nLAYER_TRANSITION_EVENTS = {\n    \"data\": \"data_changed\",\n    \"model\": \"primary_code_changed\",\n    \"solution_workbook\": \"solution_workbook_changed\",\n    \"result_analysis_workbook\": \"analysis_workbook_changed\",\n    \"matlab_script\": \"matlab_script_changed\",\n    \"figure_bundle\": \"figure_bundle_changed\",\n    \"framework\": \"paper_fragment_changed\",\n}\n\n\ndef _snapshot_transition_events(entry: Mapping[str, Any], snapshot: Mapping[str, Any]) -> list[str]:\n    current = dict(snapshot.get(\"artifact_hashes\", {}))\n    primary_changed, analysis_changed = _code_hash_mismatches(entry, snapshot)\n    events: list[str] = []\n    if primary_changed:\n        events.append(\"primary_code_changed\")\n    if analysis_changed:\n        events.append(\"analysis_code_changed\")\n    for layer in sorted(_mismatched_layers(entry, current)):\n        event = LAYER_TRANSITION_EVENTS.get(layer)\n        if event and event not in events:\n            events.append(event)\n    return events\n\n\ndef _apply_snapshot_to_state(\n    root: Path, state: dict[str, Any], snapshot: Mapping[str, Any]\n) -> tuple[set[str], list[dict[str, Any]]]:\n    key = str(snapshot[\"key\"])\n    entry = state.setdefault(\"subproblems\", {}).setdefault(key, {})\n    current = dict(snapshot.get(\"artifact_hashes\", {}))\n    transition_reports: list[dict[str, Any]] = []\n    for event in _snapshot_transition_events(entry, snapshot):\n        transition_reports.append(\n            STATE_TRANSITIONS.apply_transition(\n                state,\n                event=event,\n                source_question=key,\n                contract=STATE_TRANSITION_CONTRACT,\n            )\n        )\n    entry = state.setdefault(\"subproblems\", {}).setdefault(key, {})\n    entry[\"artifact_hashes\"] = current\n",
)
replace_once(
    "scripts/sync_project.py",
    "    if stale_layers:\n        entry[\"artifacts_stale\"] = True\n        entry[\"stale_layers\"] = sorted(stale_layers)\n        entry[\"result_summary_status\"] = \"stale\"\n        entry[\"validation_status\"] = \"pending\"\n    evidence = _question_dir(root, str(snapshot[\"chinese_name\"])) / \"figure_evidence.yaml\"\n",
    "    stale_layers = set(entry.get(\"stale_layers\", []) or [])\n    evidence = _question_dir(root, str(snapshot[\"chinese_name\"])) / \"figure_evidence.yaml\"\n",
)
replace_once(
    "scripts/sync_project.py",
    "    return stale_layers\n\n\ndef _replace_or_prepend",
    "    return stale_layers, transition_reports\n\n\ndef _replace_or_prepend",
)
replace_once(
    "scripts/sync_project.py",
    "    stale_questions: list[str] = []\n    stale_fragments: list[str] = []\n    if write and state_path.is_file():\n        for snapshot in snapshots.values():\n            stale = _apply_snapshot_to_state(root, state, snapshot)\n            if stale:\n                stale_questions.append(str(snapshot[\"key\"]))\n",
    "    stale_questions: list[str] = []\n    stale_fragments: list[str] = []\n    transition_reports: list[dict[str, Any]] = []\n    transition_state = state if write else deepcopy(state)\n    if state_path.is_file():\n        for snapshot in snapshots.values():\n            stale, reports = _apply_snapshot_to_state(root, transition_state, snapshot)\n            transition_reports.extend(reports)\n            if stale:\n                stale_questions.append(str(snapshot[\"key\"]))\n        merged_transitions = STATE_TRANSITIONS.merge_transition_reports(transition_reports)\n        stale_questions.extend(merged_transitions[\"affected_questions\"])\n        dependency_cycles = (\n            merged_transitions[\"dependency_cycles\"]\n            or STATE_TRANSITIONS.dependency_cycles(transition_state.get(\"subproblems\", {}) or {})\n        )\n        if dependency_cycles:\n            warnings.append(\"检测到跨问依赖环: \" + \"; \".join(dependency_cycles))\n    else:\n        dependency_cycles = []\n\n    if write and state_path.is_file():\n",
)
replace_once(
    "scripts/sync_project.py",
    "    else:\n        for key, snapshot in snapshots.items():\n            entry = subproblems.get(key) or subproblems.get(snapshot[\"chinese_name\"]) or {}\n            primary_changed, analysis_changed = _code_hash_mismatches(entry, snapshot)\n            if (\n                entry.get(\"artifacts_stale\")\n                or _mismatched_layers(entry, snapshot.get(\"artifact_hashes\", {}))\n                or primary_changed\n                or analysis_changed\n            ):\n                stale_questions.append(key)\n        framework = state.get(\"paper_framework\") or {}\n",
    "    else:\n        for key, entry in (transition_state.get(\"subproblems\", {}) or {}).items():\n            if isinstance(entry, Mapping) and entry.get(\"artifacts_stale\"):\n                stale_questions.append(str(key))\n        framework = state.get(\"paper_framework\") or {}\n",
)
replace_once(
    "scripts/sync_project.py",
    "        \"stale_questions\": sorted(set(stale_questions)),\n        \"stale_paper_fragments\": stale_fragments,\n        \"issues\": sorted(set(issues)),\n",
    "        \"stale_questions\": sorted(set(stale_questions)),\n        \"stale_paper_fragments\": stale_fragments,\n        \"state_transitions\": transition_reports,\n        \"dependency_cycles\": dependency_cycles,\n        \"issues\": sorted(set(issues)),\n",
)

# Code delivery: replace private stale sets with shared local/full transitions.
replace_once(
    "scripts/validate_code_delivery.py",
    "import hashlib\nfrom pathlib import Path\n",
    "import hashlib\nimport sys\nfrom pathlib import Path\n",
)
replace_once(
    "scripts/validate_code_delivery.py",
    "import yaml\n\nSKILL_ROOT = Path(__file__).resolve().parents[1]\n",
    "import yaml\n\nSKILL_ROOT = Path(__file__).resolve().parents[1]\nSCRIPT_DIR = str(Path(__file__).resolve().parent)\nif SCRIPT_DIR not in sys.path:\n    sys.path.insert(0, SCRIPT_DIR)\nimport state_transitions as STATE_TRANSITIONS  # noqa: E402\nSTATE_TRANSITION_CONTRACT = yaml.safe_load(\n    (SKILL_ROOT / \"core\" / \"state_transition_contract.yaml\").read_text(encoding=\"utf-8\")\n) or {}\n",
)
replace_once(
    "scripts/validate_code_delivery.py",
    "ANALYSIS_STALE_LAYERS = {\n    \"result_analysis_workbook\", \"matlab_script\", \"figure_bundle\", \"framework\",\n}\nPRIMARY_STALE_LAYERS = {\n    \"solution_workbook\", \"result_analysis_workbook\", \"matlab_script\", \"figure_bundle\", \"framework\",\n}\nALL_RESULT_STALE_LAYERS = {\n    \"data\", \"solution_workbook\", \"result_analysis_workbook\", \"matlab_script\", \"figure_bundle\", \"framework\",\n}\n",
    "",
)
replace_once(
    "scripts/validate_code_delivery.py",
    "def update_state(project_root: Path, config: dict[str, Any], script: Path) -> None:\n",
    "def update_state(project_root: Path, config: dict[str, Any], script: Path) -> list[dict[str, Any]]:\n",
)
replace_once(
    "scripts/validate_code_delivery.py",
    "    relative = script.relative_to(project_root).as_posix()\n\n    if stage == \"preprocessing\":\n",
    "    relative = script.relative_to(project_root).as_posix()\n    transition_reports: list[dict[str, Any]] = []\n\n    if stage == \"preprocessing\":\n",
)
replace_once(
    "scripts/validate_code_delivery.py",
    "            for entry in (state.get(\"subproblems\") or {}).values():\n                if not isinstance(entry, dict):\n                    continue\n                entry[\"result_quality_status\"] = \"pending\"\n                entry[\"result_analysis_status\"] = \"pending\"\n                entry[\"result_summary_status\"] = \"stale\"\n                entry[\"artifacts_stale\"] = True\n                entry[\"stale_layers\"] = sorted(set(entry.get(\"stale_layers\", [])) | ALL_RESULT_STALE_LAYERS)\n        state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding=\"utf-8\")\n        return\n",
    "            for key, entry in (state.get(\"subproblems\") or {}).items():\n                if not isinstance(entry, dict):\n                    continue\n                local = STATE_TRANSITIONS.apply_local_event(\n                    entry, \"data_changed\", STATE_TRANSITION_CONTRACT\n                )\n                transition_reports.append({\n                    \"event\": \"data_changed\",\n                    \"source\": \"project.preprocessing\",\n                    \"affected_questions\": [str(key)],\n                    \"dependency_cycles\": [],\n                    \"transitions\": [{\n                        \"question\": str(key),\n                        \"scope\": \"own\",\n                        \"source\": \"project.preprocessing\",\n                        \"dependency_kind\": \"data\",\n                        \"profile\": local[\"profile\"],\n                        \"stale_layers\": local[\"stale_layers\"],\n                        \"status_updates\": local[\"status_updates\"],\n                        \"emitted_impacts\": local[\"emitted_impacts\"],\n                        \"reason\": \"project-level preprocessing code changed\",\n                    }],\n                })\n        state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding=\"utf-8\")\n        return transition_reports\n",
)
replace_once(
    "scripts/validate_code_delivery.py",
    "        if old_hash and old_hash != new_hash:\n            entry[\"status\"] = \"designed\"\n            entry[\"result_quality_status\"] = \"pending\"\n            entry[\"result_analysis_status\"] = \"pending\"\n            entry[\"analysis_execution_status\"] = \"pending\"\n            entry[\"result_summary_status\"] = \"stale\"\n            entry[\"artifacts_stale\"] = True\n            entry[\"stale_layers\"] = sorted(set(entry.get(\"stale_layers\", [])) | PRIMARY_STALE_LAYERS)\n",
    "        if old_hash and old_hash != new_hash:\n            transition_reports.append(\n                STATE_TRANSITIONS.apply_transition(\n                    state,\n                    event=\"primary_code_changed\",\n                    source_question=key,\n                    contract=STATE_TRANSITION_CONTRACT,\n                )\n            )\n            entry[\"status\"] = \"designed\"\n            entry[\"primary_execution_status\"] = \"awaiting_user_execution\"\n",
)
replace_once(
    "scripts/validate_code_delivery.py",
    "        entry[\"result_analysis_code\"] = relative\n        entry[\"analysis_code_sha256\"] = new_hash\n        entry[\"analysis_execution_status\"] = \"awaiting_user_execution\"\n        if old_hash != new_hash:\n            entry[\"status\"] = \"solved\"\n            entry[\"result_analysis_status\"] = \"pending\"\n            entry[\"result_summary_status\"] = \"stale\"\n            entry[\"artifacts_stale\"] = True\n            entry[\"stale_layers\"] = sorted(set(entry.get(\"stale_layers\", [])) | ANALYSIS_STALE_LAYERS)\n            state.setdefault(\"project\", {})[\"current_phase\"] = \"result_analysis\"\n\n    state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding=\"utf-8\")\n",
    "        entry[\"result_analysis_code\"] = relative\n        entry[\"analysis_code_sha256\"] = new_hash\n        if old_hash != new_hash:\n            transition_reports.append(\n                STATE_TRANSITIONS.apply_transition(\n                    state,\n                    event=\"analysis_code_changed\",\n                    source_question=key,\n                    contract=STATE_TRANSITION_CONTRACT,\n                )\n            )\n            entry[\"status\"] = \"solved\"\n            state.setdefault(\"project\", {})[\"current_phase\"] = \"result_analysis\"\n        entry[\"analysis_execution_status\"] = \"awaiting_user_execution\"\n\n    state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding=\"utf-8\")\n    return transition_reports\n",
)
replace_once(
    "scripts/validate_code_delivery.py",
    "    checked: list[str] = []\n    for script in scripts:\n",
    "    checked: list[str] = []\n    transition_reports: list[dict[str, Any]] = []\n    for script in scripts:\n",
)
replace_once(
    "scripts/validate_code_delivery.py",
    "                update_state(root, config, script)\n",
    "                transition_reports.extend(update_state(root, config, script))\n",
)
replace_once(
    "scripts/validate_code_delivery.py",
    "        \"code_quality_metrics\": metrics,\n        \"task_code_executed\": False,\n",
    "        \"code_quality_metrics\": metrics,\n        \"state_transitions\": transition_reports,\n        \"task_code_executed\": False,\n",
)

# Convert Phase A characterization into Phase D regression assertions.
replace_once(
    "tests/test_v900_refactor_characterization.py",
    "CODE_DELIVERY = load_module(\n    \"v900_code_delivery_characterization\", \"scripts/validate_code_delivery.py\"\n)\n",
    "CODE_DELIVERY = load_module(\n    \"v900_code_delivery_characterization\", \"scripts/validate_code_delivery.py\"\n)\nSTATE_TRANSITIONS = load_module(\n    \"v900_state_transitions_characterization\", \"scripts/state_transitions.py\"\n)\nSTATE_TRANSITION_CONTRACT = yaml.safe_load(\n    (ROOT / \"core/state_transition_contract.yaml\").read_text(encoding=\"utf-8\")\n)\n",
)
replace_once(
    "tests/test_v900_refactor_characterization.py",
    "    def test_dependency_kind_currently_does_not_change_question_closure(self):\n        for kind in (\"data\", \"parameter\", \"model\", \"result\"):\n            entry = {\"depends_on\": [{\"question\": \"Q1\", \"kind\": kind}]}\n            self.assertEqual(SEMANTIC._dependency_questions(entry), {\"Q1\"})\n\n        graph = {\n            \"Q1\": {},\n            \"Q2\": {\"depends_on\": [{\"question\": \"Q1\", \"kind\": \"result\"}]},\n            \"Q3\": {\"depends_on\": [{\"question\": \"Q1\", \"kind\": \"model\"}]},\n            \"Q4\": {\"depends_on\": [{\"question\": \"Q2\", \"kind\": \"data\"}]},\n        }\n        self.assertEqual(\n            SEMANTIC._dependent_closure(graph, {\"Q1\"}),\n            {\"Q1\", \"Q2\", \"Q3\", \"Q4\"},\n        )\n\n    def test_primary_stale_rules_are_currently_duplicated_and_not_identical(self):\n        self.assertEqual(SEMANTIC.PRIMARY_STALE_LAYERS, SYNC.PRIMARY_STALE_LAYERS)\n        self.assertNotEqual(SYNC.PRIMARY_STALE_LAYERS, CODE_DELIVERY.PRIMARY_STALE_LAYERS)\n        self.assertIn(\"model\", SEMANTIC.PRIMARY_STALE_LAYERS)\n        self.assertIn(\"model\", SYNC.PRIMARY_STALE_LAYERS)\n        self.assertNotIn(\"model\", CODE_DELIVERY.PRIMARY_STALE_LAYERS)\n",
    "    def test_dependency_kind_now_controls_transition_propagation(self):\n        state = {\n            \"subproblems\": {\n                \"Q1\": semantic_subproblem(),\n                \"Q2\": {**semantic_subproblem(), \"depends_on\": [{\"question\": \"Q1\", \"kind\": \"result\"}]},\n                \"Q3\": {**semantic_subproblem(), \"depends_on\": [{\"question\": \"Q1\", \"kind\": \"model\"}]},\n                \"Q4\": {**semantic_subproblem(), \"depends_on\": [{\"question\": \"Q2\", \"kind\": \"data\"}]},\n            }\n        }\n        report = STATE_TRANSITIONS.apply_transition(\n            state,\n            event=\"semantic_identity_changed\",\n            source_question=\"Q1\",\n            contract=STATE_TRANSITION_CONTRACT,\n            context={\"semantic_change_categories\": [\"objective\"]},\n        )\n        self.assertEqual(report[\"affected_questions\"], [\"Q1\", \"Q2\", \"Q3\"])\n        self.assertNotIn(\"Q4\", report[\"affected_questions\"])\n        self.assertEqual(state[\"subproblems\"][\"Q2\"][\"human_model_approval_status\"], \"approved\")\n        self.assertEqual(state[\"subproblems\"][\"Q3\"][\"human_model_approval_status\"], \"stale\")\n\n    def test_stale_rules_now_have_one_shared_engine(self):\n        for module in (SEMANTIC, SYNC, CODE_DELIVERY):\n            self.assertFalse(hasattr(module, \"PRIMARY_STALE_LAYERS\"))\n            self.assertFalse(hasattr(module, \"ANALYSIS_STALE_LAYERS\"))\n        for relative in (\n            \"scripts/validate_semantic_governance.py\",\n            \"scripts/sync_project.py\",\n            \"scripts/validate_code_delivery.py\",\n        ):\n            text = (ROOT / relative).read_text(encoding=\"utf-8\")\n            self.assertIn(\"STATE_TRANSITIONS\", text)\n        contract = (ROOT / \"core/state_transition_contract.yaml\").read_text(encoding=\"utf-8\")\n        self.assertIn(\"semantic_identity_changed\", contract)\n        self.assertIn(\"legacy_untyped\", contract)\n",
)

# Authority regression: pointer, manifest alias, declarative gate closure and no private sets.
replace_once(
    "tests/test_authority_single_source.py",
    "    def test_full_workflow_resumes_analysis_then_submission_from_router_segments(self):\n",
    "    def test_state_transition_authority_is_single_and_declarative(self):\n        bootstrap = yaml.safe_load((ROOT / \"core/bootstrap.yaml\").read_text(encoding=\"utf-8\"))\n        self.assertEqual(\n            bootstrap[\"authoritative_sources\"][\"state_transitions\"],\n            \"core/state_transition_contract.yaml\",\n        )\n        self.assertEqual(\n            self.manifest[\"contracts\"][\"state_transition\"],\n            \"core/state_transition_contract.yaml\",\n        )\n        governance = (ROOT / \"SKILL_CHANGE_GOVERNANCE.md\").read_text(encoding=\"utf-8\")\n        self.assertIn(\"| 项目状态转换、stale 传播与依赖失效 | `core/state_transition_contract.yaml` |\", governance)\n        assurance = yaml.safe_load((ROOT / \"core/runtime_assurance_contract.yaml\").read_text(encoding=\"utf-8\"))\n        dependencies = assurance[\"contract_dependency_closure\"][\"contract_dependencies\"]\n        for gate in (\"gate:semantic_governance\", \"gate:code_delivery\", \"gate:project_sync\"):\n            self.assertIn(\"state_transition\", dependencies[gate], gate)\n        for relative in (\n            \"scripts/validate_semantic_governance.py\",\n            \"scripts/sync_project.py\",\n            \"scripts/validate_code_delivery.py\",\n        ):\n            text = (ROOT / relative).read_text(encoding=\"utf-8\")\n            self.assertNotIn(\"PRIMARY_STALE_LAYERS =\", text)\n            self.assertNotIn(\"ANALYSIS_STALE_LAYERS =\", text)\n\n    def test_full_workflow_resumes_analysis_then_submission_from_router_segments(self):\n",
)

# Changelog records this staged phase without changing release carriers.
replace_once(
    "CHANGELOG.md",
    "- Added Phase C regression/migration coverage, updated the protected Model Approval Authority baseline only for the approved contract change, and retained the v8.7.4 release carriers. State-transition unification, typed dependency propagation, artifact-identity renaming, transactional writes, competition-runtime de-hardcoding and other later v9 phases remain out of scope.\n\n## Previous release: 8.7.3\n",
    "- Added Phase C regression/migration coverage, updated the protected Model Approval Authority baseline only for the approved contract change, and retained the v8.7.4 release carriers. State-transition unification, typed dependency propagation, artifact-identity renaming, transactional writes, competition-runtime de-hardcoding and other later v9 phases remain out of scope.\n\n### Unreleased v9.0.0 staged refactor — Phase D\n\n- Added `core/state_transition_contract.yaml` as the single Authority for stale-layer transitions, lifecycle status invalidation, typed cross-question propagation, legacy-untyped fallback and deterministic cycle reporting.\n- Added the pure `scripts/state_transitions.py` engine and routed semantic governance, project sync and code-delivery state invalidation through it; the three entrypoints no longer maintain private primary/analysis stale-layer sets.\n- `depends_on.kind` now changes propagation behavior: model dependencies invalidate downstream semantic approval, while result/parameter/data dependencies invalidate only the execution/evidence layers appropriate to their declared type; legacy untyped dependencies remain conservative.\n- Added deterministic transition evidence, cycle/idempotence regression coverage and Authority-closure tests. Phase E artifact naming and Phase F transactional writes remain intentionally out of scope, and the release carriers remain 8.7.4 until the staged v9.0.0 program completes.\n\n## Previous release: 8.7.3\n",
)

# Update only the two legally changed protected Authority baselines.
protected = "tests/test_v830_editable_mechanism_diagram.py"
text = read(protected)
for relative, old_sha in (
    ("scripts/validate_semantic_governance.py", "64d7a07c0d0eabf254c7b6f0a22d05c581559431"),
    ("scripts/validate_code_delivery.py", "d7b2593a72d6ab4f9a297e46f77f1922c405c128"),
):
    new_sha = git_blob_sha(relative)
    old = f'        "{relative}": "{old_sha}",'
    new = f'        "{relative}": "{new_sha}",'
    if text.count(old) != 1:
        raise RuntimeError(f"protected baseline did not match exactly for {relative}")
    text = text.replace(old, new, 1)
write(protected, text)

print("Phase D deterministic patch applied successfully")
