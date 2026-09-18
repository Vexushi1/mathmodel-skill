from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PACKS = {
    "mechanism": ("packs/task/mechanism.md", ("守恒优先", "移动域先写材料语义", "事件先形式化")),
    "optimization": ("packs/task/optimization.md", ("单调性与边界最优", "凸性与对偶结构", "排序与交换论证")),
    "prediction": ("packs/task/prediction.md", ("预测对象与 horizon", "最小充分状态/滞后", "基准充分性")),
    "evaluation": ("packs/task/evaluation.md", ("是否真的需要构造综合指数", "支配与 Pareto", "权重必要性")),
    "statistics_ml": ("packs/task/statistics_ml.md", ("estimand / 识别对象", "可识别性优先", "充分统计量/低维参数")),
    "graph_network": ("packs/task/graph_network.md", ("树 / 森林", "DAG", "二部图")),
    "scheduling": ("packs/task/scheduling.md", ("precedence DAG", "交换论证", "事件点而非全时域")),
    "game_decision": ("packs/task/game_decision.md", ("战略互动必要性", "支配策略", "potential / identical-interest")),
    "simulation": ("packs/task/simulation.md", ("真的必须靠仿真", "最小充分状态", "事件驱动优先")),
    "spatial": ("packs/task/spatial.md", ("坐标与尺度", "卷积/平稳结构", "空间相关是否必要")),
}


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class DomainReductionCuesV930Tests(unittest.TestCase):
    def test_all_domain_packs_are_structure_first_and_contract_compatible(self):
        for name, (path, _) in PACKS.items():
            with self.subTest(pack=name):
                text = read(path)
                self.assertIn("## 2. 路线比较", text)
                self.assertIn("初始化结构化简优先项", text)
                self.assertIn("主模型", text)
                self.assertIn("comparator", text)

    def test_each_pack_has_domain_specific_reduction_cues(self):
        for name, (path, cues) in PACKS.items():
            text = read(path)
            for cue in cues:
                with self.subTest(pack=name, cue=cue):
                    self.assertIn(cue, text)

    def test_advanced_method_gate_separates_main_and_comparator_roles(self):
        text = read("packs/task/advanced_method_gate.md")
        self.assertIn("main_model", text)
        self.assertIn("quantitative_comparator", text)
        self.assertIn("exploratory_only", text)
        self.assertIn("比较问题、额外结构、数据/计算可行性、可比指标、证据边界", text)
        self.assertIn("主模型七项硬门槛", text)
        self.assertIn("不能因为“多一个高级模型更显创新”而运行", text)

    def test_domain_packs_do_not_make_advanced_models_default(self):
        banned = (
            "看到网络就使用 GNN",
            "存在随机变量就使用 DRO",
            "预测题默认使用深度学习",
            "优化题默认使用遗传算法",
        )
        for name, (path, _) in PACKS.items():
            text = read(path)
            for phrase in banned:
                with self.subTest(pack=name, phrase=phrase):
                    self.assertNotIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
