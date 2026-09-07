from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace(path: str, old: str, new: str, *, exact_count: int = 1) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != exact_count:
        raise SystemExit(f"{path}: expected {exact_count} occurrences of {old!r}, got {count}")
    p.write_text(text.replace(old, new), encoding="utf-8")


# Formal active release carriers only. Historical baseline/version records are not touched.
replace("core/bootstrap.yaml", "skill_version: 8.9.0", "skill_version: 9.0.0")
replace(".codex-plugin/plugin.json", '"version": "8.9.0"', '"version": "9.0.0"')
replace("core/output_contract.yaml", "version: 8.9.0", "version: 9.0.0")
replace("core/module_manifest.yaml", "version: 8.9.0", "version: 9.0.0")
replace("core/workflow_router.yaml", "version: 8.9.0", "version: 9.0.0")
replace("core/writing_runtime_contract.yaml", "version: 8.9.0", "version: 9.0.0")
replace("config/prose_audit_patterns.yaml", "version: 8.9.0", "version: 9.0.0")
replace("core/hsk_core_policy.md", "# HSK Core Policy v8.9.0", "# HSK Core Policy v9.0.0")

for path in ("SKILL.md", "skills/mathmodel-skill/SKILL.md"):
    replace(path, "version: 8.9.0", "version: 9.0.0")
    replace(path, "# HSK 数学建模模块化工作流 v8.9.0", "# HSK 数学建模模块化工作流 v9.0.0")

replace("README.md", "# mathmodel-skill v8.9.0", "# mathmodel-skill v9.0.0")
readme_anchor = "## v8.9.0：Stable Compatibility Checkpoint for v9 Migration\n"
readme_insert = """## v9.0.0：Phase I Compatibility Removal & Release Carrier Transition

v9.0.0 将 Phase I 已完成的兼容清理正式收口到活动 release carrier：I2 已停止 legacy `semantic_hash / validated_semantic_hash` 新写，I3 已移除活动 artifact/state alias 与无独立意义的旧实现字段，I4a 已把仍有效的 governance / subordinate-contract applicability 续期到 v9。L0 历史项目的窄只读 reader 继续保留，不能授权新的模型设计、预处理或主求解代码。

本次 I4b 只把活动 release carrier 从 `8.9.0` 切换为 `9.0.0`，不再改变 Project State、State Transition、Resolver、transaction、数值验证、写作运行时或模型审批语义，也不创建 GitHub tag/release。最终 migration/release documentation closure 与最终 release validation 继续由 Phase I I5 完成。

"""
p = ROOT / "README.md"
text = p.read_text(encoding="utf-8")
if text.count(readme_anchor) != 1:
    raise SystemExit("README.md: expected exactly one v8.9.0 section anchor")
p.write_text(text.replace(readme_anchor, readme_insert + readme_anchor, 1), encoding="utf-8")

changelog_anchor = "## Current release: 8.9.0\n"
changelog_replacement = """## Current release: 9.0.0

- Advanced the formal active release carriers from `8.9.0` to `9.0.0` after the Phase I I2/I3 compatibility-removal work and I4a v9 applicability renewal were merged and validated on `main`.
- Preserved the intentionally narrow initial-v9 historical readers for L0/read-only projects; retired legacy fields and aliases are not restored as active write or authorization surfaces.
- Kept Project State, State Transition, Resolver, transaction, numerical verification, writing runtime and Model Approval behavior unchanged in this carrier-only transition.
- Kept historical Phase-I baselines, migration fixtures and implementation records pinned to the v8.9 compatibility window instead of rewriting their provenance.
- GitHub tag/release creation plus final migration/release documentation closure remain Phase I I5 work.

## Previous release: 8.9.0
"""
replace("CHANGELOG.md", changelog_anchor, changelog_replacement)

# Current-release health tests.
for old, new in (
    ('self.assertEqual(bootstrap.get("skill_version"), "8.9.0")', 'self.assertEqual(bootstrap.get("skill_version"), "9.0.0")'),
    ('self.assertEqual(str(plugin.get("version")), "8.9.0")', 'self.assertEqual(str(plugin.get("version")), "9.0.0")'),
    ('self.assertIn("version: 8.9.0", root_skill)', 'self.assertIn("version: 9.0.0", root_skill)'),
    ('self.assertIn("# HSK 数学建模模块化工作流 v8.9.0", root_skill)', 'self.assertIn("# HSK 数学建模模块化工作流 v9.0.0", root_skill)'),
    ('self.assertEqual(str(contract.get("version")), "8.9.0")', 'self.assertEqual(str(contract.get("version")), "9.0.0")'),
):
    replace("tests/test_current_skill_health.py", old, new)

