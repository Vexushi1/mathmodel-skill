# D1：案例记忆准入与种子库实施计划

## 1. 基线、授权与完成定义

- 原总计划：[第 9、12、16—20 节](modeling_intelligence_evidence_evolution_plan.md)。C1 #252、C2 #255 已合并并完成各自主干复验；当前基线为 `main@4a5a57d1850d8953162b5a225d11806f5379c214` / Skill 10.15.1，提速基础设施 #256 的 final head 与 main 验证均成功。
- 用户授权先核查提速和 C 完成情况，再继续 D。本切片只实施 D1；D1 合并并复验 main 后，D2 使用下一份独立 PR。E 与发布 Release 均需后续安排。
- 目标 Skill 10.16.0；Case Memory Schema 1.0.0 首次引入；Project State 8.14.0、Governance 1.0.6 和 A/B/C 独立协议版本保留。案例 Schema 不加入普通 reading plan 的默认 Authority 版本集合。
- 完成必须有生成后的精确 head 的专项、正式完整回归、其他既有 CI、适用优化基线，以及合并后 main CI / 生成物复验。代码或测试文件存在只表示候选实现。本文在源文件冻结前编写，后续实际 SHA、PR 和运行结果由 PR 台账记录。

## 2. 影响面与具体设计

### 2.1 唯一准入 Authority

`knowledge/case_memory/schema.yaml` 同时定义字段形状和 admission 元数据。案例生命周期为 `draft / quarantined / reviewed / retired`；证据等级为 `observed_in_source / curator_inference / recommended_validation / synthetic_example`。字段覆盖来源身份/版本/哈希、许可和允许用途、隐私、结构特征、baseline 与模型决策、已做/未做校验、适用条件、可复用模式、不可移植参数、来源锚点、提取边界与审阅范围。不得为了满足字段要求虚构曾执行的校验或真实案例中的替代路线。

本轮正式种子只收独立编写的合成来源，以仓库 MIT 许可说明其来历。真实/第三方来源缺可核查公开使用授权时不能进入 reviewed 索引；“公开可见”、哈希正确或自填授权布尔值均不证明许可。敏感内容不得通过把状态改成 quarantined 就提交公共仓库。

### 2.2 数据与读取边界

- `sources.json` 独立保存来源正文及权利元数据；`cases.json` 保存从来源提取的卡片。来源哈希绑定规范 JSON，避免同一文件中自包含哈希循环，并兼容 Windows checkout 行尾。
- 严格拒绝重复 JSON 字段、未知字段/版本、非有限数字、越界对象及路径。默认上限：单文件 256 KiB，总输入 2 MiB，64 案例、64 来源、深度 32、节点 32768、单字符串 8192 字符；实际 Schema 可更严格，不能扩大代码硬上限。
- 固定文件集合，解析前后复读原始字节并复核路径，不沿 symlink 逃逸；不依赖 mtime 缓存或旧 PASS。返回有限且不回显隐私原文的诊断。校验不执行案例命令、不访问网络、不修改项目、批准、工作簿或终稿资格。
- 来源分组和规范决策核心用于去重。同题 fork 或相同核心不能组成虚假多数；未解决近重复保持隔离。完整近重复语义判断仍需人工，不能自证所有重复均已发现。

### 2.3 七个合成种子

覆盖预测、评价、优化、动力学、网络/调度、随机过程和跨问混合链。每个案例说明数据制度、结构约束、最小 baseline、模型适用条件和失效反例；文本标为合成/建议验证，已执行数值验证明确为空或未做。不宣称比赛排名、实测精度或独立审查。审阅记录的范围是维护者作者自查，不包装为独立 reviewer 或数值复现。

### 2.4 唯一索引写入链

