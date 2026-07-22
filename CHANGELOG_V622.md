# v6.2.4 flat-question-layout 变更记录

文件名保留 V622 作为稳定兼容路径。

## 目标

本版本不改变六模块主工作流和 Python/MATLAB 软件职责，重点消除竞赛项目中的重复目录、路径搜索辅助文件和工作簿—绘图脚本分离问题，使每问证据链在一个目录内闭合。

## P0：项目目录统一

- 赛题 PDF、附件数据表、说明文件和具体问题 Python 脚本直接放在项目根目录；
- 不再默认创建 `数据/`、`Python求解/` 和 `MATLAB绘图/`；
- Python 统一使用 `Path(__file__).resolve().parent` 定位项目根目录；
- 旧目录结构只用于历史项目迁移，不作为新项目交付格式。

## P1：每问结果目录扁平化

旧结构：

```text
结果数据表/问题X/问题X结果数据/
```

新结构：

```text
结果数据表/问题X/
├─ 问题X求解结果.xlsx
├─ 问题X敏感性与鲁棒性结果.xlsx
├─ q{x}_plot.m
└─ 图表/
```

- 删除 `问题X结果数据/` 重复层级；
- 两类标准工作簿、可选元数据和 MATLAB 绘图入口统一位于问题目录；
- 正式结果图统一导出到同级 `图表/`，可编辑图源按需放入 `图表/可编辑源/`。

## P2：MATLAB 单文件默认入口

- `q{x}_plot.m` 使用 `fileparts(mfilename("fullpath"))` 获取自身目录；
- 直接读取同目录两类固定工作簿，不再搜索项目根目录；
- 简单问题默认自包含文件、工作表、字段、空表和非法值检查，以及基础科研样式；
- 不再强制生成 `hsk_find_project_root.m`、`hsk_read_result_workbooks.m` 等辅助文件；
- 共享辅助函数仍保留为多问题复杂项目的兼容选项，但不进入默认入口。

## P3：机器契约和测试同步

- `core/output_contract.yaml`、`core/hsk_core_policy.md`、Module 03/04 和 Artifact Pack 同步新路径；
- `result_io.py` 改为直接写入 `结果数据表/问题X/`，新增问题图表目录和 MATLAB 入口路径函数；
- `hsk_check_artifact.py` 改为检查项目根目录 Python 脚本、扁平问题目录、同目录 `q{x}_plot.m` 和 `图表/`；
- `config.yaml`、`matlab_handoff.py`、Figure Contract、结果 Manifest 和提交包说明同步；
- 单元测试新增扁平路径、首次运行项目根目录、同目录 MATLAB 入口和图表目录检查。

---

# v6.2.3 contract-closure 变更记录

## 目标

本版本不增加题型 Pack，不恢复旧 Stage。重点将 v6.2.2 已有规则落实为可执行、逐问、可失效、可评分的机器契约，并减少活动包中的历史噪声。

## P0：契约闭环

- `core/module_manifest.yaml` 增加 artifact catalog、外部产物和完整生产者—消费者链；
- LaTeX 流程改为“草稿 → AI 模板感清除 → 最终编译”，避免清理结果未进入 PDF；
- `scripts/lint_skill.py` 新增模块输入无生产者、未登记产物、终点产物缺失和逆序依赖检查；
- `scripts/resolve_workflow.py` 将意图、主/次题型与竞赛解析为确定性的去重加载计划。

## P1：逐问状态与共享校验

- `core/project_state.schema.yaml` 按小问记录主/次题型、能力标志、数据/模型哈希、验证哈希、最优性措辞和失效状态；
- 新增 `scripts/validate_project_state.py`，检查阶段状态、需求计数、产物路径、证据、容差、最优性和 stale 状态；
- `core/workbook_schema.yaml` 将题型标签与验证能力分离；
- 约束、均衡、守恒、离散和收敛工作表由 capability 标志决定；
- `result_io.py` 与 `hsk_check_artifact.py` 复用同一工作簿校验函数；
- 增加重复主键、缺失值审计、非有限数值和“残差/违反量—容差—是否满足”一致性检查；
- Python 总管线移除导入阶段目录创建、全局随机种子和全局审计列表等副作用。

## P2：编译、评分和资产接入

- `core/compile_profiles.yaml` 区分仓库 `template_main` 与最终工程 `project_main`；
- `render_paper.py` 按 Profile 解析主文件，不再把硬编码候选当成唯一事实源；
- 新增 `scripts/score_submission.py`，正式消费 `config/review_weights.json`；
- 新增 `assets/figure_assets.yaml`，将 Nature 图集作为按需视觉参考接入图型选择；
- 图集不作为数据、结论或固定配色模板。

## P3：活动包与 CI

- `scripts/generate_indexes.py` 只为活动 Skill 生成索引和 Manifest；`legacy/` 仅保留 `legacy/README.md` 指针；
- 历史文件继续留在 Git 仓库，但不进入默认读取和活动完整性哈希；
- CI 将静态 lint 与 Python 3.10–3.14 单元测试矩阵拆分，减少重复工作；
- 自动生成元数据在功能分支完成后收敛为主分支维护，避免机器人提交反复触发 PR 检查。

## v6.2.2 基线

v6.2.2 完成六模块架构、十类题型 Pack、高级方法准入、两个标准工作簿、MATLAB 证据图、三套 LaTeX 冒烟编译、Python 3.10–3.14 CI、自动索引和跨平台 Manifest。v6.2.3 在该基线上完成契约闭环，v6.2.4 进一步统一项目与证据目录。
