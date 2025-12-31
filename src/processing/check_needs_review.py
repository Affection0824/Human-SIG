"""检查 needs_review 字段"""

import json
from pathlib import Path

base_dir = Path(__file__).parent.parent.parent
reviewed_dir = base_dir / 'data' / 'processed' / 'entity_resolution' / 'reviewed_files'

total_needs_review = 0
total_all = 0

for reviewed_file in reviewed_dir.glob('*_review.json'):
    with open(reviewed_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for model_name, entry in data.items():
        total_all += 1
        if entry.get('needs_review', False):
            total_needs_review += 1

print(f"总条目数: {total_all}")
print(f"needs_review=True 的条目数: {total_needs_review}")
print(f"比例: {total_needs_review/total_all*100:.1f}%")

