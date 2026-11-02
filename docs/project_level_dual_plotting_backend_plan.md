# 项目级 Python / MATLAB 双绘图后端：实施修改计划

> 文档性质：**Plan Only — 本次只制定计划，不修改功能代码**  
> 仓库：Vexushi1/mathmodel-skill  
> 当前核查基线：main `b96a7a233913f05740ff60df763cff72371db2ae`，Skill `10.23.3`（2026-11-02）  
> 计划分支：`docs/project-level-dual-plotting-backend-plan`  
> 实施目标版本：**暂定 v10.24.0（minor）**；实施前须重新确认最新 main 版本  
> 治理依据：`core/bootstrap.yaml`、`SKILL_CHANGE_GOVERNANCE.md` v1.0.6

## 0. 修改简报（后续功能 PR 必须引用）

| 必填项目 | 内容 |
|---|---|
| 修改主题 | 新增 Python 正式数据绘图后端，保留 MATLAB；一个赛题/项目只选择一次绘图后端 |
| 当前版本 | 本计划基线 10.23.3 |
| 目标版本与等级 | 功能实现拟定 10.24.0 / minor；**当前计划 PR 属 docs，不升级版本** |
| 直接目标 | 使全部问题的结果图和条件启用的项目级预处理图，统一采用项目根选择的 Python 或 MATLAB；由 Skill 对全题需求择优选型 |
| 明确不做 | 不重构现有 Figure Evidence 设计、图证据层级、科研绘图规则、Caption、人工图审批；不改变 Model/Solver/03A/03B、数据工作簿、LaTeX 论文骨架；不淘汰 MATLAB 绘图 |
| 直接 Authority | `modules/04_figure_evidence.md`、`core/output_contract.yaml`、`core/workbook_schema.yaml`、`core/project_state.schema.yaml`、`core/state_transition_contract.yaml`、`core/global_preprocessing_contract.yaml` |
| 关联 Authority | `core/workflow_router.yaml`、`core/module_manifest.yaml`、`core/user_execution_contract.yaml`、`core/hsk_core_policy.md`、`core/code_quality_contract.yaml` |
| 关键实现 | Python 绘图模板；语言无关绘图脚本状态、项目快照与同步、B2 Figure Source、读路径与正式提交包适配 |
| 禁止触碰 | 已验收数值工作簿及数值身份、旧模型批准、历史论文、其他题型模块、legacy 默认路径；禁止人工修改 MANIFEST/生成索引 |
| 兼容与迁移 | 老项目 MATLAB 图路径、状态、哈希、批准和模板可读；默认不迁移；更换绘图后端只重验图链 |
| 验收 | Python/MATLAB 双绘图后端、交叉求解后端、预处理三分支、03B 条件分支、B2/LaTeX/ZIP、Windows 3.10/3.14、MATLAB native、lint/生成索引/适用优化基线 |
| 回滚 | 撤销新功能 PR 的行为更改；保留 MATLAB 原执行路径与历史 Schema 读侧，不重算、重写用户已有数值 |

**确定需求**：添加一个 Python 渲染后端；现有 Figure Evidence 规则保持原有数学与视觉语义。Python 与 MATLAB 都可以成为整个赛题的绘图工具，但**不允许按问题切换**。模型求解后端与绘图后端仍互相独立。

## 1. 真实仓库现状与必须改的耦合

### 1.1 已核查事实

- 仓库最新核查基线的 main SHA 与版本见文首；核查时开放 PR 为 0。实施时必须重新检查，**不能复用此 SHA 作为未来最新版事实**。
- 正式结果图由 `modules/04_figure_evidence.md` 作为唯一 Figure Authority；当前活动 MATLAB 模板位于 `templates/matlab/`。
- 当前产物固定为 `问题X求解/qX_plot.m`；若 `preprocessing_decision=project_level`，额外生成 `数据预处理/data_process.m`，只读取统一工作簿。
- `core/output_contract.yaml` 以 `matlab_script`、`preprocessing_matlab_script`、`matlab_scripts`、`matlab_figure_contract`、`stage_requirements`、`stale_propagation` 等字段配置正式产物。
- `core/workbook_schema.yaml#matlab_handoff` 的映射要求包括 `matlab_script`，表头采用精确唯一匹配。
- `core/project_state.schema.yaml` 使用 `matlab_script`、`artifact_hashes.matlab_script`、`validated_artifact_hashes.matlab_script`；`core/state_transition_contract.yaml` 使用 `matlab_script_changed` 触发下游失效。
- `scripts/project_snapshot.py` 硬查 `qX_plot.m`，用 MATLAB 源码语法发现 title/export/workbook；`scripts/sync_project.py` 硬查 `data_process.m` 和相关 read-set。
- `scripts/claim_figure_source.py`、`scripts/reading_plan.py` 正式图源检查只接受 .m 和旧哈希；`scripts/submission_requirements.py` 及 ZIP 检查存在 MATLAB 文件假设。
- `.github/workflows/optimization-baseline.yml` 有可选 MATLAB publication preview；现有 MATLAB native CI 还验证**数值求解**，不能因为绘图改 Python 而删除。

### 1.2 绝不能使用的捷径

1. 仅新建 `q1_plot.py` 而不改状态/同步：正式交付仍会因缺 `q1_plot.m` 失败。
2. 在 `matlab_script` 字段里填 Python 路径：旧 Figure B2 校验会把 Python 路径当作错误 MATLAB 来源，造成状态歧义。
3. 用 `execution.solver_backend` 推导绘图语言：会错误禁止 MATLAB 求解 + Python 绘图、Python 求解 + MATLAB 绘图。
4. 删除旧 MATLAB 状态字段/测试：已有项目验收身份被破坏。
5. 因绘图语言变化撤销 Human Model Approval、重算 03A/03B：这是错误的失效传播。
6. 将两种语言各复制一份 Figure Evidence 规则：产生双 Authority 和后续版本漂移。
7. 对每一问存 backend 或建立新审批节点：违背项目级唯一选择与低维护成本要求。

## 2. 目标架构、决策时机与边界

### 2.1 项目根唯一后端

**拟议新状态（当前未实现）**：

```yaml
execution:
  solver_backend: matlab                 # 原数值求解后端，独立
plotting:
  backend: python                       # 全赛题只允许 python 或 matlab
  selection_reason: "全题科研图多为统计、Pareto和多面板图"
subproblems:
  Q1:
    plot_script: "问题一求解/q1_plot.py"
  Q2:
    plot_script: "问题二求解/q2_plot.py"
```

- 上述示例仅适用于**新 Python 绘图项目**。新 MATLAB 项目以及旧项目继续使用原有 `matlab_script: 问题一求解/q1_plot.m` 与其原有 hash，不要求重命名为 `plot_script`。内部统一脚本解析入口负责返回有效的 `backend/path/hash_field`。
- 根状态 `plotting.backend` 是**选型的唯一事实源**；逐问仅记录对应脚本身份，不重复后端选择；历史合法 MATLAB 项目没有此字段时按原有身份继续运作。
- `auto` 可作为用户请求的意图，但不能作为已解析、已锁定的 backend 值。
- **选型时间**：Module 02 只作全题可视化需求预估；进入 Figure Evidence、准备生成**第一份正式绘图脚本之前**再复核全题图需求与环境，随后一次性选择并锁定。不提前新增模型设计门禁，也不增加 Human Model Approval。
- 用户明确指定且可行则遵循；未指定时由 Skill 对**全题**预期图形、数据源、环境、维护成本综合判断。都可行时 Python 默认优先；Simulink 原生图形或确有必要的 MATLAB 图形能力时可选 MATLAB；不只看 Q1，也不只看求解语言。
- 环境尚未实际验证时，写明依赖/字体/许可证的未核验事实；不宣称已运行；若均不可行，说明阻断，不悄悄按问题切换。
- 首份正式脚本交付后后端即锁定。旧项目若已有合法 `matlab_script`，即使根 `plotting` 缺失，也不能被当作无历史选择的新项目；只有用户明确提出全项目图迁移才能更换。

