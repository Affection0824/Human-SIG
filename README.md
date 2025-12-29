# Benchmark数据爬取和组织说明

本文档详细说明了benchmark数据的组织结构、文件格式和数据爬取流程。本文档是完整的参考指南，包含了所有必要的信息和代码模板，无需参考其他文档即可理解并执行所有爬取方法。

## 目录结构

```
data/raw/
├── lmarena_leaderboard/          # LMArena数据（已预先准备好）
│   └── filtered_elo_dump.json    # 包含所有LMArena类别的过滤和合并后的ELO分数
├── benchmarks_with_data/          # 已有数据的benchmark
│   ├── manual_direct/            # 没有爬取脚本，直接获取的数据
│   │   └── {benchmark_name}/     # 每个benchmark一个文件夹
│   │       ├── input.txt         # URL或数据说明文件
│   │       └── {name}_data.csv   # 数据文件（CSV或JSON）
│   ├── pandas_read_html/         # pandas.read_html方法爬取的数据
│   │   └── {benchmark_name}/
│   │       ├── input.txt         # URL文件，包含一行URL
│   │       ├── scraper.py        # 爬取脚本
│   │       └── {name}_data.csv   # 数据文件
│   └── selenium/                 # Selenium方法爬取的数据
│       └── {benchmark_name}/
│           ├── input.txt         # URL文件，包含一行URL
│           ├── scraper.py        # 爬取脚本
│           └── {name}_data.csv   # 数据文件
└── benchmarks_without_data/      # 还没有数据的benchmark
    ├── artificial_analysis/      # 需要从Artificial Analysis总表提取
    │   ├── input.txt             # 统一表格说明文件
    │   └── {benchmark_name}/
    │       ├── input.txt         # 统一表格HTML文件路径说明
    │       ├── scraper.py        # 提取脚本（可选，待实现）
    │       └── {name}_data.csv   # 提取后的数据文件
    ├── vals_ai/                  # 需要从VALS.ai抓取
    │   └── {benchmark_name}/
    │       ├── input.txt         # URL文件
    │       ├── {name}_input.json # 从网页源码复制的JSON数据（可能包含前后无关信息）
    │       ├── scraper.py        # 转换脚本（将JSON转换为CSV）
    │       └── {name}_data.csv   # 最终数据文件（CSV格式）
    ├── lmarena/                  # LMArena数据已预先准备好（保留目录，实际数据在lmarena_leaderboard/）
    │   └── {benchmark_name}/
    │       ├── input.txt         # URL文件
    │       ├── scraper.py        # 爬取脚本
    │       └── {name}_data.csv   # 数据文件
    └── manual_source_code/       # 需要从网页源码手动提取数据
        └── {benchmark_name}/
            ├── input.txt         # URL文件
            └── {name}_data.csv   # 手动提取的数据文件
```

## 文件命名规则

每个benchmark文件夹中的文件命名遵循以下规则：
- `input.txt` 或 `input.html`: 输入文件
  - **对于可爬取的benchmark（pandas_read_html, selenium）**: 包含一行URL
  - **对于需要手动获取数据的benchmark（manual_direct, artificial_analysis, vals_ai, manual_source_code）**: 包含URL或数据获取说明，或者直接包含用户提供的数据
  - **对于artificial_analysis的统一表格**: `artificial_analysis/input.html` 或 `artificial_analysis/input.txt`（说明文件）
  - **注意**: LMArena数据已预先准备好，不需要爬取，直接从 `lmarena_leaderboard/filtered_elo_dump.json` 加载
- `scraper.py`: 数据提取/转换脚本（Python文件，仅存在于有脚本的benchmark）
- `{name}_data.csv` 或 `{name}_data.json`: 最终的数据文件

**说明**：
- 由于每个benchmark都有自己的文件夹，输入文件和脚本文件不需要包含benchmark名称，直接使用 `input.txt/html` 和 `scraper.py`
- `{name}` 是benchmark名称的文件系统友好版本（小写，空格和下划线替换，特殊字符处理），仅用于数据文件

## 各类别的文件格式说明

### 1. 已有数据的benchmark

#### 1.1 manual_direct（没有爬取脚本，直接获取的数据）

**文件格式：**

