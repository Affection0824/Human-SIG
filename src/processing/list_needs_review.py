"""
列出所有需要人工审核的条目（使用 needs_review 字段）
"""

import json
from pathlib import Path

def list_needs_review():
    """列出所有需要人工审核的条目"""
    base_dir = Path(__file__).parent.parent.parent
    reviewed_dir = base_dir / 'data' / 'processed' / 'entity_resolution' / 'reviewed_files'
    
    needs_review_list = []
    
    print("="*60)
    print("需要人工审核的条目（needs_review == true）")
    print("="*60)
    
    for reviewed_file in reviewed_dir.glob('*_review.json'):
        benchmark_id = reviewed_file.stem.replace('_review', '')
        
        with open(reviewed_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for model_name, entry in data.items():
            if entry.get('needs_review', False):
                needs_review_list.append({
                    'benchmark': benchmark_id,
                    'model_name': model_name,
                    'selected': entry.get('selected_lmarena_model'),
                    'candidates_count': len([c for c in entry.get('candidates', []) 
                                           if c.get('lmarena_model') != 'NO_MATCH_FOUND'])
                })
    
    # 按 benchmark 分组
    by_benchmark = {}
    for item in needs_review_list:
        benchmark = item['benchmark']
        if benchmark not in by_benchmark:
            by_benchmark[benchmark] = []
        by_benchmark[benchmark].append(item)
    
    # 打印结果
    total = len(needs_review_list)
    print(f"\n总共需要人工审核: {total} 个条目\n")
    
    for benchmark_id, items in sorted(by_benchmark.items()):
        if items:
            print(f"\n{benchmark_id}: {len(items)} 个需要审核")
            print("-" * 60)
            for item in items[:5]:  # 只显示前5个
                print(f"  Model: {item['model_name']}")
                print(f"    Selected: {item['selected']}")
                print(f"    Valid Candidates: {item['candidates_count']}")
                print()
            if len(items) > 5:
                print(f"  ... 还有 {len(items) - 5} 个条目")
    
    print("\n" + "="*60)
    print("识别方法:")
    print("  在 JSON 文件中查找: \"needs_review\": true")
    print("  或者在代码中过滤: entry.get('needs_review', False) == True")
    print("="*60)
    
    return needs_review_list

if __name__ == '__main__':
    list_needs_review()

