"""
验证生成的结果，检查不合理的地方
"""

import json
from pathlib import Path
from collections import defaultdict

def validate_results():
    """验证所有生成的JSON文件"""
    base_dir = Path(__file__).parent.parent.parent.parent
    extraction_dir = base_dir / 'data' / 'processed' / 'model_extraction'
    
    issues = defaultdict(list)
    
    for json_file in extraction_dir.glob('*_models.json'):
        benchmark_id = json_file.stem.replace('_models', '')
        
        with open(json_file, 'r', encoding='utf-8') as f:
            models = json.load(f)
        
        for model_name, info in models.items():
            # 检查1: 家族为None
            if not info.get('family'):
                issues[f"{benchmark_id}: 无法提取家族"].append(model_name)
            
            # 检查2: 版本号格式不一致
            version = info.get('version')
            if version:
                try:
                    float(version)
                except (ValueError, TypeError):
                    issues[f"{benchmark_id}: 版本号格式异常"].append(f"{model_name}: {version}")
            
            # 检查3: 参数量格式异常
            params = info.get('parameters')
            if params:
                if not params.endswith('B'):
                    issues[f"{benchmark_id}: 参数量格式异常"].append(f"{model_name}: {params}")
            
            # 检查4: 家族名不是已知的模型家族（这个需要手动检查）
            family = info.get('family')
            if family and family not in ['gpt', 'claude', 'gemini', 'grok', 'qwen', 'kimi', 'deepseek',
                                         'mistral', 'llama', 'glm', 'ernie', 'nova', 'granite', 'phi',
                                         'gemma', 'codestral', 'chatgpt', 'mimo', 'hunyuan', 'doubao',
                                         'apriel', 'kat', 'minimax', 'oss', 'yi', 'command', 'stepfun',
                                         'ling', 'ring', 'longcat', 'mai', 'intellect', 'cohere', 'tencent',
                                         'nvidia', 'meta', 'amazon', 'z', 'zhipu', 'baidu', 'alibaba',
                                         'xiaomi', 'meituan', 'ant', 'inclusion', '01', 'snowflake',
                                         'databricks', 'mosaic', 'tii', 'internlm', 'microsoft', 'azure',
                                         'nexusflow', 'lmsys', 'allen', 'ai21', 'ibm', 'reka', 'upstage',
                                         'cognitive', 'nous', 'openchat', 'huggingface', 'rwkv',
                                         'openassistant', 'stability', 'nomic', 'princeton', 'stanford',
                                         'uc', 'uw', 'together', 'liquid', 'lg', 'naver', 'service', 'now',
                                         'kwai', 'korea', 'telecom', 'mbzuai', 'perplexity', 'motif',
                                         'inception', 'deep', 'cogito', 'prime']:
                # 这个检查可能不准确，因为可能有新的家族
                pass
    
    # 打印报告
    print("="*60)
    print("验证结果报告")
    print("="*60)
    
    total_issues = sum(len(cases) for cases in issues.values())
    print(f"\n总问题数: {total_issues}\n")
    
    for issue_type, cases in sorted(issues.items()):
        print(f"{issue_type}: {len(cases)} 个")
        for case in cases[:5]:
            print(f"  - {case}")
        if len(cases) > 5:
            print(f"  ... 还有 {len(cases) - 5} 个")
        print()
    
    return issues

if __name__ == '__main__':
    validate_results()

