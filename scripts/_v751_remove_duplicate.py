from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
model_path = ROOT / "modules/02_model_design.md"
text = model_path.read_text(encoding="utf-8")
marker = "### 4.3 数值参数证据计划"
positions = []
start = 0
while True:
    idx = text.find(marker, start)
    if idx < 0:
        break
    positions.append(idx)
    start = idx + len(marker)
if len(positions) != 2:
    raise SystemExit(f"expected exactly two 4.3 sections before cleanup, found {len(positions)}")
second = positions[1]
end = text.find("## 5. 复杂度合理性复审", second)
if end < 0:
    raise SystemExit("section 5 boundary not found")
text = text[:second] + text[end:]
if text.count(marker) != 1:
    raise SystemExit("4.3 duplicate cleanup failed")
model_path.write_text(text, encoding="utf-8")

test_path = ROOT / "tests/test_v751_architecture_slimming.py"
test = test_path.read_text(encoding="utf-8")
anchor = "    def test_minimal_router_default_load_remains_single_policy(self):\n"
if anchor not in test:
    raise SystemExit("test insertion anchor missing")
addition = '''    def test_model_design_reasoning_sections_are_not_duplicated(self):\n        model_design = (ROOT / "modules/02_model_design.md").read_text(encoding="utf-8")\n        self.assertEqual(model_design.count("### 4.1 核心公式推理链"), 1)\n        self.assertEqual(model_design.count("### 4.2 共享基础与跨问模型增量"), 1)\n        self.assertEqual(model_design.count("### 4.3 数值参数证据计划"), 1)\n        self.assertLess(model_design.index("### 4.3 数值参数证据计划"), model_design.index("## 5. 复杂度合理性复审"))\n\n'''
test = test.replace(anchor, addition + anchor, 1)
test_path.write_text(test, encoding="utf-8")
