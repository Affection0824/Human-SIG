"""
Step 2: Generate review_files from cleaned_data (non-deterministic)

Input: data/processed/cleaned/{benchmark_id}/cleaned_data.csv
Output: data/processed/review_files/{benchmark_id}_review.json

Functions:
1. Regenerate lmarena_models.json from LMArena raw data (updated every run)
2. Read model names from cleaned_data.csv
3. Parse model information (family, subfamily, version, etc.)
4. Load LMArena model information
5. Match candidates and automatically select best match
6. Generate review_files (contains untrusted field, default 1)

Note: This file contains all necessary utility functions and can run without importing other modules
"""

import json
import csv
import re
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Set


# ============================================================================
# Model Information Parsing Module
# Used to extract family, subfamily, version, date, parameters, and other information from model names
# ============================================================================

# Known model families
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

# Subfamily suffixes (e.g., pro, preview, flash, etc.)
SUBFAMILY_SUFFIXES = ['pro', 'flash', 'heavy', 'r1', 'mini', 'max', 
                      'turbo', 'nano', 'codex', 'sonnet', 'opus', 'haiku', 
                      'air', 'plus', 'lite', 'exp', 'terminus', 'vl', 'coder', 
                      'next', 'fast', 'experimental', 
                      'advanced', 'standard', 'vision', 'turbos', 'micro', 'premier', 'omni', 'special', 'speciale',
                      'dev', 'webapp', 'deep', 
                      'alpha', 'lightning', 'maverick', 'scout', 'nemotron', 'super',
                      'ultra', 'granite', 'arctic', 'jamba', 'hermes',
                      'tulu', 'vicuna', 'starling', 'guanaco', 'dolphin', 'solar',
                      'mpt', 'falcon', 'wizardlm', 'openhermes', 'zephyr', 'smollm',
                      'stripedhyena', 'codellama', 'chatglm', 'oasst', 'pythia',
                      'dolly', 'stablelm', 'koala', 'alpaca', 'gpt4all', 'snoozy']
                      # Removed: 'h', 'preview', 'thinking', 'reasoning', 'large', 'small', 'medium', 'think'

# Parameter pattern (only matches formats like 20B, 1B, excludes thinking-32k and A2B)
PARAM_PATTERN = re.compile(r'\b(\d+\.?\d*)\s*B\b', re.IGNORECASE)

# Date patterns (sorted by priority)
DATE_PATTERNS = [
    re.compile(r'(\d{4})-(\d{2})-(\d{2})'),   # 2025-02-27
    re.compile(r'(\d{4})(\d{2})(\d{2})'),     # 20251101
    re.compile(r'(\d{2})-(\d{4})'),           # 09-2025, 11-2025 (MM-YYYY)
    re.compile(r'(\d{2})-(\d{2})'),            # 02-24, 06-17 (MM-DD)
    re.compile(r'(\d{4})(\d{2})'),            # 202412 (YYYYMM)
    re.compile(r'(\d{2})(\d{2})'),             # 1205, 2412, 2507, 2508 (MMDD)
    re.compile(r'(dec|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov)', re.IGNORECASE),  # dec, jan
]

# Version number patterns (sorted by priority)
# Note: Version numbers only match x or x.y format, where x and y are single digits (1-9 and 0-9)
# Two or more digit numbers should be dates or parameters, not version numbers
# Version numbers can be followed by letters (e.g., "4o"), but not by numbers
VERSION_PATTERNS = [
    re.compile(r'v?([1-9]\.\d)(?![0-9])'),         # v3.5, 3.5（x.y，x是1-9，y是0-9，后面不能跟数字）
    re.compile(r'v?([1-9])-([0-9])(?![0-9])'),     # v4-1, 4-1（匹配为 4.1，x是1-9，y是0-9，后面不能跟数字）
    re.compile(r'v?([1-9])(?![0-9])'),             # v3, 3, 4o（x是1-9，后面不能跟数字，但可以跟字母）
]


