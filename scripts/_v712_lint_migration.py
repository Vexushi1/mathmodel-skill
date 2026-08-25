#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "lint_skill_checks.py"


def replace_once(text: str, old: str, new: str) -> str:
    if old not in text:
        if new in text:
            return text
        raise RuntimeError(f"lint migration anchor missing: {old!r}")
    return text.replace(old, new, 1)


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '    "core/project_state.schema.yaml", "core/compile_profiles.yaml",\n',
        '    "core/project_state.schema.yaml", "core/compile_profiles.yaml", "core/runtime_assurance_contract.yaml",\n',
    )
    text = replace_once(
        text,
        '    "scripts/resolve_workflow.py", "scripts/validate_semantic_governance.py", "scripts/validate_model_approval.py", "scripts/sync_project.py",\n',
        '    "scripts/resolve_runtime.py", "scripts/runtime_assurance.py", "scripts/resolve_workflow.py", "scripts/validate_semantic_governance.py", "scripts/validate_model_approval.py", "scripts/sync_project.py",\n',
    )
    old = '''    blocks: dict[str, str | None] = {}\n    required_tokens = (\n        "core/bootstrap.yaml", "core/workflow_router.yaml", "core/hsk_core_policy.md",\n        "scripts/resolve_workflow.py", "core/writing_reasoning_contract.yaml",\n        "模型论文框架.md", "legacy/",\n    )\n'''
    new = '''    blocks: dict[str, str | None] = {}\n    startup = bootstrap.get("startup_contract", {}) or {}\n    runtime_resolver = str(startup.get("resolver", "")).strip()\n    entrypoints = bootstrap.get("entrypoints", {}) or {}\n    legacy_command = str(entrypoints.get("resolve_legacy", "")).strip()\n    legacy_parts = legacy_command.split()\n    legacy_resolver = legacy_parts[1] if len(legacy_parts) >= 2 else ""\n    if not runtime_resolver:\n        errors.append("bootstrap startup_contract.resolver is required")\n    required_tokens = (\n        "core/bootstrap.yaml", "core/workflow_router.yaml", "core/hsk_core_policy.md",\n        runtime_resolver, "core/writing_reasoning_contract.yaml",\n        "模型论文框架.md", "legacy/",\n    )\n'''
    text = replace_once(text, old, new)
    old = '''        for token in forbidden_tokens:\n            if token in block:\n                errors.append(f"skill entrypoint must not depend on compatibility pointer: {origin} -> {token}")\n\n    root_block = blocks.get("SKILL.md")\n'''
    new = '''        for token in forbidden_tokens:\n            if token in block:\n                errors.append(f"skill entrypoint must not depend on compatibility pointer: {origin} -> {token}")\n        if legacy_resolver and legacy_resolver not in text_value:\n            errors.append(f"skill entrypoint legacy resolver pointer missing: {origin} -> {legacy_resolver}")\n\n    root_block = blocks.get("SKILL.md")\n'''
    text = replace_once(text, old, new)
    PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
