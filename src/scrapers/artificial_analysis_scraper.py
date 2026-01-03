import pandas as pd
from pathlib import Path

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

def run(data_dir):
    """
    Extract data for each benchmark from combined_all_benchmarks.csv to corresponding folders
    
    Args:
        data_dir: Data directory path (contains combined_all_benchmarks.csv)
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"Error: Directory {data_path} does not exist.")
        return

    input_file = data_path / 'combined_all_benchmarks.csv'
    if not input_file.exists():
        print(f"Error: {input_file} not found.")
        return

    print(f"Reading {input_file}...")
    try:
        df = pd.read_csv(input_file)
        print(f"  Loaded table with {len(df)} rows and {len(df.columns)} columns.")
        
        for subdir_name, target_col in BENCHMARK_MAPPING.items():
            print(f"Processing {subdir_name}...")
            output_dir = data_path / subdir_name
            output_dir.mkdir(exist_ok=True)
            
            cols_to_keep = ['Model', 'Features Creator']
            if target_col in df.columns:
                cols_to_keep.append(target_col)
            
            valid_cols = [c for c in cols_to_keep if c in df.columns]
            df_subset = df[valid_cols].copy()
            
            output_file = output_dir / 'data.csv'
            df_subset.to_csv(output_file, index=False)
            print(f"  Saved filtered data to {output_file} (Rows: {len(df_subset)})")
            
    except Exception as e:
        print(f"Error processing combined_all_benchmarks.csv: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # Default to use artificial_analysis data directory
    data_directory = Path(__file__).parent.parent.parent / 'data' / 'raw' / 'artificial_analysis'
    run(data_directory)
