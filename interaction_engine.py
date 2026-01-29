# interaction_engine.py
"""
地支关系检测引擎
负责判断干支之间的刑冲合害关系
"""

class InteractionEngine:
    """干支关系检测引擎（纯静态方法）"""
    
    # ============================================
    # 地支六冲
    # ============================================
    LIUCHONG = {
        '子': '午', '午': '子',
        '丑': '未', '未': '丑',
        '寅': '申', '申': '寅',
        '卯': '酉', '酉': '卯',
        '辰': '戌', '戌': '辰',
        '巳': '亥', '亥': '巳'
    }
    
    # ============================================
    # 地支六合
    # ============================================
    LIUHE = {
        ('子', '丑'): '土',
        ('寅', '亥'): '木',
        ('卯', '戌'): '火',
        ('辰', '酉'): '金',
        ('巳', '申'): '水',
        ('午', '未'): '土'
    }
    
    # ============================================
    # 地支三合
    # ============================================
    SANHE = {
        frozenset(['申', '子', '辰']): '水',
        frozenset(['亥', '卯', '未']): '木',
        frozenset(['寅', '午', '戌']): '火',
        frozenset(['巳', '酉', '丑']): '金'
    }
    
    # ============================================
    # 地支三刑
    # ============================================
    SANXING = {
        frozenset(['寅', '巳', '申']): '无恩之刑',
        frozenset(['丑', '未', '戌']): '恃势之刑'
    }
    
    # 子卯刑（无礼之刑）
    LIANG_XING = {
        frozenset(['子', '卯']): '无礼之刑'
    }
    
    # 自刑
    ZI_XING = ['辰', '午', '酉', '亥']
    
    # ============================================
    # 地支六害
    # ============================================
    LIUHAI = {
        frozenset(['子', '未']): '子未害',
        frozenset(['丑', '午']): '丑午害',
        frozenset(['寅', '巳']): '寅巳害',
        frozenset(['卯', '辰']): '卯辰害',
        frozenset(['申', '亥']): '申亥害',
        frozenset(['酉', '戌']): '酉戌害'
    }
    
    # ============================================
    # 天干相克
    # ============================================
    TIANGAN_KE = {
        "甲": ["庚", "辛"],
        "乙": ["庚", "辛"],
        "丙": ["壬", "癸"],
        "丁": ["壬", "癸"],
        "戊": ["甲", "乙"],
        "己": ["甲", "乙"],
        "庚": ["丙", "丁"],
        "辛": ["丙", "丁"],
        "壬": ["戊", "己"],
        "癸": ["戊", "己"]
    }
    
    # ============================================
    # 核心检测方法
    # ============================================
    
    @staticmethod
    def check_chong(zhi1, zhi2):
        """
        检测六冲
        
        Returns:
            bool: True表示相冲
        """
        return InteractionEngine.LIUCHONG.get(zhi1) == zhi2
    
    @staticmethod
    def check_he(zhi1, zhi2):
        """
        检测六合
        
        Returns:
            dict: {"is_he": bool, "hehuan_element": str} 或 None
        """
        pair = frozenset([zhi1, zhi2])
        for he_pair, element in InteractionEngine.LIUHE.items():
            if frozenset(he_pair) == pair:
                return {"is_he": True, "hehuan_element": element}
        return {"is_he": False}
    
    @staticmethod
    def check_sanhe(zhi_list):
        """
        检测三合（需要3个地支）
        
        Args:
            zhi_list: 地支列表
        
        Returns:
            list: [{"zhis": [...], "element": "水"}, ...]
        """
        results = []
        zhi_set = frozenset(zhi_list)
        
        for sanhe_set, element in InteractionEngine.SANHE.items():
            if sanhe_set.issubset(zhi_set):
                results.append({
                    "zhis": list(sanhe_set),
                    "element": element
                })
        
        return results
    
    @staticmethod
    def check_xing(zhi_list):
        """
        检测三刑、二刑、自刑
        
        Returns:
            list: [{"type": "三刑", "zhis": [...], "xing_type": "..."}, ...]
        """
        results = []
        zhi_set = frozenset(zhi_list)
        
        # 三刑
        for xing_set, xing_type in InteractionEngine.SANXING.items():
            if xing_set.issubset(zhi_set):
                results.append({
                    "type": "三刑",
                    "zhis": list(xing_set),
                    "xing_type": xing_type
                })
        
        # 子卯刑
        for xing_set, xing_type in InteractionEngine.LIANG_XING.items():
            if xing_set.issubset(zhi_set):
                results.append({
                    "type": "二刑",
                    "zhis": list(xing_set),
                    "xing_type": xing_type
                })
        
        # 自刑
        for zhi in InteractionEngine.ZI_XING:
            count = zhi_list.count(zhi)
            if count >= 2:
                results.append({
                    "type": "自刑",
                    "zhi": zhi,
                    "count": count
                })
        
        return results
    
    @staticmethod
    def check_hai(zhi1, zhi2):
        """
        检测六害
        
        Returns:
            dict: {"is_hai": bool, "hai_type": str} 或 None
        """
        pair = frozenset([zhi1, zhi2])
        for hai_pair, hai_type in InteractionEngine.LIUHAI.items():
            if hai_pair == pair:
                return {"is_hai": True, "hai_type": hai_type}
        return {"is_hai": False}
    
    @staticmethod
    def check_tianke_dichong(pillar1, pillar2):
        """
        检测天克地冲（最凶组合）
        
        Args:
            pillar1: {"gan": "甲", "zhi": "寅"}
            pillar2: {"gan": "庚", "zhi": "申"}
        
        Returns:
            dict: 天克地冲信息
        """
        gan1, zhi1 = pillar1["gan"], pillar1["zhi"]
        gan2, zhi2 = pillar2["gan"], pillar2["zhi"]
        
        # 检测天干相克（双向）
        tiangan_ke = (gan2 in InteractionEngine.TIANGAN_KE.get(gan1, [])) or \
                     (gan1 in InteractionEngine.TIANGAN_KE.get(gan2, []))
        
        # 检测地支相冲
        dizhi_chong = InteractionEngine.check_chong(zhi1, zhi2)
        
        if tiangan_ke and dizhi_chong:
            # 确定克制方向
            if gan2 in InteractionEngine.TIANGAN_KE.get(gan1, []):
                ke_desc = f"{gan2}克{gan1}"
            else:
                ke_desc = f"{gan1}克{gan2}"
            
            return {
                "is_tianke_dichong": True,
                "tiangan_ke": ke_desc,
                "dizhi_chong": f"{zhi1}{zhi2}冲",
                "severity": "极凶",
                "note": "⚠️ 天克地冲，变动剧烈，需防意外、破财、疾病、官非"
            }
        
        return {"is_tianke_dichong": False}
    
    @staticmethod
    def detect_bazi_internal(pillars):
        """
        检测原局内部的刑冲合害
        
        Args:
            pillars: {
                "year": {"gan": "甲", "zhi": "子"},
                "month": {"gan": "乙", "zhi": "亥"},
                "day": {"gan": "丙", "zhi": "午"},
                "time": {"gan": "己", "zhi": "亥"}
            }
        
        Returns:
            list: 互动关系列表
        """
        interactions = []
        
        pillar_list = [
            {"name": "年柱", "position": "年支", **pillars["year"]},
            {"name": "月柱", "position": "月支", **pillars["month"]},
            {"name": "日柱", "position": "日支", **pillars["day"]},
            {"name": "时柱", "position": "时支", **pillars["time"]}
        ]
        
        zhi_list = [p["zhi"] for p in pillar_list]
        
        # 1. 检测六冲（两两对比）
        for i in range(len(pillar_list)):
            for j in range(i+1, len(pillar_list)):
                p1, p2 = pillar_list[i], pillar_list[j]
                
                if InteractionEngine.check_chong(p1["zhi"], p2["zhi"]):
                    interactions.append({
                        "type": "六冲",
                        "zhi1": p1["zhi"],
                        "zhi2": p2["zhi"],
                        "position1": p1["position"],
                        "position2": p2["position"],
                        "involved_pillars": [p1["name"], p2["name"]],
                        "note": f"{p1['position']}与{p2['position']}相冲"
                    })
        
        # 2. 检测六合（两两对比）
        for i in range(len(pillar_list)):
            for j in range(i+1, len(pillar_list)):
                p1, p2 = pillar_list[i], pillar_list[j]
                
                he_result = InteractionEngine.check_he(p1["zhi"], p2["zhi"])
                if he_result["is_he"]:
                    interactions.append({
                        "type": "六合",
                        "zhi1": p1["zhi"],
                        "zhi2": p2["zhi"],
                        "position1": p1["position"],
                        "position2": p2["position"],
                        "involved_pillars": [p1["name"], p2["name"]],
                        "hehuan_element": he_result["hehuan_element"],
                        "note": f"{p1['position']}与{p2['position']}六合化{he_result['hehuan_element']}"
                    })
        
        # 3. 检测三合
        sanhe_results = InteractionEngine.check_sanhe(zhi_list)
        for sanhe in sanhe_results:
            involved = [p for p in pillar_list if p["zhi"] in sanhe["zhis"]]
            interactions.append({
                "type": "三合",
                "zhis": sanhe["zhis"],
                "involved_pillars": [p["name"] for p in involved],
                "hehuan_element": sanhe["element"],
                "note": f"{''.join(sanhe['zhis'])}三合{sanhe['element']}局"
            })
        
        # 4. 检测三刑
        xing_results = InteractionEngine.check_xing(zhi_list)
        for xing in xing_results:
            if xing["type"] == "自刑":
                involved = [p for p in pillar_list if p["zhi"] == xing["zhi"]]
                interactions.append({
                    "type": "自刑",
                    "zhi": xing["zhi"],
                    "count": xing["count"],
                    "involved_pillars": [p["name"] for p in involved],
                    "note": f"{xing['zhi']}出现{xing['count']}次，自刑，主内心矛盾"
                })
            else:
                involved = [p for p in pillar_list if p["zhi"] in xing["zhis"]]
                interactions.append({
                    "type": xing["type"],
                    "zhis": xing["zhis"],
                    "involved_pillars": [p["name"] for p in involved],
                    "xing_type": xing["xing_type"],
                    "note": f"{''.join(xing['zhis'])}{'相刑' if xing['type']=='二刑' else '三刑'}（{xing['xing_type']}）"
                })
        
        # 5. 检测六害（两两对比）
        for i in range(len(pillar_list)):
            for j in range(i+1, len(pillar_list)):
                p1, p2 = pillar_list[i], pillar_list[j]
                
                hai_result = InteractionEngine.check_hai(p1["zhi"], p2["zhi"])
                if hai_result["is_hai"]:
                    interactions.append({
                        "type": "六害",
                        "zhi1": p1["zhi"],
                        "zhi2": p2["zhi"],
                        "position1": p1["position"],
                        "position2": p2["position"],
                        "involved_pillars": [p1["name"], p2["name"]],
                        "hai_type": hai_result["hai_type"],
                        "note": f"{hai_result['hai_type']}，主暗中阻碍"
                    })
        
        return interactions