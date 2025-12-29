"""
根据验证结果更新metadata.json中的can_read_html字段

使用方法:
    python github/src/ingestion/update_can_read_html.py
"""

import json
from pathlib import Path

def main():
    # 路径设置
    script_path = Path(__file__).resolve()
    github_dir = script_path.parent.parent.parent
    results_path = github_dir / "results" / "read_html_verification_results.json"
    metadata_path = github_dir / "config" / "metadata.json"
    
    # 读取验证结果
    with open(results_path, 'r', encoding='utf-8') as f:
        results_data = json.load(f)
    
    # 创建benchmark_name到can_read_html的映射
    verification_map = {
        r['benchmark_name']: r['can_read_html']
        for r in results_data['verification_results']
    }
    
    # 读取metadata.json
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # 更新can_read_html字段
    updated_count = 0
    for entry in metadata:
        if isinstance(entry, dict):
            # 只更新benchmark条目（不包含elo_column字段）
            if 'benchmark_name' in entry and 'elo_column' not in entry:
                benchmark_name = entry['benchmark_name']
                if benchmark_name in verification_map:
                    old_value = entry.get('can_read_html', None)
                    new_value = verification_map[benchmark_name]
                    entry['can_read_html'] = new_value
                    updated_count += 1
                    print(f"Updated {benchmark_name}: can_read_html = {new_value} (was {old_value})")
    
    # 保存更新后的metadata.json
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n总共更新了 {updated_count} 个benchmark条目的can_read_html字段")
    
    # 统计结果
    successful = sum(1 for r in results_data['verification_results'] if r['can_read_html'])
    failed = len(results_data['verification_results']) - successful
    print(f"\n验证结果汇总:")
    print(f"  成功 (can_read_html=true): {successful} 个")
    print(f"  失败 (can_read_html=false): {failed} 个")

if __name__ == "__main__":
    main()

