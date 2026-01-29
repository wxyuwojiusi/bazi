from test_ztys1 import BaziTimeProcessor
import sys

def get_input(prompt):
    print(prompt, end='', flush=True)
    return sys.stdin.readline().strip()

def main():
    print("--- 八字真太阳时交互式测试工具 (含节气排盘) ---")
    print("输入 q 退出程序")
    
    processor = BaziTimeProcessor()
    
    while True:
        try:
            print("\n" + "="*40)
            
            # 1. 组合输入：日期和时间
            dt_input = get_input("1. 请输入 [YYYY-MM-DD HH:MM] (例如 1984-11-07 23:45): ")
            if dt_input.lower() == 'q': break
            
            parts = dt_input.split()
            if len(parts) != 2:
                print("❌ 格式错误：必须包含日期和时间两部分，用空格分开")
                continue
            birth_date, birth_time = parts[0], parts[1]
            
            # 2. 组合输入：经度和纬度
            loc_input = get_input("2. 请输入 [经度 纬度] (例如 116.4 39.9): ")
            if loc_input.lower() == 'q': break
            
            loc_input = loc_input.replace(',', ' ')
            loc_parts = loc_input.split()
            if len(loc_parts) != 2:
                print("❌ 格式错误：请输入两个数值")
                continue
            longitude = float(loc_parts[0])
            latitude = float(loc_parts[1])
            
            # 调用接口
            result = processor.get_solar_data(birth_date, birth_time, longitude, latitude)
            
            st = result['solar_terms']

            print("-" * 40)
            print("【排盘基础信息 (Base Info)】:")
            print(f"✅ 真太阳时 (true_solar_time)  : {result['true_solar_time']}")
            print(f"   特殊标记 (special_time_marker): {result['special_time_marker']} (影响日柱/时柱)")
            print(f"   命理年份 (bazi_year_int)      : {st['bazi_year_int']}")
            print(f"   命理月令 (month_zhi)          : {st['month_zhi']}")
            
            print("\n【节气深度数据 (Solar Terms)】:")
            print(f"   上个节气 (prev_jie)           : {st['prev_jie']['name']} ({st['prev_jie']['datetime']})")
            print(f"   距上个节 (days_since_prev_jie): {st['days_since_prev_jie']} 天")
            print(f"   下个节气 (next_jie)           : {st['next_jie']['name']} ({st['next_jie']['datetime']})")
            print(f"   距下个节 (days_to_next_jie)   : {st['days_to_next_jie']} 天")
            print(f"   过立春否 (is_after_lichun)    : {st['is_after_lichun']}")
            
            print("-" * 30)
            print("【调试数据 (Debug/DB Info)】:")
            print(f"   原始输入 (original_time)      : {result['original_time']}")
            print(f"   采用时区 (timezone)           : {result['timezone']}")
            print(f"   地理位置 (location)           : {result['location']}")
            print(f"   夏令时?  (is_dst)             : {result['is_dst']}")
            print(f"   均时差   (equation_of_time)   : {result['equation_of_time']} 分钟")
            print(f"   经度差   (geo_offset)         : {result['geo_offset']} 分钟")
            
        except ValueError as e:
            print(f"❌ 数据错误: {e}")
        except Exception as e:
            print(f"❌ 发生异常: {e}")

if __name__ == "__main__":
    main()
