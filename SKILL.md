---
name: mathmodel-skill
version: 7.5.1
summary: HSK mathematical-modeling workflow with Problem Contract freezing, semantic closure, generalized evidence-driven conditional preprocessing, preprocessing paper/mathematical evidence, dedicated data_process MATLAB figures, dynamic evidence-driven MATLAB layouts and high-contrast scientific palettes, dependency-aware stale propagation, full-fidelity user execution, separate primary/result-analysis Python stages, affirmative evidence-driven CUMCM writing, paragraph-first proposition proofs, final prose audit and LaTeX-first delivery.
triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 建模论文, 模型论文框架, 数据预处理, 数据清洗, 主结果质量, 结果深化分析, Python求解, MATLAB绘图, LaTeX, DOCX]
---

# HSK 数学建模模块化工作流 v7.5.1

## 默认执行

先读 `core/bootstrap.yaml`，再由 `scripts/resolve_workflow.py` 按任务加载模块。进入正式模型或代码前，必须完成 Problem Contract 题意口径冻结、数据质量审计与 `preprocessing_decision`、题面—数学—代码—输出语义闭环、Complexity Sanity Check，并由 `scripts/validate_semantic_governance.py` 检查当前 semantic revision 和跨小问依赖 stale。

### `模型论文框架.md` 是项目工作记忆

`locked_model_spec` 形成后，项目根目录 `模型论文框架.md` 不只是交付给用户查看的框架文件，也是助手跨阶段、跨聊天恢复当前项目语义的首选入口。已有 current 框架时，后续预处理、求解、深化分析、绘图和写作应先按需读取相关段落；单问继续优先读取当前有效口径、对应小问和必要依赖，整篇论文、跨问综合、长上下文恢复与终审读取完整框架。不得仅依赖聊天记忆重新拼接已锁定模型。

框架负责当前语义、结果摘要和证据导航；具体数值必须回到已验收工作簿复核，semantic revision、hash 和 stale 继续由 `state/project_state.yaml` 管理。模型/参数/约束/预处理/算法语义变化后，以及主结果、深化结果、图表验收后，都要同步受影响的当前框架内容。

### 数据阶段硬规则

所有数据题都先审计，但不是所有数据题都要清洗：

```text
preprocessing_decision
├─ not_needed     → 不创建数据预处理/，直接读取原始数据
├─ question_local → 不创建全局预处理目录，本问脚本内做有数学来源的局部变换
└─ project_level  → 数据预处理.py → 数据预处理结果.xlsx → 依赖小问统一读取
```

是否进入预处理阶段必须根据**当前题目和当前附件本身**判断，不按某一种赛题或过去经验套模板。至少审计：缺失/NaN/Inf、缺失分布与连续缺口、单位/类型/主键/时间/坐标一致性、重复记录、物理或逻辑无效值、时间/空间采样与覆盖、测量噪声或漂移、模型对规则网格/完整矩阵/尺度/编码等输入要求，以及预测任务中的时间因果和信息泄漏。

两个及以上小问共享同一原始数据源只触发统一口径审计，不能单独推出需要清洗、插值、滤波、标准化或统一工作簿。存在缺失值也不能直接推出“必须插值”：应先判断变量类型、缺失位置、缺口长度、连续机制、模型是否原生支持缺失，以及删除、保持缺失、插值、统计填补、模型填补或预测填补哪一种假设最弱且可验证。

预测填补仅可用于恢复后续模型确实需要的缺测输入，并必须有独立验证且不得使用未来信息或目标标签；若赛题本身要求预测未来值、未知类别、需求、价格、风险或其他最终结果，该预测属于核心建模，不得提前包装成数据预处理。

### 预处理一旦启用，论文与图表必须形成证据链

只要实际数据变换参与后续模型，就不能在论文中只写“完成清洗”“进行了插值/标准化”。必须闭合：

```text
数据问题与必要性
→ 方法选择与替代方案
→ 数学公式/变换关系/目标函数
→ 参数与阈值来源
→ 理论、统计或物理合理性验证
→ 处理前后底层数据证据
→ MATLAB证据图
→ 后续模型输入接口
```