### 2.2 两种合法布局

```text
plotting.backend=python：
  数据预处理/data_process.py        # 仅 project_level
  问题一求解/q1_plot.py
  问题二求解/q2_plot.py
  ... 问题N求解/qN_plot.py

plotting.backend=matlab：
  数据预处理/data_process.m         # 仅 project_level
  问题一求解/q1_plot.m
  问题二求解/q2_plot.m
  ... 问题N求解/qN_plot.m

求解阶段独立：
  solver_backend=python → 各问 Python 主求解及按需深化代码
  solver_backend=matlab → 各问 MATLAB 主求解及按需深化代码
  求解结果都以既有 accepted Excel 工作簿作为 Figure 数值事实源
```

- 同一个赛题全部**工作簿驱动结果图和预处理证据图**必须使用相同后端。同一问题不能有两个同时被认定为 current 的正式 `plot` 入口。
- `not_needed` / `question_local` 不创建项目级预处理图入口；`project_level` 时必须使用当前根后端对应 `data_process.*`。
- 仍按 03B Gate 消费 `问题X结果深化分析.xlsx`；若 Gate=not_required，不为绘图虚构 03B 数据。
- draw.io、TikZ、GeoGebra 的题目专属**非数值机理图**保持现有 Mechanism Diagram Backend Selection Gate，不纳入“统一工作簿绘图语言”的限制；它们不能成为擅自改换结果图后端的借口。
- 默认只提供脚本供用户本地执行与人工查看；仅按实际需要/要求导出图，不强制生成图文件、图表子目录或二次报告。

### 2.3 必须一字不减保留的语义

- Figure Evidence L1—L4、Scientific Figure Synthesis、Basic-form Challenge、Composite Encoding、Scientific Rendering Profiles、Figure Layout / Enhancement、Publication Rendering Grammar、Portfolio QA。
- **主结果/深化图的结论性数值**应取自当前 accepted 主工作簿及按需 accepted 03B 工作簿；`not_needed/question_local` 时按原 Figure Contract **允许读取合法原始数据**辅助解释，`project_level` 则依 `covered_raw_sources` 用统一工作簿替代已覆盖的原始源，未覆盖的独立辅助附件仍可按原规则读取。所有实际来源都要精确表头唯一匹配，保留数据粒度、单位、NaN 和真实数值；禁止从摘要反推明细。
- Figure Contract 说明 Core Conclusion、Evidence Level、Primary Question、caption、证据来源与 Paper Location；正式图无整体 title/sgtitle，图题由 DOCX/LaTeX caption 承担。
- 人工看图/语义批准与机器结构审查分离；已批准图片、来源脚本与论文主张继续用哈希和实际引用闭环。
- 项目级预处理图只消费已验收统一工作簿；不能重算清洗/拟合/填补；主求解、深化分析均不得被绘图脚本调用来制造证据。
- 现有 `模型论文框架.md`、`state/project_state.yaml` 和 accepted 工作簿的语义/事实/机器状态分工不变。

### 2.4 绘图后端选择的安全写入协议（实施必须完成）

现有 `scripts/project_solver_backend.py#select_project_backend` 已采用 `ProjectStateSnapshot`、`state_generation`、read-set、`project_transaction.commit_project_state` 和 Framework 同步。**绘图后端应复用这些底层事务能力，但不能复制数值后端迁移的整套归档/回执流程。**

1. **inspect（只读）**：一次性观察项目根状态、已登记各问、`preprocessing_decision`、已有 `qX_plot.m/.py`、历史 `matlab_script` 哈希和图批准；分类 `unselected / selected / historical_matlab / conflict`。不得生成批准、环境成功回执或隐式迁移。
2. **select（首次选型）**：在尚无冲突的当前绘图身份时，携带 `backend=python|matlab`、非空理由、`expected_generation`，以原有项目事务机制原子提交根 `plotting` 和 `模型论文框架.md` 中现有图表记录的简短投影；写前核对完整 read-set 和代际版本，冲突即拒绝并重新读取。
3. **幂等与锁定**：同后端、同理由的重复请求不产生新 generation 或重复记录；已锁定项目的相反请求只能进入**显式图迁移预览**，不是新的首次 select。选型不是人工数学模型审批。
4. **历史连续性**：缺根 `plotting` 但有合法 MATLAB 图身份的项目，继续正常修改原 `qX_plot.m` 并经原 Sync/B2/提交路径维护，不能简单降为只读。必要时由人工明确的迁移请求补根状态。

不新建重复的后端状态登记表、图审美审批或通用事务框架；具体 API 文件名在 Phase 0 核对调用者后确定。

## 3. 新旧状态与兼容协议（必须先定再改代码）

### 3.1 最小增量字段与单一活动脚本解析

- 项目根新增 `plotting.backend` 与 `selection_reason`；当前 `core/project_state.schema.yaml` 顶层为 `additionalProperties: false`，必须明确新增 Schema 属性，不能仅修改 Markdown。
- **新增 `plot_script`/`artifact_hashes.plot_script`/`validated_artifact_hashes.plot_script` 仅用于 Python 当前绘图脚本**。MATLAB 继续使用现有 `matlab_script`/同名哈希及读写/验收行为。一个内部 `FigureScriptRef = (backend, path, hash_field)` 供 Snapshot、Sync、Read Plan、B2 和提交包复用，不得让每个消费者重复猜测。
- 为 Python 当前脚本加入 `plot_script_changed` 和所需 artifact layer；MATLAB `matlab_script_changed` 保持原有意义。同一当前图身份变化只能产生一个对应脚本事件；新增 Python layer 同时必须加入上游数据/模型/工作簿失效时的适用下游图层映射。
- **项目级共享预处理图暂不新增重复的项目状态/持久哈希层**。保留旧 MATLAB 分支的 `preprocessing_matlab_script` 活动角色，Python 分支可新增仅对 Python 生效的 `preprocessing_python_plot_script` 逻辑角色，**由 `stage_requirements(scope, output_contract, state)` 按 `project_level × plotting.backend` 互斥选择**。不要把 Python 脚本写进名为 MATLAB 的现有状态/正式产物字段；由 read-set、accepted 预处理工作簿、Framework 图登记与正式图片核对身份。只有真正有消费者需求时才增加持久状态字段。
- `figure_bundle`、`approved_figures` 和 Figure→Paper 现有事实与批准边界不改。这里为接口草案，最终使用前必须根据真实 State 写入者与所有消费者逐项复核。

### 3.2 历史 MATLAB 项目保护：不只可读，还必须可维护

