"""
第二步：从 cleaned_data 生成 review_files（不确定性）

输入：data/processed/cleaned/{benchmark_id}/cleaned_data.csv
输出：data/processed/review_files/{benchmark_id}_review.json

功能：
1. 从 LMArena raw data 生成 lmarena_models.json（如果不存在）
2. 从 cleaned_data.csv 读取模型名称
3. 解析模型信息（家族、子家族、版本等）
4. 加载 LMArena 模型信息
5. 匹配候选并自动选择最佳匹配
6. 生成 review_files（包含 untrusted 字段，默认 1）

注意：本文件包含所有必要的工具函数，无需导入其他模块即可运行
"""

import json
import csv
import re
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Set


# ============================================================================
# 模型信息解析模块
# 用于从模型名称中提取家族、子家族、版本、日期、参数量等信息
# ============================================================================

# 已知的模型家族
FAMILIES = {
    'gpt', 'claude', 'gemini', 'grok', 'qwen', 'kimi', 'deepseek',
    'mistral', 'llama', 'glm', 'ernie', 'nova', 'granite', 'phi',
    'gemma', 'codestral', 'chatgpt', 'mimo', 'hunyuan', 'doubao',
    'apriel', 'kat', 'minimax', 'oss', 'yi', 'command', 'stepfun',
    'ling', 'ring', 'longcat', 'mai', 'intellect', 'cohere', 'tencent',
    'nvidia', 'meta', 'amazon', 'minimax', 'moonshot', 'z', 'zhipu',
    'baidu', 'alibaba', 'xiaomi', 'meituan', 'ant', 'inclusion', '01',
    'snowflake', 'databricks', 'mosaic', 'tii', 'internlm', 'microsoft',
    'azure', 'nexusflow', 'lmsys', 'allen', 'ai21', 'ibm', 'reka',
    'upstage', 'cognitive', 'nous', 'openchat', 'huggingface', 'rwkv',
    'openassistant', 'stability', 'nomic', 'princeton', 'stanford',
    'uc', 'uw', 'together', 'liquid', 'lg', 'naver', 'service', 'now',
    'kwai', 'korea', 'telecom', 'mbzuai', 'perplexity', 'motif',
    'inception', 'deep', 'cogito', 'prime'
}

# 子家族后缀（如 pro, preview, flash 等）
SUBFAMILY_SUFFIXES = ['pro', 'preview', 'flash', 'heavy', 'r1', 'mini', 'max', 
                      'turbo', 'nano', 'chat', 'codex', 'sonnet', 'opus', 'haiku', 
                      'air', 'plus', 'lite', 'exp', 'terminus', 'vl', 'coder', 
                      'next', 'thinking', 'fast', 'reasoning', 'experimental', 
                      'advanced', 'standard', 'vision', 'turbos', 'large', 'small', 
                      'medium', 'micro', 'premier', 'omni', 'special', 'speciale',
                      'instruct', 'base', 'dev', 'webapp', 'deep', 'think', 'beta',
                      'alpha', 'lightning', 'maverick', 'scout', 'nemotron', 'super',
                      'ultra', 'nano', 'h', 'granite', 'arctic', 'jamba', 'hermes',
                      'tulu', 'vicuna', 'starling', 'guanaco', 'dolphin', 'solar',
                      'mpt', 'falcon', 'wizardlm', 'openhermes', 'zephyr', 'smollm',
                      'stripedhyena', 'codellama', 'chatglm', 'oasst', 'pythia',
                      'dolly', 'stablelm', 'koala', 'alpaca', 'gpt4all', 'snoozy']

# 参数量模式（只匹配 20B, 1B 这样的格式，不包括 thinking-32k 和 A2B）
PARAM_PATTERN = re.compile(r'\b(\d+\.?\d*)\s*B\b', re.IGNORECASE)

# 日期模式
DATE_PATTERNS = [
    re.compile(r'(\d{4})-(\d{2})-(\d{2})'),  # 2025-02-27
    re.compile(r'(\d{4})(\d{2})(\d{2})'),    # 20251101
    re.compile(r'(\d{2})(\d{2})'),           # 1205, 2412
    re.compile(r'(dec|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov)', re.IGNORECASE),  # dec, jan
]

