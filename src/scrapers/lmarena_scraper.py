import pandas as pd
from io import StringIO
from pathlib import Path

def parse_lmarena_table(input_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        html = f.read()

    dfs = pd.read_html(StringIO(html))
    if not dfs:
        raise ValueError("No tables found in HTML")
    return dfs[0]

def run(data_dir):
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"Error: Directory {data_path} does not exist.")
        return

    print(f"Running LMArena scraper on {data_path}")
    for subdir in data_path.iterdir():
        if subdir.is_dir() and not subdir.name.startswith('.') and not subdir.name.startswith('__'):
            input_file = subdir / 'input.txt'
            if input_file.exists():
                print(f"Processing {subdir.name}...")
                try:
                    df = parse_lmarena_table(input_file)
                    if not df.empty:
                        output_file = subdir / 'data.csv'
                        df.to_csv(output_file, index=False, encoding='utf-8')
                        print(f"  Saved data to {output_file} (Rows: {len(df)})")
                    else:
                        print(f"  Warning: No data extracted for {subdir.name}")
                except Exception as e:
                    print(f"  Error processing {subdir.name}: {e}")
