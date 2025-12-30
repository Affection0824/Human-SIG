import pandas as pd
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"

def run_single_benchmark(benchmark_dir):
    input_file = benchmark_dir / 'input.txt'
    with open(input_file, 'r', encoding='utf-8') as f:
        url = f.read().strip()
    
    print(f"Scraping {benchmark_dir.name} from {url}...")
    headers = {"User-Agent": USER_AGENT}
    
    try:
        tables = pd.read_html(url, storage_options=headers)
        if len(tables) == 0:
            print("  Failed: No tables found.")
            return
        
        df = tables[0]
        output_file = benchmark_dir / 'data.csv'
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"  Success! Saved to {output_file}")
    except Exception as e:
        print(f"  Error scraping {url}: {e}")

def run(data_dir):
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"Error: Directory {data_path} does not exist.")
        return

    print(f"Running Pandas Read HTML scraper on {data_path}")
    for subdir in data_path.iterdir():
        if subdir.is_dir() and not subdir.name.startswith('.') and not subdir.name.startswith('__'):
            input_file = subdir / 'input.txt'
            if input_file.exists():
                print(f"Processing {subdir.name}...")
                run_single_benchmark(subdir)
