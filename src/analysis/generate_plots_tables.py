"""
Generate Figures and Tables for Manuscript

Purpose:
    This script generates all figures and tables required for the manuscript.
    - Figures are saved to ../overleaf/images/ directory as PDF files
    - Tables are saved to ../overleaf/tables/ directory as .tex files
    CRITICAL: overleaf/ is a separate Git repository at the same level as Human-SIG/, NOT inside it.

Figures Generated:
    - Figure 0: SWE-bench Illustration
    - Figures 1-6: Spearman rho versions
    - Figures 7-11: Kendall tau versions
    - Figures 12-16: RBO versions

Tables Generated:
    - Correlation Summary Table
    - Results Summary Table (Spearman)
    - Results Summary Table (Kendall)
    - Results Summary Table (RBO)

Requirements:
    - All axis labels and legends must use spaces instead of underscores
    - All figures must include comprehensive annotations
    - High resolution output (DPI ≥ 300)
    - Save as PDF format
"""
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import pearsonr
from pathlib import Path
from datetime import datetime
import logging
import shutil

# Initialize logging first
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import adjustText
try:
    from adjustText import adjust_text
    HAS_ADJUST_TEXT = True
except ImportError:
    HAS_ADJUST_TEXT = False
    logger.warning("adjustText not available, annotations may overlap")

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
    with open(results_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_significance_report(report_path: Path) -> dict:
    """Load statistical significance report."""
    with open(report_path, 'r', encoding='utf-8') as f:
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
    
    # Load metadata to get complexity
    base_dir = Path(__file__).parent.parent.parent
    metadata_path = base_dir / "data" / "metadata.json"
    
    # Use the passed df (from analysis_ready_data.csv)
    df_plot = df.copy()
    
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
            
    df_plot['complexity'] = df_plot['benchmark_id'].map(complexity_map)
    
    category_order = ['Applying', 'Analyzing', 'Evaluating', 'Creating']
    complexity_val = {c: i+1 for i, c in enumerate(category_order)}
    df_plot['complexity_val'] = df_plot['complexity'].map(complexity_val)
    
    # Filter out missing values
    df_plot = df_plot.dropna(subset=['complexity', metric_col])
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Boxplot
    palette = {'Applying': 'lightblue', 'Analyzing': 'lightgreen', 'Evaluating': 'lightcoral', 'Creating': 'lightyellow'}
    sns.boxplot(data=df_plot, x='complexity', y=metric_col, ax=ax, order=category_order, width=0.6, palette=palette, showfliers=False)
    
    # Stripplot
    for i, cat in enumerate(category_order):
        data_subset = df_plot[df_plot['complexity'] == cat]
        if len(data_subset) > 0:
            x_coords = np.random.normal(i, 0.1, len(data_subset))
            ax.scatter(x_coords, data_subset[metric_col], 
                      color=palette[cat], alpha=0.7, s=80, edgecolors='black', linewidth=0.5, zorder=3)
            
    # Add regression line
    if len(df_plot) > 0:
        slope, intercept, r_value, p_value, std_err = stats.linregress(df_plot['complexity_val'], df_plot[metric_col])
        x_vals = np.array([0, 3])
        y_vals = intercept + slope * (x_vals + 1) # +1 because complexity_val is 1-based
        ax.plot(x_vals, y_vals, color='red', linestyle='--', linewidth=2, label=f'Regression (p={p_value:.3f})', zorder=4)
        ax.legend(fontsize=14, loc='upper left')
    
    ax.set_xlabel('Complexity Level', fontsize=20)
    ax.set_ylabel(ylabel, fontsize=20)
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
    
    # Encode complexity as ordinal
    complexity_map = {'Applying': 1, 'Analyzing': 2, 'Evaluating': 3, 'Creating': 4}
    df_plot['complexity_ordinal'] = df_plot['complexity'].map(complexity_map)
    
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
        'Complexity': 'complexity_ordinal',
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
    note_text = 'Complexity: 1=Applying, 2=Analyzing, 3=Evaluating, 4=Creating\nTask Type: 0=MCQ, 1=Generative'
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
        latex_str = styler.to_latex(
            column_format='llrrrrrrrr',
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


def create_exp1_reference_difficulty_table(base_dir: Path, output_path: Path):
    """Experiment 1: Reference Difficulty Comparison Table."""
    csv_path = base_dir / "results" / "reference_difficulty_comparison.csv"
    print(f"DEBUG: Checking for CSV at {csv_path}")
    print(f"DEBUG: Output path is {output_path}")
    
    if not csv_path.exists():
        print(f"DEBUG: CSV NOT FOUND at {csv_path}")
        logger.warning(f"Experiment 1 data not found at {csv_path}. Skipping table.")
        return
    
    print("DEBUG: Reading CSV...", flush=True)
    try:
        df = pd.read_csv(csv_path)
        print(f"DEBUG: CSV read successfully. Shape: {df.shape}", flush=True)
    except Exception as e:
        print(f"DEBUG: Error reading CSV: {e}", flush=True)
        return

    # We only want Benchmark Name, Original Difficulty, Reference Difficulty
    # The columns in the csv are: Benchmark_Name,Original_Difficulty,Reference_Difficulty,Reference_Avg_Score
    if 'Reference_Avg_Score' in df.columns:
        df = df.drop(columns=['Reference_Avg_Score'])
        
    df.columns = ['Benchmark Name', 'Original Difficulty', 'Reference Difficulty']
    
    # Calculate Pearson correlation
    # Drop rows with NaN for correlation calculation
    df_clean = df.dropna(subset=['Original Difficulty', 'Reference Difficulty'])
    
    if len(df_clean) > 2:
        print("DEBUG: Calculating Pearson r using scipy...", flush=True)
        x = df_clean['Original Difficulty']
        y = df_clean['Reference Difficulty']
        r, p_val = pearsonr(x, y)
        
        # Calculate 95% CI for Pearson r
        z = np.arctanh(r)
        sigma = 1.0 / np.sqrt(len(df_clean) - 3)
        ci_lower = np.tanh(z - 1.96 * sigma)
        ci_upper = np.tanh(z + 1.96 * sigma)
        
        try:
            from stats_utils import format_pvalue
            p_str = format_pvalue(p_val)
        except ImportError:
            if p_val < 0.001:
                p_str = f"{p_val:.2e}"
            else:
                p_str = f"{p_val:.4f}"
        
        stats_rows = [
            {'Benchmark Name': 'Pearson r', 'Original Difficulty': '', 'Reference Difficulty': f"{r:.4f}"},
            {'Benchmark Name': '95% CI', 'Original Difficulty': '', 'Reference Difficulty': f"[{ci_lower:.4f}, {ci_upper:.4f}]"},
            {'Benchmark Name': 'p-value', 'Original Difficulty': '', 'Reference Difficulty': p_str}
        ]
        df_stats = pd.DataFrame(stats_rows)
        df_combined = pd.concat([df, df_stats], ignore_index=True)
    else:
        df_combined = df
    
    with open(output_path, 'w', encoding='utf-8') as f:
        print("DEBUG: Generating LaTeX...", flush=True)
        latex_str = df_combined.to_latex(index=False, float_format="%.2f", escape=True)
        # Add a midrule before the stats
        latex_str = latex_str.replace('Pearson r', '\\midrule\nPearson r')
        lines = latex_str.split('\n')
        filtered_lines = [line for line in lines if '\\caption' not in line and '\\label' not in line]
        latex_str = '\n'.join(filtered_lines)
        if '\\bottomrule' not in latex_str:
            latex_str = latex_str.replace('\\end{tabular}', '\\bottomrule\n\\end{tabular}')
        f.write(latex_str)
    print(f"DEBUG: Saved Exp 1 table to {output_path}", flush=True)
    logger.info(f"Saved Exp 1 table to {output_path}")

def create_exp2_overall_correlation_table(df: pd.DataFrame, output_path: Path):
    """Experiment 2: Compare Category Spearman with Overall Spearman."""
    if 'spearman_rho_overall' not in df.columns:
        logger.warning("Experiment 2 overall correlation data not found. Skipping table.")
        return
        
    df_table = df[['benchmark_id', 'spearman_rho', 'spearman_pvalue', 'spearman_rho_overall', 'spearman_pvalue_overall']].copy()
    df_table = df_table.dropna(subset=['spearman_rho_overall'])
    
    df_table.columns = ['Benchmark ID', 'Category $\\rho$', 'Category p-value', 'Overall $\\rho$', 'Overall p-value']
    
    df_table['Category p-value'] = df_table['Category p-value'].apply(format_pvalue)
    df_table['Overall p-value'] = df_table['Overall p-value'].apply(format_pvalue)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        latex_str = df_table.to_latex(index=False, float_format="%.3f", escape=False)
        lines = latex_str.split('\n')
        filtered_lines = [line for line in lines if '\\caption' not in line and '\\label' not in line]
        latex_str = '\n'.join(filtered_lines)
        if '\\bottomrule' not in latex_str:
            latex_str = latex_str.replace('\\end{tabular}', '\\bottomrule\n\\end{tabular}')
        f.write(latex_str)
    logger.info(f"Saved Exp 2 table to {output_path}")

def create_exp3_uncertainty_table(base_dir: Path, output_path: Path):
    """Experiment 3: Uncertainty Propagation Table."""
    csv_path = base_dir / "results" / "uncertainty_simulation_results.csv"
    if not csv_path.exists():
        logger.warning(f"Experiment 3 data not found at {csv_path}. Skipping table.")
        return
        
    df = pd.read_csv(csv_path)
    
    df_table = pd.DataFrame({
        'Benchmark': df['Benchmark'],
        'N Models': df['N_Samples'],
        'N Questions': df['N_Questions'],
        'Original $\\rho$': df['Orig_Spearman'].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "N/A"),
        'Simulated $\\rho$': df['Simulated_Rho'].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "N/A"),
        'Simulated 95\\% CI': df.apply(lambda row: f"[{row['Simulated_95_CI_Lower']:.3f}, {row['Simulated_95_CI_Upper']:.3f}]" if pd.notna(row['Simulated_95_CI_Lower']) else "N/A", axis=1),
        'Simulated p-value': df['Simulated_P_Value'].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "N/A")
    })
    
    # Sort by Original Rho descending to match markdown
    df_table = df_table.sort_values(by='Original $\\rho$', ascending=False)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        latex_str = df_table.to_latex(index=False, escape=False)
        lines = latex_str.split('\n')
        filtered_lines = [line for line in lines if '\\caption' not in line and '\\label' not in line]
        latex_str = '\n'.join(filtered_lines)
        if '\\bottomrule' not in latex_str:
            latex_str = latex_str.replace('\\end{tabular}', '\\bottomrule\n\\end{tabular}')
        f.write(latex_str)
    logger.info(f"Saved Exp 3 table to {output_path}")