1. **`input.txt`** (文本文件)
   - 包含：数据来源URL或数据获取说明
   - 格式：纯文本，一行URL或多行说明

2. **`{name}_data.csv`** 或 **`{name}_data.json`**
   - 格式：CSV文件（UTF-8编码）或JSON文件
   - 必需列（CSV）：`model_name`（字符串）, `score`（浮点数，0-100范围）

**示例：**
- `facts/input.txt`: `https://www.kaggle.com/benchmarks/google/facts`
- `facts/facts_data.csv`: 包含model_name和score列的CSV文件
- `writingbench/input.txt`: `https://huggingface.co/spaces/WritingBench/WritingBench`
- `writingbench/writingbench_data.csv`: 从网页上下载/获取的数据文件，包含model_name和score列（位于 `benchmarks_with_data/manual_direct/writingbench/`）

---

#### 1.2 pandas_read_html（pandas.read_html方法爬取的数据）

**文件格式：**

1. **`input.txt`** (文本文件)
   - 包含：leaderboard URL
   - 格式：一行URL

2. **`scraper.py`** (Python脚本)
   - 功能：使用 `pandas.read_html()` 从URL读取HTML表格并保存为CSV
   - 输入：读取 `input.txt` 文件中的URL
   - 输出：生成 `{name}_data.csv`
   - 必需库：`pandas`, `html5lib`, `lxml`（推荐）

3. **`{name}_data.csv`**
   - 格式：CSV文件（UTF-8编码）
   - 必需列：`model_name`（字符串）, `score`（浮点数，0-100范围）

**脚本模板：**
```python
import pandas as pd
from pathlib import Path
import sys

# 设置UTF-8编码（Windows系统需要）
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# 读取URL
script_dir = Path(__file__).parent
with open(script_dir / 'input.txt', 'r', encoding='utf-8') as f:
    url = f.read().strip()

# 设置User-Agent头
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
tables = pd.read_html(url, storage_options=headers)

if len(tables) == 0:
    print("错误: 未找到表格")
    sys.exit(1)

df = tables[0]  # 通常第一个表格包含排行榜数据

# 标准化列名并保存
# 注意：需要根据实际网站的列名进行调整
# 例如：可能列名是 'Model', 'Score', 'Accuracy' 等
# 需要进行映射：df.rename(columns={'Model': 'model_name', 'Score': 'score'}, inplace=True)
df = df[['model_name', 'score']]  # 根据实际列名调整
df.to_csv(script_dir / '{name}_data.csv', index=False, encoding='utf-8')
print(f"数据已保存到: {script_dir / '{name}_data.csv'}")
```

**运行方式：**
```bash
cd data/raw/benchmarks_with_data/pandas_read_html/{benchmark_name}
python scraper.py
```

**依赖安装：**
```bash
pip install pandas html5lib lxml
```

---

#### 1.3 selenium（Selenium方法爬取的数据）

**文件格式：**

1. **`input.txt`** (文本文件)
   - 包含：leaderboard URL
   - 格式：一行URL

2. **`scraper.py`** (Python脚本)
   - 功能：使用Selenium WebDriver渲染JavaScript，提取表格HTML，解析并保存为CSV
   - 输入：读取 `input.txt` 文件中的URL
   - 输出：生成 `{name}_data.csv`
   - 必需库：`selenium`, `pandas`, Chrome浏览器

3. **`{name}_data.csv`**
   - 格式：CSV文件（UTF-8编码）
   - 必需列：`model_name`（字符串）, `score`（浮点数，0-100范围）