# I4a characterization becomes historical once I4b publishes the v9 carrier.
replace(
    "tests/test_v900_phase_i_v9_applicability.py",
    "    def test_i4a_does_not_publish_v9_release_carrier(self):\n        bootstrap = self.load(\"core/bootstrap.yaml\")\n        self.assertEqual(str(bootstrap[\"skill_version\"]), \"8.9.0\")\n",
    "    def test_i4b_publishes_v9_after_i4a_applicability_renewal(self):\n        bootstrap = self.load(\"core/bootstrap.yaml\")\n        self.assertEqual(str(bootstrap[\"skill_version\"]), \"9.0.0\")\n        i4a_record = (ROOT / \"docs/phase_i_v9_applicability_renewal.md\").read_text(encoding=\"utf-8\")\n        self.assertIn(\"当前 Skill release carrier 仍为 `8.9.0`\", i4a_record)\n        self.assertIn(\"I4b 才处理 current release carriers 从 `8.9.0` 到 `9.0.0`\", i4a_record)\n",
)

# Migration fixtures remain v8.9 historical baselines; current bootstrap now advances independently.
replace(
    "tests/test_v900_phase_i_migration_matrix.py",
    "    def test_fixture_is_bound_to_current_staged_release_and_plan(self):\n        bootstrap = yaml.safe_load((ROOT / \"core/bootstrap.yaml\").read_text(encoding=\"utf-8\"))\n        self.assertEqual(MATRIX[\"baseline_skill_version\"], bootstrap[\"skill_version\"])\n",
    "    def test_fixture_remains_bound_to_v890_staging_baseline_after_v9_release(self):\n        bootstrap = yaml.safe_load((ROOT / \"core/bootstrap.yaml\").read_text(encoding=\"utf-8\"))\n        self.assertEqual(MATRIX[\"baseline_skill_version\"], \"8.9.0\")\n        self.assertEqual(bootstrap[\"skill_version\"], \"9.0.0\")\n        self.assertNotEqual(MATRIX[\"baseline_skill_version\"], bootstrap[\"skill_version\"])\n",
)
replace(
    "tests/test_v900_phase_i_writer_retirement_readiness.py",
    "    def test_inventory_is_bound_to_current_stable_release_and_explicit_authorization(self):\n        bootstrap = yaml.safe_load(BOOTSTRAP_PATH.read_text(encoding=\"utf-8\"))\n        self.assertEqual(INVENTORY[\"baseline_skill_version\"], bootstrap[\"skill_version\"])\n        self.assertEqual(bootstrap[\"skill_version\"], \"8.9.0\")\n",
    "    def test_inventory_remains_bound_to_v890_stable_checkpoint_after_v9_release(self):\n        bootstrap = yaml.safe_load(BOOTSTRAP_PATH.read_text(encoding=\"utf-8\"))\n        self.assertEqual(INVENTORY[\"baseline_skill_version\"], \"8.9.0\")\n        self.assertEqual(bootstrap[\"skill_version\"], \"9.0.0\")\n        self.assertNotEqual(INVENTORY[\"baseline_skill_version\"], bootstrap[\"skill_version\"])\n",
)

