import pandas as pd
from pathlib import Path
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REFERENCE_MODELS = (
    "Anthropicclaude-opus-4-5-20251101",
    "gemini-2.5-pro",
    "gpt-5.1",
)

def sanitize_benchmark_id(benchmark_id: str) -> str:
    """
    Sanitize benchmark_id to match column names in master table.
    """
    sanitized = re.sub(r'[^\w\-]', '_', str(benchmark_id))
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized.strip('_')

def calculate_reference_difficulty() -> None:
    # Define paths dynamically based on script location
    # Script is in src/analysis/, so base_dir is 3 levels up
    base_dir = Path(__file__).resolve().parent.parent.parent
    master_table_path = base_dir / "data" / "processed" / "master_table" / "master_correlation_matrix.csv"
    original_data_path = base_dir / "results" / "analysis_ready_data.csv"
    
    # Output to results directory
    output_path = base_dir / "results" / "reference_difficulty_comparison.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Reference models: {list(REFERENCE_MODELS)}")
    
    # Load master table
    logger.info(f"Loading master table from {master_table_path}...")
    df_master = pd.read_csv(master_table_path)
        
    # Filter for target models
    df_reference = df_master[df_master['model_name'].isin(REFERENCE_MODELS)].copy()
    
    found_models = set(df_reference['model_name'])
    missing_models = [model for model in REFERENCE_MODELS if model not in found_models]
    if missing_models:
        message = f"Reference difficulty requires all three models; missing: {missing_models}"
        logger.error(message)
        logger.info(f"Found models: {df_reference['model_name'].tolist()}")
        raise ValueError(message)

    # Set model_name as index for easier lookup
    df_reference.set_index('model_name', inplace=True)
    
    # Identify benchmark columns (ending with _score, not starting with elo_)
    benchmark_cols = [col for col in df_master.columns if col.endswith('_score') and not col.startswith('elo_')]
    
    reference_results = []
    
    for col in benchmark_cols:
        benchmark_id_sanitized = col.removesuffix('_score')
        
        # Get scores for the 3 models
        scores = df_reference[col]
        
        # Check if all 3 are not NaN
        if scores.notna().all():
            avg_score = scores.mean()
            # Difficulty = 100 - avg_score
            difficulty = 100 - avg_score
            
            reference_results.append({
                'sanitized_id': benchmark_id_sanitized,
                'Reference_Difficulty': difficulty,
                'Reference_Avg_Score': avg_score,
            })
            
    df_reference_diff = pd.DataFrame(reference_results)
    logger.info(f"Calculated reference difficulty for {len(df_reference_diff)} benchmarks.")
    
    # Load original difficulty
    logger.info(f"Loading original data from {original_data_path}...")
    df_original = pd.read_csv(original_data_path)
    df_original_subset = df_original[['benchmark_id', 'difficulty']].copy()
    df_original_subset.rename(columns={'difficulty': 'Original_Difficulty', 'benchmark_id': 'Original_Benchmark_ID'}, inplace=True)

    # Add sanitized ID for merging
    df_original_subset['sanitized_id'] = df_original_subset['Original_Benchmark_ID'].apply(sanitize_benchmark_id)

    # Merge
    df_merged = pd.merge(
        df_reference_diff,
        df_original_subset,
        on='sanitized_id',
        how='left'
    )

    # Use Original_Benchmark_ID if available, else sanitized_id
    df_merged['Benchmark_Name'] = df_merged['Original_Benchmark_ID'].fillna(df_merged['sanitized_id'])

    # Select final columns
    final_cols = ['Benchmark_Name', 'Original_Difficulty', 'Reference_Difficulty', 'Reference_Avg_Score']
    df_final = df_merged[final_cols].copy()
    
    # Sort by Reference Difficulty Descending
    if 'Reference_Difficulty' in df_final.columns:
        df_final.sort_values('Reference_Difficulty', ascending=False, inplace=True)
    
    # Save
    logger.info(f"Saving comparison to {output_path}...")
    df_final.to_csv(output_path, index=False, lineterminator='\n')
    
    # Print table
    print("\nDifficulty Comparison (Reference vs Original):")
    # Format float columns
    print(df_final.to_string(index=False, float_format="%.2f"))
    
    print("\nNote: Reference Difficulty = 100 - Average Score of the 3 specified models.")
    print(f"Models used: {list(REFERENCE_MODELS)}")

if __name__ == "__main__":
    calculate_reference_difficulty()
