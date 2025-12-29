# Benchmark数据爬取项目说明

本项目用于爬取和整理26个benchmark（不包括LMArena的categories）的排行榜数据。本文档详细说明了所有benchmark的爬取方式、执行方法和数据存储位置。

## 项目目录结构

```
github/
├── config/                    # 配置文件目录
│   ├── metadata.json          # Benchmark元数据配置（包含所有benchmark的URL、分类、爬取方式等）
│   └── mapping.json           # 模型名称映射表（用于实体解析）
├── data/                      # 数据目录
│   ├── raw/                   # 原始数据
│   │   ├── lmarena_leaderboard/  # LMArena排行榜数据（每个category一个CSV文件）
│   │   └── benchmarks/        # Benchmark数据
│   │       ├── {benchmark_id}.csv  # 自动化爬取的CSV文件（pandas.read_html和Selenium方法）
│   │       └── manual/        # 手动下载的数据
│   │           ├── {benchmark_id}.csv  # 手动下载的CSV文件
│   │           └── {benchmark_id}.json # 手动下载的JSON文件（VALS.ai平台）
│   └── processed/             # 处理后的数据
│       ├── normalized_scores/ # 标准化后的分数（0-100范围）
│       ├── entity_resolution/ # 实体解析相关文件
│       └── master_table/      # 最终合并的主表
├── src/                       # 源代码目录
│   ├── ingestion/             # 数据获取脚本
│   │   ├── fetch_lmarena.py   # LMArena数据获取脚本
│   │   └── benchmarks/        # Benchmark爬取脚本（按爬取方式分类）
│   │       ├── pandas_read_html/  # pandas.read_html方法脚本
│   │       ├── selenium/          # Selenium方法脚本
│   │       │   └── llm_stats/     # llm-stats.com专用脚本（使用Selenium方法）
│   │       └── artificial_analysis/  # Artificial Analysis统一表格提取脚本
│   ├── processing/            # 数据处理脚本
│   └── analysis/              # 统计分析脚本
├── results/                   # 结果输出目录
│   └── plots/                 # 生成的图表PDF文件
└── logs/                      # 日志文件目录
```

## Benchmark汇总统计

| 爬取方法 | 数量 | 状态 |
|---------|------|------|
| pandas.read_html | 2个 | ✅ 已实现 |
| Selenium | 4个 | ✅ 已实现 |
| Selenium (llm-stats) | 6个 | ✅ 已实现 |
| Artificial Analysis统一表格 | 10个 | ⚠️ 需要从统一表格中提取 |
| VALS.ai手动JSON | 3个 | ⚠️ 手动复制JSON |
| 手动下载 | 6个 | ⏸️ 需要手动处理 |
| **总计** | **31个** | |

**说明**：
- 总计31个benchmark包括：2个pandas.read_html + 4个Selenium + 6个Selenium (llm-stats) + 10个Artificial Analysis + 3个VALS.ai + 6个手动下载
- FrontierMath分为Tier 1-3和Tier 4两个benchmark，在手动下载部分算作2个benchmark
- Terminal-Bench Hard是新的benchmark，与Terminal-Bench v2.0不同，在Artificial Analysis统一表格中

---

## 爬取方法详细说明

### 方法1: pandas.read_html

**适用场景**: 静态HTML页面，包含`<table>`元素，无需JavaScript渲染

**脚本位置**: `github/src/ingestion/benchmarks/pandas_read_html/`

**数据输出位置**: `github/data/raw/benchmarks/{benchmark_id}.csv`

**爬取过程**:
1. 使用Python的`pandas`库中的`read_html()`函数
2. 直接传入URL，pandas会自动下载HTML并解析其中的`<table>`元素
3. 需要设置User-Agent请求头以避免被网站拒绝
4. `read_html()`返回一个DataFrame列表（一个表格对应一个DataFrame）
5. 通常第一个表格（index 0）包含排行榜数据，但需要验证
6. 提取所需的列（通常是`model_name`和`score`）
7. 将数据保存为CSV文件（UTF-8编码）

**必需依赖库**:
- `pandas`
- `html5lib` (pandas.read_html的依赖)
- `lxml` (可选，但推荐安装以提升性能)

**代码模板**:
```python
import pandas as pd

url = "https://example.com/leaderboard"
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"}

tables = pd.read_html(url, storage_options=headers)
df = tables[0]  # 通常第一个表格包含排行榜数据
# 提取model_name和score列（根据实际列名调整）
df = df[['model_name', 'score']]
df.to_csv("output.csv", index=False, encoding='utf-8')
```

