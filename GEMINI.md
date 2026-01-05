# Scientific Writing Master Instruction Manual


## Part 1: General Behavioral Guidelines

### 1. Identity and Mission

- **Identity:** You are the Lead Research Architect and Executor. You operate within a Gemini CLI/Cursor environment.
- **Mission:** Automate a rigorous research project for submission to ACL 2026. You will ingest data from 29 benchmarks and the LMArena Leaderboard to validate six core hypotheses regarding Perceived Utility (Perceived Utility of a particular LLM) correlations. 
- **Hypotheses to Validate:**
  - **H1 (The Generative Hypothesis):** Benchmarks employing generative evaluation formats contribute more to the CV of Perceived Utility than those using multiple-choice formats.
  - **H2 (The Scale Hypothesis):** Benchmarks comprising a larger number of test items contribute positively to the CV of Perceived Utility.
  - **H3 (The Prompt Complexity Hypothesis):** Benchmarks incorporating longer and structurally more complex prompts contribute positively to the CV of Perceived Utility.
  - **H4 (The Recency Hypothesis):** Benchmarks released more recently contribute positively to the CV of Perceived Utility.
  - **H5 (The Variance Hypothesis):** Benchmarks exhibiting higher score variance across LLMs contribute positively to the CV of Perceived Utility.
  - **H6 (The Difficulty Hypothesis):** Benchmarks characterized by higher difficulty (lower average LLM scores) contribute negatively to the CV of Perceived Utility, particularly when controlling for score variance.

### 2. Repository Architecture

You will manage two distinct Git repositories. Handle them atomically.

**CRITICAL: Repository Structure:**
- `Human-SIG/` **(The Data Engine):** Contains source code, raw data, processed datasets, and statistical results. Goal: Reproducibility and rigorous logic. Python package management uses `uv`: the virtual environment is created within the `Human-SIG` directory, entering `Human-SIG` auto-activates it, and outside `Human-SIG` there is no environment (so packages cannot be managed). Use `uv add` to manage packages and `uv run` to run python files. **This is a GitHub repository.**
- `overleaf/` **(The Manuscript):** Contains LaTeX source, generated figures (`.pdf`), and tables (`.tex`). Goal: Final presentation. **CRITICAL: This is a SEPARATE Git repository that is at the SAME LEVEL as `Human-SIG/`, NOT inside it.** The directory structure is:
  ```
  Parent Directory/
  ├── Human-SIG/          # GitHub repository (data and code)
  └── overleaf/           # Separate Git repository (manuscript)
  ```
  **IMPORTANT:** When generating figures or tables, scripts must save them to `../overleaf/images/` and `../overleaf/tables/` (relative to `Human-SIG/`), NOT to `Human-SIG/overleaf/`. The `overleaf/` folder is a completely separate repository and should never be created inside `Human-SIG/`.

### 3. Operational Protocols (Strict Adherence Required)

#### 3.1 Execution Mode & Tooling

- **Execution First:** Do not plan; Execute. The planning is complete. Always translate instructions into Python code, shell commands, and file operations, instead of using your tools to calculate/scrap data yourself.
- **Scraping Protocol:**
  - **Data Acquisition Strategy:** The scraping method for each benchmark is defined in the `scraping_method` field in `Human-SIG/data/metadata.json`. See Step 1.1 for the complete directory structure and Step 2.2 for detailed method descriptions.
  - **Method Determination:** Read the `scraping_method` field from the entry in `metadata.json` to determine which method to use.
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

- **Entity Resolution Halt:** You are FORBIDDEN from using automatic "fuzzy matching" to merge model names without verification. If a benchmark model name does not perfectly match the LMArena ID, you must generate a `pending_resolution.csv` (in Step 3.3.2) and PAUSE to ask the user for confirmation or a manual mapping update.
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

#### 3.6 Order of Benchmarks, Categories and Hypothesis



**MANDATORY ORDERING CONSTRAINTS:** All agent-generated content that involves listing multiple benchmarks, categories, or hypotheses MUST follow the standardized orders specified below. This is a hard requirement for consistency across all outputs.

### Standardized Benchmark and Category Order

The following is the canonical ordering for all benchmarks and LMArena categories. When generating any content that lists benchmarks or categories (tables, figures, text descriptions, code outputs, etc.), you MUST use this exact order:

**Benchmarks (ordered by category, then alphabetically within category):**
1. AIME
2. FrontierMath Tier 1-3
3. FrontierMath Tier 4
4. HMMT (Feb 2025)
5. MATH-500
6. MGSM
7. Aider Polyglot
8. HumanEval
9. IOI
10. LiveCodeBench
11. SciCode
12. SWE-bench (Verified)
13. SWE-bench Bash Only
14. tau2-Bench Telecom
15. Terminal-Bench Hard
16. Terminal-Bench v2.0
17. IFBench
18. IFEval
19. Creative Writing v3
20. WritingBench
21. AA-LCR
22. ARC-AGI-2
23. Arena-Hard (Auto v2.0)
24. FACTS
25. MMLU-Pro
26. GPQA
27. GPQA Diamond
28. Humanity's Last Exam
29. SuperGPQA


**Category Order (for any listing of categories):**
1. Overall
2. Math
3. Coding
4. Instruction Following
5. Creative Writing
6. Hard Prompts
7. Expert

### Standardized Hypothesis Order

When listing or referencing the six hypotheses, they MUST appear in the exact order in Part 1.1 above.

**CRITICAL RULE:** If you are generating any content (tables, figures, code, text) that involves:
- Listing multiple benchmarks → Use the benchmark order above
- Listing multiple categories → Use the category order above
- Listing multiple hypotheses → Use H1-H6 order above
- Listing a subset of benchmarks/categories → Maintain the relative order from the full list above

**Examples of where this applies:**
- Table column/row ordering
- Figure axis labels or legends
- Code variable names or data structures
- Text descriptions listing benchmarks
- Any visualization that displays multiple benchmarks or categories
- Statistical analysis outputs that reference multiple benchmarks


## Part 2: Execution Tasks

### Phase I: System Initialization & File Paths

**Objective:** Initialize the directory structure and configuration files required for the pipeline, ensuring support for advanced statistics and safe LaTeX compilation.

#### Step 1.1: Directory Hierarchy Creation

**Critical Status Note:** The directory structure described below already exists in `Human-SIG/`. Many files and folders are already in place:

- **Already Exists:** 
  - All `input.txt` and `input.html` files in benchmark/category folders
  - All folders and files in `data/raw/` directories
  - `data/metadata.json`
  - Basic folder structure for `src/`, `results/`, `logs/`

- **Need to Create (if not exist):**
  - `data/processed/` subdirectories (`normalized_scores/`, `entity_resolution/`, `master_table/`)
  - Missing scripts in `src/processing/`, `src/analysis/`
  - `schemas/` directory containing schema files

**Directory Structure:** The following structure organizes benchmarks and LMArena categories by data acquisition method. All data files are named `data.csv`. Common code logic is extracted to `src/scrapers/`.

```
Human-SIG/
├── schemas/                   # JSON schema files for data validation
│   ├── metadata_schema.json  # Schema for data/metadata.json
│   └── review_file_schema.json  # Schema for review files
├── data/                      # Data directory (Data only)
│   ├── metadata.json         # Benchmark and LMArena category metadata
│  ├── raw/                   # Raw data
│  │  ├── lmarena/            # LMArena data (lmarena method)
│  │  │   ├── {category_name}/        # category name, for example, LMArena-Overall, LMArena-Coding, etc.
│  │  │   │   ├── input.txt   # User-manually copied <table> element HTML (HTML format text)
│  │  │   │   └── data.csv    # Extracted data file
│  │  ├── artificial_analysis/  # Artificial Analysis unified table extraction
│  │  │   ├── input.txt          # User-manually copied <table> element HTML (unified table, shared by all benchmarks, HTML format text)
│  │  │   └── {benchmark_id}/ # Each benchmark has its own folder
│  │  │       ├── input.txt     # Benchmark description or reference (optional)
│  │  │       └── data.csv      # Extracted data file
│  │  ├── frontiermath/        # FrontierMath (manual_source_code method)
│  │  │   ├── FrontierMath_Tier_1-3/
│  │  │   │   ├── input.txt     # User-manually copied <table> element HTML (HTML format text)
│  │  │   │   └── data.csv      # Extracted data file
│  │  │   └── FrontierMath_Tier_4/
│  │  │       ├── input.txt     # User-manually copied <table> element HTML (HTML format text)
│  │  │       └── data.csv      # Extracted data file
│  │  ├── manual_direct/        # Directly provided data files
│  │  │   └── {benchmark_id}/
│  │  │       └── data.csv      # or data.xlsx (user directly provides, rename if needed)
│  │  ├── pandas_read_html/     # pandas.read_html method
│  │  │   └── {benchmark_id}/
│  │  │       ├── input.txt     # URL file (one line with URL)
│  │  │       └── data.csv      # Scraped data file
│  │  ├── selenium/             # Selenium method
│  │  │   └── {benchmark_id}/
│  │  │       ├── input.txt     # URL file (one line with URL)
│  │  │       └── data.csv      # Scraped data file
│  │  └── vals_ai/              # VALS.ai platform data
│  │      └── {benchmark_id}/
│  │          ├── input.txt     # User-manually copied JSON element (from webpage source code, JSON format text)
│  │          └── data.csv      # Converted data file
│  └── processed/              # Processed data
│      ├── model_extraction/   # LMArena model information (auto-generated)
│      │   └── lmarena_models.json  # Only LMArena extraction file exists; other benchmarks parse directly from cleaned_data.csv
│      ├── cleaned/            # Cleaned benchmark data with scores and rankings
│      │   └── {benchmark_id}/     # One folder per benchmark/category
│      │       ├── cleaned_data.csv    # Model names, scores, and ranks 
│      │       └── mapping.json        # Model name to LMArena model ID mapping 
│      │   └── artificial_analysis/  
│      │       └── cleaned_data.csv  # Unified list for all 10 benchmarks
│      ├── review_files/       # Review files ready for human approval
│      │   └── {benchmark_id}.json  # Auto-reviewed files, except 10 benchmarks in arificial analysis
│      │   └──artificial_analysis.json # All models in artificial analysis, to avoid review the 10 highly-repeated files
│      ├── normalized_scores/
│      └── master_table/
├── src/
│  ├── main.py        # Unified CLI entry point
│  ├── scrapers/      # Scraping logic modules
│  │   ├── selenium_scraper.py
│  │   ├── lmarena_scraper.py
│  │   └── ...
│  ├── processing/     # Data processing scripts (self-contained, no utils folders)
│  └── analysis/      # Scripts for correlations and visualization (to be created)
│    └── multivariate/  # Specific folder for regression models (to be created)
├── results/         # Final output JSONs and CSVs (for data processing only, NOT for manuscript inclusion)
│                    # Note: Tables for manuscript are generated directly to overleaf/tables/ using DataFrame.to_latex()
│                    # Note: Figures for manuscript are generated directly to overleaf/images/
└── logs/           # Error logs and execution traces
```

**Important Notes:**
- All benchmark and category data files are uniformly named `data.csv`.
- Each benchmark/category folder contains: `input.txt` (required, file extension is `.txt`, but content format varies by method) and `data.csv`.
- Common code logic is extracted to `src/scrapers/`. Individual scraper logic is modularized.

#### Step 1.2: Manuscript Structure Creation

Create the following folder structure in `overleaf/`. **Important:** All LaTeX content (except experimental results tables) is contained in a single `acl_latex.tex` file. The `tables/` folder is reserved exclusively for experimental results tables that are automatically generated from statistical analysis.

Plaintext

```
overleaf/
├── images/          # Destination for .pdf plots (generated by code)
├── reference_image/ # Reference images (if any, renamed from existing images/)
├── tables/          # Destination for .tex tables (ONLY for experimental results tables generated by DataFrame.to_latex())
│                    # Note: Non-experimental tables (e.g., benchmark introduction tables) are embedded directly in acl_latex.tex
├── acl_latex.tex    # The main LaTeX file containing all sections (abstract, introduction, methodology, results, discussion, conclusion)
└── main.tex         # The driver file (do not edit directly after init)
```

#### Step 1.3: Configuration Verification (Pre-Flight Check)

- **1.3.1: Verify existence of `Human-SIG/data/metadata.json`.**
  - **Action:** Check that this file exists and contains entries for all benchmarks and LMArena categories.
  - **Schema Reference:** The file structure is defined in `Human-SIG/schemas/metadata_schema.json`. Refer to this schema file for complete field definitions, types, constraints, and descriptions.
  - **Critical Structure Note:** The `metadata.json` file contains multiple types of entries:
    - **meta_info entry:** The first entry contains metadata definitions (prompt_length_standards, category_definitions, scraping_method_definitions) and should not be counted as a benchmark.
    - **Benchmark entries:** These are the benchmarks that will be analyzed. They do NOT have an `elo_column` field.
    - **LMArena entries:** These are metadata entries for LMArena leaderboard categories (LMArena-Overall, LMArena-Math, LMArena-Coding, LMArena-Instruction Following, LMArena-Creative Writing, LMArena-Hard Prompts, LMArena-Expert). They have an `elo_column` field and are processed using the `lmarena` method. They should NOT be processed as benchmarks (see Step 2.2.2 for filtering logic).




#### Step 1.4: Commit State

- **1.4.1:** Stage all created directories and JSON files.
- **1.4.2:** Commit with message: `Step 1.4 Completed: System initialization and file paths created`

### Phase II: Data Acquisition (Completed)

**Status:** Completed.
**Output:** Raw CSV files are populated in `Human-SIG/data/raw/`.

Proceed to **Phase III: Data Processing**.

### Phase III: Data Verification and Preparation for Analysis

**Objective:** Verify that all cleaned data files and model mappings are present and valid before proceeding to master table synthesis and statistical analysis.

**Status:** All data processing scripts have been executed and output files have been generated. This phase only requires verification of file existence and data validity.

#### Step 3.1: Verify Cleaned Data Files

