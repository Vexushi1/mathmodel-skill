# Skill 全面优化实施记录

## 已批准范围与基线

2026-09-15，用户在审阅《Mathmodel Skill 全面优化计划》后明确表示“全部都批准，考虑开始进入优化部分”。本记录落实该批准，不重新定义业务 Authority。

- 批准文稿：`mathmodel_skill_optimization_plan.md`，80,455 bytes。
- 原文 SHA-256：`05808d566177dd44b3bbf924db43fad5a239c6b5d599b5faa9cc0f65af8fd365`。
- 设计与实施起点：`8a92a7924e950939dc77b15d3bb1a88400c09979`，Skill v9.1.0。
- 实施前已重读 main 的 `core/bootstrap.yaml`、`SKILL_CHANGE_GOVERNANCE.md`、`AGENTS.md`，开放 PR 查询为空。
- 完整设计稿仍以用户批准的上述文稿为准；本文是实施登记，不声称是该 20 节文稿的全文副本。

批准覆盖基础优化、配置/回执分离、论文参考驱动绘图、条件式分析和附录方案。批准不撤销各项前提：基础设施仍需测量证据；非 MATLAB 后端仍非本轮必要前置；精度与官方 Adapter 仍独立迭代；最终版本依据实际兼容性在发布时裁决。默认不删旧 reader、不修改旧项目、不直接写 main。

## 分阶段执行

| 阶段 | 主题 | 状态 |
|---|---|---|
| P0 | 计划与范围审批 | 用户已批准 |
| P1 | 可重算的读取与行为基线 | 已合并，PR #152，`0eecaf929c83f19555402564ea0b14743d9bcf7d` |
| P2 | 读取范围、事实同步和工具调用分流 | PR #153 实施；最终 head 验收/合并以实际 CI 为准 |
| P3a/P3b | 全局去重、逐章写作与清理职责 | 未开始 |
| P4 | compact 实例化与渐进登记 | 未开始 |
| P5a/P5b | RUN_CONFIG 命名、版本化回执 | 未开始 |
| P6a/P6b | 论文图例索引、独立 MATLAB profile、真实预览 | 未开始 |
| P7 | 条件式分析与附录 | 已获范围批准，尚未实现 |
| P8 | 有测量依据的基础设施整理 | 未开始 |
| P9 | 综合回归、兼容与发布 | 未开始 |

## P1 修改简报

**主题：** 固定代表请求，建立只读、可重算的 resolver 资源与行为基线。

**版本与等级：** 维护侧测试/证据增强，不改变产品行为；保持 v9.1.0，不宣称已发布 v9.2.0。

**直接目标：** 对真实 `scripts/resolve_runtime.py` 调用取证，而不是只加总路由 YAML 中的文件大小；把主张为“读取更轻”所需的对照数据先建立起来。

**范围：** 本记录、16 个请求/项目 fixture 定义、维护测量驱动、回归测试、只读 CI 取证流程及生成器正常生成的索引/MANIFEST。新增文件均在维护侧，不增加用户项目文件。

**不改：** core/modules/packs/templates/scripts 的业务内容、模型审批、identity、typed stale、工作簿 Schema、03A/03B、每问五文件、绘图后端、正式提交规则和 release carriers。

**权威来源：** `core/workflow_router.yaml`、`core/runtime_assurance_contract.yaml`；调用现有 `scripts/resolve_runtime.py`，复用 `tests/test_v900_semantic_identity_binding.py` 的 SIB 测试构造器。测试中的 approved 仅为隔离合成状态，不是用户项目批准记录。

**兼容与迁移：** 无用户项目迁移；旧 CLI 和所有运行时字段保持不变。回滚本批新增维护文件并重新生成索引即可。

## 测量口径

`tests/optimization_baseline.py` 每个案例启动独立 worker，避免两份 checkout 共享导入缓存。身份测试只写临时合成项目；resolver 调用前后比较项目文件哈希，发现写入即失败；从不导入或执行赛题求解脚本。

报告记录：

