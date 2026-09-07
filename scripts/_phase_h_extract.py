#!/usr/bin/env python3
from __future__ import annotations

import ast
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SYNC_PATH = ROOT / "scripts" / "sync_project.py"
ARTIFACT_PATH = ROOT / "scripts" / "artifact_fingerprint.py"
SNAPSHOT_PATH = ROOT / "scripts" / "project_snapshot.py"
GOLDEN_PATH = ROOT / "tests" / "fixtures" / "v900_phase_h_empty_sync_golden.yaml"
TEST_PATH = ROOT / "tests" / "test_v900_phase_h_sync_split.py"

ARTIFACT_FUNCTIONS = [
    "sha256_file",
    "sha256_text",
    "combined_hash",
    "framework_section_text",
    "framework_section_hash",
]
SNAPSHOT_FUNCTIONS = [
    "question_key",
    "chinese_question_name",
    "question_number",
    "preprocessing_decision",
    "data_source_files",
    "active_data_hash",
    "_classification",
    "_question_dir",
    "_question_names",
    "_stage_code_paths",
    "_python_files",
    "_analysis_path",
    "_figure_files",
    "_validate_workbook",
    "_has_sheets",
    "_matlab_executable_text",
    "_parse_matlab",
    "_snapshot_question",
]
SNAPSHOT_CONSTANTS = [
    "QUESTION_RE",
    "MATLAB_TITLE_RE",
    "EXPORT_RE",
    "WORKBOOK_REF_RE",
    "FIGURE_SUFFIXES",
    "DATA_SUFFIXES",
    "SOLVED_STATUSES",
    "ANALYZED_STATUSES",
    "VALID_PREPROCESSING_DECISIONS",
]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _capture_baseline() -> None:
    sync = _load_module("phase_h_baseline_sync", SYNC_PATH)
    with tempfile.TemporaryDirectory() as tmp:
        report = sync.synchronize(Path(tmp), write=False, strict=False)
    report = dict(report)
    report.pop("generated_at", None)
    GOLDEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN_PATH.write_text(
        yaml.safe_dump(report, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _function_nodes(tree: ast.Module) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    result = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result[node.name] = node
    return result


def _assignment_nodes(tree: ast.Module) -> dict[str, ast.AST]:
    result: dict[str, ast.AST] = {}
    for node in tree.body:
        names: list[str] = []
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.append(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.append(node.target.id)
        for name in names:
            result[name] = node
    return result


def _slice(lines: list[str], node: ast.AST) -> str:
    if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
        raise RuntimeError("AST node lacks line range")
    return "".join(lines[node.lineno - 1 : node.end_lineno]).rstrip() + "\n"


def _remove_nodes(text: str, nodes: list[ast.AST]) -> str:
    lines = text.splitlines(keepends=True)
    ranges = sorted(
        ((node.lineno - 1, node.end_lineno) for node in nodes),
        reverse=True,
    )
    for start, end in ranges:
        del lines[start:end]
        while start < len(lines) - 1 and lines[start] == "\n" and lines[start + 1] == "\n":
            del lines[start]
    return "".join(lines)


def _extract() -> None:
    if ARTIFACT_PATH.exists() or SNAPSHOT_PATH.exists():
        raise SystemExit("Phase H target modules already exist")

    text = SYNC_PATH.read_text(encoding="utf-8")
    tree = ast.parse(text)
    functions = _function_nodes(tree)
    assignments = _assignment_nodes(tree)
    missing_functions = [name for name in ARTIFACT_FUNCTIONS + SNAPSHOT_FUNCTIONS if name not in functions]
    missing_constants = [name for name in SNAPSHOT_CONSTANTS if name not in assignments]
    if missing_functions or missing_constants:
        raise SystemExit(f"mechanical extraction anchors missing: functions={missing_functions}, constants={missing_constants}")
    lines = text.splitlines(keepends=True)

    artifact_source = (
        '#!/usr/bin/env python3\n'
        '"""Deterministic artifact fingerprint helpers extracted mechanically from sync_project."""\n'
        'from __future__ import annotations\n\n'
        'import hashlib\n'
        'from pathlib import Path\n'
        'from typing import Iterable\n\n'
        + "\n".join(_slice(lines, functions[name]) for name in ARTIFACT_FUNCTIONS)
    ).rstrip() + "\n"
    ARTIFACT_PATH.write_text(artifact_source, encoding="utf-8")

    constant_source = "\n".join(_slice(lines, assignments[name]) for name in SNAPSHOT_CONSTANTS)
    snapshot_source = (
        '#!/usr/bin/env python3\n'
        '"""Project artifact discovery and per-question snapshots extracted mechanically from sync_project."""\n'
        'from __future__ import annotations\n\n'
        'import importlib.util\n'
        'import re\n'
        'import sys\n'
        'from pathlib import Path\n'
        'from typing import Any, Iterable, Mapping\n\n'
        'import artifact_fingerprint as ARTIFACT_FINGERPRINT\n\n'
        'SKILL_ROOT = Path(__file__).resolve().parent.parent\n\n'
        'def _load_module(name: str, path: Path):\n'
        '    spec = importlib.util.spec_from_file_location(name, path)\n'
        '    module = importlib.util.module_from_spec(spec)\n'
        '    assert spec.loader is not None\n'
        '    sys.modules[name] = module\n'
        '    spec.loader.exec_module(module)\n'
        '    return module\n\n'
        'WORKBOOK_VALIDATION = _load_module(\n'
        '    "hsk_project_snapshot_workbook_validation",\n'
        '    SKILL_ROOT / "templates/code" / "hsk_pipeline" / "workbook_validation.py",\n'
        ')\n\n'
        'sha256_file = ARTIFACT_FINGERPRINT.sha256_file\n'
        'combined_hash = ARTIFACT_FINGERPRINT.combined_hash\n'
        'framework_section_hash = ARTIFACT_FINGERPRINT.framework_section_hash\n\n'
        + constant_source + "\n\n"
        + "\n".join(_slice(lines, functions[name]) for name in SNAPSHOT_FUNCTIONS)
    ).rstrip() + "\n"
    SNAPSHOT_PATH.write_text(snapshot_source, encoding="utf-8")

    nodes_to_remove = [functions[name] for name in ARTIFACT_FUNCTIONS + SNAPSHOT_FUNCTIONS]
    nodes_to_remove += [assignments[name] for name in SNAPSHOT_CONSTANTS]
    new_text = _remove_nodes(text, nodes_to_remove)

    import_anchor = "import project_transaction as PROJECT_TX  # noqa: E402\n"
    if new_text.count(import_anchor) != 1:
        raise SystemExit(f"sync import anchor mismatch: {new_text.count(import_anchor)}")
    new_text = new_text.replace(
        import_anchor,
        import_anchor
        + "import artifact_fingerprint as ARTIFACT_FINGERPRINT  # noqa: E402\n"
        + "import project_snapshot as PROJECT_SNAPSHOT  # noqa: E402\n",
        1,
    )

    contract_anchor = "STATE_TRANSITION_CONTRACT = yaml.safe_load(\n    (SKILL_ROOT / \"core\" / \"state_transition_contract.yaml\").read_text(encoding=\"utf-8\")\n) or {}\n"
    if new_text.count(contract_anchor) != 1:
        raise SystemExit(f"sync contract anchor mismatch: {new_text.count(contract_anchor)}")
    alias_lines = [
        "",
        "# Phase H compatibility aliases: existing callers/tests keep the sync_project surface.",
        "sha256_file = ARTIFACT_FINGERPRINT.sha256_file",
        "sha256_text = ARTIFACT_FINGERPRINT.sha256_text",
        "combined_hash = ARTIFACT_FINGERPRINT.combined_hash",
        "framework_section_text = ARTIFACT_FINGERPRINT.framework_section_text",
        "framework_section_hash = ARTIFACT_FINGERPRINT.framework_section_hash",
    ]
    alias_lines.extend(f"{name} = PROJECT_SNAPSHOT.{name}" for name in SNAPSHOT_CONSTANTS)
    alias_lines.extend(f"{name} = PROJECT_SNAPSHOT.{name}" for name in SNAPSHOT_FUNCTIONS)
    alias_block = "\n".join(alias_lines) + "\n"
    new_text = new_text.replace(contract_anchor, contract_anchor + alias_block, 1)
    SYNC_PATH.write_text(new_text, encoding="utf-8")


def _write_tests() -> None:
    moved = ARTIFACT_FUNCTIONS + SNAPSHOT_FUNCTIONS
    test_source = f'''from __future__ import annotations

import ast
import importlib.util
import inspect
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def load_module(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {{relative}}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SYNC = load_module("phase_h_sync", "scripts/sync_project.py")
FINGERPRINT = load_module("phase_h_fingerprint", "scripts/artifact_fingerprint.py")
SNAPSHOT = load_module("phase_h_snapshot", "scripts/project_snapshot.py")
MOVED = {moved!r}


class PhaseHMechanicalSplitTests(unittest.TestCase):
    def test_sync_project_no_longer_defines_extracted_functions(self):
        tree = ast.parse((ROOT / "scripts/sync_project.py").read_text(encoding="utf-8"))
        defined = {{node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}}
        self.assertTrue(set(MOVED).isdisjoint(defined))

    def test_compatibility_aliases_preserve_existing_surface(self):
        for name in {ARTIFACT_FUNCTIONS!r}:
            self.assertIs(getattr(SYNC, name), getattr(FINGERPRINT, name))
        for name in {SNAPSHOT_FUNCTIONS!r}:
            self.assertIs(getattr(SYNC, name), getattr(SNAPSHOT, name))

    def test_synchronize_signature_is_unchanged(self):
        parameters = list(inspect.signature(SYNC.synchronize).parameters)
        self.assertEqual(
            parameters,
            ["project_root", "write", "strict", "delivery_scope", "schema_path", "output_contract_path"],
        )

    def test_empty_project_sync_report_matches_pre_split_golden(self):
        expected = yaml.safe_load((ROOT / "tests/fixtures/v900_phase_h_empty_sync_golden.yaml").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            actual = SYNC.synchronize(Path(tmp), write=False, strict=False)
        actual = dict(actual)
        actual.pop("generated_at", None)
        self.assertEqual(actual, expected)

    def test_fingerprint_helpers_remain_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "a.txt"
            second = root / "b.txt"
            first.write_text("alpha\\n", encoding="utf-8")
            second.write_text("beta\\n", encoding="utf-8")
            self.assertEqual(FINGERPRINT.sha256_file(first), SYNC.sha256_file(first))
            self.assertEqual(
                FINGERPRINT.combined_hash([second, first], root),
                FINGERPRINT.combined_hash([first, second], root),
            )


if __name__ == "__main__":
    unittest.main()
'''
    TEST_PATH.write_text(test_source, encoding="utf-8")


def main() -> None:
    _capture_baseline()
    _extract()
    _write_tests()
    print(json.dumps({
        "artifact_functions": ARTIFACT_FUNCTIONS,
        "snapshot_functions": SNAPSHOT_FUNCTIONS,
        "golden": str(GOLDEN_PATH.relative_to(ROOT)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
