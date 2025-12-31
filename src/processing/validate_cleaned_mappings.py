"""
验证 cleaned 目录下的 mapping.json 文件

检查是否有多个 benchmark 模型映射到同一个 LMArena 模型
"""

import json
from pathlib import Path


def validate_mappings():
    """验证所有 mapping.json 文件"""
    base_dir = Path(__file__).parent.parent.parent
    cleaned_dir = base_dir / 'data' / 'processed' / 'cleaned'
    
    total_benchmarks = 0
    total_mappings = 0
    total_unique = 0
    benchmarks_with_duplicates = 0
    
    for benchmark_dir in sorted(cleaned_dir.iterdir()):
        if not benchmark_dir.is_dir():
            continue
        
        mapping_file = benchmark_dir / 'mapping.json'
        if not mapping_file.exists():
            continue
        
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        
        total_benchmarks += 1
        total_mappings += len(mapping)
        
        # 检查重复
        values = list(mapping.values())
        unique_values = set(values)
        total_unique += len(unique_values)
        
        if len(values) != len(unique_values):
            benchmarks_with_duplicates += 1
            duplicates = {}
            for k, v in mapping.items():
                if v not in duplicates:
                    duplicates[v] = []
                duplicates[v].append(k)
            
            duplicates = {v: models for v, models in duplicates.items() if len(models) > 1}
            print(f"\n[WARNING] {benchmark_dir.name}: Found {len(duplicates)} duplicate mappings")
            for lmarena_model, benchmark_models in list(duplicates.items())[:3]:
                try:
                    print(f"   {lmarena_model}: {benchmark_models}")
                except UnicodeEncodeError:
                    print(f"   {lmarena_model.encode('ascii', 'ignore').decode('ascii')}: {len(benchmark_models)} models")
    
    print(f"\nStatistics:")
    print(f"  Total benchmarks: {total_benchmarks}")
    print(f"  Total mappings: {total_mappings}")
    print(f"  Unique LMArena models: {total_unique}")
    print(f"  Benchmarks with duplicates: {benchmarks_with_duplicates}")
    
    if benchmarks_with_duplicates == 0:
        print(f"\n[SUCCESS] All mapping.json files have no duplicate mappings!")
    else:
        print(f"\n[WARNING] {benchmarks_with_duplicates} benchmarks have duplicate mappings")


if __name__ == '__main__':
    validate_mappings()

