# Writing Validation W0 基线与候选裁决

> 本文件是 `docs/writing_readability_validation_slimming_plan.md` 的 W0 维护证据，不是新的 Writing / Runtime / Review Authority。它只记录当前调用关系、同环境测量、正反例和 W3 准入裁决；不修改任何 severity、Gate、Schema、Project State 或论文事实。

## 1. 基线、范围与复算入口

W0 基线主分支：`main@f489934efd633b1c5c5dc0930858aa4c49f6ca3a`。  
实际测量绑定 Optimization baseline evidence **#347**，workflow head：`8c543f9c6a0966d84f7a357a7fc3c12069c8f5bb`，artifact `optimization-p2-evidence` digest：`sha256:f3b906817b9ba1c5425733fffd9f5a87c3b8e3f0d2e49f5f4bcc7f01d1e85cd0`。

维护复算入口：

```bash
python scripts/measure_writing_validation.py
python scripts/measure_writing_validation.py --repeats 30 --warmup 5 --output writing-validation-w0-baseline.json
```

测量环境：Python **3.12.14**，`Linux-6.17.0-1022-azure-x86_64-with-glibc2.39`，计时器 `time.perf_counter_ns`。计时只作描述性维护证据，**不是通过阈值或 Gate**。

测量源指纹：

| 对象 | SHA-256 |
|---|---|
| measurement driver | `86e6951ba4565bb001e7e87fe1dacab8ad0250ad316b1840f5aa5e7e9c29c3c6` |
| `core/writing_runtime_contract.yaml` | `268de8b22875898797d3933841e4ee1170f7f2403649480a05bd768c5117c575` |
| `scripts/audit_paper_prose.py` | `7a534dcfd20a0ab67577a0b635b555a47f1df42a5d7ad245e936f29494ba4ccf` |
| `scripts/audit_v8_writing_surface.py` | `f897e0286789e773e9044d9d86ec9c5062abfd92495816021e21cc10f4fad2e9` |
| `config/prose_audit_patterns.yaml` | `b31c7fe810dc420b84195e525b6d13c93b2d4bb81d3113c0b1704daa1d36a8f1` |

## 2. 活动调用图与输入边界

当前 CUMCM 普通写作的相关调用链为：

```text
draft_semantic_review
  ├─ assembled_seam_sweep
  └─ audit_v8_writing_surface.py
       ↓
AI Cleanup（正文发生写入）
       ↓
LaTeX assembly（源码发生装配）
       ↓
audit_latex_project.py
  └─ audit_paper_prose.py
       └─ audit_v8_writing_surface.py
       ↓
compile / PDF
       ↓
final_review_and_delivery
```

裁决如下：

| 候选 | 输入/阶段 | 当前调用 | W0 裁决 | 理由 |
|---|---|---:|---|---|
| draft surface audit | Cleanup 前 draft | 1 次/该 stage | **保留** | 用于在 Cleanup 前定位写作表面风险 |
| formal nested surface audit | Cleanup + assembly 后 flattened LaTeX | 1 次/formal audit | **保留** | 与 draft 不是同一输入；formal source/PDF 绑定要求复验 |
| draft ↔ formal 跨阶段复用 | 中间存在 Cleanup 和 assembly 写入 | 2 个不同阶段 | **拒绝共享/缓存** | 不满足“输入、依赖、范围、模式相同且无中途写入” |
| formal → surface 嵌套 | 同一 formal audit | 1 次 | **保留** | `audit_paper_prose.py` 明确消费 surface audit；不存在同一 formal 输入的第二次 surface 调用 |
| surface 内部文本预处理 | 同一 direct surface call | 随 fixture 为 4 / 6 / 9 次 | **当前不优化** | 绝对耗时很低；为数毫秒收益引入共享 context/API 不合算 |
| 三脚本物理拆分 | project/formal/prose/surface 职责不同 | 3 个文件 | **保留** | 文件数不等于重复执行；正式入口、底层实现、表面诊断职责不同 |

因此 R8 的结论不是“存在三个脚本所以删除两个”，而是：**跨阶段复验有必要，formal 嵌套只有一次，当前唯一可见的同阶段重复预处理不足以证明值得重构。**

## 3. 同环境成本测量

固定 30 次计时、5 次 warmup。fixture 仅用于维护测量，不代表赛事模板或论文质量标准。

| Fixture | bytes / lines | Surface median | Formal 含 nested surface | Formal 去掉 nested surface | Surface 预处理调用 |
|---|---:|---:|---:|---:|---:|
| small | 761 / 18 | 6.1219 ms | 6.4034 ms | 0.2793 ms | 4 |
| medium | 3659 / 74 | 7.0808 ms | 7.8811 ms | 0.7423 ms | 6 |
| large | 12344 / 230 | 9.7019 ms | 11.8347 ms | 2.0588 ms | 9 |

输入 SHA-256：

- small：`82c27108a141647ce8c1751bb65cf4e2fee4dd24dbfdae9d4d143033544fda24`
- medium：`cdc97b632c0f5cb4a77b80043d95cb2b04ac16516d39cb1b8c2985b9c030dabb`
- large：`9c225e0952cb98633f9f99ff6a7687dc1f51f3d5a9343543758c60cce454b31f`