- resolver 最终 `load_order` 的去重文件字节与哈希；
- 机器 dependency closure 的完整路径与独立字节量；
- 两者的去重并集，避免重复加总；
- 意图、模块顺序、scope、pause、完整 gate 记录、terminal outputs、状态恢复与 artifact assurance；
- Authority fingerprint、源码 commit、fixture/测量驱动哈希、Python/PyYAML/平台版本。

`required_read_bytes`、`actual_read_tokens`、`repeat_read_bytes` 保持 null，因为本阶段没有助手实际读取轨迹。`kind_hint` 只是按路径分类的统计标签，不是新 Authority 或运行时读取政策。CUMCM 的 `resource_availability_only` 单独保留，不能把整份资源清单称为实际上下文。

P1 的比较要求同一输入与同一测量驱动，并预期业务行为、Authority 指纹与资源字节不变。**零变化是本阶段成功，不是减负收益。** 后续改变路由/Authority 时必须说明预期差异，不能把 P1 的全等比较机械用作永久禁止优化的门。

## 代表性场景

16 个案例涵盖结果摘要同步/模型变更、新图/样式返修、draw.io、项目同步、返回工作簿验收、CUMCM/MCM 写作、显式意图优先、无批准求解，以及真实 SIB 恢复下的批准、未批准、身份漂移、SIB 外措辞和 legacy 状态。

这些案例测量路由及身份边界，不声称覆盖完整数值求解、每类工作簿验收或 MATLAB 视觉效果。现有完整测试继续承担各自职责。

## 重算与验收

```bash
python -m unittest discover -s tests -p test_optimization_baseline.py
python tests/optimization_baseline.py --repo-root /path/to/baseline --output /tmp/baseline.json
python tests/optimization_baseline.py --repo-root /path/to/candidate --output /tmp/candidate.json
python tests/optimization_baseline.py --compare /tmp/baseline.json /tmp/candidate.json --output /tmp/comparison.json
```

两次测量必须使用同一份本阶段驱动及 case 文件，只改变 `--repo-root`。Pinned baseline 要使用完整 checkout/worktree，不能用一份精简下载目录冒充完整仓库。

`Optimization baseline evidence` 工作流重新运行固定基线的 lint、完整单元测试和 generated check，再测量基线与候选，上传实际 JSON 与日志。既有 `HSK Skill CI` 保持全部检查；索引由既有 refresh 工作流生成，不手填 MANIFEST。

没有看到成功日志前不得将测试标为 passed；没有合并前不得把 P1 写成 main 已完成。当前批次不进行 MATLAB 渲染、国赛 PDE 重算、第三方论文图例收集或官方规则核验。


## P1 合并收尾

2026-09-15，用户明确要求合并 P1 后继续 P2。重新核对 P1 head `37f42089ca104e2586f882a76cf2c034a7279842`：HSK Skill CI run `34918609397`（11 项）、Optimization baseline evidence run `34918609487`（1 项）均为 completed/success。此前 action_required 已由第二次成功运行解除，PR 描述已更正。

使用 expected_head_sha 保护执行 squash merge，合并提交为 `0eecaf929c83f19555402564ea0b14743d9bcf7d`，源码树为 `639ac70ccf417f6158e0d3d0f10007fd94c4ce69`。P2 从该 main 创建独立分支，不在 P1 分支续改。

## P2 修改简报与实现边界

**分支/PR：** `refactor/optimization-p2-reading-plan`，PR #153。

**等级/版本：** 向后兼容的读取能力增量，属于已批准优化计划；保留 9.1.0 release carriers，最终 minor release 在 P9 单独裁决，本 PR 不宣称发布 9.2.0。

**直接目标：** 区分资源库存、当前要读的内容与需要执行的工具；明确结果事实同步、语义变更、纯样式返修和新图设计的读取边界。

**唯一选择 Authority：** `core/workflow_router.yaml#reading_policy`。`core/runtime_assurance_contract.yaml#reading_plan` 负责 additive envelope、来源和边界；`scripts/reading_plan.py` 实现，`scripts/resolve_runtime.py` 追加 sibling `reading_plan`；Bootstrap 与 RUNTIME_ROUTER 仅指引 consumer。

**旧接口保护：** 不删除/重排/过滤 `load_order`、modules、contracts、templates、packs、pause、outputs 和 gates；完整机器 dependency closure 与旧 assurance 保留。预期变化只有新增 reading_plan，以及 Bootstrap/Router/Runtime Assurance 三份修改 Authority 的指纹；其它已指纹绑定的来源不能默许变化。

