import pandas as pd
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats
import numpy as np
from pathlib import Path
import os
import sys

# Set style
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'DejaVu Sans'  # Fallback font

def load_data():
    print("Loading data...")
    base_dir = Path(r"D:\桌面 2026.1.13\科研\Human-SIG\Human-SIG")
    metadata_path = base_dir / "new/metadata_new.json"
    results_path = base_dir / "new/results/correlation_results_overall.csv"
    
    if not metadata_path.exists():
        print(f"Error: {metadata_path} not found")
        return pd.DataFrame()
        
    if not results_path.exists():
        print(f"Error: {results_path} not found")
        return pd.DataFrame()
    
    # Load metadata
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except Exception as e:
        print(f"Error loading metadata: {e}")
        return pd.DataFrame()
        
    complexity_map = {}
    for entry in metadata:
        if 'benchmark_id' in entry and 'complexity' in entry:
            complexity_map[entry['benchmark_id']] = entry['complexity']
            
    print(f"Found {len(complexity_map)} benchmarks with complexity mapping.")
            
    # Load results
    try:
        df = pd.read_csv(results_path)
    except Exception as e:
        print(f"Error loading results: {e}")
        return pd.DataFrame()
    
    print(f"Loaded {len(df)} rows from correlation results.")
    
    # Map complexity
    df['complexity'] = df['benchmark_id'].map(complexity_map)
    
    # Filter out benchmarks without complexity (e.g. LMArena categories if present in CSV)
    df_clean = df.dropna(subset=['complexity'])
    
    print(f"After filtering, {len(df_clean)} benchmarks remain.")
    
    return df_clean

def perform_analysis(df, output_dir):
    metrics = {
        'Spearman': 'spearman_rho', 
        'Kendall': 'kendall_tau', 
        'RBO': 'rbo'
    }
    
    complexity_order = ['Applying', 'Analyzing', 'Evaluating', 'Creating']
    complexity_val = {c: i+1 for i, c in enumerate(complexity_order)}
    
    df['complexity_val'] = df['complexity'].map(complexity_val)
    
    # Calculate boxplot stats for each category
    stats_df = []
    for c in complexity_order:
        subset = df[df['complexity'] == c]
        count = len(subset)
        if count > 0:
            # We can use any metric to get count, but let's stick to Spearman for generic stats
            # or just report count. Boxplot stats differ by metric.
            # User asked for "number of benchmarks in that category", which is constant across metrics.
            pass
        
        stats_df.append({
            'Complexity': c,
            'Count': count
        })
    stats_df = pd.DataFrame(stats_df)
    
    # Calculate detailed descriptive statistics for each metric and category
    desc_stats = []
    for metric_name, metric_col in metrics.items():
        for c in complexity_order:
            subset = df[df['complexity'] == c][metric_col]
            if len(subset) > 0:
                desc = subset.describe()
                desc_stats.append({
                    'Metric': metric_name,
                    'Complexity': c,
                    'Count': int(desc['count']),
                    'Min': f"{desc['min']:.4f}",
                    'Q1': f"{desc['25%']:.4f}",
                    'Median': f"{desc['50%']:.4f}",
                    'Q3': f"{desc['75%']:.4f}",
                    'Max': f"{desc['max']:.4f}",
                    'Mean': f"{desc['mean']:.4f}",
                    'Std': f"{desc['std']:.4f}"
                })
            else:
                 desc_stats.append({
                    'Metric': metric_name,
                    'Complexity': c,
                    'Count': 0,
                    'Min': "-", 'Q1': "-", 'Median': "-", 'Q3': "-", 'Max': "-", 'Mean': "-", 'Std': "-"
                })
    desc_stats_df = pd.DataFrame(desc_stats)
    
    results = []
    
    for metric_name, metric_col in metrics.items():
        # 1. Kruskal-Wallis Test
        groups = [df[df['complexity'] == c][metric_col].values for c in complexity_order]
        # Remove empty groups
        groups = [g for g in groups if len(g) > 0]
        
        kw_stat, kw_p = stats.kruskal(*groups)
        
        # 2. Linear Regression (Ordinal)
        slope, intercept, r_value, p_value, std_err = stats.linregress(df['complexity_val'], df[metric_col])
        
        results.append({
            'Metric': metric_name,
            'KW_Stat': kw_stat,
            'KW_P': kw_p,
            'Regression_Slope': slope,
            'Regression_R2': r_value**2,
            'Regression_P': p_value
        })
        
        # 3. Plot
        plt.figure(figsize=(10, 6))
        
        # Boxplot
        sns.boxplot(x='complexity', y=metric_col, data=df, order=complexity_order, palette="Set2", showfliers=False)
        
        # Stripplot
        sns.stripplot(x='complexity', y=metric_col, data=df, order=complexity_order, color=".25", alpha=0.6)
        
        # Add regression line
        # Create x-values for regression line (0 to 3 for plotting, but regression used 1 to 4)
        x_vals = np.array([0, 3])
        y_vals = intercept + slope * (x_vals + 1) # +1 because complexity_val is 1-based
        
        plt.plot(x_vals, y_vals, color='red', linestyle='--', linewidth=2, label=f'Regression (p={p_value:.3f})')
        
        plt.title(f'{metric_name} Correlation by Complexity Level', fontsize=14)
        plt.xlabel('Complexity Level', fontsize=12)
        plt.ylabel(f'{metric_name} Correlation', fontsize=12)
        plt.legend()
        
        plot_path = output_dir / f'complexity_{metric_name.lower()}.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
    return pd.DataFrame(results), stats_df, desc_stats_df

