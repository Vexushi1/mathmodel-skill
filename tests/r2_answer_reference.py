"""Exact test-only R2 source inverses to the frozen R1 implementation."""
import hashlib

R2_SOURCE_IDENTITIES = {'core/bootstrap.yaml': ['08ffb1a0c6b6c63bd3fed1f838b7a66ac055985c47ad1e41a4c7886ae248c874',
                         '91d7d92e8e605231162aca91bccddf1b1e8b9ae9873eb238c6c644fab5d2928d'],
 'core/hsk_core_policy.md': ['8ffcdad0450316bbb99a731bd40330fe4816896deddeff312e77e6df7026d8d8',
                             'f1b61ee86c0cd609abf6463925d2e56f5a3767f0f23c81a4d70877f162425d95'],
 'core/model_approval_contract.yaml': ['95156f23ef91f9c382422b65a4de6d2f169d17f22f1cb3cb6bda5cdc80d90a70',
                                       'c01b9899bbca525e527d21235078b303e36c92ca18fb30c61fa5f3b56e6b34e0'],
 'core/module_manifest.yaml': ['c0ebed04e984c6df20e054dc2e287293d1d566480a3a07a751a1e7c935bd8f82',
                               '36baed6a4c7a4543f183ded39e42e9b3f1110937e6a428f1d7b0738bc8eeefec'],
 'core/output_contract.yaml': ['d7c0b3a5979c197df9de7c349486ebf91d402f4acea2b60d76a09be41322b2a6',
                               '3d158f2ff0037aa9476cadef30dca17b19918c9ded7430387a94dcbee460fdb9'],
 'core/workflow_router.yaml': ['00f090d0881158e0dcae880076a65c3bbaf57b13a4a0d41da8c7bc9b2382c653',
                               'f8f590df9626ac6c7b9300334d0c65e0a443f34472f7301aaf8c6d8d1f477975'],
 'core/writing_runtime_contract.yaml': ['544e8033a6bae946476d58714af1e8e9038812848f89025e14251a9883008236',
                                        '99a9a26c541198dfc1e65a7945bd36643ebe8fc99eb8a52fa15f5f14cb9c55cd'],
 'modules/01_problem_audit.md': ['2fc8fecefd068f918f4a6bc698d763081bd27b73c85464c0545be9e4b176444f',
                                 'c7e922255410b6a9ca6f28691054481a8a214c1b370be32ac263894c6e2de6fd'],
 'modules/02_model_design.md': ['e3d35bc272c51603264637ba74a8df60674074767ced96de90e12e5faee33eeb',
                                '8410825521e19cbc6d20c592e71ffecc26a62413e12a605cd15bff39698c6c51'],
 'modules/03_solve_validate.md': ['a02caf891c2f2f94ef3b72a685802a29b5d375c5ec7cb05534067dcb97a3f83a',
                                  'c28d23bdb60bb423d3ebb1286c0d8956b92076aeae992261099b71fbb53af9fc']}

R2_RANGE_TRANSITIONS = {'core/model_approval_contract.yaml': [[[[1, 318]], [[1, 332]]]],
 'modules/02_model_design.md': [[[[1, 715]], [[1, 718]]]]}