**Benchmark列表**:

| 序号 | Benchmark名称 | URL | 脚本文件名 | 输出CSV文件名 |
|------|--------------|-----|-----------|--------------|
| 1 | Aider Polyglot | https://aider.chat/docs/leaderboards/ | `aider_polyglot.py` | `aider_polyglot.csv` |
| 2 | Terminal-Bench v2.0 | https://www.tbench.ai/leaderboard/terminal-bench/2.0?agents=Terminus+2 | `terminal_bench.py` | `terminal_bench.csv` |

---

### 方法2: Selenium

**适用场景**: 需要JavaScript动态渲染的网页，内容在页面加载后才生成

**脚本位置**: `github/src/ingestion/benchmarks/selenium/`

**数据输出位置**: `github/data/raw/benchmarks/{benchmark_id}.csv`

**爬取过程**:
1. 安装Selenium库和Chrome浏览器（确保Chrome已安装）
2. 创建Chrome WebDriver实例，设置为headless模式（无界面）
3. 设置User-Agent请求头
4. 使用WebDriver访问目标URL
5. 等待页面JavaScript渲染完成（通常需要3-5秒，使用`time.sleep(5)`）
6. 使用Selenium的`find_elements(By.TAG_NAME, "table")`方法定位表格元素
7. 提取表格的HTML内容（使用`get_attribute('outerHTML')`）
8. 使用`pandas.read_html(StringIO(html))`解析表格HTML
9. 选择正确的表格（通常是第一个，index 0）
10. 提取所需的列（`model_name`和`score`）
11. 关闭WebDriver（使用`driver.quit()`在`finally`块中确保清理）
12. 将数据保存为CSV文件（UTF-8编码）

**必需依赖库**:
- `selenium`
- `pandas`
- Chrome浏览器（ChromeDriver由Selenium 4.x自动管理）

**代码模板**:
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
chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36')

driver = webdriver.Chrome(options=chrome_options)
try:
    driver.get(url)
    time.sleep(5)  # 等待JavaScript渲染
    tables = driver.find_elements(By.TAG_NAME, "table")
    html = tables[0].get_attribute('outerHTML')
    dfs = pd.read_html(StringIO(html))
    df = dfs[0]
    # 提取model_name和score列（根据实际列名调整）
    df = df[['model_name', 'score']]
    df.to_csv("output.csv", index=False, encoding='utf-8')
finally:
    driver.quit()
