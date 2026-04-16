# 当前系统评分机制说明

本文档说明 TripWeaver 当前版本的“最终方案评分”机制，覆盖评分入口、核心数据结构、六个评分维度、综合分生成方式，以及前端展示逻辑。

相关实现位置：

- 后端评分服务：[backend/app/services/plan_score_service.py](/d:/TripWeaver/backend/app/services/plan_score_service.py:45)
- 评分数据结构：[backend/app/models/schemas.py](/d:/TripWeaver/backend/app/models/schemas.py:102)
- 行程生成时写入评分：[backend/app/api/routes/trip.py](/d:/TripWeaver/backend/app/api/routes/trip.py:34)
- 结果页评分展示：[frontend/src/views/Result.vue](/d:/TripWeaver/frontend/src/views/Result.vue:366)

## 1. 设计目标

当前评分系统的目标不是比较“前后两个版本谁更好”，而是只针对“当前方案”做一次立体分析：

- 这版行程是否贴合用户偏好
- 当前预算是否合理
- 路线是否顺路
- 每天节奏是否轻松
- 遇到天气或信息变化时是否稳健
- 整趟旅行的体验层次是否丰富

评分结果既要给出一个综合分，也要解释每个维度的分数是怎么来的。

## 2. 评分入口

系统目前有两个评分入口：

### 2.1 行程生成时自动评分

在 `POST /api/trip/plan` 中，系统生成完 `trip_plan` 后，会立刻调用评分服务：

- `trip_plan.decision_score = get_plan_score_service().evaluate_trip_plan(trip_plan, request)`

这里传入的是：

- 当前生成出的完整行程 `TripPlan`
- 用户本次请求 `TripRequest`

也就是说，首次评分会同时参考：

- 行程内容本身
- 用户输入的预算档位、出行风格、同行人、行动需求、交通偏好等摘要信息

### 2.2 编辑行程后的实时重算

结果页在编辑模式下，会在行程内容变化后延迟 360ms 重新调用：

- `POST /api/trip/score`

前端传入：

- `plan`: 当前被编辑后的 `TripPlan`
- `summary`: 页面缓存的 `TripScoreSummary`

对应逻辑见：

- [frontend/src/views/Result.vue](/d:/TripWeaver/frontend/src/views/Result.vue:782)
- [backend/app/api/routes/trip.py](/d:/TripWeaver/backend/app/api/routes/trip.py:107)

因此，当前评分是“动态的当前态评分”，不是一次生成后固定不变的静态分。

## 3. 输入数据来源

评分服务的输入可以概括为两类：

### 3.1 行程结构数据

来自 `TripPlan`：

- 天数 `days`
- 每天景点 `attractions`
- 每天餐饮 `meals`
- 酒店 `hotel`
- 交通方式 `transportation`
- 交通费用 `transportation_cost`
- 天气 `weather_info`
- 已启用技能 `applied_skills`

### 3.2 用户偏好摘要

来自 `TripScoreSummary` 或 `TripRequest`：

- `budget_level`
- `travel_style`
- `companions`
- `mobility_needs`
- `transportation`
- `free_text_input`

评分服务内部会先统一成 `TripScoreSummary`，这样无论来自首次生成还是二次编辑，逻辑都是同一套。

## 4. 评分输出结构

后端返回的主结构为 `DecisionScoreSnapshot`，字段如下：

- `overall`: 综合分，0-100
- `dimensions`: 六个维度的详细得分
- `summary`: 当前方案的一句话结论
- `story`: 当前方案的整体叙事化描述
- `highlights`: 当前强项列表
- `risks`: 当前风险或待优化点列表
- `budget`: 当前预算汇总
- `estimated_distance_km`: 估算总路程
- `estimated_distance_text`: 展示用路程文本
- `comfort_text`: 展示用节奏摘要

其中每个维度 `DecisionScoreDimension` 还包含：

- `key`: 维度唯一键
- `label`: 维度名
- `description`: 维度说明
- `score`: 维度分数
- `detail`: 当前维度的摘要解释
- `narrative`: 更生动的描述文案
- `factors`: 该维度的打分因子列表

