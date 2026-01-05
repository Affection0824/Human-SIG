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
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys

# Set style
sns.set_style("whitegrid")
plt.rcParams['font.size'] = 10
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
    
    # Labels and title
    ax.set_xlabel('Difficulty (subset average score) (Easy -> Hard)', fontsize=12)
    ax.set_ylabel('Spearman ρ', fontsize=12)
    ax.set_title('Difficulty (subset average score) (Easy -> Hard) vs. Spearman rho', 
                 fontsize=14, fontweight='bold')
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Coefficient of Variation (CV)', fontsize=10)
    
    # Add legend for point size (optional)
    ax.legend(loc='best')
    
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
    
    fig, ax = plt.subplots(figsize=(6, 6))
    
    # Create boxplot
    box = ax.boxplot(
        [df_plot[df_plot['task_group'] == 'MCQ']['spearman_rho'].values,
         df_plot[df_plot['task_group'] == 'Generative/Agentic']['spearman_rho'].values],
        labels=['MCQ', 'Generative/Agentic'],
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
    
    ax.set_ylabel('Spearman ρ', fontsize=12)
    ax.set_xlabel('Task Type', fontsize=12)
    ax.set_title('Spearman rho by Task Type', fontsize=14, fontweight='bold')
    
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
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Prepare data for boxplot
    data_for_boxplot = [df_plot[df_plot['prompt_length'] == cat]['spearman_rho'].values 
                        for cat in order]
    
    # Create boxplot
    box = ax.boxplot(
        data_for_boxplot,
        labels=order,
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
    
    ax.set_ylabel('Spearman ρ', fontsize=12)
    ax.set_xlabel('Prompt Length', fontsize=12)
    ax.set_title('Spearman rho by Prompt Length', fontsize=14, fontweight='bold')
    
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
    
    ax.set_xlabel('Coefficient of Variation (CV)', fontsize=12)
    ax.set_ylabel('Spearman ρ', fontsize=12)
    ax.set_title('CV vs. Spearman rho by Task Type', fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    
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
    
    sns.heatmap(
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
        ax=ax
    )
    
    ax.set_title('Correlation Matrix of Independent Variables', 
                 fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    
    # Save figure
    output_path = output_dir / "Figure_4_Confounder_Heatmap.pdf"
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.close()
    
    print(f"Figure 4 saved to {output_path}")


def generate_all_plots():
    """Generate all figures for the manuscript."""
    # Load data
    data_path = project_root / "results" / "analysis_ready_data.csv"
    df = pd.read_csv(data_path)
    
    # Ensure output directory exists
    output_dir = ensure_output_directory()
    
    print("Generating figures...")
    print("=" * 60)
    
    # Generate all figures
    figure_1_difficulty_variance(df, output_dir)
    figure_2_task_type(df, output_dir)
    figure_3a_complexity(df, output_dir)
    figure_3b_variance_tasktype(df, output_dir)
    figure_4_confounder_heatmap(df, output_dir)
    
    print("=" * 60)
    print("All figures generated successfully!")


if __name__ == "__main__":
    generate_all_plots()

