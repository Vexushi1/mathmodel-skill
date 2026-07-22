# mathmodel-skill v6.2.2-hsk-consistency-hardening

本版本保留六模块主架构，统一 Python 求解、中文结果工作簿、每问唯一 MATLAB 绘图文件、DOCX 草稿、LaTeX 终稿和评委式终审，并修复规则、模板、工具与测试之间的不一致。

## 快速入口

1. `AGENTS.md`：最短执行入口；
2. `REPOSITORY_INDEX.md`：按任务查找模块、Pack 和模板；
3. `core/hsk_core_policy.md`：唯一全局硬规则；
4. `core/workflow_router.yaml`：机器可读路由；
5. `HSK_SKILL_FILE_INDEX_V622.md`：完整文件清单。

## 核心工作流

```text
逐字审题
→ 小问拆解与题型分类
→ 两条模型路线与高级方法准入
→ 变量、假设、公式和约束闭环
→ Python 求解、约束检查和多算法验证
→ 每问两类中文 Excel 工作簿
→ 每问唯一 QX_plot.m 生成全部正式结果图
→ DOCX 草稿检查
→ LaTeX 终稿与编译
→ 评委式终审和提交包检查
```

## 固定职责

- Python：数据处理、模型求解、优化、仿真、检验、敏感性、鲁棒性和结果工作簿输出；
- MATLAB：每问只交付一个自包含 `QX_plot.m`，只读取工作簿绘制正式结果图，不重新计算核心结果；
- DOCX：前期修改、批注和逻辑检查；
- LaTeX：最终论文与 PDF；中文国赛保留 `cumcmthesis`；
- `legacy/`：仅用于历史追溯和兼容，不参与默认运行。

## 固定结果结构

```text
结果数据表/问题X/问题X结果数据/
├─ 问题X求解结果.xlsx
└─ 问题X敏感性与鲁棒性结果.xlsx

MATLAB绘图/问题X/
└─ QX_plot.m
```

工作簿结构见 `core/workbook_schema.yaml`。所有工作表必须非空；分析不适用时写明原因。正式结果图必须绑定工作簿、工作表、`QX_plot.m` 本地图函数和论文结论。

## 科研绘图体系

正式图按四个等级选择：

- `single`：单一图形；
- `layered`：同一坐标区叠加多种图形；
- `multi-panel`：多个坐标区组成证据链；
- `hybrid`：多面板中的面板继续使用层叠组合图。

默认支持柱状+折线、散点+模型线+区间带、箱线+散点、小提琴+箱线/中位数+散点、直方图+密度、中心线+双层区间带、热图+等高线和 Pareto 散点+前沿+推荐点。配色采用高对比固定角色体系，完整规范见 `templates/figure/scientific_composite_system.md`。

## v6.2.2 重点

- 配置驱动的 LaTeX 编译链；
- 工作簿和项目状态 Schema；
- Python 3.10–3.14 CI；
- 自动文件索引和 SHA-256 Manifest；
- 十类可执行题型 Pack；
- 高级模型七项准入；
- 每问唯一、自包含的 `QX_plot.m`；
- 高对比层叠、多面板与混合组合图系统；
- 统一 DOCX 检查和图表解释去模板化。

## 本地检查

```bash
python -m pip install -r requirements-dev.txt
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
```

详细变更见 `CHANGELOG_V622.md`。
