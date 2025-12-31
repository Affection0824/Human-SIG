"""
批量提取所有benchmark的模型信息
为每个benchmark创建单独的JSON文件
"""

import json
import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from common_parser import parse_model_name

def find_model_column(headers):
    """查找模型名列"""
    possible_names = ['Model', 'model', 'Model Name', 'model_name', 'name', 'Agent', 'agent', 'AI System']
    for col in headers:
        if col in possible_names:
            return col
    return None

def extract_benchmark(csv_file: Path, benchmark_id: str, score_filter=None):
    """提取单个benchmark的模型信息"""
    models = {}
    special_cases = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            # 尝试检测分隔符
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            reader = csv.DictReader(f, delimiter=delimiter)
            headers = reader.fieldnames
            
            if not headers:
                special_cases.append(f"CSV文件无表头: {csv_file}")
                return models, special_cases
            
            model_col = find_model_column(headers)
            if not model_col:
                special_cases.append(f"未找到模型列，表头: {headers}")
                return models, special_cases
            
            score_col = None
            if score_filter:
                score_col = 'Score' if 'Score' in headers else None
            
            for row in reader:
                model_name = row[model_col].strip()
                if not model_name:
                    continue
                
                # 应用分数过滤（如果需要）
                if score_filter and score_col:
                    try:
                        score_str = row[score_col].replace('Preliminary', '').strip()
                        score = float(score_str)
                        if score < score_filter:
                            continue
                    except (ValueError, KeyError):
                        continue
                
                parsed = parse_model_name(model_name)
                
                # 检查解析结果
                if not parsed['family']:
                    special_cases.append(f"无法提取家族: {model_name}")
                
                models[model_name] = parsed
                
    except Exception as e:
        special_cases.append(f"处理文件时出错: {e}")
    
    return models, special_cases

def main():
    """主函数：处理所有benchmark"""
    base_dir = Path(__file__).parent.parent.parent.parent
    raw_dir = base_dir / 'data' / 'raw'
    output_dir = base_dir / 'data' / 'processed' / 'model_extraction'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_special_cases = {}
    
    # 处理 LMArena（所有category，但只处理Overall，其他可以后续处理）
    print("处理 LMArena Overall...")
    lmarena_file = raw_dir / 'lmarena' / 'Overall' / 'data.csv'
    if lmarena_file.exists():
        models, cases = extract_benchmark(lmarena_file, 'lmarena', score_filter=1330)
        if models:
            output_file = output_dir / 'lmarena_models.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(models, f, indent=2, ensure_ascii=False)
            print(f"  已处理 {len(models)} 个模型")
        if cases:
            all_special_cases['lmarena'] = cases
    
    # 处理 Artificial Analysis（只处理第一个，所有10个benchmark共享）
    print("\n处理 Artificial Analysis...")
    aa_file = raw_dir / 'artificial_analysis' / 'aa_lcr' / 'data.csv'
    if aa_file.exists():
        models, cases = extract_benchmark(aa_file, 'artificial_analysis')
        if models:
            output_file = output_dir / 'artificial_analysis_models.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(models, f, indent=2, ensure_ascii=False)
            print(f"  已处理 {len(models)} 个模型")
        if cases:
            all_special_cases['artificial_analysis'] = cases
    
    # 处理其他所有benchmark
    print("\n处理其他benchmark...")
    for csv_file in raw_dir.rglob('data.csv'):
        # 跳过已处理的
        if 'lmarena/Overall' in str(csv_file) or 'artificial_analysis/aa_lcr' in str(csv_file):
            continue
        
        # 确定benchmark_id
        parts = csv_file.parts
        try:
            raw_idx = parts.index('raw')
            path_after_raw = parts[raw_idx + 1:]
            
            if len(path_after_raw) < 2:
                continue
            
            if path_after_raw[-1] == 'data.csv':
                if path_after_raw[0] == 'artificial_analysis':
                    continue  # 已处理
                elif path_after_raw[0] == 'lmarena':
                    continue  # 只处理Overall
                else:
                    # method/benchmark_name
                    method = path_after_raw[0]
                    benchmark_name = path_after_raw[-2]
                    benchmark_id = f"{method}/{benchmark_name}"
                    
                    # 生成输出文件名
                    safe_name = benchmark_id.replace('/', '_')
                    output_file = output_dir / f'{safe_name}_models.json'
                    
                    print(f"  处理 {benchmark_id}...")
                    models, cases = extract_benchmark(csv_file, benchmark_id)
                    
                    if models:
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(models, f, indent=2, ensure_ascii=False)
                        print(f"    已处理 {len(models)} 个模型")
                    
                    if cases:
                        all_special_cases[benchmark_id] = cases
        except (ValueError, IndexError):
            continue
    
    # 打印所有特判情况
    print("\n" + "="*60)
    print("特判情况汇总")
    print("="*60)
    total_special = sum(len(cases) for cases in all_special_cases.values())
    print(f"总特判数量: {total_special}")
    
    for benchmark_id, cases in all_special_cases.items():
        if cases:
            print(f"\n{benchmark_id}: {len(cases)} 个特判")
            for case in cases[:5]:
                # 确保输出是ASCII安全的
                case_str = str(case).encode('ascii', 'ignore').decode('ascii')
                print(f"  - {case_str}")
            if len(cases) > 5:
                print(f"  ... 还有 {len(cases) - 5} 个")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    main()

