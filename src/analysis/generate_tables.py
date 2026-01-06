"""
Generate Tables for Manuscript

Purpose:
    This script generates experimental results tables for the manuscript using
    pandas.DataFrame.to_latex() method. All tables are saved directly to
    ../overleaf/tables/ directory (relative to Human-SIG/) as .tex files.
    CRITICAL: overleaf/ is a separate Git repository at the same level as Human-SIG/, NOT inside it.

Tables Generated:
    - Results Summary Table (Spearman only, for main text)
    - Results Summary Table (Kendall only, for appendix)
    - Results Summary Table (RBO only, for appendix)
    - Correlation Summary Table (optional, for each benchmark)
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def format_pvalue(p_val):
    """
    Format p-value with scientific notation when p < 0.001.
    
    Args:
        p_val: P-value (float or NaN)
        
    Returns:
        Formatted string (e.g., "1.23e-3" or "0.0123")
    """
    if pd.isna(p_val):
        return "N/A"
    if p_val < 0.001:
        return f"{p_val:.2e}"
    else:
        return f"{p_val:.4f}"


def load_significance_report(report_path: Path) -> dict:
    """Load statistical significance report."""
    with open(report_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_analysis_data(data_path: Path) -> pd.DataFrame:
    """Load analysis-ready data."""
    return pd.read_csv(data_path)


def create_results_table_spearman(report: dict, output_path: Path):
    """Create results summary table for Spearman metric only."""
    logger.info("Creating results summary table (Spearman only)...")
    
    # Filter to Spearman results only
    spearman_keys = [k for k in report.keys() if 'spearman_rho' in k and not k.startswith('$')]
    
    rows = []
    for key in sorted(spearman_keys):
        result = report[key]
        if isinstance(result, dict):
            # Extract hypothesis name
            if key.startswith('H1_'):
                hypothesis = 'H1 (Generative)'
            elif key.startswith('H2_'):
                hypothesis = 'H2 (Scale)'
            elif key.startswith('H3_'):
                hypothesis = 'H3 (Complexity)'
            elif key.startswith('H4_'):
                hypothesis = 'H4 (Recency)'
            elif 'H6_Difficulty_Beta1' in key:
                hypothesis = 'H6 (Difficulty)'
            elif 'H5_Variance_Beta2' in key:
                hypothesis = 'H5 (Variance)'
            else:
                hypothesis = key
            
            rows.append({
                'Hypothesis': hypothesis,
                'Effect Size': result.get('effect_size', np.nan),
                'Effect Size Type': result.get('effect_size_type', 'unknown'),
                'p_raw': result.get('p_raw', np.nan),
                'p_corrected': result.get('p_corrected', np.nan),
                'significant_strict': result.get('significant_strict', False),
                'ci_lower': result.get('ci_lower', np.nan),
                'ci_upper': result.get('ci_upper', np.nan)
            })
    
    df = pd.DataFrame(rows)
    
    # Format p-values
    df['p_raw_formatted'] = df['p_raw'].apply(format_pvalue)
    df['p_corrected_formatted'] = df['p_corrected'].apply(format_pvalue)
    
    # Format CI
    df['CI'] = df.apply(
        lambda row: f"[{row['ci_lower']:.3f}, {row['ci_upper']:.3f}]" 
        if pd.notna(row['ci_lower']) and pd.notna(row['ci_upper']) else "N/A",
        axis=1
    )
    
    # Select columns for table
    df_table = df[['Hypothesis', 'Effect Size', 'p_raw_formatted', 'p_corrected_formatted', 
                   'significant_strict', 'CI']].copy()
    df_table.columns = ['Hypothesis', 'Effect Size', 'p (raw)', 'p (corrected)', 
                        'Significant', '95% CI']
    
    # Format effect size
    df_table['Effect Size'] = df_table['Effect Size'].apply(
        lambda x: f"{x:.3f}" if pd.notna(x) else "N/A"
    )
    
    # Convert boolean to Yes/No
    df_table['Significant'] = df_table['Significant'].apply(lambda x: 'Yes' if x else 'No')
    
    # Save to LaTeX
    logger.info(f"Saving table to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        latex_str = df_table.to_latex(
            index=False,
            float_format='%.3f',
            column_format='lrrrrr',
            escape=True,
            longtable=True
        )
        # Remove caption and label lines
        lines = latex_str.split('\n')
        filtered_lines = []
        for line in lines:
            if '\\caption' not in line and '\\label' not in line:
                filtered_lines.append(line)
        latex_str = '\n'.join(filtered_lines)
        # Add bottom rule before \end{longtable}
        latex_str = latex_str.replace('\\end{longtable}', '\\bottomrule\n\\end{longtable}')
        f.write(latex_str)
    
    logger.info("Table saved successfully")


def create_results_table_kendall(report: dict, output_path: Path):
    """Create results summary table for Kendall metric only."""
    logger.info("Creating results summary table (Kendall only)...")
    
    # Filter to Kendall results only
    kendall_keys = [k for k in report.keys() if 'kendall_tau' in k and not k.startswith('$')]
    
    rows = []
    for key in sorted(kendall_keys):
        result = report[key]
        if isinstance(result, dict):
            # Extract hypothesis name
            if key.startswith('H1_'):
                hypothesis = 'H1 (Generative)'
            elif key.startswith('H2_'):
                hypothesis = 'H2 (Scale)'
            elif key.startswith('H3_'):
                hypothesis = 'H3 (Complexity)'
            elif key.startswith('H4_'):
                hypothesis = 'H4 (Recency)'
            elif 'H6_Difficulty_Beta1' in key:
                hypothesis = 'H6 (Difficulty)'
            elif 'H5_Variance_Beta2' in key:
                hypothesis = 'H5 (Variance)'
            else:
                hypothesis = key
            
            rows.append({
                'Hypothesis': hypothesis,
                'Effect Size': result.get('effect_size', np.nan),
                'Effect Size Type': result.get('effect_size_type', 'unknown'),
                'p_raw': result.get('p_raw', np.nan),
                'p_corrected': result.get('p_corrected', np.nan),
                'significant_strict': result.get('significant_strict', False),
                'ci_lower': result.get('ci_lower', np.nan),
                'ci_upper': result.get('ci_upper', np.nan)
            })
    
    df = pd.DataFrame(rows)
    
    # Format p-values
    df['p_raw_formatted'] = df['p_raw'].apply(format_pvalue)
    df['p_corrected_formatted'] = df['p_corrected'].apply(format_pvalue)
    
    # Format CI
    df['CI'] = df.apply(
        lambda row: f"[{row['ci_lower']:.3f}, {row['ci_upper']:.3f}]" 
        if pd.notna(row['ci_lower']) and pd.notna(row['ci_upper']) else "N/A",
        axis=1
    )
    
    # Select columns for table
    df_table = df[['Hypothesis', 'Effect Size', 'p_raw_formatted', 'p_corrected_formatted', 
                   'significant_strict', 'CI']].copy()
    df_table.columns = ['Hypothesis', 'Effect Size', 'p (raw)', 'p (corrected)', 
                        'Significant', '95% CI']
    
    # Format effect size
    df_table['Effect Size'] = df_table['Effect Size'].apply(
        lambda x: f"{x:.3f}" if pd.notna(x) else "N/A"
    )
    
    # Convert boolean to Yes/No
    df_table['Significant'] = df_table['Significant'].apply(lambda x: 'Yes' if x else 'No')
    
    # Save to LaTeX
    logger.info(f"Saving table to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        latex_str = df_table.to_latex(
            index=False,
            float_format='%.3f',
            column_format='lrrrrr',
            escape=True,
            longtable=True
        )
        # Remove caption and label lines
        lines = latex_str.split('\n')
        filtered_lines = []
        for line in lines:
            if '\\caption' not in line and '\\label' not in line:
                filtered_lines.append(line)
        latex_str = '\n'.join(filtered_lines)
        # Add bottom rule before \end{longtable}
        latex_str = latex_str.replace('\\end{longtable}', '\\bottomrule\n\\end{longtable}')
        f.write(latex_str)
    
    logger.info("Table saved successfully")


def create_results_table_rbo(report: dict, output_path: Path):
    """Create results summary table for RBO metric only."""
    logger.info("Creating results summary table (RBO only)...")
    
    # Filter to RBO results only
    rbo_keys = [k for k in report.keys() if 'rbo' in k and not k.startswith('$')]
    
    rows = []
    for key in sorted(rbo_keys):
        result = report[key]
        if isinstance(result, dict):
            # Extract hypothesis name
            if key.startswith('H1_'):
                hypothesis = 'H1 (Generative)'
            elif key.startswith('H2_'):
                hypothesis = 'H2 (Scale)'
            elif key.startswith('H3_'):
                hypothesis = 'H3 (Complexity)'
            elif key.startswith('H4_'):
                hypothesis = 'H4 (Recency)'
            elif 'H6_Difficulty_Beta1' in key:
                hypothesis = 'H6 (Difficulty)'
            elif 'H5_Variance_Beta2' in key:
                hypothesis = 'H5 (Variance)'
            else:
                hypothesis = key
            
            rows.append({
                'Hypothesis': hypothesis,
                'Effect Size': result.get('effect_size', np.nan),
                'Effect Size Type': result.get('effect_size_type', 'unknown'),
                'p_raw': result.get('p_raw', np.nan),
                'p_corrected': result.get('p_corrected', np.nan),
                'significant_strict': result.get('significant_strict', False)
            })
    
    df = pd.DataFrame(rows)
    
    # Format p-values (RBO doesn't have p-values, but include for consistency)
    df['p_raw_formatted'] = df['p_raw'].apply(format_pvalue)
    df['p_corrected_formatted'] = df['p_corrected'].apply(format_pvalue)
    
    # Select columns for table
    df_table = df[['Hypothesis', 'Effect Size', 'p_raw_formatted', 'p_corrected_formatted', 
                   'significant_strict']].copy()
    df_table.columns = ['Hypothesis', 'Effect Size', 'p (raw)', 'p (corrected)', 'Significant']
    
    # Format effect size
    df_table['Effect Size'] = df_table['Effect Size'].apply(
        lambda x: f"{x:.3f}" if pd.notna(x) else "N/A"
    )
    
    # Convert boolean to Yes/No
    df_table['Significant'] = df_table['Significant'].apply(lambda x: 'Yes' if x else 'No')
    
    # Save to LaTeX
    logger.info(f"Saving table to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        latex_str = df_table.to_latex(
            index=False,
            float_format='%.3f',
            column_format='lrrrr',
            escape=True,
            longtable=True
        )
        # Remove caption and label lines
        lines = latex_str.split('\n')
        filtered_lines = []
        for line in lines:
            if '\\caption' not in line and '\\label' not in line:
                filtered_lines.append(line)
        latex_str = '\n'.join(filtered_lines)
        # Add bottom rule before \end{longtable}
        latex_str = latex_str.replace('\\end{longtable}', '\\bottomrule\n\\end{longtable}')
        f.write(latex_str)
    
    logger.info("Table saved successfully")


def create_correlation_summary_table(df: pd.DataFrame, output_path: Path):
    """Create correlation summary table for each benchmark."""
    logger.info("Creating correlation summary table...")
    
    # Select relevant columns (include category)
    df_table = df[['benchmark_id', 'category', 'spearman_rho', 'spearman_pvalue', 
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
    
    # Create a function to bold minimum values
    def bold_minimum(series):
        """Return bold style for minimum value in series."""
        # Filter out NaN values
        numeric_values = pd.to_numeric(series, errors='coerce')
        valid_mask = ~pd.isna(numeric_values)
        if valid_mask.sum() == 0:
            return [''] * len(series)
        
        min_val = numeric_values[valid_mask].min()
        # Return CSS string for LaTeX conversion
        return ['font-weight: bold;' if pd.notna(val) and val == min_val else '' 
                for val in numeric_values]
    
    # Create a function to italicize non-significant p-values
    def italicize_nonsignificant(series):
        """Return italic style for non-significant p-values (p > 0.05)."""
        numeric_values = pd.to_numeric(series, errors='coerce')
        return ['font-style: italic;' if pd.notna(val) and val > 0.05 else '' 
                for val in numeric_values]
    
    # Create a function to italicize benchmark names where both p-values are non-significant
    def italicize_benchmark_name(series):
        """Return italic style for benchmark names where both p-values are non-significant."""
        # Get the corresponding p-values from df_final (same order as series)
        spearman_pvals = df_final['Spearman p-value'].values
        kendall_pvals = df_final['Kendall p-value'].values
        
        styles = []
        for i in range(len(series)):
            spearman_p = spearman_pvals[i] if i < len(spearman_pvals) else np.nan
            kendall_p = kendall_pvals[i] if i < len(kendall_pvals) else np.nan
            
            # Check if both p-values are non-significant (p > 0.05)
            # Both must be valid numbers and both > 0.05
            both_nonsig = (
                pd.notna(spearman_p) and spearman_p > 0.05 and
                pd.notna(kendall_p) and kendall_p > 0.05
            )
            
            styles.append('font-style: italic;' if both_nonsig else '')
        return styles
    
    # Create Styler and apply formatting
    styler = df_final.style.hide(axis='index')
    
    # Bold minimum values for Spearman ρ, Kendall τ, and RBO columns
    styler = styler.apply(bold_minimum, subset=['Spearman ρ'], axis=0)
    styler = styler.apply(bold_minimum, subset=['Kendall τ'], axis=0)
    styler = styler.apply(bold_minimum, subset=['RBO'], axis=0)
    
    # Italicize non-significant p-values
    styler = styler.apply(italicize_nonsignificant, subset=['Spearman p-value'], axis=0)
    styler = styler.apply(italicize_nonsignificant, subset=['Kendall p-value'], axis=0)
    
    # Italicize benchmark names where both p-values are non-significant
    styler = styler.apply(italicize_benchmark_name, subset=['Benchmark ID'], axis=0)
    
    # Format correlation coefficients
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
            environment='longtable',
            convert_css=True,
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
        # Center the table with slight left shift
        latex_str = latex_str.replace('\\begin{longtable}', '\\setlength{\\LTleft}{-0.5cm}\n\\begin{longtable}')
        # Add bottom rule before \end{longtable}
        latex_str = latex_str.replace('\\end{longtable}', '\\bottomrule\n\\end{longtable}')
        f.write(latex_str)
    
    logger.info("Table saved successfully")


def main():
    """Main execution function."""
    base_dir = Path(__file__).parent.parent.parent  # Human-SIG/
    report_path = base_dir / "results" / "statistical_significance_report.json"
    data_path = base_dir / "results" / "analysis_ready_data.csv"
    # CRITICAL: overleaf/ is a separate repository at the same level as Human-SIG/, NOT inside it
    output_dir = base_dir.parent / "overleaf" / "tables"
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info("Loading data...")
    report = load_significance_report(report_path)
    df = load_analysis_data(data_path)
    
    # Generate tables
    logger.info("\n" + "="*60)
    logger.info("Generating all tables...")
    logger.info("="*60)
    
    create_correlation_summary_table(df, output_dir / "correlation_summary_table.tex")
    create_results_table_spearman(report, output_dir / "results_table_spearman.tex")
    create_results_table_kendall(report, output_dir / "appendix_results_table_kendall.tex")
    create_results_table_rbo(report, output_dir / "appendix_results_table_rbo.tex")
    
    logger.info("\n" + "="*60)
    logger.info("All tables generated successfully!")
    logger.info(f"Tables saved to: {output_dir}")
    logger.info("="*60)


if __name__ == "__main__":
    main()

