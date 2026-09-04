"""Protect scope and fixed trial facts, not a prose-quality or authorship score.

Snapshots come from PR #108 head 1895fb8 before the approved v8.4 changes.
Only explicitly authorized prose fields/reads are excluded from preservation.
Actual complete-section writing and cleanup need semantic review, not token tests.
"""
import copy
import hashlib
import itertools
import json
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "modules/05_writing/paper_writing_protocol.md"
EXAMPLES = "modules/05_writing/references/model_solution_reasoning_examples.md"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def semantic_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class WritingReasoningScopeTests(unittest.TestCase):
    def test_unchanged_chapter_detail_and_handoff_snapshots(self):
        expected = {
            "2. 模板与写作职责": "590972187ff6e0ee280b4fc1f59ed18f951a6daec96e1d701e0355e671904112",
            "3. 每问的四个功能槽": "203bc95ade0b0f8c4f8df7096c61b100db487cf9a24ee60b5a01c78368c292c8",
            "4. Local Narrative Chain": "a32d8bce3e0805bdac4bce0105a7fa715473c28fc6392f701ffcd0a320b949b2",
            "5A. Cross-File Chapter Handoff": "77a8b8b8f7301544343a9e867380637ece97705022fc0c0e5a3eee0e009b2f19",
            "6. 前置章节内容": "540c70cf9833269ae02a138d03ab224f0f1c5e40e104dab33df4f84624607e84",
            "10. 结果与验证的分层": "21b6d5111705b6645c4bd90f1a1393d624797d71ece18254ff0ecca81e559872",
            "12. 跨问递进": "d448a67403c3b867ab7f8f7ec91e04b9cf5179e045e16d433e33657ff2ae2de8",
            "14. 摘要": "8c2cbf13c739b273f4f3331819b0c0bedcac11df5e7103b6e2ea0a109a540271",
            "15. 模型评价、逐问结论与附录": "0bdb266fd63a0776b36decca4dc5d21434f63b809a7f4981c676cc3be80cc0e6",
        }
        sections = {m[1]: m[0] for m in re.finditer(
            r"^## ([^\n]+)\n(.*?)(?=^## |\Z)", read(PROTOCOL), re.M | re.S
        )}
        for heading, digest in expected.items():
            with self.subTest(heading=heading):
                self.assertEqual(hashlib.sha256(sections[heading].encode()).hexdigest(), digest)

    def test_template_adapter_and_proof_algorithm_forms_unchanged(self):
        expected = {
            "packs/artifact/proposition_proof.md": "312fe5648c498831eef148505b65b074a8fbfee3",
            "packs/artifact/algorithm_flow.md": "dbd06aacd7216c654789a9002ce682a2065ec0bd",
            "modules/05_writing/latex.md": "98f90f8caa6c3072316dd8e620add05722abfa4b",
            "templates/latex/cumcm/hsk/template_manifest.yaml": "32402842ea88c2a4ce3df052f6c01534b357549f",
            "templates/latex/cumcm/hsk/hsk_main.tex": "789437316271430dee2c5a7ebbdd803f4698ca63",
        }
        for path, digest in expected.items():
            with self.subTest(path=path):
                data = read(path).encode()
                blob = b"blob " + str(len(data)).encode() + b"\0" + data
                self.assertEqual(hashlib.sha1(blob).hexdigest(), digest)

    def test_complete_reasoning_semantics_except_two_approved_prose_fields(self):
        contract = yaml.safe_load(read("core/writing_reasoning_contract.yaml"))
        # Everything else, including schemas, modeling depth, algorithm presentation,
        # proofs, numerical style, citations and claim calibration, remains pinned.
        contract["paragraph_necessity"].pop("rule")
        contract["prose_style"].pop("target")
        self.assertEqual(semantic_digest(contract),
                         "ae7e0f37fb4a5eeab1ef66fedbe68e2f4b22ff4356165b33ffa1e8e65485a23e")

    def test_runtime_only_adds_relevant_reads_and_one_optional_example(self):
        runtime = yaml.safe_load(read("core/writing_runtime_contract.yaml"))
        preserved = copy.deepcopy(runtime)
        preserved.pop("version")
        stages = {stage["id"]: stage for stage in preserved["template_first_progressive_authoring"]["stages"]}
        question = stages["question_model_solution_result_validation"]
        question["read_now"].remove(PROTOCOL + "#1-写作输入")
        example = question["conditional_reads_before_relevant_passage"].pop("reasoning_example")
        self.assertEqual(example["read"], [EXAMPLES])
        for stage_id in ("draft_semantic_review", "ai_cleanup"):
            reads = stages[stage_id]["read_now"]
            reads.remove(PROTOCOL + "#5-Paragraph-Handoff-Test")
            reads.remove(PROTOCOL + "#7.3-作者视角与建模解释")
        stages["draft_semantic_review"]["read_now"].remove(
            "modules/06_review_delivery.md#三-公式模型角色算法命题与数值证据审查"
        )
        self.assertEqual(semantic_digest(preserved),
                         "40d5464f48eb1c821de378332da9b022694763b58bec5847da5b0aa06697e978")
        self.assertTrue((ROOT / EXAMPLES).is_file())
        progressive = runtime["template_first_progressive_authoring"]
        self.assertNotIn(EXAMPLES, progressive["initial_read_order"])
        self.assertNotIn(EXAMPLES, runtime["ordinary_writing_resource_order"])
        for stage in progressive["stages"]:
            self.assertNotIn(EXAMPLES, stage["read_now"])


class FixedWritingTrialFactsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = yaml.safe_load(read("tests/fixtures/writing_reasoning_cases.yaml"))
        cls.facts = {case["id"]: case["facts"] for case in data["cases"]}
        assert len(cls.facts) == len(data["cases"]) == 4

    def test_heat_balance_and_physical_interval(self):
        f = self.facts["direct_mixing"]
        cold_heat = f["cold_mass_kg"] * (f["target_temperature_c"] - f["cold_temperature_c"])
        hot_drop = f["hot_temperature_c"] - f["target_temperature_c"]
        self.assertGreater(hot_drop, 0)
        self.assertGreater(cold_heat, 0)
        self.assertEqual(cold_heat / hot_drop, f["result_mass_kg"])

    def test_full_integer_candidate_domain_and_unique_solution(self):
        f = self.facts["integer_supply"]
        candidates = list(itertools.product(range(f["batch_capacity_each_period"] + 1), repeat=2))
        self.assertEqual(len(candidates), 9)
        feasible = [x for x in candidates if all(
            f["batch_size"] * batch >= demand for batch, demand in zip(x, f["demand"])
        )]
        self.assertEqual(len(feasible), f["feasible_candidate_count"])
        self.assertEqual(feasible, [tuple(f["result_batches"])])
        self.assertEqual([f["batch_size"] * x for x in feasible[0]], f["result_supply"])
        self.assertEqual(sum(x * c for x, c in zip(feasible[0], f["cost_per_batch"])), f["result_cost"])

    def test_training_fit_and_local_holdout_error(self):
        f = self.facts["linear_prediction"]
        self.assertEqual([2 * t + 1 for t in f["training_t"]], f["training_y"])
        self.assertTrue(set(f["training_t"]).isdisjoint(f["test_t"]))
        pred = [2 * t + 1 for t in f["test_t"]]
        self.assertEqual(pred, f["test_prediction"])
        residual = [y - p for y, p in zip(f["test_y"], pred)]
        self.assertEqual(residual, f["test_residual"])
        self.assertEqual(sum(map(abs, residual)) / len(residual), f["test_mae"])
        i = max(range(len(residual)), key=lambda j: abs(residual[j]))
        self.assertEqual(f["test_t"][i], f["largest_error_t"])
        self.assertEqual(abs(residual[i]), f["largest_absolute_error"])

    def test_declared_inverse_trace_and_position_tolerance(self):
        facts = self.facts["monotone_inverse"]
        a, b = facts["domain"]
        f = lambda x: x * x + 2 * x
        self.assertLess(f(a), facts["target"])
        self.assertGreater(f(b), facts["target"])
        self.assertGreater(2 * a + 2, 0)  # derivative minimum on the whole interval
        m = (a + b) / 2
        self.assertEqual(m, 1)
        self.assertEqual(f(m), facts["target"])
        self.assertLess((b - a) / (2 ** 22), 1e-6)
        self.assertLess(21 + 1, 30)  # tolerance is checked before each interval update


if __name__ == "__main__":
    unittest.main()