# 版本号模式
VERSION_PATTERNS = [
    re.compile(r'v?(\d+\.\d+)'),      # v3.5, 3.5
    re.compile(r'v?(\d+)'),           # v3, 3
]


def extract_family(name: str) -> Optional[str]:
    """
    提取模型家族名称
    
    处理各种特殊情况：
    - 组织名和模型名连在一起（如 Anthropicclaude -> claude）
    - 特殊模型系列（如 o1, o3, o4, o5 -> gpt 家族）
    - 前缀处理（如 google/gemini-3-pro -> gemini）
    """
    name_lower = name.lower()
    
    # 移除常见前缀
    if name_lower.startswith(('google/', 'openai/', 'anthropic/', 'ai21labs/', 'fireworks/')):
        name_lower = name_lower.split('/', 1)[1]
    
    # 处理组织名和模型名连在一起的情况
    replacements = {
        'anthropicclaude': 'claude',
        'moonshotaikimi': 'kimi',
        'moonshot aikimi': 'kimi',
        'minimaxminimax': 'minimax',
        'nvidiallama': 'llama',
        'metallama': 'llama',
        'tencenthunyuan': 'hunyuan',
        '01.aiyi': 'yi',
        '01 aiyi': 'yi',
        'coherecommand': 'command',
        'stepfunstep': 'stepfun',
        'snowflakesnowflake': 'snowflake',
        'openchatopenchat': 'openchat',
        'internlminternlm': 'internlm',
        'huggingfacezephyr': 'zephyr',
        'metacodellama': 'llama',
    }
    for old, new in replacements.items():
        name_lower = name_lower.replace(old, new)
    
    # 特殊处理：qwq 是 qwen 的变体
    if name_lower.startswith('qwq') or re.search(r'\bqwq\b', name_lower):
        return 'qwen'
    
    # 特殊处理：Magistral, Devstral, Ministral, Mixtral 是 Mistral 的产品线
    if any(x in name_lower for x in ['magistral', 'devstral', 'ministral', 'mixtral']):
        return 'mistral'
    
    # 特殊处理：Terminus 是 DeepSeek 的模型
    if 'terminus' in name_lower:
        return 'deepseek'
    
    # 特殊处理：Hermes, Nemotron 可能是 llama 家族的变体
    if 'hermes' in name_lower or ('nemotron' in name_lower and 'llama' in name_lower):
        return 'llama'
    if 'nemotron' in name_lower:
        return 'llama'  # 假设是 llama 家族
    
    # 特殊处理：Opus 单独出现时，可能是 Claude Opus
    if name_lower.startswith('opus') or (name_lower.startswith('opus ') and 'claude' not in name_lower):
        return 'claude'
    
    # 特殊处理：处理斜杠分隔的模型名（如 Qwen3-Coder 480B/A35B）
    if '/' in name_lower and name_lower.count('/') == 1 and not name_lower.startswith(('google/', 'openai/', 'anthropic/', 'ai21labs/', 'fireworks/')):
        parts = name_lower.split('/')
        if len(parts) == 2:
            first_part = parts[0]
            for family in sorted(FAMILIES, key=len, reverse=True):
                if family in first_part:
                    return family
    
    # 特殊处理：o1, o3, o4, o5 是 GPT 家族
    if re.match(r'^o[1-5]', name_lower) or re.search(r'\bo[1-5](?:-|$)', name_lower):
        return 'gpt'
    
    # 特殊处理：gpt-oss, oss 是 GPT 家族
    if 'oss' in name_lower and ('gpt' in name_lower or name_lower.startswith('oss')):
        return 'gpt'
    
    # 检查已知家族（按长度降序，优先匹配更长的）
    for family in sorted(FAMILIES, key=len, reverse=True):
        if name_lower.startswith(family) or f'-{family}' in name_lower or f' {family}' in name_lower:
            return family
    
    return None