每个因子 `DecisionScoreFactor` 包含：

- `label`: 因子名称
- `impact`: 对当前维度的影响值，可正可负
- `reason`: 为什么加分或扣分
- `value`: 关键指标值或上下文

## 5. 综合分计算

系统固定使用六个维度，并按权重加权求和：

| 维度 key | 中文含义 | 权重 |
| --- | --- | --- |
| `preference_fit` | 偏好贴合 | 0.25 |
| `budget_fit` | 预算友好 | 0.20 |
| `route_efficiency` | 路线顺手 | 0.15 |
| `comfort` | 舒适轻松 | 0.15 |
| `resilience` | 稳健弹性 | 0.10 |
| `richness` | 体验层次 | 0.15 |

综合分公式：

```text
overall = round(
  preference_fit * 0.25 +
  budget_fit * 0.20 +
  route_efficiency * 0.15 +
  comfort * 0.15 +
  resilience * 0.10 +
  richness * 0.15
)
```

最终再通过 `_clamp_score()` 限制在 `0-100`。

## 6. 评分前的基础统计

在计算六个维度前，系统会先从当前方案中提取一批基础统计量：

- `days`: 行程天数，至少按 1 天算
- `budget`: 预算汇总
- `avg_attractions_per_day`: 日均景点数
- `avg_visit_minutes_per_day`: 日均总停留时长
- `estimated_distance_km`: 全行程估算路程
- `avg_distance_km`: 日均估算路程
- `indoor_ratio`: 室内景点占比
- `local_ratio`: 本地感景点占比
- `iconic_count`: 地标/标志性景点数
- `unique_categories`: 景点类别数
- `unique_meals`: 不重复餐饮名称数
- `weather_severity`: 天气压力统计
- `missing_meals_days`: 少于 3 餐的天数
- `missing_hotel_days`: 缺失酒店信息的天数
- `has_rain_skill`: 是否启用 `rainy_day`
- `has_heat_skill`: 是否启用 `heat_avoidance`

这些统计量是六维打分的共同基础。

## 7. 预算汇总计算

预算由 `build_plan_budget()` 计算，包含四部分：

- 景点总费用：所有景点 `ticket_price` 求和
- 酒店总费用：每天 `hotel.estimated_cost` 求和
- 餐饮总费用：所有餐食 `estimated_cost` 求和
- 交通总费用：每天 `transportation_cost` 求和

总预算公式：

```text
budget.total =
  total_attractions +
  total_hotels +
  total_meals +
  total_transportation
```

## 8. 路程估算机制

系统不会直接读取真实导航结果来算综合评分，而是用点位坐标估算：

1. 从当天景点里提取经纬度
2. 对相邻景点用 Haversine 公式计算直线距离
3. 按交通方式乘以修正系数，模拟真实路线绕行

交通方式映射：

- `walking`: 默认
- `transit`: 如果包含 `metro / subway / bus / transit / 地铁 / 公交`
- `driving`: 如果包含 `taxi / car / drive / 打车 / 驾车 / 网约车`

路线修正系数：

- 步行 `1.18`
- 公交/地铁 `1.32`
- 驾车 `1.45`

特殊处理：

- 非北京城市中，如果坐标异常接近北京中心点，会被认为是错误坐标并忽略

## 9. 天气压力识别

天气通过 `_get_weather_severity()` 统计：

- 如果天气文本包含强降雨关键词，则 `severe_days += 1`
- 如果天气文本包含“雨”，则 `rainy_days += 1`
- 如果白天气温 `>= 30`，则：
  - `severe_days += 1`
  - `hot_days += 1`

这部分会影响舒适度和稳健弹性。

## 10. 六个维度的具体机制

### 10.1 偏好贴合 `preference_fit`

初始分：

- `58`

核心思路：

- 看当前方案是否顺着用户声明的节奏、同行关系、行动能力和交通偏好去组织

主要加减项：

