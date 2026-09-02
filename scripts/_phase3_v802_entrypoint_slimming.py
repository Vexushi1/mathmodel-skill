from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = "8.0.1"
NEW = "8.0.2"

SKILL_TEXT = r'''---
name: mathmodel-skill
version: 8.0.2
summary: HSK mathematical-modeling workflow with bootstrap-first task routing, Problem Contract freezing, independent Model Challenge, explicit Human Model Approval bound to the current semantic revision/hash, user-owned full-fidelity numerical execution, evidence-checked workbooks, MATLAB evidence visualization, Template-First paper authoring, formal LaTeX attestation, and validated delivery provenance.
triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 审题, 问题分析, 建模思路, 建模方案, 模型比较, 完整求解, 全流程, 建模论文, 模型论文框架, 模型锁定, 模型审查, 算法流程, 伪代码, 数据预处理, 数据清洗, 主结果质量, 数值有效性, 结果分析, 结果深化分析, Python求解, MATLAB绘图, LaTeX, DOCX, 终审, 提交包]
---

# HSK 数学建模模块化工作流 v8.0.2

<!-- HSK_RUNTIME_ENTRY_CONTRACT_START -->
## 运行时入口合同（非权威摘要）

本文件只负责发现、启动和 Authority 委托，不复制数学建模业务合同。无论从根目录 `SKILL.md` 还是 `skills/mathmodel-skill/SKILL.md` 进入，都按同一链路执行：

1. 首先读取 `core/bootstrap.yaml`；
2. 由 `core/workflow_router.yaml` 的 `default_load` 加载 `core/hsk_core_policy.md`；
3. 使用 `scripts/resolve_runtime.py` 根据当前意图、竞赛和项目状态解析最小 `load_order`、运行时 assurance 与 `pre_delivery_gates`；
4. 只加载 resolver 命中的 contracts、modules、packs 和 templates，不预载整个仓库；
5. 需要项目语义时读取 current `模型论文框架.md`，生命周期 revision/hash/stale 服从 `state/project_state.yaml`，具体数值回到 accepted workbook；
6. 普通写作由 Template Manifest、Paper Writing Protocol 和 compact writing runtime 渐进加载；复杂数学/证据裁决及终审按 resolver 补读 `core/writing_reasoning_contract.yaml`；
7. `legacy/` 不进入默认执行链，旧 `scripts/resolve_workflow.py` 只保留无状态/兼容入口。

本节只声明入口委托关系，**不作为模型、预处理、求解、绘图或写作规则的独立权威**；任何冲突都以 `core/bootstrap.yaml` 指向的 current Authority 与 resolver 输出为准。
<!-- HSK_RUNTIME_ENTRY_CONTRACT_END -->

## 稳定硬边界

- Problem Contract 冻结不等于模型已批准。形成 `proposed_model_spec` 后，必须完成独立 Model Reviewer 与 Devil's Advocate challenge；正式项目级预处理或主求解代码只有在用户明确批准 current `semantic_revision/hash`、形成 current `locked_model_spec` 后才允许进入对应 gate。
- 题目专属预处理、主求解与结果深化 Python 由用户本地按 `full_fidelity` 执行；助手负责生成、静态检查和验收返回 artifact，不得静默降采样、放宽容差、缩短时域或切换求解器。
- `模型论文框架.md` 保存当前项目语义与证据位置；`state/project_state.yaml` 管 revision/hash/stale；accepted workbook 是具体数值事实源。三者职责不得互相替代。
- 主求解数值有效性与 accepted 资格服从 `core/numerical_verification_contract.yaml`；accepted 后的替代世界/敏感性/稳健性分析服从 resolver 命中的结果分析模块，不反向扩张主质量门。
- MATLAB 只消费 Python 已输出且已验收的数据/工作簿进行 Figure Evidence，不重新预处理或求解；正式图名由 LaTeX/DOCX caption 承担。
- LaTeX 是默认论文主链；CUMCM 结构先由 Template Manifest 确定，再逐章读取当前写作规则。DOCX 只在用户明确要求 Word 载体时加载。
- 最终交付只执行 resolver 当前返回且按顺序排列的 `pre_delivery_gates`；入口文件不维护第二套 gate 清单。
- 仓库修改遵守 `SKILL_CHANGE_GOVERNANCE.md`。Branch Protection 若因平台权限不可用，只记录为平台治理债务，不得用 Skill 代码伪造。

## Authority 导航

| 主题 | Current Authority / consumer |
|---|---|
| 启动、最小加载 | `core/bootstrap.yaml` |
| 全局硬规则 | `core/hsk_core_policy.md` |
| 路由、阶段、gate | `core/workflow_router.yaml` |
| 题型与 capability | `core/task_taxonomy.yaml` |
| 模块输入输出 | `core/module_manifest.yaml` |
| 目录与正式交付 | `core/output_contract.yaml` |
| 项目状态与 stale | `core/project_state.schema.yaml` |
| 项目工作记忆 | `core/project_memory_contract.yaml` |
| 模型 Challenge / Human Approval | `core/model_approval_contract.yaml` |
| 数据审计与条件式预处理 | `core/global_preprocessing_contract.yaml` |
| 用户执行所有权 | `core/user_execution_contract.yaml` |
| 主求解数值有效性 | `core/numerical_verification_contract.yaml` |
| Python 工程质量 | `core/code_quality_contract.yaml` |
| runtime assurance | `core/runtime_assurance_contract.yaml` |
| 主求解 / Primary Evidence | `modules/03_solve_validate.md` |
| accepted 后结果深化 | `modules/03_result_analysis.md` |
| 科研图证据 | `modules/04_figure_evidence.md` |
| CUMCM 固定结构 | `templates/latex/cumcm/hsk/template_manifest.yaml` |
| 写作读取状态机 | `core/writing_runtime_contract.yaml` |
| 普通正文 | `modules/05_writing/paper_writing_protocol.md` |
| 复杂写作语义与证据 | `core/writing_reasoning_contract.yaml` |
| LaTeX Adapter | `modules/05_writing/latex.md` |
| 表达清理 / 终审 | `modules/05_writing/ai_cleanup.md`, `modules/06_review_delivery.md` |

## 能力发现标签

以下名称仅用于能力发现与回归，不在本入口重复定义规则：**Template Manifest、Paper Writing Protocol、Primary Evidence Capture、Scientific Figure Synthesis、Model/Solver/Validator、Claim Strength Calibration、within-question local dependency architecture、decisiveness-based detail allocation、adaptive figure-result narrative**。具体定义只读取上表 Authority。

## 兼容与版本信息

- v7 项目在 v8.x 内保持只读兼容，不自动重排或覆盖既有论文正文；迁移说明见 `docs/v8_writing_migration.md`。
- 历史版本能力与实施记录统一见 `CHANGELOG.md`、`README.md` 和 `legacy/README.md`；入口不再复制 v7.14--v8.0.1 的版本演进正文。
- 活动文件导航使用 `PROJECT_INSTRUCTIONS.md`、`RUNTIME_ROUTER.md`、`SKILL_FILE_INDEX.md`、`TEMPLATE_INDEX.md`。
'''

