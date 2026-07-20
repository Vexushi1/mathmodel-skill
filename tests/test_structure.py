import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class TestStructure(unittest.TestCase):
    def test_required_dirs(self):
        for rel in ['core','modules','packs/task','packs/competition','packs/artifact','templates/code','templates/matlab','templates/latex','scripts','tests','legacy']:
            self.assertTrue((ROOT/rel).exists(), rel)
    def test_plugin_wrapper(self):
        self.assertTrue((ROOT/'.codex-plugin/plugin.json').exists())
        self.assertTrue((ROOT/'skills/mathmodel-skill/SKILL.md').exists())
if __name__=='__main__': unittest.main()
