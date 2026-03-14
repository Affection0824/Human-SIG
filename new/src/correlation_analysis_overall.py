"""
Correlation Analysis against LMArena Overall

Purpose:
    This script calculates correlation coefficients (Spearman ρ, Kendall τ, RBO) 
    between benchmark scores and LMArena Overall ELO scores for ALL benchmarks,
    ignoring their specific categories.
    
    It generates a LaTeX table with the same format as the original correlation_summary_table.tex.

Original Code Sources:
    - Calculation logic: src/analysis/compute_features_robust.py
    - Table generation: src/analysis/generate_plots_tables.py
    - Statistical functions: src/analysis/stats_utils.py (replicated in new/src/stats_utils.py)

Usage:
    Run this script to generate the correlation summary table in new/results/.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
import sys
import re

print("Starting script execution...", flush=True)

# Add current directory to path to import stats_utils
sys.path.insert(0, str(Path(__file__).parent))

try:
    from stats_utils import (
        calculate_spearman_with_pvalue,
        calculate_kendall_with_pvalue,
        calculate_rbo,
        bootstrap_ci
    )
    print("Successfully imported stats_utils", flush=True)
except ImportError as e:
    print(f"Failed to import stats_utils: {e}", flush=True)
    sys.exit(1)

from scipy.stats import spearmanr, kendalltau

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_metadata(metadata_path: Path) -> Dict[str, Dict]:
    """
    Load metadata and create benchmark lookup dictionary.
    Source: src/analysis/compute_features_robust.py
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


def sanitize_benchmark_id(benchmark_id: str) -> str:
    """
    Sanitize benchmark_id to match column names in master table.
    Source: src/analysis/compute_features_robust.py
    """
    sanitized = re.sub(r'[^\w\-]', '_', benchmark_id)
    sanitized = re.sub(r'_+', '_', sanitized)
    sanitized = sanitized.strip('_')
    return sanitized


def format_pvalue(p_val):
    """
    Format p-value with scientific notation when p < 0.001.
    Source: src/analysis/generate_plots_tables.py
    """
    if pd.isna(p_val):
        return "N/A"
    if p_val < 0.001:
        return f"{p_val:.2e}"
    else:
        return f"{p_val:.4f}"


def calculate_correlations_overall(
    df_master: pd.DataFrame,
    benchmark_id: str,
    benchmark_meta: Dict
) -> Dict:
    """
    Calculate correlations between benchmark scores and LMArena Overall ELO.
    Modified from src/analysis/compute_features_robust.py to force elo_overall.
    """
    # FORCE elo_overall
    elo_col = 'elo_overall'
    
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
    # We are comparing against elo_overall
    if elo_col not in df_master.columns:
         logger.error(f"ELO column {elo_col} not found in master table!")
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

    df_paired = df_master[[score_col, elo_col]].dropna()
    
    n = len(df_paired)
    if n < 2:
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
            'sample_size': n
        }
    
    benchmark_scores = df_paired[score_col].values
    elo_scores = df_paired[elo_col].values
    
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
    def spearman_func(x, y):
        # Direct calculation for bootstrap
        rho, _ = spearmanr(x, y)
        return rho
    
    def kendall_func(x, y):
        # Direct calculation for bootstrap
        tau, _ = kendalltau(x, y)
        return tau
    
    logger.info(f"  Calculating bootstrap CI for {benchmark_id} (N={n})...")
    spearman_ci_lower, spearman_ci_upper = bootstrap_ci(
        benchmark_scores, elo_scores, spearman_func, n_boot=2000
    )
    
    kendall_ci_lower, kendall_ci_upper = bootstrap_ci(
        benchmark_scores, elo_scores, kendall_func, n_boot=2000
    )
    
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


