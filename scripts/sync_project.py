#!/usr/bin/env python3
"""Synchronize project artifacts with state and enforce delivery-scope contracts.

The synchronizer is conservative: it discovers and validates artifacts, computes
hashes and propagates stale state. It never invents model semantics, numerical
results, or validation success.
"""
from __future__ import annotations

import argparse
import hashlib
import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml
from openpyxl import load_workbook

SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCHEMA_PATH = SKILL_ROOT / "core" / "workbook_schema.yaml"
QUESTION_RE = re.compile(r"问题([一二三四五六七八九十百]+)")
MATLAB_TITLE_RE = re.compile(r"\b(?:title|sgtitle)\s*\(", re.IGNORECASE)
EXPORT_RE = re.compile(r"(?:exportgraphics|print)\s*\([^\n]*?[\"']([^\"']+\.(?:png|pdf|svg|tif|tiff))[\"']", re.IGNORECASE)
WORKBOOK_REF_RE = re.compile(r"[\"']([^\"']+\.xlsx)[\"']", re.IGNORECASE)
FIGURE_SUFFIXES = {".png", ".pdf", ".svg", ".tif", ".tiff"}
INPUT_SUFFIXES = {".csv", ".xlsx", ".xls", ".json", ".yaml", ".yml", ".txt", ".pdf", ".doc", ".docx", ".zip"}
IGNORED_ROOT_NAMES = {".git", ".idea", ".vscode", "__pycache__", "结果数据表", "draft_docx", "final_latex", "figures", "figures_editable", "state"}
STATUS_RANK = {"pending": 0, "audited": 1, "designed": 2, "solved": 3, "validated": 4, "written": 5, "completed": 6}
SCOPE_RANK = {"design": 0, "results": 1, "figures": 2, "docx": 3, "latex": 4, "submission": 5}
PHASE_SCOPE = {
    "problem_audit": "design", "model_design": "design", "solve_validate": "results",
    "figure_evidence": "figures", "writing_docx": "docx", "writing_latex": "latex",
    "ai_cleanup": "latex", "latex_compile_quality": "latex", "review_delivery": "submission",
    "completed": "submission",
}
HASH_KEYS = ("data", "model", "solution_workbook", "robustness_workbook", "matlab_script", "figure_bundle")


@dataclass
class SheetInfo:
    headers: list[str] = field(default_factory=list)
    data_rows: int = 0
    max_column: int = 0
    rows: list[tuple[Any, ...]] = field(default_factory=list)


@dataclass
class WorkbookInfo:
    path: str
    sha256: str
    sheets: dict[str, SheetInfo] = field(default_factory=dict)
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
    matlab_hash: str | None = None
    matlab_has_title: bool = False
    workbook_references: list[str] = field(default_factory=list)
    exported_figures: list[str] = field(default_factory=list)
    discovered_figures: list[str] = field(default_factory=list)
    figure_hash: str | None = None
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
    files = sorted({path.resolve() for path in paths if path.is_file()}, key=lambda item: item.as_posix())
    if not files:
        return None
    digest = hashlib.sha256()
    for path in files:
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            relative = path.as_posix()
        digest.update(relative.encode("utf-8"))
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
    return [
        path for path in root.iterdir()
        if path.is_file() and not path.name.startswith(".")
        and path.name not in IGNORED_ROOT_NAMES and path.suffix.lower() in INPUT_SUFFIXES
        and path.name not in {"模型论文框架.md", "sync_report.yaml"}
    ]


def normalize_headers(values: Iterable[Any]) -> list[str]:
    return [str(value).strip() if value is not None else "" for value in values]


