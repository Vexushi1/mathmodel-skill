# mathmodel-skill v7.2.2

当前工作流：**审题与 Problem Contract 冻结 → 通用数据审计与 `preprocessing_decision` → 题面—数学—代码语义闭环 → Complexity Sanity Check → semantic governance → 条件式项目级预处理（仅 `project_level`）→ 用户本地完整版 Python 主求解 → 主结果质量门 → 独立 Python 结果深化分析 → 稳定性验收 → MATLAB证据图 → LaTeX终稿**。

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

判定不依赖某一种赛题经验，而取决于**当前题目、当前附件和当前模型要求**。至少检查：

- 完整性：缺失、NaN/Inf、空白、连续缺口、边界缺失、整组缺测；
- 一致性：单位、量纲、类型、编码、主键、时间格式/时区、坐标系、多表关联；
- 有效性：违反物理边界、逻辑约束或跨字段关系的不可能值；
- 身份与重复：区分真正重复记录、重复采样和独立重复试验；
- 采样与覆盖：时间/空间步长、规则性、断档、稀疏区、覆盖不均；
- 测量质量：噪声、漂移、饱和、坏道、异常尖峰、检测下限；
- 模型适配：模型是否要求完整矩阵、规则网格、正值、尺度变换、类别编码或其他输入条件；
- 时间因果与泄漏：任何填补、标准化或特征构造是否偷用了未来信息或目标标签。

两个及以上小问共享同一原始数据，只说明需要统一审计口径，**不能单独推出需要清洗、插值、滤波、标准化或统一工作簿**。同样，存在缺失值也不能直接推出“必须插值”：必须先判断变量类型、缺失位置和缺口长度、是否存在连续机制、模型是否可原生处理，以及保持缺失、删除、插值、统计填补、模型填补或预测填补哪一种假设最弱且可验证。

### 插值与预测填补边界

插值只在连续变量具有明确局部连续性、缺口长度和边界位置允许时考虑；类别、ID、标签、事件状态及无连续机制的变量不得机械数值插值。模型化或预测填补必须有独立恢复能力验证，时序任务还必须保持时间顺序，禁止使用未来信息。

“预测填补”和“题目要求预测”严格分开：前者只是为了恢复后续模型确实需要的缺测输入，可能属于预处理；若赛题本身要求预测未来值、未知类别、需求、价格、风险、趋势或其他最终结果，则属于核心预测模型，不能提前包装成数据预处理。

任何修改数据的操作都必须说明：问题是否真实存在、不处理会影响什么、为什么选择该方法和参数、是否可能破坏真实信息、以及如何独立验证。无法闭合这些问题的处理不应保留。

地震类规则只作为领域示例：去直流、去趋势、带通、坏道修复、taper、插值/重采样均为条件操作，不是其他赛题的默认模板。

## 四个前置治理点

- `Problem Contract`：冻结原始/派生对象、已知/可计算量、决策/状态/输出量、显式/隐含约束、禁止假设、数据角色和小问依赖；
- `preprocessing_decision`：根据当前数据质量、结构、模型输入要求和泄漏风险判断“数据可直接用”“本问局部变换”“项目级公共处理”；共享数据或题型标签本身不是 `project_level` 的充分条件；
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

只有 `preprocessing_decision=project_level` 时额外存在：

```text
数据预处理/
├─ 数据预处理.py
└─ 数据预处理结果.xlsx
```

主工作簿 accepted 后冻结 `问题X求解.py`；随后单独生成 `问题X结果深化分析.py`。不默认生成独立运行配置、运行说明、校验报告、`图表/` 或额外元数据。

## 质量门

- `scripts/validate_semantic_governance.py`：题意口径、语义闭环、复杂度复审、semantic revision 与跨小问 stale；
- `core/global_preprocessing_contract.yaml`：通用数据审计、缺失/插值/预测填补边界、预处理必要性、三态判定、处理操作准入与公共数据边界；
- `core/code_quality_contract.yaml`：实际生成的预处理/主求解/深化分析 Python 的代码工程质量；
- `scripts/validate_code_delivery.py`：按 `preprocessing / primary / analysis` 阶段静态检查代码，不执行赛题；
- `scripts/validate_user_execution.py`：按当前 decision 验收适用工作簿、代码/数据哈希与质量门；
- `scripts/sync_project.py`：正式交付前按 active data source 检查产物、哈希和 stale。

代码默认以 500 行以内为目标；501--700 行给 warning；超过 700 行默认拒绝，复杂题显式豁免最多到 900 行。单函数以 80 行以内为目标，超过 120 行拒绝；函数参数以 8 个以内为目标，超过 12 个拒绝。详细规则只在 `core/code_quality_contract.yaml` 定义。

## 启动与检查

```bash
# 已判定原始数据可直接使用
python scripts/resolve_workflow.py full_solution --objective optimization --competition CUMCM --preprocessing-decision not_needed

# 已判定需要项目级统一处理
python scripts/resolve_workflow.py full_solution --objective optimization --competition CUMCM --preprocessing-decision project_level

python scripts/validate_semantic_governance.py <project_root> --write --strict
python scripts/validate_code_delivery.py <project_root> --write --strict
python scripts/sync_project.py <project_root> --write --strict --delivery-scope results
```

仓库维护执行 `python scripts/lint_skill.py`、全量单元测试和生成索引检查。DOCX 是显式可选分支；v7.2.0--7.2.1 项目重新进入设计/求解时继续沿用三态 `preprocessing_decision`，但按当前通用审计规则复核处理必要性；更早版本继续按只读兼容规则处理。
