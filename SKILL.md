---
name: mathmodel-skill
version: 6.2.5
summary: HSK modular mathematical-modeling workflow with a current-only model paper framework, per-subproblem state, root-level problem code, flat Chinese Excel workbooks, titled MATLAB figures, DOCX draft, cleaned LaTeX final, and reviewer-grade delivery.
triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 建模论文, 模型论文框架, 结果摘要, 模型选择, 敏感性分析, 鲁棒性分析, 机理图, MATLAB绘图, MATLAB图标题, LaTeX, DOCX]
---

# HSK 数学建模模块化工作流 v6.2.5

## 启动顺序

1. 始终读取 `core/hsk_core_policy.md`。
2. 读取 `core/workflow_router.yaml`，确定任务层级、模块顺序和题型 Pack。
3. 读取 `core/module_manifest.yaml`，核对模块输入、输出、生产者和机器契约。
4. 若已有项目状态，按 `core/project_state.schema.yaml` 读取 `state/project_state.yaml` 或当前对话中的等价摘要。
5. 若项目已锁定模型，优先读取项目根目录最新版 `模型论文框架.md`；该文件只保留当前有效口径。
6. 题型与验证能力按小问记录；不得用一组项目级标签统一覆盖全部小问。
7. 按需加载 `modules/`、`packs/task/`、`packs/competition/`、`packs/artifact/` 和必要视觉资产。
8. 禁止默认读取 `legacy/`；只有兼容旧项目、追溯旧规则或修复旧脚本时才加载。

## 三种完整度

- **建模方案**：审题与模型设计，停在变量、假设、公式、约束和验证计划闭环，并创建完整当前版 `模型论文框架.md`。
- **完整求解**：在建模方案基础上继续完成 Python 求解、约束/残差检查、多算法验证、两类标准工作簿和逐问结果摘要同步。
- **全流程**：继续完成保留简洁标题的 MATLAB 结果图、DOCX 草稿、LaTeX 草稿、AI 模板感清除、最终编译和评委式终审。

路由以用户实际交付物为终点，不为凑流程伪造后续成果；下游模块缺少前置结果时必须记录缺口，不能用占位数字替代。确定性加载计划可由 `scripts/resolve_workflow.py` 生成。

## `模型论文框架.md` 规则

- `locked_model_spec` 形成后，立即在项目根目录创建该文件；
- 文件是当前模型语义、论文结构、各问结果摘要和图表映射的唯一有效入口，不是修改日志；
- 模型、参数、约束、数据处理、算法、结果或图表变化时，删除受影响旧内容并完整替换为新版；
- Git 历史保存旧版本，框架正文不得长期并列旧版与新版；
- 每次正式交付模型、代码、工作簿、验证、MATLAB 图、DOCX 或 LaTeX 时，必须同步交付完整最新版框架；
- 每问求解后写入模型与算法、核心数值、验证/可行性、敏感性/鲁棒性、最终结论和证据位置；
- 模型语义与论文组织以框架为准，数值以标准工作簿为准，机器状态与 stale 以 `state/project_state.yaml` 为准。

模板为 `templates/model/model_paper_framework.md`，校验器为 `scripts/validate_model_paper_framework.py`。

## 六大运行模块

- `modules/01_problem_audit.md`：任务接入、逐字审题、小问拆解与交付映射。
- `modules/02_model_design.md`：路线比较、数据协议、变量假设公式闭环、机理图合同和当前模型论文框架锁定。
- `modules/03_solve_validate.md`：Python 求解、能力对应检查、多算法验证、敏感性与鲁棒性、Excel 输出和逐问结果摘要同步。
- `modules/04_figure_evidence.md`：保留简洁标题的 MATLAB 结果图证据链与后期机理图精修。
- `modules/05_writing/`：DOCX 草稿、LaTeX 草稿、AI 模板感清除；清理后由编译质量子模块生成 PDF。
- `modules/06_review_delivery.md`：评委式终审、可执行评分与提交包检查。

## 固定软件分工

- Python：读取项目根目录中的题目附件，完成数据处理、模型求解、优化、仿真、检验、敏感性、鲁棒性和标准工作簿输出。
- MATLAB：与对应问题工作簿同目录，读取标准工作簿绘制正式论文结果图，不重新计算核心结果；单图保留 `title`，多面板保留 `sgtitle`。
- GeoGebra/PPT/draw.io/SVG/TikZ：按需承担非数据驱动机理图。
- DOCX：前期修改与逻辑检查；LaTeX：最终论文与 PDF。

## 机器可读契约

- `core/output_contract.yaml`：项目目录、框架同步、文件名、MATLAB 标题与软件职责；
- `core/workbook_schema.yaml`：工作表、字段、非空、能力条件和 MATLAB 交接规则；
- `core/project_state.schema.yaml`：逐问状态、题型、能力、框架/结果摘要状态、哈希与失效标志；
- `core/compile_profiles.yaml`：各竞赛模板入口、项目入口和 LaTeX 编译链；
- `core/module_manifest.yaml`：模块产物生产者—消费者闭环。

Python 写入器与交付检查器复用 `result_io.py` 的同一工作簿校验函数。项目状态语义由 `scripts/validate_project_state.py` 检查，框架结构和同步由 `scripts/validate_model_paper_framework.py` 检查。

## 固定项目与结果结构

```text
项目根目录/
├─ A题.pdf
├─ 附件1.xlsx
├─ 模型论文框架.md
├─ 问题一求解.py
├─ 问题一敏感性与鲁棒性.py
└─ 结果数据表/
   └─ 问题一/
      ├─ 问题一求解结果.xlsx
      ├─ 问题一敏感性与鲁棒性结果.xlsx
      ├─ q1_plot.m
      └─ 图表/
```

不再默认创建 `数据/`、`Python求解/`、`MATLAB绘图/` 或 `问题X结果数据/` 重复层级。Python 使用脚本目录定位项目根目录；MATLAB 使用自身目录直接读取同目录工作簿。约束、均衡、守恒、离散和收敛检查由每问 capability 标志决定。所有工作表必须非空；不适用分析写入 `适用性说明`。

## 默认主线

审题 → 模型设计与锁定 → 创建/重写 `模型论文框架.md` → Python 求解验证 → 中文结果工作簿 → 同步各问结果摘要 → MATLAB 结果图与图标题 → 同步图表证据链 → DOCX 草稿 → 核心机理图精修 → LaTeX 草稿 → AI 模板感清除 → LaTeX 编译 → 终审交付。
