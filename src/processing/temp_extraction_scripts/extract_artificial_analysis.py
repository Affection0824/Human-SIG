"""
临时提取脚本：Artificial Analysis
从 data/raw/artificial_analysis/{benchmark}/data.csv 提取模型信息
所有10个benchmark共享同一个模型列表（从第一个benchmark提取即可）
"""

import json
import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from common_parser import parse_model_name

def extract_artificial_analysis():
    """提取 Artificial Analysis 模型信息（从第一个benchmark）"""
    base_dir = Path(__file__).parent.parent.parent.parent
    csv_file = base_dir / 'data' / 'raw' / 'artificial_analysis' / 'aa_lcr' / 'data.csv'
    output_file = base_dir / 'data' / 'processed' / 'model_extraction' / 'artificial_analysis_models.json'
    
    models = {}
    special_cases = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            model_name = row['Model']
            
            parsed = parse_model_name(model_name)
            
            # 检查解析结果
            if not parsed['family']:
                special_cases.append(f"无法提取家族: {model_name}")
            
            models[model_name] = parsed
    
    # 保存 JSON
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(models, f, indent=2, ensure_ascii=False)
    
    print(f"处理了 {len(models)} 个 Artificial Analysis 模型")
    if special_cases:
        print(f"\n特判情况 ({len(special_cases)} 个):")
        for case in special_cases[:10]:
            print(f"  - {case}")
        if len(special_cases) > 10:
            print(f"  ... 还有 {len(special_cases) - 10} 个")
    
    return models, special_cases

if __name__ == '__main__':
    extract_artificial_analysis()

