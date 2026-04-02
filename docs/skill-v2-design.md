# Travel Agent Skill V2 设计

## 1. 目标

第一版 skill 已经验证了三件事：

- skill 机制能稳定落到当前项目的多 agent 编排中
- skill 能真实影响 query、排序和 planning prompt
- 前端用户可以通过现有表单稳定触发 skill

第二版的目标不是简单“再加几个 skill”，而是把 skill 系统从第一版的轻量策略层升级成更可控的约束系统。

第二版要解决的核心问题：

1. skill 需要区分 `static` 和 `dynamic`
2. skill 需要有数量上限，避免互相稀释
3. `hard constraints` 不能只靠 prompt，需要后置校验闭环
4. skill 要继续保持轻量，不引入复杂自治链路


## 2. 第二版总体原则

第二版建议坚持四个原则：

### 2.1 阶段顺序固定

`static` 和 `dynamic` 的大阶段顺序要写死，不建议自由组合。

推荐顺序：

1. 入口阶段执行 `static selection`
2. 子 agent 获取结构化结果
3. 基于运行时结果执行 `dynamic augmentation`
4. 合并 skill 并做冲突处理
5. 把最终 skill 集合交给 `PlanningAgent`
6. 规划结果出来后执行 `hard constraint validation`

原因：

- `static skills` 依赖用户输入，天然应该先出
- `dynamic skills` 依赖天气、日期、中间结果，天然应该后出
- 如果不固定顺序，skill 来源会混乱，调试、解释、测试都会变难

建议：

- 阶段顺序固定
- 阶段内规则可扩展

### 2.2 skill 数量受控

第二版必须给 skill 设置执行上限，而且不能只设置总数上限，还要设置分层上限。

推荐上限：

- `hard-constraint skills` 最多 3 个
- `style/preference skills` 最多 2 个
- 最终总 skill 上限 4 个

原因：

- skill 太多会让 prompt 稀释
- query boost 太多会让召回发散
- 冲突会明显增加
- 前端解释成本会快速上升

裁剪原则：

1. 优先保留 `hard constraints`
2. 再保留高分 `dynamic skills`
3. 最后保留 `style skills`

### 2.3 hard constraints 必须闭环

第二版最重要的增强，是给 `hard constraints` 增加后置校验闭环。

推荐做法不是复杂反思链，而是轻量 validator：

1. `PlanningAgent` 产出 trip plan
2. `PlanConstraintValidator` 对结果做规则检查
3. 如果轻微违规：
   - 记录 warning
   - 尝试自动修补局部字段
4. 如果严重违规：
   - 执行一次 repair
   - 或回退到 deterministic/fallback repair

为什么必须做：

- 只靠 prompt，LLM 不会稳定 100% obey
- 如果没有校验，`hard constraints` 只是建议，不是真约束
- 第二版里预算、饮食、天气这类 skill 必须具备“校验后可解释”

### 2.4 skill 继续保持轻量

第二版依然不建议做：

- skill 自己直接发起独立工具调用
- skill 链式多轮自治决策
- 黑盒 LLM skill selector
- skill marketplace

当前项目的优势是结构简单、可控、可测，第二版不要把系统做重。


## 3. 第二版 skill 分类

第二版建议把 skill 分成两大类。

### 3.1 约束型 skill

优先级高于偏好型 skill，负责解决“不能踩线”的问题。

典型场景：

- 预算
- 饮食限制
- 天气高温
- 周末高峰
- 交通限制

### 3.2 风格型 skill

负责解决“更像用户想要的旅行”的问题。

典型场景：

- 本地体验
- 公共交通优先
- 自驾友好
- 经典打卡
- 情侣氛围


## 4. 第二版推荐 skill

下面保留并明确推荐第二版的 skill 列表。

## 4.1 P0：第二版首批必须做

### 4.1.1 `budget_guard`

目标：

- 把 `budget_level` 变成真正的执行约束

为什么值得做：

- 预算是高频输入
- 当前预算更多影响估价，约束还不够强

触发：

- `budget_level = low`
- 或 free text 命中：`省钱`、`便宜`、`高性价比`

作用：

- `AttractionAgent` 优先免费或低门票景点
- `HotelAgent` 提高经济型酒店排序
- `PlanningAgent` 控制门票、餐饮、交通成本描述
- `PlanConstraintValidator` 检查总体预算是否明显超出 `low`

skill 类型：