1. 旧项目缺 `plotting` 但有合法 `matlab_script` 时，沿用原有 MATLAB **读取、绘图修改、状态同步写入、Figure Source 复验、LaTeX/ZIP 交付**路径；默认不补新状态，也不重新签发图批准。
2. `matlab_script`、`matlab_script_changed`、`matlab_handoff`、`preprocessing_matlab_script` 及旧哈希不仅是历史兼容输入，还是未迁移 MATLAB 项目的合法当前入口；Python 源码不得伪装进这些字段。
3. 同问两个 current 绘图脚本、根 backend 与各问/预处理脚本不一致、Python/MATLAB 哈希交叉挪用都应 fail closed。旧项目目录里有不属于当前身份的存档 .py/.m 文件，不等于允许它成为第二正式入口。
4. 用户明确要求后端切换时，**本次 minor 必须能够识别并拒绝无预览的直接改选**，给出全项目图源及受影响 Figure/论文依赖清单。**自动迁移执行器、自动改写历史脚本及自动回滚工具不作为新增 Python 绘图后端的最低上线要求**；如后续实际需要，应依据当前状态和事务单独规划。人工显式迁移也必须保留 accepted 数值，创建目标图脚本后实际复核并重新批准受影响 Figure，不删除旧 .m，不冒领旧批准。
5. 旧 MATLAB 项目“修改图 → sync --write → B2/论文交付”的回归测试必须通过；本次不移除历史字段，不额外规定强制迁移窗口。

### 3.3 与现有 MATLAB profile 对齐的失效语义

```text
Python 当前脚本变化 → plot_script_changed（一次）
MATLAB 当前脚本变化 → 原 matlab_script_changed（一次）
共享项目级预处理图变化 → 仅真实共享 Figure 来源/图片/论文证据
    → 依原 Figure contract 审查当前图脚本、figure_bundle、Framework/论文绑定
    ✗ 不取消 locked_model_spec / Human Model Approval
    ✗ 不清除 accepted 03A / 03B / 预处理数值工作簿及 RUN_RECEIPT
```

当前 `core/state_transition_contract.yaml#profiles.matlab` 实际包含 `matlab_script / figure_bundle / framework` stale，且把 `validation_status` 设为 `pending`、`result_summary_status` 设为 `stale`。**这属于现行绘图和汇总层的审查语义，不等于取消 accepted 主数值。** 新 Python 图事件必须与之保持必要的同等审查强度；不得为了声称“局部 stale”就悄悄删除现有 `framework` 或汇总检查。更细粒度论文片段优化如果要求更改旧 MATLAB 行为，应另行立项。

同步 `scripts/sync_project.py#_snapshot_transition_events`、`core/output_contract.yaml#stale_propagation` 和实际消费者，确保新旧脚本事件互斥。图源码/图片 bytes 改变时需按已有 Figure 合法流程复验来源和人工外观；纯绘图变更不得被误判成求解后端或核心模型更改。

## 4. 逐文件影响清单

> 下表是实施时**检查范围**，不要求全数修改。每项最终必须在 PR 记录“修改 / 只核查 / 不适用”的结果及理由，避免机械替换所有 MATLAB 字符串。

| 文件/组 | 拟修改原因与方式 |
|---|---|
| `modules/04_figure_evidence.md` | 仍为唯一 Figure Authority；保留完整图形科学性与审美选择规则，只替换语言专属执行/交付表达 |
| `core/output_contract.yaml` | 新绘图后端、脚本名称/路径、stage requirements、哈希、stale、同步/复现产物权威 |
| `core/workbook_schema.yaml` | 新通用 Handoff 指针和字段；精确/唯一表头规则不变，保留 MATLAB Handoff 历史兼容 |
| `core/project_state.schema.yaml` | 根 `plotting`、**仅 Python 使用**的 `plot_script`/hash/layer；保留 MATLAB `matlab_script` 当前可写与语义冲突判断 |
| `core/state_transition_contract.yaml` | 新 Python 脚本事件与原 MATLAB 图/Framework/汇总审查强度相当；数值 accepted 不作废 |
| `core/global_preprocessing_contract.yaml` | `data_process.py/m` 双后端适配；原有**数值预处理脚本禁止使用 matplotlib/seaborn 直接生成论文图**的规则保留，Python 图只由 Figure 阶段执行 |
| `core/workflow_router.yaml` / `core/module_manifest.yaml` | Figure route 的终端产物与后端选择指针；不新增独立重型路由 |
| `core/hsk_core_policy.md` / `core/user_execution_contract.yaml` / `core/code_quality_contract.yaml` | 只核对绘图/求解职责和用户执行边界；按需最少更新语言硬编码 |
| `templates/matlab/q1_plot.m` / `data_process.m` / `README.md` / publication helper | **保留现有功能**；只做必要的兼容性小修，不删除、不整套翻译 |
| 新 `templates/plot/python/`（最终路径先复核） | 最小 `q1_plot.py`、`data_process.py`、必要读表/样式 helper 与 README；不强迫每题生成额外工程包 |
| `templates/figure/*.md` / `packs/artifact/figure.md` / `templates/model/model_paper_framework.md` | 只同步真正写死 MATLAB 的绘图程序/证据链接口，不改图型、布局与 Caption 内容规则 |
| `scripts/project_solver_backend.py` / `scripts/project_transaction.py` | 复用选型事务思路、generation 和 read-set；不重构求解后端或复制数值迁移机制 |
| `scripts/project_snapshot.py` | 解析唯一活动 Python/MATLAB 绘图身份，采用当前 Framework 图表登记与实际文件确认导出；原 MATLAB 路径保留 |
| `scripts/sync_project.py` | 图脚本状态、预处理脚本读集、正式 figures/docx/latex/submission scope 和 ZIP 检查 |
| `scripts/claim_figure_source.py` | B2 图源识别两后端，accepted workbook/图片/批准/片段来源检查不变 |
| `scripts/reading_plan.py` | style-only 的源码与 `approved_figures` 快捷证据按实际 active 后端核对 |
| `scripts/submission_requirements.py` | 根据当前后端精确收集复现脚本；不再全局强制 .m；官方 allowlist 仍独立核验 |
| `scripts/validate_project_state.py` / `scripts/lint_skill.py` / `scripts/lint_skill_checks.py` | 项目级一致性、Schema 和原 MATLAB-only 不变量更新，不删除有价值的检查 |
| `tests/` 的 Figure、schema、sync、submission、read-path、旧 MATLAB 测试 | 保留旧兼容正例、新增 Python 双后端与混用负例；不删除旧有效断言 |
| `.github/workflows/ci.yml`、`optimization-baseline.yml` | Python 渲染与专项 smoke；保留 MATLAB native solve CI、可选 MATLAB 图预览、既有正式 check 名称 |
| `README.md` / `SKILL.md` / `CHANGELOG.md` / 版本入口文件 | 真正实施 Minor 版本时只同步必要说明与版本矩阵 |

**特别说明**：若实现 PR 修改超过 20 个活动文件，必须在 PR 描述中列出不可拆分原因：同一项目后端、State、Snapshot、B2 Figure、Submission 和测试必须保持原子一致，不能形成半新半旧、无法通过正式验收的接口。不可借机重构其他模块。

## 5. 详细执行阶段（Phase 0—7）

### Phase 0：重新冻结基线、风险和修改简报

