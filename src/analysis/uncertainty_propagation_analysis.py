import pandas as pd
import numpy as np
import scipy.stats as stats
from pathlib import Path
import re

N_SIMULATIONS = 10_000
RANDOM_SEED = 42
MIN_COMMON_MODELS = 5
NON_PERCENTAGE_BENCHMARKS = {"Creative Writing v3"}

def load_data():
    base_dir = Path(__file__).parent.parent.parent
    master_path = base_dir / "data/processed/master_table/master_correlation_matrix.csv"
    analysis_ready_path = base_dir / "results/analysis_ready_data.csv"
    
    print("Loading data...")
    df_master = pd.read_csv(master_path)
    df_analysis = pd.read_csv(analysis_ready_path)
    
    return df_master, df_analysis, base_dir

def sanitize_benchmark_id(benchmark_id: str) -> str:
    """Sanitize benchmark ID to match column names in master table."""
    sanitized = re.sub(r'[^\w\-]', '_', str(benchmark_id))
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized.strip('_')

def load_lmarena_category_data(base_dir, category):
    """Load LMArena data for a specific category to get model-specific Elo and uncertainty (CI)."""
    # Map category to folder name
    # The categories in analysis_ready_data.csv match the LMArena folder suffixes
    # e.g., "Math" -> "LMArena-Math"
    folder_name = f"LMArena-{category}"
    lmarena_path = base_dir / f"data/raw/lmarena/{folder_name}/data.csv"
    
    if not lmarena_path.exists():
        raise FileNotFoundError(
            f"Required LMArena category file not found: {lmarena_path}"
        )

    print(f"Loading LMArena data for category '{category}' from {lmarena_path}...")
    
    df_arena = pd.read_csv(lmarena_path)

    model_data = {}
    
    if 'Model' not in df_arena.columns or '95% CI (±)' not in df_arena.columns:
        # Check if we can find columns with slightly different names
        model_col = next((c for c in df_arena.columns if 'Model' in c), None)
        ci_col = next((c for c in df_arena.columns if '95% CI' in c), None)
        
        if not model_col or not ci_col:
            raise ValueError(
                "Required Model and 95% CI columns were not found in "
                f"{lmarena_path}; columns: {df_arena.columns.tolist()}"
            )
    else:
        model_col = 'Model'
        ci_col = '95% CI (±)'
        
    elo_col = 'Elo' if 'Elo' in df_arena.columns else 'Score'
    if elo_col not in df_arena.columns:
         # Try to find a score-like column
         elo_col = next((c for c in df_arena.columns if 'Elo' in c or 'Score' in c), None)
         if not elo_col:
             raise ValueError(f"Elo/Score column not found in {lmarena_path}")

    for _, row in df_arena.iterrows():
        model = str(row[model_col]).strip()
        
        # Parse Elo (handle "1503Preliminary" etc)
        elo_str = str(row[elo_col])
        elo_val_str = re.sub(r'[^\d\.]', '', elo_str)
        try:
            elo = float(elo_val_str)
        except ValueError:
            continue

        # Parse CI
        ci_str = str(row[ci_col])
        ci_val_str = re.sub(r'[^\d\.]', '', ci_str)
        try:
            ci_val = float(ci_val_str)
            sigma = ci_val / 1.96
        except ValueError:
            print(
                f"Warning: skipping model '{model}' because its 95% CI "
                f"value cannot be parsed: {ci_str!r}"
            )
            continue
            
        model_data[model] = {'elo': elo, 'sigma': sigma}
            
    print(f"Loaded data for {len(model_data)} models in category '{category}'.")
    return model_data

def get_benchmark_scores(df_master, benchmark_id):
    """Extract model names and scores for a specific benchmark from master table."""
    # Construct column names
    score_col = f"{benchmark_id}_score"
    model_col = "model_name" # Assuming the first column is model_name
    
    if model_col not in df_master.columns:
        model_col = df_master.columns[0]
    
    if score_col not in df_master.columns:
        sanitized_id = sanitize_benchmark_id(benchmark_id)
        score_col = f"{sanitized_id}_score"
            
    if score_col not in df_master.columns:
        return {}
        
    # Get paired data
    df_subset = df_master[[model_col, score_col]].copy()
    
    # Ensure score is numeric
    df_subset[score_col] = pd.to_numeric(df_subset[score_col], errors='coerce')
    df_subset = df_subset.dropna()
    
    # Return dict: {model_name: score}
    return dict(zip(df_subset[model_col].astype(str).str.strip(), df_subset[score_col]))

