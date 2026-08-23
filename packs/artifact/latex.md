# Artifact Pack：LaTeX 终稿

本 Pack 只负责 **LaTeX 工程、编译和交付**。正文结构与表达服从 `modules/05_writing/latex.md`，跨竞赛推理、规则等级、命题预算和 Citation Evidence 服从 `core/writing_reasoning_contract.yaml`。本文件不得复制第二套正文规范。

## 一、进入条件

用户要求 LaTeX、可编译终稿、PDF 终稿或从 DOCX 迁移时加载。

进入终稿前：

- `模型论文框架.md` 为 current；
- 当前模型、结果、主要图表和命题状态已锁定；
- 具体数值可追溯到已验收工作簿；
- Citation Evidence 已至少达到可审查状态；
- stale 内容没有进入当前正文。

## 二、输入与工程契约

- 中文国赛保留 `cumcmthesis` 模板体系；MCM/ICM、电工杯使用对应模板；
- 工程根目录、主文件、图片和文献数据库使用 ASCII 文件名与路径；
- 正式结果图来自标准工作簿与 MATLAB 脚本；
- 当前模型、逐问结果摘要、图表映射、命题和 Citation Evidence 从 `模型论文框架.md` 恢复；
- 摘要、正文、表格和附录的具体数值重新从工作簿复核。

默认工程采用 **模块化 LaTeX 源码**。`main.tex` 只承担文档入口、全局配置加载、章节编排、参考文献与附录入口，不作为长正文容器。最低工程：

```text
项目根目录/
├─ 模型论文框架.md
└─ final_latex/
   ├─ main.tex
   ├─ config/
   │  ├─ preamble.tex
   │  ├─ commands.tex
   │  └─ metadata.tex
   ├─ frontmatter/
   │  └─ abstract.tex
   ├─ sections/
   │  ├─ 01_problem_statement.tex
   │  ├─ 02_problem_analysis.tex
   │  ├─ 03_assumptions.tex
   │  ├─ 04_symbols.tex
   │  ├─ 05_data.tex              # 按 preprocessing_decision 决定是否存在
   │  ├─ 06_question1.tex
   │  └─ ...                      # 按实际小问与论文结构扩展
   ├─ appendices/
   │  └─ appendices.tex
   ├─ references.bib
   ├─ figures/
   ├─ 模板类/样式文件
   └─ 最终 PDF
```

CUMCM 工程使用仓库旧版 `cumcmthesis.cls` 时，`scripts/render_paper.py` 只执行已审计、幂等的字体回退补丁，不改其他模板宏定义。

### 2.1 Modular LaTeX Source Contract

模块化源码是 **Default**，不是为了拆文件而拆文件。目标是让语义 fragment 与物理 `.tex` 文件尽量一一对应，使局部 stale 能落实为局部源码修改。

#### `main.tex` 的职责

`main.tex` 默认只包含：

- `\documentclass`；
- `\input{config/...}` 等全局配置入口；
- `\begin{document}` / `\end{document}`；
- `\maketitle`；
- `\input{frontmatter/...}`、`\input{sections/...}`、`\input{appendices/...}`；
- bibliography 入口及比赛模板要求的少量全局命令。

`main.tex` 默认不直接保存：

- 长正文自然段；
- 具体模型推导；
- 大段结果分析；
- 长公式、表格、figure、算法主体；
- 完整摘要正文。

若比赛官方模板强制把特定内容写在主文件，或第三方类文件无法可靠拆分，可保留最小必要例外，并在项目框架中记录原因。

#### 子文件职责

- `config/preamble.tex`：宏包、全局环境、编译相关设置；
- `config/commands.tex`：项目级可复用命令；
- `config/metadata.tex`：题号、队号、标题、成员等元数据；
- `frontmatter/abstract.tex`：摘要与关键词；
- `sections/*.tex`：正文一级语义单元；默认粒度为“一章或一个完整小问一个文件”；
- `appendices/*.tex`：附录与复现说明。

正文子文件不得重新声明 `\documentclass`、`\begin{document}`、`\end{document}`，也不得重复加载全局宏包。跨文件的 equation/figure/table/proposition label 仍处于同一文档命名空间，必须保持全局唯一。

#### 自适应拆分粒度

默认一个一级章节或一个完整小问对应一个 `.tex` 文件，不把每个公式、表格、三级小节机械拆成独立文件。只有当某一小问本身明显过长，且其模型、算法、结果分别形成稳定语义单元时，才允许第二级目录，例如：

```text
sections/q3/
├─ q3.tex
├─ model.tex
├─ algorithm.tex
└─ results.tex
```

其中 `q3.tex` 仅负责编排该问内部子文件。禁止为了形式制造几十个难以维护的碎片文件。

### 2.2 Paper Fragment 到物理文件映射

当项目已启用 `Paper Fragment Dependency Map` 时，写作阶段应为可局部更新的正文 fragment 记录物理文件路径，例如：

```text
abstract      -> final_latex/frontmatter/abstract.tex
q1_model      -> final_latex/sections/06_question1.tex
q2_model      -> final_latex/sections/07_question2.tex
model_review  -> final_latex/sections/09_evaluation.tex
```

