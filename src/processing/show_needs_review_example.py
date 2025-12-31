"""显示一个需要审核的条目示例"""

import json
from pathlib import Path

base_dir = Path(__file__).parent.parent.parent
reviewed_dir = base_dir / 'data' / 'processed' / 'entity_resolution' / 'reviewed_files'

# 查找第一个 needs_review: true 的条目
for reviewed_file in reviewed_dir.glob('*_review.json'):
    with open(reviewed_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for model_name, entry in data.items():
        if entry.get('needs_review', False):
            print(f"Benchmark: {reviewed_file.stem}")
            print(f"Model: {model_name}")
            print(f"needs_review: {entry.get('needs_review')}")
            print(f"selected_lmarena_model: {entry.get('selected_lmarena_model')}")
            print(f"candidates count: {len(entry.get('candidates', []))}")
            print(f"\nFull entry:")
            print(json.dumps(entry, indent=2, ensure_ascii=False))
            exit(0)

print("No needs_review: true entries found")

