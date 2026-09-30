# Windows Python 回归提速实施计划

本计划是仓库维护计划，不是数值建模 Runtime Authority。用户已授权先完成本基础设施 PR，再继续功能阶段。编制日期：2026-09-30；基线 `main@6385f9a66dcd57033f31545cc4b22ebd1d20b77a`，Skill 10.15.0，C2 / PR #255 已合并并完成 main 复验。目标 Skill 10.15.1；项目 State 和各业务协议版本不变。

## 1. 修改简报

- 主题：保持正式证据覆盖的 Windows Python 回归提速。
- 等级：patch；专用分支 `fix/v10.15.1-python-ci-performance`，单独基础设施 PR。
- 直接目标：缩短每轮等待时间，减少同一内容的重复解析、重复收集和开发阶段多事件完整运行，留下可复算耗时证据。
- 权威来源：当前 `core/bootstrap.yaml`、`SKILL_CHANGE_GOVERNANCE.md`、`AGENTS.md`、CI/generated 工作流、标准 unittest discovery、现有解析与快照/read-set 实现。
- 保留边界：Windows Python 3.10/3.14 两套全部覆盖；Windows MATLAB 原生证据链；Linux LaTeX/正式编译链；原有批准、accepted workbook、stale、事务、budget、异常和人工审查要求。
- 本 PR 不开展 D1，不改变求解后端或真实用户赛题的数据规模、网格、时域、重复数、容差和精度，不写 C 代码，不手改生成索引/MANIFEST。
- 正式验收仅在 GitHub；不在本机运行 lint、unittest、generator、MATLAB、LaTeX。

## 2. 已观察证据与尚未证明的部分

| GitHub run | 内容 | Python 3.10 unittest 步骤 | Python 3.14 unittest 步骤 |
|---|---|---:|---:|
| 36661458941 | C2 final head 51f839f2，dispatch | 3034 s | 3012 s |
| 36665855734 | 同一 head 的 PR 事件 | 6013 s | 3273 s |
| 36665935999 | 相同 Git tree 的 main 合并后验证 | 6161 s | 3328 s |

安装依赖各约 20 秒；两版本单进程串行 discover。成功作业未上传 unittest.log，也无逐测试耗时。24 项重复收集来自两个模块直接导入含 12 项测试的 TestCase 类。已定位反复读取约 64 KB State Schema、约 49 KB output contract，以及 C2→C1 嵌套检查和 State snapshot 重复解析。多个 B2b/B2c 流程重复启动轻量合成求解/验收子进程及同步链。

这些调用链支持优化候选，不能作为 CPU 占比或倍数收益证明。3.10 的显著波动也不能直接归因于 Python 版本。真实收益必须在新最终 head 的 GitHub 计时和完整证据上报告。

## 3. 解析加速与内容复用

### 3.1 共用 helper

新增一个有限容量的进程内安全 YAML helper，普通等价解析优先使用 PyYAML 现成 `CSafeLoader`；没有该扩展时回退 `SafeLoader`。调用界面仍为 Python。提供显式的纯 Python / 禁用缓存诊断选项，方便远端对照和快速回滚。

缓存按当前原始内容及 Loader 语义标识区分，使用内容 SHA-256，校验真实字节以规避错误命中；不能仅用路径或 mtime。每次读取仍观察当前字节，原有 read-set/budget/currentness/提交前重检仍执行。缓存只保存解析结果；返回独立副本，防止调用者修改共享 mapping。设容量/字节限制，不持久化到项目或跨 CI head。

### 3.2 定向接入

优先接入 resolver 的常量合同 load_yaml、State/schema 校验、sync 的合同加载、Numeric Profile schema、claim/receipt 已观察字节的普通解析、不可变 ProjectStateSnapshot 的重复解析。保留各调用者原有缺失文件、空 YAML、mapping 要求和异常处理。

不机械替换严格 UniqueLoader、重复 key/alias/depth 限制、自定义 YAML 构造器；不缓存 gate PASS、批准、回执资格、工作簿数值、项目可变事实。检查新 helper 对真实算法来源和 authority fingerprint 的传递依赖，必要时把 helper 源码纳入既有观察清单。