**脚本模板：**
```python
import sys
from pathlib import Path
import pandas as pd
from io import StringIO
import time

# 设置UTF-8编码（Windows系统需要）
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("错误: selenium库未安装，请运行: pip install selenium")
    sys.exit(1)

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"

def scrape_benchmark():
    """爬取排行榜数据"""
    if not SELENIUM_AVAILABLE:
        return None
    
    # 读取URL
    script_dir = Path(__file__).parent
    with open(script_dir / 'input.txt', 'r', encoding='utf-8') as f:
        url = f.read().strip()
    
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'user-agent={USER_AGENT}')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # 等待JavaScript渲染
        time.sleep(5)  # 可根据实际页面加载速度调整
        
        # 查找表格元素
        tables = driver.find_elements(By.TAG_NAME, "table")
        
        if len(tables) == 0:
            print("错误: 未找到表格元素")
            return None
        
        # 提取第一个表格的HTML
        html = tables[0].get_attribute('outerHTML')
        dfs = pd.read_html(StringIO(html))
        
        if len(dfs) == 0:
            print("错误: 无法解析表格")
            return None
        
        df = dfs[0]
        
        # 标准化列名（需要根据实际网站的列名进行调整）
        # df.rename(columns={'Model': 'model_name', 'Score': 'score'}, inplace=True)
        df = df[['model_name', 'score']]  # 根据实际列名调整
        
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
    df = scrape_benchmark()
    
    if df is not None:
        script_dir = Path(__file__).parent
        output_file = script_dir / '{name}_data.csv'
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"数据已保存到: {output_file}")
        print(f"数据形状: {df.shape}")
    else:
        print("爬取失败")

if __name__ == "__main__":
    main()
```

**运行方式：**
```bash
cd data/raw/benchmarks_with_data/selenium/{benchmark_name}
python scraper.py
```

**依赖安装：**
```bash
pip install selenium pandas
```

**ChromeDriver配置：**
1. 安装Chrome浏览器
2. 安装ChromeDriver：
   - **方法1（推荐）**: 使用webdriver-manager自动管理
     ```bash
     pip install webdriver-manager
     ```
     然后在脚本中使用：
     ```python
     from selenium.webdriver.chrome.service import Service
     from webdriver_manager.chrome import ChromeDriverManager
     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
     ```
   - **方法2**: 手动下载ChromeDriver并添加到PATH
     - 下载地址: https://chromedriver.chromium.org/
     - 确保ChromeDriver版本与Chrome浏览器版本匹配

---

### 2. 还没有数据的benchmark

#### 2.1 artificial_analysis（需要从Artificial Analysis总表提取）

**文件格式：**

1. **`artificial_analysis/input.html`** (HTML文件)
   - 位置：`data/raw/benchmarks_without_data/artificial_analysis/input.html`
   - 内容：从 https://artificialanalysis.ai/leaderboards/models 手动复制的完整 `<table>` 元素HTML
   - 获取方法：
     1. 访问 https://artificialanalysis.ai/leaderboards/models
     2. 使用浏览器开发者工具（F12）打开检查器
     3. 在Elements标签页中找到 `<table>` 元素
     4. 右键点击 `<table>` 标签，选择 "Copy" -> "Copy element" 或 "Copy outerHTML"
     5. 将复制的HTML保存为 `input.html` 文件到 `artificial_analysis/` 目录下

2. **`{name}/input.txt`** (说明文件)
   - 位置：每个benchmark文件夹下的 `input.txt`
   - 内容：指向统一表格的说明

3. **`scraper.py`** (Python脚本，可选)
   - 功能：从统一表格HTML中提取指定benchmark的数据列
   - 输入：读取 `artificial_analysis/input.html`
   - 输出：生成 `{name}_data.csv`
   - 说明：所有artificial_analysis类别的benchmark共享同一个统一表格HTML文件

**脚本模板：**
```python
import pandas as pd
from pathlib import Path
import sys

# 设置UTF-8编码
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

def extract_benchmark_data():
    """从统一表格中提取指定benchmark的数据"""
    script_dir = Path(__file__).parent
    
    # 读取统一表格HTML文件
    html_file = script_dir.parent / "input.html"
    if not html_file.exists():
        print(f"错误: 找不到统一表格文件 {html_file}")
        sys.exit(1)
    
    # 使用pandas.read_html解析HTML表格
    tables = pd.read_html(html_file)
    if len(tables) == 0:
        print("错误: 无法解析HTML表格")
        sys.exit(1)
    
    df = tables[0]  # 通常第一个表格是目标表格
    
    # 根据benchmark名称找到对应的列
    # 注意：需要根据实际表格结构调整列名映射
    # 例如：benchmark列名可能是 "Terminal-Bench Hard", "AA-LCR" 等
    benchmark_name = "{benchmark_name}"  # 替换为实际的benchmark名称
    
    # 提取model_name列（通常是第一列）
    # 提取对应benchmark的score列
    # 进行数据清洗和标准化
    result_df = pd.DataFrame({
        'model_name': df.iloc[:, 0],  # 第一列通常是模型名称
        'score': df[benchmark_name]   # 对应的benchmark列
    })
    
    # 保存结果
    output_file = script_dir / "{name}_data.csv"
    result_df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"数据已保存到: {output_file}")

if __name__ == "__main__":
    extract_benchmark_data()
```

