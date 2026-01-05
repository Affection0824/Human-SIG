"""
第一步：从 raw data 生成 cleaned_data.csv（确定性）

输入：data/raw/*/data.csv
输出：data/processed/cleaned/{benchmark_id}/cleaned_data.csv

功能：
1. 从原始数据 CSV 文件中提取模型名称、分数
2. 计算排名（同分并列）
3. 生成标准化的 cleaned_data.csv 文件

注意：只生成 cleaned_data.csv，不生成 mapping.json
"""

import json
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd


# ============================================================================
# 工具函数：模型名称清理
# ============================================================================

# selenium benchmark 中需要删除的公司名称后缀列表
# 注意：按照长度降序排列，以便先匹配更长的后缀（如 "NewZhipu AI" 应该在 "Zhipu AI" 之前）
SELENIUM_COMPANY_SUFFIXES = [
    'Alibaba Cloud / Qwen Team',
    'NewZhipu AI',
    'NewMiniMax',
    'Moonshot AI',
    'Mistral AI',
    'Zhipu AI',
    'DeepSeek',
    'Xiaomi',
    'NVIDIA',
    'OpenAI',
    'Anthropic',
    'Google',
    'MiniMax',
    'Amazon',
    'xAI',
    'Meta',
    'IBM',
]


def clean_model_name(model_name: str, benchmark_id: str) -> str:
    """
    清理模型名称，删除公司名称后缀等无关信息
    
    对于 selenium benchmark，删除模型名称后面的公司名称后缀
    """
    cleaned = model_name.strip()
    
    # 只处理 selenium benchmark
    if benchmark_id.startswith('selenium_'):
        # 删除公司名称后缀（可能直接连接或前面有空格）
        for company in SELENIUM_COMPANY_SUFFIXES:
            # 尝试直接连接的格式（如 "GPT-5.2 ProOpenAI"）
            if cleaned.endswith(company):
                cleaned = cleaned[:-len(company)]
            # 尝试有空格分隔的格式
            elif cleaned.endswith(f' {company}'):
                cleaned = cleaned[:-len(f' {company}')]
        
        # 再次清理前后空格
        cleaned = cleaned.strip()
    
    return cleaned


def handle_duplicate_model_names(model_data: List[Dict]) -> List[Dict]:
    """
    处理重复的模型名称，为重复的模型名称添加 (2), (3) 等后缀
    
    确保 cleaned_data 中的模型名称完全没有重复
    """
    # 统计每个模型名称出现的次数
    name_count = {}
    for item in model_data:
        name = item['model_name']
        name_count[name] = name_count.get(name, 0) + 1
    
    # 如果有重复，为后续出现的添加后缀
    if any(count > 1 for count in name_count.values()):
        name_index = {}
        result = []
        for item in model_data:
            name = item['model_name']
            if name_count[name] > 1:
                # 有重复，需要添加后缀
                if name not in name_index:
                    name_index[name] = 1
                else:
                    name_index[name] += 1
                    # 为第二个及后续的出现添加 (2), (3) 等后缀
                    item = item.copy()
                    item['model_name'] = f"{name}({name_index[name]})"
            result.append(item)
        return result
    
    return model_data


# ============================================================================
# 工具函数：分数提取和列识别
# ============================================================================

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


def find_model_column(df) -> Optional[str]:
    """
    找到模型名称列
    
    自动识别常见的模型列名：Model, model, Model Name, model_name, AI System, name, Agent
    如果没找到，返回第一列
    """
    columns = df.columns.tolist()
    
    # 常见的模型列名
    possible_names = ['Model', 'model', 'Model Name', 'model_name', 'AI System', 'name', 'Agent']
    
    for name in possible_names:
        if name in columns:
            return name
    
    # 如果没找到，返回第一列
    if len(columns) > 0:
        return columns[0]
    
    return None


def find_score_column(df, benchmark_path: Path) -> Optional[Tuple[str, str]]:
    """
    根据 benchmark 路径和 DataFrame 结构，找到分数列
    
    返回: (列名, 提取方法) 或 None
    提取方法: 'direct' 表示直接使用，'percentage' 表示百分比格式
    """
    columns = df.columns.tolist()
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
    
    # Pandas Read HTML: 特殊处理
    if 'pandas_read_html' in benchmark_str:
        if 'aider_polyglot' in benchmark_str:
            if 'Percent correct' in columns:
                return ('Percent correct', 'percentage')
        elif 'terminal_bench_v20' in benchmark_str:
            if 'Accuracy' in columns:
                return ('Accuracy', 'percentage')
    
    # Selenium: 特殊处理
    if 'selenium' in benchmark_str:
        if 'arc_agi_2' in benchmark_str:
            if 'ARC-AGI-2' in columns:
                return ('ARC-AGI-2', 'direct')
        elif 'creative_writing_v3' in benchmark_str:
            if 'Elo Score' in columns:
                return ('Elo Score', 'direct')
        elif 'swe_bench_bash_only' in benchmark_str:
            if '% Resolved' in columns:
                return ('% Resolved', 'percentage')
        elif 'Score' in columns:
            return ('Score', 'direct')
        elif 'score' in columns:
            return ('score', 'direct')
    
    # VALS AI: accuracy 列
    if 'vals_ai' in benchmark_str:
        if 'accuracy' in columns:
            return ('accuracy', 'percentage')
    
    # 通用：查找包含 score, result, accuracy, correct 的列
    for col in columns:
        col_lower = col.lower()
        if 'score' in col_lower or 'result' in col_lower or 'accuracy' in col_lower or 'correct' in col_lower:
            return (col, 'direct')
    
    return None


