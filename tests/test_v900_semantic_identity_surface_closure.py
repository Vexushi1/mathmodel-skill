from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


# Final-tree CI attestation marker; no runtime or contract semantics.
class PhaseCSemanticIdentitySurfaceClosureTests(unittest.TestCase):
    def test_manifest_model_approval_declares_structured_current_binding(self):
        manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8"))
        gate = manifest["utility_gates"]["model_approval"]
        rules = "\n".join(gate.get("rules", []))
        self.assertIn("semantic_identity_hash == validated_semantic_identity_hash == approved_semantic_identity_hash", rules)
        self.assertIn("partial structured identity state fails closed", rules)
        self.assertIn("historical read-only provenance", rules)
        self.assertNotIn("Requires approved_semantic_revision and approved_semantic_hash", rules)
        catalog = manifest["artifact_catalog"]
        self.assertIn("validated semantic_identity_hash", catalog["human_model_approval"])
        self.assertIn("validated semantic_identity_hash", catalog["locked_model_spec"])

    def test_critical_active_surfaces_do_not_restate_legacy_current_approval(self):
        paths = [
            "core/bootstrap.yaml",
            "core/workflow_router.yaml",
            "core/module_manifest.yaml",
            "core/hsk_core_policy.md",
            "SKILL.md",
            "skills/mathmodel-skill/SKILL.md",
            "AGENTS.md",
            "PROJECT_INSTRUCTIONS.md",
            "RUNTIME_ROUTER.md",
            "modules/03_solve_validate.md",
            ".codex-plugin/plugin.json",
            "README.md",
            "scripts/README.md",
            "REPOSITORY_INDEX.md",
        ]
        forbidden = [
            "semantic revision/hash",
            "semantic_revision/hash",
            "approved_semantic_revision and approved_semantic_hash to match",
            "批准当前 `semantic_revision` 与 `semantic_hash`",
            "Human Model Approval（绑定 current semantic revision/hash）",
            "challenge/approval 与当前 revision/hash 完全一致",
            "current semantic revision/hash",
            "Semantic governance may accept the current semantic hash",
        ]
        for relative in paths:
            text = (ROOT / relative).read_text(encoding="utf-8")
            for phrase in forbidden:
                self.assertNotIn(phrase, text, f"{relative} retains legacy current-approval wording: {phrase}")

    def test_current_surfaces_point_to_structured_identity_and_legacy_read_only_boundary(self):
        manifest = (ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8")
        bootstrap = (ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8")
        policy = (ROOT / "core/hsk_core_policy.md").read_text(encoding="utf-8")
        module03 = (ROOT / "modules/03_solve_validate.md").read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for text in (manifest, bootstrap, policy, module03):
            self.assertIn("semantic_identity_hash", text)
        self.assertIn("approved_semantic_identity_hash", manifest)
        self.assertIn("legacy semantic_hash", manifest.lower())
        self.assertIn("legacy", policy)
        self.assertIn("legacy", module03)
        self.assertIn("legacy text-hash provenance", agents)
        self.assertIn("never authorize new project-level preprocessing or primary solve code", agents)

    def test_root_and_packaged_skill_remain_byte_identical(self):
        self.assertEqual(
            (ROOT / "SKILL.md").read_bytes(),
            (ROOT / "skills/mathmodel-skill/SKILL.md").read_bytes(),
        )


if __name__ == "__main__":
    unittest.main()
