# v6.2.2 consistency-hardening 变更记录

## 目标

本版本不改变六模块主架构，不恢复旧 Stage。重点修复核心政策、执行模板、代码工具、索引维护和测试之间的不一致。

## 已完成：P0 第一批

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

## 待完成

- P0：完成活动索引、模板索引和 Manifest 迁移；统一全部版本号与入口文档；
- P1：工作簿 Schema、项目状态 Schema、lint、CI、字体回退、许可证；
- P2：题型 Pack 增强、高级模型准入、图型选择索引、DOCX 模板合并。