def extract_subfamily(name: str, family: Optional[str]) -> Optional[str]:
    """
    提取子家族名称
    
    子家族包括家族名后的后缀（如 pro, preview, flash 等）
    例如：gpt-5-pro -> gpt-5-pro, gemini-pro -> gemini-pro
    """
    name_lower = name.lower()
    
    # 如果家族是 gpt，o1/o3/o4/o5 的子家族就是 o1/o3/o4/o5
    if family == 'gpt':
        o_match = re.search(r'\b(o[1-5])(?:-|$)', name_lower)
        if o_match:
            return o_match.group(1)
    
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
    """
    提取版本号，统一为浮点数格式（如 3.0）
    
    例如：v3 -> 3.0, 3.5 -> 3.5, v3.5 -> 3.5
    """
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
    """
    提取日期信息
    
    支持格式：
    - 2025-02-27
    - 20251101
    - 1205, 2412
    - dec, jan 等月份缩写
    """
    for pattern in DATE_PATTERNS:
        match = pattern.search(name)
        if match:
            if len(match.groups()) == 3:
                # 2025-02-27 或 20251101
                return match.group(0)
            elif len(match.groups()) == 2:
                # 1205, 2412
                return match.group(0)
            else:
                # dec, jan
                return match.group(0).lower()
    return None


def extract_parameters(name: str) -> Optional[str]:
    """
    提取参数量（只匹配 20B, 1B 这样的格式）
    
    排除 thinking-32k 和 A2B 这样的格式
    """
    match = PARAM_PATTERN.search(name)
    if match:
        param_str = match.group(0)
        # 排除 thinking-32k 中的 32k
        if 'thinking-32k' in name.lower() and '32k' in param_str.lower():
            return None
        return param_str
    return None


def extract_other_info(name: str, family: Optional[str], subfamily: Optional[str], 
                       version: Optional[str], date: Optional[str], parameters: Optional[str]) -> Optional[List[str]]:
    """
    提取其他信息（剩余的所有信息）
    
    从模型名称中移除已提取的家族、子家族、版本、日期、参数量后，
    剩余的部分作为 other_info
    """
    other_info = []
    remaining = name
    
    # 移除已提取的信息
    if family:
        pattern = re.compile(f'^{re.escape(family)}(?![a-z])', re.IGNORECASE)
        remaining = pattern.sub('', remaining).strip('-').strip()
    
    if subfamily:
        subfamily_parts = subfamily.split('-')
        for part in subfamily_parts:
            if part != family:  # 不重复移除家族名
                pattern = re.compile(f'-?{re.escape(part)}(?![a-z])', re.IGNORECASE)
                remaining = pattern.sub('', remaining).strip('-').strip()
    
    if version:
        version_clean = version.replace('.0', '').replace('.', r'\.')
        pattern = re.compile(f'v?{re.escape(version_clean)}(?![0-9])', re.IGNORECASE)
        remaining = pattern.sub('', remaining).strip('-').strip()
    
    if date:
        pattern = re.compile(re.escape(date), re.IGNORECASE)
        remaining = pattern.sub('', remaining).strip('-').strip()
    
    if parameters:
        pattern = re.compile(re.escape(parameters), re.IGNORECASE)
        remaining = pattern.sub('', remaining).strip('-').strip()
    
    # 提取剩余的信息
    if remaining:
        parts = re.split(r'[-_\s()]+', remaining)
        for part in parts:
            part = part.strip()
            if part and part.lower() not in ['thinking', '32k', '16k', 'non']:
                # 检查是否是参数量格式（但之前没匹配到的）
                if not PARAM_PATTERN.match(part):
                    other_info.append(part)
    
    return other_info if other_info else None


def parse_model_name(model_name: str) -> Dict:
    """
    解析模型名称，返回结构化信息
    
    返回字典包含：
    - family: 家族名称（如 'gpt', 'gemini', 'claude'）
    - subfamily: 子家族名称（如 'gpt-5-pro', 'gemini-pro'）
    - version: 版本号（统一为浮点数格式，如 '3.0'）
    - date: 日期信息（如 '2025-04-16', 'dec'）
    - parameters: 参数量（如 '20B', '1B'）
    - other_info: 其他信息列表
    """
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


