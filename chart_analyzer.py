# chart_analyzer.py
"""
八字特征分析器
负责标注十神、分析根气、统计五行、检测透干等
"""

from bazi_reference import BaziReference
from interaction_engine import InteractionEngine

class ChartAnalyzer:
    """八字特征分析器"""
    
    def __init__(self):
        pass
    
    def analyze(self, chart_data):
        """
        完整分析八字特征
        
        Args:
            chart_data: ChartBuilder.build_chart() 的输出
        
        Returns:
            分析结果对象
        """
        pillars = chart_data["pillars"]
        day_gan = pillars["day"]["gan"]
        month_zhi = pillars["month"]["zhi"]
        
        # 获取真太阳时和节气数据（用于计算月令分日）
        # days_since_jie 在 bazi_service 中计算并存入 basic_info.solar_terms.days_since_prev_jie
        try:
            solar_terms = chart_data.get("basic_info", {}).get("solar_terms", {})
            days_since_jie = solar_terms.get("days_since_prev_jie", 0)
        except:
            days_since_jie = 0
            
        # 1. 计算月令司令 (Deterministic Algorithm)
        siling_info = BaziReference.get_siling_info(month_zhi, days_since_jie, day_gan)
        
        # 2. 计算旺相休囚死 (Deterministic Table Lookup)
        season = BaziReference.get_season(month_zhi)
        wangxiang_stats = {
            elem: BaziReference.get_wangxiang(season, elem)
            for elem in ["木", "火", "土", "金", "水"]
        }
        
        # 3. 互动上下文定性 (Deterministic Logic)
        interactions = InteractionEngine.detect_bazi_internal(pillars)
        interaction_context = self._qualify_interactions(interactions, siling_info, wangxiang_stats)

        return {
            "shishen_map": self._mark_shishen(pillars, day_gan),
            "wuxing_count": self._count_wuxing(pillars),
            "root_analysis": self._analyze_roots(pillars, day_gan),
            "tougan_check": self._check_tougan(pillars, day_gan),
            "internal_interactions": interactions,
            "special_flags": self._check_special_flags(pillars, day_gan),
            
            # 🆕 新增确定性计算结果，供LLM作为事实依据
            "month_siling": siling_info,
            "wangxiang_stats": wangxiang_stats,
            "interaction_context": interaction_context
        }
        
    def _qualify_interactions(self, interactions, siling_info, wangxiang_stats):
        """
        对交互关系进行初步定性（为贪合忘冲提供数据支持）
        """
        context = {
            "has_chong": False,
            "has_he": False,
            "he_strength": 0,
            "chong_strength": 0,
            "priority_hint": "无明显冲突"
        }
        
        chong_list = [i for i in interactions if i["type"] == "六冲"]
        he_list = [i for i in interactions if i["type"] == "六合"]
        
        if chong_list and he_list:
            context["has_chong"] = True
            context["has_he"] = True
            
            # 简单评估合神力量（如果是司令或旺相，力量大）
            he_item = he_list[0] # 简化，取第一个
            he_zhi1_elem = BaziReference.get_branch_element(he_item["zhi1"])
            
            # 检查合神是否得月令
            he_is_siling = False
            if siling_info and siling_info["element"] == he_item["hehuan_element"]:
                he_is_siling = True
                
            if he_is_siling:
                context["priority_hint"] = "合神得令，贪合忘冲可能性大"
            else:
                context["priority_hint"] = "合神失令，冲力可能仍存，需综合判断"
                
        return context
    
    # ============================================
    # 模块1.9：十神标注（🔧 修复版）
    # ============================================
    
    def _mark_shishen(self, pillars, day_gan):
        """
        标注所有天干和地支藏干的十神
        
        Returns:
            {
                "年干甲": "正印",
                "月干乙": "偏印",
                "时干己": "伤官",
                "年支子藏癸": "七杀",
                ...
            }
        """
        shishen_map = {}
        
        # 标注天干十神
        for position, pillar in [
            ("年干", pillars["year"]),
            ("月干", pillars["month"]),
            ("时干", pillars["time"])
        ]:
            gan = pillar["gan"]
            if gan != day_gan:
                shishen = BaziReference.get_shishen(day_gan, gan)
                shishen_map[f"{position}{gan}"] = shishen
            else:
                # 天干与日干相同（极少见，但要处理）
                shishen_map[f"{position}{gan}"] = "比肩"
        
        # 日干标记为"日主"
        shishen_map[f"日干{day_gan}"] = "日主"
        
        # 标注地支藏干十神（🔧 修复：藏干等于日干时也要标注）
        for position, pillar_key in [
            ("年支", "year"),
            ("月支", "month"),
            ("日支", "day"),
            ("时支", "time")
        ]:
            pillar = pillars[pillar_key]
            zhi = pillar["zhi"]
            hidden_stems = pillar["hidden_stems"]
            
            for cang_gan in hidden_stems:
                if cang_gan == day_gan:
                    # 藏干等于日干，标记为"比肩"
                    shishen_map[f"{position}{zhi}藏{cang_gan}"] = "比肩"
                else:
                    shishen = BaziReference.get_shishen(day_gan, cang_gan)
                    shishen_map[f"{position}{zhi}藏{cang_gan}"] = shishen
        
        return shishen_map
    
    # ============================================
    # 模块1.12：五行统计
    # ============================================
    
    def _count_wuxing(self, pillars):
        """
        统计五行分布
        
        注意：这只是辅助数据，不能直接用于旺衰判断
        
        Returns:
            {
                "木": {"count": 4.6, "ratio": "30%", "sources": [...]},
                ...
            }
        """
        wuxing_detail = {
            "木": {"count": 0, "sources": []},
            "火": {"count": 0, "sources": []},
            "土": {"count": 0, "sources": []},
            "金": {"count": 0, "sources": []},
            "水": {"count": 0, "sources": []}
        }
        
        # 统计天干（每个算1）
        for position, pillar_key in [
            ("年干", "year"),
            ("月干", "month"),
            ("日干", "day"),
            ("时干", "time")
        ]:
            pillar = pillars[pillar_key]
            gan = pillar["gan"]
            element = BaziReference.get_stem_element(gan)
            
            wuxing_detail[element]["count"] += 1
            wuxing_detail[element]["sources"].append(f"{gan}（{position}）")
        
        # 统计地支藏干（每个算0.5）
        for position, pillar_key in [
            ("年支", "year"),
            ("月支", "month"),
            ("日支", "day"),
            ("时支", "time")
        ]:
            pillar = pillars[pillar_key]
            zhi = pillar["zhi"]
            hidden_stems = pillar["hidden_stems"]
            
            for cang_gan in hidden_stems:
                element = BaziReference.get_stem_element(cang_gan)
                wuxing_detail[element]["count"] += 0.5
                wuxing_detail[element]["sources"].append(f"{zhi}藏{cang_gan}")
        
        # 计算占比
        total = sum(item["count"] for item in wuxing_detail.values())
        for element in wuxing_detail:
            ratio = wuxing_detail[element]["count"] / total if total > 0 else 0
            wuxing_detail[element]["ratio"] = f"{int(ratio * 100)}%"
            wuxing_detail[element]["count"] = round(wuxing_detail[element]["count"], 1)
        
        return wuxing_detail
    
    # ============================================
    # 模块1.13：根气分析
    # ============================================
    
    def _analyze_roots(self, pillars, day_gan):
        """
        分析日主在地支的根气
        
        Returns:
            {
                "has_root": True,
                "roots": [
                    {
                        "zhi": "午",
                        "source": "本气",
                        "changsheng_status": "帝旺",
                        "note": "午火为日主本气根，查十二长生为帝旺"
                    }
                ]
            }
        """
        roots = []
        day_element = BaziReference.get_stem_element(day_gan)
        
        for pillar_key in ["year", "month", "day", "time"]:
            pillar = pillars[pillar_key]
            zhi = pillar["zhi"]
            hidden_stems = pillar["hidden_stems"]
            
            # 查询十二长生状态
            changsheng_status = BaziReference.get_changsheng_status(day_gan, zhi)
            
            # 判断是否为有效根（帝旺、临官、长生、冠带）
            if changsheng_status in ["帝旺", "临官", "长生", "冠带"]:
                # 找到日主五行在该地支中的位置
                source = "未知"
                for i, stem in enumerate(hidden_stems):
                    if BaziReference.get_stem_element(stem) == day_element:
                        if i == 0:
                            source = "本气"
                        elif len(hidden_stems) == 2:
                            source = "中气"
                        elif i == 1:
                            source = "中气"
                        else:
                            source = "余气"
                        break
                
                roots.append({
                    "zhi": zhi,
                    "source": source,
                    "changsheng_status": changsheng_status,
                    "note": f"{zhi}为日主{source}根，查十二长生为{changsheng_status}"
                })
        
        return {
            "has_root": len(roots) > 0,
            "roots": roots
        }
    
    # ============================================
    # 模块1.8：透干检测
    # ============================================
    
    def _check_tougan(self, pillars, day_gan):
        """
        检测月令藏干是否透出天干
        
        这是格局法的关键判断依据
        
        Returns:
            {
                "month_zhi": "亥",
                "hidden_stems": ["壬", "甲"],
                "tougan_analysis": {
                    "壬": {
                        "positions": [],
                        "is_tougan": False,
                        "shishen": "七杀"
                    },
                    "甲": {
                        "positions": ["年干"],
                        "is_tougan": True,
                        "shishen": "偏印"
                    }
                },
                "pattern_hint": "月令甲木透于年干，可取偏印格"
            }
        """
        month_pillar = pillars["month"]
        month_zhi = month_pillar["zhi"]
        hidden_stems = month_pillar["hidden_stems"]
        
        # 收集所有天干
        all_gans = [
            pillars["year"]["gan"],
            pillars["month"]["gan"],
            pillars["day"]["gan"],
            pillars["time"]["gan"]
        ]
        
        pillar_names = ["年干", "月干", "日干", "时干"]
        
        tougan_analysis = {}
        
        for cang_gan in hidden_stems:
            # 排除日干本身（不算透干）
            if cang_gan == day_gan:
                positions = []
            else:
                positions = [
                    pillar_names[i]
                    for i, gan in enumerate(all_gans)
                    if gan == cang_gan and i != 2  # 不包括日柱位置
                ]
            
            tougan_analysis[cang_gan] = {
                "positions": positions,
                "is_tougan": len(positions) > 0,
                "shishen": BaziReference.get_shishen(day_gan, cang_gan)
            }
        
        # 生成格局提示
        tougan_list = [
            f"{stem}({info['shishen']})"
            for stem, info in tougan_analysis.items()
            if info["is_tougan"]
        ]
        
        if tougan_list:
            pattern_hint = f"月令{'、'.join(tougan_list)}透干，需结合司令神确定格局"
        else:
            pattern_hint = "月令藏干均未透出，按司令神定格局"
        
        return {
            "month_zhi": month_zhi,
            "hidden_stems": hidden_stems,
            "tougan_analysis": tougan_analysis,
            "pattern_hint": pattern_hint
        }
    
    # ============================================
    # 模块1.13扩展：格局预警标记
    # ============================================
    
    def _check_special_flags(self, pillars, day_gan):
        """
        标记异常特征，提醒LLM注意
        
        🔧 修改：新增 has_no_root 字段
        
        Returns:
            {
                "has_no_root": False,        # 🆕 新增：日主无根明确标记
                "wuxing_missing": ["金"],
                "wuxing_extreme": {...},
                "all_yang": False,
                "all_yin": False,
                "hint": "..."
            }
        """
        # 获取五行统计
        wuxing_count_result = self._count_wuxing(pillars)
        
        # 提取数值
        wuxing_count = {
            elem: data["count"]
            for elem, data in wuxing_count_result.items()
        }
        
        total = sum(wuxing_count.values())
        
        # 检查五行缺失
        missing = [e for e in ["木", "火", "土", "金", "水"] if wuxing_count[e] == 0]
        
        # 检查五行集中度
        wuxing_extreme = None
        if wuxing_count:
            max_element = max(wuxing_count, key=wuxing_count.get)
            max_ratio = wuxing_count[max_element] / total
            
            if max_ratio >= 0.6:
                wuxing_extreme = {
                    "element": max_element,
                    "ratio": round(max_ratio, 2),
                    "note": f"{max_element}占{int(max_ratio*100)}%，显著偏多"
                }
        
        # 检查阴阳
        all_gans = [
            pillars["year"]["gan"],
            pillars["month"]["gan"],
            pillars["day"]["gan"],
            pillars["time"]["gan"]
        ]
        
        all_yang = all(gan in BaziReference.YANG_STEMS for gan in all_gans)
        all_yin = all(gan in BaziReference.YIN_STEMS for gan in all_gans)
        
        # 🆕 检查日主有无根
        root_analysis = self._analyze_roots(pillars, day_gan)
        has_no_root = not root_analysis["has_root"]
        
        # 生成提示
        tips = []
        if wuxing_extreme:
            tips.append(f"{wuxing_extreme['element']}偏多")
        if missing:
            tips.append(f"缺{'、'.join(missing)}")
        
        hint = None
        if tips:
            hint = f"该八字{'、'.join(tips)}，五行分布不均，请注意判断是否为特殊格局"
        
        return {
            "has_no_root": has_no_root,  # 🆕 新增字段
            "wuxing_missing": missing,
            "wuxing_extreme": wuxing_extreme,
            "all_yang": all_yang,
            "all_yin": all_yin,
            "hint": hint
        }