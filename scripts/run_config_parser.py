#!/usr/bin/env python3
"""Shared static reader for embedded stage RUN_CONFIG declarations.

This module owns only the syntax-level extraction shared by delivery and
returned-execution validators. Field policy remains in the callers and
core/user_execution_contract.yaml.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any

CONFIG_NAMES = ("RUN_CONFIG", "FULL_FIDELITY_CONFIG", "FULL_RUN_CONFIG")


@dataclass(frozen=True)
class EmbeddedConfigMessages:
    non_mapping: str
    missing: str
    multiple: str


DELIVERY_MESSAGES = EmbeddedConfigMessages(
    non_mapping="{name}必须为字典常量",
    missing="缺少RUN_CONFIG字典常量（旧项目可只读FULL_FIDELITY_CONFIG/FULL_RUN_CONFIG）",
    multiple="同一脚本只能定义一个受支持运行配置，当前检测到: {names}",
)
RETURNED_EXECUTION_MESSAGES = EmbeddedConfigMessages(
    non_mapping="已交付阶段代码中的{name}必须为字典常量",
    missing="已交付阶段代码缺少RUN_CONFIG字典常量（旧项目可只读FULL_FIDELITY_CONFIG/FULL_RUN_CONFIG）",
    multiple="已交付阶段代码只能定义一个受支持运行配置，当前检测到: {names}",
)


def parse_embedded_config(
    text: str,
    *,
    messages: EmbeddedConfigMessages,
    backend: str = "python",
) -> tuple[str, dict[str, Any]]:
    """Return exactly one supported top-level literal config, fail closed otherwise."""
    if backend == "matlab":
        from matlab_code_checks import parse_config
        return parse_config(text)
    if backend != "python":
        raise ValueError(f"不支持的代码后端: {backend}")
    tree = ast.parse(text)
    found: list[tuple[str, dict[str, Any]]] = []
    declarations: list[ast.AST] = []
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        matched = [
            target.id
            for target in targets
            if isinstance(target, ast.Name) and target.id in CONFIG_NAMES
        ]
        if not matched:
            continue
        value = ast.literal_eval(node.value)
        if not isinstance(value, dict):
            raise ValueError(messages.non_mapping.format(name=matched[0]))
        found.extend((name, value) for name in matched)
        declarations.append(node)
    if not found:
        raise ValueError(messages.missing)
    if len(found) != 1:
        names = ", ".join(name for name, _ in found)
        raise ValueError(messages.multiple.format(names=names))
    if found[0][1].get("run_receipt_protocol_version") == "1.1.0":
        def root_name(node: ast.AST) -> str | None:
            while isinstance(node, (ast.Attribute, ast.Subscript)):
                node = node.value
            return node.id if isinstance(node, ast.Name) else None
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr)) and node not in declarations:
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if any(root_name(target) in CONFIG_NAMES for target in targets):
                    raise ValueError("RUN_CONFIG禁止局部重定义或后续覆盖")
            if isinstance(node, (ast.Attribute, ast.Subscript)) and isinstance(node.ctx, (ast.Store, ast.Del)) and root_name(node) in CONFIG_NAMES:
                raise ValueError("RUN_CONFIG禁止后续覆盖或删除字段")
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and root_name(node.func.value) in CONFIG_NAMES
                    and node.func.attr in {"update", "setdefault", "pop", "popitem", "clear", "__setitem__", "__delitem__"}):
                raise ValueError("RUN_CONFIG禁止后续动态修改")
        for node in ast.walk(declarations[0]):
            if isinstance(node, ast.Dict):
                keys = [ast.literal_eval(key) for key in node.keys if key is not None]
                if len(keys) != len(set(keys)):
                    raise ValueError("RUN_CONFIG字典字段重复")
    return found[0]