def run_simulation():
    df_master, df_analysis, base_dir = load_data()
    rng = np.random.default_rng(RANDOM_SEED)
    
    # Output paths
    output_csv = base_dir / "results/uncertainty_simulation_results.csv"
    
    results = []
    print(f"Starting Monte Carlo simulation ({N_SIMULATIONS} runs per benchmark)...")
    
    # Cache LMArena data to avoid reloading for same category
    lmarena_cache = {}
    
    for i, row in df_analysis.iterrows():
        benchmark_id = row['benchmark_id']
        category = row['category']
        print(f"Processing {i+1}/{len(df_analysis)}: {benchmark_id} (Category: {category})", flush=True)
        
        if pd.isna(row['question_count']) or int(row['question_count']) <= 0:
            raise ValueError(
                f"{benchmark_id} has no valid positive question_count"
            )
        n_questions = int(row['question_count'])
        
        # 1. Load LMArena data for this category
        if category not in lmarena_cache:
            lmarena_cache[category] = load_lmarena_category_data(base_dir, category)
        category_data = lmarena_cache[category]
        
        if not category_data:
            raise ValueError(f"No LMArena data loaded for category {category}")

        # 2. Get Benchmark Scores
        benchmark_scores = get_benchmark_scores(df_master, benchmark_id)
        
        if not benchmark_scores or len(benchmark_scores) < MIN_COMMON_MODELS:
            raise ValueError(
                f"{benchmark_id} has insufficient benchmark score data "
                f"(N={len(benchmark_scores)} < {MIN_COMMON_MODELS})"
            )
            
        # 3. Find Intersection of Models
        common_models = set(category_data.keys()) & set(benchmark_scores.keys())
        
        if len(common_models) < MIN_COMMON_MODELS:
            raise ValueError(
                f"{benchmark_id} has insufficient common models "
                f"(N={len(common_models)} < {MIN_COMMON_MODELS})"
            )
            
        # 4. Prepare Arrays for Simulation
        models = sorted(common_models)
        elos = np.array([category_data[m]['elo'] for m in models])
        sigmas = np.array([category_data[m]['sigma'] for m in models])
        scores = np.array([benchmark_scores[m] for m in models])
        
        n_samples = len(models)
        orig_spearman, _ = stats.spearmanr(elos, scores)

        if benchmark_id in NON_PERCENTAGE_BENCHMARKS:
            print(
                f"Skipping uncertainty simulation for {benchmark_id}: "
                "its leaderboard score is not a percentage accuracy."
            )
            s_mean = s_ci_lower = s_ci_upper = nonpositive_fraction = np.nan
            directionally_stable = np.nan
        else:
            if np.any((scores < 0) | (scores > 100)):
                raise ValueError(
                    f"{benchmark_id} contains scores outside the required 0-100 range"
                )

            # Binomial standard error under the percentage-accuracy model.
            proportions = scores / 100.0
            sigma_scores = np.sqrt(
                proportions * (1.0 - proportions) / n_questions
            ) * 100.0

            sim_spearmans = []
            for _ in range(N_SIMULATIONS):
                sim_scores = rng.normal(scores, sigma_scores)
                sim_elos = rng.normal(elos, sigmas)
                s_corr, _ = stats.spearmanr(sim_elos, sim_scores)
                if np.isfinite(s_corr):
                    sim_spearmans.append(s_corr)

            if not sim_spearmans:
                raise RuntimeError(
                    f"No finite simulation results were produced for {benchmark_id}"
                )

            sim_spearmans = np.asarray(sim_spearmans)
            s_mean = np.mean(sim_spearmans)
            s_ci_lower, s_ci_upper = np.percentile(sim_spearmans, [2.5, 97.5])
            nonpositive_fraction = np.mean(sim_spearmans <= 0)
            directionally_stable = s_ci_lower > 0

        results.append({
            'Benchmark': benchmark_id,
            'Category': category,
            'N_Samples': n_samples,
            'N_Questions': n_questions,
            'Orig_Spearman': orig_spearman,
            'Simulated_Rho': s_mean,
            'Simulated_95_CI_Lower': s_ci_lower,
            'Simulated_95_CI_Upper': s_ci_upper,
            'Nonpositive_Fraction': nonpositive_fraction,
            'Directionally_Stable_95CI': directionally_stable,
        })
        
    if not results:
        raise RuntimeError("No uncertainty-propagation results were generated")

    df_results = pd.DataFrame(results)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(output_csv, index=False, lineterminator='\n')
    print(f"Saved results to {output_csv}")

if __name__ == "__main__":
    run_simulation()
