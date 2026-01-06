"""
Feature Engineering and Correlation Calculation Script

Purpose:
    This script computes benchmark features (Difficulty, Variance) and calculates correlation
    coefficients (Spearman ρ, Kendall τ, RBO) between benchmark scores and Perceived Utility
    (LMArena ELO scores).

Complete Workflow:
    1. Load benchmark data from master_correlation_matrix.csv (all benchmarks except Creative
       Writing v3 are normalized to 0-100 scale during data preparation)
    2. Read category from metadata.json to determine which LMArena ELO column to use for
       correlation (each benchmark is compared only with its corresponding category)
    3. Compute Difficulty feature using Common Subset (models with elo_overall between 1400-1430)
    4. Compute Variance feature (Coefficient of Variation: CV = σ/μ)
    5. Calculate Spearman ρ, Kendall τ, and RBO with p-values and 95% confidence intervals
    6. Perform sanity check on high-quality benchmarks

Key Assumptions:
    - All benchmarks except Creative Writing v3 are normalized to 0-100 scale (higher is better)
    - Creative Writing v3 uses Elo scores and is not normalized
    - Each benchmark is compared only with its corresponding LMArena category (not Overall)
    - Difficulty is calculated using Common Subset (elo_overall between 1400-1430, inclusive)
    - Creative Writing v3 is excluded from Difficulty calculation

Input:
    - Master table: data/processed/master_table/master_correlation_matrix.csv
    - Metadata: data/metadata.json

Output:
    - analysis_ready_data.csv: Complete feature and correlation dataset
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from stats_utils import (
    calculate_spearman_with_pvalue,
    calculate_kendall_with_pvalue,
    calculate_rbo,
    bootstrap_ci
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_metadata(metadata_path: Path) -> Dict[str, Dict]:
    """
    Load metadata and create benchmark lookup dictionary.
    
    Args:
        metadata_path: Path to metadata.json
        
    Returns:
        Dictionary mapping benchmark_name to metadata entry
    """
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Filter to benchmarks only (exclude meta_info and LMArena entries)
    benchmarks = {
        entry['benchmark_id']: entry
        for entry in metadata
        if isinstance(entry, dict) and 'benchmark_id' in entry and 'elo_column' not in entry
    }
    
    return benchmarks


def get_elo_column_for_category(category: str) -> str:
    """
    Map benchmark category to corresponding LMArena ELO column.
    
    Args:
        category: Benchmark category (e.g., "Math", "Coding")
        
    Returns:
        ELO column name (e.g., "elo_math", "elo_coding")
    """
    category_mapping = {
        "Math": "elo_math",
        "Coding": "elo_coding",
        "Instruction Following": "elo_instruction_following",
        "Creative Writing": "elo_creative_writing",
        "Hard Prompts": "elo_hard_prompts",
        "Expert": "elo_expert"
    }
    
    if category not in category_mapping:
        raise ValueError(f"Unknown category: {category}")
    
    return category_mapping[category]


def sanitize_benchmark_id(benchmark_id: str) -> str:
    """
    Sanitize benchmark_id to match column names in master table.
    
    Args:
        benchmark_id: Original benchmark identifier
        
    Returns:
        Sanitized column name prefix
    """
    import re
    sanitized = re.sub(r'[^\w\-]', '_', benchmark_id)
    sanitized = re.sub(r'_+', '_', sanitized)
    sanitized = sanitized.strip('_')
    return sanitized


def calculate_difficulty(
    df_master: pd.DataFrame,
    benchmark_id: str,
    benchmark_meta: Dict,
    elo_min: float = 1400.0,
    elo_max: float = 1430.0
) -> Tuple[float, bool]:
    """
    Calculate Difficulty feature using Common Subset.
    
    Difficulty = 100 - subset_avg_score, where subset_avg_score is the mean score
    across models in the Common Subset (elo_overall between elo_min and elo_max, inclusive).
    
    Args:
        df_master: Master correlation matrix DataFrame
        benchmark_id: Benchmark identifier
        benchmark_meta: Benchmark metadata dictionary
        elo_min: Minimum ELO for Common Subset (default: 1400.0)
        elo_max: Maximum ELO for Common Subset (default: 1430.0)
        
    Returns:
        Tuple of (difficulty, is_estimated)
        - difficulty: Difficulty value (higher = harder benchmark)
        - is_estimated: True if fallback method was used due to insufficient overlap
    """
    # Exclude Creative Writing v3 from Difficulty calculation
    if benchmark_id == "Creative Writing v3":
        return (np.nan, False)
    
    # Sanitize benchmark_id for column name
    col_prefix = sanitize_benchmark_id(benchmark_id)
    score_col = f"{col_prefix}_score"
    
    if score_col not in df_master.columns:
        logger.warning(f"Score column not found for {benchmark_id}: {score_col}")
        return (np.nan, True)
    
    # Filter to Common Subset (elo_overall between elo_min and elo_max)
    common_subset = df_master[
        (df_master['elo_overall'] >= elo_min) &
        (df_master['elo_overall'] <= elo_max)
    ].copy()
    
    # Get scores for this benchmark in Common Subset
    subset_scores = common_subset[score_col].dropna()
    
    n_subset = len(subset_scores)
    
    if n_subset < 5:
        logger.warning(
            f"Insufficient overlap for Difficulty Common Subset for {benchmark_id} "
            f"(N={n_subset} < 5). Using fallback method."
        )
        # Fallback: use all available models (not just Common Subset)
        all_scores = df_master[score_col].dropna()
        if len(all_scores) == 0:
            return (np.nan, True)
        subset_avg_score = all_scores.mean()
        return (100 - subset_avg_score, True)
    
    # Calculate mean score in Common Subset
    subset_avg_score = subset_scores.mean()
    
    # Difficulty = 100 - subset_avg_score
    difficulty = 100 - subset_avg_score
    
    return (difficulty, False)


def calculate_cv(df_master: pd.DataFrame, benchmark_id: str) -> float:
    """
    Calculate Coefficient of Variation (CV) for a benchmark.
    
    Formula: CV = σ / μ
    
    CV normalizes variance relative to the score scale, making high-accuracy benchmarks
    (where scores are compressed near 100%) comparable to other benchmarks.
    
    Args:
        df_master: Master correlation matrix DataFrame
        benchmark_id: Benchmark identifier
        
    Returns:
        Coefficient of Variation (CV), or NaN if insufficient data
    """
    col_prefix = sanitize_benchmark_id(benchmark_id)
    score_col = f"{col_prefix}_score"
    
    if score_col not in df_master.columns:
        return np.nan
    
    scores = df_master[score_col].dropna()
    
    if len(scores) < 2:
        return np.nan
    
    mean_score = scores.mean()
    std_score = scores.std()
    
    if mean_score == 0:
        return np.nan
    
    cv = std_score / mean_score
    
    return cv


def calculate_correlations(
    df_master: pd.DataFrame,
    benchmark_id: str,
    benchmark_meta: Dict
) -> Dict:
    """
    Calculate Spearman ρ, Kendall τ, and RBO between benchmark and corresponding LMArena category.
    
    Args:
        df_master: Master correlation matrix DataFrame
        benchmark_id: Benchmark identifier
        benchmark_meta: Benchmark metadata dictionary
        
    Returns:
        Dictionary containing correlation coefficients, p-values, and confidence intervals
    """
    # Get corresponding ELO column
    category = benchmark_meta.get('category')
    if not category:
        logger.warning(f"No category found for {benchmark_id}")
        return {
            'spearman_rho': np.nan,
            'spearman_pvalue': np.nan,
            'spearman_ci_lower': np.nan,
            'spearman_ci_upper': np.nan,
            'kendall_tau': np.nan,
            'kendall_pvalue': np.nan,
            'kendall_ci_lower': np.nan,
            'kendall_ci_upper': np.nan,
            'rbo': np.nan,
            'sample_size': 0
        }
    
    elo_col = get_elo_column_for_category(category)
    
    # Sanitize benchmark_id for column name
    col_prefix = sanitize_benchmark_id(benchmark_id)
    score_col = f"{col_prefix}_score"
    rank_col = f"{col_prefix}_rank"
    
    if score_col not in df_master.columns:
        logger.warning(f"Score column not found for {benchmark_id}: {score_col}")
        return {
            'spearman_rho': np.nan,
            'spearman_pvalue': np.nan,
            'spearman_ci_lower': np.nan,
            'spearman_ci_upper': np.nan,
            'kendall_tau': np.nan,
            'kendall_pvalue': np.nan,
            'kendall_ci_lower': np.nan,
            'kendall_ci_upper': np.nan,
            'rbo': np.nan,
            'sample_size': 0
        }
    
    # Get paired data (exclude NaN)
    df_paired = df_master[[score_col, elo_col]].dropna()
    
    if len(df_paired) < 2:
        logger.warning(f"Insufficient data for correlation calculation: {benchmark_id}")
        return {
            'spearman_rho': np.nan,
            'spearman_pvalue': np.nan,
            'spearman_ci_lower': np.nan,
            'spearman_ci_upper': np.nan,
            'kendall_tau': np.nan,
            'kendall_pvalue': np.nan,
            'kendall_ci_lower': np.nan,
            'kendall_ci_upper': np.nan,
            'rbo': np.nan,
            'sample_size': len(df_paired)
        }
    
    benchmark_scores = df_paired[score_col].values
    elo_scores = df_paired[elo_col].values
    n = len(df_paired)
    
    # Calculate Spearman correlation
    spearman_rho, spearman_pvalue = calculate_spearman_with_pvalue(benchmark_scores, elo_scores)
    
    # Calculate Kendall correlation
    kendall_tau, kendall_pvalue = calculate_kendall_with_pvalue(benchmark_scores, elo_scores)
    
    # Calculate RBO (requires ranked lists)
    if rank_col in df_master.columns:
        # Get ranked lists (top models by rank)
        df_ranked = df_master[[rank_col, elo_col]].dropna()
        if len(df_ranked) > 0:
            # Sort by rank (ascending: rank 1 is best)
            df_ranked = df_ranked.sort_values(rank_col)
            # Use model names (index) as the ranked list
            benchmark_ranked = df_ranked.index.tolist()
            
            # Sort LMArena by ELO (descending: higher ELO is better)
            df_elo_ranked = df_master[[elo_col]].dropna().sort_values(elo_col, ascending=False)
            elo_ranked = df_elo_ranked.index.tolist()
            
            # Calculate RBO (only use models that appear in both lists)
            common_models = set(benchmark_ranked) & set(elo_ranked)
            if len(common_models) > 0:
                # Filter to common models and preserve order
                benchmark_ranked_filtered = [m for m in benchmark_ranked if m in common_models]
                elo_ranked_filtered = [m for m in elo_ranked if m in common_models]
                rbo = calculate_rbo(benchmark_ranked_filtered, elo_ranked_filtered, p=0.9)
            else:
                rbo = np.nan
        else:
            rbo = np.nan
    else:
        rbo = np.nan
    
    # Calculate bootstrap confidence intervals
    # For bootstrap, we only need the correlation coefficient, not p-value
    # Use direct scipy functions for speed (much faster than permutation test)
    from scipy.stats import spearmanr, kendalltau
    
    def spearman_func(x, y):
        # Direct calculation for bootstrap (no permutation test needed)
        rho, _ = spearmanr(x, y)
        return rho
    
    def kendall_func(x, y):
        # Direct calculation for bootstrap (no permutation test needed)
        tau, _ = kendalltau(x, y)
        return tau
    
    logger.info(f"  Calculating bootstrap CI for {benchmark_id} (N={n})...")
    spearman_ci_lower, spearman_ci_upper = bootstrap_ci(
        benchmark_scores, elo_scores, spearman_func, n_boot=2000
    )
    
    kendall_ci_lower, kendall_ci_upper = bootstrap_ci(
        benchmark_scores, elo_scores, kendall_func, n_boot=2000
    )
    logger.info(f"  Completed correlations for {benchmark_id}")
    
    return {
        'spearman_rho': spearman_rho,
        'spearman_pvalue': spearman_pvalue,
        'spearman_ci_lower': spearman_ci_lower,
        'spearman_ci_upper': spearman_ci_upper,
        'kendall_tau': kendall_tau,
        'kendall_pvalue': kendall_pvalue,
        'kendall_ci_lower': kendall_ci_lower,
        'kendall_ci_upper': kendall_ci_upper,
        'rbo': rbo,
        'sample_size': n
    }


def main():
    """Main execution function."""
    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    master_table_path = base_dir / "data" / "processed" / "master_table" / "master_correlation_matrix.csv"
    metadata_path = base_dir / "data" / "metadata.json"
    results_dir = base_dir / "results"
    
    # Create results directory
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info("Loading master table...")
    df_master = pd.read_csv(master_table_path)
    df_master = df_master.set_index('model_name')
    
    logger.info("Loading metadata...")
    benchmarks_meta = load_metadata(metadata_path)
    
    # Initialize results list
    results = []
    
    # Process each benchmark
    total_benchmarks = len(benchmarks_meta)
    for idx, (benchmark_id, benchmark_meta) in enumerate(benchmarks_meta.items(), 1):
        logger.info(f"Processing {benchmark_id} ({idx}/{total_benchmarks})...")
        
        # Calculate Difficulty
        logger.debug(f"  Calculating difficulty for {benchmark_id}...")
        difficulty, is_estimated_difficulty = calculate_difficulty(
            df_master, benchmark_id, benchmark_meta
        )
        
        # Calculate subset_avg_score (for reference)
        col_prefix = sanitize_benchmark_id(benchmark_id)
        score_col = f"{col_prefix}_score"
        if score_col in df_master.columns:
            common_subset = df_master[
                (df_master['elo_overall'] >= 1400.0) &
                (df_master['elo_overall'] <= 1430.0)
            ]
            subset_scores = common_subset[score_col].dropna()
            subset_avg_score = subset_scores.mean() if len(subset_scores) >= 5 else np.nan
        else:
            subset_avg_score = np.nan
        
        # Calculate CV
        logger.debug(f"  Calculating CV for {benchmark_id}...")
        cv = calculate_cv(df_master, benchmark_id)
        
        # Calculate correlations
        logger.info(f"  Calculating correlations for {benchmark_id}...")
        corr_results = calculate_correlations(df_master, benchmark_id, benchmark_meta)
        logger.info(f"  Completed {benchmark_id}: Spearman ρ = {corr_results['spearman_rho']:.3f}, N = {corr_results['sample_size']}")
        
        # Combine results
        result_row = {
            'benchmark_id': benchmark_id,
            'subset_avg_score': subset_avg_score,
            'difficulty': difficulty,
            'is_estimated_difficulty': is_estimated_difficulty,
            'cv': cv,
            'coefficient_of_variation': cv,  # Alias
            'n': corr_results['sample_size'],
            'sample_size': corr_results['sample_size'],
            'spearman_rho': corr_results['spearman_rho'],
            'spearman_pvalue': corr_results['spearman_pvalue'],
            'spearman_ci_lower': corr_results['spearman_ci_lower'],
            'spearman_ci_upper': corr_results['spearman_ci_upper'],
            'kendall_tau': corr_results['kendall_tau'],
            'kendall_pvalue': corr_results['kendall_pvalue'],
            'kendall_ci_lower': corr_results['kendall_ci_lower'],
            'kendall_ci_upper': corr_results['kendall_ci_upper'],
            'rbo': corr_results['rbo']
        }
        
        # Add metadata columns
        for key in ['category', 'release_date', 'task_type', 'prompt_length', 'question_count']:
            result_row[key] = benchmark_meta.get(key, np.nan)
        
        results.append(result_row)
    
    # Create DataFrame
    df_results = pd.DataFrame(results)
    
    # Sanity check: Check high-quality benchmarks
    logger.info("\n=== Sanity Check: High-Quality Benchmarks ===")
    high_quality_benchmarks = ['MMLU-Pro', 'HumanEval']
    
    for benchmark_id in high_quality_benchmarks:
        if benchmark_id in df_results['benchmark_id'].values:
            row = df_results[df_results['benchmark_id'] == benchmark_id].iloc[0]
            spearman_rho = row['spearman_rho']
            
            if pd.notna(spearman_rho) and spearman_rho < 0.5:
                logger.critical(
                    f"CRITICAL: Detected low Spearman correlation (< 0.5) for high-quality "
                    f"benchmark {benchmark_id}. Spearman ρ = {spearman_rho:.3f}. "
                    f"This suggests a data quality issue. Please check: "
                    f"(1) that the correct LMArena ELO column is being used based on the "
                    f"benchmark's category, and (2) that data is loaded correctly from "
                    f"cleaned_data.csv files."
                )
                # Don't halt execution, but log critical warning
            else:
                logger.info(
                    f"{benchmark_id}: Spearman ρ = {spearman_rho:.3f} "
                    f"(p = {row['spearman_pvalue']:.4f}, N = {row['sample_size']})"
                )
    
    # Save results
    output_path = results_dir / "analysis_ready_data.csv"
    df_results.to_csv(output_path, index=False, na_rep='NaN')
    logger.info(f"\nSaved analysis-ready data to {output_path}")
    logger.info(f"Shape: {df_results.shape}")
    
    # Print summary
    logger.info("\n=== Feature Engineering Summary ===")
    logger.info(f"Total benchmarks processed: {len(df_results)}")
    logger.info(f"Benchmarks with valid correlations: {df_results['spearman_rho'].notna().sum()}")
    logger.info(f"Average Spearman ρ: {df_results['spearman_rho'].mean():.3f}")
    logger.info(f"Average sample size: {df_results['sample_size'].mean():.1f}")


if __name__ == "__main__":
    main()

