# CUMCM 论文写作规范、合规模板与结果深化叙事：详细修改计划（Plan Only）

> **状态：待用户审阅／未实施（planning-only）**  
> **仓库：** `Vexushi1/mathmodel-skill`  
> **编制日期：** 2026-11-03  
> **历史编制基线：** `main@b4903613801e68d20b3d8c6620bd20004cadcf0b`，Skill `10.23.3`。
> **当前审查基线：** `v10.24.0 / main@55097cc8537f4bb8a1da7d8ca31e13c160821946`；Release、Tag 和 main 一致。  
> **文档分支：** `docs/cumcm-paper-writing-compliance-narrative-plan`  
> **本次提交类别：** `docs`，只新增本计划，不修改任何运行时 Authority、模板、脚本、测试、版本或用户项目  
> **后续实施版本：** 不抢占版本号；正式实施前以最新 `main`、已合并 PR 和仓库治理规则重新裁决 patch/minor 及目标版本。  
> **已发布依赖：** PR #288 已合并并发布 v10.24.0；后续所有功能阶段必须继承当前 Python/MATLAB 双后端及配套状态、读集、提交接口。  
> **本文件性质：** 实施蓝图，不是第二套 Runtime/Writing/Template Authority，也不是已经完成修改或通过 CI 的证明。

> **审查沿革：** §0–§9 初版，§10–§12 二次源码与官方合规审查，§13–§14 为 v10.24.0 发布后的第三次接口兼容性审查。旧版等待 #288 等已失效条件，以最后的兼容修订为准。仅计划，不代表功能验收。

## 0. 修改简报（满足 SKILL_CHANGE_GOVERNANCE.md §3）

| 治理字段 | 本次规划 |
|---|---|
| 修改主题 | CUMCM 2026 正式交付合规、MD→LaTeX 问题章节同步、结果深化分析连续性及 Handoff 减负 |
| 当前版本 | `10.24.0`（第三轮审查基线；10.23.3 仅为计划历史记录） |
| 目标版本 / 等级 | 本计划：docs／不升级；后续功能 PR 在已发布 v10.24.0 之后根据最新 main 裁决目标版本 |
| 直接目标 | AI 声明和附录必需；电子版摘要第一页；问题章节以 MD 写作 Authority 为准；深化分析有动机、证据、结论回收；简短评价章；常规值两位小数；降低 Handoff 重复维护 |
| 明确不做 | 不改模型设计、Human Approval、03A/03B 求解或数值验收、accepted Workbook、图表证据科学规范、绘图后端、提交结果数据或历史项目正文；不新建平行状态系统/自动语义评分器 |
| 核心 Authority | `SKILL_CHANGE_GOVERNANCE.md`、`core/bootstrap.yaml`、`templates/latex/cumcm/hsk/template_manifest.yaml`、`modules/05_writing/paper_writing_protocol.md`、`core/writing_reasoning_contract.yaml`、`core/writing_runtime_contract.yaml` |
| 相关消费者 | CUMCM 主/子模板、LaTeX adapter、AI Cleanup、Framework、Competition Profile、Review、template/prose audit、lint、runtime resolver、Tests、GitHub CI |
| 禁止触碰 | 已发布 v10.24.0 双后端业务行为、`legacy/` 默认执行路径、用户已有模型/数值/历史代码、未确认的其他竞赛格式、受管索引和 MANIFEST 手工内容 |
| 兼容性 | 既有 LaTeX 单文件/历史项目按原身份只读兼容；仅新建或明确要求重新实例化的 CUMCM 2026 正式模板应用新默认；其他竞赛继续按各自年度规则 |
| 验收 | 官方规则实例化、MD/TEX 标题一致、AI 双分支、附录材料/无程序分支、电子版首页、动态小问、结果深化叙事样例、Precision Profile、Handoff 无增量门禁、两版 Windows 回归、LaTeX 正式 attestation |
| 回滚 | 分阶段独立 revert；保留旧项目读取；不撤销模型批准、不重算用户数值、不覆盖历史结果 |

**授权边界：** 用户已经批准开始编写详细计划，**尚未授权按计划修改功能代码**。每个实施阶段仍要按最新主干复核影响面并单独获准后执行。不得把“计划评审通过”写成“实现已经通过”。

## 1. 仓库结构、读取链与现状

### 1.1 已确认的 Authority 关系

```text
core/bootstrap.yaml
  ├─ SKILL_CHANGE_GOVERNANCE.md                   维护纪律
  ├─ config/competition_profiles.yaml             赛事 / 年度规则的来源与核验状态
  ├─ core/writing_runtime_contract.yaml           逐阶段读取、写入与现有 seam 消费时机
  │     └─ scripts/resolve_runtime.py              启动/路由消费者
  ├─ templates/latex/cumcm/hsk/template_manifest.yaml
  │     ├─ hsk_main.tex                            一级槽位、实际 \input 与前置页面
  │     ├─ sections/{06..}_question*.tex           每问维护示例
  │     ├─ sections/09_evaluation.tex
  │     ├─ sections/10_ai_tool_statement.tex
  │     └─ appendices/appendices.tex
  ├─ modules/05_writing/paper_writing_protocol.md  常规正文、结果解释、连续性
  │     └─ core/writing_reasoning_contract.yaml    数学推导/标题/数值/Claim 的复杂 Authority
  ├─ modules/05_writing/latex.md                   只负责 LaTeX 载体
  ├─ modules/05_writing/ai_cleanup.md              只负责无损表达精简
  └─ modules/06_review/{content_review,final_delivery}.md
          └─ scripts/audit_latex_project.py
                ├─ scripts/audit_paper_prose.py
                └─ scripts/audit_v8_writing_surface.py
  辅助消费：scripts/validate_template_manifest.py、scripts/lint_skill_checks.py、
            scripts/render_paper.py、templates/model/model_paper_framework.md、
            tests/test_*、GitHub Actions。
```

**唯一权威边界：** Template Manifest 负责一级骨架与官方槽位结构；`paper_writing_protocol.md` 负责普通写作行为；`writing_reasoning_contract.yaml` 负责复杂数学语义与优先二级标题；`writing_runtime_contract.yaml` 负责何时读取/执行；`config/competition_profiles.yaml` 负责当届已核验官方要求；LaTeX 仅实例化。计划、README、示例、测试不得反向篡位。

### 1.2 已核实的具体漂移／耦合

1. **合规槽位关闭：** `template_manifest.yaml` 中 `ai_disclosure`、`appendix` 均为 `required:false/default_active:false`；`hsk_main.tex` 相应 `\input` 处于注释状态；AI 声明子文件只有填写说明而无可见真实声明。
2. **2026 年已发布，但 profile 尚未核验入库：** `config/competition_profiles.yaml#profiles.cumcm.edition_rules` 仍为 `edition:current/verification_status:unverified` 且缺来源和具体规则；不能把旧默认称为已核验合规。
3. **电子版前页风险：** `hsk_main.tex` 使用 `\documentclass{cumcmthesis}`，而 `cumcmthesis.cls` 默认开启 preface；无封面选项 `withoutpreface` 尚未成为 CUMCM 电子版默认入口。
4. **MD/TEX 二级标题冲突：** `paper_writing_protocol.md` §3.1 已首选“XX模型的建立→模型求解→模型求解结果与分析→可选模型检验（与对照）”；`template_manifest.yaml#cumcm_question_section.default_complex_question_headings`、`fixed_template_checks` 与部分维护用 `*_question*.tex` 仍用“模型建立→模型求解→求解结果→结果的分析与验证”。
5. **旧规则被测试锁死：** `scripts/validate_template_manifest.py` 的附录逻辑要求 `required/default_active` 为 false，并检查固定 A/B 子节；`tests/test_v800_template_authority.py`、`test_v872_template_assembly_consistency.py`、`test_v10233_cumcm_problem_analysis_appendix_headings.py`、`test_template_index_exclusions.py` 均涉及旧默认；`lint_skill_checks.py` 断言高精度数值配置。
6. **结果连续性已存在但偏窄：** Protocol §9、§10、§11 已有 RESULT 与 VALIDATE bridge，§4/§5 已有 Local Narrative / Paragraph Handoff；真实缺口是结果深化时的**前向动机、分析证据、后向结论回收**尚未完整规范，不应再造状态系统。
7. **Handoff 维护面广：** `paper_writing_protocol.md` §5A、`writing_runtime_contract.yaml#cross_file_chapter_handoff`、`templates/model/model_paper_framework.md#Chapter Handoff Map`、`modules/06_review/content_review.md` 和 `tests/test_v810_cross_file_chapter_handoff.py` 存在消费者。且 `scripts/resolve_runtime.py` 引用 `cross_file_chapter_handoff.activation` 的缺模板回退语义，不能直接删除该节点。
8. **数值规范需分层：** `core/writing_reasoning_contract.yaml#numeric_style_contract.high_precision_default` 为评分敏感值给出 6–7 位默认，`ai_cleanup.md` 同步强调高精度，`lint_skill_checks.py` 做字面约束。日常两位小数必须新增为**普通展示级默认**，不能覆盖可评分精度。
9. **评价章可轻量化：** `sections/09_evaluation.tex` 是三段示例，Protocol §15 与 Reasoning 的 model_evaluation 尚不应机械要求优缺点数量；用户希望“优点约三项、不足通常一到两项、推广简短”。