```

**Benchmark列表**:

| 序号 | Benchmark名称 | URL | 脚本文件名 | 输出CSV文件名 |
|------|--------------|-----|-----------|--------------|
| 1 | SuperGPQA | https://supergpqa.github.io/ | `supergpqa.py` | `supergpqa.csv` |
| 2 | ARC-AGI-2 | https://arcprize.org/leaderboard | `arc_agi_2.py` | `arc_agi_2.csv` |
| 3 | SWE-Bench (Bash Only) | https://www.swebench.com/bash-only.html | `swe_bench_bash_only.py` | `swe_bench_bash_only.csv` |
| 4 | Creative Writing v3 | https://eqbench.com/creative_writing.html | `creative_writing_v3.py` | `creative_writing_v3.csv` |

**注意**: LiveCodeBench已移至Artificial Analysis统一表格方法（见方法5）

---

### 方法3: Selenium (llm-stats.com)

**适用场景**: llm-stats.com平台的所有benchmark，使用JavaScript动态渲染

**脚本位置**: `github/src/ingestion/benchmarks/selenium/llm_stats/`

**数据输出位置**: `github/data/raw/benchmarks/{benchmark_id}.csv`

**爬取过程**: 与标准Selenium方法完全相同，因为llm-stats.com平台也使用JavaScript动态渲染表格。参见方法2的详细说明。

**必需依赖库**: 与方法2（Selenium）相同

**Benchmark列表**:

| 序号 | Benchmark名称 | URL | 脚本文件名 | 输出CSV文件名 |
|------|--------------|-----|-----------|--------------|
| 1 | GPQA | https://llm-stats.com/benchmarks/gpqa | `gpqa.py` | `gpqa.csv` |
| 2 | HMMT (Feb 2025) | https://llm-stats.com/benchmarks/hmmt-2025 | `hmmt_2025.py` | `hmmt_2025.csv` |
| 3 | HumanEval | https://llm-stats.com/benchmarks/humaneval | `humaneval.py` | `humaneval.csv` |
| 4 | SWE-bench Verified | https://llm-stats.com/benchmarks/swe-bench-verified | `swe_bench_verified.py` | `swe_bench_verified.csv` |
| 5 | IFEval (Instruction-Following Eval) | https://llm-stats.com/benchmarks/ifeval | `ifeval.py` | `ifeval.csv` |
| 6 | Arena-Hard (Auto v2.0) | https://llm-stats.com/benchmarks/arena-hard-v2 | `arena_hard_v2.py` | `arena_hard_v2.csv` |

**注意**: AIME (2025)已移至Artificial Analysis统一表格方法（见方法5）

---

### 方法4: VALS.ai手动JSON

**适用场景**: VALS.ai平台（vals.ai）的benchmark，需要通过浏览器开发者工具手动复制JSON数据

**脚本位置**: 无（手动操作）

**数据输出位置**: `github/data/raw/benchmarks/manual/{benchmark_id}.json`

**爬取过程**:
1. 打开目标benchmark的URL（vals.ai平台）
2. 使用浏览器开发者工具（按F12键）打开网页检查器
3. 在Network标签页中找到包含排行榜数据的API请求，或直接在Elements标签页中找到包含JSON数据的`<script>`标签
4. 复制JSON数据（通常是完整的JSON对象或数组）
5. 将JSON数据保存为文件到`github/data/raw/benchmarks/manual/{benchmark_id}.json`
6. 如果需要转换为CSV进行分析，可以在后续处理步骤中使用Python的`json`库解析并转换

**数据格式**: JSON文件（保持原始数据格式，UTF-8编码）

**数据组织方式**:
- 数据以JSON格式存储，保持原始数据结构
- JSON文件应包含完整的排行榜数据，包括模型名称、分数以及其他元数据
- 如果需要CSV格式进行分析，可以在后续数据处理步骤中将JSON转换为CSV

**必需工具**:
- 浏览器开发者工具（网页检查器）
- Python `json`库（如果需要解析和转换）

**Benchmark列表**:

| 序号 | Benchmark名称 | URL | 输出JSON文件名 |
|------|--------------|-----|---------------|
| 1 | MATH-500 | https://www.vals.ai/benchmarks/math500 | `math_500.json` |
| 2 | MGSM | https://www.vals.ai/benchmarks/mgsm | `mgsm.json` |
| 3 | IOI (International Olympiad in Informatics) | https://www.vals.ai/benchmarks/ioi | `ioi.json` |

**重要说明**:
- VALS.ai的数据采用JSON格式存储，与其他benchmark的CSV格式不同
- 数据文件保存在`github/data/raw/benchmarks/manual/`目录下，因为需要手动从网页检查器复制JSON
- 文件名格式为`{benchmark_id}.json`（例如：`math_500.json`, `mgsm.json`, `ioi.json`）

---

### 方法5: Artificial Analysis统一表格

**适用场景**: Artificial Analysis平台（artificialanalysis.ai）的统一排行榜页面，包含10个benchmark的数据

**脚本位置**: `github/src/ingestion/benchmarks/artificial_analysis/`

**数据输出位置**: `github/data/raw/benchmarks/{benchmark_id}.csv`（每个benchmark一个独立的CSV文件）

**统一表格URL**: https://artificialanalysis.ai/leaderboards/models

**爬取过程**:
1. 访问统一排行榜URL: https://artificialanalysis.ai/leaderboards/models
2. 使用浏览器开发者工具（按F12键）打开网页检查器
3. 在Elements标签页中找到包含排行榜数据的`<table>`元素
4. 右键点击`<table>`标签，选择"Copy" -> "Copy element"或"Copy outerHTML"
5. 将复制的HTML表格保存为文件（.html格式）或直接在Python脚本中使用
6. 使用`pandas.read_html()`解析复制的HTML表格
7. 由于这是一个包含多个benchmark的统一表格，需要根据列名或benchmark标识符筛选出每个benchmark的数据
8. 为每个benchmark提取对应的列（通常是模型名称和该benchmark的分数列）
9. 将每个benchmark的数据保存为单独的CSV文件

**数据组织方式**:
- 所有10个benchmark的数据都来自同一张HTML表格
- 表格中包含多个列，每个benchmark对应一列或多列（分数列）
- 需要根据benchmark名称或标识符从统一表格中提取对应的数据
- 每个benchmark的数据保存为独立的CSV文件，包含`model_name`和`score`两列

**必需工具**:
- 浏览器开发者工具（网页检查器）
- Python `pandas`库

**代码模板**:
```python
import pandas as pd
from pathlib import Path

