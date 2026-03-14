import pandas as pd
import numpy as np
import scipy.stats as stats
from pathlib import Path
import re
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns

def load_data():
    base_dir = Path("D:/桌面 2026.1.13/科研/Human-SIG/Human-SIG")
    master_path = base_dir / "data/processed/master_table/master_correlation_matrix.csv"
    analysis_ready_path = base_dir / "results/analysis_ready_data.csv"
    
    print("Loading data...")
    df_master = pd.read_csv(master_path)
    df_analysis = pd.read_csv(analysis_ready_path)
    
    return df_master, df_analysis, base_dir

def sanitize_benchmark_id(benchmark_id: str) -> str:
    """Sanitize benchmark ID to match column names in master table."""
    sanitized = re.sub(r'[^\w\-]', '_', str(benchmark_id))
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized.strip('_')

def load_lmarena_category_data(base_dir, category):
    """Load LMArena data for a specific category to get model-specific Elo and uncertainty (CI)."""
    # Map category to folder name
    # The categories in analysis_ready_data.csv match the LMArena folder suffixes
    # e.g., "Math" -> "LMArena-Math"
    folder_name = f"LMArena-{category}"
    lmarena_path = base_dir / f"data/raw/lmarena/{folder_name}/data.csv"
    
    if not lmarena_path.exists():
        # Try fallback to Overall if category file doesn't exist (though it should)
        print(f"Warning: Category file not found at {lmarena_path}. Falling back to Overall.")
        lmarena_path = base_dir / "data/raw/lmarena/LMArena-Overall/data.csv"

    print(f"Loading LMArena data for category '{category}' from {lmarena_path}...")
    
    try:
        df_arena = pd.read_csv(lmarena_path)
    except Exception as e:
        print(f"Error loading LMArena data: {e}")
        return {}

    model_data = {}
    
    if 'Model' not in df_arena.columns or '95% CI (±)' not in df_arena.columns or ('Elo' not in df_arena.columns and 'Score' not in df_arena.columns):
        print("Warning: Required columns (Model, Elo/Score, 95% CI) not found in LMArena data.")
        print(f"Columns found: {df_arena.columns.tolist()}")
        return {}
        
    elo_col = 'Elo' if 'Elo' in df_arena.columns else 'Score'

    for _, row in df_arena.iterrows():
        model = str(row['Model']).strip()
        
        # Parse Elo (handle "1503Preliminary" etc)
        elo_str = str(row[elo_col])
        elo_val_str = re.sub(r'[^\d\.]', '', elo_str)
        try:
            elo = float(elo_val_str)
        except ValueError:
            continue

        # Parse CI
        ci_str = str(row['95% CI (±)'])
        ci_val_str = re.sub(r'[^\d\.]', '', ci_str)
        try:
            ci_val = float(ci_val_str)
            sigma = ci_val / 1.96
        except ValueError:
            # Default sigma if parsing fails? Or skip? 
            # Better to skip or set high uncertainty
            print(f"Warning: Could not parse CI value '{ci_str}' for model '{model}'")
            sigma = 20.0 # Fallback
            
        model_data[model] = {'elo': elo, 'sigma': sigma}
            
    print(f"Loaded data for {len(model_data)} models in category '{category}'.")
    return model_data

def get_benchmark_scores(df_master, benchmark_id):
    """Extract model names and scores for a specific benchmark from master table."""
    # Construct column names
    score_col = f"{benchmark_id}_score"
    model_col = "model_name" # Assuming the first column is model_name
    
    if model_col not in df_master.columns:
        model_col = df_master.columns[0]
    
    if score_col not in df_master.columns:
        sanitized_id = sanitize_benchmark_id(benchmark_id)
        score_col = f"{sanitized_id}_score"
            
    if score_col not in df_master.columns:
        return {}
        
    # Get paired data
    df_subset = df_master[[model_col, score_col]].copy()
    
    # Ensure score is numeric
    df_subset[score_col] = pd.to_numeric(df_subset[score_col], errors='coerce')
    df_subset = df_subset.dropna()
    
    # Return dict: {model_name: score}
    return dict(zip(df_subset[model_col].astype(str).str.strip(), df_subset[score_col]))

