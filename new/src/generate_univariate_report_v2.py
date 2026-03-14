
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path

def main():
    # Define paths
    base_dir = Path(r"D:\桌面 2026.1.13\科研\Human-SIG\Human-SIG")
    correlation_results_path = base_dir / "new/results/correlation_results_overall.csv"
    analysis_ready_data_path = base_dir / "results/analysis_ready_data.csv"
    
    # Load data
    try:
        df_corr = pd.read_csv(correlation_results_path)
        df_features = pd.read_csv(analysis_ready_data_path)
    except FileNotFoundError as e:
        print(f"Error loading data: {e}")
        return

    # Data cleaning
    df_corr['benchmark_id'] = df_corr['benchmark_id'].astype(str).str.strip()
    df_features['benchmark_id'] = df_features['benchmark_id'].astype(str).str.strip()
    
    # Merge
    # We want difficulty and cv from features, and rho, tau, rbo from correlation results
    df_merged = pd.merge(df_corr, df_features[['benchmark_id', 'difficulty', 'cv']], 
                         on='benchmark_id', how='left')
    
    # Define analysis configuration
    independent_vars = {
        'difficulty': 'Difficulty',
        'cv': 'Variance (CV)'
    }
    
    dependent_vars = {
        'spearman_rho': 'Spearman Rho',
        'kendall_tau': 'Kendall Tau',
        'rbo': 'RBO'
    }
    
    results = []
    
    print("| Independent Variable | Dependent Variable | R^2 | Slope (beta) | 95% CI for Slope | P-value |")
    print("| :--- | :--- | :--- | :--- | :--- | :--- |")
    
    for x_col, x_name in independent_vars.items():
        for y_col, y_name in dependent_vars.items():
            # Drop NaNs for this pair
            df_plot = df_merged[[x_col, y_col]].dropna()
            
            if len(df_plot) < 3:
                print(f"| {x_name} | {y_name} | N/A | N/A | N/A | N/A |")
                continue
                
            x = df_plot[x_col]
            y = df_plot[y_col]
            n = len(df_plot)
            
            # Linear Regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # R-squared
            r_squared = r_value ** 2
            
            # 95% CI for Slope
            # t-critical value for 95% confidence (two-tailed) with n-2 degrees of freedom
            t_crit = stats.t.ppf(0.975, df=n-2)
            ci_lower = slope - t_crit * std_err
            ci_upper = slope + t_crit * std_err
            
            # Format p-value
            if p_value < 0.001:
                p_str = "< 0.001"
            else:
                p_str = f"{p_value:.4f}"
                
            print(f"| {x_name} | {y_name} | {r_squared:.4f} | {slope:.4f} | [{ci_lower:.4f}, {ci_upper:.4f}] | {p_str} |")

if __name__ == "__main__":
    main()
