"""
Step 1: Generate cleaned_data.csv from raw data (deterministic)

Input: data/raw/*/data.csv
Output: data/processed/cleaned/{benchmark_id}/cleaned_data.csv

Functions:
1. Extract model names and scores from raw CSV files
2. Calculate ranks (ties share the same rank)
3. Generate standardized cleaned_data.csv files

Note: Only generates cleaned_data.csv, does not generate mapping.json
"""

import json
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd


# ============================================================================
# Utility Functions: Model Name Cleaning
# ============================================================================

# List of company name suffixes to remove in selenium benchmarks
# Note: Sorted by length in descending order to match longer suffixes first (e.g., "NewZhipu AI" before "Zhipu AI")
SELENIUM_COMPANY_SUFFIXES = [
    'Alibaba Cloud / Qwen Team',
    'NewZhipu AI',
    'NewMiniMax',
    'Moonshot AI',
    'Mistral AI',
    'Zhipu AI',
    'DeepSeek',
    'Xiaomi',
    'NVIDIA',
    'OpenAI',
    'Anthropic',
    'Google',
    'MiniMax',
    'Amazon',
    'xAI',
    'Meta',
    'IBM',
]


def clean_model_name(model_name: str, benchmark_id: str) -> str:
    """
    Clean model name by removing company name suffixes and other irrelevant information
    
    For selenium benchmarks, remove company name suffixes from the end of model names
    """
    cleaned = model_name.strip()
    
    # Only process selenium benchmarks
    if benchmark_id.startswith('selenium_'):
        # Remove company name suffixes (may be directly connected or have a space before)
        for company in SELENIUM_COMPANY_SUFFIXES:
            # Try directly connected format (e.g., "GPT-5.2 ProOpenAI")
            if cleaned.endswith(company):
                cleaned = cleaned[:-len(company)]
            # Try space-separated format
            elif cleaned.endswith(f' {company}'):
                cleaned = cleaned[:-len(f' {company}')]
        
        # Clean leading and trailing spaces again
        cleaned = cleaned.strip()
    
    return cleaned


def handle_duplicate_model_names(model_data: List[Dict]) -> List[Dict]:
    """
    Handle duplicate model names by adding (2), (3) suffixes to duplicate names
    
    Ensures that model names in cleaned_data have no duplicates
    """
    # Count occurrences of each model name
    name_count = {}
    for item in model_data:
        name = item['model_name']
        name_count[name] = name_count.get(name, 0) + 1
    
    # If there are duplicates, add suffixes to subsequent occurrences
    if any(count > 1 for count in name_count.values()):
        name_index = {}
        result = []
        for item in model_data:
            name = item['model_name']
            if name_count[name] > 1:
                # Duplicate found, need to add suffix
                if name not in name_index:
                    name_index[name] = 1
                else:
                    name_index[name] += 1
                    # Add (2), (3) suffixes to second and subsequent occurrences
                    item = item.copy()
                    item['model_name'] = f"{name}({name_index[name]})"
            result.append(item)
        return result
    
    return model_data


# ============================================================================
# Utility Functions: Score Extraction and Column Identification
# ============================================================================

def extract_score_from_value(value: str) -> Optional[float]:
    """
    Extract numeric value from score, ignoring ± error portion
    
    Supported formats:
    - "1490" -> 1490.0
    - "1490 ±6" -> 1490.0
    - "71%" -> 71.0
    - "0.945" -> 0.945
    - "40.7% ±2.9%" -> 40.7
    """
    if pd.isna(value) or value == '':
        return None
    
    # Convert to string
    value_str = str(value).strip()
    
    # Remove ± and everything after it
    value_str = re.sub(r'±.*', '', value_str).strip()
    
    # Remove percentage sign
    if '%' in value_str:
        value_str = value_str.replace('%', '')
        try:
            return float(value_str)
        except ValueError:
            return None
    
    # Try to convert directly to float
    try:
        return float(value_str)
    except ValueError:
        return None


def find_model_column(df) -> Optional[str]:
    """
    Find the model name column
    
    Automatically identifies common model column names: Model, model, Model Name, model_name, AI System, name, Agent
    If not found, returns the first column
    """
    columns = df.columns.tolist()
    
    # Common model column names
    possible_names = ['Model', 'model', 'Model Name', 'model_name', 'AI System', 'name', 'Agent']
    
    for name in possible_names:
        if name in columns:
            return name
    
    # If not found, return the first column
    if len(columns) > 0:
        return columns[0]
    
    return None