def inspect_workbook(path: Path, root: Path) -> WorkbookInfo:
    info = WorkbookInfo(path=path.relative_to(root).as_posix(), sha256=sha256_file(path))
    try:
        book = load_workbook(path, read_only=True, data_only=True)
    except Exception as exc:  # noqa: BLE001
        info.issues.append(f"无法读取工作簿: {exc}")
        return info
    try:
        for sheet in book.worksheets:
            iterator = sheet.iter_rows(values_only=True)
            first = next(iterator, None)
            headers = normalize_headers(first or [])
            rows = [tuple(row) for row in iterator if any(value is not None for value in row)]
            nonempty = [value for value in headers if value]
            info.sheets[sheet.title] = SheetInfo(nonempty, len(rows), sheet.max_column, rows)
            if not nonempty:
                info.issues.append(f"工作表“{sheet.title}”缺少表头")
            if len(nonempty) != len(set(nonempty)):
                info.issues.append(f"工作表“{sheet.title}”存在重复表头")
            if not rows:
                info.issues.append(f"工作表“{sheet.title}”为空")
            for row_number, row in enumerate(rows, start=2):
                for value in row:
                    if isinstance(value, float) and not math.isfinite(value):
                        info.issues.append(f"工作表“{sheet.title}”第{row_number}行包含非有限数值")
                        break
    finally:
        book.close()
    return info


def required_columns_issues(info: WorkbookInfo, sheet: str, required: Iterable[str]) -> list[str]:
    if sheet not in info.sheets:
        return [f"缺少工作表“{sheet}”"]
    headers = set(info.sheets[sheet].headers)
    missing = [column for column in required if column not in headers]
    return [f"工作表“{sheet}”缺少字段: {missing}"] if missing else []


def validate_key_and_constraints(info: WorkbookInfo) -> list[str]:
    issues: list[str] = []
    for sheet_name, sheet in info.sheets.items():
        for key_header in ("记录键", "样本键"):
            if key_header in sheet.headers:
                index = sheet.headers.index(key_header)
                keys = [row[index] if index < len(row) else None for row in sheet.rows]
                if any(value is None or str(value).strip() == "" for value in keys):
                    issues.append(f"工作表“{sheet_name}”的{key_header}存在空值")
                normalized = [str(value) for value in keys if value is not None and str(value).strip()]
                if len(normalized) != len(set(normalized)):
                    issues.append(f"工作表“{sheet_name}”的{key_header}不唯一")
        if sheet_name == "约束违反检查" and {"违反量", "容差", "是否满足"}.issubset(sheet.headers):
            vi = sheet.headers.index("违反量"); ti = sheet.headers.index("容差"); si = sheet.headers.index("是否满足")
            for row_number, row in enumerate(sheet.rows, start=2):
                try:
                    violation = float(row[vi]); tolerance = float(row[ti])
                except (TypeError, ValueError, IndexError):
                    continue
                declared = str(row[si]).strip().lower() if si < len(row) else ""
                expected = violation <= tolerance
                true_values = {"是", "true", "1", "满足", "通过"}
                false_values = {"否", "false", "0", "不满足", "未通过"}
                if declared in true_values | false_values and (declared in true_values) != expected:
                    issues.append(f"工作表“约束违反检查”第{row_number}行判定与违反量/容差不一致")
    return issues


def active_capabilities(subproblem: Mapping[str, Any]) -> dict[str, bool]:
    top = subproblem.get("capabilities") or {}
    deprecated = (subproblem.get("classification") or {}).get("capabilities") or {}
    return {str(key): bool(value) for key, value in (top or deprecated).items()}


def profile_names(subproblem: Mapping[str, Any]) -> list[str]:
    classification = subproblem.get("classification") or {}
    objective = classification.get("objective")
    structures = set(classification.get("structures", []) or [])
    profiles: list[str] = []
    if objective == "prediction": profiles.append("prediction")
    if objective == "evaluation": profiles.append("evaluation")
    if objective == "inference": profiles.append("statistics_ml")
    if "spatial" in structures: profiles.append("spatial")
    if "network" in structures: profiles.append("graph_network")
    if not profiles:
        legacy = subproblem.get("problem_types") or {}
        profiles.extend([legacy.get("primary"), *(legacy.get("secondary", []) or [])])
    return list(dict.fromkeys(item for item in profiles if item))


