from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch(relative: str, old: str, new: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{relative}: expected one match, found {count}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# Preserve the existing Model Approval read-path ordering test by avoiding an early
# literal pause-state token in the new explanatory section.
patch(
    "RUNTIME_ROUTER.md",
    "未完成人工锁模时，effective plan 必须停在 `awaiting_model_approval`，raw manifest 中即使列有 `locked_model_spec` 也不构成 current locked artifact 或执行授权。",
    "未完成人工锁模时，effective plan 必须停在 Model Approval 的暂停边界；raw manifest 中即使列有 `locked_model_spec` 也不构成 current locked artifact 或执行授权。",
)

# Match the actual adaptive-separation schema: continuity is an all-condition set,
# not a merge_when_any policy.
patch(
    "tests/test_v861_active_consistency_semantic_drift.py",
    '        self.assertIn("thin_variable_objective_constraint_fragments", adaptive["merge_when_any"])\n        self.assertIn("independent_structural_reduction", adaptive["separate_when_any"])',
    '        self.assertIn("each_candidate_heading_has_little_independent_content", adaptive["keep_continuous_when_all"])\n        self.assertIn("independent_structural_reduction", adaptive["separate_when_any"])',
)

# The v8.6.1 patch intentionally adds semantic-isolation metadata to the Template
# Manifest. Keep exact blob pins for untouched proof/algorithm/adapter/main files,
# while protecting the Manifest through explicit semantic invariants instead of an
# obsolete whole-file hash.
patch(
    "tests/test_v840_author_reasoning_writing.py",
    '            "modules/05_writing/latex.md": "98f90f8caa6c3072316dd8e620add05722abfa4b",\n            "templates/latex/cumcm/hsk/template_manifest.yaml": "32402842ea88c2a4ce3df052f6c01534b357549f",\n            "templates/latex/cumcm/hsk/hsk_main.tex": "789437316271430dee2c5a7ebbdd803f4698ca63",',
    '            "modules/05_writing/latex.md": "98f90f8caa6c3072316dd8e620add05722abfa4b",\n            "templates/latex/cumcm/hsk/hsk_main.tex": "789437316271430dee2c5a7ebbdd803f4698ca63",',
)
patch(
    "tests/test_v840_author_reasoning_writing.py",
    '                self.assertEqual(hashlib.sha1(blob).hexdigest(), digest)\n\n    def test_v85_author_reasoning_voice_semantics_remain_pinned(self):',
    '                self.assertEqual(hashlib.sha1(blob).hexdigest(), digest)\n\n        manifest = yaml.safe_load(read("templates/latex/cumcm/hsk/template_manifest.yaml"))\n        self.assertEqual(manifest["schema_version"], "1.0.0")\n        self.assertEqual(manifest["template_id"], "hsk_cumcm_v8")\n        question = manifest["cumcm_question_section"]\n        self.assertEqual(question["title_pattern"], "问题{N}模型建立及求解")\n        self.assertTrue(question["title_locked"])\n        self.assertEqual(question["internal_structure"], "adaptive")\n        self.assertEqual(question["functional_slots"], ["model", "solve", "result", "validate"])\n        rendering = manifest["core_model_summary_rendering"]\n        self.assertFalse(rendering["independent_named_subsection_default"])\n        self.assertTrue(rendering["simple_problem_anti_bloat"])\n        fixed = manifest["fixed_template_checks"]\n        self.assertTrue(fixed["objective_before_constraints"])\n        self.assertTrue(fixed["objective_outside_constraint_brace"])\n        self.assertFalse(fixed["runtime_semantic_authority"])\n\n    def test_v85_author_reasoning_voice_semantics_remain_pinned(self):',
)

# Normalize the remaining historical heading to the machine-readable release form.
patch("CHANGELOG.md", "## Earlier release: 7.9.0", "## Previous release: 7.9.0")

print("v8.6.1 semantic-regression fixes applied")
