# Legacy Archive

本目录仅用于旧项目追溯、兼容、来源说明和人工迁移，不属于当前默认运行链路。除 `legacy/README.md` 作为历史导航入口外，`legacy/**` 不应进入活动 Skill 索引、默认 Router load 或正式交付依赖。

## 顶层归档导航

- `stage_v616/`：旧 Stage 00--12 文件；
- `old_stage_0_9/`：更早的评分、反馈层和状态系统；
- `v616_sources/`：v6.1.6 入口文件快照；
- `reference_details/`：已被后续活动模块吸收的详细旧协议与模型资料；
- `writing_phrase_corpus/`：竞赛句式、经验笔记与反例语料，仅可人工查阅，不得作为当前写作 Authority 自动套写；
- `competition_data/`：旧经验参数、rubric overlay 与历史统计数据；
- `config/`：旧评分/维度配置，仅作历史追溯，活动运行链不得读取；
- `tools/`：已退出默认运行链的一次性下载、抽取、语料处理与维护脚本；
- `papers/`：历史论文资料获取记录和人工维护说明；当前仓库不依赖其中 PDF 才能运行；
- `releases/`：历史 release 指针与 Git commit 定位说明；
- `python_plotting_deprecated_v621/`：v6.2.1 时期的 Python 绘图样式辅助代码，已被当前 MATLAB 证据绘图职责替代；
- `matlab_compat/`：已退出新项目默认链路的 MATLAB 路径搜索与显式导出辅助函数；
- `v660_self_contained_output_migration.md`：v6.6 单脚本旧项目迁移到当前每问双 Python / 双工作簿 / MATLAB 五文件接口的说明。

## 使用边界

旧项目重新进入当前流程时，迁移目标、执行边界和文件接口以当前 `core/bootstrap.yaml`、`core/user_execution_contract.yaml` 与 `core/output_contract.yaml` 为准；本目录中的历史规则、旧模板版本号、旧命题格式、旧“问题要求”或旧“结论”不得覆盖当前 Authority。

`matlab_compat/` 仅用于仍依赖旧共享函数、旧 `结果数据表/问题X/` 或自动导出目录的历史项目。v6.6 单脚本项目和更早结构继续只读兼容；一旦重新进入当前设计、求解、深化分析、绘图或终稿流程，应按当前合同完成所需迁移，而不是把旧目录结构重新引入新项目。

## 删除原则

历史文件不能因为“当前 Router 不读取”就直接删除。只有同时确认：

1. 不被活动入口或兼容入口引用；
2. 不承担旧项目迁移功能；
3. 不承担来源、版本或历史 provenance；
4. Git history 已提供等价且可定位的恢复路径；

才考虑删除。否则保留在 `legacy/`，并通过本 README 说明其用途。

除非用户明确要求兼容旧项目、追溯历史规则或人工维护历史资料，禁止加载本目录。