R2_APPROVED_REWRITES = {'core/bootstrap.yaml': [['skill_version: 11.4.0\nbootstrap_schema_version: 1.1.0\npurpose: >-\n',
                          'skill_version: 11.3.0\nbootstrap_schema_version: 1.1.0\npurpose: >-\n']],
 'core/hsk_core_policy.md': [['# HSK Core Policy v11.4.0\n'
                              '\n'
                              '本文件只定义**跨阶段硬不变量**。任何阶段的目录、字段、工作表、图型、论文小节、算法展示、兼容迁移或工具参数，均以 '
                              '`core/bootstrap.yaml` 指向的 current Authority 为准；本文件不复制这些阶段合同的完整实现。\n',
                              '# HSK Core Policy v11.3.0\n'
                              '\n'
                              '本文件只定义**跨阶段硬不变量**。任何阶段的目录、字段、工作表、图型、论文小节、算法展示、兼容迁移或工具参数，均以 '
                              '`core/bootstrap.yaml` 指向的 current Authority 为准；本文件不复制这些阶段合同的完整实现。\n']],
 'core/model_approval_contract.yaml': [['version: 1.4.0\nstatus: active\npurpose: >-\n',
                                        'version: 1.3.0\nstatus: active\npurpose: >-\n'],
                                       ['    must_check:\n'
                                        '    - problem_contract_fit\n'
                                        '    - required_answer_closure\n'
                                        '    - route_selection_fit\n'
                                        '    - variable_and_constraint_closure\n',
                                        '    must_check:\n'
                                        '    - problem_contract_fit\n'
                                        '    - route_selection_fit\n'
                                        '    - variable_and_constraint_closure\n'],
                                       ['    must_check:\n'
                                        '    - alternative_problem_interpretation\n'
                                        '    - output_omission_or_substitution\n'
                                        '    - forbidden_or_convenience_assumptions\n'
                                        '    - unused_problem_conditions_or_attachment_fields\n',
                                        '    must_check:\n'
                                        '    - alternative_problem_interpretation\n'
                                        '    - forbidden_or_convenience_assumptions\n'
                                        '    - unused_problem_conditions_or_attachment_fields\n'],
                                       ['    - literature_recency_anchor_and_novelty_bias_when_used\n'
                                        '  check_semantics:\n'
                                        '    required_answer_closure: >-\n'
                                        '      Trace every Qn-REQ-xx answer back to input data, '
                                        'mathematical relations and\n'
                                        '      algorithm return values. Check object, granularity, '
                                        'units and tie/event rules;\n'
                                        '      record the expected output location in the existing '
                                        'semantic-closure table.\n'
                                        '    output_omission_or_substitution: >-\n'
                                        '      Independently enumerate required answers from the '
                                        'original prompt. Challenge\n'
                                        '      omissions, aggregate answers substituted for per-object '
                                        'answers, missing peak\n'
                                        '      times and incompatible granularity, without adopting the '
                                        "first pass's checklist.\n"
                                        '    route_selection_fit: >-\n'
                                        '      Compatibility check id. Interpret it as whether the '
                                        'current selected model is the\n',
                                        '    - literature_recency_anchor_and_novelty_bias_when_used\n'
                                        '  check_semantics:\n'
                                        '    route_selection_fit: >-\n'
                                        '      Compatibility check id. Interpret it as whether the '
                                        'current selected model is the\n'],
                                       ['  - objective\n'
                                        '  - key_constraints\n'
                                        '  - required_answers\n'
                                        '  - preprocessing_decision\n'
                                        '  - structural_simplification\n',
                                        '  - objective\n'
                                        '  - key_constraints\n'
                                        '  - preprocessing_decision\n'
                                        '  - structural_simplification\n'],
                                       ['  - next_stage_implementation_scope\n'
                                        '  approval_brief_field_semantics:\n'
                                        '    required_answers: >-\n'
                                        '      State once which answers the model will deliver and the '
                                        'key conditions needed\n'
                                        '      to compute them, following the Qn-REQ-xx rows in the '
                                        'current framework.\n'
                                        '    primary_quality_specification_when_bound: >-\n'
                                        '      Display the complete ordered criteria from the current '
                                        'Structured Identity Block in the\n',
                                        '  - next_stage_implementation_scope\n'
                                        '  approval_brief_field_semantics:\n'
                                        '    primary_quality_specification_when_bound: >-\n'
                                        '      Display the complete ordered criteria from the current '
                                        'Structured Identity Block in the\n']],
 'core/module_manifest.yaml': [['version: 11.4.0\n'
                                'routing_authority: core/workflow_router.yaml\n'
                                'workflow_profile_compatibility:\n',
                                'version: 11.3.0\n'
                                'routing_authority: core/workflow_router.yaml\n'
                                'workflow_profile_compatibility:\n']],
 'core/output_contract.yaml': [['version: 11.4.0\n'
                                'schema: core/workbook_schema.yaml\n'
                                'preprocessing_contract: core/global_preprocessing_contract.yaml\n',
                                'version: 11.3.0\n'
                                'schema: core/workbook_schema.yaml\n'
                                'preprocessing_contract: core/global_preprocessing_contract.yaml\n']],
 'core/workflow_router.yaml': [['version: 11.4.0\nbootstrap: core/bootstrap.yaml\n\n',
                                'version: 11.3.0\nbootstrap: core/bootstrap.yaml\n\n']],
 'core/writing_runtime_contract.yaml': [['version: 11.4.0\n'
                                         'role: >-\n'
                                         '  普通论文写作的最小运行时映射。它不建立第二套数学写作 Authority，只声明普通论文写作真正需要加载的\n',
                                         'version: 11.3.0\n'
                                         'role: >-\n'
                                         '  普通论文写作的最小运行时映射。它不建立第二套数学写作 Authority，只声明普通论文写作真正需要加载的\n']],
 'modules/01_problem_audit.md': [['2. 逐句拆分背景、对象、已知条件、规则、显式约束、隐含约束和评价重点；\n'
                                  '3. 每问说明直接目标、隐含目标、数据、依赖、设问意图、最终交付、机制解释需求和评委风险；\n'
                                  '4. 按 `templates/problem/requirement_coverage.md` '
                                  '建立“题目要求—模型/代码—结果表/图—论文位置—附录”覆盖表；同一问的各项必答量分别编号为 '
                                  '`Q1-REQ-01`、`Q1-REQ-02`，逐项记录原文、对象/粒度、单位与所需最终答案；\n'
                                  '5. 只有改变模型、数据口径、约束或结论的歧义才向用户确认；\n'
                                  '6. 按 `core/task_taxonomy.yaml` 为每问确定一个 objective、至多三个 structures 和独立 '
                                  'capabilities；\n',
                                  '2. 逐句拆分背景、对象、已知条件、规则、显式约束、隐含约束和评价重点；\n'
                                  '3. 每问说明直接目标、隐含目标、数据、依赖、设问意图、最终交付、机制解释需求和评委风险；\n'
                                  '4. 建立“题目要求—模型/代码—结果表/图—论文位置—附录”覆盖表；\n'
                                  '5. 只有改变模型、数据口径、约束或结论的歧义才向用户确认；\n'
                                  '6. 按 `core/task_taxonomy.yaml` 为每问确定一个 objective、至多三个 structures 和独立 '
                                  'capabilities；\n'],
                                 ['| 决策变量 | 题目允许主动改变的量 |\n'
                                  '| 状态变量 | 系统演化、仿真或约束中变化但非直接决策的量 |\n'
                                  '| 输出量 | 按需求编号逐项列出题目要求报告、比较或提交的量，注明对象/粒度、单位、精度与并列值或未触发事件的处理 |\n'
                                  '| 显式约束 | 题面直接规定的边界、规则和限制 |\n'
                                  '| 隐含约束 | 必须由几何、物理、统计、逻辑或业务机制推出，并给依据 |\n',
                                  '| 决策变量 | 题目允许主动改变的量 |\n'
                                  '| 状态变量 | 系统演化、仿真或约束中变化但非直接决策的量 |\n'
                                  '| 输出量 | 题目最终要求报告、比较或提交的量 |\n'
                                  '| 显式约束 | 题面直接规定的边界、规则和限制 |\n'
                                  '| 隐含约束 | 必须由几何、物理、统计、逻辑或业务机制推出，并给依据 |\n']],
 'modules/02_model_design.md': [['## 4. 题面—数学—代码—输出语义闭环\n'
                                 '\n'
                                 '每个核心对象、条件、变量、约束和输出至少建立以下链条；同一问按 `Qn-REQ-xx` 逐项展开必答量：\n'
                                 '\n'
                                 '```text\n',
                                 '## 4. 题面—数学—代码—输出语义闭环\n\n每个核心对象、条件、变量、约束和输出至少建立：\n\n```text\n'],
                                ['```\n'
                                 '\n'
                                 '| 题面来源/需求编号 | 数学层 | 计算层/返回值 | 预期输出位置 | 状态 |\n'
                                 '|---|---|---|---|---|\n'
                                 '|  |  |  |  | closed / gap |\n'
                                 '\n'
                                 '逐项说明输出的对象、粒度、单位及并列值处理。新增派生量写入现有 SIB `variables` 与相关数学关系/算法语义，用稳定 ID '
                                 '关联此表；实际文件、工作表、字段、记录键和数值在求解后写入“结果摘要→证据位置”。已定义的量只缺导出时补返回与落表；新增数学量或改变求解含义时按模型变更复审。\n'
                                 '\n'
                                 'Hard gap 包括：\n'
                                 '\n'
                                 '- 题目要求有、代码没有；\n'
                                 '- 只返回总量而遗漏逐对象答案，或已计算的必答量未进入返回值与输出；\n'
                                 '- 核心代码对象有、数学来源没有；\n'
                                 '- 论文隐含约束/变换无法由题意、数据或机制支持；\n',
                                 '```\n'
                                 '\n'
                                 '| 题面来源 | 数学层 | 计算层 | 输出证据 | 状态 |\n'
                                 '|---|---|---|---|---|\n'
                                 '|  |  |  |  | closed / gap |\n'
                                 '\n'
                                 'Hard gap 包括：\n'
                                 '\n'
                                 '- 题目要求有、代码没有；\n'
                                 '- 核心代码对象有、数学来源没有；\n'
                                 '- 论文隐含约束/变换无法由题意、数据或机制支持；\n'],
                                ['Model Reviewer 是正向适配审查，至少检查（涉及外部研究方法时，同步执行 '
                                 '`core/model_approval_contract.yaml` '
                                 '中条件式文献适用与来源边界检查；研究记录的格式验证不能替代该审查）：\n'
                                 '\n'
                                 '- 按 `core/model_approval_contract.yaml#model_challenge` 的 '
                                 '`required_answer_closure` 逐项确认当前主模型回答冻结后的 Problem Contract；\n'
                                 '- 当前主模型是否已经利用题面条件完成可证明的消元、降维、分解或等价变换，且没有为了展示算法保留冗余复杂度；\n'
                                 '- 当前主模型是否达到“最小充分”：若存在更简单且仍完整的模型，是否说明为什么当前结构仍有必要；\n',
                                 'Model Reviewer 是正向适配审查，至少检查（涉及外部研究方法时，同步执行 '
                                 '`core/model_approval_contract.yaml` '
                                 '中条件式文献适用与来源边界检查；研究记录的格式验证不能替代该审查）：\n'
                                 '\n'
                                 '- 当前主模型是否真正回答冻结后的 Problem Contract；\n'
                                 '- 当前主模型是否已经利用题面条件完成可证明的消元、降维、分解或等价变换，且没有为了展示算法保留冗余复杂度；\n'
                                 '- 当前主模型是否达到“最小充分”：若存在更简单且仍完整的模型，是否说明为什么当前结构仍有必要；\n'],
                                ["Devil's Advocate "
                                 '是反方挑战，至少检查（若存在文献候选，还须独立质疑近期研究偏好、原文假设/本题边界不一致、数据不可获得和夸大的创新声明）：\n'
                                 '\n'
                                 '- 按 `core/model_approval_contract.yaml#model_challenge` 的 '
                                 '`output_omission_or_substitution` 独立检查题面必答量，再检查是否存在另一种会改变答案的合理题意解释；\n'
                                 '- 是否为了求解方便引入题目不允许的假设；\n'
                                 '- 是否闲置关键题面条件或附件字段；\n',
                                 "Devil's Advocate "
                                 '是反方挑战，至少检查（若存在文献候选，还须独立质疑近期研究偏好、原文假设/本题边界不一致、数据不可获得和夸大的创新声明）：\n'
                                 '\n'
                                 '- 是否存在另一种会改变答案的合理题意解释；\n'
                                 '- 是否为了求解方便引入题目不允许的假设；\n'
                                 '- 是否闲置关键题面条件或附件字段；\n'],
                                ['## 7. Human Model Approval 与正式锁模\n'
                                 '\n'
                                 '`model_challenge_status=passed` 后，不直接进入代码交付。先向用户提供简洁但完整的 Model '
                                 'Approval Brief，至少包含：研究对象、selected '
                                 'model、标准模型类型、核心变量、目标、关键约束、必答量及交付它们的关键条件、**modeling gap 与 '
                                 'why-this-structure**、关键适用条件/失效边界、`preprocessing_decision`、结构化简及其 '
                                 'provenance、为什么当前模型已达到最小充分、Comparator '
                                 'Envelope（若启用）及各自比较目的、Solver/Validator 角色与算法适配理由、关键 solver '
                                 'preconditions、Algorithm presentation、关键数值建模参数的证据计划、主求解 PQS '
                                 '的关键门槛、主要被否决路线理由、residual warnings '
                                 '与下一阶段实际实现范围（包括项目根唯一后端、各问具体数学求解器及依赖核验情况）。若 4.8 适用，Brief '
                                 '还应简要暴露真正会改变求解语义的精确判据、事件边界策略、缩域 evidence level、组合算子、条件式 solver '
                                 'probe/分支以及 surrogate→original 回算要求；不适用项不机械列空字段。\n'
                                 '\n'
                                 '用户必须明确批准当前模型。自然语言如“OK，就按这个模型求解”“这个框架可以，进入主求解”“Q1-Q3 '
                                 '全部冻结”可视为批准；“我看看”“继续说”“还有别的方案吗”“这个模型怎么样”以及用户沉默不得推断为批准。\n',
                                 '## 7. Human Model Approval 与正式锁模\n'
                                 '\n'
                                 '`model_challenge_status=passed` 后，不直接进入代码交付。先向用户提供简洁但完整的 Model '
                                 'Approval Brief，至少包含：研究对象、selected '
                                 'model、标准模型类型、核心变量、目标、关键约束、**modeling gap 与 '
                                 'why-this-structure**、关键适用条件/失效边界、`preprocessing_decision`、结构化简及其 '
                                 'provenance、为什么当前模型已达到最小充分、Comparator '
                                 'Envelope（若启用）及各自比较目的、Solver/Validator 角色与算法适配理由、关键 solver '
                                 'preconditions、Algorithm presentation、关键数值建模参数的证据计划、主求解 PQS '
                                 '的关键门槛、主要被否决路线理由、residual warnings '
                                 '与下一阶段实际实现范围（包括项目根唯一后端、各问具体数学求解器及依赖核验情况）。若 4.8 适用，Brief '
                                 '还应简要暴露真正会改变求解语义的精确判据、事件边界策略、缩域 evidence level、组合算子、条件式 solver '
                                 'probe/分支以及 surrogate→original 回算要求；不适用项不机械列空字段。\n'
                                 '\n'
                                 '用户必须明确批准当前模型。自然语言如“OK，就按这个模型求解”“这个框架可以，进入主求解”“Q1-Q3 '
                                 '全部冻结”可视为批准；“我看看”“继续说”“还有别的方案吗”“这个模型怎么样”以及用户沉默不得推断为批准。\n']],
 'modules/03_solve_validate.md': [['任何一项真正适用的前置条件不满足，都不得生成正式主求解代码。尤其禁止出现“模型尚未闭环，先写代码看结果再决定题意”，也禁止在 '
                                   '`project_level` 已冻结后各问重新自行清洗。\n'
                                   '\n'
                                   '## 必答结果闭环\n'
                                   '\n'
                                   '按框架“求解与验证方案”的需求编号，将每项必答量连接到数学定义、求解返回值和实际输出。例如逐站峰值、全部峰值时刻与全网总量分别计算、返回和保存。证明题连接到推导与论文位置；需要新增场景计算的要求按 '
                                   '03B 方法表落实。\n'
                                   '\n'
                                   '生成代码时逐项检查“计算 → 返回 → 组表 → 写出”。使用完整 Python 管线时，以 '
                                   '`answer_sheets=("站点峰值", ...)` 声明答案表；直接调用共享 writer 时使用同名参数；自包含入口和 '
                                   'MATLAB 的 `sheets` 列表逐项列入实际答案。表名、字段、对象键与单位对应框架中的预期输出。\n'
                                   '\n'
                                   '返回后回读实际工作簿，按题面独立确定的对象集合、字段和数值核对；逐站答案同时检查峰值与时刻，保留全部并列解。事件未触发时记录状态与原因。题面提供提交模板时，对照其行键、列名和显示精度填写。完整轨迹已保存而汇总遗漏时补导出；缺少必要状态时重跑受影响的计算，并把实际证据位置更新到框架结果摘要。\n'
                                   '\n'
                                   '## Primary Evidence Capture：主求解必须保留当前运行的高价值状态证据\n'
                                   '\n',
                                   '任何一项真正适用的前置条件不满足，都不得生成正式主求解代码。尤其禁止出现“模型尚未闭环，先写代码看结果再决定题意”，也禁止在 '
                                   '`project_level` 已冻结后各问重新自行清洗。\n'
                                   '\n'
                                   '## Primary Evidence Capture：主求解必须保留当前运行的高价值状态证据\n'
                                   '\n'],
                                  ['- `决策变量明细` / `方案对比` / `Pareto结果`：优化决策、候选方案与多目标结果；\n'
                                   '- `约束违反检查` / `均衡残差` / `守恒残差`：约束与机制残差；\n'
                                   '- `收敛诊断` / `离散精度` / `执行停止证据`：当前主数值过程与停止条件证据。\n'
                                   '\n'
                                   '优先在现有通用明细表中保存本题真实状态；需要独立答案表时，在主求解输出中声明题目专属表名和字段。跨项目通用工作表由 '
                                   '`core/workbook_schema.yaml` 定义，03B 结果落入对应的既有方法表。\n'
                                   '\n'
                                   '### 03A / 03B 硬边界\n',
                                   '- `决策变量明细` / `方案对比` / `Pareto结果`：优化决策、候选方案与多目标结果；\n'
                                   '- `约束违反检查` / `均衡残差` / `守恒残差`：约束与机制残差；\n'
                                   '- `收敛诊断` / `离散精度`：当前主数值过程证据。\n'
                                   '\n'
                                   '如果现有表结构不足以无歧义保存本题的真实状态，优先在题目专属输出中使用语义清楚的已登记通用明细表与真实字段，而不是把底层状态压缩成一个摘要数字；确需新增跨项目通用工作表时才修改工作簿 '
                                   'Authority，并必须保持旧工作簿兼容。\n'
                                   '\n'
                                   '### 03A / 03B 硬边界\n']]}


def prior_r2_text(relative, text):
    """Reverse approved blocks; retain every unrelated character."""
    for current, previous in R2_APPROVED_REWRITES.get(relative, ()):
        if text.count(current) != 1:
            raise ValueError(f"R2 source block is missing or duplicated: {relative}")
        text = text.replace(current, previous, 1)
    return text


def prior_r2_bytes(relative, raw):
    """Require exact current and predecessor identities for source fingerprints."""
    identity = R2_SOURCE_IDENTITIES.get(relative)
    if identity is None:
        return raw
    prior_sha, current_sha = identity
    if hashlib.sha256(raw).hexdigest() != current_sha:
        raise ValueError(f"R2 source bytes changed: {relative}")
    previous = prior_r2_text(relative, raw.decode("utf-8")).encode("utf-8")
    if hashlib.sha256(previous).hexdigest() != prior_sha:
        raise ValueError(f"R2 predecessor bytes differ: {relative}")
    return previous
