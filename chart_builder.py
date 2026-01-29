# chart_builder.py
"""
四柱排盘构建器
负责从时间数据生成完整的四柱八字，包括司令神和藏干
"""

from bazi_reference import BaziReference

class ChartBuilder:
    """四柱排盘构建器"""
    
    def __init__(self):
        pass
    
    def build_chart(self, solar_data, gender):
        """
        构建完整八字
        
        Args:
            solar_data: BaziTimeProcessor.get_solar_data() 的输出
            gender: "男" 或 "女"
        
        Returns:
            完整的八字对象
        """
        # 提取关键数据
        true_solar_time_str = solar_data["true_solar_time"]
        solar_terms = solar_data["solar_terms"]
        
        # 解析真太阳时
        from datetime import datetime
        true_solar_time = datetime.strptime(true_solar_time_str, "%Y-%m-%d %H:%M:%S")
        
        # 构建四柱
        pillars = self._build_pillars(true_solar_time, solar_terms)
        
        # 返回完整结构（保存所有原始数据）
        return {
            "basic_info": {
                "birth_time": solar_data["original_time"],
                "true_solar_time": true_solar_time_str,
                "location": solar_data["location"],
                "timezone": solar_data["timezone"],
                "gender": gender,
                "special_time_marker": solar_data.get("special_time_marker", "无")
            },
            "pillars": pillars,
            "solar_terms_data": solar_terms,
            
            # 保存调试信息
            "debug_info": {
                "is_dst": solar_data.get("is_dst", False),
                "equation_of_time": solar_data.get("equation_of_time", 0),
                "geo_offset": solar_data.get("geo_offset", 0),
                "longitude": solar_data.get("longitude", 0),
                "latitude": solar_data.get("latitude", 0)
            }
        }
    
    def _build_pillars(self, true_solar_time, solar_terms):
        """
        构建四柱（核心逻辑）
        
        🔧 修改：采用两步法计算司令十神
        1. 第一步：排完四柱（司令暂不计算十神）
        2. 第二步：用日干补充司令十神
        
        包含：
        - 年柱
        - 月柱（包含司令神）
        - 日柱
        - 时柱
        """
        # 1. 年柱
        year_pillar = self._build_year_pillar(solar_terms["bazi_year_int"])
        
        # 2. 月柱（第一步：暂不计算司令十神）
        month_pillar = self._build_month_pillar(
            year_pillar["gan"],
            solar_terms["month_zhi"],
            solar_terms["days_since_prev_jie"],
            day_gan=None  # 🆕 第一步不传日干
        )
        
        # 3. 日柱
        day_pillar = self._build_day_pillar(true_solar_time)
        
        # 4. 时柱
        time_pillar = self._build_time_pillar(
            day_pillar["gan"],
            true_solar_time.hour
        )
        
        # 🆕 第二步：补充司令十神
        day_gan = day_pillar["gan"]
        if month_pillar.get("siling"):
            month_pillar["siling"]["shishen"] = BaziReference.get_shishen(
                day_gan, 
                month_pillar["siling"]["stem"]
            )
        
        return {
            "year": year_pillar,
            "month": month_pillar,
            "day": day_pillar,
            "time": time_pillar
        }
    
    def _build_year_pillar(self, bazi_year_int):
        """
        构建年柱
        
        Args:
            bazi_year_int: 命理年份（已由模块1.5计算）
        
        Returns:
            年柱对象
        """
        ganzhi = BaziReference.get_ganzhi(bazi_year_int)
        gan = ganzhi[0]
        zhi = ganzhi[1]
        
        return {
            "gan": gan,
            "zhi": zhi,
            "ganzhi": ganzhi,
            "hidden_stems": BaziReference.get_hidden_stems(zhi),
            "nayin": BaziReference.get_nayin(gan, zhi),
            "year_int": bazi_year_int
        }
    
    def _build_month_pillar(self, year_gan, month_zhi, days_since_prev_jie, day_gan=None):
        """
        构建月柱（重点：包含司令计算）
        
        🔧 修改：支持传入日干以计算司令十神
        
        Args:
            year_gan: 年干（用于五虎遁）
            month_zhi: 月支（已由模块1.5确定）
            days_since_prev_jie: 距离节气的天数（用于司令计算）
            day_gan: 日干（用于计算司令十神，可选）
        
        Returns:
            月柱对象（包含司令信息）
        """
        # 1. 五虎遁推月干
        month_gan = self._wuhu_dun(year_gan, month_zhi)
        
        # 2. 计算司令神（模块1.14）
        # 🆕 传入day_gan参数
        siling_info = BaziReference.get_siling_info(
            month_zhi, 
            days_since_prev_jie,
            day_gan  # 🆕 传入日干（可能为None）
        )
        
        # 3. 获取藏干
        hidden_stems = BaziReference.get_hidden_stems(month_zhi)
        
        return {
            "gan": month_gan,
            "zhi": month_zhi,
            "ganzhi": month_gan + month_zhi,
            "hidden_stems": hidden_stems,
            "siling": siling_info,  # 司令信息嵌套在这里
            "nayin": BaziReference.get_nayin(month_gan, month_zhi)
        }
    
    def _build_day_pillar(self, true_solar_time):
        """
        构建日柱
        
        使用lunar-python库
        """
        from lunar_python import Solar
        
        solar = Solar.fromYmdHms(
            true_solar_time.year,
            true_solar_time.month,
            true_solar_time.day,
            true_solar_time.hour,
            true_solar_time.minute,
            true_solar_time.second
        )
        
        lunar = solar.getLunar()
        day_gan_zhi = lunar.getDayInGanZhi()
        
        gan = day_gan_zhi[0]
        zhi = day_gan_zhi[1]
        
        return {
            "gan": gan,
            "zhi": zhi,
            "ganzhi": day_gan_zhi,
            "hidden_stems": BaziReference.get_hidden_stems(zhi),
            "nayin": BaziReference.get_nayin(gan, zhi)
        }
    
    def _build_time_pillar(self, day_gan, hour):
        """
        构建时柱
        
        Args:
            day_gan: 日干（用于五鼠遁）
            hour: 小时（0-23）
        
        Returns:
            时柱对象
        """
        # 1. 小时转时支
        time_zhi = self._hour_to_zhi(hour)
        
        # 2. 五鼠遁推时干
        time_gan = self._wushu_dun(day_gan, time_zhi)
        
        return {
            "gan": time_gan,
            "zhi": time_zhi,
            "ganzhi": time_gan + time_zhi,
            "hidden_stems": BaziReference.get_hidden_stems(time_zhi),
            "nayin": BaziReference.get_nayin(time_gan, time_zhi)
        }
    
    # ============================================
    # 辅助方法（保持不变）
    # ============================================
    
    def _wuhu_dun(self, year_gan, month_zhi):
        """
        五虎遁月法
        
        口诀：
        甲己之年丙作首，乙庚之岁戊为头
        丙辛必定寻庚起，丁壬壬位顺行流
        若问戊癸何方发，甲寅之上好追求
        """
        # 月干起点表
        start_gan_map = {
            '甲': '丙', '己': '丙',
            '乙': '戊', '庚': '戊',
            '丙': '庚', '辛': '庚',
            '丁': '壬', '壬': '壬',
            '戊': '甲', '癸': '甲'
        }
        
        start_gan = start_gan_map[year_gan]
        
        # 从寅月开始顺推
        zhi_sequence = ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑']
        gan_sequence = BaziReference.HEAVENLY_STEMS
        
        start_gan_index = gan_sequence.index(start_gan)
        month_zhi_index = zhi_sequence.index(month_zhi)
        
        month_gan_index = (start_gan_index + month_zhi_index) % 10
        return gan_sequence[month_gan_index]
    
    def _wushu_dun(self, day_gan, time_zhi):
        """
        五鼠遁时法
        
        口诀：
        甲己还加甲，乙庚丙作初
        丙辛从戊起，丁壬庚子居
        戊癸何方发，壬子是真途
        """
        # 时干起点表
        start_gan_map = {
            '甲': '甲', '己': '甲',
            '乙': '丙', '庚': '丙',
            '丙': '戊', '辛': '戊',
            '丁': '庚', '壬': '庚',
            '戊': '壬', '癸': '壬'
        }
        
        start_gan = start_gan_map[day_gan]
        
        # 从子时开始顺推
        zhi_sequence = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        gan_sequence = BaziReference.HEAVENLY_STEMS
        
        start_gan_index = gan_sequence.index(start_gan)
        time_zhi_index = zhi_sequence.index(time_zhi)
        
        time_gan_index = (start_gan_index + time_zhi_index) % 10
        return gan_sequence[time_gan_index]
    
    def _hour_to_zhi(self, hour):
        """
        小时转时支
        
        注意：23:00-00:59 是子时（已由BaziTimeProcessor处理）
        """
        hour_to_zhi_map = [
            '子',  # 23-1
            '丑',  # 1-3
            '寅',  # 3-5
            '卯',  # 5-7
            '辰',  # 7-9
            '巳',  # 9-11
            '午',  # 11-13
            '未',  # 13-15
            '申',  # 15-17
            '酉',  # 17-19
            '戌',  # 19-21
            '亥'   # 21-23
        ]
        
        # 将24小时转换为时支索引
        if hour == 23:
            return '子'
        else:
            index = (hour + 1) // 2
            return hour_to_zhi_map[index]