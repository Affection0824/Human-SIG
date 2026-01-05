"""
Table Generation Module for Manuscript

Purpose:
    Generate experimental results tables for the manuscript using pandas.DataFrame.to_latex().
    All tables must be saved directly to overleaf/tables/ directory as .tex files.

Tables:
    - Results Summary Table: Hypothesis test results (p-values, effect sizes, significance)
    - Correlation Summary Table: Correlation coefficients (Spearman ρ, Kendall τ, RBO) 
      with p-values and 95% confidence intervals for each benchmark
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def ensure_output_directory():
    """Ensure overleaf/tables/ directory exists."""
    output_dir = project_root.parent / "overleaf" / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def generate_results_summary_table(report_path: Path, output_dir: Path):
    """
    Generate results summary table from statistical_significance_report.json.
    
    Columns: Hypothesis, Effect Size, Effect Size Type, p_raw, p_corrected, 
             significant_strict, ci_lower, ci_upper (if applicable)
    """
    # Load report
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    # Extract results
    results = report.get('results', {})
    
    # Build DataFrame
    rows = []
    for hyp_key, hyp_data in results.items():
        row = {
            'Hypothesis': hyp_key,
            'Effect Size': hyp_data.get('effect_size', np.nan),
            'Effect Size Type': hyp_data.get('effect_size_type', 'unknown'),
            'p_raw': hyp_data.get('p_raw', np.nan),
            'p_corrected': hyp_data.get('p_corrected', np.nan),
            'Significant': hyp_data.get('significant_strict', False)
        }
        
        # Add CI if available
        if 'ci_lower' in hyp_data and hyp_data['ci_lower'] is not None:
            row['CI Lower'] = hyp_data['ci_lower']
        if 'ci_upper' in hyp_data and hyp_data['ci_upper'] is not None:
            row['CI Upper'] = hyp_data['ci_upper']
        
        # Add sample size if available
        if 'sample_size' in hyp_data:
            row['Sample Size'] = hyp_data['sample_size']
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # Format columns for LaTeX
    # Format p-values and effect sizes
    if 'p_raw' in df.columns:
        df['p_raw'] = df['p_raw'].apply(lambda x: f'{x:.4f}' if pd.notna(x) else '--')
    if 'p_corrected' in df.columns:
        df['p_corrected'] = df['p_corrected'].apply(lambda x: f'{x:.4f}' if pd.notna(x) else '--')
    if 'Effect Size' in df.columns:
        df['Effect Size'] = df['Effect Size'].apply(lambda x: f'{x:.4f}' if pd.notna(x) else '--')
    if 'CI Lower' in df.columns:
        df['CI Lower'] = df['CI Lower'].apply(lambda x: f'{x:.4f}' if pd.notna(x) else '--')
    if 'CI Upper' in df.columns:
        df['CI Upper'] = df['CI Upper'].apply(lambda x: f'{x:.4f}' if pd.notna(x) else '--')
    
    # Convert Significant to Yes/No
    if 'Significant' in df.columns:
        df['Significant'] = df['Significant'].apply(lambda x: 'Yes' if x else 'No')
    
    # Reorder columns
    column_order = ['Hypothesis', 'Effect Size', 'Effect Size Type', 'p_raw', 'p_corrected', 'Significant']
    if 'CI Lower' in df.columns:
        column_order.insert(-1, 'CI Lower')
    if 'CI Upper' in df.columns:
        column_order.insert(-1, 'CI Upper')
    if 'Sample Size' in df.columns:
        column_order.append('Sample Size')
    
    # Select only columns that exist
    column_order = [col for col in column_order if col in df.columns]
    df = df[column_order]
    
    # Rename columns for LaTeX
    df = df.rename(columns={
        'p_raw': 'p (raw)',
        'p_corrected': 'p (corrected)',
        'Effect Size': 'Effect Size',
        'Effect Size Type': 'Effect Type',
        'CI Lower': 'CI Lower',
        'CI Upper': 'CI Upper',
        'Sample Size': 'N'
    })
    
    # Generate LaTeX table
    output_path = output_dir / "results_table.tex"
    
    latex_table = df.to_latex(
        buf=str(output_path),
        index=False,
        float_format='%.4f',
        caption='Hypothesis Test Results Summary',
        label='tab:results_summary',
        column_format='l' + 'r' * (len(df.columns) - 1),
        escape=False,
        na_rep='--'
    )
    
    print(f"Results summary table saved to {output_path}")


def generate_correlation_summary_table(data_path: Path, output_dir: Path):
    """
    Generate correlation summary table for each benchmark.
    
    Format: "Spearman ρ = 0.69 [95% CI: 0.52, 0.82], p = 0.001; 
             Kendall τ = 0.52 [95% CI: 0.35, 0.68], p = 0.003; 
             RBO = 0.85"
    """
    # Load data
    df = pd.read_csv(data_path)
    
    # Build rows for each benchmark
    rows = []
    for _, row in df.iterrows():
        benchmark_name = row['benchmark_name']
        
        # Format Spearman
        spearman_str = f"$\\rho$ = {row['spearman_rho']:.3f}"
        if pd.notna(row['spearman_ci_lower']) and pd.notna(row['spearman_ci_upper']):
            spearman_str += f" [95\\% CI: {row['spearman_ci_lower']:.3f}, {row['spearman_ci_upper']:.3f}]"
        if pd.notna(row['spearman_pvalue']):
            spearman_str += f", $p$ = {row['spearman_pvalue']:.3f}"
        
        # Format Kendall
        kendall_str = f"$\\tau$ = {row['kendall_tau']:.3f}"
        if pd.notna(row['kendall_ci_lower']) and pd.notna(row['kendall_ci_upper']):
            kendall_str += f" [95\\% CI: {row['kendall_ci_lower']:.3f}, {row['kendall_ci_upper']:.3f}]"
        if pd.notna(row['kendall_pvalue']):
            kendall_str += f", $p$ = {row['kendall_pvalue']:.3f}"
        
        # Format RBO
        rbo_str = f"RBO = {row['rbo']:.3f}"
        
        # Combine
        correlation_str = f"{spearman_str}; {kendall_str}; {rbo_str}"
        
        rows.append({
            'Benchmark': benchmark_name,
            'Spearman ρ': f"{row['spearman_rho']:.3f}" if pd.notna(row['spearman_rho']) else '--',
            'Spearman CI': f"[{row['spearman_ci_lower']:.3f}, {row['spearman_ci_upper']:.3f}]" 
                         if pd.notna(row['spearman_ci_lower']) and pd.notna(row['spearman_ci_upper']) else '--',
            'Spearman p': f"{row['spearman_pvalue']:.3f}" if pd.notna(row['spearman_pvalue']) else '--',
            'Kendall τ': f"{row['kendall_tau']:.3f}" if pd.notna(row['kendall_tau']) else '--',
            'Kendall CI': f"[{row['kendall_ci_lower']:.3f}, {row['kendall_ci_upper']:.3f}]" 
                        if pd.notna(row['kendall_ci_lower']) and pd.notna(row['kendall_ci_upper']) else '--',
            'Kendall p': f"{row['kendall_pvalue']:.3f}" if pd.notna(row['kendall_pvalue']) else '--',
            'RBO': f"{row['rbo']:.3f}" if pd.notna(row['rbo']) else '--'
        })
    
    df_table = pd.DataFrame(rows)
    
    # Generate LaTeX table
    output_path = output_dir / "correlation_summary_table.tex"
    
    latex_table = df_table.to_latex(
        buf=str(output_path),
        index=False,
        float_format='%.3f',
        caption='Correlation Summary for All Benchmarks',
        label='tab:correlation_summary',
        column_format='l' + 'r' * (len(df_table.columns) - 1),
        escape=False,
        na_rep='--',
        longtable=True  # Use longtable for long tables
    )
    
    print(f"Correlation summary table saved to {output_path}")


def generate_all_tables():
    """Generate all tables for the manuscript."""
    # Paths
    report_path = project_root / "results" / "statistical_significance_report.json"
    data_path = project_root / "results" / "analysis_ready_data.csv"
    
    # Ensure output directory exists
    output_dir = ensure_output_directory()
    
    print("Generating tables...")
    print("=" * 60)
    
    # Generate tables
    generate_results_summary_table(report_path, output_dir)
    generate_correlation_summary_table(data_path, output_dir)
    
    print("=" * 60)
    print("All tables generated successfully!")


if __name__ == "__main__":
    generate_all_tables()

