from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_generate_indexes():
    path = ROOT / "scripts/generate_indexes.py"
    spec = importlib.util.spec_from_file_location("generate_indexes_hygiene", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def section(text: str, title: str) -> str:
    marker = f"## {title}\n"
    if marker not in text:
        raise AssertionError(f"missing section: {title}")
    tail = text.split(marker, 1)[1]
    return tail.split("\n## ", 1)[0]


class RepositoryHygieneIndexV931Tests(unittest.TestCase):
    def test_skill_index_is_semantically_segmented_without_changing_manifest_coverage(self):
        module = load_generate_indexes()
        payloads = module.generated_payloads()
        index = payloads[module.SKILL_INDEX]
        manifest = payloads[module.MANIFEST]

        active = section(index, "Active Runtime & Reference")
        maintenance = section(index, "Current Maintenance Records")
        migration = section(index, "Migration / Compatibility Records")
        historical = section(index, "Historical Maintenance Provenance")
        legacy = section(index, "Legacy Navigation")

        current_reference = (
            "docs/v871_writing_reasoning_schema_version_policy.md",
            "docs/v900_migration_contract.md",
        )
        current_maintenance = (
            "docs/skill_optimization_status.md",
            "docs/v931_postrelease_health_remediation_plan.md",
            "docs/v931_repository_hygiene_inventory.md",
        )
        migration_records = (
            "docs/phase_i_compatibility_inventory.md",
            "docs/phase_i_v9_release_closure.md",
            "docs/semantic_state_runtime_refactor_plan.md",
            "docs/v8_writing_migration.md",
        )
        historical_records = (
            "docs/v9_3_initial_modeling_structural_reduction_refactor_plan.md",
            "docs/v921_p7_conditional_analysis_semantic_hygiene_plan.md",
            "docs/v840_author_reasoning_evaluation.md",
        )

        for relative in current_reference:
            self.assertIn(f"`{relative}`", active)
            self.assertNotIn(f"`{relative}`", historical)

        for relative in current_maintenance:
            self.assertIn(f"`{relative}`", maintenance)
            self.assertNotIn(f"`{relative}`", active)

        for relative in migration_records:
            self.assertIn(f"`{relative}`", migration)
            self.assertNotIn(f"`{relative}`", active)

        for relative in historical_records:
            self.assertIn(f"`{relative}`", historical)
            self.assertNotIn(f"`{relative}`", active)

        self.assertIn("`legacy/README.md`", legacy)
        self.assertNotIn("`legacy/v660_self_contained_output_migration.md`", index)

        for relative in current_reference + current_maintenance + migration_records + historical_records:
            self.assertEqual(index.count(f"`{relative}`"), 1, relative)
            self.assertIn(f"  {relative}", manifest)

    def test_docs_default_to_historical_unless_explicitly_promoted(self):
        module = load_generate_indexes()
        self.assertEqual(
            module.skill_index_section(Path("docs/future_maintenance_note.md")),
            "historical_provenance",
        )
        self.assertEqual(
            module.skill_index_section(Path("docs/phase_future_compatibility.md")),
            "migration_compatibility",
        )
        self.assertEqual(
            module.skill_index_section(Path("core/bootstrap.yaml")),
            "active_runtime_reference",
        )
        self.assertEqual(
            module.skill_index_section(Path("legacy/README.md")),
            "legacy_navigation",
        )

    def test_index_intro_does_not_promote_maintenance_or_history_to_runtime_authority(self):
        module = load_generate_indexes()
        index = module.generated_payloads()[module.SKILL_INDEX]
        self.assertIn("只有 **Active Runtime & Reference** 表示默认活动导航", index)
        self.assertIn("不因此成为 Runtime Authority", index)
        self.assertIn("MANIFEST", index)


if __name__ == "__main__":
    unittest.main()
