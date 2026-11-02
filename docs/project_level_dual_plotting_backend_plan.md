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

- 根状态 `plotting.backend` 是后端选择的**唯一事实源**。各问只存自身脚本路径/哈希，不记录第二份选择；不新增单独状态登记表。
- `auto` 可作为用户请求的意图，但不能作为已解析、已锁定的 backend 值。
- **选型时间**：Module 02 完成全题可预见图表需求、预处理决策和软件环境审视之后；最迟在**首份正式 Figure 脚本生成之前**选定。该步骤并入当前模型/图证据规划与项目记忆，不成为 Human Model Approval 的额外门。
- 用户明确指定且可行则遵循；未指定时由 Skill 对**全题**预期图形、数据源、环境、维护成本综合判断。都可行时 Python 默认优先；Simulink 原生图形或确有必要的 MATLAB 图形能力时可选 MATLAB；不只看 Q1，也不只看求解语言。
- 环境尚未实际验证时，写明依赖/字体/许可证的未核验事实；不宣称已运行；若均不可行，说明阻断，不悄悄按问题切换。
- 当一个正式脚本已经生成，根 backend 视为 locked；中途只接受**用户明确发起的全项目绘图迁移**，不允许为某张图自动改选。

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
- 数值来源必须是当前 accepted workbook；列名唯一且精确匹配，保留数据粒度、单位、NaN 间断、真实坐标与必要统计语义；禁止由汇总数字伪造明细。
- Figure Contract 说明 Core Conclusion、Evidence Level、Primary Question、caption、证据来源与 Paper Location；正式图无整体 title/sgtitle，图题由 DOCX/LaTeX caption 承担。
- 人工看图/语义批准与机器结构审查分离；已批准图片、来源脚本与论文主张继续用哈希和实际引用闭环。
- 项目级预处理图只消费已验收统一工作簿；不能重算清洗/拟合/填补；主求解、深化分析均不得被绘图脚本调用来制造证据。
- 现有 `模型论文框架.md`、`state/project_state.yaml` 和 accepted 工作簿的语义/事实/机器状态分工不变。

## 3. 新旧状态与兼容协议（必须先定再改代码）

### 3.1 语言无关的图脚本产物

拟增加：
- `plotting.backend` 与非空 `selection_reason`，项目根唯一。
- 逐问 `plot_script`；`artifact_hashes.plot_script` 与 `validated_artifact_hashes.plot_script`；独立的 `plot_script_changed` 图层状态事件。
- 条件式项目级 `preprocessing_plot_script`，只影响预处理图与消费它的 paper Figure evidence；不影响预处理数值工作簿 accepted 身份。
- `figure_bundle` / `approved_figures` / Figure Source bindings / paper fragments 保留，不改名也不降低审查。
- 确切字段名在 Phase 0/1 按 Schema 与同步器现有风格审核；本节是目标接口草案，不是可以直接使用的 YAML。

### 3.2 历史 MATLAB 项目保护

1. 旧项目缺 `plotting`，但有可验证的 `matlab_script` 及旧图状态：维持**历史 MATLAB 读侧**，不自动回填 Python 或重新签发批准。
2. 保留旧 `matlab_script` 路径、旧 `matlab_script_changed`、旧 `matlab_handoff` 和旧 `preprocessing_matlab_script` 的只读兼容语义；不能把新 Python 脚本伪装进旧字段。
3. 新项目若同时声明两个 current 正式绘图入口，或不同问题/预处理脚本的扩展名与根后端不一致，应明确报错并要求纠正；不可自行猜哪个优先。
4. 只在用户明确要求历史项目全量切换时：先保留合法数值工作簿和原图身份 → 选新 backend → 改写所有活动绘图入口 → 重看实际图 → 更新受影响哈希/批准/论文 Figure 绑定；不要自动删除历史 .m 文件。
5. 未明确要求转换的旧项目能正常读取、审计、复现、交付；不新增只为追求字段统一的迁移步骤。
6. 兼容层退出须未来另行治理并说明窗口，不得在本次更新时删除旧测试、旧 Schema 规则或旧项目证据。

### 3.3 正确的 stale 范围

```text
绘图源码变化 / 后端显式切换
  → plot_script / 图包、图来源有效性检查
  → 已引用相关图片的论文片段与 Figure chain
  ✗ 不触发 Problem Contract stale
  ✗ 不使 locked model / Human Model Approval stale
  ✗ 不要求重跑 accepted 03A / 03B / 预处理数值工作簿
```

脚本或图片字节变化时不得沿用旧图的人工批准/现有 hash；如果只是脚本样式变化而仍需当前正式图，按现有合法 Figure 检查和人工预览重验，不把它升级为模型修改。

## 4. 逐文件影响清单

> 下表是实施时**检查范围**，不要求全数修改。每项最终必须在 PR 记录“修改 / 只核查 / 不适用”的结果及理由，避免机械替换所有 MATLAB 字符串。

