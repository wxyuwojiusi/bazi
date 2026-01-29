from datetime import datetime, timedelta
import math
from timezonefinder import TimezoneFinder
import pytz
from lunar_python import Solar

# Bazi只用"节"划分月份，"气"只用于参考（本系统算法主要用节）
# 映射表：节气名称 -> 月支
JIE_ZHI_MAP = {
    "立春": "寅", "惊蛰": "卯", "清明": "辰", 
    "立夏": "巳", "芒种": "午", "小暑": "未", 
    "立秋": "申", "白露": "酉", "寒露": "戌", 
    "立冬": "亥", "大雪": "子", "小寒": "丑"
}

class BaziTimeProcessor:
    def __init__(self):
        # 初始化时区查找器，这是一个比较耗时的操作，建议单例模式或初始化一次
        self.tf = TimezoneFinder()

    def _get_equation_of_time(self, dt):
        """[内部方法] 计算均时差"""
        day_of_year = dt.timetuple().tm_yday
        b = 2 * math.pi * (day_of_year - 81) / 365.0
        return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)

    def _calculate_solar_terms_info(self, true_solar_time):
        """
        计算节气详细信息，为1.6(排盘)、1.14(司令)、3.1(大运)做准备
        """
        # 1. 初始化 Solar 对象
        solar = Solar.fromYmdHms(
            true_solar_time.year,
            true_solar_time.month,
            true_solar_time.day,
            true_solar_time.hour,
            true_solar_time.minute,
            true_solar_time.second
        )
        
        # 2. 获取当年及前一年的所有节气（防止年初边界问题）
        check_years = [true_solar_time.year - 1, true_solar_time.year, true_solar_time.year + 1]
        all_jie_list = []

        for y in check_years:
            # lunar_python 获取一年的节气表 (构造该年6月1日来获取整年表)
            temp_solar = Solar.fromYmdHms(y, 6, 1, 0, 0, 0)
            jie_qi_table = temp_solar.getLunar().getJieQiTable()
            
            for name, solar_obj in jie_qi_table.items():
                if name in JIE_ZHI_MAP:
                    dt = datetime.strptime(solar_obj.toYmdHms(), "%Y-%m-%d %H:%M:%S")
                    all_jie_list.append({
                        "name": name,
                        "datetime": dt,
                        "zhi": JIE_ZHI_MAP[name],
                        "year_belong": y
                    })
        
        # 按时间排序
        all_jie_list.sort(key=lambda x: x["datetime"])
        
        # 3. 核心查找逻辑：找到出生时间夹在中间的两个"节"
        prev_jie = None
        next_jie = None
        
        for i in range(len(all_jie_list) - 1):
            if all_jie_list[i]["datetime"] <= true_solar_time < all_jie_list[i+1]["datetime"]:
                prev_jie = all_jie_list[i]
                next_jie = all_jie_list[i+1]
                break
                
        # 容错处理
        if not prev_jie:
            return {"error": "Date out of range"}

        # 4. 计算立春时刻（用于年柱判定）
        bazi_year_int = true_solar_time.year
        
        # 特殊情况修正：公历1月/2月出生，但月令是小寒(丑月)，说明还没到立春，年柱-1
        if prev_jie["name"] == "小寒" and true_solar_time.month <= 2:
            bazi_year_int = true_solar_time.year - 1
            
        # 获取当年的立春时间
        try:
            lichun_node = next(item for item in all_jie_list if item["name"] == "立春" and item["year_belong"] == bazi_year_int)
            is_after_lichun = true_solar_time >= lichun_node["datetime"]
            lichun_dt_str = lichun_node["datetime"].strftime("%Y-%m-%d %H:%M:%S")
        except StopIteration:
            # 极罕见的边界情况，此时立春可能在数组范围外（需要扩大check_years，一般不会发生）
            lichun_dt_str = "Error"
            is_after_lichun = False

        # 5. 计算时间差 (天)
        diff_to_prev = (true_solar_time - prev_jie["datetime"]).total_seconds() / 86400
        diff_to_next = (next_jie["datetime"] - true_solar_time).total_seconds() / 86400
        
        return {
            "bazi_year_int": bazi_year_int,
            "month_zhi": prev_jie["zhi"],
            "is_after_lichun": is_after_lichun,
            "lichun_datetime": lichun_dt_str,
            "days_since_prev_jie": round(diff_to_prev, 4),
            "prev_jie": {
                "name": prev_jie["name"],
                "datetime": prev_jie["datetime"].strftime("%Y-%m-%d %H:%M:%S")
            },
            "next_jie": {
                "name": next_jie["name"],
                "datetime": next_jie["datetime"].strftime("%Y-%m-%d %H:%M:%S")
            },
            "days_to_next_jie": round(diff_to_next, 4)
        }

    def get_solar_data(self, birth_date_str, birth_time_str, longitude, latitude):
        """
        核心方法：获取排盘所需的完整时间数据
        
        该方法执行以下核心计算：
        1. 物理层：计算真太阳时 (考虑夏令时、均时差、经度差)
        2. 命理层(日时)：判定夜子时/早子时，决定日柱是否换日
        3. 命理层(年月)：根据真太阳时定节气，计算年柱归属和月令
        
        Args:
            birth_date_str: "YYYY-MM-DD"
            birth_time_str: "HH:MM"
            longitude: 经度
            latitude: 纬度
            
        Returns:
            dict: 包含所有计算结果的字典，可直接存入数据库或传给下游排盘模块。
            
        Example Check Output (完整的 JSON 结构示例):
        {
            "true_solar_time": "1984-02-04 09:17:59",  // [关键] 用于排八字的最终时间 (若晚子时已+1天)
            "special_time_marker": "无",               // "无" | "晚子时" | "早子时"
            
            "solar_terms": {  // [关键] 节气与月令数据
                "bazi_year_int": 1983,           // 命理年份 (未过立春算上一年)
                "month_zhi": "丑",               // 月支 (由当月节气决定)
                "is_after_lichun": false,        // 是否已过立春
                "lichun_datetime": "1984-02-04 11:18:00", // 当年立春具体时间
                
                "days_since_prev_jie": 28.9008,  // [关键] 用于计算司令神 (距上个节天数)
                "prev_jie": {                    // 上个节 (月令依据)
                    "name": "小寒",
                    "datetime": "1984-01-06 11:40:51"
                },
                
                "days_to_next_jie": 0.5839,      // [关键] 用于大运起运数 (距下个节天数)
                "next_jie": {                    // 下个节 (顺排大运依据)
                    "name": "立春",
                    "datetime": "1984-02-04 23:18:44"
                }
            },
            
            "original_time": "1984-02-04 10:00", // 原始输入
            "timezone": "Asia/Shanghai",         // 采用时区
            "location": "Lng:113.02, Lat:23.7",  // 地点详情
            "longitude": 113.02,
            "latitude": 23.7,
            "is_dst": false,           // 夏令时
            "equation_of_time": -14.1, // 均时差(分)
            "geo_offset": -27.9        // 经度差(分)
        }
        """
        # ---------------------------------------------------------
        # 第一步：物理时间计算 (夏令时 + 经度 + 均时差)
        # ---------------------------------------------------------
        
        # 1. 组合时间字符串
        local_dt_naive = datetime.strptime(f"{birth_date_str} {birth_time_str}", "%Y-%m-%d %H:%M")
        
        # 2. 自动获取时区 (解决全球通用问题)
        timezone_str = self.tf.timezone_at(lng=longitude, lat=latitude)
        if not timezone_str:
            # 海洋或无法识别区域，兜底默认为UTC（或者你可以报错）
            timezone_str = 'UTC' 
            
        # 3. 转化为带时区的对象 (自动处理夏令时)
        local_tz = pytz.timezone(timezone_str)
        try:
            local_dt_aware = local_tz.localize(local_dt_naive, is_dst=None)
        except pytz.AmbiguousTimeError:
            local_dt_aware = local_tz.localize(local_dt_naive, is_dst=False)

        # 4. 转为 UTC 标准时间
        utc_dt = local_dt_aware.astimezone(pytz.utc)

        # 5. 计算真太阳时
        # 经度时差: 经度 * 4分钟
        geo_offset = longitude * 4.0
        # 均时差
        eot_offset = self._get_equation_of_time(utc_dt)
        
        # 得到真太阳时 (物理上的真实太阳时间)
        true_solar_time = utc_dt + timedelta(minutes=geo_offset + eot_offset)
        # 去掉时区信息，变成单纯的“年月日时分”，方便后续判断
        tst_naive = true_solar_time.replace(tzinfo=None) # True Solar Time (Naive)

        # ---------------------------------------------------------
        # 第二步：命理逻辑处理 
        # ---------------------------------------------------------
        
        # 2.1 日柱/时柱计算 (处理夜子时换日)
        bazi_time = tst_naive
        zi_status = "普通时辰"
        
        # 判定晚子时 (23:00 - 23:59:59) -> 日柱换第二天
        if tst_naive.hour == 23:
            bazi_time = tst_naive + timedelta(days=1)
            zi_status = "晚子时(夜子时)"
        # 判定早子时 (00:00 - 00:59:59) -> 日柱保持当天
        elif tst_naive.hour == 0:
            zi_status = "早子时"

        # 2.2 年柱/月柱计算 (严格基于真太阳时查节气)
        # 注意：传入的是 tst_naive (物理真太阳时)，而不是换日后的 bazi_time
        # 因为立春交节时刻是天文时刻，不随子时换日而改变
        solar_terms_data = self._calculate_solar_terms_info(tst_naive)

        # ---------------------------------------------------------
        # 第三步：返回结构化数据 (数据库存储格式)
        # ---------------------------------------------------------
        
        special_marker = "无"
        if zi_status == "晚子时(夜子时)":
            special_marker = "晚子时"
        elif zi_status == "早子时":
            special_marker = "早子时"

        return {
            # 1. 最终用于排盘的时间 (日柱/时柱依据)
            "true_solar_time": bazi_time.strftime("%Y-%m-%d %H:%M:%S"),
            
            # 2. 原始输入时间
            "original_time": f"{birth_date_str} {birth_time_str}",
            
            # 3. 地理与时区信息
            "location": f"Lng:{longitude}, Lat:{latitude}", 
            "timezone": timezone_str,
            "longitude": longitude,
            "latitude": latitude,
            
            # 4. 时间修正详情
            "is_dst": bool(local_dt_aware.dst()),
            "equation_of_time": round(eot_offset, 2),
            "geo_offset": round(geo_offset, 2),
            
            # 5. 业务标记
            "special_time_marker": special_marker,
            
            # 6. 新增：节气与八字核心数据 (年柱/月柱/大运依据)
            "solar_terms": solar_terms_data
        }

