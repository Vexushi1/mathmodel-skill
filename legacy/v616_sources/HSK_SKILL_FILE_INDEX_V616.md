# HSK Skill File Index v6.1.6

本文件用于放入 ChatGPT 项目“来源”，帮助模型快速理解完整压缩包 `mathmodel-skill-6.1.6-hsk-docxdraft-latexfinal-mechanism-nature-ponytail.zip` 的文件结构。zip 用于完整归档；本索引用于快速检索。

## 1. 顶层文件

| 文件 | 用途 |
|---|---|
| `SKILL.md` | skill 总入口，描述整体能力、竞赛支持、DOCX 草稿 + LaTeX 终稿工作流和 v6.1.6 增强规则 |
| `AGENTS.md` | 代理执行规则，说明怎样按 HSK 工作流操作 |
| `README.md` | 项目说明、目录结构、使用方式 |
| `PROJECT_INSTRUCTIONS_HSK_V616.md` | 项目来源指令，优先级最高 |
| `HSK_SKILL_RUNTIME_CORE_V616.md` | 运行核心规则，适合作为来源快速读取 |
| `HSK_COMMON_TEMPLATES_V616.md` | 常用模板，含机理图合同、图位占坑、DOCX 草稿检查和 AI 模板感清除检查表 |
| `HSK_SKILL_FILE_INDEX_V616.md` | 当前文件索引 |
| `HSK_V6_1_6_DOCXDRAFT_LATEXFINAL_REPORT.md` | v6.1.6 修改报告 |
| `HSK_MODIFICATION_REPORT.md` | HSK 改造说明，已更新至 v6.1.6 主线 |
| `HSK_PONYTAIL_CODE_REPORT.md` | Ponytail 代码精简、反过度工程和代码瘦身审查 |

## 2. HSK 最高优先级 profile

| 文件 | 用途 |
|---|---|
| `profiles/hsk_latex_workflow.md` | HSK 主工作流。v6.1.6 中实际执行为 DOCX 草稿 + LaTeX 终稿，但保留该路径以兼容旧引用 |

核心内容：逐字审题、每问双路线、变量闭环、数据审计、机理图合同与占位、DOCX 草稿、代码复现、代码精壮、结果图表、后期核心机理图精修、LaTeX 终稿、评委式终审。

## 3. HSK 阶段文件

| 文件 | 用途 |
|---|---|
| `references/hsk_stage_00_task_intake.md` | 任务接入，明确竞赛、题目、附件、交付目标 |
| `references/hsk_stage_01_problem_audit.md` | 逐字审题，拆解题目要求、隐含约束和输出结果 |
| `references/hsk_stage_02_model_route_compare.md` | 每问模型路线比较：经典稳健 + 高级创新 |
| `references/hsk_stage_03_data_protocol.md` | 数据字段、单位、粒度、关联键、缺失异常审计 |
| `references/hsk_stage_04_formula_closure.md` | 变量、假设、目标函数、约束、指标闭环 |
| `references/hsk_stage_05_figure_contract_placeholder.md` | 机理图合同、图位占坑、图表分级、正文机制解释预埋 |
| `references/hsk_stage_06_code_protocol.md` | 代码实现协议：精壮代码、中文输出、运行元数据、约束检查，集成 Ponytail 增强 |
| `references/hsk_stage_07_visualization_protocol.md` | 结果图协议：论文图、数据来源、图表入文闭环，集成 Nature / SCI 图表增强 |
| `references/hsk_stage_08_docx_draft_writing.md` | DOCX 草稿论文协议，用于前期浏览、修改和逻辑审查 |
| `references/hsk_docx_paper_layout_protocol.md` | DOCX 论文草稿排版与图文证据链硬规则：原生三线表、图题与解释分离、公式居中编号、摘要分段、附录代码说明 |
| `references/hsk_stage_09_mechanism_figure_protocol.md` | 后期核心机理图筛选、精修和图—公式—正文闭环 |
| `references/hsk_stage_10_latex_final_writing.md` | LaTeX 终稿论文协议 |
| `references/hsk_stage_10_latex_writing_compat.md` | LaTeX 写作兼容入口 |
| `references/hsk_stage_11_review_panel.md` | 评委式终审、逻辑回溯和质量打分 |
| `references/hsk_stage_12_submission_checklist.md` | 提交包检查：论文、代码、数据、图表、附录 |

