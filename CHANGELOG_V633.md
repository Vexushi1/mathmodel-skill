# HSK v6.3.3 Gate Hardening

## 修复

- `sync_project.py` 在产物同步前强制执行项目状态 Schema/语义校验和模型论文框架校验，空状态与伪框架不能通过正式 gate；
- figures scope 不再依赖 `subproblem.status >= solved`，显式 figures 交付必须检查 MATLAB、正式图和 figure evidence；
- 同步器只允许设置或保持 stale，不再自动清除 `artifacts_stale` 与 `stale_layers`；
- `core/output_contract.yaml#project_sync.stage_requirements` 成为交付要求唯一事实源，Module Manifest 仅引用，运行时按 exact scope 读取；
- 首次生成 `figure_evidence.yaml` 后立即同步写入 `subproblem.evidence`；
- 项目状态 Schema 要求至少包含一个小问。

## 兼容性

- CLI、目录、三轴分类、工作簿 Schema、Python/MATLAB 职责保持兼容；
- 旧项目必须先补齐合法项目状态与当前版模型论文框架，才能通过正式同步 gate。

## 未纳入

本版本不扩展 LaTeX provenance、fallback workbook schema、ToT、多 objective、模型竞技场或 LLM 路由。