def extract_family(name: str) -> Optional[str]:
    """
    Extract model family name
    
    Handles various special cases:
    - Organization name and model name concatenated (e.g., Anthropicclaude -> claude)
    - Special model series (e.g., o1, o3, o4, o5 -> gpt family)
    - Prefix handling (e.g., google/gemini-3-pro -> gemini)
    """
    name_lower = name.lower()
    
    # Remove common prefixes
    if name_lower.startswith(('google/', 'openai/', 'anthropic/', 'ai21labs/', 'fireworks/')):
        name_lower = name_lower.split('/', 1)[1]
    
    # Handle cases where organization name and model name are concatenated
    # Note: Must be processed before checking family names to avoid incorrect matching of family names in organization names
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
        # Note: Do not replace instructalibaba with alibaba, as this would introduce false matches
        # Should let subsequent startswith check prioritize matching qwen
    }
    for old, new in replacements.items():
        name_lower = name_lower.replace(old, new)
    
    # Special handling: qwq is a variant of qwen
    if name_lower.startswith('qwq') or re.search(r'\bqwq\b', name_lower):
        return 'qwen'
    
    # Special handling: Magistral, Devstral, Ministral, Mixtral are Mistral product lines
    if any(x in name_lower for x in ['magistral', 'devstral', 'ministral', 'mixtral']):
        return 'mistral'
    
    # Special handling: Terminus is a DeepSeek model
    if 'terminus' in name_lower:
        return 'deepseek'
    
    # Special handling: Hermes, Nemotron may be llama family variants
    if 'hermes' in name_lower or ('nemotron' in name_lower and 'llama' in name_lower):
        return 'llama'
    if 'nemotron' in name_lower:
        return 'llama'  # Assume it's llama family
    
    # Special handling: When Opus appears alone, it may be Claude Opus
    if name_lower.startswith('opus') or (name_lower.startswith('opus ') and 'claude' not in name_lower):
        return 'claude'
    
    # Special handling: Handle slash-separated model names (e.g., Qwen3-Coder 480B/A35B)
    # Note: Prioritize matching family name at the beginning to avoid matching organization names (e.g., alibaba in InstructAlibaba)
    if '/' in name_lower and name_lower.count('/') == 1 and not name_lower.startswith(('google/', 'openai/', 'anthropic/', 'ai21labs/', 'fireworks/')):
        parts = name_lower.split('/')
        if len(parts) == 2:
            first_part = parts[0]
            # Prioritize checking if it starts with common family names (e.g., qwen) to avoid matching family names in organization names
            if first_part.startswith('qwen'):
                return 'qwen'
            # Then check other family names
            for family in sorted(FAMILIES, key=len, reverse=True):
                if first_part.startswith(family) or f'-{family}' in first_part or f' {family}' in first_part:
                    return family
    
    # Special handling: o1, o3, o4, o5 are GPT family
    if re.match(r'^o[1-5]', name_lower) or re.search(r'\bo[1-5](?:-|$)', name_lower):
        return 'gpt'
    
    # Special handling: gpt-oss, oss are GPT family
    if 'oss' in name_lower and ('gpt' in name_lower or name_lower.startswith('oss')):
        return 'gpt'
    
    # Special handling: Prioritize matching family name at the beginning (e.g., qwen) to avoid matching family names in organization names (e.g., alibaba in InstructAlibaba)
    # This check needs to be before general family matching to ensure priority matching of family names at the beginning
    if name_lower.startswith('qwen'):
        return 'qwen'
    
    # Check known families (sorted by length descending, prioritize longer matches)
    # Note: Only match word boundaries or specific positions to avoid matching family names in organization names
    for family in sorted(FAMILIES, key=len, reverse=True):
        if name_lower.startswith(family) or f'-{family}' in name_lower or f' {family}' in name_lower:
            return family
    
    return None


def extract_subfamily(name: str, family: Optional[str]) -> Optional[str]:
    """
    Extract subfamily name
    
    Subfamily includes suffixes after family name (e.g., pro, preview, flash, etc.)
    Example: gpt-5-pro -> gpt-5-pro, gemini-pro -> gemini-pro
    """
    name_lower = name.lower()
    
    # If family is gpt, subfamily for o1/o3/o4/o5 is o1/o3/o4/o5
    if family == 'gpt':
        o_match = re.search(r'\b(o[1-5])(?:-|$)', name_lower)
        if o_match:
            return o_match.group(1)
    
    # If family is qwen and model name starts with qwq, subfamily is qwq
    if family == 'qwen':
        if name_lower.startswith('qwq'):
            return 'qwen-qwq'
    
    # Build subfamily: family name + suffix
    subfamily_parts = []
    
    if family:
        # Find the part after family name
        # Use word boundary or directly match family name, then extract the following part
        # Prioritize matching family name at the beginning
        family_pattern = re.compile(f'^{re.escape(family)}(?=[-\\s\\d]|$)', re.IGNORECASE)
        match = family_pattern.search(name_lower)
        if not match:
            # 如果开头没匹配到，尝试匹配任何位置的家族名（但优先开头）
            family_pattern = re.compile(f'{re.escape(family)}(?=[-\\s\\d]|$)', re.IGNORECASE)
            match = family_pattern.search(name_lower)
        
        if match:
            after_family = name_lower[match.end():]
            
            # Extract the part before version number as subfamily
            # Version number pattern: v?digit.digit or v?digit (e.g., v2.5, 2.5, v3, 3)
            version_match = re.search(r'v?\d+\.?\d*', after_family)
            if version_match:
                before_version = after_family[:version_match.start()].strip('-').strip()
                if before_version:
                    subfamily_parts.append(before_version)
                # Skip version number, continue searching for suffixes
                after_version = after_family[version_match.end():].strip('-').strip()
            else:
                after_version = after_family.strip('-').strip()
            
            # Search for subfamily suffixes in the part after version number
            # Only match suffixes immediately after version number (using word boundaries or hyphen/space separators)
            # Sort by length descending, prioritize longer suffixes to avoid short suffixes (e.g., 'think') matching part of long suffixes (e.g., 'thinking')
            sorted_suffixes = sorted(SUBFAMILY_SUFFIXES, key=len, reverse=True)
            matched_positions = []  # Record matched positions to avoid overlapping matches
            
            for suffix in sorted_suffixes:
                # Use word boundary matching to ensure suffix is an independent word (not part of another word)
                suffix_pattern = re.compile(rf'\b{re.escape(suffix)}\b|^-{re.escape(suffix)}(?:-|\s|$)|^{re.escape(suffix)}-', re.IGNORECASE)
                match = suffix_pattern.search(after_version)
                if match:
                    match_start, match_end = match.span()
                    # Check if this match overlaps with already matched positions
                    overlap = any(not (match_end <= start or match_start >= end) 
                                  for start, end in matched_positions)
                    if not overlap:
                        if suffix not in subfamily_parts:
                            subfamily_parts.append(suffix)
                        matched_positions.append((match_start, match_end))
    
    if subfamily_parts:
        return f"{family}-{'-'.join(subfamily_parts)}" if family else '-'.join(subfamily_parts)
    
    return None


