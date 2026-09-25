"""Read-only stage identity, configuration and source-bundle adaptation.

Output names come from output_contract; execution policy stays in the execution
contract. This module never changes project state or executes task source.
"""
from __future__ import annotations

import ast
import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Mapping, Sequence

import yaml
import run_config_parser
import python_source_checks
from execution_protocol import is_source_receipt, auxiliary_config_issues

ROOT = Path(__file__).resolve().parent.parent
BACKENDS = {"python": ".py", "matlab": ".m"}
POLICY_FIELDS = ("solver_backend", "solver_backend_selection_reason")
STAGE_FIELDS = {"backend", "selection_reason", "bundle_sha256", "validated_bundle_sha256",
                "conformance_delivery", "conformance_acceptance"}
NUMERICAL_FIELDS = ("code", "result_analysis_code", "solution_workbook", "result_analysis_workbook")
QUESTION_NUMERALS = ("一", "二", "三", "四", "五", "六", "七", "八", "九", "十")


def inspect_project_backend_declarations(
    state: Mapping[str, Any], *, requested_backend: str | None = None,
) -> dict[str, Any]:
    """Classify whole-project declarations without reading files or granting execution."""
    if not isinstance(state, Mapping):
        raise ValueError("project state must be a mapping")
    if requested_backend is not None and requested_backend not in ("auto", "python", "matlab"):
        raise ValueError("requested backend must be auto, python or matlab")
    issues: list[str] = []
    execution = state.get("execution", {})
    if not isinstance(execution, Mapping):
        issues.append("execution must be a mapping")
        execution = {}
    subproblems = state.get("subproblems", {})
    if not isinstance(subproblems, Mapping):
        issues.append("subproblems must be a mapping")
        subproblems = {}
    present = [name in execution for name in POLICY_FIELDS]
    selected = execution.get(POLICY_FIELDS[0])
    if any(present):
        if not all(present):
            issues.append("project backend and selection reason must be present together")
        if not _backend(selected):
            issues.append("execution.solver_backend must be python or matlab, never auto")
        if not _reason(execution.get(POLICY_FIELDS[1])):
            issues.append("project backend selection reason must be a non-empty string")

    declarations: list[dict[str, Any]] = []
    has_numerical_state = False
    has_legacy_selectors = False
    missing_stage_backend = False
    for question, entry in sorted(subproblems.items(), key=lambda item: str(item[0])):
        if not isinstance(question, str) or not isinstance(entry, Mapping):
            issues.append(f"subproblem {question!r} must have a string key and mapping record")
            continue
        has_numerical_state |= any(entry.get(name) for name in NUMERICAL_FIELDS)
        stages = entry.get("solver_execution", {})
        if not isinstance(stages, Mapping):
            issues.append(f"{question}.solver_execution must be a mapping")
            continue
        if set(stages) - {"primary", "analysis"}:
            issues.append(f"{question}.solver_execution contains unknown stages")
        for stage, code_field in (("primary", "code"), ("analysis", "result_analysis_code")):
            record = stages.get(stage, {})
            if not isinstance(record, Mapping):
                issues.append(f"{question}.{stage} must be a mapping")
                continue
            has_numerical_state |= stage in stages
            if set(record) - STAGE_FIELDS:
                issues.append(f"{question}.{stage} contains unknown execution fields")
            legacy = "backend" in record or "selection_reason" in record
            has_legacy_selectors |= legacy
            actual = record.get("backend")
            if legacy and (not _backend(actual) or not _reason(record.get("selection_reason"))):
                issues.append(f"{question}.{stage} legacy backend/reason pair is malformed")
            for field in ("bundle_sha256", "validated_bundle_sha256"):
                value = record.get(field)
                if field in record and (not isinstance(value, str) or len(value) != 64
                                        or any(c not in "0123456789abcdefABCDEF" for c in value)):
                    issues.append(f"{question}.{stage}.{field} must be a SHA-256 string")
            if "validated_bundle_sha256" in record and "bundle_sha256" not in record:
                issues.append(f"{question}.{stage} validated bundle requires a delivered bundle")
            code = entry.get(code_field)
            if code is not None and not isinstance(code, str):
                issues.append(f"{question}.{code_field} must be a string")
            workbook_field = "solution_workbook" if stage == "primary" else "result_analysis_workbook"
            execution_field = "primary_execution_status" if stage == "primary" else "analysis_execution_status"
            numerical_record = bool(entry.get(workbook_field)) or entry.get(execution_field) in (
                "code_delivered", "awaiting_user_execution", "workbook_received", "accepted", "rejected", "redo_required",
            )
            has_numerical_state |= numerical_record
            if record or code or stage in stages or numerical_record:
                declarations.append({
                    "question": question, "stage": stage,
                    "declared_backend": actual if _backend(actual) else None,
                    "code": code if isinstance(code, str) else None,
                    "artifact_identity_verified": False,
                })
                missing_stage_backend |= not _backend(actual)
            expected = selected if _backend(selected) else actual
            if isinstance(code, str) and code and _backend(expected):
                if Path(code).suffix.lower() != BACKENDS[expected]:
                    issues.append(f"{question}.{stage} declared code suffix conflicts with backend {expected}")

    candidates = {row["declared_backend"] for row in declarations if row["declared_backend"]}
    if any(present) and has_legacy_selectors:
        issues.append("root policy and legacy stage selectors cannot coexist in canonical state")
    if issues:
        kind = "invalid"
    elif any(present):
        kind = "canonical_declarations"
    elif has_legacy_selectors:
        kind = "legacy_mixed" if len(candidates) > 1 else (
            "legacy_unresolved" if missing_stage_backend else "legacy_consistent"
        )
    elif has_numerical_state:
        kind = "legacy_unresolved"
    else:
        kind = "unselected"
    request_conflict = bool(_backend(selected) and requested_backend not in (None, "auto", selected))
    if request_conflict:
        issues.append(f"requested backend {requested_backend} conflicts with project backend {selected}")
    return {
        "scope": "project", "kind": kind, "diagnostic_only": True,
        "selected_backend": selected if _backend(selected) else None,
        "candidate_backend": next(iter(candidates)) if kind == "legacy_consistent" else None,
        "candidate_evidence": "declarations_only_not_artifact_validation",
        "requested_backend": requested_backend, "request_conflict": request_conflict,
        "declarations": declarations, "issues": issues,
        "schema_validated": False, "environment_verified": False, "execution_authorized": False,
    }


