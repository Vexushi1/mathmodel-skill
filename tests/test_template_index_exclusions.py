import importlib.util
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TARGET = Path("templates/latex/cumcm/hsk/sections/10_ai_tool_statement.tex")


def load_generate_indexes():
    path = ROOT / "scripts/generate_indexes.py"
    spec = importlib.util.spec_from_file_location("generate_indexes_template_exclusion", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestTemplateIndexExclusions(unittest.TestCase):
    def test_ai_statement_remains_active_but_is_not_advertised_as_template(self):
        module = load_generate_indexes()
        files = module.iter_files()

        self.assertTrue((ROOT / TARGET).is_file())
        self.assertIn(TARGET, files)
        self.assertNotIn(TARGET, module.template_index_files(files))

        payloads = module.generated_payloads()
        template_index = payloads[module.TEMPLATE_INDEX]
        skill_index = payloads[module.SKILL_INDEX]
        manifest = payloads[module.MANIFEST]

        self.assertNotIn(TARGET.as_posix(), template_index)
        self.assertIn(TARGET.as_posix(), skill_index)
        self.assertIn(f"  {TARGET.as_posix()}", manifest)

        main_tex = (ROOT / "templates/latex/cumcm/hsk/hsk_main.tex").read_text(encoding="utf-8")
        self.assertIn(r"% \input{sections/10_ai_tool_statement}", main_tex)
        active_main = "\n".join(line.split("%", 1)[0] for line in main_tex.splitlines())
        self.assertNotIn(r"\input{sections/10_ai_tool_statement}", active_main)

        template_manifest = yaml.safe_load(
            (ROOT / "templates/latex/cumcm/hsk/template_manifest.yaml").read_text(encoding="utf-8")
        )
        ai_slot = next(
            slot
            for slot in template_manifest["paper_skeleton"]["ordered_slots"]
            if slot["id"] == "ai_disclosure"
        )
        self.assertEqual(ai_slot["source"], TARGET.relative_to("templates/latex/cumcm/hsk").as_posix())
        self.assertFalse(ai_slot["required"])
        self.assertFalse(ai_slot["default_active"])


if __name__ == "__main__":
    unittest.main()
