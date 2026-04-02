# Travel Agent Skill V2 设计建议

## 1. 目标

第一版 skill 已经验证了三件事：

- skill 机制对当前项目是可落地的。
- skill 能显著影响 query 和 planning prompt。
- 前端用户能通过表单输入稳定触发 skill。

第二版不应该只是“再加几个 skill”，而应该解决第一版没有覆盖的结构性问题：

1. 从“静态偏好 skill”扩展到“动态约束 skill”。
2. 从“只影响景点和 prompt”扩展到“影响酒店、餐饮、节奏、路线密度”。
3. 从“简单命中”扩展到“有优先级、冲突处理、硬软约束”。


## 2. 第二版总体方向

建议第二版重点做两类 skill：

### 2.1 约束型 skill

这类 skill 解决“不能踩线”的问题，优先级高于偏好。

例如：

- 天气高温
- 周末/热门时段拥挤
- 低预算
- 饮食限制
- 交通方式限制

### 2.2 风格型 skill

这类 skill 解决“怎么更像用户想要的旅行”的问题。

例如：

- 经典打卡
- 本地体验
- 情侣出行
- 夜游偏好
- 一日/短途紧凑行程


## 3. 第二版优先做哪些 skill

下面是我建议的第二版 skill 列表，按优先级排序。

## 3.1 P0：必须优先做

这些 skill 能直接提升结果稳定性和用户感知。

### 3.1.1 `budget_guard`

目标：

- 把预算真正变成可执行约束，而不是只影响酒店估价。

为什么值得做：

- 预算是所有用户都会填的高频字段。
- 目前 `budget_level` 对最终 itinerary 的约束还比较弱。

触发：

- `budget_level = low`
- 或 free text 命中：`省钱`、`便宜`、`高性价比`

作用：

- `AttractionAgent` 优先免费/低门票景点
- `HotelAgent` 提高经济型酒店权重
- `PlanningAgent` 强制控制单日门票/餐饮/交通描述
- `Budget` 汇总时追加预算解释

适合当前架构：

- 你们已经有 `budget_level`、酒店估价、门票估算、交通成本估算，基础足够。

### 3.1.2 `dietary_safe`

目标：

- 把饮食限制从“字段存在”变成“餐饮安排真的可执行”。

为什么值得做：

- 第一版 `food_explorer` 偏“吃得好”，第二版要补“能不能吃”。
- 这个 skill 直接影响 meal 质量，用户体验非常敏感。

触发：

- `dietary_restrictions` 非空
- 如 `vegetarian`、`halal`、`no_spicy`

作用：

- `PlanningAgent` 对三餐生成增加硬约束
- meals 描述必须回答：吃什么、为什么符合限制
- `food_explorer` 与它可以共存，但 `dietary_safe` 优先级更高

适合当前架构：

- 你们当前餐饮主要由 `PlanningAgent` 生成，这种 skill 很容易在 prompt 层先落地。

### 3.1.3 `heat_avoidance`

目标：

- 针对高温、暴晒、夏季出行做节奏调整。

为什么值得做：

- 这是和 `rainy_day` 对称的高频天气 skill。
- 比“雨天备选”更普适，特别适合国内夏季城市旅游。

触发：

- `WeatherAgent` 返回首日高温，例如 `day_temp >= 30`
- 或 free text 命中：`怕热`、`避暑`、`中午别太晒`

作用：

- `AttractionAgent` 提高室内/树荫/傍晚友好景点得分
- `PlanningAgent` 调整时段：上午/傍晚重景点，中午休息或室内
- 餐饮与补给描述要体现降温、休息、补水

适合当前架构：

- 已有天气结构化结果，不需要额外接口。

### 3.1.4 `weekend_peak_avoidance`

目标：

- 周末或高峰日期时，减少过度拥挤和排队风险。

为什么值得做：

- 现在 itinerary 还缺少“时间维度的拥挤策略”。
- 对热门城市和一日游尤其有效。

触发：

- `start_date/end_date` 落在周五晚、周六、周日
- 或 free text 命中：`不想太挤`、`避开人多`

作用：

- `AttractionAgent` 降低“热门景点”默认权重
- `PlanningAgent` 提示避峰时段、提前预约、错峰顺序
- 路线尽量减少跨城热门区的高峰移动

适合当前架构：

- 仅依赖日期推断，不需要联网。


## 3.2 P1：第二批建议做

这些 skill 更偏差异化和风格优化。

### 3.2.1 `transit_first`

目标：

- 当用户选择公共交通时，把路线衔接性做实。

触发：

- `transportation = Public Transit`

作用：

