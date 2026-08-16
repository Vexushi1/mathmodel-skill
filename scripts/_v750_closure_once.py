#!/usr/bin/env python3
"""One-shot v7.5.0 reasoning graph closure patch; removed by workflow before final commit."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8-sig")
    if old not in text:
        raise RuntimeError(f"patch anchor missing in {rel}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"patched {rel}")


def main() -> None:
    patch(
        "core/module_manifest.yaml",
        "  code_quality: core/code_quality_contract.yaml\n  framework_template:",
        "  code_quality: core/code_quality_contract.yaml\n  writing_reasoning: core/writing_reasoning_contract.yaml\n  framework_template:",
    )
    patch(
        "core/module_manifest.yaml",
        "  formula_closure: 公式—代码—输出映射\n  semantic_closure:",
        "  formula_closure: 公式—代码—输出映射\n  formula_reasoning_chain: 核心公式Source—Derivation—Destination闭环；记录题意/定义/机制来源、关键推导与后续模型/求解/验证用途，不单独落盘\n  semantic_closure:",
    )
    patch(
        "core/module_manifest.yaml",
        "    - formula_closure\n    - semantic_closure\n    - complexity_sanity_check",
        "    - formula_closure\n    - formula_reasoning_chain\n    - semantic_closure\n    - complexity_sanity_check",
    )
    patch(
        "core/module_manifest.yaml",
        "    - formula_closure\n    - semantic_closure\n    - complexity_sanity_check\n    - validation_plan\n    - model_paper_framework\n    - semantic_governance_report",
        "    - formula_closure\n    - formula_reasoning_chain\n    - semantic_closure\n    - complexity_sanity_check\n    - validation_plan\n    - model_paper_framework\n    - semantic_governance_report",
    )
    patch(
        "core/module_manifest.yaml",
        "    - formula_closure\n    - semantic_closure\n    - complexity_sanity_check\n    - proposition_plan\n    - model_paper_framework",
        "    - formula_closure\n    - formula_reasoning_chain\n    - semantic_closure\n    - complexity_sanity_check\n    - proposition_plan\n    - model_paper_framework",
    )

    patch(
        "core/output_contract.yaml",
        "code_quality_contract: core/code_quality_contract.yaml\nbootstrap:",
        "code_quality_contract: core/code_quality_contract.yaml\nwriting_reasoning_contract: core/writing_reasoning_contract.yaml\nbootstrap:",
    )
    patch(
        "core/output_contract.yaml",
        "  expression_authority: modules/05_writing/latex.md#正文表达与章节组织协议（写作权威）\n  adaptive_sectioning_by_task_type:",
        "  expression_authority: modules/05_writing/latex.md#正文表达与章节组织协议（写作权威）\n  reasoning_contract: core/writing_reasoning_contract.yaml\n  adaptive_sectioning_by_task_type:",
    )

    patch(
        "scripts/lint_skill.py",
        '    "core/user_execution_contract.yaml", "core/code_quality_contract.yaml",\n',
        '    "core/user_execution_contract.yaml", "core/code_quality_contract.yaml", "core/writing_reasoning_contract.yaml",\n',
    )
    patch(
        "scripts/lint_skill.py",
        '    if output.get("preprocessing_contract") != "core/global_preprocessing_contract.yaml":\n        errors.append("output contract must reference preprocessing contract")\n',
        '    if output.get("preprocessing_contract") != "core/global_preprocessing_contract.yaml":\n        errors.append("output contract must reference preprocessing contract")\n    if output.get("writing_reasoning_contract") != "core/writing_reasoning_contract.yaml":\n        errors.append("output contract must reference writing-reasoning contract")\n',
    )
    patch(
        "scripts/lint_skill.py",
        '    policy = output.get("writing_policy", {})\n    if policy.get("default_mode") != "latex_first":\n',
        '    policy = output.get("writing_policy", {})\n    if policy.get("reasoning_contract") != "core/writing_reasoning_contract.yaml":\n        errors.append("writing policy must reference writing-reasoning contract")\n    if policy.get("default_mode") != "latex_first":\n',
    )

    patch(
        "tests/test_v750_writing_reasoning_architecture.py",
        "    def test_model_design_and_writing_consume_same_authority(self):\n",
        "    def test_reasoning_chain_is_registered_in_manifest_and_output_contract(self):\n        manifest = yaml.safe_load((ROOT / \"core/module_manifest.yaml\").read_text(encoding=\"utf-8\"))\n        output = yaml.safe_load((ROOT / \"core/output_contract.yaml\").read_text(encoding=\"utf-8\"))\n        self.assertEqual(manifest[\"contracts\"][\"writing_reasoning\"], \"core/writing_reasoning_contract.yaml\")\n        self.assertIn(\"formula_reasoning_chain\", manifest[\"artifact_catalog\"])\n        self.assertIn(\"formula_reasoning_chain\", manifest[\"modules\"][\"model_design\"][\"outputs\"])\n        self.assertIn(\"formula_reasoning_chain\", manifest[\"workflow_profiles\"][\"design\"][\"terminal_outputs\"])\n        self.assertEqual(output[\"writing_reasoning_contract\"], \"core/writing_reasoning_contract.yaml\")\n        self.assertEqual(output[\"writing_policy\"][\"reasoning_contract\"], \"core/writing_reasoning_contract.yaml\")\n\n    def test_model_design_and_writing_consume_same_authority(self):\n",
    )


if __name__ == "__main__":
    main()
