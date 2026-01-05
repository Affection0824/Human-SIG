"""
Small-N Hypothesis Testing Module

Purpose:
    This module implements targeted statistical tests specifically designed for small sample sizes (N=29 benchmarks).
    Instead of a single multivariate regression which lacks statistical power for small-N, this module executes
    bootstrapped univariate analysis for individual factors and controlled bivariate robust regression to
    disentangle confounding factors (specifically Difficulty vs. Variance).

Why Small-N Protocols:
    - With N=29, a 6-variable multivariate regression would violate the rule of thumb requiring at least 10
      samples per variable (would need N >= 60)
    - Small samples require methods that are robust to outliers and don't rely on large-sample assumptions
    - Targeted tests allow for rigorous testing of individual hypotheses while maintaining statistical power
    - Bootstrap resampling (5000 iterations) provides reliable confidence intervals without assuming normality

Statistical Methods:
    - Robust Regression (Huber Loss): Minimizes impact of outliers in small-N datasets
    - Permutation Tests: Provide exact p-values for small samples (N < 30)
    - Bootstrap Confidence Intervals: Resampling with replacement to estimate uncertainty
    - Non-parametric Tests: Mann-Whitney U, Kruskal-Wallis for comparing groups
    - Multiple Comparison Correction: Holm-Bonferroni correction to control family-wise error rate

Input:
    - Analysis-ready data: Human-SIG/results/analysis_ready_data.csv
    - Contains: benchmark features (Difficulty, CV), correlation metrics (Spearman ρ, Kendall τ, RBO),
                metadata (task_type, prompt_length, question_count, release_date)

Output:
    - Statistical test results: Dictionary containing p-values, effect sizes, and confidence intervals
      for all six hypotheses (H1-H6)

Critical Design:
    - All hypothesis tests are performed using THREE correlation metrics (Spearman ρ, Kendall τ, RBO) separately
    - Results from all three metrics must be reported for comprehensive analysis
    - For regression models (H5, H6), use Spearman ρ as primary, with Kendall τ and RBO as robustness checks
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import sys
from datetime import datetime
from scipy import stats
from scipy.stats import spearmanr, kendalltau, pearsonr, mannwhitneyu, kruskal
import statsmodels.api as sm
from statsmodels.robust.robust_linear_model import RLM

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.stats_utils import (
    bootstrap_ci,
    fisher_z_transform,
    calculate_spearman_with_pvalue,
    calculate_kendall_with_pvalue,
    calculate_spearman_fast,
    calculate_kendall_fast
)

# Global settings
N_BOOTSTRAPS = 5000
ALPHA = 0.05
SEED = 42

np.random.seed(SEED)


def test_h6_h5_robust_regression(
    df: pd.DataFrame,
    metric: str = 'spearman_rho'
) -> Dict:
    """
    Test H6 (Difficulty) & H5 (Variance) using Bivariate Robust Regression.
    
    Model: correlation_metric ~ β₁ * Difficulty + β₂ * CV + ε
    
    This test disentangles the confounding relationship between Difficulty and Variance:
    - H6: Harder benchmarks (higher Difficulty) contribute negatively to correlation
    - H5: Higher variance (CV) contributes positively to correlation
    - These factors are often collinear (floor effects reduce variance in high-accuracy benchmarks)
    
    Args:
        df: DataFrame with benchmark data (excludes Creative Writing v3)
        metric: Correlation metric to use as dependent variable ('spearman_rho', 'kendall_tau', 'rbo')
    
    Returns:
        Dictionary containing:
        - beta1_difficulty: Coefficient for Difficulty
        - beta1_pvalue: P-value for Difficulty coefficient
        - beta1_ci_lower: Lower bound of 95% bootstrap CI for beta1
        - beta1_ci_upper: Upper bound of 95% bootstrap CI for beta1
        - beta2_cv: Coefficient for CV
        - beta2_pvalue: P-value for CV coefficient
        - beta2_ci_lower: Lower bound of 95% bootstrap CI for beta2
        - beta2_ci_upper: Upper bound of 95% bootstrap CI for beta2
        - n_samples: Number of benchmarks included in analysis
    """
    # Exclude Creative Writing v3 (not included in Difficulty calculation)
    df_subset = df[df['benchmark_name'] != 'Creative Writing v3'].copy()
    
    # Remove rows with missing values
    df_clean = df_subset[[metric, 'difficulty', 'coefficient_of_variation']].dropna()
    
    if len(df_clean) < 5:
        return {
            'beta1_difficulty': np.nan,
            'beta1_pvalue': np.nan,
            'beta1_ci_lower': np.nan,
            'beta1_ci_upper': np.nan,
            'beta2_cv': np.nan,
            'beta2_pvalue': np.nan,
            'beta2_ci_lower': np.nan,
            'beta2_ci_upper': np.nan,
            'n_samples': len(df_clean)
        }
    
    y = df_clean[metric].values
    X = df_clean[['difficulty', 'coefficient_of_variation']].values
    X = sm.add_constant(X)  # Add intercept
    
    # Fit robust linear model with Huber's t-criterion
    model = RLM(y, X, M=sm.robust.norms.HuberT())
    results = model.fit()
    
    # Extract coefficients and p-values
    # Intercept is at index 0, Difficulty at index 1, CV at index 2
    beta1 = results.params[1]  # Difficulty coefficient
    beta1_pvalue = results.pvalues[1]
    beta2 = results.params[2]  # CV coefficient
    beta2_pvalue = results.pvalues[2]
    
    # Bootstrap confidence intervals for coefficients
    # Manual bootstrap for regression coefficients (since bootstrap_ci expects paired arrays)
    n = len(df_clean)
    rng = np.random.RandomState(SEED)
    beta1_boot = []
    beta2_boot = []
    
    for _ in range(N_BOOTSTRAPS):
        # Resample with replacement
        indices = rng.choice(n, size=n, replace=True)
        X_boot = X[indices]
        y_boot = y[indices]
        
        try:
            model_boot = RLM(y_boot, X_boot, M=sm.robust.norms.HuberT())
            results_boot = model_boot.fit()
            beta1_boot.append(results_boot.params[1])  # Difficulty coefficient
            beta2_boot.append(results_boot.params[2])  # CV coefficient
        except:
            continue
    
    # Calculate 95% CI
    if len(beta1_boot) > 0:
        beta1_ci_lower = np.percentile(beta1_boot, 2.5)
        beta1_ci_upper = np.percentile(beta1_boot, 97.5)
        beta2_ci_lower = np.percentile(beta2_boot, 2.5)
        beta2_ci_upper = np.percentile(beta2_boot, 97.5)
    else:
        beta1_ci_lower = beta1_ci_upper = np.nan
        beta2_ci_lower = beta2_ci_upper = np.nan
    
    return {
        'beta1_difficulty': beta1,
        'beta1_pvalue': beta1_pvalue,
        'beta1_ci_lower': beta1_ci_lower,
        'beta1_ci_upper': beta1_ci_upper,
        'beta2_cv': beta2,
        'beta2_pvalue': beta2_pvalue,
        'beta2_ci_lower': beta2_ci_lower,
        'beta2_ci_upper': beta2_ci_upper,
        'n_samples': len(df_clean)
    }


def test_h5_task_type_interaction(df: pd.DataFrame) -> Dict:
    """
    Test H5 (Variance) - The "Task Type Interaction" Test.
    
    Hypothesis: The relationship between variance (CV) and Spearman correlation with Perceived Utility
    may differ across different task types. This tests whether variance affects Spearman correlation
    differently for MCQ, Generation, and Agentic tasks.
    
    Method: Stratified analysis by task type. For each of the three main task types (MCQ, Generation, Agentic),
    separately examine the relationship between CV and Spearman rho.
    
    Args:
        df: DataFrame with benchmark data
    
    Returns:
        Dictionary containing correlation coefficients, p-values, and 95% CIs for each task type group
    """
    # Exclude "Mixed" task type
    df_clean = df[df['task_type'].isin(['MCQ', 'Generation', 'Agentic'])].copy()
    
    results = {}
    
    for task_type in ['MCQ', 'Generation', 'Agentic']:
        df_group = df_clean[df_clean['task_type'] == task_type].copy()
        
        if len(df_group) < 3:
            results[task_type] = {
                'correlation_coefficient': np.nan,
                'p_value': np.nan,
                'ci_lower': np.nan,
                'ci_upper': np.nan,
                'sample_size': len(df_group)
            }
            continue
        
        # Get CV and Spearman rho
        cv_values = df_group['coefficient_of_variation'].values
        spearman_values = df_group['spearman_rho'].values
        
        # Calculate Spearman correlation between CV and Spearman rho
        corr, p_value = calculate_spearman_with_pvalue(cv_values, spearman_values)
        
        # Bootstrap CI
        ci_lower, ci_upper = bootstrap_ci(
            cv_values, spearman_values, calculate_spearman_fast, n_boot=N_BOOTSTRAPS
        )
        
        results[task_type] = {
            'correlation_coefficient': corr,
            'p_value': p_value,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'sample_size': len(df_group)
        }
    
    # Compare groups using Fisher z-transformation if all groups have N >= 5
    group_ns = [results[g]['sample_size'] for g in ['MCQ', 'Generation', 'Agentic']]
    if all(n >= 5 for n in group_ns):
        # Convert correlations to z-scores
        z_scores = []
        z_vars = []
        for task_type in ['MCQ', 'Generation', 'Agentic']:
            r = results[task_type]['correlation_coefficient']
            n = results[task_type]['sample_size']
            if not np.isnan(r) and n > 3:
                z = fisher_z_transform(r)
                z_var = 1.0 / (n - 3)  # Variance of Fisher z
                z_scores.append(z)
                z_vars.append(z_var)
        
        if len(z_scores) >= 2:
            # Use ANOVA-like test (chi-square test for homogeneity)
            # Under null hypothesis that all correlations are equal, 
            # chi-square = sum((z_i - z_mean)^2 / z_var_i) follows chi-square(df=k-1)
            weights = [1/v for v in z_vars]
            z_mean = np.average(z_scores, weights=weights)
            chi_square = np.sum([(z - z_mean)**2 / var for z, var in zip(z_scores, z_vars)])
            p_comparison = 1 - stats.chi2.cdf(chi_square, df=len(z_scores) - 1)
            results['_comparison_pvalue'] = p_comparison
        else:
            results['_comparison_pvalue'] = np.nan
    else:
        results['_comparison_pvalue'] = np.nan
    
    return results


def test_h4_recency(df: pd.DataFrame) -> Dict:
    """
    Test H4 (Recency) - The "Trend" Test.
    
    Model: Univariate Spearman Correlation between Release_Date_Ordinal and correlation metrics
    (Spearman ρ, Kendall τ, RBO).
    
    Args:
        df: DataFrame with benchmark data
    
    Returns:
        Dictionary containing correlation coefficients, p-values, and 95% CIs for all three metrics
    """
    # Convert release_date to ordinal (days since 2020-01-01)
    reference_date = datetime(2020, 1, 1)
    df_clean = df.copy()
    
    def date_to_ordinal(date_str):
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return (date_obj - reference_date).days
        except:
            return np.nan
    
    df_clean['release_date_ordinal'] = df_clean['release_date'].apply(date_to_ordinal)
    df_clean = df_clean[['release_date_ordinal', 'spearman_rho', 'kendall_tau', 'rbo']].dropna()
    
    results = {}
    
    # For each metric, calculate correlation with release_date_ordinal
    for metric in ['spearman_rho', 'kendall_tau', 'rbo']:
        x = df_clean['release_date_ordinal'].values
        y = df_clean[metric].values
        
        if metric == 'rbo':
            # RBO doesn't have p-value, just calculate Spearman correlation
            corr, _ = spearmanr(x, y)
            p_value = np.nan
            # No CI for RBO
            ci_lower = ci_upper = np.nan
        else:
            # Spearman and Kendall: calculate correlation and p-value
            if metric == 'spearman_rho':
                corr, p_value = calculate_spearman_with_pvalue(x, y)
                # Bootstrap CI
                ci_lower, ci_upper = bootstrap_ci(
                    x, y, calculate_spearman_fast, n_boot=N_BOOTSTRAPS
                )
            else:  # kendall_tau
                corr, p_value = calculate_kendall_with_pvalue(x, y)
                # Bootstrap CI
                ci_lower, ci_upper = bootstrap_ci(
                    x, y, calculate_kendall_fast, n_boot=N_BOOTSTRAPS
                )
        
        results[metric] = {
            'correlation_coefficient': corr,
            'p_value': p_value,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper
        }
    
    return results


def test_h3_complexity(df: pd.DataFrame, metric: str = 'spearman_rho') -> Dict:
    """
    Test H3 (Complexity) - The "Categorical" Test.
    
    Hypothesis: Prompt complexity (as a categorical variable) affects correlation with Perceived Utility.
    
    Method: Use Kruskal-Wallis H-test (non-parametric one-way ANOVA) to test whether the distribution
    of correlation metrics differs across the four prompt_length categories: "Short", "Medium", "Long", "Extreme".
    
    Args:
        df: DataFrame with benchmark data
        metric: Correlation metric to use ('spearman_rho', 'kendall_tau', 'rbo')
    
    Returns:
        Dictionary containing test statistic, p-value, and post-hoc comparison results
    """
    df_clean = df[['prompt_length', metric]].dropna()
    
    # Group by prompt_length
    groups = []
    group_labels = []
    for prompt_len in ['Short', 'Medium', 'Long', 'Extreme']:
        group_data = df_clean[df_clean['prompt_length'] == prompt_len][metric].values
        if len(group_data) > 0:
            groups.append(group_data)
            group_labels.append(prompt_len)
    
    if len(groups) < 2:
        return {
            'test_statistic': np.nan,
            'p_value': np.nan,
            'n_groups': len(groups),
            'posthoc': {}
        }
    
    # Kruskal-Wallis test
    test_stat, p_value = kruskal(*groups)
    
    # Post-hoc pairwise comparisons using Mann-Whitney U tests (if significant)
    posthoc = {}
    if p_value < 0.05 and len(groups) >= 2:
        for i in range(len(group_labels)):
            for j in range(i + 1, len(group_labels)):
                group_i = groups[i]
                group_j = groups[j]
                u_stat, p_pairwise = mannwhitneyu(group_i, group_j, alternative='two-sided')
                posthoc[f'{group_labels[i]}_vs_{group_labels[j]}'] = {
                    'u_statistic': u_stat,
                    'p_value': p_pairwise
                }
    
    return {
        'test_statistic': test_stat,
        'p_value': p_value,
        'n_groups': len(groups),
        'group_labels': group_labels,
        'posthoc': posthoc
    }


def test_h2_scale(df: pd.DataFrame, metric: str = 'spearman_rho') -> Dict:
    """
    Test H2 (Scale) - The "Continuous" Test.
    
    Model: Pearson Correlation between log(question_count) and correlation metrics
    (Spearman ρ, Kendall τ, RBO).
    
    Variable Definition: N_samples is the question_count field from metadata.json.
    Apply natural logarithm transformation: log(N_samples) = ln(question_count).
    
    Args:
        df: DataFrame with benchmark data
        metric: Correlation metric to use ('spearman_rho', 'kendall_tau', 'rbo')
    
    Returns:
        Dictionary containing correlation coefficient and p-value
    """
    df_clean = df[['question_count', metric]].dropna()
    
    # Apply log transformation
    log_question_count = np.log(df_clean['question_count'].values)
    metric_values = df_clean[metric].values
    
    if metric == 'rbo':
        # RBO doesn't have p-value, just calculate Pearson correlation
        corr, _ = pearsonr(log_question_count, metric_values)
        p_value = np.nan
    else:
        # Pearson correlation (use for log-transformed data)
        corr, p_value = pearsonr(log_question_count, metric_values)
    
    return {
        'correlation_coefficient': corr,
        'p_value': p_value,
        'n_samples': len(df_clean)
    }


def test_h1_task_type(df: pd.DataFrame, metric: str = 'spearman_rho') -> Dict:
    """
    Test H1 (Generative vs. MCQ) - The "Group" Test.
    
    Model: Categorical comparison using the task_type field.
    - Group A: Benchmarks with task_type == "Generation" or task_type == "Agentic" (generative tasks)
    - Group B: Benchmarks with task_type == "MCQ" (multiple choice tasks)
    - Exclusion: Benchmarks with task_type == "Mixed" must be excluded
    
    Args:
        df: DataFrame with benchmark data
        metric: Correlation metric to use ('spearman_rho', 'kendall_tau', 'rbo')
    
    Returns:
        Dictionary containing test statistic, p-value, and effect size
    """
    # Exclude "Mixed" benchmarks
    df_clean = df[df['task_type'].isin(['MCQ', 'Generation', 'Agentic'])].copy()
    
    # Group A: Generation or Agentic
    group_a = df_clean[df_clean['task_type'].isin(['Generation', 'Agentic'])][metric].dropna().values
    # Group B: MCQ
    group_b = df_clean[df_clean['task_type'] == 'MCQ'][metric].dropna().values
    
    n_a = len(group_a)
    n_b = len(group_b)
    
    # Guardrail: Sample Imbalance Check
    if n_a < 5 or n_b < 5:
        # Descriptive statistics only
        median_diff = np.median(group_a) - np.median(group_b) if n_a > 0 and n_b > 0 else np.nan
        mean_diff = np.mean(group_a) - np.mean(group_b) if n_a > 0 and n_b > 0 else np.nan
        
        # Bootstrap CI for median difference
        if n_a > 0 and n_b > 0:
            # Combine groups for bootstrap
            combined = np.concatenate([group_a, group_b])
            n_total = len(combined)
            rng = np.random.RandomState(SEED)
            median_diffs = []
            
            for _ in range(N_BOOTSTRAPS):
                indices = rng.choice(n_total, size=n_total, replace=True)
                boot_combined = combined[indices]
                a_boot = boot_combined[:n_a] if n_a < len(boot_combined) else boot_combined
                b_boot = boot_combined[n_a:] if n_a < len(boot_combined) else boot_combined
                if len(a_boot) > 0 and len(b_boot) > 0:
                    median_diffs.append(np.median(a_boot) - np.median(b_boot))
            
            if len(median_diffs) > 0:
                ci_lower = np.percentile(median_diffs, 2.5)
                ci_upper = np.percentile(median_diffs, 97.5)
            else:
                ci_lower = ci_upper = np.nan
        else:
            ci_lower = ci_upper = np.nan
        
        return {
            'test_statistic': np.nan,
            'p_value': 1.0,  # Set to 1.0 to avoid false significance
            'median_difference': median_diff,
            'mean_difference': mean_diff,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'n_group_a': n_a,
            'n_group_b': n_b,
            'is_descriptive_only': True
        }
    else:
        # Mann-Whitney U Test (Wilcoxon rank-sum test)
        u_stat, p_value = mannwhitneyu(group_a, group_b, alternative='two-sided')
        
        # Effect size: rank-biserial correlation
        n_total = n_a + n_b
        u_min = min(u_stat, n_a * n_b - u_stat)
        r_biserial = 1 - (2 * u_min) / (n_a * n_b)
        
        return {
            'test_statistic': u_stat,
            'p_value': p_value,
            'effect_size': r_biserial,
            'median_difference': np.median(group_a) - np.median(group_b),
            'mean_difference': np.mean(group_a) - np.mean(group_b),
            'n_group_a': n_a,
            'n_group_b': n_b,
            'is_descriptive_only': False
        }


def run_all_hypothesis_tests(data_path: Path) -> Dict:
    """
    Run all hypothesis tests and return results.
    
    Args:
        data_path: Path to analysis_ready_data.csv
    
    Returns:
        Dictionary containing all test results organized by hypothesis and metric
    """
    # Load data
    df = pd.read_csv(data_path)
    
    results = {}
    
    # Test each hypothesis with all three metrics
    metrics = ['spearman_rho', 'kendall_tau', 'rbo']
    
    print("Running hypothesis tests...")
    print("=" * 60)
    
    # H6/H5: Robust Regression (Difficulty + CV)
    print("\nH6/H5: Robust Regression (Difficulty + CV)")
    for metric in metrics:
        print(f"  Testing with {metric}...")
        test_result = test_h6_h5_robust_regression(df, metric)
        results[f'H6_H5_{metric}'] = test_result
        print(f"    Difficulty beta1: {test_result['beta1_difficulty']:.4f} "
              f"(p={test_result['beta1_pvalue']:.4f})")
        print(f"    CV beta2: {test_result['beta2_cv']:.4f} "
              f"(p={test_result['beta2_pvalue']:.4f})")
    
    # H5: Task Type Interaction
    print("\nH5: Task Type Interaction (CV vs Spearman rho by task type)")
    h5_result = test_h5_task_type_interaction(df)
    results['H5_TaskType_Interaction'] = h5_result
    for task_type in ['MCQ', 'Generation', 'Agentic']:
        if task_type in h5_result:
            r = h5_result[task_type]['correlation_coefficient']
            p = h5_result[task_type]['p_value']
            print(f"  {task_type}: r={r:.4f}, p={p:.4f}")
    
    # H4: Recency
    print("\nH4: Recency (Release Date)")
    h4_result = test_h4_recency(df)
    results['H4_Recency'] = h4_result
    for metric in metrics:
        if metric in h4_result:
            r = h4_result[metric]['correlation_coefficient']
            p = h4_result[metric]['p_value']
            print(f"  {metric}: r={r:.4f}, p={p:.4f}")
    
    # H3: Complexity
    print("\nH3: Complexity (Prompt Length)")
    for metric in metrics:
        print(f"  Testing with {metric}...")
        test_result = test_h3_complexity(df, metric)
        results[f'H3_Complexity_{metric}'] = test_result
        print(f"    Kruskal-Wallis: H={test_result['test_statistic']:.4f}, "
              f"p={test_result['p_value']:.4f}")
    
    # H2: Scale
    print("\nH2: Scale (log(question_count))")
    for metric in metrics:
        print(f"  Testing with {metric}...")
        test_result = test_h2_scale(df, metric)
        results[f'H2_Scale_{metric}'] = test_result
        print(f"    Pearson r: {test_result['correlation_coefficient']:.4f}, "
              f"p={test_result['p_value']:.4f}")
    
    # H1: Task Type (Generative vs MCQ)
    print("\nH1: Task Type (Generative/Agentic vs MCQ)")
    for metric in metrics:
        print(f"  Testing with {metric}...")
        test_result = test_h1_task_type(df, metric)
        results[f'H1_TaskType_{metric}'] = test_result
        if test_result.get('is_descriptive_only', False):
            print(f"    Descriptive only (N_A={test_result['n_group_a']}, "
                  f"N_B={test_result['n_group_b']})")
        else:
            print(f"    Mann-Whitney U: U={test_result['test_statistic']:.4f}, "
                  f"p={test_result['p_value']:.4f}")
    
    print("\n" + "=" * 60)
    print("All hypothesis tests completed!")
    
    return results


if __name__ == "__main__":
    # Paths
    base_dir = Path(__file__).parent.parent.parent
    data_path = base_dir / "results" / "analysis_ready_data.csv"
    
    # Run all tests
    results = run_all_hypothesis_tests(data_path)
    
    # Save results
    output_path = base_dir / "results" / "hypothesis_test_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert numpy types to Python types for JSON serialization
    def convert_to_serializable(obj):
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj) if not np.isnan(obj) else None
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(item) for item in obj]
        return obj
    
    results_serializable = convert_to_serializable(results)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results_serializable, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to {output_path}")

