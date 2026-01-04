import pandas as pd
from pathlib import Path

BENCHMARK_MAPPING = {
    # Mapping keys correspond to folder names (normalized to lowercase with spaces), values correspond to CSV column names
    # Folder names now match benchmark_name in metadata.json (with spaces and special characters)
    'aime': 'Intelligence AIME 2025 (Competition Math)',
    'aa-lcr': 'Intelligence AA-LCR (Long Context Reasoning)',
    'ifbench': 'Intelligence IFBench (Instruction Following)',
    'livecodebench': 'Intelligence LiveCodeBench (Coding)',
    'mmlu-pro': 'Intelligence MMLU-Pro (Reasoning & Knowledge)',
    'scicode': 'Intelligence SciCode (Coding)',
    'tau2-bench telecom': 'Intelligence 𝜏²-Bench Telecom (Agentic Tool Use)',
    'terminal-bench hard': 'Intelligence Terminal-Bench Hard (Agentic Coding & Terminal Use)',
    'gpqa diamond': 'Intelligence GPQA Diamond (Scientific Reasoning)',
    "humanity's last exam": "Intelligence Humanity's Last Exam (Reasoning & Knowledge)",
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
        
        for subdir_name_normalized, target_col in BENCHMARK_MAPPING.items():
            # Find the actual folder name (case-insensitive, space-aware matching)
            actual_folder = None
            for folder in data_path.iterdir():
                if folder.is_dir():
                    # Normalize for comparison: lowercase, handle spaces
                    folder_normalized = folder.name.lower().replace('_', ' ')
                    if folder_normalized == subdir_name_normalized:
                        actual_folder = folder.name
                        break
            
            if actual_folder is None:
                print(f"  Warning: Folder not found for {subdir_name_normalized}, skipping...")
                continue
            
            print(f"Processing {actual_folder}...")
            output_dir = data_path / actual_folder
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
