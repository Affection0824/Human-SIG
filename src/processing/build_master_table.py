"""
Master Table Construction Script

Purpose:
    This script constructs the master correlation matrix by merging benchmark scores and ranks
    with LMArena ELO scores. The master table serves as the foundation for all correlation
    analyses in Phase IV.

Master Table Structure:
    - Index: LMArena model IDs (from Study Universe: elo_overall >= 1330)
    - Columns:
      * LMArena ELO columns: elo_overall, elo_math, elo_coding, elo_instruction_following,
        elo_creative_writing, elo_hard_prompts, elo_expert
      * For each benchmark (with N >= 6): {benchmark_id}_score and {benchmark_id}_rank
    - Missing values: NaN (not filled with zeros)

Merge Strategy:
    - Left join to preserve Study Universe: All models in Study Universe are included as rows
    - Only benchmarks with overlap count N >= 6 are included (filtered during merge loop)
    - Models that appear in benchmarks but cannot be mapped to Study Universe are excluded

Why Both Score and Rank Columns:
    - Score columns: Used for rank-correlation analysis and uncertainty propagation
    - Rank columns: Used for RBO (Rank-Biased Overlap) calculation
    - Both are necessary for comprehensive correlation analysis across different metrics

Input:
    - Cleaned data files: Human-SIG/data/processed/cleaned/{benchmark_id}/cleaned_data.csv
    - Mapping files: Human-SIG/data/processed/cleaned/{benchmark_id}/mapping.json
    - LMArena category data: Human-SIG/data/processed/cleaned/LMArena-{category}/cleaned_data.csv
    - Metadata: Human-SIG/data/metadata.json

Output:
    - Master table: Human-SIG/data/processed/master_table/master_correlation_matrix.csv

Workflow:
    1. Load Study Universe from LMArena-Overall
    2. Initialize df_master with LMArena ELO columns
    3. For each benchmark:
       a. Parse benchmark data using BenchmarkParser
       b. Check overlap count (N >= 6 required)
       c. Left join to df_master
       d. Add {benchmark_id}_score and {benchmark_id}_rank columns
    4. Calculate overlap statistics for validation and logging
    5. Save the master table
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
import logging
import re

import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from parser_utils import BenchmarkParser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def sanitize_column_name(benchmark_id: str) -> str:
    """
    Sanitize benchmark_id for use as a column name in pandas DataFrame.
    
    Replaces spaces and special characters with underscores while preserving
    the original benchmark_id value in data structures.
    
    Args:
        benchmark_id: Original benchmark identifier (e.g., "SWE-bench (Verified)")
        
    Returns:
        Sanitized column name (e.g., "SWE-bench_Verified")
    """
    # Replace spaces and special characters with underscores
    # Keep parentheses as underscores for readability
    sanitized = re.sub(r'[^\w\-]', '_', benchmark_id)
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    return sanitized


def load_lmarena_elo_scores(cleaned_data_dir: Path) -> pd.DataFrame:
    """
    Load all LMArena ELO scores from category cleaned_data.csv files.
    
    Args:
        cleaned_data_dir: Path to cleaned data directory
        
    Returns:
        DataFrame with index=model_name, columns=elo_overall, elo_math, etc.
    """
    # LMArena category names and their corresponding ELO column names
    # Ordered by standardized category order: Overall, Math, Coding, Instruction Following,
    # Creative Writing, Hard Prompts, Expert
    lmarena_categories = {
        'LMArena-Overall': 'elo_overall',
        'LMArena-Math': 'elo_math',
        'LMArena-Coding': 'elo_coding',
        'LMArena-Instruction Following': 'elo_instruction_following',
        'LMArena-Creative Writing': 'elo_creative_writing',
        'LMArena-Hard Prompts': 'elo_hard_prompts',
        'LMArena-Expert': 'elo_expert'
    }
    
    df_elo = None
    missing_categories = []
    
    for category_name, elo_column in lmarena_categories.items():
        category_dir = cleaned_data_dir / category_name
        csv_path = category_dir / "cleaned_data.csv"
        
        if not csv_path.exists():
            missing_categories.append(category_name)
            continue
        
        df_category = pd.read_csv(csv_path)
        
        # In LMArena cleaned_data.csv, model_name is the LMArena model ID
        # and score is the ELO score
        df_category = df_category[['model_name', 'score']].copy()
        df_category = df_category.rename(columns={'score': elo_column})
        df_category = df_category.set_index('model_name')
        
        if df_elo is None:
            df_elo = df_category
        else:
            # Left join to preserve all models
            df_elo = df_elo.join(df_category, how='outer')
    
    if missing_categories:
        raise FileNotFoundError(
            "Missing required LMArena category data: "
            + ", ".join(missing_categories)
        )
    if df_elo is None:
        raise ValueError("No LMArena category data found")
    
    logger.info(f"Loaded LMArena ELO scores for {len(df_elo)} models")
    return df_elo


def get_benchmark_list(metadata_path: Path) -> List[Dict]:
    """
    Load benchmark list from metadata.json, excluding LMArena categories.
    
    Args:
        metadata_path: Path to metadata.json
        
    Returns:
        List of benchmark metadata dictionaries (excluding LMArena entries)
    """
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Filter out meta_info and LMArena entries (entries with elo_column field)
    benchmarks = [
        entry for entry in metadata
        if isinstance(entry, dict) and 'benchmark_id' in entry and 'elo_column' not in entry
    ]
    
    logger.info(f"Found {len(benchmarks)} benchmarks in metadata")
    return benchmarks


def build_master_table(
    cleaned_data_dir: Path,
    metadata_path: Path,
    min_overlap: int = 6
) -> Tuple[pd.DataFrame, Dict]:
    """
    Build the master correlation matrix.
    
    Args:
        cleaned_data_dir: Path to cleaned data directory
        metadata_path: Path to metadata.json
        min_overlap: Minimum overlap count required to include benchmark (default: 6)
        
    Returns:
        Tuple of (master_table DataFrame, overlap_stats dictionary)
    """
    # Load Study Universe
    lmarena_overall_path = cleaned_data_dir / "LMArena-Overall" / "cleaned_data.csv"
    study_universe = BenchmarkParser.load_study_universe(lmarena_overall_path, min_elo=1330.0)
    
    # Load LMArena ELO scores
    df_elo = load_lmarena_elo_scores(cleaned_data_dir)
    
    # Filter ELO scores to Study Universe only
    df_master = df_elo[df_elo.index.isin(study_universe)].copy()
    
    logger.info(f"Initialized master table with {len(df_master)} models from Study Universe")
    
    # Initialize parser
    parser = BenchmarkParser(cleaned_data_dir, study_universe)
    
    # Get benchmark list
    benchmarks = get_benchmark_list(metadata_path)
    
    # Track overlap statistics
    overlap_stats = {}
    study_universe_size = len(df_master)
    
    # Merge loop: For each benchmark
    for benchmark_meta in benchmarks:
        benchmark_id = benchmark_meta['benchmark_id']
        
        try:
            # Parse benchmark data
            df_benchmark, overlap_count = parser.parse_benchmark(benchmark_id)
            
            # Check overlap count
            if overlap_count < min_overlap:
                logger.warning(
                    f"Skipping benchmark {benchmark_id}: insufficient overlap "
                    f"(N={overlap_count} < {min_overlap}) for reliable correlation analysis."
                )
                overlap_stats[benchmark_id] = {
                    'overlap_count': overlap_count,
                    'study_universe_size': study_universe_size,
                    'overlap_percentage': (overlap_count / study_universe_size * 100) if study_universe_size > 0 else 0.0,
                    'included': False
                }
                continue
            
            # Sanitize benchmark_id for column names
            col_prefix = sanitize_column_name(benchmark_id)
            
            # Prepare benchmark data for merge
            df_benchmark = df_benchmark.set_index('lmarena_model_id')
            df_benchmark = df_benchmark.rename(columns={
                'score': f'{col_prefix}_score',
                'rank': f'{col_prefix}_rank'
            })
            
            # Left join to df_master (preserve Study Universe)
            df_master = df_master.join(df_benchmark, how='left')
            
            # Ensure data types
            df_master[f'{col_prefix}_score'] = df_master[f'{col_prefix}_score'].astype('float64')
            df_master[f'{col_prefix}_rank'] = df_master[f'{col_prefix}_rank'].astype('Int64')  # Nullable int
            
            # Record overlap statistics
            overlap_stats[benchmark_id] = {
                'overlap_count': overlap_count,
                'study_universe_size': study_universe_size,
                'overlap_percentage': (overlap_count / study_universe_size * 100) if study_universe_size > 0 else 0.0,
                'included': True
            }
            
            logger.info(
                f"Added {benchmark_id}: {overlap_count} overlapping models "
                f"({overlap_stats[benchmark_id]['overlap_percentage']:.1f}%)"
            )
            
        except Exception as e:
            logger.error(f"Error processing benchmark {benchmark_id}: {e}", exc_info=True)
            overlap_stats[benchmark_id] = {
                'overlap_count': 0,
                'study_universe_size': study_universe_size,
                'overlap_percentage': 0.0,
                'included': False,
                'error': str(e)
            }
            continue
    
    # Check for benchmarks with N < 6
    excluded_benchmarks = [
        bid for bid, stats in overlap_stats.items()
        if stats.get('overlap_count', 0) < min_overlap
    ]
    
    if excluded_benchmarks:
        logger.critical(
            f"CRITICAL WARNING: {len(excluded_benchmarks)} benchmarks excluded due to "
            f"insufficient overlap (N < {min_overlap}): {excluded_benchmarks}"
        )
    
    # Reset index to make model_name a column
    df_master = df_master.reset_index()
    df_master = df_master.rename(columns={'index': 'model_name'})
    
    return df_master, overlap_stats


def main():
    """Main execution function."""
    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    cleaned_data_dir = base_dir / "data" / "processed" / "cleaned"
    metadata_path = base_dir / "data" / "metadata.json"
    output_dir = base_dir / "data" / "processed" / "master_table"

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build master table
    logger.info("Starting master table construction...")
    df_master, overlap_stats = build_master_table(
        cleaned_data_dir=cleaned_data_dir,
        metadata_path=metadata_path,
        min_overlap=6
    )
    
    # Save master table
    output_path = output_dir / "master_correlation_matrix.csv"
    df_master.to_csv(output_path, index=False, na_rep='NaN')
    logger.info(f"Saved master table to {output_path}")
    logger.info(f"Master table shape: {df_master.shape}")
    
    # Print summary
    included_count = sum(1 for stats in overlap_stats.values() if stats.get('included', False))
    excluded_count = len(overlap_stats) - included_count
    
    logger.info(f"\n=== Master Table Construction Summary ===")
    logger.info(f"Total benchmarks processed: {len(overlap_stats)}")
    logger.info(f"Benchmarks included (N >= 6): {included_count}")
    logger.info(f"Benchmarks excluded (N < 6): {excluded_count}")
    logger.info(f"Study Universe size: {overlap_stats[list(overlap_stats.keys())[0]]['study_universe_size'] if overlap_stats else 0}")
    logger.info(f"Master table shape: {df_master.shape}")


if __name__ == "__main__":
    main()

