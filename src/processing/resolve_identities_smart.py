"""
智能实体解析模块 - 改进版

本模块实现了多层级、智能化的模型名称实体解析策略，用于将benchmark中的模型名称
映射到LMArena标准化的模型ID。

核心改进：
1. 结构化解析：将模型名称分解为家族名、版本号、变体标记等组件
2. 智能候选生成：基于模型结构而非简单的字符串相似度生成候选
3. 分层过滤：通过多层级过滤减少需要人工审核的候选数量
4. 置信度评估：为每个候选匹配提供置信度评分

算法流程：
- Level 0: 全局精确匹配（低ELO过滤）
- Level 1: 研究宇宙精确匹配
- Level 2: 映射表查找
- Level 3: 智能候选生成（结构化匹配 + 相似度评分）
  - 3a: 基于模型家族的候选过滤
  - 3b: 基于版本号和变体的结构化相似度计算
  - 3c: 生成Top-K候选（K=3-5）供人工审核

输入：
- LMArena完整数据集（包含所有ELO分数）
- Benchmark清理后的数据集（来自 data/cleaned/）
- mapping.json（已有的映射关系）

输出：
- pending_resolution.csv（需要人工审核的候选匹配，已大幅减少）
- unmatched_log.csv（完全无法匹配的模型）
- 自动映射日志
"""

import json
import re
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
import pandas as pd
from difflib import SequenceMatcher


