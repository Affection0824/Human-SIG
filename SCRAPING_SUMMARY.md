# Benchmark数据爬取方式总结

本文档总结所有可自动化爬取的benchmark的爬取方式和所需依赖库。

---

## 一、爬取方法分类

目前可自动化爬取的benchmark共 **14个**，分为3种爬取方法：

### 1. pandas.read_html 方法 (2个)

**适用场景**: 网站包含可直接解析的HTML表格，无需JavaScript渲染。

**Benchmark列表**:
- Aider Polyglot
- Terminal-Bench v2.0

**爬取原理**: 
- 使用 `pandas.read_html()` 直接读取URL，自动解析HTML中的 `<table>` 元素
- 最简单高效的方法，无需浏览器驱动

**所需依赖库**:
```bash
pip install pandas
pip install html5lib  # pandas.read_html的依赖
pip install lxml      # 可选，但推荐安装以提升性能
```

**代码示例**:
```python
import pandas as pd

url = "https://aider.chat/docs/leaderboards/"
headers = {"User-Agent": "Mozilla/5.0 ..."}
tables = pd.read_html(url, storage_options=headers)
df = tables[0]  # 获取第一个表格
df.to_csv("output.csv", index=False, encoding='utf-8')
```

---

### 2. Selenium 方法 (5个)

**适用场景**: 网站使用JavaScript动态渲染表格，需要等待页面加载完成。

**Benchmark列表**:
- SuperGPQA
- ARC-AGI-2
- SWE-Bench (Bash Only)
- LiveCodeBench
- Creative Writing v3

**爬取原理**:
- 使用Selenium WebDriver启动无头Chrome浏览器
- 等待页面JavaScript渲染完成
- 提取页面中的 `<table>` 元素
- 使用 `pandas.read_html()` 解析表格HTML

**所需依赖库**:
```bash
pip install selenium
pip install pandas
```

**还需要安装ChromeDriver**:
- 确保系统已安装Google Chrome浏览器
- Selenium 4.x版本会自动下载匹配的ChromeDriver
- 或者手动下载: https://chromedriver.chromium.org/

**代码示例**:
```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
from io import StringIO
import time

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=chrome_options)
driver.get(url)

time.sleep(5)  # 等待页面加载

tables = driver.find_elements(By.TAG_NAME, "table")
html = tables[0].get_attribute('outerHTML')

dfs = pd.read_html(StringIO(html))
df = dfs[0]
df.to_csv("output.csv", index=False, encoding='utf-8')

driver.quit()
```

---

### 3. Selenium (llm-stats.com) 方法 (7个)

**适用场景**: llm-stats.com平台的所有benchmark，同样需要JavaScript渲染。

**Benchmark列表**:
- GPQA
- AIME (2025)
- HMMT (Feb 2025)
- HumanEval
- SWE-bench Verified
- IFEval (Instruction-Following Eval)
- Arena-Hard (Auto v2.0)

**爬取原理**: 
- 与Selenium方法完全相同
- 所有llm-stats.com的benchmark使用统一的爬取逻辑

**所需依赖库**: 与Selenium方法相同
```bash
pip install selenium
pip install pandas
```

**代码示例**: 与Selenium方法相同

---

## 二、完整依赖库列表

### 必需库

```bash
# 基础数据处理
pip install pandas

# HTML解析支持
pip install html5lib
pip install lxml  # 推荐安装，提升性能

# 浏览器自动化（Selenium方法需要）
pip install selenium
```

### 依赖安装命令（一键安装）

```bash
pip install pandas html5lib lxml selenium
```

---

## 三、环境要求

### 1. Python版本
- Python 3.7+

### 2. 浏览器驱动（仅Selenium方法需要）

#### Chrome/ChromeDriver
- 安装Google Chrome浏览器
- Selenium 4.x会自动管理ChromeDriver 
- 如果自动下载失败，可以手动下载ChromeDriver: 
  ```bash 
  # 使用webdriver-manager自动管理（推荐） 
  pip install webdriver-manager 
  ```

