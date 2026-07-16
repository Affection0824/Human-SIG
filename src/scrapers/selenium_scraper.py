from pathlib import Path
import pandas as pd
from io import StringIO
import time

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Error: selenium library not installed. Please run: pip install selenium")

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"

# Benchmark Configurations
BENCHMARK_CONFIGS = {
    'default': {
        'wait_time': 5,
        'table_selector': 'table',
        'required_columns': ['Model'],
        'index_col': None,
        'header': 0
    },
    'arc_agi_2': {
        'wait_time': 10,
        'required_columns': ['Team', 'Score'] 
    },
    'swe_bench_verified': {
        'wait_time': 8,
        'required_columns': ['Model', 'Resolved']
    },
    'swe_bench_bash_only': {
        'wait_time': 8,
        'required_columns': ['Model', 'Resolved']
    }
}

def get_config(benchmark_name):
    config = BENCHMARK_CONFIGS.get('default').copy()
    if benchmark_name in BENCHMARK_CONFIGS:
        config.update(BENCHMARK_CONFIGS[benchmark_name])
    return config

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument(f'user-agent={USER_AGENT}')
    
    try:
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"  Warning: Could not use webdriver-manager ({e}). Trying default...")
        driver = webdriver.Chrome(options=chrome_options)
    return driver

def extract_best_table(driver, config):
    wait_time = config.get('wait_time', 5)
    selector = config.get('table_selector', 'table')
    required_cols = config.get('required_columns', [])
    
    print(f"  Waiting {wait_time}s for page to load...")
    time.sleep(wait_time)
    
    try:
        tables = driver.find_elements(By.CSS_SELECTOR, selector)
    except Exception as e:
        print(f"  Error searching for tables: {e}")
        return None

    if not tables:
        print(f"  No tables found with selector '{selector}'")
        return None
        
    best_df = None
    max_score = -1
    
    for i, table in enumerate(tables):
        try:
            html = table.get_attribute('outerHTML')
            dfs = pd.read_html(StringIO(html), header=config.get('header', 0))
            if not dfs:
                continue
            
            df = dfs[0]
            score = 0
            if required_cols:
                cols_lower = [str(c).lower() for c in df.columns]
                matches = sum(1 for req in required_cols if any(req.lower() in c for c in cols_lower))
                score = matches
                if len(df) > 0:
                    score += 0.5
            else:
                score = len(df)
            
            if required_cols and score >= len(required_cols):
                return df
            
            if score > max_score:
                max_score = score
                best_df = df
        except Exception:
            continue
            
    return best_df

def run_single_benchmark(benchmark_dir):
    if not SELENIUM_AVAILABLE:
        print("Skipping: Selenium not installed.")
        return

    input_file = benchmark_dir / 'input.txt'
    if not input_file.exists():
        print(f"Error: {input_file} not found.")
        return
        
    with open(input_file, 'r', encoding='utf-8') as f:
        url = f.read().strip()
        
    print(f"[{benchmark_dir.name}] Scraping from {url}...")
    
    driver = None
    try:
        driver = setup_driver()
        driver.get(url)
        config = get_config(benchmark_dir.name)
        df = extract_best_table(driver, config)
        
        if df is not None and not df.empty:
            output_file = benchmark_dir / 'data.csv'
            df.to_csv(output_file, index=False, encoding='utf-8')
            print(f"  Success! Saved to {output_file} ({len(df)} rows)")
        else:
            print("  Failed: No valid data extracted.")
    except Exception as e:
        print(f"  Error scraping {url}: {e}")
    finally:
        if driver:
            driver.quit()

def run(data_dir):
    """
    Run scraper for all subdirectories in data_dir.
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"Error: Directory {data_path} does not exist.")
        return

    print(f"Running Selenium scraper on {data_path}")
    for subdir in data_path.iterdir():
        if subdir.is_dir() and not subdir.name.startswith('.') and not subdir.name.startswith('__'):
            input_file = subdir / 'input.txt'
            if input_file.exists():
                run_single_benchmark(subdir)