- `AttractionAgent` 倾向地铁/公交可达区域
- `HotelAgent` 提高交通枢纽附近酒店权重
- `PlanningAgent` 避免单日跨区过多，交通说明更具体

为什么推荐：

- 当前交通方式字段已经存在，但更多只是文本回填，没有变成真正的调度约束。

### 3.2.2 `drive_friendly`

目标：

- 当用户自驾时，优先考虑停车、路线串联和非核心商圈点位。

触发：

- `transportation = Drive`

作用：

- `AttractionAgent` 更接受稍远景点
- `HotelAgent` 倾向停车便利、进出城便利
- `PlanningAgent` 描述停车与跨区顺序

为什么推荐：

- 与 `transit_first` 成对，能让交通方式真正控制 itinerary 风格。

### 3.2.3 `checkin_spots`

目标：

- 满足“经典打卡”用户，强调地标、拍照、路线顺滑。

触发：

- `travel_style` 包含 `checkin`
- 或 free text 命中：`拍照`、`打卡`

作用：

- `AttractionAgent` 提高地标类景点得分
- `PlanningAgent` 描述增加拍照时间、最佳时段、路线顺序

为什么推荐：

- 前端已有 `checkin` 风格选项，命中路径清晰。

### 3.2.4 `local_immersion`

目标：

- 真正体现“本地体验”，而不是只是少去游客点。

触发：

- `travel_style` 包含 `local`
- 或 free text 命中：`本地人`、`不想太游客`

作用：

- `PlanningAgent` 优先使用 RAG 本地知识片段
- 减少过度标准化景点描述
- 餐饮、步行段、休息点更偏街区感和在地感

为什么推荐：

- 你们已经有知识库和 recommendation reasons，这个 skill 非常适合和 RAG 做联动。

### 3.2.5 `couple_romantic`

目标：

- 让情侣出行和家庭出行明显区分。

触发：

- `companions` 包含 `couple`

作用：

- `PlanningAgent` 更重视傍晚、夜景、轻松节奏、餐饮氛围
- 酒店和景点说明偏氛围感

为什么推荐：

- 前端已有 `couple` 选项，触发稳定。


## 4. 第二版最推荐的 6 个 skill

如果第二版只做一轮，我建议选这 6 个：

1. `budget_guard`
2. `dietary_safe`
3. `heat_avoidance`
4. `weekend_peak_avoidance`
5. `transit_first`
6. `local_immersion`

原因：

- 覆盖预算、饮食、天气、日期、交通、RAG 利用率六个核心维度。
- 都能映射到现有输入字段或现有服务结果。
- 不依赖新增前端表单。
- 能明显拉开和第一版 skill 的能力边界。


## 5. 第二版架构建议

第二版建议在当前 skill 架构上做 4 个增强。

### 5.1 Skill 分层

把 skill 分成两层：

- `static skills`
  - 来自请求字段和用户主动输入
  - 例如 `food_explorer`、`couple_romantic`
- `dynamic skills`
  - 来自运行时结果
  - 例如 `heat_avoidance`、`weekend_peak_avoidance`

建议流程：

1. 先在 `/trip/plan` 入口做 static selection
2. `WeatherAgent` 返回后做 dynamic augmentation
3. 最终把合并后的 skills 传给 `PlanningAgent`

这样可以避免天气类 skill 在规划前缺少真实依据。

### 5.2 Skill 规则分级

第一版的 `planning_rules` 还是一个扁平列表。

第二版建议拆成：

```python
class SkillDefinition(BaseModel):
    ...
    hard_rules: list[str] = Field(default_factory=list)
    soft_rules: list[str] = Field(default_factory=list)
    attraction_query_boosts: list[str] = Field(default_factory=list)
    hotel_query_boosts: list[str] = Field(default_factory=list)
    meal_rules: list[str] = Field(default_factory=list)
    routing_rules: list[str] = Field(default_factory=list)
```

原因：

- `dietary_safe`、`budget_guard` 这种显然是硬约束
- `local_immersion`、`checkin_spots` 更像软偏好

### 5.3 Skill 冲突策略

第二版 skill 增多后，冲突会明显出现。

建议加两个字段：

```python
incompatible_with: list[str]
suppresses: list[str]
```

示例：

- `budget_guard` 可压制过于昂贵的 `couple_romantic` 酒店倾向
- `dietary_safe` 优先于 `food_explorer`
- `weekend_peak_avoidance` 可弱化 `checkin_spots`

### 5.4 Skill 证据输出

第二版建议给每个 skill 返回更清晰的命中证据：

```python
class SelectedSkill(BaseModel):
    ...
    source: str = ""
    matched_fields: list[str] = Field(default_factory=list)
    matched_terms: list[str] = Field(default_factory=list)
```