class ModelNameParser:
    """
    模型名称解析器：将模型名称分解为结构化组件
    
    组件包括：
    - family: 模型家族名（如 gpt, claude, gemini）
    - version: 版本号（如 5.1, 4.5）
    - variant: 变体标记（如 high, medium, thinking）
    - date: 日期后缀（如 20251101）
    - suffix: 其他后缀信息
    """
    
    # 已知的模型家族前缀（不区分大小写）
    # 注意：o1, o3, o4 等需要特殊处理（它们是OpenAI的模型，但有自己的命名规则）
    MODEL_FAMILIES = {
        'gpt', 'claude', 'gemini', 'grok', 'qwen', 'kimi', 'deepseek',
        'mistral', 'llama', 'glm', 'ernie', 'nova', 
        'granite', 'phi', 'gemma', 'codestral', 'chatgpt', 'claude-opus',
        'claude-sonnet', 'claude-haiku', 'qwen3', 'mimo', 'hunyuan'
    }
    
    # 特殊模型系列（需要精确匹配，如 o1 不能匹配 o3）
    SPECIAL_MODEL_SERIES = {
        'o1', 'o3', 'o4', 'o5'  # OpenAI的特殊模型系列
    }
    
    # 变体标记（常见的大小/性能等级标记）
    VARIANT_MARKERS = {
        'high', 'medium', 'low', 'mini', 'micro', 'tiny', 'small', 'large',
        'xhigh', 'xxhigh', 'pro', 'flash', 'ultra', 'max', 'plus',
        'thinking', 'reasoning', 'instruct', 'base', 'preview', 'chat'
    }
    
    def __init__(self):
        # 编译正则表达式以提高性能
        self.version_pattern = re.compile(r'(\d+\.?\d*)')
        self.date_pattern = re.compile(r'(\d{4}[-_]?\d{2}[-_]?\d{2})|(\d{8})')
        self.parentheses_pattern = re.compile(r'\(([^)]+)\)')
        
    def normalize(self, name: str) -> str:
        """
        标准化模型名称：统一格式便于比较
        
        - 转小写
        - 处理点号：将点号替换为连字符（如 GPT-4.5 -> gpt-4-5）
        - 将空格、下划线、多个连字符统一为单个连字符
        - 移除多余的空格和首尾连字符
        """
        name = name.lower().strip()
        # 处理点号：将点号替换为连字符（但保留数字版本号中的点号，如 5.1 保持不变）
        # 注意：点号前后如果都是数字，可能是版本号（如 4.5），我们需要将其转换为 4-5
        # 但如果点号后是数字且前面不是数字（如 GPT-4.5），也转换为连字符
        # 为了简单起见，我们将所有点号替换为连字符，后续版本提取会处理数字部分
        name = name.replace('.', '-')
        # 将空格、下划线、多个连字符统一为单个连字符
        name = re.sub(r'[\s_\-]+', '-', name)
        # 移除首尾连字符
        name = name.strip('-')
        return name
    
    def extract_family(self, normalized_name: str) -> Optional[str]:
        """
        提取模型家族名
        
        策略：
        1. 优先检查特殊模型系列（o1, o3, o4等，需要精确匹配）
        2. 检查是否以已知家族名开头
        3. 考虑复合家族名（如 claude-opus, claude-sonnet）
        4. 处理特殊情况（如单字母开头的模型）
        """
        normalized_name = normalized_name.lower()
        
        # 优先检查特殊模型系列（如 o1, o3, o4）
        # 这些模型需要精确匹配：o1 不能匹配 o3，但 o1-mini 应该匹配 o1-xxx
        for special_series in sorted(self.SPECIAL_MODEL_SERIES, key=len, reverse=True):
            if normalized_name.startswith(special_series + '-') or normalized_name == special_series:
                return special_series
        
        # 检查复合家族名（优先匹配更长的，如 claude-opus 优先于 claude）
        for family in sorted(self.MODEL_FAMILIES, key=len, reverse=True):
            if normalized_name.startswith(family):
                return family
        
        # 检查是否以特殊模型系列开头（但不在列表中，如 o1p, o2 等）
        if re.match(r'^o[1-9][a-z]*', normalized_name):
            # 提取完整的特殊系列名（如 o1p, o2-mini）
            match = re.match(r'^(o[1-9][a-z]*)', normalized_name)
            if match:
                return match.group(1)
        
        # 尝试提取第一个单词作为家族名（如果不在已知列表中，也返回以便后续使用）
        first_part = normalized_name.split('-')[0]
        if len(first_part) > 1:
            return first_part
        
        return None
    
    def extract_version(self, normalized_name: str) -> Optional[str]:
        """
        提取版本号（如 5.1, 4.5, 3.2）
        
        策略：查找第一个数字或数字.数字模式
        """
        match = self.version_pattern.search(normalized_name)
        if match:
            return match.group(1)
        return None
    
    def extract_variant(self, normalized_name: str) -> Set[str]:
        """
        提取变体标记（可能多个，如 high, thinking）
        
        策略：
        1. 检查括号内的内容
        2. 检查已知的变体标记
        3. 返回所有匹配的变体标记
        """
        variants = set()
        
        # 检查括号内的内容
        parentheses_content = self.parentheses_pattern.findall(normalized_name)
        for content in parentheses_content:
            # 移除括号，标准化
            content = content.lower().strip()
            if content in self.VARIANT_MARKERS:
                variants.add(content)
            # 也检查内容的一部分
            for marker in self.VARIANT_MARKERS:
                if marker in content:
                    variants.add(marker)
        
        # 检查名称中的变体标记（不在括号内）
        name_without_parentheses = self.parentheses_pattern.sub('', normalized_name)
        for marker in self.VARIANT_MARKERS:
            # 使用单词边界匹配，避免误匹配（如 "high" 不应匹配 "highlight"）
            pattern = r'\b' + re.escape(marker) + r'\b'
            if re.search(pattern, name_without_parentheses, re.IGNORECASE):
                variants.add(marker)
        
        return variants
    
    def extract_date(self, normalized_name: str) -> Optional[str]:
        """提取日期后缀（如 20251101, 2025-11-01）"""
        match = self.date_pattern.search(normalized_name)
        if match:
            date_str = match.group(0)
            # 标准化日期格式为 YYYYMMDD
            date_str = re.sub(r'[-_]', '', date_str)
            if len(date_str) == 8:
                return date_str
        return None
    
    def parse(self, name: str) -> Dict[str, any]:
        """
        解析模型名称，返回结构化组件
        
        返回字典包含：
        - original: 原始名称
        - normalized: 标准化后的名称
        - family: 家族名
        - version: 版本号
        - variant: 变体标记集合
        - date: 日期后缀
        - components: 所有组成部分的列表
        """
        normalized = self.normalize(name)
        
        result = {
            'original': name,
            'normalized': normalized,
            'family': self.extract_family(normalized),
            'version': self.extract_version(normalized),
            'variant': self.extract_variant(normalized),
            'date': self.extract_date(normalized),
            'components': normalized.split('-')
        }
        
        return result


