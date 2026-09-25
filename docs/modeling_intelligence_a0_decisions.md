# 建模智能增强 A0：基线重对齐、协议落点与 A1 实施裁决

日期：2026-09-25。原计划为 `docs/modeling_intelligence_evidence_evolution_plan.md`，原文的“只编制计划”是编制时授权快照。用户已在本轮明确要求发布已完成修复并继续实施原计划；本文件记录新的分阶段授权与设计，不追认任何用户项目的模型批准。

## 1. 范围与先决事实

- 稳定发布：v10.1.0，固定 `8fc5b42a953204b64a8ff7ddc00d5fb8983072a4`；修复内容和测试见 PR #236。
- 原计划 PR #235 先与上述主干串行对齐，原始计划内容保留。一次性发布工作流已完成其目的，不能留入正式主干。
- 本轮功能范围：A0 + A1，只读 Code ↔ Model 一致性**结构**核验。A2、B1/B2、C1/C2、D1/D2、E1/E2 未完成，不能用本文件或 A1 的结构结论冒充全部增强完成。
- 拟目标 Skill 10.2.0（可选能力，minor）；Project State Schema 8.1.0（新增可选声明），conformance 记录协议1.0.0。SIB、运行回执1.0/1.1/1.2、数值验收、项目统一后端不变。发布 v10.1.0 不会自动发布本候选版本。
- 不改真实项目，不执行真实赛题，不添加模型审批、数值accepted或独立审查事实；不导入用户或第三方案例。

## 2. 读取、写入与事实源追踪

| 环节 | 现有实现与职责 | A1 决策 |
|---|---|---|
| SIB提取/身份 | semantic_identity.py 的 question_sections、inspect_question_semantics、semantic_identity_hash | 复用，不重写数学批准根；模型对象从真实SIB枚举 |
| 当前模型锁 | runtime_assurance.py 的 _semantic_lock_evidence；validate_model_approval.py | 复用同一核验逻辑，不根据记录里自填hash授予批准 |
| 一致状态快照 | ProjectStateSnapshot.capture/assert_current | 同一原始state快照，不恢复事务日志 |
| 后端与源码 | stage_code.py 的 current_project_backend、resolve_stage_code、stage_code_fingerprint、dependency_reference_issues | 所有源码来自已选阶段和真实声明依赖；不按扩展名猜项目策略 |
| 配置与回执 | run_config_parser.py、execution_protocol.py、stage_inputs.py | A1只消费源码身份和阶段，不能替代输入/回执/数值验收；1.2既有支持不改 |
| 代码符号 | Python AST；matlab_code_checks.py 的tokenize/statements/function_signature | 有限静态区域，不能解析的区域显式needs_review |
| 写入与失效 | project_transaction.py的read-set/事务；state_transitions.py和当前合同 | A1没有writer，不存PASS，不修改stale或审批；A2才讨论现有协调器消费 |
| 写作与审查 | Formula/Algorithm Trace、Claim Strength、现有两轮审查 | A1仅增加关联证据，不能给任意公式/程序等价证明 |

本轮已通过Actions公开源码快照、ZIP摘要和完整Git tree核对建立本地工作副本；不是声称git clone网络恢复。v10.1.0基线实际lint/index均exit0，完整单测1730项、3条件跳过、无失败。后续每一轮测试另记，不覆盖历史记录。

## 3. DEC01—DEC10 裁决

### DEC01：存储及唯一写入者

A记录采用原计划的 `subproblems.Qn.implementation_conformance.primary|analysis`，不增加独立项目报告文件；字段形状唯一位于Project State Schema的对应`$defs`。记录是作者声明的覆盖映射，不含`passed/approved/accepted`或reviewer字段。A1仅读取并返回派生报告，缺少记录返回not_assessed；可请求只读inventory帮助准备映射，但不自动填回状态。未来A2的正式绑定写入必须由现有代码交付/回执协调器经commit_project_state完成，任何新writer都需对应阶段测试。

B落点维持 `paper_framework.claim_evidence`；C采用顶层可选 `review_receipts`；D采用 `decisions.Qn.case_references`，语料在`knowledge/case_memory/`。这些名称仅为后续阶段预留，本轮不向Schema添加B/C/D空字段。B/C由原有项目同步/审查协调链写入，D入库为显式仓库变更；不建平行数据库或自动学习日志。

### DEC02：激活与默认行为

A1仅显式CLI/专门只读路由运行；不加入普通代码交付、回执、写作和最终提交的必经链。新字段不存在时不改变原工作流资格；存在但残缺/未知协议时只读检查必须fail closed，不能当不存在。A1结构核验成功绝不写入已有gate的PASS。A2正式接入另做激活协议及旧项目影响审查；B/C/D各自激活，不能一个开关全开。

### DEC03：确定性范围

覆盖对象：SIB的data_scope/variables/parameters/assumptions/constraints稳定ID，objective、algorithm_semantics、preprocessing_decision，以及实际extensions顶层条目。不能只枚举记录自己列出的“必需项”。

源码锚点：项目相对路径、准确符号及源码片段SHA；文件/完整source bundle另行绑定。Python解析函数和明确模块区；MATLAB复用现有lexer，只接受可确定的平坦函数边界；嵌套函数/类/动态执行/无法唯一定位返回needs_review，不尝试执行。