**运行方式：**
```bash
cd data/raw/benchmarks_without_data/artificial_analysis/{benchmark_name}
python scraper.py
```

4. **`{name}_data.csv`** (最终数据文件)
   - 格式：CSV文件（UTF-8编码）
   - 必需列：`model_name`（字符串）, `score`（浮点数，0-100范围）

**执行流程：**
1. 确保 `artificial_analysis/input.html` 文件存在（需要用户手动提供）
2. 对于每个benchmark，运行对应的 `scraper.py`（如果存在）
3. 脚本从统一表格中提取该benchmark对应的列，生成 `{name}_data.csv`

**包含的benchmark：**
- Terminal-Bench Hard
- τ²-Bench Telecom
- AA-LCR
- Humanity's Last Exam (HLE)
- MMLU-Pro
- GPQA Diamond
- LiveCodeBench
- SciCode
- IFBench
- AIME (2025)

---

#### 2.2 vals_ai（需要从VALS.ai抓取）

**文件格式：**

1. **`input.txt`** (文本文件)
   - 包含：VALS.ai平台benchmark URL
   - 格式：一行URL

2. **`{name}_input.json`** (JSON文件)
   - 说明：用户需要从网页源码中复制JSON数据。这个JSON文件可能包含前后无关的信息，需要脚本提取有效的JSON部分
   - 获取方法：
     1. 打开浏览器开发者工具（F12）
     2. 查看网页源码（View Page Source）或在Elements标签页中查找包含JSON数据的`<script>`标签
     3. 复制包含leaderboard数据的JSON片段（可能包含前后无关的文本或HTML）
     4. 将复制的数据保存为 `{name}_input.json` 文件到benchmark文件夹

3. **`scraper.py`** (Python脚本)
   - 功能：从 `{name}_input.json` 文件中提取有效的JSON数据并转换为CSV格式
   - 输入：读取 `{name}_input.json` 文件（需要处理可能的前后无关信息）
   - 输出：生成 `{name}_data.csv`（与其他benchmark统一的CSV格式）
   - 必需列：`model_name`（字符串）, `score`（浮点数，0-100范围）

**脚本模板：**
```python
import json
import pandas as pd
from pathlib import Path
import sys
import re

# 设置UTF-8编码
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

def extract_json_from_input(json_file_path):
    """从可能包含无关信息的input文件中提取有效的JSON数据"""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 尝试解析完整的文件内容
    try:
        data = json.loads(content)
        return data
    except json.JSONDecodeError:
        # 如果直接解析失败，尝试提取JSON对象
        # 使用正则表达式查找JSON对象（从{开始到}结束）
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return data
            except json.JSONDecodeError:
                pass
        
        # 如果仍然失败，尝试提取JSON数组
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return data
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"无法从 {json_file_path} 中提取有效的JSON数据")

def convert_json_to_csv():
    """将JSON数据转换为CSV"""
    script_dir = Path(__file__).parent
    
    # 读取JSON输入文件
    json_input_file = script_dir / "{name}_input.json"
    if not json_input_file.exists():
        print(f"错误: 找不到JSON输入文件 {json_input_file}")
        print("请按照README说明从网页源码复制JSON数据并保存为{name}_input.json")
        sys.exit(1)
    
    # 提取有效的JSON数据
    data = extract_json_from_input(json_input_file)
    
    # 根据实际JSON结构解析数据
    # 需要根据VALS.ai的实际JSON格式调整
    # 例如：data可能是列表，每个元素包含model_name和score
    records = []
    # 根据实际JSON结构调整解析逻辑
    if isinstance(data, list):
        for item in data:
            records.append({
                'model_name': item.get('model_name', ''),
                'score': item.get('score', 0)
            })
    elif isinstance(data, dict):
        # 如果data是字典，可能需要进一步处理
        # 根据实际结构调整
        pass
    
    df = pd.DataFrame(records)
    
    # 保存为CSV（与其他benchmark统一的格式）
    output_file = script_dir / "{name}_data.csv"
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"CSV数据已保存到: {output_file}")

if __name__ == "__main__":
    convert_json_to_csv()
```

