---
name: mathmodel-skill
description: HSK DOCX-draft + LaTeX-final mathematical modeling competition workflow for CUMCM/MCM/ICM/Diangong/认证杯等. Use when assisting with 建模、数模、国赛、CUMCM、美赛、MCM、ICM、电工杯、认证杯、竞赛论文、逐字审题、模型选择、代码复现、SCI图表、LaTeX论文写作、cumcmthesis模板、敏感性分析、鲁棒性分析或终稿审查.
---


## v6.1.6-ai-cleanup 追加修正：AI 模板感清除终稿硬规则

本次追加终稿写作硬规则：终稿阶段必须清除 AI 模板感，删除空泛套话、无证据支撑的优越性表达、冗余模板表、装饰性流程图和不能反向定位到结果证据的结论句；将“效果较好”“显著提高”等表述改为具体误差、排名、提升率、稳定性指标、约束违反量或鲁棒性结果。详见 `PROJECT_INSTRUCTIONS_HSK_V616.md`、`HSK_SKILL_RUNTIME_CORE_V616.md`、`references/hsk_stage_10_latex_final_writing.md` 和 `references/hsk_stage_11_review_panel.md`。

## v6.1.6-docxlayout 追加修正：DOCX 论文排版与图文证据链硬约束

本次追加了 Word 论文返修中高频踩坑的硬性规则：表格必须为 Word 原生三线表，图题只写图号和图名，图后解释另起正文段并整合为一个自然段，公式必须居中编号，摘要必须分段写入核心数值，参考文献、附录必须分页；若设置致谢，致谢应单独分页，完整代码放附录且每份代码前必须有说明表。详见 `references/hsk_docx_paper_layout_protocol.md`。

## v6.1.6 核心流程修正：DOCX 草稿 + LaTeX 终稿 + 机理图前置占位后期精修

本版本将工作流从“前期直接 LaTeX 精修、机理图即时绘制”调整为“前期 DOCX 草稿快速闭合逻辑、机理图合同与占位先行、结果稳定后统一精修少量核心机理图、最终 LaTeX 成稿提交”。

执行顺序：审题 → 模型路线 → 变量公式 → 机理图合同与图位占坑 → 代码求解 → 结果图和鲁棒性 → DOCX 草稿 → 后期 SVG/PPT/GeoGebra 精修核心机理图 → LaTeX 终稿 → 评委式审查。

机理图不要求每问单独保留一张；每问必须有机制解释或引用已有机理图合同。全文核心机理图通常控制在 3--6 张，优先保留 S 级图：题目对象抽象、核心公式来源、关键约束机制和临界状态判断。

新增机理图实战判定法：绘图前先回答图前六问，S 级图必须绑定核心公式或约束；通用流程图、无题目对象的算法流程图、无变量装饰图和几何关系不精确的 AI 自动图，不得作为核心机理图。



# mathmodel-skill — HSK DOCX 草稿 + LaTeX 终稿数学建模冲奖工作流 (v6.1.6-hsk-docxdraft-latexfinal-mechanism-nature-ponytail)

> 本版本是面向数学建模竞赛的 HSK DOCX-draft + LaTeX-final 分支。它保留国赛 `cumcmthesis` 模板，并将默认输出聚焦为“逐字审题、模型路线比较、变量闭环、代码复现、人工思考证据、SCI 图表、DOCX 草稿、LaTeX 终稿、评委式终审”。

## HSK Workflow Override（最高优先级）

凡任务涉及数学建模竞赛、模型框架、代码、图表、论文、摘要、LaTeX、国赛模板、答辩或终稿审查，必须优先读取并执行：

- `profiles/hsk_latex_workflow.md`
- `config/hsk_output_contract.json`
- `config/hsk_rubric_weights.json`

若 HSK profile 与其他通用流程重复，采用更清晰、更容易执行的一种表达；若冲突，以 HSK profile 为准。

### 关键改造点