1. **再次**读取实施时最新 main 的 `core/bootstrap.yaml`、`SKILL_CHANGE_GOVERNANCE.md`、实际 Authority，不使用本计划保存的老 SHA。
2. 获取最新 main SHA、版本、已有未合并 PR/分支；若重叠修改输出/状态/绘图 Authority，先串行处理，暂停写入。
3. 使用 GitHub code search/树浏览精确列出 `matlab_script`、`preprocessing_matlab_script`、`matlab_handoff`、`qX_plot.m`、`data_process.m`、`.m` ZIP 要求、Figure B2/reader 的实际消费者。
4. 建立字段映射表：旧字段→读取端→写入端→建议新字段→历史兼容→需要改的专项测试。
5. 检查 repo 中已有 Python Excel reader、Matplotlib 风格辅助与脚本入口约束，避免重复封装；确定 Python 模板路径和最小依赖。
6. 填写治理规范要求的修改简报、预计文件与禁止触碰范围；在功能 PR 描述中同步。

**Gate**：main、Authority、重叠 PR、状态/哈希消费者全部明确；未解决冲突不可写功能代码。

### Phase 1：项目级 Backend、事务与兼容合同

1. `core/output_contract.yaml` 中增加 Python 的逐问与共享预处理图路径，明确 `project_sync.stage_requirements` 和 `conditional_stage_requirements` 按**项目绘图后端与 preprocessing_decision 联合解析**：历史 MATLAB 沿用原 `matlab_scripts/preprocessing_matlab_script`，新 Python 使用新条件 role；不在所有项目上叠加两套必需脚本。更新 `stage_requirements()` 消费端，solver_backend 完全独立。
2. `core/project_state.schema.yaml` 显式新增项目根 `plotting`、**Python** 逐问 `plot_script`/hash/layer；`validate_project_state.py` 校验一赛题一后端、矛盾脚本、重复身份和旧 MATLAB 路径。
3. 建立一个轻量 `FigureScriptRef` 解析入口和 inspect/select 操作，复用 `ProjectStateSnapshot`、`project_transaction.commit_project_state`、expected_generation、read-set、Framework 同步；同值请求幂等，冲突拒绝，不移植求解后端历史归档。
4. `core/state_transition_contract.yaml` 只新增 Python 脚本事件并对齐现有 MATLAB profile 的 Figure/Framework/汇总审查；同步上游数据/模型/工作簿传播和 `sync_project.py` 事件互斥，不重置 accepted 数值身份。
5. `core/workbook_schema.yaml` 的 Python 图交接采用相同真实工作簿/原始表头唯一匹配规则；保留旧 `matlab_handoff`。`global_preprocessing_contract` 确认 Figure 阶段 Python 出图不等于数值预处理代码被允许调用 Matplotlib。
6. 只同步 Module 04 的语言/接口说明，不重写其 Synthesis、Layout、Enhancement、科研风格或人工批准逻辑。

**专项验证**：Python/MATLAB 新项目、无根 plotting 旧 MATLAB 项目均可合法写/读；Q1 Python/Q2 MATLAB、共享预处理图与根冲突、双 current 身份被拒。首次 select 成功、同值重试不增加 generation、相反选择/过期 generation/read-set 拒绝。MATLAB 原图事件语义不退化，accepted 数值不因纯图变化重验。

### Phase 2：新增 Python 绘图最小执行模板

1. 新增 `q1_plot.py`、`data_process.py` 和真正需要的少量 helper。默认每问一个清晰入口，不复制第二套 Figure Skill、调色/图型决策或独立状态文件。
2. 读取 Excel 前用原始表头检查唯一字段/空白归一化，优先用 `openpyxl` 避免 `pandas.read_excel` 自动改写重复列名导致未检测；主结果和适用 03B 必须用已验收工作簿，`not_needed/question_local` 的合法原始源和未覆盖辅助附件仅按既有 Figure 数据源契约使用。检查真实 sheet、列、单位、NaN 和排序，不修改底层数据。
3. 使用 NumPy/Pandas/Matplotlib 按原 Figure Contract 构建图形；不设强制默认色板、不在图内加整体标题，保留用户本地可见图窗、人工调整、按需导出的现有语义。
4. `data_process.py` 仅消费 accepted `数据预处理结果.xlsx` 进行呈现；预处理数值代码继续禁止在预处理阶段用 `matplotlib/seaborn` 直接生成论文图，不重复插值、训练、求解或修改 accepted 工作簿。
5. `requirements-dev.txt` 当前没有 `matplotlib`：明确最小可用版本与 Python 3.10/3.14 测试依赖，同时提供用户运行依赖说明；不得把新依赖强制加载到无绘图任务的路由。
6. 在 CI 隔离临时目录以 Agg 真正渲染折线、散点、Pareto、分布、热力图、多面板、NaN、中文字体 fallback 与必要导出；验证非空图和关键数据呈现。CI 成功不代替用户实际看图验收。

**Gate**：标准工作簿可产生真实图，缺失/重复原始表头会被识别，不写回数据、不运行求解，Python 绘图渲染依赖明确。

### Phase 3：改造快照、正式同步和读路径

1. `scripts/project_snapshot.py` 提供唯一活动脚本解析入口，返回 `backend/path/hash_field` 供所有消费者复用；无根 plotting 的旧 MATLAB 项目仍可根据合法 state 当前身份工作，不猜测新 Python 当前身份。
2. Python 静态检查限定在可靠的语法、明确违规写回/重算入口、已知整体 title 与脚本 hash；**AST 不能一般性证明任意 Python 无副作用、也不能准确推断所有动态 `savefig` 路径**，不创建解释器沙箱。正式图不允许将 `plt.title`/`ax.set_title` 等整体标题函数误当普通 panel label；但必须避免仅靠字符串出现误报。
3. `scoped_figure_files` **优先现有 Framework 图登记的准确绘图脚本/导出路径以及真实文件**。动态 `fig.savefig(output_path)` 必须由已有 Figure map 明确声明预期输出并对照当前存在/hash；仅静态可确定的字面导出可额外检查，不用源码猜测替代来源登记。
4. `scripts/sync_project.py` 核对当前后端的 `qX_plot.py/m`、条件式 `data_process.py/m`、read-set、图事件、所有正式交付 scope；相同活动图身份不得触发双事件。
5. `scripts/reading_plan.py` style-only 读取正确的活动脚本与 validated hash；缺当前图批准则返回现有正常路径，不放宽原有审查。
6. `scripts/claim_figure_source.py` 对**逐问图**沿用 B2 当前 accepted workbook→脚本/图片→批准→paper 链并支持 Python；**项目级共享预处理图**首先保持 `output_contract/sync_project/Framework` 的独立共享证据核验，不能伪造成 Q1 的 `matlab_script` 或强行扩张逐问 B2。
7. `scripts/submission_requirements.py` 和 ZIP 按实际选定后端收录 `.py/.m`，不无条件要求 MATLAB 文件；赛事官方 allowlist、论文图片引用、LaTeX 编译哈希均按原规则核验。
8. `workflow_router` / `module_manifest` 只更新正式 Figure 产物指针，不新建重型 Router 和检查层。

**Gate**：Python 图在 figures/latex/submission 正式 scope 能通过真实来源/批准验证，历史 MATLAB 图和共享预处理图均无回归，动态导出仍受现有 Figure map 证据核验。

### Phase 4：双后端历史兼容与显式迁移

