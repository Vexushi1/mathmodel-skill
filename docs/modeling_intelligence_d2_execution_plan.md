# D2：离线案例检索与显式决策引用实施计划

## 1. 基线与修改简报

- 依据总计划第 9、12、13—20 节及 A0 DEC01/02/07/08/10。D1 PR #257 已合并为 main@04617fa09c5b57e9b0fd6c1f4b95e3206c2ef296 / Skill 10.16.0；最终 head 与 main 各 9 项正式 CI 成功，两版本各 2345 项完整覆盖，main verify-main 成功。
- 已重新读取该 main 的 bootstrap、治理和 D1 最终证据，确认无开放 PR；基线 SHA 如上。目标 Skill 10.17.0，新增可选 State 字段使 Schema 升至 8.15.0；Case Memory admission 1.0.0、C2 Authority/policy 1.0.0、Governance 1.0.6、reading plan 1.1.0、Runtime Assurance 2.4.0 保持各自版本。
- 本 PR 只解决 D01/02/07/08/09/11/12：有界离线检索、按需导航、显式采用/拒绝引用和撤回影响提示。D1 的来源/许可/隐私与同源分组仍是准入 Authority。
- 不改求解器、数据规模或精度，不自动运行用户赛题，不导入真实用户资料，不增加 embedding/API/数据库，不发布 Release，不推进 E。

## 2. 单一事实源与影响面

| 内容 | 唯一所有者 | 实施要求 |
|---|---|---|
| 准入与卡片形状 | `knowledge/case_memory/schema.yaml` | D1 1.0.0 保持；不为检索复制权利或案例正文 |
| 查询、过滤、有限评分与评测协议 | 新 `core/case_memory_retrieval_contract.yaml` | 独立 1.0.0，闭合形状、预算、版本、未知条件与不支持状态 |
| 检索投影 | 新 `knowledge/case_memory/retrieval_features.json` | 只保存人工整理类型/词项及源锚点，绑定 case/version/canonical hash/source hash；不是第二案例库 |
| 项目引用形状 | `core/project_state.schema.yaml` | `decisions.Qn.case_references` 可选，两个 closed definitions，1.0.0 records 协议 |
| 检索与失效消费 | 新 Python 只读工具 | 同一次受保护读集消费 corpus/index/features/Authority，来源内容均为数据 |
| 引用写入 | 显式 Python writer | 使用已有 `commit_project_state`；默认 preview，无自动学习和默认资格 gate |
| 按需导航 | router / manifest / reading_plan / 小型 guide | 精确新 intent；普通任务不读取 corpus，不因普通关键词启用 |
| 验证 | 专项测试、固定合成 query suite、现有生成器与 CI | GitHub-only；最终 head Windows 3.10/3.14 完整覆盖、Windows MATLAB、Linux LaTeX |

其他必要文件包括 bootstrap、Module 02 指导、README/脚本文档、CHANGELOG、当前版本载体/版本矩阵、历史 Schema peeling、严格优化载体对照和 CI 专项列表。生成索引与 MANIFEST 只由既有 GitHub generator 更新。历史验收记录、旧版本 hash 和旧平台记录保留。

## 3. 确定性检索

### 3.1 当前输入与有限类型

查询协议闭合：明确 objective/structures/capabilities、有界题目摘要，以及观察制度、变量类型、信息边界和约束/必要条件。taxonomy 枚举引用现有 Authority。项目查询只从当前明确字段和显式条件形成，不能把自由文本猜测升级为本题已经满足的条件。

合法 `unknown` 或必要条件尚未明确属于 conditional/needs_review；缺少协议 mandatory 字段、非法枚举或未支持版本才属于 blocked。

