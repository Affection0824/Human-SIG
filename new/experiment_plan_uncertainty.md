# 实验方案：基于不确定性传播的相关性分析 (Uncertainty-Propagated Correlation Analysis)

## 1. 动机 (Motivation)
当前的 Benchmark 评估通常将分数视为确定的“真值”(Fixed Truth)，并据此计算相关系数（Spearman $\rho$ / Kendall $\tau$）。然而，**审稿人指出**：
1.  **分数具有不确定性**：Benchmark 得分受题目数量（$N$）和采样误差影响（Standard Error），小样本 Benchmark（如 IOI $N=6$）的波动远大于大样本 Benchmark（如 MGSM $N=2500$）。
2.  **Elo 具有不确定性**：LMArena 的 Elo 分数本身是基于 Battle 胜率的估计值，也存在置信区间（Confidence Interval）。
3.  **排名不稳定性**：微小的分数波动可能导致排名（Rank）剧烈变化，进而导致相关系数虚高或虚低，产生“假阳性”显著结果。

因此，我们需要通过**传播不确定性 (Propagating Uncertainty)** 来重新评估相关系数的显著性，识别出那些在考虑测量误差后变得不再显著相关的 Benchmark。

## 2. 原理 (Principle)
本实验将采用 **蒙特卡洛模拟 (Monte Carlo Simulation)** 方法，不再使用单点估计值，而是从每个分数的**概率分布**中采样，模拟真实的测量误差。

### A. 不确定性建模 (Uncertainty Modeling)
我们将为两个变量分别建立误差模型：

1.  **Benchmark 分数 ($S$)**
    *   假设模型答题服从二项分布 $B(n, p)$，其中 $n$ 为题目总数，$p$ 为观测得分率。
    *   **标准误 (SE)**：$SE_{score} = \sqrt{\frac{p(1-p)}{n}}$
    *   **模拟分布**：$S_{sim} \sim \mathcal{N}(S_{obs}, SE_{score}^2)$
    *   *注：对于 $p=0$ 或 $p=1$ 的极端情况，我们将使用 Laplace 平滑 ($p = \frac{k+1}{n+2}$) 来避免零方差。*

2.  **LMArena Overall Elo ($E$)**
    *   Elo 分数通常服从正态分布。由于缺乏具体的 Battle Count 数据，我们采用 LMArena 官方报告的高分段模型典型标准误。
    *   **设定标准误**：$\sigma_{Elo} = 20$ (这是一个保守且合理的估计，通常高分段模型 CI 约为 $\pm 20-30$)。
    *   **模拟分布**：$E_{sim} \sim \mathcal{N}(E_{obs}, 20^2)$

### B. 相关系数的重采样 (Resampling Correlation)
对于每一对 (Benchmark, LMArena Overall)：
1.  进行 $K=2000$ 次模拟迭代。
2.  在每次迭代中：
    *   为该 Benchmark 下的所有模型，从其对应的分布中采样一组新的分数 $S'_{sim}$ 和 $E'_{sim}$。
    *   计算这组新数据的 Spearman $\rho$ 和 Kendall $\tau$。
3.  得到 $2000$ 个 $\rho$ 和 $\tau$ 的分布。

## 3. 解决问题的理由 (Why This Solves the Problem)
1.  **捕捉小样本波动**：对于题目少（$N$ 小）的 Benchmark（如 IOI, HMMT），其 $SE_{score}$ 会很大，导致模拟出的排名经常发生变动。如果一个 Benchmark 的高相关性完全依赖于运气（即少数几个题目的做对与否），那么在模拟中它的相关系数分布将非常宽，导致置信区间包含 0。
2.  **更严格的显著性检验**：原始 p-value 假设数据是确定的。新的方法通过构建 **95% 经验置信区间 (Empirical CI)**，只有当 95% 的模拟结果都显示相关（即 CI 不包含 0）时，我们才认为它是显著的。
3.  **直接回应审稿人**：这正是审稿人建议的 "Propagate uncertainty ... rather than treating ranks as fixed truth"。

## 4. 具体步骤 (Step-by-Step Plan)

### 步骤 1: 数据准备
*   读取 `master_correlation_matrix.csv` 获取所有模型的分数。
*   读取 `analysis_ready_data.csv` 获取每个 Benchmark 的 **题目数量 (question_count)**（用于计算 $SE_{score}$）。
*   读取 `metadata.json` (可选) 辅助确认 Benchmark 信息。

### 步骤 2: 编写模拟核心代码 (`new/src/uncertainty_propagation_analysis.py`)
*   定义 `simulate_score(score, n_questions)` 函数：基于二项分布方差生成扰动分数。
*   定义 `simulate_elo(elo, sigma=20)` 函数：基于正态分布生成扰动 Elo。
*   主循环：
    *   遍历所有 Benchmark。
    *   对于每个 Benchmark，提取共同模型的 (Score, Elo) 对。
    *   执行 10000 次 Monte Carlo 采样。
    *   记录每次的 Spearman $\rho$ 和 Kendall $\tau$。

### 步骤 3: 统计与判定
*   计算 **Original p-value** (作为对比基准)。
*   计算 **Robust CI (95%)**：取模拟分布的 [2.5%, 97.5%] 分位数。
*   **判定逻辑**：
    *   **Robust Significant**: CI 的下界 > 0 (对于正相关)。
    *   **Status Change**: 标记那些 "Original Significant (p<0.05)" 但 "Robust Not Significant (CI includes 0)" 的 Benchmark。

### 步骤 4: 结果报告
*   生成 CSV: `new/results/uncertainty_analysis_results.csv`
*   生成图片: `new/results/figures/uncertainty_robustness_spearman.png`
*   生成 Markdown 报告: `new/results/uncertainty_analysis_report.md`，重点列出：
    1.  **“掉队”名单**：原本显著，现在不显著的 Benchmark。
    2.  **稳健名单**：即使考虑了噪声，依然高度相关的 Benchmark。

## 5. 预期交付物
1.  Python 脚本：`new/src/uncertainty_propagation_analysis.py`
2.  结果表格：`new/results/uncertainty_analysis_results.csv`
3.  分析报告：`new/results/uncertainty_analysis_report.md`
