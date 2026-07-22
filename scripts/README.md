# Scripts

- `lint_skill.py`：检查核心文件、YAML/JSON Schema、路由路径、活动模板、Python 语法以及生成索引的一致性。
- `generate_indexes.py`：重建 `HSK_SKILL_FILE_INDEX_V622.md`、`HSK_TEMPLATE_INDEX_V622.md` 与 `MANIFEST.sha256`；发布或移动文件后必须运行。
- `hsk_check_artifact.py`：按题型检查具体建模项目的代码职责、结果目录、工作簿字段和图像命名。
- `hsk_pack_submission.py`：打包提交产物，并排除缓存与 LaTeX 辅助文件。
- `prepare_cumcm_class.py`：仅替换旧版 `cumcmthesis.cls` 中已审计的硬编码字体块，加入跨平台回退；重复运行不会二次修改，匹配异常时拒绝宽泛替换。
- `render_paper.py`：按 `core/compile_profiles.yaml` 编译既有 LaTeX 工程，支持 XeLaTeX/Biber 与 pdfLaTeX/BibTeX 配置；CUMCM 本地类文件存在时自动执行字体兼容补丁。

推荐维护命令：

```bash
python scripts/generate_indexes.py
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
```

CUMCM 独立准备命令：

```bash
python scripts/prepare_cumcm_class.py final_latex/cumcmthesis.cls
python scripts/render_paper.py final_latex --profile cumcm --clean
```

旧评分、下载与语料处理脚本位于 `legacy/`，不属于默认运行链路。
