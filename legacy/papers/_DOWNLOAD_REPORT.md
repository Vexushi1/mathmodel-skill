# CUMCM Papers Download Report

> Historical archive note. This report records a past acquisition run and is not an active Skill dependency or current source-of-truth for writing rules.

**历史记录总计**：91 篇国赛获奖论文 PDF（约 432MB）

| 来源 | 数量 | 备注 |
|------|------|------|
| 教育部“中国大学生在线”展廊（2023） | 9 | Playwright 渲染详情页 + 图片重建 PDF（image-only） |
| 教育部展廊（2024） | 16 | 同上 |
| 教育部展廊（2025） | 7 | A 题验证为 2025 真题（无人机烟幕） |
| GitHub `zhanwen/MathModel/国赛论文/2023年优秀论文/` | 58 | 直接公开 PDF，A-F 题号齐全 |
| GitHub `Jackyleo-Zhao/cumcm-2025`（国二） | 1 | 2025 C 题 NIPT |

## 历史抽检记录

随机抽 3 篇官方展廊 PDF（2023-B226 / 2024-B195 / 2024-E218）第一页确认年份与文件名一致。2025-A196 第一页含“多情形下无人机烟幕遮蔽策略”，与当时核对的 2025 A 题一致。

## 已知限制

- 33 篇展廊重建 PDF 为图片型，`pdfplumber` 无法直接提取文字；历史 `ingest_papers.py` 流程因此只让可提取文本的论文参与统计；
- 本报告只描述当时的下载与抽检状态，不保证这些 PDF 当前仍保存在仓库或外部来源仍可访问；
- 历史统计不能自动替代当前写作、评分或引用 Authority。

## 归档工具位置

当时使用的下载脚本已归档到：

```text
legacy/tools/download_cumcm_papers.py
```

离线统计脚本位于：

```text
legacy/tools/ingest_papers.py
```

这些脚本不在默认运行时调用。只有在明确进行历史资料维护或复现时才人工使用，并应显式指定当前实际存在的输入/输出路径。
