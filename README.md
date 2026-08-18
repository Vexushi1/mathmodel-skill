# mathmodel-skill v7.7.0

HSK 数学建模工作流：**审题与 Problem Contract 冻结 → 数据审计与 `preprocessing_decision` → 语义闭环与复杂度复审 → 条件式预处理 → 用户本地 full-fidelity Python 主求解 → 独立结果深化分析 → MATLAB 证据图 → LaTeX 终稿 → AI cleanup → prose/structure/BibTeX audit → 编译终审**。

## v7.7.0：论文语义与终稿一致性治理

本版本继续收紧长论文写作语义，但不改变数值求解、工作簿 Schema、MATLAB 结果计算职责、三态预处理或每问五文件接口。

### 1. Terminology Registry

`模型论文框架.md` 新增项目级自然语言术语表。对容易混淆的对象、指标、时间量、比例量、场景和样本单元，分别登记：标准术语、定义、量纲/单位、允许简称、不推荐别名、易混术语、对应符号和适用范围。

机器只检查已经登记的冲突和漂移，不从词形相似自动判断两个术语数学等价。

### 2. 高精度 Numeric Profile

核心评分结果不再按“摘要简洁”主动降位数。统一原则是：

- 题面、官方规则、官方评讲或已核验评分口径指定精度时严格服从；
- 没有更具体口径时，对决定答案、排名、阈值、最优值、时间、坐标、概率、误差等评分型连续结果，摘要和正文默认优先保留**小数点后 6--7 位**；
- 摘要可以减少次要数字数量，但不能把保留下来的决定性答案从 6--7 位擅自压缩到 1--4 位；
- 百分比/百分点、科学计数法、单位换算和表格/正文/摘要必须对应同一个高精度底层结果；
- 整数、精确离散量或本身没有更高分辨率的数据不机械补无意义小数。

项目级 `Numeric Profile` 记录每个核心指标的单位、表示形式、必要小数位、工作簿/正文/摘要精度和评分依据。

### 3. Title Claim Gate

标题中的研究对象、主方法、核心机制或核心贡献必须和摘要、关键词、正文主模型、结果证据闭环。仅在末尾附带出现的方法不能包装成全文主方法。

### 4. 局部 paper-fragment stale

在原有 Q 级语义与产物 stale 上增加显式正文片段依赖。某一问变化时，只沿真实依赖使对应模型/结果/图、摘要该问片段、相关模型评价句和相关 Title Claim stale；无关问题背景和独立小问保持 current。

`paper_framework.sync_status=current` 现在表示框架已经同步记录机器状态，不再等价于“所有正文片段都 current”。正式提交前仍不得保留影响当前答案、摘要或标题的 stale fragment。

### 5. 深化证据 support / modify / reject

每项准备进入论文的敏感性、鲁棒性、外样本、多算法或压力测试必须指出目标主张，并标记：

```text
support → 当前主张保持，可作为增强证据
modify  → 主体结论可保留，但区间/阈值/边界/措辞/方案必须修正
reject  → 当前目标主张不能继续作为 current
```

`reject` 不等于无条件重算整题：只有否决核心答案、关键可行性、主要最优方案或模型结构时才触发 `redo_required` 和相应回退；次要 claim 可以删除或降级。

### 6. Paragraph Necessity Test

正文每一节和较长段落都检查：删除后是否会丢失题意、机制、数学关系、求解/参数依据、结果/验证证据、必要边界或标题/Citation/跨问闭环。全部为否则删除、合并或移附录。机器只给 warning，不自动删文。

### 7. AI Cleanup 与 prose audit

`ai_cleanup.md` 收束为四层：Integrity / Evidence / Style & Necessity / Optional machine diagnostics，不再横向堆叠编号检查；原则由 Skill/Authority 负责，具体静态穷举由脚本负责。

