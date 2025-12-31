"""
通用模型信息解析模块
用于从模型名称中提取家族、子家族、版本、日期、参数量等信息
"""

import re
from typing import Dict, Optional, List

# 已知的家族
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

# 子家族后缀
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
    re.compile(r'(\d{4})-(\d{2})'),          # 2025-02
    re.compile(r'(\d{4})'),                  # 2025
]

# 版本号模式
VERSION_PATTERNS = [
    re.compile(r'v?(\d+\.\d+)'),            # v3.2, 3.2
    re.compile(r'v?(\d+)'),                 # v3, 3
]


def extract_family(name: str) -> Optional[str]:
    """提取家族"""
    # 先处理带前缀的情况（如 google/gemini-3-pro-preview, ai21labs/jamba-large-1.6）
    # 注意：只处理开头的前缀（如 google/xxx），不处理模型名内部的斜杠（如 Qwen3-Coder 480B/A35B）
    if '/' in name and (name.startswith(('google/', 'openai/', 'anthropic/', 'ai21labs/', 'fireworks/', 'anthropic/')) or 
                        name.split('/', 1)[0].lower() in ['google', 'openai', 'anthropic', 'ai21labs', 'fireworks']):
        parts = name.split('/', 1)
        if len(parts) == 2:
            prefix = parts[0].lower()
            name = parts[1]  # 使用前缀后的部分
            # 特殊处理：ai21labs/jamba -> jamba（不在已知家族中，但可以识别）
            if prefix == 'ai21labs' and 'jamba' in name.lower():
                return None  # jamba 不在已知家族中
    
    name_lower = name.lower()
    
    # 处理模型名内部的斜杠（如 Qwen3-Coder 480B/A35B），取第一部分
    if '/' in name_lower and not name_lower.startswith(('google/', 'openai/', 'anthropic/', 'ai21labs/', 'fireworks/')):
        parts = name_lower.split('/', 1)
        if len(parts) == 2:
            # 检查第一部分是否包含家族
            first_part = parts[0]
            for family in sorted(FAMILIES, key=len, reverse=True):
                if family in first_part:
                    name_lower = first_part  # 使用第一部分继续处理
                    break
    
    # 特殊处理：组织名和模型名连在一起的情况
    # Anthropicclaude -> claude
    if 'anthropicclaude' in name_lower or name_lower.startswith('anthropicclaude'):
        name_lower = name_lower.replace('anthropicclaude', 'claude')
    # MoonshotAIkimi -> kimi
    if 'moonshotaikimi' in name_lower:
        name_lower = name_lower.replace('moonshotaikimi', 'kimi')
    # 处理 MoonshotAIkimi-k2-xxx 格式
    if name_lower.startswith('moonshotaikimi'):
        name_lower = 'kimi' + name_lower[len('moonshotaikimi'):]
    if 'moonshot aikimi' in name_lower or 'moonshot aikimi' in name_lower:
        name_lower = name_lower.replace('moonshot aikimi', 'kimi').replace('moonshotaikimi', 'kimi')
    # Minimaxminimax -> minimax
    if 'minimaxminimax' in name_lower:
        name_lower = name_lower.replace('minimaxminimax', 'minimax')
    # Nvidiallama -> llama
    if 'nvidiallama' in name_lower:
        name_lower = name_lower.replace('nvidiallama', 'llama')
    # Metallama -> llama
    if 'metallama' in name_lower:
        name_lower = name_lower.replace('metallama', 'llama')
    # Tencenthunyuan -> hunyuan
    if 'tencenthunyuan' in name_lower:
        name_lower = name_lower.replace('tencenthunyuan', 'hunyuan')
    # 01.AIyi -> yi
    if '01.aiyi' in name_lower or '01 aiyi' in name_lower:
        name_lower = name_lower.replace('01.aiyi', 'yi').replace('01 aiyi', 'yi')
    # Coherecommand -> command
    if 'coherecommand' in name_lower:
        name_lower = name_lower.replace('coherecommand', 'command')
    # Stepfunstep -> stepfun
    if 'stepfunstep' in name_lower:
        name_lower = name_lower.replace('stepfunstep', 'stepfun')
    # Snowflakesnowflake -> snowflake
    if 'snowflakesnowflake' in name_lower:
        name_lower = name_lower.replace('snowflakesnowflake', 'snowflake')
    # OpenChatopenchat -> openchat
    if 'openchatopenchat' in name_lower:
        name_lower = name_lower.replace('openchatopenchat', 'openchat')
    # InternLMinternlm -> internlm
    if 'internlminternlm' in name_lower:
        name_lower = name_lower.replace('internlminternlm', 'internlm')
    # HuggingFacezephyr -> zephyr (但zephyr不是家族，需要特殊处理)
    if 'huggingfacezephyr' in name_lower:
        name_lower = name_lower.replace('huggingfacezephyr', 'zephyr')
    # Metacodellama -> llama
    if 'metacodellama' in name_lower:
        name_lower = name_lower.replace('metacodellama', 'llama')
    
    # 特殊处理：qwq 是 qwen 的变体
    if name_lower.startswith('qwq') or re.search(r'\bqwq\b', name_lower):
        return 'qwen'
    
    # 特殊处理：Magistral 是 Mistral 的产品线
    if 'magistral' in name_lower:
        return 'mistral'
    
    # 特殊处理：Hermes 是 Nous Research 的模型（但不在已知家族中，暂时返回None，后续处理）
    # 特殊处理：EXAONE 是 LG AI Research 的模型
    if 'exaone' in name_lower:
        return None  # 不在已知家族中
    
    # 特殊处理：HyperCLOVA 是 Naver 的模型
    if 'hyperclova' in name_lower or 'clova' in name_lower:
        return None  # 不在已知家族中
    
    # 特殊处理：Mi:dm 是 Korea Telecom 的模型
    if 'mi:dm' in name_lower or 'midm' in name_lower:
        return None  # 不在已知家族中
    
    # 特殊处理：Sonar 是 Perplexity 的模型
    if 'sonar' in name_lower:
        return None  # 不在已知家族中
    
    # 特殊处理：K2-V2 是 MBZUAI 的模型
    if name_lower.startswith('k2') or re.search(r'\bk2-v?\d+', name_lower):
        return None  # 不在已知家族中
    
    # 特殊处理：Motif 是 Motif Technologies 的模型
    if 'motif' in name_lower:
        return None  # 不在已知家族中
    
    # 特殊处理：Nemotron 是 NVIDIA 的模型（但可能是 llama 家族的变体）
    if 'nemotron' in name_lower:
        # 检查是否包含 llama
        if 'llama' in name_lower:
            return 'llama'
        # Nemotron 本身可能是 llama 家族的变体
        return 'llama'  # 假设是 llama 家族
    
    # 特殊处理：Hermes 是 Nous Research 的模型（可能是 llama 家族的变体）
    if 'hermes' in name_lower:
        return 'llama'  # 假设是 llama 家族
    
    # 特殊处理：Opus 单独出现时，可能是 Claude Opus
    if name_lower.startswith('opus') or (name_lower.startswith('opus ') and 'claude' not in name_lower):
        return 'claude'
    
    # 特殊处理：Devstral 是 Mistral 的模型
    if 'devstral' in name_lower:
        return 'mistral'
    
    # 特殊处理：ministral 是 Mistral 的模型
    if 'ministral' in name_lower:
        return 'mistral'
    
    # 特殊处理：Terminus 是 DeepSeek 的模型
    if 'terminus' in name_lower:
        return 'deepseek'
    
    # 特殊处理：horizon, optimus, quasar 等可能是新的模型系列
    if any(x in name_lower for x in ['horizon', 'optimus', 'quasar', 'sherlock', 'openhands']):
        return None  # 不在已知家族中
    
    # 特殊处理：nanbeige 可能是新的模型系列
    if 'nanbeige' in name_lower:
        return None  # 不在已知家族中
    
    # 特殊处理：jamba 是 AI21 Labs 的模型
    if 'jamba' in name_lower:
        return None  # 不在已知家族中
    
    # 特殊处理：mixtral 是 Mistral 的模型
    if 'mixtral' in name_lower:
        return 'mistral'
    
    # 特殊处理：处理斜杠分隔的模型名（如 Qwen3-Coder 480B/A35B）
    # 注意：这种情况在函数开头已经处理了 google/xxx 这样的前缀
    # 这里处理的是模型名内部的斜杠（参数量变体）
    if '/' in name_lower and name_lower.count('/') == 1 and not name_lower.startswith(('google/', 'openai/', 'anthropic/', 'ai21labs/', 'fireworks/')):
        # 可能是参数量变体，取第一部分
        parts = name_lower.split('/')
        if len(parts) == 2:
            # 检查第一部分是否包含家族
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
    """提取子家族"""
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
    """提取版本号，统一为浮点数格式（如 3.0）"""
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
    """提取日期，保持原格式（dec, 2412, 1205 等）"""
    for pattern in DATE_PATTERNS:
        match = pattern.search(name)
        if match:
            return match.group(0)
    return None


def extract_parameters(name: str) -> Optional[str]:
    """提取参数量（只匹配 20B, 1B 这样的格式，不包括 thinking-32k 和 A2B）"""
    match = PARAM_PATTERN.search(name)
    if match:
        return match.group(0).upper()  # 统一为大写
    return None


def extract_other_info(name: str, family: Optional[str], subfamily: Optional[str], 
                      version: Optional[str], date: Optional[str], parameters: Optional[str]) -> Optional[List[str]]:
    """提取其他信息（除了已提取的信息之外的所有内容）"""
    other_info = []
    remaining = name
    
    # 处理带前缀的模型名（如 google/gemini-3-pro-preview）
    if '/' in remaining:
        parts = remaining.split('/', 1)
        if len(parts) == 2:
            # 移除前缀（如 google/, openai/, anthropic/）
            remaining = parts[1]
    
    # 移除已提取的信息
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
            if part and part.lower() not in ['thinking', '32k', '16k', 'non']:
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
