# HSK Stage 07：LaTeX 论文写作协议


## v6.1.6 调整

写作阶段分为 DOCX 草稿和 LaTeX 终稿两步：

1. 先执行 `references/hsk_stage_08_docx_draft_writing.md`，输出 DOCX 草稿用于阅读、修改、批注和逻辑审查。
2. 当模型、结果、核心图表和正文逻辑锁定后，再执行 `references/hsk_stage_10_latex_final_writing.md`，生成 LaTeX 终稿。

禁止在模型尚未稳定时过早投入大量 LaTeX 排版精修。


## 模板原则

1. 国赛论文默认使用 `templates/latex/cumcm/cumcmthesis/`。
2. 不删除原 `cumcmthesis.cls`、`example.tex`、`example.pdf`。
3. 可复制 `templates/latex/cumcm/hsk/hsk_main.tex` 到项目 `paper/main.tex` 作为起稿文件。
4. 编译默认 `xelatex` 或 `latexmk -xelatex`。

## 默认论文结构

```text
摘要
关键词
一、问题重述
二、问题分析
三、模型假设与符号说明
四、数据预处理
五、模型建立与求解
六、模型检验
七、敏感性与鲁棒性分析
八、模型评价与改进
九、结论
参考文献
附录
```

## 摘要要求

摘要必须逐问概述：方法、模型、关键结果、结论。尽量给出具体数值，不放图表，不堆公式。

## 正文规则

- 每个公式必须服务于模型表达；
- 每张图表必须在正文附近解释；
- 图表引用使用 `\cref` 或 `\ref`；
- 表格优先三线表；
- 代码放附录，不放正文；
- 结论要回答题目问题，但不需要在正文建立题目覆盖表。

## LaTeX 审查

- 编译通过；
- 无未解析引用 `??`；
- 无缺图；
- 公式编号连续；
- 图表浮动位置可接受；
- 参考文献格式统一；
- 附录代码不破坏版面。


## 摘要反推检查

摘要定稿前必须使用 `templates/shared/hsk_abstract_result_checklist.md` 反推检查：

- 每个小问是否在摘要中出现；
- 是否给出核心方法；
- 可量化问题是否给出核心数值；
- 是否给出明确结论；
- 是否与正文和 `data_output/` 结果一致。