# reasoning_orchestrator.py
"""
LLM 推理编排器
负责加载 Prompt 模板，填充算法输出的数据，并维护推理链条的状态。
使用“统一结论协议 (Unified Conclusion Protocol)”确保数据一致性。
"""

import os
import json
import re

class ReasoningOrchestrator:
    """推理编排器"""

    def __init__(self, prompts_dir="prompts"):
        self.prompts_dir = prompts_dir
        self.templates = {}
        self._load_templates()

    def _load_templates(self):
        """从 prompts 目录加载所有 .md 模板"""
        if not os.path.exists(self.prompts_dir):
            return

        for filename in os.listdir(self.prompts_dir):
            if filename.endswith(".md"):
                name = filename.replace(".md", "")
                with open(os.path.join(self.prompts_dir, filename), "r", encoding="utf-8") as f:
                    self.templates[name] = f.read()

    def render_prompt(self, template_name, data):
        """填充模板中的占位符 {{ variable_name }}"""
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found.")

        def replacement(match):
            key = match.group(1).strip()
            # 支持嵌套访问，如 analysis.wuxing_count
            value = self._get_nested_value(data, key)
            if value is None:
                return f"{{{{ {key} }}}}" # 保留占位符提醒缺失
            
            if isinstance(value, (dict, list)):
                return json.dumps(value, ensure_ascii=False, indent=2)
            return str(value)

        rendered = re.sub(r"\{\{\s*(.*?)\s*\}\}", replacement, template)
        return rendered

    def _get_nested_value(self, data, key_path):
        keys = key_path.split('.')
        current = data
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        return current

    def get_prompt_for_step(self, step_name, full_bazi_data, history=None):
        """提取特定步骤的 Prompt 并注入上下文"""
        if history is None:
            history = {}
        
        view_model = self._prepare_view_model(full_bazi_data, history)
        
        template_map = {
            "pattern": "prompt_pattern",
            "strength": "prompt_strength",
            "special_flow": "prompt_special_flow",
            "yongshen": "prompt_yongshen",
            "dayun": "prompt_dayun",
            "liunian": "prompt_liunian",
            "report": "prompt_report"
        }
        
        temp_name = template_map.get(step_name)
        if not temp_name:
            raise ValueError(f"Unknown step: {step_name}")
            
        return self.render_prompt(temp_name, view_model)

    def _prepare_view_model(self, data, history, liunian_data=None):
        """准备统一的数据模型 (View Model)"""
        # 超强防御性数据解析：处理 data 为 None 或 字段为 null 的情况
        if not data: data = {}
        pillars = data.get("pillars") or {}
        analysis = data.get("analysis") or {}
        ref = data.get("reference_tables") or {}
        basic = data.get("basic_info") or {}
        solar = data.get("solar_terms_detail") or {}
        day_elem = (pillars.get("day") or {}).get("element") or "木"

        # 1. 基础事实 (Facts)
        vm = {
            "user_name": history.get("user_name", "尊贵的缘主"),
            "gender": basic.get("gender", "未知"),
            "birth_date_display": f"{basic.get('birth_time', '未知')}",
            "true_solar_time": basic.get("true_solar_time", "未知"),
            "location_display": basic.get("location", "未知"),
            "day_gan": (pillars.get("day") or {}).get("gan", "？"),
            "month_zhi": (pillars.get("month") or {}).get("zhi", "？"),
            "season_detail": f"{ref.get('season', '？')}（{ (solar.get('prev_jie') or {}).get('name', '？') }后第 {solar.get('days_since_prev_jie', '？')} 天）",
            "season": ref.get("season", "？"),
            "shishen_table": self._format_pillars_as_table(pillars),
            "wuxing_energy_summary": self._format_wuxing_energy_summary(analysis.get("wuxing_count")),
            "hidden_stems": (pillars.get("month") or {}).get("hidden_stems", []),
            "tougan_check_list": self._format_tougan_check(analysis.get("tougan_check")),
            "tougan_pattern_hint": (analysis.get("tougan_check") or {}).get("pattern_hint", "无"),
            "siling_stem": (analysis.get("month_siling") or {}).get("stem", "？"),
            "siling_period": (analysis.get("month_siling") or {}).get("period", "？"),
            "siling_days": (analysis.get("month_siling") or {}).get("days_into", "？"),
            "siling_shishen": (analysis.get("month_siling") or {}).get("shishen", "？"),
            "siling_is_tougan": "是" if (analysis.get("tougan_check") or {}).get("tougan_analysis", {}).get((analysis.get("month_siling") or {}).get("stem"), {}).get("is_tougan") else "否",
            "potential_pattern": (analysis.get("tougan_check") or {}).get("pattern_hint", "普通格局"),
            "siling_note": f"司令神 { (analysis.get('month_siling') or {}).get('stem', '？') } 为日主之 { (analysis.get('month_siling') or {}).get('shishen', '？') }",
        }

        # 2. 推理结论 (History)
        vm.update({
            "pattern_type": history.get("pattern_type") or history.get("reasoning") or "未确定",
            "pattern_conclusion": history.get("pattern_conclusion") or history.get("reasoning") or "分析中...",
            "strength_level": history.get("strength_level") or history.get("overall_strength") or "未确定",
            "original_strength_level": history.get("strength_level") or history.get("overall_strength") or "未确定",
            "strength_conclusion": history.get("strength_conclusion") or history.get("reasoning") or "分析中...",
            "energy_result": history.get("strength_conclusion") or history.get("reasoning") or "分析中...",
            "yongshen_conclusion": history.get("yongshen_conclusion") or history.get("yongshen_advice") or "分析中...",
            "fuyi_conclusion": history.get("fuyi_conclusion") or "待评估",
            "tiaohou_conclusion": history.get("tiaohou_conclusion") or "待评估",
            "tongguan_conclusion": history.get("tongguan_conclusion") or "待评估",
            "primary_god_summary": self._get_god_summary(history),
            "dayun_report": history.get("dayun_report", "预测中..."),
            "dayun_conclusion": history.get("dayun_conclusion", "分析中..."),
            "liunian_report": history.get("liunian_report", "预测中..."),
            "liunian_conclusion": history.get("liunian_conclusion", "分析中..."),
        })

        # 3. 算法子集分析
        wangxiang = analysis.get("wangxiang_stats") or {}
        yin_bi = self._get_yin_bi_elements(day_elem)
        vm.update({
            "wangxiang_status": wangxiang.get(day_elem, "？"),
            "wangxiang_table": json.dumps(wangxiang, ensure_ascii=False, indent=2),
            "changsheng_table": self._format_changsheng(ref.get("changsheng")),
            "root_summary": (analysis.get("root_analysis") or {}).get("has_root") and "有根" or "无根",
            "root_analysis_detail": self._format_root_analysis(analysis.get("root_analysis")),
            "interactions_impact": self._format_interactions(analysis.get("internal_interactions")),
            "interaction_list": self._format_interactions(analysis.get("internal_interactions")),
            "tiaohou_reference": ref.get("tiaohou", "无明确调候"),
            "fuyi_need": self._get_fuyi_need(vm["strength_level"]),
            "yin_element": yin_bi["yin"],
            "yin_status": wangxiang.get(yin_bi["yin"], "中"),
            "bi_element": yin_bi["bi"],
            "bi_status": wangxiang.get(yin_bi["bi"], "中"),
            "conflict_list": self._format_conflicts(analysis.get("internal_interactions")),
            "has_no_root": "是" if (analysis.get("special_flags") or {}).get("has_no_root") else "否",
            "missing_elements": "、".join((analysis.get("special_flags") or {}).get("wuxing_missing", [])) or "无",
            "element_extreme": (analysis.get("special_flags") or {}).get("wuxing_extreme") or "正常",
            "structural_hint": (analysis.get("special_flags") or {}).get("hint") or "格局稳健",
            # Special Flow Detection Support
            "suspected_flow_god": analysis.get("special_flow", {}).get("is_special") and analysis.get("special_flow", {}).get("type") or "未知",
            "flow_god_percentage": analysis.get("special_flow", {}).get("energy_ratio") or "0%",
            "flow_god_is_siling": "是" if analysis.get("special_flow", {}).get("is_siling") else "否",
            "flow_god_is_tougan": "是" if analysis.get("special_flow", {}).get("is_tougan") else "否",
            "yin_strength": analysis.get("wuxing_count", {}).get(yin_bi["yin"], {}).get("ratio", "0%"),
            "bi_strength": analysis.get("wuxing_count", {}).get(yin_bi["bi"], {}).get("ratio", "0%"),
            "guan_strength": analysis.get("wuxing_count", {}).get("火", {}).get("ratio", "0%"), # 这里的官杀需要根据日主定，暂给默认
            "root_analysis_summary": (analysis.get("root_analysis") or {}).get("has_root") and "日主有根气支持" or "日主孤立无援",
        })

        # 4. 时空动态
        liunian_raw = (liunian_data or {}).get("liunian") or {}
        curr_year = str(liunian_raw.get("year", "2024"))
        dayun_info = self._get_current_dayun_info(data, curr_year)
        
        vm.update({
            "current_year": curr_year,
            "liunian_year": curr_year,
            "liunian_ganzhi": liunian_raw.get("ganzhi", "甲辰"),
            "liunian_gan": (liunian_raw.get("ganzhi", "甲辰"))[0],
            "liunian_zhi": (liunian_raw.get("ganzhi", "辰"))[-1],
            "dayun_liunian_gan_interaction": history.get("dayun_liunian_gan_interaction", "（自行分析）"),
            "dayun_liunian_zhi_interaction": history.get("dayun_liunian_zhi_interaction", "（自行分析）"),
            "current_dayun_pillar": dayun_info.get("pillar", "待定"),
            "current_dayun_age_range": dayun_info.get("age_range", "待定"),
            "current_dayun_gan": dayun_info.get("gan", "？"),
            "current_dayun_zhi": dayun_info.get("zhi", "？"),
            "dayun_list": self._format_dayun_list((data.get("dayun") or {}).get("dayun_list")),
        })

        return vm

    # --- Formatting Helpers (Always safe) ---

    def _format_pillars_as_table(self, pillars):
        if not pillars: return "数据缺失"
        rows = [
            ["项目", "年柱", "月柱", "日柱", "时柱"],
            ["干支", (pillars.get("year") or {}).get("ganzhi", "？"), (pillars.get("month") or {}).get("ganzhi", "？"), (pillars.get("day") or {}).get("ganzhi", "？"), (pillars.get("time") or {}).get("ganzhi", "？")],
            ["十神", (pillars.get("year") or {}).get("gan_shishen", "？"), (pillars.get("month") or {}).get("gan_shishen", "？"), "日主", (pillars.get("time") or {}).get("gan_shishen", "？")],
            ["地支藏干"]
        ]
        for pos in ["year", "month", "day", "time"]:
            stems = (pillars.get(pos) or {}).get("hidden_stems", [])
            rows[-1].append("、".join(stems) if stems else "无")
        return "\n".join([" | ".join(r) for r in rows])

    def _format_wuxing_energy_summary(self, wuxing):
        if not wuxing: return "无数据"
        lines = []
        for k, v in wuxing.items():
            if not isinstance(v, dict): continue
            ratio_str = v.get('ratio', '0%')
            try:
                ratio_int = int(float(ratio_str.replace('%', '')) // 10)
            except: ratio_int = 0
            bar = "█" * ratio_int + "░" * (10 - ratio_int)
            lines.append(f"{k} {bar} {ratio_str}")
        return "\n".join(lines)

    def _format_tougan_check(self, tougan_data):
        if not tougan_data or not isinstance(tougan_data, dict): return "无数据"
        lines = []
        analysis = tougan_data.get("tougan_analysis") or {}
        for stem, info in analysis.items():
            if not isinstance(info, dict): continue
            status = "透出于 " + "、".join(info.get("positions", [])) if info.get("is_tougan") else "未透"
            lines.append(f"- {stem}({info.get('shishen', '？')})：{status}")
        return "\n".join(lines) or "无"

    def _get_yin_bi_elements(self, day_elem):
        order = ["木", "火", "土", "金", "水"]
        if day_elem not in order: return {"bi": day_elem, "yin": "？"}
        idx = order.index(day_elem)
        return {"bi": day_elem, "yin": order[(idx - 1) % 5]}

    def _format_changsheng(self, cs_dict):
        if not cs_dict or not isinstance(cs_dict, dict): return "无数据"
        return "\n".join([f"- {z}：{s}" for z, s in cs_dict.items()])

    def _format_root_analysis(self, roots):
        if not roots or not isinstance(roots, dict) or not roots.get("has_root"): return "日主无根"
        root_items = roots.get("roots", [])
        return "\n".join([f"- {r.get('zhi', '？')}({r.get('source', '？')})：{r.get('changsheng_status', '？')}" for r in root_items if isinstance(r, dict)])

    def _format_interactions(self, interactions):
        if not interactions or not isinstance(interactions, list): return "无重大关系"
        return "\n".join([f"- {i.get('note', '未知关系')}" for i in interactions if isinstance(i, dict)]) or "无重大关系"

    def _format_conflicts(self, interactions):
        if not interactions or not isinstance(interactions, list): return "无重大冲突"
        conflicts = [i.get('note') for i in interactions if isinstance(i, dict) and i.get('type') in ["六冲", "三刑", "利害"]]
        return "\n".join([f"- {c}" for c in conflicts if c]) or "无重大冲突"

    def _format_dayun_list(self, dayuns):
        if not dayuns or not isinstance(dayuns, list): return "无数据"
        return "\n".join([f"- {d.get('age_range', '？')}: {d.get('pillar', '？')} ({d.get('nayin', '？')})" for d in dayuns[:5] if isinstance(d, dict)])

    def _get_fuyi_need(self, strength):
        if not strength: return "维持平衡"
        if "旺" in strength: return "裁抑（克泄耗）"
        if "弱" in strength: return "生扶（印比）"
        return "维持平衡"

    def _get_god_summary(self, history):
        if not history: return "待定"
        pg = history.get("primary_god", {})
        sg = history.get("secondary_god", {})
        tg = history.get("taboo_gods", [])
        
        def format_god(g):
            if not g: return "无"
            if isinstance(g, dict): return g.get("element", "？")
            if isinstance(g, list): return "、".join([ (x.get("element") if isinstance(x, dict) else str(x)) for x in g])
            return str(g)

        res = []
        if pg: res.append(f"用神：{format_god(pg)}")
        if sg: res.append(f"喜神：{format_god(sg)}")
        if tg: res.append(f"忌神：{format_god(tg)}")
        return "；".join(res) or "待定"

    def _get_current_dayun_info(self, data, year):
        if not data: return {}
        dayun_list = (data.get("dayun") or {}).get("dayun_list") or []
        if not dayun_list: return {}
        return dayun_list[0] # 简易逻辑

if __name__ == "__main__":
    # 本地鲁棒性测试
    orch = ReasoningOrchestrator()
    # 构造一个极端的、全是空值的字典
    bad_data = {"pillars": None, "analysis": {"tougan_check": None}}
    try:
        vm = orch._prepare_view_model(bad_data, {})
        print("✓ Super-safe check passed with empty data.")
        print(f"Sample mapping: shishen_table={vm['shishen_table'][:20]}...")
    except Exception as e:
        print(f"❌ Super-safe check failed: {e}")
