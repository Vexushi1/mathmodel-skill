import importlib.util
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
POINTERS = {
    "PROJECT_INSTRUCTIONS_HSK_V622.md": "PROJECT_INSTRUCTIONS.md",
    "HSK_RUNTIME_ROUTER_V622.md": "RUNTIME_ROUTER.md",
    "HSK_SKILL_FILE_INDEX_V622.md": "SKILL_FILE_INDEX.md",
    "HSK_TEMPLATE_INDEX_V622.md": "TEMPLATE_INDEX.md",
}


def load_resolver():
    spec = importlib.util.spec_from_file_location("resolve_workflow_v741", ROOT / "scripts/resolve_workflow.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestV741SkillClosureHygiene(unittest.TestCase):
    def test_current_authorities_are_release_aligned(self):
        bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))
        taxonomy = yaml.safe_load((ROOT / "core/task_taxonomy.yaml").read_text(encoding="utf-8"))
        current = str(bootstrap["skill_version"])
        self.assertIn(f"version: {current}", (ROOT / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual((ROOT / "core/hsk_core_policy.md").read_text(encoding="utf-8").splitlines()[0], f"# HSK Core Policy v{current}")
        self.assertIn(">=6.3.1", taxonomy["skill_compatibility"])
        self.assertIn("<8.0.0", taxonomy["skill_compatibility"])

    def test_model_design_has_no_fixed_assumption_quota(self):
        design = (ROOT / "modules/02_model_design.md").read_text(encoding="utf-8")
        self.assertNotIn("3--5 个关键假设", design)
        self.assertNotIn("3—5 个关键假设", design)
        self.assertIn("按必要性而非数量配额", design)
        self.assertIn("共享假设", design)
        self.assertIn("第一次使用前就近记录", design)

    def test_compatibility_pointers_are_preserved_but_not_active(self):
        index = (ROOT / "SKILL_FILE_INDEX.md").read_text(encoding="utf-8")
        manifest = (ROOT / "MANIFEST.sha256").read_text(encoding="utf-8")
        for legacy, active in POINTERS.items():
            pointer = (ROOT / legacy).read_text(encoding="utf-8")
            self.assertIn("Compatibility Pointer", pointer)
            self.assertIn(active, pointer)
            self.assertNotIn(f"`{legacy}`", index)
            self.assertFalse(any(line.endswith(f"  {legacy}") for line in manifest.splitlines()))

    def test_agent_entrypoint_delegates_gate_order_to_resolver(self):
        agent = yaml.safe_load((ROOT / "agents/openai.yaml").read_text(encoding="utf-8"))
        prompt = agent["interface"]["default_prompt"]
        for token in ("pre_delivery_gates", "semantic_governance", "code_delivery", "user_execution_receipt", "project_sync"):
            self.assertIn(token, prompt)
        self.assertIn("do not replace stage-specific gates with a blanket project-sync call", prompt)
        self.assertIn("DOCX is explicit-only", prompt)
        self.assertIn("Do not load legacy or V622 compatibility pointers by default", prompt)
        self.assertNotIn("Before every formal model, code, workbook, MATLAB figure, DOCX, LaTeX or submission delivery, run scripts/sync_project.py", prompt)

    def test_every_router_route_resolves_to_existing_paths(self):
        resolver = load_resolver()
        router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8"))
        available = set(manifest["external_artifacts"]) | set(manifest["artifact_catalog"])
        for gate in manifest.get("utility_gates", {}).values():
            available.update(gate.get("outputs", []))
        prefixes = ("core/", "modules/", "packs/", "templates/", "scripts/", "config/", "state/", "assets/", "agents/", "skills/", ".github/", ".codex-plugin/")
        for route_name in router["routing"]:
            decision = "project_level" if route_name == "data_preprocessing" else "not_needed"
            plan = resolver.resolve_workflow(
                route_name,
                objective="optimization",
                structures=["stochastic"],
                available_artifacts=sorted(available),
                preprocessing_decision=decision,
            )
            self.assertEqual(plan["missing_prerequisites"], [], route_name)
            paths = []
            for field in ("modules", "packs", "templates", "contracts", "load_order"):
                paths.extend(plan.get(field, []))
            paths.extend(gate.get("path") for gate in plan.get("pre_delivery_gates", []))
            for value in paths:
                if isinstance(value, str) and value.startswith(prefixes):
                    self.assertTrue((ROOT / value.split("#", 1)[0]).exists(), f"{route_name}: {value}")


if __name__ == "__main__":
    unittest.main()
