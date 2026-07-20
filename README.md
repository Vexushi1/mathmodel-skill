# mathmodel-skill v6.2.1-hsk-modular-python-matlab

本版本以 v6.2.0 的模块化路由为主干，吸收 Python/MATLAB 职责分离、MATLAB 模板、插件封装和专项测试，并统一每问结果目录。

## 核心变化

- Python 只求解和输出数据，不生成正式论文图；
- MATLAB 只读取 Excel 工作簿绘图，不重算结果；
- 每问固定输出 `问题X求解结果.xlsx` 与 `问题X敏感性与鲁棒性结果.xlsx`；
- 约束检查、多算法、逐时/逐区域明细作为中文工作表保存；
- MATLAB 图窗默认可见并保留，导出由人工调整后显式触发；
- LaTeX 路由正式接入编译质量模块；
- 旧 Stage、旧句式语料和 Python 正式绘图样式保留于 `legacy/`，默认不加载。

## 项目来源建议

1. `PROJECT_INSTRUCTIONS_HSK_V621.md`
2. `HSK_RUNTIME_ROUTER_V621.md`
3. 本压缩包

## 快速检查

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests -p 'test_*.py'
```
