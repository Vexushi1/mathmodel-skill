# v9.7.0 Python / MATLAB 求解后端迁移与验证

本文件记录本次已批准重构的范围、兼容方式与验证入口，不另立执行、数值或写作规则。规则分别服从 `core/bootstrap.yaml` 指向的 Authority。

## 1. 修改简报

| 项目 | 内容 |
|---|---|
| 修改主题 | 将固定 Python 的 03A 主求解与条件式 03B 深化分析扩展为 Python / MATLAB 自适应后端 |
| 起点 | v9.6.1，main `ec638b0790edf178999ae8c9095fe0ed5849a43c` |
| 目标版本 / 等级 | v9.7.0 / minor |
| 直接目标 | 按问题、按阶段明确后端；同一工作簿与验收链贯通求解、分析、绘图、写作、打包 |
| 修改方式 | 保持现有大模块，集中抽取阶段代码识别与身份绑定；按接口调整 Authority 和消费者 |
| 范围边界 | 项目级预处理仍为 Python；不改变数学模型批准、数值通过标准、工作簿业务字段、赛事政策、正式绘图风格与 LaTeX 架构 |
| 兼容要求 | 保留旧 Python 路径、回执 1.0、历史 FULL/P5a 读取和省略新参数的 CLI/API 输出投影 |
| 迁移要求 | 老项目不自动转换；新 MATLAB 与新协议代码显式选择、重新交付、实际运行、重新验收 |
| 回滚 | 整体撤销此主题的源码和生成元数据提交；新协议项目保留原文件，不降格伪造旧回执 |

跨文件变更属于同一执行接口闭环：只修改 03A 会使回执、状态、03B、图文与 ZIP 对 MATLAB 文件作出不同判断。因此它们在同一个主题 PR 审查，生成文件单独提交；没有复制一套 MATLAB 专属状态机、审批流或数值验收规则。

## 2. Authority 与修改面

| 环节 | Authority / 主要实现 | 本次职责 |
|---|---|---|
| 启动与选择 | `core/user_execution_contract.yaml`、`core/runtime_assurance_contract.yaml`、`scripts/resolve_runtime.py` | `auto/python/matlab` 请求，恢复项目当前选择，报告冲突与环境未验证状态 |
| 路由与产物 | `core/workflow_router.yaml`、`core/module_manifest.yaml`、`core/output_contract.yaml`、`scripts/resolve_workflow.py` | 中立的 `primary_code/stage_code` 角色与旧别名投影，只加载命中的后端和阶段模板 |
| 代码识别与配置 | `scripts/stage_code.py`、`scripts/run_config_parser.py` | 一处识别 `.py/.m` 阶段入口、静态提取配置、解析声明依赖、计算 bundle |
| 交付检查 | `core/code_quality_contract.yaml`、`scripts/validate_code_delivery.py`、`scripts/matlab_code_checks.py` | Python 原检查；MATLAB 原生 Code Analyzer、依赖与角色检查，交付身份绑定 |
| 用户执行与回执 | `core/user_execution_contract.yaml`、`scripts/validate_user_execution.py` | 兼容旧协议；1.1 绑定后端与代码闭包，实际工作簿通过原数值门后写入 accepted |
| 生命周期 | `core/project_state.schema.yaml`、`core/state_transition_contract.yaml`、snapshot/sync/runtime assurance | 可选后端元数据，当前/交付/已验收摘要分离，复用既有失效事件和 typed dependency 传播 |
| 模型与算法 | `core/model_approval_contract.yaml`、`core/writing_reasoning_contract.yaml`、模型模板与框架校验器 | 实现锚点可定位 Python 或 MATLAB 入口/函数；语言名称不替代数学语义身份 |
| 原生 MATLAB | `templates/code/matlab/` | 独立主求解和按需分析实例、原生工作簿、运行前后身份检查、失败诊断 |
| 下游消费 | `modules/04_figure_evidence.md`、写作与交付模块、`scripts/submission_requirements.py` | 接受同一已验收工作簿；按实际阶段入口和 helper 收集复现包 |
| 回归与发布 | `tests/test_solver_backend*.py`、`tests/test_matlab_code_checks.py`、`tests/matlab/`、CI | 旧链兼容、新接口负例、真实 MATLAB 与混合执行、生成索引和校验清单 |

全局 policy、入口摘要、相关 packs/模板只同步必要摘要或指针。没有新增普通论文写作 Authority。

## 3. 后端选择与阶段边界

用户明确指定求解语言时，活动 Skill 入口传 `--solver-backend python` 或 `--solver-backend matlab`；用户未指定且项目无当前阶段选择时，新求解任务显式传 `--solver-backend auto`。`auto` 是尚待完成的选择请求，不是已经探测到 MATLAB，也不是同时生成两份求解代码。选择依据包括用户明确要求、已批准模型和实际算法、现有源码/依赖、运行环境、许可证及工具箱可用性。环境事实未经检查时保留未验证，不把路由输出当作可运行证明。

