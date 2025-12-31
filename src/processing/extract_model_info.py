"""
模型信息提取脚本

从所有benchmark的cleaned数据中提取模型名称，并解析为结构化信息：
- 家族（Family）
- 子家族（Subfamily）
- 版本（Version）
- 日期（Date）
- 参数量（Parameters）
- 其他信息（Other）

特殊处理：
- o1, o3, o4等需要补充家族为gpt
- -v3.2, -M2等需要识别家族
- gpt-oss需要识别为gpt家族
"""

import re
import json
import csv
from pathlib import Path
from typing import Dict, Optional, Set, List
from collections import defaultdict
import pandas as pd


class ModelInfoExtractor:
    """模型信息提取器"""
    
    # 已知的模型家族
    FAMILIES = {
        'gpt', 'claude', 'gemini', 'grok', 'qwen', 'kimi', 'deepseek',
        'mistral', 'llama', 'glm', 'ernie', 'nova', 'granite', 'phi',
        'gemma', 'codestral', 'chatgpt', 'mimo', 'hunyuan', 'doubao',
        'apriel', 'kat', 'minimax'
    }
    
    # 特殊模型系列（需要补充家族）
    SPECIAL_SERIES = {
        'o1', 'o3', 'o4', 'o5',  # OpenAI的特殊系列，家族为gpt
        'oss',  # gpt-oss，家族为gpt
    }
    
    # 前缀识别（如-v3.2, -M2等）
    PREFIX_PATTERNS = {
        r'^-v(\d+\.?\d*)': 'deepseek',  # -v3.2 -> DeepSeek
        r'^-M(\d+\.?\d*)': 'minimax',   # -M2 -> MiniMax
        r'^-r(\d+)': 'deepseek',        # -r1 -> DeepSeek
        r'^-large': 'mistral',          # -large-3 -> Mistral
        r'^-medium': 'mistral',         # -medium-2508 -> Mistral
    }
    
    # 参数量模式（以B结尾，如20B, 1.5B）
    PARAM_PATTERN = re.compile(r'(\d+\.?\d*)\s*B\b', re.IGNORECASE)
    
    # 日期模式
    DATE_PATTERNS = [
        re.compile(r'(\d{4})-(\d{2})-(\d{2})'),  # 2025-02-27
        re.compile(r'(\d{4})(\d{2})(\d{2})'),    # 20251101
        re.compile(r'(\d{4})-(\d{2})'),          # 2025-02
        re.compile(r'(\d{2})(\d{2})(\d{2})'),    # 0905 (MMDD格式，可能是日期)
        re.compile(r'(\d{4})'),                  # 2025
    ]
    
    # 版本号模式
    VERSION_PATTERNS = [
        re.compile(r'v?(\d+\.\d+)'),            # v3.2, 3.2
        re.compile(r'v?(\d+)'),                 # v3, 3
    ]
    
    def __init__(self):
        self.extracted_models = {}  # model_name -> info dict
    
    def extract_family(self, name: str) -> Optional[str]:
        """提取家族名"""
        name_lower = name.lower()
        
        # 检查特殊系列
        for series in self.SPECIAL_SERIES:
            if name_lower.startswith(series) or f'-{series}' in name_lower or f' {series}' in name_lower:
                if series in ['o1', 'o3', 'o4', 'o5', 'oss']:
                    return 'gpt'
        
        # 检查前缀模式
        for pattern, family in self.PREFIX_PATTERNS.items():
            if re.match(pattern, name_lower):
                return family
        
        # 检查已知家族（优先匹配更长的）
        for family in sorted(self.FAMILIES, key=len, reverse=True):
            if name_lower.startswith(family) or f'-{family}' in name_lower or f' {family}' in name_lower:
                return family
        
        # 提取第一个单词作为家族（如果不在已知列表中）
        first_word = re.split(r'[\s\-_\.]+', name_lower)[0]
        if len(first_word) > 2 and first_word not in ['the', 'and', 'for']:
            return first_word
        
        return None
    
    def extract_subfamily(self, name: str, family: Optional[str]) -> Optional[str]:
        """
        提取子家族
        
        策略：
        1. 先按家族特定规则提取
        2. 然后提取通用变体关键词（nano, pro, preview, mini, flash等）
        3. 按原始模型名称中的顺序组合
        4. 使用单词边界匹配，避免误匹配（如gemini不会提取mini）
        """
        if not family:
            return None
        
        name_lower = name.lower()
        original_name = name  # 保留原始名称用于顺序提取
        
        # 通用变体关键词（需要按顺序提取）
        variant_keywords = ['nano', 'pro', 'preview', 'mini', 'flash', 'ultra', 'turbo']
        
        # 如果家族是gpt，检查子家族
        if family == 'gpt':
            # gpt-5, gpt-4o, gpt-4.5等
            match = re.search(r'gpt[-\s]?(\d+\.?\d*[a-z]*)', name_lower)
            if match:
                subfamily = f"gpt-{match.group(1)}"
                # 检查是否有变体关键词（按顺序添加到subfamily）
                # 使用单词边界匹配，按原始名称顺序
                found_variants_for_gpt = []
                for keyword in variant_keywords:
                    pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
                    if pattern.search(original_name):
                        found_variants_for_gpt.append(keyword)
                if found_variants_for_gpt:
                    subfamily += '-' + '-'.join(found_variants_for_gpt)
                # 特殊处理：codex不在variant_keywords中，需要单独检查
                if 'codex' in name_lower:
                    codex_pattern = re.compile(r'\bcodex\b', re.IGNORECASE)
                    if codex_pattern.search(original_name) and 'codex' not in found_variants_for_gpt:
                        subfamily += '-codex'
                return subfamily
            
            # o1, o3, o4等
            for series in ['o1', 'o3', 'o4', 'o5']:
                if name_lower.startswith(series) or f'-{series}' in name_lower:
                    return series
            
            # oss
            if 'oss' in name_lower:
                return 'gpt-oss'
        
        # 如果家族是gemini
        elif family == 'gemini':
            # 按顺序提取变体关键词
            found_variants_gemini = []
            for keyword in variant_keywords:
                pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
                if pattern.search(original_name):
                    found_variants_gemini.append(keyword)
            if found_variants_gemini:
                return 'gemini-' + '-'.join(found_variants_gemini)
        
        # 如果家族是claude
        elif family == 'claude':
            if 'opus' in name_lower:
                return 'claude-opus'
            elif 'sonnet' in name_lower:
                return 'claude-sonnet'
            elif 'haiku' in name_lower:
                return 'claude-haiku'
        
        # 如果家族是grok
        elif family == 'grok':
            match = re.search(r'grok[-\s]?(\d+\.?\d*)', name_lower)
            if match:
                return f"grok-{match.group(1)}"
        
        # 如果家族是qwen
        elif family == 'qwen':
            match = re.search(r'qwen(\d*\.?\d*)[-\s]?([a-z]*)', name_lower)
            if match:
                version = match.group(1) if match.group(1) else ''
                variant = match.group(2) if match.group(2) else ''
                if variant:
                    return f"qwen{version}-{variant}"
                return f"qwen{version}"
        
        # 如果家族是kimi
        elif family == 'kimi':
            if 'k2' in name_lower:
                return 'kimi-k2'
            elif 'k1' in name_lower:
                return 'kimi-k1'
        
        # 如果家族是deepseek
        elif family == 'deepseek':
            match = re.search(r'v(\d+\.?\d*)', name_lower)
            if match:
                return f"deepseek-v{match.group(1)}"
        
        # 如果家族是mistral
        elif family == 'mistral':
            if 'large' in name_lower:
                return 'mistral-large'
            elif 'medium' in name_lower:
                return 'mistral-medium'
            elif 'small' in name_lower:
                return 'mistral-small'
        
        # 如果家族是llama
        elif family == 'llama':
            match = re.search(r'llama[-\s]?(\d+\.?\d*)', name_lower)
            if match:
                return f"llama-{match.group(1)}"
        
        # 如果家族是glm
        elif family == 'glm':
            match = re.search(r'glm[-\s]?(\d+\.?\d*)', name_lower)
            if match:
                return f"glm-{match.group(1)}"
        
        # 如果家族是nova
        elif family == 'nova':
            if 'pro' in name_lower:
                return 'nova-pro'
            elif 'lite' in name_lower:
                return 'nova-lite'
            elif 'micro' in name_lower:
                return 'nova-micro'
            elif 'omni' in name_lower:
                return 'nova-omni'
        
        # 通用处理：提取变体关键词（nano, pro, preview, mini等）
        # 按原始模型名称中的顺序提取
        found_variants = []
        name_for_search = original_name  # 使用原始名称保持大小写和顺序
        
        for keyword in variant_keywords:
            # 使用单词边界匹配，避免误匹配（如gemini不会匹配mini）
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            if pattern.search(name_for_search):
                found_variants.append(keyword)
        
        # 如果找到了变体关键词，构建subfamily
        if found_variants:
            # 构建基础subfamily（家族名 + 变体）
            base_subfamily = family
            variant_part = '-'.join(found_variants)
            return f"{base_subfamily}-{variant_part}"
        
        return None
    
    def extract_version(self, name: str) -> Optional[str]:
        """提取版本号"""
        # 移除日期和参数量后再提取版本
        name_clean = name
        
        # 移除日期
        for pattern in self.DATE_PATTERNS:
            name_clean = pattern.sub('', name_clean)
        
        # 移除参数量
        name_clean = self.PARAM_PATTERN.sub('', name_clean)
        
        # 提取版本号
        for pattern in self.VERSION_PATTERNS:
            match = pattern.search(name_clean)
            if match:
                version = match.group(1)
                # 确保版本号格式合理
                if '.' in version or len(version) <= 3:
                    return version
        
        return None
    
    def extract_date(self, name: str) -> Optional[str]:
        """提取日期"""
        for pattern in self.DATE_PATTERNS:
            match = pattern.search(name)
            if match:
                if len(match.groups()) == 3:
                    # YYYY-MM-DD 或 YYYYMMDD
                    year, month, day = match.groups()
                    if len(year) == 4:
                        return f"{year}-{month}-{day}"
                    elif len(year) == 2:  # MMDD格式
                        return f"MM{year}-DD{month}"  # 标记为不完整日期
                elif len(match.groups()) == 2:
                    # YYYY-MM
                    year, month = match.groups()
                    if len(year) == 4:
                        return f"{year}-{month}"
                elif len(match.groups()) == 1:
                    year = match.group(1)
                    if len(year) == 4:
                        return year
        
        return None
    
    def extract_parameters(self, name: str) -> Optional[str]:
        """提取参数量（以B结尾）"""
        match = self.PARAM_PATTERN.search(name)
        if match:
            param = match.group(1) + 'B'
            # 确保不是thinking-32k中的32k（不是参数量）
            if 'thinking' in name.lower() and '32k' in name.lower():
                # 检查参数量是否在thinking附近
                thinking_idx = name.lower().find('thinking')
                param_idx = name.lower().find(param.lower())
                if abs(thinking_idx - param_idx) < 10:
                    return None
            return param
        return None
    
    def extract_other_info(self, name: str, family: Optional[str], subfamily: Optional[str], 
                           version: Optional[str], date: Optional[str], parameters: Optional[str]) -> List[str]:
        """
        提取其他信息：从原始模型名称中移除已提取的信息，剩余部分即为other_info
        
        策略：
        1. 先提取括号内容（这些是other_info的一部分）
        2. 从原始名称中移除括号内容（用于后续处理）
        3. 移除家族名
        4. 移除子家族中的非家族部分
        5. 移除版本号
        6. 移除日期
        7. 移除参数量
        8. 清理多余的分隔符和空格
        9. 提取剩余的有意义的部分
        10. 合并括号内容和剩余部分
        """
        if not name:
            return None
        
        # 先提取括号内容
        parentheses_pattern = re.compile(r'\(([^)]+)\)')
        parentheses_content = []
        name_without_parentheses = parentheses_pattern.sub('', name)
        
        for match in parentheses_pattern.finditer(name):
            content = match.group(1).strip()
            if content:
                # 括号内容可能包含多个词，用逗号或空格分隔
                content_parts = re.split(r'[,\s]+', content)
                parentheses_content.extend([p.strip() for p in content_parts if p.strip()])
        
        # 从原始名称开始（已移除括号）
        remaining = name_without_parentheses
        
        # 1. 移除家族名（如果存在）
        if family:
            # 移除家族名（考虑大小写变化和可能的连字符/空格）
            # 先尝试精确匹配（带边界）
            family_pattern = re.compile(r'\b' + re.escape(family) + r'(?=[\s\-_\.]|$)', re.IGNORECASE)
            remaining = family_pattern.sub('', remaining, count=1).strip()
            
            # 如果还有家族名残留（可能是在子家族中），再次尝试移除
            if family.lower() in remaining.lower():
                # 更宽松的匹配，但只在开头
                family_pattern2 = re.compile(r'^' + re.escape(family), re.IGNORECASE)
                remaining = family_pattern2.sub('', remaining).strip()
        
        # 2. 移除子家族中的非家族部分（如果存在）
        if subfamily and family:
            # 子家族格式可能是：gpt-5, gemini-pro, gemini-pro-preview, claude-sonnet等
            # 需要移除子家族中除了家族名之外的部分
            subfamily_parts = subfamily.split('-')
            if len(subfamily_parts) > 1 and subfamily_parts[0].lower() == family.lower():
                # 子家族格式：family-part (如 gpt-5, gemini-pro, gemini-pro-preview)
                # 需要移除"part"部分（可能是多个部分）
                subfamily_suffix = '-'.join(subfamily_parts[1:])  # 获取后缀部分
                if subfamily_suffix:
                    # 移除子家族后缀（如 "5", "pro", "pro-preview", "sonnet"等）
                    # 需要逐个移除每个部分，或者整体移除
                    # 先尝试整体移除
                    suffix_pattern = re.compile(re.escape(subfamily_suffix).replace('-', r'[\s\-_\.]+'), re.IGNORECASE)
                    remaining = suffix_pattern.sub('', remaining).strip()
                    
                    # 如果整体移除失败，尝试逐个部分移除
                    for part in subfamily_parts[1:]:
                        part_pattern = re.compile(r'\b' + re.escape(part) + r'\b', re.IGNORECASE)
                        remaining = part_pattern.sub('', remaining).strip()
            elif subfamily.lower().startswith(family.lower()):
                # 如果子家族以家族名开头但没有连字符分隔（如 qwen2.5）
                # 移除子家族中家族名之后的部分
                subfamily_without_family = subfamily[len(family):].strip('-').strip('.')
                if subfamily_without_family:
                    suffix_pattern = re.compile(re.escape(subfamily_without_family), re.IGNORECASE)
                    remaining = suffix_pattern.sub('', remaining).strip()
        
        # 3. 移除版本号（如果存在）
        if version:
            # 移除版本号（可能是 v3, 3, 3.0 等格式）
            version_patterns = [
                re.compile(r'\b' + re.escape(version) + r'\b', re.IGNORECASE),
                re.compile(r'\bv' + re.escape(version) + r'\b', re.IGNORECASE),
            ]
            for pattern in version_patterns:
                remaining = pattern.sub('', remaining).strip()
        
        # 4. 移除日期（如果存在）
        if date:
            # 移除各种日期格式
            date_patterns = [
                re.compile(re.escape(date), re.IGNORECASE),
                re.compile(re.escape(date.replace('-', '')), re.IGNORECASE),
                re.compile(re.escape(date.replace('-', '/')), re.IGNORECASE),
            ]
            for pattern in date_patterns:
                remaining = pattern.sub('', remaining).strip()
        
        # 5. 移除参数量（如果存在）
        if parameters:
            param_pattern = re.compile(re.escape(parameters), re.IGNORECASE)
            remaining = param_pattern.sub('', remaining).strip()
        
        # 6. 清理多余的分隔符和空格
        # 统一分隔符为空格，然后清理多余空格
        remaining = re.sub(r'[\s\-_\.]+', ' ', remaining)
        remaining = re.sub(r'\s+', ' ', remaining).strip()
        
        # 7. 提取剩余的有意义的部分
        parts = []
        if remaining:
            # 将剩余部分按空格或分隔符拆分
            remaining_parts = re.split(r'[\s\-_\.]+', remaining)
            remaining_parts = [p.strip() for p in remaining_parts if p.strip() and len(p.strip()) > 1]
            
            # 过滤掉常见无意义的词
            meaningless_words = {'ai', 'model', 'the', 'a', 'an', 'and', 'or', 'of', 'for'}
            remaining_parts = [p for p in remaining_parts if p.lower() not in meaningless_words]
            parts.extend(remaining_parts)
        
        # 8. 合并括号内容和剩余部分，但要排除已在subfamily中的关键词
        variant_keywords_set = {'nano', 'pro', 'preview', 'mini', 'flash', 'ultra', 'turbo'}
        if parentheses_content:
            filtered_parentheses = []
            if subfamily:
                # 将subfamily按-拆分，获取所有部分
                subfamily_parts_lower = set([p.lower() for p in subfamily.split('-')])
                for pc in parentheses_content:
                    pc_lower = pc.lower()
                    # 如果括号内容不在subfamily的部分中，则保留
                    if pc_lower not in subfamily_parts_lower:
                        filtered_parentheses.append(pc)
            else:
                filtered_parentheses = parentheses_content
            parts.extend(filtered_parentheses)
        
        if not parts:
            return None
        
        # 去重并返回
        seen = set()
        unique_parts = []
        for part in parts:
            part_lower = part.lower()
            if part_lower not in seen:
                seen.add(part_lower)
                unique_parts.append(part)
        
        return unique_parts if unique_parts else None
    
    def extract_info(self, model_name: str) -> Dict:
        """提取模型的所有信息"""
        family = self.extract_family(model_name)
        subfamily = self.extract_subfamily(model_name, family)
        version = self.extract_version(model_name)
        date = self.extract_date(model_name)
        parameters = self.extract_parameters(model_name)
        # other_info需要基于已提取的信息，从原始名称中提取剩余部分
        other_info = self.extract_other_info(model_name, family, subfamily, version, date, parameters)
        
        return {
            'model_name': model_name,
            'family': family,
            'subfamily': subfamily if subfamily else None,
            'version': version,
            'date': date,
            'parameters': parameters,
            'other_info': sorted(other_info) if other_info else None
        }
    
    def extract_from_benchmark(self, benchmark_path: Path) -> Dict[str, Dict]:
        """从单个benchmark提取模型信息"""
        models_info = {}
        
        if not benchmark_path.exists():
            return models_info
        
        df = pd.read_csv(benchmark_path)
        
        # 尝试多种可能的列名
        model_column = None
        for col_name in ['Model', 'model', 'name', 'model_name', 'AI System', 'ai_system', 'system']:
            if col_name in df.columns:
                model_column = col_name
                break
        
        if model_column is None:
            return models_info
        
        for model_name in df[model_column].dropna().unique():
            if model_name not in self.extracted_models:
                self.extracted_models[model_name] = self.extract_info(model_name)
            models_info[model_name] = self.extracted_models[model_name]
        
        return models_info


