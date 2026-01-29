# validator.py
"""
八字数据验证工具
帮助你理解和验证每一步的计算结果
"""

from bazi_reference import BaziReference

class BaziValidator:
    """八字验证器"""
    
    @staticmethod
    def validate_complete_chart(result):
        """
        全面验证八字数据
        
        输出人类可读的验证报告
        """
        print("=" * 70)
        print(" " * 20 + "八字数据验证报告")
        print("=" * 70)
        
        # 1. 基础信息验证
        print("\n【第一步：基础信息验证】")
        BaziValidator._validate_basic_info(result["basic_info"])
        
        # 2. 节气信息验证
        if "solar_terms_detail" in result:
            print("\n【第二步：节气信息验证】")
            BaziValidator._validate_solar_terms(result["solar_terms_detail"])
        
        # 3. 四柱验证
        print("\n【第三步：四柱排盘验证】")
        BaziValidator._validate_pillars(result["pillars"])
        
        # 4. 十神验证
        print("\n【第四步：十神标注验证】")
        BaziValidator._validate_shishen(result)
        
        # 5. 五行统计验证
        print("\n【第五步：五行统计验证】")
        BaziValidator._validate_wuxing(result["analysis"]["wuxing_count"])
        
        # 6. 根气验证
        print("\n【第六步：根气分析验证】")
        BaziValidator._validate_roots(result["analysis"]["root_analysis"], result["pillars"]["day"]["gan"])
        
        # 7. 月令司令验证
        print("\n【第七步：月令司令验证】")
        BaziValidator._validate_siling(result["pillars"]["month"], result.get("solar_terms_detail", {}))
        
        # 8. 刑冲合害验证
        print("\n【第八步：刑冲合害验证】")
        BaziValidator._validate_interactions(result["analysis"]["internal_interactions"])
        
        # 9. 透干检测验证
        print("\n【第九步：透干检测验证】")
        BaziValidator._validate_tougan(result["analysis"]["tougan_check"])
        
        # 10. 大运验证
        print("\n【第十步：大运排列验证】")
        BaziValidator._validate_dayun(result["dayun"], result["pillars"])
        
        # 11. 特殊标记验证
        print("\n【第十一步：特殊标记验证】")
        BaziValidator._validate_special_flags(result["analysis"]["special_flags"])
        
        print("\n" + "=" * 70)
        print(" " * 25 + "✓ 验证完成！")
        print("=" * 70)
    
    @staticmethod
    def _validate_basic_info(basic_info):
        """验证基础信息"""
        print(f"  原始输入时间: {basic_info['birth_time']}")
        print(f"  真太阳时:     {basic_info['true_solar_time']}")
        print(f"  时区:         {basic_info['timezone']}")
        print(f"  地点:         {basic_info['location']}")
        print(f"  性别:         {basic_info['gender']}")
        print(f"  特殊时辰:     {basic_info['special_time_marker']}")
        
        if "debug_info" in basic_info and basic_info["debug_info"]:
            debug = basic_info["debug_info"]
            print(f"\n  [调试信息]")
            print(f"    夏令时:     {debug.get('is_dst', 'N/A')}")
            print(f"    均时差:     {debug.get('equation_of_time', 'N/A')} 分钟")
            print(f"    经度差:     {debug.get('geo_offset', 'N/A')} 分钟")
            print(f"    经度:       {debug.get('longitude', 'N/A')}°")
            print(f"    纬度:       {debug.get('latitude', 'N/A')}°")
    
    @staticmethod
    def _validate_solar_terms(solar_terms):
        """验证节气信息"""
        print(f"  命理年份:     {solar_terms.get('bazi_year_int', 'N/A')}")
        print(f"  命理月令:     {solar_terms.get('month_zhi', 'N/A')}")
        print(f"  过立春:       {solar_terms.get('is_after_lichun', 'N/A')}")
        print(f"  立春时刻:     {solar_terms.get('lichun_datetime', 'N/A')}")
        
        if "prev_jie" in solar_terms:
            prev = solar_terms["prev_jie"]
            print(f"\n  上个节气:     {prev['name']} ({prev['datetime']})")
            print(f"  距上个节:     {solar_terms.get('days_since_prev_jie', 'N/A')} 天")
        
        if "next_jie" in solar_terms:
            next_j = solar_terms["next_jie"]
            print(f"  下个节气:     {next_j['name']} ({next_j['datetime']})")
            print(f"  距下个节:     {solar_terms.get('days_to_next_jie', 'N/A')} 天")
    
    @staticmethod
    def _validate_pillars(pillars):
        """验证四柱"""
        for name, pillar_key in [("年柱", "year"), ("月柱", "month"), ("日柱", "day"), ("时柱", "time")]:
            p = pillars[pillar_key]
            print(f"\n  {name}: {p['ganzhi']}")
            print(f"    天干: {p['gan']} ({BaziReference.get_stem_element(p['gan'])}) - 十神: {p.get('gan_shishen', 'N/A')}")
            print(f"    地支: {p['zhi']} ({BaziReference.get_branch_element(p['zhi'])})")
            print(f"    藏干: {', '.join(p['hidden_stems'])}")
            print(f"    纳音: {p['nayin']}")
            
            # 如果是月柱，显示司令信息
            if pillar_key == "month" and "siling" in p:
                siling = p["siling"]
                print(f"    司令: {siling['stem']}({siling['element']}) [{siling['period']}] 进入第{siling['days_into']}天")
    
    @staticmethod
    def _validate_shishen(result):
        """验证十神标注"""
        day_gan = result["pillars"]["day"]["gan"]
        print(f"  日主: {day_gan} ({BaziReference.get_stem_element(day_gan)})")
        
        # 验证天干十神
        print(f"\n  天干十神:")
        print(f"    年干 {result['pillars']['year']['gan']}: {result['pillars']['year']['gan_shishen']}")
        print(f"    月干 {result['pillars']['month']['gan']}: {result['pillars']['month']['gan_shishen']}")
        print(f"    时干 {result['pillars']['time']['gan']}: {result['pillars']['time']['gan_shishen']}")
        
        # 手动验证一个
        year_gan = result['pillars']['year']['gan']
        expected = BaziReference.get_shishen(day_gan, year_gan)
        actual = result['pillars']['year']['gan_shishen']
        if expected == actual:
            print(f"    ✓ 验证: {year_gan}对{day_gan} = {expected}")
        else:
            print(f"    ✗ 错误: {year_gan}对{day_gan} 期望{expected}，实际{actual}")
        
        # 验证地支藏干十神（抽查月支）
        print(f"\n  地支藏干十神（月支示例）:")
        month_detail = result['pillars']['month']['hidden_stems_detail']
        for item in month_detail:
            print(f"    {item['stem']}({item['element']}): {item['shishen']}")
    
    @staticmethod
    def _validate_wuxing(wuxing_count):
        """验证五行统计"""
        total = sum(item["count"] for item in wuxing_count.values())
        print(f"  五行总数: {total}")
        
        for element, data in wuxing_count.items():
            print(f"\n  {element}: {data['count']} ({data['ratio']})")
            sources_str = ", ".join(data["sources"][:4])
            if len(data["sources"]) > 4:
                sources_str += f" ... (共{len(data['sources'])}个)"
            print(f"    来源: {sources_str}")
    
    @staticmethod
    def _validate_roots(root_analysis, day_gan):
        """验证根气分析"""
        if root_analysis["has_root"]:
            print(f"  ✓ 日主有根 (共{len(root_analysis['roots'])}个)")
            for root in root_analysis["roots"]:
                print(f"    {root['zhi']}: {root['changsheng_status']} ({root['source']})")
                print(f"      说明: {root['note']}")
        else:
            print("  ✗ 日主无根（需要特别注意，可能是从格）")
    
    @staticmethod
    def _validate_siling(month_pillar, solar_terms_detail):
        """验证月令司令"""
        siling = month_pillar["siling"]
        month_zhi = month_pillar["zhi"]
        
        print(f"  月支:         {month_zhi}")
        print(f"  司令神:       {siling['stem']} ({siling['element']})")
        print(f"  司令期:       {siling['period']}")
        print(f"  进入天数:     {siling['days_into']}")
        
        # 验证计算
        days_since = solar_terms_detail.get("days_since_prev_jie", 0)
        print(f"\n  [验证] 距离节气: {days_since} 天")
        
        # 查表验证
        siling_table = BaziReference.SILING_TABLE.get(month_zhi, [])
        cumulative = 0
        for period in siling_table:
            cumulative += period["days"]
            if days_since < cumulative:
                expected_stem = period["stem"]
                if expected_stem == siling["stem"]:
                    print(f"  ✓ 司令验证通过: {expected_stem}")
                else:
                    print(f"  ✗ 司令验证失败: 期望{expected_stem}，实际{siling['stem']}")
                break
    
    @staticmethod
    def _validate_interactions(interactions):
        """验证刑冲合害"""
        if not interactions:
            print("  ✓ 原局无刑冲合害（八字平和）")
        else:
            print(f"  检测到 {len(interactions)} 个关系:")
            for inter in interactions:
                print(f"    {inter['type']}: {inter['note']}")
    
    @staticmethod
    def _validate_tougan(tougan_check):
        """验证透干检测"""
        print(f"  月支:         {tougan_check['month_zhi']}")
        print(f"  月令藏干:     {', '.join(tougan_check['hidden_stems'])}")
        print(f"\n  透干情况:")
        for stem, info in tougan_check['tougan_analysis'].items():
            status = "✓ 透出" if info['is_tougan'] else "✗ 未透"
            positions = ', '.join(info['positions']) if info['positions'] else "无"
            print(f"    {stem}({info['shishen']}): {status} - 位置: {positions}")
        print(f"\n  格局提示: {tougan_check['pattern_hint']}")
    
    @staticmethod
    def _validate_dayun(dayun_info, pillars):
        """验证大运"""
        print(f"  起运方向:     {dayun_info['direction']}")
        print(f"  起运岁数:     {dayun_info['qiyun_age']} 岁")
        print(f"  起运日期:     {dayun_info['qiyun_date']}")
        print(f"  计算详情:     {dayun_info['calculation_detail']}")
        
        # 显示前3步大运
        print(f"\n  大运序列 (前3步):")
        for dayun in dayun_info['dayun_list'][:3]:
            print(f"    {dayun['age_range']}: {dayun['pillar']} ({dayun['nayin']})")
        
        # 验证第一步大运
        month_gan = pillars["month"]["gan"]
        month_zhi = pillars["month"]["zhi"]
        first_dayun = dayun_info['dayun_list'][0]
        
        print(f"\n  [验证] 月柱: {month_gan}{month_zhi}")
        print(f"  [验证] 第一步大运: {first_dayun['pillar']}")
        
        # 简单验证顺逆
        gan_seq = BaziReference.HEAVENLY_STEMS
        month_gan_idx = gan_seq.index(month_gan)
        first_gan_idx = gan_seq.index(first_dayun['gan'])
        
        if dayun_info['direction'] == "顺排":
            expected_idx = (month_gan_idx + 1) % 10
        else:
            expected_idx = (month_gan_idx - 1) % 10
        
        if first_gan_idx == expected_idx:
            print(f"  ✓ 大运方向验证通过")
        else:
            print(f"  ✗ 大运方向可能有误")
    
    @staticmethod
    def _validate_special_flags(special_flags):
        """验证特殊标记"""
        print(f"  五行缺失:     {', '.join(special_flags['wuxing_missing']) if special_flags['wuxing_missing'] else '无'}")
        
        if special_flags['wuxing_extreme']:
            ext = special_flags['wuxing_extreme']
            print(f"  五行极端:     {ext['note']}")
        else:
            print(f"  五行极端:     无（分布较均衡）")
        
        if special_flags['all_yang']:
            print(f"  阴阳特征:     全阳（四柱天干全阳）")
        elif special_flags['all_yin']:
            print(f"  阴阳特征:     全阴（四柱天干全阴）")
        else:
            print(f"  阴阳特征:     阴阳混杂（正常）")
        
        if special_flags['hint']:
            print(f"\n  ⚠️  提示: {special_flags['hint']}")