def extract_version(name: str, parameters: Optional[str] = None, date: Optional[str] = None) -> Optional[str]:
    """
    Extract version number, unified to float format (e.g., 3.0)
    
    Examples: v3 -> 3.0, 3.5 -> 3.5, v3.5 -> 3.5, 4-1 -> 4.1
    
    Note: Avoid matching parameters (e.g., 32b) or dates (e.g., 2024)
    """
    # If parameters have been extracted, need to exclude numbers from parameters
    excluded_numbers = set()
    excluded_positions = []  # Record excluded position ranges
    
    if parameters:
        # Extract all numbers from parameters (e.g., "32b" -> "32" and "2")
        param_numbers = re.findall(r'\d+', parameters)
        excluded_numbers.update(param_numbers)
        # Also exclude all substrings of numbers in parameters (e.g., "32" contains "3" and "2")
        for num_str in param_numbers:
            # Add all substrings of the number (to avoid "2" in "32b" being identified as version number)
            for i in range(len(num_str)):
                for j in range(i + 1, len(num_str) + 1):
                    excluded_numbers.add(num_str[i:j])
        # Find parameters in original name and record their position
        param_match = re.search(re.escape(parameters), name, re.IGNORECASE)
        if param_match:
            excluded_positions.append((param_match.start(), param_match.end()))
    
    # If date has been extracted, need to exclude all numbers in date and their positions
    if date:
        # Extract all numbers from date
        date_numbers = re.findall(r'\d+', date)
        excluded_numbers.update(date_numbers)
        # Find date in original name and record its position
        date_match = re.search(re.escape(date), name, re.IGNORECASE)
        if date_match:
            excluded_positions.append((date_match.start(), date_match.end()))
    
    # Collect all candidate version numbers and their positions
    candidates = []
    
    for pattern in VERSION_PATTERNS:
        for match in pattern.finditer(name):
            # Handle 4-1 format (matched as 4.1)
            if len(match.groups()) == 2:
                major = match.group(1)
                minor = match.group(2)
                # Verify that major and minor version numbers are single digits (1-9 and 0-9)
                if len(major) > 1 or len(minor) > 1:
                    continue
                if not major.isdigit() or not minor.isdigit():
                    continue
                version_str = f"{major}.{minor}"
                # Check if both matched numbers are in the exclusion list
                if major in excluded_numbers or minor in excluded_numbers:
                    continue
            else:
                version_str = match.group(1)
                # Check version number format: may be "2.5" or "3"
                if '.' in version_str:
                    # x.y format, verify that x and y are both single digits
                    parts = version_str.split('.')
                    if len(parts) != 2:
                        continue
                    major, minor = parts
                    if len(major) > 1 or len(minor) > 1:
                        continue
                    if not major.isdigit() or not minor.isdigit():
                        continue
                    # Major version number should be 1-9
                    if major == '0':
                        continue
                else:
                    # Integer version number, should be single digit (1-9)
                    if len(version_str) > 1:
                        continue
                    if not version_str.isdigit():
                        continue
                    # Version number cannot be 0
                    if version_str == '0':
                        continue
                # Check if it's an excluded number
                if version_str in excluded_numbers:
                    continue
            
            match_start, match_end = match.span()
            
            # Check if it's within excluded position range (part of date)
            if any(start <= match_start < end or start < match_end <= end 
                   for start, end in excluded_positions):
                continue
            
            # Verify version number format: only accept x or x.y, where x and y are single digits (1-9)
            # Two or more digit numbers should be dates or parameters
            try:
                version_float = float(version_str)
                # Check if version number is in reasonable range (1-9.9)
                if version_float < 1.0 or version_float > 9.9:
                    continue
                
                # Unified format: if integer, display as 3.0, otherwise keep as is
                if version_float == int(version_float):
                    normalized = f"{int(version_float)}.0"
                else:
                    normalized = str(version_float)
                
                # Record candidate version number and its position (prioritize earlier positions)
                candidates.append((match_start, normalized))
            except ValueError:
                # If cannot convert to float, skip
                continue
    
    # If there are candidates, select the earliest one (version numbers are usually in the front part of model names)
    if candidates:
        candidates.sort(key=lambda x: x[0])  # Sort by position
        return candidates[0][1]
    
    return None


