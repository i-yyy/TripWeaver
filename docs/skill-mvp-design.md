# Travel Agent Skill MVP 设计

## 1. 目标

给当前项目增加一层最小可用的 `skill` 能力，但不重做现有多 agent 架构。

MVP 目标：

- 让系统能根据用户请求自动命中 1 到 3 个 skill。
- 让 skill 影响现有 `AttractionAgent / HotelAgent / PlanningAgent` 的行为。
- 不引入新的外部编排框架，继续沿用当前 `SupervisorAgent -> 子 Agent -> PlanningAgent` 链路。
- skill 先作为“可配置策略层”，不是新的 LLM agent 类型。

非目标：

- 不做通用插件市场。
- 不做动态 Python 代码执行。
- 不做复杂的多轮 skill 调度器。
- 不要求 skill 自己直接调用工具。


## 2. 为什么适合当前项目

当前项目是“结构化多 agent + service 编排”：

- `SupervisorAgent` 负责并发调度子 agent。
- `AttractionAgent`、`HotelAgent`、`WeatherAgent` 主要是规则和 service 调用。
- `PlanningAgent` 才是唯一真正依赖 LLM 的 agent。

这意味着 skill 最合适的位置不是替换 agent，而是补一层：

1. 根据请求选择 skill。
2. 把 skill 转成结构化约束和提示。
3. 把这些约束注入现有子 agent 和 `PlanningAgent`。

这样改动小，可验证，可回退。


## 3. MVP 定义

### 3.1 Skill 的最小职责

一个 skill 只做三件事：

- 描述“什么场景下应该启用它”。
- 提供“额外约束/偏好”。
- 提供“给规划 LLM 的提示片段”。

### 3.2 Skill 不做的事

MVP 阶段 skill 不直接：

- 发起网络请求。
- 自己管理 memory。
- 自己调用 MCP tool。
- 修改最终响应 schema。


## 4. 推荐架构

### 4.1 新增模块

建议新增：

- `backend/app/skills/definitions.py`
- `backend/app/skills/registry.py`
- `backend/app/skills/service.py`
- `backend/app/models/skill_schemas.py`

### 4.2 新增数据流

现有链路：

`/trip/plan`
-> `profile/memory/retriever`
-> `SupervisorAgent`
-> `Attraction/Weather/Hotel`
-> `PlanningAgent`

建议改成：

`/trip/plan`
-> `profile/memory/retriever`
-> `SkillService.select_skills(...)`
-> `SupervisorAgent`
-> `Attraction/Weather/Hotel` 读取 skill 约束
-> `PlanningAgent` 读取 skill prompt 和结构化约束


## 5. 数据模型

### 5.1 SkillDefinition

建议定义：

```python
class SkillDefinition(BaseModel):
    key: str
    name: str
    description: str
    priority: int = 100
    enabled: bool = True
    triggers: list[str] = Field(default_factory=list)
    required_any_tags: list[str] = Field(default_factory=list)
    required_any_keywords: list[str] = Field(default_factory=list)
    incompatible_with: list[str] = Field(default_factory=list)
    attraction_query_boosts: list[str] = Field(default_factory=list)
    hotel_query_boosts: list[str] = Field(default_factory=list)
    planning_rules: list[str] = Field(default_factory=list)
    output_hints: list[str] = Field(default_factory=list)
```

解释：

- `key`: 稳定 id，例如 `rainy_day`
- `triggers`: 人类可读标签，用于维护
- `required_any_tags`: 从 `preferences/travel_style/companions` 命中的标签
- `required_any_keywords`: 从 `free_text_input/rag/profile` 命中的关键词
- `attraction_query_boosts`: 给 `AttractionAgent` 追加检索词
- `hotel_query_boosts`: 给 `HotelAgent` 追加检索词
- `planning_rules`: 注入给 `PlanningAgent` 的硬约束
- `output_hints`: 偏文案层的提示

### 5.2 SkillSelection

建议定义：

```python
class SkillSelection(BaseModel):
    key: str
    score: float
    reasons: list[str] = Field(default_factory=list)
```

### 5.3 Agent 输入扩展

在 `backend/app/models/agent_schemas.py` 增加：

