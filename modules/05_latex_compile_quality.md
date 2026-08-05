# Module 05D：LaTeX 编译质量检查

本模块只编译 `ai_cleanup` 输出的已清理 `latex_source`，输出 `compiled_pdf` 与 `compile_report`。

## 工程与配置

- Windows 工程放纯英文路径，项目主文件使用 Profile 的 `project_main`；
- 图片文件名使用英文或拼音；
- 编译链、仓库模板入口和最终项目入口以 `core/compile_profiles.yaml` 为唯一机器可读配置；
- `scripts/render_paper.py --profile <name>` 必须与所用模板一致，不得手工混用引擎和文献工具。

## 竞赛编译链

- CUMCM：XeLaTeX → Biber → XeLaTeX → XeLaTeX，日志应显示 `This is XeTeX`；
- MCM/ICM：pdfLaTeX → BibTeX → pdfLaTeX → pdfLaTeX，除非模板明确改为 XeLaTeX；
- 电工杯中文模板：XeLaTeX → Biber → XeLaTeX → XeLaTeX；
- 未知竞赛先读取模板所用文献宏包与字体方案，再选择最接近的 profile，不得默认套用 CUMCM。

## 字体回退

Times New Roman 缺失时回退 TeX Gyre Termes；SimSun 缺失时回退 FandolSong。代码字体不得强制依赖某一台机器的 CJK 等宽字体。

## 编译故障处理

主文件名、路径、编译引擎变化，或 Biber/BibTeX/书签异常时，删除 `.aux .bcf .bbl .blg .run.xml .out .toc .lof .lot .log .synctex.gz` 后按 profile 完整重编译。

- `fontspec cannot-use-pdftex`：使用了依赖 `fontspec` 的模板，却实际调用 pdfLaTeX；
- `Wide character in die` 或 `.blg Invalid argument`：中文路径、主文件名或 Biber 编码异常；
- `No file main.bbl`、`Citation undefined`：先解决首次 LaTeX 或文献工具报出的首个错误；
- `I couldn't open database file`：检查 `.bib` 文件名、路径和 `\addbibresource`/`\bibliography`；
- `File ended while scanning use of \@writefile` 或书签错误：清理辅助文件并检查标题中的 `% # _ & { }` 与复杂公式。

## 终稿检查

无 Error、未定义引用、缺失文献、缺图、字体错误、Overfull box 和表格越界；目录页码正确；摘要单页；图题在图下、表题在表上；PDF 必须逐页检查。编译命令、profile、主文件和最终 PDF 路径写入 `compile_report` 与复现说明。
