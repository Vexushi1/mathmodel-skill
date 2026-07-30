# Scripts v6.3.4

- `lint_skill.py`：检查活动版本、核心契约、三轴分类、模块产物闭环、交付 gate、Schema、题型 Pack、模板、Python 语法和活动索引。
- `resolve_workflow.py`：将一个或多个任务意图、自然语言请求、`objective`、`structures`、`capabilities` 与竞赛类型解析为确定性的模块、Pack、模板、契约和交付前 gate；`primary`、`secondary` 仅保留为旧项目兼容参数。
- `validate_model_paper_framework.py`：验证项目根目录 `模型论文框架.md` 的必需章节、全文命题上限与 P1--P4 编号、当前同步状态、逐问章节、结果摘要锚点和可选哈希；仓库维护时用于检查模板本身。
- `validate_project_state.py`：验证真实项目状态的结构、阶段、需求计数、产物路径、证据、命题数量/引用/失效、框架/结果摘要 freshness、哈希失效、容差和最优性声明。
- `generate_indexes.py`：重建活动 `HSK_SKILL_FILE_INDEX_V622.md`、模板索引与 `MANIFEST.sha256`；UTF-8 文本按 LF 规范化计算哈希，完整 legacy 不进入活动索引。
- `hsk_check_artifact.py`：检查项目根目录当前框架、Python 脚本、`结果数据表/问题X/` 两类工作簿、同目录 `q{x}_plot.m`、MATLAB `title`/`sgtitle`、本地图表目录和逐问状态；工作簿校验复用 `result_io.py`。
- `score_submission.py`：读取 `config/review_weights.json` 计算六维评分并执行硬否决。
- `hsk_pack_submission.py`：打包提交产物，并排除缓存与 LaTeX 辅助文件。
- `render_paper.py`：按 `core/compile_profiles.yaml` 的 template/project 主入口与编译链编译 LaTeX 工程。
- `prepare_cumcm_class.py`：对复制到项目目录的 CUMCM 类文件执行窄范围、幂等兼容补丁。

MATLAB 问题绘图入口统一使用 `结果数据表/问题X/q{x}_plot.m`，并读取同目录两类工作簿；单图保留简洁 `title`，多面板保留整体 `sgtitle`；正式图写入同级 `图表/`。标题、图注、数据源和正文结论同步到项目根目录 `模型论文框架.md`。视觉参考通过 `assets/figure_assets.yaml` 按需加载，规则色板只作为默认起点。

命题与证明在框架和项目状态中按全文登记，允许为 0，最多 4 个。校验器检查条件、结论、证明等级、模型作用、失效边界和每问引用；数值实验不能替代数学证明。

推荐仓库维护命令：

```bash
python scripts/generate_indexes.py
python scripts/generate_indexes.py --check
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/resolve_workflow.py full_solution --objective optimization --structures scheduling stochastic --capabilities has_explicit_constraints requires_feasibility_check --competition CUMCM
python scripts/validate_model_paper_framework.py templates/model/model_paper_framework.md
```

真实项目校验命令：

```bash
python scripts/validate_model_paper_framework.py 模型论文框架.md --state state/project_state.yaml
python scripts/validate_project_state.py state/project_state.yaml --project-root .
```

旧评分、下载与语料处理脚本位于 `legacy/`，不属于默认运行链路或活动 Manifest。
