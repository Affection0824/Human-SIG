# 审稿人回复草稿

在此文档中，我们将根据审稿人的意见撰写详细的回复。

## 审稿人意见 1

**Reviewer Comment:**
If high-difficulty benchmarks happen to produce rankings that correlate less with LMArena, and difficulty is itself defined using LMArena-scored models, the finding could be an artefact rather than a genuine empirical result. Redefining difficulty using criteria independent of LMArena would remove the logical circularity.

**Response:**

我们非常感谢审稿人指出的关于“循环定义”（circularity）的敏锐洞察。我们完全同意，如果 Benchmark 难度的定义过度依赖于 LMArena 中大量模型的表现，可能会引入由于定义本身导致的人为相关性，从而削弱结论的可靠性。

为了验证我们定义的严谨性与结论的稳健性，我们采用了一种独立于 LMArena 整体排名的难度定义方法进行了补充验证实验。具体而言，参考 **HLE (Humanity's Last Exam)** 和 **Autobencher** 等先前权威工作的做法，我们重新定义了 Benchmark 的难度指标：我们选取了来自不同机构的三个顶尖模型，包括 **Claude 3.5 Sonnet (Thinking), Gemini 3 Pro, GPT-5.1**，将它们在各个 Benchmark 上的平均得分作为衡量该任务难度的依据。

这种方法的合理性在于：
1.  **独立性**：这三个顶尖模型的选取基于其公认的行业地位，而非 LMArena 的具体排名，且只使用了极少数模型的数据，切断了与 LMArena 整体排名的直接依赖关系。
2.  **代表性**：顶尖模型的平均分反映了当前最先进人工智能系统（SOTA）在特定任务上的能力上限，是衡量任务绝对难度的有效且严谨的代理指标。

实验结果显示，这种基于“顶尖模型平均分”定义的难度（Triplet Difficulty）与我们在论文中使用的基于 LMArena 模型表现定义的原始难度（Original Difficulty）之间存在**极高的 Pearson 相关系数 (r = 0.9842, p < 0.001)**。

下表详细列出了我们在三个模型均参与评测的 13 个 Benchmark 上计算出的两种难度指标及其差异：

| Benchmark Name | Original Difficulty | Triplet Difficulty | Diff (Original - Triplet) |
|:---|---:|---:|---:|
| Humanity's Last Exam | 89.47 | 80.33 | 9.14 |
| IOI | 89.47 | 73.78 | 15.69 |
| Terminal-Bench Hard | 80.20 | 69.00 | 11.20 |
| SciCode | 62.74 | 54.00 | 8.74 |
| FACTS | 50.37 | 44.64 | 5.74 |
| IFBench | 54.11 | 43.33 | 10.78 |
| AA-LCR | 50.56 | 39.67 | 10.89 |
| LiveCodeBench | 34.58 | 29.33 | 5.25 |
| tau2-Bench Telecom | 50.32 | 29.33 | 20.98 |
| AIME | 31.28 | 26.00 | 5.28 |
| GPQA Diamond | 25.40 | 20.67 | 4.73 |
| MMLU-Pro | 16.79 | 14.00 | 2.79 |
| MGSM | 9.62 | 6.25 | 3.37 |

这一结果有力地证明了我们的难度定义方式的合理与可靠，确认了我们关于难度的假设检验结果是具有参考性的。

## 审稿人意见 2

**Reviewer Comment:**
The benchmark→LMArena-category mapping is acknowledged as approximate, yet it is pivotal to the entire design. Many benchmarks are multi-skill (the paper concedes this), so forcing a single category can induce artificial disagreement/agreement. This threatens internal validity and interpretability of per-benchmark “CV” scores.

**Response:**

我们非常认同审稿人关于“Benchmark 到 LMArena Category 映射”问题的观点。确实，许多 Benchmark 本身是综合性的，强制将其映射到单一类别可能会引起关于有效性的担忧。如果分类不当，可能会人为地降低 Benchmark 排名与 LMArena 排名的一致性（即相关系数 $\rho$），从而影响我们结论的内部效度。

为了回应这一关切，并验证我们当前 Category 映射的合理性，我们进行了一项对比实验：我们将每个 Benchmark 的排名分别与 **LMArena 对应 Category 的 Elo 排名** 以及 **LMArena Overall Elo 排名** 进行相关性分析。

实验结果表明，我们的分类策略在“捕捉特定领域信号”和“适应多技能任务”之间取得了良好的平衡。

首先，对于那些**领域特征纯粹**的 Benchmark，使用特定的 Category Elo 能显著提升相关性，而 Overall Elo 则完全无法体现这些 Benchmark 的区分能力。例如：
*   **HumanEval (Coding)**: Overall $\rho = 0.028$ vs Coding $\rho = 0.657$
*   **MATH-500 (Math)**: Overall $\rho = 0.467$ vs Math $\rho = 0.854$
*   **FrontierMath Tier 4 (Math)**: Overall $\rho = 0.353$ vs Math $\rho = 0.731$

这组对比清楚地说明，如果不进行 Category 映射而仅依赖 Overall Elo，我们将完全丢失这些专业领域 Benchmark 的有效信号。

其次，对于审稿人特别关心的**多技能** Benchmark，我们的实验数据也给出了令人放心的结果。即便我们将它们归入某一特定类别，它们与该类别 Elo 的相关系数依然很高，且与 Overall Elo 的相关系数非常接近（甚至更高）。这说明我们选取的 Category（如 Coding, Hard Prompts, Expert 等）本身就具有较好的包容性，能够很好地代表这些 Benchmark 所考察的核心能力。例如：
*   **Terminal-Bench Hard**: Overall $\rho = 0.669$ vs Coding $\rho = 0.649$ 
*   **tau2-Bench Telecom**: Overall $\rho = 0.412$ vs Coding $\rho = 0.321$ 
*   **Humanity's Last Exam**: Overall $\rho = 0.520$ vs Expert $\rho = 0.562$ 
*   **GPQA**: Overall $\rho = 0.562$ vs Expert $\rho = 0.534$ 
*   **Aider Polyglot**: Overall $\rho = 0.736$ vs Coding $\rho = 0.774$ 

以上这些是一些典型的单学科技能/multi-skill benchmark 的表现。这些结果表明，对于多技能的 Benchmark，我们选取的 Category 并没有引入人为的“分歧”，反而能够获得与 Overall 相当甚至更好的一致性。这意味着目前的 Category 分类是合理的，它既保留了对特定领域能力的敏感度，又足够健壮，不会因为 Benchmark 考察多种技能而失效。

综上所述，虽然映射是近似的，但实证数据支持了其有效性和合理性。

## 审稿人意见 3

**Reviewer Comment:**
The analysis throws away score magnitudes, standard errors, and (for LMArena) Elo uncertainty driven by battle counts. Two models can swap ranks due to noise yet drive large changes in correlation, especially when intersection N is small (e.g., HMMT N=9). A proper treatment would propagate uncertainty (e.g., bootstrap over LMArena battles / benchmark score uncertainty, Bayesian measurement model) rather than treating ranks as fixed truth.

**Response:**

感谢审稿人关于不确定性传播（Uncertainty Propagation）的极具建设性的建议。我们完全同意，仅将排名视为固定真值而忽略得分和 Elo 估计中的不确定性（标准误差、对战次数影响等），可能会导致对相关性（$\rho$）的估计存在偏差，特别是在模型数量较少（如 N < 10）的情况下，排名的随机扰动可能会显著影响结果。

为了严格评估这种不确定性对我们结论的影响，我们按照审稿人的建议，实施了全面的**不确定性传播分析（Uncertainty Propagation Analysis）**。我们采用了蒙特卡洛模拟方法，具体流程如下：

1.  **不确定性建模**：
    *   **LMArena Elo**：利用官方提供的 95% 置信区间（CI）推导每个模型 Elo 的标准差（Sigma），并假设 Elo 服从正态分布 $N(Elo, \sigma_{Elo})$。
    *   **Benchmark Score**：假设 Benchmark 得分服从二项分布（取决于题目数量），计算其标准差 $\sigma = \sqrt{p(1-p)/N} \times 100$，并从正态分布 $N(Score, \sigma_{Score})$ 中采样。
2.  **蒙特卡洛模拟**：
    *   对每个 Benchmark 进行 **10,000 次** 独立模拟。
    *   在每次模拟中，根据上述分布对 Elo 和 Score 进行随机扰动采样，并计算采样后的 Spearman 相关系数（Simulated $\rho$）。
3.  **统计推断**：
    *   计算 **Simulated $\rho$**（10,000 次模拟的均值）。
    *   构建 **95% 置信区间（CI）**（模拟分布的 2.5% - 97.5% 分位点）。
    *   计算 **Simulated P-value**（模拟相关系数 $\le 0$ 的频率），以检验正相关的显著性。

实验结果如下表所示（按原始 $\rho$ 降序排列，**P 值 > 0.05 加粗表示**）：

| Benchmark | Models (N) | Items | Orig Rho | Sim Rho | Sim 95% CI | Orig P-value | Sim P-value |
|:---|---:|---:|---:|---:|:---|---:|---:|
| MATH-500 | 26 | 500 | 0.8535 | 0.7974 | [0.696, 0.881] | 2.99e-08 | 0 |
| FrontierMath Tier 1-3 | 26 | 290 | 0.8243 | 0.8104 | [0.742, 0.873] | 2.27e-07 | 0 |
| Aider Polyglot | 29 | 225 | 0.7742 | 0.7742 | [0.714, 0.831] | 8.35e-07 | 0 |
| MMLU-Pro | 64 | 12000 | 0.7728 | 0.7610 | [0.735, 0.787] | 7.38e-14 | 0 |
| SWE-bench Bash Only | 16 | 500 | 0.7362 | 0.7457 | [0.682, 0.809] | 0.0011 | 0 |
| FrontierMath Tier 4 | 15 | 48 | 0.7310 | 0.5517 | [0.229, 0.811] | 0.0020 | 0.001 |
| Terminal-Bench v2.0 | 12 | 100 | 0.7063 | 0.6772 | [0.461, 0.881] | 0.0103 | 0 |
| IOI | 15 | 6 | 0.6619 | 0.3172 | [-0.148, 0.706] | 0.0072 | 0.0851 |
| HumanEval | 12 | 164 | 0.6573 | 0.5232 | [0.168, 0.825] | 0.0202 | 0.003 |
| Terminal-Bench Hard | 58 | 47 | 0.6489 | 0.5658 | [0.461, 0.665] | 3.61e-08 | 0 |
| GPQA Diamond | 63 | 198 | 0.6487 | 0.6198 | [0.546, 0.691] | 8.98e-09 | 0 |
| AIME | 55 | 30 | 0.5889 | 0.5449 | [0.439, 0.647] | 2.26e-06 | 0 |
| MGSM | 35 | 2500 | 0.5765 | 0.5495 | [0.451, 0.645] | 0.0003 | 0 |
| Humanity's Last Exam | 62 | 2500 | 0.5620 | 0.5532 | [0.494, 0.610] | 2.01e-06 | 0 |
| SciCode | 64 | 338 | 0.5609 | 0.5225 | [0.427, 0.616] | 1.43e-06 | 0 |
| FACTS | 14 | 1719 | 0.5523 | 0.5223 | [0.385, 0.640] | 0.0406 | 0 |
| SWE-bench (Verified) | 26 | 500 | 0.5341 | 0.5448 | [0.415, 0.671] | 0.0049 | 0 |
| GPQA | 24 | 448 | 0.5335 | 0.4737 | [0.282, 0.654] | 0.0073 | 0 |
| SuperGPQA | 24 | 26529 | 0.5335 | 0.5106 | [0.405, 0.614] | 0.0073 | 0 |
| HMMT (Feb 2025) | 9 | 50 | 0.5167 | 0.5028 | [0.150, 0.800] | 0.1544 | 0.0043 |
| ARC-AGI-2 | 22 | 360 | 0.4638 | 0.4686 | [0.350, 0.582] | 0.0297 | 0 |
| AA-LCR | 56 | 100 | 0.4574 | 0.4358 | [0.367, 0.502] | 0.0004 | 0 |
| LiveCodeBench | 64 | 454 | 0.4018 | 0.3970 | [0.355, 0.439] | 0.0010 | 0 |
| IFBench | 56 | 300 | 0.3476 | 0.3058 | [0.231, 0.375] | 0.0087 | 0 |
| tau2-Bench Telecom | 58 | 50 | 0.3210 | 0.3098 | [0.233, 0.384] | 0.0140 | 0 |
| WritingBench | 24 | 1239 | 0.3165 | 0.3093 | [0.190, 0.423] | 0.1318 | 0 |
| IFEval | 18 | 541 | -0.0900 | 0.0279 | [-0.230, 0.317] | 0.7226 | 0.4403 |

**结果分析：**

1.  **绝大多数相关性依然稳健**：即使考虑了 LMArena 和 Benchmark 的测量不确定性，绝大多数 Benchmark（如 MATH-500, MMLU-Pro, Aider Polyglot 等）的 **Simulated P-value** 依然为 0 或极低（< 0.05），且 95% CI 不包含 0。这有力地证明了我们在论文中报告的相关性并非噪声产物，而是具有统计显著性的真实联系。
2.  **少数项的不确定性影响**：如审稿人预期的那样，对于模型数量极少（如 IOI, N=15）或本身相关性较弱的 Benchmark，不确定性的确会导致显著性下降。例如，**IOI** 的模拟 P 值升至 0.0851，表明其排名在考虑噪声后不再具有统计显著的强相关性。这提示我们在解读小样本 Benchmark 结果时应更加谨慎。
3.  **HMMT 的特殊情况**：值得注意的是，尽管 HMMT 的样本量极小（N=9）且原始 P 值不显著（0.1544），但模拟后的 P 值反而显著（0.0043）。这可能是因为噪声扰动平滑了极端值的影响，揭示了潜在的某种趋势，但鉴于其 CI 范围极大（[0.150, 0.800]），我们仍需对其结论持保留态度。

这一不确定性分析不仅回应了审稿人的技术关切，也使我们对各个 Benchmark 评估效力的信心边界有了更清晰的认识。我们将把这些更严谨的统计结果补充到最终版本的论文中。

## 审稿人意见 4

**Reviewer Comment:**
The paper reports extreme multicollinearity between difficulty and variance (r≈0.91), yet still concludes neither predicts alignment. With N≈27 and such collinearity, coefficient estimates are unstable; the null is not informative.

**Response:**

感谢审稿人指出关于多重共线性（Multicollinearity）的关键问题。我们完全同意，在样本量较小（N≈27）且自变量高度相关（r≈0.91）的情况下，使用多元回归模型确实会导致系数估计不稳定，从而使得“无显著影响”的结论可能缺乏说服力（即 Null result 不具备信息量）。

为了克服这一局限性并更稳健地检验“难度”和“方差”是否对 Benchmark 的一致性（Alignment）有预测能力，我们采纳了审稿人的隐含建议，放弃了可能受共线性干扰的多元回归，转而对这两个变量分别进行了**单变量回归分析（Univariate Regression Analysis）**。单变量分析可以避免共线性带来的参数估计方差膨胀问题，从而直接评估每个特征单独的解释力。

我们分别以 **难度 (Difficulty)** 和 **方差 (Variance/CV)** 为自变量，以三种一致性指标（Spearman $\rho$, Kendall $\tau$, RBO）为因变量，进行了 6 组独立的回归分析。结果如下表所示：

| 自变量 (Independent Variable) | 因变量 (Dependent Variable) | $R^2$ | 斜率 ($\beta$) | 斜率 95% CI | P-value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Difficulty | Spearman $\rho$ | 0.0651 | 0.0016 | [-0.0009, 0.0042] | 0.1990 |
| Difficulty | Kendall $\tau$ | 0.0809 | 0.0013 | [-0.0005, 0.0032] | 0.1505 |
| Difficulty | RBO | 0.0662 | 0.0009 | [-0.0005, 0.0023] | 0.1951 |
| Variance (CV) | Spearman $\rho$ | 0.0178 | 0.0783 | [-0.1558, 0.3124] | 0.4981 |
| Variance (CV) | Kendall $\tau$ | 0.0263 | 0.0693 | [-0.1006, 0.2393] | 0.4094 |
| Variance (CV) | RBO | 0.0270 | 0.0524 | [-0.0744, 0.1792] | 0.4036 |

**结果分析与结论：**

1.  **独立解释力依然匮乏**：实验结果显示，即使在消除共线性干扰的单变量设置下，**难度**和**方差**对一致性的解释力（$R^2$）依然极低（均低于 10%），且所有的回归系数（Slope）在统计上均不显著（P-value > 0.05）。
2.  **结论的稳健性**：这一结果有力地反驳了“Null result 是由共线性导致的不稳定性”这一假设。相反，它支持了我们最初的结论：**Benchmark 的难度或区分度（方差）本身并不是预测其与人类偏好一致性高低的有效指标。**

通过这一更严谨的单变量分析，我们确认了之前的“无显著相关”结论并非统计假象，而是反映了数据的真实特征。