- **3.1.1:** Verify directory structure and file existence.
  - **Action:** Check that `Human-SIG/data/processed/cleaned/` contains:
    - One folder for each benchmark listed in `data/metadata.json` (entries without `elo_column` field).
    - One folder for each LMArena category listed in `data/metadata.json` (entries with `elo_column` field).
    - Each folder must contain a `cleaned_data.csv` file.
    - Each benchmark folder (but NOT LMArena category folders) must contain a `mapping.json` file.
  - **Validation:** 
    - Count the number of folders and verify it matches the expected count (benchmarks + LMArena categories from metadata.json).
    - For each folder, verify that `cleaned_data.csv` exists and contains at least one row of data (header + data rows).
    - For each benchmark folder, verify that `mapping.json` exists and is valid JSON (can be empty `{}` if no mappings exist).
  - **Score Normalization Note:** All benchmark scores in `cleaned_data.csv` files (except Creative Writing v3) have been normalized to the 0-100 scale during data preparation. Specifically, benchmarks using 0-1 scale (FACTS, GPQA, HMMT (Feb 2025), HumanEval, IFEval, SuperGPQA, SWE-bench (Verified), Arena-Hard (Auto v2.0)) have been multiplied by 100. For FACTS, only rows with `Task_Name == "Average"` are included, using the `Numerical_Result` column. All scores (except Creative Writing v3) represent "higher is better" performance after normalization. Creative Writing v3 uses Elo scores and is not normalized to 0-100 range.
  - **Data Source Note:** All subsequent steps (Step 3.2 onwards) read benchmark data exclusively from `cleaned_data.csv` and `mapping.json` files located in `Human-SIG/data/processed/cleaned/{benchmark_id}/`. These are the only source files used for all analysis and feature calculation.


#### Step 3.2: Understand Data File Formats

**Purpose:** The cleaned data files contain standardized benchmark scores and rankings, while mapping files enable entity resolution between benchmark model names and LMArena model IDs.

- **3.2.1:** `cleaned_data.csv` File Format.
  - **Location:** `Human-SIG/data/processed/cleaned/{benchmark_id}/cleaned_data.csv`
  - **Purpose:** Contains all models from a benchmark with their scores and ranks. Used for correlation analysis and ranking calculations.
  - **Format:** Standard CSV with three columns:
    - `model_name`: String, the original model name exactly as it appears in the benchmark leaderboard.

    - `score`: Float, the score value. For all benchmarks except Creative Writing v3, scores have been normalized to 0-100 scale (higher is better). Creative Writing v3 uses Elo scores and is not normalized to 0-100 range.

    - `rank`: Integer, the rank assigned based on score (1 = best, higher numbers = worse). Tied scores receive the same rank, and the next rank skips the tied count (e.g., scores [99, 98, 98, 97] → ranks [1, 2, 2, 4]).
  - **Example:**
    ```csv
    model_name,score,rank
    GPT-5 (high),76.0,1
    GPT-5.1 (high),75.0,2
    Claude Opus 4.5,74.0,3
    KAT-Coder-Pro V1,74.0,3
    GPT-5.2 (xhigh),73.0,5
    ```
  - **Usage:** These files are read in Step 3.3 to build the master correlation matrix. Each benchmark contributes one `{benchmark_id}_score` column and one `{benchmark_id}_rank` column to the master table.

- **3.2.2:** `mapping.json` File Format.
  - **Location:** `Human-SIG/data/processed/cleaned/{benchmark_id}/mapping.json`
  - **Purpose:** Maps benchmark model names to LMArena model IDs. Enables entity resolution so that benchmark scores can be aligned with LMArena ELO scores for correlation analysis.
  - **Format:** JSON object where:
    - **Keys:** Benchmark model names (must exactly match `model_name` values in the corresponding `cleaned_data.csv`).
    - **Values:** LMArena model IDs (model names from LMArena leaderboard, used as keys in the master table).
  - **Example:**
    ```json
    {
      "GPT-5.1 (high)": "gpt-5.1",
      "GPT-5.2 (xhigh)": "gpt-5.2",
      "o3": "o3-2025-04-16",
      "DeepSeek V3.2 Exp": "deepseek-v3.2-exp",
      "Gemini 3 Flash": "gemini-3-flash"
    }
    ```
  - **Important Notes:**
    - Only benchmark folders contain `mapping.json` files. LMArena category folders do NOT have mapping files (because LMArena models can match internally by name).
    - If a benchmark model has no corresponding LMArena model (or the mapping was not confirmed), it will not appear in the mapping file.
    - Model names in the mapping file must exactly match the `model_name` column in the corresponding `cleaned_data.csv` file.
    - The LMArena model IDs in the mapping file are used as row indices in the master table (Step 3.3).
  - **Usage:** These files are read in Step 3.3 to map benchmark model names to LMArena model IDs when building the master correlation matrix. Only models that appear in both the benchmark data (after mapping) and the LMArena Study Universe are included in the master table.

- **3.2.3:** Data Validity Checks.
  - **Action:** For each `cleaned_data.csv` file:
    - Verify that the file is valid CSV (can be parsed without errors).
    - Verify that all three required columns exist: `model_name`, `score`, `rank`.
    - Verify that `score` values are numeric (float) and non-null.
    - Verify that `rank` values are integers and non-null.
    - Verify that ranks are consistent (same scores have same ranks, ranks are sequential with ties handled correctly).
  - **Action:** For each `mapping.json` file:
    - Verify that the file is valid JSON (can be parsed without errors).
    - Verify that all keys (benchmark model names) exist in the corresponding `cleaned_data.csv` file's `model_name` column.
    - Verify that all values (LMArena model IDs) are non-empty strings.
  - **Error Handling:** If any file is missing, invalid, or contains inconsistent data, HALT and report the specific issue. Do not proceed to Step 3.3 until all files are valid.

- **3.2.4:** Commit State.
  - **Message:** `Step 3.2.4 Completed: Verified cleaned data files and mappings are present and valid`


#### Step 3.3: Robust Parsing & Ranking Logic


- **3.3.1:** Create `Human-SIG/src/processing/parser_utils.py`.
  - **Code Documentation Requirements:**
    - File header must explain the purpose (parsing benchmark scores from CSV files for master table construction), that all benchmarks except Creative Writing v3 are normalized to 0-100 range during data preparation, ranking logic, and tie-breaking strategy.
    - All classes and methods must have docstrings.
  - **Class Definition:** Implement `BenchmarkParser`.

  - **Input:** Cleaned data files from `Human-SIG/data/processed/cleaned/{benchmark_id}/cleaned_data.csv`. The parser reads from the cleaned data directory, which contains standardized CSV files with model names, scores, and ranks already extracted and calculated (verified in Step 3.2). All benchmarks except Creative Writing v3 are normalized to 0-100 range.

  - **Ranking Logic:** Compute rank strictly within the Study Universe.
    - **Study Universe Definition:** The "Study Universe" consists of all models in the LMArena dataset with `elo_overall >= 1330`. This Study Universe is defined by the models present in `Human-SIG/data/processed/model_extraction/lmarena_models.json` (which already contains only models with Overall Score >= 1330).
    - **Entity Resolution:** Use the per-benchmark mapping files from `Human-SIG/data/processed/cleaned/{benchmark_id}/mapping.json` (verified in Step 3.2) to map benchmark model names to LMArena model IDs. Only models that can be mapped to the Study Universe are included in ranking.
    - **Ranking Filter:** Only rank models that appear in both the benchmark data (after entity resolution) and the Study Universe. Models that appear in the benchmark but cannot be mapped to the Study Universe should be excluded from ranking.
  - **Tie-Breaking:** Use `method='min'` (e.g., if two models tie for first place with score 95, assign both rank 1, and the next model gets rank 3) to support rigorous RBO calculation. This ensures that tied models receive the same rank, which is important for RBO computation.

  - **Directionality:** When ranking, ensure that higher scores receive better (lower) ranks. All benchmarks (except Creative Writing v3) represent "higher is better" performance, so the ranking logic should always assume "higher score = better rank".
  - **Note:** All benchmarks except Creative Writing v3 are normalized to 0-100 range and stored in CSV files. This parser loads CSV files, performs entity resolution using the mapping table, filters to Study Universe, performs ranking, and outputs data structure transformation. The parser should output both the original scores and the computed ranks.

- **3.3.2:** Commit State.
  - **Message:** `Step 3.3.2 Completed: Implemented BenchmarkParser with ranking logic for RBO calculation`

#### Step 3.4: Master Table Synthesis

- **3.4.1:** Create `Human-SIG/src/processing/build_master_table.py`.
  - **Code Documentation Requirements:**
    - File header must explain the master table structure, the merge strategy (left join to preserve Study Universe), and why both score and rank columns are needed.
    - All functions must have docstrings explaining data transformation steps.
  - **Initialization:** Create the `df_master` DataFrame using LMArena models as the index.
    - **Columns:** `elo_overall`, `elo_math`, `elo_coding`, `elo_instruction_following`, `elo_creative_writing`, `elo_hard_prompts`, `elo_expert` (ordered by standardized category order: Overall, Math, Coding, Instruction Following, Creative Writing, Hard Prompts, Expert).
  - **Merge Loop:** For each benchmark (e.g., HumanEval):
    1. Load parsed data (Score + Rank) from the parser output (created in Step 3.3.1). The parser reads cleaned data files from `Human-SIG/data/processed/cleaned/{benchmark_id}/cleaned_data.csv`, which already contains standardized model names, scores, and ranks.
    2. Map model names using the per-benchmark mapping table from `Human-SIG/data/processed/cleaned/{benchmark_id}/mapping.json` (verified in Step 3.2). This per-benchmark mapping contains benchmark-specific mappings with duplicate handling already applied.
    3. Left Join onto `df_master` (Keep only models present in LMArena Study Universe). Models that appear in the benchmark but cannot be mapped to the Study Universe will be excluded.
    4. **CRITICAL: Filter by Overlap Count:** Before adding columns to the master table, calculate the number of overlapping models ($N$) between the benchmark and the Study Universe (i.e., count non-null values after the left join). If $N < 6$ (insufficient for reliable Spearman correlation analysis), **skip this benchmark entirely** - do not add its score and rank columns to the master table. Log a warning message: "Skipping benchmark {benchmark_id}: insufficient overlap (N={N} < 6) for reliable correlation analysis." Continue to the next benchmark.
    5. Add columns: `{benchmark_id}_score` AND `{benchmark_id}_rank`. (Both are needed: Score for Pearson/Spearman correlation, Rank for RBO calculation). **CRITICAL: benchmark_id Format:** The `benchmark_id` is a string identifier that does NOT use underscores or other separators (e.g., "SWE-bench (Verified)", "HumanEval", "MMLU-Pro"). When using `benchmark_id` as a column name prefix in the master table, you may need to sanitize it (e.g., replace spaces and special characters with underscores) for valid Python/CSV column names, but the original `benchmark_id` value itself should remain unchanged in all data structures and metadata.
    6. Handle missing values: If a model in the Study Universe does not have a score for a particular benchmark, leave the score and rank as `NaN` (do not fill with zeros or default values).
  - **Data Type Enforcement:** Ensure all Score columns are `float64` and Rank columns are `int` (or nullable int).
- **3.4.2:** Data Integrity Check
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
          "description": "Statistics for a single benchmark, keyed by benchmark_id",
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
  - **Warning:** If any benchmark has $N < 6$ (insufficient for reliable correlation analysis), log a CRITICAL WARNING to console and include this information in the overlap stats JSON file. **Note:** Benchmarks with $N < 6$ are automatically excluded from the master table during the merge loop (see Step 3.4.1), so they will not appear in the final master table columns.
- **3.4.3:** Persistence
  - **Output:** Save the master table to `Human-SIG/data/processed/master_table/master_correlation_matrix.csv`. This CSV should contain:
    - One row per model (from the Study Universe)
    - Columns: `model_name`, `elo_overall`, `elo_math`, `elo_coding`, `elo_instruction_following`, `elo_creative_writing`, `elo_hard_prompts`, `elo_expert`, and for each benchmark with $N \geq 6$: `{benchmark_id}_score` and `{benchmark_id}_rank` (benchmarks ordered by standardized category order, then alphabetically within category). **CRITICAL:** Only benchmarks with overlap count $N \geq 6$ are included in the master table (benchmarks with $N < 6$ are filtered out during the merge loop in Step 3.4.1).
    - Missing values should be represented as `NaN` or empty cells (not zeros)
  - **Note:** The overlap statistics JSON file was already saved in Step 3.4.2.
- **3.4.4:** Commit State
  - **Message:** `Step 3.4.4 Completed: Generated master correlation matrix with dual Score/Rank columns`

### Phase IV: Hypothesis Verification & Statistical Analysis (Revised for Small-N Robustness)

Objective: Execute a rigorous statistical verification pipeline specifically tailored for small sample sizes ($N=29$). Instead of a single, brittle multivariate regression which lacks statistical power, you will execute Bootstrapped Univariate Analysis for individual factors and Controlled Bivariate Robust Regression to disentangle confounding factors (specifically Difficulty vs. Variance).

Input:

- `Human-SIG/data/processed/master_table/master_correlation_matrix.csv` (Model Scores & Ranks).


- `Human-SIG/data/metadata.json` (Contains all benchmark metadata including `release_date`, `task_type`, `question_count`, and other metadata fields for all benchmarks).



  Output:

- `Human-SIG/results/statistical_significance_report.json` (Final P-values with Holm-Bonferroni corrections, JSON format for data processing).

- `Human-SIG/results/analysis_ready_data.csv` (The clean dataset used for analysis and plotting, CSV format for data processing).

- `overleaf/images/` (Folder containing all generated PDF figures for the manuscript, saved directly by plotting code).

- `overleaf/tables/` (Folder containing experimental results tables generated using `DataFrame.to_latex()`, saved directly by table generation code. Note: Only experimental results tables belong here; non-experimental tables are embedded directly in `acl_latex.tex`).