def copy_exp4_regression_images(base_dir: Path, images_output_dir: Path):
    """Experiment 4: Copy univariate regression images to Overleaf with new numbers (17-22)."""
    figures_dir = base_dir / "results" / "figures"
    if not figures_dir.exists():
        logger.warning(f"Experiment 4 figures dir not found at {figures_dir}. Skipping.")
        return
        
    # The regression script creates files like univariate_{x}_vs_{y}.png
    # We want to map them to Figure_17 through Figure_22
    # dependent_vars = ['spearman_rho', 'kendall_tau']
    # independent_vars = ['difficulty', 'cv', 'sample_size']
    
    dependent_vars = ['spearman_rho', 'kendall_tau']
    independent_vars = ['difficulty', 'cv', 'sample_size']
    
    fig_num = 17
    for y in dependent_vars:
        for x in independent_vars:
            src_file = figures_dir / f"Figure_{fig_num}_Regression_{x}_vs_{y}.pdf"
            if src_file.exists():
                dst_file = images_output_dir / f"Figure_{fig_num}_Regression_{x}_vs_{y}.pdf"
                shutil.copy2(src_file, dst_file)
                logger.info(f"Copied {src_file.name} to {dst_file.name}")
            else:
                # Fallback to check if png exists (though we should have generated pdf)
                src_file_png = figures_dir / f"Figure_{fig_num}_Regression_{x}_vs_{y}.png"
                if src_file_png.exists():
                     logger.warning(f"Found PNG instead of PDF for Figure {fig_num}: {src_file_png}")
                else:
                     logger.warning(f"Source file not found: {src_file}")
            fig_num += 1