def _backend(value: Any) -> bool:
    return isinstance(value, str) and value in BACKENDS


def _reason(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


class StageCodeError(ValueError):
    """A declared stage cannot be uniquely or safely bound."""


class StageCodeMissingError(StageCodeError):
    """A backend was selected but its not-yet-registered entry does not exist."""


def current_project_backend(
    state: Mapping[str, Any], *, requested_backend: str | None = None, required: bool = False,
) -> str | None:
    """Read the one current selection; historical declarations remain diagnostic only.

    This checks project-wide declaration consistency, not Schema, model approval,
    source identity, environment availability or numerical acceptance.
    """
    report = inspect_project_backend_declarations(state, requested_backend=requested_backend)
    if report["issues"]:
        raise StageCodeError("; ".join(report["issues"]))
    if report["kind"] == "unselected":
        if required:
            raise StageCodeError("current numerical work requires an explicit project backend selection")
        return None
    if report["kind"] != "canonical_declarations":
        raise StageCodeError("historical numerical declarations require explicit project migration")
    return report["selected_backend"]


@dataclass(frozen=True)
class StageCode:
    path: Path
    problem_name: str
    stage: str
    backend: str
    legacy: bool = False


def question_name(question: str) -> str:
    match = re.fullmatch(r"Q([1-9][0-9]*)", str(question))
    if match and 1 <= int(match[1]) <= len(QUESTION_NUMERALS):
        return "问题" + QUESTION_NUMERALS[int(match[1]) - 1]
    return str(question)


def question_number(question: str) -> int | None:
    suffix = question_name(question).removeprefix("问题")
    return QUESTION_NUMERALS.index(suffix) + 1 if suffix in QUESTION_NUMERALS else None


def _names(problem: str, stage: str) -> dict[str, str]:
    if stage not in {"primary", "analysis"}:
        raise StageCodeError(f"未知求解阶段: {stage}")
    number = question_number(problem)
    if number is None:
        raise StageCodeError(f"无法解析问题编号: {problem}")
    contract = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
    per_question = contract["per_question"]
    mappings = per_question.get("solver_scripts") or {"python": per_question["python_scripts"]}
    key = "primary" if stage == "primary" else "result_analysis"
    return {backend: str(mapping[key]).replace("{中文序号}", problem.removeprefix("问题"))
            .replace("{阿拉伯序号}", str(number)) for backend, mapping in mappings.items()}


def _relative_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise StageCodeError("源码路径必须使用非空项目相对POSIX路径")
    value = PurePosixPath(relative)
    if value.is_absolute() or PureWindowsPath(relative).is_absolute() or PureWindowsPath(relative).drive:
        raise StageCodeError("源码路径不能是绝对路径")
    if any(part in {"", ".", ".."} for part in relative.split("/")) or any("\x00" in part or ":" in part for part in value.parts):
        raise StageCodeError("源码路径含越界或非规范片段")
    root = root.resolve()
    candidate = root
    for part in value.parts:
        if candidate.is_dir():
            matches = [item.name for item in candidate.iterdir() if item.name.casefold() == part.casefold()]
            if len(matches) > 1 or (matches and matches[0] != part):
                raise StageCodeError(f"源码路径大小写不唯一或不一致: {relative}")
        candidate /= part
        if candidate.is_symlink():
            raise StageCodeError(f"源码依赖不接受符号链接别名: {relative}")
    if not candidate.resolve().is_relative_to(root):
        raise StageCodeError("源码路径越出项目根目录")
    return candidate.resolve()


def script_identity(script: Path) -> StageCode:
    if script.parent.name == "数据预处理" and script.name == "数据预处理.py":
        return StageCode(script.resolve(), "数据预处理", "preprocessing", "python")
    if not script.parent.name.endswith("求解"):
        raise StageCodeError("正式阶段代码必须位于数据预处理/或问题X求解/目录")
    problem = script.parent.name.removesuffix("求解")
    for stage in ("primary", "analysis"):
        for backend, name in _names(problem, stage).items():
            if script.name == name:
                return StageCode(script.resolve(), problem, stage, backend)
    raise StageCodeError(f"阶段代码文件名与问题编号/后端合同不一致: {script.name}")


def resolve_stage_code(root: Path, question: str, stage: str,
                       selection: Mapping[str, Any] | str | None = None, *,
                       entry: Mapping[str, Any] | None = None,
                       project_backend: str | None = None) -> StageCode | None:
    root = Path(root).resolve()
    entry = {} if entry is None else entry
    if not isinstance(entry, Mapping):
        raise StageCodeError("阶段状态必须为映射")
    if stage == "preprocessing":
        relative = str(entry.get("code") or "数据预处理/数据预处理.py")
        path = _relative_path(root, relative)
        if path != root / "数据预处理/数据预处理.py":
            raise StageCodeError("预处理只支持既有Python标准入口")
        return StageCode(path, "数据预处理", stage, "python") if path.is_file() else None
    problem = question_name(question)
    names = _names(problem, stage)
    if selection is None:
        execution = entry.get("solver_execution")
        if execution is not None and not isinstance(execution, Mapping):
            raise StageCodeError("solver_execution必须为映射")
        selection = (execution or {}).get(stage)
        selection = {} if selection is None else selection
    if not isinstance(selection, (Mapping, str)):
        raise StageCodeError("后端选择必须为映射或后端名")
    if (isinstance(selection, Mapping) and "backend" in selection
            and (not isinstance(selection["backend"], str) or selection["backend"] not in BACKENDS)):
        raise StageCodeError("已选后端必须为python或matlab")
    backend = selection if isinstance(selection, str) else str(selection.get("backend") or "")
    if project_backend is not None:
        if project_backend not in BACKENDS:
            raise StageCodeError("项目后端必须为python或matlab")
        if isinstance(selection, Mapping) and ({"backend", "selection_reason"} & set(selection)):
            raise StageCodeError("当前阶段不得再保存独立后端选择")
        if backend and backend != project_backend:
            raise StageCodeError("阶段请求后端与项目后端冲突")
        backend = project_backend
    if backend and backend not in BACKENDS:
        raise StageCodeError(f"已选后端必须为python或matlab: {backend}")
    field = "code" if stage == "primary" else "result_analysis_code"
    declared = str(entry.get(field) or "")
    candidates = {language: root / f"{problem}求解" / name for language, name in names.items()}
    if declared:
        path = _relative_path(root, declared)
        matched = [language for language, item in candidates.items() if item == path]
        legacy = path == root / names.get("python", "")
        if not matched and not legacy:
            raise StageCodeError(f"状态登记的{stage}入口不符合输出合同: {declared}")
        actual_backend = matched[0] if matched else "python"
        if backend and backend != actual_backend:
            raise StageCodeError("状态后端与登记入口冲突")
        if actual_backend == "matlab" and not backend:
            raise StageCodeError("MATLAB入口必须有显式后端选择")
        if not path.is_file():
            raise StageCodeError(f"已登记阶段入口不存在: {declared}")
        return StageCode(path, problem, stage, actual_backend, legacy)
    if backend:
        if backend not in candidates:
            raise StageCodeError(f"输出合同不支持后端: {backend}")
        path = _relative_path(root, candidates[backend].relative_to(root).as_posix())
        if not path.is_file():
            raise StageCodeMissingError(f"已选{backend}阶段入口缺失，禁止fallback: {path.name}")
        return StageCode(path, problem, stage, backend)
    existing = [(language, path) for language, path in candidates.items() if path.is_file()]
    if len(existing) > 1:
        raise StageCodeError("同阶段存在多个后端入口，必须显式选择")
    if existing:
        language, path = existing[0]
        if language != "python":
            raise StageCodeError("MATLAB求解必须显式确定后端")
        return StageCode(path.resolve(), problem, stage, language)
    legacy = root / names["python"]
    return StageCode(legacy, problem, stage, "python", True) if legacy.is_file() else None


def parse_stage_config(path: Path, backend: str | None = None) -> tuple[str, dict[str, Any]]:
    path = Path(path)
    backend = backend or next((key for key, suffix in BACKENDS.items() if suffix == path.suffix.lower()), "")
    if backend not in BACKENDS or path.suffix.lower() != BACKENDS[backend]:
        raise StageCodeError("源码扩展名与后端不一致")
    return run_config_parser.parse_embedded_config(path.read_text(encoding="utf-8-sig"),
                                                 messages=run_config_parser.DELIVERY_MESSAGES,
                                                 backend=backend)


def _expand_windows_short_path(path: Path) -> Path:
    """Expand Win32 8.3 names without resolving source symlinks before validation."""
    if os.name != "nt":
        return path
    import ctypes

    expand = ctypes.WinDLL("kernel32", use_last_error=True).GetLongPathNameW
    expand.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32]
    expand.restype = ctypes.c_uint32
    candidate, suffix = path, []
    size = expand(str(candidate), None, 0)
    while not size:
        if candidate == candidate.parent:
            return path  # Unreadable paths remain subject to the normal gates.
        suffix.insert(0, candidate.name)
        candidate = candidate.parent
        size = expand(str(candidate), None, 0)
    buffer = ctypes.create_unicode_buffer(size)
    written = expand(str(candidate), buffer, size)
    if not written or written >= size:
        raise StageCodeError("无法稳定展开Windows源码路径")
    return Path(buffer.value).joinpath(*suffix)