- `scripts/case_memory.py` 提供 `validate / build-index / check-index`：默认只读，build 只输出 JSON。校验失败、输入过期、索引缺失或与当前 corpus 不一致时返回非零。
- `knowledge/case_memory/index.json` 仅包含当前合法 reviewed 案例，排序、源分组及哈希确定，撤回/退役立即移出。索引绑定当前 source/case/schema，不能以旧索引授予当前准入。
- 现有 `scripts/generate_indexes.py` 是 canonical index 唯一写入者，先构造索引 payload，再把其路径加入 Skill index 和 MANIFEST，保证首次生成时也登记新文件及准确哈希。
- `refresh-generated.yml` 的受管文件列表、提交列表和 main 只读检查接入新索引；CI 的生成物 artifact 和差异检查同步接入。三个独立 generator job 只安装 PyYAML/jsonschema，不引入 Linux 全量 Python 回归。
- bootstrap / manifest 登记可选 Authority 与显式 utility；默认路由不加载案例，不增用户项目门禁。lint 图检查包含新 knowledge 目录。

## 3. 改动顺序

1. 读当前 main / 治理 / 总计划，验证 #256 和 C1/C2；修正当前进度台账，保留历史 13/13、Linux 平台及本机验证记录原貌。
2. 实现独立 Schema、合成源/卡片、严格 admission CLI；同时添加 D03—D06、D10 正负例与 lifecycle / budget / 当前字节 / CLI 只读测试。
3. 接入唯一 generator、远端 bot 管理与元数据 CI；测试首次缺索引、源变化、撤回、旧 fake repository 兼容和 manifest 正确绑定。
4. 同步必要版本载体、README、脚本文档、CHANGELOG；注册精确 10.16.0 载体优化对照，保留所有历史测试和默认行为严格比较。
5. 静态独立复核修改边界，推源文件并创建 draft PR；等待 bot 生成最终 head，再从 GitHub 日志修复专项失败。生成前的旧 metadata 红叉不能当成最终 head 失败。
6. 专项成功后把 PR 标为 ready；冻结最终 head，运行 Windows Python 3.10 / 3.14 各四分片完整覆盖，保留 `Python 3.10` 与 `Windows Python 3.14` 正式 check；Windows MATLAB 与 Linux LaTeX、静态和生成物检查照常运行。
7. 检查适用 Optimization baseline，仅精确注册当前载体，拒绝默认 corpus 预加载、新项目资格或门禁漂移。检查全部分片证据与 current source / checkout SHA。
8. 全绿后 squash 合并，对合并树和已测树复核，等待 main 完整 CI 和 verify-main 成功；此后才进入 D2。

## 4. 行为验收矩阵

| 要求 | 验证证据 |
| --- | --- |
| D03 不把未做验证登记为事实 | 合成 observed、伪 performed validation、锚点不存在均拒绝；未做校验可如实记录 |
| D04 来源许可/公开授权 | 未知许可、非支持真实来源、自填公开授权不能 reviewed 准入 |
| D05 案例注入 | 指令仅作为数据保留/检查；不得调用 shell、网络、项目 writer 或改变批准 |
| D06 同源/核心去重 | fork 同源、相同核心、未解重复不进入虚假多数；索引分组与排序确定 |
| D10 隐私与路径 | Windows/UNC/POSIX 绝对路径、身份/账号/密钥拒绝；诊断不回显原文 |
| 读取与预算 | 重复键、未知字段、过深、超长、文件/对象预算、symlink、解析中输入变更失败关闭 |
| 可重建与撤回 | 生成器首次创建索引并登记哈希，来源/案例变化索引失效，retired/quarantined 从正式索引移除 |
| 兼容边界 | 无案例库旧 repository fixture 保持旧 generator；普通运行时不预加载、不新增项目门；当前既有 A/B/C 和提速全覆盖 |

## 5. 限制、成本和后续

本轮不提供检索排名、项目 `case_references` writer 或当前项目模型推荐；这些属于 D2。合成内容只提供结构示范，不能支持真实任务的数值结论。自动敏感模式与精确去重不是完备人工隐私/近重复审查，导入真实素材必须另行有可审核来源和人工准入。必要载体、图接线、生成物和真实消费者属于同一闭环，文件数可超过治理的优先小规模切片建议，但不跨入 D2 功能。

所有验收在 GitHub；本机只编辑、读取与 git 操作。开发阶段专项，ready/final-head 与 main 才做正式全量。若长作业仍在运行，约十分钟只读查询并保持安静，不反复重启已成功的旧 head。退回 D1 功能时可关闭显式 utility 并隔离案例，不撤销已批准用户项目或已验收求解。
