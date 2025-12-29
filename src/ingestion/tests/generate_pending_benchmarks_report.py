"""
生成待定benchmark测试结果的详细报告

汇总所有测试结果，列出每个benchmark的可用爬取方法和结果。
"""

import json
import sys
from pathlib import Path
import pandas as pd

# 设置Windows控制台UTF-8编码支持
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

def main():
    """生成详细报告"""
    script_path = Path(__file__).resolve()
    github_dir = script_path.parent.parent.parent
    test_results_path = github_dir / "results" / "pending_benchmarks_test_results.json"
    extraction_report_path = github_dir / "results" / "pending_benchmarks_extraction_report.json"
    data_dir = github_dir / "results" / "pending_benchmarks_data"
    
    # 读取测试结果
    with open(test_results_path, 'r', encoding='utf-8') as f:
        test_results = json.load(f)
    
    # 读取提取报告（如果有）
    extraction_report = None
    if extraction_report_path.exists():
        with open(extraction_report_path, 'r', encoding='utf-8') as f:
            extraction_report = json.load(f)
    
    detailed_results = test_results.get('detailed_results', [])
    
    print("="*100)
    print("待定Benchmark爬取方法验证报告")
    print("="*100)
    print()
    print(f"总计待测试benchmark数量: {test_results['test_summary']['total_pending']}")
    print(f"找到可用方法的benchmark数量: {test_results['test_summary']['with_successful_methods']}")
    print(f"需要手动下载的benchmark数量: {test_results['test_summary']['need_manual_download']}")
    print()
    
    # 按成功方法分类
    selenium_benchmarks = []
    json_benchmarks = []
    no_method_benchmarks = []
    
    for result in detailed_results:
        benchmark_name = result['benchmark_name']
        url = result['url']
        successful_methods = result.get('successful_methods', [])
        
        if not successful_methods:
            no_method_benchmarks.append((benchmark_name, url))
        elif any('Selenium' in m for m in successful_methods):
            selenium_benchmarks.append((benchmark_name, url, successful_methods))
        elif any('内嵌JSON' in m for m in successful_methods):
            json_benchmarks.append((benchmark_name, url, successful_methods))
    
    # 1. 成功使用Selenium爬取的benchmark
    print("="*100)
    print("1. 成功使用Selenium方法爬取的Benchmark")
    print("="*100)
    if selenium_benchmarks:
        for i, (name, url, methods) in enumerate(selenium_benchmarks, 1):
            print(f"\n{i}. {name}")
            print(f"   URL: {url}")
            print(f"   可用方法: {', '.join(methods)}")
            
            # 检查是否有保存的数据文件
            sanitized_name = name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").replace("/", "_").replace("'", "").replace(".", "")
            csv_file = data_dir / f"{sanitized_name}_selenium.csv"
            if csv_file.exists():
                try:
                    df = pd.read_csv(csv_file, encoding='utf-8')
                    print(f"   ✓ 已保存数据文件: {csv_file.name}")
                    print(f"     数据形状: {df.shape[0]} 行 x {df.shape[1]} 列")
                    print(f"     列名: {', '.join([str(col) for col in df.columns[:5]])}{'...' if len(df.columns) > 5 else ''}")
                    print(f"     前3行数据预览:")
                    for idx, row in df.head(3).iterrows():
                        print(f"       {idx}: {dict(row)[list(df.columns)[0]]}")  # 显示第一列的值
                except Exception as e:
                    print(f"   ⚠ 数据文件存在但无法读取: {e}")
    else:
        print("\n无")
    
    # 2. 找到内嵌JSON的benchmark（需要定制解析）
    print("\n" + "="*100)
    print("2. 找到内嵌JSON数据的Benchmark（需要定制JSON解析逻辑）")
    print("="*100)
    if json_benchmarks:
        for i, (name, url, methods) in enumerate(json_benchmarks, 1):
            print(f"\n{i}. {name}")
            print(f"   URL: {url}")
            print(f"   可用方法: {', '.join(methods)}")
            print(f"   ⚠ 需要: 查看页面源代码，找到JSON数据结构，编写专用解析脚本")
    else:
        print("\n无")
    
    # 3. 无可用方法的benchmark（需要手动下载）
    print("\n" + "="*100)
    print("3. 无可用爬取方法的Benchmark（需要手动下载CSV）")
    print("="*100)
    if no_method_benchmarks:
        for i, (name, url) in enumerate(no_method_benchmarks, 1):
            print(f"\n{i}. {name}")
            print(f"   URL: {url}")
            print(f"   处理方式: 手动下载CSV文件，保存到 github/data/raw/benchmarks/manual/")
    else:
        print("\n无")
    
    # 4. 详细方法测试结果
    print("\n" + "="*100)
    print("4. 详细测试结果（所有测试方法）")
    print("="*100)
    
    method_names = {
        "方法1: pandas.read_html()": "pandas.read_html()",
        "方法2: requests + BeautifulSoup": "requests + BeautifulSoup",
        "方法3: requests + lxml": "requests + lxml",
        "方法4: 查找内嵌JSON": "查找内嵌JSON",
        "方法5: 尝试API端点": "尝试API端点",
        "方法6: Selenium": "Selenium"
    }
    
    for result in detailed_results:
        benchmark_name = result['benchmark_name']
        url = result['url']
        methods = result.get('methods', [])
        
        print(f"\n{'='*100}")
        print(f"Benchmark: {benchmark_name}")
        print(f"URL: {url}")
        print(f"{'='*100}")
        
        for method_info in methods:
            method = method_info.get('method', '')
            success = method_info.get('success', False)
            error = method_info.get('error', '')
            data_shape = method_info.get('data_shape', None)
            
            status = "✓ 成功" if success else "✗ 失败"
            print(f"  {status} - {method}")
            
            if success and data_shape:
                print(f"      数据形状: {data_shape[0]} 行 x {data_shape[1]} 列")
                if 'columns' in method_info:
                    cols = method_info['columns'][:5]
                    print(f"      列名: {', '.join([str(c) for c in cols])}{'...' if len(method_info['columns']) > 5 else ''}")
            elif not success and error:
                print(f"      错误: {error}")
    
    # 5. 总结和建议
    print("\n" + "="*100)
    print("5. 总结和建议")
    print("="*100)
    print(f"""
爬取策略总结:
1. 使用Selenium方法 (已成功提取数据): {len(selenium_benchmarks)} 个benchmark
   - 这些benchmark可以使用Selenium自动爬取，数据已保存到CSV文件
   
2. 找到内嵌JSON (需要定制解析): {len(json_benchmarks)} 个benchmark
   - 这些benchmark的页面中包含JSON数据，但需要针对每个网站编写定制解析脚本
   - 建议: 使用浏览器开发者工具查看Network请求，找到API端点或JSON数据结构
   
3. 需要手动下载: {len(no_method_benchmarks)} 个benchmark
   - 这些benchmark无法用自动化方法爬取，需要手动下载CSV文件
   - 保存位置: github/data/raw/benchmarks/manual/{{benchmark_id}}.csv

建议的下一步操作:
- 对于Selenium方法成功的benchmark: 可以在GEMINI.md中指导agent使用Selenium方法
- 对于内嵌JSON的benchmark: 需要逐个分析页面结构，编写专用解析脚本
- 对于无法爬取的benchmark: 需要手动下载并保存到manual目录
    """)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