1. 使用历史 MATLAB fixture 在**完全没有根 plotting 字段**时执行“修改现有 qX_plot.m → sync --write → B2/LaTeX/ZIP 核验”，证明旧项目不仅可读，也能按原路径继续维护而不自动生成新 current 身份。
2. 验证新项目所有 Qn 与 `project_level` 图使用相同扩展名；发现冲突必须输出具体路径/阶段而非静默选择。
3. 已生成图脚本后自动切换一律禁止；用户要求切换时列出全项目需要迁移的绘图入口及相关 Figure/论文依赖。
4. 定义**显式全项目绘图迁移**的最低安全协议与预览/拒绝测试；完整自动迁移写侧不进入本 minor 必做范围。若用户按明确要求手工转换，应保留 accepted 工作簿、模型批准、03A/03B，重新执行图源和人工图审，不将历史图批准视为自动继承。
5. 对纯样式修改保持局部失效，不对已经通过的主数值工作簿进行新的求解验收；图源码/图片变化仍需如实重新验收来源，不跳过 hash。

**Gate**：历史项目与新项目能共存；纯绘图变更不触发模型语义批准，且新旧绘图图证据不能冒认。

### Phase 5：专项回归矩阵与负例

| ID | 用例 | 预期 |
|---|---|---|
| T01 | Python solver + Python plot（多问题） | 全赛题只有 Python 正式图入口 |
| T02 | MATLAB solver + Python plot | 主求解仍 MATLAB，图证据和 ZIP 可走 Python |
| T03 | Python solver + MATLAB plot | 主求解仍 Python，旧 MATLAB 图工作正常 |
| T04 | MATLAB solver + MATLAB plot | 既有 MATLAB 行为不变 |
| T05 | `project_level` + Python 图 | 仅需要 `data_process.py`；只读 accepted 统一工作簿 |
| T06 | `project_level` + MATLAB 图 | 旧 `data_process.m` 与原规则通过 |
| T07 | `not_needed` / `question_local` | 不需要项目级脚本，局部图在当前问 |
| T08 | 03B `required` 且图依赖 03B | 03B accepted 文件必须存在，不得回退到主簿 |
| T09 | 03B `not_required` | 记录真实理由后仅用主工作簿合法绘图 |
| T10 | Python 图的 B2/Caption/LaTeX | 源工作簿、脚本、图、批准与论文当前匹配 |
| T11 | 历史 MATLAB 无 plotting 字段 | 按原有状态/哈希读取与验收 |
| T12 | Python 实际渲染 | 数值、单位、NaN、图例/坐标、Caption 语义正确 |
| T13 | 已锁后端被请求切换 / 显式预览 | 无预览直接修改拒绝；清晰报告全部受影响 Figure/论文依赖，不触发模型或已验收数值失效；自动迁移写侧不属于最低范围 |
| T14 | 复现 ZIP | 精确使用当前后端和赛事真实 allowlist |
| T15 | 初次选型、相同选择重试与旧 generation 并发 | 首次原子写入、重复幂等、竞态拒绝 |
| T16 | 历史 MATLAB 继续修改图并同步验收 | 旧字段当前写侧仍工作 |
| T17 | 项目级共享预处理图的图源/图片/论文证明 | 保持共享作用域，不伪造 Q1 B2 身份 |
| T18 | 动态 savefig 路径和 Framework 图登记 | 以实际声明路径/文件检查，不凭 AST 猜测 |
| T19 | 双后端图脚本事件与原 MATLAB profile | 单事件、旧 Framework/汇总校验不降级、accepted 数值不失效 |

**必须存在的负例**：
- Q1 .py / Q2 .m 混用；项目级 data_process 与根后端不一致；同问两个 active 绘图入口。
- 新 Python 脚本写到旧 `matlab_script`；新旧 hash 混用；缺 plot backend 无合法选择却交付新图。
- Excel 表头缺失、重复、非法合并，绘图声称读取不存在的 03B 工作簿，来源/图片 hash 漂移。
- Python 绘图重新清洗或运行数值模型，或写回 accepted 文件；但不得误拦 `plt.plot`、`numpy.asarray` 等正常绘图操作。
- 图未获批准、Figure 来源被篡改、正式论文引用被改、source discovery 过程中有竞态。
- 修改配色或图脚本引发错误的模型审批 stale / 03A 重算；旧 MATLAB 项目被自动迁移。

**测试执行**：原有 MATLAB 测试继续覆盖旧兼容分支；Python 新增针对性测试，不删除有效检查。不要求两语言像素级一致，但必须核对真实数值、单位、点位、区域和结论。真实渲染测试写临时目录，明确非交互 Matplotlib backend，并报告中文字体未核验等限制。

### Phase 6：版本、生成物、PR 与 GitHub Actions

1. 实施必须开**新的功能分支**（建议 `upgrade/v10.24.0-project-plotting-backend`）；本计划 docs 分支只保存实施蓝图，不作为功能分支。
2. 单主题 PR 可用逻辑提交划分「Authority/Schema → Python 模板 → Snapshot/Sync/B2/ZIP → 兼容回归 → 版本/说明」；任何阶段不要混入无关模型或求解重构。
3. 只人工提交源文件；受管 `MANIFEST.sha256`、`SKILL_FILE_INDEX.md`、`TEMPLATE_INDEX.md` 等由 GitHub `refresh-generated` 生成。不得手工修哈希。
4. 开发时先 draft PR 做受影响专项、静态 lint、生成文件检查；修复失败根因，不在每个小提交都重复完整 Windows 回归。
5. 最终 head 冻结且 PR ready 后，GitHub 上完成：
   - Windows Python 3.10 / 3.14 各四分片及全集汇总；
   - Static contract lint / Generated file contract；
   - MATLAB R2024b **原生数值求解和分析**及实际工作簿/回执；
   - 适用 LaTeX 模板、CUMCM 图片引用、Production LaTeX attestation；
   - Windows Python 3.10/3.14 上配齐实际 Matplotlib 测试依赖的真实绘图 smoke、字体 fallback；既有 MATLAB 图预览不被删除；
   - 涉及渲染性能/现有出版样式 baseline 时检查 Optimization baseline；
   - 主流程、old MATLAB compatibility、B2 Figure/source/claim 与 submission 相关用例。
6. 记录每个 workflow run/job 的源码 head SHA、实际 checkout SHA、成功/失败/等待。`refresh-generated` 更新 head 后重新核对新最终 head，不用旧 head PASS 冒充。
7. 如 PR 变更超过 20 活动文件，按 `SKILL_CHANGE_GOVERNANCE.md` 分组解释每组为何与同一双后端目标耦合；列出检查了但无需改的文件和理由。正式检查不全通过则不合并。

**Gate**：最终功能 PR head 的全部适用 GitHub 正式检查通过；专项通过不能代替正式验收。

### Phase 7：合并后复核与发布

1. 合并之前再次检查是否有重叠 PR/合并冲突与受管生成差异，全部通过才按治理合并。
2. 合并后读取最新 main commit、Skill 版本、Changelog、生成文件状态和 main GitHub Actions；不把 PR 通过等同于 main 通过。
3. 版本发布需单独确认 Git Tag 和 GitHub Release 是否创建；**合并不等于发布**。
4. 最终报告必须附：计划与实施 PR、最终 PR head SHA、合并 SHA、核心修改文件、新旧兼容说明、workflow IDs 与具体通过状态；有阻断须说明用户动作。
5. 若实现完成且 main CI 全绿，停止监控/额外修改，不重复运行无必要回归。