def find_score_column(df, benchmark_path: Path) -> Optional[Tuple[str, str]]:
    """
    Find the score column based on benchmark path and DataFrame structure
    
    Returns: (column_name, extraction_method) or None
    Extraction method: 'direct' means use directly, 'percentage' means percentage format
    """
    columns = df.columns.tolist()
    benchmark_str = str(benchmark_path).lower()
    
    # LMArena: Score column
    if 'lmarena' in benchmark_str:
        if 'Score' in columns:
            return ('Score', 'direct')
        elif 'score' in columns:
            return ('score', 'direct')
    
    # Artificial Analysis: Find columns containing percentage
    if 'artificial_analysis' in benchmark_str:
        for col in columns:
            if len(df) > 0:
                sample_value = str(df[col].iloc[0])
                if '%' in sample_value:
                    return (col, 'percentage')
        for col in columns:
            if 'score' in col.lower() or 'result' in col.lower():
                return (col, 'direct')
    
    # FrontierMath: score_value column
    if 'frontiermath' in benchmark_str:
        if 'score_value' in columns:
            return ('score_value', 'percentage')
        elif 'score' in columns:
            return ('score', 'percentage')
    
    # Manual Direct: Special handling
    if 'manual_direct' in benchmark_str:
        if 'facts' in benchmark_str:
            if 'Numerical_Result' in columns:
                return ('Numerical_Result', 'direct')
        elif 'writingbench' in benchmark_str:
            if 'Overall' in columns:
                return ('Overall', 'direct')
    
    # Pandas Read HTML: Special handling
    if 'pandas_read_html' in benchmark_str:
        if 'aider_polyglot' in benchmark_str:
            if 'Percent correct' in columns:
                return ('Percent correct', 'percentage')
        elif 'terminal_bench_v20' in benchmark_str:
            if 'Accuracy' in columns:
                return ('Accuracy', 'percentage')
    
    # Selenium: Special handling
    if 'selenium' in benchmark_str:
        if 'arc-agi-2' in benchmark_str.lower() or 'arc_agi_2' in benchmark_str.lower():
            if 'ARC-AGI-2' in columns:
                return ('ARC-AGI-2', 'direct')
        elif 'creative_writing_v3' in benchmark_str.lower():
            if 'Elo Score' in columns:
                return ('Elo Score', 'direct')
        elif 'swe-bench_bash_only' in benchmark_str.lower() or 'swe_bench_bash_only' in benchmark_str.lower():
            if '% Resolved' in columns:
                return ('% Resolved', 'percentage')
        elif 'Score' in columns:
            return ('Score', 'direct')
        elif 'score' in columns:
            return ('score', 'direct')
    
    # VALS AI: accuracy column
    if 'vals_ai' in benchmark_str:
        if 'accuracy' in columns:
            return ('accuracy', 'percentage')
    
    # Generic: Find columns containing score, result, accuracy, correct
    for col in columns:
        col_lower = col.lower()
        if 'score' in col_lower or 'result' in col_lower or 'accuracy' in col_lower or 'correct' in col_lower:
            return (col, 'direct')
    
    return None


def calculate_ranks(scores: List[float]) -> List[int]:
    """
    Calculate ranks with ties sharing the same rank
    
    Example: [99, 98, 98, 97] -> [1, 2, 2, 4]
    
    Algorithm:
    1. Sort scores in descending order
    2. Same scores get the same rank
    3. Next rank skips the number of tied entries
    """
    if not scores:
        return []
    
    # Create list of (index, score) tuples
    indexed_scores = [(i, score) for i, score in enumerate(scores)]
    
    # Sort by score in descending order
    indexed_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Calculate ranks
    ranks = [0] * len(scores)
    current_rank = 1
    
    i = 0
    while i < len(indexed_scores):
        score = indexed_scores[i][1]
        # Find all indices with the same score
        same_score_indices = []
        j = i
        while j < len(indexed_scores) and indexed_scores[j][1] == score:
            same_score_indices.append(indexed_scores[j][0])
            j += 1
        
        # Assign rank
        for idx in same_score_indices:
            ranks[idx] = current_rank
        
        # Next rank
        current_rank += len(same_score_indices)
        i = j
    
    return ranks


# ============================================================================
# Utility Functions: Path Processing
# ============================================================================

def get_benchmark_id_from_path(raw_csv_path: Path, base_dir: Path) -> str:
    """
    Generate benchmark ID from raw CSV path
    
    Uses folder name directly, without source prefix
    
    Examples:
    - data/raw/lmarena/LMArena-Overall/data.csv -> LMArena-Overall
    - data/raw/artificial_analysis/AA-LCR/data.csv -> AA-LCR
    - data/raw/selenium/HumanEval/data.csv -> HumanEval
    """
    # Get path relative to base_dir/data/raw
    try:
        relative_path = raw_csv_path.relative_to(base_dir / 'data' / 'raw')
    except ValueError:
        # If not in expected path, use filename
        return raw_csv_path.stem
    
    # Get all parent directories (excluding data.csv)
    parts = list(relative_path.parts[:-1])  # Remove data.csv
    
    # Use the last directory name directly as benchmark_id (without source prefix)
    benchmark_id = parts[-1] if parts else raw_csv_path.stem
    
    return benchmark_id




