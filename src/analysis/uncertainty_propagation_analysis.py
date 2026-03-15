import pandas as pd
import numpy as np
import scipy.stats as stats
from pathlib import Path
import re
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
import sys

# Add parent directory to path for imports if needed
sys.path.insert(0, str(Path(__file__).parent))

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
        # Try fallback to Overall if category file doesn't exist (though it should)
        print(f"Warning: Category file not found at {lmarena_path}. Falling back to Overall.")
        lmarena_path = base_dir / "data/raw/lmarena/LMArena-Overall/data.csv"

    print(f"Loading LMArena data for category '{category}' from {lmarena_path}...")
    
    try:
        df_arena = pd.read_csv(lmarena_path)
    except Exception as e:
        print(f"Error loading LMArena data: {e}")
        return {}

    model_data = {}
    
    if 'Model' not in df_arena.columns or '95% CI (±)' not in df_arena.columns:
        # Check if we can find columns with slightly different names
        model_col = next((c for c in df_arena.columns if 'Model' in c), None)
        ci_col = next((c for c in df_arena.columns if '95% CI' in c), None)
        
        if not model_col or not ci_col:
            print("Warning: Required columns (Model, 95% CI) not found in LMArena data.")
            print(f"Columns found: {df_arena.columns.tolist()}")
            return {}
    else:
        model_col = 'Model'
        ci_col = '95% CI (±)'
        
    elo_col = 'Elo' if 'Elo' in df_arena.columns else 'Score'
    if elo_col not in df_arena.columns:
         # Try to find a score-like column
         elo_col = next((c for c in df_arena.columns if 'Elo' in c or 'Score' in c), None)
         if not elo_col:
             print("Warning: Elo/Score column not found.")
             return {}

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
            # Default sigma if parsing fails? Or skip? 
            # Better to skip or set high uncertainty
            # print(f"Warning: Could not parse CI value '{ci_str}' for model '{model}'")
            sigma = 20.0 # Fallback
            
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
    
    # Configuration
    N_SIMULATIONS = 10000 # Fixed as requested
    
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
        
        # Handle NaN question_count
        if pd.isna(row['question_count']):
             n_questions = 100 # Default fallback if unknown
        else:
             n_questions = int(row['question_count'])
        
        # 1. Load LMArena data for this category
        if category not in lmarena_cache:
            lmarena_cache[category] = load_lmarena_category_data(base_dir, category)
        category_data = lmarena_cache[category]
        
        if not category_data:
            print(f"Skipping {benchmark_id}: No LMArena data for category {category}")
            continue

        # 2. Get Benchmark Scores
        benchmark_scores = get_benchmark_scores(df_master, benchmark_id)
        
        if not benchmark_scores or len(benchmark_scores) < 5:
            print(f"Skipping {benchmark_id}: Not enough score data (N={len(benchmark_scores)})")
            continue
            
        # 3. Find Intersection of Models
        common_models = set(category_data.keys()) & set(benchmark_scores.keys())
        
        if len(common_models) < 5:
            print(f"Skipping {benchmark_id}: Not enough common models (N={len(common_models)})")
            continue
            
        # 4. Prepare Arrays for Simulation
        models = list(common_models)
        elos = np.array([category_data[m]['elo'] for m in models])
        sigmas = np.array([category_data[m]['sigma'] for m in models])
        scores = np.array([benchmark_scores[m] for m in models])
        
        # Check for abnormal score range (if > 100, assume not normalized)
        # But compute_features_robust says most are normalized.
        # If max > 1.0 and <= 100.0, assume percentage.
        # If max <= 1.0, assume 0-1 scale and multiply by 100.
        if np.max(scores) <= 1.0:
             scores = scores * 100.0
             
        # If max > 105, might be raw score not percentage (e.g. big bench) or just > 100%
        # We clamp to 0-100 for simulation logic (binomial assumption)
        # scores = np.clip(scores, 0, 100) 
        
        n_samples = len(models)
        
        try:
            # Original correlations (using Category Elo)
            orig_spearman, orig_s_p = stats.spearmanr(elos, scores)
            
            # Simulation
            sim_spearmans = []
            
            for _ in range(N_SIMULATIONS):
                # 1. Perturb scores
                # Laplace smoothing for variance calculation to avoid zero variance at 0 or 100
                p = scores / 100.0
                p_smoothed = (scores/100.0 * n_questions + 1) / (n_questions + 2)
                var = p_smoothed * (1 - p_smoothed) / n_questions
                sigma_scores = np.sqrt(var) * 100
                
                sim_scores = np.random.normal(scores, sigma_scores)
                # sim_scores = np.clip(sim_scores, 0, 100) # Optional clipping
                
                # 2. Perturb Elos using model-specific sigmas
                sim_elos = np.random.normal(elos, sigmas)
                
                # 3. Calculate correlations
                try:
                    s_corr, _ = stats.spearmanr(sim_elos, sim_scores)
                    if not np.isnan(s_corr):
                        sim_spearmans.append(s_corr)
                except:
                    pass
                
            # Calculate robust statistics
            sim_spearmans = np.array(sim_spearmans)
            
            if len(sim_spearmans) > 0:
                s_mean = np.mean(sim_spearmans)
                s_ci_lower = np.percentile(sim_spearmans, 2.5)
                s_ci_upper = np.percentile(sim_spearmans, 97.5)
                # P-value: Frequency of correlation <= 0 (Testing for positive correlation)
                s_p_value = np.mean(sim_spearmans <= 0)
                s_robust_sig = not (s_ci_lower <= 0 <= s_ci_upper)
            else:
                s_mean, s_ci_lower, s_ci_upper, s_p_value, s_robust_sig = np.nan, np.nan, np.nan, np.nan, False
                
            results.append({
                'Benchmark': benchmark_id,
                'Category': category,
                'N_Samples': n_samples,
                'N_Questions': n_questions,
                'Orig_Spearman': orig_spearman,
                'Orig_Spearman_P': orig_s_p,
                'Simulated_Rho': s_mean,
                'Simulated_95_CI_Lower': s_ci_lower,
                'Simulated_95_CI_Upper': s_ci_upper,
                'Simulated_P_Value': s_p_value,
                'Is_Robust': s_robust_sig
            })
        
        except Exception as e:
            print(f"Error processing {benchmark_id}: {e}")
            # import traceback
            # traceback.print_exc()
            continue
        
    # Save results if we ran the simulation
    if len(results) > 0:
        df_results = pd.DataFrame(results)
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        df_results.to_csv(output_csv, index=False)
        print(f"Saved results to {output_csv}")
    else:
        print("No results generated. Check warnings above.")

if __name__ == "__main__":
    run_simulation()