- `slow` 且日均景点 `<= 3` 且日均停留 `<= 420`，加 `10`
- `citywalk` 且日均路程在 `2-12km`，加 `8`
- `checkin` 且存在地标景点，加 `8`
- `local` 且本地感占比 `>= 0.3`，加 `8`
- `food` 且餐饮数量 `>= days * 3`，加 `6`
- `family` 且日均景点 `<= 3`，加 `6`
- 存在行动需求：
  - 若日均路程 `<= 8km` 且日均停留 `<= 360`，加 `12`
  - 否则减 `8`
- 如果每天交通方式都与用户交通偏好一致，加 `8`
- 每有 1 天少于 3 餐，减 `4`

特点：

- 这是综合权重最高的维度
- 强依赖用户输入摘要，如果摘要缺失，这个维度会退化为“只看方案自身”

### 10.2 预算友好 `budget_fit`

预算目标按每天档位乘天数计算：

| 预算档位 | 每天目标 |
| --- | --- |
| `low` | 420 |
| `medium` | 880 |
| `high` | 1800 |

有预算档位时：

- 基础分先设为 `100`
- 计算 `ratio = budget.total / budget_target`

规则：

- 若 `ratio < 0.72`
  - 认为预算压得过紧
  - 扣分：`(0.72 - ratio) * 28`
- 若 `0.72 <= ratio <= 1`
  - 不扣分
  - 视为预算落在舒适区
- 若 `ratio > 1`
  - 认为超预算
  - 扣分：`min(75, (ratio - 1) * 115)`

没有预算档位时：

- 直接给默认分 `82`

特点：

- 这套逻辑不是“越便宜越高分”
- 预算过低也会被认为是体验可能被压缩，因此会扣分

### 10.3 路线顺手 `route_efficiency`

初始分：

- `100`

先根据交通方式选理想日均路程：

| 路线类型 | ideal_distance | max_distance |
| --- | --- | --- |
| `walking` | 6 | 16 |
| `transit` | 14 | 36 |
| `driving` | 90 | 220 |

规则：

- 如果日均路程 `<= ideal_distance`
  - 不扣距离分
- 如果超出理想值
  - 距离扣分为：

```text
route_penalty =
  ((min(avg_distance_km, max_distance) - ideal_distance) /
   (max_distance - ideal_distance)) * 36
```

此外还看景点密度：

- 日均景点 `> 3`
  - 扣 `(avg_attractions_per_day - 3) * 14`
- 日均景点 `< 1.5`
  - 扣 `(1.5 - avg_attractions_per_day) * 8`

特点：

- 既防止路线过绕，也防止单天安排过密或过稀

### 10.4 舒适轻松 `comfort`

初始分：

- `96`

规则：

- 如果日均停留 `> 420` 分钟
  - 扣 `min(28, (avg_visit_minutes_per_day - 420) / 14)`
- 如果日均路程 `> ideal_distance + 2`
  - 扣 `min(22, (avg_distance_km - ideal_distance - 2) * 1.8)`
- 如果存在高压天气日且日均景点 `> 3`
  - 额外扣 `10`
- 如果存在行动需求且日均路程 `> 8`
  - 额外扣 `12`

特点：

- 这个维度主要回答“这趟旅行累不累”
- 它和路线顺手不同，路线顺手更关注路径组织，舒适轻松更关注体力负担

### 10.5 稳健弹性 `resilience`

基础分取决于天气：

- 如果存在高压天气日：`62`
- 否则：`86`

然后继续加减：

- 室内景点占比加分：`indoor_ratio * 24`
- 启用 `rainy_day`，加 `5`
- 启用 `heat_avoidance`，加 `5`
- 每有 1 天少于 3 餐，减 `3`
- 每有 1 天缺酒店，减 `4`
- 若没有可用天气信息，减 `12`

特点：

- 这是“抗波动能力”评分
- 不是看是否精彩，而是看方案在现实世界里会不会一出状况就散架

### 10.6 体验层次 `richness`

初始分：

- `50`

加分项：

- 景点类型多样性：`min(22, len(unique_categories) * 8)`
- 餐饮多样性：`min(14, len(unique_meals) * 2)`
- 本地感：`min(8, local_ratio * 18)`
- 地标记忆点：`min(8, iconic_count * 4)`

扣分项：

- 若景点类别少于 2 类
  - 扣 `max(0, 2 - len(unique_categories)) * 6`

