# HSK CUMCM LaTeX Template Add-on

本目录是对原国赛 `cumcmthesis` 模板的增强起稿工程，不替换原模板。

- 原模板：`templates/latex/cumcm/cumcmthesis/`
- HSK 主入口：`templates/latex/cumcm/hsk/hsk_main.tex`
- 全局配置：`config/`
- 摘要：`frontmatter/abstract.tex`
- 正文章节：`sections/`
- 附录：`appendices/`
- 参考文献库：`references.bib`

## 模块化源码约定

`hsk_main.tex` 只承担编排，不再保存大段正文。正式项目中推荐复制整个 `hsk/` 模板内容到 `final_latex/`，再将 `hsk_main.tex` 重命名为 `main.tex`。不要只复制单个主文件，否则 `\input{...}` 引用的模块会缺失。

默认结构：

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

每个一级章节或完整小问默认对应一个 `.tex` 文件；只有单问确实很长时再二级拆分，避免碎片化。`preprocessing_decision=not_needed` 时删除 `main.tex` 中对 `sections/05_data.tex` 的调用；`question_local` 时通常也不保留公共数据预处理章。

正文子文件不得声明 `\documentclass`、`\begin{document}` 或 `\end{document}`，也不得重复加载全局宏包。公式、图、表、命题的 label 在整个工程内必须唯一，跨文件 `\ref` / `\eqref` / `\cite` 按同一文档处理。

项目路径、主文件名和图片名使用 ASCII，并确保 `cumcmthesis.cls` 位于可搜索路径。

推荐从仓库根目录执行：

```bash
python scripts/audit_paper_prose.py final_latex/main.tex --bib final_latex/references.bib --strict
python scripts/render_paper.py final_latex --profile cumcm --clean
```

`audit_paper_prose.py` 应递归展开 `main.tex` 引用的项目内 `.tex` 模块后审查全文。完整编译仍以 `main.tex` 为唯一正式入口；模块化的主要收益是局部修改安全、错误定位和 diff 可读性，不等同于完整编译必然显著提速。

实际编译顺序由 `core/compile_profiles.yaml` 控制：

```text
XeLaTeX → Biber → XeLaTeX → XeLaTeX
```

模板中的题号、队伍编号、年份、小问结构和占位语句必须按当届题面修改；内部覆盖表和 QA 检查不得进入终稿。
