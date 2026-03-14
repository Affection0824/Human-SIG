import pandas as pd
import numpy as np
from pathlib import Path

def analyze_humaneval_rankings():
    # Define paths - use absolute paths or relative to current working directory
    # Current CWD is D:\桌面 2026.1.13\科研\Human-SIG\Human-SIG
    base_dir = Path("D:/桌面 2026.1.13/科研/Human-SIG/Human-SIG")
    input_path = base_dir / "data/processed/master_table/master_correlation_matrix.csv"
    output_csv = base_dir / "new/results/humaneval_ranking_comparison.csv"
    output_md = base_dir / "new/results/humaneval_ranking_comparison.md"
    
    print(f"Loading data from {input_path}...")
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        print(f"Error: Could not find {input_path}")
        return

    # Filter for models with HumanEval scores
    # Also ensure we have Overall and Coding ELOs
    # Check if 'elo_coding' exists, if not, print available columns
    if 'elo_coding' not in df.columns:
        print(f"Error: 'elo_coding' not found in columns: {df.columns.tolist()}")
        return

    mask = (
        pd.notna(df['HumanEval_score']) & 
        pd.notna(df['elo_overall']) & 
        pd.notna(df['elo_coding'])
    )
    df_he = df[mask].copy()
    
    print(f"Found {len(df_he)} models with HumanEval scores and ELOs.")
    
    if len(df_he) == 0:
        print("No matching models found.")
        return

    # Select relevant columns
    cols = ['model_name', 'HumanEval_score', 'elo_overall', 'elo_coding']
    df_he = df_he[cols]
    
    # Calculate ranks within this subset (1 is best, lower number is better rank)
    # Scores: higher is better -> ascending=False
    # ELOs: higher is better -> ascending=False
    df_he['HumanEval_Rank'] = df_he['HumanEval_score'].rank(ascending=False, method='min')
    df_he['Overall_Rank'] = df_he['elo_overall'].rank(ascending=False, method='min')
    df_he['Coding_Rank'] = df_he['elo_coding'].rank(ascending=False, method='min')
    
    # Calculate rank differences
    # Positive Diff: HumanEval Rank (e.g. 10) - Overall Rank (e.g. 1) = 9 -> HumanEval underestimates (Model is better in Overall)
    # Negative Diff: HumanEval Rank (e.g. 1) - Overall Rank (e.g. 10) = -9 -> HumanEval overestimates (Model is worse in Overall)
    df_he['Diff_HE_vs_Overall'] = df_he['HumanEval_Rank'] - df_he['Overall_Rank']
    df_he['Diff_HE_vs_Coding'] = df_he['HumanEval_Rank'] - df_he['Coding_Rank']
    
    # Sort by HumanEval Rank
    df_he_sorted = df_he.sort_values('HumanEval_Rank')
    
    # Format for display
    # Rename columns for clarity
    display_cols = {
        'model_name': 'Model',
        'HumanEval_score': 'HumanEval Score',
        'HumanEval_Rank': 'HE Rank',
        'elo_overall': 'Overall ELO',
        'Overall_Rank': 'Overall Rank',
        'elo_coding': 'Coding ELO',
        'Coding_Rank': 'Coding Rank',
        'Diff_HE_vs_Overall': 'Rank Diff (HE - Overall)',
        'Diff_HE_vs_Coding': 'Rank Diff (HE - Coding)'
    }
    df_display = df_he_sorted.rename(columns=display_cols).copy()
    
    # Save CSV
    print(f"Saving analysis to {output_csv}...")
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df_display.to_csv(output_csv, index=False)
    
    # Calculate correlations on this subset
    spearman_overall = df_he['HumanEval_score'].corr(df_he['elo_overall'], method='spearman')
    spearman_coding = df_he['HumanEval_score'].corr(df_he['elo_coding'], method='spearman')
    
    # Create Markdown table manually or use pandas
    # We want a nice readable table
    
    summary_md = f"# HumanEval Ranking Analysis\n\n"
    summary_md += f"**Subset Correlation (N={len(df_he)}):**\n"
    summary_md += f"- Spearman Correlation with Overall ELO: {spearman_overall:.3f}\n"
    summary_md += f"- Spearman Correlation with Coding ELO: {spearman_coding:.3f}\n\n"
    summary_md += "## Ranking Comparison Table\n"
    summary_md += "Sorted by HumanEval Rank (Best to Worst)\n\n"
    
    # Convert to markdown
    summary_md += df_display.to_markdown(index=False, floatfmt=".1f")
    
    print(f"Saving markdown summary to {output_md}...")
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(summary_md)
        
    print("Analysis complete.")
    print("\nTop 12 Models by HumanEval Score:")
    # Print a few columns for terminal output
    print(df_display[['Model', 'HE Rank', 'Overall Rank', 'Coding Rank']].head(12).to_string(index=False))

if __name__ == "__main__":
    analyze_humaneval_rankings()
