# B1 协议冻结与 A2 显式复验裁决

日期：2026-09-25。本文件补充原增强计划及 `docs/modeling_intelligence_b1_execution_plan.md`，先于本轮功能实现提交；不是运行时 Authority，不追认任何用户项目事实。

> **2026-09-26 接续状态：** B1功能候选已提交至[草稿PR #239](https://github.com/Vexushi1/mathmodel-skill/pull/239)，仍待最终验收与合并；未发布新Release/tag，B2/C/D/E未开始。本文“当前提交仅协议裁决”的表述指2026-09-25首次提交时的历史停点。

## 1. 基线、范围和修改简报

main=`186785e662b15989c649201a25709ae90cfee410`，Skill10.3.0/State8.2.0。A2主干CI36137982829已经completed/success。接续既有PR #239、分支 `upgrade/v10.4.0-claim-evidence-b1`；开始时唯一开放PR就是本主题。已下载B1计划提交6735ea90的完整源码，593个跟踪文件重建tree=`1bfd26fe8c15b1f3a55ba4df389121198edc772e`，与远程一致。

本轮为minor，完整能力目标Skill10.4.0/State8.3.0/Claim协议1.0.0。完成受限来源、选择器、派生图、声明值核对及专门只读路由；先反例，后实现，最后完整验收。B2全文消费和写入、C审查回执、D案例库、用户赛题求解、数值/PQS/运行回执/求解模板和事务引擎不改。Release/tag不变。

## 2. 精确记录与命名空间

唯一可选字段为 `paper_framework.claim_evidence`；其形状仅在现有State Schema定义。根记录必须同时有protocol_version=1.0.0、sources、derivations、claims。空/null/未知字段不是旧兼容；ID由source/derivation/claim各自命名空间管理，引用为 `source:<id>` 或 `derivation:<id>`，不允许claim回指参与算术。

Source至少记录id、question、stage、artifact_role、selector。role必须与primary/analysis对应，路径只能取当前状态注册路径。selector包含sheet、header_row、row_key、expected_cardinality=1、value_type、value_column（区间用lower/upper列）和identity_columns。identity_columns至少包含metric，并把比较所需scenario、sample、statistic、time等实际列映射为语义轴；报告明确哪些轴没有登记，不能推断缺失范围。

单位来源只允许实际unit列、精确数值列表头尾部的括号单位、或当前且唯一的Numeric Profile ID。Profile指标须与实际metric身份一致，且不能覆盖与工作簿明示冲突的单位。无依据返回unit_unknown/needs_review，不默认无量纲。分类文本允许显式不适用单位。布尔、日期、错误单元格、字符串数值不自动转为数值。

Derivation记录id、op、命名inputs及op对应参数。identity/convert_unit/percent_to_ratio/ratio_to_percent为单输入；difference/ratio/relative_change/improvement/percentage_points为baseline和candidate双输入，必须声明comparison_axis；aggregate为有限items集合、明确axis和reducer。不同操作不接受无关参数；重复引用、环、悬空引用和过深依赖都拒绝。报告的值由当次来源派生，不落盘成为第二数值库。

Claim记录id、scope、kind、text、evidence关系列表，可引用现有numeric_profile_id/title_claim_id。可选assertion只表示待核对的论文声明，不是权威数值；包含evidence_ref、value、unit，以及适用的Numeric Profile呈现位置。机器不得从正文自然语言猜出assertion。supports/contradicts/qualifies是声明关系，不是已证明语义；semantic_support始终单独报告未建立。正文位置和遗漏发现留给B2。

## 3. 算术和范围

只做Decimal有限算术，保留原始数值精度，禁止eval/表达式解释器/外部求解。difference=candidate-baseline；改善率必须显式higher/lower且基准严格为正；relative_change同样拒绝未定义的负/零基准解释。ratio只要求同维度和非零分母。40%到50%的绝对差是10个百分点，相对变化是0.25；%与百分点不得互换。有限单位表只支持明确同维度的比例换算，偏置单位或未知换算明确未支持。

双输入必须在comparison_axis之外具有相同metric及已声明身份轴；轴必须存在且对象不同。省略sample/statistic等轴不会获得“样本已核验”的暗示。相同来源单元格的两个别名不构成独立证据，不允许作为两个实验进行汇总；派生节点保留底层来源集合，用于重复来源检测。

汇总只允许sum/mean/min/max，输入集合有界、轴明确且各输入在非汇总轴上可比较；未知维度或跨指标不自动拼接。区间与分类首版支持定位、类型检查及identity；未实现的算术返回needs_review而不是强制转float。

assertion可以使用十进制科学计数法文本作为声明字面量，不允许任何算术表达式。未指定Numeric Profile时比原始值；有当前Profile时按照该位置的显示精度核对，精度预算有界，不发明新统一小数位规则。比对时明确区分比例、百分数和百分点。

## 4. 安全选择和来源资格

先捕获同次state/framework/源码/helper/数据/上游/工作簿及消费依据，再调用现有runtime逐问artifact qualification。analysis不能用验收前置函数冒充当前accepted。B1复用现有资格，不复制第二验收算法；若补适配helper，只负责读集和调用组织。

XLSX先检查ZIP元数据/成员数量/解压预算/路径和外链，再解析XML，拒绝DTD/实体/宏和外部关系，不访问网络、不启动Excel。采用单次捕获字节，真实行、列、单元格和XML深度预算不能被伪造dimension绕过。对缺表、重复表头、重复键、零或多匹配显式失败；选择涉及公式而没有受认可计算证据时needs_review，不利用缓存假装计算已完成。

成功和失败均在返回前复核读集。只读不恢复pending journal，不写状态、工作簿、批准、失效或回执。此边界是读前后的一致观察，不宣称文件系统原子快照。

## 5. A2 兼容问题的本轮解决方式

不改变A2完整Authority摘要算法或绑定协议，不引入旧哈希白名单/语义投影来免除复验。新增Schema及被消费依据变化后，旧A2绑定必须仍然被识别为不适用。

B1来源诊断提供只读复验指引：列出相关阶段旧/当前依据摘要（无法获得旧逐文件摘要时不猜变更文件），明确当前结构是否可观察、哪些绑定需显式重交付，并给出既有交付与回执CLI的参数数组，不执行命令。顺序为primary重交付及原回执复核，然后处理依赖它的analysis；重取当前状态后再核验B1。

原始源码/输入/工作簿字节及执行回执都未变时，现有回执协调器允许重新检查同一工作簿；这不等于新数值运行。如果源码、输入、配置或原证据发生变化，必须服从原重跑要求，不通过删除A2策略或重算旧摘要恢复资格。A2未启用项目不强制启用A2；只启用analysis不要求primary补A2声明。

必须建立真实跨版本测试：由固定A2基线生成已验收合成项目→新Skill依据下报告旧绑定需复验且项目字节不变→调用原交付/回执协调器显式恢复→再通过B1来源检查；过程中不运行数值模型第二遍，不重写工作簿，不改变数学批准。另测原数据/helper变动、回执失败、缺策略与analysis-only不能被这个指引豁免。

## 6. 验收、文件范围和接管

新增范围：Claim Authority；只读图/数值类型内核、受限XLSX helper、必要来源/read-set适配；State的可选定义；专门router/manifest/脚本导航；合成fixture和专项测试；本阶段文档及精确版本载体/测试/生成元数据。B1默认关闭路径不读取工作簿或Claim合同，不加入旧任务强制门。A2现有核验器、状态转换和事务不因本兼容指引改变规则。

测试覆盖原B01—B08/B13—B15的B1部分及预算/路径/公式/重复键/同源/并发边界；B01在此仅核验已登记声明，真实摘要正文扫描、未登记差异发现和fragment定位留B2验收。B09—B12/B16只确认不越权，完整写作集成仍留B2。新版Schema删除确切新增B1定义与字段后必须恢复原A2规范化摘要；这个测试投影不能被生产A2摘要代码消费。保留未知字段和未知版本负例。

执行台账记录实际失败与修正、唯一测试ID和重复发现、完整lint/unittest/index、精确远程head CI、合并tree和main复验。没有真实通过证据不合并，不把自动测试冒称外部独立审查。功能未合并可撤回；回退不删除用户新字段伪装旧兼容。

本文件首次提交时仅完成协议裁决；当时的下一步是建立合成有效/无效记录和红绿测试，功能及B1验收尚未完成。

## 7. 实现中的原生命周期接续条件

真实旧A2合成项目复验暴露：primary结构依据变化后，原状态引擎会清空深化必要性理由。B1只读指引必须在analysis命令前明确提示重新裁决原Analysis Necessity Gate，不能自动恢复旧理由。跨版本测试由合成项目维护者明确重新记录该判断，再调用原交付/回执协调器；不新增状态写入器、不放宽原门、不重新运行数值源码。保持完整旧依据摘要比较。

有限输入和源码预算按整个检查过程累加去重，不能每个source节点重新获得完整预算。单位选择器声明使用表头时须真实存在表头单位，不得静默回退单位列。以上均为原B1来源范围和兼容安全规则的具体化，未进入B2。

B1安全读入也需要实际MATLAB产生的XLSX验证。在既有原生A2合成步骤之后增加一个B1只读消费步骤，并在相同临时项目中核对主/深化值及恢复原state；只扩展`.github/workflows/ci.yml`中的相关测试，不改变求解器、许可证、原生门禁或用户项目。完整运行产物仍由既有artifact上传步骤收集；读取成功不能冒称B1重新执行了MATLAB求解。


## 8. 2026-09-26 接管复核：精度与歧义边界

候选准备流程此前在Git对象API返回403，不能视为功能入库。原始补丁由artifact10874013262恢复并核对ZIP摘要；主干和原有A2 Authority不变。本轮沿用PR #239，不把临时传输文件合并到main。

原候选57项专项再次通过，但补充反例揭示原覆盖不足：固定80位Decimal中1e80+1-1e80可丢失有效值；同一cell存在两个v载荷或两个sheet名称映射同一物理part存在歧义；百分数显示格式的底层比例值不能直接当显示百分数。新增8个方法，其中7个在原候选失败、1个转义百分号正常控制通过，零执行错误；最小修正后65项通过。

本阶段维持80位预算，不静默舍入有限派生运算：需要非精确算术（含超精度中间量或非终止小数）时返回needs_review，不给出伪精确值。唯一允许的显式呈现舍入仍由Numeric Profile决定。高精度identity原始值仍保留；没有扩大预算或更改数学模型。

OOXML读取拒绝重复载荷、重复sheet集合和多个sheet名称指向相同物理part；宏表内容同样拒绝。百分数样式与底层存储尺度首版未建立显式消歧协议，数值选择返回needs_review；转义或引号中的百分号只是文字，不误判为缩放。不放宽DTD、外链、公式缓存和已有资源预算。

完整B1集成和精确远程提交的验收结果以PR最终执行记录为准。本节描述已复现并修正的候选行为，不提前宣称合并、原生MATLAB通过或B2完成。

## 9. B13 Numeric Profile 显示口径复核

恢复后的候选中，未知/缺失display_form可被按普通小数处理，且百分数/整数/区间显示模式未校验实际类型。本轮新增6个测试方法，修复前8个失败断言、零执行错误，科学计数法为正对照。修正复用原State Schema的numeric_metric_entry定义，拒绝非法Profile；显示模式与scalar/interval/categorical匹配，percent必须是明确百分数量，integer必须零小数位。真实单位冲突测试补全合法display_form，继续测试原单位冲突，不通过新增形状错误遮盖它。显示精度舍入仅用于明确Profile下的待核对声明，不改变原始数值事实。最终完整回归和原生验收以PR最终记录为准。