def perform_univariate_regression_and_plot(df: pd.DataFrame, x_col: str, y_metric: str, 
                                          output_dir: Path, figure_name: str, 
                                          xlabel: str, ylabel: str):
    """
    Perform univariate regression and plot the result.
    
    Args:
        df: DataFrame containing the data
        x_col: Column name for independent variable
        y_metric: Metric name (spearman_rho, kendall_tau, rbo)
        output_dir: Directory to save the plot
        figure_name: Filename for the plot
        xlabel: Label for x-axis
        ylabel: Label for y-axis
    """
    metric_info = get_metric_info(y_metric)
    y_col = metric_info['column']
    
    # Prepare data (drop NaNs)
    # Ensure columns exist
    if x_col not in df.columns or y_col not in df.columns:
        logger.warning(f"Columns {x_col} or {y_col} not found in DataFrame.")
        return None
        
    df_plot = df[[x_col, y_col, 'benchmark_id']].dropna().copy()
    
    if len(df_plot) < 3:
        logger.warning(f"Not enough data points for regression on {x_col} vs {y_col} (N={len(df_plot)})")
        return None
    
    # Perform linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(df_plot[x_col], df_plot[y_col])
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Regression line
    sns.regplot(data=df_plot, x=x_col, y=y_col, ax=ax,
                scatter=False, ci=95, color='red', line_kws={'linewidth': 2, 'zorder': 1})
    
    # Scatter plot
    ax.scatter(df_plot[x_col], df_plot[y_col], 
               alpha=0.6, s=60, edgecolors='black', linewidth=0.5, zorder=5)
    
    # Add benchmark labels
    texts = []
    for idx, row in df_plot.iterrows():
        texts.append(ax.annotate(row['benchmark_id'], 
                   (row[x_col], row[y_col]),
                   fontsize=12, alpha=0.7, zorder=4))
    
    if HAS_ADJUST_TEXT and texts:
        adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))
    
    # Set labels
    ax.set_xlabel(xlabel, fontsize=20)
    ax.set_ylabel(ylabel, fontsize=20)
    ax.tick_params(labelsize=18)
    
    # Add annotations (stats)
    n = len(df_plot)
    p_str = f"{p_value:.4f}" if p_value >= 0.0001 else f"{p_value:.2e}"
    annotation_text = f'Slope (β) = {slope:.3f}, p = {p_str}\nN = {n}'
    
    # Position annotation in bottom right
    ax.text(0.98, 0.02, annotation_text, transform=ax.transAxes,
            fontsize=16, verticalalignment='bottom', ha='right', 
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8), zorder=3)
    
    # Save figure
    output_path = output_dir / figure_name
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved figure to {output_path}")
    
    return {
        'x_variable': x_col,
        'y_metric': y_metric,
        'slope': slope,
        'intercept': intercept,
        'r_value': r_value,
        'p_value': p_value,
        'std_err': std_err,
        'n': n
    }

