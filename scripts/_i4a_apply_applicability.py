from pathlib import Path


def replace(path: str, old: str, new: str, *, exact_count: int | None = None) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if exact_count is not None and count != exact_count:
        raise SystemExit(f"{path}: expected {exact_count} occurrences of {old!r}, got {count}")
    if count == 0:
        raise SystemExit(f"{path}: missing expected token {old!r}")
    p.write_text(text.replace(old, new), encoding="utf-8")


replace("SKILL_CHANGE_GOVERNANCE.md", "governance_version: 1.0.2", "governance_version: 1.0.3", exact_count=1)
replace("SKILL_CHANGE_GOVERNANCE.md", 'applies_to_skill: ">=6.3.0,<9.0.0"', 'applies_to_skill: ">=6.3.0,<10.0.0"', exact_count=1)

for path in (
    "core/task_taxonomy.yaml",
    "core/code_quality_contract.yaml",
    "core/workbook_schema.yaml",
    "core/user_execution_contract.yaml",
    "core/runtime_assurance_contract.yaml",
    "core/numerical_verification_contract.yaml",
    "core/global_preprocessing_contract.yaml",
    "assets/figure_assets.yaml",
):
    replace(path, "<9.0.0", "<10.0.0", exact_count=1)

replace("scripts/lint_skill_checks.py", "<9.0.0", "<10.0.0")
for old, new in (
    ("workbook schema compatibility must cover 6.3.2 through v8", "workbook schema compatibility must cover 6.3.2 through v9"),
    ("governance applicability must include v8", "governance applicability must include v9"),
    ("subordinate contract compatibility must cover active v8 line", "subordinate contract compatibility must cover active v9 line"),
    ("task taxonomy compatibility must cover the active v8 line", "task taxonomy compatibility must cover the active v9 line"),
):
    replace("scripts/lint_skill_checks.py", old, new, exact_count=1)

for path in (
    "tests/test_runtime_health_coherence.py",
    "tests/test_schemas.py",
    "tests/test_v661_code_quality_closure.py",
    "tests/test_read_path_semantic_closure.py",
):
    replace(path, "<9.0.0", "<10.0.0")

Path("docs/phase_i_v9_applicability_renewal.md").write_text("""---
status: implemented
phase: I4a
baseline_skill_version: 8.9.0
candidate_final_version: 9.0.0
baseline_main_commit: 12483b97186d7570cd54f3a549b18248732f7079
parent_plan: docs/semantic_state_runtime_refactor_plan.md
runtime_authority: false
---

# Phase I I4a — v9 Applicability Metadata Renewal

本记录说明 Phase I I4a 对活动 governance / subordinate contract compatibility metadata 的续期。它不是新的 Runtime Authority，不改变模型、状态传播、数值验证、写作或执行语义。

## 修改边界

当前 Skill release carrier 仍为 `8.9.0`。本阶段只为仍将在 v9 继续生效的活动规则续期 applicability：

- `SKILL_CHANGE_GOVERNANCE.md`: `>=6.3.0,<10.0.0`；
- `core/task_taxonomy.yaml`: `>=6.3.1,<10.0.0`；
- `core/workbook_schema.yaml`: `>=6.3.2,<10.0.0`；
- `core/global_preprocessing_contract.yaml`: `>=7.4.2,<10.0.0`；
- `core/user_execution_contract.yaml`: `>=7.4.2,<10.0.0`；
- `core/code_quality_contract.yaml`: `>=7.4.2,<10.0.0`；
- `assets/figure_assets.yaml`: `>=7.4.2,<10.0.0`；
- `core/runtime_assurance_contract.yaml`: `>=7.12.0,<10.0.0`；
- `core/numerical_verification_contract.yaml`: `>=7.14.0,<10.0.0`。

这些 metadata 表示对应 Authority / asset contract 的规则仍适用于 Skill v9；它们不是 current Skill release carrier，也不把 repository 当前版本从 `8.9.0` 提前提升为 `9.0.0`。

## 明确不修改的 `<9.0.0`

历史计划和阶段审计中的 `<9.0.0` 是当时事实，必须保留，例如：

- `docs/v801_skill_health_remediation_plan.md`；
- `docs/phase_i_compatibility_removal_readiness.md`；
- `docs/v900_migration_contract.md` 的 I1 历史非破坏性边界；
- I2/I3 implementation records 中当时明确排除的范围。

因此本阶段禁止全仓 search/replace。

## 行为不变量

- `core/bootstrap.yaml#skill_version` 继续为 `8.9.0`；
- 不恢复任何 I2/I3 已退休 legacy writer/active alias；
- 不删除 L0 historical semantic readers；
- 不修改 Project State Schema、State Transition、Resolver 或 transaction 行为；
- 不改变 subordinate contract 自身 `version/schema_version/contract_version`；
- 不创建 v9 GitHub release/tag。

## 后续

I4b 才处理 current release carriers 从 `8.9.0` 到 `9.0.0`。I5 负责最终 migration/release documentation closure 与 release validation。
""", encoding="utf-8")

Path("tests/test_v900_phase_i_v9_applicability.py").write_text("""from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class PhaseIV9ApplicabilityTests(unittest.TestCase):
    def load(self, relative: str):
        return yaml.safe_load((ROOT / relative).read_text(encoding="utf-8")) or {}

    def test_governance_is_explicitly_renewed_for_v9(self):
        text = (ROOT / "SKILL_CHANGE_GOVERNANCE.md").read_text(encoding="utf-8")
        frontmatter = yaml.safe_load(text.split("---", 2)[1]) or {}
        self.assertEqual(str(frontmatter["governance_version"]), "1.0.3")
        self.assertEqual(str(frontmatter["applies_to_skill"]), ">=6.3.0,<10.0.0")

    def test_active_contract_applicability_covers_v9(self):
        expected = {
            "core/task_taxonomy.yaml": ">=6.3.1,<10.0.0",
            "core/workbook_schema.yaml": ">=6.3.2,<10.0.0",
            "core/global_preprocessing_contract.yaml": ">=7.4.2,<10.0.0",
            "core/user_execution_contract.yaml": ">=7.4.2,<10.0.0",
            "core/code_quality_contract.yaml": ">=7.4.2,<10.0.0",
            "assets/figure_assets.yaml": ">=7.4.2,<10.0.0",
            "core/runtime_assurance_contract.yaml": ">=7.12.0,<10.0.0",
            "core/numerical_verification_contract.yaml": ">=7.14.0,<10.0.0",
        }
        for relative, compatibility in expected.items():
            with self.subTest(relative=relative):
                data = self.load(relative)
                self.assertEqual(str(data["skill_compatibility"]), compatibility)
                self.assertNotIn("<9.0.0", str(data["skill_compatibility"]))

    def test_i4a_does_not_publish_v9_release_carrier(self):
        bootstrap = self.load("core/bootstrap.yaml")
        self.assertEqual(str(bootstrap["skill_version"]), "8.9.0")

    def test_historical_pre_i4_records_are_not_rewritten(self):
        historical = (
            "docs/v801_skill_health_remediation_plan.md",
            "docs/phase_i_compatibility_removal_readiness.md",
            "docs/v900_migration_contract.md",
        )
        for relative in historical:
            with self.subTest(relative=relative):
                self.assertIn("<9.0.0", (ROOT / relative).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
""", encoding="utf-8")
