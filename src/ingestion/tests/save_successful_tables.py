"""
保存并展示能够成功爬取的benchmark表格数据

使用方法:
    python github/src/ingestion/save_successful_tables.py
"""

import json
import sys
import os
from pathlib import Path
import pandas as pd
from urllib.error import URLError, HTTPError

# 设置Windows控制台UTF-8编码支持
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

def save_benchmark_table(benchmark_name, url, output_dir):
    """
    爬取并保存单个benchmark的表格数据
    
    参数:
        benchmark_name: benchmark名称
        url: 排行榜URL
        output_dir: 输出目录路径
    
    返回:
        tuple: (success: bool, df: pd.DataFrame or None, error_message: str or None)
    """
    try:
        print(f"\n正在爬取: {benchmark_name}")
        print(f"  URL: {url}")
        
        # 设置User-Agent headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        }
        
        # 使用pandas.read_html读取URL
        tables = pd.read_html(url, storage_options=headers)
        
        if len(tables) == 0:
            return False, None, "页面中没有找到HTML表格"
        
        # 选择第一个表格（通常是排行榜表格）
        df = tables[0]
        
        # 生成sanitized文件名
        sanitized_name = benchmark_name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").replace("/", "_").replace("'", "").replace(".", "")
        
        # 保存为CSV文件
        output_path = output_dir / f"{sanitized_name}.csv"
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"  [成功] 找到 {len(tables)} 个表格，已保存第一个表格到: {output_path}")
        print(f"  表格形状: {df.shape} (行数: {df.shape[0]}, 列数: {df.shape[1]})")
        
        return True, df, None
        
    except Exception as e:
        error_msg = f"错误: {str(e)}"
        print(f"  [失败] {error_msg}")
        return False, None, error_msg

def main():
    """主函数：读取验证结果，爬取并保存成功的benchmark表格"""
    
    # 路径设置
    script_path = Path(__file__).resolve()
    github_dir = script_path.parent.parent.parent
    results_path = github_dir / "results" / "read_html_verification_results.json"
    output_dir = github_dir / "results" / "successful_tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 读取验证结果
    with open(results_path, 'r', encoding='utf-8') as f:
        results_data = json.load(f)
    
    # 筛选出成功的benchmark
    successful_benchmarks = [
        r for r in results_data['verification_results']
        if r['can_read_html'] == True
    ]
    
    print("=" * 80)
    print(f"找到 {len(successful_benchmarks)} 个成功爬取的benchmark")
    print("=" * 80)
    
    # 保存每个成功的benchmark表格
    saved_tables = []
    for benchmark in successful_benchmarks:
        benchmark_name = benchmark['benchmark_name']
        url = benchmark['url']
        
        success, df, error_msg = save_benchmark_table(benchmark_name, url, output_dir)
        
        if success and df is not None:
            saved_tables.append({
                'benchmark_name': benchmark_name,
                'url': url,
                'table_shape': df.shape,
                'columns': list(df.columns),
                'dataframe': df
            })
            
            # 展示表格前几行
            print(f"\n  表格列名: {list(df.columns)}")
            print(f"\n  表格前10行预览:")
            print("  " + "-" * 80)
            # 只显示前10行和前8列，避免输出过长
            preview_df = df.iloc[:10, :min(8, len(df.columns))]
            print(preview_df.to_string().replace("\n", "\n  "))
            print("  " + "-" * 80)
    
    print("\n" + "=" * 80)
    print("保存完成汇总")
    print("=" * 80)
    print(f"成功保存 {len(saved_tables)} 个benchmark的表格数据")
    print(f"保存位置: {output_dir}")
    print("\n保存的文件列表:")
    for item in saved_tables:
        sanitized_name = item['benchmark_name'].lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").replace("/", "_").replace("'", "").replace(".", "")
        print(f"  - {sanitized_name}.csv ({item['table_shape'][0]} 行 x {item['table_shape'][1]} 列)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

