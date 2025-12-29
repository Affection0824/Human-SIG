"""
综合爬取测试工具：对指定URL测试所有可能的爬取方法

测试方法包括：
1. pandas.read_html() - 直接读取HTML表格
2. requests + BeautifulSoup - 手动解析HTML
3. requests + lxml - 使用lxml解析器
4. 查找内嵌JSON数据
5. 尝试API端点
6. Selenium - JavaScript渲染页面

使用方法:
    python github/src/ingestion/comprehensive_scraping_test.py <URL>
    或直接运行测试所有待定的benchmark URLs
"""

import sys
import os
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
import time
from io import StringIO

# 设置Windows控制台UTF-8编码支持
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# 导入库
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
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# 用户代理
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
HEADERS = {"User-Agent": USER_AGENT}

def method_1_pandas_read_html(url):
    """方法1: pandas.read_html()"""
    if not PANDAS_AVAILABLE:
        return False, "pandas未安装", None
    
    try:
        tables = pd.read_html(url, storage_options=HEADERS)
        if len(tables) > 0:
            df = tables[0]
            return True, f"成功，找到{len(tables)}个表格，第一个表格形状: {df.shape}", df
        else:
            return False, "未找到表格", None
    except Exception as e:
        return False, f"错误: {str(e)[:100]}", None

def method_2_beautifulsoup(url):
    """方法2: requests + BeautifulSoup"""
    if not REQUESTS_AVAILABLE or not BEAUTIFULSOUP_AVAILABLE:
        return False, "requests或BeautifulSoup未安装", None
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table')
        
        if len(tables) > 0:
            table = tables[0]
            rows = table.find_all('tr')
            if len(rows) > 0:
                headers_row = rows[0]
                headers = [th.get_text(strip=True) for th in headers_row.find_all(['th', 'td'])]
                data_rows = []
                for row in rows[1:6]:  # 前5行数据
                    cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                    if cells:
                        data_rows.append(cells)
                
                if data_rows:
                    return True, f"成功，找到{len(tables)}个表格，第一个表格有{len(rows)}行", {"headers": headers, "data": data_rows}
        
        return False, f"找到{len(tables)}个表格但无有效数据", None
    except Exception as e:
        return False, f"错误: {str(e)[:100]}", None

def method_3_lxml(url):
    """方法3: requests + lxml"""
    if not REQUESTS_AVAILABLE or not LXML_AVAILABLE:
        return False, "requests或lxml未安装", None
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        doc = lxml.html.fromstring(response.content)
        tables = doc.xpath('//table')
        
        if len(tables) > 0:
            table = tables[0]
            rows = table.xpath('.//tr')
            if len(rows) > 0:
                data_rows = []
                for row in rows[:6]:
                    cells = [cell.text_content().strip() for cell in row.xpath('.//td | .//th')]
                    if cells:
                        data_rows.append(cells)
                
                if data_rows and len(data_rows) > 1:
                    return True, f"成功，找到{len(tables)}个表格，第一个表格有{len(rows)}行", {"headers": data_rows[0], "data": data_rows[1:]}
        
        return False, f"找到{len(tables)}个表格但无有效数据", None
    except Exception as e:
        return False, f"错误: {str(e)[:100]}", None

def method_4_embedded_json(url):
    """方法4: 查找内嵌JSON"""
    if not REQUESTS_AVAILABLE or not BEAUTIFULSOUP_AVAILABLE:
        return False, "requests或BeautifulSoup未安装", None
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        scripts = soup.find_all('script')
        
        json_found = []
        for script in scripts:
            script_text = script.string
            if not script_text:
                continue
            
            # 查找各种JSON模式
            patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                r'window\.__DATA__\s*=\s*({.+?});',
                r'var\s+\w+\s*=\s*({.+?});',
                r'const\s+\w+\s*=\s*({.+?});',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, script_text, re.DOTALL)
                for match in matches:
                    try:
                        data = json.loads(match)
                        if isinstance(data, dict) and len(data) > 0:
                            json_found.append(data)
                    except json.JSONDecodeError:
                        continue
        
        if json_found:
            return True, f"成功，找到{len(json_found)}个JSON对象", json_found[:3]  # 只返回前3个
        
        return False, f"检查了{len(scripts)}个script标签，未找到JSON数据", None
    except Exception as e:
        return False, f"错误: {str(e)[:100]}", None

def method_5_api_endpoints(url):
    """方法5: 尝试API端点"""
    if not REQUESTS_AVAILABLE:
        return False, "requests未安装", None
    
    parsed = urlparse(url)
    base_path = parsed.path.rstrip('/')
    benchmark_name = base_path.split('/')[-1] if base_path else ''
    
    api_endpoints = [
        f"{parsed.scheme}://{parsed.netloc}/api{base_path}",
        f"{parsed.scheme}://{parsed.netloc}/api{base_path}/data",
        f"{parsed.scheme}://{parsed.netloc}/api{base_path}/leaderboard",
        f"{url}/api",
        f"{url}/data.json",
        f"{url}/leaderboard.json",
    ]
    
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    
    for endpoint in api_endpoints:
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'json' in content_type:
                    try:
                        data = response.json()
                        return True, f"成功，找到API端点: {endpoint}", data
                    except json.JSONDecodeError:
                        continue
        except requests.exceptions.RequestException:
            continue
    
    return False, f"尝试了{len(api_endpoints)}个API端点，未找到可用端点", None

