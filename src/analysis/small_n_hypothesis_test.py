"""
Small-N Hypothesis Testing Script

Purpose:
    This script executes targeted statistical tests for each hypothesis (H1-H5) using
    methods appropriate for the small benchmark sample (N=28 overall; N=27 for
    H4/H5 after excluding Creative Writing v3). Instead of a single
    multivariate regression which lacks statistical power, this script performs:
    - Hypothesis-specific univariate analyses for H1-H3
    - Controlled Bivariate Robust Regression to disentangle confounding factors

Why Small-N Protocols:
    - N=28 overall (N=27 for H4/H5) is too small for a full multivariable regression
    - Multivariate regression would have insufficient statistical power
    - Targeted tests allow rigorous testing of individual hypotheses while maintaining power

Statistical Methods:
    - H1: Pearson correlation (Scale: log(question_count) vs correlation metrics)
    - H2: Kruskal-Wallis H-test (Complexity: complexity categories)
    - H3: Spearman correlation (Recency: release_date vs correlation metrics)
    - H4/H5: Bivariate Robust Regression (Difficulty + CV vs correlation metrics)

Input:
    - analysis_ready_data.csv: Contains features and correlation coefficients for all benchmarks

Output:
    - Statistical test results for all hypotheses (H1-H5)
    - Results stored in dictionary format for Step 8 (Holm-Bonferroni correction)
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict
from scipy import stats
from scipy.stats import pearsonr
import logging
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from stats_utils import (
    bootstrap_ci,
    bootstrap_vector_ci,
    huber_loss_regression,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global settings
N_BOOTSTRAPS = 5000


def load_analysis_data(data_path: Path) -> pd.DataFrame:
    """
    Load analysis-ready data.
    
    Args:
        data_path: Path to analysis_ready_data.csv
        
    Returns:
        DataFrame with benchmark features and correlations
    """
    df = pd.read_csv(data_path)
    required = {
        'benchmark_id', 'question_count', 'complexity', 'release_date',
        'difficulty', 'cv', 'spearman_rho', 'kendall_tau', 'rbo',
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"analysis_ready_data.csv is missing columns: {sorted(missing)}"
        )
    if len(df) != 28 or df['benchmark_id'].nunique() != 28:
        raise ValueError(
            "Hypothesis testing requires exactly 28 unique benchmarks; "
            f"found {len(df)} rows and {df['benchmark_id'].nunique()} IDs"
        )
    metrics = ['spearman_rho', 'kendall_tau', 'rbo']
    if df[metrics].isna().any().any():
        raise ValueError("All 28 benchmarks require finite Spearman, Kendall, and RBO values")
    if df['question_count'].isna().any() or (df['question_count'] <= 0).any():
        raise ValueError("All benchmarks require a positive question_count")
    logger.info(f"Loaded {len(df)} benchmarks from analysis_ready_data.csv")
    return df


def test_h1_scale(df: pd.DataFrame) -> Dict:
    """
    Test H1: Scale effect (log(question_count) vs correlation metrics).
    
    Uses Pearson correlation between log(question_count) and correlation metrics.
    
    Args:
        df: Analysis-ready DataFrame
        
    Returns:
        Dictionary with test results for Spearman, Kendall, and RBO
    """
    logger.info("Testing H1: Scale effect")
    
    # Calculate log(question_count)
    df_test = df.copy()
    df_test['log_question_count'] = np.log(df_test['question_count'])
    
    results = {}
    
    # Test for each correlation metric
    for metric in ['spearman_rho', 'kendall_tau', 'rbo']:
        # Get paired data
        df_paired = df_test[['log_question_count', metric]].dropna()
        if len(df_paired) != 28:
            raise ValueError(f"H1 requires 28 complete observations for {metric}")
        
        x = df_paired['log_question_count'].values
        y = df_paired[metric].values
        
        # Pearson correlation
        correlation, p_value = pearsonr(x, y)
        
        results[f'H1_{metric}'] = {
            'correlation': correlation,
            'p_raw': p_value,
            'effect_size': correlation,
            'effect_size_type': 'pearson_r',
            'sample_size': len(df_paired)
        }
        
        p_str = f"{p_value:.4f}" if pd.notna(p_value) else 'N/A'
        logger.info(f"  {metric}: r={correlation:.3f}, p={p_str}")
    
    return results


def test_h2_complexity(df: pd.DataFrame) -> Dict:
    """
    Test H2: Higher task complexity is associated with stronger correlation.

    The Kruskal-Wallis H-test is the primary inferential test: its p-value is
    stored as ``p_raw`` and enters the Holm-Bonferroni correction in Step 8.
    Ordinal linear regression is a complementary trend analysis whose R-squared
    is reported as H2's effect size.
    """
    logger.info("Testing H2: Complexity Categories")
    
    df_test = df.copy()
    logger.info(f"  Analyzed {len(df_test)} benchmarks with complexity data")

    complexity_order = ['Applying', 'Analyzing', 'Evaluating', 'Creating']
    complexity_val = {c: i+1 for i, c in enumerate(complexity_order)}
    df_test['complexity_val'] = df_test['complexity'].map(complexity_val)
    if df_test['complexity_val'].isna().any():
        invalid = sorted(set(df_test.loc[df_test['complexity_val'].isna(), 'complexity']))
        raise ValueError(f"H2 found missing or unsupported complexity levels: {invalid}")
    
    results = {}
    
    # Exact metric definition
    metrics = {
        'Spearman': 'spearman_rho', 
        'Kendall': 'kendall_tau', 
        'RBO': 'rbo'
    }
    
    # Test for each correlation metric
    for metric_name, metric_col in metrics.items():
        # 1. Primary inference: Kruskal-Wallis test across complexity groups.
        groups = [
            df_test.loc[df_test['complexity'] == c, metric_col].dropna().values
            for c in complexity_order
        ]
        if any(len(group) == 0 for group in groups):
            raise ValueError(f"H2 requires all four complexity groups for {metric_name}")
        kw_stat, kw_p = stats.kruskal(*groups)

        # 2. Complementary trend analysis: ordinal linear regression.
        df_metric = df_test.dropna(subset=['complexity_val', metric_col])
        slope, intercept, r_value, p_value, std_err = stats.linregress(df_metric['complexity_val'], df_metric[metric_col])
        
        results[f'H2_{metric_col}'] = {
            'primary_test': 'kruskal_wallis',
            'test_statistic': kw_stat,
            'p_raw': kw_p,
            'trend_test': 'ordinal_linear_regression',
            'regression_p_value': p_value,
            'regression_slope': slope,
            'regression_r2': r_value**2,
            'effect_size': r_value**2,
            'effect_size_type': 'r_squared',
            'sample_size': len(df_metric)
        }
        
        logger.info(f"  {metric_name}: KW p={kw_p:.4f}, Reg p={p_value:.4f}, Slope={slope:.4f}")
    
    return results


def test_h3_recency(df: pd.DataFrame) -> Dict:
    """
    Test H3: Recency effect (release_date vs correlation metrics).
    
    Uses Spearman correlation between release_date (ordinal) and correlation metrics.
    
    Args:
        df: Analysis-ready DataFrame
        
    Returns:
        Dictionary with test results for Spearman, Kendall, and RBO
    """
    logger.info("Testing H3: Recency effect")
    
    # Convert release_date to ordinal (days since reference date)
    df_test = df.copy()
    reference_date = datetime(2021, 1, 1)
    
    def date_to_ordinal(date_str):
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return (date_obj - reference_date).days
        except (TypeError, ValueError):
            return np.nan
    
    df_test['release_date_ordinal'] = df_test['release_date'].apply(date_to_ordinal)
    
    results = {}
    
    # Test for each correlation metric
    for metric in ['spearman_rho', 'kendall_tau', 'rbo']:
        # Get paired data
        df_paired = df_test[['release_date_ordinal', metric]].dropna()
        if len(df_paired) != 28:
            raise ValueError(f"H3 requires 28 valid release dates for {metric}")
        
        x = df_paired['release_date_ordinal'].values
        y = df_paired[metric].values
        
        # Spearman correlation
        correlation, p_value = stats.spearmanr(x, y)
        
        # Calculate bootstrap CI
        def spearman_func(x_data, y_data):
            return stats.spearmanr(x_data, y_data)[0]
        
        ci_lower, ci_upper = bootstrap_ci(
            x,
            y,
            spearman_func,
            n_boot=N_BOOTSTRAPS,
        )
        
        results[f'H3_{metric}'] = {
            'correlation': correlation,
            'p_raw': p_value,
            'effect_size': correlation,
            'effect_size_type': 'spearman_rho',
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'sample_size': len(df_paired)
        }
        
        p_str = f"{p_value:.4f}" if pd.notna(p_value) else 'N/A'
        logger.info(f"  {metric}: ρ={correlation:.3f}, p={p_str}")
    
    return results


def test_h4_h5_difficulty_variance(df: pd.DataFrame) -> Dict:
    """
    Test H4 (Variance) and H5 (Difficulty) using bivariate robust regression.
    
    Model: correlation_metric = β₀ + β₁ * Difficulty + β₂ * CV + ε
    
    H4 is supported if β₂ (CV coefficient) is significant and positive.
    H5 is supported if β₁ (Difficulty coefficient) is significant and negative.
    
    Args:
        df: Analysis-ready DataFrame
        
    Returns:
        Dictionary with test results for Spearman, Kendall, and RBO
    """
    logger.info("Testing H4/H5: Difficulty-Variance joint effect")
    
    # Exclude Creative Writing v3 because no defensible Difficulty value exists.
    df_test = df[df['benchmark_id'] != 'Creative Writing v3'].copy()
    
    # Filter to benchmarks with valid Difficulty and CV
    df_test = df_test[
        df_test['difficulty'].notna() &
        df_test['cv'].notna()
    ].copy()
    
    logger.info(f"  Using {len(df_test)} benchmarks (excluding Creative Writing v3)")
    if len(df_test) != 27:
        raise ValueError(
            "H4/H5 require exactly 27 benchmarks with defined Difficulty and CV; "
            f"found {len(df_test)}"
        )
    
    results = {}
    
    # Prepare independent variables
    X = df_test[['difficulty', 'cv']].values
    # Add intercept column
    X = np.column_stack([np.ones(len(X)), X])
    
    # Test for each correlation metric
    for metric in ['spearman_rho', 'kendall_tau', 'rbo']:
        y = df_test[metric].dropna().values
        
        # Filter X to match y (remove rows where y is NaN)
        mask = df_test[metric].notna()
        X_filtered = X[mask]
        y_filtered = y
        
        if len(y_filtered) != 27:
            raise ValueError(f"H4/H5 require 27 complete observations for {metric}")
        
        # Robust regression
        try:
            coefficients, reg_results = huber_loss_regression(X_filtered, y_filtered)
            
            # Extract coefficients and p-values
            # coefficients[0] = intercept, coefficients[1] = Difficulty (β₁), coefficients[2] = CV (β₂)
            beta1 = coefficients[1] if len(coefficients) > 1 else np.nan
            beta2 = coefficients[2] if len(coefficients) > 2 else np.nan
            intercept = coefficients[0] if len(coefficients) > 0 else np.nan
            
            pvalues = reg_results.get('pvalues', [np.nan] * len(coefficients))
            p_beta1 = pvalues[1] if len(pvalues) > 1 else np.nan
            p_beta2 = pvalues[2] if len(pvalues) > 2 else np.nan
            
            # Calculate both coefficient CIs from the same bootstrap samples.
            logger.info(
                "    Computing bootstrap CI for %s "
                "(this may take several minutes with %d iterations)...",
                metric,
                N_BOOTSTRAPS,
            )

            def coefficient_func(X_boot, y_boot):
                coefs, _ = huber_loss_regression(X_boot, y_boot)
                return np.array([
                    coefs[1] if len(coefs) > 1 else np.nan,
                    coefs[2] if len(coefs) > 2 else np.nan,
                ])

            def log_bootstrap_progress(completed, total):
                if completed % 100 == 0:
                    logger.info(
                        "      Bootstrap progress: %d/%d",
                        completed,
                        total,
                    )

            ci_lower, ci_upper = bootstrap_vector_ci(
                X_filtered,
                y_filtered,
                coefficient_func,
                n_boot=N_BOOTSTRAPS,
                n_statistics=2,
                progress_callback=log_bootstrap_progress,
            )
            beta1_ci_lower, beta2_ci_lower = ci_lower
            beta1_ci_upper, beta2_ci_upper = ci_upper
            logger.info(f"    Completed bootstrap CI for {metric}")
            
        except Exception as exc:
            raise RuntimeError(
                f"H4/H5 robust regression failed for {metric}"
            ) from exc
        
        # H4: Variance coefficient (β₂)
        results[f'H4_Variance_Beta2_{metric}'] = {
            'model': 'bivariate_huber_robust_regression',
            'coefficient': beta2,
            'intercept': intercept,
            'p_raw': p_beta2,
            'effect_size': beta2,
            'effect_size_type': 'beta_coefficient',
            'ci_lower': beta2_ci_lower,
            'ci_upper': beta2_ci_upper,
            'sample_size': len(y_filtered)
        }

        # H5: Difficulty coefficient (β₁)
        results[f'H5_Difficulty_Beta1_{metric}'] = {
            'model': 'bivariate_huber_robust_regression',
            'coefficient': beta1,
            'intercept': intercept,
            'p_raw': p_beta1,
            'effect_size': beta1,
            'effect_size_type': 'beta_coefficient',
            'ci_lower': beta1_ci_lower,
            'ci_upper': beta1_ci_upper,
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
    
    # Execute tests in order: H1, H2, H3, H4/H5
    all_results = {}

    # H1: Scale
    logger.info("\n" + "="*60)
    h1_results = test_h1_scale(df)
    all_results.update(h1_results)

    # H2: Complexity
    logger.info("\n" + "="*60)
    h2_results = test_h2_complexity(df)
    all_results.update(h2_results)

    # H3: Recency
    logger.info("\n" + "="*60)
    h3_results = test_h3_recency(df)
    all_results.update(h3_results)

    # H4/H5: Difficulty-Variance
    logger.info("\n" + "="*60)
    h4_h5_results = test_h4_h5_difficulty_variance(df)
    all_results.update(h4_h5_results)

    expected_results = {
        *(f'H1_{metric}' for metric in ['spearman_rho', 'kendall_tau', 'rbo']),
        *(f'H2_{metric}' for metric in ['spearman_rho', 'kendall_tau', 'rbo']),
        *(f'H3_{metric}' for metric in ['spearman_rho', 'kendall_tau', 'rbo']),
        *(f'H4_Variance_Beta2_{metric}' for metric in ['spearman_rho', 'kendall_tau', 'rbo']),
        *(f'H5_Difficulty_Beta1_{metric}' for metric in ['spearman_rho', 'kendall_tau', 'rbo']),
    }
    if set(all_results) != expected_results:
        raise RuntimeError(
            "Step 7 did not produce the required 15 tests; "
            f"missing={sorted(expected_results - set(all_results))}, "
            f"extra={sorted(set(all_results) - expected_results)}"
        )
    for key, result in all_results.items():
        if not np.isfinite(result['p_raw']) or not np.isfinite(result['effect_size']):
            raise RuntimeError(f"Step 7 produced a non-finite result for {key}")
    
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
    
    # Save results for Step 8 Holm-Bonferroni correction
    output_path = base_dir / "results" / "hypothesis_test_results.json"
    with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(
            all_results,
            f,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
            default=float,
        )
    
    logger.info(f"\nSaved hypothesis test results to {output_path}")


if __name__ == "__main__":
    main()