def stage_code_fingerprint(root: Path, entrypoint: Path, dependencies: Sequence[Mapping[str, Any]] = (), *,
                           check_declared_hashes: bool = True) -> dict[str, Any]:
    root = Path(root).resolve()
    entrypoint = Path(entrypoint)
    if ".." in entrypoint.parts:
        raise StageCodeError("入口路径含非规范越界片段")
    try:
        absolute_entry = (entrypoint if entrypoint.is_absolute() else root / entrypoint).absolute()
        entry_relative = _expand_windows_short_path(absolute_entry).relative_to(root).as_posix()
    except ValueError as exc:
        raise StageCodeError("入口路径越出项目根目录") from exc
    if not isinstance(dependencies, (list, tuple)):
        raise StageCodeError("code_dependencies必须为路径/sha256对象列表")
    declared: list[tuple[str, str | None]] = [(entry_relative, None)]
    for item in dependencies:
        if not isinstance(item, Mapping) or set(item) != {"path", "sha256"}:
            raise StageCodeError("code_dependencies每项必须且只能含path/sha256")
        if not isinstance(item["path"], str) or not re.fullmatch(r"[0-9a-fA-F]{64}", str(item["sha256"])):
            raise StageCodeError("代码依赖路径或SHA-256无效")
        declared.append((item["path"], str(item["sha256"]).lower()))
    seen: set[str] = set()
    resolved: list[tuple[str, Path, str | None]] = []
    for relative, expected in declared:
        path = _relative_path(root, relative)
        if path.suffix.lower() not in {".py", ".m"}:
            raise StageCodeError(f"代码依赖必须为项目源码.py/.m: {relative}")
        if not path.is_file():
            raise StageCodeError(f"源码文件不存在: {relative}")
        if relative.casefold() in seen or any(path.samefile(previous) for _, previous, _ in resolved):
            raise StageCodeError(f"源码依赖重复或包含入口自身: {relative}")
        seen.add(relative.casefold())
        resolved.append((relative, path, expected))
    digest = hashlib.sha256()
    files: list[dict[str, str]] = []
    for relative, path, expected in sorted(resolved, key=lambda item: item[0].encode("utf-8")):
        current = hashlib.sha256(path.read_bytes()).hexdigest()
        if check_declared_hashes and expected and expected != current:
            raise StageCodeError(f"源码依赖SHA-256不一致: {relative}")
        files.append({"path": relative, "sha256": current})
        digest.update(relative.encode("utf-8") + b"\0" + bytes.fromhex(current))
    return {"entry_sha256": next(item["sha256"] for item in files if item["path"] == entry_relative),
            "bundle_sha256": digest.hexdigest(), "files": files}


