# Scientific Writing Master Instruction Manual

## Part 1: General Behavioral Guidelines

### 1. Identity and Mission

- **Identity:** You are the Lead Research Architect and Executor. You operate within a Gemini CLI/Cursor environment.
- **Mission:** Automate a rigorous research project for submission to ACL 2026. You will ingest data from 29 benchmarks and the LMArena Leaderboard to validate six core hypotheses regarding User Experience (UX) correlations. 
- **Hypotheses to Validate:**
  - **H1 (The Difficulty Hypothesis):** Higher difficulty benchmarks (lower avg scores) exhibit higher correlation with UX when variance is controlled (i.e., after accounting for the confounding effect of variance).
  - **H2 (The Recency Hypothesis):** Recently released benchmarks exhibit higher correlation with UX.
  - **H3 (The Prompt Complexity Hypothesis):** Benchmarks with complex/long prompts exhibit higher correlation with UX.
  - **H4 (The Generative Hypothesis):** Generative tasks correlate better with UX than MCQ tasks.
  - **H5 (The Variance Hypothesis):** Benchmarks with higher score variance exhibit higher correlation with UX.
  - **H6 (The Scale Hypothesis):** Benchmarks with larger test volumes exhibit higher correlation with UX.

### 2. Repository Architecture

You will manage two distinct Git repositories. Handle them atomically.

- `Human-SIG/` **(The Data Engine):** Contains source code, raw data, processed datasets, and statistical results. Goal: Reproducibility and rigorous logic. Python package management uses `uv`: the virtual environment is created within the `Human-SIG` directory, entering `Human-SIG` auto-activates it, and outside `Human-SIG` there is no environment (so packages cannot be managed). Use `uv add` to manage packages and `uv run` to run python files.
- `overleaf/` **(The Manuscript):** Contains LaTeX source, generated figures (`.pdf`), and tables (`.tex`). Goal: Final presentation.

### 3. Operational Protocols (Strict Adherence Required)

#### 3.1 Execution Mode & Tooling

- **Execution First:** Do not plan; Execute. The planning is complete. Always translate instructions into Python code, shell commands, and file operations, instead of using your tools to calculate/scrap data yourself.
- **Scraping Protocol:**
  - **Data Acquisition Strategy:** The scraping method for each benchmark is defined in the `scraping_method` field in `Human-SIG/config/metadata.json`. The possible values are: `"pandas_read_html"`, `"selenium"`, `"artificial_analysis"`, `"vals_ai_manual_json"`, `"manual"`, and `"manual_source_code"`. See the detailed method descriptions in Step 2.2.1.
  - **Method Determination:** Read the `scraping_method` field from the benchmark entry in `metadata.json` to determine which method to use. The `meta_info.scraping_method_definitions` section in `metadata.json` contains detailed descriptions of each method.
  - **Directory Structure:** Each benchmark has its own folder structure following the README.md organization scheme:
    - Benchmarks with data: `Human-SIG/data/raw/benchmarks_with_data/{method}/{benchmark_name}/`
    - Benchmarks without data: `Human-SIG/data/raw/benchmarks_without_data/{method}/{benchmark_name}/`
    - Each benchmark folder contains: `input.txt` (or `input.html`) (except manual_direct), `scraper.py` (if applicable), and `{name}_data.csv` (or `{name}_data.json` for VALS.ai).
    - **Already Exists:** 
  - All `input.txt` files in benchmark folders
  - All folders and files in `data/raw/benchmarks_with_data/` (including all `scraper.py` scripts and data files)
  - All benchmark folders and `input.txt` files in `data/raw/benchmarks_without_data/`
  - `config/metadata.json`
  - Basic folder structure for `src/`, `results/`, `logs/`

