"""Bounded lexical source observations for conformance; no imports of task code.

These observations cannot prove mathematical meaning, runtime activation or
algebraic equivalence. The limits and candidate families belong to the contract.
"""
from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass
from typing import Any

import matlab_code_checks as matlab


@dataclass
class Symbol:
    name: str
    fragment: str
    line: int
    end_line: int
    node: Any

    def summary(self) -> dict[str, Any]:
        return {"symbol": self.name, "sha256": hashlib.sha256(self.fragment.encode("utf-8")).hexdigest(),
                "line": self.line, "end_line": self.end_line}


def _candidate(path: str, symbol: str, line: int, column: int, call: str) -> dict[str, Any]:
    key = f"{path}\0{symbol}\0{line}\0{column}\0{call}".encode("utf-8")
    return {"operation_id": "OP-" + hashlib.sha256(key).hexdigest()[:16],
            "path": path, "symbol": symbol, "line": line, "call": call,
            "meaning": "lexical_candidate_not_verified_mathematical_operation"}


def _bounded_ast(tree: ast.AST, limits: dict) -> None:
    stack, count = [(tree, 0)], 0
    while stack:
        node, depth = stack.pop()
        count += 1
        if count > limits["source_ast_nodes"] or depth > limits["source_ast_depth"]:
            raise ValueError("source AST budget exceeded")
        stack.extend((child, depth + 1) for child in ast.iter_child_nodes(node))


def python_inventory(path: str, text: str, contract: dict) -> tuple[list[Symbol], list[dict], list[str]]:
    tree = ast.parse(text)
    _bounded_ast(tree, contract["limits"])
    lines = text.splitlines(keepends=True)
    symbols = [Symbol("<module>", text, 1, len(lines), tree)]
    origins: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                origins.setdefault(alias.asname or alias.name.split(".")[0], set()).add(
                    alias.name if alias.asname else alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                origins.setdefault(alias.asname or alias.name, set()).add(node.module + "." + alias.name)

    def names(node: ast.AST) -> set[str]:
        if isinstance(node, ast.Name):
            return origins.get(node.id, {node.id})
        if isinstance(node, ast.Attribute):
            return {prefix + "." + node.attr for prefix in names(node.value)}
        return set()

    candidates: list[dict] = []
    allowed = set(contract["coverage"]["python_reverse_calls"])

    def visit(node: ast.AST, scope: str) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            scope = node.name if scope == "<module>" else scope + "." + node.name
            start = min([node.lineno, *(item.lineno for item in node.decorator_list)])
            symbols.append(Symbol(scope, "".join(lines[start - 1:node.end_lineno]), start, node.end_lineno, node))
        if isinstance(node, ast.Call):
            for call in sorted(names(node.func) & allowed):
                candidates.append(_candidate(path, scope, node.lineno, node.col_offset, call))
        for child in ast.iter_child_nodes(node):
            visit(child, scope)
    visit(tree, "<module>")
    return symbols, candidates, []


def matlab_inventory(path: str, text: str, contract: dict) -> tuple[list[Symbol], list[dict], list[str]]:
    rows = matlab.statements(matlab.tokenize(text))
    symbols = [Symbol("<module>", text, 1, len(text.splitlines()), rows)]
    candidates, limitations = [], []
    controls = {"if", "for", "parfor", "while", "switch", "try", "spmd", "arguments"}
    stack: list[str] = []
    active: tuple[str, int, int] | None = None
    for index, row in enumerate(rows):
        head = row[0].value
        if head == "classdef":
            limitations.append("MATLAB class structure is outside the verified flat-function scope")
        if head == "function":
            if active is not None or stack:
                limitations.append("MATLAB nested or implicitly terminated functions need review")
                # No anchor from an uncertain body may receive structural verification.
                return symbols, candidates, limitations
            name, _ = matlab.function_signature(row)
            active = (name, index, row[0].start)
            stack.append("function")
        elif head in controls:
            stack.append(head)
        elif head == "end":
            if not stack:
                limitations.append("unmatched MATLAB end")
            else:
                ending = stack.pop()
                if ending == "function" and active is not None:
                    name, start_row, start = active
                    stop = text.find("\n", row[-1].end)
                    stop = len(text) if stop < 0 else stop + 1
                    symbols.append(Symbol(name, text[start:stop], rows[start_row][0].line,
                                          row[-1].line, rows[start_row:index + 1]))
                    active = None
        scope = active[0] if active else "<module>"
        for i, token in enumerate(row[:-1]):
            if token.value in contract["coverage"]["matlab_reverse_calls"] and row[i + 1].value == "(":
                candidates.append(_candidate(path, scope, token.line, token.start, token.value))
    if active is not None or stack:
        limitations.append("MATLAB function/control boundaries are not explicitly closed")
    return symbols, candidates, list(dict.fromkeys(limitations))


def inspect_source(path: str, text: str, contract: dict) -> tuple[list[Symbol], list[dict], list[str]]:
    return python_inventory(path, text, contract) if path.endswith(".py") else matlab_inventory(path, text, contract)


def _arithmetic_ast(text: str, limits: dict) -> str:
    node = ast.parse(text, mode="eval")
    _bounded_ast(node, limits)
    allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Name, ast.Load, ast.Constant,
               ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.USub, ast.UAdd)
    for part in ast.walk(node):
        if not isinstance(part, allowed):
            raise ValueError("expression is outside the arithmetic comparison subset")
        if isinstance(part, ast.Constant) and (isinstance(part.value, bool) or not isinstance(part.value, (int, float))):
            raise ValueError("non-numerical constant is not an arithmetic reference")
    return ast.dump(node.body, include_attributes=False)