def calculate_ranks(scores: List[float]) -> List[int]:
    """
    计算排名，同分并列
    
    例如: [99, 98, 98, 97] -> [1, 2, 2, 4]
    
    算法：
    1. 按分数从大到小排序
    2. 相同分数获得相同排名
    3. 下一个排名跳过并列数量
    """
    if not scores:
        return []
    
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


# ============================================================================
# 工具函数：路径处理
# ============================================================================

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
    
    用于验证模型名称一致性（可选）
    """
    # 特殊处理：artificial_analysis 的所有 benchmark 共享一个文件
    if benchmark_id.startswith('artificial_analysis_'):
        return model_extraction_dir / 'artificial_analysis_models.json'
    
    # 特殊处理：LMArena 的所有 category 共享一个文件
    if benchmark_id.startswith('lmarena_'):
        return model_extraction_dir / 'lmarena_models.json'
    
    # 其他 benchmark: {method}_{benchmark_name}_models.json
    possible_files = [
        model_extraction_dir / f'{benchmark_id}_models.json',
    ]
    
    for file_path in possible_files:
        if file_path.exists():
            return file_path
    
    return None


# ============================================================================
# 主处理函数
# ============================================================================

def process_benchmark(
    raw_csv_path: Path,
    base_dir: Path,
    model_extraction_dir: Path,
    cleaned_dir: Path
):
    """
    处理单个 benchmark，生成 cleaned_data.csv
    
    步骤：
    1. 读取 raw CSV 文件（尝试多种编码）
    2. 识别模型名称列和分数列
    3. 可选：读取 model_extraction JSON 文件验证模型名称一致性
    4. 提取模型名称和分数
    5. 计算排名（同分并列）
    6. 写入 cleaned_data.csv
    """
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
    try:
        print(f"  使用模型列: {model_col}, 分数列: {score_col}")
    except UnicodeEncodeError:
        print(f"  使用模型列: {model_col}, 分数列: {score_col.encode('ascii', 'ignore').decode('ascii')}")
    
    # 读取 model_extraction JSON（用于验证模型名称一致性，可选）
    model_extraction = {}
    if model_extraction_dir.exists():
        model_extraction_file = get_model_extraction_file(benchmark_id, model_extraction_dir)
        if model_extraction_file is not None and model_extraction_file.exists():
            try:
                with open(model_extraction_file, 'r', encoding='utf-8') as f:
                    model_extraction = json.load(f)
                print(f"  从 {model_extraction_file.name} 读取了 {len(model_extraction)} 个模型（用于验证）")
            except Exception as e:
                print(f"  警告: 无法读取 model_extraction 文件: {e}")
                print(f"  将使用 CSV 中的所有模型（不进行一致性验证）")
        else:
            print(f"  提示: 未找到 model_extraction 文件: {benchmark_id}")
            print(f"  将使用 CSV 中的所有模型（不进行一致性验证）")
    else:
        print(f"  提示: model_extraction 目录不存在，将使用 CSV 中的所有模型（不进行一致性验证）")
    
    # 提取数据
    model_data = []
    
    # 对于 manual_direct_facts benchmark，只提取 Task_Name == Average 的行
    if benchmark_id == 'manual_direct_facts':
        # 查找 Task_Name 列
        task_name_col = None
        for col in df.columns:
            if 'task_name' in col.lower() or col == 'Task_Name':
                task_name_col = col
                break
        
        if task_name_col is not None:
            # 过滤只保留 Task_Name == Average 的行
            original_count = len(df)
            df = df[df[task_name_col].astype(str).str.strip() == 'Average'].copy()
            filtered_count = len(df)
            print(f"  过滤 Task_Name: 从 {original_count} 行减少到 {filtered_count} 行（只保留 Average）")
        else:
            print(f"  警告: 未找到 Task_Name 列，将处理所有行")
    
    for _, row in df.iterrows():
        model_name_raw = str(row[model_col]).strip()
        
        # 清理模型名称（删除公司名称后缀等）
        model_name_cleaned = clean_model_name(model_name_raw, benchmark_id)
        
        # 如果 model_extraction 不为空，检查清理后的名称是否存在
        # 注意：这里我们检查原始名称，因为 model_extraction 中可能包含原始名称
        if model_extraction:
            # 先检查清理后的名称，再检查原始名称
            if model_name_cleaned not in model_extraction and model_name_raw not in model_extraction:
                continue
        
        # 提取分数
        score_value = row[score_col]
        score = extract_score_from_value(score_value)
        
        if score is None:
            continue
        
        model_data.append({
            'model_name': model_name_cleaned,
            'score': score
        })
    
    if not model_data:
        print(f"  警告: 没有找到匹配的模型数据")
        return
    
    # 处理重复的模型名称（在排序前处理，以便保持原始顺序）
    model_data = handle_duplicate_model_names(model_data)
    
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


def main():
    """
    主函数
    
    遍历所有 raw data CSV 文件，为每个 benchmark 生成 cleaned_data.csv
    """
    base_dir = Path(__file__).parent.parent.parent
    raw_dir = base_dir / 'data' / 'raw'
    model_extraction_dir = base_dir / 'data' / 'processed' / 'model_extraction'
    cleaned_dir = base_dir / 'data' / 'processed' / 'cleaned'
    
    # 创建 cleaned 目录
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    
    # 查找所有 data.csv 文件
    csv_files = list(raw_dir.rglob('data.csv'))
    print(f"找到 {len(csv_files)} 个 data.csv 文件")
    
    # 处理每个 benchmark
    for csv_file in sorted(csv_files):
        process_benchmark(
            csv_file,
            base_dir,
            model_extraction_dir,
            cleaned_dir
        )
    
    print("\n完成！")


if __name__ == '__main__':
    main()
