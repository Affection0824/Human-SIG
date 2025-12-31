"""
过滤LMArena模型，只保留Score >= 1330的模型
"""

import json
import pandas as pd
from pathlib import Path


def filter_lmarena_models():
    """过滤LMArena模型，只保留Score >= 1330的模型"""
    base_dir = Path(__file__).parent.parent.parent
    
    # 读取LMArena原始数据
    lmarena_csv = base_dir / 'data' / 'cleaned' / 'lmarena' / 'overall' / 'data.csv'
    df = pd.read_csv(lmarena_csv)
    
    # 处理Score列：移除"Preliminary"等后缀，转换为数值类型
    def extract_score(score_str):
        """从Score字符串中提取数值（如'1443Preliminary' -> 1443）"""
        if pd.isna(score_str):
            return None
        score_str = str(score_str)
        # 移除"Preliminary"等后缀
        score_str = score_str.replace('Preliminary', '').replace('preliminary', '').strip()
        # 提取数字部分
        try:
            return float(score_str)
        except (ValueError, TypeError):
            return None
    
    df['Score_numeric'] = df['Score'].apply(extract_score)
    
    # 过滤Score >= 1330的模型
    filtered_df = df[df['Score_numeric'] >= 1330]
    valid_models = set(filtered_df['Model'].dropna().unique())
    
    print(f"LMArena原始数据:")
    print(f"  总模型数: {len(df)}")
    print(f"  Score >= 1330的模型数: {len(valid_models)}")
    
    # 读取现有的lmarena_models.json
    lmarena_models_file = base_dir / 'data' / 'processed' / 'model_extraction' / 'lmarena_models.json'
    
    if not lmarena_models_file.exists():
        print(f"错误: 未找到 {lmarena_models_file}")
        return
    
    with open(lmarena_models_file, 'r', encoding='utf-8') as f:
        all_models = json.load(f)
    
    print(f"\n现有lmarena_models.json:")
    print(f"  总模型数: {len(all_models)}")
    
    # 过滤模型
    filtered_models = {}
    removed_count = 0
    
    for model_name, model_info in all_models.items():
        if model_name in valid_models:
            filtered_models[model_name] = model_info
        else:
            removed_count += 1
    
    print(f"\n过滤后:")
    print(f"  保留模型数: {len(filtered_models)}")
    print(f"  移除模型数: {removed_count}")
    
    # 保存过滤后的模型
    with open(lmarena_models_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_models, f, indent=2, ensure_ascii=False)
    
    print(f"\n已更新: {lmarena_models_file}")
    
    # 检查是否有valid_models中的模型不在all_models中
    missing_models = valid_models - set(all_models.keys())
    if missing_models:
        print(f"\n警告: 有 {len(missing_models)} 个模型在CSV中但不在models.json中:")
        for model in sorted(list(missing_models))[:10]:
            print(f"  - {model}")
        if len(missing_models) > 10:
            print(f"  ... 还有 {len(missing_models) - 10} 个")


if __name__ == '__main__':
    filter_lmarena_models()

