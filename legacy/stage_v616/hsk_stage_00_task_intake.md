# HSK Stage 00：任务接入与工作区初始化

## 目标

快速确认竞赛类型、赛题材料、截止时间、团队分工和输出物要求；建立可复现工作区。除非信息缺失会影响方向判断，否则不反复追问。

## 必做动作

1. 识别竞赛：CUMCM / MCM / ICM / 电工杯 / 认证杯 / 其他。
2. 确认最终论文格式：默认 LaTeX；国赛中文论文默认 `cumcmthesis`。
3. 建立目录：

```text
project/
├── data/
├── code/
├── results/
│   ├── figures/
│   ├── tables/
│   ├── logs/
│   └── appendix/
├── paper/
│   ├── main.tex
│   ├── sections/
│   └── references.bib
└── state/
```

4. 初始化内部检查：题目要求覆盖、模型路线比较、数据字段审计、图表规划、鲁棒性检查。

## 输出

- 当前材料清单；
- 缺失材料清单；
- 推荐推进模式；
- 下一阶段审题安排。
