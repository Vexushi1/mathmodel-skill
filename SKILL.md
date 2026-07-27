---
name: mathmodel-skill
version: 6.2.6
summary: HSK modular mathematical-modeling workflow with a current-only model paper framework, optional paper-level proposition proofs capped at four, per-subproblem state, root-level problem code, flat Chinese Excel workbooks, titled MATLAB figures, DOCX draft, cleaned LaTeX final, and reviewer-grade delivery.
triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 建模论文, 模型论文框架, 结果摘要, 模型选择, 命题证明, 引理, 推论, 等价性证明, 可行性证明, 敏感性分析, 鲁棒性分析, 机理图, MATLAB绘图, MATLAB图标题, LaTeX, DOCX]
---

# HSK 数学建模模块化工作流 v6.2.6

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

- **建模方案**：审题与模型设计，停在变量、假设、公式、约束、全文命题必要性和验证计划闭环，并创建完整当前版 `模型论文框架.md`。
- **完整求解**：在建模方案基础上继续完成 Python 求解、约束/残差检查、多算法验证、两类标准工作簿、命题数值复核和逐问结果摘要同步。
- **全流程**：继续完成保留简洁标题的 MATLAB 结果图、DOCX 草稿、LaTeX 草稿、命题证明排版、AI 模板感清除、最终编译和评委式终审。

路由以用户实际交付物为终点，不为凑流程伪造后续成果；下游模块缺少前置结果时必须记录缺口，不能用占位数字替代。确定性加载计划可由 `scripts/resolve_workflow.py` 生成。

## `模型论文框架.md` 规则

- `locked_model_spec` 形成后，立即在项目根目录创建该文件；
- 文件是当前模型语义、论文结构、全文命题与证明规划、各问结果摘要和图表映射的唯一有效入口，不是修改日志；
- 模型、参数、约束、数据处理、算法、命题、证明、结果或图表变化时，删除受影响旧内容并完整替换为新版；
- Git 历史保存旧版本，框架正文不得长期并列旧版与新版；
- 每次正式交付模型、代码、工作簿、验证、MATLAB 图、DOCX 或 LaTeX 时，必须同步交付完整最新版框架；
- 每问求解后写入模型与算法、核心数值、验证/可行性、敏感性/鲁棒性、最终结论和证据位置；
- 模型语义、命题证明与论文组织以框架为准，数值以标准工作簿为准，机器状态与 stale 以 `state/project_state.yaml` 为准。

模板为 `templates/model/model_paper_framework.md`，校验器为 `scripts/validate_model_paper_framework.py`。

## 命题与证明硬规则

- 命题是全文级可选内容，可以为 0，最终论文最多 4 个，不按小问机械分配；
- 仅用于模型等价性、可行性/存在性、单调性或阈值、凸性/唯一性/解结构、约束或维度缩减、算法可行性保持、稳定性或误差界；
- 变量定义、直接代数变形、题意复述、单个样本结果、准确率比较和求解器退出状态不得包装成命题；
- 每个命题必须给出前提与定义域、结论、证明等级、模型作用和失效边界；数值检查只作复核，不能替代数学证明；
- 模型、参数、约束或定义域变化后，相关命题与证明必须重新检查并同步框架和项目状态；
- 推荐正文顺序为“模型详细推导 → 必要命题与证明 → 核心模型汇总 → 求解算法 → 结果分析”。

## 六大运行模块

- `modules/01_problem_audit.md`：任务接入、逐字审题、小问拆解、待证明关系和交付映射。
- `modules/02_model_design.md`：路线比较、数据协议、变量假设公式闭环、全文命题规划、机理图合同和当前模型论文框架锁定。
- `modules/03_solve_validate.md`：Python 求解、能力对应检查、多算法验证、敏感性与鲁棒性、Excel 输出和逐问结果摘要同步。
- `modules/04_figure_evidence.md`：保留简洁标题的 MATLAB 结果图证据链与后期机理图精修。
- `modules/05_writing/`：DOCX 草稿、LaTeX 草稿、命题证明排版、AI 模板感清除；清理后由编译质量子模块生成 PDF。
- `modules/06_review_delivery.md`：评委式终审、命题证明审计、可执行评分与提交包检查。

## 固定软件分工

- Python：读取项目根目录中的题目附件，完成数据处理、模型求解、优化、仿真、检验、敏感性、鲁棒性和标准工作簿输出。
- MATLAB：与对应问题工作簿同目录，读取标准工作簿绘制正式论文结果图，不重新计算核心结果；单图保留 `title`，多面板保留 `sgtitle`。
- GeoGebra/PPT/draw.io/SVG/TikZ：按需承担非数据驱动机理图。
- DOCX：前期修改与逻辑检查；LaTeX：最终论文与 PDF。

## 机器可读契约

- `core/output_contract.yaml`：项目目录、框架同步、命题上限与字段、文件名、MATLAB 标题和软件职责；
- `core/workbook_schema.yaml`：工作表、字段、非空、能力条件和 MATLAB 交接规则；
- `core/project_state.schema.yaml`：逐问状态、题型、能力、命题引用、框架/结果摘要状态、哈希与失效标志；
- `core/compile_profiles.yaml`：各竞赛模板入口、项目入口和 LaTeX 编译链；
- `core/module_manifest.yaml`：模块产物生产者—消费者闭环。

Python 写入器与交付检查器复用 `result_io.py` 的同一工作簿校验函数。项目状态语义由 `scripts/validate_project_state.py` 检查，框架结构、命题数量和同步由 `scripts/validate_model_paper_framework.py` 检查。

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

审题 → 模型设计与锁定 → 全文命题必要性筛选 → 创建/重写 `模型论文框架.md` → Python 求解验证 → 中文结果工作簿 → 同步各问结果摘要与命题复核 → MATLAB 结果图与图标题 → 同步图表证据链 → DOCX 草稿 → 核心机理图精修 → LaTeX 草稿与命题证明 → AI 模板感清除 → LaTeX 编译 → 终审交付。
