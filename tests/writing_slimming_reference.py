"""PR #357 exact predecessor projection for the approved A01–A04/A07 draft.

Test-only. No runtime behavior or historical snapshot is waived.
"""
WRITING_SLIMMING_REWRITES = {
    "modules/05_writing/paper_writing_protocol.md": (
        ("摘要与关键词不超过一页。第一段简明扼要地介绍研究背景，由背景引出具体问题，最后给出本文的主要模型。通常为3–4句话，最终 PDF 排版不超过4行。\n\n其后按题目顺序逐问撰写，每个小问段落必须以“针对问题X”开头。每问按以下信息链压缩：", "摘要首先用极短的总述交代研究对象、核心矛盾和全文统一路线，随后覆盖每一个实际小问。每问按以下信息链压缩："),
        ("不得为填满链条虚构模型、约束、算法或敏感性检验。", "这条链概括起来可以写成“针对 X 问题，建立 XX 模型；以 XX 为目标并满足 XX 关键条件/约束；通过 XX 方法求解，得到 XX 结果；检验显示结论在 XX 范围内保持/发生变化；因此得到 XX 结论”，但它是**内容合同而不是固定句式**。不得让每段都机械复制“针对问题 X，本文……”，也不得为填满链条虚构模型、约束、算法或敏感性检验。"),
    ),
    "modules/05_writing/ai_cleanup.md": (
        ("- **摘要**：AI Cleanup 不得修改摘要。\n", ""),
        ("改动后在**现有** draft/final Review 流程和版本对照中检查：摘要、公式与中文推导", "改动后在**现有** draft/final Review 流程和版本对照中检查：公式与中文推导"),
    ),
}


def prior_writing_slimming_text(relative: str, text: str) -> str:
    """Undo exactly the approved draft hunks, retaining any unrelated changes."""
    for current, prior in WRITING_SLIMMING_REWRITES.get(relative, ()):
        if text.count(current) != 1:
            raise ValueError(f"{relative}: approved writing hunk missing or duplicated: {current[:80]!r}")
        text = text.replace(current, prior, 1)
    return text
