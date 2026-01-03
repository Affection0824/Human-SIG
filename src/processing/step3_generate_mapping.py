"""
Step 3: Generate mapping.json from review_files (deterministic)

Input: data/processed/review_files/{benchmark_id}_review.json
Output: data/processed/cleaned/{benchmark_id}/mapping.json

Functions:
1. Read all review_files
2. Extract selected_lmarena_model field (only process string type, exclude 0 and -1)
3. Generate mapping.json for each benchmark (deduplicated)
"""

import json
from pathlib import Path
from typing import Dict


def process_review_file(
    review_file: Path,
    benchmark_id: str,
    cleaned_dir: Path
):
    """Process a single review_file and generate mapping.json"""
    print(f"\nProcessing: {review_file.name}")
    
    # Read review_file
    with open(review_file, 'r', encoding='utf-8') as f:
        review_data = json.load(f)
    
    # Extract mappings (only process string type selected_lmarena_model)
    mapping = {}
    lmarena_to_benchmark = {}  # Used to detect duplicate mappings
    duplicate_count = 0
    
    for model_name, entry in review_data.items():
        selected_model = entry.get('selected_lmarena_model')
        
        # Only record string type selected_lmarena_model (exclude 0 and -1)
        if isinstance(selected_model, str) and selected_model:
            # Check if another model already maps to the same LMArena model
            if selected_model in lmarena_to_benchmark:
                # Mapping already exists, skip this model (keep only the first one)
                duplicate_count += 1
                continue
            
            # Record mapping
            mapping[model_name] = selected_model
            lmarena_to_benchmark[selected_model] = model_name
    
    if duplicate_count > 0:
        print(f"  Patch: Found {duplicate_count} duplicate LMArena mappings, kept only the first one")
    
    # Write mapping.json
    output_dir = cleaned_dir / benchmark_id
    output_dir.mkdir(parents=True, exist_ok=True)
    mapping_file = output_dir / 'mapping.json'
    
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    print(f"  Generated {mapping_file}, containing {len(mapping)} mappings")


def main():
    """Main function"""
    base_dir = Path(__file__).parent.parent.parent
    review_files_dir = base_dir / 'data' / 'processed' / 'review_files'
    cleaned_dir = base_dir / 'data' / 'processed' / 'cleaned'
    
    # Find all review_files
    review_files = list(review_files_dir.glob('*_review.json'))
    print(f"Found {len(review_files)} review files")
    
    # Process each review_file
    for review_file in sorted(review_files):
        benchmark_id = review_file.stem.replace('_review', '')
        
        process_review_file(
            review_file,
            benchmark_id,
            cleaned_dir
        )
    
    print("\nCompleted!")


if __name__ == '__main__':
    main()

