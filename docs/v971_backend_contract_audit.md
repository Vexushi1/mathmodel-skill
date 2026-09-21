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
python tests/solver_backend_hash_smoke.py --project FRESH_OUTPUT --matlab-command MATLAB_EXE
```

最后一项仅对新建维护微例运行：实际 Code Analyzer 后分别启动全新的 MATLAB batch，验证大写数据/helper/主结果摘要、两阶段数值及公共工作簿验收，并核对分析没有修改主簿。常规 native CI 仍验证小写摘要、主/分析、两方向跨问、同问混合及预处理交接。

基线全量测试为 1289 项，3 项条件跳过。基线 lint/生成索引、84 组路由计划、20 个读取选择器均通过，但不覆盖本次复现的全部接口场景。修复提交的实际测试及 CI 结果以该 PR 为准，不能用这些基线结果替代新提交验收。

## 回滚

整体撤销本主题的源码和生成元数据提交；保留原工作簿、失败现场及已交付来源，不修改 v9.7.0 标签。若在合并发布后撤销，应使用新的 revert 提交和后续版本，不移动已有发布标签，也不把 1.1 回执改成旧版来绕过检查。
