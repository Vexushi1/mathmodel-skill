# Scripts v6.2.4

- `lint_skill.py`：检查核心文件、包版本、扁平目录契约、路由路径、模块产物闭环、Schema、题型 Pack、评分配置、视觉资产、编译入口、Python 语法和活动索引。
- `resolve_workflow.py`：将任务意图、主/次题型与竞赛解析为确定性的模块、Pack、模板和契约加载计划。
- `validate_project_state.py`：验证真实项目状态的结构、阶段、需求计数、产物路径、证据、哈希失效、容差和最优性声明。
- `generate_indexes.py`：重建活动 `HSK_SKILL_FILE_INDEX_V622.md`、模板索引与 `MANIFEST.sha256`；UTF-8 文本按 LF 规范化计算哈希，完整 legacy 不进入活动索引。
- `hsk_check_artifact.py`：检查项目根目录 Python 脚本、`结果数据表/问题X/` 两类工作簿、同目录 `q{x}_plot.m`、本地图表目录和逐问状态；工作簿校验复用 `result_io.py`。
- `score_submission.py`：读取 `config/review_weights.json` 计算六维评分并执行硬否决。
- `hsk_pack_submission.py`：打包提交产物，并排除缓存与 LaTeX 辅助文件。
- `render_paper.py`：按 `core/compile_profiles.yaml` 的 template/project 主入口与编译链编译 LaTeX 工程。
- `prepare_cumcm_class.py`：对复制到项目目录的 CUMCM 类文件执行窄范围、幂等兼容补丁。

MATLAB 问题绘图入口统一使用 `结果数据表/问题X/q{x}_plot.m`，并读取同目录两类工作簿；正式图写入同级 `图表/`。视觉参考通过 `assets/figure_assets.yaml` 按需加载，规则色板只作为默认起点。

推荐维护命令：

```bash
python scripts/generate_indexes.py
python scripts/generate_indexes.py --check
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/resolve_workflow.py full_solution --primary mechanism --secondary optimization --competition CUMCM
python scripts/validate_project_state.py state/project_state.yaml --project-root .
```

旧评分、下载与语料处理脚本位于 `legacy/`，不属于默认运行链路或活动 Manifest。
