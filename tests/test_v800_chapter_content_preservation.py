from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_runtime():
    scripts = ROOT / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    path = scripts / "resolve_runtime.py"
    spec = importlib.util.spec_from_file_location("resolve_runtime_v800_chapters", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestV800ChapterContentPreservation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = (ROOT / "modules/05_writing/paper_writing_protocol.md").read_text(
            encoding="utf-8"
        )

    def test_compact_cumcm_route_loads_chapter_content_authority(self):
        plan = load_runtime().resolve_runtime("latex", competition="CUMCM")
        self.assertIn("modules/05_writing/paper_writing_protocol.md", plan["load_order"])
        self.assertLess(
            plan["load_order"].index("modules/05_writing/paper_writing_protocol.md"),
            plan["load_order"].index("modules/05_writing/latex.md"),
        )
        runtime = yaml.safe_load(
            (ROOT / "core/writing_runtime_contract.yaml").read_text(encoding="utf-8")
        )
        capabilities = runtime["semantic_capabilities"]["chapter_content_from_protocol"]
        self.assertIn("abstract_per_question_information_closure", capabilities)
        self.assertIn("problem_restatement_without_prompt_copying", capabilities)
        self.assertIn("coherent_problem_analysis", capabilities)

    def test_problem_restatement_preserves_semantics_without_copying_prompt(self):
        for requirement in (
            "不得照抄原题",
            "先从原题抽取对象、条件、量词、单位、边界和输出",
            "不能成为漏掉条件或改变口径的理由",
            "不提前写正式模型名、公式、算法、最终数值",
        ):
            self.assertIn(requirement, self.protocol)

    def test_problem_analysis_is_a_continuous_modeling_argument(self):
        for requirement in (
            "逻辑连续的自然段",
            "困难转化为可建模任务",
            "不得写成互不承接的",
            "散乱短句",
            "软件流水线",
            "真实继承和结构增量",
        ):
            self.assertIn(requirement, self.protocol)

    def test_abstract_keeps_full_per_question_information_chain(self):
        chain = (
            "针对的对象/任务",
            "建立的标准模型类型与题目专属模型",
            "决定模型的目标、关键条件或核心约束",
            "使用的数学处理、算法或 solver",
            "高精度核心结果/方案",
            "已实施检验对稳定性、误差或适用边界的证据",
            "对设问的直接结论",
        )
        positions = [self.protocol.index(item) for item in chain]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("内容合同而不是固定句式", self.protocol)
        self.assertIn("绝不能写“敏感性检验显示模型稳定”", self.protocol)

    def test_remaining_chapter_capabilities_are_explicit(self):
        for heading_or_rule in (
            "### 6.3 模型假设与符号说明",
            "说明它影响模型的哪个部分",
            "## 15. 模型评价、逐问结论与附录",
            "不新增模型、数据、推导或未经验证的主张",
            "正文必须保留理解模型与结论所需的",
        ):
            self.assertIn(heading_or_rule, self.protocol)

    def test_canonical_template_carries_non_authoritative_execution_cues(self):
        abstract = (ROOT / "templates/latex/cumcm/hsk/frontmatter/abstract.tex").read_text(
            encoding="utf-8"
        )
        restatement = (
            ROOT / "templates/latex/cumcm/hsk/sections/01_problem_statement.tex"
        ).read_text(encoding="utf-8")
        analysis = (ROOT / "templates/latex/cumcm/hsk/sections/02_problem_analysis.tex").read_text(
            encoding="utf-8"
        )
        self.assertIn("目标/关键条件或约束", abstract)
        self.assertIn("不得为了补齐链条虚构", abstract)
        self.assertIn("不照抄原题", restatement)
        self.assertIn("不得为了改写漏掉", restatement)
        self.assertIn("逻辑连续的自然段", analysis)
        self.assertIn("不写成散乱短句、名词清单或软件流水线", analysis)

    def test_framework_and_abstract_check_preserve_the_same_information_contract(self):
        framework = (ROOT / "templates/model/model_paper_framework.md").read_text(
            encoding="utf-8"
        )
        check = (ROOT / "templates/writing/abstract_result_check.md").read_text(
            encoding="utf-8"
        )
        for text in (framework, check):
            self.assertIn("任务/对象", text)
            self.assertIn("目标或决定性条件", text)
            self.assertIn("真实检验证据", text)
            self.assertIn("直接", text)
        self.assertIn("不得为了套用摘要信息链虚构", check)


if __name__ == "__main__":
    unittest.main()
