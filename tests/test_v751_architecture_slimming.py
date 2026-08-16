from pathlib import Path
import importlib.util
import sys
import unittest
import yaml

ROOT = Path(__file__).resolve().parent.parent
REASONING = "core/writing_reasoning_contract.yaml"


def load_resolver():
    path = ROOT / "scripts/resolve_workflow.py"
    spec = importlib.util.spec_from_file_location("v751_resolver", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ArchitectureSlimmingV751Tests(unittest.TestCase):
    def test_bootstrap_is_pointer_only_and_startup_budget_is_smaller(self):
        bootstrap_path = ROOT / "core/bootstrap.yaml"
        policy_path = ROOT / "core/hsk_core_policy.md"
        bootstrap = yaml.safe_load(bootstrap_path.read_text(encoding="utf-8"))
        self.assertEqual(bootstrap["authoritative_sources"]["writing_reasoning"], REASONING)
        hard = "\n".join(bootstrap["hard_invariants"])
        for duplicated_detail in (
            "Source—Derivation—Destination",
            "GA、PSO、DE",
            "Monte Carlo",
            "问题背景通常",
        ):
            self.assertNotIn(duplicated_detail, hard)
        self.assertLessEqual(bootstrap_path.stat().st_size, 6500)
        self.assertLessEqual(bootstrap_path.stat().st_size + policy_path.stat().st_size, 22000)

    def test_reasoning_contract_keeps_v750_capabilities(self):
        contract = yaml.safe_load((ROOT / REASONING).read_text(encoding="utf-8"))
        self.assertEqual(contract["formula_reasoning_chain"]["chain"], ["source", "derivation", "destination"])
        self.assertEqual(contract["shared_foundation"]["default"], "adaptive")
        self.assertEqual(contract["cross_question_progression"]["activate_when"], "actual_dependency_exists")
        self.assertIn("final_solver_selection", contract["structure_before_algorithm"]["check_order"])
        self.assertIn("optimization_tolerance", contract["numerical_parameter_evidence"]["applies_to"])
        self.assertIn("structural_consistency", contract["multi_method_validation"]["two_levels"])
        self.assertEqual(contract["prose_style"]["name"], "evidence_driven_undergraduate_academic")

    def test_route_specific_reasoning_load_is_preserved(self):
        router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        routes = router["routing"]
        for name in ("new_problem_design", "framework_sync", "proposition_proof", "model_selection", "advanced_method", "docx", "latex"):
            self.assertIn(REASONING, routes[name].get("load", []), name)
        for name in ("problem_analysis", "data_preprocessing", "code_and_solution", "result_analysis", "returned_workbook_validation", "validation", "figures", "full_submission", "review"):
            self.assertNotIn(REASONING, routes[name].get("load", []), name)

    def test_consumers_reference_authority_instead_of_losing_semantics(self):
        for relative in (
            "modules/02_model_design.md",
            "modules/05_writing/latex.md",
            "modules/05_writing/ai_cleanup.md",
            "templates/model/model_paper_framework.md",
            "packs/artifact/proposition_proof.md",
        ):
            self.assertIn(REASONING, (ROOT / relative).read_text(encoding="utf-8"), relative)
        latex = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        for marker in ("（Source）", "（Derivation）", "（Destination）", "结构化简优先于算法升级", "数值参数必须有选择证据"):
            self.assertIn(marker, latex)

    def test_taxonomy_is_lazy_for_nonclassification_routes(self):
        resolver = load_resolver()
        original = resolver.load_yaml
        calls = []

        def traced(path):
            calls.append(path)
            return original(path)

        resolver.load_yaml = traced
        plan = resolver.resolve_workflow("figures")
        self.assertNotIn(resolver.TAXONOMY_PATH, calls)
        self.assertNotIn(REASONING, plan["load_order"])
        self.assertIn("modules/04_figure_evidence.md", plan["load_order"])

        calls.clear()
        taxonomy = yaml.safe_load(resolver.TAXONOMY_PATH.read_text(encoding="utf-8"))
        objective = next(iter(taxonomy["objectives"]))
        plan = resolver.resolve_workflow("model_selection", objective=objective)
        self.assertIn(resolver.TAXONOMY_PATH, calls)
        self.assertIn(REASONING, plan["load_order"])

    def test_model_design_reasoning_sections_are_not_duplicated(self):
        model_design = (ROOT / "modules/02_model_design.md").read_text(encoding="utf-8")
        self.assertEqual(model_design.count("### 4.1 核心公式推理链"), 1)
        self.assertEqual(model_design.count("### 4.2 共享基础与跨问模型增量"), 1)
        self.assertEqual(model_design.count("### 4.3 数值参数证据计划"), 1)
        self.assertLess(model_design.index("### 4.3 数值参数证据计划"), model_design.index("## 5. 复杂度合理性复审"))

    def test_minimal_router_default_load_remains_single_policy(self):
        router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        self.assertEqual(router["default_load"], ["core/hsk_core_policy.md"])
        self.assertEqual(router["load_policy"]["principle"], "minimal_route_specific")


if __name__ == "__main__":
    unittest.main()
