# Benchmark Data Preparation and Scraping Guide

This document details the directory structure, file formats, and data scraping workflow for the Human-SIG project.

## Environment Configuration

### Quick Start

1.  **Install Dependencies**

    Run in the project root `Human-SIG/`:

    ```bash
    uv sync
    ```

    **Note**: The project uses `uv` for package management. `uv sync` automatically installs dependencies from `pyproject.toml`.

2.  **Verify Installation**

    ```bash
    uv run python -c "import pandas, html5lib, lxml, selenium, webdriver_manager, scipy, statsmodels, seaborn, rbo; print('All dependencies installed successfully')"
    ```

## Directory Structure

```
Human-SIG/
├── config/                    # Metadata and configuration
├── data/
│   ├── raw/                   # Raw data
│   │   ├── lmarena/           # LMArena data
│   │   │   └── {category}/    # e.g., LMArena-Overall, LMArena-Coding, etc.
│   │   │       ├── input.txt  # Source HTML
│   │   │       └── data.csv   # Extracted data
│   │   ├── artificial_analysis/
│   │   │   ├── input.txt      # Unified table HTML
│   │   │   └── {benchmark}/
│   │   │       └── data.csv
│   │   ├── frontiermath/
│   │   │   └── {tier}/          # e.g., FrontierMath_Tier_1-3, FrontierMath_Tier_4
│   │   │       ├── input.txt
│   │   │       └── data.csv
│   │   ├── manual_direct/
│   │   │   └── {benchmark}/
│   │   │       └── data.csv   # Directly provided file
│   │   ├── pandas_read_html/
│   │   │   └── {benchmark}/
│   │   │       ├── input.txt  # URL
│   │   │       └── data.csv
│   │   ├── selenium/
│   │   │   └── {benchmark}/
│   │   │       ├── input.txt  # URL
│   │   │       └── data.csv
│   │   └── vals_ai/
│   │       └── {benchmark}/
│   │           ├── input.txt  # JSON/HTML source
│   │           └── data.csv
│   └── processed/             # Processed data
│       ├── model_extraction/   # LMArena model information (auto-generated)
│       │   └── lmarena_models.json
│       ├── cleaned/           # Step 1 output: cleaned data
│       │   ├── {benchmark_id}/
│       │   │   ├── cleaned_data.csv
│       │   │   └── mapping.json  # Step 3 output
│       │   └── artificial_analysis/  # Step 1 output: unified model list
│       │       └── cleaned_data.csv  # Unified list for all 10 benchmarks
│       └── review_files/       # Step 2 output: review files
│           ├── {benchmark_id}.json
│           └── artificial_analysis.json  # Unified review file for all 10 benchmarks
├── src/
│   ├── scrapers/              # Scraping logic
│   │   ├── selenium_scraper.py
│   │   ├── lmarena_scraper.py
│   │   ├── ...
│   ├── main.py                # Unified CLI entry point
│   ├── processing/            # Data processing scripts
│   └── analysis/              # Analysis scripts
```

## Workflow Overview

The project uses a unified CLI for data acquisition.

1.  **Preparation**: Place the required source content (URL, HTML, or JSON) into `input.txt` within the appropriate benchmark directory in `data/raw/`.
2.  **Execution**: Run the centralized scraper via `src/main.py`.
3.  **Result**: The script generates `data.csv` in the respective benchmark folders.

## Detailed Instructions by Method

### Universal Command

To run all scrapers:
```bash
uv run src/main.py scrape --method all
```

To run a specific method:
```bash
uv run src/main.py scrape --method <method_name>
```

### 1. manual_direct
*   **Location**: `data/raw/manual_direct/{benchmark_name}/`
*   **Preparation**: Directly place your data file as `data.csv`.
*   **Execution**: No script execution required.

### 2. pandas_read_html
*   **Location**: `data/raw/pandas_read_html/`
*   **Preparation**: Create `input.txt` in the benchmark folder containing a single line with the Leaderboard URL.
*   **Execution**:
    ```bash
    uv run src/main.py scrape --method pandas_read_html
    ```

### 3. selenium
*   **Location**: `data/raw/selenium/`
*   **Preparation**: Create `input.txt` in the benchmark folder containing a single line with the Leaderboard URL.
*   **Execution**:
    ```bash
    uv run src/main.py scrape --method selenium
    ```
    *Note*: Requires Chrome and ChromeDriver (managed automatically).