# ============================================================================
# 结构化匹配器和相似度计算模块
# 用于匹配 benchmark 模型和 LMArena 模型，并选择最佳候选
# ============================================================================

class StructuredMatcher:
    """
    基于结构化信息的匹配器
    
    用于判断两个模型信息是否可以匹配，匹配规则：
    1. 家族必须一致
    2. 子家族必须一致（如果都有）
    3. 版本号必须一致（标准化后比较）
    4. 参数量如果都有且不一致，排除匹配
    5. 日期不参与筛选
    """
    
    def _normalize_version(self, version: Optional[str]) -> Optional[str]:
        """
        标准化版本号：3和3.0视为相同，统一为浮点数格式（如3.0）
        """
        if version is None:
            return None
        
        try:
            version_float = float(version)
            if version_float == int(version_float):
                return f"{int(version_float)}.0"
            else:
                return str(version_float)
        except (ValueError, TypeError):
            return version
    
    def can_match(self, info1: Dict, info2: Dict) -> bool:
        """
        判断两个模型信息是否可以匹配
        
        规则：
        1. 家族必须一致
        2. 子家族必须一致（如果都有）
        3. 版本号必须一致（会标准化：3和3.0视为相同）
        4. 参数量如果都有且不一致，则排除匹配
        5. 日期不参与筛选
        """
        # 规则1: 家族必须一致
        if info1.get('family') != info2.get('family'):
            return False
        
        # 规则2: 子家族必须一致（如果都有）
        subfamily1 = info1.get('subfamily')
        subfamily2 = info2.get('subfamily')
        
        if subfamily1 is not None and subfamily2 is not None:
            if subfamily1 != subfamily2:
                return False
        
        if (subfamily1 is None) != (subfamily2 is None):
            return False
        
        # 规则3: 版本号必须一致（标准化后比较）
        version1 = self._normalize_version(info1.get('version'))
        version2 = self._normalize_version(info2.get('version'))
        
        if version1 is not None and version2 is not None:
            if version1 != version2:
                return False
        
        if (version1 is None) != (version2 is None):
            return False
        
        # 规则4: 参数量如果都有且不一致，排除匹配
        param1 = info1.get('parameters')
        param2 = info2.get('parameters')
        
        if param1 is not None and param2 is not None:
            if param1 != param2:
                return False
        
        return True


def normalize_other_info(other_info: Optional[List[str]]) -> Set[str]:
    """
    标准化 other_info，用于比较
    
    将列表转换为小写字符串的集合，便于计算相似度
    """
    if not other_info:
        return set()
    return set(item.lower().strip() for item in other_info if item)


def calculate_similarity(info1: Dict, info2: Dict) -> float:
    """
    计算两个模型信息的相似度分数（0-1）
    
    考虑因素及权重：
    1. other_info 的相似度（50%）- 使用 Jaccard 相似度
    2. 日期是否匹配（20%）
    3. 参数量是否匹配（20%）
    4. 子家族是否完全匹配（10%）
    """
    score = 0.0
    weights = {
        'other_info': 0.5,
        'date': 0.2,
        'parameters': 0.2,
        'subfamily': 0.1
    }
    
    # 1. other_info 相似度（Jaccard 相似度）
    other1 = normalize_other_info(info1.get('other_info'))
    other2 = normalize_other_info(info2.get('other_info'))
    
    if other1 or other2:
        if other1 and other2:
            intersection = len(other1 & other2)
            union = len(other1 | other2)
            other_sim = intersection / union if union > 0 else 0.0
        else:
            other_sim = 0.1
    else:
        other_sim = 0.8
    
    score += weights['other_info'] * other_sim
    
    # 2. 日期匹配
    date1 = info1.get('date')
    date2 = info2.get('date')
    if date1 and date2:
        if date1 == date2:
            score += weights['date'] * 1.0
        else:
            # 年份相同给部分分数
            if str(date1)[:4] == str(date2)[:4]:
                score += weights['date'] * 0.5
    elif not date1 and not date2:
        pass  # 都没有日期，不给分也不扣分
    else:
        score += weights['date'] * 0.2  # 一个有日期一个没有，给少量分数
    
    # 3. 参数量匹配
    param1 = info1.get('parameters')
    param2 = info2.get('parameters')
    if param1 and param2:
        if param1 == param2:
            score += weights['parameters'] * 1.0
        else:
            score += weights['parameters'] * 0.0  # 不一致，不给分
    elif not param1 and not param2:
        pass  # 都没有参数量，不给分也不扣分
    else:
        score += weights['parameters'] * 0.3  # 一个有参数量一个没有，给少量分数
    
    # 4. 子家族匹配
    subfamily1 = info1.get('subfamily')
    subfamily2 = info2.get('subfamily')
    if subfamily1 and subfamily2:
        if subfamily1 == subfamily2:
            score += weights['subfamily'] * 1.0
        else:
            # 部分匹配（一个包含另一个）
            if subfamily1 in subfamily2 or subfamily2 in subfamily1:
                score += weights['subfamily'] * 0.5
    elif not subfamily1 and not subfamily2:
        pass  # 都没有子家族，不给分也不扣分
    else:
        score += weights['subfamily'] * 0.2  # 一个有子家族一个没有，给少量分数
    
    return min(score, 1.0)


