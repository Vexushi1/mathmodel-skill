# mathmodel-skill v6.6.1

当前工作流：**审题与模型闭合 → 用户本地完整版 Python 求解 → 代码质量门 → 主结果质量门 → 自适应结果深化分析 → MATLAB证据图 → LaTeX终稿**。

## 每问默认交付

```text
问题X求解/
├─ 问题X求解.py
├─ 问题X求解结果.xlsx
├─ 问题X结果深化分析.xlsx
└─ qX_plot.m
```

不默认生成独立运行配置、运行说明、校验报告、`图表/` 或额外元数据。完整运行配置嵌入 Python 并写入两个工作簿的 `运行配置` 表。

## 质量门

- `core/code_quality_contract.yaml`：代码长度、函数规模、参数数量、复杂度与反模式；
- `scripts/validate_code_delivery.py`：静态检查代码，不执行赛题；
- `core/workbook_schema.yaml`：主结果和深化分析工作簿证据；
- `scripts/validate_user_execution.py`：验收用户返回工作簿、代码/数据哈希与结果质量；
- `scripts/sync_project.py`：正式交付前检查产物、哈希和 stale。

代码默认以 500 行以内为目标；501--700 行给 warning；超过 700 行默认拒绝，复杂题显式豁免最多到 900 行。单函数以 80 行以内为目标，超过 120 行拒绝；函数参数以 8 个以内为目标，超过 12 个拒绝。详细规则只在 `core/code_quality_contract.yaml` 定义。

## 启动与检查

```bash
python scripts/resolve_workflow.py full_solution --objective optimization --competition CUMCM
python scripts/validate_code_delivery.py <project_root> --write --strict
python scripts/sync_project.py <project_root> --write --strict --delivery-scope results
```

仓库维护执行 `python scripts/lint_skill.py`、全量单元测试和生成索引检查。DOCX 是显式可选分支；`legacy/` 只保存历史与只读兼容。
