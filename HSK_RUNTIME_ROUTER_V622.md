# HSK Runtime Router v6.3.2

文件名保留 V622 作为兼容路径。机器路由以 `core/workflow_router.yaml` 为准。

## 启动

```text
读取 core/bootstrap.yaml
→ 调用 scripts/resolve_workflow.py
→ 合并多个意图
→ 确定 objective / structures / 顶层 capabilities
→ 加载必要模块、Pack、模板
→ 到用户要求的模块产物停止
→ 执行 pre_delivery_gates
→ gate 成功后暴露 project_state / sync_report
```

## 示例

```bash
python scripts/resolve_workflow.py code_and_solution figures \
  --objective optimization \
  --structures stochastic \
  --competition CUMCM
```

解析结果会返回：

```yaml
module_terminal_outputs: [...]
pre_delivery_gates:
  - name: project_sync
    delivery_scope: figures
    command: python scripts/sync_project.py <project_root> --write --strict --delivery-scope figures
terminal_outputs: [..., project_state, sync_report]
```

`project_sync` 是 utility gate，不属于求解模块。它按交付 scope 检查必需产物、工作簿 Schema、MATLAB 图表链和分层哈希，不得自动把验证状态提升为 passed。`sync_report` 只有在 gate 成功后才视为 available。
