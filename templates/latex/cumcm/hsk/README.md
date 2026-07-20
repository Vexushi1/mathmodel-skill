# HSK CUMCM LaTeX Template Add-on

本目录是对原国赛 `cumcmthesis` 模板的增强起稿文件，不替换原模板。

- 原模板保留在：`templates/latex/cumcm/cumcmthesis/`
- HSK 起稿文件：`templates/latex/cumcm/hsk/hsk_main.tex`

使用时建议将 `hsk_main.tex` 复制到项目 `paper/main.tex`，并保持 `cumcmthesis.cls` 可被 LaTeX 搜索到。编译方式：

```bash
latexmk -xelatex main.tex
```
