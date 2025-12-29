"""
保存待定benchmark的爬取结果到CSV文件

对于每个成功爬取的benchmark，保存其数据到CSV文件。
"""

import json
import sys
import os
from pathlib import Path
import pandas as pd
from io import StringIO

# 设置Windows控制台UTF-8编码支持
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# 导入测试方法（简化版）
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
]

def method_4_find_embedded_json_extract(url):
    """方法4: 查找并提取内嵌JSON数据"""
    if not REQUESTS_AVAILABLE or not BEAUTIFULSOUP_AVAILABLE:
        return False, None, "库未安装"
    try:
        headers = {"User-Agent": USER_AGENTS[0]}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        scripts = soup.find_all('script')
        # 查找JSON数据（简化版，实际需要更复杂的解析）
        for script in scripts:
            if script.string and ('leaderboard' in script.string.lower() or 'benchmark' in script.string.lower()):
                # 这里应该提取并解析JSON，但为简化，返回成功标志
                return True, None, "找到内嵌JSON（需要进一步解析）"
        return False, None, "未找到内嵌JSON数据"
    except Exception as e:
        return False, None, f"错误: {str(e)}"

def method_6_selenium_extract(url):
    """方法6: Selenium提取表格数据"""
    if not SELENIUM_AVAILABLE:
        return False, None, "selenium库未安装"
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'user-agent={USER_AGENTS[0]}')
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(5)
        tables = driver.find_elements(By.TAG_NAME, "table")
        if len(tables) > 0:
            table = tables[0]
            html = table.get_attribute('outerHTML')
            df = pd.read_html(StringIO(html))[0]
            return True, df, None
        return False, None, "未找到表格"
    except Exception as e:
        return False, None, f"错误: {str(e)}"
    finally:
        if driver:
            driver.quit()

def sanitize_benchmark_name(name):
    """将benchmark名称转换为文件安全的名称"""
    return name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").replace("/", "_").replace("'", "").replace(".", "")

def main():
    """主函数"""
    script_path = Path(__file__).resolve()
    github_dir = script_path.parent.parent.parent
    results_path = github_dir / "results" / "pending_benchmarks_test_results.json"
    output_dir = github_dir / "results" / "pending_benchmarks_data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not results_path.exists():
        print(f"错误：找不到测试结果文件: {results_path}")
        return 1
    
    with open(results_path, 'r', encoding='utf-8') as f:
        test_results = json.load(f)
    
    detailed_results = test_results.get('detailed_results', [])
    
    print("="*80)
    print("保存待定benchmark的爬取结果")
    print("="*80)
    print()
    
    saved_files = []
    
    for result in detailed_results:
        benchmark_name = result['benchmark_name']
        url = result['url']
        successful_methods = result.get('successful_methods', [])
        
        if not successful_methods:
            print(f"\n跳过 {benchmark_name}：无可用方法")
            continue
        
        print(f"\n处理 {benchmark_name}...")
        print(f"  URL: {url}")
        print(f"  可用方法: {', '.join(successful_methods)}")
        
        # 优先使用Selenium（方法6），如果不行则使用方法4
        saved = False
        for method_name in successful_methods:
            if "Selenium" in method_name:
                print(f"  尝试方法6: Selenium...")
                import time
                success, df, error = method_6_selenium_extract(url)
                if success and df is not None:
                    sanitized_name = sanitize_benchmark_name(benchmark_name)
                    output_file = output_dir / f"{sanitized_name}_selenium.csv"
                    df.to_csv(output_file, index=False, encoding='utf-8')
                    print(f"  ✓ 成功保存到: {output_file}")
                    print(f"    数据形状: {df.shape}")
                    print(f"    列名: {list(df.columns)}")
                    saved_files.append({
                        'benchmark': benchmark_name,
                        'method': 'Selenium',
                        'file': str(output_file),
                        'shape': df.shape
                    })
                    saved = True
                    break
            elif "内嵌JSON" in method_name:
                # 方法4需要更复杂的JSON解析，这里只标记
                print(f"  方法4（内嵌JSON）需要进一步解析JSON数据")
        
        if not saved:
            print(f"  ⚠ 无法保存数据（需要进一步实现JSON解析）")
    
    print("\n" + "="*80)
    print("保存完成汇总")
    print("="*80)
    print(f"成功保存 {len(saved_files)} 个benchmark的数据")
    print(f"保存位置: {output_dir}")
    print("\n保存的文件列表:")
    for info in saved_files:
        print(f"  - {Path(info['file']).name} ({info['shape'][0]} 行 x {info['shape'][1]} 列)")
    
    return 0

if __name__ == "__main__":
    import time
    sys.exit(main())