#### 使用webdriver-manager（可选，但推荐）

```python
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
```

---

## 四、脚本运行方式

### 单个脚本运行

```bash
# pandas.read_html方法
python github/scrapers/benchmarks/scripts/pandas_read_html/aider_polyglot.py
python github/scrapers/benchmarks/scripts/pandas_read_html/terminal_bench.py

# Selenium方法
python github/scrapers/benchmarks/scripts/selenium/supergpqa.py
python github/scrapers/benchmarks/scripts/selenium/arc_agi_2.py
python github/scrapers/benchmarks/scripts/selenium/swe_bench_bash_only.py
python github/scrapers/benchmarks/scripts/selenium/livecodebench.py
python github/scrapers/benchmarks/scripts/selenium/creative_writing_v3.py

# Selenium (llm-stats)方法
python github/scrapers/benchmarks/scripts/selenium/llm_stats/gpqa.py
python github/scrapers/benchmarks/scripts/selenium/llm_stats/aime_2025.py
python github/scrapers/benchmarks/scripts/selenium/llm_stats/hmmt_2025.py
python github/scrapers/benchmarks/scripts/selenium/llm_stats/humaneval.py
python github/scrapers/benchmarks/scripts/selenium/llm_stats/swe_bench_verified.py
python github/scrapers/benchmarks/scripts/selenium/llm_stats/ifeval.py
python github/scrapers/benchmarks/scripts/selenium/llm_stats/arena_hard_v2.py
```

### 批量运行

可以创建一个简单的批量运行脚本：

```python
import subprocess
import sys
from pathlib import Path

scripts = [
    "scripts/pandas_read_html/aider_polyglot.py",
    "scripts/pandas_read_html/terminal_bench.py",
    "scripts/selenium/supergpqa.py",
    # ... 其他脚本
]

for script in scripts:
    script_path = Path(__file__).parent / script
    subprocess.run([sys.executable, str(script_path)])
```

---

## 五、数据输出

所有脚本运行后，会将数据保存到 `github/scrapers/benchmarks/data/` 目录：

- 文件格式: CSV
- 编码: UTF-8
- 文件名格式: `{benchmark_id}.csv`

例如:
- `aider_polyglot.csv`
- `supergpqa.csv`
- `gpqa.csv`

---

## 六、常见问题

### 1. pandas.read_html 报错 "No tables found"

**原因**: 页面可能需要JavaScript渲染，或表格格式不被识别

**解决**: 考虑使用Selenium方法

### 2. Selenium报错 "chromedriver executable needs to be in PATH"

**原因**: ChromeDriver未正确安装或配置

**解决**: 
- 使用webdriver-manager自动管理
- 或手动下载ChromeDriver并添加到PATH

### 3. UnicodeEncodeError: 'gbk' codec can't encode

**原因**: Windows控制台编码问题

**解决**: 脚本中已添加编码处理：
```python
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
```

### 4. 页面加载超时

**原因**: 网络慢或页面渲染时间长

**解决**: 增加等待时间：
```python
time.sleep(10)  # 从5秒增加到10秒
```

---

## 七、方法选择指南

| 网站特征 | 推荐方法 |
|---------|---------|
| 静态HTML表格 | pandas.read_html |
| JavaScript渲染的表格 | Selenium |
| llm-stats.com平台 | Selenium (llm-stats) |
| 需要登录/认证 | 需要特殊处理（当前未涉及） |
| API端点可用 | JSON解析方法（待完善） |

---

## 八、统计信息

| 爬取方法 | Benchmark数量 | 状态 |
|---------|--------------|------|
| pandas.read_html | 2个 | ✅ 已完成 |
| Selenium | 5个 | ✅ 已完成 |
| Selenium (llm-stats) | 7个 | ✅ 已完成 |
| **总计** | **14个** | ✅ **全部完成** |

---

最后更新: 2025-12-28

