# mathmodel-skill v6.2.2-consistency-hardening

本版本保留六模块、题型 Pack、竞赛 Pack 和交付 Pack 架构，重点修正规则、模板、代码、索引和测试之间的不一致。

## 核心能力

- Python 只求解、验证并输出两类标准 Excel 工作簿；
- MATLAB 只读取工作簿绘制正式论文图，不重算核心结果；
- 每问固定输出 `问题X求解结果.xlsx` 与 `问题X敏感性与鲁棒性结果.xlsx`；
- 工作簿字段、非空要求和题型工作表由 `core/workbook_schema.yaml` 约束；
- 项目状态由 `core/project_state.schema.yaml` 验证；
- LaTeX 按 `core/compile_profiles.yaml` 执行对应的 XeLaTeX/Biber 或 pdfLaTeX/BibTeX 编译链；
- MATLAB 自动查找项目根目录并执行跨平台字体回退；
- 旧 Stage、句式语料和 Python 正式绘图样式保留于 `legacy/`，默认不加载。

## 读取顺序

1. `REPOSITORY_INDEX.md`：任务到文件的语义导航；
2. `core/hsk_core_policy.md`：唯一全局硬规则源；
3. `core/workflow_router.yaml`：按任务和题型加载最少必要模块；
4. `core/module_manifest.yaml`：核对模块输入、输出和机器可读契约。

## 项目来源建议

1. `PROJECT_INSTRUCTIONS_HSK_V622.md`
2. `HSK_RUNTIME_ROUTER_V622.md`
3. 本仓库

## 快速检查

```bash
python -m pip install -r requirements-dev.txt
python scripts/generate_indexes.py
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
```

GitHub Actions 对 Python 3.10–3.14 执行 lint 和单元测试。
