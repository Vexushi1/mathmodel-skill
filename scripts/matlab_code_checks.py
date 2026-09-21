"""Restricted MATLAB source inspection; never evaluates task code.

The portable lexer recognizes source structure, not the full MATLAB language.
Formal delivery additionally requires the native Code Analyzer. Policy belongs
to core/code_quality_contract.yaml and core/user_execution_contract.yaml.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

FORBIDDEN_EXECUTION_CALLS = {
    "eval", "evalin", "assignin", "run", "str2func", "feval", "builtin", "dbstop", "keyboard",
    "addpath", "rmpath", "savepath", "restoredefaultpath", "mlock", "system", "unix", "dos", "pyrun", "pyrunfile",
}


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    line: int
    start: int
    end: int


def tokenize(text: str) -> list[Token]:
    """Tokenize strings, comments, continuation and transpose without executing."""
    tokens: list[Token] = []
    i, line = 0, 1
    while i < len(text):
        start, source_line = i, line
        ch = text[i]
        if ch in " \t\r\ufeff":
            i += 1
            continue
        if ch == "\n":
            tokens.append(Token("newline", "\n", line, i, i + 1))
            i, line = i + 1, line + 1
            continue
        if text.startswith("...", i):
            end = text.find("\n", i)
            if end < 0:
                break
            i, line = end + 1, line + 1
            continue
        if ch == "%":
            if text.startswith("%{", i) and not text[text.rfind("\n", 0, i) + 1:i].strip():
                opening_end = text.find("\n", i)
                if opening_end < 0 or text[i + 2:opening_end].strip():
                    raise ValueError("MATLAB块注释起始标记必须独占一行")
                match = re.search(r"(?m)^\s*%}\s*$", text[opening_end + 1:])
                if not match:
                    raise ValueError("MATLAB块注释未闭合")
                i = opening_end + 1 + match.end()
                line += text[start:i].count("\n")
            else:
                i = text.find("\n", i)
                if i < 0:
                    break
            continue
        previous = tokens[-1] if tokens else None
        transpose = (
            ch == "'" and previous is not None and previous.end == i
            and (previous.kind in {"identifier", "number", "string"} or previous.value in {")", "]", "}", "."})
        )
        if ch in "'\"" and not transpose:
            quote, value = ch, []
            i += 1
            while i < len(text):
                if text[i] == "\n":
                    raise ValueError(f"MATLAB第{source_line}行字符串未闭合")
                if text[i] == quote:
                    if i + 1 < len(text) and text[i + 1] == quote:
                        value.append(quote)
                        i += 2
                        continue
                    i += 1
                    break
                value.append(text[i])
                i += 1
            else:
                raise ValueError(f"MATLAB第{source_line}行字符串未闭合")
            tokens.append(Token("char" if quote == "'" else "string", "".join(value), source_line, start, i))
            continue
        match = re.match(r"[A-Za-z_][A-Za-z_0-9]*", text[i:])
        if match:
            i += len(match[0])
            tokens.append(Token("identifier", match[0], line, start, i))
            continue
        match = re.match(r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eEdD][+-]?\d+)?", text[i:])
        if match:
            i += len(match[0])
            tokens.append(Token("number", match[0], line, start, i))
            continue
        symbol = next((op for op in ("==", "~=", "<=", ">=", "&&", "||", ".'", ".*", "./", ".^", ".\\") if text.startswith(op, i)), ch)
        i += len(symbol)
        tokens.append(Token("symbol", symbol, line, start, i))
    return tokens


def statements(tokens: list[Token]) -> list[list[Token]]:
    result: list[list[Token]] = []
    current: list[Token] = []
    stack: list[str] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for token in tokens:
        if token.kind == "symbol" and token.value in "([{":
            stack.append(token.value)
        elif token.kind == "symbol" and token.value in pairs:
            if not stack or stack.pop() != pairs[token.value]:
                raise ValueError(f"MATLAB第{token.line}行括号不匹配")
        if not stack and token.value in {";", "\n", ","}:
            if current:
                result.append(current)
                current = []
        elif token.kind != "newline":
            current.append(token)
    if stack:
        raise ValueError("MATLAB括号未闭合")
    if current:
        result.append(current)
    return result


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", key) or len(key) > 63:
            raise ValueError(f"MATLAB配置JSON字段名不合法: {key}")
        if key in value:
            raise ValueError(f"MATLAB配置JSON字段重复: {key}")
        value[key] = item
    return value


def parse_config(text: str) -> tuple[str, dict[str, Any]]:
    rows = statements(tokenize(text))
    if not rows or rows[0][0].value != "function":
        raise ValueError("MATLAB阶段代码必须为主函数文件")
    if len(rows) < 2 or rows[1][0].value != "RUN_CONFIG":
        raise ValueError("MATLAB主函数首条语句必须声明唯一RUN_CONFIG")
    config_row = rows[1]
    values = [token.value for token in config_row]
    if values[:4] != ["RUN_CONFIG", "=", "jsondecode", "("] or values[-1:] != [")"]:
        raise ValueError("MATLAB RUN_CONFIG仅支持jsondecode纯字符字面量")
    body = config_row[4:-1]
    if body and body[0].value == "[" and body[-1].value == "]":
        body = body[1:-1]
    if not body or any(token.kind != "char" for token in body):
        raise ValueError("MATLAB配置禁止变量、表达式或非字符字面量拼接")
    for row in rows[2:]:
        if row[0].value == "function" and function_signature(row)[0] == "jsondecode":
            raise ValueError("MATLAB配置不得用本地函数遮蔽jsondecode")
        assignment = next((i for i, token in enumerate(row) if token.value == "="), None)
        if assignment is not None and any(token.value in {"RUN_CONFIG", "FULL_RUN_CONFIG", "FULL_FIDELITY_CONFIG"} for token in row[:assignment]):
            raise ValueError("MATLAB运行配置禁止重复定义或后续覆盖")
        if row[0].value in {"global", "persistent", "clear"} and any(token.value == "RUN_CONFIG" for token in row):
            raise ValueError("MATLAB运行配置禁止动态清除或全局覆盖")
    try:
        config = json.loads("".join(token.value for token in body), object_pairs_hook=_json_object,
                            parse_constant=lambda item: (_ for _ in ()).throw(ValueError(f"非法JSON数值: {item}")))
    except json.JSONDecodeError as exc:
        raise ValueError(f"MATLAB RUN_CONFIG JSON错误: {exc}") from exc
    if not isinstance(config, dict):
        raise ValueError("MATLAB RUN_CONFIG JSON根必须为对象")
    def check_values(value: Any) -> None:
        if isinstance(value, dict):
            for item in value.values():
                check_values(item)
        elif isinstance(value, list):
            for item in value:
                check_values(item)
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            if not math.isfinite(value) or (isinstance(value, int) and abs(value) > 2**53 - 1):
                raise ValueError("MATLAB配置数值必须有限且整数处于精确表示范围")
    check_values(config)
    return "RUN_CONFIG", config


def function_signature(row: list[Token]) -> tuple[str, int]:
    values = [token.value for token in row]
    offset = values.index("=") + 1 if "=" in values else 1
    if offset >= len(row) or row[offset].kind != "identifier":
        raise ValueError("MATLAB函数声明无法解析")
    parameters = 0
    if "(" in values[offset + 1:]:
        start = values.index("(", offset + 1)
        stop = values.index(")", start)
        parameters = sum(token.kind == "identifier" or token.value == "~" for token in row[start + 1:stop])
    return row[offset].value, parameters


def literal_data_reader_paths(text: str) -> list[str]:
    try:
        tokens = tokenize(text)
    except ValueError:
        return []  # Syntax errors are reported by the source-quality gate.
    readers = {"readtable", "readcell", "readmatrix", "load", "fopen", "xlsread", "importdata"}
    return list(dict.fromkeys(tokens[i + 2].value for i, token in enumerate(tokens[:-2])
                             if token.value in readers and tokens[i + 1].value == "("
                             and tokens[i + 2].kind in {"char", "string"}))


def matlab_code_findings(text: str, config: Mapping[str, Any] | None = None, *,
                         contract: Mapping[str, Any], filename: str | None = None
                         ) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    metrics: dict[str, Any] = {"native_analysis_status": "unverified", "nonblank_lines": sum(bool(line.strip()) for line in text.splitlines())}
    try:
        rows = statements(tokenize(text))
    except ValueError as exc:
        return [str(exc)], warnings, metrics
    if not rows or rows[0][0].value != "function":
        return ["MATLAB正式代码必须具有主函数入口"], warnings, metrics
    line_policy = contract["line_count"]
    exemption = (config or {}).get("code_quality_exemption", {})
    exempt = isinstance(exemption, dict) and exemption.get("enabled") is True and len(str(exemption.get("reason", "")).strip()) >= int(line_policy["exemption_reason_min_chars"])
    lines = metrics["nonblank_lines"]
    if lines > line_policy["exemption_max"] or (lines > line_policy["hard_max"] and not exempt):
        errors.append("MATLAB代码行数超过工程质量硬上限")
    elif lines > line_policy["target_max"]:
        warnings.append("MATLAB代码行数超过目标，应按合同精简")
    stack: list[tuple[str, dict[str, Any] | None]] = []
    functions: list[dict[str, Any]] = []
    plotting = {"figure", "plot", "scatter", "bar", "histogram", "heatmap", "surf", "mesh", "exportgraphics", "saveas", "sgtitle"}
    for row in rows:
        head = row[0].value
        if head == "function":
            try:
                name, parameters = function_signature(row)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            record = {"name": name, "line": row[0].line, "parameters": parameters, "complexity": 1}
            functions.append(record)
            stack.append((head, record))
        elif head in {"if", "for", "parfor", "while", "switch", "try", "spmd", "arguments"}:
            stack.append((head, None))
        elif head == "end":
            if not stack:
                errors.append(f"MATLAB第{row[0].line}行end没有对应结构")
            else:
                _, record = stack.pop()
                if record is not None:
                    record["lines"] = row[0].line - record["line"] + 1
        elif head in {"classdef", "methods", "properties"}:
            errors.append("本期MATLAB阶段代码不支持classdef结构")
        for _, record in reversed(stack):
            if record is not None:
                record["complexity"] += int(head in {"if", "elseif", "for", "parfor", "while", "case", "catch"}) + sum(token.value in {"&&", "||"} for token in row)
                break
        if head == "catch":
            index = rows.index(row)
            following = rows[index + 1] if index + 1 < len(rows) else []
            if not following or following[0].value == "end":
                errors.append("MATLAB禁止空catch吞掉异常")
        for i, token in enumerate(row):
            if token.kind != "identifier":
                continue
            is_call = i + 1 < len(row) and row[i + 1].value == "("
            if token.value in FORBIDDEN_EXECUTION_CALLS and (is_call or i == 0):
                errors.append(f"MATLAB正式代码不支持动态执行/路径污染: {token.value}")
            if token.value == "py" and i + 1 < len(row) and row[i + 1].value == ".":
                errors.append("MATLAB求解阶段不支持启动Python后端")
            if token.value in plotting and is_call:
                errors.append(f"求解阶段禁止正式绘图调用: {token.value}")
    if stack:
        errors.append("MATLAB控制结构或函数缺少显式end")
    names = [item["name"] for item in functions]
    if len(names) != len(set(names)):
        errors.append("MATLAB函数名重复")
    if filename and names and names[0] != Path(filename).stem:
        errors.append("MATLAB主函数名必须与入口文件名一致")
    for record in functions:
        for metric, policy_key in (("lines", "function_size"), ("parameters", "parameter_count"), ("complexity", "complexity")):
            value = record.get(metric, 0)
            policy = contract[policy_key]
            if value > policy["hard_max"]:
                errors.append(f"MATLAB函数{record['name']}的{metric}={value}超过硬上限")
            elif value > policy.get("target_max", policy.get("warning_max", policy["hard_max"])):
                warnings.append(f"MATLAB函数{record['name']}的{metric}={value}超过目标")
    metrics.update(function_count=len(functions), functions=functions)
    return list(dict.fromkeys(errors)), list(dict.fromkeys(warnings)), metrics


def _diagnostic_excerpt(value: str | bytes | None, limit: int = 2000) -> str:
    """Keep bounded process evidence without copying credential assignments."""
    text = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value or "")
    text = re.sub(r"(?i)\bBearer\s+[^\s,;]+", "Bearer [REDACTED]", text)
    text = re.sub(
        r"(?i)(\b[\w.-]*(?:token|password|passwd|secret|api[_-]?key|authorization)[\w.-]*[\"']?\s*[:=]\s*)"
        r"(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)",
        r"\1[REDACTED]", text,
    ).strip()
    if len(text) > limit:
        marker = "\n...[truncated]...\n"
        keep = (limit - len(marker)) // 2
        text = text[:keep] + marker + text[-keep:]
    return text


def _process_diagnostics(stdout: str | bytes | None, stderr: str | bytes | None) -> list[str]:
    return [f"MATLAB Code Analyzer {label}: {excerpt}" for label, value in (("stdout", stdout), ("stderr", stderr))
            if (excerpt := _diagnostic_excerpt(value))]


def native_code_analysis(path: Path, executable: str | None = None, *, timeout: int = 180) -> dict[str, Any]:
    """Run factory Code Analyzer on source, never run or import the stage entrypoint."""
    command = executable or shutil.which("matlab")
    if not command:
        return {"status": "unverified", "issues": ["MATLAB Code Analyzer不可用"], "warnings": []}
    path = path.resolve()
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    quoted_path = path.as_posix().replace("'", "''")
    with tempfile.TemporaryDirectory(prefix="hsk-matlab-analysis-") as directory:
        output = Path(directory) / "analysis.json"
        quoted_output = output.as_posix().replace("'", "''")
        expression = (
            f"a=codeIssues('{quoted_path}',CodeAnalyzerConfiguration='factory');"
            "p=struct('release',string(a.Release),'issues',table2struct(a.Issues),"
            "'suppressed',table2struct(a.SuppressedIssues));"
            f"p.complexity=checkcode('{quoted_path}','-id','-cyc','-notok','-fullpath');"
            f"f=fopen('{quoted_output}','w','n','UTF-8');assert(f~=-1);"
            "fprintf(f,'%s',jsonencode(p));fclose(f);"
        )
        result = None
        try:
            result = subprocess.run([str(command), "-batch", expression], cwd=directory,
                                    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False)
            if result.returncode or not output.is_file():
                reason = f"MATLAB Code Analyzer运行失败 (exit_code={result.returncode}, report_exists={output.is_file()})"
                return {"status": "unverified", "issues": [reason, *_process_diagnostics(result.stdout, result.stderr)], "warnings": []}
            payload = json.loads(output.read_text(encoding="utf-8"))
        except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
            if isinstance(exc, subprocess.TimeoutExpired):
                reason = f"TimeoutExpired after {timeout}s"
                stdout, stderr = exc.stdout, exc.stderr
            else:
                reason = f"{type(exc).__name__}: {_diagnostic_excerpt(str(exc))}"
                stdout, stderr = (result.stdout, result.stderr) if result is not None else (None, None)
            return {"status": "unverified", "issues": [f"MATLAB Code Analyzer未完成: {reason}",
                    *_process_diagnostics(stdout, stderr)], "warnings": []}
    if before != hashlib.sha256(path.read_bytes()).hexdigest():
        return {"status": "failed", "issues": ["MATLAB分析期间源文件发生改变"], "warnings": []}
    errors, warnings = [], []
    for group in ("issues", "suppressed"):
        records = payload.get(group) or []
        if isinstance(records, dict):
            records = [records]
        for record in records:
            message = f"MATLAB {record.get('CheckID', 'unknown')} L{record.get('LineStart', '?')}: {record.get('Description', '')}"
            (errors if str(record.get("Severity", "")).lower() == "error" else warnings).append(message)
    complexity = payload.get("complexity") or []
    if isinstance(complexity, dict):
        complexity = [complexity]
    metrics: list[dict[str, int]] = []
    for record in complexity:
        if record.get("id") == "CABE":
            # CABE identifies the per-function metric; only its final integer is
            # consumed, not version-dependent English wording or function names.
            numbers = re.findall(r"\d+", str(record.get("message", "")))
            if numbers:
                metrics.append({"line": int(record["line"]), "value": int(numbers[-1])})
            else:
                errors.append("MATLAB CABE复杂度诊断未提供可读数值")
    return {"status": "failed" if errors else "passed", "issues": errors, "warnings": warnings,
            "source_sha256": before, "release": payload.get("release"), "complexity_metrics": metrics,
            "complexity": complexity}
