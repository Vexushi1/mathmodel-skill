# B1 实施指南：受限主张证据解析与安全派生核验

> 阶段指南，不是当前运行时 Authority。只有已通过回归并合并的实现才能作为可用能力。本文件不把 B1 或整个 B 阶段标为完成。

> **2026-09-26 接续状态：** B1只读功能已有候选提交，正在[草稿PR #239](https://github.com/Vexushi1/mathmodel-skill/pull/239)验收，尚未合并或发布；B2/C/D/E未开始。第12节记录的是本指南首次提交时的历史停点，不能作为当前待办或验收结论。

日期：2026-09-25。依据原计划第7、10—17节及A0 DEC01/02/04/06/08/09/10；A2已正常合并，合并文件树与完整验收通过的最终PR文件树相同；主干复验状态以PR最终记录为准。用户授权在A2完成后串行进入B，未授权跳过B1直接实现B2/C/D。

## 1. 前置基线与修改简报

- 接续基线：`186785e662b15989c649201a25709ae90cfee410`，Skill10.3.0 / Project State Schema8.2.0，完整文件树`ff0e5612bb9df47ea33a0ad74e1e47ff5e613ff8`。
- A2 PR #238：先恢复未推送补丁，复核并修复上游资格读集遗漏和原生MATLAB合成声明别名；合并与测试以PR最后验收记录为准，不用旧1805项绿色结果替代新反例。
- 本阶段目标：安全读取已验收工作簿中的明确指标，用有限派生图检查算术、单位、比较对象和数据范围，并输出可定位诊断。
- 明确不做：B2正文/摘要/图注自动扫描和fragment失效写入、C审查回执、D案例库、数值模型重跑、新全局状态机或数据库、重写A2事务、修改真实用户文件、发布或移动tag。
- 当前计划提交是docs，不升级版本。完整B1可选能力集成拟采用Skill10.4.0、State Schema8.3.0、B1协议1.0.0；只有真实接口冻结和版本矩阵检查后才改载体，禁止全仓替换。
- 只维护一个B1分支/草稿PR；本阶段未验收时不得合并或把功能写成已经可用。

## 2. 必须复用的权威与调用路径

| 对象 | 现有来源 | B1边界 |
|---|---|---|
| 当前项目状态 | runtime_assurance.ProjectStateSnapshot及Project State Schema | 同次状态快照；未知/残缺B1字段不当未启用 |
| 当前模型身份 | semantic_identity及runtime现有模型锁 | 不新增批准根；历史证据不足如实报告 |
| 主结果资格 | analysis_prerequisites.primary_issues及runtime逐问evidence | 不能只看status或某个单元格值 |
| 深化资格 | runtime中逐问accepted_result_analysis_workbook检查 | 不能把analysis_issues(for_receipt=True)当当前已验收资格；它检查的是验收前提 |
| 源码、输入及上游 | stage_code、stage_inputs、A2 conformance_gate读集 | A2策略存在则消费其现有要求；缺A2策略不自动强制启用 |
| 工作簿结构/单位 | workbook_schema、实际表头、Numeric Profile | 不强迫所有历史结果改成一种新表，不臆造单位 |
| 主张强度与证据处置 | writing_reasoning_contract#claim_strength_calibration / #analysis_evidence_disposition | 不复制证据等级，不靠修饰词判证明或显著性 |
| 并发与失效 | 原read-set/transaction与typed stale | B1仅只读，不能清除任何既有stale或接受文件 |
| 路由 | 原resolver/router/reading_plan | 新工具显式按需调用，不插入旧任务的强制门 |

新增行为的唯一Authority拟为 `core/claim_evidence_contract.yaml`，记录形状只放入现有State Schema对应`$defs`。内核拟为 `scripts/claim_evidence.py`，工作簿安全读入可拆一个必要helper；不建立多个重复Schema、独立数值JSON数据库或新的模板工作簿。

这些是B1实施落点，不表示文件已经存在。直接使用现有能力须先全文核对对应实现和测试，不根据函数名猜资格含义。

## 3. 启用、存储与结果语义

遵循A0落点 `paper_framework.claim_evidence`，包含版本及有界sources/derivations/claims记录。用户/上游整理者提供声明；B1只能验证、产生stdout报告，不自动写入项目。B2才决定现有协调器如何持久化核验与fragment影响。

缺字段：not_assessed且原流程不变。显式null、未知版本、部分新字段、重复ID、非法类型：blocked，不宽松退回旧兼容。只读CLI如提供独立JSON输出，也仅在用户明确给出输出路径且不覆盖项目事实的条件下评审；首版优先stdout。

至少分开报告：

1. `source_qualification`：原artifact/执行链是否当前合格；
2. `selection_status`：指标是否在真实表内被唯一定位；
3. `arithmetic_status`：有限操作及类型、单位、范围是否成立；
4. `semantic_support`：主张的数学/统计/机制含义是否已独立核验。

B1的算术通过不提升第4项。报告不能包含暗示新approved/accepted或独立review发生的布尔值；`execution_authorized`保持false。记录存在与其语义正确不是一回事。

## 4. 最小节点与引用裁决

- Source节点：稳定ID、question、primary/analysis、现有artifact role、选择器、实际指标身份/范围引用。路径由当前State相应artifact定位，不允许用任意路径冒充accepted角色。
- Derivation节点：稳定ID、白名单操作、命名输入ID、显式单位/方向/汇总轴等必要参数。输入只能引用已存在的source/derivation，不支持内嵌代码或网络引用。
- Claim节点：稳定claim_id、问题/全局范围、事实/计算/比较等类型、声明文字或已有文字锚点、evidence IDs、关联Numeric/Title ID（适用时）、待核验范围。主张不另存可手工修改的权威数值副本。
- ID在相应命名空间唯一，跨命名空间引用带类型；派生依赖必须是DAG。未知引用、直接/间接自证环、重复边或超预算明确报错。
- `derived_from`用于确定算术依赖；supports/contradicts/qualifies只保存明确关系，不凭边存在认定语义成立；consumed_by真正写作消费属于B2。
- 外部论文不能充当本文运行结果；首版own-result source仅接受现有已验收工作簿。尚未支持的来源类型明确unsupported，不伪造支持。

正式精确JSON/YAML形状必须在实现前形成合成有效/无效样例并经Schema测试；本指南不把拟议命令或字段当已实现API。

## 5. 工作簿选择器

使用实际workbook schema，不预设每张表都叫results。最小选择由确切sheet、明确表头行、唯一行键、value列/单位来源、expected_cardinality=1构成。行键中的scenario、metric、time/sample等使用实际列值校验，不只保存作者自己描述的范围。

- 不能模糊匹配后取第一行；缺表、重复表头、零匹配、多匹配、重复键、歧义单位全部诊断。
- 相同数值或相同指标名不代表同一个观察对象、统计量或情景。基准和候选必须有各自身份，比较需匹配其余必要范围。
- 选中行号/单元格作为定位输出；不能用会因排序改变的B12独自代表指标。题目固定单元格模板仅在附带明确模板和行列语义时支持。
- 数值、分类文本和区间按类型处理；布尔值不自动当0/1，数值字符串不默认去逗号/单位后强转。暂不支持的类型返回未核验，不静默转成float。
- 有unit列时核对真实单元格；无unit列时使用已有Numeric Profile或可核验表头单位引用。没有依据是unit_unknown，不自行猜测。
- 读取同一捕获的XLSX字节，完整artifact身份先通过，再选指标；文件改变但目标值未变也不能绕过重新验收。
- 公式字符串不是数值。首版可以对所有公式单元格保守返回needs_review；允许缓存的条件须单独实现并测试当前计算证据，不能只看存在cached value。外部链接不获取、不重算；不启动Excel或其他电子表格程序。
- XLSX解析先限制ZIP成员数、解压总量、单元格预算，再使用安全只读读取；超限显式失败而不是截断后通过。

## 6. 有限派生算术与单位

首批按原计划只提供身份保持、差值、比值、相对变化、百分比/百分点转换、显式同维度单位换算及有界汇总。每项操作用独立函数/类型检查，禁止eval、任意AST执行、模板表达式、外部命令和隐藏求解器。

- 差值约定candidate-baseline；改善率另带higher/lower-is-better并明确基准。不能同一个名称在代码和论文采用相反符号。
- 比值要求分母非零；相对变化的负基准解释须明确。没有适用定义不能把算出的负百分比自动称为改善。
- 百分比与百分点分类型：40%→50%为增加10个百分点或相对增加25%，不得混写。
- 单位先按明确白名单转换为同维度；同名自定义单位可以精确相等比较，但未知换算因子不能猜。含偏置转换或跨维度转换若未实现，显式unsupported。
- 汇总必须绑定有限输入集合和轴；不能将不同metric、样本、时间、情景无说明混加。重复引用同一结果不能被包装成多个独立实验。
- 所有输入/输出必须有限，极大数、NaN、Inf、类型冲突和预算超限拒绝；内部算术保留足够精度，展示按既有Numeric Profile，不强制两位小数。
- 输出源值和派生值是本次观察的派生报告，不写回工作簿，也不把核验称作又跑了一次模型。

最小合成真值：baseline100、candidate80、越小越好，改善比例0.2；percent40→50，差10个百分点、相对0.25；3600秒→1小时。对照组必须包含基准交换、单位错误和分母0。

## 7. 并发、输入和A2衔接

先捕获state、相关framework/源码/helper/实际输入/工作簿与消费Authority，再按原资格链读取。读取结果使用相同工作簿bytes；报告前复核相同read set。不能先验证磁盘A版本，再从B版本选择单元格。

A2启用项目要复用其主/深化现有交付和验收绑定；只启用analysis时不能因此强制primary新声明。跨问引用逐问核对，不用全局某个accepted标志替代单问资格。

B1不要直接用 `analysis_issues(for_receipt=True)` 来断定analysis已验收，也不要复制runtime的accepted规则。若需公共只读适配层，先补明行为等价测试、完整调用链及读集，变更范围在PR里解释；不新增第二判断源。

B1报告不能清除旧artifact stale。B2的细粒度复用尚未实现时，保守标记相关claim待复核；不能因所选指标未变便重新签署工作簿。快照复核仍非原子文件系统锁，不承诺阻止返回后的外部变化。

**跨版本必须单独测试：** A2交付绑定包含它实际消费的完整Skill依据摘要，其中含Project State Schema和output contract。B1新增可选Schema/升级载体，可能使以前已启用A2的绑定依据变更，从而按原合同要求显式复验。不能笼统宣称“B1关闭后所有旧A2绑定仍current”，也不能为了保持绿色自动重签旧绑定。应分别测试：普通未启用A2/B1项目原路径保持；A2旧依据的绑定准确报stale/要求复验；在源码/数据未变且原执行证据仍有效时按既有明确重交付与回执复核恢复资格，不冒称新数值运行。若要减少不相关依据变化造成的复验，必须另立精确语义指纹裁决，不能塞入B1实现或使用广义hash忽略。

## 8. 与原B01—B16的验收映射

| 原场景 | B1验收 | B2保留范围 |
|---|---|---|
| B01 | 同一注册指标的已登记声明值/来源冲突可定位 | 扫描真实摘要与正文，发现未登记差异并定位实际claim/fragment |
| B02—B04 | 基准方向、百分点/比例、场景/样本一致性 | 实际句子的比较含义审查 |
| B05—B07 | 行键/表头歧义、单位/零除/非有限值、DAG错误 | 无 |
| B08 | 外部引文不能代替own-result | 正文引文实际消费 |
| B09—B10 | 不将有限算术提升成全局最优/广泛稳健，保留语义未核验 | Claim Strength与写作/深化处置完整集成 |
| B11 | 目标单元格未变也须满足整个artifact资格 | 精细fragment失效与复用 |
| B12 | 只报告辅助主张冲突，不自动重算全部问题 | 自动分派修正/回退 |
| B13 | 明确单位及显示与原始数值区分 | 全文Numeric Profile呈现扫描 |
| B14—B15 | 公式无可信计算值/危险表达式不执行 | 无 |
| B16 | 只报告已登记覆盖，不宣称穷尽所有论文主张 | 正文遗漏发现与fragment映射 |

新增边界反例：显式null/未知协议/孤立ID；重复或同源证据伪装独立；源码helper或上游附件在核验中修改；路径/符号链接越界；XLSX压缩膨胀及超行数；重复YAML键/别名；只启用analysis；检查失败/成功均不改项目字节。

原B01要求检查真实摘要与正文中的同一指标并定位claim/fragment；B1的已登记声明核验只覆盖其中一部分。完整B01须在B2验收。未覆盖的B2部分必须保持未完成，不能为了给B1打勾而删除原计划场景。

## 9. 实施白名单与步骤

第一步仅本指南及现有生成索引。功能白名单候选：新Claim Authority、最小只读内核/必要安全读取helper、现有State Schema的可选字段、显式路由/manifest/按需读取、脚本导航、专项测试与合成fixture、准确版本载体及相关断言。各完整文件在实际修改前必须阅读。

禁止修改：用户数据/批准/结果、数值/PQS/运行回执协议、求解与绘图模板、事务引擎、未受影响旧Schema规则、已有强制gate顺序、C/D路径、已有Release/tag、旧有效断言。超过20个路径仅允许完整接口闭环或版本载体必要影响，必须逐组解释；不要大量格式化。

实施顺序：

1. 原指南/本指南及当前主干事实核对，记录完整基线命令和结果。
2. 先冻结有效/无效合成记录与操作定义，不改用户项目。
3. 完成纯图/类型/算术核验及红绿测试；它不授予source资格。
4. 接入已验收XLSX的安全选择及原资格读集，做变更中断反例。
5. 接入可选Schema与专门只读路由，旧关闭路径差分不变。
6. 逐项补原B场景，完整lint/unittest/index、旧Schema投影及P2差分。
7. 生成物由现有生成器生成，传输核对Git blob/tree，最终精确head CI与真实diff通过后正常合并。
8. main复验、计划台账回填；B2另立阶段，不把B1合并称作整个B完成。

## 10. 资源预算及版本冻结条件

拟合成试点上界先固定：state/framework各2MiB；单XLSX32MiB、全部XLSX64MiB；单包ZIP成员1024、声明解压总量256MiB；单表扫描200000行、256列；全部图节点512、边2048、派生深度64；单声明文本长度4096。实际实现应核对既有读取工具能否在解析前/过程中执行这些预算，再写唯一Authority；不以显示max_row代替实际单元格计数。

预算是拒绝资源失控的边界，不是性能保证。B1启用前/后的耗时和读取量在固定合成集记录；未启用时不得读取工作簿或新合同，不因为存在案例库而全量预加载。不得看到不利结果后放宽预算来通过。

Skill、State、B1协议独立版本维护；B1不改变现有A2策略与绑定协议。原Schema删除仅新增B1字段/定义后应与A2规范化结构完全一致；任何额外差异必须重新裁决，不加入广义忽略列表。

## 11. 回滚、完成与接管

B1无项目writer时可撤回CLI/路由；已有新记录不得删除伪装老版本兼容。保持原数值事实及失效规则；不自动迁移、不倒填核验、不发布用户私有材料。

完成须同时具备：真实producer/consumer/validator引用闭合；原B1范围及新安全反例实际通过；关闭路径不变；当前head完整CI成功；无已知阻断问题；所有未核验语义和B2范围如实标记。文档写完或文件创建不等于功能完成。

本指南首次提交时只完成B1范围裁决和实现准备，B1功能尚未写入/验收。后续每次接管先读取真实PR、main、本文，再补当前停点；不重复A2、不猜字段、不把原计划历史状态当现状。


## 12. 首次提交时的历史停点（2026-09-25）

本文件首次提交时：A2 PR #238已合并，合并提交为上述186785e6，tree与已测最终head完全相同；[精确提交验收记录](https://github.com/Vexushi1/mathmodel-skill/pull/238#issuecomment-5832746470)已有1810项本地全量测试（3项条件跳过，无失败）、13/13完整CI以及原生MATLAB主/深化证据。合并后主干CI `36137982829`尚在核对，未结束前B1仅进行文档/接口准备，不提交功能实现。

当前唯一活动主题分支为 `upgrade/v10.4.0-claim-evidence-b1`。分支名称代表拟议功能目标，不表示当前Skill载体已经变成10.4.0。此首批提交仅新增本文及现有生成索引，保持10.3.0/Schema8.2.0，不增加B1空字段或尚未消费的运行时合同。

首次提交时记录的下一项工作：建立B1有效/无效合成记录、冻结精确Schema和有限操作形状，并在当前资格链上验证读取适配；然后才写只读核验内核。当时B1源核验、算术单测、XLSX安全读取、路由集成和最终CI均尚未完成，不能把文档与已有A2测试计为这些功能的验收。

当前实现依据的关键定位（均为上述固定A2提交；后续须复核current main）：

| 文件 | 本阶段使用位置 |
|---|---|
| `docs/modeling_intelligence_evidence_evolution_plan.md` | 第7节主张证据及B01—B16；第10—17节兼容/读取/验证 |
| `docs/modeling_intelligence_a0_decisions.md` | DEC01的paper_framework.claim_evidence落点及DEC04最小证据范围 |
| `scripts/runtime_assurance.py` | ProjectStateSnapshot位于本文件；hydrate_project_context逐问题的accepted evidence，不是全局布尔替代 |
| `scripts/analysis_prerequisites.py` | primary_issues及analysis_issues语义不同，后者的for_receipt不能当已验收检查 |
| `scripts/conformance_gate.py` | inspect_gate、observe_execution_sources和新增上游依赖读集 |
| `scripts/stage_inputs.py`、`scripts/stage_code.py` | 实际来源与已声明源码包身份 |
| `core/project_state.schema.yaml` | 当前paper_framework、Numeric Profile、A2声明/绑定及唯一字段形状 |
| `core/writing_reasoning_contract.yaml` | claim_strength_calibration、analysis_evidence_disposition |
| `scripts/project_transaction.py` | _check_read_set及既有事务边界；B1不改其实现 |

后续每次提交把实际测试数、失败、修正、head及CI写入本阶段PR，不倒填未执行结果；如需增加本文白名单外文件，先说明必要性及对应计划条目。整份B完成还需要独立B2阶段。