模型、参数、约束、算法或结果变化时，先按 `core/writing_reasoning_contract.yaml#paper_fragment_stale_governance` 判断真实依赖，再只修改受影响的 `.tex` 文件。不得因为局部 stale 无差别重写 `main.tex` 或整篇论文。

`abstract.tex` 是高依赖 fragment：它通常同时依赖各问主结果、Numeric Profile、Title Claim 与核心模型表述。任一直接答案变化时，应检查摘要对应句，但不自动判定全部正文 stale。

## 三、编译契约

- CUMCM：XeLaTeX → Biber → XeLaTeX → XeLaTeX；
- MCM/ICM：pdfLaTeX → BibTeX → pdfLaTeX → pdfLaTeX，除非模板明确要求其他引擎；
- 电工杯中文模板：XeLaTeX → Biber → XeLaTeX → XeLaTeX；
- 未知工程无法可靠识别时显式指定 `--profile`；
- 编译统一调用 `scripts/render_paper.py`，必要时先 `--clean`。

模块化工程的 **正式验收始终以 `main.tex` 全量编译为准**。单纯使用 `\input`/`\include` 不应宣传为显著缩短完整编译时间；它的直接收益是源码隔离、局部修改安全、错误定位和 diff 可读性。

允许按需建立局部 preview 工程以加快章节排版迭代，但 preview 只用于视觉与局部语法检查，不能替代正式编译，因为它可能无法覆盖全局编号、跨章节引用、bibliography、目录、浮动体位置和分页。

推荐迭代链：

```text
局部修改 section/abstract
→ 可选局部 preview
→ main.tex 全量 project/prose/BibTeX audit
→ main.tex 全量正式编译
→ PDF 逐页检查
```

## 四、LaTeX 特有排版要求

正文组织不在这里重复，只保留 LaTeX/工程特有要求：

- 关键词按比赛要求设置，中文国赛通常 3--6 个，不以软件名充当关键词；
- 公式、命题、图、表和文献使用可维护的 label/ref/cite 体系；
- 三线表不使用 `resizebox` 粗暴缩小整表字号；
- 图题在下、表题在上；
- MATLAB 图内可保留简洁 `title/sgtitle`，LaTeX `\caption` 负责正式编号和论文语义；
- 正文不放完整代码，完整 Python/MATLAB 放附录或附件；
- 命题正文与短证明使用项目约定环境，呈现规则由 `packs/artifact/proposition_proof.md` 负责；
- `references.bib` 中 citation key 与正文 `\cite{}` 闭合。

## 五、Citation Evidence 与模块化工程检查

单文件旧项目可继续直接运行核心 prose audit：

```bash
python scripts/audit_paper_prose.py final_latex/main.tex --bib final_latex/references.bib --strict
```

模块化工程正式使用项目包装器：

```bash
python scripts/audit_latex_project.py final_latex/main.tex --bib final_latex/references.bib --framework 模型论文框架.md --strict
```

`audit_latex_project.py` 负责递归展开项目内 `\input` / `\include`，执行确定性工程图检查，再把展开后的完整正文委托给 `audit_paper_prose.py` 的现有 prose/structure/BibTeX/framework 审查逻辑。它不是第二套写作规则。

模块化工程应确定性检查：

- `\input` / `\include` 指向的项目内 `.tex` 文件存在；
- 不出现递归 include cycle；
- 子文件不重复声明 `\documentclass` 或 document 环境；
- 全工程不存在 duplicate label；
- 正文 section 文件不是未被入口链引用的孤立文件；
- 跨文件 cite/ref/label 在递归展开后闭合。

允许机器判断：缺失 cite key、重复 bib key、明显未使用 bib 条目、`\nocite{*}` 风险，以及上述确定性模块化工程错误。

禁止机器仅凭 key 存在判断文献是否真的支持某个 claim、标准定理是否适用或来源质量是否足够；这些由写作/终审语义审查完成。

## 六、验收条件

- `.tex` 模块、模板类/样式文件、图片、`.bib`、PDF 和完整最新版 `模型论文框架.md` 均交付；
- `main.tex` 主要承担 orchestration，不回退成大段正文容器；
- 框架通过 `scripts/validate_model_paper_framework.py`；
- 模块化项目由 `audit_latex_project.py` 递归覆盖 `main.tex` 引用的全部当前 `.tex` fragment，且未留下 blocking，未解释的 review_required 已处理；
- 正文核心图表有显式引用并与真实工作簿/MATLAB 来源一致；
- citation key 全部可解析，参考文献数据库无结构性冲突；
- 编译日志无 Error、未定义引用、缺失文献、缺图、字体错误和不可接受的 Overfull box；
- 目录、页码、摘要、命题、图表和附录编号正确；
- CUMCM、MCM/ICM、电工杯模板通过仓库 CI smoke build；
- PDF 逐页检查，正文数值、命题、图表和参考文献与当前框架/工作簿一致。

命题超过默认 0--4 预算、优点/缺点数量关系、简单问题未单列“核心模型汇总”等写作选择不在 Artifact Pack 中重新判定；统一交给 Authority 与终审分级处理。