项目输入绑定注册 framework 的当前 Qn 唯一标题、当前模型口径及真实 Problem Contract 内容；`frozen` 声明不证明题意/条件正确。分类来自 `subproblems.Qn.classification`，capabilities 只取顶层严格为 True 的项，兼容 alias 必须一致。旧项目缺现代分类时不猜测，可以使用明确的 stateless query。尚未批准、甚至尚无 SIB 的冻结题意也可查询；存在 SIB 时用既有解析/身份函数核对当前声明，不把 approved hash 设为检索前置。

七张合成卡片的投影逐项标记 synthetic，并绑定真实来源段落：ordered_fixed_interval、comparable_objects、shared_resource_tasks、lumped_state、network_tasks、random_trials、prediction_decision_chain。只有 003 明确 continuous；005 的连接选择和 007 的资源决策保留 unknown。003 的线性连续适用条件、004 的均匀单状态边界、006 的分布/相关性/期限声明不能自动转为实际验证或已具备数据。

### 3.2 同一快照与硬过滤

先完成 D1 当前准入与索引相等检查，再在同一快照中消费卡片和投影。不得 check_index 后无绑定重读卡片。读取集还包括检索 Authority、features 和工具版本；只有 D1 corpus hash 不足以绑定 features 变更。

适用许可/状态/用途、排除 origins 及已知类型冲突为硬过滤。缺少必要信息明确 conditional/needs_review；信息不明不假定相容。检索关闭为 off、不读 corpus；索引缺失/过期或库不可读为 unavailable、不自动构建；真实搜索无候选为 no_match；未知/残缺查询为 blocked。

结构字段权重高于题名词项和模型名。评分为确定性有界整数及稳定 tie-break，不是适用概率。经典词项模式使用相同准入、过滤、top-k 与字节预算；关闭记忆保留明确空结果。输出少量案例、匹配依据、差异、缺少条件、不可迁移项和证据等级，禁止输出当前题虚构数值或批准结论。

首次实现可不跨调用缓存；每次从当前字节重算。报告的身份仍包含 corpus/features/query/retriever/filter，避免以后引入缓存时只按题名复用。

## 4. 评测与同源隔离

固定十条跨题名 query：七个结构相容正例、横截面预测反例、强空间梯度反例和因果识别 no_match。比较关闭、词项和结构模式，记录可观察的召回、错误推荐、必要条件提示、返回 UTF8 字节及运行成本。

这套 query 是从七张合成卡片设计的开发契约集，不是独立留出试验，不据此宣称实际建模质量提升。记录每条 query 的 derived origins，污染项不进入独立性能分母；独立样本不足时指标为 not_assessed/null，任务完成质量需要后续真实授权试点。

D1 index 的单个 origin_group 是最小 origin，不能作为整组唯一身份。D2 从所有成员的 case.source 还原全部 origins；任何排除 origin 命中连通组即排除整组。测试非最小 origin、改 ID/题名、同核心改 origin、三源桥接合并，不把 fork 视作多源证据。

## 5. 显式引用与撤回影响

引用只记录 case/version/source/case/corpus/query/filter/检索器绑定、reference/adopt/reject、采用/拒绝部分、本题证据及理由。adopt 至少一项采用内容和一项当前项目依据，缺少依据不得记录为采用。只允许已有 Qn 决策；不能自动创建 selected_model，也没有 approved/accepted/PASS 字段。引用的 current/needs_review 是逐次复核结论，不能永久相信旧写入状态。

本题证据为有界 typed 引用：范围内 State pointer、真实 framework/SIB 锚点或项目相对文件与实际内容 hash。检查定位存在性、唯一性、范围和字节身份，不将任意字符串或 caller 自填 hash 当已核实证据。持久 project-context 绑定分类/能力/依赖/题意状态的选定字段和 Qn scope，而不是会因写入引用而自变的整个 State raw hash；整个 State raw hash 只用于当次事务。

