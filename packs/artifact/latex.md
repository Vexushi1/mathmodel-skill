# Artifact Pack：LaTeX 终稿

本 Pack 只负责 **LaTeX 工程、编译和交付**。正文结构与表达服从 `modules/05_writing/latex.md`，跨竞赛推理、规则等级、Algorithm Trace、命题预算和 Citation Evidence 服从 `core/writing_reasoning_contract.yaml`。本文件不得复制第二套正文规范。

## 一、进入条件

用户要求 LaTeX、可编译终稿、PDF 终稿或从 DOCX 迁移时加载。

进入终稿前：

- `模型论文框架.md` 为 current；
- 当前模型、结果、主要图表和命题状态已锁定；
- 具体数值可追溯到已验收工作簿；
- Citation Evidence 已至少达到可审查状态；
- 需要 `stepwise/pseudocode` 的算法流程已有 current Algorithm Trace；
- stale 内容没有进入当前正文。

## 二、输入与工程契约

- 中文国赛保留 `cumcmthesis` 模板体系；MCM/ICM、电工杯使用对应模板；
- 工程根目录、主文件、图片和文献数据库使用 ASCII 文件名与路径；
- 正式结果图来自标准工作簿与 MATLAB 脚本；
- 当前模型、Algorithm Trace、逐问结果摘要、图表映射、命题和 Citation Evidence 从 `模型论文框架.md` 恢复；
- 摘要、正文、表格和附录的具体数值重新从工作簿复核。

最低工程：

```text
项目根目录/
├─ 模型论文框架.md
└─ final_latex/
   ├─ main.tex
   ├─ references.bib
   ├─ figures/
   ├─ 模板类/样式文件
   └─ 最终 PDF
```

CUMCM 工程使用仓库旧版 `cumcmthesis.cls` 时，`scripts/render_paper.py` 只执行已审计、幂等的字体回退补丁，不改其他模板宏定义。

## 三、编译契约

- CUMCM：XeLaTeX → Biber → XeLaTeX → XeLaTeX；
- MCM/ICM：pdfLaTeX → BibTeX → pdfLaTeX → pdfLaTeX，除非模板明确要求其他引擎；
- 电工杯中文模板：XeLaTeX → Biber → XeLaTeX → XeLaTeX；
- 未知工程无法可靠识别时显式指定 `--profile`；
- 编译统一调用 `scripts/render_paper.py`，必要时先 `--clean`。

## 四、LaTeX 特有排版要求

正文组织不在这里重复，只保留 LaTeX/工程特有要求：

- 关键词按比赛要求设置，中文国赛通常 3--6 个，不以软件名充当关键词；
- 公式、命题、算法、图、表和文献使用可维护的 label/ref/cite 体系；
- 三线表不使用 `resizebox` 粗暴缩小整表字号；
- 图题在下、表题在上；
- MATLAB 图内可保留简洁 `title/sgtitle`，LaTeX `\caption` 负责正式编号和论文语义；
- 正文不放完整代码，完整 Python/MATLAB 放附录或附件；
- 命题正文与短证明使用项目约定环境，呈现规则由 `packs/artifact/proposition_proof.md` 负责；
- `stepwise/pseudocode` 算法流程按 `packs/artifact/algorithm_flow.md` 的按需规则呈现；不为算法框强制引入新宏包，优先复用当前模板已有环境或普通可编译结构；
- `not_needed` 问题不为了版式统一生成空算法环境；
- `references.bib` 中 citation key 与正文 `\cite{}` 闭合。

## 五、Citation Evidence 的工程检查

在编译前运行 prose audit，并对 BibTeX 做确定性检查：

```bash
python scripts/audit_paper_prose.py final_latex/main.tex --bib final_latex/references.bib --strict
```

允许机器判断：缺失 cite key、重复 bib key、明显未使用 bib 条目、`\nocite{*}` 风险。

禁止机器仅凭 key 存在判断文献是否真的支持某个 claim、标准定理是否适用或来源质量是否足够；这些由写作/终审语义审查完成。

## 六、验收条件

- `.tex`、模板类/样式文件、图片、`.bib`、PDF 和完整最新版 `模型论文框架.md` 均交付；
- 框架通过 `scripts/validate_model_paper_framework.py`；
- prose audit 未留下 blocking，未解释的 review_required 已处理；
- 正文核心图表有显式引用并与真实工作簿/MATLAB 来源一致；
- 正式 `stepwise/pseudocode` 算法流程与 current Algorithm Trace、真实 Python 实现和工作簿结果闭合；
- citation key 全部可解析，参考文献数据库无结构性冲突；
- 编译日志无 Error、未定义引用、缺失文献、缺图、字体错误和不可接受的 Overfull box；
- 目录、页码、摘要、命题、算法、图表和附录编号正确；
- CUMCM、MCM/ICM、电工杯模板通过仓库 CI smoke build；
- PDF 逐页检查，正文数值、命题、算法流程、图表和参考文献与当前框架/工作簿一致。

命题超过默认 0--4 预算、算法流程选择 `not_needed`、优点/缺点数量关系、简单问题未单列“核心模型汇总”等写作选择不在 Artifact Pack 中重新判定；统一交给 Authority 与终审分级处理。
