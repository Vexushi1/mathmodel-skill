---
governance_version: 1.0.6
applies_to_skill: ">=6.3.0,<11.0.0"
status: active
---

# HSK Skill 修改治理规范

本文件是所有仓库级 Skill 修改的强制前置阅读文档。任何聊天、Agent、脚本或人工维护者，只要准备修改本仓库的活动文件，都必须先读取当前 `main` 分支中的 `core/bootstrap.yaml` 与本文件，再制定修改方案。

本规范解决的核心问题是：不同聊天基于不同历史上下文修改同一仓库，造成规则重复、版本漂移、文件职责冲突、未合并分支相互覆盖和生成文件失效。

---

## 1. 适用范围

以下行为均属于“Skill 修改”，必须遵守本规范：

- 修改全局规则、工作流、题型分类、产物契约或目录结构；
- 修改 Python、MATLAB、DOCX、LaTeX 模板及其职责边界；
- 新增或删除模块、Pack、Schema、脚本、模板、测试和 CI；
- 调整版本号、命名规范、交付流程、项目状态或同步机制；
- 修复可能改变实际执行行为的文档表述；
- 合并、拆分、重命名或迁移活动文件。

单纯修正不影响含义的错别字也应使用分支和 PR，但可采用精简审查流程。

---

## 2. 每个新聊天的强制启动顺序

任何新聊天不得依据记忆、旧聊天摘要或本地猜测直接修改仓库。必须按以下顺序执行：

1. 从 `main` 读取 `core/bootstrap.yaml`；
2. 从 `main` 读取 `SKILL_CHANGE_GOVERNANCE.md`；
3. 确认仓库当前 Skill 版本、`main` 最新提交和默认分支；
4. 检查是否存在尚未合并且与本次范围重叠的 PR 或分支；
5. 读取本次修改涉及的权威事实源，而不是全仓库无差别加载；
6. 在写文件前形成“修改简报”；
7. 创建独立分支，禁止直接写入 `main`；
8. 修改源码、提交并推送，由 GitHub 生成受管文件；在最终 PR head 的 GitHub Actions 正式验收通过后合并，再复核 `main` 的 GitHub Actions。

若无法确认当前 `main`、未合并 PR 或权威事实源，必须停止写入，不得以旧聊天内容代替仓库事实。

---

## 3. 修改简报：写入前必须先形成

任何非错别字级修改，在首次写文件前必须明确以下内容：

```text
修改主题：
当前版本：
目标版本：
变更等级：docs / patch / minor / major
直接目标：
明确不做：
权威事实源：
预计修改文件：
禁止触碰文件：
兼容性要求：
迁移要求：
验收测试：
回滚方式：
```

修改简报应写入 PR 描述。不得边改边扩大范围，也不得把临时想到的无关优化塞入同一 PR。

---

## 4. 单一事实源

同一规则只能有一个权威定义位置。其他文件只能引用或给出简短摘要，不得复制完整规则。

| 规则类型 | 权威事实源 |
|---|---|
| 最小启动入口与权威源指针 | `core/bootstrap.yaml` |
| 全局硬规则 | `core/hsk_core_policy.md` |
| 多意图路由与加载顺序 | `core/workflow_router.yaml` |
| 任务目标、问题结构、验证能力 | `core/task_taxonomy.yaml` |
| 模块输入输出与产物闭环 | `core/module_manifest.yaml` |
| 目录、正式交付与框架模式 | `core/output_contract.yaml` |
| 工作簿结构、字段与 MATLAB 交接 | `core/workbook_schema.yaml` |
| 项目状态、哈希与 stale | `core/project_state.schema.yaml` |
| 项目状态转换、stale 传播与依赖失效 | `core/state_transition_contract.yaml` |
| 竞赛差异 | `config/competition_profiles.yaml` 与 `packs/competition/` |
| 命题证明细则 | `packs/artifact/proposition_proof.md` |
| 活动版本变更说明 | 当前版本 Changelog |

若发现同一规则在多个活动文件中重复定义，不应继续同步复制，而应保留一个权威定义并将其他位置改为引用。

---

## 5. 变更等级与版本规则

### 5.1 docs

仅调整表述、索引或说明，不改变执行行为、Schema、CLI、目录和模板输出。

- 通常不升级 Skill 版本；
- 仍需分支、PR 和 GitHub Actions 的基础 lint；
- 若“文档修正”实际上改变行为口径，则不得标为 docs。

### 5.2 patch

修复错误，保持现有接口和项目结构兼容。

示例：解析器错误、校验遗漏、模板字段判断错误、测试缺口。