def select_best_candidate(benchmark_info: Dict, candidates: List[Dict]) -> Optional[str]:
    """
    从多个候选中选择最佳匹配
    
    算法：
    1. 过滤掉 NO_MATCH_FOUND
    2. 如果只有一个候选，直接返回
    3. 如果有多个候选，计算每个候选的相似度分数
    4. 选择相似度最高的候选（如果相似度 >= 0.3）
    
    返回: 选中的 lmarena_model 名称，如果没有合适的则返回 None
    """
    if not candidates:
        return None
    
    valid_candidates = [c for c in candidates if c.get('lmarena_model') != 'NO_MATCH_FOUND']
    
    if not valid_candidates:
        return None
    
    if len(valid_candidates) == 1:
        return valid_candidates[0].get('lmarena_model')
    
    # 多个候选，计算相似度并选择最佳
    scored_candidates = []
    for candidate in valid_candidates:
        similarity = calculate_similarity(benchmark_info, candidate)
        scored_candidates.append((similarity, candidate))
    
    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    
    # 选择相似度最高的
    best_similarity, best_candidate = scored_candidates[0]
    
    # 如果相似度太低，返回 None
    if best_similarity < 0.3:
        return None
    
    return best_candidate.get('lmarena_model')


# ============================================================================
# 主处理函数
# ============================================================================

def generate_lmarena_extraction(
    raw_csv_path: Path,
    output_file: Path,
    score_threshold: float = 1330.0
) -> Dict[str, Dict]:
    """
    从 LMArena raw data 生成 extraction 文件
    
    只保留 Score >= score_threshold 的模型
    """
    print(f"\n生成 LMArena extraction 文件...")
    print(f"  从 {raw_csv_path} 读取数据")
    print(f"  分数阈值: >= {score_threshold}")
    
    # 读取 raw CSV
    df = None
    for encoding in ['utf-8', 'gbk', 'latin-1', 'cp1252']:
        try:
            df = pd.read_csv(raw_csv_path, encoding=encoding)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if df is None:
        print(f"  错误: 无法读取 CSV 文件")
        return {}
    
    # 找到模型列和分数列
    model_col = None
    score_col = None
    
    if 'Model' in df.columns:
        model_col = 'Model'
    elif 'model' in df.columns:
        model_col = 'model'
    
    if 'Score' in df.columns:
        score_col = 'Score'
    elif 'score' in df.columns:
        score_col = 'score'
    
    if model_col is None or score_col is None:
        print(f"  错误: 未找到模型列或分数列")
        return {}
    
    # 提取模型信息
    lmarena_models = {}
    for _, row in df.iterrows():
        model_name = str(row[model_col]).strip()
        score_value = row[score_col]
        
        # 处理分数（移除 ± 误差部分）
        try:
            score_str = str(score_value).strip()
            # 移除 "Preliminary" 后缀
            score_str = score_str.replace('Preliminary', '').strip()
            # 移除 ± 及其后面的内容
            if '±' in score_str:
                score_str = score_str.split('±')[0].strip()
            score = float(score_str)
        except (ValueError, TypeError):
            continue
        
        # 只保留 Score >= threshold 的模型
        if score < score_threshold:
            continue
        
        # 解析模型信息
        try:
            parsed_info = parse_model_name(model_name)
            lmarena_models[model_name] = parsed_info
        except Exception as e:
            print(f"  警告: 解析模型名称失败 {model_name}: {e}")
            # 即使解析失败，也创建一个基本结构
            lmarena_models[model_name] = {
                'family': None,
                'subfamily': None,
                'version': None,
                'date': None,
                'parameters': None,
                'other_info': None
            }
    
    # 保存到文件
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(lmarena_models, f, indent=2, ensure_ascii=False)
    
    print(f"  已生成: {output_file}")
    print(f"  包含 {len(lmarena_models)} 个模型（Score >= {score_threshold}）")
    
    return lmarena_models


