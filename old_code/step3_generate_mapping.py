"""
第三步：从 review_files 生成 mapping.json（确定性）

输入：data/processed/review_files/{benchmark_id}_review.json
输出：data/processed/cleaned/{benchmark_id}/mapping.json

功能：
1. 读取所有 review_files
2. 提取 selected_lmarena_model 字段（只处理字符串类型，排除 0 和 -1）
3. 生成每个 benchmark 的 mapping.json（已去重）
"""

import json
from pathlib import Path
from typing import Dict


def process_review_file(
    review_file: Path,
    benchmark_id: str,
    cleaned_dir: Path
):
    """处理单个 review_file，生成 mapping.json"""
    print(f"\n处理: {review_file.name}")
    
    # 读取 review_file
    with open(review_file, 'r', encoding='utf-8') as f:
        review_data = json.load(f)
    
    # 提取映射（只处理字符串类型的 selected_lmarena_model）
    mapping = {}
    lmarena_to_benchmark = {}  # 用于检测重复映射
    duplicate_count = 0
    
    for model_name, entry in review_data.items():
        selected_model = entry.get('selected_lmarena_model')
        
        # 只记录字符串类型的 selected_lmarena_model（排除 0 和 -1）
        if isinstance(selected_model, str) and selected_model:
            # 检查是否已经有其他模型映射到同一个 LMArena 模型
            if selected_model in lmarena_to_benchmark:
                # 已经有映射，跳过这个模型（只保留第一个）
                duplicate_count += 1
                continue
            
            # 记录映射
            mapping[model_name] = selected_model
            lmarena_to_benchmark[selected_model] = model_name
    
    if duplicate_count > 0:
        print(f"  补丁: 发现 {duplicate_count} 个重复的 LMArena 映射，已只保留第一个")
    
    # 写入 mapping.json
    output_dir = cleaned_dir / benchmark_id
    output_dir.mkdir(parents=True, exist_ok=True)
    mapping_file = output_dir / 'mapping.json'
    
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    print(f"  生成了 {mapping_file}，包含 {len(mapping)} 个映射")


def main():
    """主函数"""
    base_dir = Path(__file__).parent.parent.parent
    review_files_dir = base_dir / 'data' / 'processed' / 'review_files'
    cleaned_dir = base_dir / 'data' / 'processed' / 'cleaned'
    
    # 查找所有 review_files
    review_files = list(review_files_dir.glob('*_review.json'))
    print(f"找到 {len(review_files)} 个 review 文件")
    
    # 处理每个 review_file
    for review_file in sorted(review_files):
        benchmark_id = review_file.stem.replace('_review', '')
        
        process_review_file(
            review_file,
            benchmark_id,
            cleaned_dir
        )
    
    print("\n完成！")


if __name__ == '__main__':
    main()

