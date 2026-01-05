"""
Generate Figures for Manuscript

Purpose:
    This script generates all figures required for the manuscript using seaborn and matplotlib.
    All figures are saved directly to overleaf/images/ directory as PDF files.

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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 9


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


def figure_0_placeholder(output_dir: Path):
    """Create placeholder for SWE-bench Illustration."""
    logger.info("Generating Figure 0: SWE-bench Illustration (placeholder)")
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.text(0.5, 0.5, 'SWE-bench (Verified) Illustration\n(To be completed later)', 
            ha='center', va='center', fontsize=16, 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.set_title('SWE-bench (Verified) Illustration', fontsize=14, fontweight='bold')
    
    output_path = output_dir / "Figure_0_SWE_Bench_Illustration.pdf"
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved Figure 0 to {output_path}")


def figure_1_task_type(df: pd.DataFrame, output_dir: Path):
    """Generate Figure 1: Task Type Comparison (H1)."""
    logger.info("Generating scatter plot using data: Task Type (from analysis_ready_data.csv) vs Spearman rho (from analysis_ready_data.csv)")
    
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
    median_mcq = df_filtered[df_filtered['task_type_grouped'] == 'MCQ']['spearman_rho'].median()
    median_gen = df_filtered[df_filtered['task_type_grouped'] == 'Generative']['spearman_rho'].median()
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Boxplot
    print("Generating boxplot using data: Task Type (from analysis_ready_data.csv) vs Spearman rho (from analysis_ready_data.csv)")
    sns.boxplot(data=df_filtered, x='task_type_grouped', y='spearman_rho', ax=ax, 
                order=['MCQ', 'Generative'], width=0.6)
    
    # Stripplot
    print("Generating stripplot (overlaid) using data: Task Type (from analysis_ready_data.csv) vs Spearman rho (from analysis_ready_data.csv)")
    sns.stripplot(data=df_filtered, x='task_type_grouped', y='spearman_rho', ax=ax,
                  order=['MCQ', 'Generative'], color='black', alpha=0.5, size=5, jitter=True)
    
    ax.set_xlabel('Task Type', fontsize=11)
    ax.set_ylabel('Spearman ρ', fontsize=11)
    ax.set_title('Spearman rho by Task Type', fontsize=12, fontweight='bold')
    
    # Add annotations
    ax.text(0, median_mcq, f'Median: {median_mcq:.3f}\nN={n_mcq}', 
            ha='center', va='bottom', fontsize=9, bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
    ax.text(1, median_gen, f'Median: {median_gen:.3f}\nN={n_gen}', 
            ha='center', va='bottom', fontsize=9, bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
    
    output_path = output_dir / "Figure_1_Task_Type.pdf"
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved Figure 1 to {output_path}")


def figure_2_scale(df: pd.DataFrame, output_dir: Path):
    """Generate Figure 2: Scale Effect (H2)."""
    logger.info("Generating scatter plot using data: log(question_count) (from analysis_ready_data.csv) vs Spearman rho (from analysis_ready_data.csv)")
    
    df_plot = df.copy()
    df_plot['log_question_count'] = np.log(df_plot['question_count'])
    
    # Calculate correlation
    df_clean = df_plot[['log_question_count', 'spearman_rho']].dropna()
    if len(df_clean) > 0:
        corr, p_val = pearsonr(df_clean['log_question_count'], df_clean['spearman_rho'])
    else:
        corr, p_val = np.nan, np.nan
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Scatter plot
    print("Generating scatter plot using data: log(question_count) (from analysis_ready_data.csv) vs Spearman rho (from analysis_ready_data.csv)")
    ax.scatter(df_plot['log_question_count'], df_plot['spearman_rho'], 
               alpha=0.6, s=60, edgecolors='black', linewidth=0.5)
    
    # Regression line
    print("Generating regression plot using data: log(question_count) (from analysis_ready_data.csv) vs Spearman rho (from analysis_ready_data.csv)")
    sns.regplot(data=df_plot, x='log_question_count', y='spearman_rho', ax=ax,
                scatter=False, ci=95, color='red', line_kws={'linewidth': 2})
    
    # Add benchmark labels (if not too crowded)
    for idx, row in df_plot.iterrows():
        if pd.notna(row['log_question_count']) and pd.notna(row['spearman_rho']):
            ax.annotate(row['benchmark_id'], 
                       (row['log_question_count'], row['spearman_rho']),
                       fontsize=7, alpha=0.7, xytext=(3, 3), textcoords='offset points')
    
    ax.set_xlabel('Scale (log-transformed question count)', fontsize=11)
    ax.set_ylabel('Spearman ρ', fontsize=11)
    ax.set_title('Spearman rho by Scale (log(question_count))', fontsize=12, fontweight='bold')
    
    # Add annotations
    n = len(df_clean)
    p_str = f"{p_val:.4f}" if pd.notna(p_val) else "N/A"
    annotation_text = f'r = {corr:.3f}, p = {p_str}\nN = {n}'
    ax.text(0.05, 0.95, annotation_text, transform=ax.transAxes,
            fontsize=9, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    output_path = output_dir / "Figure_2_Scale.pdf"
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved Figure 2 to {output_path}")


def figure_3_complexity(df: pd.DataFrame, output_dir: Path):
    """Generate Figure 3: Complexity Categories (H3)."""
    logger.info("Generating boxplot using data: Prompt Length (from analysis_ready_data.csv) vs Spearman rho (from analysis_ready_data.csv)")
    
    # Order categories
    category_order = ['Short', 'Medium', 'Long', 'Extreme']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Boxplot
    print("Generating boxplot using data: Prompt Length (from analysis_ready_data.csv) vs Spearman rho (from analysis_ready_data.csv)")
    sns.boxplot(data=df, x='prompt_length', y='spearman_rho', ax=ax, order=category_order, width=0.6)
    
    # Stripplot
    print("Generating stripplot (overlaid) using data: Prompt Length (from analysis_ready_data.csv) vs Spearman rho (from analysis_ready_data.csv)")
    sns.stripplot(data=df, x='prompt_length', y='spearman_rho', ax=ax,
                  order=category_order, color='black', alpha=0.5, size=5, jitter=True)
    
    ax.set_xlabel('Prompt Length', fontsize=11)
    ax.set_ylabel('Spearman ρ', fontsize=11)
    ax.set_title('Spearman rho by Prompt Length', fontsize=12, fontweight='bold')
    
    # Add annotations for sample sizes and medians
    for i, cat in enumerate(category_order):
        cat_data = df[df['prompt_length'] == cat]['spearman_rho'].dropna()
        if len(cat_data) > 0:
            n = len(cat_data)
            median = cat_data.median()
            ax.text(i, ax.get_ylim()[1] * 0.95, f'N={n}\nMed={median:.3f}', 
                   ha='center', va='top', fontsize=8, 
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
    
    output_path = output_dir / "Figure_3_Complexity_Categories.pdf"
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved Figure 3 to {output_path}")


def figure_4_recency(df: pd.DataFrame, output_dir: Path):
    """Generate Figure 4: Recency Effect (H4)."""
    logger.info("Generating scatter plot using data: Release Date (from analysis_ready_data.csv) vs Spearman rho (from analysis_ready_data.csv)")
    
    # Convert release_date to ordinal
    reference_date = datetime(2020, 1, 1)
    df_plot = df.copy()
    
    def date_to_ordinal(date_str):
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return (date_obj - reference_date).days
        except:
            return np.nan
    
    df_plot['release_date_ordinal'] = df_plot['release_date'].apply(date_to_ordinal)
    
    # Calculate correlation
    df_clean = df_plot[['release_date_ordinal', 'spearman_rho']].dropna()
    if len(df_clean) > 0:
        corr, p_val = stats.spearmanr(df_clean['release_date_ordinal'], df_clean['spearman_rho'])
    else:
        corr, p_val = np.nan, np.nan
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Scatter plot
    print("Generating scatter plot using data: Release Date (from analysis_ready_data.csv) vs Spearman rho (from analysis_ready_data.csv)")
    ax.scatter(df_plot['release_date_ordinal'], df_plot['spearman_rho'], 
               alpha=0.6, s=60, edgecolors='black', linewidth=0.5)
    
    # Regression line
    print("Generating regression plot using data: Release Date (from analysis_ready_data.csv) vs Spearman rho (from analysis_ready_data.csv)")
    sns.regplot(data=df_plot, x='release_date_ordinal', y='spearman_rho', ax=ax,
                scatter=False, ci=95, color='red', line_kws={'linewidth': 2})
    
    # Add benchmark labels
    for idx, row in df_plot.iterrows():
        if pd.notna(row['release_date_ordinal']) and pd.notna(row['spearman_rho']):
            ax.annotate(row['benchmark_id'], 
                       (row['release_date_ordinal'], row['spearman_rho']),
                       fontsize=7, alpha=0.7, xytext=(3, 3), textcoords='offset points')
    
    ax.set_xlabel('Recency (Days since 2020-01-01)', fontsize=11)
    ax.set_ylabel('Spearman ρ', fontsize=11)
    ax.set_title('Spearman rho by Recency (Release Date)', fontsize=12, fontweight='bold')
    
    # Add annotations
    n = len(df_clean)
    p_str = f"{p_val:.4f}" if pd.notna(p_val) else "N/A"
    annotation_text = f'ρ = {corr:.3f}, p = {p_str}\nN = {n}'
    ax.text(0.05, 0.95, annotation_text, transform=ax.transAxes,
            fontsize=9, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    output_path = output_dir / "Figure_4_Recency.pdf"
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved Figure 4 to {output_path}")


def figure_5_difficulty_variance(df: pd.DataFrame, output_dir: Path, hypothesis_results: dict):
    """Generate Figure 5: Difficulty-Variance Joint Effect (H5/H6)."""
    logger.info("Generating scatter plot using data: Difficulty (from analysis_ready_data.csv) vs Spearman rho (from analysis_ready_data.csv), with CV encoded as point size and color")
    
    # Exclude Creative Writing v3
    df_plot = df[df['benchmark_id'] != 'Creative Writing v3'].copy()
    df_plot = df_plot[df_plot['difficulty'].notna() & df_plot['cv'].notna() & df_plot['spearman_rho'].notna()].copy()
    
    # Get regression coefficients from hypothesis results
    beta1_key = 'H6_Difficulty_Beta1_spearman_rho'
    beta2_key = 'H5_Variance_Beta2_spearman_rho'
    beta1 = hypothesis_results.get(beta1_key, {}).get('coefficient', np.nan)
    beta2 = hypothesis_results.get(beta2_key, {}).get('coefficient', np.nan)
    p_beta1 = hypothesis_results.get(beta1_key, {}).get('p_raw', np.nan)
    p_beta2 = hypothesis_results.get(beta2_key, {}).get('p_raw', np.nan)
    
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Scatter plot with size and color encoding
    print("Generating scatter plot using data: Difficulty (from analysis_ready_data.csv) vs Spearman rho (from analysis_ready_data.csv), with CV as point size")
    scatter = ax.scatter(df_plot['difficulty'], df_plot['spearman_rho'],
                        s=df_plot['cv'] * 200,  # Scale CV for visibility
                        c=df_plot['cv'], cmap='viridis', alpha=0.6,
                        edgecolors='black', linewidth=0.5)
    
    # Regression line
    print("Generating regression plot using data: Difficulty (from analysis_ready_data.csv) vs Spearman rho (from analysis_ready_data.csv)")
    sns.regplot(data=df_plot, x='difficulty', y='spearman_rho', ax=ax,
                scatter=False, ci=95, color='red', line_kws={'linewidth': 2})
    
    # Add benchmark labels
    for idx, row in df_plot.iterrows():
        ax.annotate(row['benchmark_id'], 
                   (row['difficulty'], row['spearman_rho']),
                   fontsize=7, alpha=0.7, xytext=(3, 3), textcoords='offset points')
    
    ax.set_xlabel('Difficulty (Easy → Hard)', fontsize=11)
    ax.set_ylabel('Spearman ρ', fontsize=11)
    ax.set_title('Difficulty vs. Spearman rho (CV encoded as point size and color)', fontsize=12, fontweight='bold')
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Coefficient of Variation (CV)', fontsize=10)
    
    # Add size legend (approximate)
    sizes = [df_plot['cv'].min(), df_plot['cv'].median(), df_plot['cv'].max()]
    legend_elements = [plt.scatter([], [], s=s*200, c='gray', alpha=0.6, edgecolors='black') 
                      for s in sizes]
    labels = [f'CV = {s:.2f}' for s in sizes]
    ax.legend(legend_elements, labels, title='Point Size (CV)', loc='upper left', fontsize=8)
    
    # Add annotations
    n = len(df_plot)
    p_beta1_str = f"{p_beta1:.4f}" if pd.notna(p_beta1) else "N/A"
    p_beta2_str = f"{p_beta2:.4f}" if pd.notna(p_beta2) else "N/A"
    annotation_text = f'β1(Difficulty) = {beta1:.3f}, p = {p_beta1_str}\n'
    annotation_text += f'β2(CV) = {beta2:.3f}, p = {p_beta2_str}\n'
    annotation_text += f'N = {n}'
    ax.text(0.05, 0.95, annotation_text, transform=ax.transAxes,
            fontsize=9, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    output_path = output_dir / "Figure_5_Difficulty_Variance.pdf"
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved Figure 5 to {output_path}")


def figure_6_confounder_heatmap(df: pd.DataFrame, output_dir: Path):
    """Generate Figure 6: Confounder Correlation Heatmap."""
    logger.info("Generating heatmap using data: Correlation matrix of independent variables (from analysis_ready_data.csv)")
    
    # Prepare variables
    df_plot = df.copy()
    
    # Convert release_date to ordinal
    reference_date = datetime(2020, 1, 1)
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
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Heatmap
    print("Generating heatmap using data: Correlation matrix of independent variables (from analysis_ready_data.csv)")
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.8}, ax=ax,
                vmin=-1, vmax=1, annot_kws={'fontsize': 9})
    
    ax.set_title('Confounder Correlation Heatmap', fontsize=12, fontweight='bold', pad=20)
    
    # Add note
    note_text = 'Complexity: 1=Short, 2=Medium, 3=Long, 4=Extreme\nTask Type: 0=MCQ, 1=Generative'
    ax.text(0.5, -0.15, note_text, transform=ax.transAxes,
            ha='center', fontsize=8, style='italic',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
    
    output_path = output_dir / "Figure_6_Confounder_Heatmap.pdf"
    plt.tight_layout()
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    logger.info(f"Saved Figure 6 to {output_path}")


def main():
    """Main execution function."""
    base_dir = Path(__file__).parent.parent.parent
    data_path = base_dir / "results" / "analysis_ready_data.csv"
    results_path = base_dir / "results" / "hypothesis_test_results.json"
    output_dir = base_dir / "overleaf" / "images"
    
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
    
    figure_0_placeholder(output_dir)
    figure_1_task_type(df, output_dir)
    figure_2_scale(df, output_dir)
    figure_3_complexity(df, output_dir)
    figure_4_recency(df, output_dir)
    figure_5_difficulty_variance(df, output_dir, hypothesis_results)
    figure_6_confounder_heatmap(df, output_dir)
    
    logger.info("\n" + "="*60)
    logger.info("All figures generated successfully!")
    logger.info(f"Figures saved to: {output_dir}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