PROJECT_INSTRUCTIONS = r'''# HSK 项目调用说明

本文件只说明稳定调用程序和事实源边界。业务规则必须按 `core/bootstrap.yaml` 与 `scripts/resolve_runtime.py` 返回的 current Authority 读取，不在这里复制第二套合同。

## 启动与恢复

1. 先读 `core/bootstrap.yaml`，再运行 `scripts/resolve_runtime.py` 解析当前意图；只加载 resolver 命中的 contracts、modules、packs 和 templates。`scripts/resolve_workflow.py` 仅作无状态兼容入口。
2. 已有项目时把 project root 交给 runtime resolver。当前语义与证据位置优先从 `模型论文框架.md` 恢复；revision/hash/stale 以 `state/project_state.yaml` 为准；具体数值必须回到 accepted workbook 核对。
3. 不依据旧聊天、历史计划或 `legacy/` 猜测 current 规则；legacy 只用于追溯和兼容。

## 执行硬边界

- Problem Contract、Model Challenge passed 或用户未反对都不能替代显式 Human Model Approval。正式项目级预处理或主求解代码前，current `semantic_revision/hash` 必须与 current `locked_model_spec` 的批准状态闭合，并执行 resolver 返回的语义/模型批准 gate。
- 题目专属预处理、主求解和结果深化 Python 默认由用户本地 full-fidelity 执行。助手生成并静态检查代码、验收返回工作簿；不得为了省时静默改变采样、精度、时域、重复次数、容差或求解器。
- 主求解 accepted 资格只服从 `core/numerical_verification_contract.yaml`；accepted 后的深化分析由 `modules/03_result_analysis.md` 及 resolver 选中的合同管理。
- MATLAB 只读取已验收数据和工作簿进行 Figure Evidence，不重新执行核心计算；绘图规则只服从 `modules/04_figure_evidence.md` 与相关输出契约。

## 写作与交付

- LaTeX 为默认主链。CUMCM 先读 `templates/latex/cumcm/hsk/template_manifest.yaml` 确定固定骨架，再按 `core/writing_runtime_contract.yaml` 的 progressive authoring 顺序读取 `modules/05_writing/paper_writing_protocol.md`；复杂数学/证据语义由 `core/writing_reasoning_contract.yaml` 裁决，`modules/05_writing/latex.md` 只负责载体适配。
- DOCX 仅在用户明确要求 Word 审阅、批注、协作或指定提交格式时加载。
- 正式交付严格执行 resolver 当前返回的全部 `pre_delivery_gates` 且保持返回顺序；本文件不维护固定 gate 清单。

## 仓库维护

仓库级修改必须先读 current `core/bootstrap.yaml` 与 `SKILL_CHANGE_GOVERNANCE.md`，检查重叠 PR，使用独立分支和单主题 PR，并以真实 CI/生成文件结果验收。平台权限无法完成的 GitHub Settings 项只记录为治理债务，不得修改 Skill 代码模拟。

活动入口使用稳定文件名：`PROJECT_INSTRUCTIONS.md`、`RUNTIME_ROUTER.md`、`SKILL_FILE_INDEX.md` 和 `TEMPLATE_INDEX.md`。旧版本化入口只作兼容指针，不进入默认运行链。
'''