def method_6_selenium(url):
    """方法6: Selenium"""
    if not SELENIUM_AVAILABLE:
        return False, "selenium未安装", None
    
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'user-agent={USER_AGENT}')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(5)  # 等待JavaScript执行
        
        tables = driver.find_elements(By.TAG_NAME, "table")
        
        if len(tables) > 0:
            table = tables[0]
            html = table.get_attribute('outerHTML')
            
            if PANDAS_AVAILABLE:
                df = pd.read_html(StringIO(html))[0]
                driver.quit()
                return True, f"成功，找到{len(tables)}个表格，表格形状: {df.shape}", df
            else:
                rows = table.find_elements(By.TAG_NAME, "tr")
                data = []
                for row in rows[:10]:
                    cells = [cell.text for cell in row.find_elements(By.TAG_NAME, "td") + row.find_elements(By.TAG_NAME, "th")]
                    if cells:
                        data.append(cells)
                driver.quit()
                if data:
                    return True, f"成功，找到{len(tables)}个表格，有{len(rows)}行", data
        
        driver.quit()
        return False, f"找到{len(tables)}个表格元素但无法解析", None
        
    except Exception as e:
        if driver:
            driver.quit()
        return False, f"错误: {str(e)[:100]}", None

def test_url(benchmark_name, url):
    """测试单个URL的所有方法"""
    print(f"\n{'='*80}")
    print(f"测试: {benchmark_name}")
    print(f"URL: {url}")
    print(f"{'='*80}")
    
    methods = [
        ("方法1: pandas.read_html()", method_1_pandas_read_html),
        ("方法2: requests + BeautifulSoup", method_2_beautifulsoup),
        ("方法3: requests + lxml", method_3_lxml),
        ("方法4: 查找内嵌JSON", method_4_embedded_json),
        ("方法5: 尝试API端点", method_5_api_endpoints),
        ("方法6: Selenium", method_6_selenium),
    ]
    
    results = []
    
    for method_name, method_func in methods:
        print(f"\n{method_name}...")
        success, message, data = method_func(url)
        status = "✓ 成功" if success else "✗ 失败"
        print(f"  {status}: {message}")
        
        results.append({
            "method": method_name,
            "success": success,
            "message": message,
            "has_data": data is not None
        })
        
        # 如果成功且有数据，显示数据样本
        if success and data is not None:
            if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
                print(f"\n  数据样本（前5行）:")
                print("  " + str(data.head()).replace("\n", "\n  "))
            elif isinstance(data, dict) and "data" in data:
                print(f"\n  数据样本:")
                print(f"  表头: {data.get('headers', [])}")
                for i, row in enumerate(data['data'][:3]):
                    print(f"  行{i+1}: {row}")
            elif isinstance(data, list) and len(data) > 0:
                print(f"\n  数据样本（前3项）:")
                for i, item in enumerate(data[:3]):
                    print(f"  项{i+1}: {type(item).__name__} with {len(item) if isinstance(item, (dict, list)) else 'N/A'} elements")
    
    return results

def main():
    """主函数"""
    # 读取metadata.json
    script_path = Path(__file__).resolve()
    github_dir = script_path.parent.parent.parent
    metadata_path = github_dir / "config" / "metadata.json"
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # 找出待测试的benchmark（can_read_html=false且不是llm-stats.com）
    pending_benchmarks = []
    for entry in metadata:
        if isinstance(entry, dict):
            if 'leaderboard_url' in entry and 'elo_column' not in entry:
                url = entry.get('leaderboard_url', '')
                if entry.get('can_read_html') == False and 'llm-stats.com' not in url:
                    pending_benchmarks.append({
                        'name': entry.get('benchmark_name', 'Unknown'),
                        'url': url
                    })
    
    print(f"找到 {len(pending_benchmarks)} 个待测试的benchmark\n")
    
    # 测试每个benchmark
    all_results = {}
    
    for benchmark in pending_benchmarks:
        results = test_url(benchmark['name'], benchmark['url'])
        all_results[benchmark['name']] = {
            'url': benchmark['url'],
            'results': results
        }
    
    # 汇总结果
    print(f"\n\n{'='*80}")
    print("测试结果汇总")
    print(f"{'='*80}\n")
    
    for benchmark_name, info in all_results.items():
        successful_methods = [r for r in info['results'] if r['success']]
        print(f"{benchmark_name}:")
        print(f"  URL: {info['url']}")
        if successful_methods:
            print(f"  ✓ 找到 {len(successful_methods)} 种成功的方法:")
            for result in successful_methods:
                print(f"    - {result['method']}: {result['message']}")
        else:
            print(f"  ✗ 所有方法均失败")
        print()
    
    # 保存结果
    output_path = github_dir / "results" / "comprehensive_scraping_test_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"详细结果已保存到: {output_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