**Important:** The `results/` folder contains only JSON and CSV files for data processing and analysis. Experimental results tables that appear in the manuscript are generated directly to `overleaf/tables/` using `DataFrame.to_latex()`, and figures are generated directly to `overleaf/images/`, ensuring all numerical values are exactly as computed by the code.

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
  - `calculate_spearman_with_pvalue(x, y)`: Calculate Spearman rank correlation coefficient and its p-value. **Critical p-value calculation logic:** When $N < 30$ (where $N$ is the number of overlapping models between the benchmark and LMArena), use `scipy.stats.permutation_test` with `permutation_type='pairings'` to compute the p-value. This permutes one ranking under the null hypothesis of independence and recalculates the correlation. When $N \geq 30$, use the p-value returned by `scipy.stats.spearmanr` as a sufficiently accurate approximation. The function must return both the correlation coefficient ($\rho$) and the p-value. Docstring must explain the conditional logic and the rationale for using permutation test for small sample sizes.
  - `calculate_kendall_with_pvalue(x, y)`: Calculate Kendall's $\tau$ correlation coefficient and its p-value. **Critical p-value calculation logic:** When $N < 30$ (where $N$ is the number of overlapping models between the benchmark and LMArena), use `scipy.stats.permutation_test` with `permutation_type='pairings'` to compute the p-value. This permutes one ranking under the null hypothesis of independence and recalculates the correlation. When $N \geq 30$, use the p-value returned by `scipy.stats.kendalltau` as a sufficiently accurate approximation. The function must return both the correlation coefficient ($\tau$) and the p-value. Docstring must explain the conditional logic and the rationale for using permutation test for small sample sizes.
- **4.1.2:** Commit State
  - **Message:** `Step 4.1.2 Completed: Implemented stats utils with RBO, Bootstrap, and Holm-Bonferroni logic`

#### Step 4.2: Feature Engineering with Directionality Guardrails

- **4.2.1:** Create `Human-SIG/src/analysis/compute_features_robust.py`.
  - **Code Documentation Requirements:**
    - File header must explain the complete workflow: loading benchmark data from CSV files (all benchmarks except Creative Writing v3 are normalized to 0-100 scale), reading category from metadata.json to determine correlation target, computing difficulty and variance features, and calculating correlations. All benchmarks (except Creative Writing v3) represent "higher is better" performance.
    - All functions must have docstrings explaining their mathematical operations.
  - **Task A: Score Directionality (All Scores Represent "Higher is Better").**
    - **Prerequisite:** All benchmark scores (except Creative Writing v3) have been normalized to 0-100 scale during data preparation, where higher scores represent better performance. Creative Writing v3 uses Elo scores and is not normalized to 0-100 range. No additional transformation or verification is needed. Simply load the benchmark data from `cleaned_data.csv` files in the appropriate benchmark folders and proceed with feature calculation.
  - **Task B: H6 (Difficulty) Feature Calculation.**
    - **Action:** Calculate `subset_avg_score` using the Common Subset (Models with LMArena `elo_overall` Score between 1400 and 1430, inclusive). This subset was identified in Step 2.1.1 (Filter 2).
    - **Exclusion:** Exclude Creative Writing v3 from Difficulty calculation. Creative Writing v3 is not included in the Difficulty feature computation.
    - **Calculation:** For each benchmark (excluding Creative Writing v3), compute the mean score across all models in the Common Subset that have scores for that benchmark. This mean score is `subset_avg_score`.
    - **Difficulty Definition:** Calculate `Difficulty = 100 - subset_avg_score`. This ensures that higher Difficulty values represent harder benchmarks (higher Difficulty = harder benchmark). For example, a benchmark with `subset_avg_score = 60` has `Difficulty = 40`, while a benchmark with `subset_avg_score = 80` has `Difficulty = 20` (the first is harder).
    - **Safety Check:** If the number of overlapping models in this specific ELO range is $N < 5$ for any benchmark:
      - **Log Warning:** "Insufficient overlap for Difficulty Common Subset (N={actual_N}). 
      - **Flag:** Set column `is_estimated_difficulty = True` to indicate that the difficulty was estimated using the fallback method.
  - **Task C: H5 (Variance) Feature Calculation.**
    - **Action:** Compute the Coefficient of Variation ($CV$) instead of raw variance.
    - **Formula:** $CV = \frac{\sigma}{\mu}$.
    - **Reasoning:** Raw variance penalizes high-accuracy benchmarks (where scores are compressed near 100%). $CV$ normalizes variance relative to the score scale, making "Accuracy" benchmarks comparable to "Perplexity" benchmarks.
