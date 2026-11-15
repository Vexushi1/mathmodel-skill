# P6-B：2024 COMAP 历史题实证对照的前置核验记录

> 状态：**SOURCE PAGES VERIFIED / RAW BYTES NOT ACQUIRED / STUDY NOT PRE-REGISTERED / NO REAL SCORES**。
> 核验日期：2026-11-15；仓库基线：v10.32.0 / `57a01c47a92c16d39f6a7c966377f36c6fa22326`。
> 本文件是 Issue #323 的**题目特定执行记录**，不是第二套评估规则。唯一评估协议是 `docs/literature_p6_evaluation_protocol.md`；尚未合并的计划 PR #317 仅供参考，不能覆盖现有 Authority。

## 1. 目的与证据边界

本阶段先锁定**哪些官方题面和附件必须取得、每题哪些要求构成评价锚点、正式试验开始前还缺哪些记录**。不存储或复制 COMAP 原题内容、数据、论文或学生答案，不根据网页展示值编造文件 SHA-256；不生成基线/增强设计、盲评分数或文献收益结论。

- 当前仅确认 COMAP 官方网页和可阅读的 PDF **内容身份**，不是本地原始字节身份。浏览器/检索系统能读出 PDF 页面，不代表试验目录存在相同文件。
- 官网数据包通过 `application/zip` 提供；当前网页提取器无法返回其原始 ZIP 字节。连接的 Desktop Commander 设备离线，本次也没有可用的已授权远端下载执行环境。
- 三个案例必须按同一份题面与附件原始字节、相同基础提示与模型配置、相同预算，分别完成两次隔离生成，另由至少两名真正独立评审在揭盲前评分。全部缺失时保持 `not_ready`。
- 当前不为 P5 增加独立门禁，不调整 SIB、Human Model Approval、项目状态、03A/03B、Figure、Writing 或普通路由。

## 2. 官方案例来源与文件获取状态

以下网址只用作**来源导航**。完成真正获取后必须另存获取日志、实际字节 SHA-256、文件大小、PDF/ZIP 格式签名、必要附件成员清单，且不得因文件名相同就推定是同一版本。

### A：COMAP-2024-MCM-A（资源—性别比例—生态动力系统）

