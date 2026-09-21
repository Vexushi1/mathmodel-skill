# v9.7.1 阶段、源码与输入衔接检查

本次检查以 v9.7.0 的主干 `f87b463c4292295be5ad3607dc9ea3e0732d982f` 为基线，先复现问题、形成修改计划，再在独立分支精确修复。此页记录维护范围，不另立执行、状态或写作 Authority。

## 修改简报

目标版本为 v9.7.1，变更等级 patch。主题是使已选阶段、实际源码、声明输入、工作簿身份及其活动说明遵循现有契约。保持旧 Python 文件名、FULL/P5a/1.0 与省略后端参数的兼容投影；项目级预处理继续使用 Python。模型批准、数值通过标准、工作簿业务结构、正式图表与论文骨架均不改变。

Authority 仍为 `core/bootstrap.yaml` 指向的 user_execution、runtime_assurance、output、global_preprocessing、project_state、state_transition 和相应模块。修复作用在共同解析器和实际消费者，没有复制一套 MATLAB 状态机。版本与生成索引随源码一起形成完整交付，生成产物单独提交。

## 已复现的问题与修复位置

| 编号 | v9.7.0 的可复现行为 | 修复职责 |
|---|---|---|
| A01 | 请求分析但主结果未验收时，模块退回主求解却沿用分析后端 | `resolve_runtime.py` 以实际恢复阶段应用后端、模板及兼容投影 |
| A02 | 活动入口、局部预处理、附录和方法说明无条件要求 `.py` | 引用现有阶段命名 Authority，消除固定语言假设 |
| A03 | 输出说明推荐被当前 Schema 拒绝的 `artifact_hashes.model` | 指向当前主实现 `primary_code`，不恢复退役 writer |
| A04 | Authority 列出的 1.1 analysis 字段未包含实际必需的主簿摘要 | 补充版本与阶段共同限定的 `primary_workbook_sha256` 声明 |
| A05 | Python 多层相对导入遗漏项目 helper，输出变化后旧绑定仍有效 | 共享源码闭包按真实包上下文识别依赖 |
| A06 | MATLAB `value = helper` 未计入源码闭包 | 识别调用/句柄、平级与嵌套函数作用域、命令式参数及 persistent/global 变量；未验证解析不得声称闭包完成 |
| A07 | `RUN_CONFIG |= ...` 改变实际配置但静态提取仍返回旧值 | 1.1 共享配置提取拒绝直接增量修改与直接删除 |
| A08 | Q2 输入含 Q1 工作簿时，无变更的 sync 也撤销 Q2 accepted | 根据当前 1.1 primary 声明输入观察身份，保留原数据模式及旧项目路径 |
| A09 | 复现 ZIP 缺少 RUN_CONFIG 输入仍被判完整 | 将激活阶段实际声明输入纳入必需文件集合 |
| A10 | 合法大写数据/helper SHA 被 MATLAB 模板拒绝 | 两数值模板只对 SHA 比较忽略大小写 |
| A11 | Windows 8.3 绝对工作簿路径触发未捕获相对路径异常 | 验收入口正规化路径后检查项目边界 |
| A12 | sync 未传项目根，跳过真实 Algorithm Trace 函数检查 | 接通既有 project-aware 框架校验器 |

## 合并前补充计划：动态引用与下游闭环

2026-09-21 独立审查固定于候选 `401ed4081669e87290d471ef28dca00916b011fe`，确认 `load = importlib.import_module; load("helper")` 可漏过 1.1 源码检查：仅改变未声明 helper 即可使维护微例的真实结果从 3 变成 6，而旧工作簿仍通过交付绑定和回执检查。此处不推断缺陷首次引入版本。用户已授权继续修复原 PR #229，沿用 `fix/v9.7.1-backend-contract-closure`，不另开重叠修改分支。

补充范围仍为 patch / v9.7.1；不增加动态加载支持，不建立平行 Authority，不调整模型审批、数值门、Schema、正式交付结构、MATLAB 已声明边界或旧协议兼容窗口。预计修改共享源码检查器及必要的现有下游消费者、专项测试、本计划和 Changelog；生成文件只由 `generate_indexes.py` 更新并单独提交。

| 编号 | 修复/检查任务 | 验收证据 |
|---|---|---|
| A13 | 在共享 Python 源码闭包处保守拒绝未验证的动态执行能力引用，而非只检查直接 Call；覆盖赋值、链式别名、参数/容器传递、已声明 helper 内的同类引用及相关加载/跨后端能力 | 原始负例修复前失败、修复后通过；普通静态导入和正常数值 callable 的正例仍通过；字符串/注释不得冒充执行引用 |
| A14 | 核验新规则贯穿代码交付、delivered/validated binding、旧工作簿回执、sync/stale、runtime 和复现包；发现真实断点时仅接通现有消费者 | 对旧版本曾错误接受的隔离维护状态执行负例；不伪装成新版本成功验收。无效来源不能继续成为 accepted 的消费依据，sync 不刷新 delivered/validated 身份；合法静态 helper 完整包通过，缺 helper 包失败 |
| A15 | 修复后重跑全部单测、lint、索引/哈希/入口版本、路由及读取范围/错误路径、历史场景和当前 head CI；通过后合并，再核对 main 树和主干 CI | 记录确切 SHA、测试数、跳过原因和 CI 结论；读取计划不等于实际阅读；不以旧提交绿色状态代替新提交验收 |

执行顺序为：补充计划 → 保留失败复现 → 共享修复及负/正回归 → 下游验证 → 生成元数据 → 全量与当前提交 CI → 有条件合并 → 主干复核。若发现同主题的新断点，先在此页记录再修改；不将无关优化混入。新 1.1 项目若曾使用未验证动态加载，应改为可验证静态依赖并重新交付、执行、验收，不批量改写历史证据或通过 sync 自动恢复 accepted。回滚使用正常 revert，保留原失败现场，不移动历史标签。