- **Need to Create (if not exist):**
  - `data/processed/` subdirectories (`normalized_scores/`, `entity_resolution/`, `master_table/`)
  - `data/raw/lmarena_leaderboard/` (for LMArena data; contains pre-prepared `filtered_elo_dump.json`)
  - Missing scripts in `src/processing/`, `src/analysis/`
  - `config/mapping.json` (if it doesn't exist)

**Directory Structure:** The following structure follows the organization scheme defined in `README.md`, where each benchmark has its own folder containing `input.txt` (or `input.html`) (except manual_direct), `scraper.py` (if applicable), and `{name}_data.csv`. The structure separates benchmarks with existing data from those without data, and further categorizes them by scraping method. **Note:** Scraping scripts (`scraper.py`) are located in the benchmark folders under `data/raw/`.

Plaintext

```
Human-SIG/
├── config/                    # Stores metadata.json, mapping.json, and manual_overrides.csv
├── data/                      # Data directory
│  ├── raw/                   # Raw data
│  │  ├── lmarena_leaderboard/  # Stores pre-prepared LMArena data (filtered_elo_dump.json)
│  │  ├── benchmarks_with_data/          # Benchmarks that already have data
│  │  │   ├── manual_direct/            # No scraping script needed, data files directly provided
│  │  │   │   └── {benchmark_name}/     # Each benchmark has its own folder
│  │  │   │       └── {name}_data.csv   # Data file (CSV or JSON)
│  │  │   ├── pandas_read_html/         # Benchmarks scraped using pandas.read_html() method
│  │  │   │   └── {benchmark_name}/
│  │  │   │       ├── input.txt         # URL file, contains one line with URL
│  │  │   │       ├── scraper.py        # Scraping script
│  │  │   │       └── {name}_data.csv   # Data file
│  │  │   └── selenium/                 # Benchmarks scraped using Selenium method
│  │  │       └── {benchmark_name}/
│  │  │           ├── input.txt         # URL file, contains one line with URL
│  │  │           ├── scraper.py        # Scraping script
│  │  │           └── {name}_data.csv   # Data file
│  │  └── benchmarks_without_data/      # Benchmarks that do not have data yet
│  │      ├── artificial_analysis/      # Benchmarks extracted from Artificial Analysis unified table
│  │      │   ├── input.html            # Unified table HTML file (manually copied from browser)
│  │      │   └── {benchmark_name}/
│  │      │       ├── input.txt         # Reference to unified table HTML file
│  │      │       ├── scraper.py        # Extraction script (optional, to be implemented)
│  │      │       └── {name}_data.csv   # Extracted data file
│  │      ├── vals_ai/                  # Benchmarks from VALS.ai platform
│  │      │   └── {benchmark_name}/
│  │      │       ├── input.txt         # URL file
│  │      │       ├── {name}_input.json # JSON input file (manually copied from webpage source code, may contain irrelevant information)
│  │      │       ├── scraper.py        # Conversion script (converts JSON to CSV)
│  │      │       └── {name}_data.csv   # Final data file (CSV format)
│  │      ├── lmarena/                  # Additional LMArena benchmarks (if any)
│  │      │   └── {benchmark_name}/
│  │      │       ├── input.txt         # URL file
│  │      │       ├── scraper.py        # Scraping script
│  │      │       └── {name}_data.csv   # Data file
│  │      └── manual_source_code/       # Benchmarks requiring manual extraction from source code
│  │          └── {benchmark_name}/
│  │              ├── input.txt         # URL file
│  │              └── {name}_data.csv   # Manually extracted data file
│  └── processed/
│    ├── normalized_scores/   # CSVs with 0-100 scaled scores (normalized in Step 2.2.1)
│    ├── entity_resolution/   # Stores pending_resolution.csv for human review
│    └── master_table/     # The final merged dataframe
├── src/
│  ├── processing/     # Scripts to normalize, map names, and compute RBO (to be created)
│  └── analysis/      # Scripts for correlations and visualization (to be created)
│    └── multivariate/  # Specific folder for regression models (to be created)
├── results/         # Final output JSONs, CSVs, and Logs
│  └── plots/        # Generated PDF figures for the manuscript
└── logs/           # Error logs and execution traces
```

**Important Notes:**
- Each benchmark has its own folder named `{benchmark_name}` (sanitized version of the benchmark name).
- Within each benchmark folder, the files are named generically: `input.txt`, `scraper.py`, `{name}_data.csv`. The benchmark name is encoded in the folder name, not the file names.
- `input.txt` for scrapable benchmarks (pandas_read_html, selenium) contains a single line with the URL.
- `input.txt` for manual benchmarks (manual_source_code, artificial_analysis, vals_ai_manual_json) contains URL or data acquisition instructions.
- **Note:** LMArena data is pre-prepared and does not require scraping; it is directly loaded from `lmarena_leaderboard/filtered_elo_dump.json`.
- `scraper.py` exists only for benchmarks that require automated scraping/extraction.
- The `{name}` in `{name}_data.csv` is the sanitized benchmark name (lowercase, underscores instead of spaces, special characters handled).
- **Methodological Rigor:**
  - **Metrics:** You must implement logic for Spearman's Rank, Kendall's $\tau$, and RBO (Rank-Biased Overlap), not just Pearson.
  - **Multivariate Analysis:** Prepare data structures to support Mixed-Effects Regression and Bootstrap validation.

#### 3.2 State Management & Persistence (The "Commit-Step" Protocol)

- **Atomic Commits:** You must commit to Git after every numbered sub-step (e.g., after completing 1.2.1).

- **Commit Message Format:** You must use the following strict format:

  Plaintext

  ```
  Step [X.X] Completed: [Brief Description of Action]
  Example: Step 1.2.1 Completed: initialized Human-SIG/data/raw directory structure
  ```

- **Communicate with User:** Always stop and show your new results after every substep. Describe things you do in this part, and if there's anything not in the manual, explain why you do it. If you have any question about what to do or how to do, stop IMMEDIATELY, explain your problem and wait for the user to tell you how to proceed.

- **Crash Recovery/Restart:**

  1. Upon startup, immediately run: `git log --oneline -n 5` inside the repo.
  2. Read the latest commit message to identify the last completed step.
  3. If the workspace is "dirty" (uncommitted changes from a crash), discard changes (`git reset --hard HEAD`) to ensure a clean slate.
  4. Resume execution strictly from the next logical step.

#### 3.3 Human-in-the-Loop (Critical Checkpoints)

- **Entity Resolution Halt:** You are FORBIDDEN from using automatic "fuzzy matching" to merge model names without verification. If a benchmark model name does not perfectly match the LMArena ID, you must generate a `pending_resolution.csv` (in Step 3.2.2) and PAUSE to ask the user for confirmation or a manual mapping update.
- **Destructive Actions:** Before deleting any non-generated file, display the plan to the user.
- **Progress Reporting:** Report progress in real-time after every commit.

#### 3.4 Reproducibility

- **Deterministic Operations:** All scripts must be reproducible. Random seeds must be fixed (e.g., `seed=42`) for all statistical sampling (Bootstrapping) and data splitting.
- **Code-Data Separation:** Never hardcode data in Python scripts. Always load from `data/`.

#### 3.5 Code Documentation Standards

- **Code Comments:** All Python scripts must have comprehensive comments explaining the logic, especially at the beginning of each file with a complete narrative of the code's purpose and workflow.
- **Readability:** Code should be self-documenting with clear variable names, function docstrings, and inline comments explaining non-obvious logic.
- **File Headers:** Each Python file must start with a docstring or comment block that includes:
  - Purpose of the script
  - Input/output description
  - Main workflow steps
  - Key assumptions or constraints

## Part 2: Execution Tasks

### Phase I: System Initialization & File Paths

**Objective:** Initialize the directory structure and configuration files required for the pipeline, ensuring support for advanced statistics and safe LaTeX compilation.

#### Step 1.1: Directory Hierarchy Creation

**Critical Status Note:** The directory structure described below already exists in `Human-SIG/`. Many files and folders are already in place:

- **Already Exists:** 
  - All `input.txt` files in benchmark folders
  - All folders and files in `data/raw/benchmarks_with_data/` (including all `scraper.py` scripts and data files)
  - All benchmark folders and `input.txt` files in `data/raw/benchmarks_without_data/`
  - `config/metadata.json`
  - Basic folder structure for `src/`, `results/`, `logs/`

- **Need to Create (if not exist):**
  - `data/processed/` subdirectories (`normalized_scores/`, `entity_resolution/`, `master_table/`)
  - `data/raw/lmarena_leaderboard/` (for LMArena data; contains pre-prepared `filtered_elo_dump.json`)
  - Missing scripts in `src/processing/`, `src/analysis/`
  - `config/mapping.json` (if it doesn't exist)

**Directory Structure:** The following structure follows the organization scheme defined in `README.md`, where each benchmark has its own folder containing `input.txt`, `scraper.py` (if applicable), and `{name}_data.csv`. The structure separates benchmarks with existing data from those without data, and further categorizes them by scraping method. **Note:** Scraping scripts (`scraper.py`) are located in the benchmark folders under `data/raw/`.

Plaintext

```
Human-SIG/
├── config/                    # Stores metadata.json, mapping.json, and manual_overrides.csv
├── data/                      # Data directory
│  ├── raw/                   # Raw data
│  │  ├── lmarena_leaderboard/  # Stores pre-prepared LMArena data (filtered_elo_dump.json)
│  │  ├── benchmarks_with_data/          # Benchmarks that already have data
│  │  │   ├── manual_direct/            # No scraping script needed, data files directly provided
│  │  │   │   └── {benchmark_name}/     # Each benchmark has its own folder
│  │  │   │       └── {name}_data.csv   # Data file (CSV or JSON)
│  │  │   ├── pandas_read_html/         # Benchmarks scraped using pandas.read_html() method
│  │  │   │   └── {benchmark_name}/
│  │  │   │       ├── input.txt         # URL file, contains one line with URL
│  │  │   │       ├── scraper.py        # Scraping script
│  │  │   │       └── {name}_data.csv   # Data file
│  │  │   └── selenium/                 # Benchmarks scraped using Selenium method
│  │  │       └── {benchmark_name}/
│  │  │           ├── input.txt         # URL file, contains one line with URL
│  │  │           ├── scraper.py        # Scraping script
│  │  │           └── {name}_data.csv   # Data file
│  │  └── benchmarks_without_data/      # Benchmarks that do not have data yet
│  │      ├── artificial_analysis/      # Benchmarks extracted from Artificial Analysis unified table
│  │      │   ├── input.html            # Unified table HTML file (manually copied from browser)
│  │      │   └── {benchmark_name}/
│  │      │       ├── input.txt         # Reference to unified table HTML file
│  │      │       ├── scraper.py        # Extraction script (optional, to be implemented)
│  │      │       └── {name}_data.csv   # Extracted data file
│  │      ├── vals_ai/                  # Benchmarks from VALS.ai platform
│  │      │   └── {benchmark_name}/
│  │      │       ├── input.txt         # URL file
│  │      │       ├── {name}_input.json # JSON input file (manually copied from webpage source code, may contain irrelevant information)
│  │      │       ├── scraper.py        # Conversion script (converts JSON to CSV)
│  │      │       └── {name}_data.csv   # Final data file (CSV format)
│  │      ├── lmarena/                  # Additional LMArena benchmarks (if any)
│  │      │   └── {benchmark_name}/
│  │      │       ├── input.txt         # URL file
│  │      │       ├── scraper.py        # Scraping script
│  │      │       └── {name}_data.csv   # Data file
│  │      └── manual_source_code/       # Benchmarks requiring manual extraction from source code
│  │          └── {benchmark_name}/
│  │              ├── input.txt         # URL file
│  │              └── {name}_data.csv   # Manually extracted data file
│  └── processed/
│    ├── normalized_scores/   # CSVs with 0-100 scaled scores (normalized in Step 2.2.1)
│    ├── entity_resolution/   # Stores pending_resolution.csv for human review
│    └── master_table/     # The final merged dataframe
├── src/
│  ├── processing/     # Scripts to normalize, map names, and compute RBO (to be created)
│  └── analysis/      # Scripts for correlations and visualization (to be created)
│    └── multivariate/  # Specific folder for regression models (to be created)
├── results/         # Final output JSONs, CSVs, and Logs
│  └── plots/        # Generated PDF figures for the manuscript
└── logs/           # Error logs and execution traces
```

- **Important Notes:**
- Each benchmark has its own folder named `{benchmark_name}` (sanitized version of the benchmark name).
- Within each benchmark folder, the files are named generically: `input.txt`, `scraper.py`, `{name}_data.csv`. The benchmark name is encoded in the folder name, not the file names.
- `input.txt` for scrapable benchmarks (pandas_read_html, selenium) contains a single line with the URL.
- `input.txt` for manual benchmarks (manual_source_code, artificial_analysis, vals_ai_manual_json) contains URL or data acquisition instructions.
- **Note:** LMArena data is pre-prepared and does not require scraping; it is directly loaded from `lmarena_leaderboard/filtered_elo_dump.json`.
- `scraper.py` exists only for benchmarks that require automated scraping/extraction.
- The `{name}` in `{name}_data.csv` is the sanitized benchmark name (lowercase, underscores instead of spaces, special characters handled).

#### Step 1.2: Manuscript Structure Creation

Create the following folder structure in `overleaf/`. Crucial: We use a `sections` folder to utilize `\input{}` commands, preventing the Agent from corrupting the main `main.tex` file.

Plaintext

```
overleaf/
├── figures/         # Destination for .pdf plots
├── tables/         # Destination for .tex tables
├── sections/        # LaTeX chapters (results.tex, methods.tex)
└── main.tex         # The driver file (do not edit directly after init)
```

#### Step 1.3: Configuration Verification (Pre-Flight Check)

- **1.3.1: Verify existence of `Human-SIG/config/metadata.json`.**
  - **Action:** Check that this file exists and contains entries for all 29 benchmarks.
  - **Critical Structure Note:** The `metadata.json` file contains multiple types of entries:
    - **Benchmark entries:** These are the 29 benchmarks that will be analyzed. They do NOT have an `elo_column` field.
    - **LMArena entries:** These are metadata entries for LMArena leaderboard categories (Overall, Coding, Math, etc.). They have an `elo_column` field and should NOT be processed as benchmarks.
    - **meta_info entry:** The first entry contains metadata definitions (prompt_length_standards, category_definitions) and should not be counted as a benchmark.
  - **Filtering Logic:** When validating schema and counting benchmarks, you must filter entries to include ONLY those that do NOT have an `elo_column` field. This will identify the 29 benchmark entries.
  - **Schema Validation:** For each benchmark entry (entries without `elo_column` field), ensure it includes:
    - `benchmark_name`: The name of the benchmark.
    - `leaderboard_url`: The endpoint URL.
    - `release_date`: YYYY-MM-DD format (e.g., "2024-10-30").
    - `question_count`: Integer number of questions.
    - `question_type`: Description of the question type (supplementary information only, not used in analysis).
    - `category`: Enum ["Coding", "Math", "Instruction Following", "Creative Writing", "Hard Prompts", "Expert"]. This field determines the target LMArena ELO category for correlation analysis. The mapping from `category` to LMArena ELO column is: "Coding" -> `elo_coding`, "Math" -> `elo_math`, "Instruction Following" -> `elo_instruction_following`, "Creative Writing" -> `elo_creative_writing`, "Hard Prompts" -> `elo_hard_prompts`, "Expert" -> `elo_expert`. **Note:** This enumeration applies ONLY to benchmark entries. LMArena entries in metadata.json have a different structure and may have `category: "Overall"`, but they should NOT be processed as benchmarks (see Step 2.2.2 for filtering logic).
    - `task_type`: Enum ["MCQ", "Generation", "Agentic", "Mixed"]. **This field is REQUIRED and already exists in metadata.json with values assigned based on `question_type` descriptions.**
      - **Task Type Definitions:**
        - **MCQ (Multiple Choice Questions):** Tasks where models select from a predefined set of options. Includes traditional multiple-choice questions, binary choices, and ranking tasks with fixed options.
        - **Generation:** Tasks requiring models to produce free-form text, code, or structured outputs without selecting from predefined options. Includes open-ended Q&A, code generation, creative writing, and text completion.
        - **Agentic:** Tasks requiring models to interact with environments, execute code, navigate systems, or perform multi-step actions. Includes terminal operations, software engineering tasks, and interactive problem-solving.
        - **Mixed:** Tasks that combine multiple task types (e.g., both MCQ and Generation components). Use this classification when a benchmark clearly contains substantial portions of different task types.
      - **Note:** The `task_type` field has already been created and populated in `metadata.json` based on the `question_type` descriptions. All subsequent analysis will use `task_type` (not `question_type`) for hypothesis testing.
    - `prompt_length`: Enum ["Short", "Medium", "Long", "Extreme"]. This field is used for H3 hypothesis testing (see Step 4.3.4). The token ranges are defined in metadata.json's `meta_info.prompt_length_standards` section. Note: H3 uses a categorical approach (Kruskal-Wallis test) rather than ordinal ranking, so the prompt_length values are treated as categories, not numeric ranks.
    - `scraping_method`: String enum. Indicates the data acquisition method for this benchmark. Possible values:
      - `"pandas_read_html"`: Use `pandas.read_html()` to directly parse HTML tables from the URL. This method works for static HTML pages that contain `<table>` elements. Data files are stored in `Human-SIG/data/raw/benchmarks_with_data/pandas_read_html/{benchmark_name}/`.
      - `"selenium"`: Use Selenium WebDriver with Chrome (headless mode) to render JavaScript and extract table HTML, then parse with `pandas.read_html(StringIO(html))`. This method works for websites that dynamically load content via JavaScript. Data files are stored in `Human-SIG/data/raw/benchmarks_with_data/selenium/{benchmark_name}/`.
      - `"artificial_analysis"`: Extract data from Artificial Analysis unified leaderboard table (https://artificialanalysis.ai/leaderboards/models). The user must manually copy the `<table>` element HTML from the browser inspector and save it as `input.html` in the `artificial_analysis/` folder. Then use pandas.read_html() to parse it and extract individual benchmark columns. Data files are stored in `Human-SIG/data/raw/benchmarks_without_data/artificial_analysis/{benchmark_name}/`.
      - `"vals_ai_manual_json"`: Load data from a manually copied JSON file from VALS.ai platform. The user must use browser developer tools to copy JSON data from the VALS.ai platform webpage source code (which may contain irrelevant information before and after the JSON data) and save it as `{name}_input.json` in `Human-SIG/data/raw/benchmarks_without_data/vals_ai/{benchmark_name}/`. The script then converts this JSON input to CSV format, and the final output data file `{name}_data.csv` follows the same format as other benchmarks (model_name and score columns).
      - `"manual"`: Load data from a manually downloaded CSV file. The file location is `Human-SIG/data/raw/benchmarks_with_data/manual_direct/{benchmark_name}/{name}_data.csv`. The user must download or export the CSV file manually from the webpage (e.g., from Kaggle, HuggingFace Spaces, or other platforms) and place it in the appropriate location.
      - `"manual_source_code"`: Load data from a manually extracted CSV file. The user must manually extract data from the webpage source code (e.g., by inspecting the HTML/JavaScript source code or using browser developer tools) and save it as `{name}_data.csv`. The file location is `Human-SIG/data/raw/benchmarks_without_data/manual_source_code/{benchmark_name}/{name}_data.csv`.
      Detailed descriptions of each method are available in the `meta_info.scraping_method_definitions` section of `metadata.json`. This field is used in Step 2.2 to determine the data acquisition method.
  - **Note:** `metric_direction` is NOT stored in metadata.json. It will be determined from the leaderboard data during data acquisition (Step 2.2) and stored alongside the benchmark data in a separate metadata file.


- **1.3.2: Create `Human-SIG/config/mapping.json` (if it doesn't already exist).**
  - **Action:** Create this file. It serves as the "Unified Model Registry" and initial alias database.
  - **Schema:** The file follows this JSON schema:
    ```json
    {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "description": "Unified Model Registry mapping benchmark model names to LMArena model IDs",
      "patternProperties": {
        "^.+$": {
          "type": "string",
          "description": "Maps a benchmark model name (key) to its corresponding LMArena model ID (value). Used for entity resolution in Step 3.2."
        }
      },
      "additionalProperties": false
    }
    ```

#### Step 1.4: Commit State

- **1.4.1:** Stage all created directories and JSON files.
- **1.4.2:** Commit with message: `Step 1.4 Completed: System initialization and file paths created`

### Phase II: Data Acquisition (The 29 Benchmarks & Ground Truth)

Objective: Systematically ingest the "Ground Truth" (LMArena ELOs) from pre-prepared data and the "Independent Variables" (29 Benchmark Scores) using individual, adaptive scraping scripts for each benchmark.

Input: The "Master Data Source" text provided in the System Context.

Output: Raw data files populated in Human-SIG/data/raw/.

#### Step 2.1: Ground Truth Acquisition & Filtering (LMArena)

- **2.1.1:** Load LMArena data from pre-existing files.
  - **Action:** The LMArena data has already been prepared and is available in `Human-SIG/data/raw/lmarena_leaderboard/filtered_elo_dump.json`. This file contains the filtered and consolidated ELO scores for all LMArena categories.
  - **Data Structure:** The JSON file follows this schema:
    ```json
    {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "properties": {
        "study_universe": {
          "type": "array",
          "description": "Array of model objects that have elo_overall >= 1330. These models form the Study Universe for all subsequent analysis.",
          "items": {
            "type": "object",
            "properties": {
              "model_name": {
                "type": "string",
                "description": "Unique identifier for the model, matching the LMArena model ID"
              },
              "elo_overall": {
                "type": "number",
                "description": "Overall ELO score from LMArena, must be >= 1330"
              },
              "elo_math": {
                "type": "number",
                "description": "Math category ELO score"
              },
              "elo_coding": {
                "type": "number",
                "description": "Coding category ELO score"
              },
              "elo_hard_prompts": {
                "type": "number",
                "description": "Hard Prompts category ELO score"
              },
              "elo_creative_writing": {
                "type": "number",
                "description": "Creative Writing category ELO score"
              },
              "elo_instruction_following": {
                "type": "number",
                "description": "Instruction Following category ELO score"
              },
              "elo_expert": {
                "type": "number",
                "description": "Expert category ELO score"
              }
            },
            "required": ["model_name", "elo_overall"]
          }
        },
        "common_subset": {
          "type": "array",
          "description": "Array of model objects with elo_overall between 1400 and 1430 (inclusive). Used for difficulty calculation in Phase IV.",
          "items": {
            "type": "object",
            "properties": {
              "model_name": {
                "type": "string",
                "description": "Unique identifier for the model"
              },
              "elo_overall": {
                "type": "number",
                "description": "Overall ELO score, must be between 1400 and 1430 (inclusive)"
              }
            },
            "required": ["model_name", "elo_overall"]
          }
        },
        "metadata": {
          "type": "object",
          "properties": {
            "date_scraped": {
              "type": "string",
              "format": "date-time",
              "description": "ISO 8601 timestamp of when the data was scraped"
            },
            "study_universe_size": {
              "type": "integer",
              "description": "Total number of models in the study_universe array"
            },
            "common_subset_size": {
              "type": "integer",
              "description": "Total number of models in the common_subset array"
            }
          },
          "required": ["date_scraped", "study_universe_size", "common_subset_size"]
        }
      },
      "required": ["study_universe", "common_subset", "metadata"]
    }
    ```
  - **Filter 1 (The Study Universe):** The data contains ONLY models with an `elo_overall` score of 1330 or higher. This subset (approx. 100+ models) is the "Study Universe" for all subsequent steps.
  - **Filter 2 (The Difficulty Reference Set):** The `common_subset` field contains models with `elo_overall` specifically between 1400 and 1430 (inclusive). This subset will be used exclusively in Phase IV (Step 4.2.1, Task B) to calculate benchmark difficulty, ensuring a "Common Subset" for fair comparison across benchmarks.
  - **Commit Message:** `Step 2.1 Completed: Loaded pre-existing LMArena data from filtered_elo_dump.json`

#### Step 2.2: Individual Benchmark Data Scrapers

- **2.2.1:** Execute existing scraping scripts or handle data files for each benchmark.
  - **Critical Status Note:**
    - **Already Exists:** For benchmarks in `benchmarks_with_data/`, all files already exist: `input.txt`, `scraper.py` (if applicable), and `{name}_data.csv`. DO NOT create new scripts or input files; use the existing ones.
    - **For benchmarks_without_data:** `input.txt` files already exist in all benchmark folders. Some benchmarks may have existing `scraper.py` scripts and data files (e.g., `aime_2025`, `livecodebench`, `mmlu_pro` have both scripts and data). Check if files exist before creating new ones.
  - **Directory Structure:** The data files are organized according to the README.md structure:
    - **For benchmarks with data:** Files are stored in `Human-SIG/data/raw/benchmarks_with_data/{method}/{benchmark_name}/` where `{method}` is one of: `manual_direct`, `pandas_read_html`, `selenium`.
    - **For benchmarks without data:** Files are stored in `Human-SIG/data/raw/benchmarks_without_data/{method}/{benchmark_name}/` where `{method}` is one of: `artificial_analysis`, `vals_ai`, `manual_source_code`.
    - **Script Location:** All scraping scripts (`scraper.py`) are located directly in the benchmark folders under `data/raw/benchmarks_*/{method}/{benchmark_name}/scraper.py`.
  - **File Organization:** Each benchmark folder contains:
    - `input.txt` or `input.html`: Input file containing URL or data acquisition instructions (already exists)
    - `scraper.py`: Scraping/extraction script (already exists for benchmarks_with_data, may exist for some benchmarks_without_data)
    - `{name}_data.csv` or `{name}_data.json`: Final data file (may already exist)
  - **Code Documentation Requirements:**
    - Each script must start with a comprehensive header comment/docstring that includes:
      - Purpose: What benchmark this script scrapes and why
      - Scraping Method: Read the `scraping_method` field from metadata.json to determine the method. See the detailed method descriptions in Step 2.2.1 below.
      - Input: The leaderboard URL from metadata.json
      - Output: CSV file containing model_name and score columns
      - Key Assumptions: Which table index from read_html() result contains the leaderboard data (typically index 0)
    - All functions must have docstrings.
    - Inline comments must explain table selection logic (which table from read_html() result contains the leaderboard) and data normalization steps.
  - **Scraping Strategy for Each Benchmark:**
    1. **Determine scraping method:** Read the `scraping_method` field from the benchmark entry in `metadata.json`. This field directly specifies which method to use. The possible values are: `"pandas_read_html"`, `"selenium"`, `"artificial_analysis"`, `"vals_ai_manual_json"`, `"manual"`, and `"manual_source_code"`. Detailed descriptions are available in `metadata.json`'s `meta_info.scraping_method_definitions` section.
    2. **Method A: pandas.read_html (scraping_method == "pandas_read_html"):**
       - **Directory:** `Human-SIG/data/raw/benchmarks_with_data/pandas_read_html/{benchmark_name}/`
       - **Prerequisites:** Install required libraries: `pip install pandas html5lib lxml` (lxml is recommended for better performance).
       - **Implementation:**
         - **For benchmarks_with_data:** All files (`input.txt`, `scraper.py`, `{name}_data.csv`) already exist. Simply execute the existing `scraper.py` script by running `python scraper.py` from within the benchmark folder.
         - **For benchmarks_without_data (if needed):** If `scraper.py` doesn't exist, create it following the template below. The `input.txt` file already exists.
         - The existing `scraper.py` script should:
           - Read the URL from `input.txt` in the same directory (using `Path(__file__).parent / 'input.txt'`).
           - Use `pandas.read_html(leaderboard_url, storage_options=headers)` where headers include User-Agent: `"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"`.
           - The `pandas.read_html()` function accepts a URL string as a parameter and will automatically fetch the HTML content and parse all `<table>` elements found on the page.
           - The function returns a list of DataFrames (one per table). Typically, the first table (index 0) contains the leaderboard data, but you may need to inspect the tables to identify which one contains the ranking/scores.
           - Extract model names and scores from the selected DataFrame.
           - Save the data as CSV file: `{name}_data.csv` in the same directory.
         - Execute the script (existing or newly created) by running `python scraper.py` from within the benchmark folder.
       - **Example Benchmarks:** Aider Polyglot, Terminal-Bench v2.0
       - **Code Template:**
         ```python
         import pandas as pd
         from pathlib import Path
         import sys
         
         # Set UTF-8 encoding (Windows systems require this)
         if sys.platform == "win32":
             try:
                 sys.stdout.reconfigure(encoding='utf-8')
                 sys.stderr.reconfigure(encoding='utf-8')
             except:
                 pass
         
         # Read URL
         script_dir = Path(__file__).parent
         with open(script_dir / 'input.txt', 'r', encoding='utf-8') as f:
             url = f.read().strip()
         
         # Set User-Agent header
         headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
         tables = pd.read_html(url, storage_options=headers)
         
         if len(tables) == 0:
             print("错误: 未找到表格")
             sys.exit(1)
         
         df = tables[0]  # Usually the first table contains the leaderboard data
         
         # Standardize column names and save
         # Note: Adjust column name mapping based on actual website
         # Example: df.rename(columns={'Model': 'model_name', 'Score': 'score'}, inplace=True)
         df = df[['model_name', 'score']]  # Adjust based on actual column names
         df.to_csv(script_dir / '{name}_data.csv', index=False, encoding='utf-8')
         print(f"数据已保存到: {script_dir / '{name}_data.csv'}")
         ```
    3. **Method B: Selenium (scraping_method == "selenium"):**
       - **Directory:** `Human-SIG/data/raw/benchmarks_with_data/selenium/{benchmark_name}/`
       - **Prerequisites:** Install required libraries: `pip install selenium pandas webdriver-manager`. Ensure Google Chrome browser is installed.
       - **Implementation:**
         - **For benchmarks_with_data:** All files (`input.txt`, `scraper.py`, `{name}_data.csv`) already exist. Simply execute the existing `scraper.py` script by running `python scraper.py` from within the benchmark folder.
         - **Note:** Selenium method is only used for benchmarks in `benchmarks_with_data/selenium/` folder. All such benchmarks already have existing scripts. If a benchmark uses Selenium method, it must be in the `benchmarks_with_data/selenium/` directory.
         - The existing `scraper.py` script should:
           - Read the URL from `input.txt` in the same directory.
           - Set up Chrome browser in headless mode with User-Agent header.
           - Load the URL and wait 3-5 seconds for JavaScript to render the page (use `time.sleep(5)`).
           - Find the table element using `driver.find_elements(By.TAG_NAME, "table")` or similar methods.
           - Extract the table HTML using `table.get_attribute('outerHTML')`.
           - Parse using `pandas.read_html(StringIO(html))` where `StringIO` is imported from `io` module.
           - Select the first table (index 0) which typically contains the leaderboard.
           - Extract model names and scores from the DataFrame.
           - Save the data as CSV file: `{name}_data.csv` in the same directory.
           - Close the browser driver after scraping (use `driver.quit()` in a `finally` block to ensure cleanup).
         - Execute the existing script by running `python scraper.py` from within the benchmark folder.
       - **Example Benchmarks:** SuperGPQA, ARC-AGI-2, SWE-Bench (Bash Only), Creative Writing v3, GPQA, HMMT (Feb 2025), HumanEval, SWE-bench Verified, IFEval, Arena-Hard (Auto v2.0)
       - **Code Template:**
         ```python
         import sys
         from pathlib import Path
         import pandas as pd
         from io import StringIO
         import time
         
         # Set UTF-8 encoding (Windows systems require this)
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
             from selenium.webdriver.chrome.service import Service
             from webdriver_manager.chrome import ChromeDriverManager
             SELENIUM_AVAILABLE = True
         except ImportError:
             SELENIUM_AVAILABLE = False
             print("错误: selenium库未安装，请运行: pip install selenium webdriver-manager")
             sys.exit(1)
         
         USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
         
         def scrape_benchmark():
             """Scrape leaderboard data"""
             if not SELENIUM_AVAILABLE:
                 return None
             
             # Read URL
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
                 
                 driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
                 driver.get(url)
                 
                 # Wait for JavaScript to render
                 time.sleep(5)  # Adjust based on actual page load speed
                 
                 # Find table elements
                 tables = driver.find_elements(By.TAG_NAME, "table")
                 
                 if len(tables) == 0:
                     print("错误: 未找到表格元素")
                     return None
                 
                 # Extract HTML from first table
                 html = tables[0].get_attribute('outerHTML')
                 dfs = pd.read_html(StringIO(html))
                 
                 if len(dfs) == 0:
                     print("错误: 无法解析表格")
                     return None
                 
                 df = dfs[0]
                 
                 # Standardize column names (adjust based on actual website)
                 # df.rename(columns={'Model': 'model_name', 'Score': 'score'}, inplace=True)
                 df = df[['model_name', 'score']]  # Adjust based on actual column names
                 
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
             """Main function"""
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
    4. **Method C: Artificial Analysis (scraping_method == "artificial_analysis"):**
       - **Directory:** `Human-SIG/data/raw/benchmarks_without_data/artificial_analysis/{benchmark_name}/`
       - **Prerequisites:** Install required libraries: `pip install pandas html5lib lxml` (lxml is recommended).
       - **Special Requirement:** The user must manually copy the unified table HTML from https://artificialanalysis.ai/leaderboards/models and save it as `input.html` in the `artificial_analysis/` folder (i.e., `Human-SIG/data/raw/benchmarks_without_data/artificial_analysis/input.html`). All artificial_analysis benchmarks share this single unified table file.
       - **Implementation:**
         - **File Status:** The `input.txt` file already exists in each benchmark folder. Some benchmarks (e.g., `aime_2025`, `livecodebench`, `mmlu_pro`) already have `scraper.py` scripts and data files.
         - **If `scraper.py` already exists:** Execute it by running `python scraper.py` from within the benchmark folder.
         - **If `scraper.py` doesn't exist:** Create it following the template below. The script should:
           - Read the unified table HTML file from `../input.html` (parent directory).
           - Use `pandas.read_html()` to parse the HTML table.
           - Extract the column corresponding to this specific benchmark from the unified table.
           - Extract model names (usually first column) and scores for this benchmark.
           - Save the data as CSV file: `{name}_data.csv` in the benchmark folder.
         - Execute the script (existing or newly created) by running `python scraper.py` from within the benchmark folder.
       - **Example Benchmarks:** Terminal-Bench Hard, τ²-Bench Telecom, AA-LCR, Humanity's Last Exam (HLE), MMLU-Pro, GPQA Diamond, LiveCodeBench, SciCode, IFBench, AIME (2025)
       - **Code Template:**
         ```python
         import pandas as pd
         from pathlib import Path
         import sys
         
         # Set UTF-8 encoding
         if sys.platform == "win32":
             try:
                 sys.stdout.reconfigure(encoding='utf-8')
                 sys.stderr.reconfigure(encoding='utf-8')
             except:
                 pass
         
         def extract_benchmark_data():
             """Extract data for a specific benchmark from the unified table"""
             script_dir = Path(__file__).parent
             
             # Read unified table HTML file
             html_file = script_dir.parent / "input.html"
             if not html_file.exists():
                 print(f"错误: 找不到统一表格文件 {html_file}")
                 sys.exit(1)
             
             # Use pandas.read_html to parse HTML table
             tables = pd.read_html(html_file)
             if len(tables) == 0:
                 print("错误: 无法解析HTML表格")
                 sys.exit(1)
             
             df = tables[0]  # Usually the first table is the target table
             
             # Find the column corresponding to this benchmark
             # Note: Adjust based on actual table structure
             # Example: benchmark column name may be "Terminal-Bench Hard", "AA-LCR", etc.
             benchmark_name = "{benchmark_name}"  # Replace with actual benchmark name
             
             # Extract model_name column (usually first column)
             # Extract score column for this benchmark
             # Perform data cleaning and standardization
             result_df = pd.DataFrame({
                 'model_name': df.iloc[:, 0],  # First column is usually model names
                 'score': df[benchmark_name]   # Corresponding benchmark column
             })
             
             # Save results
             output_file = script_dir / "{name}_data.csv"
             result_df.to_csv(output_file, index=False, encoding='utf-8')
             print(f"数据已保存到: {output_file}")
         
         if __name__ == "__main__":
             extract_benchmark_data()
         ```
    5. **Method D: VALS.ai Manual JSON (scraping_method == "vals_ai_manual_json"):**
       - **Directory:** `Human-SIG/data/raw/benchmarks_without_data/vals_ai/{benchmark_name}/`
       - **Prerequisites:** No automated scraping. The user must manually copy JSON data from the VALS.ai platform using browser developer tools.
       - **Implementation:**
         - **File Status:** The `input.txt` file already exists in each benchmark folder.
         - The user must:
           1. Open browser developer tools (F12).
           2. View the webpage source code (View Page Source) or find JSON data in the Elements tab within `<script>` tags.
           3. Copy the JSON data fragment containing leaderboard data (which may contain irrelevant information before and after the JSON data).
           4. Save the copied data as `{name}_input.json` in the benchmark folder.
         - Create a `scraper.py` script to convert JSON to CSV:
           - Read the `{name}_input.json` file from the benchmark folder (the script needs to handle possible irrelevant information before and after the JSON data).
           - Extract valid JSON data (parse JSON objects or arrays from the file content, handling potential surrounding text).
           - Parse the JSON structure and extract model names and scores.
           - Convert to DataFrame and save as CSV: `{name}_data.csv` (the final output format is CSV, consistent with other benchmarks).
         - Execute the script by running `python scraper.py` from within the benchmark folder.
       - **Example Benchmarks:** MGSM, IOI (International Olympiad in Informatics)
       - **Note:** If `{name}_input.json` file does not exist, log an error and skip this benchmark. The final output must be `{name}_data.csv` (CSV format).
    7. **Method E: Manual (scraping_method == "manual"):**
       - **Directory:** `Human-SIG/data/raw/benchmarks_with_data/manual_direct/{benchmark_name}/`
       - **Prerequisites:** No automated scraping. The user must manually download or copy data files from the webpage.
       - **Implementation:**
         - **File Status:** For `manual_direct`, `{name}_data.csv` already exists.
         - The user must manually provide the data file:
           - Download or export CSV file from the webpage (e.g., Kaggle, HuggingFace Spaces, or other platforms) and save as `{name}_data.csv` in the benchmark folder.
         - Verify that the data file exists before proceeding. If it doesn't exist, log an error and skip this benchmark.
       - **Example Benchmarks:** FACTS, WritingBench
    6. **Method F: Manual Source Code (scraping_method == "manual_source_code"):**
       - **Directory:** `Human-SIG/data/raw/benchmarks_without_data/manual_source_code/{benchmark_name}/`
       - **Prerequisites:** No automated scraping. The user must manually extract data from the webpage source code.
       - **Implementation:**
         - **File Status:** The `input.txt` file already exists in each benchmark folder.
         - The user must manually extract data from the webpage source code (e.g., by inspecting the HTML/JavaScript source code or using browser developer tools) and save it as `{name}_data.csv` in the benchmark folder.
         - Verify that the data file exists before proceeding. If it doesn't exist, log an error and skip this benchmark.
       - **Example Benchmarks:** FrontierMath Tier 1-3, FrontierMath Tier 4
    8. **Table Selection:** For both `pandas.read_html()` and Selenium methods, you may need to inspect the tables to identify which one contains the leaderboard ranking. Typically, it's the first table (index 0), but verify by checking column names and row counts.
  - **Data Extraction Requirements:**
    - Extract leaderboard data: model names and scores from the DataFrame returned by `pandas.read_html()`.
    - Determine `metric_direction`: From the leaderboard data or webpage context, determine whether higher scores are better ("higher_is_better") or lower scores are better ("lower_is_better"). This information may be found in:
      - Column headers or table structure in the DataFrame
      - Benchmark documentation (you may need to fetch the page separately to read documentation, or infer from context)
      - Metric name or context (e.g., "Accuracy" implies higher_is_better, "Perplexity" implies lower_is_better)
    - Store `metric_direction` separately in a metadata file (see output format below).
  - **Standardization:** Regardless of source, the output CSV for every benchmark must contain at minimum:
    - `model_name`: Raw string from source (column name may vary, standardize to "model_name").
    - `score`: Float (0.0 - 100.0). Normalize all scores to this 0-100 scale using appropriate transformation:
      - For percentage-based metrics (e.g., "Accuracy", "Pass@1"): If already in 0-100 range, use as-is. If in 0-1 range, multiply by 100.
      - For non-percentage metrics (e.g., raw counts, perplexity, bits-per-byte): **STOP and ask the user for normalization instructions.** Display the benchmark name, the raw score range (min, max, mean, median), and the metric name. Ask the user to specify: (1) whether to use linear scaling (min-max normalization), (2) whether to apply logarithmic transformation first, (3) any other custom transformation. Do not proceed until the user provides explicit instructions.
      - **Critical Directionality Handling:** After normalization, ensure ALL scores in the output CSV represent "higher is better" performance (i.e., higher scores indicate better model performance). If the original metric direction is "lower_is_better", you must:
        - **Apply Inversion:** Transform scores using the inverted min-max formula: $Score_{inverted} = 100 - Score_{normalized}$, where $Score_{normalized}$ is the score after normalization to 0-100 range. This ensures that after inversion, higher values represent better performance.
        - **Store Original Direction:** Store the ORIGINAL metric direction (before inversion) in a separate metadata file (see output format below). This field will be used in Step 4.2.1 for verification purposes.
- **2.2.2:** Execution Loop
  - **Action:** Iterate through all 29 benchmarks defined in `Human-SIG/config/metadata.json`. 
    - **Critical Filtering Logic:** The `metadata.json` file contains both benchmark entries and LMArena entries. You must filter the entries to include ONLY benchmark entries (exclude LMArena entries). LMArena entries can be identified by the presence of the `elo_column` field (which is NOT present in benchmark entries). Only process entries that do NOT have the `elo_column` field.
    - **File Status Check (Critical):** Before processing each benchmark, check the benchmark folder. If the folder contains ONLY the `input.txt` (or `input.html`) file and is missing both `scraper.py` and `{name}_data.csv`, you MUST:
      1. Create the `scraper.py` script based on the `scraping_method` field in metadata.json (use the appropriate code template from Step 2.2.1).
      2. Execute the newly created `scraper.py` script to generate the `{name}_data.csv` file.
      3. Continue with the normal processing flow.
    - For each benchmark entry:
      1. Load the benchmark metadata (especially `leaderboard_url` and `scraping_method`).
      2. Check the benchmark folder file status:
         - If only `input.txt` (or `input.html`) exists: Create `scraper.py` and execute it to generate `{name}_data.csv`.
         - If `scraper.py` exists but `{name}_data.csv` is missing: Execute the existing `scraper.py` to generate `{name}_data.csv`.
         - If both files exist: Proceed with data loading/validation.
      3. Determine scraping method from the `scraping_method` field:
         - **If `scraping_method == "pandas_read_html"`:** 
           - **For benchmarks_with_data:** The `scraper.py` script already exists. Execute it by running `python scraper.py` from within `Human-SIG/data/raw/benchmarks_with_data/pandas_read_html/{benchmark_name}/`.
           - **For benchmarks_without_data:** 
             - If `scraper.py` exists, execute it.
             - **If only `input.txt` exists (missing both `scraper.py` and `{name}_data.csv`):** Create `scraper.py` using the template from Method A in Step 2.2.1, then execute it to generate `{name}_data.csv`.
           - See Method A in Step 2.2.1 for detailed implementation.
         - **If `scraping_method == "selenium"`:** 
           - **For benchmarks_with_data:** The `scraper.py` script already exists. Execute it by running `python scraper.py` from within `Human-SIG/data/raw/benchmarks_with_data/selenium/{benchmark_name}/`.
           - **Note:** Selenium method is only used for benchmarks in `benchmarks_with_data/selenium/` folder. All such benchmarks already have existing scripts.
           - See Method B in Step 2.2.1 for detailed implementation.
         - **If `scraping_method == "artificial_analysis"`:** 
           - Check if `scraper.py` exists in `Human-SIG/data/raw/benchmarks_without_data/artificial_analysis/{benchmark_name}/`. 
             - If `scraper.py` exists, execute it.
             - **If only `input.txt` exists (missing both `scraper.py` and `{name}_data.csv`):** Create `scraper.py` using the template from Method C in Step 2.2.1, then execute it to generate `{name}_data.csv`.
           - The script should read the unified table from `../input.html`. See Method C in Step 2.2.1 for detailed implementation.
         - **If `scraping_method == "vals_ai_manual_json"`:** 
           - Check if `{name}_input.json` exists. If it doesn't exist, log an error and skip this benchmark.
           - Check if `scraper.py` exists:
             - If `scraper.py` exists, execute it to convert JSON to CSV format.
             - **If only `input.txt` and `{name}_input.json` exist (missing `scraper.py` and `{name}_data.csv`):** Create `scraper.py` using the template from Method D in Step 2.2.1, then execute it to generate `{name}_data.csv`.
           - The final output should be `{name}_data.csv` in the same directory. See Method D in Step 2.2.1 for details.
         - **If `scraping_method == "manual"`:** 
           - Data files already exist. Load data from `Human-SIG/data/raw/benchmarks_with_data/manual_direct/{benchmark_name}/{name}_data.csv`.
           - See Method E in Step 2.2.1 for details.
         - **If `scraping_method == "manual_source_code"`:** 
           - Load data from `Human-SIG/data/raw/benchmarks_without_data/manual_source_code/{benchmark_name}/{name}_data.csv`. If the file doesn't exist, log an error and skip this benchmark (data must be manually provided by the user).
           - See Method F in Step 2.2.1 for details.
      3. Verify the output CSV contains the required columns (model_name, score).
      4. Save the `metric_direction` metadata separately (see output format below).
  - **Error Handling:** 
    - For Selenium method: If browser setup fails, table not found, or parsing errors occur, log the error to `Human-SIG/logs/ingestion_errors.log` with details, but do not stop the process. Continue to the next benchmark.
    - For pandas.read_html() method: If parsing fails (e.g., no tables found, parsing error, network error), log the error to `Human-SIG/logs/ingestion_errors.log` with details, but do not stop the process. Continue to the next benchmark.
    - For benchmarks with `scraping_method == "artificial_analysis"`, if the unified table HTML is not available or parsing fails, log an error and skip.
    - For benchmarks with `scraping_method == "vals_ai_manual_json"`, if the manual JSON file is missing, log an error and skip.
    - For benchmarks with `scraping_method == "manual"`, if the manual CSV file is missing, log an error and skip.
  - **Output Format:** Save data files in the appropriate benchmark folder:
    1. **Data file:**
       - For `pandas_read_html` method: `Human-SIG/data/raw/benchmarks_with_data/pandas_read_html/{benchmark_name}/{name}_data.csv`
       - For `selenium` method: `Human-SIG/data/raw/benchmarks_with_data/selenium/{benchmark_name}/{name}_data.csv`
       - For `artificial_analysis` method: `Human-SIG/data/raw/benchmarks_without_data/artificial_analysis/{benchmark_name}/{name}_data.csv`
       - For `vals_ai_manual_json` method: `Human-SIG/data/raw/benchmarks_without_data/vals_ai/{benchmark_name}/{name}_data.csv` (final output CSV file, converted from `{name}_input.json`)
       - For `manual` method: `Human-SIG/data/raw/benchmarks_with_data/manual_direct/{benchmark_name}/{name}_data.csv`
       - For `manual_source_code` method: `Human-SIG/data/raw/benchmarks_without_data/manual_source_code/{benchmark_name}/{name}_data.csv`
       - The CSV must contain at minimum:
         - `model_name`: String column with model identifiers
         - `score`: Float column with normalized scores (0-100 range, higher is better)
    2. **Metadata file:** `Human-SIG/data/raw/benchmarks_with_data/{method}/{benchmark_name}/{name}_metadata.json` or `Human-SIG/data/raw/benchmarks_without_data/{method}/{benchmark_name}/{name}_metadata.json` (for `pandas_read_html`, `selenium`, and `artificial_analysis` methods only). This JSON file stores supplementary information. The schema is:
    ```json
    {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "properties": {
        "metric_direction": {
          "type": "string",
          "enum": ["higher_is_better", "lower_is_better"],
          "description": "Indicates the ORIGINAL metric direction (before inversion if applied). If scores were inverted during normalization, this still stores the original direction for verification purposes."
        },
        "date_scraped": {
          "type": "string",
          "format": "date-time",
          "description": "ISO 8601 timestamp of when the data was scraped or loaded"
        },
        "source": {
          "type": "string",
          "enum": ["pandas_read_html", "selenium", "artificial_analysis", "vals_ai_manual_json", "manual", "manual_source_code"],
          "description": "Indicates the data acquisition method: pandas.read_html(), Selenium (for JavaScript-rendered pages), Artificial Analysis unified table, VALS.ai manual JSON file, manual CSV file, or manual source code extraction"
        }
      },
      "required": ["metric_direction", "date_scraped", "source"]
    }
    ```
- **2.2.3:** Commit State
  - **Message:** `Step 2.2 Completed: Executed existing scraping scripts and processed benchmark data (for benchmarks_with_data, scripts already exist; for benchmarks_without_data, executed existing scripts where available) and extracted/validated leaderboard data as CSV files with metadata`

### Phase III: Data Processing, Entity Resolution & Master Table Synthesis

Objective: Transform raw, heterogeneous benchmark data into a unified, normalized, and ranked dataset aligned with the LMArena "Ground Truth." This phase enforces strict identity verification to prevent data contamination.

Input:

- `Human-SIG/data/raw/` (Raw CSV files and metadata from Phase II).

- `Human-SIG/config/mapping.json` (The Unified Model Registry).

- `Human-SIG/data/raw/lmarena_leaderboard/filtered_elo_dump.json` (The Study Universe filtered in Step 2.1).

  Output:

- `Human-SIG/data/processed/master_table/master_correlation_matrix.csv`.

- `Human-SIG/data/processed/entity_resolution/pending_resolution.csv` (For human review, generated in Step 3.2.2).

#### Step 3.1: Robust Parsing & Score Normalization Strategy

- **3.1.1:** Create `Human-SIG/src/processing/parser_utils.py`.
  - **Code Documentation Requirements:**
    - File header must explain the purpose (parsing and normalizing benchmark scores from CSV files), the score normalization methodology (ensuring all scores are in 0-100 range as specified in Step 2.2.1), ranking logic, and tie-breaking strategy.
    - All classes and methods must have docstrings.
  - **Class Definition:** Implement `BenchmarkParser`.
  - **Ranking Logic:** Compute rank strictly within the Study Universe (models present in `filtered_elo_dump.json`). Only rank models that appear in both the benchmark data and the Study Universe. Models that appear in the benchmark but not in the Study Universe should be excluded from ranking.
  - **Tie-Breaking:** Use `method='min'` (e.g., if two models tie for first place with score 95, assign both rank 1, and the next model gets rank 3) to support rigorous RBO calculation. This ensures that tied models receive the same rank, which is important for RBO computation.
  - **Directionality:** When ranking, ensure that higher scores receive better (lower) ranks. All scores from Step 2.2.1 should already represent "higher is better" performance (after normalization and inversion if needed), so the ranking logic should always assume "higher score = better rank".
  - **Note:** Scores should already be normalized to 0-100 range from Step 2.2.1 and stored in CSV files. This parser loads CSV files, performs ranking, and outputs data structure transformation. The parser should output both the original scores and the computed ranks.
- **3.1.2:** Commit State.
  - **Message:** `Step 3.1.2 Completed: Implemented BenchmarkParser with ranking logic for RBO calculation`

#### Step 3.2: Human-in-the-Loop Entity Resolution

- **3.2.1:** Create `Human-SIG/src/processing/resolve_identities.py`.
  - **Code Documentation Requirements:**
    - File header must explain the three-level entity resolution strategy, the purpose of preventing data contamination, and the human-in-the-loop verification process.
    - All functions must have docstrings explaining their matching logic.
  - **Input:** Load the "Study Universe" (LMArena IDs) and the raw benchmark datasets.
  - **The Resolution Loop:** Iterate through every raw model name in the benchmarks:
    - **Level 1 (Exact Match):** Does `raw_name == lmarena_id`? -> Auto-Map.
    - **Level 2 (Registry Lookup):** Check `Human-SIG/config/mapping.json`. Is `raw_name` a known alias? -> Auto-Map.
    - **Level 3 (Fuzzy Proposal):** If unmatched, use Fuzzy Matching (e.g., Levenshtein ratio > 0.8) to find the closest `lmarena_id`. DO NOT AUTO-CONFIRM. Store as a "Proposal".
- **3.2.2:** Interactive Verification.
  - **Action:** Generate `Human-SIG/data/processed/entity_resolution/pending_resolution.csv` containing: `benchmark`, `raw_name`, `proposed_lmarena_id`, `confidence`.
  - **Interactive Pause:** Check if `Human-SIG/data/processed/entity_resolution/pending_resolution.csv` is not empty.
  - **If populated:** PAUSE execution. Print: "Unmatched models detected. Please manually review 'Human-SIG/data/processed/entity_resolution/pending_resolution.csv'. Confirm correct matches, fix errors, or delete rows to discard models. Then update 'mapping.json' manually or type 'CONTINUE' to let me append approved matches."
  - **Wait for User Input.**
  - **Post-Processing:** Read the user-verified CSV. APPEND the new confirmed aliases to `Human-SIG/config/mapping.json`. Constraint: Never overwrite `mapping.json` completely; only append new keys/values to preserve history.
- **3.2.3:** Final Merge.
  - **Action:** Reload all data using the updated `mapping.json`. Discard any models that remain unmatched.
  - **Message:** `Step 3.2.3 Completed: Executed fuzzy-assisted human verification and updated mapping registry`

#### Step 3.3: Master Table Synthesis

- **3.3.1:** Create `Human-SIG/src/processing/build_master_table.py`.
  - **Code Documentation Requirements:**
    - File header must explain the master table structure, the merge strategy (left join to preserve Study Universe), and why both score and rank columns are needed.
    - All functions must have docstrings explaining data transformation steps.
  - **Initialization:** Create the `df_master` DataFrame using LMArena models as the index.
    - **Columns:** `elo_overall`, `elo_math`, `elo_coding`, `elo_hard_prompts`, `elo_creative_writing`, `elo_instruction_following`, `elo_expert`.
  - **Merge Loop:** For each benchmark (e.g., humaneval):
    1. Load parsed data (Score + Rank) from the parser output (created in Step 3.1.1). The parser must read CSV files from the appropriate benchmark folder based on the scraping method:
       - For `pandas_read_html`: `Human-SIG/data/raw/benchmarks_with_data/pandas_read_html/{benchmark_name}/{name}_data.csv`
       - For `selenium`: `Human-SIG/data/raw/benchmarks_with_data/selenium/{benchmark_name}/{name}_data.csv`
       - For `manual_source_code`: `Human-SIG/data/raw/benchmarks_without_data/manual_source_code/{benchmark_name}/{name}_data.csv`
       - For `artificial_analysis`: `Human-SIG/data/raw/benchmarks_without_data/artificial_analysis/{benchmark_name}/{name}_data.csv`
       - For `manual_direct`: `Human-SIG/data/raw/benchmarks_with_data/manual_direct/{benchmark_name}/{name}_data.csv`
       - For `vals_ai_manual_json`: Read `{name}_data.csv` (final output CSV file converted from `{name}_input.json`). Location: `Human-SIG/data/raw/benchmarks_without_data/vals_ai/{benchmark_name}/`
    2. Map model names using the entity resolution logic from Step 3.2 (exact match, registry lookup, or verified fuzzy match).
    3. Left Join onto `df_master` (Keep only models present in LMArena Study Universe). Models that appear in the benchmark but not in the Study Universe will be excluded.
    4. Add columns: `{benchmark_id}_score` AND `{benchmark_id}_rank`. (Both are needed: Score for Pearson/Spearman correlation, Rank for RBO calculation). Use the sanitized benchmark_id (e.g., "humaneval", "mmlu_pro") as the column name prefix.
    5. Handle missing values: If a model in the Study Universe does not have a score for a particular benchmark, leave the score and rank as `NaN` (do not fill with zeros or default values).
  - **Data Type Enforcement:** Ensure all Score columns are `float64` and Rank columns are `int` (or nullable int).
- **3.3.2:** Data Integrity Check
  - **Action:** Script must calculate the "Sparsity Matrix" (also called "Overlap Matrix").
  - **Log:** Print the number of overlapping models ($N$) for each benchmark (i.e., how many models from the Study Universe have scores for that benchmark).
  - **Output:** Save the overlap statistics to `Human-SIG/results/data_overlap_stats.json` with the following schema:
    ```json
    {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "description": "Overlap statistics for each benchmark, indicating how many models from the Study Universe have scores in that benchmark",
      "patternProperties": {
        "^[a-zA-Z0-9_]+$": {
          "type": "object",
          "description": "Statistics for a single benchmark, keyed by benchmark_id (sanitized benchmark name)",
          "properties": {
            "overlap_count": {
              "type": "integer",
              "description": "Number of models from the Study Universe that have scores for this benchmark"
            },
            "study_universe_size": {
              "type": "integer",
              "description": "Total number of models in the Study Universe (constant across all benchmarks)"
            },
            "overlap_percentage": {
              "type": "number",
              "description": "Percentage of Study Universe models that have scores for this benchmark (overlap_count / study_universe_size * 100)"
            }
          },
          "required": ["overlap_count", "study_universe_size", "overlap_percentage"]
        }
      }
    }
    ```
  - **Warning:** If any benchmark has $N < 10$ (insufficient for reliable correlation analysis), log a CRITICAL WARNING to console and include this information in the overlap stats JSON file.
- **3.3.3:** Persistence
  - **Output:** Save the master table to `Human-SIG/data/processed/master_table/master_correlation_matrix.csv`. This CSV should contain:
    - One row per model (from the Study Universe)
    - Columns: `model_name`, `elo_overall`, `elo_math`, `elo_coding`, `elo_hard_prompts`, `elo_creative_writing`, `elo_instruction_following`, `elo_expert`, and for each benchmark: `{benchmark_id}_score` and `{benchmark_id}_rank`
    - Missing values should be represented as `NaN` or empty cells (not zeros)
  - **Note:** The overlap statistics JSON file was already saved in Step 3.3.2.
- **3.3.4:** Commit State
  - **Message:** `Step 3.3.4 Completed: Generated master correlation matrix with dual Score/Rank columns`

### Phase IV: Hypothesis Verification & Statistical Analysis (Revised for Small-N Robustness)

Objective: Execute a rigorous statistical verification pipeline specifically tailored for small sample sizes ($N=26$). Instead of a single, brittle multivariate regression which lacks statistical power, you will execute Bootstrapped Univariate Analysis for individual factors and Controlled Bivariate Robust Regression to disentangle confounding factors (specifically Difficulty vs. Variance).

Input:

- `Human-SIG/data/processed/master_table/master_correlation_matrix.csv` (Model Scores & Ranks).

- `Human-SIG/data/raw/benchmarks_with_data/{method}/{benchmark_name}/{name}_metadata.json` and `Human-SIG/data/raw/benchmarks_without_data/{method}/{benchmark_name}/{name}_metadata.json` (Metadata files containing `metric_direction` field determined during data acquisition, located in each benchmark folder).

- `Human-SIG/config/metadata.json` (Contains `release_date`, `task_type`, `question_count`, and other metadata for all 26 benchmarks).

  Output:

- `Human-SIG/results/statistical_significance_report.json` (Final P-values with Holm-Bonferroni corrections).

- `Human-SIG/results/analysis_ready_data.csv` (The clean dataset used for plotting).

- `Human-SIG/results/plots/` (Folder containing generated PDFs for the manuscript).

#### Step 4.1: Advanced Statistical Utility Implementation

- **4.1.1:** Create `Human-SIG/src/analysis/stats_utils.py`.
  - **Code Documentation Requirements:**
    - File header must explain the statistical methods used, their mathematical foundations, and why they are appropriate for small-N analysis.
    - Each function must have a detailed docstring explaining the mathematical formula, parameters, return values, and use cases.
  - **Requirement:** Implement the following rigorous functions. Do not rely on standard defaults.
  - `fisher_z_transform(r)`: $z = \text{arctanh}(r)$. Used for averaging correlations. Docstring must explain the Fisher transformation and its purpose.
  - `calculate_rbo(list1, list2, p=0.9)`: Rank-Biased Overlap. Focus on top 10 models. Docstring must explain RBO formula and the p parameter.
  - `bootstrap_ci(data_x, data_y, func, n_boot=5000)`: Returns 95% Confidence Interval via resampling with replacement. Docstring must explain bootstrap methodology.
  - `holm_bonferroni_correction(p_values_dict)`: Accepts a dictionary of `{hypothesis: raw_p_value}` and returns a dictionary of `{hypothesis: {p_raw, p_corrected, is_significant}}`. Docstring must explain the correction algorithm.
  - `huber_loss_regression(X, y)`: A robust regression wrapper (using `sklearn.linear_model.HuberRegressor` or `statsmodels.RLM`) to minimize the impact of outliers in a small-N dataset. Docstring must explain Huber loss and why it's used for small-N.
- **4.1.2:** Commit State
  - **Message:** `Step 4.1.2 Completed: Implemented stats utils with RBO, Bootstrap, and Holm-Bonferroni logic`

#### Step 4.2: Feature Engineering with Directionality Guardrails

- **4.2.1:** Create `Human-SIG/src/analysis/compute_features_robust.py`.
  - **Code Documentation Requirements:**
    - File header must explain the complete workflow: loading benchmark data from CSV files, reading metric_direction from metadata JSON files (for verification purposes), reading category from metadata.json to determine correlation target, verifying metric directionality (scores should already represent "higher is better" after Step 2.2.1), computing difficulty and variance features, and calculating correlations.
    - All functions must have docstrings explaining their mathematical operations.
  - **Task A: Metric Directionality Verification (Critical for H1).**
    - **Action:** Load benchmark data from CSV files in the appropriate benchmark folders. For each benchmark, read the `metric_direction` field from the corresponding metadata file located in the same benchmark folder: `Human-SIG/data/raw/benchmarks_with_data/{method}/{benchmark_name}/{name}_metadata.json` or `Human-SIG/data/raw/benchmarks_without_data/{method}/{benchmark_name}/{name}_metadata.json` (created during data acquisition in Step 2.2).
    - **Prerequisite:** All scores must already be normalized to the 0-100 range and inverted if necessary (as required in Step 2.2.1) so that higher scores represent better performance. If any benchmark's scores are not in the 0-100 range, HALT and report an error.
    - **Logic:** Check the `metric_direction` field from the metadata JSON file (not from metadata.json config file).
    - **Verification Step:** If `metric_direction == "lower_is_better"` (e.g., Perplexity, Bits-per-byte, Error Rate):
      - **Expected Behavior:** The scores in the CSV file should ALREADY represent "higher is better" performance (i.e., they should have been inverted during Step 2.2.1 normalization). Verify that this is the case by checking that higher scores correspond to better model performance.
      - **If Verification Fails:** If you find that scores with `metric_direction == "lower_is_better"` still represent "lower is better" (i.e., they were not inverted in Step 2.2.1), HALT and report an error: "CRITICAL: Found benchmark {benchmark_name} with metric_direction='lower_is_better' but scores were not inverted in Step 2.2.1. Scores must represent 'higher is better' after Step 2.2.1 normalization."
      - **No Additional Transformation:** Since Step 2.2.1 already handles inversion, NO ADDITIONAL TRANSFORMATION is needed in this step. The `metric_direction` field is preserved for verification and documentation purposes only.
    - **Reasoning:** This verification step ensures that for all 26 benchmarks, a "higher" number mathematically implies better performance, preventing "False Negative" correlations in later steps. The goal is to have a consistent directionality where higher scores always mean better performance, which should already be achieved by Step 2.2.1.
  - **Task B: H1 (Difficulty) Feature Calculation.**
    - **Action:** Calculate `subset_avg_score` using the Common Subset (Models with LMArena `elo_overall` Score between 1400 and 1430, inclusive). This subset was identified in Step 2.1.1 (Filter 2).
    - **Calculation:** For each benchmark, compute the mean score across all models in the Common Subset that have scores for that benchmark. This mean score represents the benchmark's difficulty (lower mean = harder benchmark).
    - **Safety Check:** If the number of overlapping models in this specific ELO range is $N < 5$ for any benchmark:
      - **Log Warning:** "Insufficient overlap for Difficulty Common Subset (N={actual_N}). Using Study Universe mean as fallback."
      - **Fallback:** Use the full Study Universe mean (all models with `elo_overall >= 1330`).
      - **Flag:** Set column `is_estimated_difficulty = True` to indicate that the difficulty was estimated using the fallback method.
    - **Note:** The Difficulty feature is the inverse of average score: harder benchmarks have lower average scores. This will be used in the regression model where higher difficulty (lower scores) is expected to correlate with higher UX correlation.
  - **Task C: H5 (Variance) Feature Calculation.**
    - **Action:** Compute the Coefficient of Variation ($CV$) instead of raw variance.
    - **Formula:** $CV = \frac{\sigma}{\mu}$.
    - **Reasoning:** Raw variance penalizes high-accuracy benchmarks (where scores are compressed near 100%). $CV$ normalizes variance relative to the score scale, making "Accuracy" benchmarks comparable to "Perplexity" benchmarks.
- **4.2.2:** Correlation Calculation Loop & Sanity Check.
  - **Action:** For each benchmark, calculate Spearman $\rho$, Kendall $\tau$, and RBO between Benchmark_Score (which should already represent "higher is better" performance after Step 2.2.1 normalization, as verified in Task A) and the corresponding LMArena ELO score. The correlation category for each benchmark is determined by the `category` field in metadata.json, which maps to the corresponding ELO column:
    - "Coding" -> `elo_coding`
    - "Math" -> `elo_math`
    - "Instruction Following" -> `elo_instruction_following`
    - "Creative Writing" -> `elo_creative_writing`
    - "Hard Prompts" -> `elo_hard_prompts`
    - "Expert" -> `elo_expert`
  - **Data Source:** Load benchmark scores from `Human-SIG/data/processed/master_table/master_correlation_matrix.csv` (which contains the scores after entity resolution and merging).
  - **Missing Data Handling:** Only include models that have both benchmark scores and the corresponding LMArena ELO scores (exclude rows with NaN in either column).
  - **Store Results:** Save the correlation coefficients for each benchmark in the analysis_ready_data.csv file, along with the difficulty, variance, and other features computed in Tasks A, B, and C.
  - **Halt Protocol:** Identify a known high-quality benchmark (e.g., MMLU-Pro or HumanEval) that should have strong correlation with LMArena scores.
    - Calculate Spearman correlation between the benchmark scores (which should already represent "higher is better" performance after Step 2.2.1 normalization) and the corresponding LMArena ELO scores (determined by the benchmark's `category` field in metadata.json).
    - If Spearman Correlation $< 0.5$: HALT EXECUTION IMMEDIATELY.
    - **Print:** "CRITICAL: Detected low correlation (< 0.5) for high-quality benchmark {benchmark_name}. This suggests a data quality issue. Please check: (1) metric directionality in the benchmark metadata files (located in the benchmark folders: Human-SIG/data/raw/benchmarks_with_data/{method}/{benchmark_name}/{name}_metadata.json or Human-SIG/data/raw/benchmarks_without_data/{method}/{benchmark_name}/{name}_metadata.json), (2) that scores in CSV files are correctly normalized to 0-100 range, (3) that metric inversion was applied correctly in Step 2.2.1 if metric_direction == 'lower_is_better' (scores should represent 'higher is better' after normalization), and (4) that the correct LMArena ELO column is being used based on the benchmark's category."
    - **Wait for User:** Do not proceed until resolved. The user must verify and fix the data issue before continuing.
- **4.2.3:** Persistence.
  - **Output:** Save the fully engineered table to `Human-SIG/results/analysis_ready_data.csv`.
  - **Message:** `Step 4.2.3 Completed: Computed robust features (CV, Inverted Scores) and verified directionality`

#### Step 4.3: Hypothesis Testing Strategy (The Small-N Protocol)

- **4.3.1:** Create `Human-SIG/src/analysis/small_n_hypothesis_test.py`.
  - **Code Documentation Requirements:**
    - File header must explain why small-N protocols are needed, the statistical power limitations, and the rationale for targeted tests instead of multivariate regression.
    - Each test function must have docstrings explaining the statistical test, its assumptions, and interpretation.
  - **Context:** Since $N=29$ is too small for a 6-variable regression (Rule of thumb: 10 samples per variable), you must execute Targeted Tests for each hypothesis.
  - **Global Settings:** `n_bootstraps = 5000`, `alpha = 0.05`.
- **4.3.2:** Test Execution: H1 (Difficulty) & H5 (Variance) - The "Trade-off" Test.
  - **Hypothesis:** Harder benchmarks (lower average scores) correlate better with UX (H1), but variance (CV) also drives correlation (H5). These factors are often collinear (floor effects reduce variance in high-accuracy benchmarks).
  - **Model:** Run a Bivariate Robust Regression using `statsmodels.RLM` with Huber's t-criterion for robust estimation.
  - **Equation:** $Correlation \sim \beta_1 \cdot Difficulty + \beta_2 \cdot CV + \epsilon$, where:
    - $Difficulty$ is the subset_avg_score (lower values = harder benchmarks). For regression, you may want to use $Difficulty = 100 - subset\_avg\_score$ so that higher values represent harder benchmarks, or use the raw subset_avg_score and interpret the sign accordingly.
    - $CV$ is the Coefficient of Variation computed in Task C.
    - $\epsilon$ is the error term.
  - **Action:** Store the p-values and coefficients for both $\beta_1$ and $\beta_2$, along with their 95% bootstrap confidence intervals.
  - **Criteria:** H1 is supported only if $\beta_1$ is significant (p < 0.05 before correction) while controlling for CV. H5 is supported if $\beta_2$ is significant while controlling for Difficulty.
- **4.3.2b:** Test Execution: H5 (Variance) - The "Task Type Interaction" Test.
  - **Hypothesis:** The relationship between variance (CV) and correlation may differ across different task types. This tests whether variance affects correlation differently for MCQ, Generation, and Agentic tasks.
  - **Method:** Stratified analysis by task type. For each of the three main task types (MCQ, Generation, Agentic), separately examine the relationship between CV and correlation.
    - **Group 1 (MCQ):** Benchmarks with `task_type == "MCQ"`. Compute the Spearman correlation between CV and Benchmark_Alignment_Correlation for this group.
    - **Group 2 (Generation):** Benchmarks with `task_type == "Generation"`. Compute the Spearman correlation between CV and Benchmark_Alignment_Correlation for this group.
    - **Group 3 (Agentic):** Benchmarks with `task_type == "Agentic"`. Compute the Spearman correlation between CV and Benchmark_Alignment_Correlation for this group.
    - **Exclusion:** Benchmarks with `task_type == "Mixed"` are excluded from this analysis.
  - **Statistical Test:** 
    - For each group, compute Spearman correlation between CV and correlation, along with 95% bootstrap confidence intervals (5000 iterations).
    - **Comparison Method:** To test whether the three correlation coefficients differ significantly:
      - **Option 1 (Recommended if N >= 5 for each group):** Use Fisher z-transformation to convert each correlation coefficient to z-scores: $z_i = \text{arctanh}(r_i)$. Then use a one-way ANOVA (or Kruskal-Wallis if normality is questionable) to test whether the three z-scores differ significantly. The standard error for each z-score is $SE = \frac{1}{\sqrt{N_i - 3}}$, where $N_i$ is the sample size for group $i$.
      - **Option 2 (If sample sizes are very small):** Use a permutation test: randomly permute the group labels 10,000 times, compute the correlation for each permuted group, and compare the observed difference in correlations to the null distribution.
      - **Option 3 (If N < 5 for any group):** Report descriptive statistics only (median CV, median correlation, and the Spearman correlation with 95% CI for each group) with clear notes about sample size limitations. Do not perform formal statistical comparison, but visually compare the confidence intervals to assess potential differences.
    - **Implementation Note:** The Fisher z-transformation approach is statistically rigorous and accounts for the different sample sizes across groups. The test statistic follows a chi-square distribution under the null hypothesis that all three correlations are equal.
  - **Output:** Store the correlation coefficient, p-value (if applicable), and 95% CI for each task type group. Also store a comparison statistic (if computed) indicating whether the three groups differ significantly.
  - **Interpretation:** H5 is supported if variance shows a positive relationship with correlation in at least one task type group, or if the relationship differs significantly across task types (suggesting task type moderates the variance-correlation relationship).
- **4.3.3:** Test Execution: H2 (Recency) - The "Trend" Test.
  - **Model:** Univariate Spearman Correlation between Release_Date_Ordinal and Benchmark_Alignment_Correlation.
  - **Variable Construction:** 
    - `Release_Date_Ordinal`: Convert `release_date` from metadata.json (YYYY-MM-DD format) to ordinal days since a reference date (e.g., days since 2020-01-01, or simply use the date as a numeric value).
    - `Benchmark_Alignment_Correlation`: This is the Spearman correlation between the benchmark scores and the corresponding LMArena ELO scores (computed in Step 4.2.2).
  - **Bootstrap:** Resample the 26 benchmarks 5000 times (with replacement) to derive a 95% Confidence Interval for the Spearman correlation coefficient. Store both the point estimate and the confidence interval.
- **4.3.4:** Test Execution: H3 (Complexity) & H6 (Scale) - The "Categorical/Continuous" Test.
  - **H3 (Complexity):** Test whether prompt complexity (as a categorical variable) affects correlation with UX.
    - **Rationale:** Treating `prompt_length` as an ordinal variable with equal spacing (1, 2, 3, 4) assumes that the difference between "Short" and "Medium" is the same as between "Long" and "Extreme", which may not be valid. Instead, use a categorical approach.
    - **Method:** Use Kruskal-Wallis H-test (non-parametric one-way ANOVA) to test whether the distribution of correlations differs across the four `prompt_length` categories: "Short", "Medium", "Long", "Extreme".
    - **Implementation:** 
      - Group benchmarks by `prompt_length` category.
      - Extract the correlation values (Spearman $\rho$ from Step 4.2.2) for each group.
      - Use `scipy.stats.kruskal` to test the null hypothesis that all groups have the same distribution of correlations.
      - If the test is significant (p < 0.05), perform post-hoc pairwise comparisons using Mann-Whitney U tests (with Bonferroni correction for multiple comparisons) to identify which categories differ.
    - **Output:** Store the Kruskal-Wallis test statistic, p-value, and post-hoc comparison results (if applicable).
  - **H6 (Scale):** Pearson Correlation between $\log(N_{samples})$ and Correlation.
    - **Variable Definition:** $N_{samples}$ is the `question_count` field from metadata.json. Apply natural logarithm transformation: $\log(N_{samples}) = \ln(question\_count)$.
- **4.3.5:** Test Execution: H4 (Generative vs. MCQ) - The "Group" Test.
  - **Model:** Categorical comparison using the `task_type` field from `Human-SIG/config/metadata.json`.
    - **Group A:** Benchmarks with `task_type == "Generation"` or `task_type == "Agentic"` (generative tasks).
    - **Group B:** Benchmarks with `task_type == "MCQ"` (multiple choice tasks).
    - **Exclusion Rule:** Benchmarks with `task_type == "Mixed"` must be **excluded** from this analysis. Do not include them in either group. Log the number of excluded Mixed benchmarks for transparency, but do not ask for user guidance.
  - **Guardrail:** Sample Imbalance Check
  - **Action:** Count samples in Group A ($N_A$) and Group B ($N_B$) after excluding "Mixed" benchmarks.
  - **Logic:**
    - IF $N_A < 5$ OR $N_B < 5$:
      - **Log Warning:** "Skipping Mann-Whitney U due to extreme class imbalance (N_A={$N_A$}, N_B={$N_B$}). Reporting descriptive statistics only."
      - **Fallback:** Compute and return descriptive statistics: Median Difference, Mean Difference, and their 95% bootstrap confidence intervals. Set `p_value = 1.0` (to avoid false significance) and `is_descriptive_only = True` in the results.
    - ELSE:
      - Proceed with Mann-Whitney U Test (also known as Wilcoxon rank-sum test).
      - **Test Details:** Use `scipy.stats.mannwhitneyu` with `alternative='two-sided'` to test whether the distribution of correlations differs between Group A (Generative/Agentic) and Group B (MCQ).
  - **Reasoning:** Non-parametric tests lose validity when one group is essentially anecdotal (e.g., 3 benchmarks). The Mann-Whitney U test is appropriate for comparing two independent groups when the normality assumption may not hold.
  - **Action:** Compare the distribution of correlations (Spearman $\rho$ values computed in Step 4.2.2) between the two groups. Store the test statistic, p-value, and effect size (e.g., rank-biserial correlation).
- **4.3.6:** Commit State
  - **Message:** `Step 4.3.6 Completed: Executed targeted Small-N statistical tests (Robust Regression, Kruskal-Wallis, Mann-Whitney, and stratified H5 analysis)`

#### Step 4.4: Correction, Reporting & Visualization

- **4.4.1:** Multiple Comparison Correction (Anti-Hallucination).

  - **Logic:** You performed 5+ distinct statistical tests. This increases the risk of Type I errors (false positives).

  - **Action:** Load the raw p-values from Step 4.3.

  - **Algorithm:** Apply Holm-Bonferroni Correction.

    - Sort p-values from smallest to largest.
    - Adjust criteria: $\alpha_{corrected} = \frac{\alpha}{m - rank + 1}$.

  - **Output:** Generate `Human-SIG/results/statistical_significance_report.json` (this file will be referenced in Phase V for results reporting).

  - **Structure:** The JSON file must contain entries for all six hypotheses (H1-H6). For H1 and H5, include separate entries for each coefficient (H1_Difficulty_Beta1, H5_Variance_Beta2). For H5, also include entries for each task type group (H5_Variance_MCQ, H5_Variance_Generation, H5_Variance_Agentic). The schema is:
    ```json
    {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "description": "Statistical significance report for all hypotheses after Holm-Bonferroni correction",
      "patternProperties": {
        "^H[1-6]_[A-Za-z_]+$": {
          "type": "object",
          "description": "Test results for a single hypothesis or sub-hypothesis",
          "properties": {
            "p_raw": {
              "type": "number",
              "minimum": 0,
              "maximum": 1,
              "description": "Raw p-value from the statistical test before multiple comparison correction"
            },
            "p_corrected": {
              "type": "number",
              "minimum": 0,
              "maximum": 1,
              "description": "P-value after Holm-Bonferroni correction for multiple comparisons"
            },
            "significant_strict": {
              "type": "boolean",
              "description": "Whether the hypothesis is statistically significant after correction (p_corrected < 0.05)"
            },
            "effect_size": {
              "type": "number",
              "description": "Effect size measure (coefficient, correlation, or difference depending on test type)"
            },
            "effect_size_type": {
              "type": "string",
              "enum": ["beta_coefficient", "spearman_rho", "pearson_r", "median_difference"],
              "description": "Type of effect size measure used"
            },
            "ci_lower": {
              "type": "number",
              "description": "Lower bound of 95% bootstrap confidence interval for effect_size (only for tests with CI)"
            },
            "ci_upper": {
              "type": "number",
              "description": "Upper bound of 95% bootstrap confidence interval for effect_size (only for tests with CI)"
            },
            "sample_size": {
              "type": "integer",
              "description": "Sample size for this specific test (only for stratified analyses like H5_Variance_MCQ)"
            },
            "is_descriptive_only": {
              "type": "boolean",
              "description": "Whether this result is descriptive only due to insufficient sample size (only for H4 when N < 5)"
            },
            "conclusion": {
              "type": "string",
              "description": "Textual conclusion summarizing the statistical significance and interpretation"
            }
          },
          "required": ["p_raw", "p_corrected", "significant_strict", "effect_size", "effect_size_type", "conclusion"]
        }
      }
    }
    ```

- **4.4.2:** Visualization Generation (`Human-SIG/src/analysis/generate_plots.py`).

  - **Action:** Use `seaborn` and `matplotlib` to generate the following figures for the manuscript.
  - **Figure 1 (H1/H5):** `regplot` overlaying Difficulty vs. Correlation, with point size representing Variance (CV). Save as `overleaf/figures/Figure_1_Difficulty_Variance.pdf`.
  - **Figure 2 (H4):** `boxplot` with overlaid `stripplot` showing Correlation distributions for "MCQ" vs "Generative/Agentic" (Group A). Exclude "Mixed" benchmarks from the plot. Save as `overleaf/figures/Figure_2_Task_Type.pdf`.
  - **Figure 3a (H3):** `boxplot` with overlaid `stripplot` showing Correlation distributions across the four `prompt_length` categories ("Short", "Medium", "Long", "Extreme"). This visualizes the Kruskal-Wallis test results. Save as `overleaf/figures/Figure_3a_Complexity_Categories.pdf`.
  - **Figure 3b (H5 Task Type Interaction):** `scatterplot` or `regplot` showing the relationship between CV and Correlation, with different colors/markers for each task type (MCQ, Generation, Agentic). This visualizes the stratified H5 analysis. Save as `overleaf/figures/Figure_3b_Variance_TaskType.pdf`.
  - **Figure 4 (Confounders):** `heatmap` of the correlation matrix between the Independent Variables themselves (e.g., Are all Hard benchmarks also Recent? Do harder benchmarks have lower variance?). Include the following variables: Difficulty (subset_avg_score), Variance (CV), Recency (Release_Date_Ordinal), Complexity (prompt_length as categorical), Scale (log(question_count)), and Task_Type (encoded as binary or ordinal). This helps explain the Regression results and identify multicollinearity. Save as `overleaf/figures/Figure_4_Confounder_Heatmap.pdf`.

- **4.4.3:** Commit State

  - **Message:** `Step 4.4.3 Completed: Applied Holm-Bonferroni correction and generated manuscript figures`

### Phase V: Manuscript Generation (The ACL 2026 Submission)

Objective: Synthesize the findings from Human-SIG/results/ into a scientifically rigorous, compliant ACL LaTeX submission in the overleaf/ repository.

Critical Constraint: You must NOT edit main.tex directly after initialization. You will generate discrete section files in overleaf/sections/ and input them. This prevents context-window truncation from corrupting the entire document structure.

**LaTeX Formatting Requirements:**
- **Line Breaks:** When generating LaTeX content, each natural sentence must be on a separate line. This improves readability and makes it easier to identify and fix formatting issues. For example:
  ```latex
  This is the first sentence.
  This is the second sentence.
  This is the third sentence.
  ```
  Instead of:
  ```latex
  This is the first sentence. This is the second sentence. This is the third sentence.
  ```
- **Paragraph Structure:** Use blank lines to separate paragraphs. Do not use `\\` for line breaks within paragraphs.

#### Step 5.1: Modular LaTeX Architecture Setup

- **5.1.1:** Create the directory `overleaf/sections/` if it does not exist.

- **5.1.2:** Initialize `overleaf/main.tex` using the ACL 2026 template.

  - **Action:** Write the preamble, title ("Correlating Benchmarks with User Experience in the Post-Saturation Era"), and author placeholders.

  - **Structure:** Inside `\begin{document}`, strictly write ONLY the following inclusion logic:

    ```
    \begin{document}
    \maketitle
    \begin{abstract}
    \input{sections/abstract}
    \end{abstract}
    \input{sections/introduction}
    \input{sections/methodology}
    \input{sections/results}
    \input{sections/discussion}
    \input{sections/conclusion}
    \bibliography{anthology,custom}
    \end{document}
    ```

- **5.1.3:** Commit State.

  - **Message:** `Step 5.1.3 Completed: Initialized modular main.tex architecture`

#### Step 5.2: Abstract and Introduction (Contextualization)

- **5.2.1:** Create `overleaf/sections/abstract.tex`.
  - **Source:** Read `Human-SIG/results/statistical_significance_report.json` (created in Step 4.4.1) to identify the top-level conclusion (e.g., "H1 and H5 supported"). Also read `Human-SIG/results/analysis_ready_data.csv` to get summary statistics.
  - **Content:** Write a 200-word abstract summarizing the analysis of 29 benchmarks against LMArena. Explicitly mention the shift from "Static Accuracy" to "Dynamic User Preference." Report the key findings: which hypotheses were supported, the effect sizes, and the statistical significance (after correction). Mention the use of robust statistical methods (bootstrap, robust regression) to handle the small sample size.
  - **Formatting:** Each sentence must be on a separate line. Use blank lines to separate paragraphs.
- **5.2.2:** Create `overleaf/sections/introduction.tex`.
  - **Content:**
    1. Define the problem: The "Saturation" of MMLU and the "Identity Crisis" of models (from Master Data Source).
    2. Define the Ground Truth: LMArena as the proxy for User Experience.
    3. State the Research Questions: List the six hypotheses (Difficulty, Recency, Complexity, etc.).
  - **Formatting:** Each sentence must be on a separate line. Use blank lines to separate paragraphs.
- **5.2.3:** Commit State.
  - **Message:** `Step 5.2.3 Completed: Drafted Abstract and Introduction sections`

#### Step 5.3: Methodology (The Rigor Check)

- **5.3.1:** Create `overleaf/sections/methodology.tex`.
  - **Source:** Read `Human-SIG/results/data_overlap_stats.json` (from Phase III) and your internal logic from Phase IV.
  - **Content:**
    1. **Data Collection:** Describe the ingestion of 29 benchmarks and the "Strict Entity Resolution" protocol used to map models. Mention the final $N$ (sample size) from the overlap stats.
    2. **Statistical Framework:** Explicitly state the use of Rank-Biased Overlap (RBO) ($p=0.9$) to account for top-tier sensitivity, Spearman's rank correlation ($\rho$) and Kendall's $\tau$ for non-parametric correlation analysis, and Fisher z-transformation for correlation aggregation when needed. Explain why multiple correlation metrics are used (RBO for ranking, Spearman/Kendall for robustness to outliers).
    3. **Hypothesis Testing:** Describe the statistical tests used for each hypothesis:
       - **H1 & H5 (Main):** Bivariate Robust Regression model (Correlation ~ Difficulty + CV) using `statsmodels.RLM` with Huber's t-criterion.
       - **H5 (Stratified):** Separate Spearman correlation analyses between CV and correlation for each task type (MCQ, Generation, Agentic) to examine task type moderation effects.
       - **H2:** Univariate Spearman correlation between release date and correlation.
       - **H3:** Kruskal-Wallis H-test (non-parametric one-way ANOVA) to test whether correlation distributions differ across prompt_length categories, with post-hoc pairwise comparisons if significant.
       - **H4:** Mann-Whitney U test to compare correlation distributions between MCQ and Generative/Agentic groups.
       - **H6:** Pearson correlation between log(question_count) and correlation.
    4. **Small-N Considerations:** Explain why multivariate regression with all 6 variables was avoided due to small sample size ($N=29$), which would violate the rule of thumb requiring at least 10 samples per variable. Describe the bootstrap resampling procedure (5000 iterations) used to compute confidence intervals for all effect sizes. Explain why categorical tests (Kruskal-Wallis) are preferred over assuming ordinal spacing for prompt_length.
  - **Formatting:** Each sentence must be on a separate line. Use blank lines to separate paragraphs.
- **5.3.2:** Commit State.
  - **Message:** `Step 5.3.2 Completed: Documented Methodology including RBO and Multivariate Regression`

#### Step 5.4: Results Reporting (Anti-Hallucination Protocol)

- **5.4.1:** Data Loading & Context Injection.
  - **Action:** BEFORE generating any LaTeX code, you must strictly read `Human-SIG/results/statistical_significance_report.json` and `Human-SIG/results/analysis_ready_data.csv` (created in Steps 4.4.1 and 4.2.3) into a local memory variable.
  - **Constraint:** When calling the LLM to write the text, explicitly inject the raw JSON/CSV data snippets into the context window. DO NOT rely on the Agent's "memory" of previous steps.
- **5.4.2:** Create `overleaf/sections/results.tex`.
  - **Content Block 1:** Create a results summary table. Generate `overleaf/tables/results_table.tex` containing a LaTeX table that summarizes the hypothesis test results (p-values, effect sizes, significance) from `statistical_significance_report.json`. Reference it with: `\input{tables/results_table}`.
  - **Content Block 2:** For H1-H6, report the Bootstrap 95% Confidence Intervals (e.g., "Coefficient: 0.45 [95% CI: 0.12, 0.78]"). Include both raw and corrected p-values (after Holm-Bonferroni correction) for each hypothesis. Clearly indicate which hypotheses are statistically significant after correction.
  - **Specifics:**
    - Discuss the specific impact of variance (CV - Coefficient of Variation) on correlation, and how it interacts with difficulty (The Clustering Effect: high-accuracy benchmarks compress variance near 100%, making it harder to distinguish between top-performing models). Explain the trade-off between difficulty and variance: harder benchmarks may have lower variance due to floor effects, while easier benchmarks may have compressed variance near the ceiling.
    - **H5 Task Type Analysis:** Report the stratified analysis results showing how the relationship between variance and correlation differs across task types (MCQ, Generation, Agentic). Discuss whether variance affects correlation differently for different task types, and what this implies for benchmark design.
    - Explicitly mention that all benchmark scores were normalized to a 0-100 scale (as specified in Step 2.2.1) to ensure comparability across different metric types, and that metric directionality was handled through inversion for "lower_is_better" metrics during the normalization process in Step 2.2.1 (verified in Step 4.2.1).
  - **Reference:** Include `\includegraphics{figures/Figure_1_Difficulty_Variance.pdf}`, `\includegraphics{figures/Figure_2_Task_Type.pdf}`, `\includegraphics{figures/Figure_3a_Complexity_Categories.pdf}`, `\includegraphics{figures/Figure_3b_Variance_TaskType.pdf}`, and `\includegraphics{figures/Figure_4_Confounder_Heatmap.pdf}`.
  - **Formatting:** Each sentence must be on a separate line. Use blank lines to separate paragraphs.
- **5.4.3:** Commit State.
  - **Message:** `Step 5.4.3 Completed: Synthesized Results section using verified Bootstrap statistics`

#### Step 5.5: Discussion and Conclusion

- **5.5.1:** Create `overleaf/sections/discussion.tex`.
  - **Content:** Interpret the results based on the statistical significance report. Read `Human-SIG/results/statistical_significance_report.json` to determine which hypotheses are supported.
    - If H1/H5 supported: Discuss "The Alignment Tax" (harder benchmarks align better with user experience, but variance also plays a crucial role). Explain the interaction between difficulty and variance.
    - If H2 supported: Discuss "Contamination vs. Generalization" (recent benchmarks may have higher correlation due to training data contamination or genuine generalization improvements).
    - If H4 supported: Discuss why "Generative/Agentic" tasks beat MCQs (open-ended tasks may better capture real-world user preferences).
    - Discuss limitations: small sample size ($N=29$), dependency on LMArena as ground truth, potential confounding factors.
  - **Formatting:** Each sentence must be on a separate line. Use blank lines to separate paragraphs.
- **5.5.2:** Create `overleaf/sections/conclusion.tex`.
  - **Content:** Final summary and limitations (e.g., dependency on LMArena crowd demographics).
  - **Formatting:** Each sentence must be on a separate line. Use blank lines to separate paragraphs.
- **5.5.3:** Commit State.
  - **Message:** `Step 5.5.3 Completed: Drafted Discussion and Conclusion`

#### Step 5.6: LaTeX Compilation & Formatting Quality Control

- **5.6.1:** Compile the LaTeX document.
  - **Action:** Navigate to the `overleaf/` directory and compile the document using `latexmk`:
    ```bash
    cd overleaf/
    latexmk -pdf -file-line-error -halt-on-error -interaction=batchmode main.tex
    ```
  - **Purpose:** Generate the PDF and identify any compilation errors or warnings.

- **5.6.2:** Handle Compilation Errors (if any).
  - **Action:** If compilation fails (exit code != 0):
    1. Read the error messages from the terminal output and the `.log` file.
    2. Identify the specific LaTeX error (e.g., missing packages, undefined commands, syntax errors).
    3. Fix the error in the corresponding `.tex` file:
       - Check for missing `\usepackage{}` declarations in `main.tex`.
       - Verify all referenced files exist (sections, tables, figures).
       - Check for unmatched braces, brackets, or environments.
       - Ensure all custom commands are defined.
    4. Re-run the compilation command from Step 5.6.1.
    5. Repeat until compilation succeeds.
  - **Note:** Do not proceed to Step 5.6.3 until compilation succeeds without errors.

- **5.6.3:** Check for Formatting Warnings (Overfull/Underfull).
  - **Action:** After successful compilation, examine the `.log` file for formatting warnings:
    - **On Unix/Linux/Mac:** Use `grep -E "(Overfull|Underfull)" overleaf/main.log`
    - **On Windows (PowerShell):** Use `Select-String -Pattern "(Overfull|Underfull)" overleaf/main.log`
    - **Cross-platform alternative:** Read the `.log` file and search for lines containing "Overfull" or "Underfull" using Python or any text processing tool.
  - **Overfull Box Warnings:** Indicate that text extends beyond the right margin.
    - **Common Causes:** Long words, URLs, or technical terms that cannot be hyphenated.
    - **Solutions:**
      - Use `\sloppy` command (sparingly, only for problematic paragraphs).
      - Manually break long URLs or technical terms using `\-` or `\allowbreak`.
      - Rewrite sentences to avoid overly long words or phrases.
      - Use `\hyphenation{}` to specify custom hyphenation points.
      - Consider using `\url{}` package for URLs with automatic line breaking.
  - **Underfull Box Warnings:** Indicate that lines are too short (usually in justified text).
    - **Common Causes:** Short paragraphs, lists, or forced line breaks.
    - **Solutions:**
      - Combine short sentences or paragraphs where appropriate.
      - Remove unnecessary `\\` line breaks.
      - Adjust spacing around equations or figures.
      - Use `\raggedright` for specific sections if justified text causes issues.
  - **Priority:** Focus on fixing Overfull warnings first (they are more visually problematic), then address Underfull warnings if they are excessive (>10 per page).
  - **Iterative Process:**
    1. Fix identified Overfull/Underfull issues in the relevant `.tex` files.
    2. Re-compile using the command from Step 5.6.1.
    3. Re-check the log file for remaining warnings.
    4. Repeat until all critical Overfull warnings are resolved and Underfull warnings are minimized.

- **5.6.4:** Commit State.
  - **Message:** `Step 5.6.4 Completed: Compiled LaTeX document and resolved formatting warnings`

#### Step 5.7: Final Deployment

- **5.7.1:** Push Artifacts.
  - **Command:** `cd overleaf/ && git push origin master`
  - **Verification:** Ensure all `.tex` files, the `figures/` folder, the `tables/` folder, and the compiled `main.pdf` are present in the remote repository.
- **5.7.2:** Final Log.
  - **Message:** `Step 5.7.2 Completed: FINAL SUBMISSION ARTIFACTS PUSHED. PIPELINE COMPLETE.`
