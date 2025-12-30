import pandas as pd
from pathlib import Path
import os

BENCHMARK_MAPPING = {
    'mmlu_pro': 'Intelligence MMLU-Pro (Reasoning & Knowledge)',
    'scicode': 'Intelligence SciCode (Coding)',
    'aime_2025': 'Intelligence AIME 2025 (Competition Math)',
    'aa_lcr': 'Intelligence AA-LCR (Long Context Reasoning)',
    'tau_bench_telecom': 'Intelligence 𝜏²-Bench Telecom (Agentic Tool Use)',
    'gpqa_diamond': 'Intelligence GPQA Diamond (Scientific Reasoning)',
    'live_code_bench': 'Intelligence LiveCodeBench (Coding)',
    'humanitys_last_exam': "Intelligence Humanity's Last Exam (Reasoning & Knowledge)",
    'terminal_bench_hard': 'Intelligence Terminal-Bench Hard (Agentic Coding & Terminal Use)',
    'ifbench': 'Intelligence IFBench (Instruction Following)',
}

def parse_html_table(input_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    dfs = pd.read_html(content)
    if not dfs:
        raise ValueError("No tables found in HTML")
    
    df = dfs[0]
    if isinstance(df.columns, pd.MultiIndex):
        new_columns = []
        for col in df.columns:
            new_columns.append(" ".join([str(c) for c in col if "Unnamed" not in str(c)]).strip())
        df.columns = new_columns
    return df

def run(data_dir):
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"Error: Directory {data_path} does not exist.")
        return

    input_file = data_path / 'input.txt'
    if not input_file.exists():
        print(f"Error: {input_file} not found.")
        return

    print(f"Parsing {input_file}...")
    try:
        df = parse_html_table(input_file)
        print(f"  Extracted table with {len(df)} rows and {len(df.columns)} columns.")
        
        for subdir_name, target_col in BENCHMARK_MAPPING.items():
            print(f"Processing {subdir_name}...")
            output_dir = data_path / subdir_name
            output_dir.mkdir(exist_ok=True)
            
            cols_to_keep = ['Model', 'Features Creator']
            if target_col in df.columns:
                cols_to_keep.append(target_col)
            
            valid_cols = [c for c in cols_to_keep if c in df.columns]
            df_subset = df[valid_cols]
            
            output_file = output_dir / 'data.csv'
            df_subset.to_csv(output_file, index=False)
            print(f"  Saved filtered data to {output_file} (Rows: {len(df_subset)})")
            
    except Exception as e:
        print(f"Error processing input.txt: {e}")
