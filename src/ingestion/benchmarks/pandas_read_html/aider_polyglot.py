"""
Aider Polyglot Leaderboard Scraper

爬取方法: pandas.read_html
URL: https://aider.chat/docs/leaderboards/

说明:
- 使用pandas.read_html()直接读取HTML表格
- 最简单高效的方法
"""

import sys
import pandas as pd
from pathlib import Path

# 设置UTF-8编码
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"

def scrape_aider_polyglot():
    """爬取Aider Polyglot排行榜数据"""
    url = "https://aider.chat/docs/leaderboards/"
    
    print(f"正在爬取: Aider Polyglot")
    print(f"URL: {url}")
    print("方法: pandas.read_html")
    
    headers = {
        "User-Agent": USER_AGENT,
    }
    
    try:
        tables = pd.read_html(url, storage_options=headers)
        
        if len(tables) == 0:
            print("[失败] 未找到表格")
            return None
        
        df = tables[0]
        print(f"[成功] 找到 {len(tables)} 个表格，第一个表格形状: {df.shape}")
        return df
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    df = scrape_aider_polyglot()
    
    if df is not None and len(df) > 0:
        script_dir = Path(__file__).parent
        data_dir = script_dir.parent.parent / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = data_dir / "aider_polyglot.csv"
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\n[成功] 数据已保存到: {output_file}")
        print(f"数据形状: {df.shape[0]} 行 x {df.shape[1]} 列")
        print(f"列名: {list(df.columns)}")
        if len(df) > 0:
            print(f"\n前5行预览:")
            print(df.head().to_string())
    else:
        print("\n[失败] 未能提取数据")


if __name__ == "__main__":
    main()

