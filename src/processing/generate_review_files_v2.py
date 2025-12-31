"""
生成待审核文件（版本2 - JSON格式）

基于结构化信息匹配：
- 家族、子家族、版本号必须完全一致（版本号会标准化：3和3.0视为相同）
- 参数量如果都有且不一致，则排除匹配
- 日期不参与筛选（不同格式可能对应同一模型）
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Set, Optional
import pandas as pd


class StructuredMatcher:
    """基于结构化信息的匹配器"""
    
    def _normalize_version(self, version: Optional[str]) -> Optional[str]:
        """标准化版本号：3和3.0视为相同"""
        if version is None:
            return None
        
        try:
            # 尝试转换为浮点数，然后标准化
            version_float = float(version)
            # 如果小数点后是0，去掉.0
            if version_float == int(version_float):
                return str(int(version_float))
            else:
                return str(version_float)
        except (ValueError, TypeError):
            # 无法转换为数字，返回原值
            return version
    
    def can_match(self, info1: Dict, info2: Dict) -> bool:
        """
        判断两个模型信息是否可以匹配
        
        规则：
        1. 家族、子家族必须完全一致
        2. 版本号必须一致（会标准化：3和3.0视为相同）
        3. 参数量如果都有且不一致，则排除匹配
        4. 日期不参与筛选
        """
        # 规则1: 家族必须一致
        if info1.get('family') != info2.get('family'):
            return False
        
        # 规则2: 子家族必须一致（如果都有）
        subfamily1 = info1.get('subfamily')
        subfamily2 = info2.get('subfamily')
        
        # 如果两个都有子家族，必须一致
        if subfamily1 is not None and subfamily2 is not None:
            if subfamily1 != subfamily2:
                return False
        
        # 如果只有一个有子家族，另一个没有，不匹配
        if (subfamily1 is None) != (subfamily2 is None):
            return False
        
        # 规则3: 版本号必须一致（标准化后比较）
        version1 = self._normalize_version(info1.get('version'))
        version2 = self._normalize_version(info2.get('version'))
        
        if version1 is not None and version2 is not None:
            if version1 != version2:
                return False
        
        # 如果只有一个有版本号，另一个没有，不匹配
        if (version1 is None) != (version2 is None):
            return False
        
        # 规则4: 参数量如果都有且不一致，排除匹配
        param1 = info1.get('parameters')
        param2 = info2.get('parameters')
        
        if param1 is not None and param2 is not None:
            if param1 != param2:
                return False
        
        # 规则5: 日期不参与筛选（已删除）
        
        return True


def load_model_info(info_file: Path) -> Dict[str, Dict]:
    """加载模型信息"""
    if not info_file.exists():
        return {}
    
    with open(info_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_review_file_json(
    benchmark_id: str,
    benchmark_models_info: Dict[str, Dict],
    lmarena_models_info: Dict[str, Dict],
    output_file: Path
):
    """为单个benchmark生成JSON格式的审核文件"""
    matcher = StructuredMatcher()
    
    # 构建JSON结构：按benchmark_model组织
    review_data = {}
    
    print(f"  处理 {len(benchmark_models_info)} 个模型...")
    
    for benchmark_model, benchmark_info in benchmark_models_info.items():
        # 找到所有可能匹配的LMArena模型
        candidates = []
        
        for lmarena_model, lmarena_info in lmarena_models_info.items():
            if matcher.can_match(benchmark_info, lmarena_info):
                # 添加完整的LMArena模型信息
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
        
        # 构建benchmark模型的信息
        review_data[benchmark_model] = {
            'benchmark_info': {
                'family': benchmark_info.get('family'),
                'subfamily': benchmark_info.get('subfamily'),
                'version': benchmark_info.get('version'),
                'date': benchmark_info.get('date'),
                'parameters': benchmark_info.get('parameters'),
                'other_info': benchmark_info.get('other_info'),
            },
            'candidates': candidates if candidates else [{'lmarena_model': 'NO_MATCH_FOUND'}]
        }
    
    # 写入JSON文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(review_data, f, indent=2, ensure_ascii=False)
    
    # 统计信息
    if review_data:
        total_candidates = sum(len(data['candidates']) for data in review_data.values())
        no_match_count = sum(1 for data in review_data.values() 
                             if data['candidates'][0].get('lmarena_model') == 'NO_MATCH_FOUND')
        
        print(f"  已生成: {output_file}")
        print(f"    总模型数: {len(review_data)}")
        print(f"    总候选数: {total_candidates} (平均 {total_candidates/len(review_data):.2f} 个/模型)")
        print(f"    未匹配数: {no_match_count}")
    else:
        print(f"  已生成: {output_file} (无模型数据)")


def main():
    """主函数"""
    base_dir = Path(__file__).parent.parent.parent
    model_info_dir = base_dir / 'data' / 'processed' / 'model_extraction'
    output_dir = base_dir / 'data' / 'processed' / 'entity_resolution' / 'review_files_v2'
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载LMArena模型信息
    lmarena_info_file = model_info_dir / 'lmarena_models.json'
    lmarena_models_info = load_model_info(lmarena_info_file)
    
    if not lmarena_models_info:
        print("错误: 未找到LMArena模型信息，请先运行 extract_model_info.py")
        return
    
    print(f"加载了 {len(lmarena_models_info)} 个LMArena模型")
    
    # 处理所有benchmark
    artificial_analysis_processed = False
    
    for info_file in model_info_dir.glob('*_models.json'):
        if info_file.name == 'all_models_info.json':
            continue
        
        benchmark_id = info_file.stem.replace('_models', '').replace('_', '/')
        
        # 特殊处理：artificial_analysis
        if benchmark_id == 'artificial_analysis':
            if artificial_analysis_processed:
                continue
            artificial_analysis_processed = True
            
            benchmark_models_info = load_model_info(info_file)
            output_file = output_dir / 'artificial_analysis_review.json'
            
            print(f"\n生成 artificial_analysis 审核文件（将应用到所有10个benchmark）...")
            generate_review_file_json(
                'artificial_analysis',
                benchmark_models_info,
                lmarena_models_info,
                output_file
            )
            continue
        
        # 其他benchmark正常处理
        benchmark_models_info = load_model_info(info_file)
        safe_name = benchmark_id.replace('/', '_').replace('\\', '_')
        output_file = output_dir / f'{safe_name}_review.json'
        
        print(f"\n生成 {benchmark_id} 审核文件...")
        generate_review_file_json(
            benchmark_id,
            benchmark_models_info,
            lmarena_models_info,
            output_file
        )
    
    print("\n" + "="*60)
    print("待审核文件生成完成！")
    print(f"文件位置: {output_dir}")
    print("文件格式: JSON")
    print("="*60)


if __name__ == '__main__':
    main()
