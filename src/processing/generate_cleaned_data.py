"""
生成 cleaned 数据文件

从 raw data 和 model_extraction 中提取模型名称、分数和排名，
生成 cleaned_data.csv 和 mapping.json 文件。

每个 benchmark 对应一个文件夹，包含：
- cleaned_data.csv: 模型名称、得分、排名
- mapping.json: 模型名称到 LMArena 模型名称的映射
"""

import json
import csv
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd


def extract_score_from_value(value: str) -> Optional[float]:
    """
    从分数值中提取数字，忽略 ± 误差部分
    
    支持格式：
    - "1490" -> 1490.0
    - "1490 ±6" -> 1490.0
    - "71%" -> 71.0
    - "0.945" -> 0.945
    - "40.7% ±2.9%" -> 40.7
    """
    if pd.isna(value) or value == '':
        return None
    
    # 转换为字符串
    value_str = str(value).strip()
    
    # 移除 ± 及其后面的内容
    value_str = re.sub(r'±.*', '', value_str).strip()
    
    # 移除百分号
    if '%' in value_str:
        value_str = value_str.replace('%', '')
        try:
            return float(value_str)
        except ValueError:
            return None
    
    # 尝试直接转换为浮点数
    try:
        return float(value_str)
    except ValueError:
        return None


def find_score_column(df: pd.DataFrame, benchmark_path: Path) -> Optional[Tuple[str, str]]:
    """
    根据 benchmark 路径和 DataFrame 结构，找到分数列
    
    返回: (列名, 提取方法) 或 None
    """
    columns = df.columns.tolist()
    
    # 特殊处理：根据 benchmark 路径判断
    benchmark_str = str(benchmark_path).lower()
    
    # LMArena: Score 列
    if 'lmarena' in benchmark_str:
        if 'Score' in columns:
            return ('Score', 'direct')
        elif 'score' in columns:
            return ('score', 'direct')
    
    # Artificial Analysis: 查找包含百分比的列
    if 'artificial_analysis' in benchmark_str:
        for col in columns:
            if len(df) > 0:
                sample_value = str(df[col].iloc[0])
                if '%' in sample_value:
                    return (col, 'percentage')
        # 如果没有找到百分比列，查找包含 "Score" 或 "Result" 的列
        for col in columns:
            if 'score' in col.lower() or 'result' in col.lower():
                return (col, 'direct')
    
    # FrontierMath: score_value 列
    if 'frontiermath' in benchmark_str:
        if 'score_value' in columns:
            return ('score_value', 'percentage')
        elif 'score' in columns:
            return ('score', 'percentage')
    
    # Manual Direct: 特殊处理
    if 'manual_direct' in benchmark_str:
        if 'facts' in benchmark_str:
            if 'Numerical_Result' in columns:
                return ('Numerical_Result', 'direct')
        elif 'writingbench' in benchmark_str:
            if 'Overall' in columns:
                return ('Overall', 'direct')
        # 通用
        if 'Score' in columns:
            return ('Score', 'direct')
    
    # Selenium: 特殊处理
    if 'selenium' in benchmark_str:
        if 'arc_agi_2' in benchmark_str:
            if 'ARC-AGI-2' in columns:
                return ('ARC-AGI-2', 'percentage')
        elif 'swe_bench_bash_only' in benchmark_str:
            if '% Resolved' in columns:
                return ('% Resolved', 'percentage')
        elif 'creative_writing_v3' in benchmark_str:
            if 'Elo Score' in columns:
                return ('Elo Score', 'direct')
        # 通用
        if 'Score' in columns:
            return ('Score', 'direct')
    
    # Pandas Read HTML: 特殊处理
    if 'pandas_read_html' in benchmark_str:
        if 'aider_polyglot' in benchmark_str:
            if 'Percent correct' in columns:
                return ('Percent correct', 'percentage')
        elif 'terminal_bench_v20' in benchmark_str:
            if 'Accuracy' in columns:
                return ('Accuracy', 'direct')
        # 通用
        if 'Score' in columns:
            return ('Score', 'direct')
    
    # VALS AI: accuracy 列
    if 'vals_ai' in benchmark_str:
        if 'accuracy' in columns:
            return ('accuracy', 'direct')
        elif 'Score' in columns:
            return ('Score', 'direct')
    
    # 通用：查找包含 "Score" 的列
    for col in columns:
        if 'score' in col.lower():
            return (col, 'direct')
    
    # 通用：查找包含 "Result" 的列
    for col in columns:
        if 'result' in col.lower():
            return (col, 'direct')
    
    # 通用：查找包含 "accuracy" 的列
    for col in columns:
        if 'accuracy' in col.lower():
            return (col, 'direct')
    
    # 通用：查找包含 "correct" 的列
    for col in columns:
        if 'correct' in col.lower():
            return (col, 'direct')
    
    return None


