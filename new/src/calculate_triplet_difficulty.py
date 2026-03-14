import pandas as pd
import numpy as np
from pathlib import Path
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sanitize_benchmark_id(benchmark_id: str) -> str:
    """
    Sanitize benchmark_id to match column names in master table.
    """
    sanitized = re.sub(r'[^\w\-]', '_', str(benchmark_id))
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized.strip('_')

def calculate_triplet_difficulty():
    # Define paths
    base_dir = Path("D:/桌面 2026.1.13/科研/Human-SIG/Human-SIG")
    master_table_path = base_dir / "data/processed/master_table/master_correlation_matrix.csv"
    original_data_path = base_dir / "results/analysis_ready_data.csv"
    output_path = base_dir / "new/data/triplet_difficulty_comparison.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define the 3 models (Group 20)
    target_models = [
        "Anthropicclaude-sonnet-4-5-20250929-thinking-32k",
        "gemini-3-pro",
        "gpt-5.1"
    ]
    
    logger.info(f"Target models: {target_models}")
    
    # Load master table
    logger.info(f"Loading master table from {master_table_path}...")
    try:
        df_master = pd.read_csv(master_table_path)
    except FileNotFoundError:
        logger.error(f"Could not find {master_table_path}")
        return
        
    # Filter for target models
    df_triplet = df_master[df_master['model_name'].isin(target_models)].copy()
    
    if len(df_triplet) != 3:
        logger.error(f"Found {len(df_triplet)} models, expected 3. Missing models?")
        logger.info(f"Found models: {df_triplet['model_name'].tolist()}")
        # Check if names are exact matches or if there are issues
        # Just continue if at least 1 found, but better to warn
        if len(df_triplet) == 0:
            return

    # Set model_name as index for easier lookup
    df_triplet.set_index('model_name', inplace=True)
    
    # Identify benchmark columns (ending with _score, not starting with elo_)
    benchmark_cols = [col for col in df_master.columns if col.endswith('_score') and not col.startswith('elo_')]
    
    triplet_results = []
    
    for col in benchmark_cols:
        benchmark_id_sanitized = col.replace('_score', '')
        
        # Get scores for the 3 models
        scores = df_triplet[col]
        
        # Check if all 3 are not NaN
        if scores.notna().all():
            avg_score = scores.mean()
            # Difficulty = 100 - avg_score
            difficulty = 100 - avg_score
            
            # Store scores for each model for display
            model_scores = {name: score for name, score in scores.items()}
            
            triplet_results.append({
                'sanitized_id': benchmark_id_sanitized,
                'Triplet_Difficulty': difficulty,
                'Triplet_Avg_Score': avg_score,
                'Model_Scores': str(model_scores)
            })
            
    df_triplet_diff = pd.DataFrame(triplet_results)
    logger.info(f"Calculated triplet difficulty for {len(df_triplet_diff)} benchmarks.")
    
    # Load original difficulty
    logger.info(f"Loading original data from {original_data_path}...")
    try:
        df_original = pd.read_csv(original_data_path)
    except FileNotFoundError:
        logger.error(f"Could not find {original_data_path}")
        return
        
    # Prepare original data for merge
    # We want benchmark_id (original name) and difficulty
    df_original_subset = df_original[['benchmark_id', 'difficulty']].copy()
    df_original_subset.rename(columns={'difficulty': 'Original_Difficulty', 'benchmark_id': 'Original_Benchmark_ID'}, inplace=True)
    
    # Add sanitized ID for merging
    df_original_subset['sanitized_id'] = df_original_subset['Original_Benchmark_ID'].apply(sanitize_benchmark_id)
    
    # Merge
    # Left: df_triplet_diff (has sanitized_id)
    # Right: df_original_subset (has sanitized_id, Original_Benchmark_ID, Original_Difficulty)
    df_merged = pd.merge(
        df_triplet_diff, 
        df_original_subset, 
        on='sanitized_id',
        how='left'
    )
    
    # Use Original_Benchmark_ID if available, else sanitized_id
    df_merged['Benchmark_Name'] = df_merged['Original_Benchmark_ID'].fillna(df_merged['sanitized_id'])
    
    # Select final columns
    final_cols = ['Benchmark_Name', 'Original_Difficulty', 'Triplet_Difficulty', 'Triplet_Avg_Score']
    df_final = df_merged[final_cols].copy()
    
    # Sort by Triplet Difficulty Descending
    df_final.sort_values('Triplet_Difficulty', ascending=False, inplace=True)
    
    # Save
    logger.info(f"Saving comparison to {output_path}...")
    df_final.to_csv(output_path, index=False)
    
    # Print table
    print("\nDifficulty Comparison (Triplet vs Original):")
    # Format float columns
    print(df_final.to_string(index=False, float_format="%.2f"))
    
    print("\nNote: Triplet Difficulty = 100 - Average Score of the 3 specified models.")
    print(f"Models used: {target_models}")

if __name__ == "__main__":
    calculate_triplet_difficulty()
