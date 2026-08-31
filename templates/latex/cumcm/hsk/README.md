# HSK CUMCM LaTeX Template Authority

本目录从 v8.0.0 起承担 **CUMCM HSK 论文结构与 LaTeX 渲染的 Template Authority**。模板决定论文固定骨架、一级章节顺序、问题章节一级标题、LaTeX 工程组织和确定性渲染方式；Writing Skill 只负责数学叙事、公式承接、求解说明、结果解释和验证表达，不再重复维护模板已经能够确定的结构。

- Template Manifest：`template_manifest.yaml`
- HSK 主入口：`hsk_main.tex`
- 原 `cumcmthesis` 资源：`../cumcmthesis/`
- 全局配置：`config/`
- 摘要：`frontmatter/abstract.tex`
- 正文章节：`sections/`
- 附录：`appendices/`
- 参考文献库：`references.bib`

> v8.0.0 Phase 1 先以仓库当前模块化 HSK 工程作为 canonical executable template。用户提供的单文件参考模板必须在原文件可读取并完成逐项核对后再导入 reference exemplar；不得根据记忆或旧版本猜测其内容。

## 1. Template 与 Writing Skill 的边界

Template Authority 可以规定：

- `documentclass`、全局宏包与 LaTeX 环境；
- 一级论文骨架和一级章节顺序；
- CUMCM 问题章节一级标题 `问题X模型建立及求解`；
- `main.tex` 的编排与正文子文件位置；
- 图、表、公式、命题、算法、参考文献和附录的渲染接口；
- 复杂优化模型中 objective 与 constraints 的确定性展示示例。

Template Authority **不可以**规定：

- 当前题目采用什么模型、solver 或 validator；
- 当前公式、参数、结果和验证证据；
- 每个问题必须使用哪些固定二级标题；
- 简单问题必须设置算法、核心模型汇总或验证小节；
- 为达到目标页数而增加无技术作用的正文。

Writing Skill 负责上述数学与论证内容，项目事实继续由当前 `模型论文框架.md`、真实工作簿和图表证据提供。

## 2. 模块化源码约定

`hsk_main.tex` 只承担编排，不保存大段正文。正式项目中推荐复制整个 `hsk/` 模板内容到 `final_latex/`，再将 `hsk_main.tex` 重命名为 `main.tex`。不要只复制单个主文件，否则 `\input{...}` 引用的模块会缺失。

默认工程结构：

```text
final_latex/
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
│  ├─ 05_data.tex
│  ├─ 06_question1.tex
│  └─ ...
├─ appendices/
│  └─ appendices.tex
└─ references.bib
```

固定一级骨架由 `template_manifest.yaml` 定义。`05_data.tex` 是条件插槽；`preprocessing_decision=not_needed` 时删除 `main.tex` 中对应调用，`question_local` 时通常也不保留公共数据预处理章。共享基础模型只有在两问及以上确实共享实质核心结构时才插入，不因模板对称强制建立。

每个一级章节或完整小问默认对应一个 `.tex` 文件；只有单问确实很长时再二级拆分，避免碎片化。问题章节的一级标题保持 `问题X模型建立及求解`，但内部 MODEL / SOLVE / RESULT / VALIDATE 是功能槽而不是固定标题，复杂问可使用更专业的题目专属二级标题，简单问可合并非必要槽位。

## 3. 核心模型收束的模板语义

“核心模型汇总”从 v8.0.0 起是 rendering mode，不是默认独立二级标题。

复杂优化模型在模型建立末尾通常先单独展示目标函数：

```latex
\begin{equation}
    \min_{\mathbf{x}} f(\mathbf{x})
\end{equation}
```

再单独展示约束：

```latex
\begin{equation}
\text{s.t.}\quad
\left\{
\begin{aligned}
    g_i(\mathbf{x}) &\le 0,\\
    h_j(\mathbf{x}) &= 0,\\
    \mathbf{x} &\in \Omega.
\end{aligned}
\right.
\end{equation}
```

目标函数不得放入约束大括号。非优化、多方程、状态空间或简单解析问题必须按真实数学结构改写，不能为了保留示例而伪造 objective / constraints。

## 4. LaTeX 工程规则

正文子文件不得声明 `\documentclass`、`\begin{document}` 或 `\end{document}`，也不得重复加载全局宏包。公式、图、表、命题的 label 在整个工程内必须唯一，跨文件 `\ref` / `\eqref` / `\cite` 按同一文档处理。

所有 `\input` / `\include` 路径统一相对于 `main.tex` 所在工程根目录书写。例如 `sections/q3/q3.tex` 引用同目录模型文件时，应写 `\input{sections/q3/model}`，不要写 `\input{model}`。审计器与正式编译使用同一根目录口径。

项目路径、主文件名和图片名使用 ASCII，并确保 `cumcmthesis.cls` 位于可搜索路径。

## 5. 审计与编译

推荐从仓库根目录执行：

```bash
python scripts/validate_template_manifest.py templates/latex/cumcm/hsk/template_manifest.yaml
python scripts/audit_latex_project.py final_latex/main.tex --bib final_latex/references.bib --framework 模型论文框架.md --strict
python scripts/render_paper.py final_latex --profile cumcm --clean
```

`validate_template_manifest.py` 只检查 Template Manifest 与仓库模板之间的确定性同步关系，不判断数学模型、solver、验证或正文质量。`audit_latex_project.py` 继续负责工程、交叉引用和 prose audit。

实际编译顺序由 `core/compile_profiles.yaml` 控制：

```text
XeLaTeX → Biber → XeLaTeX → XeLaTeX
```

模板中的题号、队伍编号、年份和具体小问数量必须按当届题面修改；内部覆盖表、项目状态术语和 QA 检查不得进入终稿。