def main():
    """主函数：提取所有benchmark的模型信息"""
    base_dir = Path(__file__).parent.parent.parent
    cleaned_data_dir = base_dir / 'data' / 'cleaned'
    output_dir = base_dir / 'data' / 'processed' / 'model_extraction'
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    extractor = ModelInfoExtractor()
    
    # 收集所有benchmark
    benchmarks = {}
    artificial_analysis_models = None
    
    print("正在提取模型信息...")
    
    for csv_file in cleaned_data_dir.rglob('data.csv'):
        # 提取benchmark标识
        parts = csv_file.parts
        try:
            cleaned_idx = parts.index('cleaned')
            if cleaned_idx + 1 < len(parts):
                benchmark_id = parts[cleaned_idx + 1]
                if len(parts) > cleaned_idx + 3:
                    benchmark_id = '/'.join(parts[cleaned_idx + 1:cleaned_idx + 3])
            else:
                benchmark_id = csv_file.parent.name
        except ValueError:
            benchmark_id = csv_file.parent.name
        
        # 特殊处理：artificial_analysis 和 lmarena
        if benchmark_id.startswith('artificial_analysis/'):
            benchmark_name = benchmark_id.split('/')[-1]
            if artificial_analysis_models is None:
                # 只提取一次
                models_info = extractor.extract_from_benchmark(csv_file)
                artificial_analysis_models = models_info
                benchmarks['artificial_analysis'] = models_info
                print(f"  artificial_analysis: {len(models_info)} 个模型")
            continue
        
        if benchmark_id.startswith('lmarena/'):
            benchmark_name = benchmark_id.split('/')[-1]
            if benchmark_name == 'overall':
                # 只处理overall（其他category的模型名称相同）
                models_info = extractor.extract_from_benchmark(csv_file)
                
                # 过滤：只保留Score >= 1330的模型
                import pandas as pd
                df = pd.read_csv(csv_file)
                
                def extract_score(score_str):
                    """从Score字符串中提取数值（如'1443Preliminary' -> 1443）"""
                    if pd.isna(score_str):
                        return None
                    score_str = str(score_str)
                    # 移除"Preliminary"等后缀
                    score_str = score_str.replace('Preliminary', '').replace('preliminary', '').strip()
                    # 提取数字部分
                    try:
                        return float(score_str)
                    except (ValueError, TypeError):
                        return None
                
                df['Score_numeric'] = df['Score'].apply(extract_score)
                filtered_df = df[df['Score_numeric'] >= 1330]
                valid_models = set(filtered_df['Model'].dropna().unique())
                
                # 只保留Score >= 1330的模型
                filtered_models_info = {k: v for k, v in models_info.items() if k in valid_models}
                
                benchmarks['lmarena'] = filtered_models_info
                print(f"  lmarena: {len(filtered_models_info)} 个模型 (已过滤Score >= 1330，原始{len(models_info)}个)")
            continue
        
        # 其他benchmark正常处理
        models_info = extractor.extract_from_benchmark(csv_file)
        benchmarks[benchmark_id] = models_info
        print(f"  {benchmark_id}: {len(models_info)} 个模型")
    
    # 保存每个benchmark的模型信息
    for benchmark_id, models_info in benchmarks.items():
        safe_name = benchmark_id.replace('/', '_').replace('\\', '_')
        output_file = output_dir / f'{safe_name}_models.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(models_info, f, indent=2, ensure_ascii=False)
        
        print(f"  已保存: {output_file}")
    
    # 保存所有模型的汇总信息
    all_models_file = output_dir / 'all_models_info.json'
    with open(all_models_file, 'w', encoding='utf-8') as f:
        json.dump(extractor.extracted_models, f, indent=2, ensure_ascii=False)
    
    print(f"\n总共提取了 {len(extractor.extracted_models)} 个唯一模型")
    print(f"汇总信息已保存: {all_models_file}")
    print("\n模型信息提取完成！")


if __name__ == '__main__':
    main()

