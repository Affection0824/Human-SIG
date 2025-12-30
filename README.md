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
│   │   │   └── {category}/    # e.g., coding, math
│   │   │       ├── input.txt  # Source HTML
│   │   │       └── data.csv   # Extracted data
│   │   ├── artificial_analysis/
│   │   │   ├── input.txt      # Unified table HTML
│   │   │   └── {benchmark}/
│   │   │       └── data.csv
│   │   ├── frontiermath/
│   │   │   └── {tier}/
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
*   **Preparation**: Copy the full table HTML from the Artificial Analysis website into `data/raw/artificial_analysis/input.txt`.
*   **Execution**:
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
*   **Preparation**: For each category (e.g., `coding`, `math`), copy the table HTML into the corresponding `input.txt`.
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