说明：Stage 文件已按执行顺序一次性重命名为 `hsk_stage_00` 至 `hsk_stage_12`，不再保留 `06a`、`07a`、`07b` 等插入编号。

## 4. 当前增强参考文件

| 文件 | 用途 |
|---|---|
| `references/hsk_model_route_index.md` | 题型—模型路线索引：预测、评价、优化、机理、分类、聚类、图论、空间、不确定性 |
| `references/hsk_advanced_model_gatekeeping.md` | 高级模型准入规则：W-DRO、CVaR、MPEC、Stackelberg、GNN、空间杜宾、DML 等 |
| `references/hsk_stage_09_mechanism_figure_protocol.md` | 机理/推导图协议，v6.1.6 强调前期合同与后期精修 |
| `references/hsk_mechanism_practical_decision_method.md` | 机理图实战判定法：五类图、图前六问、公式/约束绑定和负面清单 |
| `references/hsk_nature_figure_protocol.md` | Nature/SCI 图表契约、证据层级、配色、导出和 QA 规则 |
| `references/hsk_nature_chart_atlas.md` | 参考图表图谱索引，连接 chart-atlas 与 gallery 示例图 |
| `references/hsk_ponytail_code_protocol.md` | Ponytail 代码精简与反过度工程协议，只强化代码阶段 |

## 5. HSK 常用检查模板

| 文件 | 用途 |
|---|---|
| `templates/shared/hsk_requirement_coverage_checklist.md` | 题目要求覆盖检查 |
| `templates/shared/hsk_model_route_compare_table.md` | 模型路线比较表 |
| `templates/shared/hsk_variable_table.md` | 变量分类表 |
| `templates/shared/hsk_assumption_audit_table.md` | 假设审计表 |
| `templates/shared/hsk_data_schema_audit_table.md` | 数据字段审计表 |
| `templates/shared/hsk_mechanism_placeholder_contract.md` | 机理图合同与占位模板 |
| `templates/shared/hsk_docx_draft_checklist.md` | DOCX 草稿检查表 |
| `templates/shared/hsk_docx_layout_checklist.md` | DOCX 排版与图文证据链检查表 |
| `templates/shared/hsk_code_appendix_description_table.md` | 附录代码说明表与正文伪代码模板 |
| `templates/shared/hsk_caption_explanation_template.md` | 图题、表题和图后正文解释模板 |
| `templates/shared/hsk_per_question_mechanism_plan_table.md` | 每问机理/推导图规划表 |
| `templates/shared/hsk_mechanism_figure_contract.md` | 机理/推导图 figure contract 模板 |
| `templates/shared/hsk_mechanism_figure_qa_checklist.md` | 机理/推导图 QA 检查表 |
| `templates/shared/hsk_mechanism_practical_checklist.md` | 机理图实战判定检查表：图前六问、五类图判定和负面清单 |
| `templates/shared/hsk_figure_plan_table.md` | 图表规划表 |
| `templates/shared/hsk_robustness_check_table.md` | 鲁棒性检查表 |
| `templates/shared/hsk_result_manifest.yaml` | 结果总清单模板，绑定输出文件、论文位置、图表来源 |
| `templates/shared/hsk_constraint_violation_check_table.md` | 约束违反检查表 |
| `templates/shared/hsk_abstract_result_checklist.md` | 摘要核心结果反推检查表 |
| `templates/shared/hsk_formula_code_closure_table.md` | 公式—代码闭环检查表 |
| `templates/shared/hsk_figure_paper_check_table.md` | 图表入文检查表 |
| `templates/shared/hsk_nature_figure_contract.md` | Nature/SCI 核心图 figure contract 模板 |
| `templates/shared/hsk_nature_figure_qa_checklist.md` | Nature/SCI 图表质量 QA 检查表 |
| `HSK_COMMON_TEMPLATES_V616.md#26` | AI 模板感清除检查表：删除空泛套话、无证据结论、冗余模板表和装饰图 |
| `templates/shared/hsk_ponytail_code_slimming_checklist.md` | 代码瘦身与反过度工程审查表 |

## 6. 代码与可视化模板

