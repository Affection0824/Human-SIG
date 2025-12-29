"""
测试所有待定benchmark（can_read_html=false且不是llm-stats.com）的爬取方法

对于每个待定的benchmark，尝试所有可能的爬取方法，并记录哪些方法成功。

使用方法:
    python github/src/ingestion/test_pending_benchmarks.py
"""

import json
import sys
import os
from pathlib import Path
from urllib.parse import urlparse

# 设置Windows控制台UTF-8编码支持
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# 直接导入测试方法（复制必要的函数定义）
# 由于需要共享代码，我们将直接在这里定义测试方法
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
    import lxml.html
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from io import StringIO
import time
import re

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
]

def method_1_pandas_read_html(url):
    """方法1: pandas.read_html()"""
    if not PANDAS_AVAILABLE:
        return False, "pandas库未安装"
    try:
        headers = {"User-Agent": USER_AGENTS[0]}
        tables = pd.read_html(url, storage_options=headers)
        if len(tables) > 0:
            return True, tables[0]
        return False, "未找到表格"
    except Exception as e:
        return False, f"错误: {str(e)}"

def method_2_requests_beautifulsoup(url):
    """方法2: requests + BeautifulSoup"""
    if not REQUESTS_AVAILABLE or not BEAUTIFULSOUP_AVAILABLE:
        return False, "requests或BeautifulSoup库未安装"
    try:
        headers = {"User-Agent": USER_AGENTS[0]}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table')
        if len(tables) > 0:
            return True, f"找到{len(tables)}个表格"
        return False, "未找到表格"
    except Exception as e:
        return False, f"错误: {str(e)}"

def method_3_requests_lxml(url):
    """方法3: requests + lxml"""
    if not REQUESTS_AVAILABLE or not LXML_AVAILABLE:
        return False, "requests或lxml库未安装"
    try:
        headers = {"User-Agent": USER_AGENTS[0]}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        doc = lxml.html.fromstring(response.content)
        tables = doc.xpath('//table')
        if len(tables) > 0:
            return True, f"找到{len(tables)}个表格"
        return False, "未找到表格"
    except Exception as e:
        return False, f"错误: {str(e)}"

def method_4_find_embedded_json(url):
    """方法4: 查找内嵌JSON"""
    if not REQUESTS_AVAILABLE or not BEAUTIFULSOUP_AVAILABLE:
        return False, "requests或BeautifulSoup库未安装"
    try:
        headers = {"User-Agent": USER_AGENTS[0]}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        scripts = soup.find_all('script')
        # 简化检查：只查找明显的JSON数据
        for script in scripts:
            if script.string and ('leaderboard' in script.string.lower() or 'benchmark' in script.string.lower()):
                return True, "在script标签中找到相关数据"
        return False, "未找到内嵌JSON数据"
    except Exception as e:
        return False, f"错误: {str(e)}"

def method_5_try_api_endpoints(url):
    """方法5: 尝试API端点"""
    if not REQUESTS_AVAILABLE:
        return False, "requests库未安装"
    return False, "跳过API端点测试（通常不可用）"

def method_6_selenium(url):
    """方法6: Selenium"""
    if not SELENIUM_AVAILABLE:
        return False, "selenium库未安装"
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
            if PANDAS_AVAILABLE:
                df = pd.read_html(StringIO(html))[0]
                return True, df
            return True, f"找到{len(tables)}个表格"
        return False, "未找到表格"
    except Exception as e:
        return False, f"错误: {str(e)}"
    finally:
        if driver:
            driver.quit()

