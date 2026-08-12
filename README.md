# mathmodel-skill v7.2.1

当前工作流：**审题与 Problem Contract 冻结 → 数据审计与 `preprocessing_decision` → 题面—数学—代码语义闭环 → Complexity Sanity Check → semantic governance → 条件式项目级预处理（仅 `project_level`）→ 用户本地完整版 Python 主求解 → 主结果质量门 → 独立 Python 结果深化分析 → 稳定性验收 → MATLAB证据图 → LaTeX终稿**。

## 数据阶段：先判断，不默认清洗

所有带数据的题都先做字段、维度、单位、主键、NaN/Inf、重复、时间/空间粒度等**非破坏性审计**，然后锁定：

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

两个及以上小问共享同一原始数据，只说明需要统一审计口径，**不能单独推出需要清洗、插值、滤波、标准化或统一工作簿**。缺失填补、异常删除、插值、平滑、滤波、去趋势、归一化、标准化、重采样等修改数据的操作必须逐项给出数据、机理或模型必要性证据。

地震类数据同样执行“先审计后处理”：去直流、去趋势、带通、坏道修复、taper、插值/重采样均为条件操作，不是默认步骤；默认禁止无依据平滑速度场、AGC、逐道强归一化、默认带通和默认坏道插值。

## 四个前置治理点

- `Problem Contract`：冻结原始/派生对象、已知/可计算量、决策/状态/输出量、显式/隐含约束、禁止假设、数据角色和小问依赖；
- `preprocessing_decision`：区分“数据可直接用”“本问局部变换”“项目级公共处理”，共享数据本身不是 `project_level` 的充分条件；
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
- `core/global_preprocessing_contract.yaml`：数据审计、预处理必要性、三态判定、处理操作准入与公共数据边界；
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

仓库维护执行 `python scripts/lint_skill.py`、全量单元测试和生成索引检查。DOCX 是显式可选分支；v7.2.0 项目重新进入设计/求解时先补齐 `preprocessing_decision`，不得因历史共享数据自动迁移成 `project_level`；更早版本继续按只读兼容规则处理。