| 文件/组 | 拟修改原因与方式 |
|---|---|
| `modules/04_figure_evidence.md` | 仍为唯一 Figure Authority；保留完整图形科学性与审美选择规则，只替换语言专属执行/交付表达 |
| `core/output_contract.yaml` | 新绘图后端、脚本名称/路径、stage requirements、哈希、stale、同步/复现产物权威 |
| `core/workbook_schema.yaml` | 新通用 Handoff 指针和字段；精确/唯一表头规则不变，保留 MATLAB Handoff 历史兼容 |
| `core/project_state.schema.yaml` | 根 `plotting`、逐问脚本/哈希、旧字段兼容与冲突 Schema |
| `core/state_transition_contract.yaml` | 新图脚本事件仅影响图与依赖论文，不影响数值和审批 |
| `core/global_preprocessing_contract.yaml` | `data_process.py/m` 的项目后端引用与只读绘图职责，预处理数值规则不变 |
| `core/workflow_router.yaml` / `core/module_manifest.yaml` | Figure route 的终端产物与后端选择指针；不新增独立重型路由 |
| `core/hsk_core_policy.md` / `core/user_execution_contract.yaml` / `core/code_quality_contract.yaml` | 只核对绘图/求解职责和用户执行边界；按需最少更新语言硬编码 |
| `templates/matlab/q1_plot.m` / `data_process.m` / `README.md` / publication helper | **保留现有功能**；只做必要的兼容性小修，不删除、不整套翻译 |
| 新 `templates/plot/python/`（最终路径先复核） | 最小 `q1_plot.py`、`data_process.py`、必要读表/样式 helper 与 README；不强迫每题生成额外工程包 |
| `templates/figure/*.md` / `packs/artifact/figure.md` / `templates/model/model_paper_framework.md` | 只同步真正写死 MATLAB 的绘图程序/证据链接口，不改图型、布局与 Caption 内容规则 |
| `scripts/project_snapshot.py` | 统一发现 .py/.m 活动绘图入口，读取脚本声明、图导出、图包与源码 hash，兼容旧 .m |
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

### Phase 1：项目级 Backend 与新旧 State 合同

1. 在 `core/output_contract.yaml` 定义项目级绘图后端以及每问、项目级预处理的**唯一正式脚本**布局；新规则不依赖 solver_backend。
2. 在 `core/project_state.schema.yaml` 增加可选根 `plotting` 和语言无关 `plot_script`、hash；旧 `matlab_script` 仍合法，禁止 Python 冒用与新旧 current 双登记歧义。
3. 在 `core/state_transition_contract.yaml` 增加新绘图脚本的 Figure-only stale event，并保留旧 MATLAB 事件，避免对同一变化双重传播。
4. 在 `core/workbook_schema.yaml` 将新图交接字段泛化为 script path，精确表头/单位/NaN/数据来源约束不变，旧 `matlab_handoff` 仍可解释。
5. Module 04 只更新后端描述、源文件交付措辞；权威绘图决策和用户人工检查机制不更改。
6. `global_preprocessing_contract` 保留 accepted 数据源合同，增加两语言脚本映射，不改变预处理阶段必要性判定。

**专项验证**：新 Python 项目合法；新 MATLAB 项目合法；无新字段旧 MATLAB 项目合法；Q1 Python/Q2 MATLAB、preprocessing MATLAB/Q1 Python、新旧双 current、无已选择 backend 却生成新正式绘图代码均拒绝；不会导致 accepted 数值 stale。

### Phase 2：新增 Python 绘图最小执行模板

1. 添加 `q1_plot.py`、`data_process.py` 与最小必要 helper（建议 NumPy/Pandas/OpenPyXL + Matplotlib，按实需而非强制全装）。
2. 工作簿读取：逐图声明读取的 sheet、唯一表头、单位、必要字段、缺测语义；不得模糊表头匹配、不按摘要数字反推出底层序列；读入 Excel 的真实列顺序/缺测情况应可核查。
3. Matplotlib 的图型、布局、色板、字体、面板与增强方式仍来自 Module 04 Figure Contract；不额外发明默认强制色板或图型。
4. 正式 Figure 没有重复整体标题，保留坐标轴单位、必要注释、Legend/Panel Label；需要 PDF/SVG/PNG 导出时只对既有明确导出目标作输出。
5. 不将 `data_process.py` 变成“二次预处理”：只能读取 accepted `数据预处理结果.xlsx`；禁止训练/填补/滤波/重采样/写回；允许透明的绘图聚合、坐标映射与明确声明的可视化排序。
6. 默认每问一个入口、配置集中易维护，优先自包含；有充分理由才引用少量共享 helper，不增加全项目配置文件和新状态登记。
7. 利用**合成测试工作簿**做真实 Python 渲染烟测，覆盖折线/散点/分布、Pareto、热力图、多面板、NaN 间断、中文/ASCII 标注与导出；不得只凭 Python AST 成功就宣称外观已验证。

**Gate**：能在隔离环境读取标准 Excel、产生非空合法图片、数值/单位不改变，且无求解和写回副作用。

### Phase 3：改造快照、正式同步和读路径