def main():
    """主函数：测试所有待定的benchmark"""
    
    # 路径设置
    script_path = Path(__file__).resolve()
    github_dir = script_path.parent.parent.parent
    metadata_path = github_dir / "config" / "metadata.json"
    
    # 读取metadata.json
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # 找出待测试的benchmark（can_read_html=false且不是llm-stats.com）
    pending_benchmarks = []
    for entry in metadata:
        if isinstance(entry, dict):
            if 'leaderboard_url' in entry and 'elo_column' not in entry:
                url = entry.get('leaderboard_url', '')
                can_read_html = entry.get('can_read_html', True)
                
                # 排除llm-stats.com（已经确定用Selenium）
                if can_read_html == False and 'llm-stats.com' not in url:
                    pending_benchmarks.append({
                        'name': entry.get('benchmark_name', 'Unknown'),
                        'url': url
                    })
    
    print("="*80)
    print(f"找到 {len(pending_benchmarks)} 个待测试的benchmark")
    print("="*80)
    print()
    
    # 所有测试方法
    test_methods = [
        ("方法1: pandas.read_html()", method_1_pandas_read_html),
        ("方法2: requests + BeautifulSoup", method_2_requests_beautifulsoup),
        ("方法3: requests + lxml", method_3_requests_lxml),
        ("方法4: 查找内嵌JSON", method_4_find_embedded_json),
        ("方法5: 尝试API端点", method_5_try_api_endpoints),
        ("方法6: Selenium", method_6_selenium),
    ]
    
    # 测试结果
    all_results = []
    
    # 逐个测试
    for i, benchmark in enumerate(pending_benchmarks, 1):
        print("\n" + "="*80)
        print(f"测试 {i}/{len(pending_benchmarks)}: {benchmark['name']}")
        print(f"URL: {benchmark['url']}")
        print("="*80)
        
        benchmark_results = {
            'benchmark_name': benchmark['name'],
            'url': benchmark['url'],
            'methods': []
        }
        
        # 测试每种方法
        for method_name, method_func in test_methods:
            print(f"\n--- 测试 {method_name} ---")
            try:
                success, result = method_func(benchmark['url'])
                method_result = {
                    'method': method_name,
                    'success': success,
                    'has_data': result is not None if success else False
                }
                
                if success:
                    # 如果是DataFrame，记录基本信息
                    try:
                        import pandas as pd
                        if isinstance(result, pd.DataFrame):
                            method_result['data_shape'] = [result.shape[0], result.shape[1]]
                            method_result['columns'] = [str(col) for col in result.columns]
                            method_result['row_count'] = len(result)
                            # 不保存完整数据预览到JSON，避免序列化问题
                    except:
                        pass
                    
                    print(f"✓ {method_name} 成功")
                else:
                    method_result['error'] = str(result) if result else "未知错误"
                    print(f"✗ {method_name} 失败: {result}")
                
                benchmark_results['methods'].append(method_result)
                
            except Exception as e:
                method_result = {
                    'method': method_name,
                    'success': False,
                    'error': f"异常: {str(e)}"
                }
                benchmark_results['methods'].append(method_result)
                print(f"✗ {method_name} 异常: {str(e)}")
        
        # 汇总这个benchmark的结果
        successful_methods = [m for m in benchmark_results['methods'] if m['success']]
        benchmark_results['successful_methods_count'] = len(successful_methods)
        benchmark_results['successful_methods'] = [m['method'] for m in successful_methods]
        
        print(f"\n--- {benchmark['name']} 测试结果汇总 ---")
        print(f"成功的方法: {len(successful_methods)}/{len(test_methods)}")
        if successful_methods:
            print("可用的方法:")
            for m in successful_methods:
                print(f"  - {m['method']}")
        
        all_results.append(benchmark_results)
    
    # 最终汇总
    print("\n" + "="*80)
    print("所有待定benchmark测试结果汇总")
    print("="*80)
    
    for result in all_results:
        print(f"\n{result['benchmark_name']}:")
        print(f"  URL: {result['url']}")
        if result['successful_methods']:
            print(f"  ✓ 可用方法 ({len(result['successful_methods'])}):")
            for method in result['successful_methods']:
                print(f"    - {method}")
        else:
            print(f"  ✗ 无可用方法（需要手动下载）")
    
    # 保存详细结果
    output_path = github_dir / "results" / "pending_benchmarks_test_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'test_summary': {
                'total_pending': len(pending_benchmarks),
                'with_successful_methods': sum(1 for r in all_results if r['successful_methods_count'] > 0),
                'need_manual_download': sum(1 for r in all_results if r['successful_methods_count'] == 0)
            },
            'detailed_results': all_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n详细测试结果已保存到: {output_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

