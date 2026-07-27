#!/usr/bin/env python3
"""Synchronize HSK project state with code, workbooks, MATLAB scripts and figures.

The synchronizer is deliberately conservative: it discovers artifacts, computes
hashes and propagates stale state, but never invents model semantics, numerical
results or validation success.
"""
from __future__ import annotations

import argparse
import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml
from openpyxl import load_workbook

QUESTION_RE = re.compile(r"问题([一二三四五六七八九十百]+)")
MATLAB_TITLE_RE = re.compile(r"\b(?:title|sgtitle)\s*\(", re.IGNORECASE)
EXPORT_RE = re.compile(r"(?:exportgraphics|print)\s*\([^\n]*?[\"']([^\"']+\.(?:png|pdf|svg|tif|tiff))[\"']", re.IGNORECASE)
IGNORED_ROOT_NAMES = {
    ".git", ".idea", ".vscode", "__pycache__", "结果数据表",
    "draft_docx", "final_latex", "figures", "figures_editable", "state",
}
INPUT_SUFFIXES = {".csv", ".xlsx", ".xls", ".json", ".yaml", ".yml", ".txt", ".pdf", ".doc", ".docx", ".zip"}


@dataclass
class WorkbookInfo:
    path: str
    sha256: str
    sheets: dict[str, dict[str, Any]] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)


@dataclass
class QuestionSnapshot:
    key: str
    chinese_name: str
    code_files: list[str] = field(default_factory=list)
    model_hash: str | None = None
    solution_workbook: WorkbookInfo | None = None
    robustness_workbook: WorkbookInfo | None = None
    matlab_script: str | None = None
    matlab_has_title: bool = False
    exported_figures: list[str] = field(default_factory=list)
    discovered_figures: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def combined_hash(paths: Iterable[Path], root: Path) -> str | None:
    files = sorted({path.resolve() for path in paths if path.is_file()}, key=lambda p: p.as_posix())
    if not files:
        return None
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def question_key(chinese_name: str) -> str:
    order = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    suffix = chinese_name.removeprefix("问题")
    try:
        return f"Q{order.index(suffix) + 1}"
    except ValueError:
        return chinese_name


def root_input_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.iterdir():
        if path.name.startswith(".") or path.name in IGNORED_ROOT_NAMES or not path.is_file():
            continue
        if path.suffix.lower() in INPUT_SUFFIXES and path.name not in {"模型论文框架.md", "sync_report.yaml"}:
            files.append(path)
    return files


def inspect_workbook(path: Path, root: Path) -> WorkbookInfo:
    info = WorkbookInfo(path=path.relative_to(root).as_posix(), sha256=sha256_file(path))
    try:
        book = load_workbook(path, read_only=True, data_only=True)
    except Exception as exc:
        info.issues.append(f"无法读取工作簿: {exc}")
        return info
    try:
        for sheet in book.worksheets:
            rows = sheet.iter_rows(values_only=True)
            header_row = next(rows, None)
            headers = [str(value).strip() if value is not None else "" for value in (header_row or [])]
            nonempty_headers = [value for value in headers if value]
            data_rows = sum(1 for row in rows if any(value is not None for value in row))
            info.sheets[sheet.title] = {
                "headers": nonempty_headers,
                "data_rows": data_rows,
                "max_column": sheet.max_column,
            }
            if not nonempty_headers:
                info.issues.append(f"工作表“{sheet.title}”缺少表头")
            if data_rows == 0:
                info.issues.append(f"工作表“{sheet.title}”为空")
    finally:
        book.close()
    return info