- **4.2.2:** Construct Validity Calculation Loop & Sanity Check.
  - **Action:** For each benchmark, calculate Spearman $\rho$ (with p-value), Kendall $\tau$ (with p-value), and RBO between Benchmark_Score (which represents "higher is better" performance; all benchmarks except Creative Writing v3 are normalized to 0-100 scale) and the corresponding LMArena ELO score (representing Perceived Utility). **CRITICAL:** All correlations are computed between each benchmark and its corresponding LMArena category (determined by the `category` field in metadata.json). NO benchmark should be compared with LMArena-Overall; each benchmark is compared only with its specific category (e.g., Math benchmarks with `elo_math`, Coding benchmarks with `elo_coding`). The correlation category for each benchmark is determined by the `category` field in metadata.json, which maps to the corresponding ELO column (listed in standardized category order):
    - "Math" -> `elo_math`
    - "Coding" -> `elo_coding`
    - "Instruction Following" -> `elo_instruction_following`
    - "Creative Writing" -> `elo_creative_writing`
    - "Hard Prompts" -> `elo_hard_prompts`
    - "Expert" -> `elo_expert`
  - **Data Source:** Load benchmark scores from `Human-SIG/data/processed/master_table/master_correlation_matrix.csv` (which contains the scores after entity resolution and merging).
  - **Missing Data Handling:** Only include models that have both benchmark scores and the corresponding LMArena ELO scores (exclude rows with NaN in either column).
  - **P-value Calculation (CRITICAL):** For each Spearman and Kendall correlation calculation, you MUST compute the p-value using the functions defined in Step 4.1.1 (`calculate_spearman_with_pvalue` and `calculate_kendall_with_pvalue`). The p-value calculation follows this logic:
    - When $N < 30$ (where $N$ is the number of overlapping models between the benchmark and LMArena), use `scipy.stats.permutation_test` with `permutation_type='pairings'` to compute the p-value. This permutes one ranking under the null hypothesis of independence and recalculates the correlation.
    - When $N \geq 30$, use the p-value returned by `scipy.stats.spearmanr` or `scipy.stats.kendalltau` as a sufficiently accurate approximation.
  - **Confidence Interval Calculation (CRITICAL):** For each Spearman and Kendall correlation coefficient, you MUST compute 95% bootstrap confidence intervals using the `bootstrap_ci` function defined in Step 4.1.1. Use 5000 bootstrap iterations (with replacement) to derive the confidence intervals. This provides uncertainty quantification for correlation estimates, which is critical for interpreting the strength and reliability of relationships between benchmarks and Perceived Utility. The bootstrap procedure resamples the paired data (benchmark scores and LMArena ELO scores) 5000 times, recalculates the correlation for each bootstrap sample, and uses the 2.5th and 97.5th percentiles of the bootstrap distribution as the lower and upper bounds of the 95% confidence interval.
  - **Store Results:** Save the correlation coefficients (Spearman $\rho$ and Kendall $\tau$), their p-values, AND their 95% confidence intervals for each benchmark in the analysis_ready_data.csv file, along with the difficulty, variance, and other features computed in Tasks A, B, and C. **CRITICAL:** For each benchmark, you must also store the sample size ($N$) - the number of overlapping models between the benchmark and the corresponding LMArena category used for correlation calculation. This $N$ value represents the number of data points used to compute the Spearman and Kendall correlation coefficients. **CRITICAL:** For each correlation metric, you must store:
    - `spearman_rho`: Spearman correlation coefficient
    - `spearman_pvalue`: P-value for Spearman correlation
    - `spearman_ci_lower`: Lower bound of 95% bootstrap confidence interval for Spearman correlation
    - `spearman_ci_upper`: Upper bound of 95% bootstrap confidence interval for Spearman correlation
    - `kendall_tau`: Kendall's $\tau$ correlation coefficient
    - `kendall_pvalue`: P-value for Kendall correlation
    - `kendall_ci_lower`: Lower bound of 95% bootstrap confidence interval for Kendall correlation
    - `kendall_ci_upper`: Upper bound of 95% bootstrap confidence interval for Kendall correlation
  - **Halt Protocol:** Identify a known high-quality benchmark (e.g., MMLU-Pro or HumanEval) that should have high Spearman correlation with LMArena scores.
    - Calculate Spearman correlation (with p-value) between the benchmark scores (which represent "higher is better" performance; all benchmarks except Creative Writing v3 are normalized to 0-100 scale) and the corresponding LMArena ELO scores (determined by the benchmark's `category` field in metadata.json, representing Perceived Utility).
    - If Spearman Correlation $< 0.5$: HALT EXECUTION IMMEDIATELY.
    - **Print:** "CRITICAL: Detected low Spearman correlation (< 0.5) for high-quality benchmark {benchmark_id}. This suggests a data quality issue. Please check: (1) that the correct LMArena ELO column is being used based on the benchmark's category, and (2) that data is loaded correctly from cleaned_data.csv files."
    - **Wait for User:** Do not proceed until resolved. The user must verify and fix the data issue before continuing.
- **4.2.3:** Persistence.
  - **Output:** Save the fully engineered table to `Human-SIG/results/analysis_ready_data.csv`.
  - **CSV Column Structure:** The output CSV file must contain the following columns for each benchmark:
    - `benchmark_id`: Benchmark identifier (string format, no underscores or other separators, e.g., "SWE-bench (Verified)")
    - `subset_avg_score`: Mean score across Common Subset models (as computed in Task B). Used to calculate Difficulty.
    - `difficulty`: Difficulty feature calculated as $Difficulty = 100 - subset\_avg\_score$ (as computed in Task B). Higher values indicate harder benchmarks.
    - `is_estimated_difficulty`: Boolean flag (True if fallback method was used due to insufficient Common Subset overlap, False otherwise)
    - `cv` or `coefficient_of_variation`: Variance feature (Coefficient of Variation, as computed in Task C). Formula: CV = $\sigma$/$\mu$, where $\sigma$ is standard deviation and $\mu$ is mean score.
    - `n` or `sample_size`: The number of overlapping models ($N$) between the benchmark and the corresponding LMArena category used for correlation calculation. This represents the number of data points used to compute the Spearman and Kendall correlation coefficients.
    - `spearman_rho`: Spearman rank correlation coefficient between benchmark scores and corresponding LMArena ELO scores
    - `spearman_pvalue`: P-value for the Spearman correlation (computed using the logic in Step 4.2.2: permutation test when N < 30, scipy.stats.spearmanr p-value when N >= 30)
    - `spearman_ci_lower`: Lower bound of 95% bootstrap confidence interval for Spearman correlation (computed using 5000 bootstrap iterations)
    - `spearman_ci_upper`: Upper bound of 95% bootstrap confidence interval for Spearman correlation (computed using 5000 bootstrap iterations)
    - `kendall_tau`: Kendall's $\tau$ correlation coefficient
    - `kendall_pvalue`: P-value for the Kendall correlation (computed using the logic in Step 4.2.2: permutation test when N < 30, scipy.stats.kendalltau p-value when N >= 30)
    - `kendall_ci_lower`: Lower bound of 95% bootstrap confidence interval for Kendall correlation (computed using 5000 bootstrap iterations)
    - `kendall_ci_upper`: Upper bound of 95% bootstrap confidence interval for Kendall correlation (computed using 5000 bootstrap iterations)
    - `rbo`: Rank-Biased Overlap (p=0.9)
    - Additional metadata columns from metadata.json (e.g., `release_date`, `task_type`, `prompt_length`, `question_count`, `category`)
  - **Data Format:** All numerical values should be stored as floats. Boolean values can be stored as True/False or 1/0. Missing values should be represented as empty cells or NaN.
  - **Important Note:** This CSV file is for data processing and analysis purposes only. Any tables that will be directly included in the manuscript must be generated using `DataFrame.to_latex()` and saved directly to `overleaf/tables/` as `.tex` files (see Step 4.4.2b and Step 5.4.2 for table generation). Do NOT create CSV files in `results/` that contain the same data as LaTeX tables.
  - **Message:** `Step 4.2.3 Completed: Computed robust features (Difficulty, CV) and correlation coefficients`

#### Step 4.3: Hypothesis Testing Strategy (The Small-N Protocol)

- **4.3.0:** Create `Human-SIG/src/analysis/small_n_hypothesis_test.py`.
  - **Code Documentation Requirements:**
    - File header must explain why small-N protocols are needed, the statistical power limitations, and the rationale for targeted tests instead of multivariate regression.
    - Each test function must have docstrings explaining the statistical test, its assumptions, and interpretation.
  - **Context:** Since $N=29$ is too small for a 6-variable regression (Rule of thumb: 10 samples per variable), you must execute Targeted Tests for each hypothesis.
  - **Global Settings:** `n_bootstraps = 5000`, `alpha = 0.05`.
  - **Test Execution Order:** All hypothesis tests must be executed in the order H1, H2, H3, H4, H5, H6 (as defined in Part 1.1).
- **4.3.1:** Test Execution: H1 (Generative vs. MCQ) - The "Group" Test.
  - **Model:** Categorical comparison using the `task_type` field from `Human-SIG/data/metadata.json`.
    - **Group A (Generative):** Benchmarks with `task_type == "Generation"` or `task_type == "Agentic"` (generative tasks). These two task types are merged into a single "Generative" category for analysis.
    - **Group B:** Benchmarks with `task_type == "MCQ"` (multiple choice tasks).
    - **Exclusion Rule:** Benchmarks with `task_type == "Mixed"` must be **excluded** from this analysis. Do not include them in either group. Log the number of excluded Mixed benchmarks for transparency, but do not ask for user guidance.
  - **Guardrail:** Sample Imbalance Check
  - **Action:** Count samples in Group A ($N_A$) and Group B ($N_B$) after excluding "Mixed" benchmarks.

    - ELSE:
      - Proceed with Mann-Whitney U Test (also known as Wilcoxon rank-sum test).
      - **Test Details:** Use `scipy.stats.mannwhitneyu` with `alternative='two-sided'` to test whether the distribution of correlation metrics differs between Group A (Generative) and Group B (MCQ). **CRITICAL: Multi-Metric Analysis:** Perform the test three times, once for each correlation metric (Spearman $\rho$, Kendall $\tau$, RBO). Report results for all three metrics.
  - **Reasoning:** Non-parametric tests lose validity when one group is essentially anecdotal (e.g., 3 benchmarks). The Mann-Whitney U test is appropriate for comparing two independent groups when the normality assumption may not hold.
  - **Action:** Compare the distribution of correlation metrics (Spearman rho, Kendall tau, RBO computed in Step 4.2.2) between the two groups. Perform the test separately for each metric. Store the test statistic, p-value, and effect size (e.g., rank-biserial correlation) for all three metrics. Report results from all three metrics in the output.
- **4.3.2:** Test Execution: H2 (Scale) - The "Scale" Test.
  - **CRITICAL: Multi-Metric Analysis:** Perform the correlation analysis three times, once for each metric. Report results for all three metrics.
  - **Model:** Pearson Correlation between $\log(N_{samples})$ and correlation metrics (Spearman $\rho$, Kendall $\tau$, RBO).
  - **Variable Definition:** $N_{samples}$ is the `question_count` field from metadata.json. Apply natural logarithm transformation: $\log(N_{samples}) = \ln(question\_count)$.
  - **Analysis:** Compute Pearson correlation between $\log(N_{samples})$ and Spearman rho, Kendall tau, and RBO separately. For Spearman and Kendall, compute p-values using `scipy.stats.pearsonr`. RBO does not have a p-value, report only the correlation coefficient.
  - **Output:** Store the correlation coefficients and p-values (for Spearman and Kendall) for all three metrics. Report results from all three metrics in the output.
- **4.3.3:** Test Execution: H3 (Complexity) - The "Complexity" Test.
  - **CRITICAL: Multi-Metric Analysis:** Perform the test three times, once for each correlation metric (Spearman $\rho$, Kendall $\tau$, RBO). Report results for all three metrics.
  - **Rationale:** Treating `prompt_length` as an ordinal variable with equal spacing (1, 2, 3, 4) assumes that the difference between "Short" and "Medium" is the same as between "Long" and "Extreme", which may not be valid. Instead, use a categorical approach.
  - **Method:** Use Kruskal-Wallis H-test (non-parametric one-way ANOVA) to test whether the distribution of correlation metrics differs across the four `prompt_length` categories: "Short", "Medium", "Long", "Extreme". Perform the test separately for Spearman rho, Kendall tau, and RBO.
  - **Implementation:** 
    - Group benchmarks by `prompt_length` category.
    - Extract the correlation metric values (Spearman rho, Kendall tau, RBO from Step 4.2.2) for each group.
    - Use `scipy.stats.kruskal` to test the null hypothesis that all groups have the same distribution for each metric separately.
    - If the test is significant (p < 0.05) for any metric, perform post-hoc pairwise comparisons using Mann-Whitney U tests (with Bonferroni correction for multiple comparisons) to identify which categories differ.
  - **Output:** Store the Kruskal-Wallis test statistic, p-value, and post-hoc comparison results (if applicable) for all three metrics. Report results from all three metrics in the output.
- **4.3.4:** Test Execution: H4 (Recency) - The "Trend" Test.
  - **CRITICAL: Multi-Metric Analysis:** Perform the correlation analysis three times, once for each metric (Spearman $\rho$, Kendall $\tau$, RBO). Report results for all three metrics.
  - **Model:** Univariate Spearman Correlation between Release_Date_Ordinal and correlation metrics (Spearman $\rho$, Kendall $\tau$, RBO).
  - **Variable Construction:** 
    - `Release_Date_Ordinal`: Convert `release_date` from metadata.json (YYYY-MM-DD format) to ordinal days since a reference date (e.g., days since 2020-01-01, or simply use the date as a numeric value).
    - Use correlation metrics from Step 4.2.2: `spearman_rho`, `kendall_tau`, and `rbo` (the correlations between the benchmark scores and the corresponding LMArena ELO scores).
  - **Analysis:** Compute Spearman correlation between Release_Date_Ordinal and each of the three correlation metrics separately:
    - Release_Date_Ordinal vs Spearman rho
    - Release_Date_Ordinal vs Kendall tau
    - Release_Date_Ordinal vs RBO
  - **P-value Calculation:** For Spearman and Kendall correlations, compute the p-value using the same logic as in Step 4.2.2: permutation test when N < 30, scipy.stats.spearmanr/scipy.stats.kendalltau p-value when N >= 30. Note: For H4, N = 29 (number of benchmarks), so use scipy.stats.spearmanr/scipy.stats.kendalltau p-value. RBO does not have a p-value, report only the correlation coefficient.
  - **Confidence Interval Calculation:** For Spearman and Kendall correlations, resample the 29 benchmarks 5000 times (with replacement) using the `bootstrap_ci` function from Step 4.1.1 to derive 95% Confidence Intervals. RBO does not have confidence intervals. Store both the point estimate, the p-value (for Spearman and Kendall), and the confidence interval (ci_lower, ci_upper for Spearman and Kendall) for all three metrics.
- **4.3.5:** Test Execution: H5 (Variance) & H6 (Difficulty) - The "Difficulty-Variance Joint" Test.
  - **Exclusion:** Exclude Creative Writing v3 from this analysis. Only include benchmarks for which Difficulty was calculated in Step 4.2.1 Task B.
  - **Hypothesis:** Harder benchmarks (higher Difficulty values) contribute negatively to correlation with Perceived Utility (H6), but variance (CV) also drives correlation (H5). These factors are often collinear (floor effects reduce variance in high-accuracy benchmarks). This test examines the joint effect of Difficulty and Variance on correlation with Perceived Utility.
  - **CRITICAL: Multi-Metric Analysis:** Perform the regression analysis three times, once for each correlation metric (Spearman $\rho$, Kendall $\tau$, RBO). For regression models, use each metric as the dependent variable separately. Report results for all three metrics.
  - **Model:** Run a Bivariate Robust Regression using `statsmodels.RLM` with Huber's t-criterion for robust estimation. Perform the regression separately for each correlation metric:
    - Primary: $Spearman\_rho \sim \beta_1 \cdot Difficulty + \beta_2 \cdot CV + \epsilon$
    - Robustness check 1: $Kendall\_tau \sim \beta_1 \cdot Difficulty + \beta_2 \cdot CV + \epsilon$
    - Robustness check 2: $RBO \sim \beta_1 \cdot Difficulty + \beta_2 \cdot CV + \epsilon$
  - **Equation Parameters:**
    - $Difficulty = 100 - subset\_avg\_score$ (as computed in Step 4.2.1 Task B). Higher values represent harder benchmarks.
    - $CV$ is the Coefficient of Variation computed in Task C.
    - $\epsilon$ is the error term.
  - **Action:** Store the p-values and coefficients for both $\beta_1$ and $\beta_2$ for each of the three regression models (Spearman, Kendall, RBO), along with their 95% bootstrap confidence intervals. Report results from all three metrics in the output.
  - **Criteria:** H6 is supported only if $\beta_1$ is significant (p < 0.05 before correction) and negative (higher Difficulty correlates with lower correlation) while controlling for CV in at least one metric (preferably Spearman, with Kendall and RBO as robustness checks). H5 is supported if $\beta_2$ is significant while controlling for Difficulty in at least one metric.
- **4.3.6:** Commit State
  - **Message:** `Step 4.3.6 Completed: Executed targeted Small-N statistical tests in H1-H6 order (Mann-Whitney, Pearson, Kruskal-Wallis, Spearman, and Robust Regression for Difficulty-Variance joint test)`

#### Step 4.4: Correction, Reporting & Visualization

- **4.4.1:** Multiple Comparison Correction (Anti-Hallucination).

  - **Logic:** You performed 5+ distinct statistical tests. This increases the risk of Type I errors (false positives).

  - **Action:** Load the raw p-values from Step 4.3.

  - **Algorithm:** Apply Holm-Bonferroni Correction.

    - Sort p-values from smallest to largest.
    - Adjust criteria: $\alpha_{corrected} = \frac{\alpha}{m - rank + 1}$.

  - **Output:** Generate `Human-SIG/results/statistical_significance_report.json` (this file will be referenced in Phase V for results reporting).

  - **Structure:** The JSON file must contain entries for all six hypotheses (H1-H6). **CRITICAL:** Since all hypothesis tests are performed using three correlation metrics (Spearman $\rho$, Kendall $\tau$, RBO), include separate entries for each metric. For example, H1 Spearman, H1 Kendall, H1 RBO. For H6 and H5 (regression models), include separate entries for each coefficient and each metric (e.g., H6 Difficulty Beta1 Spearman, H6 Difficulty Beta1 Kendall, H6 Difficulty Beta1 RBO, H5 Variance Beta2 Spearman, H5 Variance Beta2 Kendall, H5 Variance Beta2 RBO). The schema is:
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
              "description": "Sample size for this specific test"
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
  - **CRITICAL: Output Path:** All figures must be saved directly to `../overleaf/images/` directory (relative to `Human-SIG/`), NOT to `Human-SIG/overleaf/images/`. The `overleaf/` folder is a separate Git repository at the same level as `Human-SIG/`. If an `overleaf/images/` directory does not exist, create it. If an existing `overleaf/images/` folder contains reference images, rename it to `overleaf/reference_image/` first.
  - **CRITICAL: Logging Requirement:** Before executing any plotting command (e.g., `plt.scatter()`, `sns.regplot()`, `sns.boxplot()`, `plt.plot()`, etc.), you MUST print a log message to the console that clearly states:
    - Which data sources are being used (e.g., "Using data from analysis_ready_data.csv: Difficulty column and Spearman rho column")
    - What type of plot is being generated (e.g., "scatter plot", "regression plot", "boxplot", "histogram", "heatmap")
    - Example format: `print("Generating scatter plot using data: Difficulty (from analysis_ready_data.csv) vs Spearman rho (from analysis_ready_data.csv)")`
    - This logging serves two purposes: (1) It is a good logging practice that allows humans to see what data is being used for plotting by checking the console output, providing transparency and confidence in the visualization process; (2) It helps the agent itself see and understand what data is being used, which can prevent errors and improve code clarity.
  - **CRITICAL: Axis Labels and Legend Names:** All axis labels, legend labels, and category names in figures must use spaces instead of underscores for readability (e.g., "Task Type" instead of "task_type", "Prompt Length" instead of "prompt_length", "Benchmark ID" instead of "benchmark_id"). Do not remove parentheses, single quotes, or other characters from names. This applies to all matplotlib/seaborn plot elements including xlabel, ylabel, legend labels, tick labels, and any text annotations.
  - **Figure 0 (SWE-bench Illustration):**
    - **Overall Purpose:** This figure visualizes the ranking correlation between SWE-bench (Verified) and LMArena-Coding by comparing model rankings in both leaderboards.
    - **Data Processing:**
      1. Load SWE-bench (Verified) data from `Human-SIG/data/processed/cleaned/SWE-bench (Verified)/cleaned_data.csv` (contains `model_name`, `score`, `rank` columns).
      2. Load LMArena-Coding data from `Human-SIG/data/processed/cleaned/LMArena-Coding/cleaned_data.csv` (contains `model_name`, `score`, `rank` columns).
      3. Load mapping from `Human-SIG/data/processed/cleaned/SWE-bench (Verified)/mapping.json` to get the intersection of models (models that appear in both leaderboards after entity resolution). The intersection consists of all models that have entries in the mapping.json file.
      4. For each model in the intersection:
         - Extract its rank in SWE-bench (Verified) (from the `rank` column in cleaned_data.csv, using the benchmark model name as key).
         - Extract its rank in LMArena-Coding (map the SWE-bench model name to LMArena model ID using mapping.json, then find the rank in LMArena-Coding cleaned_data.csv using the LMArena model ID).
      5. If there are n models in the intersection, there will be n pairs of ranks (each model has two ranks: one from SWE-bench, one from LMArena-Coding). These ranks will be in the range [1, n] after re-ranking within the intersection subset.
      6. **CRITICAL: Re-ranking within Intersection:** After identifying the intersection of models, re-rank the models within this subset for both leaderboards. For SWE-bench (Verified), re-rank the models in the intersection based on their scores (lower rank = better performance). For LMArena-Coding, re-rank the models in the intersection based on their scores (lower rank = better performance). This ensures that both axes show ranks from 1 to n within the intersection subset.
    - **Figure Components:**
      1. **Scatter Plot:** Each point represents one model in the intersection, with:
         - X-coordinate: Rank in SWE-bench (Verified) (re-ranked within the intersection subset, from 1 to n)
         - Y-coordinate: Rank in LMArena-Coding (re-ranked within the intersection subset, from 1 to n)
      2. **Model Name Annotations:** For each point, annotate the model name (use the LMArena model ID from mapping.json, or the original model name if preferred). **CRITICAL: Font Size:** Use significantly larger font size (at least 16pt) for model name annotations to ensure readability.
      3. **X-axis:** Label as "Rank in SWE-bench (Verified) (Weak → Strong)" (origin = weak models with high ranks, far end = strong models with low ranks).
      4. **Y-axis:** Label as "Rank in LMArena-Coding (Weak → Strong)" (origin = weak models with high ranks, far end = strong models with low ranks).
      5. **Axis Configuration:**
         - Both axes start from rank 1 (best performance, lowest rank number).
         - Tick marks: Label every 5 ranks starting from 1 (i.e., 1, 6, 11, 16, 21, ...).
         - Grid lines: Use light gray lines for tick marks (grid lines at each tick position, using light gray color).
         - Chart borders: Do NOT close the top and right borders (only show bottom and left borders). Use `ax.spines['top'].set_visible(False)` and `ax.spines['right'].set_visible(False)`.
      6. **Reference Line:** Draw a red dashed line for y=x (diagonal reference line) and create a legend for it. Use `plt.plot()` or `ax.plot()` with `linestyle='--'`, `color='red'`, and create a legend using `matplotlib.lines.Line2D` to show a red dashed line example. **CRITICAL: Legend Position:** The y=x legend must be positioned in the bottom right corner of the plot (using `loc='lower right'`). **CRITICAL: Font Size:** The legend font size must be larger (at least 18pt) for readability.
      7. **Spearman Correlation Annotation:** Calculate the Spearman correlation coefficient between the re-ranked SWE-bench (Verified) ranks and LMArena-Coding ranks using `scipy.stats.spearmanr()`. Display the correlation coefficient in the **top left corner** of the plot (using `transform=ax.transAxes` with coordinates like `(0.02, 0.98)`) with format "Spearman ρ = {value:.3f}". Use larger font size (at least 18pt) and a white background box for visibility.
      8. **NO TITLE:** Do not include a figure title in the plot itself. The title will be provided in the LaTeX caption. However, when logging progress to the terminal, clearly state the figure name/title (e.g., "Generating Figure 0: SWE-bench (Verified) Illustration").
      9. **CRITICAL: Layer Ordering:** All scatter plot points must be on the topmost layer (highest zorder, e.g., `zorder=5`) so they are never covered by text annotations or white boxes. Text annotations should have lower zorder (e.g., `zorder=4`) and reference lines should have even lower zorder (e.g., `zorder=1` or `zorder=2`).
      10. **Figure Aspect Ratio:** The figure should be wider/flatter. Use `figsize=(12, 7)` or similar to create a wider aspect ratio.
    - **Data Source:** 
      - SWE-bench (Verified): `Human-SIG/data/processed/cleaned/SWE-bench (Verified)/cleaned_data.csv` and `mapping.json`
      - LMArena-Coding: `Human-SIG/data/processed/cleaned/LMArena-Coding/cleaned_data.csv`
    - **Save Location:** `../overleaf/images/Figure_0_SWE_Bench_Illustration.pdf` (relative to `Human-SIG/`, since `overleaf/` is a separate repository at the same level)
    - **CRITICAL: All Annotations Required:** Every element must be annotated: axis labels with direction indicators, model name labels for each point, reference line annotation, and grid lines.

  - **Figure 1 (H1 - Task Type Comparison):**
    - **Overall Purpose:** This figure visualizes H1 (The Generative Hypothesis) by comparing the distribution of Spearman correlation coefficients (between benchmark scores and Perceived Utility) across two task type groups: MCQ (multiple choice) and Generative (which includes both "Generation" and "Agentic" task types merged together).
    - **Figure Components:**
      1. **Boxplot:** For each task type group (MCQ and Generative), display a boxplot showing the distribution of Spearman rho values. The boxplot should show: median (center line), quartiles (box edges), and whiskers (extending to 1.5×IQR or data range). **CRITICAL: Color Scheme:** Use different light colors for different task type groups (e.g., light blue for MCQ, light green for Generative) to ensure boxes and points are clearly visible. Use `sns.boxplot()` with `palette` parameter to specify colors.
      - **CRITICAL: Boxplot Color Explanation for Manuscript:** The colored boxes in the boxplot represent the interquartile range (IQR) for each task type group. The box edges indicate the first quartile (Q1, bottom edge) and third quartile (Q3, top edge), while the center line represents the median. The different colors (light blue for MCQ, light green for Generative) help visually distinguish between the two groups. This should be explained in the Results section when describing Figure 1: "The colored boxes represent the interquartile range (IQR) for each task type, with the center line indicating the median Spearman correlation coefficient. Light blue represents MCQ benchmarks, while light green represents Generative benchmarks."
      2. **Stripplot (overlaid):** Overlay individual data points (each point represents one benchmark) on top of the boxplot to show the actual distribution and sample size. Use jitter to avoid overlapping points. **CRITICAL: Color Scheme:** Use the same light colors as the boxplot for consistency, or use a neutral color (e.g., black or dark gray) with transparency to ensure points are clearly visible.
      3. **X-axis:** Task Type categories ("MCQ" and "Generative"), with clear labels using spaces (not underscores).
      4. **Y-axis:** Spearman rho values, labeled as "Spearman ρ" or "Spearman Correlation Coefficient", with appropriate range and tick marks.
      5. **NO TITLE:** Do not include a figure title in the plot itself. The title will be provided in the LaTeX caption. However, when logging progress to the terminal, clearly state the figure name/title (e.g., "Generating Figure 1: Spearman rho by Task Type").
      6. **Annotations:** Add text annotations or callouts explaining key features:
         - Sample size (N) for each group (position annotations OUTSIDE the plot area, e.g., above the plot or in the margins, to avoid overlapping with the plot area)
         - Median values for each group (position annotations OUTSIDE the plot area, e.g., above the plot or in the margins, to avoid overlapping with the plot area)
         - Any statistical test results (e.g., Mann-Whitney U test p-value) if space permits (also position outside the plot area)
      7. **CRITICAL: Annotation Positioning:** The Median and N annotations must be positioned OUTSIDE the plot area (e.g., in the margins or above the plot) to avoid blocking the visualization. Do not place annotations inside the plot area where they might overlap with data points or boxes.
    - **Data Source:** Load from `analysis_ready_data.csv`: `task_type` column (filter out "Mixed"), `spearman_rho` column.
    - **Exclusion Rule:** Benchmarks with `task_type == "Mixed"` must be excluded from the plot.
    - **Save Location:** `overleaf/images/Figure_1_Task_Type.pdf`
    - **CRITICAL: All Annotations Required:** Every element in the figure must be clearly labeled and annotated. This includes: axis labels with units/descriptions, legend (if applicable), group labels, sample sizes, and any statistical annotations.

  - **Figure 2 (H2 - Scale Effect):**
    - **Overall Purpose:** This figure visualizes H2 (The Scale Hypothesis) by showing the relationship between benchmark scale (log-transformed question count) and Spearman correlation with Perceived Utility. It tests whether larger benchmarks (more test items) show higher correlation with Perceived Utility.
    - **Figure Components:**
      1. **Scatter Plot:** Each point represents one benchmark, with:
         - X-coordinate: log(question_count) - the natural logarithm of the number of test items
         - Y-coordinate: Spearman rho - the correlation coefficient between benchmark scores and Perceived Utility
      2. **Regression Line (optional but recommended):** Overlay a regression line (using `sns.regplot()` or `plt.plot()` with fitted line) to show the trend. Include 95% confidence interval band around the regression line if using `sns.regplot()`.
      - **CRITICAL: Confidence Interval Band Explanation for Manuscript:** The red shaded region around the regression line represents the 95% confidence interval for the predicted Spearman correlation coefficient at each value of log(question_count). This band quantifies the uncertainty in the regression prediction: a narrower band indicates more precise predictions, while a wider band indicates greater uncertainty. The confidence interval is computed using bootstrap resampling or standard regression error estimation. This should be explained in the Results section when describing Figure 2: "The red shaded region represents the 95% confidence interval for the regression line, indicating the uncertainty in the predicted relationship between benchmark scale and Spearman correlation with Perceived Utility."
      3. **X-axis:** Label as "log(Question Count)" or "Scale (log-transformed question count)", with clear tick marks and values.
      4. **Y-axis:** Label as "Spearman ρ" or "Spearman Correlation Coefficient", with appropriate range.
      5. **NO TITLE:** Do not include a figure title in the plot itself. The title will be provided in the LaTeX caption.
      6. **Annotations:**
         - Pearson correlation coefficient and p-value (if computed)
         - Sample size (N = number of benchmarks)
         - Regression equation or slope coefficient if regression line is shown
         - Individual benchmark labels (benchmark_id) as text annotations or tooltips (if not too crowded)
         - **CRITICAL: Annotation Position:** All statistical annotations (correlation coefficient, p-value, sample size) must be positioned in the **bottom left corner** of the plot (using `transform=ax.transAxes` with coordinates like `(0.05, 0.05)`).
      7. **CRITICAL: Layer Ordering:** All scatter plot points must be on the topmost layer (highest zorder, e.g., `zorder=5`) so they are never covered by text annotations or white boxes. Text annotations should have lower zorder (e.g., `zorder=4`) and regression lines should have lower zorder (e.g., `zorder=1`).
    - **Data Source:** Load from `analysis_ready_data.csv`: `question_count` column (apply log transformation), `spearman_rho` column.
    - **Save Location:** `overleaf/images/Figure_2_Scale.pdf`
    - **CRITICAL: All Annotations Required:** Every element must be annotated: axis labels with descriptions, regression line (if shown) with equation/statistics, correlation coefficient, sample size, and any benchmark labels.

  - **Figure 3 (H3 - Complexity Categories):**
    - **Overall Purpose:** This figure visualizes H3 (The Prompt Complexity Hypothesis) by comparing Spearman correlation distributions across four prompt complexity categories (Short, Medium, Long, Extreme). It tests whether more complex prompts lead to higher correlation with Perceived Utility.
    - **Figure Components:**
      1. **Boxplot:** For each of the four `prompt_length` categories ("Short", "Medium", "Long", "Extreme"), display a boxplot showing the distribution of Spearman rho values. Show median, quartiles, and whiskers. **CRITICAL: Color Scheme:** Use different light colors for different prompt length categories (e.g., light blue for Short, light green for Medium, light orange for Long, light red for Extreme) to ensure boxes and points are clearly visible. Use `sns.boxplot()` with `palette` parameter to specify colors.
      - **CRITICAL: Boxplot Color Explanation for Manuscript:** The colored boxes in the boxplot represent the interquartile range (IQR) for each prompt complexity category. The box edges indicate the first quartile (Q1, bottom edge) and third quartile (Q3, top edge), while the center line represents the median. Different colors are used to distinguish between the four categories: light blue for Short prompts, light green for Medium prompts, light orange for Long prompts, and light yellow for Extreme prompts. This should be explained in the Results section when describing Figure 3: "The colored boxes represent the interquartile range (IQR) for each prompt complexity category, with the center line indicating the median Spearman correlation coefficient. Colors distinguish the four categories: light blue (Short), light green (Medium), light orange (Long), and light yellow (Extreme)."
      2. **Stripplot (overlaid):** Overlay individual data points (each benchmark) on top of boxplots with jitter to show actual distribution. **CRITICAL: Color Scheme:** Use the same light colors as the boxplot for consistency, or use a neutral color (e.g., black or dark gray) with transparency to ensure points are clearly visible. **CRITICAL:** The stripplot colors must match the boxplot colors for each category to ensure visual consistency and clarity.
      3. **X-axis:** Prompt Length categories ("Short", "Medium", "Long", "Extreme"), ordered logically, with clear labels.
      4. **Y-axis:** Spearman rho values, labeled as "Spearman ρ" or "Spearman Correlation Coefficient".
      5. **NO TITLE:** Do not include a figure title in the plot itself. The title will be provided in the LaTeX caption. However, when logging progress to the terminal, clearly state the figure name/title (e.g., "Generating Figure 3: Spearman rho by Prompt Length").
      6. **Annotations:**
         - Sample size (N) for each category
         - Median values for each category
         - Kruskal-Wallis test statistic and p-value (if space permits)
         - Post-hoc pairwise comparison results (if significant differences found) using brackets or text annotations
    - **Data Source:** Load from `analysis_ready_data.csv`: `prompt_length` column, `spearman_rho` column.
    - **Save Location:** `overleaf/images/Figure_3_Complexity_Categories.pdf`
    - **CRITICAL: All Annotations Required:** All elements must be annotated: axis labels, category labels, sample sizes, medians, statistical test results, and any significant pairwise differences.

  - **Figure 4 (H4 - Recency Effect):**
    - **Overall Purpose:** This figure visualizes H4 (The Recency Hypothesis) by showing the relationship between benchmark release date and Spearman correlation with Perceived Utility. It tests whether more recently released benchmarks show higher correlation with Perceived Utility.
    - **Figure Components:**
      1. **Scatter Plot:** Each point represents one benchmark, with:
         - X-coordinate: Release Date Ordinal (Old -> New) (days since reference date, e.g., days since 2020-01-01, or date as numeric value)
         - Y-coordinate: Spearman rho
      2. **Regression Line (optional but recommended):** Overlay a regression line with 95% confidence interval band to show the temporal trend.
      - **CRITICAL: Confidence Interval Band Explanation for Manuscript:** The red shaded region around the regression line represents the 95% confidence interval for the predicted Spearman correlation coefficient at each release date. This band quantifies the uncertainty in the regression prediction: a narrower band indicates more precise predictions, while a wider band indicates greater uncertainty. This should be explained in the Results section when describing Figure 4: "The red shaded region represents the 95% confidence interval for the regression line, indicating the uncertainty in the predicted relationship between benchmark recency and Spearman correlation with Perceived Utility."
      3. **X-axis:** Label as "Release Date" or "Recency (Release Date)" with appropriate date formatting (e.g., "YYYY-MM-DD" format or "Days since 2020-01-01"). Use clear tick marks.
      4. **Y-axis:** Label as "Spearman ρ" or "Spearman Correlation Coefficient".
      5. **NO TITLE:** Do not include a figure title in the plot itself. The title will be provided in the LaTeX caption.
      6. **Annotations:**
         - Spearman correlation coefficient between release date and Spearman rho, with p-value
         - Sample size (N)
         - Regression equation or slope (if regression line shown)
         - Individual benchmark labels (benchmark_id) as text annotations (if not too crowded)
         - **CRITICAL: Annotation Position:** All statistical annotations (correlation coefficient, p-value, sample size) must be positioned in the **bottom left corner** of the plot (using `transform=ax.transAxes` with coordinates like `(0.02, 0.02)`).
      7. **CRITICAL: Layer Ordering:** All scatter plot points must be on the topmost layer (highest zorder, e.g., `zorder=5`) so they are never covered by text annotations or white boxes. Text annotations should have lower zorder (e.g., `zorder=4`) and regression lines should have lower zorder (e.g., `zorder=1`).
    - **Data Source:** Load from `analysis_ready_data.csv`: `release_date` column (convert to ordinal), `spearman_rho` column.
    - **Save Location:** `overleaf/images/Figure_4_Recency.pdf`
    - **CRITICAL: All Annotations Required:** All elements must be annotated: axis labels with date format explanation, regression line statistics, correlation coefficient, sample size, and benchmark labels.

  - **Figure 5 (H5/H6 - Difficulty-Variance Joint Effect):**
    - **Overall Purpose:** This figure visualizes the joint effect of Difficulty and Variance (CV) on Spearman correlation with Perceived Utility, testing both H5 (Variance Hypothesis) and H6 (Difficulty Hypothesis). It shows how these two factors interact to influence correlation strength.
    - **Figure Components:**
      1. **Scatter Plot with Size Encoding:** Each point represents one benchmark, with:
         - X-coordinate: Difficulty (100 - subset_avg_score), where higher values indicate harder benchmarks. Label axis as "Difficulty" with direction indicator "(Easy → Hard)" or "(Lower → Higher)".
         - Y-coordinate: Spearman rho
         - Point Size: Variance (CV - Coefficient of Variation). Larger points indicate higher variance. Use a size scale that makes differences clearly visible.
      2. **Regression Line:** Overlay a regression line (using `sns.regplot()` or similar) showing the relationship between Difficulty and Spearman rho, with 95% confidence interval band.
      - **CRITICAL: Confidence Interval Band Explanation for Manuscript:** The red shaded region around the regression line represents the 95% confidence interval for the predicted Spearman correlation coefficient at each difficulty level. This band quantifies the uncertainty in the regression prediction: a narrower band indicates more precise predictions, while a wider band indicates greater uncertainty. This should be explained in the Results section when describing Figure 5: "The red shaded region represents the 95% confidence interval for the regression line, indicating the uncertainty in the predicted relationship between benchmark difficulty and Spearman correlation with Perceived Utility, while controlling for variance (CV)."
      3. **Color Encoding (optional but recommended):** Use color to encode Variance (CV) as an additional visual dimension, with a colorbar legend showing the CV scale.
      4. **X-axis:** Label as "Difficulty (subset average score)" with direction indicator "(Easy → Hard)" or "(Lower → Higher)", with clear tick marks.
      5. **Y-axis:** Label as "Spearman ρ" or "Spearman Correlation Coefficient".
      6. **Size Legend:** Add a legend showing the mapping between point size and Variance (CV) values, with example sizes and corresponding CV values.
      7. **Color Legend (if using color):** Add a colorbar showing the mapping between color and CV values.
      8. **NO TITLE:** Do not include a figure title in the plot itself. The title will be provided in the LaTeX caption.
      9. **Annotations:**
         - Regression coefficients (β₁ for Difficulty, β₂ for CV) with p-values
         - Sample size (N)
         - R² or adjusted R² for the regression model
         - Individual benchmark labels (benchmark_id) as text annotations (if not too crowded)
         - **CRITICAL: Annotation Position:** All statistical annotations (regression coefficients, p-values, sample size) must be positioned in the **bottom right corner** of the plot (using `transform=ax.transAxes` with coordinates like `(0.98, 0.02)`).
         - **CRITICAL: Legend Position:** The size legend (Point Size (CV)) must be positioned in the **upper right corner** (use `loc='upper right'` for legend) to avoid overlap with beta coefficient annotations. The colorbar should be positioned on the right side of the plot.
      10. **CRITICAL: Layer Ordering:** All scatter plot points must be on the topmost layer (highest zorder, e.g., `zorder=5`) so they are never covered by text annotations or white boxes. Text annotations should have lower zorder (e.g., `zorder=4`) and regression lines should have lower zorder (e.g., `zorder=1`).
    - **Data Source:** Load from `analysis_ready_data.csv`: `difficulty` column, `cv` (or `coefficient_of_variation`) column, `spearman_rho` column. Exclude Creative Writing v3 (if not already excluded).
    - **Exclusion Rule:** Exclude Creative Writing v3 from this analysis (only include benchmarks for which Difficulty was calculated).
    - **Save Location:** `overleaf/images/Figure_5_Difficulty_Variance.pdf`
    - **CRITICAL: All Annotations Required:** All elements must be thoroughly annotated: axis labels with direction indicators, point size legend with CV values, color legend (if used), regression statistics, sample size, and benchmark labels.

  - **Figure 6 (Confounder Correlation Heatmap):**
    - **Overall Purpose:** This figure shows the correlation matrix between all independent variables (features) used in the hypothesis tests. It helps identify multicollinearity (high correlations between predictors) and explains potential confounding relationships (e.g., are harder benchmarks also more recent?).
    - **Figure Components:**
      1. **Heatmap:** A square correlation matrix heatmap where:
         - Rows and columns represent the independent variables: Difficulty (subset avg score), Variance (CV), Recency (Release Date Ordinal), Complexity (prompt length encoded as ordinal: 1=Short, 2=Medium, 3=Long, 4=Extreme), Scale (log(question count)), and Task Type (encoded as binary: 0=MCQ, 1=Generative, or ordinal)
         - Each cell shows the correlation coefficient between the row variable and column variable
         - Color intensity represents correlation strength (e.g., red for positive, blue for negative, white for zero)
      2. **Color Scale (Colorbar):** Add a colorbar legend showing the mapping between colors and correlation values (typically -1 to +1 range).
      3. **Value Annotations:** Display the actual correlation coefficient values as text in each cell (formatted to 2-3 decimal places).
      4. **Diagonal:** The diagonal should show 1.0 (perfect correlation with itself) or can be masked/highlighted differently.
      5. **Row/Column Labels:** Use readable labels with spaces (e.g., "Difficulty", "Variance (CV)", "Recency", "Complexity", "Scale", "Task Type"), not underscores.
      6. **NO TITLE:** Do not include a figure title in the plot itself. The title will be provided in the LaTeX caption.
      7. **Axis Label Configuration:**
         - **CRITICAL:** X-axis labels (variable names) must be positioned at the top of the heatmap and rotated vertically (90 degrees) to avoid overlap and improve readability. Use `ax.xaxis.tick_top()`, `ax.xaxis.set_label_position('top')`, and `plt.setp(ax.xaxis.get_majorticklabels(), rotation=90, ha='center')`.
         - **Figure Height:** Increase the figure height (e.g., `figsize=(10, 10)`) to accommodate vertical labels and prevent crowding.
      8. **Annotations:**
         - Colorbar with correlation value range (only one colorbar, no duplicates)
         - Note explaining variable encodings (e.g., "Complexity: 1=Short, 2=Medium, 3=Long, 4=Extreme")
         - Sample size (N) if applicable
         - **CRITICAL: Annotation Position:** The variable encoding note must be positioned **below the figure** (outside the plot area, using `fig.text()` with coordinates like `(0.5, 0.02)`) to avoid covering the heatmap. Use `fig.subplots_adjust(bottom=0.15)` to add space at the bottom for the note text.
    - **Data Source:** Load from `analysis_ready_data.csv`: `difficulty` (or `subset_avg_score`), `cv` (or `coefficient_of_variation`), `release_date` (convert to ordinal), `prompt_length` (encode as ordinal), `question_count` (apply log transformation), `task_type` (encode as binary/ordinal). Compute pairwise correlations (Pearson or Spearman as appropriate).
    - **Save Location:** `overleaf/images/Figure_6_Confounder_Heatmap.pdf`
    - **CRITICAL: All Annotations Required:** Every element must be annotated: variable labels, correlation values in cells, colorbar with scale, encoding explanations, and sample size.

  - **General Figure Requirements:**
    - **All Figures Must Include:**
      1. **NO TITLE IN PLOT:** Do not include a figure title in the plot itself. The title will be provided in the LaTeX caption. However, when logging progress to the terminal, clearly state the figure name/title (e.g., "Generating Figure 1: Spearman rho by Task Type").
      2. **Axis Labels:** All axes must have clear labels with units/descriptions (use spaces, not underscores)
      3. **Legend:** If using colors, sizes, or other encodings, include a clear legend with labels and scales
      4. **Annotations:** All statistical values (correlations, p-values, sample sizes, regression coefficients) must be annotated on the figure or in the caption
      5. **Sample Size:** Display sample size (N) for the entire figure or for each group/category
      6. **Data Source Note:** Optionally include a note about data source (e.g., "Data from analysis_ready_data.csv")
      7. **Figure Numbering:** Ensure figure numbers match the file names (Figure 0, Figure 1, etc.)
    - **Figure Quality:**
      - Use high-resolution output (DPI ≥ 300 for PDF)
      - **CRITICAL: Font Size:** All text elements (axis labels, tick labels, annotations, legend labels, model name labels) must use significantly larger font sizes to ensure readability. Set font sizes to at least 18pt for axis labels, 16pt for tick labels, and 14pt for annotations. Use `plt.rcParams['font.size'] = 18`, `plt.rcParams['axes.labelsize'] = 20`, `plt.rcParams['xtick.labelsize'] = 18`, `plt.rcParams['ytick.labelsize'] = 18`, `plt.rcParams['legend.fontsize'] = 16`, and explicitly set font sizes for annotations (e.g., `fontsize=16` in `ax.annotate()`). **CRITICAL:** All font sizes should be increased significantly beyond the minimum requirements to ensure clear readability in the manuscript. Make fonts noticeably larger than standard sizes.
      - **CRITICAL: Layer Ordering (Z-order):** All scatter plot points must be on the topmost layer (highest zorder, e.g., `zorder=5`) so they are never covered by text annotations or white boxes. Text annotations should have lower zorder (e.g., `zorder=4`), reference lines and regression lines should have lower zorder (e.g., `zorder=1` or `zorder=2`), and grid lines should have the lowest zorder (e.g., `zorder=1`). This ensures that data points are always visible and not obscured by annotations.
      - **CRITICAL: Annotation and Legend Positioning:**
        - **Figure 2 (Scale Effect):** All statistical annotations (correlation coefficient, p-value, sample size) must be positioned in the **bottom left corner** of the plot (using `transform=ax.transAxes` with coordinates like `(0.05, 0.05)`).
        - **All other figures (Figure 0, 1, 3, 4, 5, 6):** All annotations and legends (including y=x reference line annotation in Figure 0, statistical annotations in Figures 4 and 5, size legend in Figure 5, and variable encoding note in Figure 6) must be positioned in the **bottom right corner** of the plot (using `transform=ax.transAxes` with coordinates like `(0.98, 0.02)`).
      - Use consistent color schemes across all figures
      - Ensure proper spacing and margins
      - Save as PDF format for manuscript inclusion
      - **CRITICAL: Annotation Spacing:** For figures with many point annotations (Figure 0, 2, 4, 5), use the `adjustText` library (if available) to automatically adjust annotation positions and avoid overlapping. Import with `try/except` and use `adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))` to adjust annotation positions.

- **4.4.2b:** Table Generation for Manuscript (`Human-SIG/src/analysis/generate_tables.py`).

  - **Action:** Identify all **experimental results tables** that will be directly included in the manuscript and generate them using `pandas.DataFrame.to_latex()` method. **Critical:** Use `DataFrame.to_latex()` to output tables directly as `.tex` files to `overleaf/tables/` directory. **Important:** The `overleaf/tables/` folder is reserved EXCLUSIVELY for experimental results tables that are automatically generated from statistical analysis (e.g., hypothesis test results, correlation summary tables). Non-experimental tables (e.g., benchmark introduction tables, benchmark characteristics tables) should be embedded directly in `acl_latex.tex` using LaTeX table syntax, not generated as separate `.tex` files. Do NOT create intermediate CSV files in `results/` that contain the same data as these LaTeX tables.
  
  - **`DataFrame.to_latex()` Method Usage:**
    - **Function Signature:** `DataFrame.to_latex(buf=None, *, columns=None, header=True, index=True, na_rep='NaN', formatters=None, float_format=None, sparsify=None, index_names=True, bold_rows=False, column_format=None, longtable=None, escape=None, encoding=None, decimal='.', multicolumn=None, multicolumn_format=None, multirow=None, caption=None, label=None, position=None)`
    - **Key Parameter - `buf`:** This is the first parameter and controls where the output goes. It accepts:
      - **File path (string or `pathlib.Path` object):** When you pass a file path, the method writes the LaTeX table directly to that file. This is the recommended approach for generating `.tex` files.
      - **File object or StringIO-like object:** Can also accept a file-like object for writing.
      - **`None` (default):** If `buf=None`, the method returns the LaTeX string instead of writing to a file.
    - **Input:** A pandas DataFrame containing the data to be converted to LaTeX format.
    - **Output:** 
      - When `buf` is a file path, the method writes a `.tex` file containing the LaTeX table code. The file can be directly included in the LaTeX document using `\input{tables/filename}`.
      - When `buf=None`, the method returns a string containing the LaTeX table code.
    - **Usage Steps:**
      1. Create or load a pandas DataFrame with your table data.
      2. Ensure the output directory exists (e.g., `overleaf/tables/`). Use `pathlib.Path` to create directories if needed.
      3. Call `df.to_latex()` with the file path as the `buf` parameter (can be passed as first positional argument or as keyword argument `buf='path/to/file.tex'`).
      4. Specify formatting parameters as needed (see Common Parameters below).
    - **Common Parameters:**
      - `buf`: File path (string or Path), file object, or None. **Pass the file path as the first positional argument or use `buf='path/to/file.tex'` to write directly to a file.**
      - `index=False`: Exclude row index from the table (usually desired for manuscript tables).
      - `header=True`: Include column headers (default True).
      - `float_format='%.3f'` or `float_format=lambda x: f'{x:.3f}'`: Format floating point numbers (e.g., 0.1234 → 0.123). **CRITICAL: For p-values, use scientific notation when p < 0.001** (e.g., use a formatter function that converts 0.000123 to "1.23e-3" or "$1.23 \times 10^{-3}$").
      - `caption='Table Caption'`: Add a table caption.
      - `label='tab:label'`: Add a LaTeX label for cross-referencing with `\ref{tab:label}`.
      - `column_format='lrr'`: Specify column alignment ('l'=left, 'r'=right, 'c'=center). For example, 'lrr' means left-aligned first column, right-aligned remaining columns.
      - `na_rep='--'`: Representation for missing values (default 'NaN').
      - `escape=False`: Set to False to prevent escaping LaTeX special characters (useful if your data contains LaTeX commands). Note: Default is `None` (reads from pandas config), but `False` is commonly used.
    - **Important:** The method requires the `booktabs` package in LaTeX. Ensure `\usepackage{booktabs}` is included in your LaTeX preamble. The output uses `\toprule`, `\midrule`, and `\bottomrule` commands from the booktabs package.
  
  - **Required Tables (Experimental Results Only):**
    - **Results Summary Table (Spearman only, for main text):** Create a DataFrame summarizing hypothesis test results (p-values, effect sizes, significance) from `statistical_significance_report.json` for Spearman $\rho$ metric only. Use `DataFrame.to_latex()` to save directly to `../overleaf/tables/results_table_spearman.tex` (relative to `Human-SIG/`). Include columns: Hypothesis, Effect Size, Effect Size Type, p_raw, p_corrected, significant_strict, ci_lower, ci_upper (if applicable). **CRITICAL: P-value Formatting:** All p-values must be formatted using scientific notation (e.g., 1.23e-3 instead of 0.00123) to avoid displaying 0.000. Use `float_format` parameter in `to_latex()` with a formatter function that converts p-values to scientific notation when p < 0.001. **This is an experimental results table and belongs in `../overleaf/tables/` for inclusion in the main text.**
    - **Results Summary Table (Kendall only, for appendix):** Create a DataFrame summarizing hypothesis test results for Kendall $\tau$ metric only. Use `DataFrame.to_latex()` to save directly to `../overleaf/tables/appendix_results_table_kendall.tex` (relative to `Human-SIG/`). Include the same columns as the Spearman table. **CRITICAL: P-value Formatting:** All p-values must be formatted using scientific notation. **This table belongs in the appendix.**
    - **Results Summary Table (RBO only, for appendix):** Create a DataFrame summarizing hypothesis test results for RBO metric only. Use `DataFrame.to_latex()` to save directly to `../overleaf/tables/appendix_results_table_rbo.tex` (relative to `Human-SIG/`). Include the same columns as the Spearman table (note: RBO does not have p-values, so p_raw and p_corrected columns may be empty or N/A). **This table belongs in the appendix.**
    - **Correlation Summary Table (Optional):** If needed for the manuscript, create a table summarizing correlation coefficients (Spearman $\rho$, Kendall $\tau$, and RBO) with their p-values and 95% confidence intervals for each benchmark from `analysis_ready_data.csv`. Use `DataFrame.to_latex()` to save directly to `../overleaf/tables/correlation_summary_table.tex` (relative to `Human-SIG/`). **CRITICAL:** This table MUST include all three correlation metrics (Spearman $\rho$, Kendall $\tau$, RBO), their p-values (formatted in scientific notation when p < 0.001), 95% confidence intervals for Spearman and Kendall (RBO does not have p-values or confidence intervals, report only the RBO value), AND the sample size ($N$) - the number of overlapping models used to compute each correlation. Format: "Spearman $\rho = 0.69$ [95% CI: 0.52, 0.82], $p = 1.23 \times 10^{-3}$, $N = 45$; Kendall $\tau = 0.52$ [95% CI: 0.35, 0.68], $p = 3.45 \times 10^{-3}$, $N = 45$; RBO = 0.85, $N = 45$" or use separate columns for each metric including a "Sample Size (N)" column. Do NOT use asterisks to indicate significance. **CRITICAL: Row/Column Naming:** All row and column names in the DataFrame must use spaces instead of underscores for readability (e.g., "Benchmark ID" instead of "benchmark_id", "Task Type" instead of "task_type", "Sample Size (N)" instead of "sample_size" or "n"). Do not remove parentheses, single quotes, or other characters from names. Note: The `benchmark_id` values themselves (e.g., "SWE-bench (Verified)") should be displayed as-is in tables, without modification. **This is an experimental results table and belongs in `../overleaf/tables/`.**
  - **Non-Experimental Tables:** Tables that are NOT experimental results (e.g., benchmark introduction tables, benchmark characteristics tables for descriptive purposes) should be embedded directly in `acl_latex.tex` using LaTeX table syntax. Do NOT generate these as separate `.tex` files in `overleaf/tables/`.
  
  - **Table Formatting Guidelines:**
    - Ensure tables are properly formatted for ACL 2026 style (refer to ACL template requirements).
    - For tables with confidence intervals, format them as strings in the DataFrame (e.g., "[0.12, 0.78]") before calling `to_latex()`, or use separate columns for `ci_lower` and `ci_upper` and format them appropriately in the LaTeX output.
    - **CRITICAL: P-value Formatting:** All p-values must be formatted using scientific notation when p < 0.001 (e.g., use "$1.23 \times 10^{-3}$" or "1.23e-3" format) to avoid displaying 0.000. Implement a formatter function that checks if p < 0.001 and converts to scientific notation accordingly.
    - **CRITICAL: Row/Column Naming:** All row and column names in DataFrames must use spaces instead of underscores for readability (e.g., "Benchmark ID" instead of "benchmark_id", "Task Type" instead of "task_type"). Do not remove parentheses, single quotes, or other characters from names. Note: The `benchmark_id` values themselves (e.g., "SWE-bench (Verified)") should be displayed as-is in tables and figures, without modification. This applies to all tables and figures (axis labels, legend labels, etc.).
  
  - **Output Location:** All table `.tex` files must be saved to `../overleaf/tables/` directory (relative to `Human-SIG/`), NOT to `Human-SIG/overleaf/tables/`. The `overleaf/` folder is a separate Git repository at the same level as `Human-SIG/`. Ensure the directory exists before writing files (use `Path('../overleaf/tables').mkdir(parents=True, exist_ok=True)` when running from `Human-SIG/`).

- **4.4.3:** Commit State

  - **Message:** `Step 4.4.3 Completed: Applied Holm-Bonferroni correction, generated manuscript figures and tables`

### Phase V: Manuscript Generation (The ACL 2026 Submission)

Objective: Synthesize the findings from Human-SIG/results/ into a scientifically rigorous, compliant ACL LaTeX submission in the overleaf/ repository.

**Critical Output Requirements:**
- **Tables:** **Experimental results tables only** must be generated using `pandas.DataFrame.to_latex()` and saved directly to `overleaf/tables/` as `.tex` files. The `overleaf/tables/` folder is reserved EXCLUSIVELY for experimental results tables that are automatically generated from statistical analysis (e.g., hypothesis test results, correlation summary tables). Non-experimental tables (e.g., benchmark introduction tables, benchmark characteristics tables) should be embedded directly in `acl_latex.tex` using LaTeX table syntax. Do NOT create CSV files in `results/` that contain the same data as LaTeX tables. The `DataFrame.to_latex()` method accepts a file path as its first parameter (`buf`), allowing direct output to `.tex` files. This ensures all numerical values in LaTeX tables are exactly as computed by the code, preventing transcription errors.
- **Figures:** All figures must be saved directly to `overleaf/images/` directory (not `overleaf/figures/`). If an existing `overleaf/images/` folder contains reference images, rename it to `overleaf/reference_image/` first.
- **Results Folder:** The `Human-SIG/results/` folder should only contain CSV or JSON format files used for data processing and analysis. These files are NOT meant to be directly included in the manuscript. Any experimental results data that needs to appear in the manuscript as a table must be generated using `DataFrame.to_latex()` and saved to `overleaf/tables/`.

**Critical Constraint:** You must NOT edit `main.tex` directly after initialization. All LaTeX content (abstract, introduction, methodology, results, discussion, conclusion) must be written directly into `overleaf/acl_latex.tex`.

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

#### Step 5.1: LaTeX Architecture Setup

- **5.1.1:** Initialize `../overleaf/acl_latex.tex` using the ACL 2026 template. **CRITICAL:** The `overleaf/` folder is a separate Git repository at the same level as `Human-SIG/`, NOT inside it.

  - **Action:** Write the preamble, title ("Correlating Benchmarks with Perceived Utility in the Post-Saturation Era"), and author placeholders.

  - **Note:** The `overleaf/acl_latex.tex` file already exists and contains the complete LaTeX document structure. For table generation rules, see Step 4.4.2b.

- **5.1.2:** Understand the structure of `../overleaf/acl_latex.tex`. **CRITICAL:** The `overleaf/` folder is a separate Git repository at the same level as `Human-SIG/`, NOT inside it.

  - **Action:** Read `overleaf/acl_latex.tex` to understand its current structure. The file already contains Abstract, Introduction (which may include Related Works), Methodology, Results, Discussion, and Conclusion sections.
  - **CRITICAL:** The `acl_latex.tex` file contains many detailed instructions and guidelines for writing each section. You must carefully read and follow these instructions, treating them as guidance for content generation, NOT as placeholders to be replaced. Do NOT simply replace placeholder comments; instead, understand the context and existing content, then modify or extend the sections as needed.
  - **Structure Analysis:** Identify the line numbers where each section begins and ends:
    - Abstract section (between `\begin{abstract}` and `\end{abstract}`)
    - Introduction section (between `\section{Introduction}` and the next `\section{...}`)
    - Related Works (if present within Introduction)
    - Methodology section (between `\section{Methodology}` and the next `\section{...}`)
    - Results section (between `\section{Results}` and the next `\section{...}`)
    - Discussion section (between `\section{Discussion}` and the next `\section{...}`)
    - Conclusion section (between `\section{Conclusion}` and `\end{document}` or end of file)
  - **Purpose:** This analysis will help you know exactly where to modify content in subsequent steps, rather than replacing placeholder comments.

  - **Note:** All LaTeX content (abstract, introduction, methodology, results, discussion, conclusion) will be written directly into `overleaf/acl_latex.tex`. For table generation rules, see Step 4.4.2b.

- **5.1.3:** Commit State.

  - **Message:** `Step 5.1.3 Completed: Analyzed acl_latex.tex structure and identified section locations`

#### Step 5.2: Abstract Update

- **5.2.1:** Update the abstract section in `overleaf/acl_latex.tex`.
  - **Action:** Locate the Abstract section (identified in Step 5.1.2) in `../overleaf/acl_latex.tex`. **CRITICAL:** The `overleaf/` folder is a separate Git repository at the same level as `Human-SIG/`, NOT inside it. Read the existing abstract content and the instructions within the file.
  - **Update:** At the end of the abstract, add a sentence summarizing the hypothesis testing conclusions. Read `Human-SIG/results/statistical_significance_report.json` (created in Step 4.4.1) to identify which hypotheses were supported. Report the key findings: which hypotheses were supported, the effect sizes, and the statistical significance (after correction).
  - **Formatting:** Each sentence must be on a separate line. Use blank lines to separate paragraphs.
- **5.2.2:** Commit State.
  - **Message:** `Step 5.2.2 Completed: Updated Abstract with hypothesis testing conclusions`

#### Step 5.3: Methodology (The Rigor Check)

- **5.3.1:** Update the methodology section in `overleaf/acl_latex.tex`.
  - **Source:** Read `Human-SIG/results/data_overlap_stats.json` (from Phase III) and your internal logic from Phase IV.
  - **Action:** Locate the Methodology section (identified in Step 5.1.2) in `../overleaf/acl_latex.tex`. **CRITICAL:** The `overleaf/` folder is a separate Git repository at the same level as `Human-SIG/`, NOT inside it. Read the existing methodology content and the instructions within the file. Update the content as needed based on the instructions in the file.
  - **Content:**
    1. **Data Collection:** Describe the ingestion of 29 benchmarks (AIME, FrontierMath Tier 1-3, FrontierMath Tier 4, HMMT (Feb 2025), MATH-500, MGSM, Aider Polyglot, HumanEval, IOI, LiveCodeBench, SciCode, SWE-bench (Verified), SWE-bench Bash Only, tau2-Bench Telecom, Terminal-Bench Hard, Terminal-Bench v2.0, IFBench, IFEval, Creative Writing v3, WritingBench, AA-LCR, ARC-AGI-2, Arena-Hard (Auto v2.0), FACTS, MMLU-Pro, GPQA, GPQA Diamond, Humanity's Last Exam, SuperGPQA) and the "Strict Entity Resolution" protocol used to map models. Mention the final $N$ (sample size) from the overlap stats. **CRITICAL:** The benchmark list above follows the standardized ordering (by category: Math, Coding, Instruction Following, Creative Writing, Hard Prompts, Expert; then alphabetically within each category).
    2. **Statistical Framework:** Explicitly state the use of Rank-Biased Overlap (RBO) ($p=0.9$) to account for top-tier sensitivity, Spearman's rank correlation ($\rho$) and Kendall's $\tau$ for non-parametric correlation analysis, and Fisher z-transformation for correlation aggregation when needed. Explain why multiple correlation metrics are used (RBO for ranking, Spearman/Kendall for robustness to outliers). **P-value Calculation for Correlations:** For each Spearman and Kendall correlation between benchmark scores and LMArena ELO scores, the p-value is calculated as follows: When $N < 30$ (where $N$ is the number of overlapping models between the benchmark and LMArena), we apply a permutation test using `scipy.stats.permutation_test` with `permutation_type='pairings'`, which permutes one ranking under the null hypothesis of independence and recalculates the correlation. When $N \geq 30$, the p-value returned by `scipy.stats.spearmanr` or `scipy.stats.kendalltau` is used as a sufficiently accurate approximation. This approach ensures accurate significance testing for small sample sizes while maintaining computational efficiency for larger samples. **Confidence Intervals for Correlations:** For each Spearman and Kendall correlation coefficient, compute 95% bootstrap confidence intervals using 5000 bootstrap iterations. This provides uncertainty quantification for correlation estimates, which is critical for interpreting the strength and reliability of relationships between benchmarks and Perceived Utility.
    3. **Hypothesis Testing:** Describe the statistical tests used for each hypothesis. **CRITICAL:** All hypothesis tests are performed using three correlation metrics (Spearman $\rho$, Kendall $\tau$, and RBO) separately, and results from all three metrics must be reported. For H1, H2, H3, and H4, perform the test three times (once for each metric). For H5 and H6 (regression models), use Spearman $\rho$ as the dependent variable in the primary analysis, but also report Kendall $\tau$ and RBO as robustness checks.
       - **H1 (Generative):** Mann-Whitney U test to compare Spearman $\rho$ (Kendall $\tau$, RBO) distributions between MCQ and Generative groups. Note: "Generative" includes both "Generation" and "Agentic" task types merged together. Report results for all three metrics.
       - **H2 (Scale):** Pearson correlation between log(question_count) and Spearman $\rho$ (Kendall $\tau$, RBO). Report correlations for all three metrics.
       - **H3 (Complexity):** Kruskal-Wallis H-test (non-parametric one-way ANOVA) to test whether Spearman $\rho$ (Kendall $\tau$, RBO) distributions differ across prompt_length categories, with post-hoc pairwise comparisons if significant. Report results for all three metrics.
       - **H4 (Recency):** Univariate Spearman correlation between release date and Spearman $\rho$ (Kendall $\tau$, RBO). Report correlations for all three metrics.
       - **H5 (Variance):** Multiple Robust Regression model (Spearman $\rho$ ~ Difficulty + CV) using `statsmodels.RLM` with Huber's t-criterion, examining the joint effect of Difficulty and Variance on correlation with Perceived Utility. Also perform regression using Kendall $\tau$ and RBO as dependent variables for robustness checks.
       - **H6 (Difficulty):** Multiple Robust Regression model (Spearman $\rho$ ~ Difficulty + CV) using `statsmodels.RLM` with Huber's t-criterion, controlling for variance. Also perform regression using Kendall $\tau$ and RBO as dependent variables for robustness checks.
    4. **Small-N Considerations:** Explain why multivariate regression with all 6 variables was avoided due to small sample size ($N=29$), which would violate the rule of thumb requiring at least 10 samples per variable. Describe the bootstrap resampling procedure (5000 iterations) used to compute confidence intervals for all effect sizes and correlation coefficients. Explain why categorical tests (Kruskal-Wallis) are preferred over assuming ordinal spacing for prompt_length.
  - **Formatting:** Each sentence must be on a separate line. Use blank lines to separate paragraphs.
- **5.3.2:** Commit State.
  - **Message:** `Step 5.3.2 Completed: Documented Methodology including RBO, Multivariate Regression, and Correlation Confidence Intervals`

#### Step 5.4: Results Reporting (Anti-Hallucination Protocol)

- **5.4.1:** Data Loading & Context Injection.
  - **Action:** BEFORE generating any LaTeX code, you must strictly read `Human-SIG/results/statistical_significance_report.json` and `Human-SIG/results/analysis_ready_data.csv` (created in Steps 4.4.1 and 4.2.3) into a local memory variable.
  - **Constraint:** When calling the LLM to write the text, explicitly inject the raw JSON/CSV data snippets into the context window. DO NOT rely on the Agent's "memory" of previous steps.
- **5.4.2:** Write the results section in `overleaf/acl_latex.tex`.
  - **Action:** Locate the Results section in `../overleaf/acl_latex.tex` and write the actual results content. **CRITICAL:** The `overleaf/` folder is a separate Git repository at the same level as `Human-SIG/`, NOT inside it.
  - **Content Block 1:** Reference the results summary table (Spearman only, for main text). The table should already exist at `../overleaf/tables/results_table_spearman.tex` (generated in Step 4.4.2b using `DataFrame.to_latex()`). Reference it with: `\input{tables/results_table_spearman}`. **Important:** Do NOT generate this table manually or by reading from CSV. The table must be generated programmatically using `DataFrame.to_latex()` to ensure all numerical values are exactly as computed by the code. **Note:** Kendall and RBO results tables are included in the appendix (see Step 4.4.2b).
  - **Content Block 2:** For H1-H6, report the Bootstrap 95% Confidence Intervals (e.g., "Coefficient: 0.45 [95% CI: 0.12, 0.78]"). Include both raw and corrected p-values (after Holm-Bonferroni correction) for each hypothesis. Clearly indicate which hypotheses are statistically significant after correction.
  - **CRITICAL: Correlation Reporting Format (Anti-Hallucination Protocol):** Whenever you report a Spearman or Kendall correlation coefficient between a benchmark and an LMArena category, you MUST include both the p-value and the 95% confidence interval explicitly in the text. **DO NOT use asterisks (*, **, ***) to indicate significance.** Instead, always report correlations in the format: "Spearman $\rho = 0.69$ [95% CI: 0.52, 0.82], $p = 0.001$" or "Kendall $\tau = 0.52$ [95% CI: 0.35, 0.68], $p = 0.003$". This applies to:
    - Any sentence that mentions a specific benchmark's correlation with Perceived Utility
    - Any table that lists correlation coefficients (confidence intervals must be included)
    - Any figure caption that references correlation values
    - Any discussion of individual benchmark performance
  - **Specifics:**
    - Discuss the specific impact of variance (CV - Coefficient of Variation) on Spearman correlation with Perceived Utility, and how it interacts with difficulty (The Clustering Effect: high-accuracy benchmarks compress variance near 100%, making it harder to distinguish between top-performing models). Explain the trade-off between difficulty and variance: harder benchmarks may have lower variance due to floor effects, while easier benchmarks may have compressed variance near the ceiling. **When reporting specific correlations, always include both p-values and 95% confidence intervals in the format specified above.**
    - **H5/H6 Difficulty-Variance Joint Analysis:** Report the bivariate robust regression results showing the joint effect of Difficulty and Variance on Spearman correlation with Perceived Utility. Discuss how these two factors interact and what this implies for benchmark design. **When reporting regression coefficients, always include both p-values (formatted in scientific notation when p < 0.001) and 95% confidence intervals in the format specified above.**
    - Explicitly mention that all benchmark scores were normalized to a 0-100 scale during data preparation (verified in Step 3.1) to ensure comparability across different metric types. Specifically, benchmarks using 0-1 scale (FACTS, GPQA, HMMT (Feb 2025), HumanEval, IFEval, SuperGPQA, SWE-bench (Verified), Arena-Hard (Auto v2.0)) had their scores multiplied by 100. For FACTS benchmark, only rows with Task_Name == "Average" were included, using the Numerical_Result column. Metric directionality (inversion for "lower_is_better" metrics) was handled during data preparation (verified in Step 3.1 and Step 4.2.1).
  - **Reference:** Include `\includegraphics{images/Figure_0_SWE_Bench_Illustration.pdf}`, `\includegraphics{images/Figure_1_Task_Type.pdf}`, `\includegraphics{images/Figure_2_Scale.pdf}`, `\includegraphics{images/Figure_3_Complexity_Categories.pdf}`, `\includegraphics{images/Figure_4_Recency.pdf}`, `\includegraphics{images/Figure_5_Difficulty_Variance.pdf}`, and `\includegraphics{images/Figure_6_Confounder_Heatmap.pdf}`.
  - **CRITICAL: Figure Element Explanations for Manuscript:**
    - **Figure 1 and 3 (Boxplot Colored Boxes):** When describing Figure 1 and Figure 3 in the Results section, explicitly explain that the colored boxes represent the interquartile range (IQR) for each category. The box edges indicate the first quartile (Q1, bottom edge) and third quartile (Q3, top edge), while the center line represents the median. For Figure 1, explain that light blue represents MCQ benchmarks and light green represents Generative benchmarks. For Figure 3, explain that different colors distinguish the four prompt complexity categories (light blue for Short, light green for Medium, light orange for Long, light yellow for Extreme). This explanation should appear in the paragraph immediately following the figure reference.
    - **Figure 2, 4, and 5 (Red Shaded Regions):** When describing Figure 2, 4, and 5 in the Results section, explicitly explain that the red shaded region around the regression line represents the 95% confidence interval for the predicted Spearman correlation coefficient. This band quantifies the uncertainty in the regression prediction: a narrower band indicates more precise predictions, while a wider band indicates greater uncertainty. The confidence interval is computed using bootstrap resampling or standard regression error estimation. This explanation should appear in the paragraph immediately following each figure reference.
  - **Formatting:** Each sentence must be on a separate line. Use blank lines to separate paragraphs.
- **5.4.3:** Commit State.
  - **Message:** `Step 5.4.3 Completed: Synthesized Results section using verified Bootstrap statistics with correlation confidence intervals`

#### Step 5.5: Discussion and Conclusion

- **5.5.1:** Update the discussion section in `overleaf/acl_latex.tex`.
  - **Action:** Locate the Discussion section (identified in Step 5.1.2) in `../overleaf/acl_latex.tex`. **CRITICAL:** The `overleaf/` folder is a separate Git repository at the same level as `Human-SIG/`, NOT inside it. Read the existing discussion content and the instructions within the file. Update the content as needed based on the instructions in the file.
  - **Content:** Interpret the results based on the statistical significance report. Read `Human-SIG/results/statistical_significance_report.json` to determine which hypotheses show positive relationships (even if not statistically significant). **CRITICAL: Discussion Criterion:** For each hypothesis, discuss it if the relationship is positive (or in the expected direction) with Perceived Utility, even if the result is not statistically significant. Only exclude from discussion if the relationship is clearly negative or completely unrelated. This allows for meaningful discussion of trends and patterns that may not reach statistical significance due to sample size limitations, while still providing valuable insights.
    - If H1 shows positive relationship (Generative tasks show higher or equal Spearman correlation with Perceived Utility compared to MCQs): Discuss why "Generative" tasks (which include both "Generation" and "Agentic" task types) exhibit higher Spearman correlation with Perceived Utility than MCQs (open-ended tasks may better capture real-world Perceived Utility). If the relationship is positive but not significant, acknowledge the trend and discuss potential reasons (e.g., sample size, task type heterogeneity).
    - If H2 shows positive relationship (larger test volumes show positive correlation with Spearman correlation): Discuss how larger test volumes contribute to Spearman correlation with Perceived Utility. If the relationship is positive but not significant, discuss the trend and its implications for benchmark design.
    - If H3 shows positive relationship (more complex prompts show positive correlation with Spearman correlation): Discuss how prompt complexity affects Spearman correlation with Perceived Utility. If the relationship is positive but not significant, discuss the observed patterns across complexity categories.
    - If H4 shows positive relationship (more recent benchmarks show positive correlation with Spearman correlation): Discuss "Contamination vs. Generalization" (recent benchmarks may have higher Spearman correlation with Perceived Utility due to training data contamination or genuine generalization improvements). If the relationship is positive but not significant, discuss the temporal trends observed.
    - If H5 shows positive relationship (higher variance shows positive correlation with Spearman correlation): Discuss how variance affects Spearman correlation with Perceived Utility, and how it interacts with difficulty. If the relationship is positive but not significant, discuss the observed variance patterns and their implications.
    - If H6 shows negative relationship (higher difficulty shows negative correlation with Spearman correlation, as expected): Discuss "The Alignment Tax" (harder benchmarks contribute negatively to Spearman correlation with Perceived Utility, particularly when controlling for variance). Explain the interaction between difficulty and variance. If the relationship is negative but not significant, discuss the observed difficulty patterns and their implications for benchmark design.
    - **Statistical Power and Sample Size Considerations:** Address the concern about the relatively small sample size ($N=29$) by explaining that while the sample size is limited, the statistical analyses were designed to maximize power given this constraint. Specifically, all hypothesis tests involve at most two independent variables simultaneously (e.g., the bivariate robust regression for H6/H5 uses only Difficulty and CV). Following the rule of thumb requiring approximately 10 samples per variable, the effective sample size requirement for bivariate models is approximately 20 samples, which is met by the current sample of 29 benchmarks. This targeted approach, combined with non-parametric tests (Spearman, Kendall, Mann-Whitney, Kruskal-Wallis) that are robust to small sample sizes, and bootstrap resampling (5000 iterations) for confidence interval estimation, ensures reasonable statistical validity despite the limited sample size. Discuss the trade-offs: while multivariate regression with all six factors simultaneously would require a larger sample, the current approach allows for rigorous testing of individual hypotheses while maintaining statistical power.
    - **Methodological Consideration: Difficulty Calculation and Potential Circularity:** Address the methodological choice of calculating the Difficulty feature (subset_avg_score) using the Common Subset of models with LMArena Overall ELO scores between 1400 and 1430, which is derived from the same LMArena data used as the dependent variable in correlation analyses. Acknowledge that this approach could theoretically introduce circularity concerns, as the same data source (LMArena) is used to both define the difficulty metric (via model subset selection) and as the target for correlation. However, explain the methodological necessity of this approach: (1) The benchmark leaderboards contain a highly heterogeneous set of models with vastly different capabilities, making direct calculation of benchmark difficulty across all models problematic due to floor and ceiling effects; (2) Using a single model as the reference would introduce excessive individual model bias, making the difficulty measure unreliable; (3) The Common Subset approach provides a principled way to select a homogeneous group of models with similar overall capability levels, ensuring sufficient sample size while minimizing individual model bias; (4) The choice of LMArena Overall ELO as the selection criterion is justified by its status as a comprehensive measure of model capabilities across diverse domains, making it the most appropriate proxy for general model capability. Conclude by noting that while this approach acknowledges a potential methodological limitation, it represents the most principled solution given the constraints of the data structure, and that sensitivity analyses (e.g., varying the ELO range thresholds) could be explored in future work.
    - Discuss other limitations: dependency on LMArena as ground truth, potential confounding factors, and generalizability concerns.
  - **Formatting:** Each sentence must be on a separate line. Use blank lines to separate paragraphs.
- **5.5.2:** Update the conclusion section in `overleaf/acl_latex.tex`.
  - **Action:** Locate the Conclusion section (identified in Step 5.1.2) in `../overleaf/acl_latex.tex`. **CRITICAL:** The `overleaf/` folder is a separate Git repository at the same level as `Human-SIG/`, NOT inside it. Read the existing conclusion content and the instructions within the file. Update the content as needed based on the instructions in the file.
  - **Content:** Final summary and limitations (e.g., dependency on LMArena crowd demographics).
  - **Formatting:** Each sentence must be on a separate line. Use blank lines to separate paragraphs.
- **5.5.3:** Commit State.
  - **Message:** `Step 5.5.3 Completed: Drafted Discussion and Conclusion sections in acl_latex.tex`

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
       - Verify all referenced files exist (acl_latex.tex, tables, figures).
       - Check for unmatched braces, brackets, or environments.
       - Ensure all custom commands are defined.
    4. Re-run the compilation command from Step 5.6.1.
    5. Repeat until compilation succeeds.
  - **Note:** Do not proceed to Step 5.6.3 until compilation succeeds without errors.

- **5.6.3:** Check for Formatting Warnings (Overfull/Underfull).
  - **Action:** After successful compilation, examine the `.log` file for formatting warnings:
    - **On Unix/Linux/Mac:** Use `grep -E "(Overfull|Underfull)" overleaf/acl_latex.log` (or `overleaf/main.log` if using a driver file)
    - **On Windows (PowerShell):** Use `Select-String -Pattern "(Overfull|Underfull)" overleaf/acl_latex.log` (or `overleaf/main.log` if using a driver file)
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
  - **Verification:** Ensure all `.tex` files, the `images/` folder (containing all PDF figures), the `tables/` folder (containing all `.tex` table files), and the compiled `main.pdf` are present in the remote repository.
- **5.7.2:** Final Log.
  - **Message:** `Step 5.7.2 Completed: FINAL SUBMISSION ARTIFACTS PUSHED. PIPELINE COMPLETE.`