# mathmodel-skill v7.6.0

HSK 数学建模工作流：**审题与 Problem Contract 冻结 → 数据审计与 `preprocessing_decision` → 语义闭环与复杂度复审 → 条件式预处理 → 用户本地 full-fidelity Python 主求解 → 独立结果深化分析 → MATLAB 证据图 → LaTeX 终稿 → AI cleanup → prose/BibTeX audit → 编译终审**。

## v7.6.0：写作治理收口与 Citation Evidence

本版本集中修改论文写作架构，不改变数值求解、工作簿 Schema、MATLAB 结果计算职责或每问五文件接口。

### 1. 单一写作权威

写作规则不再在多个 active 文件重复定义：

```text
core/writing_reasoning_contract.yaml
├─ 跨竞赛推理与证据治理
├─ Hard / Default / Recommendation
├─ Source → Derivation → Destination
├─ 命题预算与下游作用
└─ Citation Evidence

modules/05_writing/latex.md
└─ 正文章节组织与表达权威
```

`ai_cleanup.md`、`docx.md`、`review_delivery.md`、Artifact Packs 和检查表只消费这些 Authority：负责清理、载体差异、检查、编译或交付，不再复制第二套正文规范。

### 2. `模型论文框架.md` 回归项目记忆

框架只保存当前项目事实、选择、状态和证据位置，包括：

- 当前题意、数据、变量、参数和跨问依赖；
- Formula Trace；
- 数值参数依据；
- 当前论文结构选择；
- 命题与证明计划；
- Citation Evidence；
- 各问结果摘要；
- Python / 工作簿 / MATLAB / 正文映射。

通用的“问题背景写几段、证明写几行、命题框如何排版”等规则不再复制进每个项目框架。具体数值仍回到已验收工作簿复核，semantic revision/hash/stale 仍由 `state/project_state.yaml` 管理。

### 3. Hard / Default / Recommendation

写作规则现在分三级：

- **Hard**：会造成事实、数学语义、可复现性或正式交付错误；阻断交付；
- **Default**：高质量竞赛论文默认组织方式，题型/模板/真实结构可合理偏离；
- **Recommendation**：经验性质量建议，只给 warning。

因此以下旧机械限制已调整：

- 命题 `0--4` 是默认正文阅读预算，不是绝对上限；超过预算需说明不可合并/不可移附录的必要性；
- 不再要求“优点必须多于缺点”；
- 核心模型收束按 `required / inline / not_applicable` 自适应，不再机械要求所有小问拥有同名“核心模型汇总”小节；
- 证明的行数和分步数量只作为 Recommendation，不作为数学有效性或交付否决条件。

### 4. Citation Evidence

新增轻量 claim-to-citation 闭环：

```text
外部核心 claim
→ Citation Key
→ references.bib
→ 正文实际使用位置
```

重点覆盖外部经验参数、外部数据、领域事实、非显然标准定理、方法来源和既有研究比较。本文自己的推导、工作簿结果和数值验证不靠外部文献替代证据。

`scripts/audit_paper_prose.py` 增加可靠的 BibTeX 静态检查：缺失 cite key、重复 bib key 为 blocking；未使用条目和 `\nocite{*}` 风险为 warning。机器不判断某篇文献是否真的语义支持某个 claim，也不从正则判断数学正确性。

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
- `core/writing_reasoning_contract.yaml`：写作推理、规则等级和 Citation Evidence；
- `modules/05_writing/latex.md`：正文结构与表达；
- `core/output_contract.yaml`：目录、产物和正式交付；
- `core/project_state.schema.yaml`：机器状态；
- `templates/model/model_paper_framework.md`：项目记忆模板。

## 关键检查命令

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/validate_model_paper_framework.py 模型论文框架.md --strict
python scripts/audit_paper_prose.py final_latex/main.tex --bib final_latex/references.bib --strict
```

正式项目交付还按实际阶段执行 semantic governance、用户工作簿验收和 project sync。

## 兼容与历史

`legacy/` 只读，不进入默认执行链。旧版说明保留在 Git 历史和 `CHANGELOG.md`；README 不再重复维护每个历史版本的完整规则，以降低 active 读取面和版本漂移。

许可证与第三方声明见 `LICENSE`、`THIRD_PARTY_NOTICES.md`。