## 6. 风险与回滚矩阵

| 风险 | 防护 | 验收证据 |
|---|---|---|
| 根后端与逐问入口混用 | 根选择单一事实源；统一 resolver | 多问/项目级混合负例被拒绝 |
| 旧 MATLAB 项目失效 | 保留旧 state/hash/handoff 当前读写与提交 | 历史项目改图后 sync/B2/ZIP 通过 |
| 图源改动后继续使用旧批准 | 源码/图包哈希与 approved_figures 仍绑定 | 漂移负例失败 |
| Python 重新计算或修改数值 | 绘图职责与 accepted 数据源严格隔离 | 重新求解/写回负例被拒 |
| 读取 Excel 错列或破坏 NaN | 精确唯一表头、单位/缺测保真 | 数据正负测试及真实图检查 |
| 纯 Python 项目被要求 .m | 按当前选定后端精确收集 | figures / submission 通过 |
| 新绘图失效语义误伤数值或弱化旧图门禁 | Python 事件保留原 MATLAB 图/Framework/汇总语义，事件互斥 | 当前脚本/图重新核验而 accepted 数值不被废止 |
| CI 开销与历史覆盖降低 | draft 专项、最终一次正式矩阵，保留有效测试 | 工作流 head 与矩阵日志 |
| 非数值机理图规则遭覆盖 | draw.io/TikZ 等原独立规则不变 | 既有相关回归通过 |

**回滚**：撤销本次 minor 变更和新增 Python 活动后端；保留旧 MATLAB 绘图路径、历史项目数据及图批准，必要时仅为新项目做显式绘图状态转换，不触碰用户已验收数值结果。任何已发布用户项目需要转换时必须另行审查，不得静默批量重写。

## 7. 分阶段验收与不可变约束

| 阶段 | 交付物 | 停止条件 |
|---|---|---|
| Phase 0 | 当前 main/PR、字段消费者清单、修改简报 | 基线不明或重叠 PR 未解决 |
| Phase 1 | 项目唯一后端 + State/Authority 兼容合同 | 新旧状态歧义、错误数值 stale |
| Phase 2 | Python 真正可执行的工作簿绘图模板 | 无法真实绘图或违反只读职责 |
| Phase 3 | Snapshot/Sync/B2/读路径/ZIP 双后端 | 绕过真实图批准或错误强制 .m |
| Phase 4 | 历史兼容与显式全项目切换 | 旧项目失效、新旧图证据冒认 |
| Phase 5 | 正负例、真实 Python 图与旧 MATLAB 回归 | 有效测试被删除或质量下降 |
| Phase 6 | 最终 PR head 的正式 GitHub CI | required job 未完成或未通过 |
| Phase 7 | main 合并后 CI + 发布核对 | main 验收未闭环不得称完成 |

**最终验收逐项核对**：

- [ ] 全赛题的工作簿驱动 Figure 只选一个后端，包括 project-level 预处理图。
- [ ] 绘图后端与求解后端独立；两个求解后端、两个绘图后端的四种组合均有真实回归。
- [ ] 原有 MATLAB 图模板、历史 state/hash/handoff 及旧项目**持续修改图、同步写入与正式验收**仍可用。
- [ ] 首次后端选型复用现有项目事务、幂等与并发保护，根状态只选一次；旧 MATLAB 不强制转换。
- [ ] Figure Evidence 图等级、设计、版式、科学性/色板、人工审查、Caption 和论文证据链语义不被修改或弱化。
- [ ] 不为后端选择创建额外人工审批、不为各问重复登记 backend、不增加重复 Figure Authority。
- [ ] 不重新求解/清洗工作簿，不通过绘图产生新数值结论；已验收数值来源保持唯一。
- [ ] 绘图源码或图片变化保留现有 MATLAB 图层、Framework、汇总复核语义；无新旧双事件且不取消已锁模型/审批/accepted 主结果。
- [ ] 非数值专用机理图仍按原来的机制图后端选择规则。
- [ ] GitHub refresh-generated 负责受管文件；最终功能 PR 和合并后 main 的全部适用 CI 真实通过。
- [ ] 文档计划和实际功能进度分开报告，不将计划已提交写成能力已上线。


## 8. 第三轮执行链核查与实施前必须冻结的细化方案

> 本节是在 main `b96a7a233913f05740ff60df763cff72371db2ae` 上逐函数审读后的**补充事实与精确执行准则**。若与前述简要说明有冲突，以相应 Authority 的现行语义及本节明确的最小变更边界为准；实施时仍需复核最新 main。不要据此产生额外通用门禁。

### 8.1 实际读写调用链：逐项实施地图

| 环节 | 仓库真实入口/字段 | Python 后端必要改变 | 必须保留的行为 |
|---|---|---|---|
| 用户提出绘图任务 | `core/workflow_router.yaml#routing.figures`，`core/module_manifest.yaml#modules.figure_evidence` | 加载项目根已选后端并让 terminal outputs 对当前语言适用；新增 Python 绘图 intent 字面词时不能把纯绘图误路由到 `code_and_solution` | 原 Figure Authority、`pre_delivery_gates` 与写作/机理图路由 |
| 选择后端 | 现有 `scripts/project_solver_backend.py#select_project_backend` + `scripts/project_transaction.py` 提供事务参考 | 增加专属、轻量 inspect/select，第一次正式 Figure 脚本前写根 `plotting.backend` | `state_generation` / read-set / Framework 同步 / 幂等，不改变 `execution.solver_backend` |
| Schema | `core/project_state.schema.yaml` 顶层与 subproblems `additionalProperties: false`、`$defs.artifact_hashes` / `artifact_layer` | 允许根 `plotting` 与 Python 的 `plot_script`/hash/layer，校验跨问题一致 | MATLAB `matlab_script` 及原 hash 继续**当前可写** |
| 文件命名和要求 | `core/output_contract.yaml#per_question`、`global_preprocessing`、`project_sync.stage_requirements`；`scripts/sync_project.py#stage_requirements` | 当前 backend 只需一套 `qX_plot.py/m`；project_level 图条件 requirement 二选一 | `not_needed/question_local` 无 project_level 文件义务；不能更改原始工作簿名字 |
| 逐问快照 | `scripts/project_snapshot.py#_snapshot_question` | 把当前 `qX_plot.m` 的硬发现改为统一 `FigureScriptRef`；hash 写入当前角色 | 03A/03B 已验收、read-only source provenance 与现有情况说明 |
| 图发现 | `scripts/project_snapshot.py#scoped_figure_files` | 继续使用 Framework 明确 `绘图程序/导出文件` 以及同目录受支持图片；新增 Python 实际声明识别仅作辅助 | 当前 `figure_bundle` 真实文件集合、图片 hash、非法越界路径、缺文件拒绝；**不顺带修改旧 MATLAB 扫描范围** |
| 同步写入 | `scripts/sync_project.py#_apply_snapshot_to_state`、`_snapshot_transition_events`、`_capture_sync_question_sources` | 正确选择 `plot_script` 或 `matlab_script`；哈希差异转一个活动图脚本事件 | 写事务乐观并发/read-set、accepted 数值保留、现有状态 Schema 和必要错误门 |
| 共享预处理图 | `scripts/sync_project.py#_preprocessing_artifact_issues`、`core/global_preprocessing_contract.yaml#preprocessing_figure_contract` | project_level × backend 条件决定 `data_process.py/m` 并检查只读统一工作簿、禁重复预处理 | 原数据预处理代码**不得在数值预处理阶段用 matplotlib/seaborn 生成论文图**；Figure 阶段才用 Python 出图 |
| 快速读取 | `scripts/reading_plan.py#_figure_binding`、`_project_reads` | `style_only` 根据活动图脚本的实际 hash/已有批准判断 | 缺批准时返回正常审查路径；不得“由于是 Python 就跳过” |
| 正式 B2 Figure | `scripts/claim_figure_source.py#inspect_source_binding` 和 `_cached_discovery`、`recheck_source_discovery` | 当前逐问 `source_bindings` 允许 Python `plot_script` 的路径/sha，保持当前读集和批准流程 | `len(questions)==1`、B1 真实源、selected/current、表头、图包 hash、`approved_figures`、项目读集复验 |
| 论文源 | `scripts/claim_figure.py`、`scripts/claim_consumption.py`、`scripts/render_paper.py` | 确认现有真实图路径/图片引用在 Python 图下仍成立；**无证据不得修改论文/LaTeX Authority** | 当前图 claim/引用/原文证明和 PDF binding |
| 复现包 | `scripts/submission_requirements.py#reproducibility_requirements`、`scripts/sync_project.py#_submission_zip_issues` | 每问收录当前绘图脚本；project_level 收录已选 `data_process.py/m`，并修正 `require_matlab=True` 的无条件检查 | 正式 package allowlist、PDF、工作簿、数值求解脚本和当前源码/数据验证 |
| 自动检查 | `tests/`、`.github/workflows/ci.yml` 和 `optimization-baseline.yml` | 新 Python 模板与双后端集成测试，必要依赖明确固定 | 旧 MATLAB 图测试、MATLAB 数值求解和 LaTeX 正式审计不降级 |

