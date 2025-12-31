"""
验证审核后的数据是否完整和格式正确
"""

import json
from pathlib import Path
from collections import defaultdict

def validate_complete_data():
    """验证所有审核后的文件是否完整"""
    base_dir = Path(__file__).parent.parent.parent
    reviewed_dir = base_dir / 'data' / 'processed' / 'entity_resolution' / 'reviewed_files'
    
    stats = defaultdict(lambda: {
        'total': 0,
        'has_all_fields': 0,
        'needs_review_true': 0,
        'needs_review_false': 0,
        'selected_model_name': 0,
        'selected_0': 0,
        'selected_minus1': 0,
        'has_none': 0
    })
    
    print("="*60)
    print("验证审核后的数据完整性")
    print("="*60)
    
    all_valid = True
    
    for reviewed_file in reviewed_dir.glob('*_review.json'):
        benchmark_id = reviewed_file.stem.replace('_review', '')
        
        with open(reviewed_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for model_name, entry in data.items():
            stats[benchmark_id]['total'] += 1
            
            # 检查必需字段
            required_fields = ['benchmark_info', 'candidates', 'human_approved', 
                             'selected_lmarena_model', 'needs_review']
            has_all = all(field in entry for field in required_fields)
            
            if has_all:
                stats[benchmark_id]['has_all_fields'] += 1
            else:
                all_valid = False
                print(f"错误: {benchmark_id} - {model_name} 缺少必需字段")
            
            # 检查 selected_lmarena_model 不能是 None
            selected = entry.get('selected_lmarena_model')
            if selected is None:
                all_valid = False
                stats[benchmark_id]['has_none'] += 1
                print(f"错误: {benchmark_id} - {model_name} selected_lmarena_model 是 None")
            elif selected == 0:
                stats[benchmark_id]['selected_0'] += 1
            elif selected == -1:
                stats[benchmark_id]['selected_minus1'] += 1
            elif isinstance(selected, str):
                stats[benchmark_id]['selected_model_name'] += 1
            
            # 检查 needs_review
            needs_review = entry.get('needs_review')
            if needs_review is True:
                stats[benchmark_id]['needs_review_true'] += 1
            elif needs_review is False:
                stats[benchmark_id]['needs_review_false'] += 1
            else:
                all_valid = False
                print(f"错误: {benchmark_id} - {model_name} needs_review 不是布尔值")
    
    # 打印统计
    print(f"\n{'Benchmark':<40} {'总数':<8} {'完整':<8} {'需审核':<8} {'模型名':<8} {'0':<6} {'-1':<6}")
    print("-"*60)
    
    total_all = 0
    total_complete = 0
    total_needs_review = 0
    
    for benchmark_id, stat in sorted(stats.items()):
        print(f"{benchmark_id:<40} {stat['total']:<8} {stat['has_all_fields']:<8} "
              f"{stat['needs_review_true']:<8} {stat['selected_model_name']:<8} "
              f"{stat['selected_0']:<6} {stat['selected_minus1']:<6}")
        total_all += stat['total']
        total_complete += stat['has_all_fields']
        total_needs_review += stat['needs_review_true']
    
    print("-"*60)
    print(f"{'总计':<40} {total_all:<8} {total_complete:<8} {total_needs_review:<8}")
    print("="*60)
    
    if all_valid and total_complete == total_all:
        print("\n所有数据完整且格式正确！")
        print(f"需要人工审核的条目: {total_needs_review} 个 ({total_needs_review/total_all*100:.1f}%)")
    else:
        print("\n发现问题，请检查上述错误信息")
    
    return all_valid and total_complete == total_all

if __name__ == '__main__':
    validate_complete_data()