4. **`{name}_data.csv`** (最终数据文件)
   - 格式：CSV文件（UTF-8编码）
   - 必需列：`model_name`（字符串）, `score`（浮点数，0-100范围）
   - 说明：最终输出格式与其他benchmark统一，均为CSV格式

**执行流程：**
1. 确保 `input.txt` 文件存在，包含正确的URL
2. 从网页源码复制JSON数据，保存为 `{name}_input.json`
3. 运行 `scraper.py` 脚本，将JSON数据转换为CSV格式
4. 脚本生成 `{name}_data.csv` 文件

**注意：** MATH-500已有CSV数据，已移至 `benchmarks_with_data/manual_direct/math_500/`。如果后续需要JSON格式的原始数据，可以从VALS.ai平台网页源码复制JSON数据。

**包含的benchmark（待获取数据）：**
- MGSM
- IOI (International Olympiad in Informatics)

---


#### 2.3 lmarena（LMArena数据已预先准备好）

**说明：** LMArena数据已预先准备好，位于 `data/raw/lmarena_leaderboard/filtered_elo_dump.json`。这个JSON文件包含了所有LMArena类别的过滤和合并后的ELO分数（Overall, Coding, Math, Hard Prompts, Creative Writing, Instruction Following, Expert）。**不需要agent进行爬取，直接加载该文件即可。**

**文件位置：**
- `data/raw/lmarena_leaderboard/filtered_elo_dump.json`

**数据格式：**
- JSON格式，包含以下字段：
  - `study_universe`: 包含所有`elo_overall >= 1330`的模型数据
  - `common_subset`: 包含`elo_overall`在1400-1430之间的模型数据（用于难度计算）
  - `metadata`: 元数据信息

**说明：** `benchmarks_without_data/lmarena/` 目录保留用于任何额外的LMArena类别（如果将来需要），但目前主要的LMArena数据都已在 `lmarena_leaderboard/filtered_elo_dump.json` 中预先准备好。

---

#### 2.4 manual_source_code（需要从网页源码手动提取数据）

**文件格式：**

1. **`input.txt`** (文本文件)
   - 包含：benchmark URL
   - 格式：一行URL
   - 说明：用于标识数据来源的URL

2. **`{name}_data.csv`** (最终数据文件)
   - 格式：CSV文件（UTF-8编码）
   - 必需列：`model_name`（字符串）, `score`（浮点数，0-100范围）
   - 说明：用户需要手动从网页源码中提取数据（例如，通过检查HTML/JavaScript源码或使用浏览器开发者工具）并保存为CSV文件

**获取方法：**
1. 打开benchmark的网页
2. 使用浏览器开发者工具（F12）查看网页源码
3. 从源码中提取leaderboard数据（可能需要检查HTML结构、JavaScript代码或网络请求）
4. 将提取的数据整理为CSV格式，包含`model_name`和`score`列
5. 保存为`{name}_data.csv`文件到benchmark文件夹

**包含的benchmark：**
- FrontierMath Tier 1-3
- FrontierMath Tier 4

---

## 数据提取执行指南

### 对于已有数据的benchmark

1. **确认数据文件存在：** 检查 `{name}_data.csv` 或 `{name}_data.json` 文件是否存在
2. **验证数据格式：** 确认数据文件包含必需的列（`model_name`, `score`）
3. **如需重新爬取：** 运行对应的 `scraper.py` 脚本（如果存在）

### 对于还没有数据的benchmark

1. **检查input文件：** 确认 `input.txt` 文件存在且内容正确
2. **提供必要的数据文件**:
   - **artificial_analysis**: 需要提供 `artificial_analysis/input.html` 文件（手动从浏览器复制`<table>`元素HTML）
   - **vals_ai**: 需要提供 `{name}_input.json` 文件（从网页源码复制JSON数据，可能包含前后无关信息）
   - **manual_source_code**: 需要用户手动从网页源码中提取数据并保存为CSV文件
3. **执行数据提取**（如果脚本存在）:
   - 运行对应的 `scraper.py` 脚本
   - 脚本会读取用户提供的数据文件并生成最终的数据文件