### 4. artificial_analysis
*   **Location**: `data/raw/artificial_analysis/`
*   **Preparation**: Copy the full table HTML from the Artificial Analysis website into `data/raw/artificial_analysis/input.txt`. As there are models appear more than once (mostly because "Thinking" and "Non-Thinking" are ommitted on this platform), it is necessary to firstly run `src/scrapers/artificial_analysis_first_processer.py` to process the data into a .csv file, with all the benchmark scores, and the order of the benchmarks is in the dictionary order of model names. Then, add the -Thinking and -Non-Thinking suffix to the repeated models, and some of them, which has four same names in a row, need to add -Preview to half of them. Please click 'Model' in the leaderboard website to check the detailed information of each model. Scraping the data into raw data needs the correct `data/raw/artificial_analysis/combined_all_benchmarks.csv`.
*   **Execution**:
*   If you want to update the data and manually process the model names, update the `input.txt` first and run:
    ```bash
    uv run src/scrapers/artificial_analysis_first_processer.py
    ```
*   After processing the model names manually, run the below script to apply them into raw data:
    ```bash
    uv run src/main.py scrape --method artificial_analysis
    ```

### 5. vals_ai
*   **Location**: `data/raw/vals_ai/`
*   **Preparation**: Copy the page source or JSON data containing the `benchmarkView` structure into `input.txt` in each benchmark folder.
*   **Execution**:
    ```bash
    uv run src/main.py scrape --method vals_ai
    ```

### 6. lmarena
*   **Location**: `data/raw/lmarena/`
*   **Preparation**: For each category (e.g., `LMArena-Overall`, `LMArena-Coding`, `LMArena-Math`, `LMArena-Hard Prompts`, `LMArena-Creative Writing`, `LMArena-Instruction Following`, `LMArena-Expert`), copy the table HTML into the corresponding `input.txt`.
*   **Execution**:
    ```bash
    uv run src/main.py scrape --method lmarena
    ```

### 7. frontiermath
*   **Location**: `data/raw/frontiermath/`
*   **Preparation**: Copy the table HTML into `input.txt` for each tier folder.
*   **Execution**:
    ```bash
    uv run src/main.py scrape --method frontiermath
    ```

---

## Data Processing Pipeline

After scraping raw data, the project uses a three-step processing pipeline to extract model names, parse model information, match models with LMArena models, and generate final mappings. The pipeline consists of three automated steps and two manual review steps.

### Workflow Overview

```
Raw Data (data/raw/*/data.csv)
    ↓
[Step 1] step1_generate_cleaned_data.py (deterministic)
    ├─ Extract model names and scores
    ├─ Detect duplicate model names
    ├─ Add (2), (3) suffixes to duplicates
    └─ [Special] For artificial_analysis: Generate unified model list
    ↓
cleaned_data.csv (data/processed/cleaned/{benchmark_id}/cleaned_data.csv)
    ├─ May contain suffixed model names (e.g., "Model Name(2)")
    └─ Requires human review to confirm duplicates
    ↓
[Special] artificial_analysis unified list (data/processed/cleaned/artificial_analysis/cleaned_data.csv)
    └─ Contains all models with at least one non-empty score across 10 benchmarks
    ↓
[Manual Review 1] Review and handle duplicate model names in cleaned_data.csv
    ├─ Confirm if duplicates are real different model instances
    ├─ If data duplicates, delete or merge
    └─ If real different models, keep suffixed names
    ↓
[Step 2] step2_generate_review_files.py (non-deterministic)
    ├─ Auto-generate model_extraction/lmarena_models.json (regenerated every run)
    ├─ Parse model information from cleaned_data.csv and match
    └─ [Special] For artificial_analysis: Generate unified review file
    ↓
review_files (data/processed/review_files/{benchmark_id}_review.json)
    ├─ [Special] artificial_analysis_review.json (unified for all 10 benchmarks)
    └─ Other benchmarks: individual review files
    ↓
[Manual Review 2] Manually edit review_files (modify untrusted and selected_lmarena_model)
    ↓
[Step 3] step3_generate_mapping.py (deterministic)
    ├─ [Special] For artificial_analysis: Generate mapping.json for each benchmark
    │   └─ Filter by each benchmark's cleaned_data.csv
    └─ Other benchmarks: Generate mapping.json from individual review files
    ↓
mapping.json (data/processed/cleaned/{benchmark_id}/mapping.json)
```

### Benchmark ID Naming Convention

**Important**: The `benchmark_id` directly uses the folder name from raw data, without any source prefix.

*   `data/raw/artificial_analysis/AA-LCR/data.csv` → benchmark_id: `AA-LCR`
*   `data/raw/selenium/HumanEval/data.csv` → benchmark_id: `HumanEval`
*   `data/raw/lmarena/LMArena-Overall/data.csv` → benchmark_id: `LMArena-Overall`

All output file paths use this `benchmark_id`:
*   `data/processed/cleaned/{benchmark_id}/cleaned_data.csv`
*   `data/processed/review_files/{benchmark_id}_review.json`
*   `data/processed/cleaned/{benchmark_id}/mapping.json`

