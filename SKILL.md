---
name: mathmodel-skill
version: 6.2.2
summary: HSK modular mathematical-modeling workflow with Python-only solving, validated Chinese Excel result workbooks, MATLAB-only formal result figures, DOCX draft, LaTeX final, and reviewer-grade delivery.
triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 建模论文, 模型选择, 敏感性分析, 鲁棒性分析, 机理图, MATLAB绘图, LaTeX, DOCX]
---

# HSK 数学建模模块化工作流 v6.2.2

## 启动顺序

1. 始终读取 `core/hsk_core_policy.md`。
2. 读取 `core/workflow_router.yaml`，确定任务层级、模块顺序和题型 Pack。
3. 读取 `core/module_manifest.yaml`，核对模块输入、输出、依赖和机器契约。
4. 若已有项目状态，按 `core/project_state.schema.yaml` 读取 `state/project_state.yaml` 或当前对话中的等价摘要。
5. 按需加载 `modules/`、`packs/task/`、`packs/competition/` 和 `packs/artifact/`。
6. 禁止默认读取 `legacy/`；只有兼容旧项目、追溯旧规则或修复旧脚本时才加载。

## 三种完整度

- **建模方案**：审题与模型设计，停在变量、假设、公式、约束和验证计划闭环。
- **完整求解**：在建模方案基础上继续完成 Python 求解、约束检查、多算法验证和两类标准工作簿。
- **全流程**：继续完成 MATLAB 结果图、DOCX 草稿、LaTeX 终稿、AI 模板感清除和评委式终审。

路由以用户实际交付物为终点，不为凑流程伪造后续成果；下游模块缺少前置结果时必须记录缺口，不能用占位数字替代。

## 六大运行模块

- `modules/01_problem_audit.md`：任务接入、逐字审题、小问拆解与交付映射。
- `modules/02_model_design.md`：路线比较、数据协议、变量假设公式闭环、机理图合同。
- `modules/03_solve_validate.md`：Python 求解、约束检查、多算法验证、敏感性与鲁棒性、Excel 输出。
- `modules/04_figure_evidence.md`：MATLAB 结果图证据链与后期机理图精修。
- `modules/05_writing/`：DOCX 草稿、LaTeX 终稿、AI 模板感清除。
- `modules/06_review_delivery.md`：评委式终审与提交包检查。

## 固定软件分工

- Python：数据处理、模型求解、优化、仿真、检验、敏感性、鲁棒性和标准工作簿输出。
- MATLAB：读取标准工作簿绘制正式论文结果图，不重新计算核心结果。
- GeoGebra/PPT/draw.io/SVG/TikZ：按需承担非数据驱动机理图。
- DOCX：前期修改与逻辑检查；LaTeX：最终论文与 PDF。

## 机器可读契约

- `core/output_contract.yaml`：项目目录、文件名与软件职责；
- `core/workbook_schema.yaml`：工作表、字段、非空、条件工作表和 MATLAB 交接规则；
- `core/project_state.schema.yaml`：跨聊天项目状态；
- `core/compile_profiles.yaml`：各竞赛 LaTeX 编译链。

Python 写入器与交付检查器必须执行 `core/workbook_schema.yaml`，不能只检查工作表是否存在。

## 固定结果结构

```text
结果数据表/问题X/问题X结果数据/
├─ 问题X求解结果.xlsx
└─ 问题X敏感性与鲁棒性结果.xlsx
```

约束违反、多算法对比、逐时/逐区域明细和绘图底层数据写入两类工作簿的中文工作表，不默认散落为独立 CSV。所有工作表必须非空；不适用分析写入 `适用性说明`。

## 默认主线

审题 → 模型设计 → Python 求解验证 → 中文结果工作簿 → MATLAB 结果图 → DOCX 草稿 → 核心机理图精修 → LaTeX 终稿 → 终审交付。
