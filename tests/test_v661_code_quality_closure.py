import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class TestV661CodeQualityClosure(unittest.TestCase):
    def test_entry_docs_match_current_output_contract(self):
        for relative in ("SKILL.md", "README.md", "skills/mathmodel-skill/SKILL.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("6.6.1", text, relative)
            self.assertNotIn("└─ 图表/", text, relative)
            self.assertNotIn("输出完整版代码、运行配置和说明", text, relative)

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

    def test_code_quality_contract_thresholds(self):
        data = yaml.safe_load((ROOT / "core/code_quality_contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(data["skill_version"], "6.6.1")
        self.assertEqual(data["line_count"]["target_max"], 500)
        self.assertEqual(data["line_count"]["hard_max"], 700)
        self.assertEqual(data["line_count"]["exemption_max"], 900)
        self.assertEqual(data["function_size"]["hard_max"], 120)
        self.assertEqual(data["parameter_count"]["hard_max"], 12)


if __name__ == "__main__":
    unittest.main()
