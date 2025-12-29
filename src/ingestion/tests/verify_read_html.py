"""
验证工具：测试metadata.json中26个benchmark排行榜网址能否使用pandas.read_html成功爬取

目的：
    验证每个benchmark的leaderboard_url是否能够通过pandas.read_html()函数直接读取HTML表格
    输出验证结果和成功爬取的数据样本

使用方法：
    uv run python github/src/ingestion/verify_read_html.py

输出：
    1. 控制台输出：每个benchmark的验证状态（成功/失败）
    2. 成功爬取的数据样本会打印到控制台
"""

import json
import sys
import os
from pathlib import Path
import pandas as pd
from urllib.error import URLError, HTTPError
import traceback

# 设置Windows控制台UTF-8编码支持
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

def sanitize_benchmark_id(benchmark_name):
    """将benchmark名称转换为sanitized ID（小写，特殊字符替换为下划线）"""
    return benchmark_name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").replace("/", "_").replace("'", "")

def verify_benchmark_url(url, benchmark_name):
    """
    验证单个benchmark URL能否用pandas.read_html读取
    
    参数:
        url: 要验证的URL
        benchmark_name: benchmark名称（用于错误报告）
    
    返回:
        tuple: (success: bool, data_sample: pd.DataFrame or None, error_message: str or None)
    """
    try:
        # pandas.read_html可以直接接受URL作为参数
        # 使用storage_options传递HTTP headers，模拟浏览器请求以避免被服务器拒绝
        print(f"正在验证: {benchmark_name}")
        print(f"  URL: {url}")
        
        # 设置User-Agent headers，模拟浏览器请求
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        }
        
        # 使用pandas.read_html读取URL，通过storage_options传递headers
        # 注意：read_html返回一个DataFrame列表（因为一个页面可能有多个表格）
        tables = pd.read_html(url, storage_options=headers)
        
        if len(tables) == 0:
            return False, None, "页面中没有找到HTML表格"
        
        # 返回第一个表格作为样本（通常排行榜是第一个表格）
        sample_table = tables[0]
        
        print(f"  [成功] 找到 {len(tables)} 个表格，第一个表格形状: {sample_table.shape}")
        return True, sample_table, None
        
    except URLError as e:
        error_msg = f"URL错误: {str(e)}"
        print(f"  [失败] {error_msg}")
        return False, None, error_msg
    except HTTPError as e:
        error_msg = f"HTTP错误: {e.code} - {str(e)}"
        print(f"  [失败] {error_msg}")
        return False, None, error_msg
    except ValueError as e:
        # pandas.read_html在没有找到表格时会抛出ValueError
        error_msg = f"解析错误: {str(e)}"
        print(f"  [失败] {error_msg}")
        return False, None, error_msg
    except Exception as e:
        error_msg = f"未知错误: {str(e)}"
        print(f"  [失败] {error_msg}")
        print(f"  错误详情: {traceback.format_exc()}")
        return False, None, error_msg

def main():
    """主函数：读取metadata.json，验证所有benchmark URLs"""
    
    # 获取项目根目录（github目录的父目录）
    script_path = Path(__file__).resolve()
    github_dir = script_path.parent.parent.parent  # github/src/ingestion/verify_read_html.py -> github/
    project_root = github_dir.parent
    
    # 读取metadata.json
    metadata_path = github_dir / "config" / "metadata.json"
    if not metadata_path.exists():
        print(f"错误：找不到metadata.json文件: {metadata_path}")
        sys.exit(1)
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # 过滤出benchmark条目（排除LMArena条目和meta_info条目）
    # LMArena条目的特征是包含"elo_column"字段
    benchmarks = []
    for entry in metadata:
        if isinstance(entry, dict):
            # 跳过meta_info条目
            if "meta_info" in entry:
                continue
            # 只处理不包含elo_column的条目（即benchmark条目）
            if "elo_column" not in entry and "leaderboard_url" in entry:
                benchmarks.append(entry)
    
    print(f"找到 {len(benchmarks)} 个benchmark条目需要验证\n")
    print("=" * 80)
    print()
    
    # 验证结果存储
    results = []
    
    # 逐个验证
    for i, benchmark in enumerate(benchmarks, 1):
        benchmark_name = benchmark.get("benchmark_name", "Unknown")
        url = benchmark.get("leaderboard_url", "")
        
        if not url:
            print(f"{i}. {benchmark_name}: 跳过（无URL）")
            results.append({
                "benchmark_name": benchmark_name,
                "url": url,
                "can_read_html": False,
                "reason": "无URL"
            })
            continue
        
        print(f"{i}. {benchmark_name}")
        success, sample_data, error_msg = verify_benchmark_url(url, benchmark_name)
        
        result = {
            "benchmark_name": benchmark_name,
            "url": url,
            "can_read_html": success,
            "reason": None if success else error_msg
        }
        results.append(result)
        
        # 如果成功，显示数据样本
        if success and sample_data is not None:
            print(f"\n  数据样本（前5行，前5列）:")
            print("  " + "-" * 76)
            # 显示前5行和前5列
            display_df = sample_data.iloc[:5, :min(5, len(sample_data.columns))]
            print(display_df.to_string().replace("\n", "\n  "))
            print("  " + "-" * 76)
        
        print()
        print("=" * 80)
        print()
    
    # 统计结果
    successful = sum(1 for r in results if r["can_read_html"])
    failed = len(results) - successful
    
    print("\n" + "=" * 80)
    print("验证结果汇总")
    print("=" * 80)
    print(f"总计: {len(results)} 个benchmark")
    print(f"成功: {successful} 个")
    print(f"失败: {failed} 个")
    print()
    
    # 列出失败的benchmark
    if failed > 0:
        print("失败的benchmark列表:")
        for r in results:
            if not r["can_read_html"]:
                print(f"  - {r['benchmark_name']}: {r['reason']}")
        print()
    
    # 保存验证结果到JSON文件
    output_path = github_dir / "results" / "read_html_verification_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "verification_results": results,
            "summary": {
                "total": len(results),
                "successful": successful,
                "failed": failed
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"验证结果已保存到: {output_path}")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

