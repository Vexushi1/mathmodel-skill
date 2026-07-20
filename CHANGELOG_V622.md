# v6.2.2 consistency-hardening 变更记录

## 目标

本版本不改变六模块主架构，不恢复旧 Stage。重点修复核心政策、执行模板、代码工具、索引维护和测试之间的不一致。

## P0：执行一致性

- 新增 `core/compile_profiles.yaml`，统一 CUMCM、MCM/ICM 和电工杯编译链；
- 重构 `scripts/render_paper.py`，支持配置驱动的 XeLaTeX/Biber 与 pdfLaTeX/BibTeX；
- 重写活动区 MCM/ICM、电工杯 LaTeX 模板，清除 SEED、Stage、固定年份、固定题号和固定小问数；
- 重构 CUMCM HSK 起稿模板，删除内部覆盖说明附录并接入 Biber；
- 修复 MATLAB 嵌套问题目录中的项目根目录定位；
- 统一 Python starter 使用 `result_io.py`，禁止空工作表；
- 移除全局 warning 屏蔽；
- 将旧 Stage 评分权重移入 `legacy/config/`；
- 将活动审查权重更新为 v6.2.2 六维评分结构；
- 新增索引与 SHA-256 Manifest 生成脚本。

## P1：工程可靠性与版本治理

- 新增 `core/workbook_schema.yaml`，定义工作表、字段、单位、非空和 MATLAB 交接规则；
- 将 `core/project_state.schema.yaml` 升级为可由 JSON Schema 验证的项目状态契约；
- 正式定义题型分类器的主标签、次标签、置信度和多意图路由；
- 扩展 `lint_skill.py`，检查版本、YAML/JSON、路由路径、Schema、LaTeX 模板和 Python 语法；
- 增加 Python 3.10–3.14 GitHub Actions 测试矩阵；
- 增加生成索引与 Manifest 的自动刷新工作流；
- `hsk_check_artifact.py` 增加标准工作簿、必需工作表和非空检查；
- `hsk_pack_submission.py` 修复 `.synctex.gz`、`.run.xml`、`.bcf` 等多后缀辅助文件过滤；
- MATLAB 科研样式增加跨平台字体回退，并统一 legend、colorbar 和 text；
- Python 验证接口改为接收完整 `ModelContext`，避免只凭最终解进行敏感性和鲁棒性分析；
- 新增 MIT `LICENSE` 与 `THIRD_PARTY_NOTICES.md`；
- 根 Skill、插件元数据、核心政策、语义索引和运行入口统一升级为 v6.2.2。

## 自动验证

- Python 3.10、3.11、3.12、3.13、3.14 的 lint 与单元测试均已接入 CI；
- V622 完整文件索引、模板索引和 `MANIFEST.sha256` 由 Actions 自动维护；
- 全部修改保留在 Draft PR 中，P2 完成并终审后再转为可合并状态。

## 待完成：P2

- 统一增强现有题型 Pack；
- 增加高级模型准入 Pack；
- 增加图型选择索引；
- 合并重复 DOCX 检查模板；
- 删除容易诱发机械套话的固定图后解释句式。
