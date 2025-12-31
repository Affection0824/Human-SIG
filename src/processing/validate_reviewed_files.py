"""
验证审核后的文件格式
"""

import json
from pathlib import Path
from collections import defaultdict

def validate_reviewed_files():
    """验证所有审核后的文件"""
    base_dir = Path(__file__).parent.parent.parent
    reviewed_dir = base_dir / 'data' / 'processed' / 'entity_resolution' / 'reviewed_files'
    
    stats = defaultdict(lambda: {
        'total': 0,
        'has_human_approved': 0,
        'has_selected_model': 0,
        'selected_0': 0,
        'selected_model_name': 0,
        'selected_minus1': 0,
        'multi_candidates_auto_selected': 0
    })
    
    print("="*60)
    print("验证审核后的文件")
    print("="*60)
    
    for reviewed_file in reviewed_dir.glob('*_review.json'):
        benchmark_id = reviewed_file.stem.replace('_review', '')
        
        with open(reviewed_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for model_name, entry in data.items():
            stats[benchmark_id]['total'] += 1
            
            # 检查必需字段
            if 'human_approved' in entry:
                stats[benchmark_id]['has_human_approved'] += 1
                if entry['human_approved'] == 1:
                    stats[benchmark_id]['has_selected_model'] += 1
            
            if 'selected_lmarena_model' in entry:
                selected = entry['selected_lmarena_model']
                if selected == 0:
                    stats[benchmark_id]['selected_0'] += 1
                elif selected == -1:
                    stats[benchmark_id]['selected_minus1'] += 1
                elif isinstance(selected, str):
                    stats[benchmark_id]['selected_model_name'] += 1
            
            # 检查多候选自动选择的情况
            candidates = entry.get('candidates', [])
            if len(candidates) > 1:
                valid_candidates = [c for c in candidates if c.get('lmarena_model') != 'NO_MATCH_FOUND']
                if len(valid_candidates) > 1 and entry.get('selected_lmarena_model') not in [0, -1]:
                    stats[benchmark_id]['multi_candidates_auto_selected'] += 1
    
    # 打印统计
    print(f"\n{'Benchmark':<40} {'总数':<8} {'模型名':<8} {'0':<6} {'-1':<6} {'多候选自动':<10}")
    print("-"*60)
    
    for benchmark_id, stat in sorted(stats.items()):
        print(f"{benchmark_id:<40} {stat['total']:<8} {stat['selected_model_name']:<8} "
              f"{stat['selected_0']:<6} {stat['selected_minus1']:<6} {stat['multi_candidates_auto_selected']:<10}")
    
    print("="*60)
    
    # 检查是否有格式问题
    issues = []
    for benchmark_id, stat in stats.items():
        if stat['has_human_approved'] != stat['total']:
            issues.append(f"{benchmark_id}: 缺少 human_approved 字段")
        if stat['selected_model_name'] + stat['selected_0'] + stat['selected_minus1'] != stat['total']:
            issues.append(f"{benchmark_id}: selected_lmarena_model 字段不完整")
    
    if issues:
        print("\n发现问题:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n所有文件格式正确！")
    
    return stats

if __name__ == '__main__':
    validate_reviewed_files()

