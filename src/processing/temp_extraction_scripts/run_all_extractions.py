"""
运行所有提取脚本
"""

import subprocess
import sys
from pathlib import Path

def run_all_extractions():
    """运行所有提取脚本"""
    scripts_dir = Path(__file__).parent
    
    scripts = sorted(scripts_dir.glob('*_extract.py'))
    
    print(f"找到 {len(scripts)} 个提取脚本")
    print("="*60)
    
    results = []
    
    for script in scripts:
        print(f"\n运行: {script.name}")
        try:
            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=scripts_dir.parent.parent.parent,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if result.returncode == 0:
                print(f"  [OK] 成功: {result.stdout.strip()}")
                results.append((script.name, True, result.stdout.strip()))
            else:
                print(f"  [FAIL] 失败: {result.stderr.strip()}")
                results.append((script.name, False, result.stderr.strip()))
        except Exception as e:
            print(f"  [ERROR] 错误: {e}")
            results.append((script.name, False, str(e)))
    
    print("\n" + "="*60)
    print("运行结果摘要")
    print("="*60)
    success_count = sum(1 for _, success, _ in results if success)
    print(f"成功: {success_count}/{len(results)}")
    print(f"失败: {len(results) - success_count}/{len(results)}")
    
    if len(results) - success_count > 0:
        print("\n失败的脚本:")
        for name, success, msg in results:
            if not success:
                print(f"  - {name}: {msg}")
    
    return results

if __name__ == '__main__':
    run_all_extractions()

