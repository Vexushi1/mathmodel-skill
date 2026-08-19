# Scripts

本目录只保存活动运行/维护脚本。行为以各脚本实现及其 Authority/contract 为准；本文件只提供稳定导航，不保留旧版本的行为快照。

## 运行时入口与治理

- `resolve_workflow.py`：解析一个或多个用户意图、`objective`、`structures`、`capabilities`、`preprocessing_decision` 与竞赛类型，返回最小确定性 `load_order`、模块计划、暂停边界与 `pre_delivery_gates`；只有 `project_level` 才插入项目级数据预处理阶段。
- `validate_semantic_governance.py`：检查 Problem Contract、题面—数学—代码—输出语义闭环、Complexity Sanity Check、semantic revision、跨问 typed dependency 与 paper-fragment stale；不运行赛题代码，也不恢复数值有效性。
- `sync_project.py`：按当前 data source 和显式 delivery scope 发现产物、校验 Schema、计算分层哈希并传播 stale；不自动生成模型语义、数值结果或 `passed` 状态。

## 代码与用户执行

- `validate_code_delivery.py`：按 `preprocessing / primary / analysis` 阶段静态校验题目专属 Python 的完整运行配置、代码质量和阶段边界；不执行赛题代码。
- `validate_user_execution.py`：按当前 `preprocessing_decision` 验收适用的预处理工作簿、主求解工作簿与结果深化分析工作簿，并核对运行配置、代码/数据哈希和对应质量门。

赛题专属预处理、主求解和结果深化分析仍由用户本地以 full-fidelity 执行；脚本工具不得通过降采样、粗网格、缩短时域、减少重复、放宽容差或静默 solver fallback 改变正式求解口径。

## 项目记忆与论文检查

- `validate_project_state.py`：校验 `state/project_state.yaml` 的机器状态、分类兼容、哈希和 stale 语义。
- `validate_model_paper_framework.py`：校验 current `模型论文框架.md` 的 compact/full 结构、命题预算、Terminology/Numeric/Title/Paper Fragment 记录以及 Algorithm Trace 的确定性闭环。对 `stepwise/pseudocode` 检查关联 Algorithm ID、必填字段、模式/current 状态和已求解后的 Python code anchor；`not_needed` 不要求算法框。该脚本不从步骤文字推断算法正确性、收敛性或与 Python 的数学等价性。
- `audit_paper_prose.py`：对最终论文主文件执行非破坏性成稿审计，可结合 `--framework 模型论文框架.md` 与 `--bib references.bib`。结果分为 `blocking / review_required / warning`；默认只报告，`--strict` 阻断 `blocking` 与未处理的 `review_required`，warning 不阻断。机器不推断数学正确性、定理适用性、术语语义等价、参数最优性或 citation 是否真正支持 claim。

正文结构与表达由 `modules/05_writing/latex.md` 管理；跨竞赛 Formula Trace、Algorithm Trace、Hard/Default/Recommendation、命题、Terminology、Numeric Style、Title Claim、深化证据处置、Paragraph Necessity、Paper Fragment stale 与 Citation Evidence 由 `core/writing_reasoning_contract.yaml` 管理。脚本只执行可确定性检查，不建立第二套正文规则。

## LaTeX、评分与打包

- `render_paper.py`：按 `core/compile_profiles.yaml` 编译 CUMCM、MCM/ICM、电工杯等活动 LaTeX 工程并检查日志。
- `prepare_cumcm_class.py`：为 CUMCM CI/编译准备 class 依赖。
- `score_submission.py`：按 `config/review_weights.json` 执行评委式评分；Hard 否决不能被总分掩盖。
- `hsk_pack_submission.py`：按当前竞赛 profile 和提交边界整理提交物；内部项目记忆/检查材料不得因为 Skill 存在就自动进入官方提交包。

## 仓库维护

- `lint_skill.py`：检查版本 carrier、Authority 指针、路由/模块/Pack 可达性、生产者—消费者闭环、三态预处理、五文件合同、代码质量、writing/review 读取链、Algorithm Trace 消费、Schema、活动/legacy 隔离、Markdown/仓库引用、Python 语法和 generated-file 状态。
- `generate_indexes.py`：重建 `SKILL_FILE_INDEX.md`、`TEMPLATE_INDEX.md` 与 `MANIFEST.sha256`。这些生成文件不得手工伪造或手改哈希。

仓库维护至少执行：

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
```

正式修改流程还必须遵守根目录 `SKILL_CHANGE_GOVERNANCE.md`：从 `main` 读取 bootstrap 与治理文件、使用独立分支和单主题 PR，并在完整 CI 全绿后才合并。
