# Scripts v6.6.0

- `lint_skill.py`：检查活动版本、LaTeX-first、主求解质量门、独立结果深化分析、模块产物闭环、两类工作簿 Schema、状态字段、交付 gate、Python 语法和活动索引。
- `resolve_workflow.py`：将一个或多个任务意图、自然语言 request、objective、structures、capabilities 与竞赛类型解析为确定性的模块、Pack、模板和交付前 gate。
- `sync_project.py`：发现主求解与结果深化分析工作簿、MATLAB脚本和图表；校验工作簿；计算 data、model、solution_workbook、result_analysis_workbook、matlab_script、figure_bundle 和 framework 哈希；保守传播 stale。
- `validate_project_state.py`：分别验证 `result_quality_status` 与 `result_analysis_status`，检查 `redo_required` 回退状态、产物路径、哈希、证据、容差和最优性声明。
- `validate_model_paper_framework.py`：验证当前模型框架、逐问结果摘要、命题规划、同步状态和可选哈希。
- `hsk_check_artifact.py`：检查项目根目录 Python、`问题X求解结果.xlsx`、`问题X结果深化分析.xlsx`、同目录 `q{x}_plot.m`、正式图和逐问状态。
- `generate_indexes.py`：重建活动索引、旧文件名兼容指针与 `MANIFEST.sha256`。
- `score_submission.py`：读取评分配置执行评委式评分和硬否决。
- `hsk_pack_submission.py`：打包提交产物并排除缓存与 LaTeX 辅助文件。
- `render_paper.py`：按编译配置执行 LaTeX 编译链。
- `prepare_cumcm_class.py`：对项目中的 CUMCM 类文件执行窄范围、幂等兼容补丁。

## Python 主链

```text
run_primary_pipeline
→ 数据审计
→ 完整主求解
→ 主结果质量门
→ 问题X求解结果.xlsx

run_result_analysis_pipeline
→ 读取已通过质量门的主结果
→ 选择题目专属分析
→ 问题X结果深化分析.xlsx
```

`run_pipeline()` 只是按顺序调用两个独立阶段。主结果质量报告写入 `主结果质量门`；分析计划和结论写入 `分析设计` 与 `结论稳定性汇总`。

## 真实项目校验

```bash
python scripts/validate_model_paper_framework.py 模型论文框架.md --state state/project_state.yaml
python scripts/validate_project_state.py state/project_state.yaml --project-root .
python scripts/hsk_check_artifact.py .
python scripts/sync_project.py . --write --strict --delivery-scope results
```

## 仓库维护

```bash
python scripts/generate_indexes.py
python scripts/generate_indexes.py --check
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/resolve_workflow.py full_solution \
  --objective optimization \
  --structures scheduling stochastic \
  --capabilities has_explicit_constraints requires_feasibility_check \
  --competition CUMCM
```

默认完整工作流在图表锁定后直接进入 LaTeX；DOCX 仅由显式请求加载。旧 `问题X敏感性与鲁棒性结果.xlsx` 只作历史读取兼容，不属于新项目正式交付。