确定性单位/坐标/主键处理给出映射和一致性检查；标准化/变换给出公式和参数估计范围；插值/填补给出公式或目标函数、边界条件和人工掩蔽/留出恢复误差；滤波/平滑/重采样给出核函数、频率响应或离散映射及参数依据；异常处理给出判定指标、阈值来源及保留/处理对照。

“合理的方法证明”不等于所有清洗都写形式定理。只有存在等价性、守恒性、单调性、误差界或可行性保持等可证明命题时才写形式证明；经验型处理使用统计检验、物理约束、人工掩蔽、留出验证、残差、频谱、分布和处理前后对照等可复验证据。

`project_level` 的最终预处理目录固定为：

```text
数据预处理/
├─ 数据预处理.py
├─ 数据预处理结果.xlsx
└─ data_process.m
```

`data_process.m` 是项目级预处理证据的固定 MATLAB 绘图脚本名；文件归属 `数据预处理/`，但仅在 Figure Evidence 阶段、主求解与结果深化分析完成后生成。它只读取 `数据预处理结果.xlsx` 中 Python 已保存的处理前后、诊断和验证底层数据，绘制处理前后、缺失/填补、分布、频谱、掩蔽恢复、采样覆盖或异常阈值等证据图；禁止在 MATLAB 中重新清洗、插值、滤波、重采样、训练填补模型或重新选择参数。正式导出图片基名使用 `data_process` 或 `data_process_<evidence>`，默认仍只保留图窗人工检查。

`question_local` 的实质变换在对应小问正文写公式、参数依据和验证；若需要图证据，由该问 `qX_plot.m` 读取 Python 已输出的底层数据绘制。

赛题数值代码由用户本地以 `full_fidelity` 运行；助手生成并静态检查代码，不运行赛题代码、不自动降采样、不静默切换求解器。

每问完成数值阶段后默认恰好包含：

```text
问题X求解/
├─ 问题X求解.py
├─ 问题X求解结果.xlsx
├─ 问题X结果深化分析.py
├─ 问题X结果深化分析.xlsx
└─ qX_plot.m
```

完整运行配置分别嵌入实际生成的阶段 Python 并写入对应工作簿；运行步骤和校验结果只在聊天或标准输出中返回。主工作簿验收后冻结 `问题X求解.py`，随后独立生成 `问题X结果深化分析.py`，不得为深化分析覆盖改写主求解脚本。

### Figure Evidence 硬规则

MATLAB 结果图不固定套用单图、`1×2` 或 `2×2`。生成代码前必须先写 `Core conclusion / Evidence level / Primary question`，再通过 `modules/04_figure_evidence.md` 的 Figure Layout Gate 动态选择 `单图 / 1×2 / 2×1 / 1×3 / 2×2 / 拆图`。单图能闭合结论时不强行加 panel；两个互补证据优先双面板；`2×2` 只有在四个 panel 同属一个核心结论、具有明确成对/交叉结构且拆图会明显损失直接比较效率时保留。主结果、异质性、稳健性和数值合法性证据默认按 Evidence level 分层，不一股脑混装。

配色不再默认追求低饱和深色。白底、清晰轴线和语义一致性保持不变，但主比较允许使用中高饱和、高对比颜色，例如亮蓝 `#1478FF` 与鲜红 `#F04444`；主对象应醒目，置信区间、背景带、参考网格和次要元素使用浅色、灰色或透明度降权。禁止彩虹滥用和无序多色轮换。

### 写作阶段硬规则

LaTeX 是默认论文主链，`modules/05_writing/latex.md` 的“正文表达与章节组织协议（写作权威）”统一约束 DOCX、LaTeX 与 AI-cleanup。v7.5.1 延续 v7.4.4 的中文国赛正文结构，并增加成稿 prose audit：