def extract_date(name: str) -> Optional[str]:
    """
    Extract date information
    
    Supported formats:
    - 2025-02-27 (YYYY-MM-DD)
    - 20251101 (YYYYMMDD)
    - 09-2025, 11-2025 (MM-YYYY)
    - 02-24, 06-17 (MM-DD)
    - 202412 (YYYYMM)
    - 1205, 2412, 2507, 2508 (MMDD, 4 digits)
    - dec, jan, etc. month abbreviations
    
    Note: Avoid matching version numbers (e.g., 4.5) or parameters (e.g., 32b)
    """
    for i, pattern in enumerate(DATE_PATTERNS):
        match = pattern.search(name)
        if match:
            if len(match.groups()) == 3:
                # 2025-02-27 or 20251101
                date_str = match.group(0)
                # Verify if it's a reasonable date format
                if '-' in date_str:
                    # Format: 2025-02-27
                    return date_str
                else:
                    # Format: 20251101 (8 digits)
                    if len(date_str) == 8:
                        return date_str
            elif len(match.groups()) == 2:
                date_str = match.group(0)
                if '-' in date_str:
                    # MM-YYYY or MM-DD format
                    parts = date_str.split('-')
                    if len(parts) == 2:
                        part1, part2 = parts
                        if len(part1) == 2 and len(part2) == 4 and part1.isdigit() and part2.isdigit():
                            # MM-YYYY format
                            month = int(part1)
                            year = int(part2)
                            if 1 <= month <= 12 and 1900 <= year <= 2100:
                                return date_str
                        elif len(part1) == 2 and len(part2) == 2 and part1.isdigit() and part2.isdigit():
                            # MM-DD format
                            month = int(part1)
                            day = int(part2)
                            if 1 <= month <= 12 and 1 <= day <= 31:
                                return date_str
                else:
                    # YYYYMM or MMDD format (no hyphen)
                    if len(date_str) == 6 and date_str.isdigit():
                        # YYYYMM format
                        year = int(date_str[:4])
                        month = int(date_str[4:])
                        if 1900 <= year <= 2100 and 1 <= month <= 12:
                            return date_str
                    elif len(date_str) == 4 and date_str.isdigit():
                        # May be MMDD or YYMM format
                        part1 = int(date_str[:2])
                        part2 = int(date_str[2:])
                        
                        # First try MMDD format (first two digits are month, last two are day)
                        if 1 <= part1 <= 12 and 1 <= part2 <= 31:
                            return date_str
                        # Then try YYMM format (first two digits are year, last two are month)
                        # Year range: 00-99 (represents 2000-2099), month range: 01-12
                        elif 0 <= part1 <= 99 and 1 <= part2 <= 12:
                            return date_str
            else:
                # dec, jan, etc. month abbreviations
                month_str = match.group(0).lower()
                # Verify if it's a valid month abbreviation
                valid_months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                               'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
                if month_str in valid_months:
                    return month_str
    return None


def extract_parameters(name: str) -> Optional[str]:
    """
    Extract parameter count (only matches formats like 20B, 1B)
    
    Excludes formats like thinking-32k and A2B
    """
    match = PARAM_PATTERN.search(name)
    if match:
        param_str = match.group(0)
        # Exclude 32k in thinking-32k
        if 'thinking-32k' in name.lower() and '32k' in param_str.lower():
            return None
        return param_str
    return None