### 8.2 唯一活动脚本解析的输入、输出与冲突规则

**建议内部函数约定（设计接口，不是现有代码）**：

```text
resolve_figure_script(project_root, state, question, purpose)
  → FigureScriptRef:
       backend        = python | matlab
       path           = 项目根内的精确标准相对路径
       hash_field     = plot_script | matlab_script
       origin         = selected | historical_matlab
       active         = true
       issues         = []
```

1. 当根 `plotting.backend=python` 时，只有相应问题的 `plot_script` 与 `qN_plot.py` 路径合法；当根为 `matlab` 时继续按 `matlab_script` 和 `qN_plot.m`。根缺失时，只有可验证的旧 MATLAB 正式身份可进入旧逻辑；没有任何合法图身份则进入“待选型”，不得由 `q1_plot.py` 文件偶然存在而隐式选 Python。
2. 当前路径由 root + canonical 目录解析，并用已有项目根边界/符号链接检查；不要将已存在的未知路径直接视为当前。**未选定、旧历史、冲突、正常新项目必须分别报告**。
3. 扫描全体已登记小问 + project_level `data_process.*` 才能判断项目级唯一性。项目中残留的**非 current 存档脚本**不自动成为第二 active；但被登记为 current 或被正式 Figure map 作为当前程序引用的冲突脚本必须拒绝，不能隐藏。
4. 若新 Python 项目逐问没有脚本且仍处于早期设计/求解阶段，不应触发 figures 的提前缺文件门；只有实际递交 Figure 及更后正式 scope 时按现有激活条件要求。对已有旧项目同样尊重原 delivery-scope 语义。
5. 在 `project_snapshot`、`sync_project`、`reading_plan`、`claim_figure_source`、`submission_requirements` 复用同一解析实现；消费者各自保留原本的图质量审查职责，不新建第二套审计逻辑。

### 8.3 条件式阶段要求必须逐格定义，不能使用全局列表替换

```text
Scope           not_needed/question_local       project_level + Python       project_level + MATLAB
design          无正式 plot 脚本义务               无正式 plot 脚本义务         无正式 plot 脚本义务
code/results    不提前要求 plot                    不提前要求 plot              不提前要求 plot
figures         每问 qN_plot.py 或 .m             每问 qN_plot.py + data_process.py  每问 qN_plot.m + data_process.m
docx/latex      继续复用当前各自适用的图批准规则     共享预处理图 Python 角色        共享预处理图原 MATLAB 角色
submission      按真实当前 Figure / 复现包规则      收录 Python 图和预处理图      保留 MATLAB 图和预处理图
```

- **不能简单把 `preprocessing_matlab_script` 替换为 `preprocessing_plot_script` 并覆盖旧语义**。应在 Output Contract 明确 Python 与 MATLAB 两组互斥的要求，由 `stage_requirements(scope, output_contract, state)` 根据 `preprocessing_decision` 与合法根后端选取；旧 MATLAB 项目继续走原检查分支。
- 当前 `figure_evidence` 模块及 `figures` 路由 terminal outputs 直接使用 `matlab_scripts / preprocessing_matlab_script`；新增语言无关聚合投影可以实现，但不要删除旧别名或使其同时成为 Python 的强制 requirements。若使用新的 `plot_scripts` 终端角色，必须对齐 `module_manifest`、`workflow_router`、`output_contract` 和对应 lint。
- 与选型无关的 `approved_figures`、`figure_bundle`、`result_figures`、`preprocessing_figures`、`figure_contracts` 均保留原含义。额外 `.py` 脚本不等于主求解/分析代码，不得自动计入 `solver_execution` 或数值代码 bundle。

### 8.4 原始数据与预处理、结果图的合法消费矩阵

| `preprocessing_decision` | 数值/证据事实源 | 图脚本允许使用 | 不得实施 |
|---|---|---|---|
| `not_needed` | 当前原始附件 + 已验收每问结果 | 当前合法附件、标准 accepted 结果工作簿 | 为统一接口创建空公共预处理工作簿；模糊猜测数据 |
| `question_local` | 对应小问局部输入和已验收模型结果 | 该问图只消费原数据或已真实持久化的局部证据 | 在绘图脚本重新运行局部预处理、训练、优化 |
| `project_level` | 当前 accepted 统一预处理工作簿，另有未覆盖的独立辅助附件 | `data_process.py/m` 只读统一工作簿；`qN_plot.py/m` 依真实 Figure Contract 读 accepted 主/03B 和合法公共证据 | 重新读取 `covered_raw_sources` 已替代的原始数据、重做公共清洗、反推细粒度样本 |
| 任一决策，`03B=required` | 当前已验收的 03B 数据 | **只有 Figure 真正消费 03B 时**要求其工作簿存在且 accepted | 每个绘图入口强制读取无关/不存在的 03B |
| 任一决策，`03B=not_required` | 主结果和实际合法补充来源 | 不生成占位分析簿，结论不声称新增稳健性 | 把 `not_required` 误标为通过稳健性分析 |

### 8.5 证据保真与哈希边界的直接验收设计

