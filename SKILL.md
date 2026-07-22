---
name: mathmodel-skill
version: 6.2.2
summary: HSK modular mathematical-modeling workflow with Python-only solving, validated Chinese Excel result workbooks, one self-contained MATLAB plotting file per question, high-contrast layered and multi-panel scientific figures, DOCX draft, LaTeX final, and reviewer-grade delivery.
triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 建模论文, 模型选择, 敏感性分析, 鲁棒性分析, 机理图, MATLAB绘图, 组合图, LaTeX, DOCX]
---

# HSK 数学建模模块化工作流 v6.2.2

## 启动顺序

1. 始终读取 `core/hsk_core_policy.md`。
2. 读取 `core/workflow_router.yaml`，按任务只加载必要模块。
3. 若已有项目状态，按 `core/project_state.schema.yaml` 读取 `state/project_state.yaml` 或当前对话中的等价摘要。
4. 按需加载 `modules/`、`packs/task/`、`packs/competition/` 和 `packs/artifact/`。
5. 禁止默认读取 `legacy/`；只有兼容旧项目、追溯旧规则或修复旧脚本时才加载。

## 六大运行模块

- `modules/01_problem_audit.md`：任务接入、逐字审题、小问拆解与交付映射。
- `modules/02_model_design.md`：路线比较、数据协议、变量假设公式闭环、机理图合同。
- `modules/03_solve_validate.md`：Python 求解、约束检查、多算法验证、敏感性与鲁棒性、Excel 输出。
- `modules/04_figure_evidence.md`：每问唯一 `QX_plot.m`、高对比层叠/多面板/混合组合图、MATLAB 结果图证据链与后期机理图精修。
- `modules/05_writing/`：DOCX 草稿、LaTeX 终稿、AI 模板感清除。
- `modules/06_review_delivery.md`：评委式终审与提交包检查。

## 固定软件分工

- Python：数据处理、模型求解、优化、仿真、检验、敏感性、鲁棒性和标准工作簿输出。
- MATLAB：每个问题只交付一个自包含 `QX_plot.m`；读取两类标准工作簿，一次运行生成该问题全部正式结果图，不重新计算核心结果。
- GeoGebra/PPT/draw.io/SVG/TikZ：按需承担非数据驱动机理图。
- DOCX：前期修改与逻辑检查；LaTeX：最终论文与 PDF。

## 正式绘图体系

正式结果图按四个复杂度等级选择：

- `single`：单一图形；
- `layered`：同一坐标区叠加柱、线、散点、箱体、小提琴、区间带、等高线等多种图形；
- `multi-panel`：多个坐标区组织结果、机制和验证；
- `hybrid`：多面板中的面板继续使用层叠组合图。

默认使用高对比科研配色和固定颜色角色，完整执行 `templates/figure/scientific_composite_system.md` 与 `templates/figure/chart_selection.md`。典型层叠图包括柱状+折线、散点+模型线+区间带、箱线+散点、小提琴+箱线/中位数+散点、直方图+密度、热图+等高线和 Pareto 散点+前沿+推荐点。

## 机器可读契约

- `core/output_contract.yaml`：项目目录、文件名与软件职责；
- `core/workbook_schema.yaml`：工作表、字段、非空和单文件 MATLAB 交接规则；
- `core/project_state.schema.yaml`：跨聊天项目状态；
- `core/compile_profiles.yaml`：各竞赛 LaTeX 编译链。

## 固定结果结构

```text
结果数据表/问题X/问题X结果数据/
├─ 问题X求解结果.xlsx
└─ 问题X敏感性与鲁棒性结果.xlsx

MATLAB绘图/问题X/
└─ QX_plot.m
```

约束违反、多算法对比、逐时/逐区域明细和绘图底层数据写入两类工作簿的中文工作表，不默认散落为独立 CSV。所有工作表必须非空；不适用分析写入 `适用性说明`。同一问题不得额外交付独立结果图、敏感性图、样式或导出辅助 `.m` 文件。

## 默认主线

审题 → 模型设计 → Python 求解验证 → 中文结果工作簿 → 每问唯一 MATLAB 绘图文件 → DOCX 草稿 → 核心机理图精修 → LaTeX 终稿 → 终审交付。
