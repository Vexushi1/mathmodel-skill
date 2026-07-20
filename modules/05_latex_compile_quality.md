# LaTeX 编译质量规范 v6.2.1

## 工程与引擎

- Windows 工程放纯英文路径，主文件使用 `main.tex`；
- 图片文件名使用英文或拼音；
- 固定编译：XeLaTeX → Biber → XeLaTeX → XeLaTeX；
- 日志必须显示 `This is XeTeX`，不得误用 pdfLaTeX。

## 字体回退

Times New Roman 缺失时回退 TeX Gyre Termes；SimSun 缺失时回退 FandolSong。代码字体不得强制依赖某一台机器的 CJK 等宽字体。

## 编译故障处理

主文件名、路径、编译引擎变化，或 Biber/书签异常时，删除 `.aux .bcf .bbl .blg .run.xml .out .toc .lof .lot .log .synctex.gz` 后完整重编译。

- `fontspec cannot-use-pdftex`：实际调用了 pdfLaTeX；
- `Wide character in die` 或 `.blg Invalid argument`：中文路径/主文件名导致 Biber 编码错误；
- `No file main.bbl`、`Citation undefined`：先解决首个 XeLaTeX/Biber 错误；
- `File ended while scanning use of \@writefile` 或书签错误：清理辅助文件并检查标题特殊字符。

## 终稿检查

无 Error、未定义引用、缺失文献、缺图、字体错误、Overfull box 和表格越界；目录页码正确；摘要单页；图题在图下、表题在表上；PDF 必须逐页检查。
