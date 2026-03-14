import pandas as pd
import numpy as np

def inspect_data():
    try:
        df = pd.read_csv('data/processed/master_table/master_correlation_matrix.csv')
        
        # Check column names
        cols = [c for c in df.columns if 'Creative' in c]
        print(f"Columns related to Creative Writing: {cols}")
        
        if 'Creative_Writing_v3_score' in df.columns:
            cw = df[['elo_overall', 'Creative_Writing_v3_score']].dropna()
            print("\nDescriptive Statistics for Creative_Writing_v3_score:")
            print(cw.describe())
            print("\nFirst 10 rows:")
            print(cw.head(10))
            
            # Check for potential issues
            print("\nValue Counts:")
            print(cw['Creative_Writing_v3_score'].value_counts().head())
            
            min_score = cw['Creative_Writing_v3_score'].min()
            max_score = cw['Creative_Writing_v3_score'].max()
            print(f"\nRange: [{min_score}, {max_score}]")
            
        else:
            print("Creative_Writing_v3_score column not found!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_data()
