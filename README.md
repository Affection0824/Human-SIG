# Human-SIG

Human-SIG converts public benchmark leaderboards into a common model identity space, compares benchmark rankings with LMArena preferences, and generates the figures and tables used by the manuscript.

## What each processing and analysis step does

| Step | Script | Main input | Main output |
|---|---|---|---|
| 1 | `src/processing/step1_generate_cleaned_data.py` | `data/raw/**/data.csv` | `data/processed/cleaned/*/cleaned_data.csv` |
| 2 | `src/processing/step2_generate_review_files.py` | cleaned data and LMArena Overall | `data/processed/review_files/*.json` and `data/processed/model_extraction/lmarena_models.json` |
| 3 | `src/processing/step3_generate_mapping.py` | reviewed `selected_lmarena_model` values | benchmark-level `mapping.json` files |
| 4 | `src/processing/build_master_table.py` | cleaned data, mappings, metadata, Study Universe | `data/processed/master_table/master_correlation_matrix.csv` |
| 5 | `src/analysis/compute_features_robust.py` | master table and metadata | `results/analysis_ready_data.csv` |
| 6 | `src/analysis/calculate_reference_difficulty.py` | master table and analysis-ready data | `results/reference_difficulty_comparison.csv` |
| 7 | `src/analysis/small_n_hypothesis_test.py` | analysis-ready data | `results/hypothesis_test_results.json` |
| 8 | `src/analysis/apply_correction.py` | raw hypothesis-test results | `results/statistical_significance_report.json` |
| 9 | `src/analysis/uncertainty_propagation_analysis.py` | master table, analysis-ready data, raw LMArena data | fixed-seed Monte Carlo results in `results/uncertainty_simulation_results.csv` |
| 10 | `src/analysis/generate_plots_tables.py` | Step 5–9 result files and Figure 1 labels | five manuscript PDFs and five LaTeX tables |

Step 4 excludes a benchmark when fewer than six Study Universe models overlap with it. Step 5 calculates Difficulty, coefficient of variation, Spearman and Kendall correlations with p-values and bootstrap confidence intervals, and descriptive RBO. For the current snapshot, HumanEval and FACTS have fewer than five models in the common subset used for the preferred difficulty calculation, so Step 5 logs a warning and uses its fallback difficulty method.

## Choose a workflow

This repository supports three workflows:

1. **Reproduce the manuscript from Step 3** using the prepared data and reviewed model matches already in the repository.
2. **Rebuild model matching from Step 1** after changing raw benchmark data.
3. **Update raw data** with one of the supported scraping methods.

All commands below are run from the repository root (`Human-SIG/`).

## Requirements and environment setup