可选表达式检查只比较**已批准SIB对象**中的`implementation_expression.python|matlab`与单一静态返回/赋值表达式。没有这一显式参考时不推断LaTeX等价。Python比较受限AST结构，MATLAB比较受限词法token；不执行表达式，不把语法相同当普遍数学正确。代数等价但语法不同不自动“修正”模型，应记录合法变换并语义复核。罚函数名称不是错误条件。

反向发现首版只报告有限裁剪/截断候选，如numpy.clip和MATLAB min/max；函数调用、局部重名或字符串不会证明数学作用。未登记候选要求review；登记说明也不证明审查真实发生。约束是否传入外部求解器、第三方内部逻辑和任意数值等价仍在未核验边界。

### DEC04：B的最小证据边界

后续B1仅允许确定性工作簿语义选择器（sheet+唯一行键+列+单位/范围）、差值/比值/相对变化/显式单位换算和有界汇总。禁止任意表达式执行、公式缓存缺失当数值或调用求解器。当前A1不实现B，不需要读取或创建工作簿。B必须先调用v10.1输入/回执/accepted资格，不能重建另一资格表。

### DEC05：C的真实性与自引用

后续C保留native_isolated/human_review/separated_passes/author_self_check/unverified实际模式；沿用没有子代理时的两轮分离审查，不手填“独立=true”。记录绑定被审输入集合及规范，不绑定包含回执自身的完整state哈希。A1报告一律注明数学语义未证明、没有原生运行/独立审查发生。

### DEC06：失效衔接

A1记录不缓存通过；每次对照当前模型、源文件及bundle，旧记录重放被识别为不适用。源代码变化不直接撤销数学批准；SIB变化交由原语义治理。B/C精细影响只能增加定位能力，不能抵消现有artifact stale。A2之前不新增事件、不清除stale。

### DEC07：案例来源

后续D1首批仅独立编写的明确合成案例或用户另行明确授权内容。当前不入库真实论文、对话、姓名、路径、数据或第三方字典。许可不明隔离；检索建议不作模型批准或当前题数值来源。

### DEC08：资源与回归预算

A1不加载案例库、网络、外部进程或工作簿，不导入用户源码。拟冻结边界：state和framework各2MiB、单源码2MiB、源码总和16MiB、64个源码文件、512个模型对象/映射、256个反向候选、嵌套记录深度32。超限返回明确限制，不能截断后structure_verified。实现之后报告实测时间/规模，不追认性能提升。

扩展关闭时普通路由的modules/gates/outputs/资格语义必须与基线相同；增加的新Authority入口及版本是显式差异，不把所有assurance变化从比较中删除。旧测量基线保持，只登记精确可说明的版本/元数据变化，所有未知字段和资格漂移仍失败。

### DEC09：版本与兼容

A1是默认不启用的能力，Skill10.2.0；新增可选状态声明使Schema8.1.0，旧无字段payload继续合法，旧reader面对新字段明确不支持，不删除字段降级。新记录协议固定1.0.0。文档里的历史10.0.1/10.1.0、现有SIB/receipt版本均保留，不能全仓替换。A1不发布新的Release；稳定v10.1.0标签不变。

### DEC10：快照与回退

复用ProjectStateSnapshot与现有read-set检查。路径越界、符号链接/重复、读取过程中源码/state/framework/规范发生变化，应返回blocked，不写任何状态。该边界是读取前后的一致性观察，不声称文件系统原子快照或阻止返回后的变化。pending journal必须按原入口显式恢复；新只读工具不恢复日志。

A1回退删除只读入口/路由即可；用户已声明的新记录应保留原数据并由支持协议的版本读取，不能自动删除。A2及后续writer引入前必须另测prepared日志、read-set冲突和roll-forward，不笼统承诺失败均自动回滚。

## 4. A1修改白名单与验收

主要改动：新增conformance Authority与只读内核/专项测试；Schema仅新增可选记录；bootstrap/manifest/专门路由登记；formula_code_closure和scripts README只作使用指导；版本载体、当前版本测试和精确测量差异登记；原计划增加当前进度。禁止修改数值公式、solver模板、回执/PQS、状态转移和事务实现、写作规则及用户项目。

验收至少覆盖：缺少/悬空映射、稳定SIB覆盖、错误阶段/后端、helper变化、旧记录重放、未知协议/字段、bool revision、动态或未支持结构、表达式受控边界替换、合法单位变换与罚函数不误判、未登记clip候选、注释改变只影响源身份、快照中途漂移、路径逃逸、超限、CLI非零状态和无写入。所有测试区分structure_verified、needs_review、not_assessed与数学未证明。

先专项正负例，再完整单测/lint/index和远程完整CI。最终head变动后重新确认，不以旧绿色替代。未通过时保持候选分支，禁止宣称A2—E2完成。

## 5. 当前执行台账

A0架构与范围裁决已记录；A1尚待实现和验证。实际PR、最终head、测试计数、差异与是否合并在实现后回填。原计划52场景中A1只关闭静态/快照子范围；运行验收及跨模块场景继续留给A2及后续阶段。
