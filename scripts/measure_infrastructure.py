#!/usr/bin/env python3
"""Measure repository infrastructure hotspots without changing runtime semantics.

P8 uses this report as evidence before any validator split, parser consolidation, or
generated-metadata workflow change. The script is read-only and intentionally does
not define policy thresholds: it reports observable size/call-site/workflow facts.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "1.1.0"
PYTHON_ROOT = ROOT / "scripts"
REFRESH_WORKFLOW = ROOT / ".github" / "workflows" / "refresh-generated.yml"
WORKFLOW_ROOT = ROOT / ".github" / "workflows"


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _nonblank_lines(text: str) -> int:
    return sum(bool(line.strip()) for line in text.splitlines())


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts = [func.attr]
        value = func.value
        while isinstance(value, ast.Attribute):
            parts.append(value.attr)
            value = value.value
        if isinstance(value, ast.Name):
            parts.append(value.id)
        return ".".join(reversed(parts))
    return ""


def _top_level_function_metrics(tree: ast.Module, *, limit: int = 10) -> dict[str, Any]:
    functions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    spans = []
    for node in functions:
        end_line = int(getattr(node, "end_lineno", node.lineno) or node.lineno)
        spans.append(
            {
                "name": node.name,
                "start_line": int(node.lineno),
                "end_line": end_line,
                "span_lines": end_line - int(node.lineno) + 1,
            }
        )
    spans.sort(key=lambda item: (-int(item["span_lines"]), str(item["name"])))
    return {
        "count": len(functions),
        "check_function_count": sum(str(item["name"]).startswith("check_") for item in spans),
        "largest": spans[:limit],
    }


def _python_metrics(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    yaml_sites: list[dict[str, Any]] = []
    for path in sorted((root / "scripts").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        yaml_calls = [node for node in calls if _call_name(node) == "yaml.safe_load"]
        workbook_calls = [node for node in calls if _call_name(node) == "openpyxl.load_workbook"]
        functions = [
            node for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        top_level_functions = _top_level_function_metrics(tree)
        row = {
            "path": _relative(path, root),
            "bytes": path.stat().st_size,
            "nonblank_lines": _nonblank_lines(text),
            "function_count": len(functions),
            "top_level_function_count": top_level_functions["count"],
            "top_level_check_function_count": top_level_functions["check_function_count"],
            "largest_top_level_functions": top_level_functions["largest"],
            "yaml_safe_load_calls": len(yaml_calls),
            "openpyxl_load_workbook_calls": len(workbook_calls),
            "validator_surface": path.name.startswith("validate_") or path.name.startswith("lint_skill"),
        }
        rows.append(row)
        if yaml_calls:
            yaml_sites.append({"path": row["path"], "calls": len(yaml_calls)})

    rows.sort(key=lambda item: (-int(item["bytes"]), str(item["path"])))
    yaml_sites.sort(key=lambda item: (-int(item["calls"]), str(item["path"])))
    yaml_summary = {
        "call_count": sum(int(item["calls"]) for item in yaml_sites),
        "file_count": len(yaml_sites),
        "files": yaml_sites,
    }
    return rows, yaml_summary


def _generated_metadata_metrics(root: Path) -> dict[str, Any]:
    refresh = root / ".github" / "workflows" / "refresh-generated.yml"
    text = refresh.read_text(encoding="utf-8") if refresh.is_file() else ""
    workflow_files = sorted((root / ".github" / "workflows").glob("*.y*ml"))
    check_occurrences: list[dict[str, Any]] = []
    for path in workflow_files:
        payload = path.read_text(encoding="utf-8")
        count = payload.count("generate_indexes.py --check")
        if count:
            check_occurrences.append({"path": _relative(path, root), "count": count})
    lint_checks = root / "scripts" / "lint_skill_checks.py"
    if lint_checks.is_file():
        payload = lint_checks.read_text(encoding="utf-8")
        count = payload.count("generate_indexes.py")
        if count:
            check_occurrences.append({"path": _relative(lint_checks, root), "count": count})

    return {
        "refresh_workflow_present": refresh.is_file(),
        "feature_branch_write_permission_occurrences": text.count("contents: write"),
        "git_commit_occurrences": text.count("git commit"),
        "git_push_occurrences": text.count("git push"),
        "bot_actor_guard_present": "github.actor != 'github-actions[bot]'" in text,
        "generator_invocations": text.count("python scripts/generate_indexes.py"),
        "generated_check_occurrences": check_occurrences,
    }


def collect_metrics(root: Path = ROOT, *, top: int = 8) -> dict[str, Any]:
    root = root.resolve()
    python_rows, yaml_summary = _python_metrics(root)
    validators = [item for item in python_rows if bool(item["validator_surface"])]
    return {
        "schema_version": SCHEMA_VERSION,
        "scope": "repository_infrastructure_measurement_only",
        "python_scripts": {
            "count": len(python_rows),
            "total_bytes": sum(int(item["bytes"]) for item in python_rows),
            "largest": python_rows[:top],
        },
        "validator_hotspots": validators[:top],
        "repeated_parsing": {
            "yaml_safe_load": yaml_summary,
            "openpyxl_load_workbook_call_count": sum(
                int(item["openpyxl_load_workbook_calls"]) for item in python_rows
            ),
        },
        "generated_metadata": _generated_metadata_metrics(root),
    }


def render_text(metrics: dict[str, Any]) -> str:
    lines = [
        f"Infrastructure metrics schema: {metrics['schema_version']}",
        "Largest scripts:",
    ]
    for item in metrics["python_scripts"]["largest"]:
        lines.append(
            f"- {item['path']}: {item['bytes']} bytes, "
            f"{item['nonblank_lines']} nonblank lines, "
            f"{item['top_level_function_count']} top-level functions"
        )
        largest_functions = item.get("largest_top_level_functions", [])
        if largest_functions:
            top_function = largest_functions[0]
            lines.append(
                f"  largest function: {top_function['name']} "
                f"({top_function['span_lines']} lines)"
            )
    yaml_summary = metrics["repeated_parsing"]["yaml_safe_load"]
    lines.extend(
        [
            f"yaml.safe_load: {yaml_summary['call_count']} calls across {yaml_summary['file_count']} files",
            "Generated metadata workflow:",
            f"- git commit occurrences: {metrics['generated_metadata']['git_commit_occurrences']}",
            f"- git push occurrences: {metrics['generated_metadata']['git_push_occurrences']}",
            f"- bot actor guard: {metrics['generated_metadata']['bot_actor_guard_present']}",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--top", type=int, default=8)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    if args.top <= 0:
        parser.error("--top must be positive")
    metrics = collect_metrics(args.root, top=args.top)
    if args.json:
        print(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_text(metrics), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
