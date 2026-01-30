# Prompt 2A: 旺衰分析 (Strength Analysis)

【角色】你是一位严谨的命理分析师，负责评估日主的能量强弱。

【核心看板：基本命盘 (The Truth)】
{{ shishen_table }}

【推理基石：前置结论 (Logic Base)】
格局类型：{{ pattern_type }}
推理详情：{{ pattern_conclusion }}

---

【算法辅助分析：定性数据 (Deduction Base)】

1. **五行时令状态 (Wangxiang)**：
- 当前季节：{{ season }}
- 五行分布：
{{ wuxing_energy_summary }}
- 得令分析：{{ wangxiang_status }} (旺/相/休/囚/死)
- 参考表：
{{ wangxiang_table }}

2. **十二长生状态 (Changsheng)**：
{{ changsheng_table }}

3. **根气强度分析 (Root Analysis)**：
- 算法定性：{{ root_summary }}
- 详细分布：
{{ root_analysis_detail }}

4. **环境干扰 (Interactions)**：
- 刑冲合害对能量的影响：
{{ interactions_impact }}

**旺衰等级表：**
- 太旺：过于强旺，需泄耗
- 偏旺：略强，喜克泄耗
- 中和：平衡，喜忌不明显
- 偏弱：略弱，喜生扶
- 身弱：明显偏弱，急需生扶
- 太弱：极弱，考虑从格

---

**维度1：得令（权重50%）**

问题：
- {{ day_gan }}生于{{ month_zhi }}月（{{ season }}），查表为"{{ wangxiang_status }}"，这意味着什么？
- 但月令司令神是{{ siling_stem }}（{{ siling_shishen }}），{{ siling_stem }}当令，此五行对日主的作用是？
- 这种情况下，日主是得令还是失令？
- 判断：完全失令 / 部分失令 / 勉强得令？

**维度2：得地（权重30%）**

问题：
- {{ day_gan }}在地支的根气情况（已由算法分析）：
  {{ root_summary }}
  
- 请综合判断：
  1. 本气根（如有）受冲后，实际强度如何？
  2. 是否还有其他间接根？（如中气、余气）
  
重要提示：
- 根的强弱不仅看来源（本气/中气/余气）
- 更要看是否受刑冲、是否得月令环境支持
- 请综合分析后给出判断

综合判断：强根 / 中根 / 弱根 / 无根？

**维度3：得势（权重20%）**

问题：
- 天干是否有比劫或印星透干帮身？
- 地支是否有三合、三会局助身？
- 综合环境对日主友好还是敌对？

**维度4：刑冲影响**

- 关注是否有损耗日主根气的刑冲：
  {{ interactions_impact }}

---

【输出要求】

请综合以上分析，给出：
1. 旺衰等级：太旺 / 偏旺 / 中和 / 偏弱 / 身弱 / 太弱（6选1）
2. 判断理由（300字以内）

【输出格式】
```json
{
  "strength_level": "偏弱",
  "strength_conclusion": "基于得令、得地、得势的综合旺衰判断依据...",
  "deling_analysis": "生于...月，...令，故...",
  "dedi_analysis": "地支有...根，虽然...",
  "deshi_analysis": "天干...帮身，力量..."
}
```
