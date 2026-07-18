"""
Generate Figures and Tables for Manuscript

Purpose:
    This script generates the five figures and five tables in the manuscript.
    - Figures are saved to ../overleaf/images/ directory as PDF files
    - Tables are saved to ../overleaf/tables/ directory as .tex files
    CRITICAL: overleaf/ is a separate Git repository at the same level as Human-SIG/, NOT inside it.

Figures Generated:
    - Figure 1: SWE-bench illustration
    - Figures 2-5 in the paper: Spearman hypothesis visualizations

Tables Generated:
    - Overall-correlation, reference-difficulty, correlation-summary,
      Spearman-hypothesis, and uncertainty-propagation tables

Requirements:
    - All axis labels and legends must use spaces instead of underscores
    - All figures must include comprehensive annotations
    - High resolution output (DPI ≥ 300)
    - Save as PDF format
"""
import argparse
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from adjustText import adjust_text
from scipy import stats
from scipy.stats import pearsonr
from pathlib import Path
from datetime import datetime
import logging

from figure_1_swe_bench import ensure_figure_1_label_data, render_figure_1_from_file

# Initialize logging first
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
PLOT_SEED = 42

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
# CRITICAL: Significantly larger font sizes for readability (increased beyond minimum)
plt.rcParams['font.size'] = 18
plt.rcParams['axes.labelsize'] = 20
plt.rcParams['axes.titlesize'] = 20
plt.rcParams['xtick.labelsize'] = 18
plt.rcParams['ytick.labelsize'] = 18
plt.rcParams['legend.fontsize'] = 16


def load_analysis_data(data_path: Path) -> pd.DataFrame:
    """Load analysis-ready data."""
    df = pd.read_csv(data_path)
    required = {
        'benchmark_id', 'question_count', 'spearman_rho',
        'spearman_pvalue', 'spearman_ci_lower', 'spearman_ci_upper',
        'kendall_tau', 'kendall_pvalue', 'kendall_ci_lower',
        'kendall_ci_upper', 'rbo', 'sample_size', 'category',
        'complexity', 'release_date', 'difficulty', 'cv',
        'spearman_rho_overall',
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"analysis_ready_data.csv is missing columns: {sorted(missing)}"
        )
    if len(df) != 28 or df['benchmark_id'].nunique() != 28:
        raise ValueError(
            "The manuscript outputs require exactly 28 unique benchmarks; "
            f"found {len(df)} rows and {df['benchmark_id'].nunique()} IDs"
        )
    logger.info(f"Loaded {len(df)} benchmarks from analysis_ready_data.csv")
    return df