1. 在 `scripts/project_snapshot.py` 实现基于根 backend 的一个活动脚本 resolver，同时兼容读取历史 `qX_plot.m`；避免每个调用者各自猜测语言。
2. Python 绘图脚本通过 AST/明确声明验证必要的工作簿引用、非法整体 title（适用范围）、实际声明导出与源码 hash；字符串/注释不能假冒实际执行行为。仅执行必要静态检查，不建通用 Python 沙箱。
3. `scoped_figure_files` 沿用真实 Framework Figure map + 当前脚本声明/现有图片发现逻辑；将 MATLAB export 特判扩展为 Python 导出，可核验当前实际文件；不是自动批准。
4. `scripts/sync_project.py` 用统一解析结果核对项目级 `data_process.py/m`、逐问 `qX_plot.py/m`、read-set、图层 stale 及各交付 scope。
5. `scripts/reading_plan.py` 的图样式快捷恢复改为观察实际 active plot script + validated hash；缺失真实批准则返回现有正常全量审查，不允许为了省事绕过。
6. `scripts/claim_figure_source.py` 将绘图源码语言泛化，B2 仍必须实测真实 accepted workbook、表头、脚本 hash、图包、人工批准、论文源绑定；更新 currentness 判定，不引入第二套 B2。
7. `scripts/submission_requirements.py` 和 ZIP 基础检查收录**状态声明的正确 .py 或 .m**；不再固定要求 MATLAB 脚本，且不能因此略过官方 submission allowlist 或真实代码/工作簿。
8. 同步 `workflow_router` / `module_manifest` 的 Figure 产物指针；不增加逐问后端选择 route，不改变 pre_delivery_gate 名称。

**Gate**：Python 项目正式 figures/docx/latex/submission 不因缺 .m 失败；历史 MATLAB 项目不退化；实际缺工作簿/图片/批准、错误 hash、读集漂移必须仍失败。

### Phase 4：双后端历史兼容与显式迁移

1. 使用历史 MATLAB fixture 在**完全没有根 plotting 字段**时验证 snapshot、sync、B2、LaTeX/ZIP 读取正常，不写回新的假 current。
2. 验证新项目所有 Qn 与 `project_level` 图使用相同扩展名；发现冲突必须输出具体路径/阶段而非静默选择。
3. 已生成图脚本后自动切换一律禁止；用户要求切换时列出全项目需要迁移的绘图入口及相关 Figure/论文依赖。
4. 显式迁移保留当前 accepted 原始工作簿、模型批准、03A/03B 结果，重建图脚本、重看渲染图、重新确认受影响的 `approved_figures`、刷新 Figure 及论文绑定。
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
| T13 | 用户显式全项目换后端 | 只重验 Figure/引用，不使模型/数值 stale |
| T14 | 复现 ZIP | 精确使用当前后端和赛事真实 allowlist |

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
   - Python 实际绘图 smoke；既有 MATLAB 图预览不被简单删除；
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
| 旧 MATLAB 项目失效 | 只读兼容旧 state/hash/handoff | 无迁移历史 fixture 通过 |
| 图源改动后继续使用旧批准 | 源码/图包哈希与 approved_figures 仍绑定 | 漂移负例失败 |
| Python 重新计算或修改数值 | 绘图职责与 accepted 数据源严格隔离 | 重新求解/写回负例被拒 |
| 读取 Excel 错列或破坏 NaN | 精确唯一表头、单位/缺测保真 | 数据正负测试及真实图检查 |
| 纯 Python 项目被要求 .m | 按当前选定后端精确收集 | figures / submission 通过 |
| 绘图修改牵连数值重算 | Figure-only typed stale，模型/数值身份不动 | 样式/迁移测试 |
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
- [ ] 原有 MATLAB 图模板、历史 state/hash/handoff 及旧项目验收仍可用。
- [ ] Figure Evidence 图等级、设计、版式、科学性/色板、人工审查、Caption 和论文证据链语义不被修改或弱化。
- [ ] 不为后端选择创建额外人工审批、不为各问重复登记 backend、不增加重复 Figure Authority。
- [ ] 不重新求解/清洗工作簿，不通过绘图产生新数值结论；已验收数值来源保持唯一。
- [ ] 绘图源码或图片失效只影响图及真实依赖的论文片段，不影响已锁模型/审批/accepted 主结果。
- [ ] 非数值专用机理图仍按原来的机制图后端选择规则。
- [ ] GitHub refresh-generated 负责受管文件；最终功能 PR 和合并后 main 的全部适用 CI 真实通过。
- [ ] 文档计划和实际功能进度分开报告，不将计划已提交写成能力已上线。

---

**实施边界结论**：此次变更是给现有 Figure Skill 加一个 Python **执行后端**，并将已有 MATLAB-only 的项目状态、发现、验收和复现包语言依赖抽象为项目级双后端；原有绘图科学性、证据来源、数学模型、数值与论文治理不变。实施前按最新 main 核对字段与影响范围，遵循源码提交 → GitHub 生成 → 最终 head 验收 → 合并后 main 验收的维护流程。