独立审查确认：helper 已加入 A1/A2/backend/B1/B2/C1/C2 的相关源码观察。resolver 的 `authority_fingerprint` 按现有 `runtime_assurance_contract.yaml` 仅绑定 Authority 文件，不宣称实现源码闭包，因此不往该字段混入单个 Python helper；实现证据由最终 Git commit/tree、完整源码快照及 MANIFEST 保存，既有 legacy 比较不放宽。

### 3.3 正确性与度量

新测试覆盖纯 Python/C 解析语义、unsafe tags、空文档、malformed UTF-8/YAML、内容修改且 mtime 不变、嵌套对象修改隔离、缓存容量和并发。保留原有全部 parser/state/receipt/claim 负例。远端输出普通合同的纯 Python、C、C+cache 对照计时，准确标明这是解析微基准，不冒称完整回归或真实求解的加速倍数。

## 4. 全覆盖测试计时与分片

新增维护用 Python runner，沿用标准 `unittest discover -s tests -p test_*.py` 的模块命名、收集和 fixture 语义。每个 worker 先取得完整收集清单，再按测试文件分组选择自己的子集，禁止用关键词筛掉失败或慢测试。

- 初始固定为每版本 4 个 shard；只有两个正式 Python 版本，不扩张版本矩阵。
- 分组使用确定性 LPT 规则。初次按每文件收集测试数分配；已从 GitHub run `36681830056` 的四个 Python 3.14 shard 取得真实逐项数据，现提交 `tests/fixtures/windows_unittest_timings.json`，按实测文件耗时重新均衡。新增文件用种子的平均秒数/测试乘当前收集数量估计；没有匹配种子的合成集合保持测试数分组。
- 种子完整记录来源 head `ae97c6893430037ba9f3af0b53eb7f336e30ee24`、run、版本、四个 artifact ZIP 和原报告 SHA-256。该运行完整执行 2283 项，存在一条旧 CI 策略断言失败，故明确标记 `timing_only_failed_gate_not_acceptance`。215 个文件权重仅为 case time + exclusive fixture time，不叠加 suite block、不保存 PASS、不代替新 head 验收；Python 3.14 数据用于 3.10 只作调度估计。
- 每个 worker 记录种子原始字节哈希、身份、实际权重和分组；collector 从当前 checkout 重读种子，再核所有 worker 的哈希、权重和确定性计划。任何版本仍独立重新执行完整全集，禁止复用旧运行的 coverage artifact。
- 逐 case 输出含 setUp/tearDown/cleanup 的耗时；额外记录文件/fixture 开销、collection 时间、实际 loader、Python/依赖/runner 信息、source/checkout commit。
- 所有 shard 无论成功或失败都上传 log 和 JSON 证据。
- 每版本汇总验证 shard 数、commit、版本、分组、完整 discovery ID 清单、重复/遗漏、结果状态；任何缺失、错误、失败或 shard 未完成都使正式 gate 失败。
- 保留现有显示名 `Python ${{ matrix.python-version }}`（3.10）和 `Windows Python 3.14` 为汇总 gate。新增 shard 名称是内部执行单元，不替代或伪造这两个正式 gate。
- 专门测试覆盖 runner 的确定性分组、全集等于不重叠并集、计时/跳过/失败/fixture 异常和证据缺失拒绝。分片后的两版本必须全绿，不能只用 runner 单元测试证明全回归兼容。

## 5. 消除重复准备与多事件浪费

### 5.1 确定的重复收集

两个 v900 测试改为通过 fixture 模块引用 `UserExecutionContractTests`，避免向 discover 模块暴露该 TestCase 类。原文件 12 项全部保留；预期减少 24 次冗余执行。runner 同时检测并报告 discovery ID 重复，防止未来再次引入。

仅复用确实只读、无 fixture 变异的维护度量准备结果；每个集成测试仍保留独立项目副本和失败注入。首轮不共享带有 accepted State/回执的可变项目 seed，不删完整链测试，不削弱任何断言。

### 5.2 开发与冻结两阶段

