# HSK Runtime Router v6.3.0

文件名保留 V622 作为兼容路径。机器路由以 `core/workflow_router.yaml` 为准。

## 启动

```text
读取 core/bootstrap.yaml
→ 调用 scripts/resolve_workflow.py
→ 合并多个意图
→ 确定 objective / structures / capabilities
→ 加载必要模块、Pack、模板
→ 到用户要求的交付物停止
→ 正式交付前运行 scripts/sync_project.py
```

## 示例

```bash
python scripts/resolve_workflow.py code_and_solution figures \
  --objective optimization \
  --structures stochastic \
  --competition CUMCM
```

```bash
python scripts/resolve_workflow.py \
  --request "检查现有结果并重画MATLAB敏感性图" \
  --objective optimization
```

项目同步器是 utility gate，不属于求解模块，不得自动把验证状态提升为 passed。