解释边界：surface audit 确实占 formal prose audit 的主要 CPU 时间，但即使 12.3 KB / 230 行 synthetic 大样例，direct surface median 仍约 **9.70 ms**，formal 总 median 约 **11.83 ms**。当前没有证据支持为了这一级别的绝对成本引入持久缓存、跨阶段信任或新的共享 context 协议。

## 4. R7 正反例快照

W0 对可能放大流程负担的 review finding 只做成对证据裁决，不批量降级。

| Case | 当前 finding | 当前 severity | 配对结果 | W0 裁决 |
|---|---|---|---|---|
| 五个独立数学任务二级小节 | `question_subsection_granularity` | review_required | **误报**：仅因数量 >4 触发 | **准入 W3** |
| 变量/目标/约束/汇总机械拆分 | `possible_mechanical_model_subsection_split` | warning | 能用具体结构证据识别 | **保留** |
| Result 后直接进入验证、无风险桥 | `result_validation_bridge_risk` | review_required | 缺 bridge 时触发 | **保留** |
| Result 后明确说明待检验风险 | 同上 | — | 不触发 | **保留现级别** |
| Solver 首段直接报算法 | `solver_first_narrative` | review_required | 无结构理由时触发 | **保留** |
| Solver 先说明非凸/约束等结构 | 同上 | — | 不触发 | **保留现级别** |
| 明确功能标题 RESULT → SOLVE 倒置 | `question_stage_order_risk` | review_required | 倒置时触发 | **保留** |
| MODEL → SOLVE → RESULT 正常顺序 | 同上 | — | 不触发 | **保留现级别** |

关键快照输入均有独立 SHA-256，记录在 #347 artifact 的 `writing-validation-w0-baseline.json` 中。

## 5. 其余 review_required 库存

当前 `audit_paper_prose.py` 中除上表 count-only 候选外，还存在以下 review_required：

- 载体/版面：`figure_caption_before_graphic`、`table_caption_after_tabular`；
- 摘要/关键词：`abstract_contains_figure_or_table`、`abstract_contains_display_math`、`keyword_count`；
- 框架显式未闭合状态：`optimization_abstract_objective_pending`、`framework_subsection_granularity_pending`；
- 中文国赛默认结构：`standalone_conclusion`、`merged_assumption_symbol_section`、`missing_problem_background`、`missing_problem_statement`、`legacy_problem_requirement`、`formula_in_problem_analysis`。

W0 对这些项的裁决均为 **保留原状**：本轮没有为它们建立足以支持 severity 改动的误报/漏报对照，因此按计划“没有证据则保持原状”。

`config/prose_audit_patterns.yaml` 中三个 review_required 表面检查——`result_validation_bridge_risk`、`question_stage_order_risk`、`solver_first_narrative`——已由 §4 的成对正反例验证，均保留。

## 6. W3 唯一已批准候选

W0 只批准一个检查减重候选进入 W3：

**`question_subsection_granularity` 的 count-only review_required。**

证据链：

1. Authority/Protocol 已明确二级/三级标题不按数量判质量，Part F 又明确三级不设数量配额；
2. 当前实现仅以 `len(subsection_titles) > 4` 触发 `review_required`；
3. W0 正例中五个独立数学任务被该规则单独误报；
4. 机械拆分反例已有更具体 `possible_mechanical_model_subsection_split` warning；
5. `framework_subsection_granularity_pending` 仍保留显式项目状态未闭合的 review_required，不会因删除/合并 count-only finding 而丢掉真实待裁决状态。

W3 允许的最小方向：**合并/移除 count-only `question_subsection_granularity` finding，保留具体机械拆分提示和显式 framework pending 审查。** W3 必须用相同正反例证明硬错误集合不减少，并保持 CLI、报告结构和 formal audit 入口兼容。

除此之外，W0 **没有批准**：

- 批量把 review_required 改成 warning；
- 删除 `audit_paper_prose.py` 或 `audit_v8_writing_surface.py`；
- 跨 draft/final 持久缓存；
- 新 trust token / “已检查永久通过”状态；
- 修改正式 Gate、Review schema、Project State required 字段；
- 裁剪 CI、Python 版本矩阵或真实 LaTeX 编译。

## 7. W0 完成条件核对

- 调用图：已闭合；
- 输入阶段/指纹：已闭合；
- severity 库存：已核对；
- 调用次数：已实测/静态闭合；
- 同环境耗时：已由 #347 artifact 获取；
- 正反例：R7 关键候选已成对；
- 建议与接受/拒绝理由：已逐项记录；
- 不确定项：全部保留原状；
- Hard/数值/模型/状态/交付边界：未修改。

因此 W0 的维护证据已经完整，**W3 只能从 §6 的单一已批准候选开始**。


## 8. W3 实施接续

W0 本文 §1--§7 保留为修改前的不可变维护基线。W3 从该基线只消费 §6 的单一准入项：移除仅由二级小节数量大于 4 触发的 `question_subsection_granularity` review finding。

W3 不改变本文对其它候选的“保留/拒绝”裁决；特别是 `possible_mechanical_model_subsection_split`、`framework_subsection_granularity_pending`、三个 surface review_required、跨阶段复验和 formal→surface 嵌套均继续保留。W3 后 current measurement harness 会把 `many_independent_subsections` 的目标结果更新为“不产生 count-only finding”，但本页记录的 #347 历史 artifact 与源指纹不回写。