def validate_workbook_contract(
    solution: WorkbookInfo | None,
    robustness: WorkbookInfo | None,
    subproblem: Mapping[str, Any],
    schema: Mapping[str, Any],
    *,
    require_solution: bool,
    require_robustness: bool,
) -> list[str]:
    issues: list[str] = []
    if require_solution and solution is None:
        issues.append("缺少标准求解结果工作簿")
    if require_robustness and robustness is None:
        issues.append("缺少标准敏感性与鲁棒性工作簿")
    if solution:
        issues.extend(solution.issues)
        solution_spec = schema.get("solution_workbook", {})
        for sheet, spec in solution_spec.get("common_required_sheets", {}).items():
            issues.extend(required_columns_issues(solution, sheet, spec.get("required_columns", [])))
        capabilities = active_capabilities(subproblem)
        required_sheets = schema.get("capability_contract", {}).get("required_sheets", {})
        for capability, enabled in capabilities.items():
            if enabled:
                for sheet in required_sheets.get(capability, []):
                    if sheet not in solution.sheets:
                        issues.append(f"capability {capability} 要求工作表“{sheet}”")
        profiles = solution_spec.get("task_profiles", {})
        for profile in profile_names(subproblem):
            required_any = profiles.get(profile, {}).get("required_any", [])
            if required_any and not any(sheet in solution.sheets for sheet in required_any):
                issues.append(f"任务剖面 {profile} 至少需要一个工作表: {required_any}")
        issues.extend(validate_key_and_constraints(solution))
    if robustness:
        issues.extend(robustness.issues)
        robust_spec = schema.get("sensitivity_robustness_workbook", {})
        required_any = robust_spec.get("required_any_sheets", [])
        if required_any and not any(sheet in robustness.sheets for sheet in required_any):
            issues.append(f"敏感性与鲁棒性工作簿至少需要一个工作表: {required_any}")
        for sheet, spec in robust_spec.get("sheet_schemas", {}).items():
            if sheet in robustness.sheets:
                issues.extend(required_columns_issues(robustness, sheet, spec.get("required_columns", [])))
        issues.extend(validate_key_and_constraints(robustness))
    return issues


def discover_questions(root: Path) -> dict[str, QuestionSnapshot]:
    snapshots: dict[str, QuestionSnapshot] = {}
    result_root = root / "结果数据表"
    if result_root.is_dir():
        for directory in sorted(path for path in result_root.iterdir() if path.is_dir()):
            if QUESTION_RE.fullmatch(directory.name):
                key = question_key(directory.name)
                snapshots[key] = QuestionSnapshot(key, directory.name)
    for script in sorted(root.glob("问题*.py")):
        match = QUESTION_RE.match(script.stem)
        if match:
            chinese_name = match.group(0); key = question_key(chinese_name)
            snapshots.setdefault(key, QuestionSnapshot(key, chinese_name)).code_files.append(script.relative_to(root).as_posix())
    for snapshot in snapshots.values():
        snapshot.model_hash = combined_hash([root / item for item in snapshot.code_files], root)
        result_dir = result_root / snapshot.chinese_name
        solve = result_dir / f"{snapshot.chinese_name}求解结果.xlsx"
        robust = result_dir / f"{snapshot.chinese_name}敏感性与鲁棒性结果.xlsx"
        if solve.is_file(): snapshot.solution_workbook = inspect_workbook(solve, root)
        if robust.is_file(): snapshot.robustness_workbook = inspect_workbook(robust, root)
        number = re.sub(r"\D", "", snapshot.key)
        matlab = result_dir / f"q{number}_plot.m" if number else None
        if matlab and matlab.is_file():
            snapshot.matlab_script = matlab.relative_to(root).as_posix()
            snapshot.matlab_hash = sha256_file(matlab)
            text = matlab.read_text(encoding="utf-8", errors="replace")
            snapshot.matlab_has_title = bool(MATLAB_TITLE_RE.search(text))
            snapshot.workbook_references = sorted(set(WORKBOOK_REF_RE.findall(text)))
            snapshot.exported_figures = sorted(set(EXPORT_RE.findall(text)))
        figure_dir = result_dir / "图表"
        if figure_dir.is_dir():
            figure_paths = [path for path in figure_dir.rglob("*") if path.is_file() and path.suffix.lower() in FIGURE_SUFFIXES]
            snapshot.discovered_figures = sorted(path.relative_to(root).as_posix() for path in figure_paths)
            snapshot.figure_hash = combined_hash(figure_paths, root)
    return snapshots


