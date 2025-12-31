"""
手动解析模型信息的辅助脚本
用于帮助解析模型名称，提取家族、子家族、版本、日期、参数量等信息
"""

import re
import json
import csv
from pathlib import Path
from typing import Dict, Optional, List

# 已知的家族
FAMILIES = {
    'gpt', 'claude', 'gemini', 'grok', 'qwen', 'kimi', 'deepseek',
    'mistral', 'llama', 'glm', 'ernie', 'nova', 'granite', 'phi',
    'gemma', 'codestral', 'chatgpt', 'mimo', 'hunyuan', 'doubao',
    'apriel', 'kat', 'minimax', 'o1', 'o3', 'o4', 'o5', 'oss'
}

# 子家族后缀
SUBFAMILY_SUFFIXES = ['pro', 'preview', 'flash', 'heavy', 'r1', 'mini', 'max', 'turbo', 'nano', 'chat', 'codex', 'sonnet', 'opus', 'haiku', 'air', 'plus', 'lite', 'exp', 'terminus', 'vl', 'coder', 'next', 'thinking', 'fast', 'reasoning', 'experimental', 'advanced', 'standard', 'vision', 'turbos', 'large', 'small', 'medium', 'micro', 'premier', 'omni', 'special', 'speciale']

# 参数量模式（只匹配 20B, 1B 这样的格式，不包括 thinking-32k 和 A2B）
PARAM_PATTERN = re.compile(r'\b(\d+\.?\d*)\s*B\b', re.IGNORECASE)

# 日期模式（支持多种格式）
DATE_PATTERNS = [
    re.compile(r'(\d{4})-(\d{2})-(\d{2})'),  # 2025-02-27
    re.compile(r'(\d{4})(\d{2})(\d{2})'),    # 20251101
    re.compile(r'(\d{2})(\d{2})'),           # 1205, 2412
    re.compile(r'(dec|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov)', re.IGNORECASE),  # dec, jan
    re.compile(r'(\d{4})-(\d{2})'),         # 2025-02
]

# 版本号模式
VERSION_PATTERNS = [
    re.compile(r'v?(\d+\.\d+)'),            # v3.2, 3.2
    re.compile(r'v?(\d+)'),                 # v3, 3
]


def extract_family(name: str) -> Optional[str]:
    """提取家族"""
    name_lower = name.lower()
    
    # 特殊处理：o1, o3, o4, o5 是 GPT 家族
    if re.match(r'^o[1-5]', name_lower):
        return 'gpt'
    
    # 特殊处理：gpt-oss, oss 是 GPT 家族
    if 'oss' in name_lower and 'gpt' in name_lower:
        return 'gpt'
    
    # 检查已知家族
    for family in sorted(FAMILIES, key=len, reverse=True):
        if name_lower.startswith(family) or f'-{family}' in name_lower or f' {family}' in name_lower:
            return family
    
    return None


def extract_subfamily(name: str, family: Optional[str]) -> Optional[str]:
    """提取子家族"""
    name_lower = name.lower()
    
    # 如果家族是 gpt，o1/o3/o4/o5 的子家族就是 o1/o3/o4/o5
    if family == 'gpt':
        if re.match(r'^o[1-5]', name_lower):
            match = re.match(r'^(o[1-5])', name_lower)
            if match:
                return match.group(1)
    
    # 构建子家族：家族名 + 后缀
    subfamily_parts = []
    
    if family:
        # 查找家族名后的部分
        family_pattern = re.compile(f'{re.escape(family)}(?:-|\\s|$)', re.IGNORECASE)
        match = family_pattern.search(name_lower)
        if match:
            after_family = name_lower[match.end():]
            
            # 提取版本号之前的部分作为子家族
            version_match = re.search(r'v?\d+', after_family)
            if version_match:
                before_version = after_family[:version_match.start()].strip('-').strip()
                if before_version:
                    subfamily_parts.append(before_version)
            
            # 查找子家族后缀
            for suffix in SUBFAMILY_SUFFIXES:
                if f'-{suffix}' in after_family or f' {suffix}' in after_family:
                    if suffix not in subfamily_parts:
                        subfamily_parts.append(suffix)
    
    if subfamily_parts:
        return f"{family}-{'-'.join(subfamily_parts)}" if family else '-'.join(subfamily_parts)
    
    return None


def extract_version(name: str) -> Optional[str]:
    """提取版本号，统一为浮点数格式"""
    for pattern in VERSION_PATTERNS:
        match = pattern.search(name)
        if match:
            version_str = match.group(1)
            try:
                version_float = float(version_str)
                # 统一格式：如果是整数，显示为 3.0，否则保持原样
                if version_float == int(version_float):
                    return f"{int(version_float)}.0"
                else:
                    return str(version_float)
            except ValueError:
                return version_str
    return None