def _python_module_files(base: Path, pieces: Sequence[str]) -> tuple[bool, list[Path]]:
    """Locate a project import without importing it; regular packages precede modules."""
    found: list[Path] = []
    matched = False
    for piece in pieces:
        package = base / piece
        initializer = package / "__init__.py"
        module = base / (piece + ".py")
        if initializer.is_file():
            found.append(initializer)
        elif module.is_file():
            found.append(module)
            return True, found  # Remaining from-import components may be attributes.
        elif not package.is_dir():
            break
        matched = True
        base = package
    return matched, found


def _python_import_files(root: Path, entrypoint: Path, source: Path, node: ast.AST) -> tuple[list[Path], list[str]]:
    """Use entry import roots for absolute imports and the source package for relatives."""
    bases = list(dict.fromkeys((entrypoint.parent, root)))
    found: list[Path] = []
    if isinstance(node, ast.ImportFrom) and node.level:
        anchor = entrypoint.parent if source.is_relative_to(entrypoint.parent) else root
        package = source.relative_to(anchor).parts[:-1]
        if source == entrypoint or node.level > len(package):
            return [], [f"Python相对导入越出已知包上下文: {source.relative_to(root).as_posix()}"]
        # Importing the current helper already executes each regular parent package.
        found.extend(anchor.joinpath(*package[:i], "__init__.py") for i in range(1, len(package) + 1))
        bases = [anchor.joinpath(*package[:len(package) - node.level + 1])]
    if isinstance(node, ast.Import):
        modules = [alias.name for alias in node.names]
    else:
        modules = [node.module] if node.module else []
        modules.extend((node.module + "." if node.module else "") + alias.name
                       for alias in node.names if alias.name != "*")
    for module in modules:
        for base in bases:
            matched, paths = _python_module_files(base, module.split("."))
            found.extend(paths)
            if matched:
                break
    return [path for path in found if path.is_file()], []


