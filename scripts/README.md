# Scripts

本目录只保存活动运行/维护脚本。行为以各脚本实现及其 Authority/contract 为准；本文件只提供稳定导航，不保留旧版本的行为快照。

## 运行时入口与治理

- `resolve_runtime.py`：默认 assured runtime 入口。在兼容旧 plan 字段及 `objective / structures / capabilities` 分类轴的基础上，可选读取 `--project-root` / `--question` 恢复 current project state，验证 artifact hash，输出 intent provenance、ambiguity、declarative contract closure、authority fingerprint 与 `runtime_plan/assurance`。
- `reading_plan.py`：由默认 resolver 调用，使用同一次 hydration 的原始状态快照生成带文件哈希与行范围的初始读取、条件资料和工具接口清单；读取选择服从 `core/workflow_router.yaml#reading_policy`，不改旧计划、不执行校验门、不写项目。
- `resolve_workflow.py`：保留的无状态兼容 resolver；仍可直接解析显式 intent/classification/artifact-name 输入，但不负责 project-state hydration 或 artifact hash assurance。
- `validate_semantic_governance.py`：检查 Problem Contract、题面—数学—代码—输出语义闭环、Complexity Sanity Check、semantic revision、跨问 typed dependency 与 paper-fragment stale；不运行赛题代码，也不恢复数值有效性。
- `validate_model_approval.py`：在项目级预处理或主求解代码交付前，检查 `model_challenge_status=passed`、`human_model_approval_status=approved`，并要求 approved semantic revision / structured identity 与当前 semantic revision / structured identity 完全一致；旧 approved 记录发生语义漂移后只能作为 provenance，不能继续授权新主求解。
- `sync_project.py`：按当前 data source 和显式 delivery scope 发现产物、校验 Schema、计算分层哈希并传播 stale；不自动生成模型语义、数值结果或 `passed` 状态。
- `state_transitions.py`：纯内存执行 `core/state_transition_contract.yaml`；新增主求解／深化数值来源退役事件用于显式项目迁移的失效预览与传播，不选择后端、不归档、不撤换当前绑定，也不授权迁移。
- `project_transaction.py`：复用项目锁、候选验证、generation 和可恢复日志；`commit_project_state` 可选接收 `expected_file_hashes`，绑定 state、所有伴随写入目标和已声明只读来源的原始字节（值为 null 表示必须不存在）。传入时要求规范项目相对路径；存在未清理事务日志先阻断，须明确恢复后重新捕获快照。省略参数的历史调用保持原恢复行为。准备日志后仍按已有 roll-forward 恢复；保护限于声明读集合及协作式锁，不代表数值验收、文件系统级全局原子快照或迁移写侧已上线。
- `project_transaction.py` 的 `prepare_history_archive` / `verify_history_archive`：显式读集合的流式原始字节归档与只读复核，布局委托 `core/output_contract.yaml#backend_migration_history`，不识别数学资格或批准。准备失败保留并报告本次目录，不递归删除历史。`commit_project_state(preserved_archives=...)` 要求同时使用字节读集合，并以 journal v2 持久保存归档引用，在提交及恢复边界复核；无归档事务仍用 v1。恢复后再次读旧原始路径不是归档复核的前提；旧实现不支持 v2，存在 v2 日志时不得先降级。本批没有开放 select/migrate，历史引用须由之后的协调操作在当前状态/伴随记录中持久登记。

## 代码与用户执行

- `run_config_parser.py`：P8 收敛出的共享语法级 helper，只静态抽取顶层 `RUN_CONFIG` / legacy `FULL_*` 字典常量并保持 fail-closed；字段政策与运行语义仍由 `core/user_execution_contract.yaml` 及调用方拥有，不在此建立第二 Authority。
- `stage_code.py`：依据执行/输出 Authority 解析阶段后端、唯一入口、配置和源码 bundle，供交付/回执/同步/打包/runtime 共享；不写项目状态。
- `matlab_code_checks.py`：MATLAB 受限静态语法与工程检查适配，原生分析器未执行时如实报告未核验。
- `validate_code_delivery.py`：按 `preprocessing / primary / analysis` 阶段静态校验题目专属 Python/MATLAB 的完整运行配置、代码质量和阶段边界；不执行赛题代码。RUN_CONFIG/FULL_* 的静态语法抽取委托 `run_config_parser.py`，字段要求仍在本 validator 与 User Execution Authority 中判定。
- `validate_user_execution.py`：按当前 `preprocessing_decision` 与已激活阶段验收适用的预处理工作簿、主求解工作簿和条件存在的结果深化分析工作簿，并核对运行配置、代码/数据哈希和对应质量门；读取已交付阶段代码时复用同一语法级 config parser，但保留本调用面的 receipt/echo/错误边界。

赛题专属预处理、主求解和被 Analysis Necessity Gate=`required` 激活的结果深化分析由用户本地以 full-fidelity 执行；脚本工具不得通过降采样、粗网格、缩短时域、减少重复、放宽容差或静默 solver fallback 改变正式求解口径。Gate=`not_required` 时不生成 03B 代码/工作簿，也不得把该状态写成稳健性或稳定性已通过。项目级预处理和主求解属于 current 人工锁模后的代码阶段，不能只凭 Problem Contract 冻结或 Model Challenge 通过绕过 `validate_model_approval.py`。

