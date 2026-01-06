"""
Generate Figures for Manuscript

Purpose:
    This script generates all figures required for the manuscript using seaborn and matplotlib.
    All figures are saved directly to ../overleaf/images/ directory (relative to Human-SIG/) as PDF files.
    CRITICAL: overleaf/ is a separate Git repository at the same level as Human-SIG/, NOT inside it.

Figures Generated:
    - Figure 0: SWE-bench Illustration (placeholder)
    - Figure 1: Task Type Comparison (H1)
    - Figure 2: Scale Effect (H2)
    - Figure 3: Complexity Categories (H3)
    - Figure 4: Recency Effect (H4)
    - Figure 5: Difficulty-Variance Joint Effect (H5/H6)
    - Figure 6: Confounder Correlation Heatmap

Requirements:
    - All axis labels and legends must use spaces instead of underscores
    - All figures must include comprehensive annotations
    - High resolution output (DPI ≥ 300)
    - Save as PDF format
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
from scipy import stats
from scipy.stats import pearsonr
import logging
import shutil
try:
    from adjustText import adjust_text
    HAS_ADJUST_TEXT = True
except ImportError:
    HAS_ADJUST_TEXT = False
    logger.warning("adjustText not available, annotations may overlap")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    logger.info(f"Loaded {len(df)} benchmarks from analysis_ready_data.csv")
    return df


def load_hypothesis_results(results_path: Path) -> dict:
    """Load hypothesis test results."""
    import json
    with open(results_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_metric_info(metric: str):
    """Get metric information for plotting."""
    metric_map = {
        'spearman_rho': {
            'column': 'spearman_rho',
            'ylabel': 'Spearman ρ',
            'metric_name': 'Spearman',
            'metric_symbol': 'ρ'
        },
        'kendall_tau': {
            'column': 'kendall_tau',
            'ylabel': 'Kendall τ',
            'metric_name': 'Kendall',
            'metric_symbol': 'τ'
        },
        'rbo': {
            'column': 'rbo',
            'ylabel': 'RBO',
            'metric_name': 'RBO',
            'metric_symbol': 'RBO'
        }
    }
    return metric_map.get(metric, metric_map['spearman_rho'])


def figure_0_swe_bench_illustration(output_dir: Path):
    """Generate Figure 0: SWE-bench Illustration."""
    logger.info("Generating Figure 0: SWE-bench (Verified) Illustration")
    print("Generating scatter plot using data: SWE-bench (Verified) ranks vs LMArena-Coding ranks (from cleaned_data.csv files)")
    
    base_dir = Path(__file__).parent.parent.parent
    swe_bench_path = base_dir / "data" / "processed" / "cleaned" / "SWE-bench (Verified)"
    lmarena_coding_path = base_dir / "data" / "processed" / "cleaned" / "LMArena-Coding"
    
    # Load data
    swe_bench_df = pd.read_csv(swe_bench_path / "cleaned_data.csv")
    lmarena_coding_df = pd.read_csv(lmarena_coding_path / "cleaned_data.csv")
    
    # Load mapping
    import json
    with open(swe_bench_path / "mapping.json", 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    
    # Get intersection of models (models in mapping.json)
    intersection_models = list(mapping.keys())
    
    # Extract ranks for intersection models
    rank_pairs = []
    model_names = []
    
    for swe_model_name in intersection_models:
        if swe_model_name not in swe_bench_df['model_name'].values:
            continue
        
        lmarena_model_id = mapping[swe_model_name]
        if lmarena_model_id not in lmarena_coding_df['model_name'].values:
            continue
        
        # Get original ranks
        swe_rank_orig = swe_bench_df[swe_bench_df['model_name'] == swe_model_name]['rank'].values[0]
        lmarena_rank_orig = lmarena_coding_df[lmarena_coding_df['model_name'] == lmarena_model_id]['rank'].values[0]
        
        rank_pairs.append({
            'swe_rank_orig': swe_rank_orig,
            'lmarena_rank_orig': lmarena_rank_orig,
            'swe_score': swe_bench_df[swe_bench_df['model_name'] == swe_model_name]['score'].values[0],
            'lmarena_score': lmarena_coding_df[lmarena_coding_df['model_name'] == lmarena_model_id]['score'].values[0],
            'model_name': lmarena_model_id
        })
        model_names.append(lmarena_model_id)
    
    # Re-rank within intersection subset
    rank_df = pd.DataFrame(rank_pairs)
    
    # Re-rank SWE-bench within intersection (lower rank = better, based on score)
    rank_df = rank_df.sort_values('swe_score', ascending=False)  # Higher score = better
    rank_df['swe_rank'] = range(1, len(rank_df) + 1)
    
    # Re-rank LMArena-Coding within intersection (lower rank = better, based on score)
    rank_df = rank_df.sort_values('lmarena_score', ascending=False)  # Higher score = better
    rank_df['lmarena_rank'] = range(1, len(rank_df) + 1)
    
    # Print actual values
    print("  Data values (swe_rank, lmarena_rank):")
    for idx, row in rank_df.iterrows():
        print(f"    {row['swe_rank']}, {row['lmarena_rank']}")
    
    # Create scatter plot (wider/flatter)
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Reference line y=x (red dashed) - draw first (lower zorder)
    max_rank = max(rank_df['swe_rank'].max(), rank_df['lmarena_rank'].max())
    ax.plot([1, max_rank], [1, max_rank], 'r--', linewidth=2, zorder=1)
    
    # Scatter plot - points on top (highest zorder)
    ax.scatter(rank_df['swe_rank'], rank_df['lmarena_rank'], 
               alpha=0.7, s=100, edgecolors='black', linewidth=1.5, zorder=5)
    
    # Annotate model names with larger font, using adjust_text to avoid overlap
    # Text annotations with lower zorder so points are visible on top
    texts = []
    for idx, row in rank_df.iterrows():
        texts.append(ax.annotate(row['model_name'], 
                   (row['swe_rank'], row['lmarena_rank']),
                   fontsize=16, alpha=0.8, zorder=4,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7, edgecolor='none')))
    
    # Use adjust_text to avoid overlapping annotations
    if HAS_ADJUST_TEXT:
        adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))
    
    # Calculate Spearman correlation coefficient
    from scipy.stats import spearmanr
    spearman_rho, spearman_p = spearmanr(rank_df['swe_rank'], rank_df['lmarena_rank'])
    
    # Add Spearman correlation annotation in top left corner
    ax.text(0.02, 0.98, f'Spearman ρ = {spearman_rho:.3f}', fontsize=18, transform=ax.transAxes,
            ha='left', va='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='gray'), zorder=3)
    
    # y=x legend in bottom right corner with red dashed line example
    from matplotlib.lines import Line2D
    legend_elements = [Line2D([0], [0], color='red', linestyle='--', linewidth=2, label='y=x')]
    legend = ax.legend(legend_elements, ['y=x'], loc='lower right', fontsize=18, 
                      framealpha=0.9, fancybox=True, shadow=False)
    legend.set_zorder(3)
    
    # Axis labels (larger font)
    ax.set_xlabel('Rank in SWE-bench (Verified) (Weak → Strong)', fontsize=20)
    ax.set_ylabel('Rank in LMArena-Coding (Weak → Strong)', fontsize=20)
    
    # Axis configuration: origin = weak (high rank), far end = strong (low rank)
    # Keep normal axis direction (1 at origin, max_rank at far end)
    # But labels indicate Weak -> Strong, meaning origin (rank 1) = weak, far end (max_rank) = strong
    # Actually, wait - if rank 1 is best (strong), then origin should show rank 1, and far end shows max_rank (weak)
    # But user says "横纵坐标靠近原点的一端都是排名大（就是表现差）的模型，远端是排名小（表现好）的模型"
    # This means: origin = high rank (weak/bad), far end = low rank (strong/good)
    # So we need to reverse the axis: set xlim to (max_rank, 1) and ylim to (max_rank, 1)
    ax.set_xlim(max_rank + 0.5, 0.5)  # Reversed: high rank (weak) at origin, low rank (strong) at far end
    ax.set_ylim(max_rank + 0.5, 0.5)  # Reversed: high rank (weak) at origin, low rank (strong) at far end
    
    # Tick marks: every 5 ranks starting from 1
    tick_positions = list(range(1, max_rank + 1, 5))
    ax.set_xticks(tick_positions)
    ax.set_yticks(tick_positions)
    ax.set_xticklabels(tick_positions, fontsize=18)
    ax.set_yticklabels(tick_positions, fontsize=18)
    
    # Grid lines: light gray
    ax.grid(True, color='lightgray', linestyle='-', linewidth=0.5, alpha=0.5, zorder=1)
    
    # Remove top and right borders
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # NO TITLE (as per requirements)
    
    output_path = output_dir / "Figure_0_SWE_Bench_Illustration.pdf"
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved Figure 0 to {output_path}")


def figure_task_type(df: pd.DataFrame, output_dir: Path, metric: str = 'spearman_rho', figure_num: int = 1):
    """Generate Task Type Comparison (H1) for different metrics."""
    metric_info = get_metric_info(metric)
    metric_col = metric_info['column']
    ylabel = metric_info['ylabel']
    metric_name = metric_info['metric_name']
    
    logger.info(f"Generating Figure {figure_num}: {metric_name} by Task Type")
    
    # Filter out "Mixed" task types
    df_filtered = df[df['task_type'] != 'Mixed'].copy()
    
    # Merge "Generation" and "Agentic" into "Generative"
    df_filtered['task_type_grouped'] = df_filtered['task_type'].apply(
        lambda x: 'Generative' if x in ['Generation', 'Agentic'] else x
    )
    
    # Get sample sizes
    n_mcq = len(df_filtered[df_filtered['task_type_grouped'] == 'MCQ'])
    n_gen = len(df_filtered[df_filtered['task_type_grouped'] == 'Generative'])
    
    # Get medians
    median_mcq = df_filtered[df_filtered['task_type_grouped'] == 'MCQ'][metric_col].median()
    median_gen = df_filtered[df_filtered['task_type_grouped'] == 'Generative'][metric_col].median()
    
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Boxplot with different light colors for each category
    palette = {'MCQ': 'lightblue', 'Generative': 'lightgreen'}
    sns.boxplot(data=df_filtered, x='task_type_grouped', y=metric_col, ax=ax, 
                order=['MCQ', 'Generative'], width=0.6, palette=palette)
    
    # Stripplot with matching colors for each category
    for task_type in ['MCQ', 'Generative']:
        data_subset = df_filtered[df_filtered['task_type_grouped'] == task_type]
        if len(data_subset) > 0:
            x_pos = 0 if task_type == 'MCQ' else 1
            x_coords = np.random.normal(x_pos, 0.1, len(data_subset))
            ax.scatter(x_coords, data_subset[metric_col], 
                      color=palette[task_type], alpha=0.7, s=80, edgecolors='black', linewidth=0.5, zorder=3)
    
    ax.set_xlabel('Task Type', fontsize=20)
    ax.set_ylabel(ylabel, fontsize=20)
    ax.tick_params(labelsize=18)
    
    # Add annotations OUTSIDE the plot area (below x-axis)
    y_min = ax.get_ylim()[0]
    y_range = ax.get_ylim()[1] - y_min
    
    ax.text(0, y_min - y_range * 0.15, f'Median: {median_mcq:.3f}\nN={n_mcq}', 
            ha='center', va='top', fontsize=16, 
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='gray'))
    ax.text(1, y_min - y_range * 0.15, f'Median: {median_gen:.3f}\nN={n_gen}', 
            ha='center', va='top', fontsize=16,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='gray'))
    
    ax.set_ylim(y_min - y_range * 0.25, ax.get_ylim()[1])
    
    # Determine output filename
    if metric == 'spearman_rho':
        filename = f"Figure_{figure_num}_Task_Type.pdf"
    elif metric == 'kendall_tau':
        filename = f"Figure_{figure_num}_Task_Type_Kendall.pdf"
    else:  # rbo
        filename = f"Figure_{figure_num}_Task_Type_RBO.pdf"
    
    output_path = output_dir / filename
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved Figure {figure_num} to {output_path}")


def figure_1_task_type(df: pd.DataFrame, output_dir: Path):
    """Generate Figure 1: Task Type Comparison (H1) using Spearman rho."""
    figure_task_type(df, output_dir, 'spearman_rho', 1)


def figure_scale(df: pd.DataFrame, output_dir: Path, metric: str = 'spearman_rho', figure_num: int = 2):
    """Generate Scale Effect (H2) for different metrics."""
    metric_info = get_metric_info(metric)
    metric_col = metric_info['column']
    ylabel = metric_info['ylabel']
    metric_name = metric_info['metric_name']
    
    logger.info(f"Generating Figure {figure_num}: Scale Effect with {metric_name}")
    
    df_plot = df.copy()
    df_plot['log_question_count'] = np.log(df_plot['question_count'])
    
    # Calculate correlation
    df_clean = df_plot[['log_question_count', metric_col]].dropna()
    if len(df_clean) > 0:
        corr, p_val = pearsonr(df_clean['log_question_count'], df_clean[metric_col])
    else:
        corr, p_val = np.nan, np.nan
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Regression line
    sns.regplot(data=df_plot, x='log_question_count', y=metric_col, ax=ax,
                scatter=False, ci=95, color='red', line_kws={'linewidth': 2, 'zorder': 1})
    
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
    
    if HAS_ADJUST_TEXT and texts:
        adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))
    
    ax.set_xlabel('Scale (log-transformed question count)', fontsize=20)
    ax.set_ylabel(ylabel, fontsize=20)
    ax.tick_params(labelsize=18)
    
    # Add annotations
    n = len(df_clean)
    p_str = f"{p_val:.4f}" if pd.notna(p_val) else "N/A"
    annotation_text = f'r = {corr:.3f}, p = {p_str}\nN = {n}'
    ax.text(0.05, 0.05, annotation_text, transform=ax.transAxes,
            fontsize=16, verticalalignment='bottom', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8), zorder=3)
    
    # Determine output filename
    if metric == 'spearman_rho':
        filename = f"Figure_{figure_num}_Scale.pdf"
    elif metric == 'kendall_tau':
        filename = f"Figure_{figure_num}_Scale_Kendall.pdf"
    else:  # rbo
        filename = f"Figure_{figure_num}_Scale_RBO.pdf"
    
    output_path = output_dir / filename
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved Figure {figure_num} to {output_path}")


def figure_2_scale(df: pd.DataFrame, output_dir: Path):
    """Generate Figure 2: Scale Effect (H2) using Spearman rho."""
    figure_scale(df, output_dir, 'spearman_rho', 2)


def figure_complexity(df: pd.DataFrame, output_dir: Path, metric: str = 'spearman_rho', figure_num: int = 3):
    """Generate Complexity Categories (H3) for different metrics."""
    metric_info = get_metric_info(metric)
    metric_col = metric_info['column']
    ylabel = metric_info['ylabel']
    metric_name = metric_info['metric_name']
    
    logger.info(f"Generating Figure {figure_num}: Complexity Categories with {metric_name}")
    
    category_order = ['Short', 'Medium', 'Long', 'Extreme']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Boxplot
    palette = {'Short': 'lightblue', 'Medium': 'lightgreen', 'Long': 'lightcoral', 'Extreme': 'lightyellow'}
    sns.boxplot(data=df, x='prompt_length', y=metric_col, ax=ax, order=category_order, width=0.6, palette=palette)
    
    # Stripplot
    for i, cat in enumerate(category_order):
        data_subset = df[df['prompt_length'] == cat]
        if len(data_subset) > 0:
            x_coords = np.random.normal(i, 0.1, len(data_subset))
            ax.scatter(x_coords, data_subset[metric_col], 
                      color=palette[cat], alpha=0.7, s=80, edgecolors='black', linewidth=0.5, zorder=3)
    
    ax.set_xlabel('Prompt Length', fontsize=20)
    ax.set_ylabel(ylabel, fontsize=20)
    ax.tick_params(labelsize=18)
    
    # Add annotations
    for i, cat in enumerate(category_order):
        cat_data = df[df['prompt_length'] == cat][metric_col].dropna()
        if len(cat_data) > 0:
            n = len(cat_data)
            median = cat_data.median()
            ax.text(i, ax.get_ylim()[1] * 0.95, f'N={n}\nMed={median:.3f}', 
                   ha='center', va='top', fontsize=14, 
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
    
    # Determine output filename
    if metric == 'spearman_rho':
        filename = f"Figure_{figure_num}_Complexity_Categories.pdf"
    elif metric == 'kendall_tau':
        filename = f"Figure_{figure_num}_Complexity_Kendall.pdf"
    else:  # rbo
        filename = f"Figure_{figure_num}_Complexity_RBO.pdf"
    
    output_path = output_dir / filename
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved Figure {figure_num} to {output_path}")


def figure_3_complexity(df: pd.DataFrame, output_dir: Path):
    """Generate Figure 3: Complexity Categories (H3) using Spearman rho."""
    figure_complexity(df, output_dir, 'spearman_rho', 3)


def figure_recency(df: pd.DataFrame, output_dir: Path, metric: str = 'spearman_rho', figure_num: int = 4):
    """Generate Recency Effect (H4) for different metrics."""
    metric_info = get_metric_info(metric)
    metric_col = metric_info['column']
    ylabel = metric_info['ylabel']
    metric_name = metric_info['metric_name']
    
    logger.info(f"Generating Figure {figure_num}: Recency Effect with {metric_name}")
    
    reference_date = datetime(2021, 1, 1)
    df_plot = df.copy()
    
    def date_to_ordinal(date_str):
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return (date_obj - reference_date).days
        except:
            return np.nan
    
    df_plot['release_date_ordinal'] = df_plot['release_date'].apply(date_to_ordinal)
    
    # Calculate correlation
    df_clean = df_plot[['release_date_ordinal', metric_col]].dropna()
    if len(df_clean) > 0:
        corr, p_val = stats.spearmanr(df_clean['release_date_ordinal'], df_clean[metric_col])
    else:
        corr, p_val = np.nan, np.nan
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Regression line
    sns.regplot(data=df_plot, x='release_date_ordinal', y=metric_col, ax=ax,
                scatter=False, ci=95, color='red', line_kws={'linewidth': 2, 'zorder': 1})
    
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
    
    if HAS_ADJUST_TEXT and texts:
        adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))
    
    ax.set_xlabel('Recency (Days since 2021-01-01)', fontsize=20)
    ax.set_ylabel(ylabel, fontsize=20)
    ax.tick_params(labelsize=18)
    
    # Add annotations
    n = len(df_clean)
    p_str = f"{p_val:.4f}" if pd.notna(p_val) else "N/A"
    annotation_text = f'ρ = {corr:.3f}, p = {p_str}\nN = {n}'
    ax.text(0.02, 0.02, annotation_text, transform=ax.transAxes,
            fontsize=16, verticalalignment='bottom', ha='left', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8), zorder=3)
    
    # Determine output filename
    if metric == 'spearman_rho':
        filename = f"Figure_{figure_num}_Recency.pdf"
    elif metric == 'kendall_tau':
        filename = f"Figure_{figure_num}_Recency_Kendall.pdf"
    else:  # rbo
        filename = f"Figure_{figure_num}_Recency_RBO.pdf"
    
    output_path = output_dir / filename
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved Figure {figure_num} to {output_path}")


def figure_4_recency(df: pd.DataFrame, output_dir: Path):
    """Generate Figure 4: Recency Effect (H4) using Spearman rho."""
    figure_recency(df, output_dir, 'spearman_rho', 4)


def figure_difficulty_variance(df: pd.DataFrame, output_dir: Path, hypothesis_results: dict, 
                                metric: str = 'spearman_rho', figure_num: int = 5):
    """Generate Difficulty-Variance Joint Effect (H5/H6) for different metrics."""
    metric_info = get_metric_info(metric)
    metric_col = metric_info['column']
    ylabel = metric_info['ylabel']
    metric_name = metric_info['metric_name']
    
    logger.info(f"Generating Figure {figure_num}: Difficulty-Variance with {metric_name}")
    
    # Exclude Creative Writing v3
    df_plot = df[df['benchmark_id'] != 'Creative Writing v3'].copy()
    df_plot = df_plot[df_plot['difficulty'].notna() & df_plot['cv'].notna() & df_plot[metric_col].notna()].copy()
    
    # Get regression coefficients from hypothesis results
    beta1_key = f'H6_Difficulty_Beta1_{metric_col}'
    beta2_key = f'H5_Variance_Beta2_{metric_col}'
    beta1 = hypothesis_results.get(beta1_key, {}).get('coefficient', np.nan)
    beta2 = hypothesis_results.get(beta2_key, {}).get('coefficient', np.nan)
    p_beta1 = hypothesis_results.get(beta1_key, {}).get('p_raw', np.nan)
    p_beta2 = hypothesis_results.get(beta2_key, {}).get('p_raw', np.nan)
    
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Regression line
    sns.regplot(data=df_plot, x='difficulty', y=metric_col, ax=ax,
                scatter=False, ci=95, color='red', line_kws={'linewidth': 2, 'zorder': 1})
    
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
    
    if HAS_ADJUST_TEXT and texts:
        adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))
    
    ax.set_xlabel('Difficulty (Easy → Hard)', fontsize=20)
    ax.set_ylabel(ylabel, fontsize=20)
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
    
    # Determine output filename
    if metric == 'spearman_rho':
        filename = f"Figure_{figure_num}_Difficulty_Variance.pdf"
    elif metric == 'kendall_tau':
        filename = f"Figure_{figure_num}_Difficulty_Variance_Kendall.pdf"
    else:  # rbo
        filename = f"Figure_{figure_num}_Difficulty_Variance_RBO.pdf"
    
    output_path = output_dir / filename
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved Figure {figure_num} to {output_path}")


def figure_5_difficulty_variance(df: pd.DataFrame, output_dir: Path, hypothesis_results: dict):
    """Generate Figure 5: Difficulty-Variance Joint Effect (H5/H6) using Spearman rho."""
    figure_difficulty_variance(df, output_dir, hypothesis_results, 'spearman_rho', 5)


def figure_6_confounder_heatmap(df: pd.DataFrame, output_dir: Path):
    """Generate Figure 6: Confounder Correlation Heatmap."""
    logger.info("Generating heatmap using data: Correlation matrix of independent variables (from analysis_ready_data.csv)")
    
    # Prepare variables
    df_plot = df.copy()
    
    # Convert release_date to ordinal
    reference_date = datetime(2021, 1, 1)
    def date_to_ordinal(date_str):
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return (date_obj - reference_date).days
        except:
            return np.nan
    
    df_plot['release_date_ordinal'] = df_plot['release_date'].apply(date_to_ordinal)
    
    # Encode prompt_length as ordinal
    prompt_length_map = {'Short': 1, 'Medium': 2, 'Long': 3, 'Extreme': 4}
    df_plot['prompt_length_ordinal'] = df_plot['prompt_length'].map(prompt_length_map)
    
    # Encode task_type as binary (0=MCQ, 1=Generative)
    df_plot['task_type_binary'] = df_plot['task_type'].apply(
        lambda x: 1 if x in ['Generation', 'Agentic'] else (0 if x == 'MCQ' else np.nan)
    )
    
    # Calculate log(question_count)
    df_plot['log_question_count'] = np.log(df_plot['question_count'])
    
    # Select variables for correlation matrix
    vars_for_corr = {
        'Difficulty': 'difficulty',
        'Variance (CV)': 'cv',
        'Recency': 'release_date_ordinal',
        'Complexity': 'prompt_length_ordinal',
        'Scale': 'log_question_count',
        'Task Type': 'task_type_binary'
    }
    
    # Build correlation matrix
    corr_data = {}
    for label, col in vars_for_corr.items():
        corr_data[label] = df_plot[col].values
    
    df_corr = pd.DataFrame(corr_data)
    corr_matrix = df_corr.corr()
    
    # Print actual values
    print("Generating heatmap using data: Correlation matrix of independent variables (from analysis_ready_data.csv)")
    print("  Correlation matrix values:")
    print(corr_matrix.to_string())
    
    # Increase figure height and adjust width for better vertical label display
    # Add extra space at bottom for note text
    fig, ax = plt.subplots(figsize=(10, 10))
    fig.subplots_adjust(bottom=0.15)  # Add space at bottom for note text
    
    # Heatmap with larger font
    # Use cbar=False to avoid duplicate colorbar, then add it manually
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                square=True, linewidths=0.5, cbar=False, ax=ax,
                vmin=-1, vmax=1, annot_kws={'fontsize': 16})
    
    # Add colorbar manually (only once)
    sm = plt.cm.ScalarMappable(cmap='coolwarm', norm=plt.Normalize(vmin=-1, vmax=1))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.8)
    cbar.set_label('Correlation', fontsize=16)
    cbar.ax.tick_params(labelsize=16)
    
    # NO TITLE (as per requirements)
    
    # Move axis labels to top and rotate them vertically
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top')
    
    # Rotate x-axis labels vertically
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=90, ha='center')
    plt.setp(ax.yaxis.get_majorticklabels(), rotation=0, ha='right')
    
    # Add note with larger font positioned below the figure (outside the plot area)
    note_text = 'Complexity: 1=Short, 2=Medium, 3=Long, 4=Extreme\nTask Type: 0=MCQ, 1=Generative'
    # Position below the figure using figtext (outside plot area)
    fig.text(0.5, 0.02, note_text, ha='center', va='bottom', fontsize=14, style='italic',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.7), zorder=4)
    
    # Increase tick label font size
    ax.tick_params(labelsize=16, top=True, bottom=False, labeltop=True, labelbottom=False)
    
    output_path = output_dir / "Figure_6_Confounder_Heatmap.pdf"
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved Figure 6 to {output_path}")


# ============================================================================
# Additional figures for Kendall tau and RBO (Figures 7-16)
# ============================================================================

def main():
    """Main execution function."""
    base_dir = Path(__file__).parent.parent.parent  # Human-SIG/
    data_path = base_dir / "results" / "analysis_ready_data.csv"
    results_path = base_dir / "results" / "hypothesis_test_results.json"
    # CRITICAL: overleaf/ is a separate repository at the same level as Human-SIG/, NOT inside it
    output_dir = base_dir.parent / "overleaf" / "images"
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info("Loading data...")
    df = load_analysis_data(data_path)
    hypothesis_results = load_hypothesis_results(results_path)
    
    # Generate all figures
    logger.info("\n" + "="*60)
    logger.info("Generating all figures...")
    logger.info("="*60)
    
    # Original figures (Spearman rho)
    figure_0_swe_bench_illustration(output_dir)
    figure_1_task_type(df, output_dir)
    figure_2_scale(df, output_dir)
    figure_3_complexity(df, output_dir)
    figure_4_recency(df, output_dir)
    figure_5_difficulty_variance(df, output_dir, hypothesis_results)
    figure_6_confounder_heatmap(df, output_dir)
    
    # Kendall tau versions (Figures 7-11)
    logger.info("\n" + "="*60)
    logger.info("Generating Kendall tau versions (Figures 7-11)...")
    logger.info("="*60)
    figure_task_type(df, output_dir, 'kendall_tau', 7)
    figure_scale(df, output_dir, 'kendall_tau', 8)
    figure_complexity(df, output_dir, 'kendall_tau', 9)
    figure_recency(df, output_dir, 'kendall_tau', 10)
    figure_difficulty_variance(df, output_dir, hypothesis_results, 'kendall_tau', 11)
    
    # RBO versions (Figures 12-16)
    logger.info("\n" + "="*60)
    logger.info("Generating RBO versions (Figures 12-16)...")
    logger.info("="*60)
    figure_task_type(df, output_dir, 'rbo', 12)
    figure_scale(df, output_dir, 'rbo', 13)
    figure_complexity(df, output_dir, 'rbo', 14)
    figure_recency(df, output_dir, 'rbo', 15)
    figure_difficulty_variance(df, output_dir, hypothesis_results, 'rbo', 16)
    
    logger.info("\n" + "="*60)
    logger.info("All figures generated successfully!")
    logger.info(f"Figures saved to: {output_dir}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
