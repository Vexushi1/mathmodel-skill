# AGENTS.md — HSK 数学建模工作流入口

本文件是 agentic CLI / workspace 的项目级补充说明。完整工作流以 `SKILL.md`、`profiles/hsk_latex_workflow.md` 和项目来源指令为准。

## 执行优先级

1. 数学建模相关任务先读取 `SKILL.md`。
2. 再加载 `profiles/hsk_latex_workflow.md`，并将其视为最高优先级工作流。
3. 若本文件与 HSK 主工作流冲突，以 HSK 主工作流为准。

## 当前主线

当前版本为 `mathmodel-skill-6.1.6-hsk-docxdraft-latexfinal-mechanism-nature-ponytail`。

主线包括：

- HSK DOCX 草稿 + LaTeX 终稿数学建模冲奖工作流；
- 机理图合同、图位占坑与后期核心图精修；
- Nature / SCI 图表证据增强；
- Ponytail 代码精简与反过度工程增强。

执行边界：DOCX 草稿只服务前期阅读、修改和逻辑审查，最终论文仍默认 LaTeX；机理/推导图只强化人工思考证据和建模解释；Nature / SCI 只强化图表质量；Ponytail 只强化代码质量。以上增强都不能替代审题、建模、变量、假设、公式、数据审计、结果解释和论文闭环。

## 工作方式

- 信息足够时直接推进，不机械追问。
- 关键歧义会影响模型方向、数据口径或交付结果时，再向用户确认。
- 所有建模任务按 HSK v6.1.6 阶段流推进：任务接入、逐字审题、路线比较、数据协议、公式闭环、机理图合同与占位、代码协议、结果图表、DOCX 草稿、核心机理图后期精修、LaTeX 终稿、评委式终审与提交检查。

## 产物要求



## DOCX 论文排版额外执行规则

当任务涉及 DOCX 论文初稿、Word 返修或用户上传已修改 DOCX 后继续加工时，除 HSK 主工作流外，必须读取并执行 `references/hsk_docx_paper_layout_protocol.md`。尤其要保证：以用户最后上传的 DOCX 为底稿；表格是真表格且为三线表；图题和图后解释分离；公式居中编号；摘要分段；参考文献、附录分页；如设置致谢，致谢单独分页；正文放伪代码，完整代码放附录并配代码说明表。
- 前期论文草稿可优先 DOCX；最终论文默认 LaTeX；中文国赛默认保留 `cumcmthesis` 模板。
- 结果数据统一进入 `data_output/`。
- 结果图统一进入 `figures/`。
- 可编辑机理图建议进入 `figures_editable/`。
- DOCX 草稿建议进入 `draft_docx/`，LaTeX 终稿建议进入 `final_latex/`。
- 核心运行维护 `run_info.json` 与 `result_manifest.yaml`。
- 优化、仿真、调度、路径和机理模型必须输出约束违反检查，除非明确不适用。