def update_framework_header(path: Path, *, stale: bool, scope: str, timestamp: str) -> bool:
    if not path.is_file(): return False
    text = path.read_text(encoding="utf-8")
    replacements = {
        r"(?m)^- 最近同步：.*$": f"- 最近同步：`{scope}`",
        r"(?m)^- 最近同步时间：.*$": f"- 最近同步时间：`{timestamp}`",
        r"(?m)^- 当前状态：.*$": f"- 当前状态：`{'stale' if stale else 'current'}`",
    }
    changed = False
    for pattern, replacement in replacements.items():
        text, count = re.subn(pattern, replacement, text)
        changed = changed or bool(count)
    if changed: path.write_text(text, encoding="utf-8")
    return changed


def infer_scope(state: Mapping[str, Any], explicit: str | None) -> str:
    if explicit:
        if explicit not in SCOPE_RANK: raise ValueError(f"未知交付范围: {explicit}")
        return explicit
    phase = str((state.get("project", {}) or {}).get("current_phase", "model_design"))
    return PHASE_SCOPE.get(phase, "design")


def artifact_hashes(snapshot: QuestionSnapshot, data_hash: str | None) -> dict[str, str]:
    values = {
        "data": data_hash, "model": snapshot.model_hash,
        "solution_workbook": snapshot.solution_workbook.sha256 if snapshot.solution_workbook else None,
        "robustness_workbook": snapshot.robustness_workbook.sha256 if snapshot.robustness_workbook else None,
        "matlab_script": snapshot.matlab_hash, "figure_bundle": snapshot.figure_hash,
    }
    return {key: value for key, value in values.items() if value}


def stale_layers(current: Mapping[str, str], validated: Mapping[str, str]) -> list[str]:
    return [key for key in HASH_KEYS if validated.get(key) and current.get(key) != validated.get(key)]


def figure_chain_issues(snapshot: QuestionSnapshot, root: Path) -> list[str]:
    issues: list[str] = []
    if not snapshot.matlab_script:
        return ["图表交付缺少MATLAB脚本"]
    if not snapshot.matlab_has_title:
        issues.append("MATLAB脚本缺少title或sgtitle")
    expected_books = {
        Path(snapshot.solution_workbook.path).name if snapshot.solution_workbook else "",
        Path(snapshot.robustness_workbook.path).name if snapshot.robustness_workbook else "",
    } - {""}
    referenced = {Path(item).name for item in snapshot.workbook_references}
    if referenced and not referenced.issubset(expected_books):
        issues.append(f"MATLAB引用了非本问标准工作簿: {sorted(referenced - expected_books)}")
    result_dir = root / "结果数据表" / snapshot.chinese_name
    discovered_names = {Path(item).name for item in snapshot.discovered_figures}
    for declared in snapshot.exported_figures:
        name = Path(declared).name
        if name not in discovered_names and not (result_dir / declared).is_file():
            issues.append(f"MATLAB声明导出的图不存在: {declared}")
    if not snapshot.discovered_figures:
        issues.append("图表交付未发现正式图文件")
    source_paths = [root / item for item in [snapshot.matlab_script] if item]
    for book in (snapshot.solution_workbook, snapshot.robustness_workbook):
        if book: source_paths.append(root / book.path)
    newest_source = max((path.stat().st_mtime for path in source_paths if path.is_file()), default=0)
    for relative in snapshot.discovered_figures:
        figure = root / relative
        if figure.stat().st_mtime < newest_source:
            issues.append(f"正式图早于工作簿或MATLAB脚本: {relative}")
    return issues