def find_model_column(df: pd.DataFrame) -> Optional[str]:
    """找到模型名称列"""
    columns = df.columns.tolist()
    
    # 常见列名（按优先级）
    model_column_names = [
        'Model', 'model', 
        'Model Name', 'model_name', 
        'name', 'Name',
        'AI System',  # selenium/arc_agi_2
        'model_name',  # vals_ai
        'Agent'  # pandas_read_html/terminal_bench_v20
    ]
    
    for col in model_column_names:
        if col in columns:
            return col
    
    # 查找包含 "model" 的列
    for col in columns:
        if 'model' in col.lower():
            return col
    
    # 查找包含 "name" 的列
    for col in columns:
        if 'name' in col.lower():
            return col
    
    return None


def calculate_ranks(scores: List[float]) -> List[int]:
    """
    计算排名，同分并列
    
    例如: [99, 98, 98, 97] -> [1, 2, 2, 4]
    """
    # 创建 (索引, 分数) 的列表
    indexed_scores = [(i, score) for i, score in enumerate(scores)]
    
    # 按分数从大到小排序
    indexed_scores.sort(key=lambda x: x[1], reverse=True)
    
    # 计算排名
    ranks = [0] * len(scores)
    current_rank = 1
    
    i = 0
    while i < len(indexed_scores):
        score = indexed_scores[i][1]
        # 找到所有相同分数的索引
        same_score_indices = []
        j = i
        while j < len(indexed_scores) and indexed_scores[j][1] == score:
            same_score_indices.append(indexed_scores[j][0])
            j += 1
        
        # 分配排名
        for idx in same_score_indices:
            ranks[idx] = current_rank
        
        # 下一个排名
        current_rank += len(same_score_indices)
        i = j
    
    return ranks


def get_benchmark_id_from_path(raw_csv_path: Path, base_dir: Path) -> str:
    """
    从 raw CSV 路径生成 benchmark ID
    
    例如:
    - data/raw/lmarena/Overall/data.csv -> lmarena_overall
    - data/raw/artificial_analysis/aa_lcr/data.csv -> artificial_analysis_aa_lcr
    - data/raw/selenium/humaneval/data.csv -> selenium_humaneval
    """
    # 获取相对于 base_dir/data/raw 的路径
    try:
        relative_path = raw_csv_path.relative_to(base_dir / 'data' / 'raw')
    except ValueError:
        # 如果不在预期路径下，使用文件名
        return raw_csv_path.stem
    
    # 获取所有父目录和文件名（不包括 data.csv）
    parts = list(relative_path.parts[:-1])  # 去掉 data.csv
    
    # 组合成 benchmark_id
    benchmark_id = '_'.join(parts)
    
    return benchmark_id


def get_model_extraction_file(benchmark_id: str, model_extraction_dir: Path) -> Optional[Path]:
    """
    根据 benchmark_id 找到对应的 model_extraction JSON 文件
    """
    # 特殊处理：artificial_analysis 的所有 benchmark 共享一个文件
    if benchmark_id.startswith('artificial_analysis_'):
        return model_extraction_dir / 'artificial_analysis_models.json'
    
    # 特殊处理：LMArena 的所有 category 共享一个文件
    if benchmark_id.startswith('lmarena_'):
        return model_extraction_dir / 'lmarena_models.json'
    
    # 其他 benchmark: {method}_{benchmark_name}_models.json
    # 但 benchmark_id 已经是 {method}_{benchmark_name} 格式
    possible_files = [
        model_extraction_dir / f'{benchmark_id}_models.json',
    ]
    
    for file_path in possible_files:
        if file_path.exists():
            return file_path
    
    return None


def get_reviewed_file(benchmark_id: str, reviewed_files_dir: Path) -> Optional[Path]:
    """
    根据 benchmark_id 找到对应的 reviewed JSON 文件
    """
    # 特殊处理：artificial_analysis
    if benchmark_id.startswith('artificial_analysis_'):
        return reviewed_files_dir / 'artificial_analysis_review.json'
    
    # 特殊处理：LMArena
    if benchmark_id.startswith('lmarena_'):
        return reviewed_files_dir / 'lmarena_review.json'
    
    # 其他 benchmark: {benchmark_id}_review.json
    possible_files = [
        reviewed_files_dir / f'{benchmark_id}_review.json',
    ]
    
    for file_path in possible_files:
        if file_path.exists():
            return file_path
    
    return None


