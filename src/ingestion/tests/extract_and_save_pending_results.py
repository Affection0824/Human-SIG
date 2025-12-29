"""
提取并保存待定benchmark的爬取数据

对于每个成功爬取的benchmark，使用相应的方法提取数据并保存为CSV。
"""

import json
import sys
import os
from pathlib import Path
import pandas as pd
from io import StringIO
import time
import re

# 设置Windows控制台UTF-8编码支持
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

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

def sanitize_benchmark_name(name):
    """将benchmark名称转换为文件安全的名称"""
    return name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").replace("/", "_").replace("'", "").replace(".", "")

def extract_with_selenium(url):
    """使用Selenium提取表格数据"""
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

def extract_with_json(url):
    """使用内嵌JSON提取数据（简化版，实际需要更复杂的解析）"""
    # 这个方法需要针对每个网站定制JSON解析逻辑
    # 这里返回None表示需要手动处理
    return False, None, "需要针对每个网站定制JSON解析逻辑"

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
    print("提取并保存待定benchmark的爬取数据")
    print("="*80)
    print()
    
    saved_files = []
    extraction_report = []
    
    for result in detailed_results:
        benchmark_name = result['benchmark_name']
        url = result['url']
        successful_methods = result.get('successful_methods', [])
        
        print(f"\n{'='*80}")
        print(f"处理: {benchmark_name}")
        print(f"URL: {url}")
        print(f"可用方法: {', '.join(successful_methods)}")
        print(f"{'='*80}")
        
        benchmark_extraction = {
            'benchmark_name': benchmark_name,
            'url': url,
            'methods_tested': successful_methods,
            'extracted_data': []
        }
        
        # 优先使用Selenium（方法6），因为可以提取实际数据
        for method_name in successful_methods:
            if "Selenium" in method_name:
                print(f"\n使用 方法6: Selenium 提取数据...")
                success, df, error = extract_with_selenium(url)
                if success and df is not None:
                    sanitized_name = sanitize_benchmark_name(benchmark_name)
                    output_file = output_dir / f"{sanitized_name}_selenium.csv"
                    df.to_csv(output_file, index=False, encoding='utf-8')
                    
                    print(f"✓ 成功保存到: {output_file}")
                    print(f"  数据形状: {df.shape} (行数: {df.shape[0]}, 列数: {df.shape[1]})")
                    print(f"  列名: {list(df.columns)}")
                    print(f"\n  前10行数据预览:")
                    print("  " + "-" * 80)
                    preview_str = df.head(10).to_string()
                    for line in preview_str.split('\n'):
                        print(f"  {line}")
                    print("  " + "-" * 80)
                    
                    # 将列名转换为字符串列表（处理MultiIndex的情况）
                    columns_str = [str(col) if not isinstance(col, tuple) else str(col) for col in df.columns]
                    saved_files.append({
                        'benchmark': benchmark_name,
                        'method': 'Selenium',
                        'file': str(output_file),
                        'shape': [df.shape[0], df.shape[1]],
                        'columns': columns_str
                    })
                    
                    # 将列名转换为字符串列表（处理MultiIndex的情况）
                    columns_str = [str(col) if not isinstance(col, tuple) else str(col) for col in df.columns]
                    benchmark_extraction['extracted_data'].append({
                        'method': 'Selenium',
                        'success': True,
                        'file': str(output_file),
                        'shape': [df.shape[0], df.shape[1]],
                        'columns': columns_str
                    })
                    break
                else:
                    print(f"✗ 提取失败: {error}")
                    benchmark_extraction['extracted_data'].append({
                        'method': 'Selenium',
                        'success': False,
                        'error': error
                    })
            
            elif "内嵌JSON" in method_name:
                print(f"\n方法4（内嵌JSON）需要针对每个网站定制JSON解析逻辑")
                print(f"  建议：查看页面源代码，找到JSON数据结构，然后编写专用解析脚本")
                benchmark_extraction['extracted_data'].append({
                    'method': '内嵌JSON',
                    'success': False,
                    'note': '需要针对每个网站定制JSON解析逻辑'
                })
        
        extraction_report.append(benchmark_extraction)
    
    # 保存提取报告
    report_path = github_dir / "results" / "pending_benchmarks_extraction_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_benchmarks': len(detailed_results),
                'successfully_extracted': len(saved_files),
                'need_custom_parsing': len([r for r in extraction_report if any('内嵌JSON' in m for m in r['methods_tested'])])
            },
            'extraction_results': extraction_report
        }, f, indent=2, ensure_ascii=False, default=str)
    
    # 最终汇总
    print("\n" + "="*80)
    print("提取完成汇总")
    print("="*80)
    print(f"成功提取并保存 {len(saved_files)} 个benchmark的数据")
    print(f"保存位置: {output_dir}")
    print(f"提取报告: {report_path}")
    
    if saved_files:
        print("\n成功保存的文件列表:")
        for info in saved_files:
            print(f"\n  {info['benchmark']}:")
            print(f"    方法: {info['method']}")
            print(f"    文件: {Path(info['file']).name}")
            print(f"    形状: {info['shape'][0]} 行 x {info['shape'][1]} 列")
            print(f"    列名: {', '.join(info['columns'][:5])}{'...' if len(info['columns']) > 5 else ''}")
    
    # 列出需要手动处理或定制解析的benchmark
    need_manual = [r for r in extraction_report if not any(d.get('success') for d in r['extracted_data'])]
    if need_manual:
        print(f"\n需要手动处理或定制解析的benchmark ({len(need_manual)} 个):")
        for r in need_manual:
            print(f"  - {r['benchmark_name']}: {', '.join(r['methods_tested'])}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