```python
class SelectedSkill(BaseModel):
    key: str
    name: str
    score: float = 0.0
    planning_rules: list[str] = Field(default_factory=list)
    attraction_query_boosts: list[str] = Field(default_factory=list)
    hotel_query_boosts: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
```

并在以下输入里加字段：

- `SupervisorAgentInput.skills: List[SelectedSkill]`
- `AttractionAgentInput.skills: List[SelectedSkill]`
- `HotelAgentInput.skills: List[SelectedSkill]`
- `PlanningAgentInput.skills: List[SelectedSkill]`


## 6. Skill 选择机制

### 6.1 选择原则

MVP 不需要 LLM 选 skill，直接走规则打分，原因：

- 可解释。
- 成本低。
- 容易测。
- 对你们当前场景够用。

### 6.2 输入源

打分输入来自：

- `TripRequest.preferences`
- `TripRequest.travel_style`
- `TripRequest.companions`
- `TripRequest.dietary_restrictions`
- `TripRequest.mobility_needs`
- `TripRequest.free_text_input`
- `profile_context`
- `rag_context`

### 6.3 评分逻辑

建议：

- 标签命中一次 `+1.0`
- 关键词命中一次 `+0.6`
- 来自 `mobility_needs/dietary_restrictions` 的强约束命中 `+1.2`
- `incompatible_with` 冲突后保留高分 skill
- 最终只保留前 3 个 skill

伪代码：

```python
for skill in registry:
    score = 0
    reasons = []
    if request tags hit:
        score += 1.0
    if keyword hit in free_text/profile/rag:
        score += 0.6
    if hard constraint hit:
        score += 1.2
    if score > 0:
        selected.append(SkillSelection(...))
```


## 7. 第一批 Skill

MVP 只建议做 4 个，已经能覆盖你们现有旅游场景的大部分高频需求。

### 7.1 `rainy_day`

触发：

- `free_text_input` 包含“下雨 / 雨天 / 室内 / rain”
- 或天气返回明显降雨

影响：

- `AttractionAgent` 追加查询词：`室内景点`、`博物馆`、`美术馆`
- `PlanningAgent` 规则：
  - 优先室内景点
  - 减少跨区移动
  - 每天至少保留一个雨备方案

### 7.2 `family_friendly`

触发：

- `companions` 包含 `family`

影响：

- `AttractionAgent` 追加：`亲子景点`、`公园`
- `PlanningAgent` 规则：
  - 节奏不要过密
  - 用餐和休息点要明确
  - 避免晚间过远移动

### 7.3 `low_mobility`

触发：

- `mobility_needs` 包含 `low walking load` 等

影响：

- `AttractionAgent` 过滤高步行强度景点
- `HotelAgent` 更偏向交通便利的酒店
- `PlanningAgent` 规则：
  - 每天景点数量上限降低
  - 增加打车/近距离交通说明
  - 午间休息明确写出

### 7.4 `food_explorer`

触发：

- `preferences` 或 `travel_style` 包含 `food`
- 或 `free_text_input` 明确提到美食

影响：

- `PlanningAgent` 规则：
  - 每天餐饮描述必须具体
  - 餐饮与当天路线绑定
  - 保留本地特色与预算说明


## 8. 与现有 Agent 的结合方式

### 8.1 AttractionAgent

现状：

- `_build_queries()` 由标签和自由文本生成查询词。

改造：

- 从 `payload.skills` 收集 `attraction_query_boosts`
- 拼到现有 query 列表前部
- 仍然保留去重和上限控制

最小改动点：

- `backend/app/agents/attraction_agent.py`

### 8.2 HotelAgent

现状：

- `_build_queries()` 主要从住宿类型生成查询词。

改造：

- 从 `payload.skills` 注入 `hotel_query_boosts`
- `low_mobility` 可在 `_score_poi()` 里提高“交通便利/核心区”酒店得分

最小改动点：

- `backend/app/agents/hotel_agent.py`

### 8.3 WeatherAgent

MVP 不要求它读取 skill。

更合理的做法是反过来：

- `SkillService` 初选 `rainy_day`
- `PlanningAgent` 再结合天气结果二次强化