- [官方项目页面](https://www.comap.org/membership/member-resources/item/resource-availability-and-sex-ratios)。
- [官方完整题面 PDF](https://www.comap.org/component/zoo/?element=71992483-3d3b-47dc-a146-3c901bdea04f&format=raw&item_id=3309&method=download&task=callelement)：**4 页已可阅读；原始 PDF 字节未归档**。
- 题面未列出必需的外附数据文件；原题来源仍须实际哈希。
- 评价锚点：可变性别比例对整个生态系统的影响；对七鳃鳗自身的收益与代价；系统稳定性；对其他物种（包括寄生者）可能产生的影响。不能只给单种群数量曲线而漏掉生态交互和稳定性。
- 题设中的不同资源情境及男性比例约 78% / 56% 是原题背景，不可擅自扩展为完整函数关系或把它们冒充可直接拟合的时间序列数据。

### C：COMAP-2024-MCM-C（逐分时序统计）

- [官方项目页面](https://www.comap.org/membership/member-resources/item/momentum-in-tennis)。
- [官方完整题面 PDF](https://www.comap.org/component/zoo/?element=71992483-3d3b-47dc-a146-3c901bdea04f&format=raw&item_id=3304&method=download&task=callelement)：**8 页已可阅读；原始 PDF 字节未归档**。
- [官网 Problem Data ZIP](https://www.comap.org/component/zoo/?element=979148b8-68eb-4e88-83df-a28439d5b0e5&format=raw&item_id=3304&method=download&task=callelement)：官网有入口，但 **ZIP 字节/成员及 SHA-256 未核验**。
- 题面列出 `Wimbledon_featured_matches.csv`、`data_dictionary.csv` 和 `data_examples`。现有 P6 目录将前两项列为必需，`data_examples` 属解释辅助材料；如两臂使用它，必须使用同一份并在共同输入清单中声明，不得单臂额外读取。
- 评价锚点：带发球优势校正的逐分表现指标与流向图；对“波动只是随机事件”假说的可检验比较；变化点预报及影响因素；跨比赛测试、失败诊断与迁移边界；给教练的一至两页建议备忘录。
- 防止信息泄漏：同一比赛的相邻点不能作为相互独立的训练/测试样本随机混洗；跨比赛预测指标须区分未来信息和事后描述。以上是**评价风险提示**，不是预设某个方法获胜。

### D：COMAP-2024-ICM-D（五大湖网络调度）

- [官方项目页面](https://www.comap.org/membership/member-resources/item/great-lakes-water-problem)。
- [官方完整题面 PDF（稳定公开镜像）](https://www.contest.comap.com/undergraduate/contests/mcm/contests/2024/problems/2024_ICM_Problem_D.pdf)：**5 页已可阅读；原始 PDF 字节未归档**。
- [官方 Problem D Addendum PDF](https://www.contest.comap.com/undergraduate/contests/mcm/contests/2024/problems/Problem_D_Addendum.pdf)：**内容已可阅读，仍须取得原始字节并哈希**。
- [官网 Data ZIP](https://www.comap.org/component/zoo/?element=979148b8-68eb-4e88-83df-a28439d5b0e5&format=raw&item_id=3305&method=download&task=callelement)：官网有入口，但 **ZIP 字节/成员及 SHA-256 未核验**。题面明确列出 `Problem_D_Great_Lakes.xlsx`、Problem D Addendum 和数据来源示例。
- 评价锚点：从苏必利尔湖至大西洋的水量网络与管理方案；两处可控出流（Compensating Works 和 Moses-Saunders Dam）；湖泊水位、实际可控量与不受控环境扰动的区分；2017 年水位比较和敏感性；对安大略湖利益相关者的重点分析；致 IJC 领导层的一页备忘录。
- **约束等级**：官方将部分细项写为可选考虑事项，盲评不得以缺少所有可选细项为由机械扣分；要优先看是否覆盖核心控制任务、安大略湖重点与正式交付。水量守恒和单位一致性是必须核查的数学充分性问题。

## 3. 试验开始前必须锁定的特定参数

| 字段 | 当前记录 | 完成要求 |
|---|---|---|
| study_id | `P6B-COMAP2024-PILOT-01`（预留） | 与工作目录、试验日志一致 |
| 官方原始 PDF / ZIP | 未获得原始字节 | 下载来源、时间、字节数、SHA-256、附件成员齐备 |
| 两臂共同输入 | 未冻结 | 每题使用相同的原始题面及必要附件摘要；共享补充材料一致 |
| 模型配置 | 未指定 | 真实模型版本、系统设置和参数先固定，禁止事后更换 |
| 基础提示 | 未冻结 | 按同一版本的模板保存实际字节并计算 SHA-256；两臂完全相同 |
| 预算 | 候选方案：每臂 90 分钟 | 运行前冻结真实可执行的单臂预算与计时口径，基线/增强一致 |
| X/Y 随机化 | 未执行 | 按题随机分配基线/增强；在评审提交前封存映射 |
| 运行隔离 | 未执行 | 不共享候选设计、检索记录、上一臂模型摘要或评审反馈 |
| 独立评审 | 未确定 | 每题至少两名未参与生成的独立评审；先匿名打分并固定记录 |
| 七轴评分 | 沿用 P6-A 权威协议 | 不变更指标、分值或事后调权 |
| 效果报告 | 未执行 | 仅当三题完备时输出 `descriptive_only` 与成本；不宣称因果 |

这是一份**前置核验记录**，不是已经完成预注册的声明。只有官方输入、模型配置、提示模板、预算、匿名映射和评审方案在首个试验开始之前全部真实固定，才能设置 `protocol_pre_registered=true`。

## 4. 原件到手后的最短操作路径

1. 在**非公开**的实验工作目录保存官方 PDF 和 ZIP 原始字节，不要将版权材料推送到公开 Skill 仓库；记录原始 URL、获取时间、响应身份与文件 SHA-256。
2. 对 ZIP 只读列出成员，检查文件名、格式、非空、大小异常、路径穿越与嵌套压缩包；验证 C 的主 CSV/字典、D 的湖泊工作簿/Addendum。解压后的单个文件也要各自记录 SHA-256。
3. 根据本文件第 2 节的题设锚点冻结共享输入和不带评分结果的评审证据要求；如果修改案例必要附件列表，须先核对 `docs/literature_p6_historical_case_catalog.json` 与工具契约，不能暗改。
4. 按现有协议进行三个案例的两条件隔离设计、真实时间/检索记录以及独立盲评；数据不齐时**不执行有结论的比较**。
5. 使用仓库现有只读 CLI 运行 `python scripts/literature_p6_benchmark.py evaluate --study study.json --study-root <local-private-dir>`。若返回 `not_ready` 或 `invalid`，保持 P6-B 未完成，先补全证据再评估 P5 门禁必要性。

## 5. 交付与停止条件

当前真实完成的仅是**三题官方题面及 D 题 Addendum 的公开可阅读核验、题面目标/附件清单对齐、预注册依赖梳理**。尚未完成文件原始字节、六份独立设计、独立盲评或质量报告。本文件独立于运行时，不赋予 P6 实验 PASS、模型批准或版本发布资格；后续进度统一在 Issue #323 记录。