def extract_other_info(name: str, family: Optional[str], subfamily: Optional[str], 
                       version: Optional[str], date: Optional[str], parameters: Optional[str]) -> Optional[List[str]]:
    """
    Extract other information (all remaining information)
    
    After removing extracted family, subfamily, version, date, and parameters from model name,
    the remaining part is used as other_info
    
    Note: Only remove the exact extracted parts to avoid mistakenly removing other information (e.g., "Thinking")
    """
    other_info = []
    remaining = name
    
    # Remove extracted information (use more precise matching to avoid mistaken removal)
    if family:
        # Only remove family name at the beginning (followed by space, hyphen, or digit)
        pattern = re.compile(f'^{re.escape(family)}(?=[-\\s\\d]|$)', re.IGNORECASE)
        remaining = pattern.sub('', remaining).strip('-').strip()
    
    if subfamily:
        # When removing subfamily, need to be careful to avoid removing too much
        subfamily_parts = subfamily.split('-')
        for part in subfamily_parts:
            if part != family:  # Don't remove family name again
                # Only remove parts that are independent words or hyphen-separated
                pattern = re.compile(rf'(?:^|[-_\s]){re.escape(part)}(?=[-_\s\\d]|$)', re.IGNORECASE)
                remaining = pattern.sub('', remaining).strip('-').strip()
    
    if version:
        # Handle version number removal: need to match multiple formats, but match precisely
        # Remove standard formats: v3.5, 3.5, v3, 3
        version_clean = version.replace('.0', '').replace('.', r'\.')
        # Match standard format (can have separators like space, hyphen, underscore before/after, but not part of another word)
        pattern1 = re.compile(rf'(?:^|[-_\s])v?{re.escape(version_clean)}(?=[-_\s\\d]|$)', re.IGNORECASE)
        remaining = pattern1.sub('', remaining).strip('-').strip()
        
        # If version number is in x.y format, also need to match x-y format (format in original name)
        if '.' in version and version != version.replace('.', ''):
            parts = version.split('.')
            if len(parts) == 2:
                # Match x-y format
                pattern2 = re.compile(rf'(?:^|[-_\s])v?{re.escape(parts[0])}-{re.escape(parts[1])}(?=[-_\s\\d]|$)', re.IGNORECASE)
                remaining = pattern2.sub('', remaining).strip('-').strip()
                # Also match x.y format (if not already removed)
                pattern3 = re.compile(rf'(?:^|[-_\s])v?{re.escape(parts[0])}\.{re.escape(parts[1])}(?=[-_\s\\d]|$)', re.IGNORECASE)
                remaining = pattern3.sub('', remaining).strip('-').strip()
    
    if date:
        # Precisely match date to avoid mistaken removal
        pattern = re.compile(rf'(?:^|[-_\s]){re.escape(date)}(?=[-_\s]|$)', re.IGNORECASE)
        remaining = pattern.sub('', remaining).strip('-').strip()
    
    if parameters:
        # Precisely match parameter count to avoid mistaken removal
        pattern = re.compile(rf'(?:^|[-_\s]){re.escape(parameters)}(?=[-_\s]|$)', re.IGNORECASE)
        remaining = pattern.sub('', remaining).strip('-').strip()
    
    # Extract remaining information
    if remaining:
        # Use smarter splitting, preserve word boundaries
        # Note: Content in parentheses needs special handling (e.g., "non-thinking")
        parts = re.split(r'[-_\s()]+', remaining)
        
        # Check if there's a non prefix, if so, need special handling
        # Extract non-thinking or non-reasoning as a whole
        processed_parts = []
        skip_next = False
        for i, part in enumerate(parts):
            if skip_next:
                skip_next = False
                continue
            
            part = part.strip()
            if not part:
                continue
            
            # Check if it's a non prefix and next part is thinking or reasoning
            if part.lower() == 'non' and i + 1 < len(parts):
                next_part = parts[i + 1].strip().lower() if parts[i + 1] else ''
                if next_part in ['thinking', 'reasoning']:
                    # Combine non-thinking or non-reasoning as a whole
                    combined = f"non-{parts[i + 1].strip()}"
                    processed_parts.append(combined)
                    skip_next = True
                    continue
            
            # Check if it's a standalone thinking or reasoning, and there's non before it
            # If non-thinking/non-reasoning has already been processed, skip
            if part.lower() in ['thinking', 'reasoning']:
                # Check if there's non before it
                if i > 0 and parts[i - 1].strip().lower() == 'non':
                    # There's already non before, should have been merged and processed, skip
                    continue
            
            processed_parts.append(part)
        
        # Process extracted information
        for part in processed_parts:
            part = part.strip()
            # Filter out some common non-informative words
            if part and part.lower() not in ['32k', '16k', 'non', '']:
                # Check if it's parameter format (but wasn't matched before)
                if not PARAM_PATTERN.match(part):
                    other_info.append(part)
    
    return other_info if other_info else None