def load_hypothesis_results(results_path: Path) -> dict:
    """Load hypothesis test results."""
    with open(results_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_significance_report(report_path: Path) -> dict:
    """Load statistical significance report."""
    with open(report_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def figure_1_swe_bench_illustration(df: pd.DataFrame, output_dir: Path):
    """Generate Figure 1 using the stored main-analysis Spearman result."""
    logger.info("Generating Figure 1: SWE-bench (Verified) Illustration")
    base_dir = Path(__file__).parent.parent.parent
    label_data_path = ensure_figure_1_label_data(base_dir)
    output_path = output_dir / "Figure_1_SWE_Bench_Illustration.pdf"
    rows = df.loc[
        df["benchmark_id"] == "SWE-bench (Verified)",
        "spearman_rho",
    ]
    if len(rows) != 1 or pd.isna(rows.iloc[0]):
        raise ValueError(
            "Figure 1 requires exactly one stored Spearman result for "
            "SWE-bench (Verified)"
        )
    render_figure_1_from_file(
        label_data_path,
        output_path,
        spearman_rho=float(rows.iloc[0]),
    )


def figure_2_scale(df: pd.DataFrame, output_dir: Path):
    """Generate Figure 2: Scale Effect (H1) using Spearman rho."""
    metric_col = 'spearman_rho'
    logger.info("Generating Figure 2: Scale Effect with Spearman rho")
    
    df_plot = df.copy()
    df_plot['log_question_count'] = np.log(df_plot['question_count'])
    
    # Calculate correlation
    df_clean = df_plot[['log_question_count', metric_col]].dropna()
    if len(df_clean) != len(df_plot):
        raise ValueError(
            "Figure 2 requires valid question counts and Spearman rho for all benchmarks"
        )
    corr, p_val = pearsonr(df_clean['log_question_count'], df_clean[metric_col])
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Regression line
    sns.regplot(data=df_plot, x='log_question_count', y=metric_col, ax=ax,
                scatter=False, ci=95, seed=PLOT_SEED, color='red',
                line_kws={'linewidth': 2, 'zorder': 1})
    
    # Scatter plot
    ax.scatter(df_plot['log_question_count'], df_plot[metric_col], 
               alpha=0.6, s=60, edgecolors='black', linewidth=0.5, zorder=5)
    
    # Add benchmark labels
    texts = []
    for idx, row in df_plot.iterrows():
        if pd.notna(row['log_question_count']) and pd.notna(row[metric_col]):
            texts.append(ax.annotate(row['benchmark_id'], 
                       (row['log_question_count'], row[metric_col]),
                       fontsize=12, alpha=0.7, zorder=4))
    
    if texts:
        np.random.seed(PLOT_SEED)
        adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))
    
    ax.set_xlabel('Scale (log-transformed question count)', fontsize=20)
    ax.set_ylabel('Spearman ρ', fontsize=20)
    ax.tick_params(labelsize=18)
    
    # Add annotations
    n = len(df_clean)
    p_str = f"{p_val:.4f}" if pd.notna(p_val) else "N/A"
    annotation_text = f'r = {corr:.3f}, p = {p_str}\nN = {n}'
    ax.text(0.05, 0.05, annotation_text, transform=ax.transAxes,
            fontsize=16, verticalalignment='bottom', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8), zorder=3)
    
    output_path = output_dir / "Figure_2_Scale.pdf"
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved Figure 2 to {output_path}")


