# test_complete.py
"""
完整测试流程
"""

from bazi_service import BaziService
from validator import BaziValidator
import json

def main():
    # ====================================
    # 步骤1: 生成八字
    # ====================================
    print("=" * 70)
    print(" " * 25 + "步骤1: 生成八字")
    print("=" * 70)
    
    service = BaziService()
    
    # 输入信息
    birth_date = "1990-04-26"
    birth_time = "00:53"
    longitude = 104.68
    latitude = 31.03
    gender = "女"


    # birth_date = "1984-11-06"
    # birth_time = "03:00"
    # longitude = 98.588  # 经度
    # latitude = 24.43    # 纬度
    # gender = "男"
    
    print(f"\n输入参数:")
    print(f"  出生日期: {birth_date}")
    print(f"  出生时间: {birth_time}")
    print(f"  经度:     {longitude}°")
    print(f"  纬度:     {latitude}°")
    print(f"  性别:     {gender}")
    
    # 生成八字
    result = service.generate_complete_chart(
        birth_date,
        birth_time,
        longitude,
        latitude,
        gender
    )
    
    print("\n✓ 八字生成完成")
    
    # ====================================
    # 步骤2: 保存完整JSON
    # ====================================
    print("\n" + "=" * 70)
    print(" " * 22 + "步骤2: 保存JSON文件")
    print("=" * 70)
    
    with open("output_full.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("\n✓ 已保存到 output_full.json")
    
    # ====================================
    # 步骤3: 运行验证
    # ====================================
    print("\n" + "=" * 70)
    print(" " * 25 + "步骤3: 数据验证")
    print("=" * 70)
    
    BaziValidator.validate_complete_chart(result)
    
    # ====================================
    # 步骤4: 测试流年分析
    # ====================================
    print("\n" + "=" * 70)
    print(" " * 18 + "步骤4: 测试流年分析 (2024年)")
    print("=" * 70)
    
    liunian_2024 = service.analyze_specific_year(result, 2024)
    
    print("\n流年分析结果:")
    print(json.dumps(liunian_2024, ensure_ascii=False, indent=2))
    
    # 保存流年分析
    with open("output_liunian_2024.json", "w", encoding="utf-8") as f:
        json.dump(liunian_2024, f, ensure_ascii=False, indent=2)
    
    print("\n✓ 流年分析已保存到 output_liunian_2024.json")
    
    # ====================================
    # 完成
    # ====================================
    print("\n" + "=" * 70)
    print(" " * 24 + "✓ 所有测试完成！")
    print("=" * 70)
    print("\n生成的文件:")
    print("  1. output_full.json          - 完整八字数据")
    print("  2. output_liunian_2024.json  - 2024年流年分析")

if __name__ == "__main__":
    main()