def run_simulation():
    df_master, df_analysis, base_dir = load_data()
    
    # Configuration
    N_SIMULATIONS = 10000 # Fixed as requested
    
    # Output paths
    output_csv = base_dir / "new/results/uncertainty_analysis_results.csv"
    output_report = base_dir / "new/results/uncertainty_analysis_report.md"
    
    results = []
    print(f"Starting Monte Carlo simulation ({N_SIMULATIONS} runs per benchmark)...")
    
    # Cache LMArena data to avoid reloading for same category
    lmarena_cache = {}
    
    for i, row in df_analysis.iterrows():
        benchmark_id = row['benchmark_id']
        category = row['category']
        print(f"Processing {i+1}/{len(df_analysis)}: {benchmark_id} (Category: {category})", flush=True)
        n_questions = row['question_count']
        
        # 1. Load LMArena data for this category
        if category not in lmarena_cache:
            lmarena_cache[category] = load_lmarena_category_data(base_dir, category)
        category_data = lmarena_cache[category]
        
        if not category_data:
            print(f"Skipping {benchmark_id}: No LMArena data for category {category}")
            continue

        # 2. Get Benchmark Scores
        benchmark_scores = get_benchmark_scores(df_master, benchmark_id)
        
        if not benchmark_scores or len(benchmark_scores) < 5:
            print(f"Skipping {benchmark_id}: Not enough score data (N={len(benchmark_scores)})")
            continue
            
        # 3. Find Intersection of Models
        common_models = set(category_data.keys()) & set(benchmark_scores.keys())
        
        if len(common_models) < 5:
            print(f"Skipping {benchmark_id}: Not enough common models (N={len(common_models)})")
            continue
            
        # 4. Prepare Arrays for Simulation
        models = list(common_models)
        elos = np.array([category_data[m]['elo'] for m in models])
        sigmas = np.array([category_data[m]['sigma'] for m in models])
        scores = np.array([benchmark_scores[m] for m in models])
        
        # Check for abnormal score range
        if np.max(scores) > 105:
            print(f"Skipping {benchmark_id}: Score range {np.min(scores)}-{np.max(scores)} exceeds 100.")
            continue
            
        n_samples = len(models)
        
        try:
            # Original correlations (using Category Elo)
            orig_spearman, orig_s_p = stats.spearmanr(elos, scores)
            orig_kendall, orig_k_p = stats.kendalltau(elos, scores)
            
            # Simulation
            sim_spearmans = []
            # sim_kendalls = [] # Kendall is too slow for 10000 runs with N=290
            
            for _ in range(N_SIMULATIONS):
                # 1. Perturb scores
                # Laplace smoothing for variance calculation to avoid zero variance at 0 or 100
                p = scores / 100.0
                p_smoothed = (scores/100.0 * n_questions + 1) / (n_questions + 2)
                var = p_smoothed * (1 - p_smoothed) / n_questions
                sigma_scores = np.sqrt(var) * 100
                
                sim_scores = np.random.normal(scores, sigma_scores)
                sim_scores = np.clip(sim_scores, 0, 100)
                
                # 2. Perturb Elos using model-specific sigmas
                sim_elos = np.random.normal(elos, sigmas)
                
                # 3. Calculate correlations
                try:
                    s_corr, _ = stats.spearmanr(sim_elos, sim_scores)
                    # k_corr, _ = stats.kendalltau(sim_elos, sim_scores)
                    
                    if not np.isnan(s_corr):
                        sim_spearmans.append(s_corr)
                    # if not np.isnan(k_corr):
                    #     sim_kendalls.append(k_corr)
                except:
                    pass
                
            # Calculate robust statistics
            sim_spearmans = np.array(sim_spearmans)
            # sim_kendalls = np.array(sim_kendalls)
            
            if len(sim_spearmans) > 0:
                s_mean = np.mean(sim_spearmans)
                s_ci_lower = np.percentile(sim_spearmans, 2.5)
                s_ci_upper = np.percentile(sim_spearmans, 97.5)
                # P-value: Frequency of correlation <= 0 (Testing for positive correlation)
                s_p_value = np.mean(sim_spearmans <= 0)
                s_robust_sig = not (s_ci_lower <= 0 <= s_ci_upper)
            else:
                s_mean, s_ci_lower, s_ci_upper, s_p_value, s_robust_sig = np.nan, np.nan, np.nan, np.nan, False
                
            results.append({
                'Benchmark': benchmark_id,
                'Category': category,
                'N_Samples': n_samples,
                'N_Questions': n_questions,
                'Orig_Spearman': orig_spearman,
                'Orig_Spearman_P': orig_s_p,
                'Robust_Spearman_Mean': s_mean,
                'Robust_Spearman_CI_Lower': s_ci_lower,
                'Robust_Spearman_CI_Upper': s_ci_upper,
                'Robust_Spearman_P_Value': s_p_value,
                'Spearman_Significant_Orig': orig_s_p < 0.05,
                'Spearman_Significant_Robust': s_robust_sig,
                'Spearman_Status_Change': (orig_s_p < 0.05) and not s_robust_sig,
            })
        
        except Exception as e:
            print(f"Error processing {benchmark_id}: {e}")
            import traceback
            traceback.print_exc()
            continue
        
    # Save results if we ran the simulation
    if len(results) > 0:
        df_results = pd.DataFrame(results)
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        df_results.to_csv(output_csv, index=False)
        print(f"Saved results to {output_csv}")
    
        # Generate Plots
        sns.set(style="whitegrid")
        
        # Plot 1: Robust CI vs Original Spearman (Error Bars)
        plt.figure(figsize=(12, 8))
        
        # Sort by Original Spearman
        df_plot = df_results.sort_values('Orig_Spearman', ascending=False).reset_index(drop=True)
        
        # Use vlines for CI to avoid negative error values if Original is outside CI
        # This also clearly shows the robust range vs original point
        plt.vlines(x=range(len(df_plot)), 
                   ymin=df_plot['Robust_Spearman_CI_Lower'], 
                   ymax=df_plot['Robust_Spearman_CI_Upper'], 
                   color='gray', alpha=0.5, linewidth=2, label='Robust 95% CI')
                   
        # Plot Robust Mean (if available, otherwise skip)
        if 'Robust_Spearman_Mean' in df_plot.columns:
            plt.scatter(range(len(df_plot)), df_plot['Robust_Spearman_Mean'], 
                        color='gray', marker='_', s=100, label='Robust Mean')
    
        # Color points by significance status
        # colors = ['red' if row['Spearman_Status_Change'] else 'blue' for _, row in df_plot.iterrows()]
        
        # Plot Original Spearman
        # We plot individually to handle labels correctly for legend
        added_labels = set()
        for i, row in df_plot.iterrows():
            color = 'red' if row['Spearman_Status_Change'] else 'blue'
            label_text = 'Lost Significance' if row['Spearman_Status_Change'] else 'Original Spearman (Robust)'
            
            if label_text not in added_labels:
                plt.scatter(i, row['Orig_Spearman'], color=color, s=80, zorder=10, label=label_text)
                added_labels.add(label_text)
            else:
                plt.scatter(i, row['Orig_Spearman'], color=color, s=80, zorder=10)
                       
        plt.axhline(0, color='black', linestyle='--', linewidth=1)
        plt.xticks(range(len(df_plot)), df_plot['Benchmark'], rotation=90)
        plt.ylabel('Spearman Correlation (with 95% Robust CI)')
        plt.title(f'Robustness of Benchmark Correlations under Uncertainty (N={N_SIMULATIONS} Simulations)')
        plt.legend()
        plt.tight_layout()
        
        output_fig = base_dir / "new/results/figures/uncertainty_robustness_spearman.png"
        output_fig.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_fig, dpi=300)
        print(f"Saved figure to {output_fig}")
        
        # Generate Report
        with open(output_report, 'w', encoding='utf-8') as f:
            f.write("# 不确定性传播相关性分析（实验方法与结果）\n\n")
            
            # Methodology Section
            f.write("## 1. 实验方法论\n\n")
            f.write("本实验旨在评估 Benchmark 分数与 LMArena Elo 分数之间相关性的稳健性，通过蒙特卡洛模拟传播测量不确定性。\n\n")
            
            f.write("### 1.1 数据来源与处理\n")
            f.write("- **LMArena 数据**：使用 `data/raw/lmarena` 目录下对应 Category（如 Math, Coding）的 `data.csv` 文件。\n")
            f.write("  - **Elo 值**：使用文件中的 Elo 得分（或 Score）作为均值。\n")
            f.write("  - **不确定性 (Sigma)**：利用文件中提供的 95% 置信区间 (CI) 推导标准差，公式为 `sigma = CI / 1.96`。\n")
            f.write("- **Benchmark 数据**：使用各 Benchmark 的原始得分。\n")
            f.write("  - **不确定性**：假设 Benchmark 得分服从二项分布，标准差由题目数量决定：`sigma = sqrt(p(1-p)/N) * 100` (其中 p 为得分/100，N 为题目数)。\n\n")
            
            f.write("### 1.2 模拟过程\n")
            f.write(f"- **模拟次数**：对每个 Benchmark 进行 N={N_SIMULATIONS} 次蒙特卡洛模拟。\n")
            f.write("- **得分扰动**：\n")
            f.write("  - LMArena Elo：从 `N(Elo, Sigma_Elo)` 中采样。\n")
            f.write("  - Benchmark Score：从 `N(Score, Sigma_Score)` 中采样（并截断在 0-100 之间）。\n")
            f.write("- **相关性计算**：在每次模拟中，计算采样后的 Elo 与 Score 之间的 Spearman 秩相关系数 (Rho)。\n\n")
            
            f.write("### 1.3 统计量定义\n")
            f.write("- **原始 Rho (Orig Rho)**：基于原始数据的 Spearman 相关系数。\n")
            f.write("- **模拟 Rho (Simulated Rho)**：10000 次模拟相关系数的平均值。\n")
            f.write("- **模拟 95% CI**：10000 次模拟相关系数分布的第 2.5 百分位和第 97.5 百分位 (`[2.5%, 97.5%]`)。\n")
            f.write("- **原始 P 值 (Orig P-value)**：基于原始数据的双尾 P 值。\n")
            f.write("- **模拟 P 值 (Simulated P-value)**：模拟相关系数小于等于 0 的频率（即单尾检验，检验是否存在显著正相关）。\n\n")
            
            # Results Table Section
            f.write("## 2. 实验结果汇总\n\n")
            f.write("下表展示了所有 Benchmark 的不确定性分析结果，按原始 Rho 降序排列。\n\n")
            
            # Prepare formatted table data
            table_rows = []
            for _, row in df_results.sort_values('Orig_Spearman', ascending=False).iterrows():
                # Format CI string
                ci_str = f"[{row['Robust_Spearman_CI_Lower']:.3f}, {row['Robust_Spearman_CI_Upper']:.3f}]"
                
                table_rows.append({
                    'Benchmark': row['Benchmark'],
                    '模型数量': row['N_Samples'],
                    '题目数量': row['N_Questions'],
                    '原始 Rho': f"{row['Orig_Spearman']:.4f}",
                    '模拟 Rho': f"{row['Robust_Spearman_Mean']:.4f}",
                    '模拟 95% CI': ci_str,
                    '原始 P值': f"{row['Orig_Spearman_P']:.4g}",
                    '模拟 P值': f"{row['Robust_Spearman_P_Value']:.4f}"
                })
            
            df_table = pd.DataFrame(table_rows)
            f.write(df_table.to_markdown(index=False))
            f.write("\n\n")
            
            # Analysis Section
            f.write("## 3. 简要分析\n\n")
            f.write("1. **稳健性**：大部分 Benchmark 的模拟 95% CI 都在 0 以上，且模拟 P 值极低 (<0.05)，说明其与 LMArena Category Elo 的正相关关系是稳健的。\n")
            f.write("2. **不显著项**：模拟 P 值较大（>0.05）或 CI 包含 0 的项（如 IOI, IFEval），表明在考虑测量误差后，无法确信其与人类偏好（LMArena）存在正相关。\n")
    
        print(f"Saved report to {output_report}")
    else:
        print("No results generated. Check warnings above.")

if __name__ == "__main__":
    run_simulation()