def parse_model_name(model_name: str) -> Dict:
    """
    Parse model name and return structured information
    
    Returns dictionary containing:
    - family: Family name (e.g., 'gpt', 'gemini', 'claude')
    - subfamily: Subfamily name (e.g., 'gpt-5-pro', 'gemini-pro')
    - version: Version number (unified to float format, e.g., '3.0')
    - date: Date information (e.g., '2025-04-16', 'dec')
    - parameters: Parameter count (e.g., '20B', '1B')
    - other_info: List of other information
    
    Note: Extraction order is important, extract parameters and date first, then version number, to avoid conflicts
    """
    family = extract_family(model_name)
    subfamily = extract_subfamily(model_name, family)
    
    # Extract parameters and date first (these have clear formats, less prone to misidentification)
    parameters = extract_parameters(model_name)
    date = extract_date(model_name)
    
    # Then extract version number (need to exclude numbers from parameters and date)
    version = extract_version(model_name, parameters, date)
    
    # Finally extract other information
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
# Structured Matcher and Similarity Calculation Module
# Used to match benchmark models with LMArena models and select the best candidate
# ============================================================================

class StructuredMatcher:
    """
    Matcher based on structured information
    
    Used to determine if two model information can match, matching rules:
    1. Family must match
    2. Subfamily must match (if both have)
    3. Version number must match (compared after normalization)
    4. If both have parameters and they don't match, exclude the match
    5. Date does not participate in filtering
    """
    
    def _normalize_version(self, version: Optional[str]) -> Optional[str]:
        """
        Normalize version number: 3 and 3.0 are considered the same, unified to float format (e.g., 3.0)
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
        Determine if two model information can match
        
        Rules:
        1. Family must match
        2. Subfamily must match (if both have)
        3. Version number must match (will be normalized: 3 and 3.0 are considered the same)
        4. If both have parameters and they don't match, exclude the match
        5. Date does not participate in filtering
        """
        # Rule 1: Family must match
        if info1.get('family') != info2.get('family'):
            return False
        
        # Rule 2: Subfamily must match (if both have)
        subfamily1 = info1.get('subfamily')
        subfamily2 = info2.get('subfamily')
        
        if subfamily1 is not None and subfamily2 is not None:
            if subfamily1 != subfamily2:
                return False
        
        if (subfamily1 is None) != (subfamily2 is None):
            return False
        
        # Rule 3: Version number must match (compared after normalization)
        version1 = self._normalize_version(info1.get('version'))
        version2 = self._normalize_version(info2.get('version'))
        
        if version1 is not None and version2 is not None:
            if version1 != version2:
                return False
        
        if (version1 is None) != (version2 is None):
            return False
        
        # Rule 4: If both have parameters and they don't match, exclude the match (case-insensitive)
        param1 = info1.get('parameters')
        param2 = info2.get('parameters')
        
        if param1 is not None and param2 is not None:
            if param1.lower() != param2.lower():
                return False
        
        return True


def normalize_other_info(other_info: Optional[List[str]]) -> Set[str]:
    """
    Normalize other_info for comparison
    
    Convert list to a set of lowercase strings for easier similarity calculation
    """
    if not other_info:
        return set()
    return set(item.lower().strip() for item in other_info if item)


def calculate_similarity(info1: Dict, info2: Dict) -> float:
    """
    Calculate similarity score (0-1) between two model information
    
    Factors and weights:
    1. other_info similarity (50%) - using Jaccard similarity
    2. Date match (20%)
    3. Parameter match (20%)
    4. Subfamily exact match (10%)
    """
    score = 0.0
    weights = {
        'other_info': 0.5,
        'date': 0.2,
        'parameters': 0.2,
        'subfamily': 0.1
    }
    
    # 1. other_info similarity (Jaccard similarity)
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
    
    # 2. Date match
    date1 = info1.get('date')
    date2 = info2.get('date')
    if date1 and date2:
        if date1 == date2:
            score += weights['date'] * 1.0
        else:
            # Same year gives partial score
            if str(date1)[:4] == str(date2)[:4]:
                score += weights['date'] * 0.5
    elif not date1 and not date2:
        pass  # Neither has date, no points given or deducted
    else:
        score += weights['date'] * 0.2  # One has date one doesn't, give small score
    
    # 3. Parameter match
    param1 = info1.get('parameters')
    param2 = info2.get('parameters')
    if param1 and param2:
        if param1 == param2:
            score += weights['parameters'] * 1.0
        else:
            score += weights['parameters'] * 0.0  # Don't match, no points
    elif not param1 and not param2:
        pass  # Neither has parameters, no points given or deducted
    else:
        score += weights['parameters'] * 0.3  # One has parameters one doesn't, give small score
    
    # 4. Subfamily match
    subfamily1 = info1.get('subfamily')
    subfamily2 = info2.get('subfamily')
    if subfamily1 and subfamily2:
        if subfamily1 == subfamily2:
            score += weights['subfamily'] * 1.0
        else:
            # Partial match (one contains the other)
            if subfamily1 in subfamily2 or subfamily2 in subfamily1:
                score += weights['subfamily'] * 0.5
    elif not subfamily1 and not subfamily2:
        pass  # Neither has subfamily, no points given or deducted
    else:
        score += weights['subfamily'] * 0.2  # One has subfamily one doesn't, give small score
    
    return min(score, 1.0)