- `hard constraint`

### 4.1.2 `dietary_safe`

目标：

- 把饮食限制真正作用到每日三餐

为什么值得做：

- 第一版有 `food_explorer`，但缺“能不能吃”的约束
- 餐饮错误是高敏感问题

触发：

- `dietary_restrictions` 非空
- 如 `vegetarian`、`halal`、`no_spicy`

作用：

- `PlanningAgent` 生成三餐时加入硬约束
- meal 描述必须回答：吃什么、为什么符合限制
- `PlanConstraintValidator` 检查三餐是否违反限制

skill 类型：

- `hard constraint`

### 4.1.3 `heat_avoidance`

目标：

- 针对高温天气调整节奏和时段

为什么值得做：

- 和 `rainy_day` 对称，是高频天气需求
- 适用范围很广

触发：

- `WeatherAgent` 返回首日高温，例如 `day_temp >= 30`
- 或 free text 命中：`怕热`、`避暑`、`中午别太晒`

作用：

- `AttractionAgent` 提高室内、阴凉、傍晚友好景点
- `PlanningAgent` 调整时段，上午和傍晚安排主景点，中午安排休息或室内
- `PlanConstraintValidator` 检查高温日是否仍安排过多暴晒户外点

skill 类型：

- `dynamic hard constraint`

### 4.1.4 `weekend_peak_avoidance`

目标：

- 在周末或高峰日期减少拥挤与排队风险

为什么值得做：

- itinerary 现在缺少“时间维度的拥挤策略”
- 对热门城市非常有效

触发：

- 日期落在周五晚、周六、周日
- 或 free text 命中：`不想太挤`、`避开人多`

作用：

- `AttractionAgent` 降低热门打卡点默认权重
- `PlanningAgent` 加入错峰顺序、预约提醒、避峰时段
- validator 检查是否仍把多个热门点堆在同一高峰时段

skill 类型：

- `dynamic hard constraint`


## 4.2 P1：第二批建议做

### 4.2.1 `transit_first`

目标：

- 让公共交通成为真实约束，而不只是文本偏好

触发：

- `transportation = Public Transit`

作用：

- `AttractionAgent` 倾向公共交通可达区域
- `HotelAgent` 提高交通枢纽附近酒店权重
- `PlanningAgent` 减少跨区移动，细化换乘说明

skill 类型：

- `style/preference`，但优先级较高

### 4.2.2 `drive_friendly`

目标：

- 让自驾场景拥有不同的路线风格

触发：

- `transportation = Drive`

作用：

- `AttractionAgent` 接受稍远但串联性好的景点
- `HotelAgent` 倾向停车便利
- `PlanningAgent` 说明停车与跨区顺序

skill 类型：

- `style/preference`

### 4.2.3 `checkin_spots`

目标：

- 满足经典打卡和拍照导向用户

触发：

- `travel_style` 包含 `checkin`
- 或 free text 命中：`拍照`、`打卡`

作用：

- `AttractionAgent` 提高地标景点权重
- `PlanningAgent` 增加最佳时段、拍照停留说明

skill 类型：

- `style/preference`

### 4.2.4 `local_immersion`

目标：

- 更充分利用现有 RAG 和本地知识库

触发：

- `travel_style` 包含 `local`
- 或 free text 命中：`本地人`、`不想太游客`

作用：

- `PlanningAgent` 优先利用本地知识片段
- 餐饮、街区、步行段更偏在地感
- `AttractionAgent` 可降低标准热门点权重

skill 类型：

- `style/preference`

### 4.2.5 `couple_romantic`

目标：

- 把情侣行程和家庭行程明显区分

触发：

- `companions` 包含 `couple`

作用：

- `PlanningAgent` 更偏夜景、傍晚、氛围餐饮、轻松节奏

skill 类型：

- `style/preference`


## 4.3 第二版最推荐的 6 个 skill

如果第二版只做一轮，我建议选这 6 个：

1. `budget_guard`
2. `dietary_safe`
3. `heat_avoidance`
4. `weekend_peak_avoidance`
5. `transit_first`
6. `local_immersion`

原因：

- 覆盖预算、饮食、天气、日期、交通、RAG 六个关键维度
- 都能映射到现有字段和现有服务结果
- 不需要新增前端表单
- 能明显拉开与第一版 skill 的边界


## 5. 第二版执行流程

第二版建议把 skill 生命周期固定成下面这条链路。

