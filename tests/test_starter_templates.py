import ast
import importlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STARTER_DIR = ROOT / "templates/code/starter"
PIPELINE_DIR = ROOT / "templates/code/hsk_pipeline"
STARTERS = {
    "classification.py": "inference",
    "evaluation.py": "evaluation",
    "optimization.py": "optimization",
    "prediction.py": "prediction",
    "simulation.py": "simulation",
}


class TestStarterTemplates(unittest.TestCase):
    def test_starters_are_primary_only_side_effect_free_entries(self):
        forbidden = (
            "np.random.seed", "PROJECT_ROOT =", "SOLUTION_BOOK", "ROBUSTNESS_BOOK",
            "workbook_paths(", "write_workbook(", "def validate_model(",
            "run_pipeline(", "ResultAnalysisResult", "analyze_results",
            "sync_analysis_framework", "result_analysis_hook=",
        )
        for filename, objective in STARTERS.items():
            path = STARTER_DIR / filename
            text = path.read_text(encoding="utf-8")
            ast.parse(text)
            self.assertIn(f'objective="{objective}"', text)
            self.assertIn("run_primary_pipeline(", text)
            self.assertIn("evaluate_primary_quality", text)
            self.assertIn("sync_primary_framework", text)
            self.assertIn("REQUIRED_CAPABILITIES", text)
            self.assertIn('if __name__ == "__main__":', text)
            for token in forbidden:
                self.assertNotIn(token, text, f"{filename}: {token}")

    def test_importing_starters_does_not_create_outputs(self):
        code_root = str(ROOT / "templates/code")
        added = code_root not in sys.path
        previous = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        if added:
            sys.path.insert(0, code_root)
        try:
            before = {path.name for path in STARTER_DIR.glob("*.py")}
            for filename in STARTERS:
                importlib.import_module(f"starter.{Path(filename).stem}")
            after = {path.name for path in STARTER_DIR.glob("*.py")}
            self.assertEqual(before, after)
            self.assertFalse((STARTER_DIR / "结果数据表").exists())
        finally:
            sys.dont_write_bytecode = previous
            if added:
                sys.path.remove(code_root)

    def test_pipeline_keeps_split_runners_and_compatibility_api(self):
        init_text = (PIPELINE_DIR / "__init__.py").read_text(encoding="utf-8")
        pipeline_text = (PIPELINE_DIR / "main_pipeline.py").read_text(encoding="utf-8")
        for token in ("run_primary_pipeline", "run_result_analysis_pipeline", "run_pipeline"):
            self.assertIn(token, init_text)
        self.assertIn("def run_primary_pipeline(", pipeline_text)
        self.assertIn("def run_result_analysis_pipeline(", pipeline_text)
        self.assertIn("def run_pipeline(", pipeline_text)
        self.assertIn('"运行配置": solution["运行配置"]', pipeline_text)
        self.assertIn('required = {"运行配置", "分析设计", "结论稳定性汇总"}', pipeline_text)

    def test_profiles_enable_required_primary_capabilities(self):
        optimization = (STARTER_DIR / "optimization.py").read_text(encoding="utf-8")
        prediction = (STARTER_DIR / "prediction.py").read_text(encoding="utf-8")
        classification = (STARTER_DIR / "classification.py").read_text(encoding="utf-8")
        simulation = (STARTER_DIR / "simulation.py").read_text(encoding="utf-8")
        for token in ("has_explicit_constraints=True", "requires_feasibility_check=True"):
            self.assertIn(token, optimization)
        for text in (prediction, classification):
            self.assertIn("requires_out_of_sample_validation=True", text)
            self.assertIn("requires_leakage_check=True", text)
        self.assertIn("requires_convergence_diagnostic=True", simulation)
        self.assertIn("requires_uncertainty_quantification=True", simulation)

    def test_cleanup_removes_obsolete_active_templates(self):
        self.assertFalse((PIPELINE_DIR / "config.yaml").exists())
        self.assertFalse((ROOT / "templates/review/robustness_check.md").exists())
        self.assertTrue((ROOT / "templates/code/full_fidelity_config.yaml").is_file())
        self.assertTrue((ROOT / "templates/review/result_analysis_check.md").is_file())

    def test_cleanup_has_no_recreatable_or_migrated_residual_files(self):
        self.assertFalse((ROOT / "state/.gitkeep").exists())
        self.assertTrue((ROOT / "state/project_state.example.yaml").is_file())
        self.assertFalse((ROOT / "templates/latex/cumcm/cumcmthesis/example.pdf").exists())
        self.assertTrue((ROOT / "templates/latex/cumcm/cumcmthesis/example.tex").is_file())
        for name in ("hsk_find_project_root.m", "hsk_export_figure.m"):
            self.assertFalse((ROOT / "templates/matlab" / name).exists())
            self.assertTrue((ROOT / "legacy/matlab_compat" / name).is_file())


if __name__ == "__main__":
    unittest.main()