def snapshot_to_dict(snapshot: QuestionSnapshot, current_hashes: Mapping[str, str]) -> dict[str, Any]:
    def payload(info: WorkbookInfo | None) -> dict[str, Any] | None:
        if info is None: return None
        return {
            "path": info.path, "sha256": info.sha256,
            "sheets": {name: {"headers": sheet.headers, "data_rows": sheet.data_rows, "max_column": sheet.max_column} for name, sheet in info.sheets.items()},
            "issues": info.issues,
        }
    return {
        "question": snapshot.chinese_name, "code_files": snapshot.code_files,
        "artifact_hashes": dict(current_hashes),
        "solution_workbook": payload(snapshot.solution_workbook),
        "robustness_workbook": payload(snapshot.robustness_workbook),
        "matlab_script": snapshot.matlab_script, "matlab_has_title": snapshot.matlab_has_title,
        "workbook_references": snapshot.workbook_references,
        "exported_figures": snapshot.exported_figures, "discovered_figures": snapshot.discovered_figures,
        "issues": snapshot.issues,
    }


def synchronize(
    root: Path,
    *,
    write: bool,
    question: str | None = None,
    delivery_scope: str | None = None,
    schema_path: Path = DEFAULT_SCHEMA_PATH,
) -> dict[str, Any]:
    root = root.resolve(); state_path = root / "state" / "project_state.yaml"
    state = load_yaml(state_path); schema = load_yaml(schema_path)
    snapshots = discover_questions(root)
    if question:
        normalized = question if question.startswith("Q") else question_key(question)
        snapshots = {key: value for key, value in snapshots.items() if key == normalized}
        if not snapshots: raise ValueError(f"未发现小问: {question}")
    scope = infer_scope(state, delivery_scope)
    data_hash = combined_hash(root_input_files(root), root)
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    issues: list[str] = []; stale_questions: list[str] = []
    if not state: issues.append("缺少state/project_state.yaml；同步器不会创建模型语义状态")
    subproblems = state.get("subproblems", {}) if state else {}
    snapshots_payload: dict[str, Any] = {}

    for key, snapshot in snapshots.items():
        sub = subproblems.get(key)
        if not isinstance(sub, dict):
            issues.append(f"{key}: 项目状态中缺少对应小问"); continue
        status_rank = STATUS_RANK.get(str(sub.get("status", "pending")), 0)
        require_results = status_rank >= STATUS_RANK["solved"] or SCOPE_RANK[scope] >= SCOPE_RANK["results"]
        require_figures = SCOPE_RANK[scope] >= SCOPE_RANK["figures"] and status_rank >= STATUS_RANK["solved"]
        contract_issues = validate_workbook_contract(
            snapshot.solution_workbook, snapshot.robustness_workbook, sub, schema,
            require_solution=require_results, require_robustness=require_results,
        )
        if require_results and not snapshot.code_files: contract_issues.append("缺少问题求解Python脚本")
        if require_figures: contract_issues.extend(figure_chain_issues(snapshot, root))
        snapshot.issues.extend(contract_issues)
        issues.extend(f"{key}: {item}" for item in snapshot.issues)

        current = artifact_hashes(snapshot, data_hash)
        validated = dict(sub.get("validated_artifact_hashes", {}) or {})
        if not validated:
            if sub.get("validated_data_hash"): validated["data"] = sub["validated_data_hash"]
            if sub.get("validated_model_hash"): validated["model"] = sub["validated_model_hash"]
        changed = stale_layers(current, validated)
        if changed:
            stale_questions.append(key); sub["artifacts_stale"] = True; sub["stale_layers"] = changed
            sub["result_summary_status"] = "stale"
            if sub.get("status") in {"validated", "written", "completed"}: sub["status"] = "solved"
            if sub.get("validation_status") == "passed": sub["validation_status"] = "pending"
        sub["artifact_hashes"] = current
        if data_hash: sub["data_hash"] = data_hash
        if snapshot.model_hash: sub["model_hash"] = snapshot.model_hash
        if snapshot.code_files: sub["code"] = snapshot.code_files[0]
        if snapshot.solution_workbook: sub["solution_workbook"] = snapshot.solution_workbook.path
        if snapshot.robustness_workbook: sub["robustness_workbook"] = snapshot.robustness_workbook.path
        if snapshot.matlab_script: sub["matlab_script"] = snapshot.matlab_script
        evidence = set(sub.get("evidence", []))
        evidence.update(snapshot.code_files)
        for value in [
            snapshot.solution_workbook.path if snapshot.solution_workbook else None,
            snapshot.robustness_workbook.path if snapshot.robustness_workbook else None,
            snapshot.matlab_script, *snapshot.discovered_figures,
        ]:
            if value: evidence.add(value)
        sub["evidence"] = sorted(evidence)
        snapshots_payload[key] = snapshot_to_dict(snapshot, current)

    if SCOPE_RANK[scope] >= SCOPE_RANK["docx"] and not (root / "模型论文框架.md").is_file():
        issues.append("正式写作交付缺少模型论文框架.md")
    if SCOPE_RANK[scope] >= SCOPE_RANK["docx"] and not state:
        issues.append("正式写作交付缺少项目状态")

    stale = bool(stale_questions)
    if write:
        update_framework_header(root / "模型论文框架.md", stale=stale, scope=question or f"{scope}交付同步", timestamp=timestamp)
    framework_hash = sha256_file(root / "模型论文框架.md") if (root / "模型论文框架.md").is_file() else None

    if state:
        execution = state.setdefault("execution", {})
        execution["last_run"] = timestamp
        execution["command"] = f"python scripts/sync_project.py --write --delivery-scope {scope}"
        execution["last_sync_report"] = "sync_report.yaml"
        artifacts = state.setdefault("artifacts", {})
        artifacts["code"] = sorted({path for item in snapshots.values() for path in item.code_files})
        artifacts["results"] = sorted({path for item in snapshots.values() for path in [item.solution_workbook.path if item.solution_workbook else None, item.robustness_workbook.path if item.robustness_workbook else None] if path})
        artifacts["figures"] = sorted({path for item in snapshots.values() for path in item.discovered_figures})
        artifacts["sync_report"] = "sync_report.yaml"
        framework = state.setdefault("paper_framework", {})
        framework["path"] = "模型论文框架.md"
        framework["sync_status"] = "stale" if stale else "current"
        framework["last_synced_at"] = timestamp
        framework["last_sync_scope"] = question or scope
        if framework_hash: framework["sha256"] = framework_hash

    report = {
        "sync_version": "1.1.0", "skill_version": "6.3.1", "generated_at": timestamp,
        "project_root": root.as_posix(), "delivery_scope": scope, "write_requested": write,
        "data_hash": data_hash, "framework_hash": framework_hash,
        "stale_questions": stale_questions, "questions": snapshots_payload, "issues": issues,
        "policy": {"promotes_validation": False, "rewrites_model_semantics": False, "stale_propagation": True},
    }
    if write:
        if state:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
        (root / "sync_report.yaml").write_text(yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding="utf-8")
        if state and framework_hash:
            persisted = load_yaml(state_path)
            if (persisted.get("paper_framework", {}) or {}).get("sha256") != framework_hash:
                raise RuntimeError("同步后框架哈希写入不一致")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", nargs="?", default=".")
    parser.add_argument("--question", help="Q1或问题一")
    parser.add_argument("--delivery-scope", choices=sorted(SCOPE_RANK, key=SCOPE_RANK.get))
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA_PATH))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    try:
        report = synchronize(
            Path(args.project_root), write=args.write, question=args.question,
            delivery_scope=args.delivery_scope, schema_path=Path(args.schema),
        )
    except (ValueError, OSError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc
    if not args.write: print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False))
    if args.strict and (report["issues"] or report["stale_questions"]): return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
