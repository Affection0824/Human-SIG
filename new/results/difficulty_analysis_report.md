# 难度分析报告：顶尖模型与原始基准的对比

## 1. 选定模型 (Group 20)
选择了以下 Overall ELO >= 1420 的顶尖模型来计算新的难度分数：

- Anthropicclaude-sonnet-4-5-20250929-thinking-32k
- gemini-3-pro
- gpt-5.1

## 2. 选定 Benchmark (N=13)
这三个模型共同拥有的 Benchmark：

- Humanity's Last Exam
- IOI
- Terminal-Bench Hard
- SciCode
- FACTS
- IFBench
- AA-LCR
- LiveCodeBench
- tau2-Bench Telecom
- AIME
- GPQA Diamond
- MMLU-Pro
- MGSM

## 3. 难度对比
- **Original Difficulty**: 使用 Common Subset 模型 (ELO 1400-1430) 计算的原始难度。
- **Triplet Difficulty**: 使用选定的 3 个顶尖模型计算的新难度。
- **Diff**: Original - Triplet (正值表示顶尖模型觉得更容易)。

| Benchmark_Name       |   Original_Difficulty |   Triplet_Difficulty |   Diff |
|:---------------------|----------------------:|---------------------:|-------:|
| Humanity's Last Exam |                 89.47 |                80.33 |   9.14 |
| IOI                  |                 89.47 |                73.78 |  15.69 |
| Terminal-Bench Hard  |                 80.20 |                69.00 |  11.20 |
| SciCode              |                 62.74 |                54.00 |   8.74 |
| FACTS                |                 50.37 |                44.64 |   5.74 |
| IFBench              |                 54.11 |                43.33 |  10.78 |
| AA-LCR               |                 50.56 |                39.67 |  10.89 |
| LiveCodeBench        |                 34.58 |                29.33 |   5.25 |
| tau2-Bench Telecom   |                 50.32 |                29.33 |  20.98 |
| AIME                 |                 31.28 |                26.00 |   5.28 |
| GPQA Diamond         |                 25.40 |                20.67 |   4.73 |
| MMLU-Pro             |                 16.79 |                14.00 |   2.79 |
| MGSM                 |                  9.62 |                 6.25 |   3.37 |

## 4. 相关性分析
Original Difficulty 和 Triplet Difficulty 之间的 Pearson 相关系数：

- **Pearson 相关系数 (r)**: 0.9842
- **95% 置信区间**: [0.9466, 0.9954]
- **P-value**: 1.2621e-09
- **样本量**: 13

**结论**: 极强正相关。这表明即使由能力强得多的模型进行评估，Benchmark 的相对难度排序仍然高度一致，尽管绝对难度分数有所下降（分数上升）。
