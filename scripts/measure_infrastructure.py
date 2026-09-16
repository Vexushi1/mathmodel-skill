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
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "1.1.0"
PYTHON_ROOT = ROOT / "scripts"
REFRESH_WORKFLOW = ROOT / ".github" / "workflows" / "refresh-generated.yml"
WORKFLOW_ROOT = ROOT / ".github" / "workflows"
LINT_HOTSPOT = "scripts/lint_skill_checks.py"


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


def _top_level_function_rows(tree: ast.AST) -> list[dict[str, Any]]:
    """Return source-order spans for top-level functions only.

    This is structural evidence, not a semantic duty classifier. Nested functions are
    deliberately excluded so a future split can distinguish module surface from local
    implementation detail.
    """
    rows: list[dict[str, Any]] = []
    body = getattr(tree, "body", [])
    for node in body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        end_line = int(getattr(node, "end_lineno", node.lineno))
        rows.append(
            {
                "name": node.name,
                "start_line": int(node.lineno),
                "end_line": end_line,
                "span_lines": end_line - int(node.lineno) + 1,
                "async": isinstance(node, ast.AsyncFunctionDef),
                "decorator_count": len(node.decorator_list),
            }
        )
    return rows


def _name_prefix_family(name: str) -> str:
    normalized = name.lstrip("_")
    for prefix in (
        "check",
        "validate",
        "load",
        "parse",
        "build",
        "collect",
        "resolve",
        "render",
        "extract",
        "find",
        "scan",
        "is",
        "has",
    ):
        if normalized == prefix or normalized.startswith(prefix + "_"):
            return prefix
    if normalized == "main":
        return "entrypoint"
    return "other"


def _span_bucket(span_lines: int) -> str:
    if span_lines <= 20:
        return "1-20"
    if span_lines <= 50:
        return "21-50"
    if span_lines <= 100:
        return "51-100"
    if span_lines <= 200:
        return "101-200"
    return "201+"


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
        top_level_functions = _top_level_function_rows(tree)
        row = {
            "path": _relative(path, root),
            "bytes": path.stat().st_size,
            "nonblank_lines": _nonblank_lines(text),
            "function_count": len(functions),
            "top_level_function_count": len(top_level_functions),
            "nested_function_count": len(functions) - len(top_level_functions),
            "max_top_level_function_span_lines": max(
                (int(item["span_lines"]) for item in top_level_functions),
                default=0,
            ),
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


def _lint_hotspot_structure(root: Path, *, top_functions: int) -> dict[str, Any]:
    path = root / LINT_HOTSPOT
    if not path.is_file():
        return {"path": LINT_HOTSPOT, "present": False}

    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    all_functions = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    functions = _top_level_function_rows(tree)
    spans = [int(item["span_lines"]) for item in functions]
    family_counts = Counter(_name_prefix_family(str(item["name"])) for item in functions)
    bucket_counts = Counter(_span_bucket(int(item["span_lines"])) for item in functions)
    largest = sorted(
        functions,
        key=lambda item: (-int(item["span_lines"]), int(item["start_line"]), str(item["name"])),
    )[:top_functions]
    return {
        "path": LINT_HOTSPOT,
        "present": True,
        "bytes": path.stat().st_size,
        "nonblank_lines": _nonblank_lines(text),
        "top_level_function_count": len(functions),
        "nested_function_count": len(all_functions) - len(functions),
        "top_level_span_lines_total": sum(spans),
        "top_level_span_lines_median": float(median(spans)) if spans else 0.0,
        "top_level_span_lines_max": max(spans, default=0),
        "name_prefix_families": dict(sorted(family_counts.items())),
        "span_buckets": {
            key: int(bucket_counts.get(key, 0))
            for key in ("1-20", "21-50", "51-100", "101-200", "201+")
        },
        "functions_source_order": functions,
        "largest_functions": largest,
        "interpretation_boundary": (
            "function names and spans are structural evidence only; they do not prove semantic independence"
        ),
    }


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
        "actions_write_permission_occurrences": text.count("actions: write"),
        "git_commit_occurrences": text.count("git commit"),
        "git_push_occurrences": text.count("git push"),
        "bot_actor_guard_present": "github.actor != 'github-actions[bot]'" in text,
        "generator_invocations": text.count("python scripts/generate_indexes.py"),
        "full_ci_dispatch_occurrences": text.count("gh workflow run ci.yml"),
        "optimization_baseline_dispatch_occurrences": text.count(
            "gh workflow run optimization-baseline.yml"
        ),
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
        "lint_skill_checks_structure": _lint_hotspot_structure(root, top_functions=top),
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
            f"{item['nonblank_lines']} nonblank lines"
        )
    lint_structure = metrics["lint_skill_checks_structure"]
    if lint_structure.get("present"):
        lines.extend(
            [
                "lint_skill_checks.py structure:",
                f"- top-level functions: {lint_structure['top_level_function_count']}",
                f"- nested functions: {lint_structure['nested_function_count']}",
                f"- median top-level span: {lint_structure['top_level_span_lines_median']} lines",
                f"- max top-level span: {lint_structure['top_level_span_lines_max']} lines",
                "- largest top-level functions:",
            ]
        )
        for item in lint_structure["largest_functions"]:
            lines.append(
                f"  - {item['name']}: lines {item['start_line']}-{item['end_line']} "
                f"({item['span_lines']} lines)"
            )
    yaml_summary = metrics["repeated_parsing"]["yaml_safe_load"]
    lines.extend(
        [
            f"yaml.safe_load: {yaml_summary['call_count']} calls across {yaml_summary['file_count']} files",
            "Generated metadata workflow:",
            f"- git commit occurrences: {metrics['generated_metadata']['git_commit_occurrences']}",
            f"- git push occurrences: {metrics['generated_metadata']['git_push_occurrences']}",
            f"- full CI dispatch occurrences: {metrics['generated_metadata']['full_ci_dispatch_occurrences']}",
            f"- optimization baseline dispatch occurrences: {metrics['generated_metadata']['optimization_baseline_dispatch_occurrences']}",
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