class StructuredMatcher:
    """
    结构化匹配器：基于模型名称的结构化组件进行智能匹配
    
    匹配策略：
    1. 家族名必须匹配（或高度相似）
    2. 版本号相似度评分
    3. 变体标记重叠度评分
    4. 整体字符串相似度作为辅助指标
    """
    
    def __init__(self, parser: ModelNameParser):
        self.parser = parser
        # 访问parser中的特殊模型系列定义
        self.SPECIAL_MODEL_SERIES = parser.SPECIAL_MODEL_SERIES
    
    def version_similarity(self, v1: Optional[str], v2: Optional[str]) -> float:
        """
        计算版本号相似度
        
        策略：
        - 如果版本号完全相同：1.0
        - 如果都是数字，计算数值接近度
        - 如果版本号格式不同：0.0
        """
        if v1 is None or v2 is None:
            return 0.0 if (v1 is None and v2 is None) else 0.3
        
        if v1 == v2:
            return 1.0
        
        try:
            # 尝试解析为浮点数
            f1, f2 = float(v1), float(v2)
            # 计算数值接近度（差异越小，相似度越高）
            diff = abs(f1 - f2)
            # 使用指数衰减：差异为0时相似度为1，差异为1时相似度约为0.37
            similarity = 1.0 / (1.0 + diff)
            return similarity
        except ValueError:
            # 无法转换为数字，返回较低的相似度
            return 0.2 if v1 in v2 or v2 in v1 else 0.0
    
    def variant_overlap(self, variants1: Set[str], variants2: Set[str]) -> float:
        """
        计算变体标记重叠度
        
        策略：
        - Jaccard相似度：交集大小 / 并集大小
        - 如果都为空，返回0.5（中性）
        """
        if not variants1 and not variants2:
            return 0.5  # 都没有变体标记，视为中性
        
        if not variants1 or not variants2:
            return 0.2  # 一个有，一个没有，相似度较低
        
        intersection = len(variants1 & variants2)
        union = len(variants1 | variants2)
        
        return intersection / union if union > 0 else 0.0
    
    def family_match(self, family1: Optional[str], family2: Optional[str]) -> Tuple[bool, float]:
        """
        判断家族名是否匹配
        
        返回：(是否匹配, 相似度分数)
        
        策略：
        - 完全相同：完全匹配，相似度1.0
        - 特殊模型系列（o1, o3等）：必须精确匹配，o1 不能匹配 o3
        - 特殊处理：o1/o3 可以匹配 gpt 家族（如果LMArena模型名称中包含o1/o3）
        - 包含关系（如 gpt 包含在 gpt-5 中）：高度匹配，相似度0.9
        - 字符串相似度：使用SequenceMatcher（但特殊系列除外）
        """
        if family1 is None or family2 is None:
            return (False, 0.0)
        
        if family1 == family2:
            return (True, 1.0)
        
        # 特殊模型系列必须精确匹配（o1 不能匹配 o3）
        if family1 in self.SPECIAL_MODEL_SERIES or family2 in self.SPECIAL_MODEL_SERIES:
            # 如果都是特殊系列但不相同（如 o1 vs o3），则不匹配
            if family1 in self.SPECIAL_MODEL_SERIES and family2 in self.SPECIAL_MODEL_SERIES:
                if family1 != family2:
                    return (False, 0.0)
                else:
                    return (True, 1.0)
            
            # 特殊处理：如果一个是特殊系列（如 o1），另一个是 gpt 家族
            # 允许匹配（因为 o1 可能是 gpt-o1 的简写）
            if (family1 in self.SPECIAL_MODEL_SERIES and family2 == 'gpt') or \
               (family2 in self.SPECIAL_MODEL_SERIES and family1 == 'gpt'):
                return (True, 0.85)  # 给予较高但略低于完全匹配的分数
            
            # 如果一个是特殊系列，另一个不是gpt，则不匹配
            if (family1 in self.SPECIAL_MODEL_SERIES) != (family2 in self.SPECIAL_MODEL_SERIES):
                return (False, 0.0)
        
        # 检查包含关系（考虑复合家族名，如 claude-opus 包含 claude）
        if family1 in family2 or family2 in family1:
            return (True, 0.9)
        
        # 使用字符串相似度
        similarity = SequenceMatcher(None, family1, family2).ratio()
        # 只有相似度 > 0.7 才认为可能是同一家族
        return (similarity > 0.7, similarity)
    
    def compute_structured_similarity(self, parsed1: Dict, parsed2: Dict) -> float:
        """
        计算结构化相似度分数
        
        综合评分：
        - 家族匹配（必须，权重0.4）
        - 版本相似度（权重0.3）
        - 变体重叠度（权重0.2）
        - 整体字符串相似度（权重0.1）
        """
        # 1. 家族匹配（必须满足）
        family_match, family_score = self.family_match(
            parsed1.get('family'), parsed2.get('family')
        )
        
        if not family_match:
            return 0.0  # 家族不匹配，直接返回0
        
        # 2. 版本相似度
        version_score = self.version_similarity(
            parsed1.get('version'), parsed2.get('version')
        )
        
        # 3. 变体重叠度
        variant_score = self.variant_overlap(
            parsed1.get('variant', set()), parsed2.get('variant', set())
        )
        
        # 4. 整体字符串相似度（作为辅助指标）
        string_similarity = SequenceMatcher(
            None, parsed1['normalized'], parsed2['normalized']
        ).ratio()
        
        # 加权综合评分
        structured_score = (
            family_score * 0.4 +
            version_score * 0.3 +
            variant_score * 0.2 +
            string_similarity * 0.1
        )
        
        return structured_score


