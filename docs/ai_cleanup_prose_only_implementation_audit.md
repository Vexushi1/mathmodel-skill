# AI Cleanup Prose-Only：实施范围与消费者核对（v10.26.2）

> 来源：PR #293 中的独立 [Plan Only](https://github.com/Vexushi1/mathmodel-skill/pull/293)，实施基线为 C 阶段合并后的 main@e0c99f7cff730d7f64f49b3c8033aa2c30136df7。本文为维护核查记录，**不是新的运行 Authority、数学等价性证明或 CI 通过回执**。

## 修改简报与权责裁决

| 项目 | 内容 |
|---|---|
| 直接目标 | 将 05C 从“兼有公式/标题/数值裁决的 Cleanup”收缩为普通自然语言润色 |
| 版本/变更等级 | main 10.26.1 → 10.26.2，patch（阶段/接口与旧项目继续兼容） |
| 改动权威 | 05C 的语言润色消费者；Runtime `ai_cleanup` 阶段的唯一 gate |
| 不改变 | 写作 Reasoning/Protocol 的公式角色、证明与结构编辑权限；Review 的数学/证据发现与级别；accepted workbook、State、模型批准、图表与模板内容 |
| 兼容性 | `draft_semantic_review → ai_cleanup → latex_assembly_audit_and_compile → final_review_and_delivery`；`read_now`、`write_now=cleaned_paper_text`、全部竞赛 fallback 与已有项目均保持 |
| 禁止触碰 | 用户项目内容、全部源码生成索引的人工哈希、旧版本/tag、数值计算/执行产物、AI 身份判别 |
| 运行时差异 | 唯一已授权 P2 字段变化是 `writing_runtime.authoring_sequence[ai_cleanup].gate`，以及 10.26.2 version carrier |
| 回滚 | 功能 PR 原子 revert；不回滚此前 A/B/C 改造，不迁移已交付的论文 |

## 具体生产者—消费者矩阵

| 上游 Authority/产物 | 原职责（仍有效） | Cleanup 新权限 | 下游验证 |
|---|---|---|---|
| Paper Writing Protocol §5 / §7 / §11 | 段落必要性、Formula Role 裁决、Result → Validation Bridge | 阅读但不执行数学删减、表格拆分或结果验证扩写 | 现有 draft/final Review |
| Writing Reasoning Contract | Core Derivation Body Closure、Claim Strength、Numeric Profile、算法/命题、证据等级 | 公式、文字推导、数值格式、证明及算法只读；有疑问报告 | Formula/Proof/Algorithm Trace 既有复核 |
| current Framework / accepted workbook / State | 语义、数值、stale | 不改已验收事实、身份或状态 | 既有依赖和交付门 |
| Module 05B LaTeX Adapter | 载体、引用与编译 | 不改 math/code/label/caption；普通 prose 变更需重新生成 current 源码与 PDF 证据 | 既有 compile/PDF check |
| Module 06 Draft/Final | 修正数学/语义/证据缺口，终稿覆盖 | 消费审查完成的 findings、回送未决，纯文本后复核 | 不新建 coverage family |
| GitHub lint/Tests | 规则一致性和单一职责 | 05C 独立禁令、15KB cap、旧冻结 hashes、历史 P2 逆投影均应通过 | GitHub 上最终 head 正式 CI，不宣称词频检测能证明数学完整 |

## 代表性正反例与验收边界

- **AC-01 / AC-15（正例）**：纯空话、无信息增益章节管理句在当前 fragment 内允许删；其他问题/章节不动。
- **AC-02 / AC-03（负例）**：公式符号、方向、编号、align、引用 key 均不得更改，即使自认等价。
- **AC-04 / AC-05 / AC-17（负例）**：中文推导、核心证明、支持性公式甚至已写入正文的普通代数都只读；压缩须回到前置写作 Authority。
- **AC-06 / AC-10 / AC-11（负例）**：全局最优、因果、证明、未经运行的深化分析、外部引文不得自行加强、补造或删除。
- **AC-07（负例）**：包括解释性两位小数的数字，Cleanup 不得舍入；上游 Numeric Profile 不撤销。
- **AC-08 / AC-09（负例）**：章节标题、文件边界、caption、图表数据、表头/图例及标签只读。
- **AC-12（负例）**：已定义的学术术语与首次解释保留，不擅自换名。
- **AC-13（回退）**：发现数学错误时只记录位置与问题，回到 Model/Prose/Review Authority。
- **AC-14 / AC-16（兼容）**：CUMCM、MCM/ICM、DOCX 路由不回退；LaTeX 普通文字变化后旧 PDF/attestation 不能冒充 current。

测试只能核验**规范源码、路由和特定的禁止权限**；它不运行语言模型，也不能证明未来某篇论文的改写保持了全部数学语义。最终数学语义由既有人工审阅和实际产物对照闭合。新增的是一组仓库单元测试，**不是用户本地 checker、审计账本或交付门**。

## 影响面已检查并判定不改

`core/writing_reasoning_contract.yaml`、`modules/05_writing/paper_writing_protocol.md`、`modules/06_review_delivery.md` 及两叶 Review、`modules/05_writing/latex.md`、Template Manifest、`scripts/resolve_runtime.py`、`scripts/reading_plan.py`、项目 State/Schema、Matlab/Python 求解与 Figure、accepted Workbook。它们各已有对应 Authority，重复改写反而产生第二套定义或无关回归。

## 生成与正式证据

PR 仅推送源文件，`refresh-generated` 自动更新 MANIFEST/索引；以最终 PR head 检查 Windows Python 3.10/3.14 全分片与汇总、Static/Generated、MATLAB Native、三个 LaTeX、Production attestation、两个 Python Figure 和适用 Optimization baseline。正式 CI/合并后 main CI 未结束时**不报告 PASS**。Release 继续按用户统一发布安排。
