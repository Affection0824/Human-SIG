"""
临时提取脚本：LMArena Overall
从 data/raw/lmarena/Overall/data.csv 提取模型信息
只保留 Score >= 1330 的模型
"""

import json
import csv
from pathlib import Path
import sys

# 添加父目录到路径以导入 common_parser
sys.path.insert(0, str(Path(__file__).parent))
from common_parser import parse_model_name

def extract_lmarena_overall():
    """提取 LMArena Overall 模型信息"""
    base_dir = Path(__file__).parent.parent.parent.parent
    csv_file = base_dir / 'data' / 'raw' / 'lmarena' / 'Overall' / 'data.csv'
    output_file = base_dir / 'data' / 'processed' / 'model_extraction' / 'lmarena_models.json'
    
    models = {}
    special_cases = []  # 记录特判情况
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            model_name = row['Model']
            try:
                # 处理 Score 列可能包含 "Preliminary" 的情况
                score_str = row['Score'].replace('Preliminary', '').strip()
                score = float(score_str)
            except (ValueError, KeyError):
                special_cases.append(f"无法解析Score: {row}")
                continue
            
            # 只保留 Score >= 1330 的模型
            if score >= 1330:
                parsed = parse_model_name(model_name)
                
                # 检查解析结果
                if not parsed['family']:
                    special_cases.append(f"无法提取家族: {model_name}")
                
                models[model_name] = parsed
    
    # 保存 JSON
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(models, f, indent=2, ensure_ascii=False)
    
    print(f"处理了 {len(models)} 个 LMArena 模型（Score >= 1330）")
    if special_cases:
        print(f"\n特判情况 ({len(special_cases)} 个):")
        for case in special_cases[:10]:  # 只显示前10个
            print(f"  - {case}")
        if len(special_cases) > 10:
            print(f"  ... 还有 {len(special_cases) - 10} 个")
    
    return models, special_cases

if __name__ == '__main__':
    extract_lmarena_overall()