def figure_3_complexity(df: pd.DataFrame, output_dir: Path):
    """Generate Figure 3: Complexity Categories (H2) using Spearman rho."""
    metric_col = 'spearman_rho'
    logger.info("Generating Figure 3: Complexity Categories with Spearman rho")
    
    df_plot = df.copy()
    
    category_order = ['Applying', 'Analyzing', 'Evaluating', 'Creating']
    complexity_val = {c: i+1 for i, c in enumerate(category_order)}
    df_plot['complexity_val'] = df_plot['complexity'].map(complexity_val)
    
    # Filter out missing values
    df_plot = df_plot.dropna(subset=['complexity', metric_col])
    if len(df_plot) != len(df):
        raise ValueError(
            "Figure 3 requires complexity and Spearman rho for all benchmarks"
        )
    unexpected = set(df_plot['complexity']) - set(category_order)
    if unexpected:
        raise ValueError(
            f"Figure 3 found unsupported complexity levels: {sorted(unexpected)}"
        )
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Boxplot
    palette = {'Applying': 'lightblue', 'Analyzing': 'lightgreen', 'Evaluating': 'lightcoral', 'Creating': 'lightyellow'}
    sns.boxplot(
        data=df_plot,
        x='complexity',
        y=metric_col,
        hue='complexity',
        ax=ax,
        order=category_order,
        hue_order=category_order,
        width=0.6,
        palette=palette,
        showfliers=False,
        dodge=False,
        legend=False,
    )
    
    # Stripplot
    rng = np.random.default_rng(PLOT_SEED)
    for i, cat in enumerate(category_order):
        data_subset = df_plot[df_plot['complexity'] == cat]
        if len(data_subset) > 0:
            x_coords = rng.normal(i, 0.1, len(data_subset))
            ax.scatter(x_coords, data_subset[metric_col], 
                      color=palette[cat], alpha=0.7, s=80, edgecolors='black', linewidth=0.5, zorder=3)
            
    # Add regression line
    if len(df_plot) > 0:
        slope, intercept, r_value, p_value, std_err = stats.linregress(df_plot['complexity_val'], df_plot[metric_col])
        x_vals = np.array([0, 3])
        y_vals = intercept + slope * (x_vals + 1) # +1 because complexity_val is 1-based
        ax.plot(x_vals, y_vals, color='red', linestyle='--', linewidth=2, label=f'Regression (p={p_value:.3f})', zorder=4)
        ax.legend(fontsize=14, loc='upper left')
    
    ax.set_xlabel('Prompt Complexity', fontsize=20)
    ax.set_ylabel('Spearman ρ', fontsize=20)
    ax.tick_params(labelsize=18)
    
    # Add annotations
    for i, cat in enumerate(category_order):
        cat_data = df_plot[df_plot['complexity'] == cat][metric_col].dropna()
        if len(cat_data) > 0:
            n = len(cat_data)
            median = cat_data.median()
            ax.text(i, ax.get_ylim()[1] * 0.95, f'N={n}\nMed={median:.3f}', 
                   ha='center', va='top', fontsize=14, 
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
    
    output_path = output_dir / "Figure_3_Complexity_Categories.pdf"
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved Figure 3 to {output_path}")


def figure_4_recency(df: pd.DataFrame, output_dir: Path):
    """Generate Figure 4: Recency Effect (H3) using Spearman rho."""
    metric_col = 'spearman_rho'
    logger.info("Generating Figure 4: Recency Effect with Spearman rho")
    
    reference_date = datetime(2021, 1, 1)
    df_plot = df.copy()
    
    def date_to_ordinal(date_str):
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return (date_obj - reference_date).days
        except (TypeError, ValueError):
            return np.nan
    
    df_plot['release_date_ordinal'] = df_plot['release_date'].apply(date_to_ordinal)
    
    # Calculate correlation
    df_clean = df_plot[['release_date_ordinal', metric_col]].dropna()
    if len(df_clean) != len(df_plot):
        raise ValueError(
            "Figure 4 requires valid release dates and Spearman rho for all benchmarks"
        )
    corr, p_val = stats.spearmanr(df_clean['release_date_ordinal'], df_clean[metric_col])
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Regression line
    sns.regplot(data=df_plot, x='release_date_ordinal', y=metric_col, ax=ax,
                scatter=False, ci=95, seed=PLOT_SEED, color='red',
                line_kws={'linewidth': 2, 'zorder': 1})
    
    # Scatter plot
    ax.scatter(df_plot['release_date_ordinal'], df_plot[metric_col], 
               alpha=0.6, s=60, edgecolors='black', linewidth=0.5, zorder=5)
    
    # Add benchmark labels
    texts = []
    for idx, row in df_plot.iterrows():
        if pd.notna(row['release_date_ordinal']) and pd.notna(row[metric_col]):
            texts.append(ax.annotate(row['benchmark_id'], 
                       (row['release_date_ordinal'], row[metric_col]),
                       fontsize=12, alpha=0.7, zorder=4))
    
    if texts:
        np.random.seed(PLOT_SEED)
        adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))
    
    ax.set_xlabel('Recency (Days since 2021-01-01)', fontsize=20)
    ax.set_ylabel('Spearman ρ', fontsize=20)
    ax.tick_params(labelsize=18)
    
    # Add annotations
    n = len(df_clean)
    p_str = f"{p_val:.4f}" if pd.notna(p_val) else "N/A"
    annotation_text = f'ρ = {corr:.3f}, p = {p_str}\nN = {n}'
    ax.text(0.02, 0.02, annotation_text, transform=ax.transAxes,
            fontsize=16, verticalalignment='bottom', ha='left', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8), zorder=3)
    
    output_path = output_dir / "Figure_4_Recency.pdf"
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved Figure 4 to {output_path}")