def select_best_candidate(benchmark_info: Dict, candidates: List[Dict]) -> Optional[str]:
    """
    Select the best match from multiple candidates
    
    Algorithm:
    1. Filter out NO_MATCH_FOUND
    2. If only one candidate, return directly
    3. If multiple candidates, calculate similarity score for each
    4. Select candidate with highest similarity (if similarity >= 0.3)
    
    Returns: Selected lmarena_model name, or None if no suitable match
    """
    if not candidates:
        return None
    
    valid_candidates = [c for c in candidates if c.get('lmarena_model') != 'NO_MATCH_FOUND']
    
    if not valid_candidates:
        return None
    
    if len(valid_candidates) == 1:
        return valid_candidates[0].get('lmarena_model')
    
    # Multiple candidates, calculate similarity and select best
    scored_candidates = []
    for candidate in valid_candidates:
        similarity = calculate_similarity(benchmark_info, candidate)
        scored_candidates.append((similarity, candidate))
    
    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    
    # Select candidate with highest similarity
    best_similarity, best_candidate = scored_candidates[0]
    
    # If similarity is too low, return None
    if best_similarity < 0.3:
        return None
    
    return best_candidate.get('lmarena_model')


# ============================================================================
# Main Processing Functions
# ============================================================================

def generate_lmarena_extraction(
    raw_csv_path: Path,
    output_file: Path,
    score_threshold: float = 1330.0
) -> Dict[str, Dict]:
    """
    Generate extraction file from LMArena raw data
    
    Only keep models with Score >= score_threshold
    """
    print(f"\nGenerating LMArena extraction file...")
    print(f"  Reading data from {raw_csv_path}")
    print(f"  Score threshold: >= {score_threshold}")
    
    # Read raw CSV
    df = None
    for encoding in ['utf-8', 'gbk', 'latin-1', 'cp1252']:
        try:
            df = pd.read_csv(raw_csv_path, encoding=encoding)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if df is None:
        print(f"  Error: Unable to read CSV file")
        return {}
    
    # Find model column and score column
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
        print(f"  Error: Model column or score column not found")
        return {}
    
    # Extract model information
    lmarena_models = {}
    for _, row in df.iterrows():
        model_name = str(row[model_col]).strip()
        score_value = row[score_col]
        
        # Process score (remove ± error portion)
        try:
            score_str = str(score_value).strip()
            # Remove "Preliminary" suffix
            score_str = score_str.replace('Preliminary', '').strip()
            # Remove ± and everything after it
            if '±' in score_str:
                score_str = score_str.split('±')[0].strip()
            score = float(score_str)
        except (ValueError, TypeError):
            continue
        
        # Only keep models with Score >= threshold
        if score < score_threshold:
            continue
        
        # Parse model information
        try:
            parsed_info = parse_model_name(model_name)
            lmarena_models[model_name] = parsed_info
        except Exception as e:
            print(f"  Warning: Failed to parse model name {model_name}: {e}")
            # Even if parsing fails, create a basic structure
            lmarena_models[model_name] = {
                'family': None,
                'subfamily': None,
                'version': None,
                'date': None,
                'parameters': None,
                'other_info': None
            }
    
    # Save to file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(lmarena_models, f, indent=2, ensure_ascii=False)
    
    print(f"  Generated: {output_file}")
    print(f"  Contains {len(lmarena_models)} models (Score >= {score_threshold})")
    
    return lmarena_models


def load_lmarena_models(lmarena_file: Path, raw_csv_path: Path) -> Dict[str, Dict]:
    """
    Load LMArena model information
    
    Regenerate from raw data every run to ensure data is up to date
    """
    # Regenerate every run, don't check if file exists
    return generate_lmarena_extraction(raw_csv_path, lmarena_file)


