"""PR #357 exact predecessor projection for the approved writing draft.

Test-only. No runtime behavior or historical snapshot is waived.
"""
WRITING_SLIMMING_REWRITES = {
    "modules/05_writing/paper_writing_protocol.md": (
        ("多问论文按问分小节，但问与问之间要明确真实继承和结构增量：后问先说明沿用前问的哪个对象、状态、关系或结果，再指出新增条件怎样改变变量、目标、约束或求解困难。没有继承时直接说明新任务，不虚构递进。问题分析不提前展开完整推导，不把模型建立、算法百科、最终数值或性能结论塞进分析段。\n\n问题分析采用纯文本，不出现数学公式或数学表达式。", "多问论文按问分小节，但问与问之间要明确真实继承和结构增量：后问先说明沿用前问的哪个对象、状态、关系或结果，再指出新增条件怎样改变变量、目标、约束或求解困难。没有继承时直接说明新任务，不虚构递进。问题分析不提前展开完整推导，不把模型建立、算法百科、最终数值或性能结论塞进分析段。"),
        ("模型假设直接分条陈述，简明扼要，无须逐条说明原因、来源或影响。保留真实、合理的建模假设；题面事实、单位约定和程序正确性不包装成假设。", "模型假设只保留会改变变量、目标、约束、状态、分布、近似误差或适用边界的条件。每项假设应能恢复其来源或必要性，并说明它影响模型的哪个部分；题面事实、单位约定、程序正确性和“忽略一切次要因素”不能包装成假设。若结果对某项假设敏感，应在验证或模型不足中交代其失效影响。"),
        ("简要说明模型自身的优点与不足，通常列3项优点、1–2项不足。改进方向和推广按实际情况简述。\n\n模型评价不能替代误差、残差、可行性、外样本、敏感性或置信区间等验证。\n\n", "模型评价只评价本文实际建立和验证过的模型：优势要绑定具体结构、机制、计算性质或结果证据；不足要说明影响哪个结果、参数范围、场景或适用边界；改进方向应与不足一一对应。推广只有在存在明确可迁移对象时保留，并说明可继承的结构、需要重新标定的参数/约束以及不能直接迁移的条件。\n\n模型评价不能替代误差、残差、可行性、外样本、敏感性或置信区间等验证。通常约 3 项有据优势（兼顾模型结构与求解性质）、1–2 项具体局限，再用短段说明确有依据的推广条件；数量只作阅读预算，不是硬配额。缺少真实可迁移对象时省略推广小节，不为凑数制造空泛应用场景。\n\n"),
        ("## 19. 与完整 Authority 的关系", "模型评价中优点和缺点的数量按模型实际决定，不检查“优点必须多于缺点”；每一项评价都要绑定具体结构、证据或失效边界。\n\n## 19. 与完整 Authority 的关系"),
        ("#### 7.3.2 “我们”“本文”与对象主语\n\n论文中可以使用“我们”，也可以使用“本文”，根据语境自然选择，不限制使用比例。\n\n", "#### 7.3.2 “我们”“本文”与对象主语\n\n适度作者声音是正常可用的表达，不是必须先改为无人称才能放行的例外。一般而言：局部观察、判断、取舍、探究和主动检验可以自然使用“我们”；研究范围、全文方法或论文整体贡献可以使用“本文”；已经证明的数学事实、已经核验的数据结果或清楚的对象关系通常优先让数学对象、图表或结果本身承担主语。\n\n例如严格得到 $f'(x)>0$ 后，直接写“$f(x)$ 在该区间严格单调递增”通常比“我们认为 $f(x)$ 单调递增”更准确；后者会把已经证明的事实降格为主观判断。相反，“因此，我们认为评价该预测时应同时报告平均误差与局部最大误差”可以表达由实际误差证据支持的评价取舍。\n\n这些只是功能指导，不是硬性主语映射。不要求新增第一人称，不把原本自然的表达统一改成“本文”，也不把对象主语机械改成“我们发现”。**不按代词频率**、问号数量或“口语词”数量打分，不设置“我们/本文”比例。\n\n"),
        ("#### 7.3.7 事实来源、团队经历与反模板边界", "#### 7.3.6 Reasoning Necessity 与 Problem-Specificity\n\n对“我们认为/希望/发现/需要/采用”“本文建立/提出”等作者声音句，先执行 **Reasoning Necessity**：删掉这句话以后，读者是否会失去至少一项不可替代的信息——为什么这样定义、为什么这个约束必要、为什么可以简化、solver 为什么适配、当前还缺什么、结果为什么需要继续比较、该式有什么下游作用、验证正在挑战什么风险或结论边界是什么？若全部不会丢失，则优先删除、合并或换成更直接的对象主语。\n\n再执行 **Problem-Specificity**：若把研究对象名称替换成另一道赛题后，该句仍能原样使用，例如“为了更好地解决该问题，我们建立数学模型进行分析”，说明它高度模板化，应回到当前赛题的机制、数据结构、约束、几何/网络关系或评价指标重写。\n\n这两个测试都是语义判断，不用关键词或词频自动评分；其目标是保留有信息的作者思考，而不是保留所有第一人称句。\n\n#### 7.3.7 事实来源、团队经历与反模板边界"),
        ("摘要与关键词不超过一页。第一段简明扼要地介绍研究背景，由背景引出具体问题，最后给出本文的主要模型。通常为3–4句话，最终 PDF 排版不超过4行。\n\n其后按题目顺序逐问撰写，每个小问段落必须以“针对问题X”开头。每问按以下信息链压缩：", "摘要首先用极短的总述交代研究对象、核心矛盾和全文统一路线，随后覆盖每一个实际小问。每问按以下信息链压缩："),
        ("不得为填满链条虚构模型、约束、算法或敏感性检验。", "这条链概括起来可以写成“针对 X 问题，建立 XX 模型；以 XX 为目标并满足 XX 关键条件/约束；通过 XX 方法求解，得到 XX 结果；检验显示结论在 XX 范围内保持/发生变化；因此得到 XX 结论”，但它是**内容合同而不是固定句式**。不得让每段都机械复制“针对问题 X，本文……”，也不得为填满链条虚构模型、约束、算法或敏感性检验。"),
    ),
    "modules/05_writing/ai_cleanup.md": (
        ("- **摘要**：AI Cleanup 不得修改摘要。\n", ""),
        ("改动后在**现有** draft/final Review 流程和版本对照中检查：摘要、公式与中文推导", "改动后在**现有** draft/final Review 流程和版本对照中检查：公式与中文推导"),
    ),
    "core/writing_reasoning_contract.yaml": (
        ("problem_background:\n  authority: modules/05_writing/paper_writing_protocol.md#6.1-问题重述\n\nmodel_evaluation:\n  authority: modules/05_writing/paper_writing_protocol.md#15-模型评价逐问结论与附录\n\n", "problem_background:\n  governance_level: recommendation\n  default: one_paragraph\n  allow_second_short_paragraph_when: reality_background_to_specific_research_object_needs_semantic_narrowing\n  second_paragraph_must: narrow_object_or_core_conflict\n  forbidden_second_paragraph: document_structure_or_chapter_management_only\n\nmodel_evaluation:\n  governance_level: recommendation\n  strengths_typical: [2, 4]\n  strengths_usual_target: 3\n  weaknesses_typical: [1, 2]\n  count_relation_required: false\n  concise_transfer_rule: 仅在确有迁移对象时简述可继承的结构、需要重新标定的参数或约束和适用边界，避免空泛应用罗列。\n  rule: 优点结合真实模型结构与求解性质，局限说明受影响的结果及范围；数量按实际模型决定，不检查“优点必须多于缺点”，也不机械增加推广小节。\n\n"),
        ("  anti_template_boundary:\n    - 正文避免无必要地连续重复句式；摘要已规定的固定句式除外。\n\n", "  anti_template_boundary:\n    - 不从单一优秀论文复制固定句式、算法名、章节编号或题目专属模型。\n    - 不要求所有论文设置“模型准备”、问题关系图、命题、核心模型汇总独立小节、正式算法框或统一敏感性章节。\n    - 不按固定标题数量判定论文质量；章节层级由当前论证链和真实数学结构决定。\n    - 不把“承接—建式—解释—求解—结果”固化为固定句型或固定标题；规则只抽象逻辑功能。\n    - 规则只抽象可跨题型复用的推理结构，具体章节和证据按当前赛题决定。\n\n"),
        ("  anti_template_boundary:\n    - 见 scope.anti_template_boundary。\n", "  anti_template_boundary:\n    - 不复制任何优秀论文的固定句子、章节编号、算法或题目专属建模顺序。\n    - 不要求每个公式前出现同一承接词，不要求每段固定使用“因此/进一步/从而”。\n    - 不固定三级标题数量、流程图数量、Step 1--n、模型建立末尾总结句或图表分析三句式。\n    - 不把PSO、GA、DE、二分法、坐标搜索或任何参考论文算法设为默认 solver。\n    - 不把机理题中的某一对象顺序推广成统计、预测、网络、仿真或机器学习题的固定模板。\n    - 不把 Figure Result Narrative 固化为“图身份—特征—数值—原因—结论”的固定句数或固定措辞。\n    - 不把“模型适用性”固化为每问独立小节；适用理由优先贴近模型或 solver 首次出现处。\n    - 不把局部求解依赖升级为全文大章节重排规则。\n"),
        ("  prose_target:\n    analysis_sentence_should_add_one_of:\n", "  prose_target:\n    preferred_subjects:\n      - current_object\n      - current_relation\n      - current_condition\n      - current_result\n      - current_mathematical_task\n    reduce_repeated_subjects: [本文, 本问, 该模型, 我们]\n    analysis_sentence_should_add_one_of:\n"),
        ("      作者表达按 Paper Writing Protocol §7.3 执行。", "      reduce_repeated_subjects 只针对机械重复的步骤宣告，不是第一人称禁令；\n      有信息的作者视角及其表达边界按 Paper Writing Protocol §7.3 执行。"),
        ("    subject_roles:\n      quota: none\n      rule: 见 Paper Writing Protocol §7.3.2。\n", "    subject_roles:\n      author_we: local_reasoning_action\n      paper_this_work: paper_scope_or_contribution\n      object_subject: established_mathematical_or_empirical_fact\n      quota: none\n      rule: >-\n        “我们”“本文”与对象/结果主语都可合法使用；按当前语义功能自然选择，\n        不批量互换，也不因正式性偏好统一成某一主语。\n"),
        ("    prohibit:\n      - pronoun_frequency_target", "    necessity_tests:\n      - reasoning_necessity\n      - problem_specificity\n    necessity_rule: >-\n      删除作者声音句后若不丢失选择理由、当前缺口、数学作用、验证目标或结论边界，应压缩、换主语或删除；\n      若替换研究对象后句子仍可原样用于任意赛题，应优先回到当前机制、数据、约束或评价目标重写。\n    prohibit:\n      - pronoun_frequency_target"),
        ("        - terminology_drift_check\n        - paragraph_necessity_check\n", "        - terminology_drift_check\n        - caption_length_check\n        - paragraph_necessity_check\n"),
        ("    may_warn:\n      - generic_algorithm_exposition_without_local_variable_or_constraint_terms\n      - repeated_result_number_sentence\n    must_not_do:\n", "    may_warn:\n      - highly_similar_adjacent_paragraphs\n      - generic_algorithm_exposition_without_local_variable_or_constraint_terms\n      - repeated_result_number_sentence\n      - repeated_meta_summary\n    must_not_do:\n"),
        ("machine_audit_boundary:\n  report_only_for_semantic_style_risks: true\n  may_warn:\n    - dense_formula_blocks_with_little_prose\n    - repeated_cross_question_redefinition\n    - unexplained_numeric_parameter_assignment\n    - unused_bibliography_entry\n    - terminology_drift\n    - numeric_style_drift\n    - unreferenced_label_or_equation\n    - raw_python_like_pseudocode\n    - management_transition\n  may_review:\n", "machine_audit_boundary:\n  report_only_for_semantic_style_risks: true\n  may_warn:\n    - dense_formula_blocks_with_little_prose\n    - repeated_further_obtain_or_similarly_obtain\n    - repeated_meta_navigation\n    - repeated_cross_question_redefinition\n    - unexplained_numeric_parameter_assignment\n    - repeated_identical_question_opening_pattern\n    - unused_bibliography_entry\n    - terminology_drift\n    - numeric_style_drift\n    - unreferenced_label_or_equation\n    - unusually_long_caption\n    - paragraph_redundancy_risk\n    - raw_python_like_pseudocode\n    - management_transition\n  may_review:\n"),
    ),
    "modules/06_review/content_review.md": (
        ("只消费 Protocol §7.3 与 reasoning Authority，核对 Question Closure 与 Claim Strength；段落必要性按 Protocol §5。明确禁止 `first_person_ratio`、`human_like_score`、`AI_like_score`，不根据作者声音判断身份。", "只消费 Protocol §7.3 与 reasoning Authority。检查 Reasoning Necessity、Problem-Specificity、Question Closure 与 Claim Strength；不做“人工感”评分，不用第一人称/连接词频率推断作者身份；明确禁止 `first_person_ratio`、`human_like_score`、`AI_like_score`。必要理由可以保留“我们”，客观事实可以重设为对象主语；不得由表面自然度牺牲公式来源、证明、Algorithm Trace 或证据边界。"),
    ),
}


