# mathmodel-skill v6.2.4-flat-question-layout

本版本保留六模块主架构，在 v6.2.3 契约闭环基础上统一项目路径：赛题、附件和 Python 脚本直接位于项目根目录；每问两类工作簿、唯一 MATLAB 入口和图表统一收敛到 `结果数据表/问题X/`，删除重复目录层级。

## 快速入口

1. `AGENTS.md`：最短执行入口；
2. `REPOSITORY_INDEX.md`：按任务查找模块、Pack 和模板；
3. `core/hsk_core_policy.md`：唯一全局硬规则；
4. `core/workflow_router.yaml`：机器可读路由；
5. `core/module_manifest.yaml`：模块产物闭环；
6. `HSK_SKILL_FILE_INDEX_V622.md`：活动文件清单，文件名为兼容路径，标题显示当前版本。

## 核心工作流

```text
逐字审题
→ 每问题型、能力与依赖拆解
→ 两条模型路线与高级方法准入
→ 变量、假设、公式和约束闭环
→ Python 求解、约束/残差检查和多算法验证
→ 每问两类中文 Excel 工作簿
→ MATLAB 读取同目录工作簿绘制正式结果图
→ DOCX 草稿检查
→ LaTeX 草稿
→ AI 模板感清除
→ Profile 驱动编译
→ 评委式终审和提交包检查
```

## 固定职责

- Python：读取项目根目录中的题目附件，完成数据处理、模型求解、优化、仿真、检验、敏感性、鲁棒性和结果工作簿输出；
- MATLAB：与对应问题工作簿同目录，只读取工作簿绘制正式结果图，不重新计算核心结果；
- DOCX：前期修改、批注和逻辑检查；
- LaTeX：最终论文与 PDF；中文国赛保留 `cumcmthesis`；
- `legacy/`：仅用于历史追溯和兼容，不参与活动索引与 Manifest，除 `legacy/README.md` 指针外不默认加载。

## 固定项目结构

```text
项目根目录/
├─ A题.pdf
├─ 附件1.xlsx
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

## v6.2.4 重点

- 删除 `问题X结果数据/` 重复层级，两类工作簿直接位于 `结果数据表/问题X/`；
- 具体问题 Python 脚本与赛题、附件同放项目根目录，不再默认创建 `Python求解/`；
- `q{x}_plot.m` 与对应工作簿同目录，不再默认创建 `MATLAB绘图/`；
- MATLAB 使用自身脚本目录直接定位工作簿，简单问题默认采用单文件自包含读取、校验和样式；
- 正式结果图统一导出到 `结果数据表/问题X/图表/`；
- `result_io.py`、`hsk_check_artifact.py`、MATLAB 模板、Figure Contract、Manifest 和测试同步到新路径；
- 旧目录仅允许作为历史项目迁移输入，不作为新项目输出。

## 本地检查

```bash
python -m pip install -r requirements-dev.txt
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
python scripts/resolve_workflow.py full_solution --primary mechanism --secondary optimization --competition CUMCM
```

详细变更见 `CHANGELOG_V622.md`。
