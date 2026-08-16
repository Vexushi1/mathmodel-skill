from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def replace_once(path, old, new):
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"missing compatibility anchor in {path}: {old}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "modules/05_writing/latex.md",
    "**共享基础模型不是固定章节。** 只有两个及以上小问共享核心状态方程、几何/概率/网络关系、判定函数或统一评价结构，并且重复定义会明显造成冗余时，才单列",
    "**共享基础模型：按需单列，后问写增量。** 它不是固定章节；只有两个及以上小问共享核心状态方程、几何/概率/网络关系、判定函数或统一评价结构，并且重复定义会明显造成冗余时，才单列",
)

replace_once(
    "modules/05_writing/latex.md",
    "正文因此应形成“为什么现在需要这个式子 → 怎样由当前条件得到 → 得到了什么 → 下一步在哪里使用”的连续链，而不是把 `formula_reasoning_chain` 内部合同表复制进论文。共享基础、跨问递进、**结构化简优先于算法升级**和**数值参数必须有选择证据**同样直接消费该合同：正文只写当前题实际启用的内容，不罗列未使用的候选机制或证据方法。",
    "正文因此应形成“为什么现在需要这个式子 → 怎样由当前条件得到 → 得到了什么 → 下一步在哪里使用”的连续链，而不是把 `formula_reasoning_chain` 内部合同表复制进论文。共享基础、跨问递进、**结构化简优先于算法升级**和**数值参数必须有选择证据**同样直接消费该合同：正文只写当前题实际启用的内容，不罗列未使用的候选机制或证据方法。数值参数证据按模型类型自适应；数值离散、随机模拟、统计/时间序列、机器学习与优化等具体证据族由 reasoning contract 定义。",
)

replace_once(
    "modules/05_writing/latex.md",
    "正式命题的准入和数量由 `packs/artifact/proposition_proof.md` 管理。命题紧跟其支撑的模型推导，推荐顺序为“详细推导 → 必要命题与短证明 → 核心模型汇总 → 求解”。",
    "正式命题的准入和数量由 `packs/artifact/proposition_proof.md` 管理。命题紧跟其支撑的模型推导，推荐顺序为“详细推导 → 必要命题与短证明 → 核心模型汇总 → 求解”。普通局部性质若不满足命题准入，保留为文字或公式说明，不机械升级为正式命题。",
)

replace_once(
    "templates/model/model_paper_framework.md",
    "- 问题分析安排：各问难点、对象关系和真实跨问依赖如何组织：\n- 共享基础模型：",
    "- 问题分析安排：各问难点、对象关系和真实跨问依赖如何组织：\n- 对象恢复图：`不需要 / 需要`；对象、变量和约束如何映射：\n- 假设组织：共享假设与局部假设如何分层放置：\n- 局部证据闭环：每问结果后就近放置哪些验证/深化证据：\n- 模型检验安排：误差、可行性、外样本、敏感性或其他量化证据如何组织：\n- 算法说明预算：哪些算法只需任务专属短说明，哪些实质改进需要展开：\n- 共享基础模型：",
)
