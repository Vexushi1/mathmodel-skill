from __future__ import annotations

import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_resolver():
    spec = importlib.util.spec_from_file_location(
        "resolve_workflow_v861", ROOT / "scripts/resolve_workflow.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestV861ActiveConsistencySemanticDrift(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))
        cls.output = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        cls.reasoning = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))
        cls.manifest = yaml.safe_load((ROOT / "templates/latex/cumcm/hsk/template_manifest.yaml").read_text(encoding="utf-8"))
        cls.resolver = load_resolver()

    def test_v860_evaluation_closes_release_state_without_erasing_candidate_history(self):
        text = (ROOT / "docs/v860_model_construction_solution_rationale_evaluation.md").read_text(encoding="utf-8")
        self.assertIn("## 0. Final Release Status", text)
        self.assertIn("41373e1a0ce3472df2c5afc15a3f4c0b9db379fa", text)
        self.assertIn("HSK Skill CI #2384", text)
        self.assertIn("release_status = released", text)
        self.assertIn("Candidate-stage CI 历史观察", text)
        self.assertIn("release_status = pending", text)
        self.assertIn("candidate-stage historical observations", text)

    def test_older_evaluations_are_explicit_historical_non_authorities(self):
        for relative in (
            "docs/v840_author_reasoning_evaluation.md",
            "docs/v850_author_reasoning_voice_evaluation.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("historical implementation/evaluation record", text, relative)
            self.assertIn("runtime authority = none", text, relative)
            self.assertIn("Current repository status", text, relative)

    def test_all_release_headings_are_machine_readable(self):
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        semver_headings = [
            line for line in text.splitlines()
            if re.match(r"^## .*?\b\d+\.\d+\.\d+$", line)
        ]
        self.assertGreaterEqual(len(semver_headings), 3)
        pattern = re.compile(r"^## (Current|Previous) release: (\d+\.\d+\.\d+)$")
        parsed = []
        for line in semver_headings:
            match = pattern.match(line)
            self.assertIsNotNone(match, line)
            parsed.append(match.groups())
        self.assertEqual(parsed[0], ("Current", str(self.bootstrap["skill_version"])))
        versions = [version for _, version in parsed]
        self.assertEqual(len(versions), len(set(versions)))
        self.assertTrue(all(kind == "Previous" for kind, _ in parsed[1:]))

    def test_template_fixed_tokens_are_smoke_only_and_runtime_structure_is_adaptive(self):
        fixed = self.manifest["fixed_template_checks"]
        self.assertEqual(fixed["role"], "maintained_example_smoke_only")
        self.assertFalse(fixed["runtime_semantic_authority"])
        self.assertEqual(fixed["literal_subsection_tokens_apply_to"], "sections/06_question1.tex")
        self.assertIn("runtime_required_headings", fixed["must_not_infer"])
        question = self.manifest["cumcm_question_section"]
        self.assertEqual(question["internal_structure"], "adaptive")
        self.assertEqual(question["default_complex_question_headings_role"], "maintained_example_profile_only")
        adaptive = self.reasoning["model_establishment_solution_narrative"]["within_question_subsection_architecture"]["adaptive_separation"]
        self.assertIn("each_candidate_heading_has_little_independent_content", adaptive["keep_continuous_when_all"])
        self.assertIn("independent_structural_reduction", adaptive["separate_when_any"])

    def test_a196_is_provenance_not_runtime_model_or_solver_authority(self):
        isolation = self.manifest["reference_semantic_isolation"]
        self.assertEqual(isolation["a196_role"], "provenance_and_chapter_topology_only")
        self.assertFalse(isolation["runtime_writing_semantic_authority"])
        self.assertFalse(isolation["runtime_internal_subsection_authority"])
        self.assertFalse(isolation["model_or_solver_selection_authority"])
        reasoning_text = (ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8").lower()
        router_text = (ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8").lower()
        self.assertNotIn("a196", reasoning_text)
        self.assertNotIn("a196", router_text)

    def test_output_contract_exposes_v86_reasoning_owners_without_copying_rules(self):
        policy = self.output["writing_policy"]
        self.assertEqual(
            policy["model_construction_rationale_contract"],
            "core/writing_reasoning_contract.yaml#model_construction_rationale",
        )
        self.assertEqual(
            policy["numerical_parameter_evidence_contract"],
            "core/writing_reasoning_contract.yaml#numerical_parameter_evidence",
        )
        self.assertIn("model_construction_rationale", self.reasoning)
        self.assertIn("numerical_parameter_evidence", self.reasoning)

    def test_runtime_router_distinguishes_raw_candidate_surface_from_effective_plan(self):
        text = (ROOT / "RUNTIME_ROUTER.md").read_text(encoding="utf-8")
        self.assertIn("Declarative candidate surface", text)
        self.assertIn("effective plan", text)
        self.assertIn("raw manifest", text)
        self.assertIn("resolver 返回计划", text)

    def test_resolved_boundaries_remain_effective(self):
        unapproved = self.resolver.resolve_workflow(
            "full_solution", objective="optimization", preprocessing_decision="not_needed"
        )
        self.assertEqual(unapproved["pause_state"], "awaiting_model_approval")
        self.assertIn("awaiting_model_approval", unapproved["terminal_outputs"])
        self.assertNotIn("locked_model_spec", unapproved["terminal_outputs"])
        self.assertNotIn("modules/03_solve_validate.md", unapproved["modules"])

        preprocessing = self.resolver.resolve_workflow(
            "full_solution",
            objective="optimization",
            preprocessing_decision="project_level",
            available_artifacts=["locked_model_spec"],
        )
        self.assertEqual(preprocessing["pause_state"], "awaiting_user_preprocessing")
        self.assertIn("modules/03_data_preprocessing.md", preprocessing["modules"])
        self.assertNotIn("modules/03_solve_validate.md", preprocessing["modules"])

        solve = self.resolver.resolve_workflow(
            "full_solution",
            objective="optimization",
            preprocessing_decision="not_needed",
            available_artifacts=["locked_model_spec"],
        )
        self.assertEqual(solve["pause_state"], "awaiting_user_execution")
        self.assertIn("modules/03_solve_validate.md", solve["modules"])
        self.assertIn("python_code", solve["terminal_outputs"])

    def test_current_release_carriers_remain_in_sync_during_patch(self):
        current = str(self.bootstrap["skill_version"])
        plugin = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(str(plugin["version"]), current)
        for relative in ("SKILL.md", "skills/mathmodel-skill/SKILL.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertRegex(text, rf"(?m)^version:\s*{re.escape(current)}$")


if __name__ == "__main__":
    unittest.main()
