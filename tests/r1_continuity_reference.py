"""Exact test-only R1 source inverses to the frozen v11.2.0 release."""
import hashlib

R1_SOURCE_IDENTITIES = {'core/bootstrap.yaml': ['f0d1314f657e7c6ef47b052ad018511ad58fef16578660a087a093606fa6a43c',
                         '08ffb1a0c6b6c63bd3fed1f838b7a66ac055985c47ad1e41a4c7886ae248c874'],
 'core/workflow_router.yaml': ['fcfb4c1da8ceedf2c0fafdf1371832a7d4147c36f9fb03df36ffcd677d46911a',
                               '00f090d0881158e0dcae880076a65c3bbaf57b13a4a0d41da8c7bc9b2382c653'],
 'core/hsk_core_policy.md': ['35aded644ce7b978a02498d93c00a1f5e59e54d3f70a8d80efef7facac585a73',
                             '8ffcdad0450316bbb99a731bd40330fe4816896deddeff312e77e6df7026d8d8'],
 'core/writing_runtime_contract.yaml': ['80b0ecff6a962fef52aad606e2bff9b0abb3501d8a9fe9b248a0c70584c1cc38',
                                        '544e8033a6bae946476d58714af1e8e9038812848f89025e14251a9883008236'],
 'core/output_contract.yaml': ['7e69b8b4f7c6c4225c65fd0f37a93dcc1239ce18fabccb5cef02af5d0a62fd67',
                               'd7c0b3a5979c197df9de7c349486ebf91d402f4acea2b60d76a09be41322b2a6'],
 'core/model_approval_contract.yaml': ['3d97b5a170b1ddd6155fe47b0864caa4a2a4bf513238d6cf38ab85a0436bbc3d',
                                       '95156f23ef91f9c382422b65a4de6d2f169d17f22f1cb3cb6bda5cdc80d90a70'],
 'core/project_state.schema.yaml': ['5ab0e1b5897e70e2ce04d1de7f684a6003d9a97ad1e45201e734ae5360c722c1',
                                    'e7ff5632deb387a9d19a63d529690e2bfd3a476e767c1d8c095e94db1bc5c135'],
 'core/runtime_assurance_contract.yaml': ['f24feaf7159a64f771dceaaedb7b6ffb1b1dc665d2286e55cc937f5ed2448d0c',
                                          '9ba7a072062a1a1cdc0002c51fb7f8ebfaa145b4f9c5f02675ad54477f96a293'],
 'core/user_execution_contract.yaml': ['1b018787540da4f7a9adbc21d85655c194e80eedeb34622aeb3bfe05ff2d9306',
                                       '2c42b5ab0e83294f5e61b65b2cf54395c2e2332f31d2648ac2634e6f3be1e202'],
 'modules/02_model_design.md': ['ca5c299e4cbeea9caff80fbbaba2e3711262081ffe258ef5ca51e0ee7fcaf306',
                                'e3d35bc272c51603264637ba74a8df60674074767ced96de90e12e5faee33eeb'],
 'modules/03_solve_validate.md': ['55d954d1b5ecfaf94d35be9540ce8da07ff50a71ddd7c4a79b7b56c1726b4996',
                                  'a02caf891c2f2f94ef3b72a685802a29b5d375c5ec7cb05534067dcb97a3f83a'],
 'modules/03_result_analysis.md': ['f363466483925b0fa7bf29eb3d92472474ecfabb2dca1feb1a4c16067a446110',
                                   '7c0ecc01589916e0aedb26253870bf4807ee894b4eed568b358585f80da72ba3'],
 'modules/04_figure_evidence.md': ['1ff0c1d742f0b9f8e0a64e5d8d6d7931ec77bba1ff1824d39c206e8d3974d046',
                                   'c2e1719c8feacded3e13eeda9797e36ec79b6a7fd57331426d2b6eee8d7dbb17'],
 'modules/05_writing/paper_writing_protocol.md': ['09994c876bc02cacd320d6898429eb95e4e2c095cb2900739dc815ab8deb0094',
                                                  '2155e045d8684ff99027d59fad963effd4ca27590195b61abe873c099f699067'],
 'modules/05_writing/latex.md': ['7fa3c8e7145a58844b32cf357c4b71f4b68215ac67f59a76b447fd55115c7555',
                                 '508e3ccfe7372554c252b0797a63786e057ad7a066dd1b145cf741cfcb819261'],
 'core/code_quality_contract.yaml': ['d203441e5793a45c05871d0f6feb6488aa2ce3c3efbd3d1f0d74708d9d214b0a',
                                     'f02698433f51778a41003cec425eebf275d02dc3618ae29f9b06867aaf48154f'],
 'modules/06_review_delivery.md': ['ea9385e9c12d0b24e8e7c5ee4e439be76e767aaeee9b6f1c705c14ed06142c7f',
                                   '4549f96207afe4574b724e83e10e128eb3748fb8fa80d7f3bb7b0d4dd1424646'],
 'modules/06_review/content_review.md': ['2910db96b2207e6fe4f568bee52e47149efddd8a24b74ea6862c2e48454fb111',
                                         '2feef9dc342d5aa3cad0b38e28bad2c4b6c21b771c175c8c5a4fa073f98ee978'],
 'modules/06_review/final_delivery.md': ['817ec1db0c1f1ec979d04016109f65aa17e62640b862f49755f0a5efc0254fa4',
                                         '9eaf2477060cd5ad360baaa8059ed708780d25840ab446d38754083d7a22f353'],
 'packs/artifact/review.md': ['3b54a34d7b86ba4f6f86d225b65a99faa0bbbff8a8fab93b7aa32db0e7fbdc34',
                              '03f8c3774d93b279d3476e05c9a7fe502ecc519507d650957133516a7c6cf61a'],
 'packs/artifact/code.md': ['e76c177c1e834ead74b99754ae3591619b1a92e43eea14a30a44ca53a5cfb348',
                            '7226001fc19abbe4928841e908abebbceb48f8dbf63c4c4f58ceb22b5462890f']}

R1_RANGE_TRANSITIONS = {'core/model_approval_contract.yaml': [[[[1, 296]], [[1, 318]]]],
 'core/output_contract.yaml': [[[[468, 514]], [[470, 516]]], [[[1, 637]], [[1, 639]]]],
 'core/user_execution_contract.yaml': [[[[1, 562]], [[1, 570]]]],
 'packs/artifact/review.md': [[[[1, 37]], [[1, 32]]]]}