def load_lmarena_models(lmarena_file: Path, raw_csv_path: Path) -> Dict[str, Dict]:
    """
    加载 LMArena 模型信息
    
    如果文件不存在，从 raw data 生成
    """
    if lmarena_file.exists():
        try:
            with open(lmarena_file, 'r', encoding='utf-8') as f:
                models = json.load(f)
            print(f"  从 {lmarena_file.name} 加载了 {len(models)} 个 LMArena 模型")
            return models
        except Exception as e:
            print(f"  警告: 无法读取 LMArena 模型文件: {e}")
            print(f"  将重新生成...")
    
    # 文件不存在或读取失败，从 raw data 生成
    return generate_lmarena_extraction(raw_csv_path, lmarena_file)


def load_benchmark_models(cleaned_csv_path: Path) -> List[str]:
    """从 cleaned_data.csv 读取模型名称列表"""
    models = []
    with open(cleaned_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            models.append(row['model_name'])
    return models


def process_benchmark(
    benchmark_id: str,
    cleaned_csv_path: Path,
    lmarena_models: Dict[str, Dict],
    output_file: Path
):
    """处理单个 benchmark，生成 review_file"""
    print(f"\n处理: {benchmark_id}")
    
    # 从 cleaned_data.csv 读取模型名称
    benchmark_model_names = load_benchmark_models(cleaned_csv_path)
    print(f"  从 cleaned_data.csv 读取了 {len(benchmark_model_names)} 个模型")
    
    # 解析每个模型的信息
    benchmark_models_info = {}
    for model_name in benchmark_model_names:
        try:
            parsed_info = parse_model_name(model_name)
            benchmark_models_info[model_name] = parsed_info
        except Exception as e:
            print(f"  警告: 解析模型名称失败 {model_name}: {e}")
            # 即使解析失败，也创建一个基本结构
            benchmark_models_info[model_name] = {
                'family': None,
                'subfamily': None,
                'version': None,
                'date': None,
                'parameters': None,
                'other_info': None
            }
    
    # 匹配候选并自动选择
    matcher = StructuredMatcher()
    review_data = {}
    
    for benchmark_model, benchmark_info in benchmark_models_info.items():
        # 找到所有可能匹配的 LMArena 模型
        candidates = []
        
        for lmarena_model, lmarena_info in lmarena_models.items():
            if matcher.can_match(benchmark_info, lmarena_info):
                candidate_info = {
                    'lmarena_model': lmarena_model,
                    'family': lmarena_info.get('family'),
                    'subfamily': lmarena_info.get('subfamily'),
                    'version': lmarena_info.get('version'),
                    'date': lmarena_info.get('date'),
                    'parameters': lmarena_info.get('parameters'),
                    'other_info': lmarena_info.get('other_info'),
                }
                candidates.append(candidate_info)
        
        # 如果没有候选，添加 NO_MATCH_FOUND
        if not candidates:
            candidates = [{'lmarena_model': 'NO_MATCH_FOUND'}]
        
        # 自动选择最佳匹配
        valid_candidates = [c for c in candidates if c.get('lmarena_model') != 'NO_MATCH_FOUND']
        
        if not valid_candidates:
            selected_lmarena_model = 0
        elif len(valid_candidates) == 1:
            selected_lmarena_model = valid_candidates[0].get('lmarena_model')
        else:
            # 多个候选，使用相似度算法选择
            selected = select_best_candidate(benchmark_info, valid_candidates)
            selected_lmarena_model = selected if selected else 0
        
        # 构建 review 条目
        review_data[benchmark_model] = {
            'benchmark_info': {
                'family': benchmark_info.get('family'),
                'subfamily': benchmark_info.get('subfamily'),
                'version': benchmark_info.get('version'),
                'date': benchmark_info.get('date'),
                'parameters': benchmark_info.get('parameters'),
                'other_info': benchmark_info.get('other_info'),
            },
            'candidates': candidates,
            'untrusted': 1,  # 默认不可信（由 agent 完成）
            'selected_lmarena_model': selected_lmarena_model
        }
    
    # 写入 JSON 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(review_data, f, indent=2, ensure_ascii=False)
    
    # 统计信息
    total_models = len(review_data)
    matched_count = sum(1 for data in review_data.values() 
                        if isinstance(data.get('selected_lmarena_model'), str))
    no_match_count = sum(1 for data in review_data.values() 
                        if data.get('selected_lmarena_model') == 0)
    multi_candidates_count = sum(1 for data in review_data.values() 
                                 if len([c for c in data.get('candidates', []) 
                                        if c.get('lmarena_model') != 'NO_MATCH_FOUND']) > 1)
    
    print(f"  已生成: {output_file.name}")
    print(f"    总模型数: {total_models}")
    print(f"    已匹配: {matched_count}")
    print(f"    未匹配: {no_match_count}")
    print(f"    多候选: {multi_candidates_count}")


def main():
    """主函数"""
    base_dir = Path(__file__).parent.parent.parent
    raw_dir = base_dir / 'data' / 'raw'
    cleaned_dir = base_dir / 'data' / 'processed' / 'cleaned'
    model_extraction_dir = base_dir / 'data' / 'processed' / 'model_extraction'
    review_files_dir = base_dir / 'data' / 'processed' / 'review_files'
    
    # 创建输出目录
    review_files_dir.mkdir(parents=True, exist_ok=True)
    model_extraction_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载或生成 LMArena 模型信息
    lmarena_file = model_extraction_dir / 'lmarena_models.json'
    lmarena_raw_csv = raw_dir / 'lmarena' / 'Overall' / 'data.csv'
    
    print("=" * 60)
    print("加载 LMArena 模型信息...")
    lmarena_models = load_lmarena_models(lmarena_file, lmarena_raw_csv)
    
    if not lmarena_models:
        print("错误: 无法加载或生成 LMArena 模型信息，脚本无法继续")
        return
    
    print(f"共 {len(lmarena_models)} 个 LMArena 模型可用于匹配")
    print("=" * 60)
    
    # 查找所有 cleaned_data.csv 文件
    cleaned_csv_files = list(cleaned_dir.rglob('cleaned_data.csv'))
    print(f"\n找到 {len(cleaned_csv_files)} 个 cleaned_data.csv 文件")
    
    # 处理每个 benchmark（排除 LMArena）
    for cleaned_csv_path in sorted(cleaned_csv_files):
        benchmark_id = cleaned_csv_path.parent.name
        
        # 跳过 LMArena（因为 LMArena 内部肯定可以匹配）
        if benchmark_id.startswith('lmarena_'):
            print(f"\n跳过 LMArena: {benchmark_id}")
            continue
        
        output_file = review_files_dir / f'{benchmark_id}_review.json'
        
        process_benchmark(
            benchmark_id,
            cleaned_csv_path,
            lmarena_models,
            output_file
        )
    
    print("\n完成！")


if __name__ == '__main__':
    main()