def generate_regression_figures_and_tables(df: pd.DataFrame, images_output_dir: Path, tables_output_dir: Path):
    """Generate regression figures (17-22) and their corresponding stats table."""
    logger.info("\n" + "="*60)
    logger.info("Generating regression figures (17-22)...")
    logger.info("="*60)

    # Check for missing values in difficulty/cv
    missing_features = df[df['difficulty'].isna() | df['cv'].isna()]
    if not missing_features.empty:
        logger.warning(f"Benchmarks missing difficulty/cv features ({len(missing_features)}):")
        logger.warning(missing_features['benchmark_id'].tolist())
    
    # Perform regressions
    results = []
    metrics = ['spearman_rho', 'kendall_tau', 'rbo']
    fig_num = 17

    # 1. Difficulty vs Correlation
    for metric in metrics:
        metric_name_clean = get_metric_info(metric)['metric_name'].replace(' ', '_').replace('(', '').replace(')', '')
        figure_name = f"Figure_{fig_num}_Difficulty_vs_{metric_name_clean}.pdf"
        
        res = perform_univariate_regression_and_plot(
            df, 
            x_col='difficulty', 
            y_metric=metric, 
            output_dir=images_output_dir, 
            figure_name=figure_name,
            xlabel='Difficulty (Easy → Hard)',
            ylabel=get_metric_info(metric)['ylabel']
        )
        if res:
            res['x_variable'] = 'Difficulty'
            res['Figure'] = f"Figure {fig_num}"
            results.append(res)
        
        fig_num += 1
            
    # 2. Variance (CV) vs Correlation
    for metric in metrics:
        metric_name_clean = get_metric_info(metric)['metric_name'].replace(' ', '_').replace('(', '').replace(')', '')
        figure_name = f"Figure_{fig_num}_CV_vs_{metric_name_clean}.pdf"
        
        res = perform_univariate_regression_and_plot(
            df, 
            x_col='cv', 
            y_metric=metric, 
            output_dir=images_output_dir, 
            figure_name=figure_name,
            xlabel='Variance (CV)',
            ylabel=get_metric_info(metric)['ylabel']
        )
        if res:
            res['x_variable'] = 'Variance (CV)'
            res['Figure'] = f"Figure {fig_num}"
            results.append(res)
        
        fig_num += 1

    if results:
        df_results = pd.DataFrame(results)
        
        # Save to LaTeX
        stats_output_path = tables_output_dir / "regression_analysis_stats.tex"
        with open(stats_output_path, 'w', encoding='utf-8') as f:
            latex_str = df_results.to_latex(index=False, float_format="%.4f", escape=True)
            # Add midrule after header
            lines = latex_str.split('\n')
            filtered_lines = [line for line in lines if '\\caption' not in line and '\\label' not in line]
            latex_str = '\n'.join(filtered_lines)
            if '\\bottomrule' not in latex_str:
                latex_str = latex_str.replace('\\end{tabular}', '\\bottomrule\n\\end{tabular}')
            f.write(latex_str)
        logger.info(f"Saved regression statistics to {stats_output_path}")