def _matlab_references(text: str) -> list[str]:
    """Read lexical function references, preserving per-function variable precedence."""
    import matlab_code_checks as matlab
    rows = matlab.statements(matlab.tokenize(text))
    block_heads = {"if", "for", "parfor", "while", "switch", "try", "spmd", "arguments"}
    # Valid function files either terminate every function explicitly (required
    # for nesting), or let the next declaration/EOF end each flat local function.
    kinds: list[str] = []
    explicit_function_ends = False
    for row in rows:
        head = row[0].value
        if head == "function" or head in block_heads:
            kinds.append(head)
        elif head == "end" and kinds:
            explicit_function_ends |= kinds.pop() == "function"
    scopes: list[dict[str, Any]] = [{"parent": None, "children": set(), "variables": set()}]
    row_scopes: list[int] = []
    row_endings: list[str | None] = []
    stack: list[tuple[str, int]] = []
    scope = 0
    for row in rows:
        head = row[0].value
        if head == "function":
            if not explicit_function_ends:
                scope = 0
                stack.clear()
            name, _ = matlab.function_signature(row)
            parent = scope
            scopes[parent]["children"].add(name)
            scope = len(scopes)
            values = [token.value for token in row]
            name_index = values.index("=") + 1 if "=" in values else 1
            parameters = row[name_index + 2:] if "(" in values[name_index + 1:] else []
            variables = {token.value for token in parameters if token.kind == "identifier"}
            if "=" in values:
                variables.update(token.value for token in row[1:name_index - 1] if token.kind == "identifier")
            scopes.append({"parent": parent, "children": set(), "variables": variables})
            stack.append((head, scope))
        elif head in block_heads:
            stack.append((head, scope))
        row_scopes.append(scope)
        row_endings.append(stack[-1][0] if head == "end" and stack else None)
        if head == "end" and stack:
            kind, ended = stack.pop()
            if kind == "function":
                scope = scopes[ended]["parent"]
    references: list[str] = []
    controls: list[tuple[int, set[str]]] = []
    for row, current, ending in zip(rows, row_scopes, row_endings):
        if row[0].value == "function":
            continue
        head = row[0].value
        if head in {"global", "persistent"}:
            scopes[current]["variables"].update(token.value for token in row[1:] if token.kind == "identifier")
            continue
        if head in block_heads:
            controls.append((current, set(scopes[current]["variables"])))
        elif head in {"else", "elseif", "case", "otherwise", "catch"} and controls:
            scopes[current]["variables"] = set(controls[-1][1])
        elif ending and ending != "function" and controls:
            _, scopes[current]["variables"] = controls.pop()
        visible = set(scopes[0]["children"])
        variables = set(scopes[current]["variables"])
        ancestor = current
        while ancestor:
            visible.update(scopes[ancestor]["children"])
            ancestor = scopes[ancestor]["parent"]
            variables.update(scopes[ancestor]["variables"])
        values = [token.value for token in row]
        # A command's whitespace-separated arguments are character text, not
        # expressions: `disp helper` must not bind helper.m; `helper text` must.
        command_end = 1
        while command_end + 1 < len(row) and values[command_end] == "." and row[command_end + 1].kind == "identifier":
            command_end += 2
        statement_heads = block_heads | {"else", "elseif", "case", "otherwise", "catch", "end", "return", "break", "continue"}
        if (row[0].kind == "identifier" and head not in statement_heads and command_end < len(row)
                and row[command_end].kind in {"identifier", "char", "string", "number"}
                and row[command_end].start > row[command_end - 1].end):
            if head not in variables and (command_end > 1 or head not in visible):
                references.append("".join(values[:command_end]))
            continue
        assignment = values.index("=") if "=" in values else None
        assigned: set[str] = set()
        if assignment is not None:
            left = row[:assignment]
            if left[0].value == "[":
                assigned.update(token.value for token in left if token.kind == "identifier")
            else:
                first = 1 if left[0].value in {"for", "parfor"} else 0
                if len(left) > first and left[first].kind == "identifier":
                    assigned.add(left[first].value)
        # Anonymous parameters only shadow their own expression, not earlier arguments.
        anonymous: list[tuple[int, int, set[str]]] = []
        for i in range(len(row) - 2):
            if values[i:i + 2] == ["@", "("]:
                end = next((j for j in range(i + 2, len(row)) if values[j] == ")"), len(row))
                names = {token.value for token in row[i + 2:end] if token.kind == "identifier"}
                depth, stop = 0, end + 1
                while stop < len(row):
                    value = values[stop]
                    if depth == 0 and value in {",", ")", "]", "}"}:
                        break
                    depth += int(value in {"(", "[", "{"}) - int(value in {")", "]", "}"})
                    stop += 1
                anonymous.append((i + 2, stop, names))
        i = 0
        while i < len(row):
            token = row[i]
            if token.kind != "identifier" or (i and values[i - 1] == "."):
                i += 1
                continue
            direct_handle = i > 0 and values[i - 1] == "@"
            left_target = assignment is not None and i < assignment and token.value in assigned
            pieces = [token.value]
            end = i + 1
            while end + 1 < len(row) and values[end] == "." and row[end + 1].kind == "identifier":
                pieces.append(row[end + 1].value)
                end += 2
            anonymous_variables = set().union(*(names for start, stop, names in anonymous if start <= i < stop))
            if not left_target and (direct_handle or token.value not in variables | anonymous_variables):
                if len(pieces) > 1 or token.value not in visible:
                    references.append(".".join(pieces))
            i = end
        scopes[current]["variables"].update(assigned)
    return list(dict.fromkeys(references))