### 5.1 Phase A：Static Selection

输入：

- `TripRequest`
- `profile_context`
- `memory_context`
- `rag_context`

输出：

- 第一批 `static skills`

候选：

- `budget_guard`
- `dietary_safe`
- `transit_first`
- `drive_friendly`
- `checkin_spots`
- `local_immersion`
- `couple_romantic`

### 5.2 Phase B：Sub-Agent Execution

执行：

- `AttractionAgent`
- `WeatherAgent`
- `HotelAgent`

此阶段读取 `static skills`

### 5.3 Phase C：Dynamic Augmentation

基于运行时结果补 dynamic skills：

- `rainy_day`
- `heat_avoidance`
- `weekend_peak_avoidance`

这一步建议是追加，不是重选整套 skill。

### 5.4 Phase D：Merge And Resolve

合并 static/dynamic skills 后：

1. 去重
2. 冲突处理
3. 应用数量上限
4. 得到最终 `final skills`

### 5.5 Phase E：Planning

`PlanningAgent` 接收：

- final skills
- hard rules
- soft rules
- meal rules
- routing rules

### 5.6 Phase F：Post Validation

规划结果出来后执行：

- `PlanConstraintValidator`

结果：

- pass
- pass with warnings
- repair needed


## 6. skill 数量上限设计

第二版建议把 skill 限制写成正式规则。

### 6.1 上限规则

- `hard constraints` 最多 3 个
- `dynamic skills` 最多 2 个
- `style skills` 最多 2 个
- 总上限 4 个

### 6.2 选择优先级

建议保留顺序：

1. `hard constraints`
2. 高分 `dynamic skills`
3. 高分 `style skills`

### 6.3 裁剪示例

如果用户同时命中：

- `budget_guard`
- `dietary_safe`
- `heat_avoidance`
- `weekend_peak_avoidance`
- `transit_first`
- `local_immersion`

最终可能保留：

- `budget_guard`
- `dietary_safe`
- `heat_avoidance`
- `transit_first`

被裁掉的原因应该记录在日志或 evidence 中。


## 7. hard constraints 后置校验闭环

这是第二版必须新增的系统能力。

## 7.1 设计目标

把 hard constraint 从“prompt 约束”升级成“系统约束”。

## 7.2 建议新增模块

- `backend/app/services/plan_constraint_validator.py`

## 7.3 校验输入

- `TripRequest`
- final selected skills
- `TripPlan`
- 天气与结构化结果

## 7.4 校验输出

```python
class ValidationIssue(BaseModel):
    code: str
    severity: str
    message: str
    day_index: int | None = None
    repair_hint: str = ""


class ValidationResult(BaseModel):
    passed: bool
    warnings: list[ValidationIssue]
    errors: list[ValidationIssue]
```

## 7.5 第一批校验规则

### `budget_guard`

检查：

- 总预算是否明显超出目标档位
- 单日门票/酒店/餐饮是否异常偏高

### `dietary_safe`

检查：

- 三餐描述是否体现饮食限制
- 是否出现明显冲突食物

### `heat_avoidance`

检查：

- 高温日是否仍大量安排正午户外高强度景点

### `rainy_day`

检查：

- 雨天是否仍以户外长时间暴露景点为主

### `low_mobility`

检查：

- 单日景点数是否过多
- 是否缺少休息和低强度交通说明

## 7.6 修补策略

建议两级修补：

### 轻微违规

- 直接局部修补字段
- 如修改 meal 描述、补充 warning、降低预算说明

### 严重违规

- 执行一次 `repair_prompt`
- 或调用 fallback rebuild 部分天计划

目标不是做复杂反思，而是保证系统稳定可控。


## 8. skill 数据模型增强建议

第二版建议把 skill 从第一版的扁平规则升级成分层规则。

```python
class SkillDefinition(BaseModel):
    key: str
    name: str
    description: str = ""
    priority: int = 100
    layer: str = "static"  # static / dynamic
    category: str = "style"  # hard / dynamic-hard / style
    enabled: bool = True
    incompatible_with: list[str] = Field(default_factory=list)
    suppresses: list[str] = Field(default_factory=list)
    required_any_tags: list[str] = Field(default_factory=list)
    required_any_keywords: list[str] = Field(default_factory=list)
    hard_rules: list[str] = Field(default_factory=list)
    soft_rules: list[str] = Field(default_factory=list)
    attraction_query_boosts: list[str] = Field(default_factory=list)
    hotel_query_boosts: list[str] = Field(default_factory=list)
    meal_rules: list[str] = Field(default_factory=list)
    routing_rules: list[str] = Field(default_factory=list)
    output_hints: list[str] = Field(default_factory=list)
```

