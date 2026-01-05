"""
Visualization Generation Module

Purpose:
    Generate all figures for the manuscript using seaborn and matplotlib.
    All figures must be saved directly to overleaf/images/ directory.

Figures:
    - Figure 1: Difficulty vs Spearman rho, with point size representing CV
    - Figure 2: Boxplot showing Spearman rho distributions for MCQ vs Generative/Agentic
    - Figure 3a: Boxplot showing Spearman rho distributions across prompt_length categories
    - Figure 3b: Scatterplot showing CV vs Spearman rho by task type
    - Figure 4: Heatmap of correlation matrix between independent variables
    - Figure 5: Ranking comparison scatter plot between SWE-Bench (Verified) and LMArena-Coding
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys
from datetime import datetime
from scipy.stats import spearmanr

# Set style
sns.set_style("whitegrid")
plt.rcParams['font.size'] = 16  # Increased base font size
plt.rcParams['figure.dpi'] = 300

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def ensure_output_directory():
    """Ensure overleaf/images/ directory exists."""
    output_dir = project_root.parent / "overleaf" / "images"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def figure_1_difficulty_variance(df: pd.DataFrame, output_dir: Path):
    """
    Figure 1: Difficulty (subset average score) vs Spearman rho, 
    with point size representing Variance (CV).
    
    Title: "Difficulty (subset average score) (Easy -> Hard) vs. Spearman rho"
    """
    # Exclude Creative Writing v3 (not in Difficulty calculation)
    df_plot = df[df['benchmark_name'] != 'Creative Writing v3'].copy()
    
    # Remove missing values
    df_plot = df_plot[['subset_avg_score', 'spearman_rho', 'coefficient_of_variation']].dropna()
    
    # Log data sources and plot type
    print("Generating scatter plot using data from analysis_ready_data.csv:")
    print("  - Figure description: Difficulty (subset average score) (Easy -> Hard) vs. Spearman rho")
    print("  - X-axis: Difficulty (subset_avg_score column)")
    print("  - Y-axis: Spearman rho (spearman_rho column)")
    print("  - Point size: Coefficient of Variation (coefficient_of_variation column)")
    print("  - Plot type: scatter plot with regression line overlay")
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Create scatter plot with point size representing CV
    scatter = ax.scatter(
        df_plot['subset_avg_score'],
        df_plot['spearman_rho'],
        s=df_plot['coefficient_of_variation'] * 100,  # Scale CV for point size
        alpha=0.6,
        c=df_plot['coefficient_of_variation'],
        cmap='viridis',
        edgecolors='black',
        linewidths=0.5
    )
    
    # Add regression line
    z = np.polyfit(df_plot['subset_avg_score'], df_plot['spearman_rho'], 1)
    p = np.poly1d(z)
    ax.plot(df_plot['subset_avg_score'], p(df_plot['subset_avg_score']), 
            "r--", alpha=0.5, linewidth=2, label='Trend line')
    
    # Labels (title removed)
    ax.set_xlabel('Difficulty (subset average score) (Easy -> Hard)', fontsize=18)
    ax.set_ylabel('Spearman ρ', fontsize=18)
    
    # Increase tick label font size
    ax.tick_params(axis='both', which='major', labelsize=16)
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Coefficient of Variation (CV)', fontsize=16)
    cbar.ax.tick_params(labelsize=16)
    
    # Add legend for point size (optional)
    ax.legend(loc='best', fontsize=16)
    
    plt.tight_layout()
    
    # Save figure
    output_path = output_dir / "Figure_1_Difficulty_Variance.pdf"
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    
    print(f"Figure 1 saved to {output_path}")


def figure_2_task_type(df: pd.DataFrame, output_dir: Path):
    """
    Figure 2: Boxplot with overlaid stripplot showing Spearman rho distributions
    for "MCQ" vs "Generative/Agentic" (Group A).
    
    Exclude "Mixed" benchmarks from the plot.
    Title: "Spearman rho by Task Type"
    """
    # Exclude "Mixed" benchmarks
    df_plot = df[df['task_type'].isin(['MCQ', 'Generation', 'Agentic'])].copy()
    
    # Create Group A (Generative/Agentic)
    df_plot['task_group'] = df_plot['task_type'].apply(
        lambda x: 'Generative/Agentic' if x in ['Generation', 'Agentic'] else 'MCQ'
    )
    
    # Remove missing values
    df_plot = df_plot[['task_group', 'spearman_rho']].dropna()
    
    # Log data sources and plot type
    print("Generating boxplot with stripplot overlay using data from analysis_ready_data.csv:")
    print("  - Figure description: Spearman rho by Task Type")
    print("  - X-axis: Task Type (task_type column, grouped as MCQ vs Generative/Agentic)")
    print("  - Y-axis: Spearman rho (spearman_rho column)")
    print("  - Plot type: boxplot with overlaid stripplot")
    
    fig, ax = plt.subplots(figsize=(6, 6))
    
    # Create boxplot
    box = ax.boxplot(
        [df_plot[df_plot['task_group'] == 'MCQ']['spearman_rho'].values,
         df_plot[df_plot['task_group'] == 'Generative/Agentic']['spearman_rho'].values],
        tick_labels=['MCQ', 'Generative/Agentic'],
        patch_artist=True,
        widths=0.6
    )
    
    # Color the boxes
    colors = ['lightblue', 'lightcoral']
    for patch, color in zip(box['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    # Add stripplot overlay
    for i, group in enumerate(['MCQ', 'Generative/Agentic']):
        data = df_plot[df_plot['task_group'] == group]['spearman_rho'].values
        x_pos = np.random.normal(i + 1, 0.04, size=len(data))
        ax.scatter(x_pos, data, alpha=0.6, s=50, color='black', zorder=3)
    
    ax.set_ylabel('Spearman ρ', fontsize=18)
    ax.set_xlabel('Task Type', fontsize=18)
    
    # Increase tick label font size
    ax.tick_params(axis='both', which='major', labelsize=16)
    
    plt.tight_layout()
    
    # Save figure
    output_path = output_dir / "Figure_2_Task_Type.pdf"
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    
    print(f"Figure 2 saved to {output_path}")


def figure_3a_complexity(df: pd.DataFrame, output_dir: Path):
    """
    Figure 3a: Boxplot with overlaid stripplot showing Spearman rho distributions
    across the four prompt_length categories ("Short", "Medium", "Long", "Extreme").
    
    Title: "Spearman rho by Prompt Length"
    """
    # Remove missing values
    df_plot = df[['prompt_length', 'spearman_rho']].dropna()
    
    # Define order
    order = ['Short', 'Medium', 'Long', 'Extreme']
    df_plot = df_plot[df_plot['prompt_length'].isin(order)]
    
    # Log data sources and plot type
    print("Generating boxplot with stripplot overlay using data from analysis_ready_data.csv:")
    print("  - Figure description: Spearman rho by Prompt Length")
    print("  - X-axis: Prompt Length categories (prompt_length column: Short, Medium, Long, Extreme)")
    print("  - Y-axis: Spearman rho (spearman_rho column)")
    print("  - Plot type: boxplot with overlaid stripplot")
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Prepare data for boxplot
    data_for_boxplot = [df_plot[df_plot['prompt_length'] == cat]['spearman_rho'].values 
                        for cat in order]
    
    # Create boxplot
    box = ax.boxplot(
        data_for_boxplot,
        tick_labels=order,
        patch_artist=True,
        widths=0.6
    )
    
    # Color the boxes
    colors = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow']
    for patch, color in zip(box['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    # Add stripplot overlay
    for i, cat in enumerate(order):
        data = df_plot[df_plot['prompt_length'] == cat]['spearman_rho'].values
        x_pos = np.random.normal(i + 1, 0.04, size=len(data))
        ax.scatter(x_pos, data, alpha=0.6, s=50, color='black', zorder=3)
    
    ax.set_ylabel('Spearman ρ', fontsize=18)
    ax.set_xlabel('Prompt Length', fontsize=18)
    
    # Increase tick label font size
    ax.tick_params(axis='both', which='major', labelsize=16)
    
    plt.tight_layout()
    
    # Save figure
    output_path = output_dir / "Figure_3a_Complexity_Categories.pdf"
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    
    print(f"Figure 3a saved to {output_path}")


def figure_3b_variance_tasktype(df: pd.DataFrame, output_dir: Path):
    """
    Figure 3b: Scatterplot or regplot showing the relationship between CV and Spearman rho,
    with different colors/markers for each task type (MCQ, Generation, Agentic).
    
    Title: "CV vs. Spearman rho by Task Type"
    """
    # Exclude "Mixed" benchmarks
    df_plot = df[df['task_type'].isin(['MCQ', 'Generation', 'Agentic'])].copy()
    
    # Remove missing values
    df_plot = df_plot[['task_type', 'coefficient_of_variation', 'spearman_rho']].dropna()
    
    # Log data sources and plot type
    print("Generating scatter plot with regression lines using data from analysis_ready_data.csv:")
    print("  - Figure description: CV vs. Spearman rho by Task Type")
    print("  - X-axis: Coefficient of Variation (coefficient_of_variation column)")
    print("  - Y-axis: Spearman rho (spearman_rho column)")
    print("  - Color/Marker: Task Type (task_type column: MCQ, Generation, Agentic)")
    print("  - Plot type: scatter plot with task-type-specific regression lines")
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Define colors and markers for each task type
    task_styles = {
        'MCQ': {'color': 'blue', 'marker': 'o', 'label': 'MCQ'},
        'Generation': {'color': 'red', 'marker': 's', 'label': 'Generation'},
        'Agentic': {'color': 'green', 'marker': '^', 'label': 'Agentic'}
    }
    
    # Plot each task type
    for task_type in ['MCQ', 'Generation', 'Agentic']:
        task_data = df_plot[df_plot['task_type'] == task_type]
        if len(task_data) > 0:
            ax.scatter(
                task_data['coefficient_of_variation'],
                task_data['spearman_rho'],
                c=task_styles[task_type]['color'],
                marker=task_styles[task_type]['marker'],
                label=task_styles[task_type]['label'],
                s=100,
                alpha=0.7,
                edgecolors='black',
                linewidths=0.5
            )
            
            # Add regression line for this task type
            if len(task_data) >= 3:
                z = np.polyfit(task_data['coefficient_of_variation'], 
                             task_data['spearman_rho'], 1)
                p = np.poly1d(z)
                x_line = np.linspace(task_data['coefficient_of_variation'].min(),
                                    task_data['coefficient_of_variation'].max(), 100)
                ax.plot(x_line, p(x_line), '--', color=task_styles[task_type]['color'],
                       alpha=0.5, linewidth=2)
    
    ax.set_xlabel('Coefficient of Variation (CV)', fontsize=18)
    ax.set_ylabel('Spearman ρ', fontsize=18)
    
    # Increase tick label font size
    ax.tick_params(axis='both', which='major', labelsize=16)
    
    ax.legend(loc='best', fontsize=16)
    
    plt.tight_layout()
    
    # Save figure
    output_path = output_dir / "Figure_3b_Variance_TaskType.pdf"
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    
    print(f"Figure 3b saved to {output_path}")


def figure_4_confounder_heatmap(df: pd.DataFrame, output_dir: Path):
    """
    Figure 4: Heatmap of the correlation matrix between the Independent Variables themselves.
    
    Variables included:
    - Difficulty (subset_avg_score)
    - Variance (CV)
    - Recency (Release_Date_Ordinal)
    - Complexity (prompt_length as categorical - encode as ordinal)
    - Scale (log(question_count))
    - Task_Type (encoded as binary or ordinal)
    """
    from datetime import datetime
    
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
    
    # Encode prompt_length as ordinal (1, 2, 3, 4)
    prompt_length_map = {'Short': 1, 'Medium': 2, 'Long': 3, 'Extreme': 4}
    df_plot['prompt_length_ordinal'] = df_plot['prompt_length'].map(prompt_length_map)
    
    # Encode task_type as binary (MCQ=0, Generation=1, Agentic=1, Mixed=2)
    task_type_map = {'MCQ': 0, 'Generation': 1, 'Agentic': 1, 'Mixed': 2}
    df_plot['task_type_ordinal'] = df_plot['task_type'].map(task_type_map)
    
    # Create correlation matrix
    corr_vars = [
        'subset_avg_score',  # Difficulty
        'coefficient_of_variation',  # Variance (CV)
        'release_date_ordinal',  # Recency
        'prompt_length_ordinal',  # Complexity
        'question_count'  # Scale (will log transform)
    ]
    
    # Apply log transformation to question_count
    df_plot['log_question_count'] = np.log(df_plot['question_count'])
    corr_vars = [v if v != 'question_count' else 'log_question_count' for v in corr_vars]
    
    # Add task_type_ordinal
    corr_vars.append('task_type_ordinal')
    
    # Select and dropna
    df_corr = df_plot[corr_vars].dropna()
    
    # Calculate correlation matrix
    corr_matrix = df_corr.corr()
    
    # Log data sources and plot type
    print("Generating heatmap using data from analysis_ready_data.csv:")
    print("  - Figure description: Correlation Matrix of Independent Variables")
    print("  - Variables: Difficulty (subset_avg_score), Variance (coefficient_of_variation),")
    print("    Recency (release_date_ordinal), Complexity (prompt_length_ordinal),")
    print("    Scale (log(question_count)), Task Type (task_type_ordinal)")
    print("  - Plot type: correlation heatmap (seaborn heatmap)")
    
    # Create labels
    labels = [
        'Difficulty\n(subset_avg_score)',
        'Variance\n(CV)',
        'Recency\n(release_date)',
        'Complexity\n(prompt_length)',
        'Scale\n(log(question_count))',
        'Task Type\n(ordinal)'
    ]
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    
    heatmap_plot = sns.heatmap(
        corr_matrix,
        annot=True,
        fmt='.2f',
        cmap='coolwarm',
        center=0,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8},
        xticklabels=labels,
        yticklabels=labels,
        ax=ax,
        annot_kws={"size": 16}  # Increase annotation font size
    )
    
    # Increase tick label font size
    ax.tick_params(axis='both', which='major', labelsize=16)
    
    # Increase colorbar label and tick font size
    if hasattr(heatmap_plot, 'collections') and len(heatmap_plot.collections) > 0:
        cbar = heatmap_plot.collections[0].colorbar
        if cbar:
            cbar.ax.tick_params(labelsize=16)
    
    plt.tight_layout()
    
    # Save figure
    output_path = output_dir / "Figure_4_Confounder_Heatmap.pdf"
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    
    print(f"Figure 4 saved to {output_path}")


def figure_5_ranking_comparison(output_dir: Path):
    """
    Figure 5: Scatter plot comparing rankings between SWE-Bench (Verified) and LMArena-Coding.
    
    For models present in both rankings, compute sub-rankings within the intersection set,
    then plot scatter plot with y=x reference line and Spearman correlation coefficient.
    
    Title: "Comparison of large language model (LLM) ranking in SWE-Bench (Verified) and the overall ranking in LMArena-Coding"
    """
    # Load master table
    master_table_path = project_root / "data" / "processed" / "master_table" / "master_correlation_matrix.csv"
    
    # Log data sources and plot type
    print("Generating ranking comparison scatter plot using data from master_correlation_matrix.csv:")
    print("  - Figure description: Comparison of large language model (LLM) ranking in SWE-Bench (Verified) and the overall ranking in LMArena-Coding")
    print("  - X-axis: Rank in SWE-Bench (Verified) (swe_bench_verified_score column)")
    print("  - Y-axis: Rank in LMArena-Coding (elo_coding column)")
    print("  - Plot type: scatter plot with y=x reference line and Spearman correlation")
    
    df_master = pd.read_csv(master_table_path)
    df_master = df_master.set_index('model_name')
    
    # Get columns for SWE-Bench (Verified) and LMArena-Coding
    swe_score_col = 'swe_bench_verified_score'
    swe_rank_col = 'swe_bench_verified_rank'
    elo_coding_col = 'elo_coding'
    
    # Find intersection: models with non-null values in both rankings
    df_intersection = df_master[[swe_score_col, elo_coding_col]].dropna()
    
    if len(df_intersection) < 2:
        print(f"  Warning: Insufficient data for comparison (only {len(df_intersection)} models in intersection)")
        return
    
    # Compute sub-rankings within the intersection set
    # For SWE-Bench: higher score = better, so rank 1 = best
    # Use rank method with ascending=False (higher score gets lower rank number, i.e., rank 1)
    swe_subranks = df_intersection[swe_score_col].rank(method='min', ascending=False).astype(int)
    
    # For LMArena-Coding: higher ELO = better, so rank 1 = best
    # Use rank method with ascending=False (higher ELO gets lower rank number, i.e., rank 1)
    elo_subranks = df_intersection[elo_coding_col].rank(method='min', ascending=False).astype(int)
    
    # Create DataFrame with sub-ranks
    df_plot = pd.DataFrame({
        'swe_subrank': swe_subranks,
        'elo_subrank': elo_subranks
    })
    
    # Calculate Spearman correlation
    spearman_rho, spearman_pvalue = spearmanr(df_plot['swe_subrank'], df_plot['elo_subrank'])
    
    # Create figure (wider aspect ratio for better readability)
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot scatter points
    ax.scatter(
        df_plot['swe_subrank'],
        df_plot['elo_subrank'],
        alpha=0.7,
        s=100,
        color='blue',
        edgecolors='black',
        linewidths=0.5,
        zorder=3
    )
    
    # Add model name labels
    for idx, row in df_plot.iterrows():
        # Shorten model names for readability
        model_name = idx
        # Truncate very long names
        if len(model_name) > 30:
            model_name = model_name[:27] + "..."
        ax.annotate(
            model_name,
            (row['swe_subrank'], row['elo_subrank']),
            fontsize=14,
            alpha=0.8,
            xytext=(5, 5),
            textcoords='offset points',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7, edgecolor='none')
        )
    
    # Add y=x reference line
    max_rank = max(df_plot['swe_subrank'].max(), df_plot['elo_subrank'].max())
    min_rank = min(df_plot['swe_subrank'].min(), df_plot['elo_subrank'].min())
    ax.plot([min_rank, max_rank], [min_rank, max_rank], 
            'r--', linewidth=2, alpha=0.7, label='y = x', zorder=1)
    
    # Set axis labels with (Weak -> Strong) notation
    ax.set_xlabel('Rank in SWE-Bench (Verified) (Weak -> Strong)', fontsize=18)
    ax.set_ylabel('Rank in LMArena-Coding (Weak -> Strong)', fontsize=18)
    
    # Increase tick label font size
    ax.tick_params(axis='both', which='major', labelsize=16)
    
    # Set custom tick locations: 1, 6, 11, 16, 21, 26
    max_rank = max(df_plot['swe_subrank'].max(), df_plot['elo_subrank'].max())
    tick_locations = [1, 6, 11, 16, 21, 26]
    # Filter to only include ticks within the data range
    tick_locations = [t for t in tick_locations if t <= max_rank]
    ax.set_xticks(tick_locations)
    ax.set_yticks(tick_locations)
    
    # Reverse axes so that rank 1 (best) is at the top/right
    # This means higher ranks (worse performance) are closer to origin
    ax.invert_xaxis()
    ax.invert_yaxis()
    
    # Hide top and right spines (borders)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Title removed
    
    # Add Spearman correlation coefficient text box
    corr_text = f'Correlation Coefficient = {spearman_rho:.2f}'
    ax.text(0.98, 0.02, corr_text,
            transform=ax.transAxes,
            fontsize=16,
            verticalalignment='bottom',
            horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='black'),
            zorder=4)
    
    # Add legend with larger font
    ax.legend(loc='upper left', fontsize=16)
    
    # Adjust aspect ratio to make plot flatter (wider)
    ax.set_aspect('auto', adjustable='box')
    
    plt.tight_layout()
    
    # Save figure
    output_path = output_dir / "Figure_5_Ranking_Comparison.pdf"
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    
    print(f"Figure 5 saved to {output_path}")
    print(f"  Spearman ρ = {spearman_rho:.4f}, p-value = {spearman_pvalue:.4f}")
    print(f"  Number of models in intersection: {len(df_plot)}")


def generate_all_plots():
    """Generate all figures for the manuscript."""
    # Load data
    data_path = project_root / "results" / "analysis_ready_data.csv"
    df = pd.read_csv(data_path)
    
    # Ensure output directory exists
    output_dir = ensure_output_directory()
    
    # Setup logging to both console and file
    log_dir = project_root / "results"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"plot_generation_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    class Tee:
        """Class to write to both console and file."""
        def __init__(self, *files):
            self.files = files
        
        def write(self, obj):
            for f in self.files:
                f.write(obj)
                f.flush()
        
        def flush(self):
            for f in self.files:
                f.flush()
    
    # Open log file and create Tee object
    log_file_handle = open(log_file, 'w', encoding='utf-8')
    tee = Tee(sys.stdout, log_file_handle)
    
    # Redirect print to both console and file
    original_print = print
    def log_print(*args, **kwargs):
        kwargs['file'] = tee
        original_print(*args, **kwargs)
    
    # Temporarily replace print
    import builtins
    builtins.print = log_print
    
    try:
        print("=" * 60)
        print(f"Plot Generation Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print(f"Data source: {data_path}")
        print(f"Output directory: {output_dir}")
        print("=" * 60)
        print("Generating figures...")
        print("=" * 60)
        
        # Generate all figures
        figure_1_difficulty_variance(df, output_dir)
        figure_2_task_type(df, output_dir)
        figure_3a_complexity(df, output_dir)
        figure_3b_variance_tasktype(df, output_dir)
        figure_4_confounder_heatmap(df, output_dir)
        figure_5_ranking_comparison(output_dir)
        
        print("=" * 60)
        print("All figures generated successfully!")
        print(f"Log file saved to: {log_file}")
        print("=" * 60)
    finally:
        # Restore original print
        builtins.print = original_print
        log_file_handle.close()


if __name__ == "__main__":
    generate_all_plots()

