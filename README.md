# mathmodel-skill v7.4.0

当前工作流：**审题与 Problem Contract 冻结 → 通用数据审计与 `preprocessing_decision` → 题面—数学—代码语义闭环 → Complexity Sanity Check → semantic governance → 条件式项目级预处理（仅 `project_level`）→ 用户本地完整版 Python 主求解 → 主结果质量门 → 独立 Python 结果深化分析 → 稳定性验收 → MATLAB预处理/结果证据图 → 题型自适应 LaTeX 写作 → AI cleanup → 编译终审**。

## 数据阶段：先判断，不默认清洗

所有带数据的题都先做**非破坏性审计**，然后锁定：

```text
preprocessing_decision
├─ not_needed     → 不创建数据预处理/，各问直接读取原始数据
├─ question_local → 不创建全局预处理目录，本问脚本内做有数学来源的局部变换
└─ project_level  → 数据预处理/数据预处理.py
                     ↓
                    数据预处理结果.xlsx
                     ↓
                    依赖小问统一读取
```

判定不依赖某一种赛题经验，而取决于**当前题目、当前附件和当前模型要求**。至少检查完整性、一致性、有效性、重复身份、时间/空间采样与覆盖、测量质量、模型输入条件以及时间因果和信息泄漏风险。

两个及以上小问共享同一原始数据，只说明需要统一审计口径，**不能单独推出需要清洗、插值、滤波、标准化或统一工作簿**。同样，存在缺失值也不能直接推出“必须插值”：必须先判断变量类型、缺失位置和缺口长度、是否存在连续机制、模型是否可原生处理，以及保持缺失、删除、插值、统计填补、模型填补或预测填补哪一种假设最弱且可验证。

插值只在连续变量具有明确局部连续性、缺口长度和边界位置允许时考虑；类别、ID、标签、事件状态及无连续机制的变量不得机械数值插值。模型化或预测填补必须有独立恢复能力验证，时序任务还必须保持时间顺序，禁止使用未来信息。

“预测填补”和“题目要求预测”严格分开：前者只是为了恢复后续模型确实需要的缺测输入，可能属于预处理；若赛题本身要求预测未来值、未知类别、需求、价格、风险、趋势或其他最终结果，则属于核心预测模型，不能提前包装成数据预处理。

## 预处理一旦启用，论文不能敷衍

只要实际数据变换参与后续模型，就必须形成：

```text
数据问题与必要性
→ 方法选择与替代方案
→ 数学公式/变换关系/目标函数
→ 参数、阈值、窗口、频带或超参数来源
→ 理论、统计或物理合理性验证
→ 处理前后底层数据证据
→ MATLAB证据图
→ 后续模型输入接口
```

不同处理写作深度不同：

- 单位换算、坐标修正、主键/时间对齐等确定性结构处理：给出映射关系和一致性条件；
- 标准化、归一化、对数/Box-Cox 等：给出变换公式、参数估计口径和处理前后尺度/分布验证；
- 插值、统计/模型/预测填补：给出公式或目标函数、边界条件/特征集合，并做人工掩蔽或留出恢复误差；
- 滤波、平滑、去噪、重采样：给出核函数、频率响应或离散映射以及参数来源，并验证有效信息保留；
- 异常识别、删除、修复：给出判定指标、阈值来源和保留/处理方案对照。

形式证明只在确实存在等价性、守恒性、单调性、误差界或可行性保持等命题时使用。经验型清洗不能编造“证明”，应使用统计检验、物理约束、人工掩蔽、留出验证、残差、频谱、分布或处理前后对照。

## 项目级预处理 MATLAB：`data_process.m`

只有 `preprocessing_decision=project_level` 时额外存在：

```text
数据预处理/
├─ 数据预处理.py
├─ 数据预处理结果.xlsx
└─ data_process.m
```

`数据预处理.py` 必须把论文和绘图真正需要的底层证据写入工作簿，包括：

- `预处理方法证据`；
- `处理前后对比`；
- `绘图数据索引`；
- 题目专属的处理前/后、诊断、人工掩蔽/留出验证等底层数据。

`data_process.m` 只读取 `数据预处理结果.xlsx`，可以画处理前后时序/空间场/剖面、缺失与填补、分布、频谱、残差、真实值—恢复值、采样覆盖、异常阈值等图。**MATLAB 不重新清洗、插值、滤波、重采样、训练填补模型或重新确定参数。**

每个 project-level 项目至少有一张预处理图真正回答“为什么需要处理”或“处理是否合理”，而不是只让曲线看起来更平滑。默认只保留图窗人工检查；需要正式导出时使用 `data_process` 或 `data_process_<evidence>` 作为 ASCII 图片基名。

`question_local` 若存在实质数据变换，则在对应小问正文写公式、参数依据和验证；需要图时由该问 `qX_plot.m` 读取 Python 已输出的底层数据绘制。