版本：`x.y.z -> x.y.(z+1)`。

### 5.3 minor

新增向后兼容的能力、模块、可选字段或工作流。

示例：新增同步检查、增加可选 capability、增加不破坏旧调用的 CLI 参数。

版本：`x.y.z -> x.(y+1).0`。

### 5.4 major

破坏兼容性的目录、Schema、CLI、命名或职责调整。

必须提供迁移说明、兼容窗口和旧项目处理方案。

版本：`x.y.z -> (x+1).0.0`。

禁止为了显示“升级很大”随意提高版本等级，也禁止把破坏性修改伪装成 patch。

---

## 6. 分支与 PR 纪律

### 6.1 一次聊天一个分支

同一聊天只维护一个明确分支。不同聊天不得共同向同一未合并分支连续写入，除非用户明确指定接管该分支并先读取完整 PR 状态。

推荐命名：

```text
docs/<topic>
fix/v<version>-<topic>
upgrade/v<version>-<topic>
refactor/<topic>
```

### 6.2 一个 PR 一个主题

一个 PR 只能解决一个核心问题。以下内容不得混入同一 PR：

- 与目标无关的目录清理；
- 顺手重写其他模块；
- 无验收标准的“整体优化”；
- 大量格式化导致的噪声 diff；
- 未经说明的版本升级。

### 6.3 禁止直接写 main

除仓库自动生成工作流外，人工和 Agent 修改均应经分支与 PR。紧急热修也应建立最小 PR，不得绕过审查链。

### 6.4 重叠 PR 处理

发现其他未合并 PR 修改相同权威文件时：

1. 停止当前写入；
2. 判断两个 PR 是否可串行；
3. 优先合并基础 PR；
4. 当前分支基于最新 `main` 重建或变基；
5. 推送新的远端 head，等待远端生成工作流形成最终 head，并重新完成该最终 head 的 GitHub Actions 正式验收。

不得让两个聊天分别修改同一契约后依次强行合并。

---

## 7. 影响面检查

修改某类规则时，至少检查下列关联文件。此表是“检查范围”，不是要求每次全部修改。

| 变更对象 | 必查关联 |
|---|---|
| Skill 版本 | `core/bootstrap.yaml`、`.codex-plugin/plugin.json`、`core/output_contract.yaml`、lint、Changelog、入口文档 |
| 路由 | `core/workflow_router.yaml`、`scripts/resolve_workflow.py`、`core/module_manifest.yaml`、路由测试 |
| 题型分类 | `core/task_taxonomy.yaml`、`packs/task/classifier.md`、状态 Schema、解析器、测试 |
| 产物或目录 | `core/output_contract.yaml`、Manifest、状态 Schema、同步器、模板、检查器、测试 |
| 工作簿 | `core/workbook_schema.yaml`、`result_io.py`、artifact checker、MATLAB handoff、测试 |
| MATLAB 读取规则 | workbook Schema、MATLAB 模板、handoff、绘图模块、测试 |
| 项目同步 | `scripts/sync_project.py`、状态 Schema、Manifest、输出契约、同步测试 |
| 命题证明 | 命题 Pack、模型设计模块、DOCX/LaTeX 模板、终审规则、测试 |
| LaTeX | 写作模块、编译配置、模板、CI 编译任务、引用检查 |
| 生成索引 | `scripts/generate_indexes.py`、生成工作流、MANIFEST；禁止手工伪造 |

修改完成后，PR 必须说明“检查了哪些关联，哪些无需修改及原因”。

---

## 8. 生成文件规则

以下文件属于生成产物，原则上不得手工编辑：

- `HSK_SKILL_FILE_INDEX_V622.md`；
- `HSK_TEMPLATE_INDEX_V622.md`；
- `SKILL_FILE_INDEX.md`；
- `TEMPLATE_INDEX.md`；
- `MANIFEST.sha256`；
- 其他由 `scripts/generate_indexes.py` 明确生成的文件。

仓库维护的正式生成流程：

```text
修改源文件并仅提交源文件
→ 推送分支
→ refresh-generated 在 GitHub 运行 generate_indexes.py
→ bot 有差异时提交生成结果，确定最终 head
→ draft PR / 无 PR 分支调度专项验证，ready PR 调度正式完整验证
→ 冻结 PR 后对最终 head 完成 HSK Skill CI 与适用的 Optimization baseline
→ 核对生成差异、实际 checkout commit 与远端证据
```