### 1.3 2026 年官方依据（实施时复核有效版本）

- [全国大学生数学建模竞赛论文格式规范（2026 年修订稿），组委会 2026-07-02](https://dxs.moe.gov.cn/zx/a/hd_sxjm_gsyw/260702/2046411.shtml)：电子版第一页是摘要专用页，承诺书及编号专用页不在电子版；正文不超过 30 页，附录在正文后；附录列支撑材料文件及完整可运行源程序；无程序/无支撑材料时按规定明示；电子版与支撑材料分别提交且有各自文件大小要求；保持匿名与参考文献规范。
- [全国大学生数学建模竞赛 AI 工具使用规定（2026 年试行），组委会 2026-08-07](https://dxs.moe.gov.cn/zx/a/hd_sxjm_gsyw/260807/2051819.shtml)：2026-09-01 起适用；参考文献前须有“AI工具使用声明”，实际使用与未使用均须据实择一；使用 AI 时按规定另附 `AI工具使用详情.pdf`。2025 年版声明位置与要求不同，严禁混用。
- 这里的“2026 必需”是**特定年度、特定竞赛**的合规要求，不得无条件推广到 MCM/ICM、电工杯及未来尚未核验的 CUMCM 年份。用户对非国赛或学校论文的明确另行要求应交由各自规则处理。
- **官方格式高于用户格式偏好。** 纸质版确有前置专用页要求时使用明确的 print 模式；电子版默认无前置页。不得为纸质版的要求污染电子版输出。

## 2. 目标架构与不变量

1. **稳定一级结构：** 维持当前摘要→问题重述→问题分析→假设→符号→条件数据/模型准备→逐问求解→模型评价→AI 声明→参考文献→附录。固定的“问题X的分析”、附录一级“附录”与必要的 A/B 子节保留；新增官方要求不重排数学章节。
2. **单一写作 Authority：** 复杂问首选二级标题取自现有 MD/Reasoning；维护 `.tex` 可运行示例与其同步，简单问和有充分理由的例外依旧自适应。不要复制一整套 MD 到模板。
3. **研究叙事链：** 主结果→分析动机→参数/误差/对照/收敛/边界等真实证据→支持、修正、限定或拓展主结论。仅在确需时预告，句式不固定，不为“丰富论文”虚构分析任务。
4. **证据边界不变：** 敏感性、鲁棒性、模型/算法对照、1200 次迭代、收敛、成本节省等陈述必须有 accepted 证据；不能把目标曲线平缓等同全局最优，也不能仅因迭代次数更多就声称严格收敛证明。
5. **展示与计算隔离：** 普通非评分关键的连续数值默认两位小数；核心答案、决策变量、坐标、概率、评分、误差、极小量等按题面、分辨率、统计不确定性和 Numeric Profile 决定；不得修改工作簿原值、精度口径、提交文件或后续计算。
6. **少门禁、少登记：** 仅维护真实跨问模型/公式/结果依赖和必须防止 stale 的锚点；普通语言桥接不新增 Schema、状态枚举、必填表、命令或阶段审批。语义检查继续依靠既有 draft/final review，不假装机器能判断自然性或数学正确性。
7. **旧项目兼容：** 不自动改写用户历史论文或重生成旧项目正文；不因本次标题、桥接措辞与展示格式调整反向触发 Model Approval、03A/03B 或 Workbook 重验；需重新交付适用 2026 CUMCM 的旧项目时单独执行合规实例化及复核。

## 3. 实施拆分与文件级修改

### Phase A｜2026 CUMCM 格式合规、LaTeX 页面与对外文件交付（内部建议拆为 A1/A2）

**A1 年度规则数据**  
修改候选：`config/competition_profiles.yaml`、`packs/competition/cumcm.md`、`modules/06_review/final_delivery.md`；必要时 `templates/review/final_review_matrix.yaml`、`scripts/validate_submission_package.py`。  
- 录入可溯源的 CUMCM 2026 规则：edition/verified_at/source、匿名、电子版首页/页面、摘要页、正文上限、附录、AI 声明、提交文件与大小。现有配置字段表达不了的版式要求，只增加最小必要字段并提供消费者，禁止让年度规则失去来源或写死到全竞赛。
- `verification_status` 仅在官方来源实际复核后置 verified；年度切换重新核验。不凭旧默认给未来届次开官方硬门禁。
- 正式交付复用现有 `edition_compliance` / `ai_disclosure` / `reproducibility_and_package` / `rendered_page_surface` 检查族，不新增新的并行评分/门禁体系；机器检查文件存在、位置、大小、材料名单一致性，人工复核事实真实性、版面与声明内容。

**A2 AI 声明的双分支**  
修改候选：`templates/latex/cumcm/hsk/template_manifest.yaml`、`hsk_main.tex`、`sections/10_ai_tool_statement.tex`、`templates/latex/cumcm/hsk/README.md`、`modules/05_writing/latex.md`。  
- 对 **CUMCM 2026 正式实例**，AI 声明始终在参考文献之前且不得省略；`未使用` 与 `使用` 均按官方文本及真实项目事实填写，绝不从文风、Prompt 或模型能力推断使用情况。
- 模板维护用的 smoke 不得冒充已经确认的使用事实。采用“中性占位仅供维护/在正式交付阻断未填写状态”或等价可复现实例化办法；决不能将占位词作为最终声明。**必须通过编译样例及正式提交反例证明不会静默交付空声明**。
- 仅在真实使用 AI 时要求 `AI工具使用详情.pdf` 和对应支撑材料内容；未使用分支不得强造详情文件。

**A3 必需附录与动态材料**  
修改候选：同一 Manifest、`hsk_main.tex`、`appendices/appendices.tex`、`README.md`、Protocol §15，以及 `scripts/validate_template_manifest.py`、`scripts/audit_paper_prose.py`。  
- CUMCM 2026 正式实例的附录一级标题必需；内容列出现有支撑材料文件及完整源代码等官方规定项目。确无程序/支撑材料时准确使用官方规定的说明，不制造文件或虚假“附录A/B”。
- A/B/C 是**实际材料的子节编号**，允许只有 A、或没有必要分节的简短说明；保留一级“附录”与真实内容，不能再把“固定必须同时有 A 和 B”作为业务规则。附录中的完整代码要求应服从官方规则，不把正文关键推导/核心证明仅因篇幅转移到附录。
- 分清论文 PDF 附录与独立支撑材料压缩包两种交付物，检验对应性，不把“论文有程序清单”等同于“支撑材料已复现验收”。

**A4 电子版／纸质版页面模式**  
修改候选：`hsk_main.tex`、`templates/latex/cumcm/hsk/README.md`、`modules/05_writing/latex.md`、`scripts/render_paper.py` / 既有编译配置消费点（仅必要时）。  
- 电子版默认 `\documentclass[withoutpreface]{cumcmthesis}` 或等价无前置页配置；不得默认出现承诺书、编号页或目录。
- 纸质版仅在要求且显式选用时生成应有的专用页；保持统一论文正文/附录内容和符合官方的页码口径。**不能只靠静态包含 `withoutpreface` 就宣称 PDF 首页合格**。
- CUMCM 模板烟测和正式样例编译后验证 PDF 首页为摘要、论文页码正常、参考文献前 AI 声明与最后附录顺序正确。视觉/PDF 页检查由既有 LaTeX 质量流程执行；确需新检查时应嵌入已有流程。

**Phase A 必须同步的旧断言：** `tests/test_v800_template_authority.py`、`test_v872_template_assembly_consistency.py`、`test_v10233_cumcm_problem_analysis_appendix_headings.py`、`test_template_index_exclusions.py`、`test_v810_cross_file_chapter_handoff.py`、`scripts/validate_template_manifest.py`；根据真实失败再补最小专项，不为保持旧例外而削弱有效测试。旧项目与新模板的差异要用**明确版本/实例化场景**区分，而不是把所有旧行为一律当错。

### Phase B｜Markdown 规则、LaTeX 示例与结果叙事一致性（建议独立 PR）

**B1 MD 规范→TEX 维护示例**  
唯一写作定义仍在 `paper_writing_protocol.md#3.1` + `writing_reasoning_contract.yaml#cumcm_default_second_level`：
```text
问题X模型建立及求解
  XX模型的建立
  模型求解
  模型求解结果与分析
  模型检验 / 模型检验与对照（真实独立证据存在时）
```
更新 `templates/latex/cumcm/hsk/sections/06_question1.tex`、`07_question2.tex`、`08_question3.tex` 的维护示例；同步 `template_manifest.yaml#cumcm_question_section` 的 example-only token、`fixed_template_checks.required_question_tokens`、`templates/latex/cumcm/hsk/README.md`、`scripts/validate_template_manifest.py` 和针对示例标题的测试。  
- 不建立固定四节配额；“XX”按真实模型命名。对多独立模型、简单直接计算、后问承接增量，继续允许已规定例外。
- 正式一级标题不变，问题分析“问题X的分析”不动。检查 Q1/Q2/Q3 的示例与作用域，不能只改 Q1 而让其他例子依旧误导。
- 示例中的合法优化目标/约束数学渲染与冒烟用途必须保留，不能因标题同步破坏 `objective_before_constraints` 和编译能力。

**B2 结果深化分析连续性（本主题核心）**  
在 `paper_writing_protocol.md` §9/§10/§11 **就地合并或扩展**原有 Result→Validation Bridge；`writing_reasoning_contract.yaml` 仅在当前语义 Authority 不足时补充最小 cross-reference，不建立第二套 Bridge；`ai_cleanup.md` 只消费其写作要求并防机械改写。  
- 主结果：先给出答案与决定性证据；存在实际后续分析任务时，可明确尚待检验的参数、误差、模型选择、迭代设置或适用范围，不把未完成的检验写成已验证。
- 深化分析：开头指出“承接哪个主结果、为何分析、改变/固定什么、比较哪个指标”；允许参数敏感性、多模型/多算法对照、收敛精度、随机稳定性、误差、边界/情景、消融或真实任务拓展，但**不要求每问都做这些实验**。
- 分析结尾：必须在影响主结论的分析中说明 support / modify / reject 或明确的限制/推广作用（自然中文，不把内部状态词写入正文）；存在反证时同步修正主结果、摘要和相关 Claim。
- 句式不预设：“进一步”“与此同时”“后文将说明”都是可用而非必需；禁止关键词比例评分、字数配额、每图固定分析句、为过渡而生成虚假实验。
- 结果分析内部多个真实任务允许三级标题；独立且已有 accepted evidence 的检验/对照允许第四功能槽；若是求解过程必要的数值终止条件，可放 SOLVE，不机械升级为 VALIDATE。
- **300 vs 1200 次迭代回归案例：** 确实运行且可比，300 次与 1200 次目标值及关键变量在明示精度/容差内接近，则可说明较短预算足以取得近似一致解；只有实际计时/成本证据才能对“节约多少算力”量化；一致性不构成全局最优证明。若 1200 次显著改进或结构解不同，不得声称“300 次已足够”。
- 不重跑 03A/03B、不改图表证据来源、算法真实运行身份或 Figure Registry；只消费现有内容与 accepted 结果。

**B3 模型评价与推广**  
修改 `paper_writing_protocol.md` §15、`sections/09_evaluation.tex` 与必要的 `writing_reasoning_contract.yaml#model_evaluation` 提示：
- 一级“模型的评价与推广”保留必需；优点通常约 3 项，兼顾模型结构与求解算法的真实优势；不足通常 1–2 项（比优点少约 1–2 项），与具体约束或局限对应；推广简短且明确迁移条件。
- 数量仅为写作预算/参考，不是自动删条目、强制凑条目或机器 hard gate；已有依据不足时不为突出优点编造精度、显著性、效率或鲁棒性。
- 不复制逐问检验数据，不把“模型推广”写成空泛应用场景罗列。避免大幅增加页数。

**B4 普通展示两位小数与高精度保护**  
修改 `core/writing_reasoning_contract.yaml#numeric_style_contract`、`paper_writing_protocol.md` §9.1/§14、`ai_cleanup.md#B3`、`templates/model/model_paper_framework.md#Numeric Profile`，审查 `scripts/lint_skill_checks.py`、`scripts/audit_paper_prose.py` 以及相关 numeric/profile 测试：
- 加入一般连续说明性数值 `ordinary_display_default_decimal_places: 2` 或语义等价的**建议级默认**；高精度评分任务保留原 6–7 位条件保护，题目、官方输出、科学计数、物理/统计有效精度优先。
- 优先由当前项目 Numeric Profile 在每个指标确定“摘要/正文/表格/提交”精度，核心答案不得因为“普通两位小数”被截断；计算源数据永不按展示默认重算。
- 统一比例、百分数/百分点、整数、极小误差、科学计数和置信区间；图轴简化不等于关键点可降精度。
- `lint_skill_checks.py` 若保留 6–7 位保护，应升级为**条件语义**的断言而不是强制所有指标高精度；`audit_paper_prose.py` 仍以实际 Numeric Profile 检测漂移，不根据全局 2 位规则自动判定数学精度正确。

### Phase C｜Cross-File Handoff 精简与现有审稿闭环（单独复核后实施）

这是**基于既有机制的减重**，不是删除所有衔接能力。

**C1 定位真实消费者**：复核 `paper_writing_protocol.md` §4/§5/§5A/§11/§12、`writing_runtime_contract.yaml#cross_file_chapter_handoff`、`templates/model/model_paper_framework.md#Chapter Handoff Map`、`modules/06_review/content_review.md`、`scripts/resolve_runtime.py`、`tests/test_v810_cross_file_chapter_handoff.py`、`tests/reading_plan_evidence.py`、runtime goldens 与 framework validator（如有实际读取）。对每个字段/状态写明产生者、消费时机、真正防范的失败，找不到必要消费者则不得将其继续设为必填。

**C2 最小方案优先：**
- 普通正文的行文连接、相邻段落、同一问 RESULT→深化分析、跨问纯措辞：**即时上下文生成 + draft/final 语义审阅**，不持久登记每个 seam。
- 真正会使后问结论错误的跨问模型、参数、公式、结果、图表、claim 依赖：复用现有 Formula/Result/Paper Fragment/依赖锚点与 stale 传播，尽可能不复制。
- 摘要→问题重述、评价→AI 声明→参考文献→附录等结构邻接：仅按最终活动文件做结构和一致性检查，不要求写“过渡句”或逐边界填表。
- `Chapter Handoff Map` 原有历史行须可读；新实例可以省去无意义的 plain narrative seam 行，或仅对有实际冲突/动态继承的节点轻量登记。修改删除判定必须以现有下游消费者为准。
- 保留 `resolve_runtime.py` 所需的 `cross_file_chapter_handoff.activation` 回退边界，除非同 PR 中证明可以用既有源无损替代并更新测试。
- 纯桥接改写不得递增模型 `semantic_revision`、不得 invalidates locked model、不得重触发批准、03A、03B、Workbook 数值重验。

**C3 不接受的重构**：不再建 `IntraQuestionHandoffMap`、`ResultAnalysisBridgeState`、新表、新缓存、新评分器；不对每图/每段新增强制检查；不靠连接词存在判定审稿通过；不在全仓强制迁移历史 Framework。

**C4 决策门槛**：如果经源码追踪，当前 seam map 实际并不导致显著重复读写或运行成本，则只轻量改写运行与审稿说明，不为了“重构”删除已有真实能力；记录保留/删除项及可复核理由，不编造性能收益。

## 4. 逐文件影响矩阵（检查范围≠全部必须修改）

| 层级 | 文件 / 路径 | 本主题负责的变化 | 主要风险与同步消费者 |
|---|---|---|---|
| 竞赛年度 | `config/competition_profiles.yaml`、`packs/competition/cumcm.md` | 官方 2026 profile、来源/适用期 | 旧年规则覆盖新年；其他赛事误触发 |
| 结构 | `templates/latex/cumcm/hsk/template_manifest.yaml` | AI/附录启用规则、示例 headings、静态检查 token | 旧 `required:false` 和固定 A/B 断言 |
| LaTeX 入口 | `hsk_main.tex`、`config/*`（必要时） | 电子版首页、活动 `\input`、slot 顺序 | `cumcmthesis.cls` preface；PDF 页面 |
| LaTeX 子文件 | `sections/*_question*.tex`、`09_evaluation.tex`、`10_ai_tool_statement.tex`、`appendices/appendices.tex` | MD 标题同步、评价示例、真实声明与附录 | smoke 占位/示例错误入正式 PDF |
| 写作 Authority | `modules/05_writing/paper_writing_protocol.md` | 结果深化链、评价与数值、附录语义 | 与 Reasoning/Manifest 竞争 Authority |
| 数学 Authority | `core/writing_reasoning_contract.yaml` | 必要的精度/叙事边界微调 | 评分敏感数值被错误降精度 |
| 运行 | `core/writing_runtime_contract.yaml`、`scripts/resolve_runtime.py` | 交付槽位读取与 seam 减负 | 读取失效／fallback 断裂 |
| 项目框架 | `templates/model/model_paper_framework.md`、实际消费者 | Numeric Profile 建议、旧 map 兼容 | 数据事实与展示口径漂移 |
| 表达 | `modules/05_writing/ai_cleanup.md`、`modules/05_writing/latex.md` | 按 Authority 清理，不重复定义 | Cleanup 改动真实结果 |
| 审稿 | `modules/06_review/{content_review,final_delivery}.md`、`templates/review/final_review_matrix.yaml` | 合规终审、结果回收、人机职责 | 新增重复 gate／官方依据过期 |
| 校验 | `scripts/validate_template_manifest.py`、`audit_paper_prose.py`、`audit_latex_project.py`、`render_paper.py`（按需） | 与新规则同步的结构/载体检查 | 旧失败断言、新假 PASS、编译回归 |
| lint | `scripts/lint_skill_checks.py`、`config/prose_audit_patterns.yaml`（按需） | 更新旧字面断言、保留语义边界 | 为过 CI 删除有效保障 |
| 回归 | `tests/test_v800_template_authority.py`、`test_v872_template_assembly_consistency.py`、`test_v10233_cumcm_problem_analysis_appendix_headings.py`、`test_template_index_exclusions.py`、`test_v810_cross_file_chapter_handoff.py`、`test_v840_author_reasoning_writing.py`、相关 runtime/numeric/review tests | 旧模板/运行 goldens 正负样例 | 仅变更 happy-path、遗漏旧项目 |
| CI 与生成 | `.github/workflows/ci.yml`（仅真实需要）、`scripts/generate_indexes.py` 的受管输出 | 正式 GitHub 验收 | 手工修改 `MANIFEST.sha256`/索引 |
| 禁止变更 | 03A/03B、solver backend、Figure backend、accepted Workbooks、Model Approval、历史论文 | 只读影响面核查 | 将纯写作优化变成模型或绘图重构 |

## 5. 有效性样例与负例矩阵（计划要求实现阶段覆盖）

| ID | 场景 | 预期结果 | 允许检查类型 |
|---|---|---|---|
| T01 | CUMCM 2026、确认未用 AI | 参考文献前**准确声明未使用**；不生成 AI 详情 PDF | 结构自动检查 + 事实人工确认 |
| T02 | CUMCM 2026、确认用 AI | 准确披露用途，支撑材料存在指定详情 PDF | 文件检查 + 内容人审 |
| T03 | AI 使用事实未知／占位未填写 | 不得给出正式合规交付 PASS；不自动选择任一声明 | Hard/Review 按已验证规则 |
| T04 | 附录有程序和支撑材料 | 保留完整代码与材料清单、与实际包对应；无空 A/B | 结构 + 人工复现 |
| T05 | 确无程序或支撑材料 | 仍有一级“附录”及规定说明，不造虚假文件 | 结构 + 真实事实确认 |
| T06 | CUMCM 电子版 | 编译 PDF **第一页摘要**、无承诺/编号页；正文/附录顺序正确 | 真实 PDF 检查 |
| T07 | 明确纸质版要求 | 可以显式开启规定专用页；电子版默认不受影响 | 双模式 LaTeX |
| T08 | Q1/Q2/Q3、简单问/复杂问 | MD 与 TEX 默认示例一致，允许合法例外，目标/约束烟测不倒退 | Manifest + 真实示例 |
| T09 | 主结果后参数敏感性 | 指出被扰动参数、基准条件、响应量、有效范围并回收结论 | 人工语义审稿 |
| T10 | 主模型与另一个模型比较 | 对照存在且指标可比，解释差异而非宣称无据优势 | 证据 + 人审 |
| T11 | 300 vs 1200 次迭代同解 | 明确容差、关键变量/目标一致性及计算效率证据；不虚称证明全局最优 | 证据 + 人审 |
| T12 | 1200 次明显改进／不同解 | 修正或限制 300 次结论；摘要/正文同步 | 证据 + Claim 审核 |
| T13 | 未做敏感性/对照 | 不补虚假实验，不设置空 VALIDATE | 结构 + 人审 |
| T14 | 普通数值与高精度评分值同在 | 说明性值两位、评分关键值按题目精度；Workbook/提交结果原值不变 | Numeric Profile + audit |
| T15 | 旧项目无 Chapter Handoff Map | 仍能读取/局部写作；纯措辞改动不触发模型 stale | runtime + framework tests |
| T16 | 单文件/非 CUMCM | 不强推 CUMCM 附录、前页或 MD 标题 | 兼容回归 |
| T17 | 官方年度未核验 | 不冒充已核验 hard；提示核验，不静默采用上年规则 | compliance review |
| T18 | 模型评价简短且内容真实 | 约三项优势、1–2 项不足只是默认建议；例外合法 | 人审，不设硬数量门禁 |
| T19 | 注释里有 `\input`、LaTeX 代码 listing 中含节标题 | 不误判为活动章节或官方声明 | audit 假阳性测试 |
| T20 | 编译图表/引用/B2 证据链 | 原有引用、caption、Figure/Workbook 绑定不回退 | formal LaTeX/claim regression |

**分层验收原则：** 自动检查只做文件、槽位、结构、显式冲突、Numeric Profile 声明与编译；“为什么要做敏感性分析”“比较是否公平”“结果有没有解释透彻”等由助手人工按证据判断，禁止创建自动“自然度评分”或连接词硬门禁。

## 6. 施工顺序、批准节点与完成定义

**计划 PR：** 本文件单独提交，`docs` 变更；保留 Draft/待审查，用户批准后按实施阶段另建功能 PR。  
**实施 PR 方案：**
1. **PR-A1（CUMCM 2026 正式论文合规）**：修订年度规则和正文模板、AI 双分支、附录完整代码、电子/纸质模式、既有审计与真实编译样例；独立验收。
2. **PR-A2（官方对外文件交付）**：基于 A1 的真实论文 PDF，补齐对外独立论文文件与条件性支撑材料压缩包、文件清单与包内校验；保留内部证明 ZIP 而不将它当官方上传文件。A2 合并并验收后才可称 Phase A 完成。
3. **PR-B（写作内容）**：基于最新主干完成 Phase B，避免在 MD/TEX、Reasoning 和 Test 三处形成平行规范；完整回归再合并。
4. **PR-C（Handoff 减重）**：Phase C 先形成真实消费者/行为差异证据，再决定是最小语义瘦身还是局部实现重构。仅在有可验证收益、兼容与回滚方案后推进。若不需要新增代码，允许只修改现有 Authority/说明及测试，不强迫“重构做大”。

**每个 PR 前必须：**
- 重新读取最新 `main`、`core/bootstrap.yaml`、治理规范和相应 Authority，核对开放 PR、受影响文件及原始预期（严禁使用本计划的固定 SHA 当实时主干）。
- 冻结本阶段明确范围、文件清单、功能级验收和回滚。PR #288 已合并；必须基于已发布主干继承其新接口，并审查实施时出现的其他重叠 PR。
- 仅维护一个事实源；检查全部消费者与稳定示例，解释哪些候选文件最终无需修改及原因。
- 业务行为变更按治理裁决 patch/minor 和真实版本载体；Schema/字段改动必须给出兼容语义和退出条件，不为计划阶段升级 release。

**GitHub-only 维护验收：**
- 开发阶段在 GitHub Actions 跑影响面专项；用户本地不承担 GitHub 仓库维护测试。
- 生成索引、`MANIFEST.sha256` 等由 `refresh-generated` 工作流更新，绝不手工伪造；检查 bot 生成 diff 仅限预期文件。
- 在最终 ready PR head 上核对 GitHub Actions 的 Windows Python 3.10/3.14 完整分片覆盖、Static contract lint、Generated file contract、LaTeX templates、Production LaTeX attestation，以及适用的 MATLAB native/Optimization baseline；保持既有 required check 名称。源码或受管生成 commit 变化后，按最终 head 重新验收，不复用旧 PASS。
- 合并后在当前 main 上复核正式 GitHub CI，报告合并 SHA、真实工作流及通过/失败/未完成状态；仅计划提交时不冒充实现验收。
- 若提交前/编译后 PDF 页面、AI 声明事实或附录材料不满足官方规则，明确阻断正式交付，不能修改测试使其变 PASS。

**完成定义：** 官方格式与真实输出一致；MD/TEX/example/audit 不发生规范漂移；Result→深化分析能在代表性论文样例中实现可追溯的分析动机与回收结论；Handoff 不再因普通措辞产生重复登记或模型失效；Numeric Profile 不降级评分精度；其他赛题/后端/历史项目均无越界变化。

## 7. 主要风险、取舍和回滚

| 风险 | 处理原则 | 回滚 |
|---|---|---|
| CUMCM 2026 与未来年度规则不同 | 赛事 × 年度核验，不把 2026 永久当默认事实 | 回退年度实例化逻辑，保留可溯源规则 |
| 新模板默认活动槽位含占位内容 | 模板 smoke 可独立测试，正式实例必须填真内容且拒绝未填声明/附录 | 回滚实例化与模板变更，不伪造已提交事实 |
| 附录既是必需又不允许空 A/B | 一级附录必有有效内容，二级仅依真实分类出现；独立代码/支撑材料一致 | 恢复实例化前版本，旧项目不覆盖 |
| 取消 preface 导致纸质版缺页 | 明确 electronic/print 模式并编译双样例 | 回滚模式选择，保留可选 `withoutpreface` |
| 更新旧 .tex 示例破坏目标/约束渲染 | 同时保护数学式、唯一 label、Q1/Q2/Q3 动态标题 | 撤销示例/校验同步提交 |
| 结果桥接变成文章套话 | 只规定语义责任与证据回收，不规定固定句式或强制插句 | 回退写作 Protocol 局部规则 |
| Handoff 缩减引起 runtime fallback 失效 | 消费者清单＋旧框架加载回归；不直接删契约 key | 单独撤销 Phase C |
| 2 位小数导致评分关键数据丢精度 | Numeric Profile 层级覆盖，原数值/程序无损，评分场景继续高精度 | 回退 ordinary-display default，保持高精度事实源 |
| PR #288 并行改动 | 独立分支、文件交集审查、串行重基与最终 CI | 不覆盖已发布图源身份、受控读取和对应 CI |

## 8. 后续实施开始前的逐项核查清单

- [ ] 用户批准本计划进入功能修改；计划 PR 与功能 PR 的授权分别确认。
- [ ] 刷新 `main` SHA、Skill 版本、开放 PR / 实际 diff、2026 官方来源与年度配置。
- [ ] 逐文件核查模板/源码/校验器/测试，并把检查项分成“必须修改”“仅需确认无需修改”。
- [ ] Phase A 的 AI 双事实分支、附录动态内容、电子/纸质模式、PDF 首页均有真样例与反例。
- [ ] Phase B 的 MD/TEX 同步不把普通 complex example 误升为所有问题硬配额。
- [ ] 结果深化分析覆盖敏感性、对照、迭代充分性、反证修改主结论、缺失证据不强造。
- [ ] 2 位小数默认不覆盖评分输出、坐标、优化变量、误差/统计有效精度。
- [ ] Handoff 先做消费者追踪和受影响缓存/状态排查，避免引入新 required 字段与 gate。
- [ ] 保留 Model Approval、数值运行与工作簿、Figure 权威、AI 事实真实性、B2/C2 等现有硬边界。
- [ ] 仅通过 GitHub 自动生成索引；最终 head 的正式验收完整；合并后复核 main。
- [ ] 若任何计划假设与届时源码不同，先修订计划说明，不能悄悄扩大实现范围。

## 9. 下一阶段执行指令（供后续聊天复用）

> 请从最新 `main` 读取 `core/bootstrap.yaml`、`SKILL_CHANGE_GOVERNANCE.md` 和 `docs/cumcm_paper_writing_compliance_narrative_refactor_plan.md`，核对当前版本、开放 PR、真实文件依赖与 2026 CUMCM 官方规则。确认用户已批准的实施阶段后，按 Phase A1→A2→B→C 串行推进，先修 Authority，再同步 CUMCM LaTeX、现有消费者与真实测试。禁止直接改 main、禁止破坏已发布的双绘图后端接口、禁止新增重复状态表/过早门禁、禁止为了两位小数降精度、禁止把尚未运行的分析写成已验证。最终依据本阶段真实 diff 与 GitHub Actions 报告交付。

---
**编制结果声明：** 本计划为只读源码与官方规则核查后形成的设计，不代表已经运行任何回归或 LaTeX 编译，不代表已完成 2026 年合规改造；正式验收只能来自后续实际功能 PR 的最终 GitHub Actions 与输出样例。


## 10. 二次深入审查：强制修正项（2026-11-03）

> 本章来自对现行 GitHub main 的实际消费者和 2026 国赛官方文字的逐点核查，属于实施前置修正。**仅规划，非已完成修复。** 原计划中“必要时修改”的候选文件必须通过下面的消费路径核查，不能因为代码改动超过 MD 范围就跳过。

### 10.1 第一优先级：国赛对外双文件 ≠ 内部 official ZIP

**源码事实：**
- `scripts/hsk_pack_submission.py` 的 `--mode official` 由 `official_files()` 读取 `config/competition_profiles.yaml#edition_rules.submission_files`，并在 `submission/submission.zip` 写入文件与 `submission_manifest.yaml`；它是内部来源证明容器。
- `scripts/validate_submission_package.py` 主要校验该 ZIP 的 allowlist、PDF 哈希、来源当前性和 manifest，并**不自动证明**其中某个支撑 ZIP 的内部代码/数据/AI 使用详情符合国赛规定。
- 2026 官方对外是**论文单文件（PDF 或 Word，推荐 PDF，≤20MB，不压缩）**和**独立支撑材料 RAR/ZIP（条件性提交，≤20MB）**。确无支撑材料时允许不提供压缩文件，但必须在论文附录声明“本论文没有支撑材料”。

**必须落地的方案：**
1. 保留内部 `submission/submission.zip` 及其 manifest 的合法审计功能，**不得把它作为第三份官方上传文件、论文 PDF 或官方支撑包**；也不得直接把 `submission/reproducibility.zip` 当成国赛支撑材料，因为它可能包含项目状态、历史日志、过期分析或身份信息。
2. 正式实例交付区分“内部证明产物”与“对外上传文件集合”：论文 PDF 独立存在；存在代码、AI 使用或其他必要支撑材料时再提供官方支撑 ZIP/RAR。外部上传集合不得包含中间 JSON/YAML、状态/审查记录或额外套娃 ZIP。
3. 基于 **当前赛题真实事实** 判断支撑包是否必需：使用过程序、Excel/SPSS 交互命令、独立采集的数据、必要中间图表等时不可任意宣称“无支撑材料”；使用 AI 时必须有 ZIP/RAR 且内含**精确文件名** `AI工具使用详情.pdf`。无程序、无独立数据等均必须与实际工作结果相符。
4. 现有 `edition_rules.submission_files` 为字符串 allowlist：精确路径必需，glob 零匹配被允许。**禁止仅通过给 ZIP 加可空 glob 使“实际必须提交支撑材料而缺失”的项目取得 PASS**。优先复用已有官方 allowlist/项目状态，在原工具最小增补条件完整性逻辑；若需增加字段，必须写明单一来源、真实消费者和迁移/回滚，不能建第二份相互竞争的文件清单。
5. 既有 `submission_requirements.py`、`hsk_pack_submission.py`、`validate_submission_package.py`、`packs/artifact/full_submission.md`、`core/output_contract.yaml#submission`、`modules/06_review/final_delivery.md`、官方打包及失败/允许缺失的测试必须一起复核；必要时改造这些**真正执行的代码**。外部支撑 ZIP 需检查**包内内容和附录列示文件相符**，不能只检验 ZIP 在内部 allowlist 中出现。
6. PDF 和支撑 ZIP/RAR 均做各自 20MB 和身份信息/匿名性检查；支撑包不应包含竞赛提供的原始附件（除官方另要求），需包含实际独立使用的必要源文件和数据。所有外部交付物应能被终审明确列出路径、实际内容、适用规则与验收证据。

**正向验收：** 仅论文、论文+支撑 ZIP、使用 AI+详情 PDF、Excel/SPSS 交互命令四组真实实例。**负向验收：** 缺代码、缺支撑 ZIP、缺 AI 详情、包内名单与论文附录不符、超过 20MB、对外出现第三份内部 ZIP、支撑包意外包含个人信息，必须分别给出准确 finding。

### 10.2 年度判定与单一 canonical 模板的冲突消解

当前 `config/competition_profiles.yaml` 为 `edition: current, verification_status: unverified`。且 `scripts/hsk_pack_submission.py` / `validate_submission_package.py` 当前只检查 `verification_status`、`verified_at`、`source` 和 `submission_files`，**未完成对项目真实年份与 verified 规则年份一致性的绑定**。`template_manifest.yaml` 则只有一个 CUMCM HSK 模板，不能凭 `default_active:true` 自动认为任何历史项目均受 2026 规定。

**最小可执行决策：**
- `edition_rules` 的 2026 实际年份应具体记录（不能仅写 current），验证日期、**官方来源 URL** 和具有依据的提交规则须同源；本地项目实际 edition 来源优先复用既有项目字段，缺失时明确 `review_required`，不得从系统日期猜测。
- **2026 年新建正式 CUMCM 实例**默认保留 AI 声明和附录；**2025 及更早历史工程**保持只读兼容，不迁移正文和旧 LaTeX；未来届次重新核验，禁止静默延用 2026 verified 判定。若项目选择了官方模式但无法识别届次，阻断合规 PASS，提供补齐事实的诊断。
- 明确“canonical 模板维护态”和“正式交付实例态”的职责：模板可以有显著中性占位；交付实例不得保留 TODO、空 AI 声明、空附录或假的 A/B。模板 smoke 允许不具备真实赛题使用事实，但**不得把烟测通过认定为竞赛交付合规**。
- 在上述边界内，优先直接更新现有 `manifest`、`edition_rules`、写作 runtime 的 activation/消费点；只有该表达确实不够时才添最小字段/实例化映射。不可新增第二套赛事选择器或第二份官方规则定义。
- `scripts/audit_paper_prose.py#audit_text` 目前没有当前届次或项目状态；**不得仅凭出现“问题一模型建立及求解”就对所有 CUMCM LaTeX 加 2026 年 AI/附录 Hard**。正式官方 Hard 由能够看到 verified edition 与项目事实的现有终审/交付路径判定；通用 prose audit 只审其能确定的结构事实。
- `core/writing_runtime_contract.yaml#evaluation_references_conclusion_appendix` 的 `read_now/write_now/gate` 仍写“附录 when needed”，也未列 AI 声明写入目标；`template_manifest.yaml#runtime_contract.prose_writer_may_change` 仍允许关闭两者。这些运行时消费者必须与 2026 的“必需性”同步。**仅在主文件取消注释不算完成**。

### 10.3 AI 声明真实填充、官方用语及无程序附录

**官方 2026 AI 原则：** 在参考文献之前保留“AI工具使用声明”，由参赛队确认使用事实后，采用官方两种声明之一。未使用者正文为 **“本参赛队在竞赛过程中未使用任何AI工具。”**；使用者按官方文本写明主要用途和“详细使用情况见支撑材料”，替换用途占位。使用 AI 时支撑包中必须有 `AI工具使用详情.pdf`，其内容覆盖名称和版本、使用目的和环节、主要提示方式与使用过程、采纳/修改/核验情况（语言润色有官方例外）。**不沿用 2025 年“参考文献之后”披露位置**。

**实现要求：** 模板中性占位不能给任何队伍自动认定“已使用”或“未使用”；正式交付需明确选择真实分支、替换未填内容，空标题/说明注释/TODO 不能通过。建议在 2026 模板 smoke 内放**可见的未填标记**便于维护端发现，再由现有审稿/正式交付检查保证未替换状态拒绝 PASS；如果有更轻的实现，必须能同样防漏。不能为此发明新的用户表单或重复状态登记。

**官方 2026 附录原则：** 保留一级“附录”，列明**支撑材料文件列表及建模用的全部完整、可运行源程序代码**（含 Excel/SPSS 等交互命令）。确实没有使用程序时明确写 **“本论文没有用到程序”**；确实没有支撑材料时写 **“本论文没有支撑材料”**。这两句陈述不同事实，可能同时成立，不能互相替代。用户历史偏好的“附录只写标题不放代码”不能覆盖该竞赛 2026 正式要求。

**动态子节：** 有材料时可用“附录A”“附录B”顺序编号，只有一项材料就只有 A；只有官方无程序/无材料的短说明时，允许直接写在一级“附录”之下，不得为“二级标题齐全”生成空 A/B。维护烟测是否保存 A/B 注释示例与正式实例的 A/B 数量分开。修改 `scripts/validate_template_manifest.py` 时，同时撤掉“附录必须 required=false/default_active=false”和“维护示例必须实际固定 A+B”的旧断言；`scripts/audit_paper_prose.py` 的实际正文审计也需允许有内容的一级附录无子节，却继续识别空 A/B 和编号错序。

**源码真实性：** 如使用 `\lstinputlisting`/受控源文件包含生成代码附录，需要核验 `scripts/latex_delivery.py#source_bundle_snapshot`、`actual_input_files`、`compile_report` 与附录源码的引用/内容绑定、项目路径安全、XeLaTeX 编码/换页和长代码可读性。源程序真实内容变化不得继续复用旧 PDF 和验收；绝不把仅在 PDF 打印了代码视为支撑 ZIP 已可复现。

### 10.4 PDF 页面与匿名性必须做真正渲染验证

现有 `cumcmthesis.cls` 来自 2017 年版，`\\maketitle` 在 `withoutpreface` 分支仍会生成标题并设页码，因此不能简单删除 `\\maketitle` 来“去封面”。必须在真实模板编译后核实：
- 电子版**第一页即摘要页**（无空白页、承诺书、编号专用页、目录），标题/关键词与摘要均在专用页，摘要原则上不超过 1 页；
- 阿拉伯页码从摘要页 1 开始连续；A4 纸张、四边页边距 ≥2.5 cm；**正文 ≤30 页、附录不限页数**；参考文献、AI 声明和附录位置正确；
- 电子版论文单文件 ≤20MB，支持文件另计 ≤20MB；纸质版按明确要求生成两张前置页，论文实质正文和附录与电子版一致；
- 不能在 PDF 可见正文、PDF 作者/标题元数据、论文附录或 ZIP 中泄露校名、姓名、队伍/赛区等身份；`config/metadata.tex` 现有 `\\schoolname`、`\\membera`、`\\baominghao` 不应因为选择 `withoutpreface` 就被推定为已匿名。
- 复用 `modules/05_latex_compile_quality.md` 的既有逐页视觉检查与 `final_review_matrix.yaml#rendered_page_surface`，没有必要重复创建报告或新提交门禁；PDF 内容和哈希改变后重新验收，不复用旧证据。

### 10.5 v10.24.0 发布后接口对齐（第三轮审查已更新）

PR #288 已合并，原“等待并行 PR”属于历史条件，不再是实施阻塞。经 `v10.23.3...v10.24.0` 对比，`core/writing_runtime_contract.yaml` 此次仅发生文件级版本更新，既有 Cross-File Handoff 规则仍在；但 `scripts/lint_skill_checks.py`、`scripts/reading_plan.py`、`scripts/submission_requirements.py`、`core/output_contract.yaml`、`core/project_state.schema.yaml` 和 CI 有实际接口变化。后续实施必须以 §13–§14 的 v10.24.0 兼容矩阵为准，不得恢复旧 MATLAB-only 规则或使用 10.23.3 测试基线假装通过。

### 10.6 结果深化分析与 Handoff：避免“减重反而新增系统”

复核确认 `paper_writing_protocol.md` 已有 Local Narrative Chain、Paragraph Handoff Test、Result→Validation Bridge，`writing_runtime_contract.yaml` 有 `cross_file_chapter_handoff`，`templates/model/model_paper_framework.md` 存在可选 Chapter Handoff Map，`scripts/resolve_runtime.py` 引用其缺模板 fallback。**Phase B 先完善已有主结果→分析动机→真实深化证据→结论回收；Phase C 再根据实际 consumer 依赖减重，不能倒序删掉必要上下文。**

300→1200 次迭代并且同精度解的示例必须比较**目标值、关键决策变量和明示容差**；可以说明延长迭代没有带来可观改善，**如果确有计时或计算成本证据**再量化节约收益；不能仅凭曲线变平宣称全局最优。对照模型的样本/评价指标应可比，反例（1200 次显著改善、对照模型更优或敏感区间不稳定）必须回写/限制原主结论。**词汇不固定，不增加强制段落表、桥接 ID 或新门禁**。

Handoff 减重必须逐项分析产生者、消费者、真实 stale 传播与兼容，尤其是 `resolve_runtime.py` 的 `activation.non_cumcm_or_missing_manifest`。若删除 Chapter Handoff Map 中的默认登记，仅在语义或依赖确实会失效时保留锚点；普通章节连接不必先落状态才能写。假如当前实现并不存在明显重复登记开销，则只做语义/读取范围最小修订，不以虚构性能改进为重构理由。

## 11. 深化后必须新增的负例及验收闭合

| ID | 反例/场景 | 必须验证的行为 |
|---|---|---|
| R21 | 2026 CUMCM，无 AI、无程序、无其他支撑材料 | PDF 有准确无 AI 声明和两个适用的附录说明；无第二份空 ZIP |
| R22 | 2026 CUMCM，使用程序但缺支撑 ZIP | 正式交付失败，不能因为 `submission_files` 可空 glob 而 PASS |
| R23 | 2026 CUMCM，用了 AI 但缺 `AI工具使用详情.pdf` | 正式交付失败，不以论文中的“见支撑材料”代替实际详情 |
| R24 | 2026 CUMCM，支撑 ZIP 存在但代码/数据与附录列表不一致 | 识别具体缺失或陈旧文件，不把“ZIP 文件在包中”视为通过 |
| R25 | 只把内部 `submission/submission.zip` 交给对外平台 | 明确不属于合法的独立论文/支撑文件集合，不导出为官方文件 |
| R26 | 历史 2025 CUMCM、未来届次未 verified | 不套用 2026 年声明/附录/首页 Hard；不能静默把“current”解释成 2026 |
| R27 | LaTeX canonical smoke 包含 TODO，占位尚未填充 | smoke 可说明模板可编译，但正式提交严禁 PASS |
| R28 | 仅一级“附录”加合法无材料说明；只有“附录A”的单组材料 | 都合法；空 A/B、附录 B 起始、二级标题错序仍报错 |
| R29 | 300→1200 次主要结果一致/不一致两种真实证据 | 一致时可在容差内支持 300 次足够；不一致时限制或修正原主张 |
| R30 | 修改被 PDF 打印的源程序而不重编 | 旧 source bundle/compile evidence 失效，不得让旧 PDF 合规结论保持 current |
| R31 | `\documentclass[withoutpreface]` 仍输出空首页或身份元数据 | 真实 PDF 首页/匿名检查能发现，不能仅依赖字符串 |
| R32 | 论文 PDF 或支撑 ZIP >20 MB／不应公开字段进入 ZIP | 必须报告具体文件、规则和违规事实 |
| R33 | CUMCM 年份未知但 `edition_rules=verified(2026)` | 不可将官方终审默认为通过；要求有效项目届次 |
| R34 | 改桥接句但模型与数字事实未变 | 不触发 `semantic_revision`、Human Model Approval、03A/03B/Workbook 重新求解 |
| R35 | 基于 v10.24.0 修改运行时/lint/CI | 保留新版双后端、读取计划与 Python Figure 回归；不能复用 v10.23.3 的旧 PASS |

**检查责任边界：** 文件与哈希、年份对齐、格式槽位、正文/附录与支撑包清单可由已有机器消费者检测；使用 AI 的真实事实、模型/算法对照是否公平、敏感性与迭代的数学解释、全文自然衔接，以及每页可视/可复现情况仍须人工复核。不能把通用正文扫描器扩展成无事实来源的论文质量判决器。

## 12. 经过二次审查的实施就绪条件与 PR 依赖

**实施前先闭合以下四个决策（不能开始写代码时才临场猜测）：**

1. **2026 年份与正式/维护模式判定：** 确定现有项目何处记录届次，Verified Source 如何匹配，并拿出 2025 历史和 2027 未核验的反例；必要的最小字段调整和兼容映射须列明。
2. **AI/附录在模板内的无事实占位：** 选择“默认活动槽位+明显未填示例+正式阶段强制替换”或可证明同样安全的方式；拿出 canonical smoke 与真实正式稿两套预期结果。
3. **官方支持文件方案：** 明确 `submission.zip` 仍属于内部证明产物、对外使用独立论文文件及条件支撑 ZIP/RAR；确定真实材料列表、无支撑条件、AI 详情强制条件及 ZIP 包内核验职责，不得把功能全部交给人工但却报告自动 PASS。
4. **打印程序与 LaTeX 来源绑定：** 明确读取程序代码与 accepted 源文件的绑定位置、路径安全、动态输入快照及失效传播；覆盖 Excel/SPSS 等非普通 .py/.m 交互命令的实际呈现要求。

**调整后的实施节奏：**

```text
本计划 PR #289 二次审查 → 用户审议
  → A1 CUMCM 官方年度规则 + AI/附录 + 电子/纸质 PDF
  → A2 对外官方文件导出 + 条件支撑 ZIP + 包内核验
  → B  MD/TEX 标题同步 + 结果深化叙事 + 评价章 + Numeric Profile
  → C  Handoff 消费者验证与最小去重
  → 最终 head GitHub 全量 CI/LaTeX/受管生成结果
  → 合并后 main 验收
```

- **PR #288 已合并并发布**，不存在继续等待它的前置条件。A1/A2/B/C 必须全部基于 v10.24.0 之后最新 main 及真实双后端接口开展；如未来出现新的重叠 PR，再按仓库治理串行协调。
- 后续每个实施 PR 仍按 `SKILL_CHANGE_GOVERNANCE.md` 单主题、独立分支、最终 head GitHub Actions 验收、生成文件自动更新及 main 复核；超过 20 个活动文件须说明为何无法再拆分。
- 实施不要求用户本地运行 Skill 仓库 CI；不手工编造官方提交结果/工作簿/生成哈希/CI 通过状态。
- **“计划完整”只能意味着依赖、决策、测试和回滚已列明；不能替代实施时的新主干核对、真实 PDF 编译、包级验收和人工审稿。**


## 13. v10.24.0 深度兼容审查（2026-11-03）

### 13.1 发布身份与计划范围

- 已核验正式 Release、Tag、当前 main、`core/bootstrap.yaml` 均为 **v10.24.0**，发布提交 `55097cc8537f4bb8a1da7d8ca31e13c160821946`；PR #288 已合并；合并后 main CI `41594545153` 成功。Release 中提到的 Python 图表用例只是该版本验收，不构成本计划未来功能通过的证据。
- GitHub `compare(v10.23.3, v10.24.0)` 显示主要变动在双绘图后端的 State/Output/Figure/Reading/Submission/CI。核心论文 `paper_writing_protocol.md`、`writing_reasoning_contract.yaml`、`template_manifest.yaml`、`hsk_main.tex`、`validate_template_manifest.py` 并未在本次版本直接更改，故**计划写作目标保留，无须重构全部论文 Authority**。
- PR #289 原自 v10.23.3 分支；已发布 main 领先，须将计划 PR 基于 **最新 main** 重建或安全变基，只带本计划及 GitHub 自动生成文件，不可强行合并旧版 MANIFEST/索引。此项属于计划 PR 的独立合并前验收。

### 13.2 新增的必要接口保护与测试

| 影响面 | 现行事实源 | 计划实施必须执行的检查 |
|---|---|---|
| 双图源身份 | `state/project_state.yaml#plotting.backend`、`scripts/plot_backend.py#resolve_question_script` | 项目只选 Python 或 MATLAB 图源一次；A2 打印和支撑包清单按实际 `plot_script/qN_plot.py` 或 `matlab_script/qN_plot.m`；不能从数值求解语言推测绘图语言 |
| 历史兼容 | 无 `plotting` 字段继续兼容历史 MATLAB | A2/B/C 不强制历史项目填写新图源，不自动迁移或把同时缺 .py/.m 当成功 |
| 条件预处理 | `preprocessing_decision=project_level` 才有 `preprocessing_python_plot_script` 或 `preprocessing_matlab_script` | 外部官方支撑包只收集当前实际选用的 `data_process.py/.m`；`not_needed/question_local` 不要求预处理目录 |
| 正式提交读集 | `scripts/submission_requirements.py` 已检查所选图源及 validated SHA，`scripts/validate_submission_package.py` 仍验证内部证明 ZIP | A2 区分“对外独立论文 + 条件支撑 ZIP”和内部 ZIP，不能削弱 Run Receipt、accepted 源、Figure bundle、哈希与依赖有效性 |
| 原始/已验收源码边界 | `core/output_contract.yaml#project_sync.source_identity_lifecycle` 区分 current source 和 accepted run | 附录代码必须绑定实际 accepted 运行版本或明确差异，不得用新交付源码假装已复现旧数值；改图源/代码令论文编译证明 stale，却不自动触发 03A/03B 重算 |
| 受控 Reading Plan | `scripts/reading_plan.py#_figure_binding`、`_project_reads` 改为后端感知；`tests/reading_plan_evidence.py` 将 v10.24.0 作为审批准入载体 | B/C 改 `writing_runtime_contract.yaml`、阅读配置或 Handoff 时先判断具体 read_now/读集变化；只批准真实窄变更，保留历史 P2 negative regression，禁止直接覆盖 golden 使漂移失去可见性 |
| 已发布绘图 CI | `.github/workflows/ci.yml` 新增 Windows 3.10/3.14 Python Figure rendering | 后续写作 PR 不应移除/跳过双后端实际测试；保留 CUMCM/MCM/Diangong 与 Production LaTeX attestation |
| **附录 CI 确定性冲突** | `.github/workflows/ci.yml` 当前 `Prepare CUMCM appendix-active smoke` 断言注释 token `% \\input{appendices/appendices}` 精确一次，并填固定 A/B | **A1 必须修改该 CI 生产者与检查逻辑**。当 2026 正式模板默认活动附录时，旧 `assert source.count(marker)==1` 会直接失败；新 smoke 应覆盖一级无材料说明、仅 A、多材料，且验证活动装配与真实 PDF |
| 03B 结果深化边界 | `modules/03_result_analysis.md` 的 Analysis Necessity Gate | Phase B 只改变证据驱动叙事；没有独立深化证据时不得因为论文要衔接就强制生成 03B；300 与 1200 次比较应明确容差与关键决策变量，不能凭曲线平缓宣称全局最优 |

**程序附录的另一个隐患：** 若采用 `\\lstinputlisting` 等包含实际代码，须确认 `scripts/latex_delivery.py#source_bundle_snapshot`、`actual_input_files`、compile report 是否跟踪该外部源码；不能只因为 PDF 成功编译就判定附录打印代码与实际 accepted 脚本一致。代码/图源、附录、支撑 ZIP 三者需在同一可追溯清单中关联；不要复制并维护第二套哈希状态机。

### 13.3 v10.24.0 新增回归案例

| ID | 真实场景 | 验收 |
|---|---|---|
| V24-01 | Python solver × Python Figure | 收集实际 `.py`，不强制 MATLAB 图源 |
| V24-02 | MATLAB solver × Python Figure | Solver 与 Figure 身份独立，不错绑 |
| V24-03 | Python solver × MATLAB Figure | 图源为实际 `qN_plot.m`，不推断成 Python |
| V24-04 | 旧 MATLAB 项目无 plotting 字段 | 保留读取/论文/提交兼容，不能自动迁移 |
| V24-05 | project_level 与 question_local/not_needed | `data_process.py/.m` 仅在 project_level 生效 |
| V24-06 | 附录中的主源/图源代码变化未重编 | 使 LaTeX/交付证明失效，不使 accepted 数值无故重跑 |
| V24-07 | 主结果已完成而 03B=not_required | 不生成假敏感性或空分析工作簿 |
| V24-08 | 附录由默认关闭改为开启 | CI 更新旧 appendix smoke 的注释查找逻辑，真实编译、附录结构和 PDF 验收通过 |
| V24-09 | B/C 修改 Runtime/读取时机 | 与 Reading Plan 当前核验载体一致，变化必须有局部读集准入依据 |
| V24-10 | 新写作计划不涉及绘图实现 | Python Figure rendering Windows 3.10/3.14、MATLAB 与正式 LaTeX CI 不回退 |
| V24-11 | 对外官方支撑 ZIP 有 Python Figure 源文件 | 只收选定后端实际使用文件，与附录清单一致；不把内部证明 ZIP 当官方上传 |
| V24-12 | 基于 10.23.3 的旧计划 PR | 在 v10.24.0 主干安全变基、GitHub 自动刷新受管索引，最终 head CI 独立验收 |

## 14. 最新版实施路线与结论

**最新版执行顺序（取代旧 §10.5 / §12 中等待 PR #288 的历史条件）：**

```text
v10.24.0 main -> 本计划 PR #289 对齐当前 main + GitHub CI
  -> 用户授权后 A1：年度规则、AI 声明、附录、PDF 页面、更新附录旧 CI
  -> A2：独立论文 PDF、条件支撑 ZIP、Python/MATLAB 双图源和实际代码证据
  -> B：MD/TEX 章节同步、结果深化分析、评价章、普通两位小数及高精度保护
  -> C：逐消费者核查 Handoff 减重，不新增重复状态门禁，保护受控 Reading Plan
  -> 每一阶段当前 head GitHub Windows Python 3.10/3.14、MATLAB、
     Python Figure rendering、全竞赛 LaTeX、formal attestation、静态/生成文件检查
  -> 合并后 main 验收
```

版本控制：本计划 PR 仍是 `docs`，不升级 Skill；功能更改后的真实版本编号/patch-minor 分类必须依据当前 main 和治理规则重新裁决。Release `v10.24.0` 已发布，不得改写其版本载体。原有数学论证、Human Approval、接受的工作簿、03B 证据真实性和 Figure 人工审查均保持不变。

**审查结论：** 截至 v10.24.0，原论文写作方案在 Authority 设计上可兼容，但必须同步修改既有 CUMCM CI 附录 smoke、保留当前双图源/受控 Reading Plan/Submission 的证据身份链，并使计划 PR 本身对齐新主干。上述条款属于未来功能 PR 的明确可验证要求，不表示功能已实现。