这样前端以后可以展示：

- 为什么命中了这个 skill
- 它主要影响了什么


## 6. 第二版与各 Agent 的接入建议

## 6.1 AttractionAgent

第二版不只是 query boost，还应该增加：

- `must_include_tags`
- `must_avoid_tags`
- `score_multipliers`

示例：

- `budget_guard`：降低高票价景点
- `weekend_peak_avoidance`：降低热门/网红点
- `heat_avoidance`：提高室内景点

## 6.2 HotelAgent

第二版要把酒店从“按住宿类型查”升级为“按约束排序”。

重点让 skill 影响：

- 交通便利性
- 家庭/情侣适配度
- 预算层级
- 是否适合休息恢复

## 6.3 PlanningAgent

第二版仍然是 skill 的核心落点。

建议 prompt 中增加两块：

1. `hard_constraints`
2. `style_preferences`

示例：

```json
{
  "skills": [
    {
      "key": "dietary_safe",
      "hard_rules": [
        "所有餐饮建议必须符合饮食限制"
      ],
      "soft_rules": []
    }
  ]
}
```

同时建议让 planner 输出时显式体现：

- 哪些安排受到了 skill 影响
- 为什么这样安排

## 6.4 WeatherAgent

第一版里天气 skill 主要是外部静态命中。

第二版建议让 `WeatherAgent` 参与二次触发：

- `rainy_day`
- `heat_avoidance`
- `wind_sensitive`

这一步不需要它直接选择 skill，只需要产出足够明确的结构化 signal。


## 7. 第二版数据模型建议

建议把当前 `SelectedSkill` 升级成：

```python
class SelectedSkill(BaseModel):
    key: str
    name: str
    description: str = ""
    score: float = 0.0
    priority: int = 100
    source: str = ""
    matched_fields: list[str] = Field(default_factory=list)
    matched_terms: list[str] = Field(default_factory=list)
    hard_rules: list[str] = Field(default_factory=list)
    soft_rules: list[str] = Field(default_factory=list)
    attraction_query_boosts: list[str] = Field(default_factory=list)
    hotel_query_boosts: list[str] = Field(default_factory=list)
    meal_rules: list[str] = Field(default_factory=list)
    routing_rules: list[str] = Field(default_factory=list)
    output_hints: list[str] = Field(default_factory=list)
```

这比第一版更适合扩展，但仍然保持轻量。


## 8. 第二版开发顺序建议

建议按这个顺序做，而不是同时铺太多。

### 阶段 A：增强框架

1. skill 分层：static/dynamic
2. hard/soft rules 拆分
3. 冲突处理
4. skill evidence 输出

### 阶段 B：上 3 个高价值约束 skill

1. `budget_guard`
2. `dietary_safe`
3. `heat_avoidance`

### 阶段 C：上 3 个风格与路径 skill

1. `weekend_peak_avoidance`
2. `transit_first`
3. `local_immersion`

这样能保证第二版不是“skill 数量变多”，而是“能力结构升级”。


## 9. 测试建议

第二版要重点补这几类测试。

### 9.1 冲突测试

例如：

- `food_explorer + dietary_safe`
- `checkin_spots + weekend_peak_avoidance`
- `budget_guard + couple_romantic`

### 9.2 动态触发测试

例如：

- 天气高温时自动命中 `heat_avoidance`
- 周末日期时自动命中 `weekend_peak_avoidance`

### 9.3 Agent 行为测试

例如：

- `budget_guard` 是否真的降低高成本输出
- `dietary_safe` 是否真的影响三餐文案
- `transit_first` 是否真的减少跨区移动

### 9.4 前端可解释性测试

例如：

- 响应里的 `applied_skills` 是否包含证据字段
- 结果页是否能稳定展示 skill 来源和作用


## 10. 第二版的边界

第二版依然不建议做这些：

- skill 自己直接发起独立工具调用
- skill 链式多轮自治决策
- skill marketplace
- 基于 LLM 的黑盒 skill selector

原因很简单：

- 当前项目的成功点在于结构简单、行为可控
- 第二版的重点应该是约束质量和解释能力，而不是把系统做重


## 11. 最终建议

如果只给第二版一个总方向，我的建议是：

“从偏好型 skill，升级到约束型 + 动态型 skill”

具体落地上：

- 先补 `budget_guard`、`dietary_safe`、`heat_avoidance`
- 再补 `weekend_peak_avoidance`、`transit_first`、`local_immersion`
- 同时升级 skill 数据结构，加入 hard/soft rules 和证据字段

这样第二版会明显比第一版更像一个真正可持续扩展的 skill 系统，而不是几个 prompt tag 的集合。
