import pandas as pd
import itertools
import json
from pathlib import Path

def find_model_triplets():
    # Define paths - use absolute paths or relative to CWD
    # Current CWD is D:\桌面 2026.1.13\科研\Human-SIG\Human-SIG
    base_dir = Path("D:/桌面 2026.1.13/科研/Human-SIG/Human-SIG")
    input_path = base_dir / "data/processed/master_table/master_correlation_matrix.csv"
    output_json = base_dir / "new/data/model_triplets_candidates.json"
    output_txt = base_dir / "new/data/model_triplets_candidates.txt"
    
    # Ensure output directory exists
    output_json.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading data from {input_path}...")
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        print(f"Error: Could not find {input_path}")
        return

    # Filter models with elo_overall >= 1420
    df_filtered = df[df['elo_overall'] >= 1420].copy()
    print(f"Found {len(df_filtered)} models with Overall ELO >= 1420.")
    
    if len(df_filtered) < 3:
        print("Not enough models found to form a triplet.")
        return

    # Identify benchmark columns
    # Exclude columns starting with 'elo_'
    # Identify by ending with '_score'
    benchmark_cols = []
    for col in df.columns:
        if col.endswith('_score') and not col.startswith('elo_'):
            benchmark_cols.append(col)
    
    print(f"Identified {len(benchmark_cols)} benchmarks.")
    
    # Store clean names mapping
    benchmark_names_map = {col: col.replace('_score', '') for col in benchmark_cols}
    
    # Generate all combinations of 3 models
    # Use index to iterate
    model_indices = df_filtered.index.tolist()
    triplets = list(itertools.combinations(model_indices, 3))
    print(f"Generating combinations for {len(model_indices)} models ({len(triplets)} triplets)...")
    
    candidates = []
    
    for idx1, idx2, idx3 in triplets:
        # Get rows
        row1 = df_filtered.loc[idx1]
        row2 = df_filtered.loc[idx2]
        row3 = df_filtered.loc[idx3]
        
        model1_name = row1['model_name']
        model2_name = row2['model_name']
        model3_name = row3['model_name']
        
        # Check shared benchmarks
        shared_list = []
        for col in benchmark_cols:
            # Check if all 3 have non-NaN values
            if pd.notna(row1[col]) and pd.notna(row2[col]) and pd.notna(row3[col]):
                shared_list.append(benchmark_names_map[col])
        
        count = len(shared_list)
        
        if count > 0:
            candidates.append({
                'models': [
                    {'name': model1_name, 'elo_overall': float(row1['elo_overall'])},
                    {'name': model2_name, 'elo_overall': float(row2['elo_overall'])},
                    {'name': model3_name, 'elo_overall': float(row3['elo_overall'])}
                ],
                'shared_benchmark_count': count,
                'shared_benchmarks': shared_list
            })
    
    # Sort by count descending
    candidates.sort(key=lambda x: x['shared_benchmark_count'], reverse=True)
    
    # Take top 20
    top_candidates = candidates[:20]
    
    # Format output structure for JSON
    # Just list of dicts is fine
    
    print(f"Saving top {len(top_candidates)} candidates to {output_json}...")
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(top_candidates, f, indent=2, ensure_ascii=False)
        
    # Save readable text
    print(f"Saving readable list to {output_txt}...")
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write(f"Top {len(top_candidates)} Model Triplets (ELO >= 1420)\n")
        f.write("=" * 60 + "\n\n")
        
        for i, cand in enumerate(top_candidates, 1):
            f.write(f"Group {i}:\n")
            f.write(f"  Shared Benchmarks Count: {cand['shared_benchmark_count']}\n")
            f.write("  Models:\n")
            for m in cand['models']:
                f.write(f"    - {m['name']} (ELO: {m['elo_overall']})\n")
            f.write(f"  Benchmarks: {', '.join(cand['shared_benchmarks'])}\n")
            f.write("-" * 50 + "\n")
            
    print("Done.")

if __name__ == "__main__":
    find_model_triplets()