首版 State 不复制完整 query 对象：writer 实际校验当前 query 并重算命中，持久保存 query hash 和可重建 project-context。后续 inspect 只复核 case/source/context/固定检索规则，明确 `ranking_not_recomputed` 和 `original_query_not_available`，不声称当前仍为推荐命中。未保存的自定义 exclusions/filter hash 仅为历史 provenance。需要重放时可另行加入当前项目内真实 query 源引用，不按 hash 猜回输入。

默认只读 preview；明确写入时复用 ProjectStateSnapshot、当前 State Schema 和事务协调器。补充 State/输入字节预算、Qn/scope/绑定检查及候选 delta 白名单。只允许 case_references 与事务 generation 变化，保留选模、语义身份、Challenge、Human Approval、accepted、stale 和执行状态。

项目根 read-set 传入 expected_file_hashes；Skill corpus/索引/规范读集独立复核，并通过已有 staged validator 观察提交边界。既有事务不保证跨根原子性，不作这样的承诺；每次后续引用消费仍校验当前字节。prepared journal 要求显式恢复与新快照，测试准备前失败、准备后故障和原 roll-forward。重复相同引用不递增 generation。

引用去重比较冻结语义 payload，排除复核时间和动态 current 派生状态；重新复核不会凭时间变化制造新决策记录。

撤回/变更/过滤身份漂移列出受影响引用待复查，默认不写项目；若显式记录 needs_review，也用相同受限事务。不能自动宣布旧数值错误或撤销审批。采用内容真正改变模型时继续原语义修订、Challenge 和人工批准链。引用变更若影响 C2 明确绑定输入，旧回执应正常过期，不能自动重签或豁免。

## 6. State 与路由兼容

C2 consumer 精确支持 State {8.14.0, 8.15.0}，未知版本仍拒绝；当前 lint/版本测试精确要求 8.15.0。保留 C2 1.0.0，因为其字段、激活和资格语义没有改变。

新增严格 previous_d2_schema，仅移除预期 case_references 属性和明确 D2 definitions 后恢复 8.14.0，并核对冻结 D1 canonical Schema digest。previous_c2_schema 增加这一精确 predecessor，所有历史 hash 和旧还原步骤保持。旧 C2/D1 优化载体集合保留，新增严格 D2 集合；任何未声明的默认读库、gate 或资格变化均失败。

新 case_memory_retrieve route 无 boundary role、formal_delivery=false、pre_delivery_gates=[]。单一意图 profile 只 read_now 小型 guide/检索 Authority，tool_interfaces 导航既有 manifest utility；混合意图保持原 fallback，只在精确包含该 intent 时追加工具接口并去重。工具声明不证明运行成功，不预授予输出。普通模型设计、写作和数值交付既有资格保持；Module 02 仅指导在明确需求时选择该工具。

## 7. 验收、顺序与回退

1. D1 merge/main 通过后刷新 main、形成真实基线和独立 D2 分支，再将本稿转为仓库计划。
2. 核心、writer/State、行为测试并行在明确文件所有权下实施；根集成路由、版本、文档及必要当前断言。独立静态复审全部完成再冻结。
3. GitHub generator 形成 bot head，draft 专项覆盖新检索、类型冲突、unknown、groups、失效、关闭/缺失、writer 并发/故障/越权、C2/历史 peeling 和普通默认路线不加载。
4. 远端专项失败仅窄修；源码变化后等待新的 bot head。专项/静态/生成物全绿再 ready，避免 push+PR 重复完整运行。
5. 最终 head 正式两版本全覆盖与其余 required jobs、适用 Optimization baseline 全成功后 squash merge；再核对 main 全量及 verify-main。实际 head/tree/test counts、artifact、失败及修复记录写 PR 台账，不以旧绿色代替。
6. 回退可关闭检索路由；保留用户已写引用原始数据，不删除 State 字段或案例记录来伪造兼容。关闭/索引缺失不改变既有数值或批准资格。D2 完成后停止，不进入 E。

本稿尚无 D2 运行、PR 或合并证据。
