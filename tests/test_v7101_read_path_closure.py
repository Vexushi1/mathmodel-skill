from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class TestV7101ReadPathClosure(unittest.TestCase):
    def test_patch_release_carriers_match_bootstrap(self) -> None:
        version = str(yaml.safe_load(read("core/bootstrap.yaml"))["skill_version"])
        self.assertIn(f"version: {version}", read("SKILL.md"))
        self.assertIn(f"version: {version}", read("skills/mathmodel-skill/SKILL.md"))
        self.assertEqual(json.loads(read(".codex-plugin/plugin.json"))["version"], version)
        self.assertTrue(read("README.md").startswith(f"# mathmodel-skill v{version}"))
        self.assertIn(f"## Current release: {version}", read("CHANGELOG.md"))
        self.assertIn(f"# HSK Core Policy v{version}", read("core/hsk_core_policy.md"))
        for relative in ("core/workflow_router.yaml", "core/module_manifest.yaml", "core/output_contract.yaml"):
            self.assertEqual(str(yaml.safe_load(read(relative))["version"]), version, relative)

    def test_resolver_returned_pre_delivery_gates_are_complete_consumer_contract(self) -> None:
        bootstrap = read("core/bootstrap.yaml")
        agent_prompt = yaml.safe_load(read("agents/openai.yaml"))["interface"]["default_prompt"]
        agents = read("AGENTS.md")
        project = read("PROJECT_INSTRUCTIONS.md")
        runtime = read("RUNTIME_ROUTER.md")
        self.assertIn("every `pre_delivery_gates` entry returned by the resolver", bootstrap)
        self.assertIn("authoritative and complete gate sequence", agent_prompt)
        self.assertIn("execute every returned gate in resolver order", agent_prompt)
        self.assertIn("every gate returned in the resolver's current `pre_delivery_gates` sequence", agents)
        self.assertIn("resolver 当前返回的全部 `pre_delivery_gates`", project)
        self.assertIn("完整且有序的执行序列", runtime)
        self.assertNotIn("semantic_governance, code_delivery, user_execution_receipt and project_sync", agent_prompt)

    def test_terminal_docs_reach_validated_package_after_generation(self) -> None:
        for relative in ("SKILL.md", "skills/mathmodel-skill/SKILL.md", "RUNTIME_ROUTER.md"):
            text = read(relative)
            self.assertIn("validated_submission_package", text, relative)
            self.assertIn("pre_delivery_gates", text, relative)
        runtime = read("RUNTIME_ROUTER.md")
        self.assertLess(runtime.index("review_delivery"), runtime.index("生成 official / reproducibility submission package"))
        self.assertLess(runtime.index("生成 official / reproducibility submission package"), runtime.index("validated_submission_package"))

    def test_delivery_tool_navigation_is_complete(self) -> None:
        expected = (
            "scripts/latex_delivery.py",
            "scripts/render_paper.py",
            "scripts/hsk_pack_submission.py",
            "scripts/validate_submission_package.py",
        )
        repository_index = read("REPOSITORY_INDEX.md")
        scripts_readme = read("scripts/README.md")
        for token in expected:
            self.assertIn(token, repository_index, token)
            self.assertIn(token.removeprefix("scripts/"), scripts_readme, token)

    def test_result_manifest_uses_internal_metadata(self) -> None:
        text = read("templates/review/result_manifest.yaml")
        self.assertIn("项目级 internal_metadata/", text)
        self.assertNotIn("项目级 metadata/", text)

    def test_lint_backend_derives_release_version_from_bootstrap(self) -> None:
        text = read("scripts/lint_skill_checks.py")
        self.assertIn('ROOT / "core/bootstrap.yaml"', text)
        self.assertIn('["skill_version"]', text)
        self.assertIsNone(re.search(r'^PACKAGE_VERSION\s*=\s*["\']\d', text, re.MULTILINE))

    def test_router_semantics_are_not_rewritten(self) -> None:
        router_text = read("core/workflow_router.yaml")
        router = yaml.safe_load(router_text)
        version = str(yaml.safe_load(read("core/bootstrap.yaml"))["skill_version"])
        self.assertIn("submission_package_validation", router_text)
        self.assertEqual(str(router["version"]), version)


if __name__ == "__main__":
    unittest.main()
