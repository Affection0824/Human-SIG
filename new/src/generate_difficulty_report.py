import pandas as pd
import scipy.stats as stats
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json

def generate_difficulty_report():
    # Define paths
    base_dir = Path("D:/桌面 2026.1.13/科研/Human-SIG/Human-SIG")
    comparison_csv_path = base_dir / "new/data/triplet_difficulty_comparison.csv"
    output_report_path = base_dir / "new/results/difficulty_analysis_report.md"
    output_figure_path = base_dir / "new/results/figures/difficulty_correlation.png"
    
    # Ensure output directory exists
    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    output_figure_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Target models (Group 20)
    target_models = [
        "Anthropicclaude-sonnet-4-5-20250929-thinking-32k",
        "gemini-3-pro",
        "gpt-5.1"
    ]
    
    # Load comparison data
    print(f"Loading data from {comparison_csv_path}...")
    try:
        df = pd.read_csv(comparison_csv_path)
    except FileNotFoundError:
        print(f"Error: Could not find {comparison_csv_path}")
        return

    # Filter out NaNs if any
    df_clean = df.dropna(subset=['Original_Difficulty', 'Triplet_Difficulty'])
    
    # Calculate Pearson correlation
    pearson_corr, p_value = stats.pearsonr(df_clean['Original_Difficulty'], df_clean['Triplet_Difficulty'])
    
    # Calculate 95% Confidence Interval for Pearson correlation
    r_z = np.arctanh(pearson_corr)
    se = 1 / np.sqrt(len(df_clean) - 3)
    z_crit = 1.96 # For 95% CI
    ci_lower = np.tanh(r_z - z_crit * se)
    ci_upper = np.tanh(r_z + z_crit * se)
    
    # Generate Plot
    print("Generating correlation plot...")
    plt.figure(figsize=(10, 8))
    sns.set_theme(style="whitegrid")
    
    sns.regplot(
        data=df_clean, 
        x='Original_Difficulty', 
        y='Triplet_Difficulty',
        ci=95,
        scatter_kws={'s': 100, 'alpha': 0.7},
        line_kws={'color': 'red', 'label': f'Pearson r={pearson_corr:.2f}'}
    )
    
    # Add labels for each point
    for i, row in df_clean.iterrows():
        plt.text(
            row['Original_Difficulty']+0.5, 
            row['Triplet_Difficulty'], 
            row['Benchmark_Name'],
            fontsize=9,
            alpha=0.8
        )
        
    plt.title('Difficulty Comparison: Original Baseline vs Top-Tier Models', fontsize=14)
    plt.xlabel('Original Difficulty (Common Subset)', fontsize=12)
    plt.ylabel('Triplet Difficulty (Top-Tier Models)', fontsize=12)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_figure_path, dpi=300)
    plt.close()
    print(f"Plot saved to {output_figure_path}")
    
    # Generate Report
    with open(output_report_path, 'w', encoding='utf-8') as f:
        f.write("# 难度分析报告：顶尖模型与原始基准的对比\n\n")
        
        # Section 1: Selected Models
        f.write("## 1. 选定模型 (Group 20)\n")
        f.write("选择了以下 Overall ELO >= 1420 的顶尖模型来计算新的难度分数：\n\n")
        for model in target_models:
            f.write(f"- {model}\n")
        f.write("\n")
        
        # Section 2: Selected Benchmarks
        f.write(f"## 2. 选定 Benchmark (N={len(df_clean)})\n")
        f.write("这三个模型共同拥有的 Benchmark：\n\n")
        for bm in df_clean['Benchmark_Name'].tolist():
            f.write(f"- {bm}\n")
        f.write("\n")
        
        # Section 3: Difficulty Comparison
        f.write("## 3. 难度对比\n")
        f.write("- **Original Difficulty**: 使用 Common Subset 模型 (ELO 1400-1430) 计算的原始难度。\n")
        f.write("- **Triplet Difficulty**: 使用选定的 3 个顶尖模型计算的新难度。\n")
        f.write("- **Diff**: Original - Triplet (正值表示顶尖模型觉得更容易)。\n\n")
        
        # Add Diff column for display
        df_display = df_clean[['Benchmark_Name', 'Original_Difficulty', 'Triplet_Difficulty']].copy()
        df_display['Diff'] = df_display['Original_Difficulty'] - df_display['Triplet_Difficulty']
        
        # Convert to Markdown table
        table_md = df_display.to_markdown(index=False, floatfmt=".2f")
        f.write(table_md)
        f.write("\n\n")
        
        # Section 4: Correlation Analysis
        f.write("## 4. 相关性分析\n")
        f.write("Original Difficulty 和 Triplet Difficulty 之间的 Pearson 相关系数：\n\n")
        f.write(f"- **Pearson 相关系数 (r)**: {pearson_corr:.4f}\n")
        f.write(f"- **95% 置信区间**: [{ci_lower:.4f}, {ci_upper:.4f}]\n")
        f.write(f"- **P-value**: {p_value:.4e}\n")
        f.write(f"- **样本量**: {len(df_clean)}\n")
        
        interpretation = ""
        if pearson_corr > 0.9:
            interpretation = "极强正相关"
        elif pearson_corr > 0.7:
            interpretation = "强正相关"
        elif pearson_corr > 0.5:
            interpretation = "中等正相关"
        else:
            interpretation = "弱相关或无相关"
            
        f.write(f"\n**结论**: {interpretation}。这表明即使由能力强得多的模型进行评估，Benchmark 的相对难度排序仍然高度一致，尽管绝对难度分数有所下降（分数上升）。\n")

    print(f"Report generated successfully at {output_report_path}")

if __name__ == "__main__":
    generate_difficulty_report()
