# HSK v6.3.4 Starter Cleanup

## 修复

- 全面重写 `templates/code/starter/` 五类题型入口，删除导入阶段设置随机种子、创建结果目录和直接写工作簿的旧行为；
- `templates/code/hsk_pipeline/main_pipeline.py` 新增统一 `run_pipeline()`，集中执行配置校验、随机种子、数据审计、求解、验证、两类工作簿写入和模型论文框架同步；
- starter 显式传递 objective、structures 和完整 capabilities，工作簿不再绕过三轴 Schema；
- 新增 `hsk_pipeline/__init__.py` 与 starter 使用说明，明确复制结构和题目专属钩子职责。

## 清理

- 删除已有真实状态示例后失去作用的 `state/.gitkeep`；
- 删除可由 `example.tex` 重建、且不参与编译与测试的 `cumcmthesis/example.pdf`；
- 将退出新项目默认链路的 `hsk_find_project_root.m` 和 `hsk_export_figure.m` 迁入 `legacy/matlab_compat/`；
- 保留仍有回归测试和旧项目兼容价值的 `hsk_read_result_workbooks.m`；
- 图集清单改用独立 `schema_version` 与 `skill_compatibility`，不再把资产 Schema 与 Skill 发布版本混用。

## 验收口径

- 导入 starter 不得创建目录、设置随机种子、读取数据、求解或写文件；
- 五个 starter 必须使用统一 `run_pipeline()`，并声明 objective、structures 和完整 capabilities；
- optimization starter 必须要求显式约束与可行性检查，prediction/classification 必须要求外样本和泄漏检查，simulation 必须要求收敛与不确定性检查；
- 活动模板中不得残留已迁移 MATLAB 辅助函数、冗余 `.gitkeep` 或可再生示例 PDF；
- 生成索引与 `MANIFEST.sha256` 必须由 `scripts/generate_indexes.py` 刷新。

## 兼容性

- 路由、工作簿 Schema、项目目录和正式交付 gate 不变；
- 历史项目仍可从 `legacy/matlab_compat/` 取回旧 MATLAB 辅助函数；
- 新项目应复制完整 `hsk_pipeline/` 与一个题型 starter，不再使用旧的单文件直接写表入口。
