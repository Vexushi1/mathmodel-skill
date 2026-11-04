"""B-stage CUMCM writing contracts: example titles, evidence narrative and precision."""
from pathlib import Path
import importlib.util
import shutil
import sys
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates/latex/cumcm/hsk"


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "cumcm_b_validator", ROOT / "scripts/validate_template_manifest.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CUMCMWritingBTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = yaml.safe_load((TEMPLATE / "template_manifest.yaml").read_text(encoding="utf-8"))
        cls.reasoning = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))
        cls.protocol = (ROOT / "modules/05_writing/paper_writing_protocol.md").read_text(encoding="utf-8")
        cls.cleanup = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")

    def test_maintained_example_headings_are_consistent(self):
        self.assertEqual(
            self.manifest["cumcm_question_section"]["default_complex_question_headings"],
            ["XX模型的建立", "模型求解", "模型求解结果与分析"])
        self.assertEqual(self.manifest["cumcm_question_section"]["optional_validation_headings"],
                         ["模型检验", "模型检验与对照"])
        self.assertEqual(load_validator().validate_template_manifest(TEMPLATE / "template_manifest.yaml"), [])
        for name in ("06_question1.tex", "07_question2.tex", "08_question3.tex"):
            text = (TEMPLATE / "sections" / name).read_text(encoding="utf-8")
            active = "\n".join(line.split("%", 1)[0] for line in text.splitlines())
            self.assertIn(r"\subsection{模型求解结果与分析}", active)
            self.assertNotIn(r"\subsection{模型检验}", active)
            self.assertNotIn(r"\subsection{求解结果}", active)

    def test_maintained_validator_rejects_legacy_and_swapped_titles(self):
        with tempfile.TemporaryDirectory() as root:
            dest = Path(root) / "hsk"
            shutil.copytree(TEMPLATE, dest)
            path = dest / "sections/06_question1.tex"
            source = path.read_text(encoding="utf-8")
            for broken in (source.replace(r"\subsection{模型求解结果与分析}",
                                          r"\subsection{求解结果}", 1),
                           source.replace(r"\subsection{模型求解}",
                                          r"\subsection{模型检验}", 1)):
                path.write_text(broken, encoding="utf-8")
                self.assertTrue(load_validator().validate_template_manifest(dest / "template_manifest.yaml"))

    def test_result_narrative_never_implies_unexecuted_03b(self):
        for phrase in ("主结果 → 分析动机 → 真实证据 → 结论回收",
                       "300 次与 1200 次迭代", "不能证明全局最优",
                       "不为了语言衔接生成新 03B"):
            self.assertIn(phrase, self.protocol)
        self.assertIn("Paper Writing Protocol §11", self.cleanup)

    def test_two_decimals_only_for_ordinary_display(self):
        policy = self.reasoning["numeric_style_contract"]
        self.assertEqual(policy["ordinary_display_default"]["governance_level"], "recommendation")
        self.assertEqual(policy["ordinary_display_default"]["decimal_places"], 2)
        self.assertIn("core_answers_or_submission_values",
                      policy["ordinary_display_default"]["exceptions"])
        self.assertEqual(policy["high_precision_default"]["preferred_decimal_places_when_not_otherwise_specified"],
                         [6, 7])
        self.assertIn("不改 accepted 工作簿", self.cleanup)

    def test_evaluation_budget_is_not_a_hard_quota(self):
        rule = self.reasoning["model_evaluation"]
        self.assertEqual(rule["strengths_usual_target"], 3)
        self.assertFalse(rule["count_relation_required"])
        self.assertIn("不机械增加推广小节", rule["rule"])


if __name__ == "__main__":
    unittest.main()
