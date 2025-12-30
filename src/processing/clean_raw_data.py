"""
Purpose: Cleans raw benchmark data by removing organization prefixes/suffixes from model names.
This addresses issues where scraping concatenated Model and Organization columns (e.g., 'Anthropicclaude...')
or where vendor prefixes are present (e.g. 'anthropic/claude...').
It reads from 'data/raw/' and writes to 'data/cleaned/'.
"""

import os
import pandas as pd
import shutil

# List of known organizations to strip.
# Sorted by length (descending) to ensure greedy matching.
KNOWN_ORGS = [
    "Alibaba Cloud / Qwen Team",
    "Alibaba Cloud",
    "ModelBest",
    "Moonshot AI",
    "MoonshotAI",
    "DeepSeek AI",
    "DeepSeek",
    "Anthropic",
    "Microsoft",
    "Zhipu AI",
    "MiniMax",
    "OpenAI",
    "Google",
    "Xiaomi",
    "Nvidia",
    "NVIDIA",
    "01.AI",
    "Meta",
    "xAI",
    "Mistral",
    "Cohere",
    "Databricks",
    "Salesforce",
    "Snowflake",
    "Tencent",
    "Baidu",
    "Z.ai",
    "StepFun",
    "Amazon",
    "Allen AI",
    "Reka AI",
    "InternLM",
    "OpenChat",
    "HuggingFace",
    "Stability",
    "Azure",
    "RWKV",
    "LMSYS",
    "Upstage AI",
    "MosaicML",
    "Cognitive Computations",
    "Inception AI",
    "Ant Group",
    "Prime Intellect",
    "NexusFlow",
    "Minimax",
    "Stepfun",
]

def clean_model_name(name: str) -> str:
    if not isinstance(name, str):
        return name
    
    name = name.strip()
    
    # 1. Iteratively check and remove prefixes/suffixes
    matched = True
    while matched:
        matched = False
        for org in KNOWN_ORGS:
            # Case-insensitive check for robustness, but replacement should be careful
            # Actually, standardizing on case-insensitive matching is safer for "cleaning".
            
            # Check Suffix
            if name.lower().endswith(org.lower()):
                # Check if it's just the org name
                if name.lower() == org.lower():
                    continue 
                # Strip the suffix (case insensitive slice)
                name = name[:-len(org)].strip()
                matched = True
                break
            
            # Check Prefix (Concatenated or Spaced)
            if name.lower().startswith(org.lower()):
                if name.lower() == org.lower():
                    continue
                name = name[len(org):].strip()
                matched = True
                break
    
    # 2. Handle Slash Prefixes (e.g., "anthropic/claude-3")
    if '/' in name:
        name = name.split('/')[-1].strip()
                
    return name

def process_file(src_path: str, dest_path: str):
    try:
        # Try reading with default engine, fall back if needed
        df = pd.read_csv(src_path)
    except Exception as e:
        print(f"Skipping {src_path}: Read error ({e})")
        return

    # Normalize columns to find model column
    normalized_cols = [str(c).lower().replace(' ', '_').strip() for c in df.columns]
    
    model_col = None
    # Priority check for likely model column names
    candidates = ['model_name', 'model', 'name', 'model_id']
    
    for candidate in candidates:
        if candidate in normalized_cols:
            model_col = df.columns[normalized_cols.index(candidate)]
            break
            
    # Fallback: check first column if it's string-like
    if not model_col:
        if len(df.columns) > 0:
            # Check if first column is object/string type
            if pd.api.types.is_object_dtype(df.iloc[:, 0]) or pd.api.types.is_string_dtype(df.iloc[:, 0]):
                 model_col = df.columns[0]
    
    if model_col:
        original_names = df[model_col].astype(str).tolist()
        cleaned_names = [clean_model_name(n) for n in original_names]
        
        # Verify if changes were made
        # changes = sum(1 for o, c in zip(original_names, cleaned_names) if o != c)
        # if changes > 0:
        #    print(f"Cleaned {changes} names in {os.path.basename(src_path)}")
            
        df[model_col] = cleaned_names
    
    # Ensure dest dir exists
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    df.to_csv(dest_path, index=False)

def main():
    # Detect base directory relative to execution
    if os.path.exists("data/raw"):
        raw_dir = "data/raw"
        cleaned_dir = "data/cleaned"
    else:
        print("Error: Could not find data/raw directory. Make sure you are in Human-SIG root.")
        return

    print(f"Cleaning data from {raw_dir} -> {cleaned_dir}...")
    
    for root, dirs, files in os.walk(raw_dir):
        # Calculate relative path to mirror structure
        rel_path = os.path.relpath(root, raw_dir)
        dest_root = os.path.join(cleaned_dir, rel_path)
        
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_root, file)
            
            # EXCLUSION: Do not copy .txt files
            if file.endswith(".txt"):
                continue

            if file.endswith(".csv"):
                # Process all CSVs (including LMArena) to ensure consistent naming
                process_file(src_file, dest_file)
            else:
                # Copy other non-txt files (e.g. .xlsx if any)
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                shutil.copy2(src_file, dest_file)

    print("Data cleaning complete.")

if __name__ == "__main__":
    main()