- **发现范围**：`scoped_figure_files` 当前合并“同问目录下的受支持图片 + MATLAB 脚本字面导出 + Framework 图表登记”。Python 适配必须沿用现有相同作用域并保留 `figure_bundle` 算法；多余历史图片是否属于已有发现范围，按**原规则**处理，不在这次语言扩展中静默缩小或者扩大。
- **脚本来源**：Python `plot_script` 的 current hash 与 validated hash 均按真实源码 SHA-256；当前 Figure Source 继续检查源码 bytes、figure bundle、approved_figures、论文引用和最终审计所消费的文件，而不把首次静态检查当批准。
- **动态导出**：`fig.savefig(output_path)` 不可静态确定时，以当前 Framework `导出文件`、真实文件和下游论文引用作证。禁止为了消除动态 AST 不确定性新增一份强制 YAML 或自定义“文件声明语言”。
- **无导出阶段**：当前 Figure 模板默认打开本地图窗让用户检查，无导出是合法脚本交付状态；但正式入文/显式 Figure 绑定必须具备真实图片与必要的批准，不能因为 Python 可运行而自动进入 `approved_figures`。
- **读集与事务**：在 `_capture_sync_question_sources`、`_verify_sync_question_sources`、B2 `recheck_source_discovery` 和项目事务处纳入当前 Python 脚本与真实已消费图；必须支持必要的“预期不存在”读取保护，避免检查中脚本被替换的 TOCTOU。
- **stale 对齐**：以当前 MATLAB `matlab_script_changed` 的图/Framework/汇总失效语义作为不可变回归基线。若一个 Python 脚本改动使 `plot_script` 和 `figure_bundle` 同时不匹配，必须依现有状态事件合并规则不重复发同等后果；源/图片/论文证明仍逐项当前有效。accepted 数值不被纯图变更覆盖。

### 8.6 复现包真实代码中的两处必须同时修改的硬编码

1. `scripts/submission_requirements.py#reproducibility_requirements` 每问执行 `question_path("matlab_script", ...)`，project_level 又用 `global_preprocessing.matlab_script` 补收 `data_process.m`。必须按活动后端选择实际 `.py` 或 `.m`，且显式核对标准相对路径和当前注册身份；不能因为用户选 Python 就漏掉 Python 求解脚本、工作簿或证据图片。
2. `scripts/sync_project.py#_scope_artifact_issues` 在已有 `required_paths` 清单时仍向 `_submission_zip_issues(..., require_matlab=True, ...)` 传入硬要求。**修复须与上一步同时落地**：在精确 `required_paths` 已完整且当前后端可能全 Python 时不再单独强制“至少一个 .m”。保留 PDF、工作簿存在、文件精确清单及既有官方包验证；不要用“ZIP 有一个 .py 即合格”代替精确路径。
3. 验收应包含两类：纯 Python 数值 + Python 图（确实 0 个 .m）能按合法清单通过；MATLAB 数值 + Python 图（包含求解 .m）也能通过，但缺少真实 `qN_plot.py` 仍必须失败。

### 8.7 负例优先级、测试定位与最小执行顺序

**直接复用或扩展的已有测试文件（名称已在 main 树上核对）**：

| 功能边界 | 优先检查测试 |
|---|---|
| 项目选型幂等/并发 | `tests/test_project_solver_backend_select.py`、`test_project_backend_policy_shared.py` 作为事务形态参考；新增 Python Plot Backend 专项，不改变数值后端测试 |
| Schema 与 stale | `tests/test_result_state_semantics.py`、`test_v900_state_transitions.py`、`test_sync_project.py` |
| Figure Source 和 B2 | `tests/test_b2b3b_figure_source.py`、`test_b2b4_formal_figure_gate.py`、`test_b2b4_figure_integration.py` |
| Python/MATLAB 职责 | `tests/test_python_matlab_ownership.py`、`test_preprocessing_decision_contract.py` |
| Figure 样式与脚本 | `tests/test_v910_publication_rendering.py`、`test_p6b_matlab_preview_contract.py`、`test_v742_dynamic_figure_layout.py` |
| 读路径与项目快照 | `tests/test_reading_plan.py`、`test_sync_project_source_read_set.py`、`test_project_state_read_snapshot.py` |
| 官方/复现提交 | `tests/test_b2b2_sync_gate.py`、提交包现有正式 contract 测试 + Python/MATLAB 交叉新测试 |

**实施每一批提交的验收顺序**：先静态契约/Schema 针对性测试 → 当前绘图 Script Resolver/选型事务单测 → Python workbook 真实渲染烟测 → Snapshot/Sync/Read Plan → B2/提交包/LaTeX → 原 MATLAB 历史项目持续维护测试 → 最终 PR head 正式 CI。旧测试先识别其断言对应的原 MATLAB 合法场景，再决定扩展或针对性更新；不能直接删除测试或用生成一个空的 .m 文件骗过要求。

新增必须覆盖的最小反例：

- root Python 与 Q2 MATLAB current 冲突；`data_process.m` 仍被 Framework 登记为 active 时无法悄悄切 Python；无根选择但有旧 `matlab_script` 时不得误认 unselected。
- Python 绘图存在未注册的 `qN_plot.py` 时不能自动变成正式图来源；明确存档的旧脚本不能被二次计入图 hash。
- 当前字段/validated hash 不符、Figure 图片遭替换或被未批准新图片污染 bundle；旧 MATLAB 在同一输入上依然按原检查拒绝。
- `pandas` 重复列重命名导致原始表头碰撞；`not_needed` 的合法 raw source 错误地被拒；`project_level` 读取 covered raw source 被错误放行。
- 动态导出路径没有注册、注册指向错误文件、图目录符号链接越出项目根、读集观察期间源文件改动；人工批准缺失不能由 CI smoke 自动补齐。
- 纯 Python ZIP 仍因没有 .m 被拒，或删除 `q1_plot.py` 后因有一个无关 .py 就被放行。
- 本地 `Agg` / GUI 环境差异不允许产生伪造用户人工视觉验收；Python 3.10/3.14 在 CI 均能找到真实 `matplotlib` 依赖。

### 8.8 版本与实施范围控制：避免“新增后端”膨胀为整套迁移工具

**v10.24.0（暂定）本次最低完成范围**：项目级选型 + Python 绘图模板 + MATLAB 原路径维持 + Snapshot/Sync/B2/Read Plan/正式包/CI 必要适配。**默认不开发全自动 MATLAB→Python 历史项目迁移器、回滚引擎、图形脚本依赖追踪沙箱、智能推荐学习系统、另一个 Figure Registry 或新的图形审批流程。**

如果已有锁定项目用户请求切换，先执行**只读识别与全题影响预览**；当前功能最低要求是拒绝不安全的覆盖，并说明必要人工迁移/重新审图流程。完整迁移器如有真实需求，再按当时 main 单独做范围和证据评审，不作为本次 minor 的隐藏必做项。

**停止与回退条件**：任何阶段出现旧 MATLAB 项目不能合法 sync/验收、Python 图必须伪装成 `matlab_script`、新 Figure Source 绕过已有批准、项目主数值工作簿被纯图变更判 invalidated、或新功能必须侵入 Problem/Model Solver 权威，均先暂停当前功能提交，回到 Phase 0/1 修正设计而不是叠加临时补丁。


---

**实施边界结论**：此次变更是给现有 Figure Skill 加一个 Python **执行后端**，并将已有 MATLAB-only 的项目状态、发现、验收和复现包语言依赖抽象为项目级双后端；原有绘图科学性、证据来源、数学模型、数值与论文治理不变。实施前按最新 main 核对字段与影响范围，遵循源码提交 → GitHub 生成 → 最终 head 验收 → 合并后 main 验收的维护流程。