4. **验证输出：** 确认生成的数据文件格式正确，包含必需的列

### 通用注意事项

- 所有CSV文件应使用UTF-8编码
- `score` 列应为浮点数类型，范围在0-100之间（表示百分比）
- `model_name` 列应为字符串类型，包含模型的完整名称或标识符
- 数据文件应保存为 `{name}_data.csv` 或 `{name}_data.json`
- 脚本文件（`scraper.py`）应能够独立运行，读取同目录下的 `input.txt` 文件作为输入
- `input.txt`文件的含义：
  - **对于可爬取的benchmark（pandas_read_html, selenium, lmarena）**: 包含一行URL
  - **对于需要手动获取数据的benchmark**: 包含URL或数据获取说明，实际数据需要用户提供对应的数据文件

---

## 环境配置和依赖安装

### Python版本要求
- Python 3.7 或更高版本

### 依赖库安装

**基础依赖（所有方法都需要）：**
```bash
pip install pandas
```

**pandas.read_html方法额外依赖：**
```bash
pip install html5lib lxml
```

**Selenium方法额外依赖：**
```bash
pip install selenium
# 推荐：自动管理ChromeDriver
pip install webdriver-manager
```

### ChromeDriver配置（仅Selenium方法需要）

**方法1：使用webdriver-manager（推荐）**
```python
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
```

**方法2：手动安装**
1. 查看Chrome浏览器版本：`chrome://version/`
2. 下载匹配的ChromeDriver：https://chromedriver.chromium.org/
3. 将ChromeDriver添加到系统PATH，或放在Python脚本同目录

## 脚本运行指南

### 基本运行步骤

1. **进入benchmark文件夹**
   ```bash
   cd data/raw/benchmarks_with_data/{method}/{benchmark_name}
   # 例如：cd data/raw/benchmarks_with_data/pandas_read_html/aider_polyglot
   ```

2. **确认必要文件存在**
   - `input.txt` - 包含URL或数据说明
   - `scraper.py` - 爬取脚本（如果适用）

3. **运行脚本**
   ```bash
   python scraper.py
   ```

4. **检查输出**
   - 脚本会在同目录下生成 `{name}_data.csv` 文件
   - 查看控制台输出确认是否成功

### 常见问题和解决方案

**问题1：`ModuleNotFoundError: No module named 'pandas'`**
- 解决：安装依赖库 `pip install pandas html5lib lxml`

**问题2：`selenium.common.exceptions.WebDriverException: Message: 'chromedriver' executable needs to be in PATH`**
- 解决：使用webdriver-manager自动管理，或在脚本中指定ChromeDriver路径

**问题3：`UnicodeEncodeError: 'gbk' codec can't encode character`**
- 解决：脚本已包含UTF-8编码设置，如仍有问题，检查系统locale设置

**问题4：`ValueError: No tables found`**
- 解决：网站结构可能已变化，需要检查URL是否有效，或改用Selenium方法

**问题5：表格解析后列名不正确**
- 解决：根据实际网站调整脚本中的列名映射，使用 `df.rename(columns={...})`

**问题6：Selenium脚本超时或找不到元素**
- 解决：增加等待时间 `time.sleep(10)`，或使用 `WebDriverWait` 等待元素出现

## 数据格式说明

### CSV文件标准格式

所有CSV文件应遵循以下标准：

1. **编码**：UTF-8
2. **必需列**：
   - `model_name` (字符串) - 模型名称
   - `score` (浮点数) - 分数，范围通常在0-100之间（表示百分比）
3. **可选列**（某些benchmark可能有额外信息）：
   - `elo_score` (数字) - Elo评分（LMArena使用）
   - `rank` (整数) - 排名
   - `dataset` (字符串) - 数据集名称

### 数据标准化示例

```python
# 示例：将不同格式的列名统一为标准格式
df.rename(columns={
    'Model': 'model_name',
    'Model Name': 'model_name',
    'Score': 'score',
    'Accuracy': 'score',
    'Accuracy (%)': 'score'
}, inplace=True)

# 确保score为数值类型
df['score'] = pd.to_numeric(df['score'], errors='coerce')

# 移除缺失值
df = df.dropna(subset=['model_name', 'score'])
```

## 更新日期

最后更新: 2025-12-28