| 文件/目录 | 用途 |
|---|---|
| `templates/shared/code_starter/optimization.py` | 优化题代码模板 |
| `templates/shared/code_starter/prediction.py` | 预测题代码模板 |
| `templates/shared/code_starter/evaluation.py` | 评价题代码模板 |
| `templates/shared/code_starter/classification.py` | 分类题代码模板 |
| `templates/shared/code_starter/simulation.py` | 仿真题代码模板 |
| `templates/shared/code_starter_hsk/main_pipeline.py` | HSK 主链路代码骨架：读取、检查、求解、保存、绘图 |
| `templates/shared/code_starter_hsk/config.yaml` | HSK 代码配置模板 |
| `templates/shared/code_starter_hsk/visualization_style.py` | 可复现绘图风格模板 |
| `templates/shared/hsk_nature_style.py` | Nature / SCI 风格 Matplotlib 辅助函数 |
| `templates/shared/requirements.txt` | Python 依赖建议 |

## 7. LaTeX 与论文模板

| 文件/目录 | 用途 |
|---|---|
| `templates/latex/cumcm/cumcmthesis/` | 国赛 `cumcmthesis` 原模板，必须保留 |
| `templates/latex/cumcm/hsk/hsk_main.tex` | HSK 国赛 LaTeX 起稿文件 |
| `templates/latex/mcm/main.tex` | MCM/ICM 英文论文起稿 |
| `templates/latex/diangong/main.tex` | 电工杯论文起稿 |

## 8. 图表参考资产

| 目录 | 用途 |
|---|---|
| `assets/nature_figure/chart-atlas/` | 10 类常用图表参考：柱状、折线、热图、散点、雷达、分布、森林图、面积、图像板、网络矩阵 |
| `assets/nature_figure/gallery/` | 5 张多面板参考图，帮助规划 Nature / SCI 风格结果图 |

## 9. Ponytail 参考资产

| 文件 | 用途 |
|---|---|
| `assets/ponytail/ponytail_SKILL.md` | Ponytail 极简代码实现原则原始参考 |
| `assets/ponytail/ponytail-review_SKILL.md` | Ponytail 代码瘦身审查原则原始参考 |

## 10. 脚本

| 文件 | 用途 |
|---|---|
| `scripts/hsk_check_artifact.py` | 提交产物检查 |
| `scripts/hsk_pack_submission.py` | 提交包打包 |
| `scripts/render_paper.py` | 论文渲染辅助 |
| `scripts/score_artifact.py` | 产物评分辅助 |
| `scripts/extract_diff.py` | 差异提取辅助 |

## 11. 测试文件

| 文件 | 用途 |
|---|---|
| `tests/test_code_starter_smoke.py` | 代码模板烟雾测试 |
| `tests/test_hsk_compact_cn_output_policy.py` | 中文结果输出策略测试 |
| `tests/test_hsk_delivery_closure_policy.py` | 交付闭环策略测试 |
| `tests/test_hsk_nature_figure_policy.py` | Nature / SCI 图表策略测试 |
| `tests/test_hsk_mechanism_figure_policy.py` | 机理/推导图协议、模板和注册测试 |
| `tests/test_hsk_ponytail_code_policy.py` | Ponytail 代码精简策略测试 |
| `tests/test_latex_template_compile.py` | LaTeX 模板检查 |

## 12. 建议放入 ChatGPT 项目来源的文件

建议项目来源保留：

```text
PROJECT_INSTRUCTIONS_HSK_V616.md
HSK_SKILL_RUNTIME_CORE_V616.md
HSK_SKILL_FILE_INDEX_V616.md
HSK_COMMON_TEMPLATES_V616.md
mathmodel-skill-6.1.6-hsk-docxdraft-latexfinal-mechanism-nature-ponytail.zip
```

其中 zip 作为完整归档，4 个 md 用于快速读取。不要同时保留 v6.1.5 或更早版本的同类来源文件，避免规则混检索。


补充说明：本次追加 DOCX 排版规则后，若项目来源只保留 4 个 md，也应同步使用更新后的 `PROJECT_INSTRUCTIONS_HSK_V616.md`、`HSK_SKILL_RUNTIME_CORE_V616.md`、`HSK_SKILL_FILE_INDEX_V616.md`、`HSK_COMMON_TEMPLATES_V616.md`。
