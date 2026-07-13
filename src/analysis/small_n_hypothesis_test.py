"""
Small-N Hypothesis Testing Script

Purpose:
    This script executes targeted statistical tests for each hypothesis (H1-H6) using
    methods appropriate for small sample sizes (N=28 benchmarks). Instead of a single
    multivariate regression which lacks statistical power, this script performs:
    - Bootstrapped Univariate Analysis for individual factors
    - Controlled Bivariate Robust Regression to disentangle confounding factors

Why Small-N Protocols:
    - N=28 is too small for a 6-variable regression (rule of thumb: 10 samples per variable)
    - Multivariate regression would have insufficient statistical power
    - Targeted tests allow rigorous testing of individual hypotheses while maintaining power

Statistical Methods:
    - H1: Mann-Whitney U test (categorical comparison: Generative vs MCQ)
    - H2: Pearson correlation (Scale: log(question_count) vs correlation metrics)
    - H3: Kruskal-Wallis H-test (Complexity: complexity categories)
    - H4: Spearman correlation (Recency: release_date vs correlation metrics)
    - H5/H6: Bivariate Robust Regression (Difficulty + CV vs correlation metrics)

Input:
    - analysis_ready_data.csv: Contains features and correlation coefficients for all benchmarks
    - metadata.json: Contains benchmark metadata

Output:
    - Statistical test results for all hypotheses (H1-H6)
    - Results stored in dictionary format for Step 4.4 (Holm-Bonferroni correction)
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from scipy import stats
from scipy.stats import mannwhitneyu, kruskal, pearsonr
import logging
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from stats_utils import (
    bootstrap_ci,
    huber_loss_regression
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global settings
N_BOOTSTRAPS = 5000
ALPHA = 0.05


def load_analysis_data(data_path: Path) -> pd.DataFrame:
    """
    Load analysis-ready data.
    
    Args:
        data_path: Path to analysis_ready_data.csv
        
    Returns:
        DataFrame with benchmark features and correlations
    """
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} benchmarks from analysis_ready_data.csv")
    return df


def test_h1_generative(df: pd.DataFrame) -> Dict:
    """
    Test H1: Generative vs MCQ task types.
    
    Uses Mann-Whitney U test to compare correlation distributions between:
    - Group A (Generative): task_type == "Generation" or "Agentic"
    - Group B (MCQ): task_type == "MCQ"
    
    Excludes "Mixed" task types.
    
    Args:
        df: Analysis-ready DataFrame
        
    Returns:
        Dictionary with test results for Spearman, Kendall, and RBO
    """
    logger.info("Testing H1: Generative vs MCQ")
    
    # Filter out "Mixed" task types
    df_filtered = df[df['task_type'] != 'Mixed'].copy()
    
    # Group A: Generative (includes both "Generation" and "Agentic")
    group_a = df_filtered[df_filtered['task_type'].isin(['Generation', 'Agentic'])].copy()
    
    # Group B: MCQ
    group_b = df_filtered[df_filtered['task_type'] == 'MCQ'].copy()
    
    n_a = len(group_a)
    n_b = len(group_b)
    
    logger.info(f"  Group A (Generative): N={n_a}")
    logger.info(f"  Group B (MCQ): N={n_b}")
    logger.info(f"  Excluded (Mixed): N={len(df) - n_a - n_b}")
    
    results = {}
    
    # Test for each correlation metric
    for metric in ['spearman_rho', 'kendall_tau', 'rbo']:
        if metric not in df_filtered.columns:
            continue
        
        group_a_values = group_a[metric].dropna().values
        group_b_values = group_b[metric].dropna().values
        
        if len(group_a_values) < 2 or len(group_b_values) < 2:
            logger.warning(f"  Insufficient data for {metric}")
            results[f'H1_{metric}'] = {
                'test_statistic': np.nan,
                'p_raw': np.nan,
                'effect_size': np.nan,
                'effect_size_type': 'median_difference',
                'n_a': len(group_a_values),
                'n_b': len(group_b_values)
            }
            continue
        
        # Mann-Whitney U test
        statistic, p_value = mannwhitneyu(
            group_a_values, group_b_values,
            alternative='two-sided'
        )
        
        # Effect size: median difference
        median_diff = np.median(group_a_values) - np.median(group_b_values)
        
        # Calculate rank-biserial correlation (effect size for Mann-Whitney)
        # r = 1 - (2U) / (n1 * n2), where U is the test statistic
        u_stat = min(statistic, n_a * n_b - statistic)
        rank_biserial = 1 - (2 * u_stat) / (n_a * n_b)
        
        results[f'H1_{metric}'] = {
            'test_statistic': statistic,
            'p_raw': p_value,
            'effect_size': median_diff,
            'effect_size_type': 'median_difference',
            'rank_biserial': rank_biserial,
            'n_a': n_a,
            'n_b': n_b,
            'median_a': np.median(group_a_values),
            'median_b': np.median(group_b_values)
        }
        
        logger.info(f"  {metric}: U={statistic:.2f}, p={p_value:.4f}, median_diff={median_diff:.3f}")
    
    return results


def test_h2_scale(df: pd.DataFrame) -> Dict:
    """
    Test H2: Scale effect (log(question_count) vs correlation metrics).
    
    Uses Pearson correlation between log(question_count) and correlation metrics.
    
    Args:
        df: Analysis-ready DataFrame
        
    Returns:
        Dictionary with test results for Spearman, Kendall, and RBO
    """
    logger.info("Testing H2: Scale effect")
    
    # Calculate log(question_count)
    df_test = df.copy()
    df_test['log_question_count'] = np.log(df_test['question_count'])
    
    results = {}
    
    # Test for each correlation metric
    for metric in ['spearman_rho', 'kendall_tau', 'rbo']:
        if metric not in df_test.columns:
            continue
        
        # Get paired data
        df_paired = df_test[['log_question_count', metric]].dropna()
        
        if len(df_paired) < 3:
            logger.warning(f"  Insufficient data for {metric}")
            results[f'H2_{metric}'] = {
                'correlation': np.nan,
                'p_raw': np.nan,
                'effect_size': np.nan,
                'effect_size_type': 'pearson_r',
                'sample_size': len(df_paired)
            }
            continue
        
        x = df_paired['log_question_count'].values
        y = df_paired[metric].values
        
        # Pearson correlation
        correlation, p_value = pearsonr(x, y)
        
        results[f'H2_{metric}'] = {
            'correlation': correlation,
            'p_raw': p_value,
            'effect_size': correlation,
            'effect_size_type': 'pearson_r',
            'sample_size': len(df_paired)
        }
        
        p_str = f"{p_value:.4f}" if pd.notna(p_value) else 'N/A'
        logger.info(f"  {metric}: r={correlation:.3f}, p={p_str}")
    
    return results


def test_h3_complexity(df: pd.DataFrame) -> Dict:
    """
    Test H3: High-complexity tasks (Evaluating, Creating) show lower correlation 
    than low-complexity tasks (Applying, Analyzing).
    
    Uses Kruskal-Wallis H-test for overall difference and 
    ordinal linear regression for the trend.
    """
    logger.info("Testing H3: Complexity Categories")
    
    base_dir = Path(__file__).parent.parent.parent
    metadata_path = base_dir / "data" / "metadata.json"
    
    # 1. Load data
    # Use the passed dataframe directly
    df_corr = df.copy()
    
    # 2. Load metadata
    complexity_map = {}
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            for entry in metadata:
                if 'benchmark_id' in entry and 'complexity' in entry:
                    complexity_map[entry['benchmark_id']] = entry['complexity']
    
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
    else:
        logger.warning(f"Metadata file not found at {metadata_path}")
        
    # 3. Map complexity
    df_test = df_corr.copy()
    df_test['complexity'] = df_test['benchmark_id'].map(complexity_map)
    
    # Filter out benchmarks without complexity
    df_test = df_test.dropna(subset=['complexity'])
    logger.info(f"  Analyzed {len(df_test)} benchmarks with complexity data")

    complexity_order = ['Applying', 'Analyzing', 'Evaluating', 'Creating']
    complexity_val = {c: i+1 for i, c in enumerate(complexity_order)}
    df_test['complexity_val'] = df_test['complexity'].map(complexity_val)
    
    results = {}
    
    # Exact metric definition
    metrics = {
        'Spearman': 'spearman_rho', 
        'Kendall': 'kendall_tau', 
        'RBO': 'rbo'
    }
    
    # Set style (matched to analyze_complexity.py)
    import seaborn as sns
    import matplotlib.pyplot as plt
    sns.set_theme(style="whitegrid")
    plt.rcParams['font.family'] = 'DejaVu Sans'

    # Test for each correlation metric
    for metric_name, metric_col in metrics.items():
        if metric_col not in df_test.columns:
             logger.warning(f"  Metric {metric_col} not found in data")
             continue
        
        # 1. Kruskal-Wallis Test
        groups = [df_test[df_test['complexity'] == c][metric_col].values for c in complexity_order]
        clean_groups = [g for g in groups if len(g) > 0]
        
        if len(clean_groups) < 2:
            logger.warning(f"  Insufficient groups for {metric_name}")
            continue
            
        kw_stat, kw_p = stats.kruskal(*clean_groups)
        
        # 2. Linear Regression (Ordinal)
        df_metric = df_test.dropna(subset=['complexity_val', metric_col])
        slope, intercept, r_value, p_value, std_err = stats.linregress(df_metric['complexity_val'], df_metric[metric_col])
        
        results[f'H3_{metric_col}'] = {
            'test_statistic': kw_stat,
            'p_raw': kw_p,
            'regression_p_value': p_value,
            'regression_slope': slope,
            'regression_r2': r_value**2,
            'effect_size': r_value**2,
            'effect_size_type': 'r_squared'
        }
        
        # 3. Plot
        plt.figure(figsize=(10, 6))
        
        # Boxplot
        sns.boxplot(
            x='complexity',
            y=metric_col,
            hue='complexity',
            data=df_test,
            order=complexity_order,
            hue_order=complexity_order,
            palette="Set2",
            showfliers=False,
            dodge=False,
            legend=False,
        )
        
        # Stripplot
        sns.stripplot(x='complexity', y=metric_col, data=df_test, order=complexity_order, color=".25", alpha=0.6)
        
        # Add regression line
        # Create x-values for regression line (0 to 3 for plotting, but regression used 1 to 4)
        x_vals = np.array([0, 3])
        y_vals = intercept + slope * (x_vals + 1) # +1 because complexity_val is 1-based
        
        plt.plot(x_vals, y_vals, color='red', linestyle='--', linewidth=2, label=f'Regression (p={p_value:.3f})')
        
        plt.title(f'{metric_name} Correlation by Complexity Level', fontsize=14)
        plt.xlabel('Complexity Level', fontsize=12)
        plt.ylabel(f'{metric_name} Correlation', fontsize=12)
        plt.legend()
        
        # Save plot - DISABLED to avoid redundancy
        # plot_path = output_dir / f'complexity_{metric_name.lower()}.png'
        # plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"  {metric_name}: KW p={kw_p:.4f}, Reg p={p_value:.4f}, Slope={slope:.4f}")
        # logger.info(f"  Saved plot to {plot_path}")
    
    return results


def test_h4_recency(df: pd.DataFrame) -> Dict:
    """
    Test H4: Recency effect (release_date vs correlation metrics).
    
    Uses Spearman correlation between release_date (ordinal) and correlation metrics.
    
    Args:
        df: Analysis-ready DataFrame
        
    Returns:
        Dictionary with test results for Spearman, Kendall, and RBO
    """
    logger.info("Testing H4: Recency effect")
    
    # Convert release_date to ordinal (days since reference date)
    df_test = df.copy()
    reference_date = datetime(2020, 1, 1)
    
    def date_to_ordinal(date_str):
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return (date_obj - reference_date).days
        except:
            return np.nan
    
    df_test['release_date_ordinal'] = df_test['release_date'].apply(date_to_ordinal)
    
    results = {}
    
    # Test for each correlation metric
    for metric in ['spearman_rho', 'kendall_tau', 'rbo']:
        if metric not in df_test.columns:
            continue
        
        # Get paired data
        df_paired = df_test[['release_date_ordinal', metric]].dropna()
        
        if len(df_paired) < 3:
            logger.warning(f"  Insufficient data for {metric}")
            results[f'H4_{metric}'] = {
                'correlation': np.nan,
                'p_raw': np.nan,
                'effect_size': np.nan,
                'effect_size_type': 'spearman_rho',
                'sample_size': len(df_paired)
            }
            continue
        
        x = df_paired['release_date_ordinal'].values
        y = df_paired[metric].values
        
        # Spearman correlation
        correlation, p_value = stats.spearmanr(x, y)
        
        # Calculate bootstrap CI
        def spearman_func(x_data, y_data):
            return stats.spearmanr(x_data, y_data)[0]
        
        ci_lower, ci_upper = bootstrap_ci(x, y, spearman_func, n_boot=5000)
        
        results[f'H4_{metric}'] = {
            'correlation': correlation,
            'p_raw': p_value,
            'effect_size': correlation,
            'effect_size_type': 'spearman_rho',
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'sample_size': len(df_paired)
        }
        
        p_str = f"{p_value:.4f}" if pd.notna(p_value) and metric != 'rbo' else 'N/A'
        logger.info(f"  {metric}: ρ={correlation:.3f}, p={p_str}")
    
    return results


def test_h5_h6_difficulty_variance(df: pd.DataFrame) -> Dict:
    """
    Test H5 (Variance) and H6 (Difficulty) using bivariate robust regression.
    
    Model: correlation_metric ~ β₁ * Difficulty + β₂ * CV + ε
    
    H5 is supported if β₂ (CV coefficient) is significant and positive.
    H6 is supported if β₁ (Difficulty coefficient) is significant and negative.
    
    Args:
        df: Analysis-ready DataFrame
        
    Returns:
        Dictionary with test results for Spearman, Kendall, and RBO
    """
    logger.info("Testing H5/H6: Difficulty-Variance joint effect")
    
    # Exclude Creative Writing v3 from Difficulty calculation
    df_test = df[df['benchmark_id'] != 'Creative Writing v3'].copy()
    
    # Filter to benchmarks with valid Difficulty and CV
    df_test = df_test[
        df_test['difficulty'].notna() &
        df_test['cv'].notna()
    ].copy()
    
    logger.info(f"  Using {len(df_test)} benchmarks (excluding Creative Writing v3)")
    
    results = {}
    
    # Prepare independent variables
    X = df_test[['difficulty', 'cv']].values
    # Add intercept column
    X = np.column_stack([np.ones(len(X)), X])
    
    # Test for each correlation metric
    for metric in ['spearman_rho', 'kendall_tau', 'rbo']:
        if metric not in df_test.columns:
            continue
        
        y = df_test[metric].dropna().values
        
        # Filter X to match y (remove rows where y is NaN)
        mask = df_test[metric].notna()
        X_filtered = X[mask]
        y_filtered = y
        
        if len(y_filtered) < 3:
            logger.warning(f"  Insufficient data for {metric}")
            results[f'H6_Difficulty_Beta1_{metric}'] = {
                'coefficient': np.nan,
                'p_raw': np.nan,
                'effect_size': np.nan,
                'effect_size_type': 'beta_coefficient'
            }
            results[f'H5_Variance_Beta2_{metric}'] = {
                'coefficient': np.nan,
                'p_raw': np.nan,
                'effect_size': np.nan,
                'effect_size_type': 'beta_coefficient'
            }
            continue
        
        # Robust regression
        try:
            coefficients, reg_results = huber_loss_regression(X_filtered, y_filtered)
            
            # Extract coefficients and p-values
            # coefficients[0] = intercept, coefficients[1] = Difficulty (β₁), coefficients[2] = CV (β₂)
            beta1 = coefficients[1] if len(coefficients) > 1 else np.nan
            beta2 = coefficients[2] if len(coefficients) > 2 else np.nan
            
            pvalues = reg_results.get('pvalues', [np.nan] * len(coefficients))
            p_beta1 = pvalues[1] if len(pvalues) > 1 else np.nan
            p_beta2 = pvalues[2] if len(pvalues) > 2 else np.nan
            
            # Calculate bootstrap CI for coefficients
            # Bootstrap by resampling rows
            # Use 5000 iterations for robust CI estimation
            logger.info(f"    Computing bootstrap CI for {metric} (this may take several minutes with 5000 iterations)...")
            np.random.seed(42)
            beta1_boot = []
            beta2_boot = []
            
            n_boot = 5000  # Full bootstrap for robust CI
            for i in range(n_boot):
                if (i + 1) % 100 == 0:
                    logger.info(f"      Bootstrap progress: {i+1}/{n_boot}")
                indices = np.random.choice(len(X_filtered), size=len(X_filtered), replace=True)
                X_boot = X_filtered[indices]
                y_boot = y_filtered[indices]
                try:
                    coefs, _ = huber_loss_regression(X_boot, y_boot)
                    if len(coefs) > 1 and np.isfinite(coefs[1]):
                        beta1_boot.append(coefs[1])
                    if len(coefs) > 2 and np.isfinite(coefs[2]):
                        beta2_boot.append(coefs[2])
                except Exception as e:
                    # Silently continue on errors
                    continue
            
            beta1_ci_lower = np.percentile(beta1_boot, 2.5) if len(beta1_boot) > 0 else np.nan
            beta1_ci_upper = np.percentile(beta1_boot, 97.5) if len(beta1_boot) > 0 else np.nan
            beta2_ci_lower = np.percentile(beta2_boot, 2.5) if len(beta2_boot) > 0 else np.nan
            beta2_ci_upper = np.percentile(beta2_boot, 97.5) if len(beta2_boot) > 0 else np.nan
            logger.info(f"    Completed bootstrap CI for {metric}")
            
        except Exception as e:
            logger.error(f"  Error in robust regression for {metric}: {e}")
            beta1 = np.nan
            beta2 = np.nan
            p_beta1 = np.nan
            p_beta2 = np.nan
            beta1_ci_lower = beta1_ci_upper = np.nan
            beta2_ci_lower = beta2_ci_upper = np.nan
        
        # H6: Difficulty coefficient (β₁)
        results[f'H6_Difficulty_Beta1_{metric}'] = {
            'coefficient': beta1,
            'p_raw': p_beta1,
            'effect_size': beta1,
            'effect_size_type': 'beta_coefficient',
            'ci_lower': beta1_ci_lower,
            'ci_upper': beta1_ci_upper,
            'sample_size': len(y_filtered)
        }
        
        # H5: Variance coefficient (β₂)
        results[f'H5_Variance_Beta2_{metric}'] = {
            'coefficient': beta2,
            'p_raw': p_beta2,
            'effect_size': beta2,
            'effect_size_type': 'beta_coefficient',
            'ci_lower': beta2_ci_lower,
            'ci_upper': beta2_ci_upper,
            'sample_size': len(y_filtered)
        }
        
        p_beta1_str = f"{p_beta1:.4f}" if pd.notna(p_beta1) else 'N/A'
        p_beta2_str = f"{p_beta2:.4f}" if pd.notna(p_beta2) else 'N/A'
        logger.info(f"  {metric}: β₁(Difficulty)={beta1:.3f}, p={p_beta1_str}")
        logger.info(f"  {metric}: β₂(CV)={beta2:.3f}, p={p_beta2_str}")
    
    return results


def main():
    """Main execution function."""
    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    data_path = base_dir / "results" / "analysis_ready_data.csv"
    
    # Load data
    logger.info("Loading analysis-ready data...")
    df = load_analysis_data(data_path)
    
    # Execute tests in order: H1, H2, H3, H4, H5/H6
    all_results = {}
    
    # H1: Generative vs MCQ
    logger.info("\n" + "="*60)
    h1_results = test_h1_generative(df)
    all_results.update(h1_results)
    
    # H2: Scale
    logger.info("\n" + "="*60)
    h2_results = test_h2_scale(df)
    all_results.update(h2_results)
    
    # H3: Complexity
    logger.info("\n" + "="*60)
    h3_results = test_h3_complexity(df)
    all_results.update(h3_results)
    
    # H4: Recency
    logger.info("\n" + "="*60)
    h4_results = test_h4_recency(df)
    all_results.update(h4_results)
    
    # H5/H6: Difficulty-Variance
    logger.info("\n" + "="*60)
    h5_h6_results = test_h5_h6_difficulty_variance(df)
    all_results.update(h5_h6_results)
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("Hypothesis Testing Summary")
    logger.info("="*60)
    
    for key, result in all_results.items():
        p_val = result.get('p_raw', np.nan)
        effect = result.get('effect_size', np.nan)
        p_str = f"{p_val:.4f}" if pd.notna(p_val) else 'N/A'
        effect_str = f"{effect:.3f}" if pd.notna(effect) else 'N/A'
        logger.info(f"{key}: effect={effect_str}, p={p_str}")
    
    # Save results (will be used in Step 4.4 for Holm-Bonferroni correction)
    output_path = base_dir / "results" / "hypothesis_test_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"\nSaved hypothesis test results to {output_path}")


if __name__ == "__main__":
    main()

