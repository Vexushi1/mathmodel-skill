"""Author-voice routing and conservative diagnostics, not an authorship detector.

Instruction checks protect the intended boundary. Audit examples exercise actual
diagnostics; they do not establish mathematical validity or overall prose quality.
"""
import importlib.util
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = "modules/05_writing/paper_writing_protocol.md#7.3-作者视角与建模解释"


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def load_audit(filename):
    spec = importlib.util.spec_from_file_location(f"v831_{filename}", ROOT / "scripts" / f"{filename}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class AuthorReasoningVoiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.surface = load_audit("audit_v8_writing_surface")
        cls.prose = load_audit("audit_paper_prose")
        cls.protocol = read("modules/05_writing/paper_writing_protocol.md")
        cls.runtime = yaml.safe_load(read("core/writing_runtime_contract.yaml"))
        cls.reasoning = yaml.safe_load(read("core/writing_reasoning_contract.yaml"))

    def test_question_stage_reads_shared_authority_before_writing(self):
        stages = self.runtime["template_first_progressive_authoring"]["stages"]
        stage = next(item for item in stages if item["id"] == "question_model_solution_result_validation")
        self.assertIn(AUTHORITY, stage["read_now"])
        self.assertEqual(
            self.reasoning["prose_style"]["human_reasoning_trace"]["prose_authority"], AUTHORITY
        )
        for consumer in ("modules/05_writing/ai_cleanup.md", "modules/06_review_delivery.md"):
            self.assertIn(AUTHORITY.split("modules/05_writing/", 1)[1], read(consumer))
        self.assertIn("### 7.3 作者视角与建模解释", self.protocol)

    def test_reasoning_information_is_not_a_fixed_voice_template(self):
        section = self.protocol.split("### 7.3 作者视角与建模解释", 1)[1].split("## 8.", 1)[0]
        for requirement in (
            "当前缺口", "选择依据", "数学处理", "解释与用途",
            "不是固定四句话", "不要求新增第一人称", "不把原本自然的表达统一改成",
            "不能代替证明", "不为增加人工感编造", "不影响真实 AI 使用披露",
            "简单解析或直接计算问题", "环境与格式不变",
        ):
            self.assertIn(requirement, section)
        cleanup = read("modules/05_writing/ai_cleanup.md")
        self.assertIn("不是删除第一人称本身", cleanup)
        self.assertIn("不替作者编造理由", cleanup)
        self.assertIn("公式来源、推导、命题证明、伪代码及求解细节", cleanup)
        self.assertEqual(self.reasoning["schema_version"], "1.7.0")
        trace = self.reasoning["prose_style"]["human_reasoning_trace"]
        self.assertEqual(trace["subject_roles"]["quota"], "none")
        self.assertIn("pronoun_frequency_target", trace["prohibit"])
        self.assertIn("authorship_inference_from_voice", trace["prohibit"])

    def test_explanatory_voice_variants_have_identical_clean_diagnostics(self):
        # Finite candidate enumeration is illustrative, not a current paper result.
        for voice in ("我们需要", "需要", "当前任务需要"):
            with self.subTest(voice=voice):
                tex = (
                    r"\section{问题一模型建立及求解}" "\n"
                    r"\subsection{模型求解}" "\n"
                    f"前述边界已将决策限制在有限候选域，{voice}判断哪些候选满足原约束，"
                    "再通过枚举法逐一评价可行候选的目标函数。\n\n"
                    "计算输出保留候选对应的决策变量及其目标值，供下一步比较可行方案。"
                    "\n" r"\subsection{求解结果}" "\n"
                    r"在候选 $x\in\{1,2,3\}$ 均可行、目标为最小化 $(x-2)^2$ 的示例中，"
                    r"逐一评价得到目标值依次为 $1,0,1$，故推荐 $x=2$；其目标值低于其余可行候选。"
                )
                self.assertEqual(self.surface.audit_text(tex), [])
                self.assertEqual(self.prose.audit_text(tex), [])

    def test_algorithm_announcement_without_structure_is_still_reported(self):
        for subject in ("我们", "本文", ""):
            with self.subTest(subject=subject):
                tex = (
                    r"\section{问题一模型建立及求解}" "\n"
                    r"\subsection{模型求解}" "\n"
                    f"{subject}采用遗传算法求解，该算法收敛速度快。"
                )
                codes = {item.code for item in self.surface.audit_text(tex)}
                self.assertIn("solver_first_narrative", codes)

    def test_first_person_does_not_exempt_missing_citation_evidence(self):
        tex = r"我们根据文献\cite{missing}引入当前关系。"
        findings = self.prose.audit_bibliography(tex, None)
        self.assertTrue(any(f.code == "bibliography_missing" and f.severity == "blocking" for f in findings))

    def test_subjective_wording_does_not_exempt_registered_claim_conflict(self):
        tex = "我们认为当前解是全局最优。"
        framework = "Headline Claim Evidence Level：`HEURISTIC`\n当前主张：全局最优"
        findings = self.prose.audit_framework_consistency(tex, framework)
        self.assertTrue(any(
            f.code == "heuristic_global_optimum_scope_conflict" and f.severity == "blocking"
            for f in findings
        ))


if __name__ == "__main__":
    unittest.main()