def create_correlation_summary_table_clean(df: pd.DataFrame, output_path: Path):
    """
    Create a clean correlation summary table sorted by Spearman rho descending.
    No special formatting (bold/italics).
    """
    logger.info("Creating clean correlation summary table sorted by Spearman rho...")
    
    # Sort by Spearman rho descending
    df_sorted = df.sort_values('spearman_rho', ascending=False).copy()
    
    # Select relevant columns (include category)
    df_table = df_sorted[['benchmark_id', 'category', 'spearman_rho', 'spearman_pvalue', 
                   'spearman_ci_lower', 'spearman_ci_upper',
                   'kendall_tau', 'kendall_pvalue',
                   'kendall_ci_lower', 'kendall_ci_upper',
                   'rbo', 'sample_size']].copy()
    
    # Rename columns to use spaces
    df_table.columns = ['Benchmark ID', 'Category', 'Spearman ρ', 'Spearman p-value',
                       'Spearman CI Lower', 'Spearman CI Upper',
                       'Kendall τ', 'Kendall p-value',
                       'Kendall CI Lower', 'Kendall CI Upper',
                       'RBO', 'N']
    
    # Simplify Category names
    df_table['Category'] = df_table['Category'].replace({
        'Instruction Following': 'IF',
        'Hard Prompts': 'HP',
        'Creative Writing': 'CW'
    })
    
    # Format CIs before creating final dataframe
    df_table['Spearman CI'] = df_table.apply(
        lambda row: f"[{row['Spearman CI Lower']:.3f}, {row['Spearman CI Upper']:.3f}]"
        if pd.notna(row['Spearman CI Lower']) and pd.notna(row['Spearman CI Upper']) else "N/A",
        axis=1
    )
    df_table['Kendall CI'] = df_table.apply(
        lambda row: f"[{row['Kendall CI Lower']:.3f}, {row['Kendall CI Upper']:.3f}]"
        if pd.notna(row['Kendall CI Lower']) and pd.notna(row['Kendall CI Upper']) else "N/A",
        axis=1
    )
    
    # Select final columns (keep original numeric values for styling)
    df_final = df_table[['Benchmark ID', 'Category', 'Spearman ρ', 'Spearman CI', 'Spearman p-value',
                         'Kendall τ', 'Kendall CI', 'Kendall p-value',
                         'RBO', 'N']].copy()
    
    # Create Styler and apply formatting
    styler = df_final.style.hide(axis='index')
    
    # Format correlation coefficients (simple formatting, no bold/italics)
    styler = styler.format({
        'Spearman ρ': lambda x: f"{x:.3f}" if pd.notna(x) else "N/A",
        'Kendall τ': lambda x: f"{x:.3f}" if pd.notna(x) else "N/A",
        'RBO': lambda x: f"{x:.3f}" if pd.notna(x) else "N/A",
        'Spearman p-value': format_pvalue,
        'Kendall p-value': format_pvalue
    })
    
    # Save to LaTeX
    logger.info(f"Saving table to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        latex_str = styler.to_latex(
            column_format='llrrrrrrrr',
            convert_css=False,  # Disable CSS conversion to avoid bold/italics from styles
            hrules=True
        )
        # Remove caption and label lines
        lines = latex_str.split('\n')
        filtered_lines = []
        for line in lines:
            if '\\caption' not in line and '\\label' not in line:
                filtered_lines.append(line)
        latex_str = '\n'.join(filtered_lines)
        # Simplify column headers: Spearman ρ -> ρ, Kendall τ -> τ
        latex_str = latex_str.replace('Spearman ρ', '$\\rho$')
        latex_str = latex_str.replace('Kendall τ', '$\\tau$')
        latex_str = latex_str.replace('Spearman p-value', 'p-value')
        latex_str = latex_str.replace('Kendall p-value', 'p-value')
        latex_str = latex_str.replace('Spearman CI', 'Spearman CI')
        latex_str = latex_str.replace('Kendall CI', 'Kendall CI')
        # Replace \end{tabular} with \bottomrule\n\end{tabular} if not already present
        if '\\bottomrule' not in latex_str:
            latex_str = latex_str.replace('\\end{tabular}', '\\bottomrule\n\\end{tabular}')
        f.write(latex_str)
    
    logger.info("Clean sorted table saved successfully")


def main():
    print("In main()...", flush=True)
    # Define paths
    base_dir = Path(__file__).parent.parent.parent  # Human-SIG root
    master_table_path = base_dir / "data" / "processed" / "master_table" / "master_correlation_matrix.csv"
    metadata_path = base_dir / "data" / "metadata.json"
    
    # Output directory: new/results
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info(f"Loading master table from {master_table_path}...")
    if not master_table_path.exists():
        logger.error(f"Master table not found at {master_table_path}")
        return
        
    df_master = pd.read_csv(master_table_path)
    # Ensure model_name is index for easy access if needed, but we use columns mostly
    # df_master = df_master.set_index('model_name') 
    
    logger.info(f"Loading metadata from {metadata_path}...")
    benchmarks_meta = load_metadata(metadata_path)
    
    results = []
    
    # Process each benchmark
    total_benchmarks = len(benchmarks_meta)
    print(f"Total benchmarks: {total_benchmarks}", flush=True)
    for idx, (benchmark_id, benchmark_meta) in enumerate(benchmarks_meta.items(), 1):
        logger.info(f"Processing {benchmark_id} ({idx}/{total_benchmarks})...")
        
        # Calculate correlations against Overall
        corr_results = calculate_correlations_overall(df_master, benchmark_id, benchmark_meta)
        
        # Combine results
        result_row = {
            'benchmark_id': benchmark_id,
            'category': benchmark_meta.get('category', 'Unknown'), # Keep original category for table grouping
            'spearman_rho': corr_results['spearman_rho'],
            'spearman_pvalue': corr_results['spearman_pvalue'],
            'spearman_ci_lower': corr_results['spearman_ci_lower'],
            'spearman_ci_upper': corr_results['spearman_ci_upper'],
            'kendall_tau': corr_results['kendall_tau'],
            'kendall_pvalue': corr_results['kendall_pvalue'],
            'kendall_ci_lower': corr_results['kendall_ci_lower'],
            'kendall_ci_upper': corr_results['kendall_ci_upper'],
            'rbo': corr_results['rbo'],
            'sample_size': corr_results['sample_size']
        }
        
        results.append(result_row)
    
    # Create DataFrame
    df_results = pd.DataFrame(results)
    
    # Save CSV results just in case
    csv_output_path = results_dir / "correlation_results_overall.csv"
    df_results.to_csv(csv_output_path, index=False)
    logger.info(f"Saved CSV results to {csv_output_path}")
    
    # Generate Sorted Clean LaTeX table
    tex_output_path = results_dir / "correlation_summary_table_overall_sorted.tex"
    create_correlation_summary_table_clean(df_results, tex_output_path)
    logger.info(f"Analysis complete. Results saved to {results_dir}")


if __name__ == "__main__":
    main()
