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
| P1 | 可重算的读取与行为基线 | 本分支实施；验收/合并以 PR 和 CI 实际记录为准 |
| P2 | 读取范围、事实同步和工具调用分流 | 待 P1 合并 |
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