`scripts/audit_paper_prose.py` 新增不存在的 `\ref`、未引用 label、图表引用距离、caption 相对位置、Abstract 图表/展示公式、可识别关键词数量、已登记术语漂移和 Numeric Profile 精度异常检查，同时继续保持“不用 regex 判断数学正确性”的边界。

## 当前写作权威

写作规则仍由两个 Authority 收口：

```text
core/writing_reasoning_contract.yaml
├─ 跨竞赛推理与证据治理
├─ Hard / Default / Recommendation
├─ Source → Derivation → Destination
├─ Terminology / Numeric / Title Claim
├─ 命题、深化证据、Paragraph Necessity
└─ Citation Evidence

modules/05_writing/latex.md
└─ 正文章节组织与表达权威
```

`ai_cleanup.md`、`docx.md`、`review_delivery.md`、Artifact Packs 和检查表只消费这些 Authority，不维护第二套正文规范。

## 当前数值工作流

### 数据审计与三态预处理

所有数据题都先做非破坏性审计，但不默认清洗：

```text
preprocessing_decision
├─ not_needed
├─ question_local
└─ project_level
```

共享数据、缺失值或某类赛题的历史经验都不能单独推出 `project_level`。任何改变模型输入的数据处理必须有数据、机理或模型必要性、参数依据和验证证据。

只有 `project_level` 创建：

```text
数据预处理/
├─ 数据预处理.py
├─ 数据预处理结果.xlsx
└─ data_process.m
```

### 每问唯一五文件目录

```text
问题X求解/
├─ 问题X求解.py
├─ 问题X求解结果.xlsx
├─ 问题X结果深化分析.py
├─ 问题X结果深化分析.xlsx
└─ qX_plot.m
```

主求解与结果深化分析是两个独立 Python 阶段。主工作簿 accepted 后冻结主脚本，再生成深化分析脚本。赛题代码由用户本地 full-fidelity 执行，助手只生成、静态检查并验收返回工作簿。

### MATLAB Figure Evidence

MATLAB 只读取 Python 输出的数据和标准工作簿绘图，不重新求解。图形布局按核心结论、证据等级和主要问题动态选择；默认保留图窗供人工调整，不批量自动导出。

## 运行时权威链

```text
SKILL.md / skills/mathmodel-skill/SKILL.md
        ↓
core/bootstrap.yaml
        ↓
core/workflow_router.yaml
        ↓
scripts/resolve_workflow.py
        ↓
route-specific contracts / modules / packs / templates
```

全局硬规则：`core/hsk_core_policy.md`。

主要合同：

- `core/global_preprocessing_contract.yaml`：条件式数据预处理；
- `core/code_quality_contract.yaml`：Python 工程质量；
- `core/user_execution_contract.yaml`：用户本地执行与工作簿验收；
- `core/writing_reasoning_contract.yaml`：推理、术语、数值、Title Claim、规则等级和 Citation Evidence；
- `modules/05_writing/latex.md`：正文结构与表达；
- `core/output_contract.yaml`：目录、产物和正式交付；
- `core/project_state.schema.yaml`：机器状态；
- `templates/model/model_paper_framework.md`：项目记忆模板。

## 关键检查命令

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/validate_model_paper_framework.py 模型论文框架.md --strict
python scripts/audit_paper_prose.py final_latex/main.tex --bib final_latex/references.bib --framework 模型论文框架.md --strict
```

正式项目交付还按实际阶段执行 semantic governance、用户工作簿验收和 project sync。

## 兼容与历史

`legacy/` 只读，不进入默认执行链。v7.6 的 `v0.7-project-memory` 和 semantic-governance 1.0.0 保持只读兼容；项目重新进入当前 writing/review 流程时再补充 v0.8 的 Terminology/Numeric/Title/Paper Fragment 语义。历史版本说明保留在 Git 历史和 `CHANGELOG.md`。

许可证与第三方声明见 `LICENSE`、`THIRD_PARTY_NOTICES.md`。