## 写作阶段：按题型证据链写，不按模板写

v7.4.0 将正文表达从“章节清单 + 终稿去套话”升级为共享写作协议。权威规则位于 `modules/05_writing/latex.md` 的“正文表达与章节组织协议（写作权威）”，DOCX 与 AI cleanup 复用同一套规则。

核心要求：

- 问题重述只恢复研究对象、关键条件和逐问输入/输出，不逐句复制赛题，也不提前写模型与结果；
- 问题分析重点解释本问难点、关键对象关系、跨问依赖以及为什么需要当前模型，不写“预处理—建模—求解—绘图”的流水账；
- 模型假设只保留真正改变变量、目标、约束、分布或适用边界的条件，题面事实和单位约定不得伪装成假设；
- 模型推导从本题对象和机制进入变量、关系式、约束和可计算形式，不写无直接作用的算法百科和模型发展史；
- 核心结果段优先形成“关键数值/现象 → 比较基准 → 机制解释 → 题目结论 → 必要边界”；
- 模型评价不再强制“优点三条、缺点两条、推广一段”，而应写当前模型的机制闭环、验证证据、计算结构、解释能力和明确的失效来源；
- 物理机理、统计回归、机器学习、优化网络、动态仿真和多问混合题采用不同的章节证据链，避免所有论文三级标题机械同构。

AI cleanup 进一步执行“替换测试”：如果把本题研究对象换成另一类赛题后某段仍基本成立，除必要过渡与标准数学定义外，应优先视为模板段并改写或删除。

## 四个前置治理点

- `Problem Contract`：冻结原始/派生对象、已知/可计算量、决策/状态/输出量、显式/隐含约束、禁止假设、数据角色和小问依赖；
- `preprocessing_decision`：根据当前数据质量、结构、模型输入要求和泄漏风险判断“数据可直接用”“本问局部变换”“项目级公共处理”；
- `semantic closure / revision`：题面对象与要求 → 数学变量/公式/目标/约束 → Python变量/函数 → 工作簿输出/验证证据；数据判定、处理口径、模型或依赖变化按 typed dependencies 传播 stale；
- `complexity sanity`：复杂题异常降维、异常解耦、关键条件或附件闲置、关键约束长期不生效、后问复制前问或计算异常容易时强制复审。

## 每问默认交付

```text
问题X求解/
├─ 问题X求解.py
├─ 问题X求解结果.xlsx
├─ 问题X结果深化分析.py
├─ 问题X结果深化分析.xlsx
└─ qX_plot.m
```

`data_process.m` 属于项目级预处理目录，不改变每问五文件合同。

主工作簿 accepted 后冻结 `问题X求解.py`；随后单独生成 `问题X结果深化分析.py`。不默认生成独立运行配置、运行说明、校验报告、`图表/` 或额外元数据。

## 质量门

- `scripts/validate_semantic_governance.py`：题意口径、语义闭环、复杂度复审、semantic revision 与跨小问 stale；
- `core/global_preprocessing_contract.yaml`：通用数据审计、缺失/插值/预测填补边界、预处理必要性、论文数学证据与 `data_process` 图证据；
- `core/code_quality_contract.yaml`：实际生成的预处理/主求解/深化分析 Python 的代码工程质量；
- `scripts/validate_code_delivery.py`：按 `preprocessing / primary / analysis` 阶段静态检查代码，不执行赛题；
- `scripts/validate_user_execution.py`：验收适用工作簿、代码/数据哈希、预处理论文/绘图底层证据与质量门；
- `scripts/sync_project.py`：正式交付前按 active data source 检查产物、哈希和 stale，并在 project-level 的 figures 及后续阶段要求 `data_process.m`。

代码默认以 500 行以内为目标；501--700 行给 warning；超过 700 行默认拒绝，复杂题显式豁免最多到 900 行。单函数以 80 行以内为目标，超过 120 行拒绝；函数参数以 8 个以内为目标，超过 12 个拒绝。详细规则只在 `core/code_quality_contract.yaml` 定义。

## 启动与检查

```bash
python scripts/resolve_workflow.py full_solution --objective optimization --competition CUMCM --preprocessing-decision not_needed
python scripts/resolve_workflow.py full_solution --objective optimization --competition CUMCM --preprocessing-decision project_level
python scripts/validate_semantic_governance.py <project_root> --write --strict
python scripts/validate_code_delivery.py <project_root> --write --strict
python scripts/sync_project.py <project_root> --write --strict --delivery-scope figures
```

仓库维护执行 `python scripts/lint_skill.py`、全量单元测试和生成索引检查。DOCX 是显式可选分支；v7.2.0--v7.2.2 项目重新进入设计、预处理、绘图或写作时继续沿用三态 `preprocessing_decision`，但按当前通用审计与论文证据规则复核；历史只读交付不强制反向补 `data_process.m`。
