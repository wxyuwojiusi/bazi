【核心看板：基本命盘 (The Truth)】
基础信息：
- 性别：{{ gender }}
- 出生时间：{{ birth_date_display }}
- 真太阳时：{{ true_solar_time }}
- 节气背景：{{ season_detail }}

【专业排盘表 (Practitioner's View)】
{{ shishen_table }}

---

【算法原始数据：深度特征 (Deduction Base)】

1. **月令透干检测 (Important)**：
- 月支：{{ month_zhi }}
- 月令藏干：{{ hidden_stems }}
- 透干详情：
{{ tougan_check_list }}
- 算法提示：{{ tougan_pattern_hint }}

2. **月令司令神 (Priority)**：
- 司令藏干：{{ siling_stem }}
- 司令期：{{ siling_period }}（进入第 {{ siling_days }} 天）
- 说明：{{ siling_note }}

3. **辅助特征**：
- 五行占比：
{{ wuxing_energy_summary }}
- 异常标记：
  - 日主无根：{{ has_no_root }}
  - 缺失五行：{{ missing_elements }}
  - 极端分布：{{ element_extreme }}
- 算法预判建议：{{ structural_hint }}

4. **刑冲作用力**：
{{ interaction_list }}

---

【分析任务】

请按以下步骤判断格局：

**Step 1：特殊格局排查**

检查是否满足特殊格局条件：

1. 从格（日主极弱，弃命从势）
   - 日主有无强根？（查异常标记）
   - 四柱是否某一十神成势（占比>60%且得令透干）？
   - 判断：是/否

2. 专旺格（某一五行占绝对优势）
   - 某一五行是否占70%以上？
   - 日主是否为该五行？
   - 判断：是/否

3. 化气格（天干合化，化神得令）
   - 日干是否与他干合化？
   - 化神是否得令透干？
   - 判断：是/否

**Step 2：普通格局判断**

如果不是特殊格局，则判断普通格局：

- 看月令司令神：{{ siling_stem }}（{{ siling_shishen }}）
- {{ siling_stem }}是否透干：{{ siling_is_tougan }}
- 初步格局：{{ potential_pattern }}

**Step 3：最终判定**

请给出结论：
- 格局类型
- 判断依据（200字以内）
- 下一步：进入旺衰分析 / 进入顺势分析

【输出格式】
```json
{
  "pattern_type": "正印格|从格|...",
  "pattern_conclusion": "基于司令神与透根情况的详细判断依据...",
  "next_step": "旺衰分析|顺势分析"
}
```
