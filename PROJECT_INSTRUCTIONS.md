# HSK 项目调用说明

<a id="web-app-start"></a>

## 网页和 App 项目指令

将下面一段保存为项目指令，或在新会话随题目一起发送。过去保存的文字不会随仓库更新。改用此入口时，在项目指令中替换原来的数学建模段落一次即可。新项目使用 v11.4.0 对应的固定 commit；已有项目继续沿用原先保存的固定提交，除非项目所有者明确选择升级。

```text
使用 https://github.com/Vexushi1/mathmodel-skill。已有项目沿用其固定提交。新项目将我选的提交链接、版本或 Release（未指定时用 main）解析为完整 commit，固定后从该提交读取 SKILL.md、core/bootstrap.yaml 和全局规则。遵守平台和系统指令。
若固定提交没有声明 v11_full_read，按该提交自己的启动合同工作。若已声明，我选择启用它。正式建模即使只做一问，也先取得全部现行规范原文。只查字段、修改已有图的配色、维护或咨询，按请求范围取读。局部任务转为正式建模时自动补齐全文，再推进对应动作。
在此模式下，换阶段、换问、换章、新图或改变范围，先读取适用的完整原文。已知缺段就补取。跨会话恢复正式任务、只剩摘要或已说不清规则范围，重新取齐整套。已有项目从当前模型论文框架恢复模型及人工批准，从实际工作簿读取数值。
读齐 Skill 后直接审题。模型双审与明确批准按模型批准合同执行，用户运行数值代码，返回结果按结果交接合同核对并继续。
```

v11.4.0 通过 v11_full_read 显式选择器启用正式任务全文启动。旧项目继续使用原先固定提交中的入口和能力；主动升级时明确选择新提交，并保全原始项目状态与产物。固定版本和迁移边界见[迁移说明](docs/v11_0_0_migration.md)。旧版项目沿原入口工作的记录仍可从[固定的 v10.35.3 指令](https://github.com/Vexushi1/mathmodel-skill/blob/4f765d3e1326d3ca7555933059e9313f99b86347/docs/stage_reading_execution_refactor_plan.md#132-可复制正文)追溯。

## 启动与恢复

1. 按固定提交的 core/bootstrap.yaml 选择启动范围，直接读取规则正文。需要机器诊断时调用 scripts/resolve_runtime.py，已有项目传入项目根和本次小问。
2. 读取当前 模型论文框架.md 中的模型、双审、批准和证据位置，按 core/model_approval_contract.yaml 接续；从实际工作簿取数，按 core/user_execution_contract.yaml#result_handoff 核对。state/project_state.yaml 保存真实登记与机器运行结果。
3. 阶段选段、条件补读及同阶段材料的复用服从 core/runtime_assurance_contract.yaml#reading_plan.consumer_protocol。可用工具和分段读取方法见[阶段正文读取](scripts/README.md#阶段正文读取)。旧 scripts/resolve_workflow.py 仅作无状态兼容入口。

新项目登记全部已确认小问及依赖，在第一份真实 `proposed_model_spec` 形成后建立 State 与框架；可用 `scripts/initialize_project.py` 完成初建。已有项目按当前请求和框架确定本次小问。显式调用 `resolve_runtime.py` 时传入 `--question Qn`；单问产物检查使用 `sync_project.py --question Qn`，项目级同步与正式 `docx/latex/submission` 检查保持全项目范围。

## 执行硬边界

- Problem Contract 冻结后形成 proposed_model_spec，完成独立 Model Reviewer 与 Devil's Advocate，进入 awaiting_model_approval。用户明确批准后按 core/model_approval_contract.yaml 保存当前 locked_model_spec 及批准依据，再交付代码。
- 需要项目级预处理时使用固定 Python 入口；question_local 变换随项目后端对应的本问主求解实现执行。主求解和在 Analysis Necessity Gate=`required` 时激活的独立结果深化代码均由项目根唯一后端确定语言，默认由用户本地 full-fidelity 执行。助手生成并静态检查代码、验收返回工作簿；不得为了省时静默改变采样、精度、时域、重复次数、容差或求解器。
- Artifact 名称只作导航：每问文件布局只服从 core/output_contract.yaml。基础三文件为项目根 execution.solver_backend 对应的主入口、问题X求解结果.xlsx 与当前绘图后端的 qX_plot.py 或 qX_plot.m；仅当 Analysis Necessity Gate=`required` 时追加同一项目后端对应的独立深化入口与 问题X结果深化分析.xlsx。Python 项目使用 问题X求解.py 和条件式 问题X结果深化分析.py，MATLAB 项目使用对应的 .m 入口；不得逐问或逐阶段混合选择。必要辅助源码按执行 Authority 声明。旧表述“最终默认恰好包含五个文件”只适用于 Gate=`required` 且不需要辅助源码的路径，不是所有新项目的无条件默认。
- 按 core/user_execution_contract.yaml#result_handoff 核对实际主结果，数值要求服从 core/numerical_verification_contract.yaml。随后判断 Analysis Necessity Gate：`required` 进入 modules/03_result_analysis.md；`not_required` 记录理由并继续绘图或写作。
- 项目选定的 Python/MATLAB 绘图入口读取已核对的实际工作簿进行 Figure Evidence。主结果图读取主工作簿；消费 03B 结果的图再读取对应深化工作簿。绘图规则服从 modules/04_figure_evidence.md。

## 写作与交付

- LaTeX 为默认主链。CUMCM 先读 templates/latex/cumcm/hsk/template_manifest.yaml 确定固定骨架，再按 core/writing_runtime_contract.yaml 的 progressive authoring 顺序读取 modules/05_writing/paper_writing_protocol.md；复杂数学/证据语义由 core/writing_reasoning_contract.yaml 裁决，modules/05_writing/latex.md 只负责载体适配。既定论文大章节骨架保持不变；公开 LaTeX 项目审计统一从 scripts/audit_latex_project.py 进入。
- DOCX 仅在用户明确要求 Word 审阅、批注、协作或指定提交格式时加载。
- 显式启用机器验收时，执行 resolver 当前返回的全部 `pre_delivery_gates`，保持返回顺序。

## 仓库维护

仓库级修改必须先读 current core/bootstrap.yaml 与 SKILL_CHANGE_GOVERNANCE.md，检查重叠 PR，使用独立分支和单主题 PR，并以真实 CI/生成文件结果验收。平台权限无法完成的 GitHub Settings 项只记录为治理债务，不得修改 Skill 代码模拟。

活动入口使用稳定文件名：PROJECT_INSTRUCTIONS.md、RUNTIME_ROUTER.md、SKILL_FILE_INDEX.md 和 TEMPLATE_INDEX.md。旧版本化入口只作兼容指针，不进入默认运行链。