def discover_questions(root: Path) -> dict[str, QuestionSnapshot]:
    snapshots: dict[str, QuestionSnapshot] = {}
    result_root = root / "结果数据表"
    if result_root.is_dir():
        for directory in sorted(path for path in result_root.iterdir() if path.is_dir()):
            if not QUESTION_RE.fullmatch(directory.name):
                continue
            key = question_key(directory.name)
            snapshots[key] = QuestionSnapshot(key=key, chinese_name=directory.name)

    for script in sorted(root.glob("问题*.py")):
        match = QUESTION_RE.match(script.stem)
        if not match:
            continue
        chinese_name = match.group(0)
        key = question_key(chinese_name)
        snapshots.setdefault(key, QuestionSnapshot(key=key, chinese_name=chinese_name)).code_files.append(
            script.relative_to(root).as_posix()
        )

    for snapshot in snapshots.values():
        snapshot.model_hash = combined_hash([root / path for path in snapshot.code_files], root)
        result_dir = result_root / snapshot.chinese_name
        solve = result_dir / f"{snapshot.chinese_name}求解结果.xlsx"
        robust = result_dir / f"{snapshot.chinese_name}敏感性与鲁棒性结果.xlsx"
        if solve.is_file():
            snapshot.solution_workbook = inspect_workbook(solve, root)
            snapshot.issues.extend(snapshot.solution_workbook.issues)
        if robust.is_file():
            snapshot.robustness_workbook = inspect_workbook(robust, root)
            snapshot.issues.extend(snapshot.robustness_workbook.issues)
        number = re.sub(r"\D", "", snapshot.key)
        matlab = result_dir / f"q{number}_plot.m" if number else None
        if matlab and matlab.is_file():
            snapshot.matlab_script = matlab.relative_to(root).as_posix()
            text = matlab.read_text(encoding="utf-8", errors="replace")
            snapshot.matlab_has_title = bool(MATLAB_TITLE_RE.search(text))
            snapshot.exported_figures = sorted(set(EXPORT_RE.findall(text)))
            if not snapshot.matlab_has_title:
                snapshot.issues.append("MATLAB脚本缺少title或sgtitle")
        figure_dir = result_dir / "图表"
        if figure_dir.is_dir():
            snapshot.discovered_figures = sorted(
                path.relative_to(root).as_posix()
                for path in figure_dir.rglob("*")
                if path.is_file() and path.suffix.lower() in {".png", ".pdf", ".svg", ".tif", ".tiff"}
            )
    return snapshots


def framework_hash(root: Path) -> str | None:
    path = root / "模型论文框架.md"
    return sha256_file(path) if path.is_file() else None


def update_framework_header(path: Path, *, stale: bool, scope: str, timestamp: str) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    replacements = {
        r"(?m)^- 最近同步：.*$": f"- 最近同步：`{scope}`",
        r"(?m)^- 最近同步时间：.*$": f"- 最近同步时间：`{timestamp}`",
        r"(?m)^- 当前状态：.*$": f"- 当前状态：`{'stale' if stale else 'current'}`",
    }
    changed = False
    for pattern, replacement in replacements.items():
        new_text, count = re.subn(pattern, replacement, text)
        if count:
            text = new_text
            changed = True
    if changed:
        path.write_text(text, encoding="utf-8")
    return changed


def snapshot_to_dict(snapshot: QuestionSnapshot) -> dict[str, Any]:
    def workbook_payload(info: WorkbookInfo | None) -> dict[str, Any] | None:
        if info is None:
            return None
        return {"path": info.path, "sha256": info.sha256, "sheets": info.sheets, "issues": info.issues}
    return {
        "question": snapshot.chinese_name,
        "code_files": snapshot.code_files,
        "model_hash": snapshot.model_hash,
        "solution_workbook": workbook_payload(snapshot.solution_workbook),
        "robustness_workbook": workbook_payload(snapshot.robustness_workbook),
        "matlab_script": snapshot.matlab_script,
        "matlab_has_title": snapshot.matlab_has_title,
        "exported_figures": snapshot.exported_figures,
        "discovered_figures": snapshot.discovered_figures,
        "issues": snapshot.issues,
    }


