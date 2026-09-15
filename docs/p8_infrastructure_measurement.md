# P8 基础设施测量基线

> 本文件是维护证据，不是新的 Runtime / Workflow Authority。业务语义继续由 `core/bootstrap.yaml` 指向的 Authority、现有 validator 与 CI gate 决定。

## 1. 目的与边界

P8 的前提是“有测量依据再整理”，因此先固定可复算事实，再决定是否拆大型 validator、合并重复解析或调整 generated-metadata 工作流。该阶段不得因为文件大、调用重复或 CI 麻烦就删除测试、降低断言、绕过 generated check、缩减 Python 版本矩阵或改变模型/数值/状态语义。

可复算入口：

```bash
python scripts/measure_infrastructure.py
python scripts/measure_infrastructure.py --json
```

测量脚本只读 `scripts/*.py` 与 `.github/workflows/`，使用 AST 统计调用点；不写项目状态、不写 generated metadata、不执行赛题代码。

## 2. main@P7 的文件体量事实

P7 合并后的 `main` 为 `ff3bd24f622224a79476d6aa5b825cd8af886307`。GitHub contents 元数据显示当前 `scripts/` 中体量最大的 Python 文件为：

| 排名 | 文件 | bytes | 说明 |
|---:|---|---:|---|
| 1 | `scripts/lint_skill_checks.py` | 92,631 | 跨合同静态检查集合，明显高于其余脚本 |
| 2 | `scripts/validate_model_paper_framework.py` | 37,234 | framework validator |
| 3 | `scripts/audit_paper_prose.py` | 34,800 | prose audit |
| 4 | `scripts/sync_project.py` | 33,694 | project sync |
| 5 | `scripts/generate_mechanism_drawio.py` | 33,583 | mechanism figure generator |
| 6 | `scripts/validate_project_state.py` | 27,836 | project-state validator |
| 7 | `scripts/resolve_workflow.py` | 27,741 | legacy-compatible resolver |
| 8 | `scripts/validate_code_delivery.py` | 27,675 | code-delivery validator |
| 9 | `scripts/validate_user_execution.py` | 25,814 | returned-execution validator |
| 10 | `scripts/runtime_assurance.py` | 25,322 | runtime assurance |

结论只到“维护热点”层面：**文件大本身不是删除/拆分理由**。其中 `lint_skill_checks.py` 约为第二名的 2.49 倍，值得作为首个结构候选；其余文件是否拆分必须看职责耦合与回归证据。

## 3. 重复解析事实

默认分支代码搜索显示，`yaml.safe_load` 分散在多处活动脚本，包括 resolver、runtime assurance、sync、submission、LaTeX、多个 validator 以及 `lint_skill_checks.py`。P8 测量脚本用 AST 给出精确的：

- `yaml.safe_load` 调用总数；
- 含该调用的脚本数；
- 各脚本调用点数；
- `openpyxl.load_workbook` 调用总数。

当前已经确认的高价值重复之一是 P5 后形成的运行配置静态解析：`validate_code_delivery.py` 与 `validate_user_execution.py` 都识别 `RUN_CONFIG / FULL_FIDELITY_CONFIG / FULL_RUN_CONFIG`，都要求同一脚本只能出现一个受支持顶层字典配置。后续若提取共享 helper，必须保持两端现有错误边界、legacy 只读兼容和 fail-closed 多配置语义，并由 P5a/P5b 回归锁定。

不得把所有 `yaml.safe_load` 机械替换为单一 helper：现有调用对“文件不存在”“空文件”“必须为 mapping”“错误是否上抛”的语义并不完全相同。只有语义等价的一组才允许合并。

## 4. generated-metadata 工作流事实

`.github/workflows/refresh-generated.yml` 当前设计为：

- 默认 `contents: read`；
- feature branch 的 `refresh-feature-branch` 单独获取 `contents: write`；
- 运行 `python scripts/generate_indexes.py`；
- generated 文件变化时由 `github-actions[bot]` commit + push；
- main 只执行 `python scripts/generate_indexes.py --check`。

该设计保护了 main 的只读校验，但近期优化 PR 已多次出现同一种操作成本：bot 刷新 `MANIFEST.sha256` / Index 后，最终 head 需要 same-tree 用户身份提交重新触发完整 HSK Skill CI 与 Optimization baseline。P5a #157、P6a #159、P6b #160、P7 #161 的验收记录都出现了该模式。

因此 P8 可以研究自动化 final-head 再验证，但有硬边界：

1. 不得用“generated workflow 自己跑几个测试”替代现有完整 CI；
2. 不得伪造 commit status；
3. 不得关闭 generated check；
4. 若无法让 bot-generated final head 触发**同等完整**的 HSK Skill CI + Optimization baseline，则保留当前 same-tree retrigger，而不是为了少一步操作降低门禁。

## 5. P8 后续整理顺序

依据当前测量，后续按风险从低到高处理：

1. **重复解析 helper**：优先处理有现成 P5 行为测试保护的 RUN_CONFIG 静态解析，不改 Authority 字段；
2. **大型 validator**：先对 `lint_skill_checks.py` 做职责/函数分布测量，再按纯结构模块拆分；CLI、错误文本和检查集合保持等价；
3. **generated metadata**：只有在能对 bot final head 自动运行同等级完整门禁时才改变 retrigger 机制；
4. 每一步均运行完整 `lint_skill.py`、全量 unittest、`generate_indexes.py --check`、HSK Skill CI 和 Optimization baseline。

P8 不触及 release carriers。版本与兼容窗口统一留给 P9。
