"""
检测未审核模型脚本

检测 data.csv 中的模型是否都已经在审核文件中被审核过。
如果有未审核的模型，发出警告，但允许用户继续（未审核的模型会被丢弃）。

使用场景：
- 用户替换了 input.txt，新增了一些模型
- 用户不想审核新模型，只想继续处理
- 系统会警告有未审核的模型，但允许继续
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple


def get_benchmark_id_from_path(data_csv_path: Path) -> Optional[str]:
    """
    从 data.csv 路径推断 benchmark_id
    
    路径示例：
    - data/raw/artificial_analysis/mmlu_pro/data.csv -> artificial_analysis
    - data/raw/selenium/humaneval/data.csv -> selenium/humaneval
    - data/raw/pandas_read_html/aider_polyglot/data.csv -> pandas_read_html/aider_polyglot
    - data/cleaned/artificial_analysis/mmlu_pro/data.csv -> artificial_analysis
    - data/cleaned/selenium/humaneval/data.csv -> selenium/humaneval
    """
    # 转换为相对于 data/raw 或 data/cleaned 的路径
    parts = data_csv_path.parts
    try:
        # 查找 'raw' 或 'cleaned' 的位置
        data_dir_idx = None
        for idx, part in enumerate(parts):
            if part in ['raw', 'cleaned']:
                data_dir_idx = idx
                break
        
        if data_dir_idx is None:
            return None
        
        # data_dir 之后的路径部分
        path_after_data_dir = parts[data_dir_idx + 1:]
        
        if len(path_after_data_dir) < 2:
            return None
        
        # 最后一个部分是文件名（data.csv），倒数第二个是benchmark名称
        if path_after_data_dir[-1] == 'data.csv':
            # 特殊处理：artificial_analysis
            if path_after_data_dir[0] == 'artificial_analysis':
                return 'artificial_analysis'
            else:
                # 其他情况：method/benchmark_name
                if len(path_after_data_dir) >= 2:
                    method = path_after_data_dir[0]
                    benchmark_name = path_after_data_dir[-2]  # 倒数第二个
                    return f"{method}/{benchmark_name}"
        
        return None
    except (ValueError, IndexError):
        return None


def get_review_file_path(benchmark_id: str, review_files_dir: Path) -> Optional[Path]:
    """
    根据 benchmark_id 获取对应的审核文件路径
    
    特殊处理：
    - artificial_analysis -> artificial_analysis_review.json
    - 其他 -> {method}_{benchmark_name}_review.json
    """
    if benchmark_id == 'artificial_analysis':
        return review_files_dir / 'artificial_analysis_review.json'
    else:
        # 将 method/benchmark_name 转换为 method_benchmark_name
        safe_name = benchmark_id.replace('/', '_')
        return review_files_dir / f'{safe_name}_review.json'


def is_model_reviewed(model_name: str, review_data: Dict) -> bool:
    """
    检查模型是否已经被审核
    
    审核标准（从 reviewed_files 读取）：
    1. 模型在审核文件中存在
    2. human_approved == 1（人类已认可）
    3. selected_lmarena_model 是模型名称（字符串），不是 0 或 -1
    """
    if model_name not in review_data:
        return False
    
    model_data = review_data[model_name]
    
    # 检查 human_approved 字段（从 reviewed_files 读取）
    human_approved = model_data.get('human_approved', 0)
    if human_approved != 1:
        return False
    
    # 检查 selected_lmarena_model 字段
    selected_model = model_data.get('selected_lmarena_model')
    # 只有是字符串（模型名称）才视为已审核
    if isinstance(selected_model, str) and selected_model:
        return True
    
    # 如果是 0 或 -1，视为未审核（无匹配）
    return False


def extract_models_from_csv(data_csv_path: Path) -> List[str]:
    """
    从 data.csv 文件中提取模型名称列表
    
    假设模型名称在 'Model' 列中
    """
    try:
        df = pd.read_csv(data_csv_path)
        
        # 查找模型列（可能是 'Model', 'model', 'Model Name' 等）
        model_column = None
        for col in df.columns:
            if col.lower() in ['model', 'model name', 'model_name']:
                model_column = col
                break
        
        if model_column is None:
            print(f"  警告: 在 {data_csv_path} 中未找到模型列")
            return []
        
        # 提取模型名称，去除空值
        models = df[model_column].dropna().astype(str).tolist()
        # 去除空白字符串
        models = [m.strip() for m in models if m.strip()]
        
        return models
    except Exception as e:
        print(f"  错误: 读取 {data_csv_path} 失败: {e}")
        return []


def check_unreviewed_models(
    data_csv_path: Path,
    review_files_dir: Path,
    verbose: bool = True
) -> Tuple[bool, List[str]]:
    """
    检查指定 data.csv 文件中的模型是否都已审核
    
    返回: (has_unreviewed, unreviewed_models)
    - has_unreviewed: 是否有未审核的模型
    - unreviewed_models: 未审核的模型列表
    """
    # 1. 从路径推断 benchmark_id
    benchmark_id = get_benchmark_id_from_path(data_csv_path)
    if benchmark_id is None:
        if verbose:
            print(f"  警告: 无法从路径推断 benchmark_id: {data_csv_path}")
        return False, []
    
    if verbose:
        print(f"  检测到 benchmark_id: {benchmark_id}")
    
    # 2. 获取审核文件路径
    review_file = get_review_file_path(benchmark_id, review_files_dir)
    if review_file is None:
        if verbose:
            print(f"  警告: 无法确定审核文件路径")
        return False, []
    
    # 3. 检查审核文件是否存在
    if not review_file.exists():
        if verbose:
            print(f"  警告: 审核文件不存在: {review_file}")
            print(f"  提示: 如果这是新benchmark，请先运行 generate_review_files_v2.py 生成审核文件")
        # 如果审核文件不存在，所有模型都视为未审核
        models = extract_models_from_csv(data_csv_path)
        return len(models) > 0, models
    
    # 4. 加载审核文件
    try:
        with open(review_file, 'r', encoding='utf-8') as f:
            review_data = json.load(f)
    except Exception as e:
        if verbose:
            print(f"  错误: 读取审核文件失败: {e}")
        return False, []
    
    # 5. 提取 data.csv 中的模型列表
    models = extract_models_from_csv(data_csv_path)
    if not models:
        if verbose:
            print(f"  警告: 未从 {data_csv_path} 中提取到模型")
        return False, []
    
    if verbose:
        print(f"  从 data.csv 中提取到 {len(models)} 个模型")
    
    # 6. 检查每个模型是否已审核
    unreviewed_models = []
    for model in models:
        if not is_model_reviewed(model, review_data):
            unreviewed_models.append(model)
    
    has_unreviewed = len(unreviewed_models) > 0
    
    if verbose:
        if has_unreviewed:
            print(f"  ⚠️  发现 {len(unreviewed_models)} 个未审核的模型")
        else:
            print(f"  ✅ 所有 {len(models)} 个模型都已审核")
    
    return has_unreviewed, unreviewed_models


def check_all_benchmarks(
    base_dir: Path,
    review_files_dir: Path,
    data_dir: str = 'cleaned'  # 可以是 'raw' 或 'cleaned'
) -> Dict[str, Tuple[bool, List[str]]]:
    """
    检查所有 benchmark 的未审核模型
    
    返回: {benchmark_id: (has_unreviewed, unreviewed_models)}
    """
    data_base_dir = base_dir / 'data' / data_dir
    results = {}
    
    print(f"扫描 {data_base_dir} 目录...")
    
    # 遍历所有 data.csv 文件
    for data_csv_path in data_base_dir.rglob('data.csv'):
        benchmark_id = get_benchmark_id_from_path(data_csv_path)
        if benchmark_id is None:
            continue
        
        print(f"\n检查 {benchmark_id} ({data_csv_path.relative_to(base_dir)})...")
        has_unreviewed, unreviewed_models = check_unreviewed_models(
            data_csv_path,
            review_files_dir,
            verbose=True
        )
        
        results[benchmark_id] = (has_unreviewed, unreviewed_models)
    
    return results


def print_summary(results: Dict[str, Tuple[bool, List[str]]]):
    """打印检查结果摘要"""
    total_benchmarks = len(results)
    benchmarks_with_unreviewed = sum(1 for has_unreviewed, _ in results.values() if has_unreviewed)
    total_unreviewed = sum(len(models) for _, models in results.values())
    
    print("\n" + "="*60)
    print("检查结果摘要")
    print("="*60)
    print(f"总 benchmark 数: {total_benchmarks}")
    print(f"有未审核模型的 benchmark 数: {benchmarks_with_unreviewed}")
    print(f"总未审核模型数: {total_unreviewed}")
    
    if benchmarks_with_unreviewed > 0:
        print("\n⚠️  以下 benchmark 有未审核的模型:")
        for benchmark_id, (has_unreviewed, unreviewed_models) in results.items():
            if has_unreviewed:
                print(f"  - {benchmark_id}: {len(unreviewed_models)} 个未审核模型")
                if len(unreviewed_models) <= 10:
                    for model in unreviewed_models:
                        print(f"      • {model}")
                else:
                    print(f"      (前10个: {', '.join(unreviewed_models[:10])}...)")
        print("\n提示: 未审核的模型在后续处理中会被丢弃。")
        print("      如果需要保留这些模型，请先运行 generate_review_files_v2.py 生成审核文件，")
        print("      然后审核这些模型，最后运行 apply_review_results_v2.py 应用审核结果。")
    else:
        print("\n✅ 所有 benchmark 的模型都已审核！")
    
    print("="*60)


def main():
    """主函数"""
    import sys
    
    base_dir = Path(__file__).parent.parent.parent
    # 从 reviewed_files 读取（包含 human_approved 和 selected_lmarena_model 字段）
    review_files_dir = base_dir / 'data' / 'processed' / 'entity_resolution' / 'reviewed_files'
    
    # 如果提供了命令行参数，检查指定的文件
    if len(sys.argv) > 1:
        data_csv_path = Path(sys.argv[1])
        if not data_csv_path.is_absolute():
            data_csv_path = base_dir / data_csv_path
        
        if not data_csv_path.exists():
            print(f"错误: 文件不存在: {data_csv_path}")
            return
        
        print(f"检查单个文件: {data_csv_path}")
        has_unreviewed, unreviewed_models = check_unreviewed_models(
            data_csv_path,
            review_files_dir,
            verbose=True
        )
        
        if has_unreviewed:
            print(f"\n⚠️  警告: 发现 {len(unreviewed_models)} 个未审核的模型:")
            for model in unreviewed_models:
                print(f"  - {model}")
            print("\n提示: 这些模型在后续处理中会被丢弃。")
            print("      如果需要保留，请先审核这些模型。")
        else:
            print("\n✅ 所有模型都已审核！")
    else:
        # 检查所有 benchmark
        results = check_all_benchmarks(base_dir, review_files_dir, data_dir='cleaned')
        print_summary(results)


if __name__ == '__main__':
    main()