class SmartEntityResolver:
    """
    智能实体解析器：主类
    
    实现多层级匹配策略，大幅减少需要人工审核的候选数量
    """
    
    def __init__(
        self,
        lmarena_data_path: str,
        cleaned_data_dir: str,
        mapping_json_path: str,
        study_universe_threshold: int = 1330,
        max_candidates_per_model: int = 3
    ):
        self.lmarena_data_path = Path(lmarena_data_path)
        self.cleaned_data_dir = Path(cleaned_data_dir)
        self.mapping_json_path = Path(mapping_json_path)
        self.study_universe_threshold = study_universe_threshold
        self.max_candidates = max_candidates_per_model
        
        self.parser = ModelNameParser()
        self.matcher = StructuredMatcher(self.parser)
        
        # 数据存储
        self.lmarena_full_df = None
        self.lmarena_study_universe = None
        self.mapping_registry = {}
        self.benchmark_models = defaultdict(set)  # benchmark_name -> set of model names
        self.elo_column = None  # LMArena数据中的ELO列名（将在load_data中设置，可能是'Score'或'elo_overall'）
        
        # 结果存储
        self.auto_mapped = {}  # benchmark_model_name -> lmarena_id
        self.pending_resolution = []  # List of dicts for CSV
        self.unmatched_log = []  # List of dicts for CSV
    
    def load_data(self):
        """加载所有必要的数据"""
        print("正在加载LMArena数据...")
        self.lmarena_full_df = pd.read_csv(self.lmarena_data_path)
        print(f"  加载了 {len(self.lmarena_full_df)} 个LMArena模型")
        
        # 创建研究宇宙（ELO >= 1330）
        # 注意：LMArena数据使用'Score'列存储ELO分数，但在某些阶段可能使用'elo_overall'
        self.elo_column = 'elo_overall' if 'elo_overall' in self.lmarena_full_df.columns else 'Score'
        self.lmarena_study_universe = self.lmarena_full_df[
            self.lmarena_full_df[self.elo_column] >= self.study_universe_threshold
        ].copy()
        print(f"  研究宇宙包含 {len(self.lmarena_study_universe)} 个模型（{self.elo_column} >= {self.study_universe_threshold}）")
        
        # 加载映射表
        if self.mapping_json_path.exists():
            with open(self.mapping_json_path, 'r', encoding='utf-8') as f:
                self.mapping_registry = json.load(f)
            print(f"  加载了 {len(self.mapping_registry)} 个已有映射关系")
        else:
            print("  映射表不存在，将创建新文件")
        
        # 加载所有benchmark数据
        print("正在加载benchmark数据...")
        benchmark_count = 0
        for benchmark_dir in self.cleaned_data_dir.rglob('data.csv'):
            # 提取benchmark名称（从路径中推断）
            parts = benchmark_dir.parts
            # 找到 'cleaned' 之后的第一个目录名作为benchmark标识
            try:
                cleaned_idx = parts.index('cleaned')
                if cleaned_idx + 1 < len(parts):
                    benchmark_id = parts[cleaned_idx + 1]
                    # 如果还有子目录，也包含进来（如 frontiermath/frontiermath_tier_1_3）
                    if len(parts) > cleaned_idx + 3:
                        benchmark_id = '/'.join(parts[cleaned_idx + 1:cleaned_idx + 3])
                else:
                    benchmark_id = benchmark_dir.parent.name
            except ValueError:
                benchmark_id = benchmark_dir.parent.name
            
            df = pd.read_csv(benchmark_dir)
            # 假设模型名称在 'Model' 列（需要根据实际数据调整）
            if 'Model' in df.columns:
                models = set(df['Model'].dropna().unique())
                self.benchmark_models[benchmark_id] = models
                benchmark_count += 1
                print(f"  {benchmark_id}: {len(models)} 个模型")
        
        print(f"总共加载了 {benchmark_count} 个benchmark")
    
    def level_0_exact_match(self, raw_name: str) -> Optional[Tuple[str, int]]:
        """
        Level 0: 全局精确匹配（低ELO过滤）
        
        返回: (lmarena_id, elo_overall) 或 None
        """
        # 标准化后精确匹配
        normalized = self.parser.normalize(raw_name)
        
        # 在完整LMArena数据中查找
        for idx, row in self.lmarena_full_df.iterrows():
            lmarena_normalized = self.parser.normalize(row['Model'])
            if normalized == lmarena_normalized:
                return (row['Model'], row.get(self.elo_column, 0))
        
        return None
    
    def level_1_target_exact_match(self, raw_name: str) -> Optional[str]:
        """
        Level 1: 研究宇宙精确匹配
        
        返回: lmarena_id 或 None
        """
        normalized = self.parser.normalize(raw_name)
        
        for idx, row in self.lmarena_study_universe.iterrows():
            lmarena_normalized = self.parser.normalize(row['Model'])
            if normalized == lmarena_normalized:
                return row['Model']
        
        return None
    
    def level_2_registry_lookup(self, raw_name: str) -> Optional[str]:
        """
        Level 2: 映射表查找
        
        返回: lmarena_id 或 None
        """
        return self.mapping_registry.get(raw_name)
    
    def level_3_smart_candidates(self, raw_name: str) -> List[Tuple[str, float]]:
        """
        Level 3: 智能候选生成
        
        策略：
        1. 解析benchmark模型名称
        2. 基于家族名过滤LMArena候选（如果家族提取成功）
        3. 计算结构化相似度
        4. 如果没有家族匹配的候选，使用宽松的字符串相似度作为备选
        5. 返回Top-K候选（按相似度降序）
        
        返回: List of (lmarena_id, similarity_score) tuples
        
        关键改进：
        - 保证完整性：即使家族提取失败或不匹配，也会使用字符串相似度作为备选
        - 双重策略：先尝试结构化匹配，如果失败则使用字符串相似度，确保所有可能匹配都被考虑
        """
        parsed_benchmark = self.parser.parse(raw_name)
        benchmark_family = parsed_benchmark.get('family')
        
        candidates = []
        
        # 如果提取到家族名，优先使用结构化匹配
        if benchmark_family:
            # 遍历研究宇宙中的所有模型
            for idx, row in self.lmarena_study_universe.iterrows():
                lmarena_id = row['Model']
                parsed_lmarena = self.parser.parse(lmarena_id)
                
                # 计算结构化相似度
                similarity = self.matcher.compute_structured_similarity(
                    parsed_benchmark, parsed_lmarena
                )
                
                # 只保留相似度 > 0.3 的候选
                if similarity > 0.3:
                    candidates.append((lmarena_id, similarity))
        
        # 如果结构化匹配没有找到足够的候选，使用字符串相似度作为补充
        # 这样可以确保即使家族提取失败或家族不匹配，高相似度的模型也会被考虑
        if len(candidates) < self.max_candidates:
            normalized_benchmark = self.parser.normalize(raw_name)
            fallback_candidates = []
            
            for idx, row in self.lmarena_study_universe.iterrows():
                lmarena_id = row['Model']
                lmarena_normalized = self.parser.normalize(lmarena_id)
                string_similarity = SequenceMatcher(None, normalized_benchmark, lmarena_normalized).ratio()
                
                # 使用较高的阈值（0.6）来避免过多的低质量候选
                if string_similarity > 0.6:
                    # 检查是否已经在结构化匹配的候选列表中
                    if not any(lmarena_id == c[0] for c in candidates):
                        fallback_candidates.append((lmarena_id, string_similarity * 0.8))  # 降低权重，因为不是结构化匹配
            
            # 合并候选列表，去重并排序
            all_candidates = candidates + fallback_candidates
            # 按lmarena_id去重（保留相似度最高的）
            unique_candidates = {}
            for lmarena_id, similarity in all_candidates:
                if lmarena_id not in unique_candidates or similarity > unique_candidates[lmarena_id]:
                    unique_candidates[lmarena_id] = similarity
            
            candidates = list(unique_candidates.items())
        
        # 如果没有提取到家族名，完全依赖字符串相似度
        if not benchmark_family and not candidates:
            return self._fallback_string_similarity(raw_name)
        
        # 按相似度降序排序，返回Top-K
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:self.max_candidates]
    
    def _fallback_string_similarity(self, raw_name: str) -> List[Tuple[str, float]]:
        """
        备选方案：如果无法提取家族名，使用传统字符串相似度
        
        注意：这应该很少发生，但作为安全网保留
        使用较低的阈值（0.5）以确保不会遗漏潜在的匹配
        """
        normalized = self.parser.normalize(raw_name)
        candidates = []
        
        for idx, row in self.lmarena_study_universe.iterrows():
            lmarena_normalized = self.parser.normalize(row['Model'])
            similarity = SequenceMatcher(None, normalized, lmarena_normalized).ratio()
            
            # 使用0.5的阈值，确保不会遗漏潜在匹配
            if similarity > 0.5:
                candidates.append((row['Model'], similarity))
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:self.max_candidates]
    
    def resolve_all(self):
        """
        执行完整的实体解析流程
        
        流程：
        1. 遍历所有benchmark的所有模型
        2. 按层级尝试匹配
        3. 生成待审核列表和未匹配列表
        """
        print("\n开始实体解析...")
        
        total_models = sum(len(models) for models in self.benchmark_models.values())
        processed = 0
        
        for benchmark_id, models in self.benchmark_models.items():
            print(f"\n处理 {benchmark_id} ({len(models)} 个模型)...")
            
            for raw_name in models:
                processed += 1
                if processed % 50 == 0:
                    print(f"  已处理 {processed}/{total_models} 个模型...")
                
                # Level 0: 全局精确匹配（低ELO过滤）
                level0_result = self.level_0_exact_match(raw_name)
                if level0_result:
                    lmarena_id, elo = level0_result
                    if elo < self.study_universe_threshold:
                        # 低ELO模型，自动丢弃
                        self.unmatched_log.append({
                            'benchmark': benchmark_id,
                            'raw_name': raw_name,
                            'reason': f'Low ELO ({elo})',
                            'lmarena_id': lmarena_id
                        })
                        continue
                    else:
                        # 高ELO模型，自动映射
                        self.auto_mapped[raw_name] = lmarena_id
                        continue
                
                # Level 1: 研究宇宙精确匹配
                level1_result = self.level_1_target_exact_match(raw_name)
                if level1_result:
                    self.auto_mapped[raw_name] = level1_result
                    continue
                
                # Level 2: 映射表查找
                level2_result = self.level_2_registry_lookup(raw_name)
                if level2_result:
                    self.auto_mapped[raw_name] = level2_result
                    continue
                
                # Level 3: 智能候选生成
                candidates = self.level_3_smart_candidates(raw_name)
                
                if candidates:
                    # 检查是否有高置信度候选（相似度 > 0.8）
                    high_confidence = [c for c in candidates if c[1] > 0.8]
                    
                    if len(high_confidence) == 1:
                        # 只有一个高置信度候选，可以自动映射（但标记为需要验证）
                        # 或者仍然加入待审核列表，取决于策略
                        # 这里我们选择加入待审核，但标记为高置信度
                        self.pending_resolution.append({
                            'benchmark': benchmark_id,
                            'raw_name': raw_name,
                            'proposed_lmarena_id': high_confidence[0][0],
                            'confidence': high_confidence[0][1],
                            'alternative_candidates': '; '.join([f"{c[0]} ({c[1]:.3f})" for c in candidates[1:]])
                        })
                    else:
                        # 多个候选或多个低置信度候选，加入待审核
                        top_candidate = candidates[0]
                        self.pending_resolution.append({
                            'benchmark': benchmark_id,
                            'raw_name': raw_name,
                            'proposed_lmarena_id': top_candidate[0],
                            'confidence': top_candidate[1],
                            'alternative_candidates': '; '.join([f"{c[0]} ({c[1]:.3f})" for c in candidates[1:]])
                        })
                else:
                    # 没有找到候选，加入未匹配日志
                    self.unmatched_log.append({
                        'benchmark': benchmark_id,
                        'raw_name': raw_name,
                        'reason': 'No candidates found',
                        'lmarena_id': ''
                    })
        
        print(f"\n解析完成！")
        print(f"  自动映射: {len(self.auto_mapped)} 个")
        print(f"  待审核: {len(self.pending_resolution)} 个")
        print(f"  未匹配: {len(self.unmatched_log)} 个")
    
    def save_results(self, output_dir: Path):
        """保存结果到CSV文件"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存待审核列表
        if self.pending_resolution:
            pending_path = output_dir / 'pending_resolution.csv'
            with open(pending_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'benchmark', 'raw_name', 'proposed_lmarena_id', 'confidence', 'alternative_candidates'
                ])
                writer.writeheader()
                writer.writerows(self.pending_resolution)
            print(f"\n待审核列表已保存到: {pending_path}")
        
        # 保存未匹配日志
        if self.unmatched_log:
            unmatched_path = output_dir / 'unmatched_log.csv'
            with open(unmatched_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'benchmark', 'raw_name', 'reason', 'lmarena_id'
                ])
                writer.writeheader()
                writer.writerows(self.unmatched_log)
            print(f"未匹配日志已保存到: {unmatched_path}")


def main():
    """
    主函数：执行智能实体解析
    
    使用示例：
    python resolve_identities_smart.py
    """
    # 配置路径
    base_dir = Path(__file__).parent.parent.parent
    lmarena_data_path = base_dir / 'data' / 'cleaned' / 'lmarena' / 'overall' / 'data.csv'
    cleaned_data_dir = base_dir / 'data' / 'cleaned'
    mapping_json_path = base_dir / 'config' / 'mapping.json'
    output_dir = base_dir / 'data' / 'processed' / 'entity_resolution'
    
    # 创建解析器
    resolver = SmartEntityResolver(
        lmarena_data_path=str(lmarena_data_path),
        cleaned_data_dir=str(cleaned_data_dir),
        mapping_json_path=str(mapping_json_path),
        study_universe_threshold=1330,
        max_candidates_per_model=3  # 每个模型最多生成3个候选
    )
    
    # 执行解析
    resolver.load_data()
    resolver.resolve_all()
    resolver.save_results(output_dir)
    
    print("\n智能实体解析完成！")
    print(f"请审查 {output_dir / 'pending_resolution.csv'} 中的候选匹配")


if __name__ == '__main__':
    main()

