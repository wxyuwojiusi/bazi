# bazi_service.py
"""
八字系统总控服务
负责调度所有模块，组装最终JSON输出
"""

from bazi_time_processor import BaziTimeProcessor
from chart_builder import ChartBuilder
from chart_analyzer import ChartAnalyzer
from timeline_calculator import TimelineCalculator
from bazi_reference import BaziReference

class BaziService:
    """八字系统总控服务"""
    
    def __init__(self):
        self.time_processor = BaziTimeProcessor()
        self.chart_builder = ChartBuilder()
        self.chart_analyzer = ChartAnalyzer()
        self.timeline_calculator = TimelineCalculator()
    
    def generate_complete_chart(self, birth_date, birth_time, longitude, latitude, gender):
        """
        生成完整八字分析
        
        这是对外的唯一接口
        
        Args:
            birth_date: "YYYY-MM-DD"
            birth_time: "HH:MM"
            longitude: 经度
            latitude: 纬度
            gender: "男" 或 "女"
        
        Returns:
            完整的八字分析JSON（给LLM的最终数据）
        """
        # ========================================
        # Step 1: 时间处理（模块1.5）
        # ========================================
        solar_data = self.time_processor.get_solar_data(
            birth_date,
            birth_time,
            longitude,
            latitude
        )
        
        # ========================================
        # Step 2: 排盘（模块1.6 + 1.7 + 1.14）
        # ========================================
        chart_data = self.chart_builder.build_chart(solar_data, gender)
        
        # ========================================
        # Step 3: 特征分析（模块1.8 + 1.9 + 1.12 + 1.13 + 1.10）
        # ========================================
        analysis_result = self.chart_analyzer.analyze(chart_data)
        
        # ========================================
        # Step 4: 参考表准备（模块1.11）
        # ========================================
        reference_tables = self._prepare_reference_tables(chart_data)
        
        # ========================================
        # Step 5: 大运计算（模块3.1）
        # ========================================
        dayun_info = self.timeline_calculator.calculate_dayun(
            chart_data,
            chart_data["solar_terms_data"]
        )
        
        # ========================================
        # Step 6: 组装最终JSON
        # ========================================
        return self._assemble_final_json(
            chart_data,
            analysis_result,
            reference_tables,
            dayun_info
        )
    
    def _prepare_reference_tables(self, chart_data):
        """
        准备参考表数据（给LLM查询用）
        """
        pillars = chart_data["pillars"]
        day_gan = pillars["day"]["gan"]
        month_zhi = pillars["month"]["zhi"]
        
        # 获取季节
        season = BaziReference.get_season(month_zhi)
        
        # 旺相休囚死表
        wangxiang = {}
        for element in ["木", "火", "土", "金", "水"]:
            wangxiang[element] = BaziReference.get_wangxiang(season, element)
        
        # 十二长生表（只列出日主的）
        changsheng = {}
        for zhi in BaziReference.EARTHLY_BRANCHES:
            changsheng[zhi] = BaziReference.get_changsheng_status(day_gan, zhi)
        
        # 调候用神
        tiaohou = BaziReference.get_tiaohou(day_gan, month_zhi)
        
        return {
            "season": season,
            "wangxiang": wangxiang,
            "changsheng": changsheng,
            "tiaohou": tiaohou
        }
    
    def _assemble_final_json(self, chart_data, analysis_result, reference_tables, dayun_info):
        """
        组装最终JSON（嵌套结构 + 完整调试信息）
        
        这是给LLM的最终数据格式
        """
        pillars = chart_data["pillars"]
        
        # 为每个柱子添加十神标注
        def enrich_pillar(pillar, position):
            """给柱子添加十神等额外信息"""
            enriched = pillar.copy()
            
            # 天干十神
            gan = pillar["gan"]
            gan_key = f"{position}{gan}"
            enriched["gan_shishen"] = analysis_result["shishen_map"].get(gan_key, "")
            
            # 🔧 修复：地支藏干十神（从 shishen_map 提取）
            zhi = pillar["zhi"]
            enriched["hidden_stems_detail"] = []
            for stem in pillar["hidden_stems"]:
                stem_key = f"{position}{zhi}藏{stem}"
                enriched["hidden_stems_detail"].append({
                    "stem": stem,
                    "element": BaziReference.get_stem_element(stem),
                    "shishen": analysis_result["shishen_map"].get(stem_key, "未知")
                })
            
            return enriched
        
        return {
            # 🆕 增强：完整基础信息（包含调试数据）
            "basic_info": {
                # 核心信息
                "birth_time": chart_data["basic_info"]["birth_time"],
                "true_solar_time": chart_data["basic_info"]["true_solar_time"],
                "location": chart_data["basic_info"]["location"],
                "timezone": chart_data["basic_info"]["timezone"],
                "gender": chart_data["basic_info"]["gender"],
                "special_time_marker": chart_data["basic_info"]["special_time_marker"],
                
                # 🆕 调试信息
                "debug_info": chart_data.get("debug_info", {})
            },
            
            # 🆕 节气详细信息
            "solar_terms_detail": chart_data.get("solar_terms_data", {}),
            
            "pillars": {
                "year": enrich_pillar(pillars["year"], "年干"),
                "month": enrich_pillar(pillars["month"], "月干"),
                "day": enrich_pillar(pillars["day"], "日干"),
                "time": enrich_pillar(pillars["time"], "时干")
            },
            
            "analysis": {
                "wuxing_count": analysis_result["wuxing_count"],
                "root_analysis": analysis_result["root_analysis"],
                "tougan_check": analysis_result["tougan_check"],
                "internal_interactions": analysis_result["internal_interactions"],
                "special_flags": analysis_result["special_flags"],
                
                # 🆕 新增确定性计算结果，供LLM作为事实依据
                "month_siling": analysis_result.get("month_siling"),
                "wangxiang_stats": analysis_result.get("wangxiang_stats"),
                "interaction_context": analysis_result.get("interaction_context")
            },
            
            "reference_tables": reference_tables,
            
            "dayun": dayun_info
        }
    
    # ========================================
    # 流年分析接口（可选）
    # ========================================
    
    def analyze_specific_year(self, complete_chart, year):
        """
        分析特定流年
        
        Args:
            complete_chart: generate_complete_chart() 的输出
            year: 公历年份
        
        Returns:
            流年分析结果
        """
        # 重建chart_data格式（简化版）
        chart_data = {
            "pillars": complete_chart["pillars"],
            "basic_info": complete_chart["basic_info"]
        }
        
        return self.timeline_calculator.analyze_liunian(
            chart_data,
            complete_chart["dayun"],
            year
        )