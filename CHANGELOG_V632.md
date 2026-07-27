# HSK v6.3.2 Delivery Gate Closure

## 修复

- `result_io.py`、`hsk_check_artifact.py` 与 `sync_project.py` 统一调用同一工作簿验证核心；
- design、docx、latex、submission scope 检查真实交付文件；
- 全局框架哈希与逐问章节哈希分离；
- 任意已验证哈希变化都强制设置 stale；
- explanation、optimization、simulation 必须提供专项结果表；
- MATLAB 空工作簿引用不再视为通过；
- 新增 `figure_evidence.yaml` 哈希证据，mtime 仅作辅助警告；
- 数据哈希优先使用 `project_state.data.sources`，避免论文与提交包污染。

## 未纳入

本版本不增加 ToT、多 objective、模型竞技场或 LLM 路由。
