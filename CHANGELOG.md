# Changelog

## Current release: 6.4.0

### LaTeX-first default workflow

- 默认 `full_workflow` 从正式图表直接进入 LaTeX、AI 模板感清除、编译与终审，不再自动加载 DOCX。
- `docx` 路由、`writing_docx` 模块和 `docx` delivery scope 保留，仅由显式 Word/DOCX 请求触发。
- DOCX 不再是 LaTeX 的事实源或进入门槛；LaTeX 直接读取当前 `模型论文框架.md`、标准工作簿和已批准图表。

### Stable active filenames

- 新增 `PROJECT_INSTRUCTIONS.md`、`RUNTIME_ROUTER.md`、`SKILL_FILE_INDEX.md` 和 `TEMPLATE_INDEX.md` 作为稳定活动入口。
- 旧 `V622` 文件名保留为兼容指针，不再复制活动规则。
- `scripts/generate_indexes.py` 统一生成新索引、旧兼容指针和 `MANIFEST.sha256`。

### Compatibility

- 旧项目仍可显式执行 DOCX route 和 DOCX delivery scope。
- 目录、工作簿 Schema、项目状态字段、同步器 stale 语义和 Python—Excel—MATLAB 证据链保持兼容。
- 历史版本 Changelog 保留，不参与当前规则入口。