**Special handling for artificial_analysis**:
*   The 10 artificial_analysis benchmarks (AA-LCR, AIME, GPQA_Diamond, etc.) share a unified model list and review file:
    *   Unified model list: `data/processed/cleaned/artificial_analysis/cleaned_data.csv`
    *   Unified review file: `data/processed/review_files/artificial_analysis_review.json`
    *   Individual mapping files: `data/processed/cleaned/{benchmark_id}/mapping.json` (filtered by each benchmark's cleaned_data.csv)

---

## Step 1: Generate Cleaned Data (Deterministic)

### Overview

Extract model names and scores from raw CSV files, calculate rankings, and generate standardized `cleaned_data.csv` files.

**Input**: `data/raw/*/data.csv` (all raw data files)

**Output**: 
*   `data/processed/cleaned/{benchmark_id}/cleaned_data.csv` (for each benchmark)
*   `data/processed/cleaned/artificial_analysis/cleaned_data.csv` (unified model list for artificial_analysis benchmarks)

### Script Location

**Script**: `src/processing/step1_generate_cleaned_data.py`

**Execution**:
```bash
cd Human-SIG
python src/processing/step1_generate_cleaned_data.py
```

### Processing Logic

The script is self-contained with all necessary utility functions and requires no external module imports.

1.  **Traverse all raw data**: Read all `data.csv` files from `data/raw/` directory
2.  **Identify column names**:
    *   Model name column: Auto-detect "Model", "model", "Model Name", "AI System", "model_name", "name", "Agent", etc.
    *   Score column: Auto-detect based on benchmark type (e.g., "Score", "Intelligence AA-LCR", "score_value", "Numerical_Result", "accuracy", etc.)
3.  **Extract data**:
    *   Extract model names and scores from CSV
    *   Process all models in CSV without any filtering
4.  **Handle duplicate model names**:
    *   Detect duplicate model names within the same benchmark
    *   If duplicates found, add suffixes to subsequent occurrences:
        *   First occurrence remains unchanged (e.g., "Model Name")
        *   Second occurrence marked as "Model Name(2)"
        *   Third occurrence marked as "Model Name(3)"
        *   And so on
    *   **Important**: These suffixed model names require human review
5.  **Process score formats**:
    *   Remove ± error parts (e.g., "1490 ±6" → 1490.0)
    *   Handle percentage format (e.g., "71%" → 71.0)
    *   Handle decimal format (e.g., "0.945" → 0.945)
    *   Convert to float for ranking calculation

    *   **Special handling for FACTS benchmark**: Only extract rows where `Task_Name == "Average"`, use `Numerical_Result` column for scores
    *   **Score normalization**: For benchmarks using 0-1 scale (FACTS, GPQA, HMMT (Feb 2025), HumanEval, IFEval, SuperGPQA, SWE-bench (Verified), Arena-Hard (Auto v2.0)), multiply scores by 100 to normalize to 0-100 scale

6.  **Calculate rankings**:
    *   Sort by score in descending order
    *   Tied scores: Models with same score get same rank
    *   Next rank skips tied count (e.g., scores [99, 98, 98, 97] → ranks [1, 2, 2, 4])
7.  **Special handling for artificial_analysis**:
    *   After processing all benchmarks, generate a unified model list for artificial_analysis
    *   Collect all models that have at least one non-empty score (not "--") across the 10 artificial_analysis benchmarks
    *   Generate `data/processed/cleaned/artificial_analysis/cleaned_data.csv` containing only model names (no scores/ranks)
    *   This unified list is used in step 2 to generate a single review file instead of 10 separate files

### Output File

**Output directory**: `data/processed/cleaned/{benchmark_id}/`

**File format**: `cleaned_data.csv`

Contains three columns:
*   `model_name`: Model name (exactly as in raw CSV)
*   `score`: Score (float)
*   `rank`: Rank (integer, tied scores share rank)

**Example**:
```csv
model_name,score,rank
GPT-5 (high),76.0,1
GPT-5.1 (high),75.0,2
Claude Opus 4.5,74.0,3
KAT-Coder-Pro V1,74.0,3
GPT-5.2 (xhigh),73.0,5
```

### Duplicate Model Name Handling

**Automatic processing**:
*   Script automatically detects duplicate model names within the same benchmark
*   Adds `(2)`, `(3)`, `(4)` suffixes to duplicate names
*   Ensures each model name in `cleaned_data.csv` is unique

**Example**:
```csv
model_name,score,rank
GPT-5,76.0,1
GPT-5(2),75.0,2
Claude Opus 4.5,74.0,3
Claude Opus 4.5(2),73.0,4
```

**Human review requirements**:
*   All model names with `(2)`, `(3)` suffixes require manual review
*   Need to confirm if duplicates are:
    *   **Real different model instances**: Keep suffixed names (e.g., different versions, configurations)
    *   **Data duplicates**: Delete duplicate entries or merge data

### Notes

*   Script automatically handles multiple encodings (UTF-8, GBK, Latin-1, CP1252)
*   Each benchmark corresponds to an independent folder and `cleaned_data.csv` file
*   **Important**: Before running step 2, must review and handle duplicate model names in `cleaned_data.csv`

---

## Manual Review 1: Review Duplicate Model Names

### Why Review Duplicates?

In step 1, the script automatically adds `(2)`, `(3)` suffixes to duplicate model names, but these duplicates may be:
1.  **Real different model instances**: e.g., different versions, configurations, or release dates of the same model
2.  **Data duplicates**: Errors in raw data where the same model was recorded multiple times

Before proceeding to step 2 (model parsing and matching), need to confirm the nature of these duplicates to avoid bringing duplicate data into subsequent steps.

### How to Identify Duplicates for Review

**Method 1: Check cleaned_data.csv**
*   Open `data/processed/cleaned/{benchmark_id}/cleaned_data.csv`
*   Search for model names containing `(` and `)` (e.g., `Model Name(2)`)

**Method 2: Use check script**
Run the following Python code to quickly find all duplicates:
```python
import csv
import re
from pathlib import Path

base_dir = Path('data/processed/cleaned')
for csv_file in base_dir.rglob('cleaned_data.csv'):
    benchmark_id = csv_file.parent.name
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    duplicates = [r for r in rows if re.search(r'\((\d+)\)$', r['model_name'])]
    if duplicates:
        print(f"{benchmark_id}: {len(duplicates)} duplicate models")
        for dup in duplicates[:5]:  # Show first 5
            print(f"  - {dup['model_name']}")
```

### Review Steps

#### Step 1: Open cleaned_data.csv

Use Excel, VS Code, or any CSV viewer to open:
```
data/processed/cleaned/{benchmark_id}/cleaned_data.csv
```

#### Step 2: Check Each Duplicate Model

For each model name with `(2)`, `(3)` suffixes:

**Case 1: Real different model instances**

Example:
```csv
model_name,score,rank
GPT-5,76.0,1
GPT-5(2),75.0,2
```

**Criteria**:
*   Two models have different scores
*   May be different versions, configurations, or test dates of the same model
*   Two different entries exist in raw data

**Action**:
*   **Keep both entries**, suffixed name remains unchanged
*   In subsequent step 2, these two models will be parsed and matched separately

**Case 2: Data duplicates**

Example:
```csv
model_name,score,rank
Claude Opus 4.5,74.0,3
Claude Opus 4.5(2),74.0,3
```

**Criteria**:
*   Two models have same score (or very close)
*   May be the same model recorded twice in raw data
*   No obvious differences (version, configuration, date, etc.)

**Action**:
*   **Delete duplicate entry**: Remove the suffixed row from `cleaned_data.csv`
*   Or if scores differ slightly, keep the one with higher score

#### Step 3: Modify cleaned_data.csv

**Using Excel**:
1.  Open CSV file
2.  Find duplicate rows to delete
3.  Delete entire row
4.  Save file (ensure saved as CSV format)

**Using text editor**:
1.  Open CSV file
2.  Find duplicate row to delete
3.  Delete the row (including newline)
4.  Save file

**Using Python script**:
```python
import csv
import re
from pathlib import Path

csv_file = Path('data/processed/cleaned/{benchmark_id}/cleaned_data.csv')
rows_to_keep = []

with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Check if this is a duplicate to delete (adjust logic as needed)
        if re.search(r'\(2\)$', row['model_name']):
            # Check if duplicate of previous entry (adjust logic as needed)
            continue
        rows_to_keep.append(row)

# Write back to file
with open(csv_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['model_name', 'score', 'rank'])
    writer.writeheader()
    writer.writerows(rows_to_keep)
```

### Review Checklist

For each suffixed model name, check:
*   [ ] Is it a real different model instance?
    *   [ ] If yes, keep the suffixed name
*   [ ] Is it a data duplicate?
    *   [ ] If yes, delete the duplicate entry
*   [ ] Is the modified `cleaned_data.csv` correctly formatted?
*   [ ] Are changes saved?

### Notes

*   **Must complete review before running step 2**: If `cleaned_data.csv` contains unprocessed duplicates, they will be carried into subsequent steps
*   **Keep real different models**: If two suffixed models are indeed different instances (e.g., different versions), must keep them
*   **Delete data duplicates**: If confirmed as data errors, must delete them
*   **Recalculate rankings**: If duplicate entries are deleted, rankings may be affected (usually minimal impact)

---

## Step 2: Generate Review Files (Non-Deterministic)

### Overview

Read model names from `cleaned_data.csv`, parse model information, match LMArena candidates, automatically select best match, and generate `review_files`.

**Input**:
*   `data/processed/cleaned/{benchmark_id}/cleaned_data.csv`
*   `data/raw/lmarena/LMArena-Overall/data.csv` (LMArena raw data, used to generate unified `lmarena_models.json` file)

**Output**: 
*   `data/processed/review_files/{benchmark_id}.json` (for each benchmark)
*   `data/processed/review_files/artificial_analysis.json` (unified review file for all 10 artificial_analysis benchmarks)

**Notes**:
*   LMArena benchmarks are skipped (because LMArena models can match internally)
*   Script automatically generates unified `lmarena_models.json` from `LMArena-Overall` raw data (regenerated every run to ensure latest data)
*   The `lmarena_models.json` file contains all LMArena models with Score >= 1330 (Study Universe), used for matching all other benchmarks
*   Other benchmarks don't need separate extraction files, directly read model names from `cleaned_data.csv` and parse

### Script Location

**Script**: `src/processing/step2_generate_review_files.py`

**Execution**:
```bash
cd Human-SIG
python src/processing/step2_generate_review_files.py
```

### Processing Logic

The script is self-contained with all necessary utility functions (model parsing, matchers, etc.) and requires no external module imports.

1.  **Generate LMArena model information**:
    *   **Unified design**: Only one `lmarena_models.json` file exists, generated from `data/raw/lmarena/LMArena-Overall/data.csv`
    *   **Regenerated every run**: Ensures data is latest (doesn't check if file exists, regenerates every time)
    *   Only keeps models with Score >= 1330 (Study Universe)
    *   This unified file is used for matching all other benchmarks with LMArena models in step 2
    *   This design facilitates review and subsequent analysis
2.  **Read model names**: Read all model names from `cleaned_data.csv`
3.  **Parse model information**: Use built-in model parsing functions to parse each model name, extract:
    *   `family` (family)
    *   `subfamily` (subfamily)
    *   `version` (version)
    *   `date` (date)
    *   `parameters` (parameter count)
    *   `other_info` (other information)
4.  **Match candidates**: Use structured matching algorithm to find all possible LMArena candidates for each benchmark model:
    *   Family, subfamily, version must match exactly
    *   If parameters exist in both and don't match, exclude match
    *   Date doesn't participate in filtering
5.  **Automatically select best match**:
    *   Single candidate and not NO_MATCH_FOUND: Use directly
    *   Multiple candidates: Use similarity algorithm to select best match (considers other_info, date, parameters, subfamily)
    *   No candidates or only NO_MATCH_FOUND: Set to `0`
6.  **Generate review_file**: Contains structured information and candidate list for all models

### Output File

**Output directory**: `data/processed/review_files/`

**File format**: `{benchmark_id}.json`

**File structure**:
```json
{
  "GPT-5.2 (xhigh)": {
    "benchmark_info": {
      "family": "gpt",
      "subfamily": null,
      "version": "5.2",
      "date": null,
      "parameters": null,
      "other_info": ["5.2", "xhigh"]
    },
    "candidates": [
      {
        "lmarena_model": "gpt-5.2",
        "family": "gpt",
        "subfamily": null,
        "version": "5.2",
        "date": null,
        "parameters": null,
        "other_info": ["5.2"]
      }
    ],
    "untrusted": 1,
    "selected_lmarena_model": "gpt-5.2"
  },
  "o3": {
    "benchmark_info": {
      "family": "gpt",
      "subfamily": "o3",
      "version": "3.0",
      "date": null,
      "parameters": null,
      "other_info": null
    },
    "candidates": [
      {
        "lmarena_model": "o3-2025-04-16",
        "family": "gpt",
        "subfamily": "o3",
        "version": "3.0",
        "date": "2025-04-16",
        "parameters": null,
        "other_info": null
      },
      {
        "lmarena_model": "o3-mini-high",
        "family": "gpt",
        "subfamily": "o3",
        "version": "3.0",
        "date": null,
        "parameters": null,
        "other_info": ["mini", "high"]
      }
    ],
    "untrusted": 1,
    "selected_lmarena_model": "o3-2025-04-16"
  }
}
```

### Field Descriptions

**`benchmark_info`**:
*   Structured information parsed from model name (family, subfamily, version, date, parameters, other information)

**`candidates`**:
*   List of all possible matching LMArena models
*   If no candidates, contains one `{"lmarena_model": "NO_MATCH_FOUND"}` entry

**`untrusted`**:
*   **Default value**: `1` (indicates completed by agent, not trusted)
*   **After human review**: Change to `0` (indicates data is rigorous, but doesn't affect subsequent generation)
*   **Note**: Subsequent code doesn't read this field, it's only used to mark data rigor

**`selected_lmarena_model`**:
*   **Model name (string)**: Automatically selected or unique candidate LMArena model name
*   `0`: Automatically determined no corresponding model
*   `-1`: Human review confirmed no corresponding model (requires manual setting)

### Special Handling

**LMArena skip**:
*   All `LMArena-*` benchmarks are automatically skipped (e.g., `LMArena-Overall`, `LMArena-Coding`, etc.)
*   Because LMArena models can match internally, no need to generate review_file

**Artificial Analysis (Special Handling)**:
*   The 10 artificial_analysis benchmarks (AA-LCR, AIME, GPQA_Diamond, etc.) are processed as a unified list
*   Use the unified model list from `data/processed/cleaned/artificial_analysis/cleaned_data.csv` (generated in step 1)
*   Generate a single review file: `artificial_analysis_review.json` instead of 10 separate files
*   This avoids duplicate review work since many models appear in multiple artificial_analysis benchmarks

---

## Manual Review 2: Review Model Matching Results

### Review File Location

**Review file directory**: `data/processed/review_files/`

**File format**: JSON (`.json` extension)

### How to Identify Entries Needing Review

**Method 1: Use `untrusted` field**
*   Search in JSON file: `"untrusted": 1`
*   These entries are all automatically reviewed by agent and require human confirmation

**Method 2: Check `selected_lmarena_model`**
*   `selected_lmarena_model: 0` indicates automatically determined no match, needs confirmation
*   `selected_lmarena_model` is string but `untrusted: 1` indicates automatic selection, needs confirmation

### Review Steps

#### Step 1: Open Review File

Use one of the following tools to open JSON file:
*   **VS Code** (recommended): Auto-formatting, syntax highlighting, JSON validation
*   **Notepad++**: Lightweight editor
*   **Online JSON viewer**: e.g., https://jsonviewer.stack.hu/

#### Step 2: Review Each Model

For each model entry:

**Case 1: `untrusted: 1` with multiple candidates**

Example:
```json
{
  "o3": {
    "benchmark_info": {...},
    "candidates": [
      {"lmarena_model": "o3-2025-04-16", ...},
      {"lmarena_model": "o3-mini-high", ...},
      {"lmarena_model": "o3-mini", ...}
    ],
    "untrusted": 1,
    "selected_lmarena_model": "o3-2025-04-16"
  }
}
```

**Actions**:
1.  Check if `selected_lmarena_model` value is correct
2.  If incorrect, modify to correct candidate model name
3.  If confirmed correct, change `untrusted` to `0`
4.  If confirmed no match, change `selected_lmarena_model` to `-1`, `untrusted` to `0`

**Case 2: `untrusted: 1` with single candidate**

Example:
```json
{
  "GPT-5.2 (xhigh)": {
    "benchmark_info": {...},
    "candidates": [
      {"lmarena_model": "gpt-5.2", ...}
    ],
    "untrusted": 1,
    "selected_lmarena_model": "gpt-5.2"
  }
}
```

**Actions**:
1.  Check if automatic selection result is correct
2.  If correct, change `untrusted` to `0`
3.  If incorrect, modify `selected_lmarena_model` to correct value, then set `untrusted: 0`

**Case 3: `selected_lmarena_model: 0` (no match)**

Example:
```json
{
  "Gemini 3 Pro Preview (high)": {
    "benchmark_info": {...},
    "candidates": [
      {"lmarena_model": "NO_MATCH_FOUND"}
    ],
    "untrusted": 1,
    "selected_lmarena_model": 0
  }
}
```

**Actions**:
1.  Check if there really is no matching model
2.  If confirmed no match, change `selected_lmarena_model` to `-1`, `untrusted` to `0`
3.  If match exists but algorithm didn't find it, manually add candidate to `candidates` array, then modify `selected_lmarena_model`

#### Step 3: Save Changes

*   Ensure JSON format is valid (VS Code auto-detects)
*   Save file (Ctrl+S)

### Review Checklist

For each model, check:
*   [ ] Is `selected_lmarena_model` value correct?
*   [ ] If correct, is `untrusted` set to `0`?
*   [ ] If no match, is `selected_lmarena_model` `-1` and `untrusted` `0`?
*   [ ] Is JSON format correct (no syntax errors)?

### Special Handling: artificial_analysis

**Important**: The 10 `artificial_analysis` benchmarks share a unified review file:
*   `artificial_analysis.json` (contains all models from the unified list)

**Review process**:
*   Review the unified `artificial_analysis.json` file
*   This file contains all models that appear in at least one of the 10 artificial_analysis benchmarks
*   After review, step 3 will automatically generate individual `mapping.json` files for each benchmark, filtered by each benchmark's `cleaned_data.csv`

---

## Step 3: Generate Mapping.json (Deterministic)

### Overview

Read review results from `review_files`, extract `selected_lmarena_model` field, and generate `mapping.json` file for each benchmark.

**Input**: 
*   `data/processed/review_files/{benchmark_id}.json` (for each benchmark)
*   `data/processed/review_files/artificial_analysis.json` (unified review file for artificial_analysis)

**Output**: `data/processed/cleaned/{benchmark_id}/mapping.json`

**Note**: The script is self-contained with all necessary utility functions and requires no external module imports.

### Script Location

**Script**: `src/processing/step3_generate_mapping.py`

**Execution**:
```bash
cd Human-SIG
python src/processing/step3_generate_mapping.py
```

### Processing Logic

The script is self-contained with all necessary utility functions and requires no external module imports.

1.  **Read all review_files**: Read all `*.json` files from `data/processed/review_files/` (excluding `artificial_analysis.json` which is handled separately)
2.  **Special handling for artificial_analysis**:
    *   If `artificial_analysis.json` exists, process it separately
    *   For each of the 10 artificial_analysis benchmarks:
        *   Load the benchmark's `cleaned_data.csv` to get the list of models in that benchmark
        *   Filter the unified review file to only include models present in that benchmark
        *   Extract mappings and generate `mapping.json` for that benchmark
3.  **Extract final mappings** (for other benchmarks):
    *   For each model, read `selected_lmarena_model` field
    *   If value is model name (string), create mapping
    *   If value is `0` or `-1`, skip (don't create mapping)
4.  **Deduplication**: If multiple benchmark models map to same LMArena model, only keep first mapping (subsequent duplicates automatically skipped)
5.  **Generate mapping.json**: Write mappings to `cleaned/{benchmark_id}/mapping.json`

### Output File

**Output file**: `data/processed/cleaned/{benchmark_id}/mapping.json`

**File format**:
```json
{
  "GPT-5.2 (xhigh)": "gpt-5.2",
  "Gemini 3 Flash": "gemini-3-flash",
  "o3": "o3-2025-04-16",
  "DeepSeek V3.2": "deepseek-v3.2",
  ...
}
```

**Important features**:
*   Only contains valid mappings (`selected_lmarena_model` is string)
*   Each LMArena model appears at most once in the benchmark (duplicate mappings automatically removed, only first kept)
*   Model names exactly match naming in `cleaned_data.csv`

### Notes

*   Only entries where `selected_lmarena_model` is model name (string) are added to mapping table
*   Entries where `selected_lmarena_model` is `0` or `-1` are skipped
*   `untrusted` field is not read and doesn't affect mapping generation

---

## Field Reference

### Review File Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `benchmark_info` | Object | Structured information of model in benchmark |
| `candidates` | Array | List of possible matching LMArena models |
| `untrusted` | Number | 1=untrusted (agent completed), 0=trusted (human reviewed) |
| `selected_lmarena_model` | String/Number | Model name/0/-1 |

### `selected_lmarena_model` Value Descriptions

| Value | Type | Description |
|-------|------|-------------|
| `"model-name"` | String | LMArena model name |
| `0` | Number | Automatically determined no corresponding model |
| `-1` | Number | Human confirmed no corresponding model |

### Quick Reference

| Situation | Action |
|-----------|--------|
| Automatic selection correct | Change `untrusted` to `0` |
| Automatic selection incorrect | Modify `selected_lmarena_model`, then set `untrusted: 0` |
| Confirm no match | Change `selected_lmarena_model` to `-1`, `untrusted` to `0` |
| Need to add candidate | Add to `candidates`, then modify `selected_lmarena_model` |

---

## Statistical Analysis Pipeline

After completing the data processing pipeline (Steps 1-3), the following steps perform statistical analysis and generate results for the manuscript.

### Prerequisites

Ensure the following files are ready:
*   Cleaned data: `data/processed/cleaned/{benchmark_id}/cleaned_data.csv` (all benchmarks)
*   Mapping files: `data/processed/cleaned/{benchmark_id}/mapping.json` (all benchmarks)
*   LMArena data: `data/processed/cleaned/LMArena-{category}/cleaned_data.csv` (all LMArena categories)
*   Metadata: `data/metadata.json`
*   Study Universe: `data/processed/model_extraction/lmarena_models.json`

---

## Step 4: Master Table Construction

**Script**: `src/processing/build_master_table.py`

Construct master correlation matrix by merging benchmark scores and ranks with LMArena ELO scores.

**Input**: Cleaned data files, mapping files, LMArena data, metadata, Study Universe

**Output**: 
*   `data/processed/master_table/master_correlation_matrix.csv` - Master table with all benchmark scores and ranks
*   `results/data_overlap_stats.json` - Overlap statistics for each benchmark

**Execution**:
```bash
cd Human-SIG
uv run python src/processing/build_master_table.py
```

---

## Step 5: Feature Engineering

**Script**: `src/analysis/compute_features_robust.py`

Calculate benchmark features (Difficulty, CV) and correlation metrics (Spearman ρ, Kendall τ, RBO) with bootstrap confidence intervals.

**Input**: Master table, metadata

**Output**: `results/analysis_ready_data.csv` - Dataset with all features and correlation metrics

**Execution**:
```bash
cd Human-SIG
uv run python src/analysis/compute_features_robust.py
```

---

## Step 6: Hypothesis Testing

**Script**: `src/analysis/small_n_hypothesis_test.py`

Execute statistical tests for H1-H6 using three correlation metrics (Spearman ρ, Kendall τ, RBO). Includes stratified analysis for H5 by task type.

**Input**: Analysis-ready data, metadata

**Output**: `results/hypothesis_test_results.json` - Raw test results with p-values and effect sizes

**Execution**:
```bash
cd Human-SIG
uv run python src/analysis/small_n_hypothesis_test.py
```

---

## Step 7: Multiple Comparison Correction

**Script**: `src/analysis/apply_correction.py`

Apply Holm-Bonferroni correction to control family-wise error rate.

**Input**: Hypothesis test results

**Output**: `results/statistical_significance_report.json` - Corrected p-values and significance flags

**Execution**:
```bash
cd Human-SIG
uv run python src/analysis/apply_correction.py
```

---

## Step 8: Generate Figures

**Script**: `src/analysis/generate_plots.py`

Generate 6 PDF figures for the manuscript. Logs data sources, plot types, and figure descriptions to console and log file.

**Input**: Analysis-ready data, master table (for Figure 5)

**Output**: 
*   `overleaf/images/Figure_1_Difficulty_Variance.pdf` - Difficulty (subset average score) (Easy -> Hard) vs. Spearman rho
*   `overleaf/images/Figure_2_Task_Type.pdf` - Spearman rho by Task Type
*   `overleaf/images/Figure_3a_Complexity_Categories.pdf` - Spearman rho by Prompt Length
*   `overleaf/images/Figure_3b_Variance_TaskType.pdf` - CV vs. Spearman rho by Task Type
*   `overleaf/images/Figure_4_Confounder_Heatmap.pdf` - Correlation Matrix of Independent Variables
*   `overleaf/images/Figure_5_Ranking_Comparison.pdf` - Comparison of large language model (LLM) ranking in SWE-Bench (Verified) and the overall ranking in LMArena-Coding
*   `results/plot_generation_log_YYYYMMDD_HHMMSS.txt` - Generation log with figure descriptions

**Execution**:
```bash
cd Human-SIG
uv run python src/analysis/generate_plots.py
```

---

## Step 9: Generate Tables

**Script**: `src/analysis/generate_tables.py`

Generate LaTeX tables for the manuscript using `pandas.DataFrame.to_latex()`.

**Input**: Statistical significance report, analysis-ready data (optional)

**Output**:
*   `overleaf/tables/results_table.tex` - Hypothesis test results summary
*   `overleaf/tables/correlation_summary_table.tex` - Correlation summary

**Execution**:
```bash
cd Human-SIG
uv run python src/analysis/generate_tables.py
```

---

## Complete Workflow

Run all analysis steps in sequence:

```bash
cd Human-SIG

# Step 4: Build Master Table
uv run python src/processing/build_master_table.py

# Step 5: Feature Engineering
uv run python src/analysis/compute_features_robust.py

# Step 6: Hypothesis Testing
uv run python src/analysis/small_n_hypothesis_test.py

# Step 7: Multiple Comparison Correction
uv run python src/analysis/apply_correction.py

# Step 8: Generate Figures
uv run python src/analysis/generate_plots.py

# Step 9: Generate Tables
uv run python src/analysis/generate_tables.py
```

---

## Output Files

**Data Files** (`results/`):
*   `data_overlap_stats.json` - Overlap statistics
*   `analysis_ready_data.csv` - Feature-engineered dataset
*   `hypothesis_test_results.json` - Raw test results
*   `statistical_significance_report.json` - Corrected results
*   `plot_generation_log_*.txt` - Plot generation logs

**Manuscript Files** (`overleaf/`):
*   `images/Figure_*.pdf` (6 figures)
*   `tables/*.tex` (2 tables)
