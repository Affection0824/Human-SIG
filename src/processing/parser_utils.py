"""
Benchmark Parser Utility Module

Purpose:
    This module provides the BenchmarkParser class for parsing benchmark scores from CSV files
    and preparing them for master table construction. The parser reads standardized cleaned data
    files (which contain model names, scores, and pre-computed ranks), performs entity resolution
    using mapping files to align benchmark model names with LMArena model IDs, filters to the
    Study Universe (models with elo_overall >= 1330), and recomputes ranks within the Study Universe
    using the 'min' method for tie-breaking to support rigorous RBO calculation.

Input:
    - Cleaned data files from Human-SIG/data/processed/cleaned/{benchmark_id}/cleaned_data.csv
      Format: CSV with columns: model_name, score, rank
    - Mapping files from Human-SIG/data/processed/cleaned/{benchmark_id}/mapping.json
      Format: JSON object mapping benchmark model names to LMArena model IDs
    - Study Universe definition from Human-SIG/data/processed/model_extraction/lmarena_models.json
      Contains all LMArena models with elo_overall >= 1330

Output:
    - Dictionary with keys: 'scores' and 'ranks'
      - 'scores': Dict mapping LMArena model IDs to benchmark scores
      - 'ranks': Dict mapping LMArena model IDs to benchmark ranks (recomputed within Study Universe)

Key Assumptions:
    - All benchmarks except Creative Writing v3 are normalized to 0-100 range during data preparation
    - All benchmarks (except Creative Writing v3) represent "higher is better" performance
    - Ranking uses method='min' for tie-breaking (e.g., two models with score 95 both get rank 1,
      next model gets rank 3) to support RBO calculation
    - Only models that can be mapped to the Study Universe are included in ranking
    - Models that appear in benchmark but cannot be mapped are excluded

Workflow:
    1. Load cleaned_data.csv to get benchmark model names, scores, and ranks
    2. Load mapping.json to map benchmark model names to LMArena model IDs
    3. Load Study Universe (all model IDs from lmarena_models.json)
    4. Perform entity resolution: map benchmark model names to LMArena IDs
    5. Filter to only include models present in both benchmark data (after mapping) and Study Universe
    6. Recompute ranks within the filtered Study Universe using method='min'
    7. Return scores and ranks as dictionaries keyed by LMArena model ID
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, Set, Optional


class BenchmarkParser:
    """
    Parser for benchmark data files that performs entity resolution and ranking within Study Universe.
    
    This class reads cleaned benchmark data files, maps benchmark model names to LMArena model IDs
    using mapping files, filters to the Study Universe, and recomputes ranks using the 'min' method
    for tie-breaking to support RBO calculation.
    """
    
    def __init__(self, study_universe: Set[str]):
        """
        Initialize the BenchmarkParser with a Study Universe.
        
        Args:
            study_universe: Set of LMArena model IDs that define the Study Universe
                          (models with elo_overall >= 1330)
        """
        self.study_universe = study_universe
    
    @classmethod
    def load_study_universe(cls, lmarena_models_path: Path) -> Set[str]:
        """
        Load the Study Universe from lmarena_models.json.
        
        The Study Universe consists of all models in the LMArena dataset with elo_overall >= 1330.
        The lmarena_models.json file already contains only models meeting this criterion.
        
        Args:
            lmarena_models_path: Path to lmarena_models.json file
            
        Returns:
            Set of LMArena model IDs (keys from the JSON file)
        """
        with open(lmarena_models_path, 'r', encoding='utf-8') as f:
            lmarena_models = json.load(f)
        return set(lmarena_models.keys())
    
    def parse_benchmark(
        self,
        cleaned_data_path: Path,
        mapping_path: Optional[Path] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Parse a benchmark data file and return scores and ranks for models in Study Universe.
        
        This method:
        1. Loads the cleaned_data.csv file (contains model_name, score, rank)
        2. Loads the mapping.json file (maps benchmark model names to LMArena IDs)
        3. Performs entity resolution to map benchmark model names to LMArena IDs
        4. Filters to only include models present in both benchmark data (after mapping) and Study Universe
        5. Recomputes ranks within the filtered Study Universe using method='min' for tie-breaking
        6. Returns scores and ranks as dictionaries keyed by LMArena model ID
        
        Args:
            cleaned_data_path: Path to cleaned_data.csv file
            mapping_path: Optional path to mapping.json file. If None, assumes no mapping exists
                         (e.g., for LMArena categories which don't need mapping)
        
        Returns:
            Dictionary with keys:
                - 'scores': Dict mapping LMArena model IDs to benchmark scores (float)
                - 'ranks': Dict mapping LMArena model IDs to benchmark ranks (int)
        """
        # Load cleaned data
        df = pd.read_csv(cleaned_data_path)
        
        # Verify required columns exist
        required_columns = ['model_name', 'score', 'rank']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(
                f"cleaned_data.csv must contain columns: {required_columns}. "
                f"Found: {list(df.columns)}"
            )
        
        # Load mapping if provided
        mapping: Dict[str, str] = {}
        if mapping_path is not None and mapping_path.exists():
            with open(mapping_path, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
        
        # Perform entity resolution
        # Map benchmark model names to LMArena model IDs
        df['lmarena_id'] = df['model_name'].map(mapping)
        
        # If no mapping file exists (e.g., for LMArena categories), use model_name as lmarena_id
        if not mapping:
            df['lmarena_id'] = df['model_name']
        
        # Filter to Study Universe: only include models that can be mapped and are in Study Universe
        df_filtered = df[df['lmarena_id'].notna() & df['lmarena_id'].isin(self.study_universe)].copy()
        
        if len(df_filtered) == 0:
            # No overlapping models
            return {'scores': {}, 'ranks': {}}
        
        # Extract scores (use original scores from CSV, which are already normalized to 0-100
        # for all benchmarks except Creative Writing v3)
        scores_dict = dict(zip(df_filtered['lmarena_id'], df_filtered['score']))
        
        # Recompute ranks within Study Universe using method='min' for tie-breaking
        # Higher scores get better (lower) ranks
        # Method 'min' means: if two models tie for first place with score 95, both get rank 1,
        # and the next model gets rank 3 (not rank 2)
        df_filtered['recomputed_rank'] = df_filtered['score'].rank(method='min', ascending=False).astype(int)
        
        ranks_dict = dict(zip(df_filtered['lmarena_id'], df_filtered['recomputed_rank']))
        
        return {
            'scores': scores_dict,
            'ranks': ranks_dict
        }