def synchronize(root: Path, *, write: bool, question: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    state_path = root / "state" / "project_state.yaml"
    state = load_yaml(state_path)
    snapshots = discover_questions(root)
    if question:
        normalized = question if question.startswith("Q") else question_key(question)
        snapshots = {key: value for key, value in snapshots.items() if key == normalized}
        if not snapshots:
            raise ValueError(f"未发现小问: {question}")

    data_hash = combined_hash(root_input_files(root), root)
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    issues: list[str] = []
    stale_questions: list[str] = []
    if not state:
        issues.append("缺少state/project_state.yaml；同步器仅生成发现报告，不创建模型语义状态")
    subproblems = state.get("subproblems", {}) if state else {}

    for key, snapshot in snapshots.items():
        issues.extend(f"{key}: {item}" for item in snapshot.issues)
        sub = subproblems.get(key)
        if not isinstance(sub, dict):
            issues.append(f"{key}: 项目状态中缺少对应小问")
            continue
        previous_data = sub.get("validated_data_hash")
        previous_model = sub.get("validated_model_hash")
        data_changed = bool(previous_data and data_hash and previous_data != data_hash)
        model_changed = bool(previous_model and snapshot.model_hash and previous_model != snapshot.model_hash)
        stale = data_changed or model_changed
        if stale:
            stale_questions.append(key)
            sub["artifacts_stale"] = True
            sub["result_summary_status"] = "stale"
            if sub.get("status") in {"validated", "written", "completed"}:
                sub["status"] = "solved"
            if sub.get("validation_status") == "passed":
                sub["validation_status"] = "pending"
        if data_hash:
            sub["data_hash"] = data_hash
        if snapshot.model_hash:
            sub["model_hash"] = snapshot.model_hash
        sub["code"] = snapshot.code_files[0] if snapshot.code_files else sub.get("code", "")
        if snapshot.solution_workbook:
            sub["solution_workbook"] = snapshot.solution_workbook.path
        if snapshot.robustness_workbook:
            sub["robustness_workbook"] = snapshot.robustness_workbook.path
        evidence = set(sub.get("evidence", []))
        for path in [
            *(snapshot.code_files or []),
            snapshot.solution_workbook.path if snapshot.solution_workbook else None,
            snapshot.robustness_workbook.path if snapshot.robustness_workbook else None,
            snapshot.matlab_script,
            *snapshot.discovered_figures,
        ]:
            if path:
                evidence.add(path)
        sub["evidence"] = sorted(evidence)

    if state:
        state.setdefault("execution", {})["last_run"] = timestamp
        state["execution"]["command"] = "python scripts/sync_project.py --write"
        state.setdefault("artifacts", {})
        state["artifacts"]["code"] = sorted({path for item in snapshots.values() for path in item.code_files})
        state["artifacts"]["results"] = sorted({
            path for item in snapshots.values() for path in [
                item.solution_workbook.path if item.solution_workbook else None,
                item.robustness_workbook.path if item.robustness_workbook else None,
            ] if path
        })
        state["artifacts"]["figures"] = sorted({path for item in snapshots.values() for path in item.discovered_figures})
        framework = state.setdefault("paper_framework", {})
        framework["path"] = "模型论文框架.md"
        framework["sync_status"] = "stale" if stale_questions else framework.get("sync_status", "current")
        framework["last_synced_at"] = timestamp
        framework["last_sync_scope"] = question or "all discovered subproblems"
        current_framework_hash = framework_hash(root)
        if current_framework_hash:
            framework["sha256"] = current_framework_hash

    report = {
        "sync_version": "1.0.0",
        "skill_version": "6.3.0",
        "generated_at": timestamp,
        "project_root": root.as_posix(),
        "write_requested": write,
        "data_hash": data_hash,
        "framework_hash": framework_hash(root),
        "stale_questions": stale_questions,
        "questions": {key: snapshot_to_dict(value) for key, value in snapshots.items()},
        "issues": issues,
        "policy": {"promotes_validation": False, "rewrites_model_semantics": False, "stale_propagation": True},
    }
    if write:
        if state:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
        update_framework_header(
            root / "模型论文框架.md",
            stale=bool(stale_questions),
            scope=question or "项目产物自动同步",
            timestamp=timestamp,
        )
        report["framework_hash"] = framework_hash(root)
        (root / "sync_report.yaml").write_text(yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", nargs="?", default=".")
    parser.add_argument("--question", help="Q1或问题一")
    parser.add_argument("--write", action="store_true", help="写回state、框架头部和sync_report.yaml")
    parser.add_argument("--strict", action="store_true", help="存在问题或stale时返回非零状态")
    args = parser.parse_args()
    try:
        report = synchronize(Path(args.project_root), write=args.write, question=args.question)
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
    if not args.write:
        print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False))
    if args.strict and (report["issues"] or report["stale_questions"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
