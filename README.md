# mathmodel-skill v6.2.5-current-model-framework

本版本在 v6.2.4 扁平目录与实表固定列读取基础上，引入项目根目录 `模型论文框架.md` 作为当前模型语义、论文结构、逐问结果摘要和图表映射的唯一有效入口，并恢复 MATLAB 正式结果图的简洁标题。

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
→ 创建/重写 模型论文框架.md
→ Python 求解、约束/残差检查和多算法验证
→ 每问两类中文 Excel 工作簿
→ 同步逐问结果摘要
→ MATLAB 读取同目录工作簿绘制带简洁标题的正式结果图
→ 同步标题—图注—数据—结论证据链
→ DOCX 草稿检查
→ LaTeX 草稿
→ AI 模板感清除
→ Profile 驱动编译
→ 评委式终审和提交包检查
```

## `模型论文框架.md`

- 模型锁定后在项目根目录创建；
- 只保留当前有效模型、参数、约束、数据处理、算法、结果和图表映射；
- 发生变化时删除旧内容并完整替换，不在文件中累计修改日志；
- Git 历史保存旧版本；
- 每问求解后写入模型与算法、核心数值、验证/可行性、敏感性/鲁棒性、最终结论和证据位置；
- 每次正式交付模型、代码、工作簿、验证、MATLAB 图、DOCX 或 LaTeX 时，同步交付完整最新版；
- 模型语义和论文结构以框架为准，数值以标准工作簿为准，机器状态与 stale 以 `state/project_state.yaml` 为准。

模板：`templates/model/model_paper_framework.md`  
校验：`python scripts/validate_model_paper_framework.py 模型论文框架.md --state state/project_state.yaml`

## 固定职责

- Python：读取项目根目录中的题目附件，完成数据处理、模型求解、优化、仿真、检验、敏感性、鲁棒性和结果工作簿输出；
- MATLAB：与对应问题工作簿同目录，只读取工作簿绘制正式结果图，不重新计算核心结果；单图使用 `title`，多面板使用整体 `sgtitle`，默认保留在导出图中；
- DOCX：前期修改、批注和逻辑检查；
- LaTeX：最终论文与 PDF；中文国赛保留 `cumcmthesis`；
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

## v6.2.5 重点

- 新增根目录 `模型论文框架.md` 当前口径契约与完整模板；
- 模型/参数/约束/数据/算法/结果变化时执行“删除旧版—重写当前版”，Git 负责历史；
- 每问结果摘要正式纳入求解交付，记录核心数值、验证、鲁棒性和证据位置；
- 模块产物闭环、路由、项目状态 Schema、交付合同和审查规则全部接入框架同步；
- 新增 `scripts/validate_model_paper_framework.py`，并接入 `hsk_check_artifact.py`；
- MATLAB 单图恢复 `title`，多面板恢复整体 `sgtitle`，图标题默认保留；
- Figure Contract 增加 MATLAB title、DOCX/LaTeX caption 和框架登记位置；
- 图注继续置于 DOCX/LaTeX 图下，但用于补充统计口径，不与图内标题逐字重复；
- 延续 v6.2.4 的项目根目录 Python、扁平问题目录、同目录工作簿与 `q{x}_plot.m`、实表真实表头与固定列读取规则。

## 本地检查

```bash
python -m pip install -r requirements-dev.txt
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
python scripts/resolve_workflow.py full_solution --primary mechanism --secondary optimization --competition CUMCM
python scripts/validate_model_paper_framework.py 模型论文框架.md --state state/project_state.yaml
```

详细变更见 `CHANGELOG_V622.md`。