(ROOT / "docs/phase_i_v9_release_carrier_transition.md").write_text(
    """---
status: implemented
phase: I4b
baseline_skill_version: 8.9.0
target_skill_version: 9.0.0
baseline_main_commit: 92b494154ed49f134d5d18eb9b6c4eebade2aec0
parent_plan: docs/semantic_state_runtime_refactor_plan.md
i4a_record: docs/phase_i_v9_applicability_renewal.md
runtime_authority: false
github_release_or_tag_created: false
---

# Phase I I4b — v9 Release Carrier Transition

本记录说明 Phase I I4b 将活动 Skill release carrier 从 `8.9.0` 切换到 `9.0.0`。它是 release metadata / entrypoint 一致性变更，不建立新的 Runtime Authority，也不改变数学、状态、求解、写作或执行语义。

## 活动 release carriers

以下活动 surface 必须一致声明 `9.0.0`：

- `core/bootstrap.yaml#skill_version`；
- `.codex-plugin/plugin.json#version`；
- 根目录与 packaged `SKILL.md` frontmatter / 标题；
- `README.md` current heading；
- `core/hsk_core_policy.md` 标题；
- `CHANGELOG.md#Current release`；
- `core/workflow_router.yaml#version`；
- `core/module_manifest.yaml#version`；
- `core/output_contract.yaml#version`；
- `core/writing_runtime_contract.yaml#version`；
- `config/prose_audit_patterns.yaml#version`。

## 历史 provenance 不重写

I0/I1/I2/I3/I4a 的 `baseline_skill_version: 8.9.0`、migration fixtures 与当时的“release carrier 仍为 8.9.0”陈述是历史事实，继续保留。I4b 只改变 current active release carrier，不通过全仓字符串替换篡改阶段证据。

## 行为不变量

- 不恢复 I2 已停止的 legacy semantic writers；
- 不恢复 I3 已移除的 active artifact aliases / obsolete state fields；
- 不删除 initial-v9 L0 historical readers；
- 不修改 Project State Schema、State Transition、Resolver、transaction、numerical verification、writing runtime 或 Model Approval 行为；
- I4a 的 active applicability 继续为 `<10.0.0`；
- 不创建 GitHub tag 或 GitHub Release。

## 后续

Phase I I5 负责最终 migration/release documentation closure、最终 release validation，以及在确认全部 release gate 后处理外部 release/tag（如项目流程要求）。
""",
    encoding="utf-8",
)

(ROOT / "tests/test_v900_phase_i_release_carriers.py").write_text(
    """from pathlib import Path
import json
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "9.0.0"


class PhaseII4bReleaseCarrierTests(unittest.TestCase):
    def test_all_active_release_carriers_are_v9(self):
        bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8")) or {}
        plugin = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        root_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        packaged_skill = (ROOT / "skills/mathmodel-skill/SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(str(bootstrap["skill_version"]), EXPECTED)
        self.assertEqual(str(plugin["version"]), EXPECTED)
        self.assertEqual(root_skill, packaged_skill)
        self.assertIn(f"version: {EXPECTED}", root_skill)
        self.assertIn(f"# HSK 数学建模模块化工作流 v{EXPECTED}", root_skill)
        self.assertTrue((ROOT / "README.md").read_text(encoding="utf-8").startswith(f"# mathmodel-skill v{EXPECTED}"))
        self.assertTrue((ROOT / "core/hsk_core_policy.md").read_text(encoding="utf-8").startswith(f"# HSK Core Policy v{EXPECTED}"))
        self.assertTrue((ROOT / "CHANGELOG.md").read_text(encoding="utf-8").startswith(f"# Changelog\n\n## Current release: {EXPECTED}"))
        for relative in (
            "core/workflow_router.yaml",
            "core/module_manifest.yaml",
            "core/output_contract.yaml",
            "core/writing_runtime_contract.yaml",
            "config/prose_audit_patterns.yaml",
        ):
            data = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8")) or {}
            self.assertEqual(str(data["version"]), EXPECTED, relative)

    def test_historical_v890_phase_i_baselines_are_preserved(self):
        for relative in (
            "docs/v900_migration_contract.md",
            "docs/phase_i_legacy_writer_retirement.md",
            "docs/phase_i_artifact_alias_retirement.md",
            "docs/phase_i_artifact_state_surface_removal.md",
            "docs/phase_i_v9_applicability_renewal.md",
            "tests/fixtures/v900_phase_i_migration_matrix.yaml",
            "tests/fixtures/v900_phase_i_writer_retirement_inventory.yaml",
        ):
            with self.subTest(relative=relative):
                self.assertIn("8.9.0", (ROOT / relative).read_text(encoding="utf-8"))

    def test_i4a_applicability_and_i4b_scope_remain_explicit(self):
        governance = (ROOT / "SKILL_CHANGE_GOVERNANCE.md").read_text(encoding="utf-8")
        record = (ROOT / "docs/phase_i_v9_release_carrier_transition.md").read_text(encoding="utf-8")
        self.assertIn('applies_to_skill: ">=6.3.0,<10.0.0"', governance)
        self.assertIn("runtime_authority: false", record)
        self.assertIn("github_release_or_tag_created: false", record)
        self.assertIn("不创建 GitHub tag 或 GitHub Release", record)
        self.assertIn("Phase I I5", record)


if __name__ == "__main__":
    unittest.main()
""",
    encoding="utf-8",
)