每问在 `solver_execution.primary` 中保存后端和选择理由；只有实际需要 03B 时才建立 `solver_execution.analysis`。03B 默认继承主求解后端，有明确必要性时可独立选择另一后端。恢复已有项目时使用当前状态，显式新偏好与状态冲突时报告待复核，不静默改写现有代码身份。

| 阶段 | Python 入口 | MATLAB 入口 | 说明 |
|---|---|---|---|
| 03A 主求解 | `问题一求解/问题一求解.py` | `问题一求解/q1_solver.m` | 同一问只能有一个当前入口，保留旧名称兼容 |
| 03B 深化分析 | `问题一求解/问题一结果深化分析.py` | `问题一求解/q1_analysis.m` | current accepted 主结果 + Analysis Necessity Gate 为 required 才交付 |
| 项目级预处理 | 原 Python 入口 | 不新增 | 保持原 1.0 回执和数据身份 |
| 正式绘图 | 不改变现有职责 | 原 `q1_plot.m` / `data_process.m` | 只读已验收证据，不作为求解阶段入口 |

其他问题用对应中文序号和 `qN` 编号。裸词“MATLAB”不足以确定业务意图；“MATLAB 求解”不应自动增加绘图任务。`not_required` 是 03B 的合法终态，不强制生成分析脚本/工作簿。

## 4. 配置、回执与身份

新 03A/03B 的 RUN_CONFIG 使用 `run_receipt_protocol_version: 1.1.0`，包含 `solver_backend`；项目级预处理继续使用 1.0.0。MATLAB 采用可静态读取的唯一 JSON 字面量声明，例如 `RUN_CONFIG = jsondecode('...');`。解析不执行 MATLAB、不求值表达式、不允许通过动态覆盖隐藏实际配置。

原入口 SHA 字段继续有效。新 bundle 覆盖入口以及 RUN_CONFIG 声明的实际项目源码 helper：

1. 将文件路径规范为项目内相对 POSIX 路径，检查越界、冲突和声明摘要。
2. 按路径的 UTF-8 字节顺序排序。
3. 每项连接路径 UTF-8 字节、一个 NUL、文件 SHA-256 的 32 个原始字节。
4. 对连接结果计算 SHA-256；不添加前缀，不把 bundle 写回它自身所覆盖的入口配置。

运行回执在原 `运行配置(项目, 值)` 工作表增加 `solver_backend` 和 `code_bundle_sha256`。不要求用户另交 JSON/YAML 回执。数据摘要、主工作簿摘要和数值证据保持各自职责，不能用代码摘要代替。

新 1.1 代码在 `project_level` 下显式写 `data_identity_mode="preprocessing_workbook"`，`data_paths` 恰为已验收的预处理 XLSX，`data_sha256` 沿用该工作簿的普通文件 SHA-256。`not_needed/question_local` 默认 `combined`，使用既有输入集合摘要；不能因为更换求解语言而重定义预处理的数据身份。项目级 Python 预处理自身仍为原 1.0，不写该新字段。

`bundle_sha256` 表示正式交付时的身份，`validated_bundle_sha256` 表示已验收运行的身份。snapshot 发现新文件只能更新观察值；禁止把新观察值补写成旧运行的证明。入口/任一 helper 改变后，必须重新交付、实际运行和验收。仅修改选择理由不等于代码发生改变。

MATLAB 实例在求解前绑定代码、helper 和输入，写出前再次检查。运行中发生变化会报错，不能将运行结束后新文件的摘要附在旧内存结果上。代码动态加载无法确定实际来源时不得声称闭包已验证。

## 5. 交付与执行命令

以下命令从 Skill 根目录运行；`PROJECT` 是独立用户项目的绝对路径，不能用 Skill 源码目录代替。`MATLAB_EXE` 是实际 MATLAB 可执行文件；使用时替换占位值，并按本地 shell 为含空格路径加引号。

```text
python scripts/resolve_runtime.py --request "MATLAB求解" --solver-backend matlab --project-root PROJECT --question Q1
python scripts/validate_code_delivery.py PROJECT --script 问题一求解/q1_solver.m --stage primary --matlab-command MATLAB_EXE --strict --write
```

后一个命令只进行原生静态 Code Analyzer 和原有代码交付/批准检查，不运行赛题模型。没有可用原生分析器时 MATLAB 代码只能标记 `unverified`，不得写入正式交付。缺少批准、输入/源文件绑定或必要代码质量证据时按原门禁返回失败。

代码交付后，由用户为每次正式 MATLAB 数值运行启动新的 `-batch` 进程，例如本问独立入口：

```text
MATLAB_EXE -batch "addpath('PROJECT/问题一求解'); q1_solver"
```

修改入口或 helper 后必须重新启动新进程；不得复用可能缓存旧函数的 GUI 会话。`clear/rehash` 不能解除所有已锁定函数，因此入口和项目 helper 禁止 `mlock`；该限制不等于禁止正常 `persistent`。新进程要求防止旧内存实现与新磁盘摘要混合，仍须保留运行前后身份复核。产生工作簿后验收：

```text
python scripts/validate_user_execution.py PROJECT --workbook 问题一求解/问题一求解结果.xlsx --strict --write
```