R1_APPROVED_REWRITES = {'core/bootstrap.yaml': [['skill_version: 11.3.0\n', 'skill_version: 11.2.0\n'],
                         ['    - Read the same-version rule text directly under '
                          'core/runtime_assurance_contract.yaml#reading_plan.formal_rule_delivery, then use '
                          'the router for business actions.\n',
                          '    - Use core/runtime_assurance_contract.yaml for stage reads, assurance and '
                          'dependency closure. Use the router for business actions.\n'],
                         ['    - Select the project solver backend from the known needs of all questions and '
                          'the current model under core/user_execution_contract.yaml. Review an existing '
                          "project's affected stages before changing its backend.\n",
                          '    - Under core/user_execution_contract.yaml inspect before writing solver '
                          'backend choices. Select a first choice; migrate a historical or locked choice '
                          'only after preview and explicit project confirmation.\n'],
                         ['  - For explicit machine validation, execute every `pre_delivery_gates` entry '
                          'returned by the resolver in order.\n'
                          '  - Restore the current model and its human approval from 模型论文框架.md; consume '
                          'actual results under core/user_execution_contract.yaml#result_handoff.\n'
                          '  - Project preprocessing and primary solve code follow Model Challenge and '
                          'explicit user approval under core/model_approval_contract.yaml.\n',
                          '  - Execute every `pre_delivery_gates` entry returned by the resolver in order '
                          'for formal delivery.\n'
                          '  - Restore project semantics from current 模型论文框架.md, machine state from project '
                          'state, and numerical facts from accepted workbooks.\n'
                          '  - Project preprocessing and primary solve code require Model Challenge and '
                          'explicit user approval of the current semantic_revision and validated '
                          'semantic_identity_hash under core/model_approval_contract.yaml. Legacy '
                          'semantic_hash is read-only.\n']],
 'core/workflow_router.yaml': [['version: 11.3.0\n', 'version: 11.2.0\n'],
                               ['  numeric_fact_source: current_standard_workbooks\n',
                                '  numeric_fact_source: accepted_standard_workbooks\n'],
                               ['  - Read concrete numerical claims from the current workbooks under '
                                'core/user_execution_contract.yaml#result_handoff; use framework result '
                                'summaries and Numeric Profile to locate and display them.\n',
                                '  - Verify concrete numerical claims against accepted workbooks; framework '
                                'result summaries and Numeric Profile are navigation/display-policy layers, '
                                'not replacements for the numerical source of truth.\n'],
                               ['  - Update affected framework sections after semantic changes and after '
                                'checking primary results, result analysis or figure evidence.\n',
                                '  - Synchronize affected framework sections after semantic changes and '
                                'after accepted primary results, result analysis or figure evidence.\n'],
                               ['  - Use core/model_approval_contract.yaml for contest approval and '
                                'core/user_execution_contract.yaml#result_handoff for returned results. Run '
                                'pre_delivery_gates in their declared order when machine validation is '
                                'explicitly requested; formal_delivery_gates apply to '
                                'paper/review/submission scopes.\n',
                                '  - Apply formal_delivery_gates only to actual paper/review/submission '
                                'scopes, not intermediate design or framework outputs; all returned gates '
                                'still execute in their declared order.\n'],
                               ['  - Review Problem Contract, semantic closure and complexity before Model '
                                'Challenge; deliver project-level preprocessing or primary solve code after '
                                'the current model has passed both reviews and received explicit Human Model '
                                'Approval.\n',
                                '  - Problem Contract, semantic closure and complexity sanity must pass '
                                'before Model Challenge; project-level preprocessing or primary solve code '
                                'additionally requires challenge passed plus explicit Human Model Approval '
                                'bound to the current semantic_revision and validated semantic_identity_hash '
                                'under core/model_approval_contract.yaml; legacy hash provenance cannot '
                                'authorize new task code.\n'],
                               ['  - Check the returned primary workbook under result_handoff, then decide '
                                'whether post-primary result analysis is required.\n'
                                '  - Keep the primary solve script aligned with its checked workbook; when '
                                'analysis is required, use a separate stage-specific file with the '
                                'project-root numerical backend.\n'
                                '  - Use checked primary results and, when required, completed analysis '
                                'evidence for numerical figures and writing under Module 04 and the output '
                                'contract.\n',
                                '  - Primary user-produced workbook must be accepted before the Analysis '
                                'Necessity Gate can decide whether post-primary result analysis is '
                                'required.\n'
                                '  - Accepted primary workbooks freeze the primary solve script; when the '
                                'Gate is required, result-analysis code is a separate stage-specific file '
                                'that inherits the one project-root numerical backend.\n'
                                '  - Formal numerical-figure delivery and writing require validated_results '
                                'under Module 04 and the output contract. Selecting a figure-planning route '
                                'from accepted primary evidence is not formal delivery approval; every '
                                'scoped numerical claim still needs accepted primary evidence plus either '
                                'accepted passed analysis or a reasoned not_required disposition.\n']],
 'core/hsk_core_policy.md': [['# HSK Core Policy v11.3.0\n', '# HSK Core Policy v11.2.0\n'],
                             ['3. 建模方案、框架草稿等中间产物按当前阶段交付；终稿与提交包的检查在对应阶段进行。交付方式见 §6。\n',
                              '3. `pre_delivery_gates` 只约束 resolver '
                              '为当前任务、当前阶段实际返回的门禁。建模方案、框架草稿等中间产物不执行只为论文终稿或提交包设置的正式交付门禁；重复检查在相关输入、语义身份或产物确实变化前不重跑。\n'],
                             ['8. **批准对应当前模型。** 按 `core/model_approval_contract.yaml` '
                              '保存两次审查结论、用户明确批准及其对应模型；恢复同一模型时沿用已有批准。\n',
                              '8. **批准只绑定 current structured identity。** 只有用户明确批准当前 `semantic_revision` 与已验证 '
                              '`semantic_identity_hash`，且 current = validated = approved identity '
                              '后，`locked_model_spec` 才成为 current。legacy semantic hash 只保留只读 '
                              'provenance，不能授权新的项目级预处理或主求解。\n'],
                             ['批准与机器身份字段的具体写入由 `core/model_approval_contract.yaml` 定义。\n',
                              '上述字段、状态和验证细节只服从对应 Authority；`scripts/validate_semantic_governance.py` 与 '
                              '`scripts/validate_model_approval.py` 是 current 机器门，不由本文件维护第二套检查清单。\n'],
                             ['- `模型论文框架.md`：当前模型、双审结论、人工批准及证据位置；\n'
                              '- 实际返回的标准工作簿：具体数值事实，按 `core/user_execution_contract.yaml#result_handoff` '
                              '逐项核对；\n',
                              '- `模型论文框架.md`：current 项目语义与助手可读工作记忆；\n- accepted 标准工作簿：具体数值事实；\n'],
                             ['继续现有项目时执行 **read-before-use / '
                              'write-after-change**：读取框架中的当前模型、批准与必要依赖，从实际工作簿取数；发生变化后更新受影响的内容。机器字段保留实际工具运行结果。\n',
                              '四者不得互相替代。继续现有项目时必须 **read-before-use / write-after-change**：使用 current '
                              '框架恢复目标小问和必要依赖，具体数值回到 accepted workbook，状态判断回到 project '
                              'state；语义、结果或图表验收发生真实变化后，只同步受影响 current 内容。聊天记忆不能覆盖 current 项目事实。\n'],
                             ['将项目选定的版本解析到固定提交，并按 `core/bootstrap.yaml#startup_contract` '
                              '选择正式、局部或恢复范围。已有项目沿用其固定来源。\n',
                              '先核对固定仓库提交、入口版本和当前请求，按该提交 `core/bootstrap.yaml#startup_contract` '
                              '选择读取范围。在已有项目中沿用其固定来源。仅拿到分支或标签时，先解析到具体提交，后续读同一提交的原文。若已有项目的固定提交无法确认，先查项目已有记录，并说明仍待定位的规则范围。按启动合同选中全文或恢复时，取齐下述整套规范。默认的阶段读取或一次局部请求，取当前动作完整适用的正文。请求与入口示例不完全相同时，按实际交付判断。解释数据字段可保持局部，若要求据此改变模型的数据口径或形成正式结论，先完成正式开场。遇到边界不清，先核实请求与项目证据，保留仍未确定的条件。各模式都按此问当前批准和证据限定可执行的动作。\n'],
                             ['**正式开场。** 从固定提交读取 `core/full_reading/manifest.json`，按卷路径读齐全部规范正文，然后直接审题。开场不运行 '
                              'Skill 校验、哈希比对或本地 checker。按行读取时保留父段与上下文，补齐截断或遗漏内容。镜像只读一份。清单不可用时，按同一提交的 '
                              'bootstrap 指针和模块、模板登记取得现行规范原文。读取方法见 '
                              '`core/runtime_assurance_contract.yaml#reading_plan.formal_rule_delivery`。\n',
                              '**正式开场。** 从固定提交读取 `core/full_reading/manifest.json`，按其中的卷路径取回全部正文。清单由 '
                              '`core/module_manifest.yaml#rule_corpus` '
                              '的来源登记生成，可从每卷反查原文件、字节范围及物理别名。优先逐卷取完整原文。按行取得的响应可能省略段末换行，须保留请求范围和返回正文，按读取协议重组后与固定源核对。下文各条的适用条件仍取原文件的前言、父级和例外。镜像只读一份，示例保留其用途。只有 '
                              'GitHub 读权限时也可按固定路径逐卷读取；工具详情及可核验范围见 '
                              '`core/runtime_assurance_contract.yaml#reading_plan.formal_rule_delivery`。清单不可用时按固定树、bootstrap '
                              '指针、模块和模板登记追到现行合同明确委托的原文，包括规范性配置、案例和绘图资源的使用条件。不能界定全部来源时明确缺口，只推进有独立依据的动作。\n'],
                             ['**续做与缺口。** '
                              '跨聊天、只剩摘要或已无法界定规则范围时，重新阅读整套规范与完整当前框架。同一连续任务已读齐全文且范围清楚时，返回工作簿、转下一问或续写下一章，直接读取该阶段原文与证据。已知缺段只补所缺。换阶段、小问、章节、新图或证据范围时，按 '
                              '`core/runtime_assurance_contract.yaml#reading_plan.consumer_protocol` '
                              '取得相应完整原文。同阶段且原文、范围和证据未变时复用已有内容。\n',
                              '**续做与缺口。** '
                              '采用候选入口的正式任务跨聊天、只剩摘要或已无法界定失去哪些规则时，从固定源重新取得整套规范正文并通读已有的完整当前框架。阶段读取模式的跨聊天恢复仍依现行 '
                              'consumer_protocol 和 '
                              'project_memory_contract。同一连续正式任务已完成全文开场且整套范围仍清楚时，交回一份工作簿、转下一问或续写下一章，直接按相应阶段合同取回该动作原文和证据。整套范围明确、仅有已知缺段时，回到同一源补取对应段，核查首尾正文和上下文，防止行数相同但末行不全。换阶段、小问、章节、新图或证据范围时，按 '
                              '`core/runtime_assurance_contract.yaml#reading_plan.consumer_protocol` '
                              '重新取得该动作的完整适用原文，核实条件补读。只有原文仍完整可见、来源、范围与证据均未变的同阶段小修改可复用。全文写作、跨问综合和终审按 router 的 '
                              'project_memory_contract 通读完整当前框架。\n'],
                             ['**阶段工具。** 需要机器诊断时显式调用 '
                              'resolver，保留其当前问题的依赖诊断和有序检查。日常建模、代码交付与结果接续使用模型批准合同和结果交接合同。\n',
                              '**工具与证据。** 有匹配的资源根、依赖和项目材料时，用现有 resolver '
                              '决定动作、依赖与门序。只有仓库读取能力时，由助手取同一固定提交的原文。说明具体缺口及它影响的动作，并继续与该缺口无关的已授权工作。可选赛事材料依 §1.1 '
                              '回退。路径、目录清单、哈希、聊天摘要或已下载文件的大小均不能证明当前正文可见；规则取齐也不能证明批准、数值验收或交付通过。按实际运行报告工具结果，不另请用户运行本地 '
                              'checker 或逐章确认已读。\n'],
                             ['4. **主求解核对本次数值是否有效。** 按 Primary Quality '
                              'Specification、残差、可行性和离散/收敛证据检查当前模型与数值方法的实际结果；参数敏感性、压力场景、替代算法/结构、多 '
                              'seed/初值稳定性和异质性在独立结果深化分析中处理。\n',
                              '4. **主求解只回答当前计算能否 accepted。** Primary Quality Specification、Verification '
                              'ID、残差、可行性、离散/收敛和其它主数值证据只用于判断当前 locked model '
                              '与声明数值方法下的本次计算是否有效；参数敏感性、压力场景、替代算法/结构、多 seed/初值结论稳定性、异质性和广义 claim stability 属于 '
                              'accepted 之后的独立结果深化分析。\n'],
                             ['6. **按真实运行核对结果。** 依据 `core/user_execution_contract.yaml#result_handoff` '
                              '核对数据、参数、停止原因、运行范围及质量证据；数值检查服从 `core/numerical_verification_contract.yaml`。\n',
                              '6. **预期身份与实际执行证据都要保留。** 代码/数据指纹、实际停止原因、真实运行范围与质量证据按 user-execution / '
                              'numerical-verification Authority 核验；工作簿自行写出的 `passed` 不能替代机器可复算证据。\n'],
                             ['1. 正式论文使用当前模型、已逐项核对的实际数值和已确认图表。过期结果回到相应阶段更新。\n',
                              '1. 正式论文只能使用 current 模型、accepted 数值和已确认图表。stale 结果不得写成 current，不能用润色或版式掩盖语义/证据 '
                              'gap。\n'],
                             ['4. 外部经验参数、外部数据、领域事实、非显然标准定理和既有研究比较等核心 claim，形成 Citation '
                              'Evidence；本文推导和实际工作簿结果分别标明自身依据。\n',
                              '4. 外部经验参数、外部数据、领域事实、非显然标准定理和既有研究比较等需要外部来源的核心 claim，必须形成 Citation '
                              'Evidence；本文自己的推导和 accepted workbook 结果不得用外部引用代替。\n'],
                             ['1. 普通比赛依据当前模型批准、真实结果与本次交付要求推进。显式启用机器验收时，按 `scripts/resolve_runtime.py` 返回的 '
                              '`pre_delivery_gates` 顺序执行并读取实际报告。\n',
                              '1. `scripts/resolve_runtime.py` 返回的 `pre_delivery_gates` '
                              '是本次正式交付的完整有序机器门；必须按顺序真实执行并检查报告。读取更少、文件存在或 ZIP 生成都不等于 gate 已通过。\n'],
                             ['3. 最终审查与提交内容由 `modules/06_review_delivery.md`、`core/output_contract.yaml` '
                              '定义；显式工具验收按 resolver 返回的 LaTeX audit/compile attestation 与 submission package '
                              '检查执行。\n',
                              '3. 最终审查、LaTeX audit/compile attestation 与 submission package 只服从 '
                              '`modules/06_review_delivery.md`、`core/output_contract.yaml` 及 resolver 当前返回的 '
                              'gate；未核验赛事规则不得伪装成官方 Hard 要求。\n'],
                             ['| 主结果后的深化分析 | `modules/03_result_analysis.md` |\n',
                              '| accepted 后结果深化 | `modules/03_result_analysis.md` |\n']],
 'core/writing_runtime_contract.yaml': [['version: 11.3.0\n', 'version: 11.2.0\n']],
 'core/output_contract.yaml': [['version: 11.3.0\n', 'version: 11.2.0\n'],
                               ['  user_execution_authority: core/user_execution_contract.yaml\n'
                                '  result_handoff_authority: '
                                'core/user_execution_contract.yaml#result_handoff\n',
                                '  user_execution_authority: core/user_execution_contract.yaml\n'],
                               ['  role: explicit_machine_validation_pointer_only\n',
                                '  role: pre_delivery_integrity_gate_pointer_only\n'],
                               ['  workbook_authority: core/workbook_schema.yaml\n'
                                '  result_handoff_authority: '
                                'core/user_execution_contract.yaml#result_handoff\n',
                                '  workbook_authority: core/workbook_schema.yaml\n'],
                               ['  result_analysis_scope: 主工作簿核对后的敏感性、稳健性、阈值、多模型检验、同模型多算法检验、异质性与claim '
                                'stability；仅Gate=required时生成03B代码和工作簿；两类新比较遵循modules/03_result_analysis.md\n',
                                '  result_analysis_scope: 主工作簿accepted后的敏感性、稳健性、阈值、多模型检验、同模型多算法检验、异质性与claim '
                                'stability；仅Gate=required时生成03B代码和工作簿；两类新比较遵循modules/03_result_analysis.md\n'],
                               ['  stage_policy:\n'
                                '    primary: '
                                '主求解阶段继承项目根execution.solver_backend，按solver_scripts交付对应入口；数据入口由preprocessing_decision决定，只做主求解、PQS要求的内在数值有效性检查和不改变当前计算世界的Primary '
                                'Evidence Capture，主工作簿核对后冻结该脚本。\n'
                                '    result_analysis: 主工作簿核对后先执行Analysis Necessity '
                                'Gate；仅required时按solver_scripts生成继承同一项目根后端的独立深化入口，沿用preprocessing_decision与数据事实源并形成敏感性/稳健性/边界/替代方法等深化分析工作簿。\n',
                                '  stage_policy:\n'
                                '    primary: '
                                '主求解阶段继承项目根execution.solver_backend，按solver_scripts交付对应入口；数据入口由preprocessing_decision决定，只做主求解、PQS要求的内在数值有效性检查和不改变当前计算世界的Primary '
                                'Evidence Capture，主工作簿accepted后冻结该脚本。\n'
                                '    result_analysis: 主工作簿accepted后先执行Analysis Necessity '
                                'Gate；仅required时按solver_scripts生成继承同一项目根后端的独立深化入口，沿用preprocessing_decision与数据事实源并形成敏感性/稳健性/边界/替代方法等深化分析工作簿。\n'],
                               ['  two_python_stage_policy:\n'
                                '    primary: '
                                '主求解阶段继承项目根execution.solver_backend，按solver_scripts交付对应入口；数据入口由preprocessing_decision决定，只做主求解、PQS要求的内在数值有效性检查和不改变当前计算世界的Primary '
                                'Evidence Capture，主工作簿核对后冻结该脚本。\n'
                                '    result_analysis: 主工作簿核对后先执行Analysis Necessity '
                                'Gate；仅required时按solver_scripts生成继承同一项目根后端的独立深化入口，沿用preprocessing_decision与数据事实源并形成敏感性/稳健性/边界/替代方法等深化分析工作簿。\n',
                                '  two_python_stage_policy:\n'
                                '    primary: '
                                '主求解阶段继承项目根execution.solver_backend，按solver_scripts交付对应入口；数据入口由preprocessing_decision决定，只做主求解、PQS要求的内在数值有效性检查和不改变当前计算世界的Primary '
                                'Evidence Capture，主工作簿accepted后冻结该脚本。\n'
                                '    result_analysis: 主工作簿accepted后先执行Analysis Necessity '
                                'Gate；仅required时按solver_scripts生成继承同一项目根后端的独立深化入口，沿用preprocessing_decision与数据事实源并形成敏感性/稳健性/边界/替代方法等深化分析工作簿。\n'],
                               ['  solver: 项目根只选择一次数值后端；每问按该后端的solver_scripts交付独立主求解脚本，主工作簿核对后仅在Analysis '
                                'Necessity '
                                'Gate=required时增加同后端独立深化脚本。not_needed/question_local可读取原始数据，project_level读取统一工作簿。主求解入口负责主求解、当前主计算最低数值有效性检查及不改变当前计算世界的高价值状态/过程/结构Evidence '
                                'Capture；深化入口仅在Gate=required时负责敏感性、稳健性、边界、替代方法/结构等独立深化分析并保留细粒度底层证据。\n',
                                '  solver: '
                                '项目根只选择一次数值后端；每问按该后端的solver_scripts交付独立主求解脚本，主工作簿accepted后仅在Analysis '
                                'Necessity '
                                'Gate=required时增加同后端独立深化脚本。not_needed/question_local可读取原始数据，project_level读取统一工作簿。主求解入口负责主求解、当前主计算最低数值有效性检查及不改变当前计算世界的高价值状态/过程/结构Evidence '
                                'Capture；深化入口仅在Gate=required时负责敏感性、稳健性、边界、替代方法/结构等独立深化分析并保留细粒度底层证据。\n'],
                               ['- 主工作簿核对后冻结主求解入口，并执行Analysis Necessity '
                                'Gate；required时按solver_scripts单独生成继承项目根后端的深化入口，not_required时必须记录理由且不得用该状态支持鲁棒性/稳定性主张。\n',
                                '- 主工作簿accepted后冻结主求解入口，并执行Analysis Necessity '
                                'Gate；required时按solver_scripts单独生成继承项目根后端的深化入口，not_required时必须记录理由且不得用该状态支持鲁棒性/稳定性主张。\n']],
 'core/model_approval_contract.yaml': [['    scope: explicit_machine_validation\n', ''],
                                       ["    Save the user's statement, its source and approved questions "
                                        'with the current model\n'
                                        '    and review conclusions in the framework. Set '
                                        'human_model_approval_status to approved\n'
                                        '    and approved_semantic_revision to the approved revision. '
                                        'Deliver the updated framework\n'
                                        '    when the host cannot write project files directly.\n'
                                        '  resume_rule: >-\n'
                                        '    Read the current model and saved approval; check the question, '
                                        'revision and actual\n'
                                        '    model content, then continue with the required inputs. '
                                        'Result-location updates,\n'
                                        '    wording changes and absent machine hashes do not require '
                                        'another approval.\n'
                                        '  machine_binding_rule: >-\n'
                                        '    For explicit machine validation, establish the current '
                                        'validated SIB first, then\n'
                                        '    check the saved two-pass review and user approval against that '
                                        'model. Restore the\n'
                                        '    corresponding challenge/approval statuses and bind '
                                        'approved_semantic_identity_hash\n'
                                        '    to the validated identity. Validation does not create user '
                                        'approval; legacy\n'
                                        '    approved_semantic_hash remains historical read-only '
                                        'provenance.\n',
                                        '    Explicit approval copies the current structured '
                                        'semantic_identity_hash into\n'
                                        '    approved_semantic_identity_hash when structured identity is '
                                        'present. After the\n'
                                        '    Phase C migration boundary, pre-code approval must not newly '
                                        'write or refresh\n'
                                        '    legacy approved_semantic_hash. Migration or validation code '
                                        'must never synthesize\n'
                                        '    human approval.\n'],
                                       ['  activation: selected_model_or_algorithm_comparison\n',
                                        '  activation: current_analysis_comparison_1.0.0_only\n'],
                                       ['  ordinary_workflow: >-\n'
                                        '    Check the actual primary workbook under '
                                        'core/user_execution_contract.yaml#result_handoff.\n'
                                        '    Save the comparison models/algorithms, common evaluation scope, '
                                        'independent reviews\n'
                                        '    and explicit user approval in the existing framework comparison '
                                        'section. Freeze the\n'
                                        '    concrete checks before code delivery and continue within that '
                                        'approved scope.\n'
                                        '  primary_identity: unchanged_user_approved_model\n',
                                        '  scope_shape: '
                                        'core/project_state.schema.yaml#/$defs/analysis_comparison\n'
                                        '  implementation: scripts/analysis_comparison.py\n'
                                        '  framework_marker: '
                                        'HSK_ANALYSIS_COMPARISON_BEGIN_END_Qn_after_result_summary\n'
                                        '  primary_identity: unchanged_full_current_validated_approved_SIB\n'
                                        '  scope_digest:\n'
                                        '    includes: [protocol_version, question, '
                                        'baseline_semantic_identity_hash, complete_model_specs, '
                                        'algorithm_definitions, comparison_questions, '
                                        'common_evaluation_protocols]\n'
                                        '    excludes: [future_primary_workbook_hash, actual_results, '
                                        'final_evidence_row_positions, approval_records]\n'],
                                       ['    each_record_requires: [distinct_review_reference, '
                                        'passed_verdict, actual_method, '
                                        'concrete_boundary_and_independence_conclusion, no_blocking_items, '
                                        'no_unresolved_items]\n',
                                        '    each_record_requires: [distinct_review_reference, '
                                        'matching_scope_sha256, passed_verdict, actual_method, '
                                        'concrete_boundary_and_independence_conclusion, no_blocking_items, '
                                        'no_unresolved_items]\n'],
                                       ['    binding: current_comparison_scope_saved_in_framework\n',
                                        '    binding: current_scope_sha256\n'],
                                       ['    create_after: primary_workbook_checked_under_result_handoff\n',
                                        '    create_only_after_primary_accepted: true\n'],
                                       ['  machine_validation:\n'
                                        '    activation: '
                                        'explicit_current_analysis_comparison_1.0.0_validation\n'
                                        '    scope_shape: '
                                        'core/project_state.schema.yaml#/$defs/analysis_comparison\n'
                                        '    implementation: scripts/analysis_comparison.py\n'
                                        '    framework_marker: '
                                        'HSK_ANALYSIS_COMPARISON_BEGIN_END_Qn_after_result_summary\n'
                                        '    primary_identity: '
                                        'unchanged_full_current_validated_approved_SIB\n'
                                        '    scope_digest:\n'
                                        '      includes: [protocol_version, question, '
                                        'baseline_semantic_identity_hash, complete_model_specs, '
                                        'algorithm_definitions, comparison_questions, '
                                        'common_evaluation_protocols]\n'
                                        '      excludes: [future_primary_workbook_hash, actual_results, '
                                        'final_evidence_row_positions, approval_records]\n'
                                        '    review_binding: matching_scope_sha256\n'
                                        '    human_approval_binding: current_scope_sha256\n'
                                        '    concrete_plan_requires: accepted_primary_execution\n',
                                        ''],
                                       ['    locked_model_spec is current after Model Challenge passes and '
                                        'the user explicitly\n'
                                        '    approves the current model and semantic revision. Restore that '
                                        'approval from the\n'
                                        '    framework under human_approval.resume_rule. Explicit machine '
                                        'validation additionally\n'
                                        '    applies human_approval.binding.\n',
                                        '    selected_models and semantic closure do not by themselves '
                                        'create a locked_model_spec.\n'
                                        '    locked_model_spec is current only after Model Challenge passes '
                                        'and the user explicitly\n'
                                        '    approves the current semantic revision and current structured '
                                        'semantic identity.\n'
                                        '    Legacy semantic_hash approval remains readable historical '
                                        'provenance but cannot\n'
                                        '    authorize new preprocessing or primary-solve code after Phase C '
                                        'migration applies.\n'],
                                       ['  - result_location_update_without_semantic_change\n', ''],
                                       ['    - approved_questions_and_semantic_revision\n'
                                        '    - user_approval_statement_and_source\n',
                                        ''],
                                       ['  old_projects_without_fields: '
                                        'restore_current_framework_review_and_approval\n',
                                        '  old_projects_without_fields: read_only_compatible\n'],
                                       ['    For explicit machine validation of an old project, establish a '
                                        'complete current\n'
                                        '    SIB and its validated baseline, then apply '
                                        'human_approval.machine_binding_rule.\n'
                                        '    Ordinary continuation uses the saved current model, review and '
                                        'approval. A real\n'
                                        '    model change requires the corresponding review and user '
                                        'approval again.\n',
                                        '    When an old project re-enters model_design, data_preprocessing, '
                                        'solve_validate,\n'
                                        '    or regenerates primary code after a semantic change, establish '
                                        'a complete current\n'
                                        '    SIB, pass semantic governance to create the validated identity '
                                        'baseline, rerun the\n'
                                        '    required Model Challenge, and obtain explicit Human Approval of '
                                        'the current identity\n'
                                        '    before code generation. Do not infer a verified SIB '
                                        'automatically from old prose.\n']],
 'core/project_state.schema.yaml': [['          description: v8 legacy Markdown semantic-scope '
                                     'hash；历史只读。显式机器验收使用 current SIB。\n',
                                     '          description: v8 legacy Markdown semantic-scope '
                                     'hash；仅历史只读兼容。无SIB项目重新进入active workflow时必须先建立current SIB，活动代码不得写入。\n'],
                                    ['          description: v8 legacy validated Markdown semantic-scope '
                                     'hash；历史只读。显式机器验收使用 current SIB。\n',
                                     '          description: v8 legacy validated Markdown semantic-scope '
                                     'hash；仅历史只读兼容。无SIB项目重新进入active workflow时必须先建立current SIB，活动代码不得写入。\n']],
 'core/runtime_assurance_contract.yaml': [['  Define the machine-readable runtime assurance layer for '
                                           'explicit resolver\n'
                                           '  invocation: context hydration, intent provenance, artifact '
                                           'assurance,\n'
                                           '  declarative contract dependency closure, and authority '
                                           'fingerprinting.\n'
                                           '  Ordinary competition reading follows '
                                           'reading_plan.formal_rule_delivery;\n'
                                           '  approval and result handoff follow their owning contracts.\n',
                                           '  Define the machine-readable runtime assurance layer that sits '
                                           'above the legacy\n'
                                           '  resolver plan: context hydration, intent provenance, artifact '
                                           'assurance,\n'
                                           '  declarative contract dependency closure, and authority '
                                           'fingerprinting. This\n'
                                           '  contract does not redefine modeling, workbook, approval, '
                                           'execution, writing,\n'
                                           '  numerical-verification, or submission semantics owned by their '
                                           'existing authorities.\n'],
                                          ['    version_binding: Resolve the chosen ref once to its full Git '
                                           'commit and read the inventory and rule text from that commit.\n'
                                           '    github_only: Read every volume listed in the manifest, then '
                                           'start problem analysis.\n'
                                           '    github_line_ranges: Read complete sections in source order, '
                                           'including their parent context. Retrieve any missing or '
                                           'truncated ranges.\n'
                                           '    continuity: Supplement known missing volumes or ranges. '
                                           'After cross-chat recovery or loss of the reading scope, read the '
                                           'complete rule text and current project framework again.\n',
                                           '    version_binding: Resolve the chosen ref once to its full Git '
                                           'commit. Obtain the inventory, expected hashes and all content at '
                                           'that same commit.\n'
                                           '    byte_identity: Verify the actual UTF-8 response bytes '
                                           'against the independently retrieved manifest. Git blob IDs and '
                                           'newline-normalized distribution hashes have distinct meanings.\n'
                                           '    offsets: Zero-based half-open byte ranges in the original '
                                           'file and volume. Preserve complete code points, source order and '
                                           'the original line endings.\n'
                                           '    github_only: Retrieve the manifest and bounded volumes as '
                                           'complete files at the pin when available. Authenticate the '
                                           'returned bytes independently. For explicit GitHub line slices, '
                                           'retain the requested inclusive ranges, response text and blob '
                                           'identity.\n'
                                           '    github_line_ranges: A ranged GitHub file response may omit '
                                           'its terminal LF. Reassemble only observed line bodies with the '
                                           'documented separators and check against the original blob. '
                                           'Report reconstructed lines separately from raw whole-file '
                                           'transport. Retry precise gaps or fetch the affected whole blob '
                                           'when framing is ambiguous. Without hashing report visible ranges '
                                           'and verification limits.\n'
                                           '    continuity: Retry only identified missing or damaged volumes '
                                           'while the complete scope and intact bodies remain available. An '
                                           'identical retransmission counts once. After a lost scope, '
                                           'summary-only context or cross-chat formal recovery, retrieve all '
                                           'bodies afresh.\n'
                                           '    evidence_boundary: Receipt verification describes the '
                                           'supplied texts at the selected commit. Record current visible '
                                           'text separately. Internal context retention is unobservable. '
                                           'Project evidence, model approval and delivery gates keep their '
                                           'own authorities.\n'],
                                          ['      source_identity: '
                                           'same_reading_plan.source_identity_for_every_chunk\n',
                                           '      source_identity: '
                                           'same_reading_plan.source_identity_for_every_chunk\n'
                                           '      sha256: '
                                           'calculate_full_source_sha256_when_available_otherwise_mark_unavailable\n'
                                           '      blob_id: distinct_from_sha256\n'],
                                          ['        - repeated_ranges_are_read_once\n'
                                           '        - source_identity_is_consistent\n',
                                           '        - overlap_is_detected_and_rejected_not_silently_counted\n'
                                           '        - source_identity_is_consistent\n'
                                           '        - '
                                           'compare_text_with_independently_obtained_source_bytes_when_available\n'
                                           '      structural_coverage_only: Without trusted original bytes a '
                                           'matching number of lines cannot establish byte integrity.\n'],
                                          ['      complete_only_when: all_required_text_is_read\n',
                                           '      complete_only_when: '
                                           'all_required_ranges_returned_and_checked\n'],
                                          ['      pre_delivery_gates: '
                                           'explicit_machine_validation_uses_resolver_returned_order\n',
                                           '      pre_delivery_gates: '
                                           'use_resolver_returned_order_without_parallel_gate_list\n'],
                                          ['    - Explicit machine-validation clients use the complete '
                                           'returned gate sequence.\n',
                                           '    - The legacy resource plan and complete machine closure '
                                           'remain available to old clients; new clients must not run fewer '
                                           'gates.\n']],
 'core/user_execution_contract.yaml': [['purpose: '
                                        '定义用户本地完整数值执行、真实结果交接及显式机器验收。主求解与按需深化分析使用项目已选后端，运行事实写入各自工作簿。\n',
                                        'purpose: '
                                        '定义用户本地完整版数值执行链；所有数据项目先根据当前题目、当前附件和模型输入要求锁定preprocessing_decision，只有project_level才增加项目级预处理执行边界。每问主求解使用项目唯一已选Python或MATLAB后端的独立入口；结果深化分析仅在主工作簿accepted后经过Analysis '
                                        'Necessity '
                                        'Gate且判定required时使用独立入口，并必须继承同一项目数值后端。P5a起新生成阶段脚本使用RUN_CONFIG承载任务可变输入，全局user/full-fidelity/no-degradation政策由本Authority继承；P5b起新生成阶段脚本通过run_receipt_protocol_version绑定版本化RUN_RECEIPT，实际运行事实仍写入既有工作簿运行配置工作表。v7.14起新生成主求解还绑定Primary '
                                        'Quality Specification与主数值证据独立复核，但不得把结果深化分析提前塞进主求解。\n'],
                                       ['result_handoff:\n'
                                        '  approval_authority: '
                                        'core/model_approval_contract.yaml#human_approval\n'
                                        '  read: 打开本问实际返回的工作簿，按工作表、精确字段、记录键和单位读取答案及底层证据。\n'
                                        '  check: 对照当前模型、输入和Primary Quality '
                                        'Specification核对结果、约束、残差及适用数值证据；有缺项或错误时定位到受影响的计算。\n'
                                        '  record: 在模型论文框架的本问结果摘要记录文件、表、字段、记录键、单位和可支持的结论；保留尚待处理的具体问题。\n'
                                        '  continue: 核对后的主结果进入Analysis Necessity '
                                        'Gate；required时完成相应分析，not_required时记录理由；图文从各自真实来源取数。\n'
                                        '  replacement: 工作簿内容或上游模型、数据变化时，重新核对受影响的结果、图文和后问依赖。\n'
                                        '  machine_validation: '
                                        '显式工具按code_delivery、returned_workbook和execution_states执行机器资格检查并记录accepted、verified与验证哈希；比赛接续使用上述实物记录。\n',
                                        ''],
                                       ['  - Current question stages carry source-bundle and acceptance '
                                        'identities, never a second backend or selection reason. Primary and '
                                        'analysis must both match the project backend; analysis consumes the '
                                        'current primary workbook under result_handoff.\n',
                                        '  - Current question stages carry source-bundle and acceptance '
                                        'identities, never a second backend or selection reason. Primary and '
                                        'analysis must both match the project backend; analysis consumes the '
                                        'current accepted primary workbook.\n'],
                                       ['  - 按result_handoff读取用户返回的工作簿，核对真实结果与数值证据，并更新框架中的结果位置\n'
                                        '  - 依据已取得的材料继续处理；缺少必要输入时指出具体缺项\n'
                                        '  - '
                                        '核对预处理、主求解及Gate=required时的深化分析结果后，按绘图后端生成data_process.py或data_process.m；绘图脚本只读工作簿\n',
                                        '  - '
                                        '由助手读取用户返回的工作簿并执行Schema、哈希、质量门和主数值证据一致性校验；用户正常交接是实际产物与必要失败信息，不额外执行checker或提交独立校验报告\n'
                                        '  - '
                                        '工具或必要材料不可用时报告具体未完成项，不把内部校验转交用户代跑、不授予新accepted或verified；仅有上下文不足不写结果失败，已观察到的真实错误和漂移仍按原规则处理\n'
                                        '  - 在预处理工作簿accepted、主求解以及Gate=required时必要的结果深化分析完成后，于Figure '
                                        'Evidence阶段按绘图后端生成data_process.py或data_process.m；该绘图脚本只读工作簿绘图，不执行数值预处理\n'],
                                       ['    freeze_after: result_handoff_completed\n',
                                        '    freeze_after: preprocessing_workbook_accepted\n'],
                                       ['    role: '
                                        '按已选后端交付唯一主求解入口，只负责主求解与PQS要求的当前主计算内在数值有效性检查并输出问题X求解结果.xlsx；主工作簿按result_handoff核对后该脚本冻结，不为结果深化分析改写。\n',
                                        '    role: '
                                        '按已选后端交付唯一主求解入口，只负责主求解与PQS要求的当前主计算内在数值有效性检查并输出问题X求解结果.xlsx；主工作簿accepted后该脚本冻结，不为结果深化分析改写。\n'],
                                       ['    activation: 主工作簿按result_handoff核对后执行Analysis Necessity '
                                        'Gate；仅Gate=required时激活\n',
                                        '    activation: 主工作簿accepted后先执行Analysis Necessity '
                                        'Gate；仅Gate=required时激活\n'],
                                       ['  primary_prerequisites: '
                                        '比赛流程按result_handoff核对主结果；显式CLI验收检查accepted、quality '
                                        'passed、项目内路径、实际与验收哈希、相关数值stale及适用的project_level预处理。\n',
                                        '  primary_prerequisites: 读写和CLI都验证accepted且quality '
                                        'passed的主工作簿、项目内路径、实际与验收哈希、相关数值stale及适用的project_level预处理；图或论文独有stale不使主数值结果失效。\n'],
                                       ['    专用比较按 '
                                        'core/model_approval_contract.yaml#analysis_comparison_approval '
                                        '接续；显式机器验收使用 analysis_comparison，同一问各类检验分别核验。\n',
                                        '    专用比较使用 analysis_comparison；同一问同时采用两类检验时，各自核验对应记录。\n'],
                                       ['  activation: 显式机器验收中，当前比较登记、方法、源码标记、回执标记或专用比较表触发本协议。\n',
                                        '  activation: '
                                        'any_current_analysis_comparison_registry_method_source_marker_receipt_marker_or_new_comparison_sheet\n']],
 'modules/02_model_design.md': [['批准后，在框架当前审批节保存批准小问、semantic '
                                 'revision、用户原话及消息来源，连同当前模型和两次审查结论一起保存。已有项目状态同步记录：\n',
                                 '批准时在 machine state 中绑定当前结构化语义身份：\n'],
                                ['approved_semantic_revision = current semantic_revision\n',
                                 'approved_semantic_revision = current semantic_revision\n'
                                 'approved_semantic_identity_hash = current semantic_identity_hash\n'],
                                ['宿主不能直接写项目文件时，交付更新后的完整框架。机器身份字段按实际验证结果填写；普通比赛按 '
                                 '`core/model_approval_contract.yaml#human_approval` 继续，无需先运行仓库检查。\n',
                                 '这里的 `semantic_identity_hash` 必须来自当前 `模型论文框架.md` 中完整、可解析且已通过 '
                                 '`scripts/semantic_identity.py` canonicalization 的 SIB，并先由 semantic '
                                 'governance 建立 `validated_semantic_identity_hash`。legacy `semantic_hash / '
                                 'approved_semantic_hash` 只保留旧项目历史只读 provenance；旧项目重新进入 `model_design / '
                                 'data_preprocessing / solve_validate` 或重新生成主代码前，必须先建立 current SIB、重新完成必要的 '
                                 'Challenge 与 Human Approval。**不得根据旧 prose 自动推断完整 SIB 并声称 verified。**\n'],
                                ['→ proposed_model_spec\n',
                                 '→ proposed_model_spec\n→ current validated SIB\n'],
                                ['`locked_model_spec` 对应用户已批准的当前模型与 semantic revision。尚未取得明确批准时停在 '
                                 '`awaiting_model_approval`。\n',
                                 '因此 `locked_model_spec` 只能在 challenge passed 且用户明确批准当前 `semantic_revision / '
                                 'semantic_identity_hash` 后成为 current。未批准或仍只有 legacy approval provenance '
                                 '时，本模块必须停在 `awaiting_model_approval`，不得交付正式预处理代码或主求解代码。\n'],
                                ['实际模型变化后，旧 `model_challenge_status`、`human_model_approval_status` 与 '
                                 '`locked_model_spec` 变 stale，重新完成受影响的设计、双审与批准。Markdown '
                                 '排版、纯措辞、图注、公式编号、小节标题压缩、结果位置回填和不改变模型的 LaTeX 文件拆分沿用原批准。\n'
                                 '\n'
                                 '跨会话恢复先读当前模型和保存的批准，核对小问、revision 与实际模型内容，再读取本问所需输入并继续；机器字段缺失不触发重复批准。\n',
                                 '当前 `semantic_revision` 或 structured `semantic_identity_hash` 改变时，旧 '
                                 '`model_challenge_status`、`human_model_approval_status` 与 '
                                 '`locked_model_spec` 同时变 stale；必须重新完成必要的语义闭环、Complexity Sanity、Model '
                                 'Challenge 和 Human Approval。Markdown 排版、纯措辞、图注、公式编号、小节标题压缩或不改变 SIB identity '
                                 '的 LaTeX 文件拆分只更新 text provenance，不触发重新审批。无 SIB 的 legacy `semantic_hash` '
                                 '仅用于迁移期只读兼容。\n'],
                                ['显式启用机器验收时，`scripts/validate_semantic_governance.py` '
                                 '先建立当前验证基线，再按批准合同核对已保存的双审和用户批准、恢复对应状态并绑定身份，由 '
                                 '`scripts/validate_model_approval.py` 校验。治理引起的机器 stale '
                                 '不会删除框架中的批准记录；实际模型变化仍按上段处理。\n',
                                 '若已验证的模型身份或语义修订号变化，`scripts/validate_semantic_governance.py` '
                                 '在更新基线前，按依赖类型将本问及受影响后问的相应产物标记 stale。旧结果在重新求解和验收前保持 stale。代码前再由 '
                                 '`scripts/validate_model_approval.py` 核验 challenge/approval 与当前 '
                                 'revision/identity 的绑定关系。\n'],
                                ['`proposed_model_spec` 形成后按 `templates/model/model_paper_framework.md` '
                                 '建立或更新项目根目录 `模型论文框架.md`，保存当前模型、双审结论及批准记录；用户批准后更新为 `locked_model_spec`。SIB '
                                 '内嵌于框架，机器身份解析复用 `scripts/semantic_identity.py`。\n',
                                 '`proposed_model_spec` 形成后即可按 `templates/model/model_paper_framework.md` '
                                 '建立或更新项目根目录 `模型论文框架.md`，用于承载当前模型口径、Semantic Identity Block、Model Challenge '
                                 '和 Approval Brief；用户批准后再把当前模型状态提升为 `locked_model_spec`。框架不是批准本身，批准事实以 '
                                 'machine state 中绑定的当前 revision/identity 为准。SIB 仍内嵌在 framework '
                                 '中，不建立第二份模型真相；解析与 canonicalization 只复用 '
                                 '`scripts/semantic_identity.py`，本模块不得复制另一套 parser/canonical 规则。\n'],
                                ['1. 继续某一问前读取当前模型、双审结论、用户批准记录、结果摘要和必要依赖；\n',
                                 '1. 继续某一问前优先读取当前有效口径、该问当前模型/结果摘要、Challenge/Approval 状态和必要依赖；\n'],
                                ['4. 框架过期时按实际模型和结果更新受影响内容，再继续下游工作；\n'
                                 '5. 具体数值从真实工作簿读取，交接见 `core/user_execution_contract.yaml#result_handoff`。\n',
                                 '4. 框架 stale 时先依据 project state 与已验收产物修正，再继续下游工作；\n'
                                 '5. 具体数值回到 accepted standard workbook 核验，框架摘要不替代数值事实源。\n'],
                                ['- SIB 保存本问实际数学定义；显式机器验收时通过共享 parser/canonicalizer 建立身份；\n',
                                 '- 进入 structured identity 路径时，先完整填充当前问 SIB 并通过共享 parser/canonicalizer '
                                 '校验，再原子写入 framework；不得把带 placeholder 或半成品 marker 的 live SIB 当作当前身份；\n'],
                                ['- 交付前核对当前模型、审查与批准记录，并保存完整框架。\n', '- 正式交付前通过语义治理、Model Approval 验证和框架验证。\n'],
                                ['模型、双审、批准与论文组织从当前框架恢复；项目状态登记修订、依赖及实际机器验证结果；数值从真实工作簿读取。\n',
                                 '事实源边界：模型语义与论文组织仍以 current framework 为项目记忆，其中 SIB '
                                 '只提供稳定机器身份；修订、依赖、identity/text provenance、Challenge/Approval 状态与 stale 以 '
                                 'project state 为准；具体数值以 accepted standard workbook 为准。三者职责不得互相替代。\n'],
                                ['2. **审批完整性**：按 `core/model_approval_contract.yaml#human_approval` '
                                 '核对当前模型的双审结论与用户批准，保存对应记录。\n',
                                 '2. **审批完整性**：调用 `scripts/validate_model_approval.py` 检查 current Challenge '
                                 '/ Approval。审批状态、用户显式批准、revision/identity 绑定、blocking/review_required 处置及 '
                                 'stale 规则只由 `core/model_approval_contract.yaml` 定义，本模块不复制字段级判定表。\n'],
                                ['设计完成后向用户提交 Model Approval Brief 和当前框架，等待明确批准；批准后形成 current '
                                 '`locked_model_spec`。若 `preprocessing_decision=project_level`，进入 Module '
                                 '03P；否则进入主求解。\n',
                                 '若设计完整性已经满足但 Model Approval gate 尚未通过，形成 '
                                 '`route_comparison`、`selected_models`、`proposed_model_spec`、Model Approval '
                                 'Brief、`awaiting_model_approval`、`mechanism_contracts`（适用时）与 current '
                                 'framework 后停止；不得把“用户未反对”解释为 approval。Gate 通过后才形成 current '
                                 '`locked_model_spec`。若 `preprocessing_decision=project_level`，下一阶段进入 Module '
                                 '03P；否则直接进入主求解。\n']],
 'modules/03_solve_validate.md': [['若项目根目录已有 current '
                                   '`模型论文框架.md`，正式生成本问代码前必须先读取“当前有效口径”、本问“当前模型口径/求解与验证方案/模型挑战与人工锁模”以及必要前问依赖，用它恢复当前模型语义；不得仅凭聊天记忆重建变量、参数、目标或约束。具体输入与结果按 '
                                   '`core/user_execution_contract.yaml#result_handoff` 从当前数据和工作簿核对。\n',
                                   '若项目根目录已有 current '
                                   '`模型论文框架.md`，正式生成本问代码前必须先读取“当前有效口径”、本问“当前模型口径/求解与验证方案/模型挑战与人工锁模”以及必要前问依赖，用它恢复当前模型语义；不得仅凭聊天记忆重建变量、参数、目标或约束。具体输入数值和已验收结果仍回到当前数据事实源/标准工作簿核验。\n'],
                                  ['按 `core/model_approval_contract.yaml#human_approval` '
                                   '读取本问双审结论、用户批准和对应模型版本，接续代码交付。当前模型尚未获得批准时回到 Module 02，停在 '
                                   '`awaiting_model_approval`。\n',
                                   '进入本模块前，助手为当前小问依次执行 `scripts/validate_semantic_governance.py` 与 '
                                   '`scripts/validate_model_approval.py`。前者负责当前题意/语义/复杂度与 stale 一致性，后者是 '
                                   'Challenge/Human Approval 的唯一字段级运行门；具体批准状态、revision/structured identity '
                                   '绑定与失效条件只服从 `core/model_approval_contract.yaml`，本模块不复制第二套检查清单。\n'
                                   '\n'
                                   '任一 gate 未通过都不得生成正式主求解代码；Model Approval 未通过时返回 Module 02，并停在 '
                                   '`awaiting_model_approval`。\n'],
                                  ['主求解质量检查的唯一数值规则 Authority 为 '
                                   '`core/numerical_verification_contract.yaml`。它只回答：**在当前 locked model 与声明的 '
                                   'numerical method 下，本次主计算是否具有足够的内在数值有效性，可以支持本问答案与后续分析。**\n',
                                   '主求解质量检查的唯一数值规则 Authority 为 '
                                   '`core/numerical_verification_contract.yaml`。它只回答：**在当前 locked model 与声明的 '
                                   'numerical method 下，本次主计算是否具有足够的内在数值有效性，可以成为 accepted solution '
                                   'workbook。**\n'],
                                  ['**不得把参数敏感性、现实参数扰动、阈值/失效边界扩展搜索、场景压力测试、替代算法比较、替代结构/模型比较、多随机种子或多初值稳健性、异质性、误差分解、广义外样本稳定性等结果深化分析内容写入主求解质量门。** '
                                   '这些内容在主工作簿核对后进入 Module '
                                   '03B。若某一主算法按数学定义本身需要多起点/多随机种子才能构成一次完整求解，这些运行可以作为主算法内部步骤，但不得据此在 03A '
                                   '中生成“跨算法稳健性”或“结论稳定性”分析。\n',
                                   '**不得把参数敏感性、现实参数扰动、阈值/失效边界扩展搜索、场景压力测试、替代算法比较、替代结构/模型比较、多随机种子或多初值稳健性、异质性、误差分解、广义外样本稳定性等结果深化分析内容写入主求解质量门。** '
                                   '这些内容只能在主工作簿 accepted 后进入 Module '
                                   '03B。若某一主算法按数学定义本身需要多起点/多随机种子才能构成一次完整求解，这些运行可以作为主算法内部步骤，但不得据此在 03A '
                                   '中生成“跨算法稳健性”或“结论稳定性”分析。\n'],
                                  ['用户返回工作簿后，按 `core/user_execution_contract.yaml#result_handoff` '
                                   '读取运行配置、答案和底层数值证据，独立核对适用的质量判据。v7.13 历史工作簿保持只读兼容；旧项目重新进入当前主求解时应按 v7.14 '
                                   '轨迹生成本问新工作簿。\n',
                                   '用户返回工作簿后，助手通过 `scripts/validate_user_execution.py` 核验执行所有权、full-fidelity '
                                   '配置和代码/数据哈希，并由其调用 `scripts/validate_numerical_evidence.py` '
                                   '独立复核适用主数值证据；工作簿自行写出的“是否通过”不能替代机器可重算的证据一致性。v7.13 '
                                   '历史工作簿保持只读兼容；旧项目重新进入当前主求解时应按 v7.14 轨迹生成本问新工作簿。\n'],
                                  ['→ Human Model Approval（保存对应模型、revision与用户批准）\n',
                                   '→ Human Model Approval（绑定 current semantic_revision + validated '
                                   'semantic_identity_hash；legacy hash 只读兼容）\n'
                                   '→ semantic governance gate\n'
                                   '→ model approval gate\n'],
                                  ['→ 助手静态检查执行配置与代码工程质量\n', '→ 助手执行代码交付检查：执行配置 + 代码工程质量门\n'],
                                  ['→ 按result_handoff核对答案、运行配置与数值证据\n→ 核对后冻结所选主求解入口及其声明源码依赖\n',
                                   '→ 助手验收：运行配置/哈希 + 主结果质量门 + numerical evidence独立复核\n'
                                   '→ accepted后冻结所选主求解入口及其声明源码依赖\n'],
                                  ['若实现过程中发现必须新增核心变量、修改目标函数/约束、改变 '
                                   '`preprocessing_decision`、公共数据处理或算法语义，应停止代码交付，递增 `semantic_revision`，更新 '
                                   '`semantic_change_categories`，把旧 '
                                   '`model_challenge_status`、`human_model_approval_status` 和 '
                                   '`locked_model_spec` 标记 stale，必要时回退 Module 03P 或 Module 02，重新闭环、重新 '
                                   'Challenge、按批准合同保存新的用户 Approval。\n',
                                   '若实现过程中发现必须新增核心变量、修改目标函数/约束、改变 '
                                   '`preprocessing_decision`、公共数据处理或算法语义，应停止代码交付，递增 `semantic_revision`，更新 '
                                   '`semantic_change_categories`，把旧 '
                                   '`model_challenge_status`、`human_model_approval_status` 和 '
                                   '`locked_model_spec` 标记 stale，必要时回退 Module 03P 或 Module 02，重新闭环、重新 '
                                   'Challenge、重新取得用户 Approval，并再次运行两个治理门。\n'],
                                  ['新生成主脚本必须只定义一个静态可读 `RUN_CONFIG`（Python 顶层字典或 MATLAB 主函数初始区域的受限 JSON '
                                   '字面量，语法服从执行 Authority），其中锁定 stage/problem/data '
                                   'path+hash/solver/seed/tolerance/limit/expected workbook 等任务可变输入，并在 '
                                   'primary 阶段写入 '
                                   '`primary_quality_protocol_version`。`execution_owner=user`、`execution_profile=full_fidelity` '
                                   '与六个 no-degradation 标志由 `core/user_execution_contract.yaml` '
                                   '全局继承，不在脚本中重复自报；`solver_version` 等实际运行事实仍由返回主工作簿 `运行配置` 记录和验收。旧 '
                                   '`FULL_FIDELITY_CONFIG/FULL_RUN_CONFIG` 仅作只读兼容且继续按旧完整字段要求校验。默认不生成独立 '
                                   'YAML、运行说明或校验报告。主工作簿核对后不得为了结果深化分析覆盖更新主求解入口；深化分析进入 Module '
                                   '03B，并按同一项目后端生成独立入口。若后续发现主模型必须修改，应显式回退 Module 02/本模块，先传播 '
                                   'stale，再重新审查、批准并验收主结果。\n',
                                   '新生成主脚本必须只定义一个静态可读 `RUN_CONFIG`（Python 顶层字典或 MATLAB 主函数初始区域的受限 JSON '
                                   '字面量，语法服从执行 Authority），其中锁定 stage/problem/data '
                                   'path+hash/solver/seed/tolerance/limit/expected workbook 等任务可变输入，并在 '
                                   'primary 阶段写入 '
                                   '`primary_quality_protocol_version`。`execution_owner=user`、`execution_profile=full_fidelity` '
                                   '与六个 no-degradation 标志由 `core/user_execution_contract.yaml` '
                                   '全局继承，不在脚本中重复自报；`solver_version` 等实际运行事实仍由返回主工作簿 `运行配置` 记录和验收。旧 '
                                   '`FULL_FIDELITY_CONFIG/FULL_RUN_CONFIG` 仅作只读兼容且继续按旧完整字段要求校验。默认不生成独立 '
                                   'YAML、运行说明或校验报告。主工作簿 accepted 后不得为了结果深化分析覆盖更新主求解入口；深化分析进入 Module '
                                   '03B，并按同一项目后端生成独立入口。若后续发现主模型必须修改，应显式回退 Module 02/本模块，先传播 '
                                   'stale，再重新审查、批准并验收主结果。\n']],
 'modules/03_result_analysis.md': [['按 `core/user_execution_contract.yaml#result_handoff` '
                                    '核对主结果后，判断本问是否需要独立深化分析。在生成任何 独立深化入口 之前，先执行 Analysis Necessity '
                                    'Gate：根据题目/用户显式要求、建模阶段遗留的 material risk、真实主结果边界性以及准备写入论文的 '
                                    'claim，判断当前小问是否确实需要改变参数、场景、seed、初值、算法、模型结构或验证窗口，建立一个新的计算世界来检验结论稳定性。\n',
                                    '本模块只接受已验收的主工作簿，但**不是每个已验收主结果都必须进入本模块**。在生成任何 独立深化入口 之前，先执行 Analysis '
                                    'Necessity Gate：根据题目/用户显式要求、建模阶段遗留的 material risk、真实主结果边界性以及准备写入论文的 '
                                    'claim，判断当前小问是否确实需要改变参数、场景、seed、初值、算法、模型结构或验证窗口，建立一个新的计算世界来检验结论稳定性。\n'],
                                   ['若 Gate 判定 '
                                    '`required`，再根据真实主结果选择参数敏感性、场景压力、多算法/多初值、结构稳健性、阈值、异质性、误差分解或外样本稳定性。若 '
                                    'current `模型论文框架.md` '
                                    '已存在，制定分析计划前先读取本问当前模型、验证方案、主结果摘要、适用/失效边界和跨问依赖，再用已核对主工作簿复核具体数值；不得脱离框架按聊天印象选择分析对象。\n',
                                    '若 Gate 判定 '
                                    '`required`，再根据真实主结果选择参数敏感性、场景压力、多算法/多初值、结构稳健性、阈值、异质性、误差分解或外样本稳定性。若 '
                                    'current `模型论文框架.md` '
                                    '已存在，制定分析计划前先读取本问当前模型、验证方案、主结果摘要、适用/失效边界和跨问依赖，再用已验收主工作簿复核具体数值；不得脱离框架按聊天印象选择分析对象。\n'],
                                   ['v7.14 起，`core/numerical_verification_contract.yaml` '
                                    '只负责主工作簿核对之前的**当前主计算内在数值有效性**。本模块继续独占主工作簿核对后的参数敏感性、压力场景、替代算法/结构、多随机种子或多初值稳健性、阈值与失效边界、异质性、误差分解及广义外样本稳定性；这些内容**不得被主求解质量门提前吸收**，也不得为了让主工作簿“看起来验证充分”而预先塞回 '
                                    '主求解入口。\n',
                                    'v7.14 起，`core/numerical_verification_contract.yaml` 只负责主工作簿 accepted '
                                    '之前的**当前主计算内在数值有效性**。本模块继续独占主工作簿 accepted '
                                    '后的参数敏感性、压力场景、替代算法/结构、多随机种子或多初值稳健性、阈值与失效边界、异质性、误差分解及广义外样本稳定性；这些内容**不得被主求解质量门提前吸收**，也不得为了让主工作簿“看起来验证充分”而预先塞回 '
                                    '主求解入口。\n'],
                                   ['如果某个主算法按其数学定义本身需要多起点、多随机种子或内部重复才能完成一次主求解，这些运行可以留在 03A 的主算法内部；但一旦问题变成“不同 '
                                    'seed / 初值 / 替代算法下结论是否保持”，就属于本模块，核对主工作簿后经过 Analysis Necessity Gate，再在 '
                                    '`required` 时形成 `result_analysis_plan`。\n',
                                    '如果某个主算法按其数学定义本身需要多起点、多随机种子或内部重复才能完成一次主求解，这些运行可以留在 03A 的主算法内部；但一旦问题变成“不同 '
                                    'seed / 初值 / 替代算法下结论是否保持”，就属于本模块，并必须在 accepted 主工作簿之后先经过 Analysis '
                                    'Necessity Gate，再在 `required` 时形成 `result_analysis_plan`。\n'],
                                   ['- `not_needed`：可读取必要原始数据 + 已核对主工作簿；\n',
                                    '- `not_needed`：可读取必要原始数据 + 已验收主工作簿；\n'],
                                   ['- `project_level`：读取 `数据预处理/数据预处理结果.xlsx` + 已核对主工作簿，禁止再次直接读取对应共享原始数据。\n',
                                    '- `project_level`：读取 `数据预处理/数据预处理结果.xlsx` + '
                                    '已验收主工作簿，禁止再次直接读取对应共享原始数据。\n'],
                                   ['核对主工作簿后、生成 03B 代码前，对当前小问给出 `required / not_required` 二选一结论。以下任一 '
                                    'material 条件成立时，原则上应判定 `required`：\n',
                                    '在 accepted 主工作簿之后、生成 03B 代码之前，对当前小问给出 `required / not_required` '
                                    '二选一结论。以下任一 material 条件成立时，原则上应判定 `required`：\n'],
                                   ['- `validation_plan` 中存在主结果得到后才能检验、且会影响核心答案或论文主张的 residual risk；\n',
                                    '- `validation_plan` 中存在 accepted 后才能检验、且会影响核心答案或论文主张的 residual risk；\n'],
                                   ['下游按 `result_handoff` 消费核对后的主结果和实际需要的分析证据。`not_required` '
                                    '保存具体理由；机器验收状态按执行合同的 `analysis_necessity_state_mapping` 记录。\n',
                                    '兼容语义：旧项目 `result_analysis_status=passed` '
                                    '保持原义；`pending/failed/redo_required` 不变；新增 `not_required` 只表示 Gate '
                                    '明确裁定无需 03B。它不生成伪 `result_analysis_workbook`，也不冒充 '
                                    '`accepted_result_analysis_workbook`。下游只在“accepted 主结果 + 有理由的 '
                                    '`not_required`”或“accepted 03B 工作簿 + `passed`”两种情况下获得 '
                                    '`validated_results`。\n'],
                                   ['Gate=`required` 后按 `core/user_execution_contract.yaml#solver_backends` '
                                    '继承项目根唯一求解后端，不在 03B 另选语言。独立入口名称来自输出 Authority；03B 配置/回执及可选项目级辅助输入版本遵循 '
                                    '`core/user_execution_contract.yaml#code_delivery`：无辅助输入为 1.1，合法辅助输入路径为 '
                                    '1.2，并使用独立源码 bundle。按 `result_handoff` '
                                    '读取已返回的主工作簿及其输入依据。主阶段的执行状态不被深化阶段覆盖；`RUN_CONFIG` 与回执中的 backend '
                                    '记录实际运行事实，须与项目策略一致。\n',
                                    'Gate=`required` 后按 `core/user_execution_contract.yaml#solver_backends` '
                                    '继承项目根唯一求解后端，不在 03B 另选语言。独立入口名称来自输出 Authority；03B 配置/回执及可选项目级辅助输入版本遵循 '
                                    '`core/user_execution_contract.yaml#code_delivery`：无辅助输入为 1.1，合法辅助输入路径为 '
                                    '1.2，并使用独立源码 bundle。读取 accepted '
                                    '主工作簿前由共享前提检查核对主代码与数据身份，不能通过调用主入口重新计算主结果。主阶段的执行状态不被深化阶段覆盖；`RUN_CONFIG` '
                                    '与回执中的 backend 记录实际运行事实，须与项目策略一致。\n'],
                                   ['`required` 分支：\n\n```text\n主工作簿核对完成\n',
                                    '`required` 分支：\n\n```text\n主工作簿accepted\n'],
                                   ['→ 读取当前数据事实源 + 已核对问题X求解结果.xlsx + 必要前问标准工作簿\n',
                                    '→ 读取当前数据事实源 + 已验收问题X求解结果.xlsx + 必要前问标准工作簿\n'],
                                   ['→ 按result_handoff核对返回工作簿\n', '→ 助手按执行Authority验收返回工作簿\n'],
                                   ['→ 回填结果摘要，或回退受影响阶段\n', '→ analyzed或redo_required\n'],
                                   ['`not_required` 分支：\n\n```text\n主工作簿核对完成\n',
                                    '`not_required` 分支：\n\n```text\n主工作簿accepted\n'],
                                   ['→ 下游从主工作簿读取支持当前计算世界内claim的证据\n', '→ 下游只使用accepted主工作簿支持当前计算世界内的claim\n'],
                                   ['Module 02 的 Comparator 按具体比较问题关联稳定检验 '
                                    'ID。在框架结果摘要后的现有比较节保存数学／算法范围、共同评价、双审结论和用户批准，服从 '
                                    '`core/model_approval_contract.yaml#analysis_comparison_approval`。比较范围变化只失效该范围及 '
                                    'analysis 链，主模型真正变化才处理主批准与结果。\n',
                                    'Module 02 的 Comparator 按具体比较问题关联稳定检验 ID。数学／算法比较规范置于框架 `#### 结果摘要` 之后的独立 '
                                    '`HSK_ANALYSIS_COMPARISON_BEGIN/END Qn` marker，不能混入主 SIB '
                                    '或主语义哈希区。规范、范围审查和批准服从 `core/model_approval_contract.yaml`；当前主身份仍须 '
                                    'current = validated = approved。比较范围变化只失效该范围及 analysis '
                                    '链，主模型真正变化才按原语义治理使主批准和结果失效。\n'],
                                   ['主工作簿核对后，在该节冻结本次具体检验、对象引用、共同评价、判据和预期证据位置。`required` 项逐项执行并记录真实证据及 '
                                    'disposition；`exploratory` '
                                    '项记录实际完成情况。明确题目／用户要求和未关闭核心风险继续列为必需项，技术失败时记录缺项及后续动作。\n',
                                    '主工作簿 accepted 后，在现有 `analysis_comparison.checks` '
                                    '中冻结本次具体检验、对象引用、共同评价、判据和预期证据选择器。`required` 项必须逐项执行并形成真实非空证据及 '
                                    'disposition；敏感性或另一张实质表不能替代它。`exploratory` 未完成不阻塞当前必要答案，但不得写成已验证。仍有 '
                                    'current required 项时不得整体 `not_required`；明确题目／用户要求和未关闭核心风险不能因计算失败撤销。\n'],
                                   ['显式运行比较验收工具时，按 `core/user_execution_contract.yaml#analysis_comparison` '
                                    '填写 `analysis_comparison.checks`、独立 `HSK_ANALYSIS_COMPARISON_BEGIN/END '
                                    'Qn` marker 和配置／回执绑定；计划摘要排除实际结果和运行后处置。普通比较沿用上面的框架记录与真实工作簿交接。\n',
                                    '配置与回执扩展仅按 `core/user_execution_contract.yaml` '
                                    '激活；计划摘要排除实际结果和运行后处置，主簿和源码身份继续使用现有绑定。机器能核对规范一致性、有限指标算术、覆盖和来源，不能从名称自动证明数学等价、算法独立性或模型正确性。\n'],
                                   ['这条规则的目的，是让 Figure Evidence '
                                    '阶段可以直接从核对后的工作簿构造稳定区、阈值边界、ECDF、箱线/小提琴+散点、Small '
                                    'Multiples、Pareto/性能剖面等科研图，而不在 绘图阶段重新运行分析。\n',
                                    '这条规则的目的，是让 Figure Evidence 阶段可以直接从 accepted '
                                    '工作簿构造稳定区、阈值边界、ECDF、箱线/小提琴+散点、Small Multiples、Pareto/性能剖面等科研图，而不在 '
                                    '绘图阶段重新运行分析。\n']],
 'modules/04_figure_evidence.md': [['- 图表代码始终只消费当前 Figure Contract 允许的真实数据源：已核对求解工作簿、按需 03B 工作簿，以及 '
                                    '`not_needed/question_local` 的合法原始附件等；`project_level` '
                                    '的覆盖原始数据改用统一预处理工作簿。禁止在渲染代码中重新执行预处理、拟合或数值求解。\n',
                                    '- 图表代码始终只消费当前 Figure Contract 允许的真实数据源：已验收求解工作簿、按需 03B 工作簿，以及 '
                                    '`not_needed/question_local` 的合法原始附件等；`project_level` '
                                    '的覆盖原始数据改用统一预处理工作簿。禁止在渲染代码中重新执行预处理、拟合或数值求解。\n'],
                                   ['进入本模块时先读取 current `模型论文框架.md` '
                                    '中的当前有效口径、相关小问结果摘要、待办缺口和既有图表映射，用于确定“哪些结论需要图证据”；随后按 '
                                    '`core/user_execution_contract.yaml#result_handoff` '
                                    '从真实工作簿读取具体数值和底层序列。不得仅凭聊天记忆或框架摘要数字反推图数据。\n',
                                    '进入本模块时先读取 current `模型论文框架.md` '
                                    '中的当前有效口径、相关小问结果摘要、待办缺口和既有图表映射，用于确定“哪些结论需要图证据”；随后再从真实工作簿读取具体数值和底层序列。不得仅凭聊天记忆或框架摘要数字反推图数据。\n'],
                                   ['1. 继承已经锁定的 `preprocessing_decision`；若为 `project_level`，核对 '
                                    '`数据预处理结果.xlsx` 的实际数据与预处理质量证据；\n',
                                    '1. 继承已经锁定的 `preprocessing_decision`；若为 `project_level`，确认 '
                                    '`数据预处理结果.xlsx` 已 accepted 且预处理质量门通过；\n'],
                                   ['3. 主工作簿核对后执行 Analysis Necessity Gate：Gate=`required` '
                                    '时，已选深化实现基于题目风险完成实际需要的结果深化分析并验收 `问题X结果深化分析.xlsx`；Gate=`not_required` '
                                    '时必须记录非空理由，不生成或要求 03B 代码/工作簿，也不得据此声称稳健性、稳定性或替代方法一致性已经验证；\n',
                                    '3. 主工作簿 accepted 后执行 Analysis Necessity Gate：Gate=`required` '
                                    '时，已选深化实现基于题目风险完成实际需要的结果深化分析并验收 `问题X结果深化分析.xlsx`；Gate=`not_required` '
                                    '时必须记录非空理由，不生成或要求 03B 代码/工作簿，也不得据此声称稳健性、稳定性或替代方法一致性已经验证；\n'],
                                   ['5. 若为 `project_level`，此时按项目根已选绘图后端生成并人工检查 `数据预处理/data_process.py` 或 '
                                    '`数据预处理/data_process.m`，只把已核对预处理工作簿中的底层证据转成图；\n',
                                    '5. 若为 `project_level`，此时按项目根已选绘图后端生成并人工检查 `数据预处理/data_process.py` 或 '
                                    '`数据预处理/data_process.m`，只把已验收预处理工作簿中的底层证据转成图；\n'],
                                   ['先确认实际交付几张图，并与各自的 Figure Contract 和 Spec '
                                    '对应。用户分别要机理草图与误差分布图时，机理草图可先依据题面列出对象、关系和待定假设，误差图先列需核对的工作簿、字段和单位。已取得当前批准模型后，机理图可按本节选择正式后端。只有数值图取得其当前已核对证据后，才可绘制点值、分布或误差带。分别检查、登记每张图的证据与状态，申请整组交付时核对每一张。\n',
                                    '先确认实际交付几张图，并与各自的 Figure Contract 和 Spec '
                                    '对应。用户分别要机理草图与误差分布图时，机理草图可先依据题面列出对象、关系和待定假设，误差图先列需核对的工作簿、字段和单位。已取得当前批准模型后，机理图可按本节选择正式后端。只有数值图取得其当前已验收证据后，才可绘制点值、分布或误差带。分别检查、登记每张图的证据与状态，申请整组交付时核对每一张。\n'],
                                   ['| 工作簿驱动的主结果、分布、误差、敏感性、空间场、Pareto 或网络权重 | 项目级唯一选择的 Python / MATLAB | '
                                    '数值、坐标、统计量和区间必须来自已核对事实源 |\n',
                                    '| 工作簿驱动的主结果、分布、误差、敏感性、空间场、Pareto 或网络权重 | 项目级唯一选择的 Python / MATLAB | '
                                    '数值、坐标、统计量和区间必须来自已验收事实源 |\n'],
                                   ['`多模型检验` 与 `同模型多算法检验` 同样服从下述准入；按检验 ID、记录键、模型／算法和共同评价口径读取 current 底层证据。缺失 '
                                    'required '
                                    '比较不得由敏感性图补位；不同自然目标未经共同映射不能画成可比数值。比较差异或负结果也可形成有解释价值的图，不以“一致”作为图准入条件。\n',
                                    '`多模型检验` 与 `同模型多算法检验` 同样服从下述准入；按检验 ID、记录键、模型／算法和共同评价口径读取 current '
                                    'accepted 底层证据。缺失 required '
                                    '比较不得由敏感性图补位；不同自然目标未经共同映射不能画成可比数值。比较差异或负结果也可形成有解释价值的图，不以“一致”作为图准入条件。\n'],
                                   ['以同一 Figure ID '
                                    '闭合当前真实来源、工作表与精确字段、绘图脚本、实际入文图片、caption、邻近正文编号引用和框架登记；有真实记录键、配对或排序语义时一并保留其依据，单位与统计口径不得在调图中改变。计划中的文件名不等于已生成或已批准的图片。来源、脚本或图片变化后按既有同步与 '
                                    'stale 规则刷新受影响登记和引用，不凭静态检查自动恢复入文批准；正文交接与位置调整按 Writing Protocol §13.0 '
                                    '执行。\n',
                                    '以同一 Figure ID 闭合当前 accepted '
                                    '来源、工作表与精确字段、绘图脚本、实际入文图片、caption、邻近正文编号引用和框架登记；有真实记录键、配对或排序语义时一并保留其依据，单位与统计口径不得在调图中改变。计划中的文件名不等于已生成或已批准的图片。来源、脚本或图片变化后按既有同步与 '
                                    'stale 规则刷新受影响登记和引用，不凭静态检查自动恢复入文批准；正文交接与位置调整按 Writing Protocol §13.0 '
                                    '执行。\n']],
 'modules/05_writing/paper_writing_protocol.md': [['正式正文只使用当前有效来源：题目与附件、current `模型论文框架.md`、按 '
                                                   '`core/user_execution_contract.yaml#result_handoff` '
                                                   '核对的数值事实源、已确认图表与必要文献。不得从聊天记忆恢复已经被项目框架删除或替换的旧模型、旧参数、旧结果和旧图。\n',
                                                   '正式正文只使用当前有效来源：题目与附件、current '
                                                   '`模型论文框架.md`、当前数值事实源、已确认图表与必要文献。不得从聊天记忆恢复已经被项目框架删除或替换的旧模型、旧参数、旧结果和旧图。\n'],
                                                  ['- **证据解释**只消费 current 的已核对主求解证据、真实 03B 分析工作簿或经现有规则判定无需独立 '
                                                   '03B 的直接证据。可选敏感性、边界、收敛精度、误差、模型/算法对照、消融或实际应用情景，不要求每问都做。\n',
                                                   '- **证据解释**只消费 current 的已验收主求解证据、真实 03B 分析工作簿或经现有规则判定无需独立 '
                                                   '03B 的直接证据。可选敏感性、边界、收敛精度、误差、模型/算法对照、消融或实际应用情景，不要求每问都做。\n'],
                                                  ['1. **该问开始先盘点。** 结合当前模板、active '
                                                   '骨架和标题规划，读取本问全部相关登记，包括仅在全局证据链出现、跨问共享、位置空缺或待定的对象，复用同一 '
                                                   'Figure '
                                                   'ID／已有表标识及来源。一并查看用户本轮提供的章节交接材料；其中的预留标识可帮助定位对象，结果仍须回到实际来源核实。不能先按“结果节图”筛选而漏掉未定项。全论文或跨聊天恢复仍按现行要求读取完整框架；随后再按本问与功能节定向读取。\n'
                                                   '2. **安排后分节消费。** 按真实支撑判断和 current '
                                                   '证据确定主要展示位置及解释任务，再按标识检索必要登记行、表头、合同和证据。当前 resolver '
                                                   '不自动筛选图表行；这是现有项目文本的读取动作。未运行、未导出、未确认或缺实际证据的对象只能保留待办或舍弃，不能因排好位置自动变成可入文。机理图沿用自身来源与审阅要求，不补造工作簿。\n',
                                                   '1. **该问开始先盘点。** 结合当前模板、active '
                                                   '骨架和标题规划，读取本问全部相关登记，包括仅在全局证据链出现、跨问共享、位置空缺或待定的对象，复用同一 '
                                                   'Figure '
                                                   'ID／已有表标识及来源。一并查看用户本轮提供的章节交接材料；其中的预留标识可帮助定位对象，结果仍须回到已验收的来源核实。不能先按“结果节图”筛选而漏掉未定项。全论文或跨聊天恢复仍按现行要求读取完整框架；随后再按本问与功能节定向读取。\n'
                                                   '2. **安排后分节消费。** 按真实支撑判断和 current '
                                                   '证据确定主要展示位置及解释任务，再按标识检索必要登记行、表头、合同和证据。当前 resolver '
                                                   '不自动筛选图表行；这是现有项目文本的读取动作。未运行、未导出、未确认或缺相应 accepted '
                                                   '证据的对象只能保留待办或舍弃，不能因排好位置自动变成可入文。机理图沿用自身来源与审阅要求，不补造工作簿。\n'],
                                                  ['本步骤只使用已有 Figure ID、工作簿与图表映射，不另设必填工作单。图表位置或 caption '
                                                   '调整**不等于**已批准模型或 accepted 数值改变、也不要求重新运行 03A/03B；但受影响的 '
                                                   'Framework、论文 Figure 引用、LaTeX 正式审计与编译证明仍需按当前依赖关系刷新。图表数据必须 '
                                                   'current 且已经核对，不因新标题需求而制造 03B 或其他不存在的实验。\n',
                                                   '本步骤只使用已有 Figure ID、工作簿与图表映射，不另设必填工作单。图表位置或 caption '
                                                   '调整**不等于**已批准模型或 accepted 数值改变、也不要求重新运行 03A/03B；但受影响的 '
                                                   'Framework、论文 Figure 引用、LaTeX 正式审计与编译证明仍需按当前依赖关系刷新。图表数据必须 '
                                                   'current 且真实已验收，不因新标题需求而制造 03B 或其他不存在的实验。\n']],
 'modules/05_writing/latex.md': [['- 当前 `模型论文框架.md`、按 `core/user_execution_contract.yaml#result_handoff` '
                                  '核对的工作簿和图表映射：项目事实与证据。\n',
                                  '- 当前 `模型论文框架.md`、已验收工作簿和图表映射：项目事实与证据。\n']],
 'core/code_quality_contract.yaml': [['- 交付前检查代码工程质量及其与批准模型的一致性；显式工具流程先执行semantic_governance，再检查代码质量。\n',
                                      '- 代码工程质量门必须位于semantic_governance '
                                      'gate之后；代码不能静默引入数学层没有定义的核心变量、目标项、约束、阈值或预处理语义。\n'],
                                     ['- 结果深化分析脚本只保留当前数据事实源和已核对主结果读取、题目专属深化分析、稳定性判定、深化工作簿输出和主入口；不得复制主求解主链。\n',
                                      '- '
                                      '结果深化分析脚本只保留当前数据事实源和已验收主结果读取、题目专属深化分析、稳定性判定、深化工作簿输出和主入口；不得复制主求解主链。\n']],
 'modules/06_review_delivery.md': [['以下任一成立不得最终交付：题意/输出硬要求缺失；current claim 使用 '
                                    'stale/未核对事实；必要模型/公式/约束、非显然核心推导或证明逻辑断裂；关键数值/单位/精度错误；局部/启发式结果被宣称为严格全局结论；外部核心 '
                                    'claim 无必要来源；正式引用、编译或提交内容存在错误；verified official rule '
                                    '明确违规；或尚未完成本次交付所需的实际审阅。\n',
                                    '以下任一成立不得最终交付：题意/输出硬要求缺失；current claim 使用 '
                                    'stale/未验收事实；必要模型/公式/约束、非显然核心推导或证明逻辑断裂；关键数值/单位/精度错误；局部/启发式结果被宣称为严格全局结论；外部核心 '
                                    'claim 无必要来源；正式引用/编译/包级 gate 失败；verified official rule 明确违规；或 required '
                                    'delivery gate 尚未成功执行。\n']],
 'modules/06_review/content_review.md': [['核验题目要求、附件、输出格式、单位和精度；从 current `模型论文框架.md` 恢复模型，按 '
                                          '`core/user_execution_contract.yaml#result_handoff` '
                                          '读取实际工作簿。模型/结果/图/命题/正文 fragment 的 stale 只沿真实依赖传播，不能“整篇保险起见”全部判旧。\n',
                                          '核验题目要求、附件、输出格式、单位和精度；检查 current '
                                          '`模型论文框架.md`、`state/project_state.yaml` 与 accepted '
                                          '标准工作簿的职责边界。模型/结果/图/命题/正文 fragment 的 stale '
                                          '只沿真实依赖传播，不能“整篇保险起见”全部判旧。\n'],
                                         ['框架应能恢复当前模型身份、Model/Solver/Validator、Formula/Algorithm Trace、Model '
                                          'Construction Rationale、Reduction Provenance、solver '
                                          'precondition、关键参数依据、Terminology/Numeric/Title/Claim '
                                          '状态、结果和图表证据位置；具体数值回到实际工作簿。每问文件与目录只核对 '
                                          '`core/output_contract.yaml#per_question`。\n',
                                          '框架应能恢复当前模型身份、Model/Solver/Validator、Formula/Algorithm Trace、Model '
                                          'Construction Rationale、Reduction Provenance、solver '
                                          'precondition、关键参数依据、Terminology/Numeric/Title/Claim '
                                          '状态、结果和图表证据位置；具体数值回到 accepted workbook。每问文件与目录只核对 '
                                          '`core/output_contract.yaml#per_question`。\n']],
 'modules/06_review/final_delivery.md': [['交付前核对当前 LaTeX 源码、真实编译日志与 PDF，处理未解析引用、编译错误及源码与成品不一致。每问文件、目录和提交内容按 '
                                          '`core/output_contract.yaml#per_question`、Artifact Packs '
                                          '与已核验赛事规则逐项检查。PDF 逐页检查由助手按 Module 05D 执行。\n',
                                          '交付须用最新 LaTeX audit、compile report、PDF、project sync、submission '
                                          'package validation。每问条件 3+2 文件及目录/包边界依 '
                                          '`core/output_contract.yaml#per_question` 与 Artifact '
                                          'Packs，不复列；stale source bundle、未解析引用、编译错误、manifest/hash 不一致依既有 '
                                          'gate。PDF 逐页检查由助手按 Module 05D 执行。\n'],
                                         ['final review 读取 current framework、active assembly、题目要求、verified '
                                          'competition rules、真实图表与编译证据；数值按 '
                                          '`core/user_execution_contract.yaml#result_handoff` '
                                          '从工作簿核对，已有工具报告一并读取。\n',
                                          'final review 读取 current framework、state、active '
                                          'assembly、题目要求、verified competition rules、accepted numeric/figure '
                                          'evidence、audit/compile/package reports。旧聊天记忆不作为事实源。\n']],
 'packs/artifact/review.md': [['审查时读取当前框架、题面、论文及对应实物证据，按本次请求范围逐项复核。结果来源按 '
                               '`core/user_execution_contract.yaml#result_handoff` 核对；仅审阅请求不写入项目。\n',
                               '审查前按 resolver 当前返回的 `pre_delivery_gates` 顺序执行适用检查。仅审阅或只读请求不写入项目；正式提交交付时再消费对应 '
                               'scope 的同步与提交门，不能直接套用固定 `submission --write` 命令。\n'
                               '\n'
                               '```bash\n'
                               'python scripts/validate_model_paper_framework.py 模型论文框架.md --state '
                               'state/project_state.yaml\n'
                               'python scripts/validate_project_state.py state/project_state.yaml '
                               '--project-root .\n'
                               '```\n'],
                              ['执行 `final_review_and_delivery` 时读取当前 competition profile、competition '
                               'Pack、edition rule verification、最终 PDF、真实编译日志及已有的 '
                               '`latex_audit_report.yaml`、`compile_report.yaml`，并按 '
                               '`modules/06_review/final_delivery.md#九final-submission-compliance--evidence-sweep` '
                               '完成八类动态 coverage，同时消费共用内容审查。新生成的正式终审报告使用 '
                               '`templates/review/final_review_matrix.yaml`；旧 `scores + hard_fail + '
                               'evidence` 报告仍可作为兼容输入。\n',
                               '执行 `final_review_and_delivery` 时读取当前 competition profile、competition '
                               'Pack、edition rule verification、最终 PDF、`latex_audit_report.yaml` 与 '
                               '`compile_report.yaml`，并按 '
                               '`modules/06_review/final_delivery.md#九final-submission-compliance--evidence-sweep` '
                               '完成八类动态 coverage，同时消费共用内容审查。新生成的正式终审报告使用 '
                               '`templates/review/final_review_matrix.yaml`；旧 `scores + hard_fail + '
                               'evidence` 报告仍可作为兼容输入。\n'],
                              ['Gate=`not_required` 必须有非空 `result_analysis_requirement_reason`，此时缺少 03B '
                               '文件不构成 layout finding，也不得写成“稳健性/稳定性已通过”。Gate=`required` 时核对当前 03B '
                               '代码、实际工作簿及其支持的结论。主工作簿核对后冻结主求解脚本，已激活的深化分析使用同一项目后端对应的独立入口；旧单脚本四文件目录、旧 '
                               '`结果数据表/问题X/` 和旧敏感性与鲁棒性工作簿只能作为历史项目只读兼容输入。\n',
                               'Gate=`not_required` 必须有非空 `result_analysis_requirement_reason`，此时缺少 03B '
                               '文件不构成 layout finding，也不得写成“稳健性/稳定性已通过”。Gate=`required` 时则必须核对当前 03B '
                               '代码、工作簿与状态/哈希链，缺失不得静默豁免。主工作簿 accepted '
                               '后冻结主求解脚本，已激活的深化分析使用同一项目后端对应的独立入口；旧单脚本四文件目录、旧 `结果数据表/问题X/` '
                               '和旧敏感性与鲁棒性工作簿只能作为历史项目只读兼容输入。\n'],
                              ['若 `preprocessing_decision=project_level`，同时检查 `数据预处理/数据预处理.py`、已核对的 '
                               '`数据预处理结果.xlsx` 和 Figure Evidence 阶段按 `plotting.backend` 选定的 '
                               '`data_process.py` 或 `data_process.m`；若为 '
                               '`not_needed/question_local`，不得因不存在全局预处理目录而扣分。\n',
                               '若 `preprocessing_decision=project_level`，同时检查 `数据预处理/数据预处理.py`、已验收 '
                               '`数据预处理结果.xlsx` 和 Figure Evidence 阶段按 `plotting.backend` 选定的 '
                               '`data_process.py` 或 `data_process.m`；若为 '
                               '`not_needed/question_local`，不得因不存在全局预处理目录而扣分。\n']],
 'packs/artifact/code.md': [['- `per_question.solver_scripts` 中项目根后端对应的主入口：按 '
                             '`core/model_approval_contract.yaml#human_approval` 恢复批准模型，并读取本问所需数据后交付；\n'
                             '- 同一项目后端对应的独立深化入口：按 `core/user_execution_contract.yaml#result_handoff` 核对主结果，且 '
                             'Analysis Necessity Gate=`required` 时交付。\n',
                             '- `per_question.solver_scripts` 中项目根后端对应的主入口：主求解程序，按 applicable approval/data '
                             'gates 交付；\n'
                             '- 同一项目后端对应的独立深化入口：仅在主工作簿 accepted 且 Analysis Necessity Gate=`required` '
                             '时交付的独立深化分析程序。\n'],
                            ['基础布局是主求解代码、`问题X求解结果.xlsx` 与已选绘图后端的 `qX_plot.py` 或 `qX_plot.m`；Gate=`required` '
                             '时再追加结果深化分析代码与 `问题X结果深化分析.xlsx`。因此只有 Gate=`required` '
                             '路径才具有两个阶段明确的代码入口；Gate=`not_required` 时仅保留主求解代码。Gate=`required` '
                             '的兼容五文件路径中会形成同目录两个真实工作簿（主工作簿 + 03B 工作簿）；该表述仅描述被 Gate 激活的路径，不适用于 '
                             'Gate=`not_required`。主工作簿核对后冻结主求解脚本，不用深化分析代码覆盖它。Gate=`not_required` 时记录非空理由，不生成 '
                             '03B 代码/工作簿，也不得把缺少 03B 解释为稳健性或稳定性已验证。\n',
                             '基础布局是主求解代码、`问题X求解结果.xlsx` 与已选绘图后端的 `qX_plot.py` 或 `qX_plot.m`；Gate=`required` '
                             '时再追加结果深化分析代码与 `问题X结果深化分析.xlsx`。因此只有 Gate=`required` '
                             '路径才具有两个阶段明确的代码入口；Gate=`not_required` 时仅保留主求解代码。Gate=`required` '
                             '的兼容五文件路径中会形成同目录两个真实工作簿（主工作簿 + 03B 工作簿）；该表述仅描述被 Gate 激活的路径，不适用于 '
                             'Gate=`not_required`。主工作簿 accepted 后冻结主求解脚本，不用深化分析代码覆盖它。Gate=`not_required` '
                             '时记录非空理由，不生成 03B 代码/工作簿，也不得把缺少 03B 解释为稳健性或稳定性已验证。\n'],
                            ['代码与结果分别检查：\n', '实际交付的计算代码都必须通过两类互补质量门：\n'],
                            ['- **工程质量**：按 `core/code_quality_contract.yaml` 检查代码规模、复杂度及对应语言的工程问题；\n'
                             '- **数值结果**：用户运行后按 `result_handoff` 读取实际工作簿，核对运行配置、可行性、残差、收敛、外样本或题型专项证据。\n',
                             '- **工程质量门**：`core/code_quality_contract.yaml` + '
                             '`scripts/validate_code_delivery.py`，按语言分派共同规模/复杂度和对应工程检查；MATLAB '
                             '原生分析未完成时不能宣称完整工程验收；\n'
                             '- **数值结果质量门**：用户运行后由工作簿 Schema 与 `validate_user_execution.py` '
                             '检查运行配置、对应阶段代码哈希、可行性、残差、收敛、外样本或题型专项证据。\n'],
                            ['代码精简不得删除随机种子、目标函数、约束、质量检查、结果输出或复现信息。Gate=`required` '
                             '时，深化分析脚本应读取已核对主工作簿和当前允许的数据事实源，不复制完整主求解流程。主求解/深化入口不生成论文结果图；项目选定的 Python/MATLAB '
                             '主结果图默认只需同目录主工作簿，只有 Figure Evidence 明确消费真实 03B '
                             '证据时才读取条件存在的深化工作簿；必须精确匹配表头，不得重新求解。旧 v6.6.x 单脚本四文件项目与旧 `结果数据表/问题X/` '
                             '仅作**只读兼容**。\n',
                             '代码精简不得删除随机种子、目标函数、约束、质量检查、结果输出或复现信息。Gate=`required` '
                             '时，深化分析脚本应读取已验收主工作簿和当前允许的数据事实源，不复制完整主求解流程。主求解/深化入口不生成论文结果图；项目选定的 Python/MATLAB '
                             '主结果图默认只需同目录主工作簿，只有 Figure Evidence 明确消费真实 03B '
                             '证据时才读取条件存在的深化工作簿；必须精确匹配表头，不得重新求解。旧 v6.6.x 单脚本四文件项目与旧 `结果数据表/问题X/` '
                             '仅作**只读兼容**。\n']]}

def prior_r1_text(relative, text):
    """Reverse approved blocks; leave every unrelated character observable."""
    for current, previous in R1_APPROVED_REWRITES.get(relative, ()):
        if text.count(current) != 1:
            raise ValueError(f"R1 source block is missing or duplicated: {relative}")
        text = text.replace(current, previous, 1)
    return text


def prior_r1_bytes(relative, raw):
    """Require exact current and predecessor identities for source fingerprints."""
    identity = R1_SOURCE_IDENTITIES.get(relative)
    if identity is None:
        return raw
    prior_sha, current_sha = identity
    if hashlib.sha256(raw).hexdigest() != current_sha:
        raise ValueError(f"R1 source bytes changed: {relative}")
    previous = prior_r1_text(relative, raw.decode("utf-8")).encode("utf-8")
    if hashlib.sha256(previous).hexdigest() != prior_sha:
        raise ValueError(f"R1 predecessor bytes differ: {relative}")
    return previous
