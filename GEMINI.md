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
  - **Data Acquisition Strategy:** The scraping method for each benchmark is defined in the `scraping_method` field in `Human-SIG/config/metadata.json`. See Step 1.1 for the complete directory structure and Step 2.2 for detailed method descriptions.
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

## Part 2: Execution Tasks

### Phase I: System Initialization & File Paths

**Objective:** Initialize the directory structure and configuration files required for the pipeline, ensuring support for advanced statistics and safe LaTeX compilation.

#### Step 1.1: Directory Hierarchy Creation

**Critical Status Note:** The directory structure described below already exists in `Human-SIG/`. Many files and folders are already in place:

- **Already Exists:** 
  - All `input.txt` and `input.html` files in benchmark/category folders
  - All folders and files in `data/raw/` directories
  - `config/metadata.json`
  - Basic folder structure for `src/`, `results/`, `logs/`

- **Need to Create (if not exist):**
  - `data/processed/` subdirectories (`normalized_scores/`, `entity_resolution/`, `master_table/`)
  - Missing scripts in `src/processing/`, `src/analysis/`
  - `config/mapping.json` (if it doesn't exist)

**Directory Structure:** The following structure organizes benchmarks and LMArena categories by data acquisition method. All data files are named `data.csv` (no longer using `{name}_data.csv`). Common code logic is extracted to `src/scrapers/`.

```
Human-SIG/
├── config/                    # Stores metadata.json, mapping.json, and manual_overrides.csv
├── data/                      # Data directory (Data only)
│  ├── raw/                   # Raw data
│  │  ├── lmarena/            # LMArena data (lmarena method)
│  │  │   ├── {category_name}/        # category name, for example, Overall, Coding, etc.
│  │  │   │   ├── input.txt   # User-manually copied <table> element HTML (HTML format text)
│  │  │   │   └── data.csv    # Extracted data file
│  │  ├── artificial_analysis/  # Artificial Analysis unified table extraction
│  │  │   ├── input.txt          # User-manually copied <table> element HTML (unified table, shared by all benchmarks, HTML format text)
│  │  │   └── {benchmark_name}/ # Each benchmark has its own folder
│  │  │       ├── input.txt     # Benchmark description or reference (optional)
│  │  │       └── data.csv      # Extracted data file
│  │  ├── frontiermath/        # FrontierMath (manual_source_code method)
│  │  │   ├── frontiermath_tier_1_3/
│  │  │   │   ├── input.txt     # User-manually copied <table> element HTML (HTML format text)
│  │  │   │   └── data.csv      # Extracted data file
│  │  │   └── frontiermath_tier4/
│  │  │       ├── input.txt     # User-manually copied <table> element HTML (HTML format text)
│  │  │       └── data.csv      # Extracted data file
│  │  ├── manual_direct/        # Directly provided data files
│  │  │   └── {benchmark_name}/
│  │  │       └── data.csv      # or data.xlsx (user directly provides, rename if needed)
│  │  ├── pandas_read_html/     # pandas.read_html method
│  │  │   └── {benchmark_name}/
│  │  │       ├── input.txt     # URL file (one line with URL)
│  │  │       └── data.csv      # Scraped data file
│  │  ├── selenium/             # Selenium method
│  │  │   └── {benchmark_name}/
│  │  │       ├── input.txt     # URL file (one line with URL)
│  │  │       └── data.csv      # Scraped data file
│  │  └── vals_ai/              # VALS.ai platform data
│  │      └── {benchmark_name}/
│  │          ├── input.txt     # User-manually copied JSON element (from webpage source code, JSON format text)
│  │          └── data.csv      # Converted data file
│  └── processed/              # Processed data
│      ├── normalized_scores/
│      ├── entity_resolution/
│      └── master_table/
├── src/
│  ├── main.py        # Unified CLI entry point
│  ├── scrapers/      # Scraping logic modules
│  │   ├── selenium_scraper.py
│  │   ├── lmarena_scraper.py
│  │   └── ...
│  ├── processing/     # Scripts to normalize, map names, and compute RBO (to be created)
│  └── analysis/      # Scripts for correlations and visualization (to be created)
│    └── multivariate/  # Specific folder for regression models (to be created)
├── results/         # Final output JSONs, CSVs, and Logs
│  └── plots/        # Generated PDF figures for the manuscript
└── logs/           # Error logs and execution traces
```

**Important Notes:**
- All benchmark and category data files are uniformly named `data.csv` (no longer using `{name}_data.csv`).
- Each benchmark/category folder contains: `input.txt` (required, file extension is `.txt`, but content format varies by method) and `data.csv`.
- Common code logic is extracted to `src/scrapers/`. Individual scraper logic is modularized.

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
  - **Action:** Check that this file exists and contains entries for all benchmarks and LMArena categories.
  - **Critical Structure Note:** The `metadata.json` file contains multiple types of entries:
    - **Benchmark entries:** These are the benchmarks that will be analyzed. They do NOT have an `elo_column` field.
    - **LMArena entries:** These are metadata entries for LMArena leaderboard categories (Overall, Coding, Math, etc.). They have an `elo_column` field and are processed using the `lmarena` method.
    - **meta_info entry:** The first entry contains metadata definitions (prompt_length_standards, category_definitions) and should not be counted as a benchmark.
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
    - `scraping_method`: String enum. Indicates the data acquisition method. Possible values: `"pandas_read_html"`, `"selenium"`, `"artificial_analysis"`, `"vals_ai_manual_json"`, `"manual"`, `"manual_source_code"`, and `"lmarena"`. See Step 2.2.2 for detailed method descriptions. All output data files are named `data.csv` and stored in the respective method directory under `data/raw/`.


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

### Phase II: Data Acquisition (Completed)

**Status:** Completed.
**Output:** Raw CSV files are populated in `Human-SIG/data/raw/`.

Proceed to **Phase III: Data Processing**.

### Phase III: Data Processing, Entity Resolution & Master Table Synthesis

Objective: Transform raw, heterogeneous benchmark data into a unified, normalized, and ranked dataset aligned with the LMArena "Ground Truth." This phase enforces strict identity verification to prevent data contamination.

Input:

- `Human-SIG/data/cleaned/` (Cleaned CSV files from Step 3.1).

- `Human-SIG/config/mapping.json` (The Unified Model Registry).

  Output:

- `Human-SIG/data/processed/master_table/master_correlation_matrix.csv`.

- `Human-SIG/data/processed/entity_resolution/pending_resolution.csv` (For human review, generated in Step 3.3.2).

#### Step 3.1: Preliminary Data Cleaning

**Objective:** Clean the raw data to remove organization suffixes and standardise model names before further processing. This step addresses issues where scraping concatenated Model and Organization columns (e.g., "GPT-5.1 ThinkingOpenAI").

- **3.1.1:** Create `Human-SIG/src/processing/clean_raw_data.py`.
  - **Action:** Implement a script that:
    1. Reads all `data.csv` files from `Human-SIG/data/raw/`.
    2. Identifies the model name column.
    3. Strips known organization suffixes (e.g., "OpenAI", "Google", "xAI", "Anthropic", "DeepSeek") from model names.
    4. Saves the cleaned files to a new directory `Human-SIG/data/cleaned/`, preserving the subdirectory structure.
  - **Input:** `Human-SIG/data/raw/`
  - **Output:** `Human-SIG/data/cleaned/` (mirroring the structure of `data/raw/` but with cleaned CSVs).
- **3.1.2:** Commit State.
  - **Message:** `Step 3.1.2 Completed: Executed preliminary data cleaning to remove organization suffixes`

#### Step 3.2: Human-in-the-Loop Entity Resolution (Smart Structured Matching)

- **3.2.1:** Create `Human-SIG/src/processing/resolve_identities.py` (or use `resolve_identities_smart.py` for improved algorithm).
  - **Code Documentation Requirements:**
    - File header must explain the multi-level entity resolution strategy with structured matching, the purpose of preventing data contamination, and the human-in-the-loop verification process.
    - All functions must have docstrings explaining their matching logic, especially the structured parsing and similarity calculation methods.
  - **Input:** Load the **FULL** LMArena dataset (all ELOs) and the cleaned benchmark datasets from `Human-SIG/data/cleaned/`.
  - **Study Universe Definition:** Define `target_candidates` as LMArena models with `elo_overall >= 1330`.
  - **The Resolution Loop:** Iterate through every raw model name in the benchmarks:
    - **Level 0 (Global Exact Match - The "Low ELO" Filter):** Check if `raw_name` exists in the **FULL** LMArena dataset (after normalization: lowercase, standardize separators).
      - If Match Found AND ELO < 1330: **Auto-Discard** (Log as "Known Low-ELO"). Do not proceed to fuzzy matching.
      - If Match Found AND ELO >= 1330: **Auto-Map** (Keep).
    - **Level 1 (Target Exact Match):** (Redundant if Level 0 matches, but serves as sanity check) Does `raw_name == lmarena_id` (normalized, in Study Universe)? -> Auto-Map.
    - **Level 2 (Registry Lookup):** Check `Human-SIG/config/mapping.json`. Is `raw_name` a known alias? -> Auto-Map.
    - **Level 3 (Smart Structured Matching - The Core Innovation):** If unmatched at Levels 0-2, use **Structured Matching** to find the best candidates within the **Study Universe (ELO >= 1330) ONLY**.
      - **3a. Structured Parsing:** Parse the benchmark model name into components:
        - `family`: Model family name (e.g., "gpt", "claude", "gemini")
        - `version`: Version number (e.g., "5.1", "4.5")
        - `variant`: Variant markers (e.g., {"high", "thinking"})
        - `date`: Date suffix if present
      - **3b. Family-Based Filtering:** Only consider LMArena models whose family name matches (or is highly similar to) the benchmark model's family. This prevents cross-family false matches (e.g., "gpt-4" should NOT match "glm-4").
      - **3c. Structured Similarity Calculation:** For each candidate LMArena model, compute a structured similarity score based on:
        - Family match (40% weight, **must match**): Exact match = 1.0, containment = 0.9, string similarity > 0.7 = partial match, otherwise = 0.0 (disqualifies candidate)
        - Version similarity (30% weight): Uses exponential decay based on numerical difference (e.g., 5.1 vs 5.2 ≈ 0.5 similarity)
        - Variant overlap (20% weight): Jaccard similarity of variant marker sets
        - Overall string similarity (10% weight): Auxiliary metric using SequenceMatcher
      - **3d. Top-K Candidate Selection:** Generate at most K candidates (default K=3) with the highest structured similarity scores. Only candidates with similarity > 0.3 are considered.
      - **3e. Output:** Add to `pending_resolution.csv` with columns: `benchmark`, `raw_name`, `proposed_lmarena_id`, `confidence` (the structured similarity score), `alternative_candidates` (other top candidates with their scores).
      - If no candidates found (similarity <= 0.3 for all models): Add to `unmatched_log.csv` for quick sanity check.
    - **Exclusion:** Models in `unmatched_log.csv` are considered discarded *unless* manually moved to mapping.json.
  - **Key Improvement:** The structured matching approach dramatically reduces the number of candidates that need human review (from potentially 10,000+ to 500-2,000 manageable cases) while ensuring all plausible matches are included. Unlike simple fuzzy string matching (e.g., Levenshtein distance), structured matching prevents cross-family false positives (e.g., "gpt-4" matching "glm-4") and correctly identifies matches with different formatting (e.g., "GPT-5.1 (high)" matching "gpt-5.1-high").
- **3.2.2:** Interactive Verification.
  - **Action:** Generate `Human-SIG/data/processed/entity_resolution/pending_resolution.csv` containing: `benchmark`, `raw_name`, `proposed_lmarena_id`, `confidence`, `alternative_candidates`.
  - **Interactive Pause:** Check if `Human-SIG/data/processed/entity_resolution/pending_resolution.csv` is not empty.
  - **If populated:** PAUSE execution. Print: "Unmatched models detected. Please manually review 'Human-SIG/data/processed/entity_resolution/pending_resolution.csv'. The structured matching algorithm has generated a manageable list of candidates (typically 500-2000 entries, reduced from 10,000+ using simple fuzzy matching). Review the proposed matches, paying attention to confidence scores (> 0.8 = high confidence, 0.5-0.8 = medium, < 0.5 = low). Confirm correct matches, fix errors, or delete rows to discard models. Then update 'mapping.json' manually or type 'CONTINUE' to let me append approved matches."
  - **Wait for User Input.**
  - **Post-Processing:** Read the user-verified CSV. APPEND the new confirmed aliases to `Human-SIG/config/mapping.json`. Constraint: Never overwrite `mapping.json` completely; only append new keys/values to preserve history.
- **3.2.3:** Final Merge.
  - **Action:** Reload all data using the updated `mapping.json`. Discard any models that remain unmatched.
  - **Message:** `Step 3.2.3 Completed: Executed smart structured matching and human verification, updated mapping registry`

#### Step 3.3: Robust Parsing & Score Normalization Strategy

- **3.3.1:** Create `Human-SIG/src/processing/parser_utils.py`.
  - **Code Documentation Requirements:**
    - File header must explain the purpose (parsing and normalizing benchmark scores from CSV files), the score normalization methodology (ensuring all scores are in 0-100 range as specified in Step 2.2), ranking logic, and tie-breaking strategy.
    - All classes and methods must have docstrings.
  - **Class Definition:** Implement `BenchmarkParser`.
  - **Ranking Logic:** Compute rank strictly within the Study Universe.
    - **Study Universe Definition:** The "Study Universe" consists of all models in the LMArena dataset with `elo_overall >= 1330`. Models with ELO below this threshold are excluded from the Study Universe.
    - **Ranking Filter:** Only rank models that appear in both the benchmark data and the Study Universe. Models that appear in the benchmark but not in the Study Universe should be excluded from ranking.
  - **Tie-Breaking:** Use `method='min'` (e.g., if two models tie for first place with score 95, assign both rank 1, and the next model gets rank 3) to support rigorous RBO calculation. This ensures that tied models receive the same rank, which is important for RBO computation.
  - **Directionality:** When ranking, ensure that higher scores receive better (lower) ranks. All scores from Step 2.2 should already represent "higher is better" performance (after normalization and inversion if needed), so the ranking logic should always assume "higher score = better rank".
  - **Note:** Scores should already be normalized to 0-100 range from Step 2.2 (and cleaned in Step 3.1) and stored in CSV files. This parser loads CSV files from `data/cleaned/`, performs ranking, and outputs data structure transformation. The parser should output both the original scores and the computed ranks.
- **3.3.2:** Commit State.
  - **Message:** `Step 3.3.2 Completed: Implemented BenchmarkParser with ranking logic for RBO calculation`

#### Step 3.4: Master Table Synthesis

- **3.4.1:** Create `Human-SIG/src/processing/build_master_table.py`.
  - **Code Documentation Requirements:**
    - File header must explain the master table structure, the merge strategy (left join to preserve Study Universe), and why both score and rank columns are needed.
    - All functions must have docstrings explaining data transformation steps.
  - **Initialization:** Create the `df_master` DataFrame using LMArena models as the index.
    - **Columns:** `elo_overall`, `elo_math`, `elo_coding`, `elo_hard_prompts`, `elo_creative_writing`, `elo_instruction_following`, `elo_expert`.
  - **Merge Loop:** For each benchmark (e.g., humaneval):
    1. Load parsed data (Score + Rank) from the parser output (created in Step 3.2.1). The parser must read CSV files from the appropriate benchmark folder based on the scraping method:
       - For `pandas_read_html`: `Human-SIG/data/raw/pandas_read_html/{benchmark_name}/data.csv`
       - For `selenium`: `Human-SIG/data/raw/selenium/{benchmark_name}/data.csv`
       - For `manual_source_code`: `Human-SIG/data/raw/frontiermath/{subdirectory}/data.csv`
       - For `artificial_analysis`: `Human-SIG/data/raw/artificial_analysis/{benchmark_name}/data.csv`
       - For `manual_direct`: `Human-SIG/data/raw/manual_direct/{benchmark_name}/data.csv`
       - For `vals_ai_manual_json`: `Human-SIG/data/raw/vals_ai/{benchmark_name}/data.csv`
       - For `lmarena`: `Human-SIG/data/raw/lmarena/{category_name}/data.csv`
    2. Map model names using the entity resolution logic from Step 3.3 (exact match, registry lookup, or verified fuzzy match).
    3. Left Join onto `df_master` (Keep only models present in LMArena Study Universe). Models that appear in the benchmark but not in the Study Universe will be excluded.
    4. Add columns: `{benchmark_id}_score` AND `{benchmark_id}_rank`. (Both are needed: Score for Pearson/Spearman correlation, Rank for RBO calculation). Use the sanitized benchmark_id (e.g., "humaneval", "mmlu_pro") as the column name prefix.
    5. Handle missing values: If a model in the Study Universe does not have a score for a particular benchmark, leave the score and rank as `NaN` (do not fill with zeros or default values).
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
- **3.4.3:** Persistence
  - **Output:** Save the master table to `Human-SIG/data/processed/master_table/master_correlation_matrix.csv`. This CSV should contain:
    - One row per model (from the Study Universe)
    - Columns: `model_name`, `elo_overall`, `elo_math`, `elo_coding`, `elo_hard_prompts`, `elo_creative_writing`, `elo_instruction_following`, `elo_expert`, and for each benchmark: `{benchmark_id}_score` and `{benchmark_id}_rank`
    - Missing values should be represented as `NaN` or empty cells (not zeros)
  - **Note:** The overlap statistics JSON file was already saved in Step 3.4.2.
- **3.4.4:** Commit State
  - **Message:** `Step 3.4.4 Completed: Generated master correlation matrix with dual Score/Rank columns`

### Phase IV: Hypothesis Verification & Statistical Analysis (Revised for Small-N Robustness)

Objective: Execute a rigorous statistical verification pipeline specifically tailored for small sample sizes ($N=29$). Instead of a single, brittle multivariate regression which lacks statistical power, you will execute Bootstrapped Univariate Analysis for individual factors and Controlled Bivariate Robust Regression to disentangle confounding factors (specifically Difficulty vs. Variance).

Input:

- `Human-SIG/data/processed/master_table/master_correlation_matrix.csv` (Model Scores & Ranks).

- `Human-SIG/config/metadata.json` (Contains all benchmark metadata including `metric_direction`, `release_date`, `task_type`, `question_count`, and other metadata fields for all benchmarks).


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
    - File header must explain the complete workflow: loading benchmark data from CSV files, reading metric_direction from config/metadata.json (for verification purposes), reading category from metadata.json to determine correlation target, verifying metric directionality (scores should already represent "higher is better" after Step 2.2.1), computing difficulty and variance features, and calculating correlations.
    - All functions must have docstrings explaining their mathematical operations.
  - **Task A: Metric Directionality Verification (Critical for H1).**
    - **Action:** Load benchmark data from CSV files in the appropriate benchmark folders. For each benchmark, read the `metric_direction` field from `Human-SIG/config/metadata.json` (the centralized metadata file containing all benchmark information).
    - **Prerequisite:** All scores must already be normalized to the 0-100 range and inverted if necessary (as required in Step 2.2.1) so that higher scores represent better performance. If any benchmark's scores are not in the 0-100 range, HALT and report an error.
    - **Logic:** Check the `metric_direction` field from `Human-SIG/config/metadata.json`.
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
    - **Print:** "CRITICAL: Detected low correlation (< 0.5) for high-quality benchmark {benchmark_name}. This suggests a data quality issue. Please check: (1) metric directionality in the metadata file (Human-SIG/config/metadata.json), (2) that scores in CSV files are correctly normalized to 0-100 range, (3) that metric inversion was applied correctly in Step 2.2.1 if metric_direction == 'lower_is_better' (scores should represent 'higher is better' after normalization), and (4) that the correct LMArena ELO column is being used based on the benchmark's category."
    - **Wait for User:** Do not proceed until resolved. The user must verify and fix the data issue before continuing.
- **4.2.3:** Persistence.
  - **Output:** Save the fully engineered table to `Human-SIG/results/analysis_ready_data.csv`.
  - **CSV Column Structure:** The output CSV file must contain the following columns for each benchmark:
    - `benchmark_name` or `benchmark_id`: Benchmark identifier
    - `subset_avg_score`: Difficulty feature (mean score across Common Subset models, as computed in Task B). Lower values indicate harder benchmarks.
    - `is_estimated_difficulty`: Boolean flag (True if fallback method was used due to insufficient Common Subset overlap, False otherwise)
    - `cv` or `coefficient_of_variation`: Variance feature (Coefficient of Variation, as computed in Task C). Formula: CV = $\sigma$/$\mu$, where $\sigma$ is standard deviation and $\mu$ is mean score.
    - `spearman_rho`: Spearman rank correlation coefficient between benchmark scores and corresponding LMArena ELO scores
    - `kendall_tau`: Kendall's $\tau$ correlation coefficient
    - `rbo`: Rank-Biased Overlap (p=0.9)
    - Additional metadata columns from metadata.json (e.g., `release_date`, `task_type`, `prompt_length`, `question_count`, `category`)
  - **Data Format:** All numerical values should be stored as floats. Boolean values can be stored as True/False or 1/0. Missing values should be represented as empty cells or NaN.
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
       - **H1 & H5 (Main):** Multiple Robust Regression model (Correlation ~ Difficulty + CV) using `statsmodels.RLM` with Huber's t-criterion.
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
    - **Statistical Power and Sample Size Considerations:** Address the concern about the relatively small sample size ($N=29$) by explaining that while the sample size is limited, the statistical analyses were designed to maximize power given this constraint. Specifically, all hypothesis tests involve at most two independent variables simultaneously (e.g., the bivariate robust regression for H1/H5 uses only Difficulty and CV). Following the rule of thumb requiring approximately 10 samples per variable, the effective sample size requirement for bivariate models is approximately 20 samples, which is met by the current sample of 29 benchmarks. This targeted approach, combined with non-parametric tests (Spearman, Kendall, Mann-Whitney, Kruskal-Wallis) that are robust to small sample sizes, and bootstrap resampling (5000 iterations) for confidence interval estimation, ensures reasonable statistical validity despite the limited sample size. Discuss the trade-offs: while multivariate regression with all six factors simultaneously would require a larger sample, the current approach allows for rigorous testing of individual hypotheses while maintaining statistical power.
    - **Methodological Consideration: Difficulty Calculation and Potential Circularity:** Address the methodological choice of calculating the Difficulty feature (subset_avg_score) using the Common Subset of models with LMArena Overall ELO scores between 1400 and 1430, which is derived from the same LMArena data used as the dependent variable in correlation analyses. Acknowledge that this approach could theoretically introduce circularity concerns, as the same data source (LMArena) is used to both define the difficulty metric (via model subset selection) and as the target for correlation. However, explain the methodological necessity of this approach: (1) The benchmark leaderboards contain a highly heterogeneous set of models with vastly different capabilities, making direct calculation of benchmark difficulty across all models problematic due to floor and ceiling effects; (2) Using a single model as the reference would introduce excessive individual model bias, making the difficulty measure unreliable; (3) The Common Subset approach provides a principled way to select a homogeneous group of models with similar overall capability levels, ensuring sufficient sample size while minimizing individual model bias; (4) The choice of LMArena Overall ELO as the selection criterion is justified by its status as a comprehensive measure of model capabilities across diverse domains, making it the most appropriate proxy for general model capability. Conclude by noting that while this approach acknowledges a potential methodological limitation, it represents the most principled solution given the constraints of the data structure, and that sensitivity analyses (e.g., varying the ELO range thresholds) could be explored in future work.
    - Discuss other limitations: dependency on LMArena as ground truth, potential confounding factors, and generalizability concerns.
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