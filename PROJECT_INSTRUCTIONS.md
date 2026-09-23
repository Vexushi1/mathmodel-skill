# HSK 项目调用说明

本文件只说明稳定调用程序和事实源边界。业务规则必须按 `core/bootstrap.yaml` 与 `scripts/resolve_runtime.py` 返回的 current Authority 读取，不在这里复制第二套合同。

## 启动与恢复

1. 先读 `core/bootstrap.yaml`，再运行 `scripts/resolve_runtime.py` 解析当前意图；只加载 resolver 命中的 contracts、modules、packs 和 templates。`scripts/resolve_workflow.py` 仅作无状态兼容入口。
2. 已有项目时把 project root 交给 runtime resolver。当前语义与证据位置优先从 `模型论文框架.md` 恢复；revision/structured identity/text provenance/stale 以 `state/project_state.yaml` 为准；具体数值必须回到 accepted workbook 核对。
3. 不依据旧聊天、历史计划或 `legacy/` 猜测 current 规则；legacy 只用于追溯和兼容。

## 执行硬边界

- Problem Contract 冻结后形成 `proposed_model_spec`，依次经过独立 `Model Reviewer` 与 `Devil's Advocate`；challenge passed 后进入 `awaiting_model_approval`，只有用户显式批准 current `semantic_revision` 与 validated `semantic_identity_hash`，并由 Model Approval gate 确认 current = validated = approved identity 后，才形成 current `locked_model_spec`；legacy hash 只读兼容不能授权新代码。正式项目级预处理或主求解代码前仍必须执行 resolver 返回的语义/模型批准 gate。
- 需要项目级预处理时使用固定 Python 入口；`question_local` 变换随项目后端对应的本问主求解实现执行。主求解和在 Analysis Necessity Gate=`required` 时激活的独立结果深化代码均由项目根唯一后端确定语言，默认由用户本地 full-fidelity 执行。助手生成并静态检查代码、验收返回工作簿；不得为了省时静默改变采样、精度、时域、重复次数、容差或求解器。
- Artifact 名称只作导航：每问文件布局只服从 `core/output_contract.yaml`。基础三文件为项目根 `execution.solver_backend` 对应的主入口、`问题X求解结果.xlsx` 与 `qX_plot.m`；仅当 Analysis Necessity Gate=`required` 时追加同一项目后端对应的独立深化入口与 `问题X结果深化分析.xlsx`。Python 项目使用 `问题X求解.py` 和条件式 `问题X结果深化分析.py`，MATLAB 项目使用对应的 `.m` 入口；不得逐问或逐阶段混合选择。必要辅助源码按执行 Authority 声明。旧表述“最终默认恰好包含五个文件”只适用于 Gate=`required` 且不需要辅助源码的路径，不是所有新项目的无条件默认。
- 主求解 accepted 资格只服从 `core/numerical_verification_contract.yaml`；accepted 后先执行 Analysis Necessity Gate。Gate=`required` 时由 `modules/03_result_analysis.md` 管理独立深化分析；Gate=`not_required` 时必须记录非空理由，不生成 03B 代码/工作簿，也不得据此声称稳健性或稳定性已通过。
- MATLAB 绘图入口只读取已验收数据和当前合法工作簿进行 Figure Evidence，不重新执行核心计算。主结果图只要求主工作簿；只有目标 Figure 实际消费已验收 03B 证据时才要求深化工作簿，且缺失时必须 fail closed。绘图规则只服从 `modules/04_figure_evidence.md` 与相关输出契约。

## 写作与交付

- LaTeX 为默认主链。CUMCM 先读 `templates/latex/cumcm/hsk/template_manifest.yaml` 确定固定骨架，再按 `core/writing_runtime_contract.yaml` 的 progressive authoring 顺序读取 `modules/05_writing/paper_writing_protocol.md`；复杂数学/证据语义由 `core/writing_reasoning_contract.yaml` 裁决，`modules/05_writing/latex.md` 只负责载体适配。 `既定论文大章节骨架保持不变`；公开 LaTeX 项目审计统一从 `scripts/audit_latex_project.py` 进入。
- DOCX 仅在用户明确要求 Word 审阅、批注、协作或指定提交格式时加载。
- 正式交付严格执行 resolver 当前返回的全部 `pre_delivery_gates` 且保持返回顺序；本文件不维护固定 gate 清单。

## 仓库维护

仓库级修改必须先读 current `core/bootstrap.yaml` 与 `SKILL_CHANGE_GOVERNANCE.md`，检查重叠 PR，使用独立分支和单主题 PR，并以真实 CI/生成文件结果验收。平台权限无法完成的 GitHub Settings 项只记录为治理债务，不得修改 Skill 代码模拟。

活动入口使用稳定文件名：`PROJECT_INSTRUCTIONS.md`、`RUNTIME_ROUTER.md`、`SKILL_FILE_INDEX.md` 和 `TEMPLATE_INDEX.md`。旧版本化入口只作兼容指针，不进入默认运行链。