SURFACE_TEST = r'''from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class TestV802EntrypointSurfaceSlimming(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.packaged_skill = (ROOT / "skills/mathmodel-skill/SKILL.md").read_text(encoding="utf-8")
        cls.instructions = (ROOT / "PROJECT_INSTRUCTIONS.md").read_text(encoding="utf-8")

    def test_root_and_packaged_entrypoints_remain_exactly_equal(self):
        self.assertEqual(self.root_skill, self.packaged_skill)

    def test_entrypoint_keeps_mandatory_delegation_and_hard_boundaries(self):
        for token in (
            "core/bootstrap.yaml",
            "core/workflow_router.yaml",
            "core/hsk_core_policy.md",
            "scripts/resolve_runtime.py",
            "scripts/resolve_workflow.py",
            "core/model_approval_contract.yaml",
            "core/numerical_verification_contract.yaml",
            "core/writing_reasoning_contract.yaml",
            "模型论文框架.md",
            "state/project_state.yaml",
            "legacy/",
            "pre_delivery_gates",
            "full_fidelity",
        ):
            self.assertIn(token, self.root_skill)

    def test_entrypoint_no_longer_copies_versioned_business_rulebooks(self):
        for token in (
            "### 数据与求解",
            "### Figure Evidence",
            "v7.16 进一步要求",
            "v7.18 进一步强化",
            "v7.19 在保持",
            "v8.0.0 将模板",
            "v8.0.1 完成",
            "问题X求解/\n├─",
            "箱线+原始散点",
            "约 3--4 个",
        ):
            self.assertNotIn(token, self.root_skill)

    def test_project_instructions_is_procedure_not_duplicate_contract(self):
        for required in (
            "scripts/resolve_runtime.py",
            "模型论文框架.md",
            "state/project_state.yaml",
            "full-fidelity",
            "core/numerical_verification_contract.yaml",
            "modules/03_result_analysis.md",
            "modules/04_figure_evidence.md",
            "pre_delivery_gates",
            "SKILL_CHANGE_GOVERNANCE.md",
        ):
            self.assertIn(required, self.instructions)
        for duplicated in (
            "问题X求解.py",
            "问题X结果深化分析.py",
            "required / inline / not_applicable",
            "命题 0--4",
            "主比较允许中高饱和",
        ):
            self.assertNotIn(duplicated, self.instructions)

    def test_current_release_carriers_are_802(self):
        bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))
        plugin = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(str(bootstrap["skill_version"]), "8.0.2")
        self.assertEqual(str(plugin["version"]), "8.0.2")
        self.assertIn("version: 8.0.2", self.root_skill)
        self.assertTrue((ROOT / "README.md").read_text(encoding="utf-8").startswith("# mathmodel-skill v8.0.2"))
        self.assertTrue((ROOT / "core/hsk_core_policy.md").read_text(encoding="utf-8").startswith("# HSK Core Policy v8.0.2"))
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertTrue(changelog.startswith("# Changelog\n\n## Current release: 8.0.2"))
        for relative in (
            "core/workflow_router.yaml",
            "core/module_manifest.yaml",
            "core/output_contract.yaml",
            "core/writing_runtime_contract.yaml",
            "config/prose_audit_patterns.yaml",
        ):
            data = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))
            self.assertEqual(str(data["version"]), "8.0.2", relative)

    def test_historical_801_audit_remains_historical(self):
        audit = (ROOT / "docs/v801_chapter_capability_preservation_audit.md").read_text(encoding="utf-8")
        self.assertIn("v8.0.1", audit)
        review_test = (ROOT / "tests/test_v801_chapter_capability_preservation.py").read_text(encoding="utf-8")
        self.assertIn("v7.20/v8.0.1", review_test)


if __name__ == "__main__":
    unittest.main()
'''


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected exactly one occurrence of {old!r}, got {count}")
    write(path, text.replace(old, new, 1))


