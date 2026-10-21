# Module 06 来源迁移与 P3 验收记录

> 维护记录，不是新的运行时 Authority。本次只实施计划的 P3，目标 v10.22.0；P4 保持后续范围。
> 基线：v10.21.0，main a944de224ac967b7d4b76f8ce411eaef9a71e7b2。P2 合并后 CI #39552530400 已成功。本次候选、最终 head 验收与合并状态以 [PR #274](https://github.com/Vexushi1/mathmodel-skill/pull/274) 的实际记录为准。

## 1. 唯一来源与原文保全

运行时调度只读 core/module_manifest.yaml 的 modules.review_delivery.reading_sources。旧入口继续保留；业务段落按下表逐字迁移，其他位置只引用，不复制质量标准。

| 基线段落 | 当前所有者 |
|---|---|
| 前言、两种消费时机、一 评审分级 | modules/06_review_delivery.md |
| 二 题意／框架／stale，含全部 seam 检查 | modules/06_review/content_review.md |
| 三 公式／角色／算法／命题／数值及全部子检查 | modules/06_review/content_review.md |
| 四 Terminology／Numeric／Claim | modules/06_review/content_review.md |
| 五 标题／结构／段落及历史能力检查 | modules/06_review/content_review.md |
| 六 深化分析／图表／信息价值 | modules/06_review/content_review.md |
| 七 Citation Evidence | modules/06_review/content_review.md |
| 八 编译／复现／提交包 | modules/06_review/final_delivery.md |
| 九 终稿上下文、八类 coverage、finding、官方规则及机器／人工边界 | modules/06_review/final_delivery.md |
| 十 返修优先级、十一 Blocking 条件 | modules/06_review_delivery.md |

基线正文快照为 tests/fixtures/module06_v10210_source.md，共 15,998 UTF-8 字节，SHA-256 为 e78903a21d92bf040bbf13e71a031b0629d86e675b891995f6d99b3dc75a95fe。它只作历史比较，不能被运行时加载，也不能用于回填缺失的当前正文。

测试从三个实际 canonical 文件重组旧前言与十一节，逐字对照快照。两个叶文件末尾按 Git 空白规范仅保留一个换行，重组时只恢复原文的这两个分节空行，不从历史快照回填任何词句。v830 的原保护 hash 和既有历史逆投影保留；仅将保护输入改为真实来源重组。删除、重复、改弱任一业务段均不能靠新 hash 取得通过。

## 2. 阅读与兼容

- 当前草稿阶段：入口真实边界／分级／返修／阻断段及共用叶；不提前读取终稿证据／提交材料。
- 当前终稿阶段：入口真实边界段、共用叶和终稿叶；八类检查和全部 active scope 仍须覆盖。
- entry_headings 来自同一 manifest，使当前阶段不必消费旧锚点导航 stub；不另建章节顺序。
- 旧无 scope 整文件请求：展开完整入口与两个叶文件。旧锚点必须取到对应真实正文，不能只取得链接。
- 缺正文、删除已声明的映射、歧义或不足闭包不能被标成完整；必要时按明确原因回退合法完整闭包，或要求重新解析。
- 正文和映射元数据绑定固定版本／commit 与源字节；现场重新算 hash 不能为 dirty 文件自证。

旧路径和锚点在本兼容窗口保留。删除兼容层须先证明无活动消费者、完成引用迁移和回归，并有独立发布说明；本批不移除旧入口。

## 3. 回执和业务职责

C1 draft 快照新增共用叶，final 新增共用和终稿叶；两者也绑定实际调度来源 core/module_manifest.yaml，映射变化但正文未变不能继续沿用旧审查资格。现有 source snapshot、read-set、失效和 C2 策略继续工作，不新增 Schema／协议版本／用户回执。

叶文件变化而入口不变也必须失去相应 current 资格。漏绑快照或来源缺失不能自动补出新的 passed。C1 契约自身也是既有绑定源，所以该契约变化可能影响历史 model-challenge 回执的 current 状态；不能只承诺影响 draft/final。历史记录保持只读，实际使用按原 policy 复验，不自动重批模型、不改用户项目。

模型批准、用户 full_fidelity 数值执行、工作簿验收、resolver 当前 gate 序列及 PDF 逐页检查的助手责任均不改变。PDF 详细规则继续归 05D。

## 4. 字节度量及适用范围

首版静态源字节：入口 6,474；共用叶 11,305；终稿叶 2,947；完整兼容闭包 20,726。新增文件前言和旧锚点指针也占字节，不能只用入口缩小宣称终审总量下降。

当前阶段的入口必要范围为 2,332 字节。按声明范围去重后，review 子集的草稿约 13,637 字节，终稿约 16,584 字节；最终以同 head 的选择器／并集测量为准。这不包含 Protocol、reasoning、项目输入等其他必读来源，也不是实际读取 token 或全任务成本。完整旧消费者的回退／兼容展开另计。

原 16,000 字节预算继续只约束入口；不为两个叶各复制一个上限，也不抬高旧阈值来通过。测试检查真实 stage 集合、内容保全和去重，actual_read_tokens 没有真实轨迹时仍为空。

## 5. 验收、回滚与后续

本地仅做文件读取、文本修改和 diff 检查；测试、生成和正式验收全部在 GitHub。开发专项须覆盖原文重组、旧锚点／完整闭包、缺源／歧义、dirty 来源／映射、C1/C2 失效、所有被搬移内容的原能力测试。冻结最终 head 后须完成原 Windows 双版本全分片和汇总、lint／生成、MATLAB、LaTeX／Production 及适用基线；合并后复核 main。

回滚通过 revert PR 恢复完整旧 06、消费者、来源声明与测试，并由 GitHub 重建生成材料；不覆盖用户数值、论文和真实批准。

P3 的功能候选、PR、最终 head、远端 run 和主分支复核完成后在 PR 记录实际证据；未完成项不得提前写成 passed。P4 的全流程使用与恢复验证另行推进。