def load_benchmark_models(cleaned_csv_path: Path) -> List[str]:
    """
    Read model name list from cleaned_data.csv
    
    For data from vals_ai, remove organization prefix before model name (e.g., openai/, google/, etc.)
    """
    models = []
    # Known organization prefix list for vals.ai
    known_prefixes = ['openai', 'google', 'anthropic', 'alibaba', 'fireworks', 'grok', 
                      'kimi', 'minimax', 'mistralai', 'cohere', 'ai21labs', 'together', 'zai']
    
    with open(cleaned_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            model_name = row['model_name']
            # If model name contains slash and part before slash is a known prefix, remove prefix
            if '/' in model_name:
                parts = model_name.split('/', 1)
                if parts[0].lower() in known_prefixes:
                    model_name = parts[1]
            models.append(model_name)
    return models


def process_benchmark(
    benchmark_id: str,
    cleaned_csv_path: Path,
    lmarena_models: Dict[str, Dict],
    output_file: Path
):
    """Process a single benchmark and generate review_file"""
    print(f"\nProcessing: {benchmark_id}")
    
    # Read model names from cleaned_data.csv
    benchmark_model_names = load_benchmark_models(cleaned_csv_path)
    print(f"  Read {len(benchmark_model_names)} models from cleaned_data.csv")
    
    # Parse information for each model
    benchmark_models_info = {}
    for model_name in benchmark_model_names:
        try:
            parsed_info = parse_model_name(model_name)
            benchmark_models_info[model_name] = parsed_info
        except Exception as e:
            print(f"  Warning: Failed to parse model name {model_name}: {e}")
            # Even if parsing fails, create a basic structure
            benchmark_models_info[model_name] = {
                'family': None,
                'subfamily': None,
                'version': None,
                'date': None,
                'parameters': None,
                'other_info': None
            }
    
    # Match candidates and automatically select
    matcher = StructuredMatcher()
    review_data = {}
    
    for benchmark_model, benchmark_info in benchmark_models_info.items():
        # Find all possible matching LMArena models
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
        
        # If no candidates, add NO_MATCH_FOUND
        if not candidates:
            candidates = [{'lmarena_model': 'NO_MATCH_FOUND'}]
        
        # Automatically select best match
        valid_candidates = [c for c in candidates if c.get('lmarena_model') != 'NO_MATCH_FOUND']
        
        if not valid_candidates:
            selected_lmarena_model = 0
        elif len(valid_candidates) == 1:
            selected_lmarena_model = valid_candidates[0].get('lmarena_model')
        else:
            # Multiple candidates, use similarity algorithm to select
            selected = select_best_candidate(benchmark_info, valid_candidates)
            selected_lmarena_model = selected if selected else 0
        
        # Build review entry
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
            'untrusted': 1,  # Default untrusted (completed by agent)
            'selected_lmarena_model': selected_lmarena_model
        }
    
    # Write JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(review_data, f, indent=2, ensure_ascii=False)
    
    # Statistics
    total_models = len(review_data)
    matched_count = sum(1 for data in review_data.values() 
                        if isinstance(data.get('selected_lmarena_model'), str))
    no_match_count = sum(1 for data in review_data.values() 
                        if data.get('selected_lmarena_model') == 0)
    multi_candidates_count = sum(1 for data in review_data.values() 
                                 if len([c for c in data.get('candidates', []) 
                                        if c.get('lmarena_model') != 'NO_MATCH_FOUND']) > 1)
    
    print(f"  Generated: {output_file.name}")
    print(f"    Total models: {total_models}")
    print(f"    Matched: {matched_count}")
    print(f"    No match: {no_match_count}")
    print(f"    Multiple candidates: {multi_candidates_count}")


def main():
    """Main function"""
    base_dir = Path(__file__).parent.parent.parent
    raw_dir = base_dir / 'data' / 'raw'
    cleaned_dir = base_dir / 'data' / 'processed' / 'cleaned'
    model_extraction_dir = base_dir / 'data' / 'processed' / 'model_extraction'
    review_files_dir = base_dir / 'data' / 'processed' / 'review_files'
    
    # Create output directories
    review_files_dir.mkdir(parents=True, exist_ok=True)
    model_extraction_dir.mkdir(parents=True, exist_ok=True)
    
    # Load or generate LMArena model information
    lmarena_file = model_extraction_dir / 'lmarena_models.json'
    lmarena_raw_csv = raw_dir / 'lmarena' / 'LMArena-Overall' / 'data.csv'
    
    print("=" * 60)
    print("Loading LMArena model information...")
    lmarena_models = load_lmarena_models(lmarena_file, lmarena_raw_csv)
    
    if not lmarena_models:
        print("Error: Unable to load or generate LMArena model information, script cannot continue")
        return
    
    print(f"Total {len(lmarena_models)} LMArena models available for matching")
    print("=" * 60)
    
    # Find all cleaned_data.csv files
    cleaned_csv_files = list(cleaned_dir.rglob('cleaned_data.csv'))
    print(f"\nFound {len(cleaned_csv_files)} cleaned_data.csv files")
    
    # Process each benchmark (exclude LMArena)
    for cleaned_csv_path in sorted(cleaned_csv_files):
        benchmark_id = cleaned_csv_path.parent.name
        
        # Skip LMArena (because LMArena can definitely match internally)
        if benchmark_id.startswith('LMArena-'):
            print(f"\nSkipping LMArena: {benchmark_id}")
            continue
        
        output_file = review_files_dir / f'{benchmark_id}_review.json'
        
        process_benchmark(
            benchmark_id,
            cleaned_csv_path,
            lmarena_models,
            output_file
        )
    
    print("\nCompleted!")


if __name__ == '__main__':
    main()
