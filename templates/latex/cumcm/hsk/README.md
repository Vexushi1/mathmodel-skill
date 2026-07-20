# HSK CUMCM LaTeX Template Add-on v6.2.2

本目录是对原国赛 `cumcmthesis` 模板的增强起稿文件，不替换原模板。

- 原模板：`templates/latex/cumcm/cumcmthesis/`
- HSK 起稿文件：`templates/latex/cumcm/hsk/hsk_main.tex`
- 参考文献库：`templates/latex/cumcm/hsk/references.bib`

使用时将 `hsk_main.tex` 复制为项目 `final_latex/main.tex`，同时复制 `references.bib`，并确保 `cumcmthesis.cls` 位于可搜索路径。项目路径、主文件名和图片名使用 ASCII。

推荐从仓库根目录执行：

```bash
python scripts/render_paper.py final_latex --profile cumcm --clean
```

实际编译顺序由 `core/compile_profiles.yaml` 控制：

```text
XeLaTeX → Biber → XeLaTeX → XeLaTeX
```

模板中的题号、队伍编号、年份、小问结构和占位语句必须按当届题面修改；内部覆盖表和 QA 检查不得进入终稿。
