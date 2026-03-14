import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import adjustText for better label placement
try:
    from adjustText import adjust_text
    HAS_ADJUST_TEXT = True
except ImportError:
    HAS_ADJUST_TEXT = False
    logger.warning("adjustText not found. Labels may overlap.")

def get_metric_info(metric):
    """Get display info for metrics."""
    if metric == 'spearman_rho':
        return {'column': 'spearman_rho', 'ylabel': 'Spearman Correlation (ρ)', 'metric_name': 'Spearman Rho'}
    elif metric == 'kendall_tau':
        return {'column': 'kendall_tau', 'ylabel': 'Kendall Correlation (τ)', 'metric_name': 'Kendall Tau'}
    elif metric == 'rbo':
        return {'column': 'rbo', 'ylabel': 'Rank-Biased Overlap (RBO)', 'metric_name': 'RBO'}
    else:
        return {'column': metric, 'ylabel': metric, 'metric_name': metric}

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

def main():
    # Define paths - use absolute paths
    base_dir = Path("D:/桌面 2026.1.13/科研/Human-SIG/Human-SIG")
    correlation_results_path = base_dir / "new/results/correlation_results_overall.csv"
    analysis_ready_data_path = base_dir / "results/analysis_ready_data.csv"
    output_dir = base_dir / "new/results/figures"
    stats_output_path = base_dir / "new/results/hypothesis_testing_univariate_stats.csv"
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Loading data...")
    try:
        df_corr = pd.read_csv(correlation_results_path)
        # Read analysis_ready_data.csv, handling potential encoding issues if any
        df_features = pd.read_csv(analysis_ready_data_path)
    except FileNotFoundError as e:
        logger.error(f"Error loading data: {e}")
        return

    # Check column names
    logger.info(f"Correlation columns: {df_corr.columns.tolist()}")
    logger.info(f"Features columns: {df_features.columns.tolist()}")
    
    # Ensure benchmark_id is string and strip whitespace for cleaner merging
    df_corr['benchmark_id'] = df_corr['benchmark_id'].astype(str).str.strip()
    df_features['benchmark_id'] = df_features['benchmark_id'].astype(str).str.strip()
    
    # Merge
    # We want to attach 'difficulty' and 'cv' to our correlation results
    # Use left join on df_corr to keep all benchmarks we analyzed
    df_merged = pd.merge(df_corr, df_features[['benchmark_id', 'difficulty', 'cv']], 
                         on='benchmark_id', how='left')
    
    logger.info(f"Merged DataFrame shape: {df_merged.shape}")
    
    # Check for missing values in difficulty/cv
    missing_features = df_merged[df_merged['difficulty'].isna() | df_merged['cv'].isna()]
    if not missing_features.empty:
        logger.warning(f"Benchmarks missing difficulty/cv features ({len(missing_features)}):")
        logger.warning(missing_features['benchmark_id'].tolist())
    
    # Perform regressions
    results = []
    
    metrics = ['spearman_rho', 'kendall_tau', 'rbo']
    
    # 1. Difficulty vs Correlation
    for metric in metrics:
        metric_name_clean = get_metric_info(metric)['metric_name'].replace(' ', '_').replace('(', '').replace(')', '')
        figure_name = f"Univariate_Regression_Difficulty_{metric_name_clean}.pdf"
        
        res = perform_univariate_regression_and_plot(
            df_merged, 
            x_col='difficulty', 
            y_metric=metric, 
            output_dir=output_dir, 
            figure_name=figure_name,
            xlabel='Difficulty (Easy → Hard)',
            ylabel=get_metric_info(metric)['ylabel']
        )
        if res:
            res['x_variable'] = 'Difficulty'
            results.append(res)
            
    # 2. Variance (CV) vs Correlation
    for metric in metrics:
        metric_name_clean = get_metric_info(metric)['metric_name'].replace(' ', '_').replace('(', '').replace(')', '')
        figure_name = f"Univariate_Regression_Variance_{metric_name_clean}.pdf"
        
        res = perform_univariate_regression_and_plot(
            df_merged, 
            x_col='cv', 
            y_metric=metric, 
            output_dir=output_dir, 
            figure_name=figure_name,
            xlabel='Variance (CV)',
            ylabel=get_metric_info(metric)['ylabel']
        )
        if res:
            res['x_variable'] = 'Variance (CV)'
            results.append(res)
            
    # Save stats
    if results:
        df_stats = pd.DataFrame(results)
        df_stats.to_csv(stats_output_path, index=False)
        logger.info(f"Saved regression statistics to {stats_output_path}")
        
        # Print summary
        logger.info("\nRegression Summary:")
        # Select columns to display
        display_cols = ['x_variable', 'y_metric', 'slope', 'p_value', 'n']
        print(df_stats[display_cols].to_string(index=False))

if __name__ == "__main__":
    main()
