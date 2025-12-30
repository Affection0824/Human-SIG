import sys
import pandas as pd
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"

def run_scraper(benchmark_dir):
    """
    通用pandas.read_html爬虫函数
    :param benchmark_dir: benchmark目录路径 (Path对象)
    """
    input_file = benchmark_dir / 'input.txt'
    if not input_file.exists():
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        url = f.read().strip()
    
    print(f"Scraping {benchmark_dir.name} from {url}...")
    
    headers = {
        "User-Agent": USER_AGENT,
    }
    
    try:
        tables = pd.read_html(url, storage_options=headers)
        
        if len(tables) == 0:
            print("Error: No tables found.")
            return
        
        df = tables[0]
        output_file = benchmark_dir / 'data.csv'
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"Success! Saved to {output_file}")
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        import traceback
        traceback.print_exc()
