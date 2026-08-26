from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def bootstrap() -> dict:
    return yaml.safe_load(read("core/bootstrap.yaml")) or {}


class DefaultRuntimeReadPathTests(unittest.TestCase):
    def test_bootstrap_default_resolver_is_assured_runtime(self):
        data = bootstrap()
        self.assertEqual(
            data.get("startup_contract", {}).get("resolver"),
            "scripts/resolve_runtime.py",
        )
        self.assertEqual(
            data.get("entrypoints", {}).get("resolve"),
            "python scripts/resolve_runtime.py",
        )
        self.assertEqual(
            data.get("entrypoints", {}).get("resolve_legacy"),
            "python scripts/resolve_workflow.py",
        )

    def test_active_navigation_docs_do_not_present_legacy_resolver_as_default(self):
        skill = read("SKILL.md")
        default_block = skill.split("## 默认执行", 1)[1].split("### 项目工作记忆", 1)[0]
        self.assertIn("scripts/resolve_runtime.py", default_block)
        self.assertIn("scripts/resolve_workflow.py", default_block)
        self.assertIn("legacy", default_block.lower())
        self.assertNotIn("再由 `scripts/resolve_workflow.py` 按任务加载最小模块集", default_block)

        router = read("RUNTIME_ROUTER.md")
        example_block = router.split("## 示例", 1)[1]
        self.assertIn("python scripts/resolve_runtime.py", example_block)
        self.assertNotIn("python scripts/resolve_workflow.py", example_block)

        repo_index = read("REPOSITORY_INDEX.md")
        startup_block = repo_index.split("## 启动", 1)[1].split("## 活动入口", 1)[0]
        self.assertIn("scripts/resolve_runtime.py", startup_block)
        self.assertIn("scripts/resolve_workflow.py", startup_block)
        self.assertIn("无状态兼容", startup_block)
        tools_block = repo_index.split("## 工具", 1)[1]
        self.assertIn("scripts/resolve_runtime.py", tools_block)
        self.assertIn("默认 assured resolver", tools_block)
        self.assertIn("scripts/resolve_workflow.py", tools_block)
        self.assertIn("无状态兼容 resolver", tools_block)

    def test_default_resolver_cli_runs_explicit_intent(self):
        resolver = ROOT / bootstrap()["startup_contract"]["resolver"]
        proc = subprocess.run(
            [sys.executable, str(resolver), "problem_analysis"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        plan = yaml.safe_load(proc.stdout) or {}
        self.assertEqual(plan.get("intents"), ["problem_analysis"])
        self.assertIn("runtime_plan", plan)
        self.assertIn("assurance", plan)
        self.assertEqual(plan["assurance"]["status"], "pass")
        self.assertEqual(
            plan["assurance"]["intent_resolution"]["mode"], "explicit"
        )

    def test_default_resolver_cli_runs_inferred_intent(self):
        resolver = ROOT / bootstrap()["startup_contract"]["resolver"]
        proc = subprocess.run(
            [
                sys.executable,
                str(resolver),
                "--request",
                "请审题并建模",
                "--objective",
                "optimization",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        plan = yaml.safe_load(proc.stdout) or {}
        self.assertEqual(plan.get("intents"), ["new_problem_design"])
        self.assertEqual(
            plan["assurance"]["intent_resolution"]["selected_intents"],
            ["new_problem_design"],
        )
        self.assertFalse(plan["assurance"]["intent_resolution"]["ambiguity"])


if __name__ == "__main__":
    unittest.main()
