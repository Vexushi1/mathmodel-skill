# P3b 写作角色来源映射

本文件是 Skill 全面优化计划 P3b 的维护证据，不建立新的正文写作 Authority。

## 修改简报

- **修改主题**：P3b——逐章/局部写作读取与 AI Cleanup / Review 职责收束。
- **当前版本**：9.1.0；起点 main 为 `9cb5005b780c278953463d1ebeb891928974bb1f`（P3a #154 已合并）。
- **目标版本**：本 PR 不修改 release carrier；最终 minor release 在 P9 裁决。
- **变更等级**：minor-compatible / semantic-preserving refactor。
- **直接目标**：让 Runtime 只负责“何时读什么/激活什么”，Protocol 只负责普通正文数学叙事，Cleanup 只负责表达清理且保护必要推理，Review 只负责检查/分级/返修/交付；减少跨文件重复解释，局部写作不扩大为无关全文工作。
- **明确不做**：不修改模型、求解、工作簿、数值验证、Formula/Algorithm/Proposition 的数学定义，不进入 P4 框架实例化，不调整 RUN_CONFIG，不改 MATLAB Figure Skill，不改变赛事模板一级骨架。
- **兼容性**：现有 CUMCM Template-First 顺序、逐问 Preflight、MCM/DOCX full-authority fallback、所有 LaTeX/审计/编译 gate、项目状态和旧项目保持兼容。
- **迁移**：无用户项目迁移；已有 Framework/Algorithm Trace/Proposition/Title Claim 不重写。
- **回滚**：恢复 P3a 的 writing files 与 P3b 测试/映射，重新生成索引；不触及用户数值产物。

## 唯一 Authority 边界

| 能力 | 唯一业务 Authority | P3b consumer 职责 |
|---|---|---|
| 复杂数学语义、Formula Role、命题、Algorithm Trace、Claim Strength、Citation Evidence、Model/Solver/Validator | `core/writing_reasoning_contract.yaml` | Runtime 只按状态激活；Cleanup/Review 只引用与核验，不复述完整定义 |
| 普通正文组织、MODEL→SOLVE→RESULT→VALIDATE、Local Narrative、Paragraph/Cross-File Handoff、结果解释 | `modules/05_writing/paper_writing_protocol.md` | 保留可直接用于当前章节写作的规则，减少状态机/治理重复 |
| 写作时机、逐章 read→write→gate、逐问 Capability Preflight、条件资源、fallback | `core/writing_runtime_contract.yaml` | 不解释数学规则，只声明状态到资源/阶段的映射 |
| 固定 CUMCM 一级结构与槽位 | `templates/latex/cumcm/hsk/template_manifest.yaml` | Protocol/Cleanup/Review 不复制一级骨架细节 |
| LaTeX 载体与环境 | `modules/05_writing/latex.md` | 仅 Adapter，不决定正文数学内容 |
| 表达清理 | `modules/05_writing/ai_cleanup.md` | 只做 Keep / Compress / Re-subject / Delete 等表达动作与保护检查 |
| 终审 | `modules/06_review_delivery.md` | 只做 scope、severity、location、repair、delivery decision，并引用上游 Authority |

## 必须保留的能力回归

P3b 不以“文件更短”为成功标准。下列能力必须保持：

1. `final_model_relation` 与必要 `key_bridge_relation` 在 Cleanup 后仍可恢复，关键桥接不得因“不是最终 solver 方程”被删掉。
2. Proposition 为 `planned/current` 时，即使用户本轮没有再次说“证明”，仍自动激活 reasoning Authority 与 proposition pack；candidate 只触发必要性审查，不自动造命题。
3. Algorithm Presentation 为 `stepwise/pseudocode` 时，即使用户本轮没有再次说“伪代码”，仍自动激活 current Algorithm Trace 与 algorithm-flow pack；`not_needed` 不生成装饰算法框。
4. 逐问关键状态 `missing` 必须进入 `needs_adjudication`；`stale/review_required` 不得被润色成 current。
5. 数值精度、单位、citation key、claim scope、solver precondition、Reduction Provenance 与真实验证边界不得被 Cleanup 改弱或改强。
6. 单问/局部修改只读取当前目标片段及真实依赖；除非发生跨问、Title/Abstract、assembled seam、全篇一致性或 final review 风险，不得机械扩大为全文重写。
7. MCM/ICM、DOCX 及没有当前独立 Template Manifest 的路径继续 full-reasoning fallback，不套用 CUMCM 固定骨架。
8. final review 可以分批读取物理文件，但必须形成完整 assembled coverage；不得抽样几个章节就宣称全文通过。

## 去重原则

- **Runtime**：状态名称、resource activation、gate、fallback 可以详细；模型为什么成立、段落为什么这样写不在 Runtime 展开。
- **Protocol**：保留作者真正写当前段落需要的数学叙事规则；项目状态字段、hash/stale 传播、机器严重性枚举只引用 Authority。
- **Cleanup**：保留“可以改什么、不能删什么、改后复核什么”；模型命名、优化表达、图结果叙事、命题、数值、引用的完整规则不再复制成长清单。
- **Review**：保留“审什么、如何分级、定位到哪里、如何返修、何时可交付”；正文写法本身回指 Protocol/Reasoning。

## 验收证据

P3b 新增回归至少覆盖批准计划中的 FW05–FW09：planned proposition + pseudocode 自动激活、missing state 不静默降级、Cleanup 保留必要 bridge derivation、MCM/DOCX 不误套 CUMCM、full-paper review 完整覆盖而非抽样。同时比较 P3a→P3b 的 runtime/route/gate 行为，除本 PR 明确新增的 writing scope/consumer metadata 外不得出现无关变化。