### 8.4 PlanningAgent

这是 skill 最重要的接入点。

现状：

- `_build_prompt()` 已经把请求、画像、记忆、RAG、天气、景点、酒店都打成 JSON。

改造：

- 在 `structured_context` 中加入 `skills`
- 在 prompt 顶部增加“启用的 skill 规则”

建议新增结构：

```python
"skills": [
  {
    "key": "...",
    "name": "...",
    "reasons": [...],
    "planning_rules": [...]
  }
]
```

建议 prompt 增补一句：

`如果 skills 中存在规则，必须优先满足 skill 规则，再安排景点、酒店与餐饮。`

最小改动点：

- `backend/app/agents/planning_agent.py`


## 9. 配置形式

MVP 推荐“代码内注册”，不要先做数据库配置后台。

示例：

```python
SKILL_REGISTRY = [
    SkillDefinition(
        key="rainy_day",
        name="雨天备选",
        description="下雨或用户明确要求室内时启用",
        required_any_keywords=["下雨", "雨天", "室内", "rain"],
        attraction_query_boosts=["室内景点", "博物馆", "美术馆"],
        planning_rules=[
            "优先安排室内或半室内景点",
            "减少长距离步行与跨区移动",
            "为当天提供雨备说明",
        ],
    ),
]
```

原因：

- 更快上线。
- 更容易写单测。
- 技术债可控。

后续如果验证有效，再把定义迁到 YAML 或数据库。


## 10. API 与前端展示

MVP 推荐先做“后端内部可用”，前端只做轻量展示。

### 10.1 后端响应

可以在 `TripPlanResponse.data` 中新增一个非必填字段：

```python
applied_skills: List[str] = []
```

更完整一点可以返回：

```python
applied_skills: List[SkillSelection]
```

### 10.2 前端展示

结果页只需展示：

- 已启用技能：`雨天备选`、`亲子友好`

不用先做复杂解释 UI。


## 11. 测试方案

至少加三类测试。

### 11.1 Skill 选择测试

文件建议：

- `backend/tests/test_skill_service.py`

验证：

- `family` 能命中 `family_friendly`
- `low walking load` 能命中 `low_mobility`
- `雨天` 能命中 `rainy_day`
- 冲突 skill 能正确裁剪

### 11.2 Agent 注入测试

验证：

- `AttractionAgent` 在启用 `rainy_day` 后查询词包含 `室内景点`
- `PlanningAgent._build_prompt()` 输出包含 `skills`

### 11.3 端到端回归测试

验证：

- 不传 skill 相关信号时，系统行为与现在基本一致
- 传 skill 相关信号时，计划结果出现对应约束


## 12. 实施顺序

建议按这个顺序做，能最快出结果：

1. 定义 `skill_schemas.py`
2. 实现 `registry.py`
3. 实现 `SkillService.select_skills()`
4. 扩展 `agent_schemas.py`
5. 在 `/trip/plan` 中选择 skill 并传入 `SupervisorAgent`
6. 改 `AttractionAgent` 和 `HotelAgent` 的 query 逻辑
7. 改 `PlanningAgent._build_prompt()`
8. 增加测试


## 13. MVP 边界判断

只要满足下面四点，就算 MVP 成功：

- 系统能稳定选出 skill
- skill 能改变 query 或 prompt
- 最终行程可观察到 skill 影响
- 不影响现有无 skill 请求的正常结果


## 14. 后续演进

如果 MVP 验证有效，下一阶段再做：

- skill 配置改为 YAML
- skill 支持 hard constraints 和 soft preferences 区分
- skill 与知识库文档做映射
- 根据反馈数据自动增强 skill 触发器
- 给前端增加“为什么启用了这个 skill”的解释


## 15. 最小结论

对这个项目来说，`skill` 最合理的定义不是“一个新的 agent”，而是：

“一层可选择、可解释、可注入到现有多 agent 编排中的策略模块”

这样能最大化复用你们现有：

- `TripRequest`
- 画像
- 记忆
- RAG
- 结构化子 agent
- `PlanningAgent` 的 LLM 生成能力

同时把实现复杂度控制在一个小版本内。
