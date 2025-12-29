"""
Creative Writing v3 Leaderboard Scraper

爬取方法: Selenium
URL: https://eqbench.com/creative_writing.html

说明:
- 该网站使用JavaScript动态渲染表格数据
- 使用Selenium等待页面加载完成后提取table元素
- 使用pandas.read_html解析HTML表格
"""

import sys
from pathlib import Path
import pandas as pd
from io import StringIO
import time

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("错误: selenium库未安装，请运行: pip install selenium")

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"

def scrape_creative_writing_v3():
    """爬取Creative Writing v3排行榜数据"""
    if not SELENIUM_AVAILABLE:
        return None
    
    url = "https://eqbench.com/creative_writing.html"
    driver = None
    
    try:
        print(f"正在爬取: Creative Writing v3")
        print(f"URL: {url}")
        print("方法: Selenium (等待JavaScript渲染)")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'user-agent={USER_AGENT}')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        print("等待页面加载...")
        time.sleep(5)
        
        tables = driver.find_elements(By.TAG_NAME, "table")
        
        if len(tables) == 0:
            print("错误: 未找到表格元素")
            return None
        
        print(f"找到 {len(tables)} 个表格")
        
        table = tables[0]
        html = table.get_attribute('outerHTML')
        
        dfs = pd.read_html(StringIO(html))
        if len(dfs) == 0:
            print("错误: 无法解析表格")
            return None
        
        df = dfs[0]
        print(f"成功提取数据: {df.shape[0]} 行 x {df.shape[1]} 列")
        
        return df
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if driver:
            driver.quit()

def main():
    """主函数"""
    df = scrape_creative_writing_v3()
    
    if df is not None:
        script_dir = Path(__file__).parent
        data_dir = script_dir.parent.parent / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = data_dir / "creative_writing_v3.csv"
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\n数据已保存到: {output_file}")
        print(f"数据形状: {df.shape}")
        print(f"\n前5行预览:")
        try:
            print(df.head().to_string())
        except UnicodeEncodeError:
            print("数据预览（跳过包含特殊字符的行）")
    else:
        print("爬取失败")

if __name__ == "__main__":
    main()

