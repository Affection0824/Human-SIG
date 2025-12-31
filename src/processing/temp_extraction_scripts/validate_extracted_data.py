"""
验证提取的模型信息，检查不合理之处
"""

import json
from pathlib import Path
from collections import defaultdict

def validate_json_file(json_file: Path) -> list:
    """验证单个 JSON 文件，返回问题列表"""
    issues = []
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 统计信息
    families = defaultdict(int)
    versions = defaultdict(int)
    no_family = []
    duplicate_versions = []
    
    for model_name, info in data.items():
        # 检查 1: 没有提取出家族名
        if not info.get('family'):
            no_family.append(model_name)
            issues.append(f"  - {model_name}: 未提取出家族名")
        
        # 检查 2: 版本号格式不一致
        version = info.get('version')
        if version:
            # 检查版本号格式（应该是 "X.0" 或 "X.Y" 格式）
            try:
                v_float = float(version)
                if v_float == int(v_float):
                    expected = f"{int(v_float)}.0"
                    if version != expected:
                        issues.append(f"  - {model_name}: 版本号格式不一致，应为 {expected}，实际为 {version}")
            except ValueError:
                issues.append(f"  - {model_name}: 版本号格式异常: {version}")
        
        # 检查 3: other_info 中包含版本号（说明提取逻辑有问题）
        other_info = info.get('other_info')
        if other_info and version:
            version_clean = version.replace('.0', '').replace('.', '')
            for item in other_info:
                if version_clean in str(item) or version in str(item):
                    issues.append(f"  - {model_name}: other_info 中包含版本号 {version}: {item}")
        
        # 检查 4: 家族名不在已知家族列表中（可能是提取错误）
        family = info.get('family')
        if family:
            families[family] += 1
            # 检查是否是合理的家族名（至少应该是小写字母）
            if not family.islower() or not family.isalpha():
                issues.append(f"  - {model_name}: 家族名格式异常: {family}")
    
    # 检查 5: 统计信息
    if no_family:
        issues.insert(0, f"  未提取出家族名的模型数量: {len(no_family)}")
    
    return issues


def main():
    """主函数：验证所有 JSON 文件"""
    base_dir = Path(__file__).parent.parent.parent.parent
    json_dir = base_dir / 'data' / 'processed' / 'model_extraction'
    
    json_files = sorted(json_dir.glob('*_models.json'))
    
    print("="*60)
    print("验证提取的模型信息")
    print("="*60)
    
    total_issues = 0
    
    for json_file in json_files:
        print(f"\n检查: {json_file.name}")
        issues = validate_json_file(json_file)
        
        if issues:
            print(f"  发现 {len(issues)} 个问题:")
            for issue in issues[:20]:  # 只显示前20个问题
                print(issue)
            if len(issues) > 20:
                print(f"  ... 还有 {len(issues) - 20} 个问题")
            total_issues += len(issues)
        else:
            print("  [OK] 未发现问题")
    
    print("\n" + "="*60)
    print(f"总计发现 {total_issues} 个问题")
    print("="*60)
    
    return total_issues


if __name__ == '__main__':
    main()

