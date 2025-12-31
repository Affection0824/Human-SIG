"""
查找需要人工审核的条目
"""

import json
from pathlib import Path
from collections import defaultdict

def find_needs_review():
    """查找所有需要人工审核的条目"""
    base_dir = Path(__file__).parent.parent.parent
    reviewed_dir = base_dir / 'data' / 'processed' / 'entity_resolution' / 'reviewed_files'
    
    needs_review = defaultdict(list)
    
    print("="*60)
    print("查找需要人工审核的条目")
    print("="*60)
    
    for reviewed_file in reviewed_dir.glob('*_review.json'):
        benchmark_id = reviewed_file.stem.replace('_review', '')
        
        with open(reviewed_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for model_name, entry in data.items():
            candidates = entry.get('candidates', [])
            selected = entry.get('selected_lmarena_model')
            human_approved = entry.get('human_approved', 0)
            
            # 需要人工审核的情况：
            # 1. human_approved == 0 且 selected_lmarena_model == 0 且有多个有效候选
            # 2. human_approved == 0 且有多个候选但自动选择了其中一个（需要确认是否正确）
            
            valid_candidates = [c for c in candidates if c.get('lmarena_model') != 'NO_MATCH_FOUND']
            
            if human_approved == 0:
                if len(valid_candidates) > 1:
                    # 多个候选，需要人工确认
                    needs_review[benchmark_id].append({
                        'model_name': model_name,
                        'selected': selected,
                        'candidates_count': len(valid_candidates),
                        'reason': 'multiple_candidates'
                    })
                elif len(valid_candidates) == 1 and selected == 0:
                    # 只有一个候选但设为0，可能是无法确定，需要人工审核
                    needs_review[benchmark_id].append({
                        'model_name': model_name,
                        'selected': selected,
                        'candidates_count': len(valid_candidates),
                        'reason': 'single_candidate_but_0'
                    })
    
    # 打印结果
    total_needs_review = sum(len(entries) for entries in needs_review.values())
    print(f"\n总共需要人工审核: {total_needs_review} 个条目\n")
    
    for benchmark_id, entries in sorted(needs_review.items()):
        if entries:
            print(f"\n{benchmark_id}: {len(entries)} 个需要审核")
            print("-" * 60)
            for entry in entries[:5]:  # 只显示前5个
                print(f"  Model: {entry['model_name']}")
                print(f"    Selected: {entry['selected']}")
                print(f"    Candidates: {entry['candidates_count']}")
                print(f"    Reason: {entry['reason']}")
                print()
            if len(entries) > 5:
                print(f"  ... 还有 {len(entries) - 5} 个条目")
    
    print("\n" + "="*60)
    print("提示: 需要人工审核的条目特征:")
    print("  - human_approved == 0")
    print("  - selected_lmarena_model == 0 且有多个候选")
    print("  - 或者有多个候选但自动选择了其中一个（需要确认）")
    print("="*60)
    
    return needs_review

if __name__ == '__main__':
    find_needs_review()

