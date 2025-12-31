"""
验证生成的审核文件
"""

import json
from pathlib import Path
from collections import defaultdict

def validate_review_files():
    """验证所有生成的审核文件"""
    base_dir = Path(__file__).parent.parent.parent.parent
    review_dir = base_dir / 'data' / 'processed' / 'entity_resolution' / 'review_files_v2'
    
    stats = {}
    
    for review_file in review_dir.glob('*_review.json'):
        benchmark_id = review_file.stem.replace('_review', '')
        
        with open(review_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total_models = len(data)
        matched_models = sum(1 for v in data.values() 
                            if v['candidates'][0].get('lmarena_model') != 'NO_MATCH_FOUND')
        no_match_models = total_models - matched_models
        total_candidates = sum(len(v['candidates']) for v in data.values())
        avg_candidates = total_candidates / total_models if total_models > 0 else 0
        
        stats[benchmark_id] = {
            'total_models': total_models,
            'matched_models': matched_models,
            'no_match_models': no_match_models,
            'total_candidates': total_candidates,
            'avg_candidates': avg_candidates
        }
    
    # 打印统计信息
    print("="*60)
    print("审核文件统计")
    print("="*60)
    print(f"{'Benchmark':<40} {'模型数':<8} {'已匹配':<8} {'未匹配':<8} {'平均候选数':<10}")
    print("-"*60)
    
    total_all_models = 0
    total_matched = 0
    total_no_match = 0
    
    for benchmark_id, stat in sorted(stats.items()):
        print(f"{benchmark_id:<40} {stat['total_models']:<8} {stat['matched_models']:<8} "
              f"{stat['no_match_models']:<8} {stat['avg_candidates']:<10.2f}")
        total_all_models += stat['total_models']
        total_matched += stat['matched_models']
        total_no_match += stat['no_match_models']
    
    print("-"*60)
    print(f"{'总计':<40} {total_all_models:<8} {total_matched:<8} {total_no_match:<8}")
    print("="*60)
    
    return stats

if __name__ == '__main__':
    validate_review_files()