保留 PR 和 main 正式验证。开发分支 push 优先由 refresh-generated 生成受管文件，避免源提交立刻启动整套回归；draft PR / 显式 targeted dispatch 运行专项 Python 与基础静态/生成检查。冻结为 ready PR（包含 ready_for_review 事件）或显式 full dispatch 后运行两版本分片与全部正式 specialist gates；main push 总是完整验证。

refresh-generated 即使没有生成差异也要有明确后续验证路径。对 draft/no-PR 默认调度专项；已有 ready PR 在 bot 形成新最终 head 后须调度完整验证，原 source head 的 generated check 必须先通过才能启动完整 Python。禁止因重排触发而留下无人验证的最终 head。

避免在已经完成最终 head 分支 full run 后才新建 ready PR；本 PR 提前建立 draft，最后对 bot 生成的最终 head 冻结。仍保留 PR 事件和其 required check 名称；无法读取 branch protection 时不删除潜在 required contexts，不伪造 status，不以旧 head 的 artifact 代替当前验收。

所有正式 job 显式 checkout 当前 PR head（main/dispatch 使用当前提交）；报告分别保留 source SHA、实际 checkout SHA 和 GitHub event SHA。默认 PR merge ref 不再混入源码身份。汇总 gate 在 prerequisite/shard 失败、取消或跳过时明确失败。CI concurrency 按事件、ref、targeted/full 区分，专项不能取消完整验收。无 generated 差异且 ready PR 的去重需核对同一 head 的两个正式 Python gates，draft 成功但 full gates skipped 不构成正式证据。

## 6. 影响面与具体交付

预计修改：`.github/workflows/ci.yml`、`refresh-generated.yml`、必要 optimization paths；新 YAML/CI runner 与测试；第 3 节列出的定向普通解析入口；两项重复 fixture imports；`tests/test_actions_runtime_modernization.py`；`SKILL_CHANGE_GOVERNANCE.md` 1.0.6、`AGENTS.md`、README/scripts README；Skill 10.15.1 现有版本载体、Changelog及对应版本测试。

生成物只由 GitHub bot 更新。保留历史已经真实发生的旧矩阵、旧 CI 数量和验收记录。新版治理描述完整 coverage 的分片等价要求，移除“只能单进程执行指定命令”的现行表述，保留旧标准 discover 作为 coverage 参考。

## 7. 串行实施、验收和回滚

1. 当前计划先落盘，完成独立分支和具体文件责任分配。
2. 实现 parser/cache 与负例；实现 runner/重复收集修复；同步 CI/治理/版本。
3. 静态独立审查，检查严格 parser、快照read-set、新 helper source closure和 required contexts。
4. 仅提交源码并 push；GitHub bot 更新 generated metadata；draft PR 的远端专项先发现接线问题，失败按日志窄修。
5. 将 PR 冻结，对生成后的精确 head 完成两版本 4-shard 全集、汇总 coverage、static/generated、Windows MATLAB、Linux LaTeX和适用优化基线。
6. 报告每版本 wall time、所有 shard 总 runner time、最慢 case/file与解析微基准；与第 2 节既有证据比较并说明 runner 波动。正确性是硬门，速度不是降低覆盖的理由。
7. 全绿才 squash 合并；main 同样复核完整 shard coverage与生成物；之后才继续功能计划。

可分开回滚 parser/cache（纯 Python/禁用缓存诊断；必要时 revert 接入）或 shard/trigger（恢复单进程和原触发）。任何回滚都保留正式两版本测试和当前证据要求，不自动迁移项目、不改业务协议版本。

## 8. 当前执行状态

2026-09-30：计划已形成，用户已授权实施。PR #256 已建立，源码实现、版本同步及 parser/工作流独立静态审查已完成，draft GitHub 专项 242 项通过。首轮正式运行发现旧版 Changelog 标题分类断言，按既有格式修复；第二轮完整测量发现 baseline 不允许 draft 排除条件的旧断言，按本计划精确更新，并把该模块加入专项。现在根据四个远端 shard 的实测耗时重新分组。修改后的最终 head 完整验收、合并及 main 复验仍未完成，后续真实证据记录于该独立 PR 描述，不能提前标记完成。
