import pandas as pd
from pathlib import Path
from io import StringIO

BENCHMARK_MAPPING = {
    # Mapping keys correspond to new folder names (for documentation reference), values correspond to CSV column names
    'MMLU-Pro': 'Intelligence MMLU-Pro (Reasoning & Knowledge)',
    'SciCode': 'Intelligence SciCode (Coding)',
    'AIME': 'Intelligence AIME 2025 (Competition Math)',
    'AA-LCR': 'Intelligence AA-LCR (Long Context Reasoning)',
    'tau2-Bench_Telecom': 'Intelligence 𝜏²-Bench Telecom (Agentic Tool Use)',
    'GPQA_Diamond': 'Intelligence GPQA Diamond (Scientific Reasoning)',
    'LiveCodeBench': 'Intelligence LiveCodeBench (Coding)',
    'Humanitys_Last_Exam': "Intelligence Humanity's Last Exam (Reasoning & Knowledge)",
    'Terminal-Bench_Hard': 'Intelligence Terminal-Bench Hard (Agentic Coding & Terminal Use)',
    'IFBench': 'Intelligence IFBench (Instruction Following)',
}

def parse_html_table(input_path):
    """Parse tables from HTML file"""
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    dfs = pd.read_html(StringIO(content))
    if not dfs:
        raise ValueError("No tables found in HTML")
    
    df = dfs[0]
    if isinstance(df.columns, pd.MultiIndex):
        new_columns = []
        for col in df.columns:
            new_columns.append(" ".join([str(c) for c in col if "Unnamed" not in str(c)]).strip())
        df.columns = new_columns
    return df

def run(data_dir, output_file='combined_data.csv'):
    """
    Extract all benchmark data from input.txt and merge into a single CSV file
    
    Args:
        data_dir: Data directory path (contains input.txt)
        output_file: Output filename, default is 'combined_data.csv'
    """
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
        
        # Build columns to keep: Model, Features Creator, Intelligence Index, and all benchmark columns
        cols_to_keep = ['Model', 'Features Creator']
        
        # Find and add "artificial analysis intelligence index" column (case variations possible)
        intelligence_index_col = None
        for col in df.columns:
            if 'intelligence index' in str(col).lower() or 'artificial analysis intelligence index' in str(col).lower():
                intelligence_index_col = col
                break
        
        if intelligence_index_col:
            cols_to_keep.append(intelligence_index_col)
            print(f"  Found Intelligence Index column: {intelligence_index_col}")
        
        # Add all existing benchmark columns
        for target_col in BENCHMARK_MAPPING.values():
            if target_col in df.columns:
                cols_to_keep.append(target_col)
        
        # Keep only existing columns
        valid_cols = [c for c in cols_to_keep if c in df.columns]
        df_subset = df[valid_cols].copy()
        
        # Sort by model name in dictionary order
        if 'Model' in df_subset.columns:
            df_subset = df_subset.sort_values(by='Model', ascending=True).reset_index(drop=True)
            print(f"  Sorted by Model name (dictionary order)")
        
        # Save to output file
        output_path = data_path / output_file
        df_subset.to_csv(output_path, index=False)
        print(f"  Saved combined data to {output_path}")
        print(f"  Total rows: {len(df_subset)}, Total columns: {len(df_subset.columns)}")
        print(f"  Included benchmarks: {len([c for c in df_subset.columns if c in BENCHMARK_MAPPING.values()])}")
        
    except Exception as e:
        print(f"Error processing input.txt: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # Default to use artificial_analysis data directory
    data_directory = Path(__file__).parent.parent.parent / 'data' / 'raw' / 'artificial_analysis'
    run(data_directory, output_file='combined_all_benchmarks.csv')

