# E2：发布评审与交接记录

Skill **10.17.1**；本文件是维护验收记录，不建立新的 Runtime、数学、数值、审查或案例 Authority。

> **2026-10-01 发布授权与政策更新：** 用户已明确授权发布新版本，并明确要求第三方许可不作为仓库发布的硬性前置。按 [第三方声明的发布政策](../THIRD_PARTY_NOTICES.md#repository-publication-policy)，保留素材、原署名及 `not_assessed` 事实，不将未知状态改为 MIT 或已获许可。Case Memory 准入、权限和隐私合同保持原义。正式发布取本政策文档 PR 合并并完成 main 复验后的完整 SHA；实际验收、合并和 Release 身份由该 PR 台账及 GitHub 对象登记，不预填未来成功。下方“尚未授权”的记录保留 E2 最初交接时的事实，由本段覆盖当前操作授权。

用户授权完成 E1 综合验收与 E2 发布评审、交接。**实际创建 tag、draft Release 或正式 GitHub Release 尚未获得明确授权，也未执行。** 当前真正 latest Release 为 [v10.1.0](https://github.com/Vexushi1/mathmodel-skill/releases/tag/v10.1.0)，固定于 `8fc5b42a953204b64a8ff7ddc00d5fb8983072a4`；开发主干 Skill 版本与 GitHub 发布对象分别记录。

E2 仅更新当前说明、验收台账、第三方材料记录与交接导航。按 [Governance 第 5.1 节](../SKILL_CHANGE_GOVERNANCE.md#51-docs)，保持 Skill 10.17.1；独立协议、运行行为、代码、CI、Schema、模板输出和用户项目保持各自当前语义。

## 1. E1 精确验收证据

| 项目 | 记录 |
|---|---|
| 实施 PR | [#259](https://github.com/Vexushi1/mathmodel-skill/pull/259) |
| 最后生成后的 source head | `b28731db29fa9e52d98e7a31ffde819db5f02e98` |
| 专项验证 | [run 36747213248](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36747213248)，634 项；实际结果与日志见该运行和 PR 关闭台账 |
| 正式完整验证 | [run 36748623437](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36748623437)，九个正式门；Windows Python 两版本各 2453 项，分别四个文件分片 |
| Optimization baseline | [run 36748623490](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36748623490)；必需 source_snapshot / characterize 与可选 preview 的实际 disposition 分开记录 |
| squash main | `c270900683a5080cb914bdf3f05ef1993170f847` |
| 已测 head 与合并 main 的 Git tree | `350315a2dc90b3e3592c758e54cb4a47ea1f1f29` |
| 合并后正式 CI | [run 36752661198](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36752661198) |
| 合并后生成物检查 | [run 36752661194](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36752661194)，verify-main |

E1 的具体场景、方法和范围见 [实施记录](modeling_intelligence_e1_execution_plan.md)、[52 场景与十条跨模块链映射](modeling_intelligence_e1_acceptance_matrix.md)及 PR #259 的最终关闭台账。正式 Python 证据包含标准 discovery 全集、分片分组、Python 版本、实际 checkout/source/event SHA、错误列表、日志与 artifact 身份；不能用汇总绿色替代这些覆盖事实。

E2 自身的 PR final head、CI、squash 与 main 复验登记在 **E2 PR 的关闭台账**，以避免把包含本记录的源码 head 反写进自身造成循环变化。本文成稿不预登记 E2 未来 CI 成功。

本节 E1 head/main 的九项正式门和八个 Python worker 均成功；两版本覆盖摘要都核对 2453 个标准 discovery ID、四片、当前 source/checkout 与 `errors=[]`。专项为 634 项、544.685 秒、1 项条件 skip；完整模式的专项 job 不适用。Optimization 两项必需 job 成功、未改渲染源码的可选 preview skipped；历史 Windows MATLAB preview 证据未登记为本轮重跑。

### 1.1 保存的有限资源与原生证据

| 产物 | 当前身份 |
|---|---|
| [E1 resource artifact 11114491398](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36748623437/artifacts/11114491398) | ZIP SHA-256 `8e0ec824567d4a3c8e582ab90ca630388cf05cc30f4f879c00f1a0138454402c`；`e1-resources.json` SHA-256 `928eeb854f6e9e5ad9a547b4672a545ffa94df4d3808b303c5bead271c5671d4`；source/checkout/tree 与上表相同 |
| [Windows MATLAB native artifact 11113538791](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36748623437/artifacts/11113538791) | ZIP SHA-256 `a96231b6a862191e3d20af0fec1a07ba6b1d35e193934f996da6703d6e7b6e43`；复核真实 primary/analysis、receipt/XLSX、A2/B1、辅助输入、同后端、Unicode/引号和哈希大小写 |
| [Strict Optimization artifact 11113821342](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36748623490/artifacts/11113821342) | ZIP SHA-256 `8ea8755a41a47b66b02d5ac92073ab716f7162dabdbaab30aaf75b56f168cd09`；19 个当前 P2 场景 `unexpected_legacy_changes=[]`，仅登记过的历史变化/精确载体差异例外；原固定基线 16 场景相等 |

| 固定单样本操作 | elapsed（毫秒） | Python 跟踪分配峰值（bytes） | 返回 UTF-8 bytes | 实际 corpus-open 次数 |
|---|---:|---:|---:|---:|
| ordinary routing / extensions off | 802.7152 | 2559006 | 15987 | 0 |
| explicit retrieval off | 0.1915 | 2008 | 202 | 0 |
| explicit retrieval on | 664.3566 | 1050174 | 3105 | 15 |

每行只有一个固定样本；用途不同，不作算法优劣或统计性能结论。计时解释及未冻结阈值见第 6 节。检索开发评测为 30 行（10 个派生查询 × 3 种模式）、无预期外错误；`independent_performance.status=not_assessed`。

Python 完整回归 wall time（不含 queue/setup）：head 3.10 为 1202.6085171 秒、3.14 为 800.4357765 秒；main 分别为 1119.0614506 / 884.2630975 秒。运行环境负载不同，不把差值归因于本轮提速或用户数值算法。head 的四片总 runner time 分别为 3349.5169152 / 2868.2998889 秒，main 为 3778.4207222 / 3092.3604141 秒。

## 2. A—D 的已合并范围

| 阶段 | 实施与证据 | 有限能力边界 |
|---|---|---|
| A0/A1 | [#237](https://github.com/Vexushi1/mathmodel-skill/pull/237)，历史 main CI 36119863180 | Code ↔ Model 结构/身份/静态引用闭合；不证明任意约束有效或普遍数学等价 |
| A2 | [#238](https://github.com/Vexushi1/mathmodel-skill/pull/238)，历史 main CI 36137982829 | 显式阶段接入真实 primary/analysis bundle、交付/receipt 与失效链；不替代原批准和数值验收 |
| B1 | [#239](https://github.com/Vexushi1/mathmodel-skill/pull/239)，历史 main CI 36212303219 | 已登记来源、selector、单位与有限算术；不推断显著性、机制、全局最优或稳健性 |
| B2 收口 | [#250](https://github.com/Vexushi1/mathmodel-skill/pull/250)，历史 main CI 36429993892 | 正文/Figure/载体消费、局部失效与结构化否证回退；整体语义及视觉另行审阅 |
| C1 | [#252](https://github.com/Vexushi1/mathmodel-skill/pull/252)，历史 main CI 36526211226 | 可选回执只读核验；声明 PASS 不自证独立执行 |
| C2 | [#255](https://github.com/Vexushi1/mathmodel-skill/pull/255)，main CI 36665935999 | 显式 scoped receipt 门禁与修后复验；不替代 Human Model Approval 或 accepted 资格 |
| D1 | [#257](https://github.com/Vexushi1/mathmodel-skill/pull/257)，main CI 36708442608 | 七条合成来源/案例的准入、去重、来源与证据屏障；不自动入库真实项目 |
| D2 | [#258](https://github.com/Vexushi1/mathmodel-skill/pull/258)，main CI 36729741410 | 有界离线检索、合法 no_match、显式采用/拒绝引用与 currentness；开发种子测量不是独立效果评估 |

历史 Linux Python 和 13/13 CI 记录保留当时事实。本次正式 Python 平台为 Windows 3.10、Windows 3.14；不能批量重写旧记录来表示新平台。

## 3. 总计划第 20 节：17 项判据 disposition

`machine_complete` 表示本记录范围内的有限实现、行为测试、来源身份与证据链闭合；它不会授予任意用户项目数学、数值、人类审查或公开发布资格。机器可判定部分和诚实保留的 `not_assessed`、不支持与 `publication_pending` 分别登记。

| 序号 | 判据摘要 | disposition 与证据范围 |
|---|---|---|
| 1 | 当前事实与单一 Authority | `machine_complete`：bootstrap/治理/current main 与图闭包核查；E2 记录只引用 Authority，不复制资格规则 |
| 2 | A 冻结负例与合法变换边界 | `machine_complete`：A01—A12、E1 允许近似/工程变化及未知区域行为映射；普遍数学等价、任意算法正确性 `not_assessed` |
| 3 | A 绑定实际阶段 bundle | `machine_complete`：A2/native primary/analysis、源身份及原批准/数值门；真实赛题独立运行不由仓库 fixture 代替 |
| 4 | B selector/算术/单位/范围/关键主张 | `machine_complete`：B01—B16 正负例及声明闭包；任意论文语义穷尽 `not_assessed` |
| 5 | B 不绕过 accepted/freshness | `machine_complete`：原资格消费者、helper drift 和旧 workbook/正文影响链；好看的数字不能覆盖当前源失效 |
| 6 | C 拒绝重放与虚构独立性 | `machine_complete`：当前快照、旧 PASS、命令失败与不支持身份的拒绝/未核验行为；可信原生或人类身份不自证 |
| 7 | C 修复与复验可追踪 | `machine_complete`：C10—C12 scoped coverage 与关键 finding 的当前单独复验；Human Model Approval 保持用户明确批准边界 |
| 8 | D 来源/权利/隐私/迁移记录 | `machine_complete` 于当前七条明确合成 source/card：字段、精确来源和准入屏障闭合；作者/隐私声明不替代独立人工认证，不包含未经授权真实案例 |
| 9 | D 可解释匹配/no_match/资格隔离 | `machine_complete`：有类型条件、未知/冲突/同源排除、显式引用事务及批准/accepted 保护；独立建模效果 `not_assessed` |
| 10 | 默认只读与唯一事务协调 | `machine_complete`：检查默认只读；各业务写入走唯一适用入口及既有 ProjectTransaction 协调。D2 的 `case_references.record_reference(write=True)` 是显式业务 writer，业务增量仅限所选小问 `case_references` 与 `state_generation`；未增加并行事务层 |
| 11 | 旧项目/残缺/未知/并发/恢复 | `machine_complete`：既有兼容、严格协议、read-set 与故障注入行为映射；纯当前 State 不独立证明历史未被删改 |
| 12 | 主流程/MATLAB/PQS/LaTeX/包 | `machine_complete`：正式九门、native primary/analysis/XLSX/receipt/A2/B1、Linux LaTeX 与当前包证明链；人工视觉、整体图注语义 `not_assessed` |
| 13 | 关闭/开启成本与按需读取 | 有限资源观测已记录：普通 routing 与 explicit retrieval off/on；关闭时真实 corpus-open 禁止；全部业务受控 on/off、总 RSS、未预冻耗时阈值及 contest solver 性能 `not_assessed` |
| 14 | 52 场景与跨模块实际映射 | `machine_complete`：A12+B16+C12+D12 场景及十条混合链对应具体行为方法/审查；场景数与测试数分开，未用关键词存在断言代替行为 |
| 15 | producer/consumer/validator/失效规则 | `machine_complete`：E1 映射与现有 Authority 所有权链；案例建议不产生当前题数据或批准，失效仅由真实依赖触发 |
| 16 | final head 基础/专项/生成物/CI | `machine_complete` 于第 1 节 E1 精确证据；E2 自身运行与 main 事实仅由 PR 关闭台账登记，不预填未来 PASS |
| 17 | 版本/迁移/来源/回退不夸大 | 文档交接已记录：Skill 10.17.1 与独立协议、旧项目/回退、下列实际来源和有限未核验项；第三方再分发权利 `not_assessed`，实际 tag/Release `publication_pending` |

因此，本记录关闭的是既定有限范围的机器实现与维护交接。真实建模质量、人类语义/视觉、未受支持身份和第三方再分发授权继续按各自 owner 与证据处理。

## 4. 版本与当前协议

| 对象 | 独立版本/支持范围 |
|---|---|
| Skill 与根/package 入口 | **10.17.1**；root/package `SKILL.md` 字节一致；bootstrap 为 Skill 身份源 |
| Bootstrap Schema / Governance | 1.1.0 / 1.0.6（适用 `>=6.3.0,<11.0.0`） |
| Project State | **8.15.0**；可选 `case_references`，严格保护 8.14.0 predecessor |
| User Execution / Runtime Assurance / State Transition | 3.2.0 / 2.4.0 / 1.6.0 |
| Model Approval / Code Quality | 1.1.0 / 1.4.0 |
| Code ↔ Model Conformance | Authority 1.1.0；记录协议 1.0.0 |
| Claim Evidence / Claim Consumption | 1.0.0 / Authority 1.8.0；消费策略使用精确 1.0.0—1.5.0 模式/协议对 |
| C1 / C2 | 各 1.0.0；C2 consumer 精确支持 State 8.14.0 / 8.15.0 |
| D1 / D2 | 各 1.0.0；分别 introduced in Skill 10.16.0 / 10.17.0 |
| Workbook / Writing Reasoning / Task Taxonomy | 2.3.1 / 1.10.0 / 2.1.0 |
| Global Preprocessing / Source bundle | 1.3.0 / 1.1.0 |
| RUN_RECEIPT | 默认 preprocessing 1.0.0，primary/analysis 1.1.0；明确辅助输入场景的 1.2.0 资格按 User Execution 单独核对 |
| Primary Quality / 框架模板 | 1.0.0 / `v0.8-project-memory` |
| Reading plan / compile-profile lineage | 1.1.0 / 6.2.3 |

Skill docs 交接不改变上述独立协议或其资格语义。当前版本断言、前驱 hash 和严格 Optimization 行为比较保持；新增导航文档不进入普通任务默认 corpus 加载。

## 5. 兼容与回退

1. **未声明扩展的旧项目：**沿用当前 Authority 的只读兼容；不补造 A/B/C/D PASS，不暗加案例库、强制产物或资格。原数值、批准和硬门仍生效。
2. **主动进入当前协议：**先 inspect/dry-run、说明影响；用户项目记录写入、后端迁移、模型批准和真实资料公开各需要适用的明确授权。仓库实施授权不会自动涵盖这些行为。
3. **部分字段/未知版本/重放：**失败关闭，不删除新字段伪装旧格式；历史连续性需要已有记录与证据。
4. **项目数值职责：**项目根统一 Python/MATLAB 后端，primary 与已启用 analysis 继承；用户 Windows full-fidelity 执行与精度、数据/网格/时域不缩减。PQS 与 Analysis Necessity Gate 保持分离；`not_required` 不表示稳健性已测。
5. **状态与恢复：**必要写入核对 generation、原字节与 read set，并由原事务 owner 提交。prepared journal 按原显式恢复入口处理；不承诺所有失败自动回滚。
6. **D withdrawal/关闭：**当前引用可报告 needs_review；关闭检索不删除已保存引用、不自动重算或撤销无关 accepted/批准。
7. **仓库回退：**文档主题可经审查 revert PR 并远端复核；用户状态不是 revert 删除对象。旧 reader 不支持 State 8.15.0 时保留原数据并报告不支持，不删字段降级。
8. **解析回退：**`HSK_YAML_PURE_PYTHON=1` 选择 SafeLoader；`HSK_YAML_DISABLE_CACHE=1` 禁用普通解析缓存。只复用内容解析和独立对象副本，当前字节、严格 parser、预算和 freshness 仍执行，不缓存 gate PASS 或项目资格。
9. **发布回退：**如以后获准发布，固定完整提交；保留旧 v10.1.0 标签，不移动已发布标签，修复另行记录。

当前 `scripts/safe_yaml.py` 原字节 SHA-256 为 `4186425547074ff8a12d06a24edf5ff48851a9685d6057c777d6906eb6dabc03`。D1 Schema 原字节 SHA 为 `17c23997d95a3b6d3dcadf887a0f477904e7b72427d59337d91815f9d4cedd4c`，consumer 规范化 pin 为 `4d6a70e50fb5a238833efb672dc70734204588e0980dc5a8bd4adcdd515714b1`；D2 Authority 原字节 SHA 为 `33fee96a83af85a021bf47d4612eeba127fb032950372b3b150b9d5244baa51c`，规范化 pin 为 `f5156422cba89433934515693cba3de6d7047eca3252d9659b8388d10ca8c615`。原字节与规范化身份分别维护。

## 6. 正式平台与资源测量解释

正式 Python full regression 仅为 **Windows 3.10 / Windows 3.14**，各四个文件分片，保持 `Python 3.10`、`Windows Python 3.14` check 名称与标准 discovery 全集。Windows Server 2022 + MATLAB R2024b 验证原生 primary/analysis、XLSX handoff、receipt、A2/B1 与同后端链。Linux 保留 CUMCM、MCM-ICM、Diangong 和 Production LaTeX attestation；静态、生成、来源快照等 Linux 工具作业不构成 Linux Python 兼容承诺。

仓库维护验收仅在 GitHub：source push → remote generated final head → 专项/冻结完整覆盖 → squash 与 tree 对照 → main full/verify-main。未执行本地 lint、unittest、generator、MATLAB 或 LaTeX。真实赛题数值运行仍由用户在本机完成。

E1 资源报告观测固定普通 routing、explicit retrieval off/on 的 elapsed、Python 分配峰值、输出 UTF-8 字节、真实 Path.open 次数和声明资源身份。每次样本清普通解析缓存、重验当前快照；普通关闭路径禁止 corpus 打开。计时包含序列化/观测开销，排除初始 import、依赖 preflight、身份捕获、queue/setup；tracemalloc 不是总 RSS，声明加载量不是助手实际 token，Path.open 次数不是物理磁盘 I/O。

A0 没有预冻秒数/RSS 阈值，资源报告记录 measurement 并保留 `not_assessed` 性能门状态；已有尺寸/节点/对象/context 预算保持。其它同步/交付/写作测试有真实逐项 CI 计时，但不构成全部业务受控 on/off 实验。仓库回归时长、该有限资源观测与真实赛题求解速度分别解释。

## 7. 实际材料来源与再分发状态

规则与具体范围见 [LICENSE](../LICENSE)、[THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md)。HSK MIT 声明只覆盖具有相应权利的 HSK-authored 内容；公开可见、可下载或用户提供均不自动获得再许可。

### 7.1 CUMCMThesis 2017 快照

实际目录 `templates/latex/cumcm/cumcmthesis/` 的 class 标头为 `[2017/09/16 v2.6 Standard LaTeX Template for CUMCM]`，目录内没有随附 LICENSE。class Git blob 为 `4c0c3f27cc20e71c981812df91858a53f75196a5`，材料原字节 SHA-256 为 `6eb262856c676d81198b68277138984408dc9d0d6f92f4214190b942141c894c`。

2026-10-01 查询[官方 upstream root/LICENSE](https://api.github.com/repos/latexstudio/CUMCMThesis/contents/LICENSE)得到 404。该次查询仅说明此路径未获取到许可文件；不证明 upstream 没有其它许可，也不能为 2017 旧快照建立许可。保留原 class/header/attribution，快照再分发许可标记 `not_assessed`，不将其重标为仓库 MIT。

### 7.2 15 张视觉参考 PNG

`assets/nature_figure/chart-atlas/` 10 张、`gallery/` 5 张，合计 15 张 / 5,719,993 bytes。用途说明和目录名称不证明真实来源、原创或再分发许可。逐项 author/source/generation-or-acquisition/license/permission 证据尚未建立，状态为 `provenance_not_assessed / redistribution_permission_not_established`。

以下路径相对于 `assets/nature_figure/`：

| 文件 | 原字节 SHA-256 |
|---|---|
| `chart-atlas/atlas-01-bar-charts.png` | `4a0e3040bbdbfe5ec48b66515f719f83ad7304fadb2e56432cd3e8f7ccbabd65` |
| `chart-atlas/atlas-02-line-trends.png` | `9a8189149180a68679738bc4be152ee40b17d71261d71b3759d315a7169da0d9` |
| `chart-atlas/atlas-03-heatmaps.png` | `40dd7c7c14c45b45cc22ee23e19f2dc1901f38b26a1fb4b0f26a30dbd10c0423` |
| `chart-atlas/atlas-04-scatter-bubble.png` | `1bbfbc38a3f246e4fd7c59b9ed1003ddbc7280ee160b7c38abf8d410b27fe6f8` |
| `chart-atlas/atlas-05-radar-polar.png` | `e7fa7d98cd4f5263f5550d7ac8824e60071c20b2927aef52ac6d18d62fd29ffa` |
| `chart-atlas/atlas-06-distributions.png` | `a1fe533d07dae36d11c997577ded61adb16bf5d4dd5c0dee2ff92ae570f0f01e` |
| `chart-atlas/atlas-07-forest-interval.png` | `dc61a5257eae4748348c72c51f2e70e59979c6892f52dadf7bb4ba6f8b98b00b` |
| `chart-atlas/atlas-08-area-stacked.png` | `350c25e427d945dee5fd98316eb6ebe307304b9d187d954a88c05852d664a60b` |
| `chart-atlas/atlas-09-image-plates.png` | `bbc8c0b8708d42465e57cb7c56b4d2ecfbaa63340a5a6dfefbcb51189cd1a995` |
| `chart-atlas/atlas-10-network-matrix.png` | `cd384abe10aa86bd310c1288a42f33735cb555c267bddae1ecd262905a7a1de5` |
| `gallery/fig1-material-mechanism-rich.png` | `2e0706fae3256e1de2388f8605f35b9b6ac23cfc397161a952f34cc5fa2f2192` |
| `gallery/fig2-spatial-imaging-rich.png` | `90081b3f778b9ede2dba41c60b6abf0c28a239060c69428344539529cd7f3257` |
| `gallery/fig3-in-vivo-efficacy-rich.png` | `25d6fc50f5808104a7cb19f4795cea4229fbc6159fa7509f716a94f7c160a033` |
| `gallery/fig4-single-cell-systems-rich.png` | `999edb06b942f988a51b11f947845e42e4c346b2f9e5d5a6425def9e43bb69d1` |
| `gallery/fig5-validation-perturbation-rich.png` | `245ad31f97b2054628987444e44d6a007f352f65ae6254189f5ed8ba9b0301c6` |

### 7.3 用户提供的版式参考与 A196 笔记

| 材料 | 当前来源事实 | 状态 |
|---|---|---|
| `templates/latex/cumcm/hsk/reference/example_mm_r1.tex` | 标注 user-provided visual/layout reference；非当前 executable competition class。Git blob `6694bf11d94449f692a7c19b8db7cead95e3432e`；原字节 SHA `58e852add7ad04924d5dcad77948044331c3a0d5d0b7ac5ddfdcf608db2538f1` | 作者/权利与公开再分发授权未附证；`not_assessed` |
| `templates/latex/cumcm/hsk/reference/a196_framework_notes.md` | 自述来自用户上传 A196.pdf，仅章节结构笔记、不复制正文/公式/图表/数据。Git blob `a12f4c673ecbda0780e220c43b1f107d46b0f061`；原字节 SHA `2c29e9005f646a6382aabbfa8cc21cd351c71e6a4ad707871e5e33536f659cbe` | 笔记与原论文权利分开；未认证原论文公开再分发授权 |

### 7.4 历史论文目录与当前合成库

`legacy/papers/` 当前仅有 `README.md`、`_DOWNLOAD_REPORT.md` 两个 MD，没有 91 篇 PDF。91 篇 / 约 432MB 是历史取得记录，不能登记为本轮当前或待发布包内容；该目录不进入默认运行链。

D1/D2 当前 source/card 各 7 条、同源组 7 个，声明 independently-authored synthetic、repository MIT 及明确合成/推荐验证证据等级；未执行这些合成方案的建模计算。准入与真实文本绑定闭合，作者/隐私自查声明不替代独立认证。真实题目、论文、用户对话或项目数据入库须另行明确授权与来源审查，不能凭权限字符串自动准入。

## 8. 保留的有限未核验范围

- 整体论文语义、整段图注、人类语义覆盖、图片视觉充分性：`not_assessed`。
- 可信原生隔离 reviewer / 人类 attestation：当前协议不自证可信身份；自述 PASS 不产生批准或 accepted 资格。
- 真实赛题建模质量、独立分组留出集效果、获奖提升：`not_assessed`。种子派生开发查询不作独立效果证据。
- 真实赛题求解性能、全部业务受控 on/off、总 RSS 与未预冻时间门槛：`not_assessed`。
- 动态/不确定 LaTeX、未支持 DOCX OOXML 或缺独立渲染证明的 DOCX 正式提交，按现有 Authority 报告不支持/失败关闭；读取支持不授予正式提交资格。
- 第 7 节第三方再分发权利：`not_assessed`；材料仍有具体记录，不填“全仓 MIT 已核清”。
- 实际 tag、Release 和发行资产：`publication_pending`；GitHub 自动 source archive 包含受跟踪材料，附加 assets 为空不代表无需核查再分发范围。

## 9. 发布评审结论与交接

发布评审建议维持 **Skill 10.17.1**，以 E2 文档 PR 合并且 main 复验完成的完整 SHA 作为将来发行目标，发布说明同时列明 A—D 能力、E1 精确证据、独立协议、兼容/回退、第三方状态与未核验边界。当前未创建 v10.17.1 tag/Release，也未生成或上传发行包。

2026-10-01 用户已授权正式发布，并批准许可确认不作为发布硬门。版本保持 v10.17.1，固定 SHA 取本政策 PR 完成 main 复验后的完整提交；使用带有限验收与来源状态说明的 Release 正文及 GitHub 自动 source archives，不另上传发行附件。第 7 节来源与许可未知事实继续披露，原署名和第三方权利声明保留；不把这项发布授权当成第三方许可或 Case Memory 准入资格。

交接入口：[总计划](modeling_intelligence_evidence_evolution_plan.md)、[E1 验收映射](modeling_intelligence_e1_acceptance_matrix.md)、[当前 README](../README.md)、[案例准入说明](../knowledge/case_memory/README.md)、[第三方声明](../THIRD_PARTY_NOTICES.md)。当前事实以 bootstrap、实际 GitHub 对象和对应 PR 关闭台账为准。
