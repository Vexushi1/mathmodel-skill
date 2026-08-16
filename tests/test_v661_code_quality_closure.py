import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class TestV661CodeQualityClosure(unittest.TestCase):
    def test_entry_docs_match_current_output_contract(self):
        current = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))["skill_version"]
        for relative in ("SKILL.md", "README.md", "skills/mathmodel-skill/SKILL.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(str(current), text, relative)
            self.assertNotIn("└─ 图表/", text, relative)
            self.assertNotIn("输出完整版代码、运行配置和说明", text, relative)
            self.assertIn("问题X结果深化分析.py", text, relative)

    def test_workbook_runtime_checkers_exist(self):
        data = yaml.safe_load((ROOT / "core/workbook_schema.yaml").read_text(encoding="utf-8"))
        runtime = data["runtime_enforcement"]
        self.assertNotIn("artifact_checker", runtime)
        for key in (
            "code_delivery_checker",
            "returned_workbook_checker",
            "project_sync",
            "shared_validator",
        ):
            self.assertTrue((ROOT / runtime[key]).is_file(), (key, runtime[key]))

    def test_bootstrap_registers_code_quality_authority(self):
        data = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))
        self.assertEqual(
            data["authoritative_sources"]["code_quality"],
            "core/code_quality_contract.yaml",
        )

    def test_matlab_handoff_has_no_default_export_or_evidence_file(self):
        data = yaml.safe_load((ROOT / "core/workbook_schema.yaml").read_text(encoding="utf-8"))
        evidence = data["matlab_handoff"]["evidence_chain"]
        self.assertFalse(evidence["declared_export_must_exist"])
        self.assertFalse(evidence["formal_figure_must_not_predate_workbook_or_script"])
        self.assertFalse(evidence["independent_evidence_file_default"])
        self.assertNotIn("figure_evidence.yaml", evidence["provenance_record"])

    def test_code_quality_contract_thresholds_are_preserved_for_both_scripts(self):
        data = yaml.safe_load((ROOT / "core/code_quality_contract.yaml").read_text(encoding="utf-8"))
        current = str(yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))["skill_version"])
        # v7.5.1 is a writing-only patch. The code-quality domain contract did not
        # change behavior, so it intentionally retains its v7.4.2 release marker.
        self.assertEqual(current, "7.5.1")
        self.assertEqual(str(data["skill_version"]), "7.4.2")
        self.assertEqual(data["line_count"]["target_max"], 500)
        self.assertEqual(data["line_count"]["hard_max"], 700)
        self.assertEqual(data["line_count"]["exemption_max"], 900)
        self.assertEqual(data["function_size"]["hard_max"], 120)
        self.assertEqual(data["parameter_count"]["hard_max"], 12)
        self.assertIn("问题X求解/问题X求解.py", data["scope"])
        self.assertIn("问题X求解/问题X结果深化分析.py", data["scope"])


if __name__ == "__main__":
    unittest.main()