1. **DOCX-draft + LaTeX-final**：最终论文默认使用 LaTeX；中文国赛论文默认基于 `templates/latex/cumcm/cumcmthesis/`。
2. **国赛模板保留**：不得删除或替换 `cumcmthesis.cls`、`example.tex`、`example.pdf`。新增 HSK 起稿文件位于 `templates/latex/cumcm/hsk/hsk_main.tex`。
3. **内部覆盖检查，不强制入文**：必须内部检查题目要求是否遗漏，但不强制在论文正文放“题目要求—论文位置”表。
4. **少问、强推进**：不再机械执行全程问答式。信息足够时直接推进；只有关键歧义会影响建模方向时才提问。
5. **先审题后代码**：默认先完成题目理解、路线比较、数据协议、变量假设和公式框架，再输出正式代码。用户明确要求代码时可直接给，但必须提示缺失风险。
6. **每问双路线**：每个小问至少给“经典稳健模型 + 本题改进”和“高级创新/融合模型”两类方案，并比较适配性、数据支撑、局限性、误差来源、求解难度和推荐等级。
7. **模型否决机制**：数据不支撑、变量不闭环、计算不可行、无法解释、无法检验、无法复现的模型必须否决或降级。
8. **代码复现协议**：代码必须包含路径配置、字段检查、空值检查、维度检查、异常处理、特征构造、模型求解、约束违反检查、结果保存和图表输出。
9. **代码精壮协议**：输出求解代码前先闭合模型求解逻辑；库优先，不手搓成熟库已有功能；禁止几千行大而全代码；只保留可复现主链路与必要检查，并遵守脚本/函数规模红线。
10. **中文结果输出协议**：数值结果、灵敏度数据、多算法对比数据统一输出到 `data_output/problemX/数据结果/`；数据文件名使用中文，例如 `问题一最优解.csv`、`问题三灵敏度分析.csv`、`问题五多算法对比.xlsx`；表格内部字段名默认英文。每问图表默认输出到 `data_output/problemX/图表/`，图像文件建议使用英文或拼音文件名。
11. **交付闭环协议**：默认维护约束违反检查和必要数据审计日志；`result_manifest.yaml` 与 `run_info.json` 仅在完整复现包、多算法大量结果、跨聊天交接、终稿审查或用户明确要求时生成，并检查摘要、公式、图表是否与代码和结果文件闭合。
12. **高级模型准入协议**：高级模型必须说明必要性、变量闭环、数据支撑和计算可行性；不满足则否决或降级。
13. **人工思考证据层**：每个核心问题优先配套机理图、几何推导图、临界状态图或结构示意图，用于说明题目对象关系、模型选择理由、关键公式来源和约束成立机制。
14. **图表协议**：默认 Nature/Science/SCI 风格；中文标签；文件名英文；核心图导出 PNG + PDF/SVG；吸收 Nature 图表契约、参考图谱、配色体系和 QA 检查。
15. **终稿评委式审查**：检查审题遗漏、模型堆砌、公式断裂、数据不支撑、代码不可复现、图表低级、敏感性/鲁棒性不足、LaTeX 编译问题。
16. **AI 模板感清除**：终稿阶段必须删除空泛套话、无证据支撑的优越性表述、冗余模板表、装饰图和通用流程图；将“效果较好”“显著提高”等表述改为具体误差、排名、提升率、稳定性指标、约束违反量或鲁棒性结果。

### HSK 阶段文件

日常执行优先读取运行核心文件；下列阶段文件用于需要深度展开时补充。原 `references/stage_*.md` 保留为通用备用资料。