生成无差异也必须进入对应验证路径。生成文件检查通过后才启动完整 Python 分片；源码提交和 bot 生成提交不能同时无条件启动整套回归。若已有同一最终 head 的等价正式运行，须明确核对其范围与状态后才可避免重复调度。仓库维护仅以 GitHub 证据验收，本地不要求运行 generator；用户要求 GitHub-only 时不运行本地诊断。禁止手工修改哈希以“让 CI 通过”。若自动生成工作流提交了生成文件，应确认该提交只包含预期生成结果。

---

## 9. 测试与验收

### 9.1 分层验证与正式平台

开发分支 push 与 draft PR 优先在 GitHub Actions 安排受影响的专项测试及基础静态/生成检查。PR 冻结为 ready 时（包括 `ready_for_review` 事件）、显式 full dispatch 和 main push 执行正式完整验证；专项成功不能代替冻结验收。源码或生成文件提交发生变化后，必须对新的最终 head 重新验收。

正式 Python full regression 仅有 Windows + Python 3.10、Windows + Python 3.14 两套。覆盖参考仍为 `python -m unittest discover -s tests -p "test_*.py"`；CI 每版本按测试文件分为 4 个独立进程分片，保留标准 discovery 的全集与 fixture 语义。每版本汇总必须核对所有分片的实际 checkout commit、Python 版本、分组、discovery ID 全集和结果，拒绝重复、遗漏、失败、缺失或未完成证据。保留现有 `Python 3.10` 与 `Windows Python 3.14` 正式 check 名称作为汇总门；不能把缺失分片或上游失败变成通过。所有正式 job 显式 checkout 同一 source head，分别记录 PR source head、实际 checkout commit 和 GitHub event SHA，不能以旧 head 的日志或产物代替当前验收。

已提交的耗时种子仅用于确定性文件分片调度，保存来源 commit、run、Python 版本和原始报告哈希。完整执行但门禁失败的历史报告也可提供度量，不能保存或复用 PASS。Python 3.14 度量用于 3.10 时仅作运行时长估计；各版本仍按当前 head 独立完成全部覆盖与正式验收。新增文件用种子的平均秒数/测试作调度估计；汇总从当前 checkout 重读种子并核对内容哈希、实际权重与分组。

最终 head 还须通过 Static contract lint、Generated file contract、MATLAB native contract、LaTeX templates、Production LaTeX attestation 及适用的 Optimization baseline 等远端检查。所有分片无论成功或失败均保存日志及逐项/文件/收集耗时；报告每版本 wall time 与所有分片总 runner time，实测后才说明收益，不用解析微基准替代完整回归证据。

Linux runner 可以用于 LaTeX / TeX Live、静态工具、生成文件、Git 来源快照等工具作业；作业内部调用 Python helper 不构成 Linux Python 正式兼容承诺。不得在没有明确兼容目标与验收依据时无限扩展完整 Python 矩阵，也不得在其他 workflow 隐藏执行 Linux 整仓完整 unittest。

仓库维护不要求 Codex、Agent 或开发者在本地运行 lint、unittest、`generate_indexes.py`、MATLAB 或 LaTeX；正式验收仅在 GitHub。用户要求 GitHub-only 时不运行本地诊断。正式证据为最终 PR head 的 GitHub Actions job、日志与产物、该 head 与实际 checkout / 合并提交的对应关系，以及合并后 `main` 的 GitHub Actions。若 required check 名称受变更影响，合并前须核对 GitHub Settings；无法核对时保留现有正式 check 名称与验证语义，不能擅自删除或改名。

这项远端验收规则仅适用于 Skill 仓库维护。真实用户赛题的 Python / MATLAB 数值代码仍由用户在实际环境按 `full_fidelity` 执行，并按原有工作簿、回执与验收契约交付。

正式 MATLAB 原生数值 CI 在 Windows Server 2022 + MATLAB R2024b 执行，必须实测主求解、独立结果深化分析、accepted XLSX 交接、版本化 RUN_RECEIPT，以及 A2/B1 对真实合成执行证据的检查。可选 MATLAB 绘图预览是独立的渲染检查，不能代替这条原生数值验收链。

### 9.2 解析复用的安全边界

普通等价 YAML 解析可以使用 PyYAML 已有的 `CSafeLoader`，不可用时回退 `SafeLoader`；无需编写 C 代码。有限容量的进程内解析缓存按当前内容哈希与 Loader 语义区分，核对真实字节并返回独立副本。每次读取仍观察当前字节；read-set、budget、currentness 和提交前重检继续执行。严格重复 key/alias/depth 限制与自定义构造器不能被普通 helper 替换。不得缓存 gate PASS、批准、回执资格、工作簿数值或项目可变事实。须保留纯 Python / 禁用缓存的远端诊断和回滚路径。