def extract_date(name: str) -> Optional[str]:
    """提取日期，保持原格式"""
    for pattern in DATE_PATTERNS:
        match = pattern.search(name)
        if match:
            if len(match.groups()) == 3:
                # YYYY-MM-DD 或 YYYYMMDD
                return match.group(0)
            elif len(match.groups()) == 2:
                # MM-DD 或 YYYY-MM
                return match.group(0)
            elif len(match.groups()) == 1:
                # dec, jan 等月份缩写，或 YYYY
                return match.group(1)
    return None


def extract_parameters(name: str) -> Optional[str]:
    """提取参数量（只匹配 20B, 1B 这样的格式）"""
    match = PARAM_PATTERN.search(name)
    if match:
        return match.group(0).upper()  # 统一为大写
    return None


def extract_other_info(name: str, family: Optional[str], subfamily: Optional[str], 
                      version: Optional[str], date: Optional[str], parameters: Optional[str]) -> List[str]:
    """提取其他信息（除了已提取的信息之外的所有内容）"""
    other_info = []
    name_lower = name.lower()
    
    # 移除已提取的信息
    remaining = name
    
    if family:
        # 移除家族名（但要保留子家族中的家族名）
        if subfamily and family in subfamily:
            # 如果子家族包含家族名，只移除独立的家族名
            pattern = re.compile(f'^{re.escape(family)}(?![a-z])', re.IGNORECASE)
            remaining = pattern.sub('', remaining).strip('-').strip()
        else:
            pattern = re.compile(f'^{re.escape(family)}(?![a-z])', re.IGNORECASE)
            remaining = pattern.sub('', remaining).strip('-').strip()
    
    if subfamily:
        # 移除子家族（但要小心，因为子家族可能包含家族名）
        subfamily_parts = subfamily.split('-')
        for part in subfamily_parts:
            if part != family:  # 不重复移除家族名
                pattern = re.compile(f'-?{re.escape(part)}(?![a-z])', re.IGNORECASE)
                remaining = pattern.sub('', remaining).strip('-').strip()
    
    if version:
        # 移除版本号
        version_clean = version.replace('.0', '').replace('.', r'\.')
        pattern = re.compile(f'v?{re.escape(version_clean)}(?![0-9])', re.IGNORECASE)
        remaining = pattern.sub('', remaining).strip('-').strip()
    
    if date:
        # 移除日期
        pattern = re.compile(re.escape(date), re.IGNORECASE)
        remaining = pattern.sub('', remaining).strip('-').strip()
    
    if parameters:
        # 移除参数量
        pattern = re.compile(re.escape(parameters), re.IGNORECASE)
        remaining = pattern.sub('', remaining).strip('-').strip()
    
    # 提取剩余的信息
    if remaining:
        # 分割剩余部分
        parts = re.split(r'[-_\s()]+', remaining)
        for part in parts:
            part = part.strip()
            if part and part.lower() not in ['thinking', '32k', '16k', 'non']:  # 排除一些常见但不算其他信息的词
                # 检查是否是参数量格式（但之前没匹配到的）
                if not PARAM_PATTERN.match(part):
                    other_info.append(part)
    
    return other_info if other_info else None


def parse_model_name(model_name: str) -> Dict:
    """解析模型名称，返回结构化信息"""
    family = extract_family(model_name)
    subfamily = extract_subfamily(model_name, family)
    version = extract_version(model_name)
    date = extract_date(model_name)
    parameters = extract_parameters(model_name)
    other_info = extract_other_info(model_name, family, subfamily, version, date, parameters)
    
    return {
        'family': family,
        'subfamily': subfamily,
        'version': version,
        'date': date,
        'parameters': parameters,
        'other_info': other_info
    }


def process_lmarena_overall():
    """处理 LMArena Overall，只保留 Score >= 1330 的模型"""
    base_dir = Path(__file__).parent.parent.parent
    csv_file = base_dir / 'data' / 'raw' / 'lmarena' / 'Overall' / 'data.csv'
    output_file = base_dir / 'data' / 'processed' / 'model_extraction' / 'lmarena_models.json'
    
    models = {}
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            model_name = row['Model']
            try:
                score = float(row['Score'].replace('Preliminary', ''))
            except ValueError:
                continue
            
            # 只保留 Score >= 1330 的模型
            if score >= 1330:
                parsed = parse_model_name(model_name)
                models[model_name] = parsed
    
    # 保存 JSON
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(models, f, indent=2, ensure_ascii=False)
    
    print(f"处理了 {len(models)} 个 LMArena 模型（Score >= 1330）")
    return models


if __name__ == '__main__':
    process_lmarena_overall()

