from __future__ import annotations

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OLD = "9.1.0"
NEW = "9.2.0"


def replace_once(relative: str, old: str, new: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{relative}: expected exactly one occurrence of {old!r}, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def insert_after_once(relative: str, marker: str, insertion: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    count = text.count(marker)
    if count != 1:
        raise RuntimeError(f"{relative}: expected exactly one marker {marker!r}, found {count}")
    path.write_text(text.replace(marker, marker + insertion, 1), encoding="utf-8")


def main() -> None:
    # Active release carriers. Historical provenance is intentionally untouched.
    replace_once("core/bootstrap.yaml", "skill_version: 9.1.0", "skill_version: 9.2.0")
    replace_once(".codex-plugin/plugin.json", '"version": "9.1.0"', '"version": "9.2.0"')

    for relative in ("SKILL.md", "skills/mathmodel-skill/SKILL.md"):
        replace_once(relative, "version: 9.1.0", "version: 9.2.0")
        replace_once(
            relative,
            "# HSK 数学建模模块化工作流 v9.1.0",
            "# HSK 数学建模模块化工作流 v9.2.0",
        )

    replace_once("core/hsk_core_policy.md", "# HSK Core Policy v9.1.0", "# HSK Core Policy v9.2.0")

    for relative in (
        "core/workflow_router.yaml",
        "core/module_manifest.yaml",
        "core/output_contract.yaml",
        "core/writing_runtime_contract.yaml",
        "config/prose_audit_patterns.yaml",
    ):
        replace_once(relative, "version: 9.1.0", "version: 9.2.0")

    # README: advance current heading and add one release-neutral summary block.
    replace_once("README.md", "# mathmodel-skill v9.1.0", "# mathmodel-skill v9.2.0")
    readme_marker = "\n## v9.1.0：MATLAB Publication Rendering\n"
    readme_release = (
        "\n## v9.2.0：全面优化、运行协议与条件式证据链\n\n"
        "v9.2.0 汇总 P1–P8 已分阶段合并并通过回归的兼容优化：按任务 `reading_plan` 与 Authority 去重、compact `模型论文框架.md` 实例化、canonical `RUN_CONFIG` + versioned `RUN_RECEIPT`、MATLAB publication profile 与真实 preview gate、条件式 Analysis Necessity Gate / 附录，以及基于测量证据的基础设施整理。P9 只做综合回归、兼容窗口裁决和 release carrier 收尾，不重写这些阶段的业务实现。\n\n"
        "旧 `FULL_FIDELITY_CONFIG / FULL_RUN_CONFIG` 与 P5a 过渡期缺 receipt marker/version 的项目在 9.2.0 中继续**只读兼容**；新 writer 仍必须使用 `RUN_CONFIG` 并声明 `run_receipt_protocol_version=1.0.0`，未知显式协议版本继续 fail closed。上述 reader 的删除只允许在未来明确的 major migration 中进行，并须先提供旧项目识别/迁移证据、兼容矩阵更新与专门回归。\n"
    )
    insert_after_once("README.md", readme_marker, readme_release)

    # Changelog: turn the previous current release into a proper previous release.
    changelog_prefix = "# Changelog\n\n## Current release: 9.1.0\n\n"
    changelog_release = (
        "# Changelog\n\n## Current release: 9.2.0\n\n"
        "- Consolidated the approved P1–P8 optimization program into a single minor release without introducing breaking directory, Schema, CLI, numerical, Model Approval, MATLAB or LaTeX semantics.\n"
        "- Added task-scoped `reading_plan`, global-policy/writing-role deduplication, compact model-paper framework instantiation, canonical `RUN_CONFIG` and versioned `RUN_RECEIPT`, publication-profile MATLAB rendering with a real preview gate, and conditional result-analysis/appendix lifecycle support.\n"
        "- Retained legacy `FULL_FIDELITY_CONFIG / FULL_RUN_CONFIG` and P5a versionless receipt paths as read-only compatibility in 9.2.0; new writers remain canonical and unknown explicit receipt versions fail closed.\n"
        "- Recorded an explicit compatibility exit condition: reader removal is deferred to a future major migration (earliest v10) with migration/detection evidence, compatibility-matrix update and dedicated regression.\n"
        "- Closed P8 infrastructure work using measured evidence: generated-metadata final-head validation is preserved, duplicated RUN_CONFIG parsing is shared, and the large validator is not forcibly split where host-adapter coupling makes a mechanical move unsafe.\n"
        "- Release acceptance remains the complete HSK Skill CI plus Optimization baseline evidence on the final generated head; tests/gates are not deleted or weakened for this release.\n\n"
        "## Previous release: 9.1.0\n\n"
    )
    replace_once("CHANGELOG.md", changelog_prefix, changelog_release)

    # P5a/P5b compatibility is an additive Authority record; existing readers stay unchanged.
    compat_marker = (
        "  legacy_config_names:\n"
        "  - FULL_FIDELITY_CONFIG\n"
        "  - FULL_RUN_CONFIG\n"
    )
    compat_block = (
        "  compatibility_window:\n"
        "    release_decision: 9.2.0-read-only-retained\n"
        "    legacy_full_config_read_only: true\n"
        "    p5a_versionless_receipt_read_only: true\n"
        "    new_writer_must_use_run_config: true\n"
        "    new_writer_receipt_protocol_required: true\n"
        "    earliest_removal_skill_major: 10\n"
        "    removal_requires:\n"
        "    - explicit_major_migration\n"
        "    - legacy_project_detection_or_migration_evidence\n"
        "    - compatibility_matrix_update\n"
        "    - dedicated_regression\n"
    )
    insert_after_once("core/user_execution_contract.yaml", compat_marker, compat_block)

    # Optimization status is implementation evidence only; bring the phase table current.
    status_old = (
        "| P6a/P6b | 论文图例索引、独立 MATLAB profile、真实预览 | P6a 实施中，PR #159；P6b 未开始 |\n"
        "| P7 | 条件式分析与附录 | 已获范围批准，尚未实现 |\n"
        "| P8 | 有测量依据的基础设施整理 | 未开始 |\n"
        "| P9 | 综合回归、兼容与发布 | 未开始 |"
    )
    status_new = (
        "| P6a/P6b | 论文图例索引、独立 MATLAB profile、真实预览 | 已合并，PR #159 / #160 |\n"
        "| P7 | 条件式分析与附录 | 已合并，PR #161 |\n"
        "| P8 | 有测量依据的基础设施整理 | 已完成并合并，P8e PR #170 收尾 |\n"
        "| P9 | 综合回归、兼容与发布 | 实施中，PR #171，目标 v9.2.0 |"
    )
    replace_once("docs/skill_optimization_status.md", status_old, status_new)

    # Release-closeout record: implementation is now present; final run IDs remain a final-head task.
    replace_once(
        "docs/p9_release_closeout.md",
        "待本 PR 完成实现并在最终 generated head 通过完整 CI 后填写。",
        "P9 release 实现已写入本 PR；最终 generated head 的 HSK Skill CI / Optimization baseline run ID 与 merge SHA 在最终验收时补入。",
    )

    # Dedicated release regression: keep old read compatibility while asserting canonical writers and carriers.
    test_path = ROOT / "tests/test_p9_release_closeout.py"
    if test_path.exists():
        raise RuntimeError("tests/test_p9_release_closeout.py already exists")
    test_path.write_text(
        '''from pathlib import Path\nimport json\nimport unittest\n\nimport yaml\n\nROOT = Path(__file__).resolve().parents[1]\nEXPECTED = "9.2.0"\n\n\nclass P9ReleaseCloseoutTests(unittest.TestCase):\n    def test_release_carriers_are_v920(self):\n        bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8")) or {}\n        plugin = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))\n        self.assertEqual(str(bootstrap["skill_version"]), EXPECTED)\n        self.assertEqual(str(plugin["version"]), EXPECTED)\n        root_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")\n        packaged = (ROOT / "skills/mathmodel-skill/SKILL.md").read_text(encoding="utf-8")\n        self.assertEqual(root_skill, packaged)\n        self.assertIn(f"version: {EXPECTED}", root_skill)\n        self.assertIn(f"# HSK 数学建模模块化工作流 v{EXPECTED}", root_skill)\n        self.assertTrue((ROOT / "README.md").read_text(encoding="utf-8").startswith(f"# mathmodel-skill v{EXPECTED}"))\n        self.assertTrue((ROOT / "core/hsk_core_policy.md").read_text(encoding="utf-8").startswith(f"# HSK Core Policy v{EXPECTED}"))\n        for relative in (\n            "core/workflow_router.yaml",\n            "core/module_manifest.yaml",\n            "core/output_contract.yaml",\n            "core/writing_runtime_contract.yaml",\n            "config/prose_audit_patterns.yaml",\n        ):\n            data = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8")) or {}\n            self.assertEqual(str(data["version"]), EXPECTED, relative)\n\n    def test_legacy_execution_paths_are_read_only_with_major_exit_condition(self):\n        contract = yaml.safe_load((ROOT / "core/user_execution_contract.yaml").read_text(encoding="utf-8")) or {}\n        delivery = contract["code_delivery"]\n        self.assertEqual(delivery["canonical_config_name"], "RUN_CONFIG")\n        self.assertEqual(delivery["legacy_config_names"], ["FULL_FIDELITY_CONFIG", "FULL_RUN_CONFIG"])\n        window = delivery["compatibility_window"]\n        self.assertTrue(window["legacy_full_config_read_only"])\n        self.assertTrue(window["p5a_versionless_receipt_read_only"])\n        self.assertTrue(window["new_writer_must_use_run_config"])\n        self.assertTrue(window["new_writer_receipt_protocol_required"])\n        self.assertEqual(window["earliest_removal_skill_major"], 10)\n        self.assertIn("explicit_major_migration", window["removal_requires"])\n        self.assertTrue(delivery["run_receipt_protocol"]["new_writer_required"])\n        self.assertTrue(delivery["run_receipt_protocol"]["p5a_transitional_missing_marker_read_supported"])\n        receipt = contract["returned_workbook"]["versioned_receipt"]\n        self.assertTrue(receipt["p5a_transitional_missing_version_read_supported"])\n        self.assertTrue(receipt["legacy_full_config_missing_version_read_supported"])\n        self.assertEqual(receipt["declared_unknown_version_policy"], "fail_closed")\n\n    def test_release_docs_record_minor_compatibility_decision(self):\n        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")\n        self.assertTrue(changelog.startswith("# Changelog\\n\\n## Current release: 9.2.0"))\n        self.assertIn("## Previous release: 9.1.0", changelog)\n        record = (ROOT / "docs/p9_release_closeout.md").read_text(encoding="utf-8")\n        self.assertIn("最早 v10", record)\n        self.assertIn("unknown", record.lower())\n        self.assertIn("fail closed", record.lower())\n\n\nif __name__ == "__main__":\n    unittest.main()\n''',
        encoding="utf-8",
    )

    subprocess.run(["python", "scripts/generate_indexes.py"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
