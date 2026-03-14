import pandas as pd
from pathlib import Path
import scipy.stats as stats

def calculate_pearson():
    # Define paths
    base_dir = Path("D:/桌面 2026.1.13/科研/Human-SIG/Human-SIG")
    input_path = base_dir / "new/data/triplet_difficulty_comparison.csv"
    
    print(f"Loading data from {input_path}...")
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        print(f"Error: Could not find {input_path}")
        return

    # Check for NaN
    df_clean = df.dropna(subset=['Original_Difficulty', 'Triplet_Difficulty'])
    
    if len(df_clean) < 2:
        print("Not enough data points to calculate correlation.")
        return

    # Calculate Pearson correlation
    pearson_corr, p_value = stats.pearsonr(df_clean['Original_Difficulty'], df_clean['Triplet_Difficulty'])
    
    print(f"\nPearson Correlation Coefficient (r): {pearson_corr:.4f}")
    print(f"P-value: {p_value:.4e}")
    print(f"Sample size (N): {len(df_clean)}")

if __name__ == "__main__":
    calculate_pearson()
