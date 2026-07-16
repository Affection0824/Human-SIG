"""
Benchmark Parser Utility Module

Purpose:
    This module provides the BenchmarkParser class for parsing benchmark scores from CSV files
    and preparing them for master table construction. The parser reads standardized cleaned data
    files (cleaned_data.csv) that contain model names, scores, and ranks. All benchmarks except
    Creative Writing v3 have been normalized to 0-100 scale during data preparation.

Input:
    - Cleaned data files from Human-SIG/data/processed/cleaned/{benchmark_id}/cleaned_data.csv
    - Mapping files from Human-SIG/data/processed/cleaned/{benchmark_id}/mapping.json
    - Study Universe definition from LMArena-Overall cleaned_data.csv (models with elo_overall >= 1330)

Output:
    - Parsed benchmark data with scores and ranks, filtered to Study Universe models only
    - Both original scores and computed ranks are output for correlation analysis

Workflow:
    1. Load cleaned_data.csv containing model_name, score, rank columns
    2. Load mapping.json to map benchmark model names to LMArena model IDs
    3. Filter to Study Universe (models present in LMArena with elo_overall >= 1330)
    4. Perform entity resolution using mapping table
    5. Recompute ranks within Study Universe using method='min' for tie-breaking
    6. Output both scores and ranks for master table construction

Key Assumptions:
    - All benchmarks except Creative Writing v3 are normalized to 0-100 scale (higher is better)
    - Creative Writing v3 uses Elo scores and is not normalized
    - Ranking logic assumes "higher score = better rank" for all benchmarks
    - Tied scores receive the same rank (method='min'), which is critical for RBO calculation
    - Only models that can be mapped to Study Universe are included in ranking
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BenchmarkParser:
    """
    Parser for benchmark cleaned data files.
    
    This class handles loading benchmark scores from cleaned_data.csv files,
    performing entity resolution using mapping.json files, filtering to Study Universe,
    and computing ranks within the Study Universe for RBO calculation.
    """
    
    def __init__(self, cleaned_data_dir: Path, study_universe: set):
        """
        Initialize the BenchmarkParser.
        
        Args:
            cleaned_data_dir: Path to the cleaned data directory (Human-SIG/data/processed/cleaned/)
            study_universe: Set of LMArena model IDs that form the Study Universe (elo_overall >= 1330)
        """
        self.cleaned_data_dir = Path(cleaned_data_dir)
        self.study_universe = study_universe
        
    def load_cleaned_data(self, benchmark_id: str) -> pd.DataFrame:
        """
        Load cleaned_data.csv for a benchmark.
        
        Args:
            benchmark_id: The benchmark identifier (e.g., "HumanEval", "SWE-bench (Verified)")
            
        Returns:
            DataFrame with columns: model_name, score, rank
        """
        benchmark_dir = self.cleaned_data_dir / benchmark_id
        csv_path = benchmark_dir / "cleaned_data.csv"
        
        if not csv_path.exists():
            raise FileNotFoundError(f"Cleaned data file not found: {csv_path}")
        
        df = pd.read_csv(csv_path)
        
        # Validate required columns
        required_columns = ['model_name', 'score', 'rank']
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns in {csv_path}: {missing_columns}")
        
        # Validate data types
        if not pd.api.types.is_numeric_dtype(df['score']):
            raise ValueError(f"Score column must be numeric in {csv_path}")
        if not pd.api.types.is_integer_dtype(df['rank']):
            # Try to convert to int if possible
            df['rank'] = pd.to_numeric(df['rank'], errors='coerce').astype('Int64')
        
        logger.info(f"Loaded {len(df)} models from {benchmark_id}")
        return df
    
    def load_mapping(self, benchmark_id: str) -> Dict[str, str]:
        """
        Load mapping.json for a benchmark.
        
        Args:
            benchmark_id: The benchmark identifier
            
        Returns:
            Dictionary mapping benchmark model names to LMArena model IDs
            Mapping dictionary for the requested benchmark
        """
        benchmark_dir = self.cleaned_data_dir / benchmark_id
        mapping_path = benchmark_dir / "mapping.json"
        
        if not mapping_path.exists():
            raise FileNotFoundError(f"Mapping file not found: {mapping_path}")
        
        with open(mapping_path, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        
        logger.info(f"Loaded {len(mapping)} mappings for {benchmark_id}")
        return mapping
    
    def parse_benchmark(self, benchmark_id: str) -> Tuple[pd.DataFrame, int]:
        """
        Parse a benchmark's cleaned data and return scores/ranks for Study Universe models.
        
        This method:
        1. Loads cleaned_data.csv
        2. Loads the required mapping.json
        3. Maps benchmark model names to LMArena model IDs
        4. Filters to Study Universe models only
        5. Recomputes ranks within Study Universe using method='min' for tie-breaking
        
        Args:
            benchmark_id: The benchmark identifier
            
        Returns:
            Tuple of (DataFrame with columns: lmarena_model_id, score, rank, overlap_count)
            - lmarena_model_id: LMArena model ID (used as index in master table)
            - score: Original score from cleaned_data.csv
            - rank: Recomputed rank within Study Universe (method='min' for ties)
            - overlap_count: Number of overlapping models (for validation)
        """
        # Load cleaned data
        df = self.load_cleaned_data(benchmark_id)
        
        # Load mapping
        mapping = self.load_mapping(benchmark_id)
        
        # Map benchmark model names to LMArena model IDs.
        df['lmarena_model_id'] = df['model_name'].map(mapping)
        
        # Filter to Study Universe only
        df_filtered = df[df['lmarena_model_id'].isin(self.study_universe)].copy()
        
        # Count overlap
        overlap_count = len(df_filtered)
        
        if overlap_count == 0:
            logger.warning(f"No overlapping models found for {benchmark_id} in Study Universe")
            return pd.DataFrame(columns=['lmarena_model_id', 'score', 'rank']), 0
        
        # Recompute ranks within Study Universe
        # Use method='min' for tie-breaking (critical for RBO calculation)
        # Higher scores get better (lower) ranks
        df_filtered['rank'] = df_filtered['score'].rank(method='min', ascending=False).astype(int)
        
        # Select and reorder columns
        result_df = df_filtered[['lmarena_model_id', 'score', 'rank']].copy()
        
        logger.info(f"Parsed {benchmark_id}: {overlap_count} models in Study Universe")
        
        return result_df, overlap_count
    
    @staticmethod
    def load_study_universe(lmarena_overall_path: Path, min_elo: float = 1330.0) -> set:
        """
        Load Study Universe from LMArena-Overall cleaned_data.csv.
        
        The Study Universe consists of all models in LMArena with elo_overall >= min_elo.
        
        Args:
            lmarena_overall_path: Path to LMArena-Overall cleaned_data.csv
            min_elo: Minimum ELO score for inclusion in Study Universe (default: 1330.0)
            
        Returns:
            Set of LMArena model IDs (model_name values) that form the Study Universe
        """
        if not lmarena_overall_path.exists():
            raise FileNotFoundError(f"LMArena-Overall data not found: {lmarena_overall_path}")
        
        df = pd.read_csv(lmarena_overall_path)
        
        # Filter to models with score >= min_elo
        # Note: In LMArena-Overall, the 'score' column is elo_overall
        df_universe = df[df['score'] >= min_elo].copy()
        
        study_universe = set(df_universe['model_name'].unique())
        
        logger.info(f"Loaded Study Universe: {len(study_universe)} models with elo_overall >= {min_elo}")
        
        return study_universe

