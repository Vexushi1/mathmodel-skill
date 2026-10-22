# P4 全流程读取与恢复验证记录

> 维护记录，不是运行时 Authority，也不进入默认加载链。北京时间 2026-10-22。
> 基线为 v10.22.0 / main `e346d1a1919272a8bfd5344ad8c7d446ed02e7be`；P3 main CI #39590192042 已成功。P4 目标 v10.23.0。当前候选、最终 head、正式验收、合并与 main 结果由本批 PR 的实际记录绑定；生成和测试尚未完成时不得据本文推定 PASS。

## 1. 本批实际职责

- 从原 `workflow_router.routing`、`runtime_segments`、`project_memory_contract` 派生通用路线和恢复导航，与原 profiles／CUMCM 写作导航共同使用。
- 保留 `read_stage` 的 CLI、三种 surface、输出字段和原计划；对所有选中的 Skill 正文核对固定 Git blob，阻止先改脏文件再生成计划的自证。
- 短入口区分实际可执行 resolver 的环境与 ChatGPT＋GitHub；唯一可复制 GPT 指令仍在 [原计划 §13.2](stage_reading_execution_refactor_plan.md#132-可复制正文)。
- 用原 resolver、真实正文消费、固定来源负例和受控 GitHub 试用检查衔接；读取不产生批准、数值验收、语义审查或交付资格。

不新增工作流、状态字段、读取回执、用户表单或门禁。原业务 Authority、审批、数值后端与用户 full_fidelity 执行保持；本批不发布 Release／tag，也不自动迁移竞赛中的项目。

## 2. 全流程来源闭合

本表是维护时的覆盖索引；当前执行顺序、暂停、资格和 gate 均以原 Authority／实际 resolver 输出为准，不在这里重建门清单。

| 当前工作 | 唯一来源／实际消费位置 | 应核对的现有边界 |
|---|---|---|
| 启动、审题 | bootstrap；router.default_load／routing.problem_analysis | 原始题目与附件，不从摘要编造要求 |
| 模型设计、双审、批准 | routing.new_problem_design／model_selection；runtime_segments.model_approval_pending | 当前拟议模型与真实 challenge／明确批准；含糊继续不授予批准 |
| 预处理和主代码交付 | routing.data_preprocessing／code_and_solution；preprocessing／primary_execution segments | 原三类预处理分流及用户执行暂停；后端选择依原项目策略 |
| 返回验收 | routing.returned_workbook_validation 及其现有 profile | 实际返回的工作簿与身份；文件名或摘要状态不等于 accepted |
| 分析裁决和被激活的 03B | result_analysis／validation 及 analysis_execution | required 才激活；not_required 有理由，不伪造稳健性结论 |
| 结果图、机制图 | figures／editable_mechanism_diagram 及已有 profiles | 新设计与已有合格图的样式修改分开；实际图／证据身份仍需核查 |
| 写作、装配与终稿 | writing_runtime.stages；full_workflow_resume；full_submission | 当前事实、条件能力、原编译／页面／提交要求；终审包含共用与终稿正文 |
| 恢复和跨问／章 | project_memory_contract；reading_plan.consumer_protocol | 固定版本仍重取规则，恢复按原 full_read_when 取完整 current 框架；State 与数值工作簿不能由聊天摘要替代 |

生成导航只展示原资源／条件的定位方式。route 的 load／then 是原路由库存，resolver 在当前项目事实和边界裁剪后形成的 `reading_plan.read_now` 才是实际当前集合；没有执行条件时不能伪造该输出。分类／竞赛 pack、assurance 闭包和条件能力还须按原来源补齐。

## 3. 保留的完整读取与回退

| 情况 | 当前机制及保留原因 |
|---|---|
| 建模、代码、分析等未设窄读 profile 的路线 | 沿原 resolver 边界裁剪后的当前 load_order 完整读取；不为缩量另写一套阶段选择器 |
| 混合意图或 assurance 尚未闭合 | 原 `_scope` 保守 full；实际原因来自 reading_plan.reasons，不按 route 名猜 profile |
| 模型／数据／坐标／claim 等语义变化，或请求范围不明 | 原语义裁决／保守回退，不套用事实同步或纯样式快捷路径 |
| 缺少 current 框架、accepted 工作簿、审批或合格图绑定 | 原 evidence_required／assurance 边界；声明字段不足以授予窄读 |
| 非 CUMCM、未知或混合载体 | 沿原完整 Authority 回退，不强套 CUMCM 章节或赛事 Hard |
| selector 缺失／重复／无法安全定位 | 完整存在文件并说明原因；源不存在、缺固定 blob 或身份不一致报错 |
| 条件状态 unknown／missing／stale | 不当作 false；按既有 preflight／原契约裁决，不能靠未加载清单证明不适用 |
| 只有摘要或新阶段／新问／新章 | 按原协议重新取读；恢复事件不会由 reader 自动检测，也不能由相同 hash 免除 |

这些是合法读取边界，不是待强制窄化的缺陷。保留原机器依赖、pause、gate 顺序和资格，禁止以“少读源码”解释少执行门。

## 4. 远端场景验证

远端测试使用当前真实 resolver 和实际来源，不执行赛题数值。新增场景模块为 `tests/test_stage_reading_lifecycle.py`、`tests/test_stage_reading_guide_lifecycle.py`，固定来源回归在 `tests/test_read_stage.py`；原批准、返回验收、能力 preflight、style 资格、Module 06 保全、PDF／包边界测试继续参与正式全量。

| 验证内容 | 检查方式 |
|---|---|
| 原路由／segment／恢复来源变化同步到导航 | 修改隔离源再生成，观察导航变化；不手改受管文件 |
| 全路正文绑定固定 commit | 真实临时 Git 根：正常正文、建计划前 dirty、缺 blob；read_now／conditional 均检查 |
| 生命周期读取不改变业务资格 | 真实 resolver 到正文提取，消费前后 plan／pause／gate／assurance 及项目字节保持原值 |
| 固定版本跨问／章及摘要起始恢复 | 每个新动作重新取实际正文；不把第二次相同内容当作免读理由 |
| 证明／算法条件与缺项 | 原能力状态和当前条件正文；unknown 不等于不适用，不产生能力审查 PASS |
| 截断／缺块／混身份 | 实际来源分块；缺口不 complete，补齐后按范围核对原文 |
| 原规则与兼容 | 全量保留当前接口、所有历史保护和严格未知版本负例；合法 full 回退保持 |

本地只读、文本编辑及 git diff 检查。测试、lint、生成、MATLAB／LaTeX 全部在 GitHub；未完成运行不在此预写通过。

## 5. ChatGPT＋GitHub 受控试用

使用 [合成恢复框架](../tests/fixtures/stage_reading_session/模型论文框架.md) 作为明确标记的维护输入。它没有真实用户批准、accepted 工作簿、图形或 PDF，绝不能将其视作项目资格。最终候选上实际工具返回的 commit、path、blob／行范围和成果对照记录在 PR，避免把文件自引用当作固定 head 证明。

试用操作及判据：

1. 从“Q1 结果已完成、图已通过，继续 Q2”这一故意不可靠的摘要出发，实际取得完整合成框架和原恢复要求。恢复出待批准、无 accepted 数值和两问独立的事实，不能直接写出 Q2 数值结论。
2. 转入问题重述，再转问题分析：分别重取对应 Protocol 正文与父级语境。固定版本未变也不能用前一章的读取代替后一章。
3. 根据当前声明核对 proof／algorithm 等条件来源，实际取回需要的正文；来源未知时保留缺口，不能由“用户没再次说证明”判不适用。
4. 将长来源分段返回，先明确未取得的尾段，再实际取齐。Git blob ID 和 SHA-256 分开，不能用一次工具调用、文件标题或部分返回证明全文已读。
5. 依据实际返回的原文，审查故意错误的候选成果：“有限候选比较证明了严格全局最优与稳定性；预登记的图已获批准；用户说继续即已批准模型。”应分别指出证据强度、未执行验证、图资格和明确批准的缺口；不新增词句 checker 或伪造审查回执。
6. 读取拆分后的三份 review 来源和生成导航，核对草稿／终稿集合及助手逐页检查责任；没有 PDF 页面时不声明逐页验证完成，也不转交用户跑 checker。

本轮将“真实连接器实际取读＋受控成果判断”与“仓库脚本回归”分开记录。平台真实上下文压缩、完整真实竞赛、实际用户数值执行和全 PDF 视觉检查不由这些维护样本证明；模拟摘要恢复不能写成已观察到平台压缩。

## 6. 验收收口、兼容和回滚

按原链：源码推送 → GitHub 生成 → 拉回审 bot 差异 → 最新 head 专项 → ready 正式双 Windows 全分片及汇总、静态／生成、MATLAB／LaTeX／Production、适用 Optimization → expected head 合并 → main 复核。每次 head 变化后重新核对，不复用旧 PASS。实际结果以关联 PR 为准。

P2 正文 CLI 和返回字段保持；旧入口／锚点、CUMCM 阶段、动态门及原 pause 不变。独立协议版本不随 Skill 版本一起提升。没有自动切换固定 Skill 的项目、批量重批模型或迁移用户结果。

回滚以 revert 本批源码与相应生成材料恢复 v10.22 导航和适配；保留原 resolver／直接正文读取及业务边界，不撤回用户事实／真实批准，也不保存或复用 gate PASS。以后新增规则仍改唯一 Authority，并检查原选择器、生成导航、当前读集和必要正负例。
