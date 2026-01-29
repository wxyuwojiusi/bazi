# timeline_calculator.py
"""
大运流年计算器
负责排大运和流年分析
"""

from bazi_reference import BaziReference
from interaction_engine import InteractionEngine

class TimelineCalculator:
    """大运流年计算器"""
    
    def __init__(self):
        pass
    
    def calculate_dayun(self, chart_data, solar_terms_data):
        """
        计算大运
        
        Args:
            chart_data: ChartBuilder.build_chart() 的输出
            solar_terms_data: 节气数据（来自chart_data["solar_terms_data"]）
        
        Returns:
            {
                "direction": "顺排|逆排",
                "qiyun_age": 3,
                "qiyun_date": "1987-11-07",
                "dayun_list": [...]
            }
        """
        pillars = chart_data["pillars"]
        gender = chart_data["basic_info"]["gender"]
        
        year_gan = pillars["year"]["gan"]
        month_gan = pillars["month"]["gan"]
        month_zhi = pillars["month"]["zhi"]
        
        # 1. 判断顺逆
        direction = self._determine_direction(year_gan, gender)
        
        # 2. 计算起运岁数
        qiyun_info = self._calculate_qiyun_age(
            solar_terms_data,
            direction
        )
        
        # 3. 生成大运序列
        dayun_list = self._generate_dayun_sequence(
            month_gan,
            month_zhi,
            direction,
            qiyun_info["qiyun_age"]
        )
        
        return {
            "direction": direction,
            "qiyun_age": qiyun_info["qiyun_age"],
            "qiyun_date": qiyun_info["qiyun_date"],
            "calculation_detail": qiyun_info["calculation"],
            "dayun_list": dayun_list
        }
    
    def _determine_direction(self, year_gan, gender):
        """
        确定大运顺逆
        
        规则：
        - 阳男阴女：顺排
        - 阴男阳女：逆排
        """
        is_yang_year = year_gan in BaziReference.YANG_STEMS
        
        if gender == "男":
            return "顺排" if is_yang_year else "逆排"
        else:  # 女
            return "顺排" if not is_yang_year else "逆排"
    
    def _calculate_qiyun_age(self, solar_terms_data, direction):
        """
        计算起运岁数
        
        规则：
        - 顺排：从出生时刻顺数到下一个"节"
        - 逆排：从出生时刻逆数到上一个"节"
        - 3天=1岁，1天=4个月，1时辰=10天
        
        Returns:
            {
                "qiyun_age": 3,
                "qiyun_date": "1987-11-07",
                "calculation": "10.5天 ÷ 3 = 3.5岁，取整为3岁"
            }
        """
        if direction == "顺排":
            days = solar_terms_data["days_to_next_jie"]
            target_jie = solar_terms_data["next_jie"]["name"]
        else:
            days = solar_terms_data["days_since_prev_jie"]
            target_jie = solar_terms_data["prev_jie"]["name"]
        
        # 3天 = 1岁
        years = days / 3
        
        # 取整（四舍五入）
        qiyun_age = round(years)
        
        # 如果起运岁数为0，按1岁起运（命理惯例）
        if qiyun_age == 0:
            qiyun_age = 1
        
        # 粗略计算起运日期（实际应该从节气时刻推算）
        from datetime import datetime, timedelta
        
        # 这里简化处理，实际应该用节气datetime
        birth_year = solar_terms_data.get("bazi_year_int", 1984)
        qiyun_date = f"{birth_year + qiyun_age}-01-01"  # 简化
        
        return {
            "qiyun_age": qiyun_age,
            "qiyun_date": qiyun_date,
            "target_jie": target_jie,
            "calculation": f"{round(days, 2)}天 ÷ 3 = {round(years, 2)}岁，取整为{qiyun_age}岁"
        }
    
    def _generate_dayun_sequence(self, month_gan, month_zhi, direction, qiyun_age):
        """
        生成大运序列
        
        Args:
            month_gan: 月柱天干
            month_zhi: 月柱地支
            direction: "顺排" 或 "逆排"
            qiyun_age: 起运岁数
        
        Returns:
            [
                {"age_range": "3-12岁", "start_age": 3, "end_age": 12, "gan": "丙", "zhi": "子"},
                ...
            ]
        """
        gan_sequence = BaziReference.HEAVENLY_STEMS
        zhi_sequence = BaziReference.EARTHLY_BRANCHES
        
        # 找到月柱干支的索引
        current_gan_index = gan_sequence.index(month_gan)
        current_zhi_index = zhi_sequence.index(month_zhi)
        
        dayun_list = []
        current_age = qiyun_age
        
        for i in range(8):  # 一般排8步大运
            if direction == "顺排":
                gan_index = (current_gan_index + i + 1) % 10
                zhi_index = (current_zhi_index + i + 1) % 12
            else:  # 逆排
                gan_index = (current_gan_index - i - 1) % 10
                zhi_index = (current_zhi_index - i - 1) % 12
            
            gan = gan_sequence[gan_index]
            zhi = zhi_sequence[zhi_index]
            
            dayun_list.append({
                "age_range": f"{current_age}-{current_age + 9}岁",
                "start_age": current_age,
                "end_age": current_age + 9,
                "gan": gan,
                "zhi": zhi,
                "pillar": f"{gan}{zhi}",
                "nayin": BaziReference.get_nayin(gan, zhi)
            })
            
            current_age += 10
        
        return dayun_list
    
    # ============================================
    # 流年分析（预留接口）
    # ============================================
    
    def analyze_liunian(self, chart_data, dayun_info, year):
        """
        分析特定流年
        
        Args:
            chart_data: 原局八字
            dayun_info: 当前大运信息
            year: 公历年份
        
        Returns:
            流年分析结果
        """
        # 获取流年干支
        liunian_ganzhi = BaziReference.get_ganzhi(year)
        liunian = {
            "year": year,
            "gan": liunian_ganzhi[0],
            "zhi": liunian_ganzhi[1]
        }
        
        # 找到对应的大运
        dayun_list = dayun_info["dayun_list"]
        current_age = year - chart_data["pillars"]["year"]["year_int"]
        
        current_dayun = None
        for dayun in dayun_list:
            if dayun["start_age"] <= current_age <= dayun["end_age"]:
                current_dayun = dayun
                break
        
        if not current_dayun:
            return {"error": "未找到对应大运"}
        
        # 检测流年与原局、大运的关系
        interactions = self._check_liunian_interactions(
            chart_data["pillars"],
            current_dayun,
            liunian
        )
        
        return {
            "liunian": liunian,
            "current_dayun": current_dayun,
            "interactions": interactions
        }
    
    def _check_liunian_interactions(self, pillars, dayun, liunian):
        """
        检测流年与原局、大运的刑冲合害
        
        Returns:
            {
                "liunian_vs_yuanju": [...],
                "liunian_vs_dayun": [...],
                "tianke_dichong": {...},
                "suiyun_binglin": {...}
            }
        """
        interactions = {
            "liunian_vs_yuanju": [],
            "liunian_vs_dayun": [],
            "tianke_dichong": {},
            "suiyun_binglin": {}
        }
        
        # 1. 流年 vs 原局四支
        positions = {
            "年支": pillars["year"]["zhi"],
            "月支": pillars["month"]["zhi"],
            "日支": pillars["day"]["zhi"],
            "时支": pillars["time"]["zhi"]
        }
        
        for pos_name, original_zhi in positions.items():
            # 六合检测
            he_result = InteractionEngine.check_he(liunian["zhi"], original_zhi)
            if he_result["is_he"]:
                interactions["liunian_vs_yuanju"].append({
                    "type": "六合",
                    "liunian_zhi": liunian["zhi"],
                    "original_position": pos_name,
                    "original_zhi": original_zhi,
                    "hehuan_element": he_result["hehuan_element"],
                    "note": f"流年{liunian['zhi']}与{pos_name}{original_zhi}六合化{he_result['hehuan_element']}"
                })
            
            # 六冲检测
            if InteractionEngine.check_chong(liunian["zhi"], original_zhi):
                interactions["liunian_vs_yuanju"].append({
                    "type": "六冲",
                    "liunian_zhi": liunian["zhi"],
                    "original_position": pos_name,
                    "original_zhi": original_zhi,
                    "note": f"流年{liunian['zhi']}与{pos_name}{original_zhi}相冲"
                })
        
        # 2. 流年 vs 大运
        dayun_pillar = {"gan": dayun["gan"], "zhi": dayun["zhi"]}
        liunian_pillar = {"gan": liunian["gan"], "zhi": liunian["zhi"]}
        
        # 六合检测
        he_result = InteractionEngine.check_he(liunian["zhi"], dayun["zhi"])
        if he_result["is_he"]:
            interactions["liunian_vs_dayun"].append({
                "type": "六合",
                "note": f"流年{liunian['zhi']}与大运{dayun['zhi']}六合化{he_result['hehuan_element']}"
            })
        
        # 六冲检测
        if InteractionEngine.check_chong(liunian["zhi"], dayun["zhi"]):
            interactions["liunian_vs_dayun"].append({
                "type": "六冲",
                "note": f"流年{liunian['zhi']}与大运{dayun['zhi']}相冲"
            })
        
        # 天克地冲检测
        tianke_dichong_result = InteractionEngine.check_tianke_dichong(
            dayun_pillar,
            liunian_pillar
        )
        interactions["tianke_dichong"] = tianke_dichong_result
        
        # 岁运并临检测
        if dayun["gan"] == liunian["gan"] and dayun["zhi"] == liunian["zhi"]:
            interactions["suiyun_binglin"] = {
                "is_binglin": True,
                "pillar": f"{dayun['gan']}{dayun['zhi']}",
                "severity": "极凶",
                "note": "⚠️ 岁运并临（大运流年干支完全相同），主大变动、重大事件，需谨慎应对"
            }
        else:
            interactions["suiyun_binglin"] = {"is_binglin": False}
        
        return interactions