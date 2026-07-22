# Artifact Pack：LaTeX 终稿

## 进入条件

用户要求 LaTeX、可编译终稿、PDF 终稿或从 DOCX 迁移时加载。进入终稿前，模型口径、核心结果、约束检验、主要图表和参考文献应已锁定。

## 输入契约

- 中文国赛保留 `cumcmthesis` 模板体系；MCM/ICM、电工杯按对应模板；
- 工程根目录、主文件、图片和文献数据库使用 ASCII 文件名与路径；
- 正式结果图必须来自标准工作簿与 MATLAB 脚本；
- 摘要、正文、表格和附录数值必须能追溯到代码输出。

## 工程契约

至少交付：

```text
final_latex/
├─ main.tex
├─ references.bib
├─ figures/
├─ 模板类文件或样式文件
└─ 最终 PDF
```

CUMCM 工程若使用仓库旧版 `cumcmthesis.cls`，通过 `scripts/render_paper.py` 编译时会执行精确、幂等的跨平台字体回退补丁；补丁只替换已审计字体块，不修改其余模板宏定义。

## 编译契约

- CUMCM：XeLaTeX → Biber → XeLaTeX → XeLaTeX；
- MCM/ICM：pdfLaTeX → BibTeX → pdfLaTeX → pdfLaTeX，除非模板明确要求其他引擎；
- 电工杯中文模板：XeLaTeX → Biber → XeLaTeX → XeLaTeX；
- 未知工程无法可靠识别时必须显式指定 `--profile`，不得默认套用 MCM/ICM；
- 编译统一调用 `scripts/render_paper.py`，必要时先 `--clean` 清理辅助文件。

## 内容与排版契约

- 摘要覆盖每问的模型、算法、关键数值和结论，原则上不放图表和复杂公式；
- 关键词 3--6 个，不写软件名；
- 公式、图、表和参考文献交叉引用闭合；
- 三线表不以 `resizebox` 粗暴缩小字号；
- 图题在下、表题在上，图内不重复总标题；
- 正文不放完整代码，复杂算法用必要伪代码，完整代码放附录或附件；
- 执行 `modules/05_writing/ai_cleanup.md` 删除无证据判断和模板化套话。

## 验收条件

- `.tex`、模板类文件、图片、`.bib` 和 PDF 均交付，不只交 PDF；
- 编译日志无 Error、未定义引用、缺失文献、缺图、字体错误和不可接受的 Overfull box；
- 目录、页码、摘要分页、图表位置和附录编号正确；
- CUMCM、MCM/ICM、电工杯模板通过仓库 CI smoke build；
- PDF 逐页检查，正文数值与工作簿、图表和附录一致。
