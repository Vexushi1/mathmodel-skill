# 论文资料库（legacy/papers）

> 本目录是历史资料获取记录与人工维护区，**不属于 Skill 默认运行链**。当前活动 Router、写作模块和评分流程不依赖这里存在 PDF 才能运行。

## 当前仓库状态

当前受版本控制的该目录主要保留本说明与 `_DOWNLOAD_REPORT.md`。历史论文批量下载、抽取和统计过程已经归档；论文 PDF 本身不应被重新当作活动 Skill 依赖。

`_DOWNLOAD_REPORT.md` 记录过往 CUMCM 论文获取与抽检情况。相关一次性维护脚本已经移动到 `legacy/tools/`，仅用于人工复现或历史核对。

## 如需人工补充历史论文

若维护者明确需要重建历史资料集：

1. 将人工确认来源的 PDF 放入 `legacy/papers/` 的适当子目录；
2. 需要离线统计时，可显式运行归档脚本：
   ```bash
   python legacy/tools/ingest_papers.py --papers-dir legacy/papers/
   ```
3. 该脚本是历史维护工具，不是当前写作或评分 Authority；其输出只能作为人工参考，不能直接覆盖当前 `core/`、`modules/` 或 `packs/` 中的活动规则；
4. 如需修改当前写作阈值、评分规则或论文结构，应回到当前活动 Authority 按 `SKILL_CHANGE_GOVERNANCE.md` 单独修改，不能从 legacy 资料自动反推并写回。

## 来源与使用边界

可人工查找公开来源，包括官方公开展厅、公开 GitHub 仓库或其他可验证来源；来源真实性、年份、题号和奖项等级必须由维护者自行核对。历史第三方索引和社区汇总只能作为线索，不能自动视为权威。

Skill 运行时禁止默认扫描或加载本目录中的 PDF，以避免把历史语料、旧规则或未经核验的外部材料混入当前项目语义。即使本目录没有任何 PDF，当前 Skill 仍应完整运行。