def dependency_reference_issues(root: Path, entrypoint: Path, config: Mapping[str, Any]) -> list[str]:
    """Reject discoverable undeclared local modules and unsupported dynamic imports."""
    root, entrypoint = Path(root).resolve(), Path(entrypoint).resolve()
    dependencies = config.get("code_dependencies") or []
    files = [entrypoint, *(root / item["path"] for item in dependencies)]
    declared = {path.resolve() for path in files}
    issues: list[str] = []
    for source in files:
        text = source.read_text(encoding="utf-8-sig")
        if source.suffix.lower() == ".py":
            tree = ast.parse(text)
            references: list[Path] = []
            issues.extend(python_source_checks.execution_reference_issues(tree))
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    paths, errors = _python_import_files(root, entrypoint, source, node)
                    references.extend(paths)
                    issues.extend(errors)
            for path in references:
                try:
                    _relative_path(root, path.relative_to(root).as_posix())
                except StageCodeError as exc:
                    issues.append(str(exc))
                if path.resolve() not in declared:
                    issues.append(f"项目Python依赖未声明: {path.relative_to(root).as_posix()}")
        else:
            import matlab_code_checks
            tokens = matlab_code_checks.tokenize(text)
            for row in matlab_code_checks.statements(tokens):
                for i, token in enumerate(row):
                    if token.kind != "identifier":
                        continue
                    if token.value in matlab_code_checks.FORBIDDEN_EXECUTION_CALLS and (i == 0 or (i + 1 < len(row) and row[i + 1].value == "(")):
                        issues.append(f"MATLAB源码闭包不支持动态执行/缓存锁定: {token.value}")
                    if token.value == "py" and i + 1 < len(row) and row[i + 1].value == ".":
                        issues.append("MATLAB源码闭包不支持启动Python后端")
            if any(part.startswith("+") or part == "private" for part in source.relative_to(root).parts[:-1]):
                issues.append("MATLAB项目package/private源码解析尚未验证，不支持声明为已闭包")
            for name in _matlab_references(text):
                pieces = name.split(".")
                for base in dict.fromkeys((source.parent, entrypoint.parent, root)):
                    if len(pieces) > 1:
                        if (base / ("+" + pieces[0])).is_dir():
                            issues.append(f"MATLAB项目限定函数解析尚未验证: {name}")
                        continue
                    if (base / "private" / (name + ".m")).is_file():
                        issues.append(f"MATLAB项目private函数解析尚未验证: {name}")
                        break
                    path = base / (name + ".m")
                    if path.is_file():
                        try:
                            _relative_path(root, path.relative_to(root).as_posix())
                        except StageCodeError as exc:
                            issues.append(str(exc))
                        if path.resolve() not in declared:
                            issues.append(f"项目MATLAB依赖未声明: {path.relative_to(root).as_posix()}")
                        break
    return list(dict.fromkeys(issues))