def generate_report(results_df, stats_df, desc_stats_df, output_path):
    markdown = "# Prompt Complexity Analysis Report\n\n"
    
    markdown += "## 1. 实验方法 (Methodology)\n\n"
    markdown += "我们将所有Benchmark按照认知复杂度（Cognitive Complexity）分为四个等级：\n"
    markdown += "1. **Applying (应用)**: 执行已知规则或算法。\n"
    markdown += "2. **Analyzing (分析)**: 分解信息，寻找逻辑联系。\n"
    markdown += "3. **Evaluating (评价)**: 基于标准进行批判性判断。\n"
    markdown += "4. **Creating (创造)**: 整合信息生成新作品或架构。\n\n"
    markdown += "为了检验复杂度与Benchmark有效性（与LMArena的一致性）之间的关系，我们进行了以下两项统计检验：\n"
    markdown += "- **Kruskal-Wallis H Test**: 检验不同复杂度组别的相关系数分布是否存在显著差异（非参数检验）。\n"
    markdown += "- **Ordinal Linear Regression**: 将复杂度作为有序变量 (1-4) 进行线性回归，检验是否存在显著的线性趋势。\n\n"
    
    markdown += "## 2. 实验结果 (Results)\n\n"
    
    # P-value summary table
    markdown += "### 显著性检验结果汇总 (Significance Test Summary)\n\n"
    markdown += "| Metric | Kruskal-Wallis p-value | Regression p-value |\n"
    markdown += "| :--- | :--- | :--- |\n"
    
    for _, row in results_df.iterrows():
        kw_p = f"{row['KW_P']:.4f}"
        reg_p = f"{row['Regression_P']:.4f}"
        
        # Highlight significant p-values
        if row['KW_P'] < 0.05:
            kw_p = f"**{kw_p}**"
        if row['Regression_P'] < 0.05:
            reg_p = f"**{reg_p}**"
            
        markdown += f"| {row['Metric']} | {kw_p} | {reg_p} |\n"
        
    markdown += "\n"
    
    markdown += "### 详细统计结果 (Detailed Statistical Results)\n\n"
    
    # Format detailed table
    table_md = "| Metric | Kruskal-Wallis H | KW p-value | Regression Slope | $R^2$ | Regression p-value |\n"
    table_md += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
    
    for _, row in results_df.iterrows():
        kw_h = f"{row['KW_Stat']:.4f}"
        kw_p = f"{row['KW_P']:.4f}"
        slope = f"{row['Regression_Slope']:.4f}"
        r2 = f"{row['Regression_R2']:.4f}"
        reg_p = f"{row['Regression_P']:.4f}"
        
        # Highlight significant p-values
        if row['KW_P'] < 0.05:
            kw_p = f"**{kw_p}**"
        if row['Regression_P'] < 0.05:
            reg_p = f"**{reg_p}**"
            
        table_md += f"| {row['Metric']} | {kw_h} | {kw_p} | {slope} | {r2} | {reg_p} |\n"
        
    markdown += table_md
    markdown += "\n\n"
    
    markdown += "## 3. 图表解释与样本量 (Boxplot Interpretation & Sample Size)\n\n"
    markdown += "下表列出了各个复杂度分类下的 Benchmark 数量，以及箱线图（Boxplot）中各元素的统计学含义。\n\n"
    
    # Boxplot explanation table
    markdown += "| 元素 (Element) | 含义 (Meaning) |\n"
    markdown += "| :--- | :--- |\n"
    markdown += "| **有色方块 (Colored Box)** | **四分位距 (IQR)**: 覆盖数据的中间50%范围，从第25百分位数 (Q1) 到第75百分位数 (Q3)。方块的高度反映了该组数据的离散程度（方差）。 |\n"
    markdown += "| **方块内的横线 (Line inside box)** | **中位数 (Median)**: 数据的中间值，将数据分为上下两部分。 |\n"
    markdown += "| **上下须 (Whiskers)** | **数据范围 (Range)**: 延伸至1.5倍IQR范围内的最大值和最小值（不包括离群点）。超出此范围的点通常被视为离群点（Outliers）。 |\n"
    markdown += "| **黑点 (Black Dots)** | **原始数据点 (Raw Data)**: 每个点代表一个具体的 Benchmark。 |\n\n"

    # Sample size table
    markdown += "### 各分类 Benchmark 数量统计\n\n"
    markdown += "| Complexity Category | Benchmark Count |\n"
    markdown += "| :--- | :--- |\n"
    for _, row in stats_df.iterrows():
        markdown += f"| {row['Complexity']} | {row['Count']} |\n"
    
    markdown += f"| **Total** | **{stats_df['Count'].sum()}** |\n\n"
    
    # Descriptive statistics table
    markdown += "### 各分类箱线图数值统计 (Descriptive Statistics)\n\n"
    markdown += "下表列出了每个Metric在不同复杂度分类下的具体统计数值（对应箱线图中的各个元素）。\n\n"
    markdown += "| Metric | Complexity | Count | Min | Q1 | Median | Q3 | Max | Mean | Std |\n"
    markdown += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
    for _, row in desc_stats_df.iterrows():
        markdown += f"| {row['Metric']} | {row['Complexity']} | {row['Count']} | {row['Min']} | {row['Q1']} | {row['Median']} | {row['Q3']} | {row['Max']} | {row['Mean']} | {row['Std']} |\n"
    markdown += "\n"

    markdown += "## 4. 结果分析 (Analysis)\n\n"
    
    # Automated analysis generation based on results
    for _, row in results_df.iterrows():
        metric = row['Metric']
        reg_p = row['Regression_P']
        slope = row['Regression_Slope']
        
        markdown += f"### {metric} Analysis\n"
        if reg_p < 0.05:
            trend = "正向" if slope > 0 else "负向"
            markdown += f"- **趋势**: 发现了显著的{trend}线性趋势 (p={reg_p:.4f})。\n"
            markdown += f"- **解释**: 随着任务认知复杂度的提升，Benchmark与LMArena的一致性显著{'提高' if slope > 0 else '降低'}。\n"
        else:
            markdown += f"- **趋势**: 未发现显著的线性趋势 (p={reg_p:.4f})。\n"
            markdown += f"- **解释**: 任务认知复杂度的提升并没有显著改变Benchmark与LMArena的一致性。\n"
            
        if row['KW_P'] < 0.05:
            markdown += f"- **分布差异**: 不同复杂度组别之间的分布存在显著差异 (KW p={row['KW_P']:.4f})。\n"
        else:
            markdown += f"- **分布差异**: 不同复杂度组别之间的分布没有显著差异 (KW p={row['KW_P']:.4f})。\n"
        
        markdown += "\n"
        
    markdown += "## 5. 图表 (Figures)\n\n"
    markdown += "以下图表展示了不同复杂度等级下的相关系数分布及回归趋势线：\n\n"
    markdown += "![Spearman Correlation by Complexity](images/complexity_spearman.png)\n"
    markdown += "*Figure 1: Spearman Correlation Distribution across Complexity Levels*\n\n"
    markdown += "![Kendall Correlation by Complexity](images/complexity_kendall.png)\n"
    markdown += "*Figure 2: Kendall Correlation Distribution across Complexity Levels*\n\n"
    markdown += "![RBO Correlation by Complexity](images/complexity_rbo.png)\n"
    markdown += "*Figure 3: RBO Correlation Distribution across Complexity Levels*\n"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown)
        
    print(f"Report generated at {output_path}")

def main():
    output_dir = Path(r"D:\桌面 2026.1.13\科研\Human-SIG\Human-SIG\new\results\images")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df = load_data()
    print(f"Loaded {len(df)} benchmarks with complexity data.")
    
    results_df, stats_df, desc_stats_df = perform_analysis(df, output_dir)
    
    report_path = Path(r"D:\桌面 2026.1.13\科研\Human-SIG\Human-SIG\new\results\complexity_analysis_report.md")
    generate_report(results_df, stats_df, desc_stats_df, report_path)
    
    print("Analysis complete.")

if __name__ == "__main__":
    main()