- 问题重述默认采用“问题背景 + 问题提出”；问题背景通常一个自然段，问题提出按“问题一：”“问题二：”逐问用自己的理解转述研究对象、关键条件和待求输出；
- 问题分析按问题一、问题二……逐问分小节，只讲难点、对象关系、跨问依赖和建模抓手，禁止数学公式与最终结果；“问题提出”和“问题分析”不能换词重复；
- “模型假设”和“符号说明”为两个独立一级章节；可见假设使用 1.、2.、3. 自然编号，不显示 H1/A1 等内部合同编号；
- 符号尽量避免长文本和多层复合下标；场景、模型、方案等信息可优先使用简短上标，真实元素/坐标/时间索引保留短下标；
- 各问主章节默认使用“问题X模型建立及求解”，内部小节按题型动态命名；
- 每问详细推导后、数值求解前必须设置“核心模型汇总”，集中给出实际求解的目标、方程、约束和边界；
- 每问主结果默认放在“求解结果”小节，深化证据按实际方法命名；默认不设置固定“小问结论”，最后一个结果/深化段自然回答当前设问；
- 中文国赛默认不设置全文独立“结论”一级章；仅当届模板、用户或论文类型明确要求时增加；
- 命题短证明采用“分段优先、分点按需”：连续推理使用自然段和必要公式，只有分情况、存在性/唯一性、多条件验证等明显多阶段结构才使用 2--6 个编号步骤；命题显示编号使用阿拉伯章节号；机器契约不再保留会误导为“所有证明必须分步”的 segmented 字段；
- 表格严格“表上”，图片严格“图下”；三线表数值和短文本默认水平、垂直居中；每张正文核心图、核心表必须有邻近的显式编号引用和解释；
- 默认评价章节使用“模型的评价与推广”，确有实质改进时可用“模型的改进、评价与推广”；这一两级策略保持不变；优点多于缺点且优点不超过 4 条，改进/推广按证据选写；
- AI 模板清理后再进行科研初学者式学术重写：语言略朴素、生涩、认真但保持规范书面语，以正向连续叙述为主；高密度“但/然而/不是/不能/只能”等结构必须复查真实冲突，不通过故意病句、口语化、频繁自我否定或机械同义词替换制造风格；
- 完成逐段清理后运行 `python scripts/audit_paper_prose.py final_latex/main.tex`。默认只报告 pass/warning/review_required；warning 只用于人工复查，不机械封禁单个转折词；最终编译前用 `--strict` 清除结构性 review_required。

正文仍坚持本题对象和证据优先：问题重述不复制赛题；模型推导不写无关算法百科；结果解释必须把核心图表/关键数值、机制、题目回答和必要边界贴在一起；模型检验用量化证据，不能被万能优缺点替代。共享基础模型只定义一次，后续小问只写新增变量、目标、约束和证据。

DOCX 仅在用户显式要求时加载，不是 LaTeX 前置；其正文表达与 LaTeX 使用同一权威写作协议。

## 主链

```text
逐字审题 → Problem Contract冻结
→ 通用数据审计 → preprocessing_decision
→ 两条模型路线 → 变量/假设/公式/约束闭合
→ 题面—数学—代码语义闭环 → Complexity Sanity Check
→ semantic governance gate
→ [仅project_level] 项目级预处理 → 预处理质量门
→ Python完整主求解 → 主代码质量门 → 用户完整运行
→ 主结果质量门 → 独立Python结果深化分析 → 深化代码质量门 → 用户完整运行
→ 稳定性验收/必要时回退重算
→ [project_level] data_process预处理证据图
→ MATLAB各问结果图 → 题型自适应LaTeX直写 → AI-cleanup与语言重写
→ prose audit → 编译与终审
```

题意解释、数据范围、变量、参数、假设、目标、约束、`preprocessing_decision`、实际预处理、算法语义或小问依赖变化时必须递增 `semantic_revision`；已验证语义变化先使受影响结果 stale，再按 `data / parameter / model / result` 依赖递归传播。接受新语义不恢复旧数值，仍须重新执行适用的数据处理、求解与验收。

代码工程质量由 `core/code_quality_contract.yaml` 唯一定义并由 `scripts/validate_code_delivery.py` 检查实际生成的 `preprocessing / primary / analysis` Python；工作簿由 `scripts/validate_user_execution.py` 按当前数据决策验收。目录与正式交付以 `core/output_contract.yaml` 为准。

MATLAB 默认只保留图窗，不在求解目录创建 `图表/` 或自动导出。v7.2.0--v7.2.2 项目重新进入设计、预处理、绘图或写作时继续沿用三态 `preprocessing_decision`，并按当前通用审计与论文证据规则复核；历史只读交付不强制反向补文件。
