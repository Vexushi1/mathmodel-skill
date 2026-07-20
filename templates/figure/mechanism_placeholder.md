# HSK 机理图合同与占位模板

## 1. 机理图合同表

| 图号 | 图名 | 对应问题 | 图的作用 | 图中对象 | 支撑公式/约束 | 评委质疑点 | 图等级 | 后期处理方式 |
|---|---|---|---|---|---|---|---|---|
| 图 X |  | 问题一 / 问题二 | mechanism / derivation / boundary / validation |  |  | 若无该图，评委可能质疑…… | S / A / B | SVG / PPT / GeoGebra / Python / 不画 |

## 2. DOCX 图位占坑模板

```text
【图 X 占位：图名】
对应问题：
图的作用：
图中对象：
支撑公式/约束：
Reviewer risk：
后期处理方式：
```

## 3. LaTeX 图位占坑模板

```latex
\begin{figure}[htbp]
\centering
\fbox{\parbox{0.82\textwidth}{\centering
图 X 占位：图名\\
作用：说明……机制\\
支撑公式：$...$\\
后期处理：SVG/PPT/GeoGebra 精修后替换
}}
\caption{图题}
\label{fig:placeholder_x}
\end{figure}
```
