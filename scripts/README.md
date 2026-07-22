# Scripts

- `lint_skill.py`：检查核心文件、YAML/JSON Schema、路由路径、活动模板、Python 语法、标准 MATLAB 绘图入口以及生成索引的一致性。
- `generate_indexes.py`：重建 `HSK_SKILL_FILE_INDEX_V622.md`、`HSK_TEMPLATE_INDEX_V622.md` 与 `MANIFEST.sha256`；发布或移动文件后必须运行。
- `hsk_check_artifact.py`：检查具体建模项目的代码职责、结果目录和图像命名。
- `hsk_pack_submission.py`：打包提交产物，并排除缓存与 LaTeX 辅助文件。
- `render_paper.py`：按 `core/compile_profiles.yaml` 编译既有 LaTeX 工程，支持 XeLaTeX/Biber 与 pdfLaTeX/BibTeX 配置。
- `prepare_cumcm_class.py`：对复制到项目目录的 CUMCM 类文件执行窄范围、幂等的字体回退补丁。

MATLAB 问题绘图入口统一使用 `q{x}_plot.m`，例如问题一为 `q1_plot.m`。规则色板只作为默认起点，可在问题脚本中按信息展示效率和变量语义调整。

推荐维护命令：

```bash
python scripts/generate_indexes.py
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
```

旧评分、下载与语料处理脚本位于 `legacy/`，不属于默认运行链路。
