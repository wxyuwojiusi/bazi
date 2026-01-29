# example_usage.py
"""
完整使用示例
"""

from bazi_service import BaziService

# 创建服务实例
service = BaziService()

# 输入信息
birth_date = "1984-11-06"
birth_time = "03:00"
longitude = 98.588  # 经度
latitude = 24.43    # 纬度
gender = "男"

# 生成完整八字分析
result = service.generate_complete_chart(
    birth_date,
    birth_time,
    longitude,
    latitude,
    gender
)

# 输出结果（这就是给LLM的数据）
import json
print(json.dumps(result, ensure_ascii=False, indent=2))

# 可选：分析特定流年
liunian_2024 = service.analyze_specific_year(result, 2024)
print(json.dumps(liunian_2024, ensure_ascii=False, indent=2))