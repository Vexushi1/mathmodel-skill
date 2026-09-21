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

ROOT = Path(__file__).resolve().parent.parent
BACKENDS = {"python": ".py", "matlab": ".m"}
QUESTION_NUMERALS = ("一", "二", "三", "四", "五", "六", "七", "八", "九", "十")


class StageCodeError(ValueError):
    """A declared stage cannot be uniquely or safely bound."""


class StageCodeMissingError(StageCodeError):
    """A backend was selected but its not-yet-registered entry does not exist."""


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
                       entry: Mapping[str, Any] | None = None) -> StageCode | None:
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


def dependency_reference_issues(root: Path, entrypoint: Path, config: Mapping[str, Any]) -> list[str]:
    """Reject discoverable undeclared local modules and unsupported dynamic imports."""
    dependencies = config.get("code_dependencies") or []
    files = [entrypoint, *(root / item["path"] for item in dependencies)]
    declared = {path.resolve() for path in files}
    issues: list[str] = []
    for source in files:
        text = source.read_text(encoding="utf-8-sig")
        if source.suffix.lower() == ".py":
            tree = ast.parse(text)
            modules: list[str] = []
            imported_names: dict[str, str] = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_names.update({alias.asname or alias.name.split(".")[0]: alias.name for alias in node.names})
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported_names.update({alias.asname or alias.name: node.module + "." + alias.name for alias in node.names})
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        modules.append(node.module)
                    modules.extend((node.module + "." if node.module else "") + alias.name for alias in node.names)
                elif isinstance(node, ast.Call):
                    name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
                    if name in {"__import__", "import_module", "exec", "eval", "run_path", "run_module", "spec_from_file_location"}:
                        issues.append("新源码闭包不支持动态Python代码加载")
                    target = node.func
                    chain: list[str] = []
                    while isinstance(target, ast.Attribute):
                        chain.insert(0, target.attr)
                        target = target.value
                    if isinstance(target, ast.Name):
                        chain.insert(0, imported_names.get(target.id, target.id))
                    called = ".".join(chain)
                    if called in {"importlib.import_module", "importlib.util.spec_from_file_location",
                                   "runpy.run_path", "runpy.run_module", "builtins.eval", "builtins.exec", "builtins.__import__"}:
                        issues.append("新源码闭包不支持动态Python代码加载")
                    if (called.startswith(("subprocess.", "matlab.engine.")) or called in {"os.system", "os.popen"}
                            or called.startswith(("os.exec", "os.spawn"))):
                        issues.append("求解阶段不支持shell/跨后端进程启动")
            for module in modules:
                pieces = module.split(".")
                for base in (root, source.parent):
                    candidates = [base.joinpath(*pieces).with_suffix(".py"), base.joinpath(*pieces, "__init__.py")]
                    candidates.extend(base.joinpath(*pieces[:i], "__init__.py") for i in range(1, len(pieces)))
                    for path in candidates:
                        if path.is_file() and path.resolve() not in declared:
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
            calls = {token.value for i, token in enumerate(tokens[:-1]) if token.kind == "identifier" and tokens[i + 1].value == "("}
            local = {matlab_code_checks.function_signature(row)[0] for row in matlab_code_checks.statements(tokens) if row[0].value == "function"}
            for name in calls - local:
                for base in (root, source.parent):
                    path = base / (name + ".m")
                    if path.is_file() and path.resolve() not in declared:
                        issues.append(f"项目MATLAB依赖未声明: {path.relative_to(root).as_posix()}")
    return list(dict.fromkeys(issues))


def requires_bundle_binding(root: Path, entry: Mapping[str, Any], stage: str) -> bool:
    """Detect the new contract, without granting binding or legacy acceptance."""
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
            return config.get("run_receipt_protocol_version") == "1.1.0"
    except (OSError, ValueError, SyntaxError):
        pass
    return False


def validate_stage_binding(root: Path, entry: Mapping[str, Any], stage: str, *,
                           require_delivered: bool = True, require_validated: bool = False) -> list[str]:
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
    field = "code" if stage == "primary" else "result_analysis_code"
    hash_field = "primary_code_sha256" if stage == "primary" else "analysis_code_sha256"
    relative = str(entry.get(field) or "")
    if not relative:
        return [f"{stage}缺少已交付入口路径"] if selection else []
    try:
        path = _relative_path(root, relative)
        if not path.is_file():
            raise StageCodeError(f"{stage}入口文件不存在")
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if entry.get(hash_field) and actual_hash != str(entry[hash_field]).lower():
            raise StageCodeError(f"{stage}入口SHA-256与已交付代码不一致")
        if not selection and path.suffix == ".py":
            # Preserve historical source-only checks, including old non-config fixtures.
            try:
                _, config = parse_stage_config(path, "python")
            except (ValueError, SyntaxError):
                return []
            if config.get("run_receipt_protocol_version") != "1.1.0":
                return []
        else:
            _, config = parse_stage_config(path)
        identity = script_identity(path)
        if require_delivered and not re.fullmatch(r"[0-9a-fA-F]{64}", str(entry.get(hash_field, ""))):
            raise StageCodeError(f"{stage}新协议缺少已交付入口SHA-256")
        backend = selection.get("backend")
        if not isinstance(backend, str) or backend not in BACKENDS or backend != identity.backend or config.get("solver_backend") != backend:
            raise StageCodeError(f"{stage}状态、入口及RUN_CONFIG后端不一致")
        if config.get("stage") != stage or config.get("problem_name") != identity.problem_name:
            raise StageCodeError(f"{stage}配置与目录身份不一致")
        if config.get("run_receipt_protocol_version") != "1.1.0":
            raise StageCodeError("新后端绑定必须使用RUN_RECEIPT 1.1.0")
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