工作簿存在、MATLAB 正常退出或静态检查通过均不能替代 accepted。具体项目仍须通过其模型批准、PQS、Schema 与独立数值证据复核。深化分析另走同样阶段链，并绑定已验收主工作簿。

维护用 MATLAB 模板适用基线 R2024b，依赖 JVM 和有效 MATLAB 许可证，不需额外工具箱。具体模型如采用 Optimization Toolbox 等，须如实声明并核对；本版本不自动安装软件、购买许可证或把模板微型例子的通过当作任意模型的通过。

## 6. 工作簿与跨后端衔接

两种语言共用原工作表、字段、PQS、Evidence Capture 与验收器。MATLAB 原生 XLSX writer 先写同目录临时工作簿，成功完成后才替换目标，避免旧 sheet/尾行残留；失败保留此前有效文件。分析输出不得改写主结果。

数值、逻辑、文本、中文字段、前导零标识符和大整数文本按明确类型交接。缺失值必须有字段级含义，不得自动补零或删行。重复表头/键、非法非有限数值、空结果和错误摘要通过负例验证，不能依靠 reader 静默修正。

MATLAB→Python、Python→MATLAB 和同问混合 03A→03B 通过已验收工作簿交换数据。下游接收前需验证上游摘要和字段；语言切换不允许省略原有 Q1→Q2 的数据/参数依赖关系。

主求解/分析代码变化分别使用原 `primary_code_changed` / `analysis_code_changed` 事件，保持传播层级和已批准数学语义边界。若实际算法或模型语义也改变，仍按现有审批与语义 revision 流程处理。

## 7. 旧项目、打包与回滚

- 未新增后端元数据的旧 Python 项目继续按既有命名、已登记路径与旧回执验收。省略新 CLI 参数保留历史 artifact token；新调用使用中立名称，旧别名不会变成另一套文件角色。
- 将现有阶段改为 MATLAB 时，应保留历史证据，明确新的阶段入口、后端、选择理由与依赖；重新交付/运行/验收。旧的 accepted 记录不能直接继承给新代码。
- 复现包按项目当前每问、每阶段实际入口和声明 helper 精确检查。仅有 `q1_plot.m` 不能充当 `q1_solver.m`；纯 MATLAB 求解项目不因没有无关 `.py` 而失败。项目声明的 Python 预处理仍须打包。
- official 模式仍遵守原赛事精确 allowlist/PDF-only 规则，不强加复现包的源文件要求。
- 回滚应整体撤销本主题及其生成元数据。运行过新 MATLAB/1.1 的项目保留原始工作簿和记录，退回仅支持旧协议的 Skill 时不得伪造 1.0 来绕过兼容边界；可继续使用已验证的 v9.7.0，或重新生成旧后端并完成原执行链。

## 8. 验证与通过条件

| 类别 | 自动验证入口 | 必须观察的结果 |
|---|---|---|
| 旧接口与业务回归 | `python -m unittest discover -s tests` | 原 Python/FULL/P5a、审批、数值、状态、图文与包边界仍通过；跳过项明确列出 |
| 新配置与身份 | `tests/test_solver_backends.py` | 入口冲突、静态配置、helper闭包、后端/摘要篡改、旧协议兼容 |
| MATLAB 静态检查 | `tests/test_matlab_code_checks.py` | 原生结果分类、缺失分析器不得正式交付、不能把词法检查当运行 |
| 路由与生命周期 | `tests/test_solver_backend_integration.py`、`tests/test_solver_backend_runtime_resume.py` | 中立/旧输出投影、状态恢复、阶段模板、源文件失效、跨问依赖、包与锚点；选择阶段未交付入口不误报缺失 |
| 实际 MATLAB 主/分析 | `tests/test_solver_backend_end_to_end.py`、`tests/matlab/run_solver_backend_smoke.m` | 实际数值与工作簿、原 Python 验收器和 MATLAB reader 均通过；主结果字节保持 |
| 实际混合后端 | `tests/solver_backend_mixed_smoke.py` | 两方向跨问交接与同问混合阶段分别真实计算、验收和核对摘要 |
| 预处理衔接 | `tests/test_solver_backend_preprocessing.py` | 真实合成 XLSX 经旧1.0预处理回执 accepted，再以原文件身份进入1.1代码/回执门；覆盖共享原始数据禁读与预处理1.1拒绝，不代表执行过预处理数值代码 |
| 发布一致性 | `scripts/lint_skill.py`、`scripts/generate_indexes.py --check`、`git diff --check` | Authority/入口、Schema、资源引用、版本和五个生成文件同步 |

原生 MATLAB job 与 Python CI 分开运行，原可选绘图预览 job 的手动开关保留。CI 的 R2024b/Linux、维护机 R2025b/Windows 和一般 Python 单元测试代表不同证据；任何 skipped、未运行或外部环境失败不能写成通过。测试使用独立维护微型模型，不运行用户赛题。

发布前必须完成全套适用检查，审查实际新增和修改文件，更新生成索引/manifest，并在 PR 中记录最后验证状态。未来未知模型、工具箱和数据仍需其自己的完整运行验收，本次测试不构成对所有未来输入的无错误保证。
