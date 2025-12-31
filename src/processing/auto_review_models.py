"""
自动审核模型匹配结果

为所有审核文件添加两个新字段：
1. human_approved: 0（初始）或 1（人类认可）
2. selected_lmarena_model: 模型名、0（自动判断无对应）、-1（人类确认无对应）

自动审核逻辑：
- candidates > 1: 根据规则选择最佳匹配
- candidates == 1 且不是 NO_MATCH_FOUND: 直接使用
- candidates == 1 且是 NO_MATCH_FOUND: 设为 0
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import Counter


def normalize_other_info(other_info: Optional[List[str]]) -> set:
    """标准化 other_info，用于比较"""
    if not other_info:
        return set()
    # 转换为小写并去除空白
    return set(item.lower().strip() for item in other_info if item)


def calculate_similarity(info1: Dict, info2: Dict) -> float:
    """
    计算两个模型信息的相似度分数（0-1）
    
    考虑因素：
    1. other_info 的相似度（最重要）
    2. 日期是否匹配（如果都有）
    3. 参数量是否匹配（如果都有）
    4. 子家族是否完全匹配
    """
    score = 0.0
    weights = {
        'other_info': 0.5,
        'date': 0.2,
        'parameters': 0.2,
        'subfamily': 0.1
    }
    
    # 1. other_info 相似度
    other1 = normalize_other_info(info1.get('other_info'))
    other2 = normalize_other_info(info2.get('other_info'))
    
    if other1 or other2:
        if other1 and other2:
            # Jaccard 相似度
            intersection = len(other1 & other2)
            union = len(other1 | other2)
            other_sim = intersection / union if union > 0 else 0.0
        else:
            # 一个为空，一个不为空，相似度较低
            other_sim = 0.1
    else:
        # 都为空，相似度较高
        other_sim = 0.8
    
    score += weights['other_info'] * other_sim
    
    # 2. 日期匹配
    date1 = info1.get('date')
    date2 = info2.get('date')
    if date1 and date2:
        # 如果日期相同，加分
        if date1 == date2:
            score += weights['date'] * 1.0
        else:
            # 日期不同，但都包含相同的年份或月份，给部分分
            if str(date1)[:4] == str(date2)[:4]:
                score += weights['date'] * 0.5
    elif not date1 and not date2:
        # 都没有日期，不扣分也不加分
        pass
    else:
        # 一个有日期，一个没有，稍微扣分
        score += weights['date'] * 0.2
    
    # 3. 参数量匹配
    param1 = info1.get('parameters')
    param2 = info2.get('parameters')
    if param1 and param2:
        if param1 == param2:
            score += weights['parameters'] * 1.0
        else:
            # 参数量不同，扣分
            score += weights['parameters'] * 0.0
    elif not param1 and not param2:
        # 都没有参数量，不扣分也不加分
        pass
    else:
        # 一个有参数量，一个没有，稍微扣分
        score += weights['parameters'] * 0.3
    
    # 4. 子家族匹配
    subfamily1 = info1.get('subfamily')
    subfamily2 = info2.get('subfamily')
    if subfamily1 and subfamily2:
        if subfamily1 == subfamily2:
            score += weights['subfamily'] * 1.0
        else:
            # 子家族不同，但可能有关联（如包含关系）
            if subfamily1 in subfamily2 or subfamily2 in subfamily1:
                score += weights['subfamily'] * 0.5
    elif not subfamily1 and not subfamily2:
        # 都没有子家族，不扣分也不加分
        pass
    else:
        # 一个有子家族，一个没有，稍微扣分
        score += weights['subfamily'] * 0.2
    
    return min(score, 1.0)


def select_best_candidate(benchmark_info: Dict, candidates: List[Dict]) -> Optional[str]:
    """
    从多个候选中选择最佳匹配
    
    返回: 选中的 lmarena_model 名称，如果没有合适的则返回 None
    """
    if not candidates:
        return None
    
    # 过滤掉 NO_MATCH_FOUND
    valid_candidates = [c for c in candidates if c.get('lmarena_model') != 'NO_MATCH_FOUND']
    
    if not valid_candidates:
        return None
    
    # 如果只有一个候选，直接返回
    if len(valid_candidates) == 1:
        return valid_candidates[0].get('lmarena_model')
    
    # 多个候选，计算相似度并选择最佳
    scored_candidates = []
    for candidate in valid_candidates:
        similarity = calculate_similarity(benchmark_info, candidate)
        scored_candidates.append((similarity, candidate))
    
    # 按相似度排序
    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    
    # 选择相似度最高的
    best_similarity, best_candidate = scored_candidates[0]
    
    # 如果最佳相似度太低（< 0.3），可能不是同一个模型
    if best_similarity < 0.3:
        # 检查是否有其他候选的相似度也很高
        if len(scored_candidates) > 1:
            second_similarity = scored_candidates[1][0]
            # 如果前两个相似度很接近，可能无法确定，返回 None 让人类审核
            if abs(best_similarity - second_similarity) < 0.1:
                return None
    
    return best_candidate.get('lmarena_model')


def auto_review_review_file(review_file: Path, output_file: Path):
    """自动审核单个审核文件"""
    with open(review_file, 'r', encoding='utf-8') as f:
        review_data = json.load(f)
    
    reviewed_data = {}
    stats = {
        'total': 0,
        'auto_selected': 0,
        'no_match': 0,
        'needs_review': 0
    }
    
    for model_name, entry in review_data.items():
        stats['total'] += 1
        
        benchmark_info = entry.get('benchmark_info', {})
        candidates = entry.get('candidates', [])
        
        # 初始化两个新字段
        human_approved = 0
        selected_lmarena_model = None
        
        # 自动审核逻辑：始终尝试选择最佳匹配
        valid_candidates = [c for c in candidates if c.get('lmarena_model') != 'NO_MATCH_FOUND']
        
        if not valid_candidates:
            # 没有有效候选，设为 0
            selected_lmarena_model = 0
            stats['no_match'] += 1
            needs_review = False  # 没有候选，不需要人工审核
        elif len(valid_candidates) == 1:
            # 只有一个有效候选，直接使用
            selected_lmarena_model = valid_candidates[0].get('lmarena_model')
            stats['auto_selected'] += 1
            needs_review = False  # 只有一个候选，不需要人工审核
        else:
            # 多个候选，选择最佳匹配（即使需要人工确认，也给出自动选择结果）
            best_match = select_best_candidate(benchmark_info, candidates)
            if best_match:
                selected_lmarena_model = best_match
                stats['auto_selected'] += 1
                # 有多个候选，即使自动选择了，也需要人工确认
                needs_review = True
            else:
                # 无法确定最佳匹配，但仍有候选，选择相似度最高的
                # 计算所有候选的相似度
                scored_candidates = []
                for candidate in valid_candidates:
                    similarity = calculate_similarity(benchmark_info, candidate)
                    scored_candidates.append((similarity, candidate))
                
                # 按相似度排序
                scored_candidates.sort(key=lambda x: x[0], reverse=True)
                
                if scored_candidates:
                    # 选择相似度最高的（即使相似度很低）
                    _, best_candidate = scored_candidates[0]
                    selected_lmarena_model = best_candidate.get('lmarena_model')
                    stats['auto_selected'] += 1
                    needs_review = True  # 相似度低或无法确定，需要人工审核
                else:
                    selected_lmarena_model = 0
                    stats['no_match'] += 1
                    needs_review = False
        
        # 构建新的条目
        reviewed_entry = {
            'benchmark_info': benchmark_info,
            'candidates': candidates,
            'human_approved': human_approved,
            'selected_lmarena_model': selected_lmarena_model,
            'needs_review': needs_review  # 明确标记是否需要人工审核
        }
        
        reviewed_data[model_name] = reviewed_entry
    
    # 保存审核后的文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(reviewed_data, f, indent=2, ensure_ascii=False)
    
    return stats


def main():
    """主函数"""
    base_dir = Path(__file__).parent.parent.parent
    review_dir = base_dir / 'data' / 'processed' / 'entity_resolution' / 'review_files_v2'
    output_dir = base_dir / 'data' / 'processed' / 'entity_resolution' / 'reviewed_files'
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_stats = {}
    
    print("="*60)
    print("开始自动审核...")
    print("="*60)
    
    for review_file in review_dir.glob('*_review.json'):
        benchmark_id = review_file.stem.replace('_review', '')
        output_file = output_dir / review_file.name
        
        print(f"\n处理 {benchmark_id}...")
        stats = auto_review_review_file(review_file, output_file)
        all_stats[benchmark_id] = stats
        
        print(f"  总模型数: {stats['total']}")
        print(f"  自动选择: {stats['auto_selected']}")
        print(f"  无匹配: {stats['no_match']}")
        print(f"  需要人工审核: {stats['needs_review']}")
        print(f"  已保存: {output_file}")
    
    # 打印总体统计
    print("\n" + "="*60)
    print("自动审核完成！")
    print("="*60)
    
    total_all = sum(s['total'] for s in all_stats.values())
    total_auto = sum(s['auto_selected'] for s in all_stats.values())
    total_no_match = sum(s['no_match'] for s in all_stats.values())
    total_review = sum(s['needs_review'] for s in all_stats.values())
    
    print(f"\n总体统计:")
    print(f"  总模型数: {total_all}")
    print(f"  自动选择: {total_auto} ({total_auto/total_all*100:.1f}%)")
    print(f"  无匹配: {total_no_match} ({total_no_match/total_all*100:.1f}%)")
    print(f"  需要人工审核: {total_review} ({total_review/total_all*100:.1f}%)")
    print(f"\n文件位置: {output_dir}")
    print("="*60)


if __name__ == '__main__':
    main()