## 项目记忆与论文检查

- `validate_project_state.py`：校验 `state/project_state.yaml` 的机器状态、分类兼容、哈希和 stale 语义。
- `validate_model_paper_framework.py`：校验 current `模型论文框架.md` 的 compact/full 结构、命题预算、Terminology/Numeric/Title/Paper Fragment 记录以及 Algorithm Trace 的确定性闭环。对 `stepwise/pseudocode` 检查关联 Algorithm ID、必填字段、模式/current 状态和已求解后的 实际代码锚点；`not_needed` 不要求算法框。该脚本不从步骤文字推断算法正确性、收敛性或与实现的数学等价性。
- `audit_latex_project.py`：正式 LaTeX 项目审计入口。递归展开 active `\input/\include`、检查 fragment/source-file 工程闭环，再委托 `audit_paper_prose.py` 完成 prose/structure/BibTeX/framework 审查；兼容单文件工程自然退化为单文件模式。
- `audit_paper_prose.py`：底层非破坏性成稿审计实现；结果分为 `blocking / review_required / warning`。它保留维护级直接调用能力，但不是活动 LaTeX route 的默认入口。机器不推断数学正确性、定理适用性、术语语义等价、参数最优性或 citation 是否真正支持 claim。

正文结构与表达由 `modules/05_writing/latex.md` 管理；跨竞赛 Formula Trace、Algorithm Trace、Hard/Default/Recommendation、命题、Terminology、Numeric Style、Title Claim、深化证据处置、Paragraph Necessity、Paper Fragment stale 与 Citation Evidence 由 `core/writing_reasoning_contract.yaml` 管理。脚本只执行可确定性检查，不建立第二套正文规则。

## LaTeX、评分与打包

- `latex_delivery.py`：计算并核验 formal source bundle、audit report、compile profile、编译日志与 PDF 的证明链哈希；供正式编译和同步门复用。
- `render_paper.py`：按 `core/compile_profiles.yaml` 执行正式 LaTeX audit → compile → compile-report 链；模板 smoke build 不等价于正式交付证明。
- `prepare_cumcm_class.py`：为 CUMCM CI/编译准备 class 依赖。
- `score_submission.py`：按 `config/review_weights.json` 执行评委式评分；Hard 否决不能被总分掩盖。
- `hsk_pack_submission.py`：按当前竞赛 profile 和提交边界生成 official / reproducibility 提交包及 `submission_manifest.yaml`；内部项目记忆/检查材料不得因为 Skill 存在就自动进入官方提交包。
- `validate_submission_package.py`：对 manifest、ZIP 实际内容、当前项目同路径文件与 compiled PDF 哈希做最终包级验证；ZIP 存在本身不等价于 `validated_submission_package`。

## 仓库维护

- `project_solver_backend.py inspect --project-root <项目根目录>`：v10 迁移准备中的只读声明诊断；区分根选择、历史一致/混合/缺失声明和冲突，不替代完整 Schema、来源、回执或审批校验，不授予执行资格。可加 `--migration-target python|matlab --reason <reason>` 生成全题来源/回执核验、类型化退役与字段差异预览；`ready_for_review`及预览摘要不是迁移确认或新Schema验收。当前只开放 inspect，不写状态、不创建归档、不恢复事务；现有运行时选择规则尚未切换。
- `lint_skill.py`：检查版本 carrier、Authority 指针、路由/模块/Pack 可达性、生产者—消费者闭环、三态预处理、当前每问 conditional layout（base3 + Gate=`required` 时 +2）、代码质量、writing/review 读取链、Algorithm Trace 消费、Schema、活动/legacy 隔离、Markdown/仓库引用、Python 语法和 generated-file 状态。
- `measure_infrastructure.py`：P8 维护测量入口；只读统计脚本体量、validator hotspot、重复解析调用点与 generated-metadata workflow 形态，为后续结构整理提供可复算证据，不定义业务阈值或修改 runtime state。
- `generate_indexes.py`：重建 `SKILL_FILE_INDEX.md`、`TEMPLATE_INDEX.md` 与 `MANIFEST.sha256`。`SKILL_FILE_INDEX.md` 按 Active Runtime/Reference、Current Maintenance、Migration/Compatibility、Historical Provenance、Legacy Navigation 分区；该分区只影响导航展示，不改变 `iter_files()` / MANIFEST 覆盖。生成文件不得手工伪造或手改哈希。
- `.github/workflows/ci.yml`：完整 HSK Skill CI 同时保留 `push`、`pull_request` 与显式 `workflow_dispatch` 入口；显式调度执行的是同一组完整 jobs，不能用部分检查替代。
- `.github/workflows/refresh-generated.yml`：feature branch 仍只负责生成并提交受管 metadata；当 bot push 产生新的 final head 时，显式调度既有完整 HSK Skill CI 与 Optimization baseline，对该最终 head 做等价复验；main 路径仍保持只读 `--check`，不得用部分检查替代完整门禁。

仓库维护至少执行：

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
```

正式修改流程还必须遵守根目录 `SKILL_CHANGE_GOVERNANCE.md`：从 `main` 读取 bootstrap 与治理文件、使用独立分支和单主题 PR，并在完整 CI 全绿后才合并。
