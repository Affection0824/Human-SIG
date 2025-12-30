import sys
from pathlib import Path
import pandas as pd
from io import StringIO
import time
import os

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("错误: selenium库未安装，请运行: pip install selenium")

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"

def run_scraper(benchmark_dir):
    """
    通用Selenium爬虫函数
    :param benchmark_dir: benchmark目录路径 (Path对象)
    """
    if not SELENIUM_AVAILABLE:
        print("Skipping: Selenium not installed.")
        return

    input_file = benchmark_dir / 'input.txt'
    if not input_file.exists():
        print(f"Error: {input_file} not found.")
        return
        
    with open(input_file, 'r', encoding='utf-8') as f:
        url = f.read().strip()
        
    print(f"Scraping {benchmark_dir.name} from {url}...")
    
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'user-agent={USER_AGENT}')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        print("Waiting for page load...")
        time.sleep(5) # Simple wait
        
        tables = driver.find_elements(By.TAG_NAME, "table")
        
        if len(tables) == 0:
            print("Error: No tables found.")
            return
            
        print(f"Found {len(tables)} tables. Using the first one.")
        table = tables[0]
        html = table.get_attribute('outerHTML')
        
        dfs = pd.read_html(StringIO(html))
        if len(dfs) == 0:
            print("Error: Could not parse table with pandas.")
            return
            
        df = dfs[0]
        output_file = benchmark_dir / 'data.csv'
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"Success! Saved to {output_file}")
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
