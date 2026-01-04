"""
Step 3: Generate mapping.json from review_files (deterministic)

Input: data/processed/review_files/{benchmark_id}.json
Output: data/processed/cleaned/{benchmark_id}/mapping.json

Functions:
1. Read all review_files
2. Extract selected_lmarena_model field (only process string type, exclude 0 and -1)
3. Generate mapping.json for each benchmark (deduplicated)
4. Special handling for artificial_analysis: use unified review file and filter by each benchmark's cleaned_data.csv
"""

import json
import csv
from pathlib import Path
from typing import Dict, Set


def load_benchmark_models(cleaned_csv_path: Path) -> Set[str]:
    """Load model names from cleaned_data.csv"""
    models = set()
    if not cleaned_csv_path.exists():
        return models
    
    with open(cleaned_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            models.add(row['model_name'])
    return models


def process_review_file(
    review_file: Path,
    benchmark_id: str,
    cleaned_dir: Path,
    base_dir: Path
):
    """Process a single review_file and generate mapping.json"""
    print(f"\nProcessing: {review_file.name}")
    
    # Read review_file
    with open(review_file, 'r', encoding='utf-8') as f:
        review_data = json.load(f)
    
    # For non-artificial_analysis benchmarks, no filtering needed
    # (artificial_analysis benchmarks are handled separately in main())
    filter_models = None
    
    # Extract mappings (only process string type selected_lmarena_model)
    mapping = {}
    lmarena_to_benchmark = {}  # Used to detect duplicate mappings
    duplicate_count = 0
    
    for model_name, entry in review_data.items():
        # If filtering is needed, only include models in the benchmark's cleaned_data.csv
        if filter_models is not None and model_name not in filter_models:
            continue
        
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
    raw_dir = base_dir / 'data' / 'raw'
    artificial_analysis_dir = raw_dir / 'artificial_analysis'
    
    # Find all review_files (exclude artificial_analysis.json which is handled separately)
    review_files = [f for f in review_files_dir.glob('*.json') if f.name != 'artificial_analysis.json']
    print(f"Found {len(review_files)} review files")
    
    # Check if artificial_analysis.json exists
    artificial_analysis_review = review_files_dir / 'artificial_analysis.json'
    
    if artificial_analysis_review.exists():
        print(f"\n{'=' * 60}")
        print("Processing artificial_analysis unified review file...")
        
        # Read the unified review file
        with open(artificial_analysis_review, 'r', encoding='utf-8') as f:
            unified_review_data = json.load(f)
        
        # Find all artificial_analysis benchmarks
        artificial_analysis_benchmarks = []
        if artificial_analysis_dir.exists():
            for benchmark_dir in artificial_analysis_dir.iterdir():
                if benchmark_dir.is_dir() and (benchmark_dir / 'data.csv').exists():
                    benchmark_id = benchmark_dir.name
                    artificial_analysis_benchmarks.append(benchmark_id)
        
        print(f"  Found {len(artificial_analysis_benchmarks)} artificial_analysis benchmarks")
        
        # Process each artificial_analysis benchmark separately
        for benchmark_id in sorted(artificial_analysis_benchmarks):
            print(f"\n  Processing {benchmark_id}...")
            
            # Load models from this benchmark's cleaned_data.csv
            cleaned_csv_path = cleaned_dir / benchmark_id / 'cleaned_data.csv'
            filter_models = load_benchmark_models(cleaned_csv_path)
            
            if not filter_models:
                print(f"    Warning: No models found in {cleaned_csv_path}")
                continue
            
            print(f"    Filtering by {benchmark_id} cleaned_data.csv: {len(filter_models)} models")
            
            # Extract mappings for this benchmark
            mapping = {}
            lmarena_to_benchmark = {}
            duplicate_count = 0
            
            for model_name, entry in unified_review_data.items():
                # Only include models in this benchmark's cleaned_data.csv
                if model_name not in filter_models:
                    continue
                
                selected_model = entry.get('selected_lmarena_model')
                
                # Only record string type selected_lmarena_model (exclude 0 and -1)
                if isinstance(selected_model, str) and selected_model:
                    # Check if another model already maps to the same LMArena model
                    if selected_model in lmarena_to_benchmark:
                        duplicate_count += 1
                        continue
                    
                    # Record mapping
                    mapping[model_name] = selected_model
                    lmarena_to_benchmark[selected_model] = model_name
            
            if duplicate_count > 0:
                print(f"    Patch: Found {duplicate_count} duplicate LMArena mappings, kept only the first one")
            
            # Write mapping.json for this benchmark
            output_dir = cleaned_dir / benchmark_id
            output_dir.mkdir(parents=True, exist_ok=True)
            mapping_file = output_dir / 'mapping.json'
            
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(mapping, f, ensure_ascii=False, indent=2)
            
            print(f"    Generated {mapping_file}, containing {len(mapping)} mappings")
        
        print(f"{'=' * 60}")
    
    # Process other review_files normally
    for review_file in sorted(review_files):
        benchmark_id = review_file.stem  # File name without extension is the benchmark_id
        
        # Skip artificial_analysis.json (already processed above)
        if benchmark_id == 'artificial_analysis':
            continue
        
        # Skip individual artificial_analysis benchmark review files
        # (they are already processed via unified review file above)
        if artificial_analysis_dir.exists() and (artificial_analysis_dir / benchmark_id / 'data.csv').exists():
            continue
        
        process_review_file(
            review_file,
            benchmark_id,
            cleaned_dir,
            base_dir
        )
    
    print("\nCompleted!")


if __name__ == '__main__':
    main()