def compare_expression(symbol: Symbol, expected: str, backend: str, anchor: dict, limits: dict) -> tuple[str, str]:
    """Compare only a declared approved reference with a small literal source shape."""
    if backend == "python":
        node = symbol.node
        if not isinstance(node, ast.FunctionDef) or node.decorator_list:
            return "needs_review", "expression requires an undecorated flat Python function"
        body = list(node.body)
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
            body = body[1:]
        if len(body) != 1 or not isinstance(body[0], ast.Return) or body[0].value is None:
            return "needs_review", "expression requires one static return, without hidden assignments"
        actual = ast.unparse(body[0].value)
        try:
            equal = _arithmetic_ast(actual, limits) == _arithmetic_ast(expected, limits)
        except (ValueError, SyntaxError, RecursionError):
            return "needs_review", "reference or implementation is outside the arithmetic subset"
    else:
        rows = symbol.node
        target = anchor.get("expression_target")
        if not target or not rows or rows[0][0].value != "function":
            return "needs_review", "MATLAB expression requires an explicit output target and flat function"
        # A single assignment is intentionally narrower than general MATLAB expressions.
        header = [token.value for token in rows[0]]
        if len(header) < 4 or header[1:3] != [target, "="]:
            return "needs_review", "MATLAB target is not the declared single function output"
        body = rows[1:-1]
        if len(body) != 1 or len(body[0]) < 3 or [t.value for t in body[0][:2]] != [target, "="]:
            return "needs_review", "MATLAB expression requires one simple assignment"
        actual_tokens, expected_tokens = body[0][2:], matlab.tokenize(expected)
        allowed = {"+", "-", "*", "/", "^", ".*", "./", ".^", "(", ")"}
        def values(tokens):
            result = []
            for i, token in enumerate(tokens):
                if token.kind not in {"identifier", "number"} and token.value not in allowed:
                    raise ValueError("unsupported arithmetic token")
                if token.kind == "identifier" and i + 1 < len(tokens) and tokens[i + 1].value == "(":
                    raise ValueError("function calls/indexing require semantic review")
                result.append(token.value)
            return result
        try:
            equal = values(actual_tokens) == values(expected_tokens)
        except ValueError:
            return "needs_review", "MATLAB expression is outside the arithmetic subset"
    return ("matched", "syntactic reference matched; mathematical equivalence is not established") if equal else (
        "different", "syntactic expression differs; adjudicate a legal transformation or restore the approved expression")