def figure_5_difficulty_variance(
    df: pd.DataFrame,
    output_dir: Path,
    hypothesis_results: dict,
):
    """Generate Figure 5: joint H4/H5 result using Spearman rho."""
    metric_col = 'spearman_rho'
    logger.info("Generating Figure 5: Difficulty-Variance with Spearman rho")
    
    # Exclude Creative Writing v3
    df_plot = df[df['benchmark_id'] != 'Creative Writing v3'].copy()
    df_plot = df_plot[df_plot['difficulty'].notna() & df_plot['cv'].notna() & df_plot[metric_col].notna()].copy()
    
    # Get regression coefficients from hypothesis results
    beta1_key = 'H5_Difficulty_Beta1_spearman_rho'
    beta2_key = 'H4_Variance_Beta2_spearman_rho'
    beta1 = hypothesis_results.get(beta1_key, {}).get('coefficient', np.nan)
    beta2 = hypothesis_results.get(beta2_key, {}).get('coefficient', np.nan)
    intercept = hypothesis_results.get(beta1_key, {}).get('intercept', np.nan)
    p_beta1 = hypothesis_results.get(beta1_key, {}).get('p_raw', np.nan)
    p_beta2 = hypothesis_results.get(beta2_key, {}).get('p_raw', np.nan)

    if len(df_plot) != 27:
        raise ValueError(
            "Figure 5 requires 27 non-Creative-Writing benchmarks; "
            f"found {len(df_plot)}"
        )
    if not np.all(np.isfinite([intercept, beta1, beta2, p_beta1, p_beta2])):
        raise ValueError(
            "Figure 5 requires finite bivariate Huber coefficients and p-values"
        )

    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Plot the fitted bivariate Huber model at the median observed CV. This is
    # the same model reported in the annotation, rather than an unrelated
    # univariate least-squares fit.
    x_line = np.linspace(df_plot['difficulty'].min(), df_plot['difficulty'].max(), 100)
    median_cv = df_plot['cv'].median()
    y_line = intercept + beta1 * x_line + beta2 * median_cv
    ax.plot(x_line, y_line, color='red', linewidth=2, zorder=1)
    
    # Scatter plot with size and color encoding
    scatter = ax.scatter(df_plot['difficulty'], df_plot[metric_col],
                        s=df_plot['cv'] * 200,
                        c=df_plot['cv'], cmap='viridis', alpha=0.6,
                        edgecolors='black', linewidth=0.5, zorder=5)
    
    # Add benchmark labels
    texts = []
    for idx, row in df_plot.iterrows():
        texts.append(ax.annotate(row['benchmark_id'], 
                   (row['difficulty'], row[metric_col]),
                   fontsize=12, alpha=0.7, zorder=4))
    
    if texts:
        np.random.seed(PLOT_SEED)
        adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))
    
    ax.set_xlabel('Difficulty (Easy → Hard)', fontsize=20)
    ax.set_ylabel('Spearman ρ', fontsize=20)
    ax.tick_params(labelsize=18)
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Coefficient of Variation (CV)', fontsize=16)
    cbar.ax.tick_params(labelsize=16)
    
    # Add size legend
    sizes = [df_plot['cv'].min(), df_plot['cv'].median(), df_plot['cv'].max()]
    legend_elements = [plt.scatter([], [], s=s*200, c='gray', alpha=0.6, edgecolors='black') 
                      for s in sizes]
    labels = [f'CV = {s:.2f}' for s in sizes]
    legend = ax.legend(legend_elements, labels, title='Point Size (CV)', 
                      bbox_to_anchor=(0.75, 0.35), loc='center left', fontsize=14, title_fontsize=16)
    legend.set_zorder(3)
    
    # Add annotations
    n = len(df_plot)
    p_beta1_str = f"{p_beta1:.4f}" if pd.notna(p_beta1) else "N/A"
    p_beta2_str = f"{p_beta2:.4f}" if pd.notna(p_beta2) else "N/A"
    annotation_text = f'β1(Difficulty) = {beta1:.3f}, p = {p_beta1_str}\n'
    annotation_text += f'β2(CV) = {beta2:.3f}, p = {p_beta2_str}\n'
    annotation_text += f'N = {n}'
    ax.text(0.98, 0.02, annotation_text, transform=ax.transAxes,
            fontsize=16, verticalalignment='bottom', ha='right', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8), zorder=3)
    
    output_path = output_dir / "Figure_5_Difficulty_Variance.pdf"
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved Figure 5 to {output_path}")


