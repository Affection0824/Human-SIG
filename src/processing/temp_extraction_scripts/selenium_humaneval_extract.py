"""
临时提取脚本: selenium/humaneval
从 data/raw/selenium/humaneval/data.csv 提取模型信息
"""

import csv
import json
import sys
from pathlib import Path

# 添加 common_parser 到路径
sys.path.insert(0, str(Path(__file__).parent))
from common_parser import parse_model_name

def extract_models():
    """提取模型信息"""
    base_dir = Path(__file__).parent.parent.parent.parent
    csv_file = base_dir / 'data' / 'raw' / Path('selenium/humaneval/data.csv')
    output_file = base_dir / 'data' / 'processed' / 'model_extraction' / 'selenium_humaneval_models.json'
    
    models = {}
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            model_name = row.get('Model')
            
            # 跳过空值
            if not model_name:
                continue
            
            # 清理模型名称（移除组织名称等）
            model_clean = model_name.strip()
            
            # 跳过空字符串
            if not model_clean:
                continue
            
            # 对于 LMArena，需要过滤 Score >= 1330
            
            # 解析模型名称
            parsed = parse_model_name(model_clean)
            models[model_name] = parsed
    
    # 保存 JSON
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(models, f, indent=2, ensure_ascii=False)
    
    print(f"处理了 {len(models)} 个模型: selenium/humaneval")
    return models

if __name__ == '__main__':
    extract_models()
