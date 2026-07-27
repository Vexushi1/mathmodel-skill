# mathmodel-skill v6.2.6-proposition-proof

本版本在 v6.2.5 当前模型论文框架与 MATLAB 图标题闭环基础上，引入**全文级命题与证明规划**：命题可以为 0，最终论文最多 4 个。命题优先用于问题简化、模型必要性说明、关键点识别、降维、候选范围缩减、约束删减、算法可行性和理论边界；正文默认使用短证明，并将命题正文与证明置于同一个外框中。

## 快速入口

1. `AGENTS.md`：最短执行入口；
2. `REPOSITORY_INDEX.md`：按任务查找模块、Pack 和模板；
3. `core/hsk_core_policy.md`：唯一全局硬规则；
4. `core/workflow_router.yaml`：机器可读路由；
5. `core/module_manifest.yaml`：模块产物闭环；
6. `templates/model/model_paper_framework.md`：项目根目录框架模板；
7. `HSK_SKILL_FILE_INDEX_V622.md`：活动文件清单，文件名为兼容路径，标题显示当前版本。

## 核心工作流

```text
逐字审题
→ 每问题型、能力与依赖拆解
→ 两条模型路线与高级方法准入
→ 变量、假设、公式和约束闭环
→ 全文命题必要性筛选（0–4 个）
→ 创建/重写 模型论文框架.md
→ Python 求解、约束/残差检查、命题数值复核和多算法验证
→ 每问两类中文 Excel 工作簿
→ 同步逐问结果摘要与命题状态
→ MATLAB 读取同目录工作簿绘制带简洁标题的正式结果图
→ 同步标题—图注—数据—结论证据链
→ DOCX 草稿检查
→ LaTeX 草稿、命题短证明与统一外框排版
→ AI 模板感清除
→ Profile 驱动编译
→ 评委式终审和提交包检查
```

## `模型论文框架.md`

- 模型锁定后在项目根目录创建；
- 只保留当前有效模型、参数、约束、数据处理、算法、命题、证明、结果和图表映射；
- 发生变化时删除旧内容并完整替换，不在文件中累计修改日志；
- Git 历史保存旧版本；
- 全文维护 0--4 个命题的编号、条件、结论、证明等级、模型作用、失效边界和状态；
- 记录正文短证明目标、外框形式和附录迁移条件；
- 每问求解后写入模型与算法、核心数值、验证/可行性、敏感性/鲁棒性、最终结论和证据位置；
- 每次正式交付模型、代码、工作簿、验证、MATLAB 图、DOCX 或 LaTeX 时，同步交付完整最新版；
- 模型语义、命题证明和论文结构以框架为准，数值以标准工作簿为准，机器状态与 stale 以 `state/project_state.yaml` 为准。

模板：`templates/model/model_paper_framework.md`  
项目校验：`python scripts/validate_model_paper_framework.py 模型论文框架.md --state state/project_state.yaml`

## 命题与证明规则

- 全文命题数量按实际需要确定，可以为 0，最多 4 个，不按小问机械分配；
- 命题优先用于问题简化、模型必要性说明、关键点或阈值识别、维度或候选范围缩减、冗余约束删除、算法可行性保持和理论边界；
- 每个命题必须给出假设与定义域、结论、证明等级、建模作用和失效边界；
- A 级为完整证明，B 级为关键证明链，C 级为引用标准定理并核验本题条件；
- 正文默认采用 B 级短证明，通常保留 2--6 个逻辑步骤、3--8 行，原则上不超过三分之一页；超过半页的完整技术证明移入附录；
- 命题正文与短证明置于同一个外框，框内不嵌套第二层边框；默认白底细边、无阴影和无大面积底色，可使用黑色、深灰或克制的深蓝边线；
- “不得使用彩色框”的限制针对流程图和机理图中的装饰性框，不适用于命题证明环境；
- 数值实验、交叉验证、模型准确率比较和求解器退出状态只能作证据或复核，不能替代严格证明；
- 推荐正文顺序：模型详细推导 → 必要命题与短证明 → 核心模型汇总 → 求解算法 → 结果分析；
- 模型、参数、约束或定义域变化后，相关证明必须重新检查；失效证明不得保留在终稿。

## 固定职责

- Python：读取项目根目录中的题目附件，完成数据处理、模型求解、优化、仿真、检验、敏感性、鲁棒性和结果工作簿输出；
- MATLAB：与对应问题工作簿同目录，只读取工作簿绘制正式结果图，不重新计算核心结果；单图使用 `title`，多面板使用整体 `sgtitle`，默认保留在导出图中；
- DOCX：前期修改、批注、命题短证明与外框检查；
- LaTeX：最终论文、命题证明外框排版与 PDF；中文国赛保留 `cumcmthesis`；
- `legacy/`：仅用于历史追溯和兼容，不参与活动索引与 Manifest，除 `legacy/README.md` 指针外不默认加载。

## 固定项目结构

```text
项目根目录/
├─ A题.pdf
├─ 附件1.xlsx
├─ 模型论文框架.md
├─ 问题一求解.py
├─ 问题一敏感性与鲁棒性.py
└─ 结果数据表/
   ├─ 问题一/
   │  ├─ 问题一求解结果.xlsx
   │  ├─ 问题一敏感性与鲁棒性结果.xlsx
   │  ├─ q1_plot.m
   │  └─ 图表/
   ├─ 问题二/
   │  ├─ 问题二求解结果.xlsx
   │  ├─ 问题二敏感性与鲁棒性结果.xlsx
   │  ├─ q2_plot.m
   │  └─ 图表/
   └─ ...
```

工作簿结构见 `core/workbook_schema.yaml`。题型决定专项结果，capability 标志决定约束、均衡、守恒、离散和收敛检查。写入器与交付检查器复用同一校验实现。

## v6.2.6 重点

- 新增全文命题与证明硬规则：可为 0，最多 4 个；
- 命题用途进一步收敛到问题简化、模型必要性、关键点识别、降维、约束删减、算法可行性和理论边界；
- 正文默认使用 B 级短证明，不再通篇展开初等代数；
- 命题正文与短证明使用同一个外框，流程图/机理图的彩色框限制不适用于命题证明环境；
- `modules/02_model_design.md` 增加命题准入、证明等级、命题合同和失效管理；
- `模型论文框架.md` 增加命题规划、P1--P4 登记、正文长度、外框形式、数值复核和失效边界；
- `core/output_contract.yaml`、`core/project_state.schema.yaml` 和模块产物闭环接入 `proposition_plan`；
- DOCX、LaTeX、AI 模板感清除、终审和提交包规则全面同步；
- CUMCM HSK 模板新增 `hskproposition` 外框、按章节编号的 `proposition` 和“证明：”格式的 `hskproof` 环境；
- 校验器、静态 lint 和单元测试检查命题数量、编号、状态、短证明、外框字段完整性和引用一致性；
- 延续 v6.2.5 当前模型框架、MATLAB 标题，以及 v6.2.4 扁平目录和实表固定列读取规则。

## 本地检查

```bash
python -m pip install -r requirements-dev.txt
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
python scripts/resolve_workflow.py proposition_proof --primary mechanism --competition CUMCM
python scripts/validate_model_paper_framework.py templates/model/model_paper_framework.md
```

详细变更见 `CHANGELOG_V622.md`。
