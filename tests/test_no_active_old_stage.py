import unittest,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class OldStageTest(unittest.TestCase):
    def test_active_files_do_not_depend_on_old_stage(self):
        for top in ['core','modules','packs']:
            for f in (ROOT/top).rglob('*'):
                if f.suffix not in {'.md','.yaml'}: continue
                text=f.read_text(encoding='utf-8')
                self.assertNotRegex(text,r'references/hsk_stage_',str(f))
                self.assertNotRegex(text,r'feedback_layer[1-4]',str(f))
if __name__=='__main__': unittest.main()
