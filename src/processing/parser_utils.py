"""
Purpose: This module provides the BenchmarkParser class for parsing and normalizing benchmark scores from CSV files.
Methodology:
- Score Normalization: Ensures all scores are on a 0-100 scale. If a max score is <= 1.0, it's assumed to be a ratio and multiplied by 100.
- Ranking Logic: Models are ranked based on their scores where higher scores receive better (lower) ranks (e.g., Rank 1 is the top performer).
- Tie-Breaking: Uses 'method=min' (standard competition ranking) to ensure tied models receive the same rank, supporting rigorous RBO calculation.
- Study Universe: Ranking should be performed strictly on models present in the LMArena Study Universe.
"""

import pandas as pd
import numpy as np

class BenchmarkParser:
    """
    BenchmarkParser handles the ingestion, standardization, and ranking of benchmark results.
    """

    @staticmethod
    def parse_file(file_path: str) -> pd.DataFrame:
        """
        Reads a benchmark CSV file and standardizes it to have 'model_name' and 'score' columns.
        
        Args:
            file_path (str): The path to the raw benchmark data file.
            
        Returns:
            pd.DataFrame: A standardized DataFrame with ['model_name', 'score'].
        """
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return pd.DataFrame(columns=['model_name', 'score'])

        # Normalize column names to lowercase and underscores
        df.columns = [c.lower().replace(' ', '_').strip() for c in df.columns]
        
        # Mapping common model name columns
        if 'model' in df.columns and 'model_name' not in df.columns:
            df.rename(columns={'model': 'model_name'}, inplace=True)
            
        # Mapping common score columns
        if 'score' not in df.columns:
            possible_score_cols = ['acc', 'accuracy', 'pass_rate', 'win_rate', 'elo', 'rating', 'value']
            for col in possible_score_cols:
                if col in df.columns:
                    df.rename(columns={col: 'score'}, inplace=True)
                    break
        
        if 'model_name' not in df.columns or 'score' not in df.columns:
            # Fallback: assume first column is model and second is score if not named
            if len(df.columns) >= 2:
                df.rename(columns={df.columns[0]: 'model_name', df.columns[1]: 'score'}, inplace=True)
            else:
                print(f"Warning: {file_path} missing required columns. Found: {df.columns.tolist()}")
                return pd.DataFrame(columns=['model_name', 'score'])
            
        # Ensure score is numeric
        df['score'] = pd.to_numeric(df['score'], errors='coerce')
        df.dropna(subset=['score'], inplace=True)
        
        # Normalize to 0-100 scale
        if not df.empty and df['score'].max() <= 1.0:
            df['score'] = df['score'] * 100.0
            
        return df[['model_name', 'score']]

    @staticmethod
    def rank_models(df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes ranks for models based on their scores.
        
        Ranking Logic:
        - Higher score = Better rank (Rank 1 is best).
        - Method = 'min': Ties get the same rank (e.g., 1, 1, 3).
        
        Args:
            df (pd.DataFrame): DataFrame containing a 'score' column.
            
        Returns:
            pd.DataFrame: The DataFrame with an added 'rank' column.
        """
        if df.empty:
            df['rank'] = []
            return df
            
        # Higher score gets a lower rank number (1 is best)
        # method='min' ensures ties are handled consistently for RBO
        df['rank'] = df['score'].rank(ascending=False, method='min').astype(int)
        return df
