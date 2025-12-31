"""
测试实体解析算法的改进功能

用于验证：
1. o1/o3 别名区分
2. 格式多样性处理（点号、空格、括号）
3. 完整性保证
"""

from resolve_identities_smart import ModelNameParser, StructuredMatcher

def test_normalization():
    """测试标准化功能"""
    parser = ModelNameParser()
    
    test_cases = [
        ("GPT-4.5", "gpt-4-5"),  # 点号处理
        ("GPT 4.5", "gpt-4-5"),  # 空格处理
        ("GPT_4.5", "gpt-4-5"),  # 下划线处理
        ("GPT-4-5", "gpt-4-5"),  # 连字符
        ("GPT-5.1 (high)", "gpt-5-1-high"),  # 括号和点号
        ("o1-mini", "o1-mini"),  # 特殊系列
    ]
    
    print("=== 测试标准化功能 ===")
    for input_name, expected in test_cases:
        result = parser.normalize(input_name)
        status = "✅" if result == expected else "❌"
        print(f"{status} {input_name:20} → {result:20} (期望: {expected})")
    print()

def test_family_extraction():
    """测试家族提取，特别是o1/o3区分"""
    parser = ModelNameParser()
    
    test_cases = [
        ("o1", "o1"),  # 应该提取为o1
        ("o1-mini", "o1"),  # 应该提取为o1
        ("o3-2025-04-16", "o3"),  # 应该提取为o3
        ("o1p", "o1p"),  # 未知变体，提取为o1p
        ("GPT-4.5", "gpt"),  # GPT家族
        ("gpt-5.1-high", "gpt"),  # GPT家族
        ("Claude 3.5 Sonnet", "claude"),  # Claude家族
    ]
    
    print("=== 测试家族提取 ===")
    for input_name, expected_family in test_cases:
        parsed = parser.parse(input_name)
        result_family = parsed.get('family')
        status = "✅" if result_family == expected_family else "❌"
        print(f"{status} {input_name:25} → 家族: {result_family:15} (期望: {expected_family})")
    print()

def test_family_matching():
    """测试家族匹配，验证o1不匹配o3"""
    parser = ModelNameParser()
    matcher = StructuredMatcher(parser)
    
    test_cases = [
        (("o1", "o1"), True, "o1 应该匹配 o1"),
        (("o1", "o3"), False, "o1 不应该匹配 o3"),
        (("o1-mini", "o1-xxx"), True, "o1-mini 应该匹配 o1-xxx"),
        (("gpt-4", "gpt-5"), True, "gpt-4 应该匹配 gpt-5（同家族）"),
        (("gpt-4", "glm-4"), False, "gpt-4 不应该匹配 glm-4（不同家族）"),
    ]
    
    print("=== 测试家族匹配 ===")
    for (name1, name2), should_match, description in test_cases:
        parsed1 = parser.parse(name1)
        parsed2 = parser.parse(name2)
        family1 = parsed1.get('family')
        family2 = parsed2.get('family')
        
        matches, score = matcher.family_match(family1, family2)
        status = "✅" if matches == should_match else "❌"
        print(f"{status} {name1:15} vs {name2:15}: 匹配={matches}, 分数={score:.2f} - {description}")
    print()

def test_variant_extraction():
    """测试变体提取（括号、变体标记）"""
    parser = ModelNameParser()
    
    test_cases = [
        ("GPT-5.1 (high)", {"high"}),
        ("GPT-5.1 (high, thinking)", {"high", "thinking"}),
        ("gpt-5.1-high", {"high"}),
        ("o1-mini", {"mini"}),
    ]
    
    print("=== 测试变体提取 ===")
    for input_name, expected_variants in test_cases:
        parsed = parser.parse(input_name)
        result_variants = parsed.get('variant', set())
        status = "✅" if result_variants == expected_variants else "⚠️"
        print(f"{status} {input_name:30} → 变体: {result_variants} (期望: {expected_variants})")
    print()

if __name__ == '__main__':
    print("实体解析算法测试\n")
    print("=" * 60)
    
    test_normalization()
    test_family_extraction()
    test_family_matching()
    test_variant_extraction()
    
    print("=" * 60)
    print("测试完成！")

