import json
import os

file_path = r"d:\桌面 2026.1.13\科研\Human-SIG\Human-SIG\new\metadata_new.json"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"Error: File not found at {file_path}")
    exit(1)

# Update meta_info
if len(data) > 0 and 'meta_info' in data[0]:
    meta_info = data[0]['meta_info']
    if 'prompt_length_standards' in meta_info:
        del meta_info['prompt_length_standards']

    meta_info['complexity_definitions'] = {
        "Applying": "在具体的、通常是情境化的任务中执行程序、遵循明确的规则或运用已知算法解决常规问题。",
        "Analyzing": "将庞杂的信息分解为构成要素，梳理其内在的逻辑联系，寻找隐藏的模式，或应对高度抽象的推理问题。",
        "Evaluating": "基于复杂的标准、深度的专业知识或逻辑自洽性，对信息进行批判性判断、鉴别真伪。",
        "Creating": "整合各种元素或知识，生成全新的架构、代码工程补丁或富有创意的作品。这是认知的最高境界。"
    }

# Complexity Mapping
complexity_mapping = {
    "Applying": [
        "IFEval", "IFBench", "MGSM", "MATH-500", "HumanEval", 
        "Aider Polyglot", "LiveCodeBench", "Terminal-Bench Hard", "Terminal-Bench v2.0"
    ],
    "Analyzing": [
        "AA-LCR", "ARC-AGI-2", "AIME", "HMMT (Feb 2025)", 
        "FrontierMath Tier 1-3", "FrontierMath Tier 4", "IOI"
    ],
    "Evaluating": [
        "GPQA", "GPQA Diamond", "SuperGPQA", "Humanity's Last Exam", 
        "MMLU-Pro", "FACTS"
    ],
    "Creating": [
        "SWE-bench (Verified)", "SWE-bench Bash Only", "SciCode", 
        "tau2-Bench Telecom", "Creative Writing v3", "WritingBench"
    ]
}

# Create a reverse mapping for O(1) lookup
benchmark_to_complexity = {}
for complexity, benchmarks in complexity_mapping.items():
    for bm in benchmarks:
        benchmark_to_complexity[bm] = complexity

# Update benchmarks
updated_benchmarks = []
not_mapped = []

for item in data:
    if 'benchmark_id' in item:
        bm_id = item['benchmark_id']
        
        # Skip LMArena categories if they are in the list (usually at the end)
        if bm_id.startswith('LMArena-'):
            continue
            
        # Remove prompt_length if it exists
        if 'prompt_length' in item:
            del item['prompt_length']
            
        # Add complexity
        if bm_id in benchmark_to_complexity:
            item['complexity'] = benchmark_to_complexity[bm_id]
            updated_benchmarks.append(bm_id)
        else:
            not_mapped.append(bm_id)
            print(f"Warning: No complexity mapping found for {bm_id}")

print(f"Updated {len(updated_benchmarks)} benchmarks with complexity.")
if not_mapped:
    print(f"Benchmarks not mapped: {not_mapped}")

# Save the updated JSON
with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Successfully saved updated metadata to {file_path}")
