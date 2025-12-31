"""
生成所有 benchmark 的临时提取脚本
自动检测每个 CSV 的格式，生成对应的提取脚本
"""

import csv
import json
from pathlib import Path
import sys

# 添加 common_parser 到路径
sys.path.insert(0, str(Path(__file__).parent))
from common_parser import parse_model_name


def detect_csv_format(csv_file: Path) -> dict:
    """检测 CSV 文件的格式"""
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        # 读取前几行
        sample_rows = []
        for i, row in enumerate(reader):
            if i >= 5:
                break
            sample_rows.append(row)
    
    # 检测模型列
    model_column = None
    for col in headers:
        col_lower = col.lower()
        if 'model' in col_lower or col_lower == 'name' or col_lower == 'ai system':
            model_column = col
            break
    
    # 特殊处理：frontiermath 使用 name 列而不是 model_key
    if 'name' in headers and 'model_key' in headers:
        model_column = 'name'
    
    # 检测分数列（用于 LMArena）
    score_column = None
    for col in headers:
        col_lower = col.lower()
        if col_lower == 'score':
            score_column = col
            break
    
    return {
        'model_column': model_column,
        'score_column': score_column,
        'headers': headers,
        'sample_rows': sample_rows
    }


def generate_extraction_script(benchmark_id: str, csv_file: Path, format_info: dict, output_dir: Path):
    """为单个 benchmark 生成提取脚本"""
    model_column = format_info['model_column']
    score_column = format_info['score_column']
    
    if not model_column:
        print(f"警告: {benchmark_id} 未找到模型列")
        return None
    
    script_name = benchmark_id.replace('/', '_').replace('\\', '_') + '_extract.py'
    script_path = output_dir / script_name
    
    # 判断是否是 LMArena
    is_lmarena = 'lmarena' in str(csv_file).lower()
    
    # 获取相对路径（相对于项目根目录）
    # csv_file 路径类似: Human-SIG/data/raw/...
    # 需要找到项目根目录（包含 data 目录的目录）
    project_root = csv_file.parents[2]  # 从 data/raw/benchmark/data.csv 到项目根目录
    csv_relative = csv_file.relative_to(project_root)
    csv_path_str = str(csv_relative).replace('\\', '/')
    
    # 输出文件名
    output_filename = benchmark_id.replace('/', '_').replace('\\', '_') + '_models.json'
    
    script_content = f'''"""
临时提取脚本: {benchmark_id}
从 data/raw/{csv_path_str.replace('data/raw/', '')} 提取模型信息
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
    csv_file = base_dir / 'data' / 'raw' / Path('{csv_path_str.replace('data/raw/', '')}')
    output_file = base_dir / 'data' / 'processed' / 'model_extraction' / '{output_filename}'
    
    models = {{}}
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            model_name = row.get('{model_column}')
            
            # 跳过空值
            if not model_name:
                continue
            
            # 清理模型名称（移除组织名称等）
            model_clean = model_name.strip()
            
            # 跳过空字符串
            if not model_clean:
                continue
            
            # 对于 LMArena，需要过滤 Score >= 1330
'''
    
    if is_lmarena and score_column:
        script_content += f'''            try:
                score_str = row['{score_column}'].replace('Preliminary', '').strip()
                score = float(score_str)
                if score < 1330:
                    continue
            except (ValueError, KeyError):
                continue
'''
    
    script_content += f'''            
            # 解析模型名称
            parsed = parse_model_name(model_clean)
            models[model_name] = parsed
    
    # 保存 JSON
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(models, f, indent=2, ensure_ascii=False)
    
    print(f"处理了 {{len(models)}} 个模型: {benchmark_id}")
    return models

if __name__ == '__main__':
    extract_models()
'''
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    return script_path


def main():
    """主函数：为所有 benchmark 生成提取脚本"""
    base_dir = Path(__file__).parent.parent.parent.parent
    raw_data_dir = base_dir / 'data' / 'raw'
    output_dir = Path(__file__).parent
    
    scripts_generated = []
    
    # 遍历所有 data.csv 文件
    for csv_file in raw_data_dir.rglob('data.csv'):
        # 确定 benchmark_id
        parts = csv_file.parts
        try:
            raw_idx = parts.index('raw')
            path_after_raw = parts[raw_idx + 1:]
            
            if len(path_after_raw) < 2:
                continue
            
            # 特殊处理：artificial_analysis（所有子目录共享同一个 JSON 文件）
            if path_after_raw[0] == 'artificial_analysis':
                benchmark_id = 'artificial_analysis'
                # 只处理第一个子目录，其他跳过（因为它们共享同一个 JSON）
                if path_after_raw[1] != 'aa_lcr':
                    continue
            # 特殊处理：lmarena（只处理 Overall，其他类别跳过）
            elif path_after_raw[0] == 'lmarena':
                if path_after_raw[1] != 'Overall':
                    continue
                benchmark_id = 'lmarena'
            else:
                # 其他情况：method/benchmark_name
                if len(path_after_raw) >= 2:
                    method = path_after_raw[0]
                    benchmark_name = path_after_raw[-2]  # 倒数第二个
                    benchmark_id = f"{method}/{benchmark_name}"
                else:
                    continue
        except (ValueError, IndexError):
            continue
        
        # 检测格式
        print(f"\n检测 {benchmark_id} 的格式...")
        format_info = detect_csv_format(csv_file)
        
        if not format_info['model_column']:
            print(f"  警告: 未找到模型列，跳过")
            continue
        
        print(f"  模型列: {format_info['model_column']}")
        if format_info['score_column']:
            print(f"  分数列: {format_info['score_column']}")
        
        # 生成脚本
        script_path = generate_extraction_script(benchmark_id, csv_file, format_info, output_dir)
        if script_path:
            scripts_generated.append((benchmark_id, script_path))
            print(f"  已生成: {script_path.name}")
    
    print(f"\n" + "="*60)
    print(f"共生成 {len(scripts_generated)} 个提取脚本")
    print("="*60)
    
    return scripts_generated


if __name__ == '__main__':
    main()