### 9.3 按影响面追加

按影响面在 GitHub Actions 中安排并核对：

- 路由或分类：代表性 `resolve_workflow.py` 检查；
- 同步器或状态：`tests.test_sync_project`、`tests.test_schemas`；
- 工作簿：`tests.test_result_io` 与 artifact checker 测试；
- MATLAB：模板静态测试与真实表头唯一匹配，涉及原生执行时核对 native job；
- LaTeX：对应竞赛模板编译与未定义引用检查；
- 目录或产物契约：contract closure 和 structure 测试；
- 版本升级：版本一致性和远端生成索引检查。

测试失败时不得合并。不得通过删除测试、降低断言或把错误加入例外列表来掩盖真实冲突。

---

## 10. 兼容与迁移

任何会影响旧项目的修改，PR 必须回答：

1. 旧项目是否仍可运行；
2. 旧字段、旧 CLI、旧目录保留多久；
3. 是否提供自动迁移或兼容映射；
4. 何时删除兼容层；
5. 如何回滚。

兼容代码必须有明确退出条件，不能永久积累无主的 legacy 分支。

`legacy/` 只保存历史材料，不得成为活动代码的默认依赖。

---

## 11. 明确禁止的修改方式

- 不读取当前 `main`，直接根据旧聊天记忆修改；
- 在多个文件重复粘贴同一硬规则；
- 为一次局部需求新增大批模板、索引或配置层；
- 未检查现有 PR 就创建重叠修改；
- 直接修改 `main`；
- 将无关重构混入功能 PR；
- 全仓库盲目替换版本号；
- 手工伪造 MANIFEST 或测试通过结果；
- 为通过测试而删除有效约束；
- 未提供迁移说明就改变目录、Schema、CLI 或职责边界；
- 修改 `legacy/` 后让活动文件依赖它；
- 在 PR 未合并前宣称修改已经进入 `main`。

---

## 12. PR 描述的最低内容

每个 PR 至少包含：

```text
变更背景
直接目标
明确不做
变更等级与目标版本
权威事实源
关键改动
兼容与迁移
测试结果
生成文件状态
风险与回滚
```

若 PR 修改超过 20 个活动文件，必须额外解释为何不能拆分，以及每组文件的职责。

---

## 13. 完成报告

修改完成后，聊天回复不得只说“已修改”。必须给出：

- 分支和 PR；
- 是否已合并；
- 合并提交 SHA；
- 核心修改文件；
- 权威规则发生了什么变化；
- 兼容性；
- 最终 PR head SHA、GitHub Actions workflow run 与各正式门状态，以及合并后 `main` 的 GitHub Actions 状态；
- 尚未完成或存在不确定性的事项。

若 CI 仍在运行，应明确写“尚未完成验证”，不得提前宣称全部通过。

---

## 14. 快速判定：是否应该修改 Skill

只有同时满足以下条件，才应修改仓库：

1. 需求具有跨项目复用价值，而不是单个赛题的临时偏好；
2. 当前规则确实无法覆盖，或存在可复现的缺陷；
3. 修改位置存在明确权威事实源；
4. 能定义验收测试；
5. 不会用更轻量的项目级配置解决；
6. 修改后的维护成本低于它解决的问题。

若仅服务当前赛题，应优先写入该项目的 `模型论文框架.md`、项目状态或局部脚本，不应污染全局 Skill。

---

## 15. 新聊天可直接使用的开场指令

```text
准备修改 Vexushi1/mathmodel-skill。先从 main 读取 core/bootstrap.yaml 和 SKILL_CHANGE_GOVERNANCE.md，确认当前版本、最新提交、未合并 PR 与权威事实源。先给出修改简报，不要直接写文件。确认范围后创建独立分支和单主题 PR；提交源文件并推送，由 GitHub refresh-generated 提交受管文件。开发阶段优先受影响专项测试，冻结 PR 前由 GitHub Actions 在最终 head 上完成 Windows Python 3.10/3.14 正式完整回归，以及 lint、生成索引和受影响专项检查；合并后复核 main。仓库维护不要求本地测试或生成器。禁止依据旧聊天记忆、直接写 main、重复定义规则或手工伪造生成文件。
```

---

## 16. 本规范自身的修改

修改本规范属于治理变更，至少按 patch 或 minor 级别审查。必须说明：

- 为什么现有规则不足；
- 新规则解决什么可复现问题；
- 是否增加不必要的流程负担；
- 是否需要同步 `AGENTS.md`、`core/bootstrap.yaml`、PR 模板和仓库索引。

本规范只保留当前有效版本，历史由 Git 保存。
