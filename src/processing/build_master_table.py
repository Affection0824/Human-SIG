"""
Master Table Construction Module

Purpose:
    This module constructs the master correlation matrix by merging benchmark scores and ranks
    with LMArena ELO scores. The master table serves as the foundation for all correlation analyses
    and hypothesis testing.

Master Table Structure:
    - Index: LMArena model IDs (Study Universe: models with elo_overall >= 1330)
    - Columns:
        - ELO columns: elo_overall, elo_math, elo_coding, elo_instruction_following,
          elo_creative_writing, elo_hard_prompts, elo_expert
        - Benchmark columns: For each benchmark, two columns are added:
          - {benchmark_id}_score: Benchmark score (float64)
          - {benchmark_id}_rank: Benchmark rank within Study Universe (int)
    - Missing values: Represented as NaN (not filled with zeros or default values)

Merge Strategy:
    - Left join to preserve Study Universe: All models in the Study Universe are included
      as rows, even if they don't have scores for a particular benchmark
    - Models that appear in benchmark but cannot be mapped to Study Universe are excluded
    - Both score and rank columns are needed:
      - Score: For Pearson/Spearman correlation calculations
      - Rank: For RBO (Rank-Biased Overlap) calculations

Input:
    - LMArena category data: Human-SIG/data/processed/cleaned/LMArena-{category}/cleaned_data.csv
    - Benchmark data: Human-SIG/data/processed/cleaned/{benchmark_id}/cleaned_data.csv
    - Mapping files: Human-SIG/data/processed/cleaned/{benchmark_id}/mapping.json
    - Metadata: Human-SIG/data/metadata.json (to identify benchmarks vs LMArena categories)
    - Study Universe: Human-SIG/data/processed/model_extraction/lmarena_models.json

Output:
    - Master table: Human-SIG/data/processed/master_table/master_correlation_matrix.csv
    - Overlap statistics: Human-SIG/results/data_overlap_stats.json

Workflow:
    1. Load Study Universe from lmarena_models.json
    2. Initialize df_master with LMArena ELO scores (from LMArena category cleaned_data.csv files)
    3. For each benchmark (from metadata.json, entries without elo_column):
       a. Load benchmark data using BenchmarkParser
       b. Perform entity resolution using mapping.json
       c. Left join benchmark scores and ranks onto df_master
       d. Add {benchmark_id}_score and {benchmark_id}_rank columns
    4. Calculate overlap statistics (sparsity matrix)
    5. Save master table and overlap statistics
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
import re

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.processing.parser_utils import BenchmarkParser


def sanitize_benchmark_id(benchmark_name: str) -> str:
    """
    Sanitize benchmark name to create a valid column name (benchmark_id).
    
    Converts benchmark name to lowercase, replaces spaces and special characters
    with underscores, and removes consecutive underscores.
    
    Examples:
        "HumanEval" -> "humaneval"
        "MMLU-Pro" -> "mmlu_pro"
        "SWE-bench (Verified)" -> "swe_bench_verified"
    
    Args:
        benchmark_name: Original benchmark name
    
    Returns:
        Sanitized benchmark ID suitable for use as column name
    """
    # Convert to lowercase
    sanitized = benchmark_name.lower()
    # Replace spaces, hyphens, parentheses, and other special chars with underscores
    sanitized = re.sub(r'[^a-z0-9]+', '_', sanitized)
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    return sanitized


def load_lmarena_elo_scores(
    data_dir: Path,
    study_universe: set,
    category_order: List[str]
) -> pd.DataFrame:
    """
    Load LMArena ELO scores for all categories and create initial master DataFrame.
    
    Args:
        data_dir: Path to data/processed/cleaned directory
        study_universe: Set of LMArena model IDs (Study Universe)
        category_order: List of category names in standardized order
    
    Returns:
        DataFrame with LMArena model IDs as index and ELO columns
    """
    # Map category names to column names
    category_to_column = {
        'Overall': 'elo_overall',
        'Math': 'elo_math',
        'Coding': 'elo_coding',
        'Instruction Following': 'elo_instruction_following',
        'Creative Writing': 'elo_creative_writing',
        'Hard Prompts': 'elo_hard_prompts',
        'Expert': 'elo_expert'
    }
    
    # Initialize DataFrame with Study Universe as index
    df_master = pd.DataFrame(index=sorted(study_universe))
    
    # Load ELO scores for each category
    for category in category_order:
        category_folder = f"LMArena-{category}"
        category_path = data_dir / category_folder / "cleaned_data.csv"
        
        if not category_path.exists():
            print(f"Warning: {category_path} not found. Skipping {category}.")
            continue
        
        # Load category data
        df_category = pd.read_csv(category_path)
        
        # Use model_name as the key (LMArena categories don't need mapping)
        df_category = df_category.set_index('model_name')
        
        # Map to column name
        column_name = category_to_column[category]
        
        # Left join to preserve Study Universe
        df_master[column_name] = df_category['score'].reindex(df_master.index)
    
    return df_master


def build_master_table(
    data_dir: Path,
    metadata_path: Path,
    lmarena_models_path: Path,
    output_dir: Path,
    results_dir: Path
) -> None:
    """
    Build the master correlation matrix by merging all benchmark data with LMArena ELO scores.
    
    This function:
    1. Loads Study Universe from lmarena_models.json
    2. Initializes df_master with LMArena ELO scores
    3. For each benchmark, loads data using BenchmarkParser and merges onto df_master
    4. Calculates overlap statistics
    5. Saves master table and overlap statistics
    
    Args:
        data_dir: Path to data/processed/cleaned directory
        metadata_path: Path to data/metadata.json
        lmarena_models_path: Path to data/processed/model_extraction/lmarena_models.json
        output_dir: Path to data/processed/master_table directory (for output CSV)
        results_dir: Path to results directory (for overlap stats JSON)
    """
    # Load metadata
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Filter out meta_info entry and LMArena entries (entries with elo_column)
    benchmarks = [
        entry for entry in metadata
        if 'benchmark_name' in entry and 'elo_column' not in entry
    ]
    
    # Load Study Universe
    study_universe = BenchmarkParser.load_study_universe(lmarena_models_path)
    print(f"Study Universe size: {len(study_universe)} models")
    
    # Initialize parser
    parser = BenchmarkParser(study_universe)
    
    # Standardized category order for ELO columns
    category_order = ['Overall', 'Math', 'Coding', 'Instruction Following',
                      'Creative Writing', 'Hard Prompts', 'Expert']
    
    # Initialize master DataFrame with LMArena ELO scores
    df_master = load_lmarena_elo_scores(data_dir, study_universe, category_order)
    print(f"Initialized master table with {len(df_master)} models")
    
    # Overlap statistics
    overlap_stats = {}
    
    # Process each benchmark
    for benchmark_entry in benchmarks:
        benchmark_name = benchmark_entry['benchmark_name']
        benchmark_id = sanitize_benchmark_id(benchmark_name)
        
        print(f"\nProcessing benchmark: {benchmark_name} (ID: {benchmark_id})")
        
        # Paths
        benchmark_folder = data_dir / benchmark_name
        cleaned_data_path = benchmark_folder / "cleaned_data.csv"
        mapping_path = benchmark_folder / "mapping.json"
        
        if not cleaned_data_path.exists():
            print(f"  Warning: {cleaned_data_path} not found. Skipping.")
            continue
        
        # Check if mapping file exists (benchmarks should have it, LMArena categories don't)
        if not mapping_path.exists():
            mapping_path = None
        
        # Parse benchmark data
        try:
            parsed_data = parser.parse_benchmark(cleaned_data_path, mapping_path)
            scores_dict = parsed_data['scores']
            ranks_dict = parsed_data['ranks']
        except Exception as e:
            print(f"  Error parsing {benchmark_name}: {e}. Skipping.")
            continue
        
        # Calculate overlap
        overlap_count = len(scores_dict)
        overlap_percentage = (overlap_count / len(study_universe)) * 100
        
        overlap_stats[benchmark_id] = {
            'overlap_count': overlap_count,
            'study_universe_size': len(study_universe),
            'overlap_percentage': round(overlap_percentage, 2)
        }
        
        print(f"  Overlap: {overlap_count} models ({overlap_percentage:.2f}%)")
        
        if overlap_count < 10:
            print(f"  CRITICAL WARNING: Insufficient overlap (N={overlap_count}) for reliable correlation analysis!")
        
        # Create Series for scores and ranks
        scores_series = pd.Series(scores_dict, name=f'{benchmark_id}_score', dtype='float64')
        ranks_series = pd.Series(ranks_dict, name=f'{benchmark_id}_rank', dtype='Int64')  # Nullable int
        
        # Left join to preserve Study Universe (models without scores get NaN)
        df_master[f'{benchmark_id}_score'] = scores_series.reindex(df_master.index)
        df_master[f'{benchmark_id}_rank'] = ranks_series.reindex(df_master.index)
    
    # Save overlap statistics
    results_dir.mkdir(parents=True, exist_ok=True)
    overlap_stats_path = results_dir / "data_overlap_stats.json"
    
    overlap_stats_json = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "description": "Overlap statistics for each benchmark, indicating how many models from the Study Universe have scores in that benchmark",
        **overlap_stats
    }
    
    with open(overlap_stats_path, 'w', encoding='utf-8') as f:
        json.dump(overlap_stats_json, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved overlap statistics to {overlap_stats_path}")
    
    # Add model_name column for CSV output (index as column)
    df_master_output = df_master.reset_index()
    df_master_output.rename(columns={'index': 'model_name'}, inplace=True)
    
    # Ensure proper column order: model_name, then ELO columns, then benchmark columns
    elo_columns = [col for col in df_master_output.columns if col.startswith('elo_')]
    benchmark_columns = [col for col in df_master_output.columns 
                        if col not in ['model_name'] + elo_columns]
    
    # Sort benchmark columns by benchmark_id (alphabetically)
    benchmark_columns_sorted = sorted(benchmark_columns, key=lambda x: x.split('_')[0])
    
    column_order = ['model_name'] + elo_columns + benchmark_columns_sorted
    df_master_output = df_master_output[column_order]
    
    # Save master table
    output_dir.mkdir(parents=True, exist_ok=True)
    master_table_path = output_dir / "master_correlation_matrix.csv"
    df_master_output.to_csv(master_table_path, index=False, na_rep='NaN')
    
    print(f"Saved master table to {master_table_path}")
    print(f"Master table shape: {df_master_output.shape}")
    print(f"Columns: {len(df_master_output.columns)} (1 model_name + {len(elo_columns)} ELO + {len(benchmark_columns)} benchmark columns)")


if __name__ == "__main__":
    # Paths
    base_dir = Path(__file__).parent.parent.parent
    data_dir = base_dir / "data" / "processed" / "cleaned"
    metadata_path = base_dir / "data" / "metadata.json"
    lmarena_models_path = base_dir / "data" / "processed" / "model_extraction" / "lmarena_models.json"
    output_dir = base_dir / "data" / "processed" / "master_table"
    results_dir = base_dir / "results"
    
    build_master_table(
        data_dir=data_dir,
        metadata_path=metadata_path,
        lmarena_models_path=lmarena_models_path,
        output_dir=output_dir,
        results_dir=results_dir
    )

