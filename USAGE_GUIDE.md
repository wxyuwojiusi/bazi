# 八字系统使用指南

## 快速开始

### 1. 生成八字
```python
from bazi_service import BaziService

service = BaziService()

result = service.generate_complete_chart(
    birth_date="1984-02-04",
    birth_time="10:00",
    longitude=113.02,
    latitude=23.70,
    gender="男"
)
```

### 2. 验证结果
```python
from validator import BaziValidator

# 输出详细验证报告
BaziValidator.validate_complete_chart(result)
```

### 3. 理解输出结构

输出的JSON分为以下几个部分：

#### 3.1 basic_info（基础信息）
- **作用**: 记录时间和地点信息
- **给LLM**: ✓ 需要（用于生成报告的开头）
- **关键字段**:
  - `true_solar_time`: 真太阳时（排盘的真实依据）
  - `special_time_marker`: 子时标记（影响日柱判断）

#### 3.2 pillars（四柱）
- **作用**: 八字的核心数据
- **给LLM**: ✓✓✓ 必需（这是分析的基础）
- **关键字段**:
  - `month.siling`: 月令司令神（格局判断的关键）
  - `hidden_stems_detail`: 地支藏干及其十神

#### 3.3 analysis（分析结果）
- **作用**: 算法标注的特征
- **给LLM**: ✓✓ 重要（辅助判断）
- **子字段**:
  - `wuxing_count`: 五行统计（参考，不能直接判断旺衰）
  - `root_analysis`: 根气分析（判断日主强弱的依据）
  - `tougan_check`: 透干检测（格局法的关键）
  - `internal_interactions`: 刑冲合害（影响吉凶）
  - `special_flags`: 特殊标记（提醒LLM注意）

#### 3.4 reference_tables（参考表）
- **作用**: 防止LLM幻觉
- **给LLM**: ✓✓✓ 必需（避免编造数据）
- **包含**:
  - `wangxiang`: 旺相休囚死表
  - `changsheng`: 十二长生表
  - `tiaohou`: 调候用神建议

#### 3.5 dayun（大运）
- **作用**: 运势预测的基础
- **给LLM**: ✓✓ 重要（流年分析需要）
- **包含**: 8步大运序列

### 4. 给LLM的Prompt示例

#### Prompt 1：格局定性

\`\`\`
你是一位命理师，正在分析八字的格局。

【输入数据】
{将 result 的完整JSON粘贴在这里}

【任务】
请按以下步骤判断格局：

1. 查看月令司令神
   - 月支: {从 pillars.month.zhi 提取}
   - 司令神: {从 pillars.month.siling.stem 提取}
   - 司令期: {从 pillars.month.siling.period 提取}

2. 查看透干情况
   - {从 analysis.tougan_check 提取}

3. 判断格局类型
   - 是否为特殊格局？
   - 如果是普通格局，是什么格？

【输出格式】
json
{
  "pattern_type": "正印格",
  "reasoning": "..."
}
\`\`\`

#### Prompt 2：旺衰分析

\`\`\`
【上一步结论】
格局类型：正印格

【当前任务】
分析日主旺衰（6级分类）

【关键数据】
1. 得令分析
   - 季节: {从 reference_tables.season 提取}
   - 日主五行旺相状态: {从 reference_tables.wangxiang 提取}
   - 月令司令神: {从 pillars.month.siling 提取}

2. 得地分析
   - 日主根气: {从 analysis.root_analysis 提取}
   - 受刑冲影响: {从 analysis.internal_interactions 提取}

3. 得势分析
   - 五行分布: {从 analysis.wuxing_count 提取}

【输出格式】
json
{
  "strength_level": "偏弱",
  "reasoning": "..."
}
\`\`\`

## 常见问题

### Q1: 为什么 special_flags 都是空的？

A: 这不是错误！只有满足以下条件才会有标记：
- `wuxing_missing`: 五行缺失（某一五行为0）
- `wuxing_extreme`: 五行极端集中（某一五行占比≥60%）
- `all_yang/all_yin`: 四柱天干全阳或全阴

你的八字如果比较平衡，这些标记就都是空的。

### Q2: hidden_stems_detail 里的 shishen 为什么是空字符串？

A: 这是一个bug！我会在下一个版本修复。
目前的workaround：查看 `analysis` 部分，那里有完整的十神标注。

### Q3: 如何验证计算是否正确？

A: 使用验证工具：
\`\`\`python
from validator import BaziValidator
BaziValidator.validate_complete_chart(result)
\`\`\`

验证工具会：
- 核对每一步计算
- 显示中间结果
- 标注可能的错误