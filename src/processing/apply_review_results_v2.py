"""
应用审核结果脚本（版本2 - JSON格式）

读取JSON格式的审核文件，提取每个benchmark模型的最终映射，更新mapping.json。
"""

import json
from pathlib import Path
from typing import Dict


def load_review_file_json(review_file: Path) -> Dict[str, str]:
    """
    加载JSON格式的审核文件，提取每个benchmark模型的最终映射
    
    返回: {benchmark_model: lmarena_model} 字典
    注意：每个模型应该只保留一个候选（审核后candidates数组应该只有一个元素）
    """
    mappings = {}
    
    if not review_file.exists():
        print(f"  警告: 审核文件不存在: {review_file}")
        return mappings
    
    with open(review_file, 'r', encoding='utf-8') as f:
        review_data = json.load(f)
    
    for benchmark_model, model_data in review_data.items():
        candidates = model_data.get('candidates', [])
        
        # 跳过未匹配的模型
        if not candidates or candidates[0].get('lmarena_model') == 'NO_MATCH_FOUND':
            continue
        
        # 如果审核正确，应该只有一个候选
        if len(candidates) > 1:
            print(f"  警告: {benchmark_model} 有 {len(candidates)} 个候选，只保留第一个")
        
        # 取第一个候选（应该是审核后保留的唯一候选）
        lmarena_model = candidates[0].get('lmarena_model')
        if lmarena_model and lmarena_model != 'NO_MATCH_FOUND':
            mappings[benchmark_model] = lmarena_model
    
    return mappings


def apply_review_results(
    review_files_dir: Path,
    mapping_json_path: Path,
    artificial_analysis_benchmarks: list
):
    """
    应用所有审核结果到映射表
    """
    # 加载现有映射表
    if mapping_json_path.exists():
        with open(mapping_json_path, 'r', encoding='utf-8') as f:
            existing_mappings = json.load(f)
    else:
        existing_mappings = {}
    
    print(f"现有映射数量: {len(existing_mappings)}")
    
    # 处理所有审核文件
    new_mappings = {}
    total_benchmarks = 0
    
    # 特殊处理：artificial_analysis
    artificial_analysis_file = review_files_dir / 'artificial_analysis_review.json'
    if artificial_analysis_file.exists():
        print(f"\n处理 artificial_analysis 审核文件...")
        aa_mappings = load_review_file_json(artificial_analysis_file)
        print(f"  找到 {len(aa_mappings)} 个映射")
        
        # 应用到所有 artificial_analysis benchmark
        for benchmark_name in artificial_analysis_benchmarks:
            for benchmark_model, lmarena_model in aa_mappings.items():
                key = benchmark_model  # 使用模型名称作为key
                new_mappings[key] = lmarena_model
                total_benchmarks += 1
        
        print(f"  已应用到 {len(artificial_analysis_benchmarks)} 个benchmark")
    
    # 处理其他benchmark
    for review_file in review_files_dir.glob('*_review.json'):
        # 跳过 artificial_analysis（已经处理）
        if review_file.name == 'artificial_analysis_review.json':
            continue
        
        # 提取benchmark_id（从文件名）
        benchmark_id = review_file.stem.replace('_review', '').replace('_', '/')
        
        print(f"\n处理 {benchmark_id} 审核文件...")
        mappings = load_review_file_json(review_file)
        print(f"  找到 {len(mappings)} 个映射")
        
        for benchmark_model, lmarena_model in mappings.items():
            key = benchmark_model
            new_mappings[key] = lmarena_model
            total_benchmarks += 1
    
    # 合并映射（新映射覆盖旧映射）
    existing_mappings.update(new_mappings)
    
    # 保存更新后的映射表
    with open(mapping_json_path, 'w', encoding='utf-8') as f:
        json.dump(existing_mappings, f, indent=2, ensure_ascii=False)
    
    print(f"\n" + "="*60)
    print(f"映射表更新完成！")
    print(f"  新增映射: {len(new_mappings)} 个")
    print(f"  总映射数: {len(existing_mappings)} 个")
    print(f"  映射表位置: {mapping_json_path}")
    print("="*60)


def main():
    """主函数"""
    base_dir = Path(__file__).parent.parent.parent
    review_files_dir = base_dir / 'data' / 'processed' / 'entity_resolution' / 'review_files_v2'
    mapping_json_path = base_dir / 'config' / 'mapping.json'
    
    artificial_analysis_benchmarks = [
        'aa_lcr', 'aime_2025', 'gpqa_diamond', 'humanitys_last_exam',
        'ifbench', 'live_code_bench', 'mmlu_pro', 'scicode',
        'tau_bench_telecom', 'terminal_bench_hard'
    ]
    
    apply_review_results(
        review_files_dir=review_files_dir,
        mapping_json_path=mapping_json_path,
        artificial_analysis_benchmarks=artificial_analysis_benchmarks
    )


if __name__ == '__main__':
    main()