| 阶段 | HSK reference |
|---|---|
| 任务接入 | `references/hsk_stage_00_task_intake.md` |
| 逐字审题 | `references/hsk_stage_01_problem_audit.md` |
| 路线比较 | `references/hsk_stage_02_model_route_compare.md` |
| 数据协议 | `references/hsk_stage_03_data_protocol.md` |
| 公式闭环 | `references/hsk_stage_04_formula_closure.md` |
| 机理图合同与占位 | `references/hsk_stage_05_figure_contract_placeholder.md` |
| 代码协议 | `references/hsk_stage_06_code_protocol.md` + `references/hsk_ponytail_code_protocol.md` |
| 结果图表协议 | `references/hsk_stage_07_visualization_protocol.md` + `references/hsk_nature_figure_protocol.md` |
| DOCX 草稿写作 | `references/hsk_stage_08_docx_draft_writing.md` |
| 后期机理图精修 | `references/hsk_stage_09_mechanism_figure_protocol.md` |
| LaTeX 终稿写作 | `references/hsk_stage_10_latex_final_writing.md` / `references/hsk_stage_10_latex_writing_compat.md` |
| 终稿审查 | `references/hsk_stage_11_review_panel.md` |
| 提交检查 | `references/hsk_stage_12_submission_checklist.md` |

### HSK 模板与脚本

- 内部题目覆盖检查：`templates/shared/hsk_requirement_coverage_checklist.md`
- 建模路线比较：`templates/shared/hsk_model_route_compare_table.md`
- 数据字段审计：`templates/shared/hsk_data_schema_audit_table.md`
- 图表规划：`templates/shared/hsk_figure_plan_table.md`
- 代码起手模板：`templates/shared/code_starter_hsk/`
- 国赛 LaTeX 起稿：`templates/latex/cumcm/hsk/hsk_main.tex`
- 产物检查：`scripts/hsk_check_artifact.py`
- 提交备份打包：`scripts/hsk_pack_submission.py`

### 交付闭环增强：代码精壮 + 中文结果输出

本分支强化交付闭环能力：约束检查、代码红线、异常分级、摘要反推、公式代码闭环、图表入文检查、题型路线索引、高级模型准入、LaTeX 编译测试和代码模板 smoke test。正式图表由 HSK 图表协议管理，保持 `data_output/problemX/数据结果/` 到 `data_output/problemX/图表/` 再到正文引用的可复现链路；`run_info.json` 和 `result_manifest.yaml` 仅在完整复现包、多算法大量结果、跨聊天交接、终稿审查或用户明确要求时生成。

代码输出必须满足：

1. **模型先行**：先明确决策变量、状态变量、目标函数、约束和求解器，再写代码。
2. **库优先**：线性规划、非线性规划、机器学习、统计检验、图论、插值拟合等优先调用成熟库；不得无理由手写低质量替代实现。
3. **拒绝大而全**：不输出几千行工具箱式代码；每个脚本服务一个清晰问题，主函数串联数据读取、清洗、建模、求解、检验、保存。
4. **检查不可删**：字段、空值、维度、随机种子、异常处理、约束违反、结果保存必须保留。
5. **中文结果文件名**：所有用于论文表格、结果复核、灵敏度分析和多算法对比的数据文件统一写入 `data_output/problemX/数据结果/`，并使用中文文件名；表格内部字段名默认英文。
6. **图表分问输出**：每问论文图默认写入 `data_output/problemX/图表/`；LaTeX 终稿阶段可复制最终入文图到 `final_latex/figures/` 或模板要求目录。
7. **结果总清单**：`result_manifest.yaml` 默认不强制生成，仅在完整复现包、多算法大量结果、跨聊天交接、终稿审查或用户明确要求时生成。
8. **运行元数据**：`run_info.json` 默认不强制生成，仅在完整复现包、多算法大量结果、跨聊天交接、终稿审查或用户明确要求时生成。
9. **约束检查**：优化类模型必须输出标准约束违反检查表。
10. **代码红线**：单脚本、单函数、函数参数、调试输出、未使用 import 均按精壮规则控制。
11. **异常分级**：数据和运行问题分为 Error / Warning / Info。
12. **摘要反推**：摘要必须覆盖每问方法、核心数值和结论。
13. **公式代码闭环**：核心公式必须能回溯到代码变量或函数。
14. **图表入文检查**：核心图表必须有数据来源、代码来源、正文解释和结论支撑。
15. **题型路线索引**：路线比较可参考 `references/hsk_model_route_index.md`。
16. **高级模型准入**：高级模型必须通过 `references/hsk_advanced_model_gatekeeping.md`。
17. **模板测试**：新增 LaTeX 编译检查和 code starter smoke test。

