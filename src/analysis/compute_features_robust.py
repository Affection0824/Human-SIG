"""
Robust Feature Engineering and Correlation Calculation Module

Purpose:
    This module computes robust features (Difficulty, Coefficient of Variation) and calculates
    correlation coefficients (Spearman ρ, Kendall τ, RBO) between benchmark scores and LMArena
    ELO scores representing Perceived Utility.

Complete Workflow:
    1. Load benchmark data from master_correlation_matrix.csv (all benchmarks except Creative Writing v3
       are normalized to 0-100 scale during data preparation)
    2. Read category from metadata.json to determine which LMArena ELO column to use for correlation
    3. Compute Difficulty feature using Common Subset (models with elo_overall between 1400-1430)
    4. Compute Coefficient of Variation (CV) for variance feature
    5. Calculate correlations (Spearman, Kendall, RBO) between benchmark scores and corresponding
       LMArena ELO scores
    6. Calculate 95% bootstrap confidence intervals for correlation coefficients
    7. Save all features and correlations to analysis_ready_data.csv

Key Assumptions:
    - All benchmarks except Creative Writing v3 are normalized to 0-100 scale (higher is better)
    - Creative Writing v3 uses Elo scores and is not normalized
    - Each benchmark is correlated with its corresponding LMArena category (not LMArena-Overall)
    - Difficulty is calculated using Common Subset (elo_overall between 1400-1430, inclusive)
    - Creative Writing v3 is excluded from Difficulty calculation
    - CV normalizes variance relative to mean score, making high-accuracy benchmarks comparable

Input:
    - Master table: Human-SIG/data/processed/master_table/master_correlation_matrix.csv
    - Metadata: Human-SIG/data/metadata.json

Output:
    - Analysis-ready data: Human-SIG/results/analysis_ready_data.csv
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.stats_utils import (
    calculate_spearman_with_pvalue,
    calculate_kendall_with_pvalue,
    calculate_spearman_fast,
    calculate_kendall_fast,
    calculate_rbo,
    bootstrap_ci
)


def sanitize_benchmark_id(benchmark_name: str) -> str:
    """Sanitize benchmark name to create benchmark_id (same as in build_master_table.py)."""
    import re
    sanitized = benchmark_name.lower()
    sanitized = re.sub(r'[^a-z0-9]+', '_', sanitized)
    sanitized = re.sub(r'_+', '_', sanitized)
    sanitized = sanitized.strip('_')
    return sanitized


def get_elo_column_for_category(category: str) -> str:
    """
    Map benchmark category to corresponding LMArena ELO column.
    
    Args:
        category: Benchmark category (e.g., "Math", "Coding")
    
    Returns:
        ELO column name (e.g., "elo_math", "elo_coding")
    """
    category_to_elo = {
        'Math': 'elo_math',
        'Coding': 'elo_coding',
        'Instruction Following': 'elo_instruction_following',
        'Creative Writing': 'elo_creative_writing',
        'Hard Prompts': 'elo_hard_prompts',
        'Expert': 'elo_expert'
    }
    return category_to_elo.get(category, 'elo_overall')


def calculate_difficulty(
    df_master: pd.DataFrame,
    benchmark_id: str,
    elo_overall_col: str = 'elo_overall'
) -> Tuple[float, bool]:
    """
    Calculate Difficulty feature using Common Subset method.
    
    The Common Subset consists of models with elo_overall between 1400 and 1430 (inclusive).
    Difficulty is calculated as: Difficulty = 100 - subset_avg_score
    
    Args:
        df_master: Master correlation matrix DataFrame
        benchmark_id: Sanitized benchmark ID (e.g., "humaneval")
        elo_overall_col: Name of elo_overall column (default "elo_overall")
    
    Returns:
        Tuple of (difficulty_value, is_estimated_flag)
        - difficulty_value: Difficulty score (higher = harder benchmark)
        - is_estimated_flag: True if insufficient overlap (N < 5), False otherwise
    """
    score_col = f'{benchmark_id}_score'
    
    # Filter to Common Subset: elo_overall between 1400 and 1430 (inclusive)
    common_subset = df_master[
        (df_master[elo_overall_col] >= 1400) &
        (df_master[elo_overall_col] <= 1430)
    ].copy()
    
    # Get scores for models in Common Subset that have scores for this benchmark
    subset_scores = common_subset[score_col].dropna()
    
    n_overlap = len(subset_scores)
    
    if n_overlap < 5:
        # Insufficient overlap - use fallback: calculate mean across all models with scores
        all_scores = df_master[score_col].dropna()
        if len(all_scores) == 0:
            return (np.nan, True)
        subset_avg_score = all_scores.mean()
        is_estimated = True
        print(f"  Warning: Insufficient overlap for Difficulty Common Subset (N={n_overlap}). "
              f"Using fallback method (all models with scores).")
    else:
        subset_avg_score = subset_scores.mean()
        is_estimated = False
    
    # Difficulty = 100 - subset_avg_score (higher Difficulty = harder benchmark)
    difficulty = 100 - subset_avg_score
    
    return (difficulty, is_estimated)


def calculate_cv(df_master: pd.DataFrame, benchmark_id: str) -> float:
    """
    Calculate Coefficient of Variation (CV) for variance feature.
    
    Formula: CV = σ / μ
    where σ is standard deviation and μ is mean score.
    
    CV normalizes variance relative to the score scale, making high-accuracy benchmarks
    (where scores are compressed near 100%) comparable to other benchmarks.
    
    Args:
        df_master: Master correlation matrix DataFrame
        benchmark_id: Sanitized benchmark ID
    
    Returns:
        Coefficient of Variation (float)
    """
    score_col = f'{benchmark_id}_score'
    scores = df_master[score_col].dropna()
    
    if len(scores) == 0:
        return np.nan
    
    mean_score = scores.mean()
    std_score = scores.std()
    
    if mean_score == 0:
        return np.nan
    
    cv = std_score / mean_score
    return cv


def calculate_correlations_with_ci(
    df_master: pd.DataFrame,
    benchmark_id: str,
    elo_col: str
) -> Dict:
    """
    Calculate Spearman, Kendall, and RBO correlations with p-values and confidence intervals.
    
    Args:
        df_master: Master correlation matrix DataFrame
        benchmark_id: Sanitized benchmark ID
        elo_col: LMArena ELO column name (e.g., "elo_math")
    
    Returns:
        Dictionary containing:
        - spearman_rho: Spearman correlation coefficient
        - spearman_pvalue: P-value for Spearman correlation
        - spearman_ci_lower: Lower bound of 95% bootstrap CI
        - spearman_ci_upper: Upper bound of 95% bootstrap CI
        - kendall_tau: Kendall's τ correlation coefficient
        - kendall_pvalue: P-value for Kendall correlation
        - kendall_ci_lower: Lower bound of 95% bootstrap CI
        - kendall_ci_upper: Upper bound of 95% bootstrap CI
        - rbo: Rank-Biased Overlap (p=0.9)
    """
    score_col = f'{benchmark_id}_score'
    rank_col = f'{benchmark_id}_rank'
    
    # Get paired data (exclude rows with NaN in either column)
    df_paired = df_master[[score_col, elo_col, rank_col]].dropna()
    
    if len(df_paired) < 2:
        return {
            'spearman_rho': np.nan,
            'spearman_pvalue': np.nan,
            'spearman_ci_lower': np.nan,
            'spearman_ci_upper': np.nan,
            'kendall_tau': np.nan,
            'kendall_pvalue': np.nan,
            'kendall_ci_lower': np.nan,
            'kendall_ci_upper': np.nan,
            'rbo': np.nan
        }
    
    benchmark_scores = df_paired[score_col].values
    elo_scores = df_paired[elo_col].values
    
    # Calculate Spearman correlation with p-value
    spearman_rho, spearman_pvalue = calculate_spearman_with_pvalue(
        benchmark_scores, elo_scores
    )
    
    # Calculate 95% bootstrap CI for Spearman
    # Use fast version for bootstrap (no permutation test, much faster)
    print(f"    Computing Spearman bootstrap CI (5000 iterations)...", end='', flush=True)
    spearman_ci_lower, spearman_ci_upper = bootstrap_ci(
        benchmark_scores, elo_scores, calculate_spearman_fast, n_boot=5000
    )
    print(" Done")
    
    # Calculate Kendall correlation with p-value
    kendall_tau, kendall_pvalue = calculate_kendall_with_pvalue(
        benchmark_scores, elo_scores
    )
    
    # Calculate 95% bootstrap CI for Kendall
    # Use fast version for bootstrap (no permutation test, much faster)
    print(f"    Computing Kendall bootstrap CI (5000 iterations)...", end='', flush=True)
    kendall_ci_lower, kendall_ci_upper = bootstrap_ci(
        benchmark_scores, elo_scores, calculate_kendall_fast, n_boot=5000
    )
    print(" Done")
    
    # Calculate RBO
    # RBO requires ranked lists of model IDs (best first)
    # Sort by benchmark scores (descending) to get benchmark ranking
    df_ranked_benchmark = df_paired.sort_values(by=score_col, ascending=False)
    benchmark_ranked = df_ranked_benchmark.index.tolist()
    
    # Sort by ELO scores (descending) to get ELO ranking
    df_ranked_elo = df_paired.sort_values(by=elo_col, ascending=False)
    elo_ranked = df_ranked_elo.index.tolist()
    
    rbo = calculate_rbo(benchmark_ranked, elo_ranked, p=0.9)
    
    return {
        'spearman_rho': spearman_rho,
        'spearman_pvalue': spearman_pvalue,
        'spearman_ci_lower': spearman_ci_lower,
        'spearman_ci_upper': spearman_ci_upper,
        'kendall_tau': kendall_tau,
        'kendall_pvalue': kendall_pvalue,
        'kendall_ci_lower': kendall_ci_lower,
        'kendall_ci_upper': kendall_ci_upper,
        'rbo': rbo
    }


def compute_features_robust(
    master_table_path: Path,
    metadata_path: Path,
    output_path: Path
) -> None:
    """
    Main function to compute all features and correlations.
    
    Args:
        master_table_path: Path to master_correlation_matrix.csv
        metadata_path: Path to metadata.json
        output_path: Path to output analysis_ready_data.csv
    """
    # Load data
    print("Loading master table and metadata...")
    df_master = pd.read_csv(master_table_path)
    df_master = df_master.set_index('model_name')
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Filter to benchmarks only (exclude meta_info and LMArena entries)
    benchmarks = [
        entry for entry in metadata
        if 'benchmark_name' in entry and 'elo_column' not in entry
    ]
    
    print(f"Processing {len(benchmarks)} benchmarks...")
    
    # Results list
    results = []
    
    # Process each benchmark
    for benchmark_entry in benchmarks:
        benchmark_name = benchmark_entry['benchmark_name']
        benchmark_id = sanitize_benchmark_id(benchmark_name)
        category = benchmark_entry.get('category', 'Overall')
        
        print(f"\nProcessing: {benchmark_name} (ID: {benchmark_id}, Category: {category})")
        
        # Get ELO column for this category
        elo_col = get_elo_column_for_category(category)
        
        # Check if benchmark exists in master table
        score_col = f'{benchmark_id}_score'
        if score_col not in df_master.columns:
            print(f"  Warning: {score_col} not found in master table. Skipping.")
            continue
        
        # Calculate Difficulty (exclude Creative Writing v3)
        if benchmark_name != "Creative Writing v3":
            difficulty, is_estimated = calculate_difficulty(df_master, benchmark_id)
            subset_avg_score = 100 - difficulty if not np.isnan(difficulty) else np.nan
        else:
            difficulty = np.nan
            is_estimated = False
            subset_avg_score = np.nan
            print("  Excluding Creative Writing v3 from Difficulty calculation.")
        
        # Calculate CV
        cv = calculate_cv(df_master, benchmark_id)
        print(f"  CV: {cv:.4f}")
        
        # Calculate correlations
        print(f"  Calculating correlations...")
        corr_results = calculate_correlations_with_ci(df_master, benchmark_id, elo_col)
        
        print(f"  Spearman ρ: {corr_results['spearman_rho']:.4f} "
              f"(p={corr_results['spearman_pvalue']:.4f}, "
              f"CI=[{corr_results['spearman_ci_lower']:.4f}, {corr_results['spearman_ci_upper']:.4f}])")
        print(f"  Kendall τ: {corr_results['kendall_tau']:.4f} "
              f"(p={corr_results['kendall_pvalue']:.4f}, "
              f"CI=[{corr_results['kendall_ci_lower']:.4f}, {corr_results['kendall_ci_upper']:.4f}])")
        print(f"  RBO: {corr_results['rbo']:.4f}")
        
        # Halt Protocol: Check high-quality benchmarks
        if benchmark_name in ["MMLU-Pro", "HumanEval"]:
            if corr_results['spearman_rho'] < 0.5:
                print(f"\nCRITICAL: Detected low Spearman correlation (< 0.5) for high-quality "
                      f"benchmark {benchmark_name}. This suggests a data quality issue. "
                      f"Please check: (1) that the correct LMArena ELO column is being used "
                      f"based on the benchmark's category, and (2) that data is loaded "
                      f"correctly from cleaned_data.csv files.")
                raise ValueError(f"Low correlation for {benchmark_name}")
        
        # Compile results
        result_row = {
            'benchmark_name': benchmark_name,
            'benchmark_id': benchmark_id,
            'category': category,
            'subset_avg_score': subset_avg_score,
            'difficulty': difficulty,
            'is_estimated_difficulty': is_estimated,
            'coefficient_of_variation': cv,
            **corr_results,
            **{k: v for k, v in benchmark_entry.items() if k != 'benchmark_name'}
        }
        
        results.append(result_row)
    
    # Create DataFrame
    df_results = pd.DataFrame(results)
    
    # Ensure proper column order
    column_order = [
        'benchmark_name', 'benchmark_id', 'category',
        'subset_avg_score', 'difficulty', 'is_estimated_difficulty', 'coefficient_of_variation',
        'spearman_rho', 'spearman_pvalue', 'spearman_ci_lower', 'spearman_ci_upper',
        'kendall_tau', 'kendall_pvalue', 'kendall_ci_lower', 'kendall_ci_upper',
        'rbo'
    ]
    
    # Add metadata columns
    metadata_columns = [col for col in df_results.columns if col not in column_order]
    column_order.extend(metadata_columns)
    
    # Reorder columns (only include columns that exist)
    column_order = [col for col in column_order if col in df_results.columns]
    df_results = df_results[column_order]
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(output_path, index=False, na_rep='NaN')
    
    print(f"\nSaved analysis-ready data to {output_path}")
    print(f"Shape: {df_results.shape}")


if __name__ == "__main__":
    # Paths
    base_dir = Path(__file__).parent.parent.parent
    master_table_path = base_dir / "data" / "processed" / "master_table" / "master_correlation_matrix.csv"
    metadata_path = base_dir / "data" / "metadata.json"
    output_path = base_dir / "results" / "analysis_ready_data.csv"
    
    compute_features_robust(
        master_table_path=master_table_path,
        metadata_path=metadata_path,
        output_path=output_path
    )