def process_benchmark(
    raw_csv_path: Path,
    base_dir: Path,
    model_extraction_dir: Path,
    reviewed_files_dir: Path,
    cleaned_dir: Path
):
    """处理单个 benchmark"""
    print(f"\n处理: {raw_csv_path}")
    
    # 获取 benchmark_id
    benchmark_id = get_benchmark_id_from_path(raw_csv_path, base_dir)
    print(f"  Benchmark ID: {benchmark_id}")
    
    # 创建输出目录
    output_dir = cleaned_dir / benchmark_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 读取 raw CSV（尝试多种编码）
    df = None
    for encoding in ['utf-8', 'gbk', 'latin-1', 'cp1252']:
        try:
            df = pd.read_csv(raw_csv_path, encoding=encoding)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            print(f"  错误: 无法读取 CSV 文件: {e}")
            return
    
    if df is None:
        print(f"  错误: 无法使用任何编码读取 CSV 文件")
        return
    
    # 找到模型列和分数列
    model_col = find_model_column(df)
    score_info = find_score_column(df, raw_csv_path)
    
    if model_col is None:
        print(f"  警告: 未找到模型名称列，可用列: {df.columns.tolist()}")
        return
    
    if score_info is None:
        print(f"  警告: 未找到分数列，可用列: {df.columns.tolist()}")
        return
    
    score_col, score_method = score_info
    # 避免 Windows 控制台编码问题
    try:
        print(f"  使用模型列: {model_col}, 分数列: {score_col}")
    except UnicodeEncodeError:
        print(f"  使用模型列: {model_col}, 分数列: {score_col.encode('ascii', 'ignore').decode('ascii')}")
    
    # 读取 model_extraction JSON
    model_extraction_file = get_model_extraction_file(benchmark_id, model_extraction_dir)
    if model_extraction_file is None:
        print(f"  警告: 未找到 model_extraction 文件: {benchmark_id}")
        return
    
    with open(model_extraction_file, 'r', encoding='utf-8') as f:
        model_extraction = json.load(f)
    
    print(f"  从 {model_extraction_file.name} 读取了 {len(model_extraction)} 个模型")
    
    # 提取数据：只处理 model_extraction 中存在的模型
    model_data = []
    for _, row in df.iterrows():
        model_name_raw = str(row[model_col]).strip()
        
        # 检查这个模型是否在 model_extraction 中
        if model_name_raw not in model_extraction:
            continue
        
        # 提取分数
        score_value = row[score_col]
        score = extract_score_from_value(score_value)
        
        if score is None:
            continue
        
        model_data.append({
            'model_name': model_name_raw,
            'score': score
        })
    
    if not model_data:
        print(f"  警告: 没有找到匹配的模型数据")
        return
    
    # 按分数排序并计算排名
    model_data.sort(key=lambda x: x['score'], reverse=True)
    scores = [item['score'] for item in model_data]
    ranks = calculate_ranks(scores)
    
    # 添加排名
    for i, item in enumerate(model_data):
        item['rank'] = ranks[i]
    
    # 写入 cleaned_data.csv
    cleaned_csv_path = output_dir / 'cleaned_data.csv'
    with open(cleaned_csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['model_name', 'score', 'rank'])
        writer.writeheader()
        writer.writerows(model_data)
    
    print(f"  生成了 {cleaned_csv_path}，包含 {len(model_data)} 个模型")
    
    # 读取 reviewed file 生成 mapping.json
    reviewed_file = get_reviewed_file(benchmark_id, reviewed_files_dir)
    if reviewed_file is None:
        print(f"  警告: 未找到 reviewed 文件: {benchmark_id}")
        mapping = {}
    else:
        with open(reviewed_file, 'r', encoding='utf-8') as f:
            reviewed_data = json.load(f)
        
        mapping = {}
        lmarena_to_benchmark = {}  # 用于检测重复映射：lmarena_model -> [benchmark_model_names]
        duplicate_count = 0  # 统计重复数量
        
        for model_name, entry in reviewed_data.items():
            # 只处理在 model_extraction 中存在的模型
            if model_name not in model_extraction:
                continue
            
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
                lmarena_to_benchmark[selected_model] = model_name  # 只记录第一个映射的模型名
        
        if duplicate_count > 0:
            print(f"  补丁: 发现 {duplicate_count} 个重复的 LMArena 映射，已只保留第一个")
        print(f"  从 {reviewed_file.name} 读取了 {len(mapping)} 个映射关系（已去重）")
    
    # 写入 mapping.json
    mapping_json_path = output_dir / 'mapping.json'
    with open(mapping_json_path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    print(f"  生成了 {mapping_json_path}，包含 {len(mapping)} 个映射")


def main():
    """主函数"""
    base_dir = Path(__file__).parent.parent.parent
    raw_dir = base_dir / 'data' / 'raw'
    model_extraction_dir = base_dir / 'data' / 'processed' / 'model_extraction'
    reviewed_files_dir = base_dir / 'data' / 'processed' / 'entity_resolution' / 'reviewed_files'
    cleaned_dir = base_dir / 'data' / 'processed' / 'cleaned'
    
    # 创建 cleaned 目录
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    
    # 查找所有 data.csv 文件
    csv_files = list(raw_dir.rglob('data.csv'))
    
    print(f"找到 {len(csv_files)} 个 data.csv 文件")
    
    # 处理每个 benchmark
    for csv_file in sorted(csv_files):
        try:
            process_benchmark(
                csv_file,
                base_dir,
                model_extraction_dir,
                reviewed_files_dir,
                cleaned_dir
            )
        except Exception as e:
            print(f"处理 {csv_file} 时出错: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n完成！")


if __name__ == '__main__':
    main()