def main() -> None:
    write("SKILL.md", SKILL_TEXT)
    write("skills/mathmodel-skill/SKILL.md", SKILL_TEXT)
    write("PROJECT_INSTRUCTIONS.md", PROJECT_INSTRUCTIONS)
    write("tests/test_v802_entrypoint_surface_slimming.py", SURFACE_TEST)

    replacements = {
        "core/bootstrap.yaml": ("skill_version: 8.0.1", "skill_version: 8.0.2"),
        "core/workflow_router.yaml": ("version: 8.0.1", "version: 8.0.2"),
        "core/module_manifest.yaml": ("version: 8.0.1", "version: 8.0.2"),
        "core/output_contract.yaml": ("version: 8.0.1", "version: 8.0.2"),
        "core/writing_runtime_contract.yaml": ("version: 8.0.1", "version: 8.0.2"),
        "config/prose_audit_patterns.yaml": ("version: 8.0.1", "version: 8.0.2"),
        ".codex-plugin/plugin.json": ('"version": "8.0.1"', '"version": "8.0.2"'),
        "core/hsk_core_policy.md": ("# HSK Core Policy v8.0.1", "# HSK Core Policy v8.0.2"),
    }
    for path, (old, new) in replacements.items():
        replace_once(path, old, new)

    current_health = read("tests/test_v7141_skill_health.py")
    if current_health.count("8.0.1") < 4:
        raise RuntimeError("current health test no longer has the expected current-version literals")
    write("tests/test_v7141_skill_health.py", current_health.replace("8.0.1", "8.0.2"))

    writing_runtime_test = read("tests/test_v800_writing_runtime.py")
    if writing_runtime_test.count('"8.0.1"') != 1:
        raise RuntimeError("writing runtime test current-version assertion drifted")
    write("tests/test_v800_writing_runtime.py", writing_runtime_test.replace('"8.0.1"', '"8.0.2"', 1))

    readme = read("README.md")
    if not readme.startswith("# mathmodel-skill v8.0.1\n"):
        raise RuntimeError("README current heading drifted")
    readme = readme.replace("# mathmodel-skill v8.0.1\n", "# mathmodel-skill v8.0.2\n", 1)
    marker = "## v8.0.1：Chapter Capability Preservation\n"
    if readme.count(marker) != 1:
        raise RuntimeError("README v8.0.1 history marker drifted")
    release_note = (
        "## v8.0.2：Entrypoint Surface Slimming\n\n"
        "本补丁不改变数学建模 runtime、Model Approval、03A/03B、Workbook/Project State、Python/MATLAB/LaTeX ownership 或写作 Authority。"
        "它把 `SKILL.md` 与 `PROJECT_INSTRUCTIONS.md` 收缩为启动程序、稳定硬边界和 Authority 指针，删除此前复制在入口中的版本演进、数值阶段、Figure 与逐章写作细则；"
        "root/package Skill 继续完全一致，resolver 仍决定最小 route-specific load。历史 v8.0.1 能力保全说明保留在下方和对应审计文档中。\n\n"
    )
    write("README.md", readme.replace(marker, release_note + marker, 1))

    changelog = read("CHANGELOG.md")
    old_heading = "## Current release: 8.0.1\n"
    if changelog.count(old_heading) != 1:
        raise RuntimeError("CHANGELOG current release heading drifted")
    new_top = (
        "## Current release: 8.0.2\n\n"
        "- Slimmed `SKILL.md` and packaged `skills/mathmodel-skill/SKILL.md` to discovery, startup delegation, stable hard boundaries and Authority pointers instead of duplicating detailed domain contracts and release-history rulebooks.\n"
        "- Slimmed `PROJECT_INSTRUCTIONS.md` to project startup/recovery, execution ownership, writing/delivery delegation and repository-maintenance procedure; detailed preprocessing, 03A/03B, figure, algorithm and writing semantics remain in their single Authorities.\n"
        "- Preserved exact root/package Skill parity, bootstrap-first `resolve_runtime.py` routing, Human Model Approval, user-owned full-fidelity execution, accepted-workbook numeric facts, MATLAB non-recomputation, Template-First writing, legacy isolation and resolver-returned pre-delivery gates.\n"
        "- Added regression coverage that prevents versioned business rulebooks from regrowing inside the entrypoints while keeping the v8.0.1 chapter-capability audit explicitly historical.\n\n"
        "## Previous release: 8.0.1\n"
    )
    write("CHANGELOG.md", changelog.replace(old_heading, new_top, 1))

    status_path = "docs/v801_skill_health_remediation_status.md"
    status = read(status_path)
    status = status.replace("| Phase 2 | in_progress | 归档已发生事实漂移的 v7.16 Branch Protection 施工计划 |", "| Phase 2 | complete | 旧 v7.16 Branch Protection 施工计划已归档，active path 只保留 current pointer |")
    status = status.replace("| Phase 3 | pending | Active Entrypoint Surface Slimming |", "| Phase 3 | in_progress | Active Entrypoint Surface Slimming；目标 patch `8.0.2` |")
    write(status_path, status)

    print("v8.0.2 entrypoint slimming source migration applied")


if __name__ == "__main__":
    main()
