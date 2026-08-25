#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if old not in text:
        if new in text:
            return
        raise RuntimeError(f"test migration anchor missing in {path}: {old!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    patch(
        "scripts/README.md",
        "- `resolve_runtime.py`：默认 assured runtime 入口。在兼容旧 plan 字段的基础上，可选读取 `--project-root` / `--question` 恢复 current project state，验证 artifact hash，输出 intent provenance、ambiguity、declarative contract closure、authority fingerprint 与 `runtime_plan/assurance`。",
        "- `resolve_runtime.py`：默认 assured runtime 入口。在兼容旧 plan 字段及 `objective / structures / capabilities` 分类轴的基础上，可选读取 `--project-root` / `--question` 恢复 current project state，验证 artifact hash，输出 intent provenance、ambiguity、declarative contract closure、authority fingerprint 与 `runtime_plan/assurance`。",
    )

    old = '''        for token in (\n            "core/bootstrap.yaml", "core/workflow_router.yaml", "core/hsk_core_policy.md",\n            "scripts/resolve_workflow.py", "core/writing_reasoning_contract.yaml",\n            "模型论文框架.md", "legacy/",\n        ):\n            self.assertIn(token, block)\n'''
    new = '''        bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))\n        runtime_resolver = bootstrap["startup_contract"]["resolver"]\n        for token in (\n            "core/bootstrap.yaml", "core/workflow_router.yaml", "core/hsk_core_policy.md",\n            runtime_resolver, "core/writing_reasoning_contract.yaml",\n            "模型论文框架.md", "legacy/",\n        ):\n            self.assertIn(token, block)\n        legacy_command = (bootstrap.get("entrypoints") or {}).get("resolve_legacy")\n        if legacy_command:\n            legacy_resolver = legacy_command.split()[1]\n            self.assertIn(legacy_resolver, ROOT_SKILL.read_text(encoding="utf-8"))\n            self.assertIn(legacy_resolver, PACKAGED_SKILL.read_text(encoding="utf-8"))\n'''
    patch("tests/test_v752_entrypoint_parity.py", old, new)

    patch(
        "tests/test_v712_runtime_assurance.py",
        '        plan = self.runtime.resolve_runtime(request="请审题并建模")',
        '        plan = self.runtime.resolve_runtime(request="请审题并建模", objective="optimization")',
    )


if __name__ == "__main__":
    main()
