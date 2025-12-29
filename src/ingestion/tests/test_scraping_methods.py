"""
综合测试脚本：尝试多种方法爬取网站排行榜数据

测试方法包括：
1. pandas.read_html() - 直接读取HTML表格
2. requests + BeautifulSoup - 手动解析HTML
3. requests + lxml - 使用lxml解析器
4. 查找内嵌JSON数据 - 检查script标签中的JSON
5. 尝试API端点 - 检查常见的API路径
6. selenium - 如果需要JavaScript渲染（如果已安装）
7. 不同的User-Agent和请求头

使用方法:
    python github/src/ingestion/test_scraping_methods.py <URL>
    或直接运行测试 GPQA URL
"""

import sys
import os
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from io import StringIO
import time

# 设置Windows控制台UTF-8编码支持
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# 导入基础库
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("警告: requests库未安装")

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False
    print("警告: beautifulsoup4库未安装")

try:
    import lxml.html
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    print("警告: lxml库未安装")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("警告: pandas库未安装")

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("警告: selenium库未安装")

# 用户代理列表
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

def method_1_pandas_read_html(url):
    """方法1: 使用pandas.read_html()直接读取HTML表格"""
    print("\n" + "="*80)
    print("方法1: pandas.read_html()")
    print("="*80)
    
    if not PANDAS_AVAILABLE:
        return False, "pandas库未安装"
    
    try:
        headers = {
            "User-Agent": USER_AGENTS[0]
        }
        tables = pd.read_html(url, storage_options=headers)
        
        if len(tables) > 0:
            print(f"✓ 成功！找到 {len(tables)} 个表格")
            print(f"第一个表格形状: {tables[0].shape}")
            print("\n前5行数据:")
            print(tables[0].head())
            return True, tables[0]
        else:
            return False, "未找到表格"
    except Exception as e:
        return False, f"错误: {str(e)}"