# ============================================================================
# Main Processing Functions
# ============================================================================

def process_benchmark(
    raw_csv_path: Path,
    base_dir: Path,
    cleaned_dir: Path
):
    """
    Process a single benchmark and generate cleaned_data.csv
    
    Steps:
    1. Read raw CSV file (try multiple encodings)
    2. Identify model name column and score column
    3. Extract model names and scores
    4. Handle duplicate model names (add suffixes)
    5. Calculate ranks (ties share the same rank)
    6. Write cleaned_data.csv
    """
    print(f"\nProcessing: {raw_csv_path}")
    
    # Get benchmark_id
    benchmark_id = get_benchmark_id_from_path(raw_csv_path, base_dir)
    print(f"  Benchmark ID: {benchmark_id}")
    
    # Create output directory
    output_dir = cleaned_dir / benchmark_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Read raw CSV (try multiple encodings)
    df = None
    for encoding in ['utf-8', 'gbk', 'latin-1', 'cp1252']:
        try:
            df = pd.read_csv(raw_csv_path, encoding=encoding)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            print(f"  Error: Unable to read CSV file: {e}")
            return
    
    if df is None:
        print(f"  Error: Unable to read CSV file with any encoding")
        return
    
    # Find model column and score column
    model_col = find_model_column(df)
    score_info = find_score_column(df, raw_csv_path)
    
    if model_col is None:
        print(f"  Warning: Model name column not found, available columns: {df.columns.tolist()}")
        return
    
    if score_info is None:
        print(f"  Warning: Score column not found, available columns: {df.columns.tolist()}")
        return
    
    score_col, score_method = score_info
    try:
        print(f"  Using model column: {model_col}, score column: {score_col}")
    except UnicodeEncodeError:
        print(f"  Using model column: {model_col}, score column: {score_col.encode('ascii', 'ignore').decode('ascii')}")
    
    # Extract data
    model_data = []
    
    # For manual_direct_facts benchmark, only extract rows where Task_Name == Average
    if benchmark_id == 'manual_direct_facts':
        # Find Task_Name column
        task_name_col = None
        for col in df.columns:
            if 'task_name' in col.lower() or col == 'Task_Name':
                task_name_col = col
                break
        
        if task_name_col is not None:
            # Filter to keep only rows where Task_Name == Average
            original_count = len(df)
            df = df[df[task_name_col].astype(str).str.strip() == 'Average'].copy()
            filtered_count = len(df)
            print(f"  Filtered Task_Name: from {original_count} rows to {filtered_count} rows (keeping only Average)")
        else:
            print(f"  Warning: Task_Name column not found, processing all rows")
    
    for _, row in df.iterrows():
        model_name_raw = str(row[model_col]).strip()
        
        # Clean model name (remove company name suffixes, etc.)
        model_name_cleaned = clean_model_name(model_name_raw, benchmark_id)
        
        # Extract score
        score_value = row[score_col]
        score = extract_score_from_value(score_value)
        
        if score is None:
            continue
        
        model_data.append({
            'model_name': model_name_cleaned,
            'score': score
        })
    
    if not model_data:
        print(f"  Warning: No matching model data found")
        return
    
    # Handle duplicate model names (before sorting to preserve original order)
    model_data = handle_duplicate_model_names(model_data)
    
    # Sort by score and calculate ranks
    model_data.sort(key=lambda x: x['score'], reverse=True)
    scores = [item['score'] for item in model_data]
    ranks = calculate_ranks(scores)
    
    # Add ranks
    for i, item in enumerate(model_data):
        item['rank'] = ranks[i]
    
    # Write cleaned_data.csv
    cleaned_csv_path = output_dir / 'cleaned_data.csv'
    with open(cleaned_csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['model_name', 'score', 'rank'])
        writer.writeheader()
        writer.writerows(model_data)
    
    print(f"  Generated {cleaned_csv_path}, containing {len(model_data)} models")


def main():
    """
    Main function
    
    Iterate through all raw data CSV files and generate cleaned_data.csv for each benchmark
    """
    base_dir = Path(__file__).parent.parent.parent
    raw_dir = base_dir / 'data' / 'raw'
    cleaned_dir = base_dir / 'data' / 'processed' / 'cleaned'
    
    # Create cleaned directory
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all data.csv files
    csv_files = list(raw_dir.rglob('data.csv'))
    print(f"Found {len(csv_files)} data.csv files")
    
    # Process each benchmark
    for csv_file in sorted(csv_files):
        process_benchmark(
            csv_file,
            base_dir,
            cleaned_dir
        )
    
    print("\nCompleted!")


if __name__ == '__main__':
    main()
