from datetime import datetime, timedelta
import math
from timezonefinder import TimezoneFinder # 用于通过经纬度查找时区名称
import pytz # 用于处理历史上的夏令时规则

class SolarTimeCalculator:
    def __init__(self):
        self.tf = TimezoneFinder()

    def _calculate_equation_of_time(self, dt):
        """
        计算均时差 (Equation of Time)，单位：分钟
        这里使用近似公式，误差在秒级，满足八字排盘需求
        """
        day_of_year = dt.timetuple().tm_yday
        b = 2 * math.pi * (day_of_year - 81) / 365.0
        eot = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
        return eot

    def get_true_solar_time(self, birth_str, time_str, longitude, latitude):
        """
        全球通用真太阳时计算入口
        
        Args:
            birth_str: "YYYY-MM-DD"
            time_str: "HH:MM"
            longitude: 经度 (东经正，西经负)
            latitude: 纬度 (用于确定时区)
        """
        # 1. 拼接字符串为 datetime 对象 (此时是 naive time，没有时区概念)
        local_dt_naive = datetime.strptime(f"{birth_str} {time_str}", "%Y-%m-%d %H:%M")
        
        # 2. 【关键一步】根据经纬度获取时区名称 (例如: 'Asia/Shanghai', 'America/New_York')
        timezone_str = self.tf.timezone_at(lng=longitude, lat=latitude)
        if not timezone_str:
            # 如果在海洋上或者找不到，默认兜底处理（通常很少见），这里暂时抛错或默认UTC
            raise ValueError("无法定位该地点的时区信息")
            
        # 3. 【夏令时自动处理】将 naive time 本地化
        # pytz 会自动查询历史数据库：
        # - 如果是 1988年5月1日北京，它会自动识别是夏令时（UTC+9）
        # - 如果是 1984年11月7日北京，它会自动识别是标准时（UTC+8）
        local_tz = pytz.timezone(timezone_str)
        try:
            # is_dst=None 让库自动根据时间判断是否模糊，通常能自动处理
            local_dt_aware = local_tz.localize(local_dt_naive, is_dst=None) 
        except pytz.AmbiguousTimeError:
            # 处理夏令时切换回冬令时那重叠的1小时，通常默认选标准时
            local_dt_aware = local_tz.localize(local_dt_naive, is_dst=False)

        # 4. 转换为 UTC 时间 (世界标准时间)
        # 这一步就把夏令时、时区偏移全部抹平了，变成了纯粹的物理时间
        utc_dt = local_dt_aware.astimezone(pytz.utc)
        
        # 5. 计算真太阳时
        # 公式：真太阳时 = UTC + (经度 * 4分钟) + 均时差
        
        # 5.1 经度校正 (分钟)
        geo_offset_minutes = longitude * 4.0
        
        # 5.2 均时差校正 (分钟)
        eot_minutes = self._calculate_equation_of_time(utc_dt)
        
        # 5.3 最终合成
        total_offset = timedelta(minutes=geo_offset_minutes + eot_minutes)
        true_solar_time = utc_dt + total_offset
        
        # 为了方便展示，通常去掉时区信息，返回“真太阳时的读数”
        # 注意：八字排盘通常需要的是“年月日的干支”，此时用这个 final_time 即可
        final_time_naive = true_solar_time.replace(tzinfo=None)

        return {
            "original_location": f"{timezone_str} (Lng: {longitude})",
            "input_local_time": local_dt_naive,
            "is_dst": bool(local_dt_aware.dst()), # 是否处于夏令时
            "utc_time": utc_dt,
            "true_solar_time": final_time_naive,
            "equation_of_time": round(eot_minutes, 2)
        }

if __name__ == "__main__":
    # --- 验证测试 ---
    calculator = SolarTimeCalculator()
    
    print("--- 案例1：中国北京，非夏令时 (1984-11-07 22:30) ---")
    # 你的原始案例
    res1 = calculator.get_true_solar_time("1984-11-07", "22:30", 116.4, 39.9)
    print(f"输入时间: {res1['input_local_time']}")
    print(f"夏令时?: {res1['is_dst']}") 
    print(f"真太阳时: {res1['true_solar_time']}") 
    # 预期：北京(116.4)比标准(120)慢约14分钟，加上均时差，真太阳时应在 22:15 左右
    
    print("\n--- 案例2：中国北京，夏令时期间 (1988-05-01 12:00) ---")
    # 1988年中国确实有夏令时，12:00 其实是物理时间的 11:00
    res2 = calculator.get_true_solar_time("1988-05-01", "12:00", 116.4, 39.9)
    print(f"输入时间: {res2['input_local_time']}")
    print(f"夏令时?: {res2['is_dst']} (程序自动识别为 True)")
    print(f"真太阳时: {res2['true_solar_time']}")
    # 预期：先减夏令时1小时变11:00，再减经度差14分，结果应在 10:45 左右
    
    print("\n--- 案例3：美国纽约，夏令时期间 (2000-06-01 12:00) ---")
    res3 = calculator.get_true_solar_time("2000-06-01", "12:00", -74.0, 40.7)
    print(f"夏令时?: {res3['is_dst']} (美国每年都有，自动识别)")
    print(f"真太阳时: {res3['true_solar_time']}")