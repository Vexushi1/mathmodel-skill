# HSK 公式—代码闭环检查表

代码文件与函数锚点填写本问实际登记的 Python/MATLAB 主或深化入口；辅助源码必须属于当前实现依赖，不以示例文件名代替真实路径。公式数学角色与原表列序保持。

> 用途：检查论文公式是否真正进入代码，代码变量是否能回溯到论文符号。公式漂亮但代码不用，或代码使用变量但论文未定义，都属于高风险问题。

| 公式编号 | 公式作用 | 关键符号 | 正文解释是否充分 | 对应代码文件 | 对应代码变量/函数 | 是否参与求解 | 风险 |
|---|---|---|---|---|---|---|---|
| (1) | 目标函数 | $Z,x_i,c_i$ | 是/否 | `当前主求解入口` | `objective(x)` | 是/否 |  |
| (2) | 约束条件 | $g_j(x)$ | 是/否 | `当前主求解入口` | `constraint_violation()` | 是/否 |  |
| (3) | 评价指标 | $S_i,w_j$ | 是/否 | `当前已声明实现文件` | `compute_score()` | 是/否 |  |

## 闭环判定

- 每个核心公式必须编号并被正文引用；
- 每个符号必须在符号表或公式邻近文本中解释；
- 每个目标函数、约束、评价指标必须能对应到代码变量或函数；
- 若公式仅用于理论说明而不参与求解，需在“公式作用”中写明；
- 代码中出现的重要变量不得脱离论文符号体系。

## A1 可选只读结构核验

使用 `scripts/model_code_conformance.py <project_root> --question Q1 --stage primary`；分析阶段显式使用 `--stage analysis`。`--inventory` 返回当前已批准SIB选择器、唯一可定位符号、源码摘要和有限反向候选，只作填报导航，不写入项目、不产生通过记录。

记录放在 `subproblems.Q1.implementation_conformance.primary`（或analysis），形状只服从 `core/project_state.schema.yaml#/$defs/implementation_conformance_record`，语义与边界只服从 `core/model_code_conformance_contract.yaml`。绑定当前 `semantic_revision`、`semantic_identity_hash`、后端、阶段入口和完整源码bundle；每条映射使用真实SIB的field/id、数学作用说明、相对源码路径、唯一符号和片段SHA。不能把只列自己认为重要的模型条目当作完整覆盖；不能拿主求解记录验收深化源码。

可选表达式检查仅消费已批准SIB条目内的 `implementation_expression`，Python为单一静态return的受限算术AST，MATLAB为平坦函数的单一赋值表达式。**不能为通过此检查自动向已批准模型补参考表达式**；修改SIB仍须现有语义与批准流程。代数等价/合法近似/数值选择须声明关系与依据，不因语法不同直接判断模型错误。没有明确参考时保留语义复核，不用函数名或注释猜公式。

`structure_verified`只表示声明覆盖、身份和静态引用闭合；不证明约束参与了求解，不证明数学等价，也不替代工作簿验收。`needs_review`和`not_assessed`的退出码为2，`blocked`为1，只有结构通过为0。反向裁剪候选的填报说明不是独立审查记录。A1默认只读stdout，尚未接入代码交付/回执/论文的强制门；A2单独处理该集成。