def method_2_requests_beautifulsoup(url):
    """方法2: requests + BeautifulSoup 解析HTML"""
    print("\n" + "="*80)
    print("方法2: requests + BeautifulSoup")
    print("="*80)
    
    if not REQUESTS_AVAILABLE or not BEAUTIFULSOUP_AVAILABLE:
        return False, "requests或BeautifulSoup库未安装"
    
    try:
        headers = {
            "User-Agent": USER_AGENTS[0],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 查找表格
        tables = soup.find_all('table')
        print(f"找到 {len(tables)} 个<table>标签")
        
        if len(tables) > 0:
            # 尝试解析第一个表格
            table = tables[0]
            rows = table.find_all('tr')
            print(f"第一个表格有 {len(rows)} 行")
            
            # 提取表头
            headers_row = rows[0] if rows else None
            if headers_row:
                headers_text = [th.get_text(strip=True) for th in headers_row.find_all(['th', 'td'])]
                print(f"表头: {headers_text}")
            
            # 提取前几行数据
            data_rows = []
            for row in rows[1:6]:  # 只取前5行数据
                cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                if cells:
                    data_rows.append(cells)
                    print(f"数据行: {cells}")
            
            if data_rows:
                return True, {"headers": headers_text, "data": data_rows}
            else:
                return False, "表格存在但无数据行"
        else:
            # 检查是否有div或其他容器包含数据
            print("\n检查其他可能的数据容器...")
            
            # 查找包含"leaderboard"、"ranking"、"table"等关键词的元素
            keywords = ['leaderboard', 'ranking', 'table', 'benchmark', 'score']
            for keyword in keywords:
                elements = soup.find_all(attrs={'class': re.compile(keyword, re.I)})
                if elements:
                    print(f"找到包含'{keyword}'的元素: {len(elements)}个")
                    for elem in elements[:3]:  # 只显示前3个
                        text = elem.get_text(strip=True)[:200]
                        print(f"  内容预览: {text}...")
            
            return False, "未找到<table>标签"
            
    except Exception as e:
        return False, f"错误: {str(e)}"

def method_3_requests_lxml(url):
    """方法3: requests + lxml 解析HTML"""
    print("\n" + "="*80)
    print("方法3: requests + lxml")
    print("="*80)
    
    if not REQUESTS_AVAILABLE or not LXML_AVAILABLE:
        return False, "requests或lxml库未安装"
    
    try:
        headers = {
            "User-Agent": USER_AGENTS[0],
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        doc = lxml.html.fromstring(response.content)
        
        # 查找表格
        tables = doc.xpath('//table')
        print(f"找到 {len(tables)} 个<table>元素")
        
        if len(tables) > 0:
            table = tables[0]
            rows = table.xpath('.//tr')
            print(f"第一个表格有 {len(rows)} 行")
            
            # 提取数据
            data_rows = []
            for row in rows[:6]:  # 前6行（包括表头）
                cells = [cell.text_content().strip() for cell in row.xpath('.//td | .//th')]
                if cells:
                    data_rows.append(cells)
                    print(f"行数据: {cells}")
            
            if data_rows and len(data_rows) > 1:
                return True, {"headers": data_rows[0], "data": data_rows[1:]}
            else:
                return False, "表格存在但数据不足"
        else:
            return False, "未找到<table>元素"
            
    except Exception as e:
        return False, f"错误: {str(e)}"

def method_4_find_embedded_json(url):
    """方法4: 查找页面中内嵌的JSON数据"""
    print("\n" + "="*80)
    print("方法4: 查找内嵌JSON数据")
    print("="*80)
    
    if not REQUESTS_AVAILABLE or not BEAUTIFULSOUP_AVAILABLE:
        return False, "requests或BeautifulSoup库未安装"
    
    try:
        headers = {
            "User-Agent": USER_AGENTS[0],
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 查找script标签中的JSON数据
        scripts = soup.find_all('script')
        print(f"找到 {len(scripts)} 个<script>标签")
        
        json_data_found = []
        
        for i, script in enumerate(scripts):
            script_text = script.string
            if not script_text:
                continue
            
            # 尝试查找JSON对象
            # 方法1: 查找 window.__INITIAL_STATE__ 或类似的结构
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
                        json_data_found.append(data)
                        print(f"\n✓ 在script标签{i}中找到JSON数据（使用模式: {pattern[:30]}...）")
                        print(f"JSON键: {list(data.keys())[:10]}")
                    except json.JSONDecodeError:
                        continue
            
            # 方法2: 查找看起来像JSON的字符串（更深入的搜索）
            script_lower = script_text.lower()
            if any(keyword in script_lower for keyword in ['leaderboard', 'benchmark', 'gpqa', 'model', 'score', 'rank']):
                # 尝试多种JSON提取模式
                # 模式1: 查找 JSON.parse(...) 或类似结构
                json_parse_patterns = [
                    r'JSON\.parse\(["\'](.+?)["\']\)',
                    r'JSON\.parse\(`(.+?)`\)',
                ]
                for pattern in json_parse_patterns:
                    matches = re.findall(pattern, script_text, re.DOTALL)
                    for match in matches:
                        try:
                            # 可能需要解码
                            decoded = match.replace('\\"', '"').replace("\\'", "'")
                            data = json.loads(decoded)
                            if isinstance(data, dict) and len(data) > 0:
                                json_data_found.append(data)
                                print(f"\n✓ 在script标签{i}中找到JSON.parse数据")
                                print(f"JSON键: {list(data.keys())[:10]}")
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            continue
                
                # 模式2: 查找嵌套的JSON对象（更复杂的正则）
                # 尝试查找大块的JSON数据
                json_block_patterns = [
                    r'\{[^{}]*(?:\{[^{}]*\}[^{}]*){3,}.*?\}',  # 嵌套多层的大对象
                ]
                for pattern in json_block_patterns:
                    matches = re.findall(pattern, script_text, re.DOTALL)
                    for match in matches[:3]:  # 只检查前3个
                        try:
                            data = json.loads(match)
                            if isinstance(data, dict) and len(data) > 5:  # 至少5个键
                                json_data_found.append(data)
                                print(f"\n✓ 在script标签{i}中找到大型JSON对象")
                                print(f"JSON键: {list(data.keys())[:15]}")
                        except json.JSONDecodeError:
                            continue
                
                # 模式3: 查找数组数据
                array_patterns = [
                    r'\[[^\]]*\{[^}]*\}[^\]]*\]',  # 包含对象的数组
                ]
                for pattern in array_patterns:
                    matches = re.findall(pattern, script_text, re.DOTALL)
                    for match in matches[:3]:
                        try:
                            data = json.loads(match)
                            if isinstance(data, list) and len(data) > 0:
                                json_data_found.append(data)
                                print(f"\n✓ 在script标签{i}中找到JSON数组（长度: {len(data)}）")
                                if isinstance(data[0], dict):
                                    print(f"数组元素键: {list(data[0].keys())[:10]}")
                        except json.JSONDecodeError:
                            continue
        
        # 查找data属性中的JSON
        elements_with_data = soup.find_all(attrs={'data-': True})
        for elem in elements_with_data[:10]:  # 检查前10个
            for attr_name, attr_value in elem.attrs.items():
                if 'data-' in attr_name and attr_value:
                    try:
                        data = json.loads(attr_value)
                        json_data_found.append(data)
                        print(f"\n✓ 在元素属性 {attr_name} 中找到JSON数据")
                    except (json.JSONDecodeError, TypeError):
                        continue
        
        if json_data_found:
            return True, json_data_found
        else:
            return False, "未找到内嵌JSON数据"
            
    except Exception as e:
        return False, f"错误: {str(e)}"

def method_5_try_api_endpoints(base_url):
    """方法5: 尝试常见的API端点"""
    print("\n" + "="*80)
    print("方法5: 尝试API端点")
    print("="*80)
    
    if not REQUESTS_AVAILABLE:
        return False, "requests库未安装"
    
    # 从URL中提取基础路径
    parsed = urlparse(base_url)
    base_path = parsed.path.rstrip('/')
    
    # 从URL中提取benchmark名称
    benchmark_name = base_path.split('/')[-1] if base_path else ''
    
    # 常见的API端点模式
    api_endpoints = [
        # 基础API路径
        f"{parsed.scheme}://{parsed.netloc}/api{base_path}",
        f"{parsed.scheme}://{parsed.netloc}/api{base_path}/data",
        f"{parsed.scheme}://{parsed.netloc}/api{base_path}/leaderboard",
        f"{parsed.scheme}://{parsed.netloc}/api/benchmarks/{benchmark_name}",
        f"{parsed.scheme}://{parsed.netloc}/api/v1/benchmarks/{benchmark_name}",
        f"{parsed.scheme}://{parsed.netloc}/api/v2/benchmarks/{benchmark_name}",
        # JSON文件
        f"{base_url}/api",
        f"{base_url}/data.json",
        f"{base_url}/leaderboard.json",
        f"{base_url}/api/leaderboard",
        # GraphQL端点
        f"{parsed.scheme}://{parsed.netloc}/graphql",
        f"{parsed.scheme}://{parsed.netloc}/api/graphql",
        # 其他可能的端点
        f"{parsed.scheme}://{parsed.netloc}/api/benchmark/{benchmark_name}/leaderboard",
        f"{parsed.scheme}://{parsed.netloc}/api/benchmarks/{benchmark_name}/scores",
        f"{parsed.scheme}://{parsed.netloc}/api/benchmarks/{benchmark_name}/results",
    ]
    
    headers = {
        "User-Agent": USER_AGENTS[0],
        "Accept": "application/json",
    }
    
    for endpoint in api_endpoints:
        try:
            print(f"尝试: {endpoint}")
            response = requests.get(endpoint, headers=headers, timeout=10)
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'json' in content_type:
                    try:
                        data = response.json()
                        print(f"✓ 成功！找到API端点: {endpoint}")
                        print(f"响应数据类型: {type(data)}")
                        if isinstance(data, dict):
                            print(f"JSON键: {list(data.keys())[:10]}")
                        return True, data
                    except json.JSONDecodeError:
                        continue
        except requests.exceptions.RequestException:
            continue
    
    return False, "未找到可用的API端点"

def method_6_selenium(url):
    """方法6: 使用Selenium处理JavaScript渲染的页面"""
    print("\n" + "="*80)
    print("方法6: Selenium (需要Chrome浏览器)")
    print("="*80)
    
    if not SELENIUM_AVAILABLE:
        return False, "selenium库未安装"
    
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 无头模式
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'user-agent={USER_AGENTS[0]}')
        
        print("启动Chrome浏览器...")
        driver = webdriver.Chrome(options=chrome_options)
        
        print(f"访问URL: {url}")
        driver.get(url)
        
        # 等待页面加载
        print("等待页面加载...")
        time.sleep(5)  # 等待5秒让JavaScript执行
        
        # 查找表格
        try:
            tables = driver.find_elements(By.TAG_NAME, "table")
            print(f"找到 {len(tables)} 个表格元素")
            
            if len(tables) > 0:
                table = tables[0]
                html = table.get_attribute('outerHTML')
                
                # 使用pandas解析
                if PANDAS_AVAILABLE:
                    from io import StringIO
                    df = pd.read_html(StringIO(html))[0]
                    print(f"✓ 成功！表格形状: {df.shape}")
                    print("\n前5行数据:")
                    print(df.head())
                    return True, df
                else:
                    # 手动解析
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    data = []
                    for row in rows[:10]:
                        cells = [cell.text for cell in row.find_elements(By.TAG_NAME, "td") + row.find_elements(By.TAG_NAME, "th")]
                        if cells:
                            data.append(cells)
                    if data:
                        return True, data
        except Exception as e:
            print(f"查找表格时出错: {str(e)}")
        
        # 检查页面源代码中是否有数据
        page_source = driver.page_source
        if 'leaderboard' in page_source.lower() or 'table' in page_source.lower():
            print("页面源代码中包含'leaderboard'或'table'关键词")
            # 尝试用BeautifulSoup解析
            if BEAUTIFULSOUP_AVAILABLE:
                soup = BeautifulSoup(page_source, 'html.parser')
                tables = soup.find_all('table')
                if tables:
                    print(f"使用BeautifulSoup找到 {len(tables)} 个表格")
                    return True, f"找到 {len(tables)} 个表格，需要进一步解析"
        
        return False, "未找到表格数据"
        
    except Exception as e:
        return False, f"错误: {str(e)}"
    finally:
        if driver:
            driver.quit()
            print("关闭浏览器")

def main():
    """主函数"""
    # 默认测试URL
    test_url = "https://llm-stats.com/benchmarks/gpqa"
    
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    
    print("="*80)
    print(f"测试URL: {test_url}")
    print("="*80)
    
    results = []
    
    # 方法1: pandas.read_html
    success, result = method_1_pandas_read_html(test_url)
    results.append(("方法1: pandas.read_html()", success, result))
    
    # 方法2: requests + BeautifulSoup
    success, result = method_2_requests_beautifulsoup(test_url)
    results.append(("方法2: requests + BeautifulSoup", success, result))
    
    # 方法3: requests + lxml
    success, result = method_3_requests_lxml(test_url)
    results.append(("方法3: requests + lxml", success, result))
    
    # 方法4: 查找内嵌JSON
    success, result = method_4_find_embedded_json(test_url)
    results.append(("方法4: 查找内嵌JSON", success, result))
    
    # 方法5: 尝试API端点
    success, result = method_5_try_api_endpoints(test_url)
    results.append(("方法5: 尝试API端点", success, result))
    
    # 方法6: Selenium（如果需要JavaScript）
    success, result = method_6_selenium(test_url)
    results.append(("方法6: Selenium", success, result))
    
    # 汇总结果
    print("\n" + "="*80)
    print("测试结果汇总")
    print("="*80)
    
    successful_methods = []
    for method_name, success, result in results:
        status = "✓ 成功" if success else "✗ 失败"
        print(f"{status}: {method_name}")
        if success:
            successful_methods.append((method_name, result))
    
    if successful_methods:
        print(f"\n找到 {len(successful_methods)} 种成功的方法:")
        for method_name, result in successful_methods:
            print(f"  - {method_name}")
            # 如果是DataFrame，保存为CSV
            if PANDAS_AVAILABLE and isinstance(result, pd.DataFrame):
                output_dir = Path(__file__).parent.parent.parent / "results" / "scraped_data"
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # 从URL提取文件名
                url_name = urlparse(test_url).path.split('/')[-1] or "scraped_data"
                method_name_safe = method_name.split(':')[0].replace(' ', '_').lower()
                output_path = output_dir / f"{url_name}_{method_name_safe}.csv"
                
                result.to_csv(output_path, index=False, encoding='utf-8-sig')
                print(f"    数据已保存到: {output_path}")
    else:
        print("\n所有方法均未能成功爬取数据")
    
    return 0 if successful_methods else 1

if __name__ == "__main__":
    sys.exit(main())

