"""Conservative syntax checks for unverified Python execution references.

This is a source-provenance gate, not a Python sandbox. Inspect capability values
at their origin, before assignment/callback/container aliases can hide a Call.
Only stage_code's modern source-bundle path invokes this checker.
"""
from __future__ import annotations

import ast

_DYNAMIC_NAMES = frozenset({
    "__import__", "eval", "exec", "import_module", "reload", "run_path",
    "run_module", "spec_from_file_location", "spec_from_loader", "module_from_spec",
    "SourceFileLoader", "SourcelessFileLoader", "ExtensionFileLoader",
    "load_module", "exec_module",
})
_NAMESPACES = frozenset({
    "importlib", "importlib.util", "importlib.machinery", "runpy", "builtins",
    "subprocess", "os", "matlab.engine",
})
_DYNAMIC = "新源码闭包不支持动态Python代码加载"
_PROCESS = "求解阶段不支持shell/跨后端进程启动"
_NAMESPACE = "新源码闭包不支持执行命名空间的间接传递/反射"


def execution_reference_issues(tree: ast.AST) -> list[str]:
    """Reject forbidden references, including those not immediately called.

    Import origins are an over-approximation: an unrelated import in a sibling
    scope must not erase a dangerous origin. Strings/comments have no Load node.
    Ordinary static imports, numerical callables and os.path remain supported.
    """
    nodes = list(ast.walk(tree))
    parents = {child: node for node in nodes for child in ast.iter_child_nodes(node)}
    origins: dict[str, set[str]] = {}
    imported_values: set[str] = set()
    wildcard_namespace = False
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name.split(".")[0]
                origin = alias.name if alias.asname else local
                origins.setdefault(local, set()).add(origin)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            for alias in node.names:
                wildcard_namespace |= alias.name == "*" and node.module in _NAMESPACES
                origin = node.module + "." + alias.name
                imported_values.add(origin)
                origins.setdefault(alias.asname or alias.name, set()).add(origin)

    def qualified(node: ast.AST) -> set[str]:
        if isinstance(node, ast.Name):
            return origins.get(node.id, {node.id})
        if isinstance(node, ast.Attribute):
            return {prefix + "." + node.attr for prefix in qualified(node.value)}
        return set()

    issues: list[str] = [_NAMESPACE] if wildcard_namespace else []

    def inspect(names: set[str]) -> None:
        for name in sorted(names):
            if name.rsplit(".", 1)[-1] in _DYNAMIC_NAMES:
                issues.append(_DYNAMIC)
            if (name.startswith(("subprocess.", "matlab.engine."))
                    or name in {"os.system", "os.popen", "os.startfile"}
                    or name.startswith(("os.exec", "os.spawn"))):
                issues.append(_PROCESS)

    inspect(imported_values)
    for node in nodes:
        if not isinstance(node, (ast.Name, ast.Attribute)) or not isinstance(node.ctx, ast.Load):
            continue
        names = qualified(node)
        # Keep the existing conservative leaf-name boundary even for a value
        # returned by an expression whose qualified origin cannot be resolved.
        leaf = node.id if isinstance(node, ast.Name) else node.attr
        inspect(names | {leaf})
        if leaf == "__builtins__":
            issues.append(_NAMESPACE)
        parent = parents.get(node)
        attribute_base = isinstance(parent, ast.Attribute) and parent.value is node
        if not attribute_base and names & _NAMESPACES:
            issues.append(_NAMESPACE)
        if isinstance(node, ast.Attribute) and node.attr == "__dict__":
            if qualified(node.value) & _NAMESPACES:
                issues.append(_NAMESPACE)
    return list(dict.fromkeys(issues))
