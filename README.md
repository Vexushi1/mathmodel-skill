# mathmodel-skill v6.2.3-contract-closure

本版本保留六模块主架构，重点把规则落实为可执行契约：逐问题型与能力状态、模块产物生产者—消费者闭环、共享工作簿校验、项目状态语义检查、Profile 驱动的 LaTeX 入口、可执行评分和活动包索引。

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
→ MATLAB 读取工作簿绘制正式结果图
→ DOCX 草稿检查
→ LaTeX 草稿
→ AI 模板感清除
→ Profile 驱动编译
→ 评委式终审和提交包检查
```

## 固定职责

- Python：数据处理、模型求解、优化、仿真、检验、敏感性、鲁棒性和结果工作簿输出；
- MATLAB：只读取工作簿绘制正式结果图，不重新计算核心结果；
- DOCX：前期修改、批注和逻辑检查；
- LaTeX：最终论文与 PDF；中文国赛保留 `cumcmthesis`；
- `legacy/`：仅用于历史追溯和兼容，不参与活动索引与 Manifest，除 `legacy/README.md` 指针外不默认加载。

## 固定结果结构

```text
结果数据表/问题X/问题X结果数据/
├─ 问题X求解结果.xlsx
└─ 问题X敏感性与鲁棒性结果.xlsx
```

工作簿结构见 `core/workbook_schema.yaml`。题型决定专项结果，capability 标志决定约束、均衡、守恒、离散和收敛检查。写入器与交付检查器复用同一校验实现。

## v6.2.3 重点

- `core/module_manifest.yaml` 建立可 lint 的产物闭环；
- `state/project_state.yaml` 按小问记录主/次题型、能力、数据/模型哈希和失效状态；
- `scripts/validate_project_state.py` 执行阶段、路径、证据与最优性语义检查；
- `scripts/resolve_workflow.py` 输出确定性模块/Pack 加载计划；
- `result_io.py` 统一写入和交付校验，并检查主键、缺失审计、非有限数值及残差一致性；
- `scripts/score_submission.py` 正式消费 `config/review_weights.json`；
- `assets/figure_assets.yaml` 将 Nature 图集作为按需视觉参考接入；
- LaTeX Profile 区分仓库 `template_main` 与项目 `project_main`；
- 活动索引与 Manifest 不再枚举完整 legacy；
- CI 将静态 lint 与 Python 版本矩阵拆分。

## 本地检查

```bash
python -m pip install -r requirements-dev.txt
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
python scripts/resolve_workflow.py full_solution --primary mechanism --secondary optimization --competition CUMCM
```

详细变更见 `CHANGELOG_V622.md`。