- [`uv`](https://docs.astral.sh/uv/getting-started/installation/)
- Python `>=3.14`
- Chrome for the Selenium scraper only; ChromeDriver is managed automatically
- Write access to `../overleaf/` when generating manuscript files

From the repository root, run one of the following setup commands. `uv` reads `pyproject.toml` and `uv.lock`, creates or updates `.venv/`, and uses a compatible Python version. If Python 3.14 or newer is not installed locally, `uv` can download it automatically. You do not need to create or activate the virtual environment manually.

| Task | Command |
|---|---|
| Basic processing and non-plotting analysis | `uv sync` |
| Complete Steps 3–10 reproduction | `uv sync --group plotting` |
| Acquire or scrape raw data | `uv sync --group scraping` |
| Install everything | `uv sync --group plotting --group scraping` |

Every option installs the base project dependencies; `plotting` and `scraping` add only the packages needed for those tasks. The commands below use `uv run`, which runs inside `.venv/`. Commands that need an optional group repeat the corresponding `--group` flag so they remain self-contained. Because `uv sync` synchronizes the selected dependency set, rerun the appropriate setup command when switching workflows.

## Reproduce the manuscript from Step 3

Use this route for the current repository snapshot. It does not rerun scraping, cleaned-data generation, or model-match generation.

### Required inputs

The repository must already contain:

- `data/processed/cleaned/*/cleaned_data.csv`
- `data/processed/review_files/*.json`
- `data/metadata.json`
- the prepared LMArena raw data under `data/raw/lmarena/`

Step 3 reads `selected_lmarena_model` from the existing review files. The `untrusted` field is review metadata and is not used by the mapping script.

### Run Steps 3–10

```bash
# Create or update the environment required by the complete final workflow
uv sync --group plotting

# Step 3: build benchmark-to-LMArena mappings
uv run src/processing/step3_generate_mapping.py

# Step 4: build the master table
uv run src/processing/build_master_table.py

# Step 5: calculate benchmark features and correlations
uv run src/analysis/compute_features_robust.py

# Step 6: calculate the reference-model difficulty comparison
uv run src/analysis/calculate_reference_difficulty.py

# Step 7: test H1–H5
uv run src/analysis/small_n_hypothesis_test.py

# Step 8: apply Holm–Bonferroni correction
uv run src/analysis/apply_correction.py

# Step 9: propagate score and LMArena uncertainty
uv run src/analysis/uncertainty_propagation_analysis.py

# Step 10: generate the five manuscript figures and five manuscript tables
uv run --group plotting src/analysis/generate_plots_tables.py
```

Step 7 tests H1 Scale, H2 Complexity, H3 Recency, H4 Variance, and H5 Difficulty. For H2, the Kruskal–Wallis test is the primary inference: its p-value is stored as `p_raw`, appears in the hypothesis table, and enters the Step 8 correction. The ordinal linear regression is a complementary trend analysis; its $R^2$ is H2's reported effect size, while its slope and p-value remain available in `hypothesis_test_results.json`. H4 and H5 are estimated together in one bivariate Huber robust regression rather than in separate univariate models. Each hypothesis is evaluated with Spearman, Kendall, and RBO, so Step 8 corrects 15 metric-level tests.

## Scope and reproducibility notes

### Creative Writing v3

Creative Writing v3 is retained in general correlation analyses, but it is deliberately excluded from the difficulty-based evaluation because a defensible difficulty scale cannot be identified for its leaderboard score.

Consequently:

- Step 7 excludes it from the difficulty–variance regression.
- Step 9 records its observed correlation but deliberately leaves its Monte Carlo fields unavailable because the binomial percentage-accuracy model does not apply.
- Step 10 excludes it from `uncertainty_table.tex`.

### Reference difficulty models

Step 6 follows the model identifiers in `calculate_reference_difficulty.py`:

- Claude Opus 4.5: `Anthropicclaude-opus-4-5-20251101`
- Gemini 2.5 Pro: `gemini-2.5-pro`
- GPT-5.1: `gpt-5.1`

Reference difficulty is `100 - mean score` across these three models. In the current master table all three model rows are present, and a benchmark is included only when all three scores are available. If a reference-model row is missing entirely, treat the Step 6 error as an input problem and do not use a partial-model result.

### Exact reproducibility

Steps 3–10 are deterministic or use fixed random seed `42`. Step 5 uses 2,000 bootstrap resamples for each Spearman and Kendall confidence interval; Step 7 uses 5,000 benchmark-level bootstrap resamples for H3–H5; and Step 9 performs 10,000 Monte Carlo trials for each percentage-based benchmark. Generated CSV, JSON, and LaTeX table contents are reproducible for the pinned environment. PDF files may still differ byte-for-byte because of rendering metadata even when their data and visual content are unchanged.

Step 9 samples LMArena Elo values from normal distributions derived from their reported 95% confidence intervals. It models each percentage benchmark score with the binomial standard error implied by its question count. `Nonpositive_Fraction` is the share of perturbation trials with Spearman $\rho \le 0$; it is not a null-hypothesis p-value. `Directionally_Stable_95CI` is true exactly when the simulated 95% interval lies entirely above zero.

### RBO calculation

Step 5 additionally calculates RBO as an auxiliary robustness metric. It does not add a separate workflow step or generation command: its per-benchmark values are stored in `analysis_ready_data.csv` and formatted as a column in `correlation_summary_table.tex` by the existing Step 10 command. At depth `d`, agreement is the overlap between the two ranking prefixes divided by `d`:

```text
A_d = |S[:d] intersect T[:d]| / d
RBO = (1 - p) * sum(d=1..infinity, p^(d-1) * A_d)
```

The workflow uses `p=0.9` and restricts both rankings to the same shared set of Study Universe models. For the resulting equal-length finite rankings of length `k`, it uses the standard extrapolated form: the observed sum through depth `k` plus `A_k * p^k`. Ties in benchmark rank and LMArena Elo are resolved lexicographically by model ID. Each benchmark is compared with both its matching LMArena category (`rbo`) and LMArena Overall (`rbo_overall`). The calculation is implemented internally and does not require an external RBO package.

### Output location

Step 10 writes outside this repository to the sibling directory:

```text
project-parent/
├── Human-SIG/
└── overleaf/
    ├── images/
    └── tables/
```

The script creates `images/` and `tables/` if necessary and overwrites files with matching names.

## Rebuild cleaned data and model matching

Run this route only after changing raw data or when you intentionally want to regenerate the review files.

```text
raw data
  -> Step 1: cleaned data
  -> manual duplicate review
  -> Step 2: heuristic model matches
  -> manual match review
  -> Step 3: mappings
```

### Step 1: generate cleaned data

```bash
uv sync
uv run src/processing/step1_generate_cleaned_data.py
```

Step 1:

- recursively discovers every `data/raw/**/data.csv` file;
- detects model and score columns;
- parses percentages, decimals, and values with `±` errors;
- normalizes known 0–1 benchmarks to 0–100;
- assigns competition ranks such as `1, 2, 2, 4`;
- adds numeric suffixes such as `(2)` and `(3)` to repeated model names; and
- creates one unified Artificial Analysis model list at `data/processed/cleaned/artificial_analysis/cleaned_data.csv`.

Review numeric duplicate suffixes before Step 2. A different score alone is not proof that two rows are different model variants; confirm against the source data. If rows are removed or merged, ensure that the remaining ranks are still consistent.

### Step 2: generate review files

```bash
uv run src/processing/step2_generate_review_files.py
```

Step 2 is a deterministic heuristic matcher, not a trusted final review. It:

- rebuilds `data/processed/model_extraction/lmarena_models.json` from LMArena Overall;
- defines the Study Universe as models with Overall score `>= 1330`;
- parses model family, subfamily, version, date, parameters, and other qualifiers;
- proposes LMArena candidates; and
- writes review entries with `untrusted: 1`.

LMArena benchmarks are skipped because they already use LMArena model identities. The ten Artificial Analysis benchmarks share `data/processed/review_files/artificial_analysis.json`.

For each review entry:

- set `selected_lmarena_model` to the correct LMArena model identifier, or `0` when no corresponding model exists;
- set `untrusted` to `0` after the decision is reviewed; and
- keep the JSON syntactically valid.

### Step 3: generate mappings

```bash
uv run src/processing/step3_generate_mapping.py
```

Step 3 includes non-empty string-valued `selected_lmarena_model` entries; numeric sentinel values such as `0` and `-1` are ignored. If multiple benchmark names select the same LMArena model, the first entry is retained. Artificial Analysis uses its unified review file and creates a filtered mapping for each of its ten benchmarks.

## Update raw benchmark data

Install the scraping environment first:

```bash
uv sync --group scraping
```

The unified CLI accepts the following methods:

| Method | Input location and format | Command |
|---|---|---|
| `manual_direct` | Place the supplied file at `data/raw/manual_direct/{benchmark}/data.csv`; no command is needed | — |
| `pandas_read_html` | Put one leaderboard URL in `data/raw/pandas_read_html/{benchmark}/input.txt` | `uv run --group scraping src/main.py scrape --method pandas_read_html` |
| `selenium` | Put one leaderboard URL in `data/raw/selenium/{benchmark}/input.txt` | `uv run --group scraping src/main.py scrape --method selenium` |
| `vals_ai` | Put page source or JSON containing `benchmarkView` in `data/raw/vals_ai/{benchmark}/input.txt` | `uv run --group scraping src/main.py scrape --method vals_ai` |
| `lmarena` | Put table HTML in each `data/raw/lmarena/LMArena-{category}/input.txt` | `uv run --group scraping src/main.py scrape --method lmarena` |
| `frontiermath` | Put table HTML in each tier directory under `data/raw/frontiermath/` | `uv run --group scraping src/main.py scrape --method frontiermath` |
| `artificial_analysis` | Follow the separate workflow below | `uv run --group scraping src/main.py scrape --method artificial_analysis` |

Run every registered scripted method with:

```bash
uv run --group scraping src/main.py scrape --method all
```

`manual_direct` is not a scripted method. After acquisition, verify that every expected benchmark directory contains a non-empty `data.csv`; the current CLI prints scraper errors but does not aggregate them into a failing process exit code.

These commands update raw files only. To propagate changed data into the analysis, return to the rebuild workflow at Step 1, complete both manual reviews, run Step 3, and then resume the main workflow at Step 4.

### Artificial Analysis workflow

Artificial Analysis requires one manual disambiguation step because the public table can repeat a display name for Thinking, Non-Thinking, and Preview variants.

1. Copy the complete table HTML to `data/raw/artificial_analysis/input.txt`.
2. Generate the combined editable CSV:

   ```bash
   uv run --group scraping src/scrapers/artificial_analysis_first_processer.py
   ```

3. Review `data/raw/artificial_analysis/combined_all_benchmarks.csv`. Use the model detail page to label repeated rows with the correct `-Thinking`, `-Non-Thinking`, and, where applicable, `-Preview` suffixes. Do not assign suffixes from row order alone.
4. Generate benchmark-level raw files:

   ```bash
   uv run --group scraping src/main.py scrape --method artificial_analysis
   ```

## Manuscript outputs and selector IDs

Figure and table selectors follow their order of appearance in the paper. Step 10 generates all ten outputs by default; use selectors only to regenerate a subset.

| Selector | Output |
|---|---|
| Figure `1` | `../overleaf/images/Figure_1_SWE_Bench_Illustration.pdf` |
| Figure `2` | `../overleaf/images/Figure_2_Scale.pdf` |
| Figure `3` | `../overleaf/images/Figure_3_Complexity_Categories.pdf` |
| Figure `4` | `../overleaf/images/Figure_4_Recency.pdf` |
| Figure `5` | `../overleaf/images/Figure_5_Difficulty_Variance.pdf` |
| Table `1` | `../overleaf/tables/overall_correlation_table.tex` |
| Table `2` | `../overleaf/tables/reference_difficulty_table.tex` |
| Table `3` | `../overleaf/tables/correlation_summary_table.tex` |
| Table `4` | `../overleaf/tables/results_table_spearman.tex` |
| Table `5` | `../overleaf/tables/uncertainty_table.tex` |

## Figure 1 labels

Figure 1 uses `data/figure_1_swe_bench_labels.csv` to preserve editable labels. Each row has a stable `model_id`; Step 10 recomputes both projected midranks from the current mappings and scores, then carries the matching `display_name` forward. The figure does not recalculate Spearman correlation: it displays the authoritative `spearman_rho` already produced by Step 5 in `results/analysis_ready_data.csv`. Edit only `display_name` unless the underlying model mapping itself changes; display-name changes cannot affect ranks or the displayed coefficient.

To intentionally recreate the CSV from current scores and mappings, run the exporter below. This resets `display_name` to `model_id`, so normally Step 10's automatic rank synchronization is preferable.

```bash
uv run --group plotting src/analysis/export_figure_1_swe_bench_data.py
```

Edit the `display_name` column, then render only Figure 1:

```bash
uv run --group plotting src/analysis/render_figure_1_swe_bench.py
```

All figure-rendering scripts require `adjustText` for label placement. Install the `plotting` group before rendering; the scripts fail immediately when this dependency is missing rather than silently saving figures with unadjusted, potentially overlapping labels.

## Repository layout

```text
Human-SIG/
├── data/
│   ├── metadata.json
│   ├── figure_1_swe_bench_labels.csv
│   ├── raw/
│   │   ├── artificial_analysis/
│   │   ├── frontiermath/
│   │   ├── lmarena/
│   │   ├── manual_direct/
│   │   ├── pandas_read_html/
│   │   ├── selenium/
│   │   └── vals_ai/
│   └── processed/
│       ├── cleaned/{benchmark_id}/
│       │   ├── cleaned_data.csv
│       │   └── mapping.json
│       ├── model_extraction/lmarena_models.json
│       ├── review_files/
│       └── master_table/master_correlation_matrix.csv
├── results/
├── src/
│   ├── analysis/
│   ├── processing/
│   ├── scrapers/
│   └── main.py
├── pyproject.toml
├── uv.lock
└── README.md
```

Step 1 derives `benchmark_id` directly from the raw benchmark directory name and preserves its case. Keep raw directory names aligned with the identifiers used by metadata and review files, especially on case-sensitive systems.

## Troubleshooting

- **A plotting import is missing:** rerun `uv sync --group plotting` or include `--group plotting` in the `uv run` command.
- **A scraper import is missing:** rerun `uv sync --group scraping` or include `--group scraping` in the `uv run` command.
- **Step 10 cannot write files:** confirm that the repository has a writable sibling path at `../overleaf/`, or allow the script to create it.
- **Unicode symbols or a non-ASCII path look corrupted on Windows:** enable UTF-8 before running commands, for example `$env:PYTHONUTF8="1"` in PowerShell.