建议把 `SelectedSkill` 升级成：

```python
class SelectedSkill(BaseModel):
    key: str
    name: str
    description: str = ""
    score: float = 0.0
    priority: int = 100
    layer: str = ""
    category: str = ""
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


## 9. 与各 Agent 的接入建议

## 9.1 AttractionAgent

第二版不只是 query boost，还建议增加：

- `must_include_tags`
- `must_avoid_tags`
- `score_multipliers`

典型映射：

- `budget_guard`：降低高票价景点
- `weekend_peak_avoidance`：降低热门打卡点
- `heat_avoidance`：提高室内景点

## 9.2 HotelAgent

第二版重点让酒店排序真正受约束影响：

- 预算层级
- 交通便利性
- 家庭或情侣适配度
- 是否适合休息恢复

## 9.3 PlanningAgent

第二版建议 prompt 明确拆成：

- `hard_constraints`
- `style_preferences`
- `meal_rules`
- `routing_rules`

planner 输出阶段也应尽量体现：

- 哪些安排受到了 skill 影响
- 为什么这样安排

## 9.4 WeatherAgent

第二版建议让天气参与二次触发，而不是单纯提供 summary。

重点支持：

- `rainy_day`
- `heat_avoidance`
- 未来可扩展 `wind_sensitive`


## 10. 冲突处理建议

第二版 skill 增多后，冲突一定会出现。

建议规则：

- `dietary_safe` 优先于 `food_explorer`
- `budget_guard` 可以压制昂贵导向的浪漫或高消费倾向
- `weekend_peak_avoidance` 可以弱化 `checkin_spots`
- `heat_avoidance` 与 `rainy_day` 可共存，但都属于高优先动态约束

推荐实现：

1. 按优先级排序
2. 应用 `suppresses`
3. 应用 `incompatible_with`
4. 再执行数量裁剪


## 11. 开发顺序建议

建议按下面顺序推进，而不是同时铺太多。

### 阶段 A：框架升级

1. `static/dynamic` 固定顺序
2. `hard/soft rules` 拆分
3. skill 数量上限
4. 冲突处理
5. skill evidence 输出
6. `PlanConstraintValidator`

### 阶段 B：首批高价值约束 skill

1. `budget_guard`
2. `dietary_safe`
3. `heat_avoidance`

### 阶段 C：第二批动态与风格 skill

1. `weekend_peak_avoidance`
2. `transit_first`
3. `local_immersion`

这样第二版升级的是“系统能力”，不是单纯“skill 数量”。


## 12. 测试建议

第二版要重点补下面几类测试。

### 12.1 阶段顺序测试

验证：

- `static skills` 一定先于 `dynamic skills`
- `dynamic augmentation` 不会覆盖掉更高优先级的 hard constraints

### 12.2 数量上限测试

验证：

- 总 skill 数不会超过上限
- hard constraints 优先保留
- style skills 被裁剪时有明确 evidence

### 12.3 冲突测试

验证：

- `food_explorer + dietary_safe`
- `checkin_spots + weekend_peak_avoidance`
- `budget_guard + couple_romantic`

### 12.4 validator 测试

验证：

- `budget_guard` 是否真的校验超标
- `dietary_safe` 是否真的校验 meal 文案
- `heat_avoidance` 是否真的校验高温正午安排

### 12.5 前端可解释性测试

验证：

- `applied_skills` 是否包含来源、命中字段、命中词
- 前端是否能稳定展示最终 skill 与影响说明


## 13. 最终建议

如果给第二版一个总方向，我的建议是：

“从偏好型 skill，升级到受控执行的约束型 + 动态型 skill 系统”

具体落地上：

- 保留并优先实现 `budget_guard`、`dietary_safe`、`heat_avoidance`、`weekend_peak_avoidance`、`transit_first`、`local_immersion`
- 把 `static/dynamic` 执行顺序写死
- 对 skill 数量设置分层上限
- 给 `hard constraints` 加后置校验闭环

这样第二版会比第一版更稳定、更可解释，也更接近一个真正可持续扩展的 skill 系统。