特点：

- 这项评估的是“记忆点”和“层次感”
- 它不直接代表用户偏好，只代表内容是否单薄

## 11. 文案层结论生成

### 11.1 综合结论 `summary` 与 `story`

系统按综合分区间生成总评：

- `>= 90`: 很能打
- `>= 80`: 可以稳稳出发
- `>= 70`: 有骨架，但值得再收一收
- `< 70`: 还需要继续打磨

同时返回更具画面感的 `story` 文案，用于结果页顶部展示。

### 11.2 高亮 `highlights`

规则：

- 取分数最高的 3 个维度
- 若某维度 `>= 88`，文案为“表现很亮眼”
- 若 `>= 80`，文案为“已经站稳”
- 否则为“是当前强项”

### 11.3 风险 `risks`

规则：

- 将维度按分数升序排列
- 只取分数 `< 78` 的前 2 项
- 若 `< 65`，文案为“建议优先补一补”
- 否则为“还能再抛光”

## 12. 前端展示机制

结果页评分区当前是“单方案分析”模式，不再对比基线方案。

主要表现为：

- 只展示当前综合分
- 展示当前方案的气质标签 `scoreMood`
- 展示路线与舒适度概览
- 每个维度只展示当前分数，不展示 delta
- 每个维度支持点击“查看这个分数怎么来的”

相关逻辑见：

- [frontend/src/views/Result.vue](/d:/TripWeaver/frontend/src/views/Result.vue:712)

### 12.1 前端状态标签

结果页会对每个维度做状态分层：

- `>= 85`: `状态很稳`
- `>= 75`: `基本顺手`
- `>= 65`: `还能再抛光`
- `< 65`: `建议再调整`

### 12.2 打分过程展开

点击某维度后，前端会把 `dimension.factors` 展开为因子卡片：

- 正向影响显示 `+x`
- 负向影响显示 `-x`
- 零影响显示 `±0`

这部分完全依赖后端返回的 `factors`，前端不自行推导加减分。

### 12.3 编辑态实时刷新

在结果页编辑模式下：

- 监听 `tripPlan` 深度变化
- 节流 360ms
- 自动调用 `/api/trip/score`
- 回写最新 `decision_score`

因此，删除景点、调整顺序、修改停留时间和票价后，评分会跟着变化。

## 13. 当前机制的特点

### 13.1 优点

- 结构清晰，六个维度职责明确
- 综合分可解释，不是黑盒分
- 因子级明细可直接展示给用户
- 支持编辑态实时重算，反馈速度快

### 13.2 当前限制

- 路程是估算值，不是直接使用真实导航耗时
- 预算模型是规则型模型，不考虑城市物价差异
- 天气压力判断还比较粗粒度
- 用户偏好理解主要依赖结构化字段，`free_text_input` 目前没有深入参与打分
- 室内、本地感、地标感等识别依赖关键词命中，存在召回误差

## 14. 一个简化示例

假设一个 2 天行程有以下特征：

- 中预算
- 日均 2.5 个景点
- 日均停留 360 分钟
- 日均路程 7km
- 含 1 个博物馆、1 个老街区、1 个地标点
- 每天三餐完整
- 有雨天技能

那么系统通常会出现这样的趋势：

- 偏好贴合：高
- 预算友好：中高，取决于是否接近预算目标
- 路线顺手：高
- 舒适轻松：高
- 稳健弹性：中高到高
- 体验层次：中高

最终综合分通常会落在“可以稳稳出发”或更高区间。

## 15. 维护建议

如果后续要继续迭代评分系统，建议优先从下面几个方向扩展：

1. 把路线评分从“距离估算”升级为“真实路线时长 + 换乘成本”
2. 为不同城市引入预算系数，而不是统一全国阈值
3. 让 `free_text_input` 中的强约束直接参与因子生成
4. 为每个维度增加更标准化的因子编码，方便埋点和 A/B 实验
5. 为前端增加“为什么扣分最多”的自动摘要，帮助用户快速调整

---

如果需要，我可以继续在这份文档基础上再补两版内容：

- 面向产品的精简版
- 面向开发的公式与字段对照版
