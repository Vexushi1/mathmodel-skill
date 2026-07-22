# v6.2.3 contract-closure 变更记录

文件名保留 V622 作为稳定兼容路径。

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

v6.2.2 完成六模块架构、十类题型 Pack、高级方法准入、两个标准工作簿、MATLAB 证据图、三套 LaTeX 冒烟编译、Python 3.10–3.14 CI、自动索引和跨平台 Manifest。本版本在该基线上做契约闭环，不改变软件职责和竞赛主工作流。
