# P8 `lint_skill_checks.py` 结构测量证据

> 本文件是 P8 维护证据，不是 Runtime / Workflow Authority。函数名族与函数跨度只描述源码结构，不证明语义独立性。

## 1. 测量口径

- 基线：`main@a1641af6a93b41e06b45be6dde8b621dd7af2fa1`（P8c 合并后）。
- 测量 schema：`1.1.0`。
- 入口：`python scripts/measure_infrastructure.py --json --top 20`。
- AST 只把模块顶层 `def/async def` 计入可拆分表面；嵌套函数单独计数，不把局部实现误当模块 API。
- `name_prefix_families` 是词法分组，不是职责判定；任何实际拆分仍须读取对应函数依赖并保持 CLI、错误文本与检查集合等价。

## 2. 结构事实

- 文件：`scripts/lint_skill_checks.py`
- bytes：**92,631**
- 非空行：**1,317**
- 顶层函数：**25**
- 嵌套函数：**3**
- 顶层函数跨度合计：**1,288 行**
- 顶层函数跨度中位数：**24.0 行**
- 最大顶层函数跨度：**260 行**

### 跨度分布

| 区间（行） | 函数数 |
|---|---:|
| `1-20` | 10 |
| `21-50` | 5 |
| `51-100` | 8 |
| `101-200` | 1 |
| `201+` | 1 |

### 名称前缀分布（仅词法证据）

| 前缀族 | 函数数 |
|---|---:|
| `check` | 20 |
| `entrypoint` | 1 |
| `load` | 2 |
| `other` | 2 |

### 最大的顶层函数

| 排名 | 函数 | 行范围 | 跨度 |
|---:|---|---:|---:|
| 1 | `check_contracts` | 635–894 | 260 |
| 2 | `check_templates` | 1001–1179 | 179 |
| 3 | `check_router` | 446–545 | 100 |
| 4 | `check_editable_mechanism_diagrams` | 1269–1354 | 86 |
| 5 | `check_manifest` | 548–632 | 85 |
| 6 | `check_final_review_compliance` | 1182–1266 | 85 |
| 7 | `check_repository_references` | 216–292 | 77 |
| 8 | `check_skill_entrypoint_parity` | 140–213 | 74 |
| 9 | `check_project_state_and_framework` | 897–963 | 67 |
| 10 | `check_bootstrap_and_governance` | 378–428 | 51 |
| 11 | `check_resolver_smoke` | 295–341 | 47 |
| 12 | `check_competition_writing_runtime` | 966–998 | 33 |
| 13 | `main` | 1379–1402 | 24 |
| 14 | `check_compatibility_pointers` | 97–119 | 23 |
| 15 | `check_versions` | 353–375 | 23 |
| 16 | `_check_repo_reference` | 122–137 | 16 |
| 17 | `check_taxonomy` | 431–443 | 13 |
| 18 | `check_syntax` | 1357–1365 | 9 |
| 19 | `check_generated` | 1368–1376 | 9 |
| 20 | `load_module` | 75–81 | 7 |

## 3. P8 解释边界与下一步

1. 该测量证明的是维护热点的**结构分布**，不是“文件大所以必须拆”的规则。
2. 后续若拆分，只允许纯结构搬移：`scripts/lint_skill.py` CLI、现有检查集合、错误文本、返回码与 generated-file gate 必须保持等价。
3. 优先阅读跨度最大的函数及其共享 helper/常量依赖，寻找能够按既有检查族成组迁移的边界；不得按固定行数机械切割。
4. 若依赖分析显示检查族高度交叉，则 P8 可以保留单文件；“不拆”同样是基于测量的合法结论。
5. 任何候选结构拆分都必须重新跑 `lint_skill.py`、全量 unittest、generated check、HSK Skill CI 与 Optimization baseline。