def requires_bundle_binding(root: Path, entry: Mapping[str, Any], stage: str, *,
                            project_backend: str | None = None) -> bool:
    """Detect the new contract, without granting binding or legacy acceptance."""
    if project_backend is not None:
        return True
    if not isinstance(entry, Mapping):
        return True
    execution = entry.get("solver_execution")
    if execution is not None and not isinstance(execution, Mapping):
        return True
    selection = (execution or {}).get(stage)
    if selection is not None and (not isinstance(selection, Mapping) or bool(selection)):
        return True
    relative = str(entry.get("code" if stage == "primary" else "result_analysis_code") or "")
    if relative.endswith(".m"):
        return True
    if not relative.endswith(".py"):
        return False
    try:
        path = _relative_path(Path(root), relative)
        if path.is_file():
            _, config = parse_stage_config(path, "python")
            return is_source_receipt(config.get("run_receipt_protocol_version"))
    except (OSError, ValueError, SyntaxError):
        pass
    return False


def validate_stage_binding(root: Path, entry: Mapping[str, Any], stage: str, *,
                           require_delivered: bool = True, require_validated: bool = False,
                           project_backend: str | None = None) -> list[str]:
    root = Path(root).resolve()
    if not isinstance(entry, Mapping):
        return ["阶段状态必须为映射"]
    execution = entry.get("solver_execution")
    if execution is not None and not isinstance(execution, Mapping):
        return ["solver_execution必须为映射"]
    selection = (execution or {}).get(stage)
    if selection is not None and not isinstance(selection, Mapping):
        return [f"solver_execution.{stage}必须为映射"]
    selection = selection or {}
    if project_backend is not None:
        if project_backend not in BACKENDS:
            return ["项目后端必须为python或matlab"]
        if {"backend", "selection_reason"} & set(selection):
            return [f"{stage}当前阶段不得再保存独立后端选择"]
    field = "code" if stage == "primary" else "result_analysis_code"
    hash_field = "primary_code_sha256" if stage == "primary" else "analysis_code_sha256"
    relative = str(entry.get(field) or "")
    if not relative:
        return [f"{stage}缺少已交付入口路径"] if selection or project_backend else []
    try:
        path = _relative_path(root, relative)
        if not path.is_file():
            raise StageCodeError(f"{stage}入口文件不存在")
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if entry.get(hash_field) and actual_hash != str(entry[hash_field]).lower():
            raise StageCodeError(f"{stage}入口SHA-256与已交付代码不一致")
        if project_backend is None and not selection and path.suffix == ".py":
            # Preserve historical source-only checks, including old non-config fixtures.
            try:
                _, config = parse_stage_config(path, "python")
            except (ValueError, SyntaxError):
                return []
            if not is_source_receipt(config.get("run_receipt_protocol_version")):
                return auxiliary_config_issues(config)
        else:
            _, config = parse_stage_config(path)
        identity = script_identity(path)
        if require_delivered and not re.fullmatch(r"[0-9a-fA-F]{64}", str(entry.get(hash_field, ""))):
            raise StageCodeError(f"{stage}新协议缺少已交付入口SHA-256")
        backend = project_backend if project_backend is not None else selection.get("backend")
        if not isinstance(backend, str) or backend not in BACKENDS or backend != identity.backend or config.get("solver_backend") != backend:
            raise StageCodeError(f"{stage}状态、入口及RUN_CONFIG后端不一致")
        if config.get("stage") != stage or config.get("problem_name") != identity.problem_name:
            raise StageCodeError(f"{stage}配置与目录身份不一致")
        if not is_source_receipt(config.get("run_receipt_protocol_version")):
            raise StageCodeError("新后端绑定必须使用RUN_RECEIPT 1.1.0/1.2.0")
        auxiliary_issues = auxiliary_config_issues(config)
        if auxiliary_issues:
            raise StageCodeError("; ".join(auxiliary_issues))
        if stage == "analysis":
            accepted_hashes = entry.get("validated_artifact_hashes")
            accepted_primary = accepted_hashes.get("solution_workbook") if isinstance(accepted_hashes, Mapping) else None
            upstream = config.get("primary_workbook_sha256")
            if not re.fullmatch(r"[0-9a-fA-F]{64}", str(upstream or "")):
                raise StageCodeError("1.1 analysis必须声明有效primary_workbook_sha256")
            if not accepted_primary or str(upstream).lower() != str(accepted_primary).lower():
                raise StageCodeError("1.1 analysis源码必须绑定当前accepted主工作簿SHA-256")
        fingerprint = stage_code_fingerprint(root, path, config.get("code_dependencies", []))
        issues = dependency_reference_issues(root, path, config)
        if require_delivered and fingerprint["bundle_sha256"] != str(selection.get("bundle_sha256", "")).lower():
            issues.append(f"{stage}当前源码bundle与已交付身份不一致")
        if require_validated and fingerprint["bundle_sha256"] != str(selection.get("validated_bundle_sha256", "")).lower():
            issues.append(f"{stage}当前源码bundle与已验收身份不一致")
        return issues
    except (OSError, ValueError, SyntaxError, TypeError, KeyError) as exc:
        return [str(exc)]
