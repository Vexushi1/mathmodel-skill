import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module():
    path = ROOT / "scripts" / "validate_code_delivery.py"
    spec = importlib.util.spec_from_file_location("validate_code_delivery_quality", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


CODE = load_module()


class CodeQualityContractTests(unittest.TestCase):
    def test_small_clean_code_passes(self):
        errors, warnings, metrics = CODE.code_quality_findings(
            "import math\n\ndef f(x):\n    return math.sqrt(x)\n"
        )
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(metrics["print_calls"], 0)

    def test_501_to_700_lines_warns(self):
        text = "\n".join(f"x{i} = {i}" for i in range(520))
        errors, warnings, _ = CODE.code_quality_findings(text)
        self.assertEqual(errors, [])
        self.assertTrue(any("超过目标500行" in item for item in warnings), warnings)

    def test_over_700_lines_requires_exemption(self):
        text = "\n".join(f"x{i} = {i}" for i in range(710))
        errors, _, _ = CODE.code_quality_findings(text, {})
        self.assertTrue(any("超过700行" in item for item in errors), errors)
        config = {
            "code_quality_exemption": {
                "enabled": True,
                "reason": "该问题包含多阶段约束与结果深化分析，继续拆分会破坏每问唯一脚本合同。",
            }
        }
        errors, warnings, _ = CODE.code_quality_findings(text, config)
        self.assertEqual(errors, [])
        self.assertTrue(any("复杂题豁免" in item for item in warnings), warnings)

    def test_over_900_lines_always_fails(self):
        text = "\n".join(f"x{i} = {i}" for i in range(901))
        config = {
            "code_quality_exemption": {
                "enabled": True,
                "reason": "该问题包含多阶段约束与结果深化分析，继续拆分会破坏每问唯一脚本合同。",
            }
        }
        errors, _, _ = CODE.code_quality_findings(text, config)
        self.assertTrue(any("绝对上限900行" in item for item in errors), errors)

    def test_large_function_and_many_parameters_fail(self):
        body = "\n".join("    x += 1" for _ in range(121))
        text = "def f(a,b,c,d,e,f,g,h,i,j,k,l,m):\n    x = 0\n" + body + "\n    return x\n"
        errors, _, _ = CODE.code_quality_findings(text)
        self.assertTrue(any("函数f" in item and "行硬上限" in item for item in errors), errors)
        self.assertTrue(any("13个参数" in item for item in errors), errors)

    def test_forbidden_plotting_and_debug_antipatterns_fail(self):
        text = "import matplotlib.pyplot as plt\ntry:\n    breakpoint()\nexcept:\n    pass\n"
        errors, _, _ = CODE.code_quality_findings(text)
        self.assertTrue(any("绘图库" in item for item in errors), errors)
        self.assertTrue(any("裸except" in item for item in errors), errors)
        self.assertTrue(any("breakpoint" in item for item in errors), errors)

    def test_unused_import_and_print_are_warnings(self):
        errors, warnings, _ = CODE.code_quality_findings("import os\nprint('x')\n")
        self.assertEqual(errors, [])
        self.assertTrue(any("未使用import" in item for item in warnings), warnings)
        self.assertTrue(any("print" in item for item in warnings), warnings)


if __name__ == "__main__":
    unittest.main()