**本批不做：** 不改变旧 resolver CLI、模型审批、identity、typed stale、工作簿 Schema、03A/03B、五文件、赛题算法、MATLAB/LaTeX 模板；不执行赛题数值代码；不压缩全部写作正文；不实施 RUN_CONFIG 或条件式分析。

### 读取分流

`reading_plan` 提供 read_now、conditional、tool_interfaces。read_now 是初始读取安排，conditional 在条件成立时仍需读取；工具接口来自已有 gate/Manifest，执行结果不能由计划推断。完整 load_order 仍供旧客户端和回退使用。

结果摘要快捷读取必须同时具有明确限域请求、显式小问、current 框架及哈希、真实已验证模型/主工作簿与可恢复依赖；否则完整回退。纯样式还要求分析工作簿、现有 approved_figures、MATLAB 脚本及图束的 validated 哈希。第一版只使用既有 per-question 图束发现范围，项目级图若没有可验证的小问绑定，宁可完整回退，不新增审批字段或凭空猜测。

请求关键词只是保守的读取选择线索，不证明语义没有变化；人工仍需核验请求、当前框架和证据。事实同步不改变 SIB/参数/假设/审批，结果变化仍按原有规则影响依赖和正文 stale。任何新发现的语义变化扩大读取并回到现有治理。

新结果图只初读结果证据与设计规则，图型选择时读取 chart_selection，实现选中的高级增强时才读取 enhancement patterns。机理图读取机理分支。CUMCM 写作完全委托已有 initial_read_order / authoring_sequence / capability preflight，不建立第二套写作调度。

### 来源与安全

每个读取条目绑定完整文件 SHA-256、相对路径和一基闭区间行号。Markdown 保留文档前言与祖先标题的适用说明；YAML 保留父映射头，必要元数据在 selector 明确列出。重复/缺失标题、非法子树或 YAML alias 等不能安全定位时扩大到完整存在文件；文件缺失、越界路径不产生空规则。文件 SHA 改变后必须重新解析。

这是读取预算，不是阅读完成回执。planned_skill_read_bytes 与 planned_project_read_bytes 分开计算，actual_read_bytes/tokens 无轨迹时为 null。不得将条件资源省去不算就宣称整任务成本降低，也不得把已经存在的 CUMCM 渐进写作当作 P2 新收益。

### 测试与对照

P1 完整代码通过 CI git archive 保存为仅 tracked 文件的源码工件，断网环境下载后核对 ZIP 与 tree 身份；不导出 .git、凭据或未跟踪内容。该精确 P1 树在本地重新通过 lint、930 个完整单元测试和 generated check。

新增 `test_reading_plan.py` 检查真实选择、范围 union 字节、中文/CRLF、代码块伪标题、缺失/重复/alias 回退、路径/symlink 越界、证据不足、身份/数据/图漂移、混合意图、只读边界、工具/条件资源可达性及原写作委托。新增 `reading_plan_evidence.py` 在隔离进程对相同 19 个请求比较 P1 与候选版本的全部旧 plan 字段，仅允许上述三份 Authority 指纹值按预期变化；不忽略其它行为差异。

P1 原有 driver 与断言不修改。CI 先以 pinned P1 driver 重跑 8a92a79→0eecaf9 的历史全等控制，再独立比较 P1→P2；没有将 P1 的全等要求放宽成可随意放行的新比较器。

本地精确源码工作树已通过 lint、947 个完整单元测试（含 17 个新增专项测试）与 generated check；隔离进程对照为 19/19 旧计划行为一致。此处只记录本地验证，不等价于远端最新 head CI 已通过；远端验收和合并仍按 PR 实际记录。

### 兼容、迁移与回滚

旧客户端可以继续只消费 load_order；新客户端从 Bootstrap/路由导航消费 reading_plan。无用户项目状态、审批或数值产物迁移，不清理旧字段和 legacy reader。回滚 P2 新增 sibling、helper 和读取配置，恢复导航并重新生成索引即可；P1 基线和测试仍可独立保留。