# ============================================================================
# Table Generation Functions
# ============================================================================

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


def format_hypothesis_name(result_key: str) -> str:
    """Map a result key to the H1-H5 label used in manuscript tables."""
    if result_key.startswith('H1_'):
        return 'H1 (Scale)'
    if result_key.startswith('H2_'):
        return 'H2 (Complexity)'
    if result_key.startswith('H3_'):
        return 'H3 (Recency)'
    if 'H4_Variance_Beta2' in result_key:
        return 'H4 (Variance)'
    if 'H5_Difficulty_Beta1' in result_key:
        return 'H5 (Difficulty)'
    return result_key


def create_results_table_spearman(report: dict, output_path: Path):
    """Create the Spearman hypothesis table.

    For H2, ``effect_size`` is the complementary ordinal-regression R-squared,
    while ``p_raw`` is the primary Kruskal-Wallis p-value.
    """
    logger.info("Creating results summary table (Spearman only)...")
    
    # Filter to Spearman results only
    expected_keys = {
        'H1_spearman_rho',
        'H2_spearman_rho',
        'H3_spearman_rho',
        'H4_Variance_Beta2_spearman_rho',
        'H5_Difficulty_Beta1_spearman_rho',
    }
    missing = expected_keys - set(report)
    if missing:
        raise ValueError(f"Significance report is missing tests: {sorted(missing)}")
    spearman_keys = sorted(expected_keys)
    
    rows = []
    for key in sorted(spearman_keys):
        result = report[key]
        if not isinstance(result, dict):
            raise ValueError(f"Significance report entry {key} is not an object")
        rows.append({
            'Hypothesis': format_hypothesis_name(key),
            'Effect Size': result.get('effect_size', np.nan),
            'Effect Size Type': result.get('effect_size_type', 'unknown'),
            'p_raw': result.get('p_raw', np.nan),
            'p_corrected': result.get('p_corrected', np.nan),
            'is_significant': result.get('is_significant', False),
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
                   'is_significant', 'CI']].copy()
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
            escape=True
        )
        # Remove caption and label lines
        lines = latex_str.split('\n')
        filtered_lines = []
        for line in lines:
            if '\\caption' not in line and '\\label' not in line:
                filtered_lines.append(line)
        latex_str = '\n'.join(filtered_lines)
        # Replace \end{tabular} with \bottomrule\n\end{tabular} if not already present
        if '\\bottomrule' not in latex_str:
            latex_str = latex_str.replace('\\end{tabular}', '\\bottomrule\n\\end{tabular}')
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
        # User requested to add a vertical line after the two p-value columns.
        # The columns are: Benchmark ID (l), Category (l), Spearman ρ (r), Spearman CI (r), Spearman p-value (r), Kendall τ (r), Kendall CI (r), Kendall p-value (r), RBO (r), N (r)
        # So format: llrrr|rrr|r|r
        latex_str = styler.to_latex(
            column_format='llrrr|rrr|r|r',
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
        # Replace \end{tabular} with \bottomrule\n\end{tabular} if not already present
        if '\\bottomrule' not in latex_str:
            latex_str = latex_str.replace('\\end{tabular}', '\\bottomrule\n\\end{tabular}')
        f.write(latex_str)
    
    logger.info("Table saved successfully")


def create_reference_difficulty_table(base_dir: Path, output_path: Path):
    """Create the manuscript's reference-difficulty comparison table."""
    csv_path = base_dir / "results" / "reference_difficulty_comparison.csv"
    logger.info("Creating reference difficulty table from %s", csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"Reference difficulty data not found: {csv_path}")
    df = pd.read_csv(csv_path)

    required = {
        'Benchmark_Name',
        'Original_Difficulty',
        'Reference_Difficulty',
        'Reference_Avg_Score',
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Reference difficulty data is missing columns: {sorted(missing)}"
        )

    # We only want Benchmark Name, Original Difficulty, Reference Difficulty
    # The columns in the csv are: Benchmark_Name,Original_Difficulty,Reference_Difficulty,Reference_Avg_Score
    if 'Reference_Avg_Score' in df.columns:
        df = df.drop(columns=['Reference_Avg_Score'])
        
    df.columns = ['Benchmark Name', 'Original Difficulty', 'Reference Difficulty']
    
    # Calculate Pearson correlation
    # Drop rows with NaN for correlation calculation
    df_clean = df.dropna(subset=['Original Difficulty', 'Reference Difficulty'])
    
    logger.debug("Reference-difficulty table preview before dropna:\n%s", df.head())
    logger.debug("Reference-difficulty clean table shape: %s", df_clean.shape)

    if len(df_clean) <= 3:
        raise ValueError(
            "Reference-difficulty correlation and Fisher-z CI require "
            "at least four complete rows"
        )

    x = df_clean['Original Difficulty']
    y = df_clean['Reference Difficulty']
    r, p_val = pearsonr(x, y)

    # Calculate the Fisher-z 95% CI for Pearson r.
    z = np.arctanh(r)
    sigma = 1.0 / np.sqrt(len(df_clean) - 3)
    ci_lower = np.tanh(z - 1.96 * sigma)
    ci_upper = np.tanh(z + 1.96 * sigma)
    p_str = format_pvalue(p_val)

    stats_rows = [
        {'Benchmark Name': 'Pearson r', 'Original Difficulty': '', 'Reference Difficulty': f"{r:.4f}"},
        {'Benchmark Name': '95% CI', 'Original Difficulty': '', 'Reference Difficulty': f"[{ci_lower:.4f}, {ci_upper:.4f}]"},
        {'Benchmark Name': 'p-value', 'Original Difficulty': '', 'Reference Difficulty': p_str}
    ]
    df_stats = pd.DataFrame(stats_rows)
    df_combined = pd.concat([df, df_stats], ignore_index=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Use to_latex with column_format='lrr' for right alignment of numeric columns
        latex_str = df_combined.to_latex(index=False, float_format="%.2f", escape=True, column_format='lrr')
        # Add a midrule before the stats
        latex_str = latex_str.replace('Pearson r', '\\midrule\nPearson r')
        lines = latex_str.split('\n')
        filtered_lines = [line for line in lines if '\\caption' not in line and '\\label' not in line]
        latex_str = '\n'.join(filtered_lines)
        if '\\bottomrule' not in latex_str:
            latex_str = latex_str.replace('\\end{tabular}', '\\bottomrule\n\\end{tabular}')
        f.write(latex_str)
    logger.info(f"Saved reference difficulty table to {output_path}")

def create_overall_correlation_table(df: pd.DataFrame, output_path: Path):
    """Compare category-specific and Overall Spearman correlations."""
    if 'spearman_rho_overall' not in df.columns:
        raise ValueError("analysis_ready_data.csv has no spearman_rho_overall column")
        
    df_table = df[['benchmark_id', 'spearman_rho', 'spearman_rho_overall']].copy()
    df_table = df_table.dropna(subset=['spearman_rho_overall'])
    
    df_table.columns = ['Benchmark ID', 'Category $\\rho$', 'Overall $\\rho$']
    
    def format_rho_custom(rho):
        if pd.isna(rho):
            return "N/A"
        val_str = f"{rho:.3f}"
        if rho < 0:
            return f"\\bfseries {val_str}"
        return val_str
    
    # Apply formatting
    df_table['Category $\\rho$'] = df_table['Category $\\rho$'].apply(format_rho_custom)
    df_table['Overall $\\rho$'] = df_table['Overall $\\rho$'].apply(format_rho_custom)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # User requested: "All numeric parts (including two rho cols) all RIGHT aligned"
        # Columns are: 'Benchmark ID', 'Category $\rho$', 'Overall $\rho$'
        # Format: lrr
        latex_str = df_table.to_latex(index=False, escape=False, column_format='lrr')
        lines = latex_str.split('\n')
        filtered_lines = [line for line in lines if '\\caption' not in line and '\\label' not in line]
        latex_str = '\n'.join(filtered_lines)
        if '\\bottomrule' not in latex_str:
            latex_str = latex_str.replace('\\end{tabular}', '\\bottomrule\n\\end{tabular}')
        f.write(latex_str)
    logger.info(f"Saved overall correlation table to {output_path}")

def create_uncertainty_table(base_dir: Path, output_path: Path):
    """Create the Monte Carlo uncertainty-propagation table."""
    csv_path = base_dir / "results" / "uncertainty_simulation_results.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Uncertainty data not found: {csv_path}")

    df = pd.read_csv(csv_path)

    required = {
        'Benchmark', 'N_Samples', 'N_Questions', 'Orig_Spearman',
        'Simulated_Rho', 'Simulated_95_CI_Lower',
        'Simulated_95_CI_Upper', 'Nonpositive_Fraction',
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Uncertainty data is missing columns: {sorted(missing)}")

    excluded = df[df['Simulated_Rho'].isna()]['Benchmark'].tolist()
    if excluded != ['Creative Writing v3']:
        raise ValueError(
            "Only Creative Writing v3 may lack uncertainty simulations; "
            f"found {excluded}"
        )

    # Filter out Creative Writing v3
    df = df[df['Benchmark'] != 'Creative Writing v3']
    simulation_columns = [
        'Simulated_Rho',
        'Simulated_95_CI_Lower',
        'Simulated_95_CI_Upper',
        'Nonpositive_Fraction',
    ]
    if len(df) != 27 or df[simulation_columns].isna().any().any():
        raise ValueError(
            "Uncertainty table requires 27 complete simulated benchmarks"
        )

    # Custom formatting functions
    def format_rho_custom(rho):
        if pd.isna(rho):
            return "N/A"
        val_str = f"{rho:.4f}"
        if rho < 0:
            return f"\\bfseries {val_str}"
        return val_str

    def format_fraction(value):
        if pd.isna(value):
            return "N/A"
        val_str = f"{value:.4f}"
        if value > 0.05:
            return f"\\itshape {val_str}"
        return val_str

    df_table = pd.DataFrame({
        'Benchmark': df['Benchmark'],
        'Models': df['N_Samples'],
        'Questions': df['N_Questions'],
        'Original $\\rho$': df['Orig_Spearman'].apply(format_rho_custom),
        'Simulated $\\rho$': df['Simulated_Rho'].apply(format_rho_custom),
        'Simulated 95\\% CI': df.apply(lambda row: f"[{row['Simulated_95_CI_Lower']:.3f}, {row['Simulated_95_CI_Upper']:.3f}]" if pd.notna(row['Simulated_95_CI_Lower']) else "N/A", axis=1),
        'Non-positive fraction': df['Nonpositive_Fraction'].apply(format_fraction)
    })
    
    # Sort by Original Rho descending to match markdown (using raw values for sorting would be better but this maintains current logic order)
    # Re-sort based on original values in df since df_table has formatted strings
    df_table['sort_key'] = df['Orig_Spearman']
    df_table = df_table.sort_values(by='sort_key', ascending=False).drop(columns=['sort_key'])
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Column alignment: First column left (l), rest right (r)
        # Columns: Benchmark, Models, Questions, Original rho, Simulated rho, CI,
        # non-positive fraction
        # Total 7 columns -> lrrrrrr
        latex_str = df_table.to_latex(index=False, escape=False, column_format='lrrrrrr')
        lines = latex_str.split('\n')
        filtered_lines = [line for line in lines if '\\caption' not in line and '\\label' not in line]
        latex_str = '\n'.join(filtered_lines)
        if '\\bottomrule' not in latex_str:
            latex_str = latex_str.replace('\\end{tabular}', '\\bottomrule\n\\end{tabular}')
        f.write(latex_str)
    logger.info(f"Saved uncertainty table to {output_path}")

# ============================================================================
# Main Execution Function
# ============================================================================

def main():
    """Generate the manuscript's five figures and five tables."""
    parser = argparse.ArgumentParser(description="Generate manuscript figures and tables")
    parser.add_argument(
        '--figures',
        type=int,
        nargs='+',
        choices=range(1, 6),
        help='Paper figure numbers to generate (1-5). If omitted, generate all five.',
    )
    parser.add_argument(
        '--tables',
        type=int,
        nargs='+',
        choices=range(1, 6),
        help='Paper table numbers to generate (1-5). If omitted, generate all five.',
    )
    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent.parent  # Human-SIG/
    
    # Data paths
    data_path = base_dir / "results" / "analysis_ready_data.csv"
    results_path = base_dir / "results" / "hypothesis_test_results.json"
    report_path = base_dir / "results" / "statistical_significance_report.json"
    
    # Output directories
    # CRITICAL: overleaf/ is a separate repository at the same level as Human-SIG/, NOT inside it
    tables_output_dir = base_dir.parent / "overleaf" / "tables"
    images_output_dir = base_dir.parent / "overleaf" / "images"
    
    # Create output directories
    tables_output_dir.mkdir(parents=True, exist_ok=True)
    images_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data (shared between tables and figures)
    logger.info("="*60)
    logger.info("Loading data...")
    logger.info("="*60)
    df = load_analysis_data(data_path)
    hypothesis_results = load_hypothesis_results(results_path)
    report = load_significance_report(report_path)
    
    # ========================================================================
    # Generate Tables
    # ========================================================================
    logger.info("\n" + "="*60)
    logger.info("Generating selected tables...")
    logger.info("="*60)
    
    # Table selectors follow the order in which tables appear in the paper.
    if args.tables is None or 1 in args.tables:
        create_overall_correlation_table(df, tables_output_dir / "overall_correlation_table.tex")
    if args.tables is None or 2 in args.tables:
        create_reference_difficulty_table(base_dir, tables_output_dir / "reference_difficulty_table.tex")
    if args.tables is None or 3 in args.tables:
        create_correlation_summary_table(df, tables_output_dir / "correlation_summary_table.tex")
    if args.tables is None or 4 in args.tables:
        create_results_table_spearman(report, tables_output_dir / "results_table_spearman.tex")
    if args.tables is None or 5 in args.tables:
        create_uncertainty_table(base_dir, tables_output_dir / "uncertainty_table.tex")
    
    logger.info("\n" + "="*60)
    logger.info("Selected tables generated successfully!")
    logger.info(f"Tables saved to: {tables_output_dir}")
    logger.info("="*60)
    
    # ========================================================================
    # Generate Figures
    # ========================================================================
    logger.info("\n" + "="*60)
    logger.info("Generating selected figures...")
    logger.info("="*60)
    
    # Figure selectors follow the order in which figures appear in the paper.
    if args.figures is None or 1 in args.figures:
        figure_1_swe_bench_illustration(df, images_output_dir)
    if args.figures is None or 2 in args.figures:
        figure_2_scale(df, images_output_dir)
    if args.figures is None or 3 in args.figures:
        figure_3_complexity(df, images_output_dir)
    if args.figures is None or 4 in args.figures:
        figure_4_recency(df, images_output_dir)
    if args.figures is None or 5 in args.figures:
        figure_5_difficulty_variance(df, images_output_dir, hypothesis_results)
    
    logger.info("\n" + "="*60)
    logger.info("Selected figures generated successfully!")
    logger.info(f"Figures saved to: {images_output_dir}")
    logger.info("="*60)
    
    # Final summary
    logger.info("\n" + "="*60)
    logger.info("SELECTED TABLES AND FIGURES GENERATED SUCCESSFULLY!")
    logger.info("="*60)


if __name__ == "__main__":
    main()