# ============================================================================
# Main Execution Function
# ============================================================================

def main():
    """Main execution function - generates both tables and figures."""
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
    logger.info("Generating all tables...")
    logger.info("="*60)
    
    create_correlation_summary_table(df, tables_output_dir / "correlation_summary_table.tex")
    create_results_table_spearman(report, tables_output_dir / "results_table_spearman.tex")
    create_results_table_kendall(report, tables_output_dir / "appendix_results_table_kendall.tex")
    create_results_table_rbo(report, tables_output_dir / "appendix_results_table_rbo.tex")
    
    # New tables for experiments 1, 2, 3
    create_exp1_reference_difficulty_table(base_dir, tables_output_dir / "reference_difficulty_table.tex")
    create_exp2_overall_correlation_table(df, tables_output_dir / "overall_correlation_table.tex")
    create_exp3_uncertainty_table(base_dir, tables_output_dir / "uncertainty_table.tex")
    
    logger.info("\n" + "="*60)
    logger.info("All tables generated successfully!")
    logger.info(f"Tables saved to: {tables_output_dir}")
    logger.info("="*60)
    
    # ========================================================================
    # Generate Figures
    # ========================================================================
    logger.info("\n" + "="*60)
    logger.info("Generating all figures...")
    logger.info("="*60)
    
    # Original figures (Spearman rho)
    figure_0_swe_bench_illustration(images_output_dir)
    figure_1_task_type(df, images_output_dir)
    figure_2_scale(df, images_output_dir)
    figure_3_complexity(df, images_output_dir)
    figure_4_recency(df, images_output_dir)
    figure_5_difficulty_variance(df, images_output_dir, hypothesis_results)
    figure_6_confounder_heatmap(df, images_output_dir)
    
    # Kendall tau versions (Figures 7-11)
    logger.info("\n" + "="*60)
    logger.info("Generating Kendall tau versions (Figures 7-11)...")
    logger.info("="*60)
    figure_task_type(df, images_output_dir, 'kendall_tau', 7)
    figure_scale(df, images_output_dir, 'kendall_tau', 8)
    figure_complexity(df, images_output_dir, 'kendall_tau', 9)
    figure_recency(df, images_output_dir, 'kendall_tau', 10)
    figure_difficulty_variance(df, images_output_dir, hypothesis_results, 'kendall_tau', 11)
    
    # RBO versions (Figures 12-16)
    logger.info("\n" + "="*60)
    logger.info("Generating RBO versions (Figures 12-16)...")
    logger.info("="*60)
    figure_task_type(df, images_output_dir, 'rbo', 12)
    figure_scale(df, images_output_dir, 'rbo', 13)
    figure_complexity(df, images_output_dir, 'rbo', 14)
    figure_recency(df, images_output_dir, 'rbo', 15)
    figure_difficulty_variance(df, images_output_dir, hypothesis_results, 'rbo', 16)
    
    # New figures for experiment 4 (Regression)
    generate_regression_figures_and_tables(df, images_output_dir, tables_output_dir)
    
    logger.info("\n" + "="*60)
    logger.info("All figures generated successfully!")
    logger.info(f"Figures saved to: {images_output_dir}")
    logger.info("="*60)
    
    # Final summary
    logger.info("\n" + "="*60)
    logger.info("ALL TABLES AND FIGURES GENERATED SUCCESSFULLY!")
    logger.info("="*60)


if __name__ == "__main__":
    main()


