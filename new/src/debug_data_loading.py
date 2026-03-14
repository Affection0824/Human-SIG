import pandas as pd
from pathlib import Path
import sys

# Add src to path if needed, or just run inline
base_dir = Path("D:/桌面 2026.1.13/科研/Human-SIG/Human-SIG")
master_path = base_dir / "data/processed/master_table/master_correlation_matrix.csv"
analysis_ready_path = base_dir / "results/analysis_ready_data.csv"
lmarena_path = base_dir / "data/raw/lmarena/LMArena-Overall/data.csv"

print(f"Checking paths:")
print(f"Master: {master_path.exists()}")
print(f"Analysis: {analysis_ready_path.exists()}")
print(f"LMArena: {lmarena_path.exists()}")

try:
    df_master = pd.read_csv(master_path)
    print(f"Master shape: {df_master.shape}")
    print(f"Master columns: {df_master.columns.tolist()[:5]}")
except Exception as e:
    print(f"Error loading master: {e}")

try:
    df_analysis = pd.read_csv(analysis_ready_path)
    print(f"Analysis shape: {df_analysis.shape}")
    print(f"First few benchmarks: {df_analysis['benchmark_id'].head().tolist()}")
except Exception as e:
    print(f"Error loading analysis: {e}")

try:
    df_arena = pd.read_csv(lmarena_path)
    print(f"LMArena shape: {df_arena.shape}")
    print(f"LMArena columns: {df_arena.columns.tolist()}")
    print(f"First few rows of '95% CI (±)': {df_arena['95% CI (±)'].head().tolist()}")
except Exception as e:
    print(f"Error loading LMArena: {e}")