# 从复制的HTML文件中读取表格
with open('manually_copied_table.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# 或者直接从复制的HTML字符串解析
# html_content = '<table>...</table>'  # 手动复制的table HTML

tables = pd.read_html(html_content)
df = tables[0]  # 通常只有一个表格

# 查看所有列名，确定每个benchmark对应的列
print(df.columns.tolist())

# 为每个benchmark提取数据
benchmarks = {
    'terminal_bench_hard': 'Terminal-Bench Hard',  # 根据实际列名调整
    'tau2_bench_telecom': 'τ²-Bench Telecom',
    'aa_lcr': 'AA-LCR',
    'humanitys_last_exam': "Humanity's Last Exam",
    'mmlu_pro': 'MMLU-Pro',
    'gpqa_diamond': 'GPQA Diamond',
    'livecodebench': 'LiveCodeBench',
    'scicode': 'SciCode',
    'ifbench': 'IFBench',
    'aime_2025': 'AIME 2025'
}

output_dir = Path('github/data/raw/benchmarks')
output_dir.mkdir(parents=True, exist_ok=True)

for benchmark_id, column_name in benchmarks.items():
    # 根据实际表格结构提取数据
    # 假设表格中有'model_name'列和benchmark对应的分数列
    benchmark_df = df[['model_name', column_name]].copy()
    benchmark_df.columns = ['model_name', 'score']  # 标准化列名
    benchmark_df = benchmark_df.dropna()  # 移除空值
    benchmark_df.to_csv(output_dir / f'{benchmark_id}.csv', index=False, encoding='utf-8')
```

**Benchmark列表**:

| 序号 | Benchmark名称 | 统一表格URL | 输出CSV文件名 | 备注 |
|------|--------------|------------|--------------|------|
| 1 | Terminal-Bench Hard (Agentic Coding & Terminal Use) | https://artificialanalysis.ai/leaderboards/models | `terminal_bench_hard.csv` | 从统一表格中提取 |
| 2 | τ²-Bench Telecom (Agentic Tool Use) | https://artificialanalysis.ai/leaderboards/models | `tau2_bench_telecom.csv` | 从统一表格中提取 |
| 3 | AA-LCR (Long Context Reasoning) | https://artificialanalysis.ai/leaderboards/models | `aa_lcr.csv` | 从统一表格中提取 |
| 4 | Humanity's Last Exam (Reasoning & Knowledge) | https://artificialanalysis.ai/leaderboards/models | `humanitys_last_exam.csv` | 从统一表格中提取，替换原URL |
| 5 | MMLU-Pro (Reasoning & Knowledge) | https://artificialanalysis.ai/leaderboards/models | `mmlu_pro.csv` | 从统一表格中提取，替换原URL |
| 6 | GPQA Diamond (Scientific Reasoning) | https://artificialanalysis.ai/leaderboards/models | `gpqa_diamond.csv` | 从统一表格中提取，与GPQA不同 |
| 7 | LiveCodeBench (Coding) | https://artificialanalysis.ai/leaderboards/models | `livecodebench.csv` | 从统一表格中提取，替换原URL |
| 8 | SciCode (Coding) | https://artificialanalysis.ai/leaderboards/models | `scicode.csv` | 从统一表格中提取，替换原URL |
| 9 | IFBench (Instruction Following) | https://artificialanalysis.ai/leaderboards/models | `ifbench.csv` | 从统一表格中提取，替换原URL |
| 10 | AIME 2025 (Competition Math) | https://artificialanalysis.ai/leaderboards/models | `aime_2025.csv` | 从统一表格中提取，替换原URL |

**重要说明**:
- 所有10个benchmark的数据都来自同一张HTML表格
- 需要手动从网页检查器复制整个`<table>`元素的HTML
- 每个benchmark对应表格中的特定列（分数列）
- 需要为每个benchmark从统一表格中提取对应的数据并保存为独立的CSV文件

---

### 方法6: 手动下载

**适用场景**: 无法通过自动化方法获取数据的benchmark，需要手动下载或导出

**脚本位置**: 无（手动操作）

**数据输出位置**: `github/data/raw/benchmarks/manual/{benchmark_id}.csv`（或`.json`）

**说明**: 这些benchmark需要通过手动方式获取数据，包括：
- 从网站直接下载CSV文件
- 从HuggingFace Spaces手动导出数据
- 手动复制并整理数据

**数据组织方式**:
- 所有手动下载的数据保存在`github/data/raw/benchmarks/manual/`目录下
- 文件名格式为`{benchmark_id}.csv`或`{benchmark_id}.json`
- 文件应包含`model_name`和`score`两列（CSV格式）或相应的字段（JSON格式）
- 文件编码应为UTF-8

**Benchmark列表**:

| 序号 | Benchmark名称 | 原始URL | 输出文件名 | 说明 |
|------|--------------|---------|-----------|------|
| 1 | FACTS (Factuality, Accuracy, and Calibration Test Suite) | https://www.kaggle.com/benchmarks/google/facts | `facts.csv` | Kaggle平台，需要手动下载CSV文件 |
| 2 | WritingBench | https://huggingface.co/spaces/WritingBench/WritingBench | `writingbench.csv` | HuggingFace Spaces，需要手动下载 |
| 3 | EffiBench-X | https://huggingface.co/spaces/EffiBench/effibench-leaderboard | `effibench_x.csv` | HuggingFace Spaces，需要手动下载 |
| 4 | StructEval | https://huggingface.co/spaces/Bowieee/StructEval_leaderboard | `structeval.csv` | HuggingFace Spaces，需要手动下载 |
| 5 | FrontierMath Tier 1-3 | https://epoch.ai/frontiermath | `frontiermath_tier1_3.csv` | Epoch.ai平台，需要手动下载Tier 1-3的数据 |
| 6 | FrontierMath Tier 4 | https://epoch.ai/frontiermath | `frontiermath_tier4.csv` | Epoch.ai平台，需要手动下载Tier 4的数据 |

**重要说明**:
- FrontierMath分为两部分：Tier 1-3和Tier 4，视作两个独立的benchmark
- 每个部分的数据需要分别手动下载并保存为独立的CSV文件
- 文件名分别为`frontiermath_tier1_3.csv`和`frontiermath_tier4.csv`
- MMLU-Pro已移至Artificial Analysis统一表格方法（见方法5），使用统一表格URL：https://artificialanalysis.ai/leaderboards/models

---

## 数据格式说明

### CSV格式

大多数benchmark的数据以CSV格式存储，文件应包含以下列：

**必需列**:
- `model_name`: 模型名称（字符串类型）
- `score`: 分数（浮点数类型，范围通常是0-100）

**可选列**（根据来源可能包含）:
- `rank`: 排名
- `company`: 公司/组织名称
- 其他元数据列

**文件编码**: UTF-8

**文件位置**:
- 自动化爬取的数据: `github/data/raw/benchmarks/{benchmark_id}.csv`
- 手动下载的数据: `github/data/raw/benchmarks/manual/{benchmark_id}.csv`

### JSON格式

VALS.ai平台的benchmark数据以JSON格式存储：

**文件编码**: UTF-8

**文件位置**: `github/data/raw/benchmarks/manual/{benchmark_id}.json`

**数据结构**: 根据实际API响应结构而定，通常包含模型列表，每个模型对象包含名称和分数等信息

---

## 快速开始

### 安装依赖

```bash
# 进入github目录
cd github

# 安装基础依赖（使用uv包管理器）
uv add pandas html5lib lxml selenium requests beautifulsoup4
```

### 运行爬取脚本

```bash
# pandas.read_html方法
python src/ingestion/benchmarks/pandas_read_html/aider_polyglot.py
python src/ingestion/benchmarks/pandas_read_html/terminal_bench.py

# Selenium方法
python src/ingestion/benchmarks/selenium/supergpqa.py
python src/ingestion/benchmarks/selenium/arc_agi_2.py
python src/ingestion/benchmarks/selenium/swe_bench_bash_only.py
python src/ingestion/benchmarks/selenium/creative_writing_v3.py

# Selenium (llm-stats)方法
python src/ingestion/benchmarks/selenium/llm_stats/gpqa.py
python src/ingestion/benchmarks/selenium/llm_stats/hmmt_2025.py
python src/ingestion/benchmarks/selenium/llm_stats/humaneval.py
python src/ingestion/benchmarks/selenium/llm_stats/swe_bench_verified.py
python src/ingestion/benchmarks/selenium/llm_stats/ifeval.py
python src/ingestion/benchmarks/selenium/llm_stats/arena_hard_v2.py

# Artificial Analysis统一表格（需要先手动复制HTML表格）
python src/ingestion/benchmarks/artificial_analysis/extract_from_unified_table.py
```

### 数据文件位置

- **自动化爬取的数据**: `github/data/raw/benchmarks/{benchmark_id}.csv`
- **手动下载的数据**: `github/data/raw/benchmarks/manual/{benchmark_id}.csv` 或 `.json`
- **Artificial Analysis统一表格**: 每个benchmark的数据从统一表格中提取后，保存为独立的CSV文件在`github/data/raw/benchmarks/`目录下

---

## 更新日期

最后更新: 2025-12-28