def prior_writing_slimming_text(relative: str, text: str) -> str:
    """Undo exactly the approved draft hunks, retaining any unrelated changes."""
    for current, prior in WRITING_SLIMMING_REWRITES.get(relative, ()):
        if text.count(current) != 1:
            raise ValueError(f"{relative}: approved writing hunk missing or duplicated: {current[:80]!r}")
        text = text.replace(current, prior, 1)
    return text


WRITING_STAGE_GATE_REWRITES = {
    "problem_analysis": ("形成对象/条件 → 困难 → 数学抓手 → 建模转化 → 准备建立的结构 → 跨问关系的连续论证，不得写成散乱清单或软件流水线。问题分析采用纯文本，不出现数学公式或数学表达式。", "形成对象/条件 → 困难 → 数学抓手 → 建模转化 → 准备建立的结构 → 跨问关系的连续论证，不得写成散乱清单或软件流水线。"),
    "assumptions_symbols_and_preparation": ("模型假设按 Protocol §6.3 分条陈述；假设、符号、数据处理和共享关系均有真实依据；未激活的条件章节保持关闭。", "假设、符号、数据处理和共享关系均有真实依据；未激活的条件章节保持关闭。"),
    "abstract_title_and_keywords": ("摘要按 Protocol §14 撰写，逐问闭合任务—模型—目标/条件—方法—结果—真实检验—结论，标题和关键词均有正文及结果证据，不虚构敏感性或鲁棒性。", "摘要逐问闭合任务—模型—目标/条件—方法—结果—真实检验—结论，标题和关键词均有正文及结果证据，不虚构敏感性或鲁棒性。"),
    "ai_cleanup": ("只清除普通自然语言中的模板感、空话及纯重复；摘要、公式、中文推导、证明、伪代码、算法、数值及显示格式、术语定义、引用、图表实体、章节标题与层级均只读。数学或证据问题返回既有前置审查，不在 Cleanup 改写；改后在原有 Review 中复核受保护内容，不新增门禁。", "只清除普通自然语言中的模板感、空话及纯重复；公式、中文推导、证明、伪代码、算法、数值及显示格式、术语定义、引用、图表实体、章节标题与层级均只读。数学或证据问题返回既有前置审查，不在 Cleanup 改写；改后在原有 Review 中复核受保护内容，不新增门禁。"),
}


def prior_writing_slimming_plan(plan):
    """Project exact approved gate text only; retain all other plan fields."""
    from copy import deepcopy

    predecessor = deepcopy(plan)
    deltas = []
    for prefix in (("writing_runtime",), ("runtime_plan", "writing_runtime")):
        node = predecessor
        for key in prefix:
            node = node.get(key) if isinstance(node, dict) else None
        if not isinstance(node, dict):
            continue
        stages = node.get("authoring_sequence", [])
        for stage_id, (current, prior) in WRITING_STAGE_GATE_REWRITES.items():
            matches = [(i, stage) for i, stage in enumerate(stages)
                       if isinstance(stage, dict) and stage.get("id") == stage_id]
            if len(matches) == 1 and matches[0][1].get("gate") == current:
                index, stage = matches[0]
                stage["gate"] = prior
                deltas.append({"path": ".".join((*prefix, "authoring_sequence", str(index), "gate")),
                               "baseline": prior, "candidate": current,
                               "approval": "PR #357 approved writing stage text"})
    return predecessor, deltas