本节先于实现提交，保留计划与验收依据；最终执行状态、精确提交验收和合并状态以 PR 后续完成评论及该提交 CI 为准，不把旧提交结果当作新提交通过。

### 补充执行记录

A13/A14 已由共享 `scripts/python_source_checks.py` 接入 `stage_code.py`，保持原有下游消费者和状态转换 Authority；新增 `tests/test_python_execution_reference_closure.py`。检查从危险能力的引用源头阻断赋值、链式、回调、默认参数、容器和 helper 中的别名，而非为每个下游复制规则。保留原始历史工作簿并验证新检查器拒绝其不完整来源。

二次体检在 `1a68d169057363c9cac0e7dcc593223d867137e1` 进一步确认模块注册表和环境命名空间反射可绕过第一轮修复，已先记录于 PR 再补修：`sys.modules`、`globals()`、`locals()` 以及无参 `vars()` 或其逃逸引用不再获得来源闭包证明；普通 `vars(object)` 数据属性读取保留。新增反射负例与公共交付、绑定、回执检查，本轮专项 17 个测试方法，另保留并整合新增反射复验模块的 4 个方法。两个隔离真实运行复现均显示修复前 helper 变化使结果从 3 变 6、旧回执仍通过，修复后的共享 gate 则拒绝原历史工作簿。

A15 使用当前生成源码快照核对 Git tree、全部单测、路由/读取选择器、哈希与版本，并核对同一 head 的 CI。由生成工作流触发的 `workflow_dispatch` 是现有全量检查入口；未实际执行的重复 PR 事件不能计作测试通过。合并必须等最终候选全部所需检查完成，合并后的主干状态再单独核验。

本检查器是对支持范围内来源证明的保守静态门，不是执行不可信 Python 的安全沙箱；未提供任意反射、混淆代码或外部安装包内部行为的安全性证明。未验证动态依赖应改为显式静态依赖并重新交付/执行/验收，而不是扩张通过声明。


### A13 补充边界复验

在 `1a68d169057363c9cac0e7dcc593223d867137e1` 上进一步复现：受限命名空间的 `__getattribute__` 及 from-import 反射属性可绕过引用检查；MATLAB 根模块值别名可隐藏 engine 调用；纯 `subprocess.PIPE/STDOUT/DEVNULL` 常量被误判为进程启动。修复仍在同一 `python_source_checks` 中完成，不覆盖已有阶段或状态实现。新增 `tests/test_python_reference_followup.py` 验证反射来源、根模块逃逸、无执行能力常量及真正执行产生的旧工作簿（答案 3→6、入口哈希不变）的拒绝与身份不刷新。常量例外仅限这三个值；直接调用原有进程命名空间仍被拒绝。原始候选上四项新增测试有 13 个失败子例，保留负例后再修复。

## 兼容与使用边界

- 旧 Python 项目不自动迁移；原始 FULL/P5a/1.0 配置继续按旧接口读取。新 1.1 阶段必须声明真实项目 helper 和输入，不能用遗漏依赖的旧绑定继续确认新源码结果。
- primary 的实际输入集合可包含当前合法的上游已验收工作簿；项目级预处理继续使用已验收 XLSX 的普通文件 SHA。analysis 仍遵循现有主数据身份继承规则，单独核对其声明输入不会覆盖主数据身份。
- 同步仅观察当前文件并报告失效，不能刷新交付或已验收身份。修改配置、helper 或输入后，按原流程重新交付、执行、验收；不要仅靠 sync 恢复 accepted。
- 当前 MATLAB 模板对普通同目录/根目录 helper 验证解析位置。尚不能证明的 package/private 项目解析应明确阻断正式闭包；不能因为 Code Analyzer 无错误就当作已证明实际依赖来源。
- 复现包收集当前合法输入，official 提交仍使用原比赛 allowlist；本次没有让 official 包自动携带全部数据和源码。
- 发布载体使用 9.7.1；独立 Schema 版本、历史引入版本及兼容来源版本保持各自语义，不全仓替换历史数字。

## 验证入口

```text
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/generate_indexes.py --check
python -m unittest tests.test_solver_backend_runtime_boundaries
python -m unittest tests.test_solver_backend_source_closure
python -m unittest tests.test_solver_backend_contract_alignment
python -m unittest tests.test_solver_backend_downstream_identity
python -m unittest tests.test_python_execution_reference_closure
python -m unittest tests.test_python_reference_followup
python tests/solver_backend_hash_smoke.py --project FRESH_OUTPUT --matlab-command MATLAB_EXE
```

最后一项仅对新建维护微例运行：实际 Code Analyzer 后分别启动全新的 MATLAB batch，验证大写数据/helper/主结果摘要、两阶段数值及公共工作簿验收，并核对分析没有修改主簿。常规 native CI 仍验证小写摘要、主/分析、两方向跨问、同问混合及预处理交接。

基线全量测试为 1289 项，3 项条件跳过。基线 lint/生成索引、84 组路由计划、20 个读取选择器均通过，但不覆盖本次复现的全部接口场景。修复提交的实际测试及 CI 结果以该 PR 为准，不能用这些基线结果替代新提交验收。

## 回滚

整体撤销本主题的源码和生成元数据提交；保留原工作簿、失败现场及已交付来源，不修改 v9.7.0 标签。若在合并发布后撤销，应使用新的 revert 提交和后续版本，不移动已有发布标签，也不把 1.1 回执改成旧版来绕过检查。