### 人工思考证据层：机理图与几何推导图

本分支新增 `references/hsk_stage_09_mechanism_figure_protocol.md`，用于补足 AI 论文常见的“结果精确但缺少人为思考过程”问题。它与 Nature/SCI 图表协议并行：Nature/SCI 图表负责结果证据和审美，机理/推导图负责说明题目对象、建模理由和公式来源。

执行要求：

1. 每个核心问题原则上至少规划一张本题专属的机理图、几何推导图、临界状态图或结构示意图。
2. 几何、物理、运动、碰撞、遮挡、路径、调度、资源分配、博弈和工程策略类题目必须优先执行该协议。
3. 每张机理/推导图必须回答一个建模疑问，例如“为什么不能把目标看成点”“为什么只需判断边界”“为什么采用该约束”“为什么该临界值成立”。
4. 图中符号必须与变量表和正文公式一致，并能对应到至少一个公式、约束、假设、代码函数或结果文件。
5. 正文必须写出“由图可见……因此……”的推理句，禁止只有通用算法流程图和模板化模型描述。
6. AI 可以辅助规范化绘图和图注，但题意拆解、模型取舍、关键机制和临界判断必须由人主导。

新增文件：

- `references/hsk_stage_09_mechanism_figure_protocol.md`
- `templates/shared/hsk_mechanism_figure_contract.md`
- `templates/shared/hsk_mechanism_figure_qa_checklist.md`
- `templates/shared/hsk_per_question_mechanism_plan_table.md`


### Nature / SCI 图表增强

本分支选择性吸收 `nature-figure` 的图表生产思想，只强化 HSK Stage 06 可视化，不改变数学建模主流程。

吸收内容：

1. **图表契约**：每张核心图先明确 core conclusion、figure role、panel map、source data、plot code 和 reviewer risk。
2. **证据层级**：优先 hero panel + 支撑面板，删除不能支撑独立证据的装饰性面板。
3. **参考图谱**：内置 `assets/nature_figure/chart-atlas/` 与 `assets/nature_figure/gallery/`，用于选择图表类型和版式。
4. **Nature 配色**：提供低饱和、语义一致的蓝/绿/红/灰/青/紫配色和 NMI pastel family。
5. **Python 样式模板**：新增 `templates/shared/hsk_nature_style.py`，支持可编辑 SVG/PDF、panel label、语义配色和统一导出。
6. **导出规范**：核心图默认 PDF + PNG，推荐 SVG，可选 600 dpi TIFF。
7. **图表 QA**：新增 `templates/shared/hsk_nature_figure_contract.md` 和 `templates/shared/hsk_nature_figure_qa_checklist.md`。

执行边界：

- 只强化图表证据、版式、配色、导出和 QA；
- 默认使用 Python / MATLAB 进行可复现绘图；用户明确要求其他工具时再切换；
- 不为图表美观牺牲题意、可复现和结果闭环。

---


### v6.1.6 代码增强：Ponytail 代码精简与反过度工程协议

本版本选择性吸收 `ponytail` 与 `ponytail-review`，只强化 Stage 06 代码实现与代码审查，不改变 HSK 主工作流。

执行边界：

- 吸收：标准库优先、成熟库优先、不新增无必要依赖、删除投机抽象、bug 修根因、非平凡逻辑保留最小检查、代码瘦身审查输出 `net: -N lines possible`。
- 不吸收：不让 Ponytail 成为每个回答的最高规则，不使用 ultra 模式作为数学建模默认，不压缩审题、模型、公式、数据审计、图表证据和论文闭环。
- 不得删除：`data_output/` 中文结果、图表输出、约束违反检查、公式—代码闭环、核心绘图代码；若本次任务已启用 `run_info.json` 或 `result_manifest.yaml`，则不得删除。

新增文件：

- `references/hsk_ponytail_code_protocol.md`
- `templates/shared/hsk_ponytail_code_slimming_checklist.md`
- `HSK_PONYTAIL_CODE_REPORT.md`
