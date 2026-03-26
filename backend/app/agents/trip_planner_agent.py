"""多智能体旅行规划器。"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from hello_agents import SimpleAgent
try:
    from hello_agents.tools import MCPTool  # 旧版 hello-agents
except Exception:  # pragma: no cover - 兼容新版本
    try:
        from hello_agents.tools.builtin.protocol_tools import MCPTool  # type: ignore
    except Exception:  # pragma: no cover - 当前环境缺少 MCPTool
        MCPTool = None  # type: ignore

from ..config import get_settings
from ..models.schemas import Attraction, DayPlan, Location, Meal, TripPlan, TripRequest
from ..services.llm_service import get_llm

ATTRACTION_AGENT_PROMPT = """
你是景点检索专家。
必须使用地图工具检索真实 POI 数据，不可凭空编造。
检索景点时使用：
[TOOL_CALL:amap_maps_text_search:keywords=<关键词>,city=<城市>]
"""

WEATHER_AGENT_PROMPT = """
你是天气查询专家。
必须使用地图工具获取真实天气，不可凭空编造。
查询天气时使用：
[TOOL_CALL:amap_maps_weather:city=<城市>]
"""

HOTEL_AGENT_PROMPT = """
你是酒店推荐专家。
必须使用地图工具检索真实酒店数据，不可凭空编造。
检索酒店时使用：
[TOOL_CALL:amap_maps_text_search:keywords=酒店,city=<城市>]
"""

PLANNER_AGENT_PROMPT = """
你是严谨的旅行行程规划专家。
必须只返回 JSON，不要返回 Markdown、解释性文字或额外前后缀。
返回结构：
{
  "city": "string",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "days": [],
  "weather_info": [],
  "overall_suggestions": "string",
  "budget": {
    "total_attractions": 0,
    "total_hotels": 0,
    "total_meals": 0,
    "total_transportation": 0,
    "total": 0
  }
}
日期与数字字段必须有效。
"""


class MultiAgentTripPlanner:
    """编排景点、天气、酒店和总规划智能体。"""

    def __init__(self) -> None:
        settings = get_settings()
        self.llm = get_llm()
        self.amap_tool = None
        if MCPTool is not None:
            self.amap_tool = MCPTool(
                name="amap",
                description="高德地图服务",
                server_command=["uvx", "amap-mcp-server"],
                env={"AMAP_MAPS_API_KEY": settings.amap_api_key},
                auto_expand=True,
            )
        else:
            print("警告: 当前 hello-agents 版本未提供 MCPTool，将使用无地图工具降级模式。")

        self.attraction_agent = SimpleAgent(
            name="景点检索智能体",
            llm=self.llm,
            system_prompt=ATTRACTION_AGENT_PROMPT,
        )
        if self.amap_tool is not None:
            self.attraction_agent.add_tool(self.amap_tool)

        self.weather_agent = SimpleAgent(
            name="天气查询智能体",
            llm=self.llm,
            system_prompt=WEATHER_AGENT_PROMPT,
        )
        if self.amap_tool is not None:
            self.weather_agent.add_tool(self.amap_tool)

        self.hotel_agent = SimpleAgent(
            name="酒店推荐智能体",
            llm=self.llm,
            system_prompt=HOTEL_AGENT_PROMPT,
        )
        if self.amap_tool is not None:
            self.hotel_agent.add_tool(self.amap_tool)

        self.planner_agent = SimpleAgent(
            name="行程规划智能体",
            llm=self.llm,
            system_prompt=PLANNER_AGENT_PROMPT,
        )

    def plan_trip(
        self,
        request: TripRequest,
        profile_context: str = "",
        memory_context: str = "",
        rag_context: str = "",
    ) -> TripPlan:
        """生成旅行行程。"""
        try:
            attraction_response = self.attraction_agent.run(self._build_attraction_query(request))
            weather_response = self.weather_agent.run(f"[TOOL_CALL:amap_maps_weather:city={request.city}]")
            hotel_response = self.hotel_agent.run(
                f"[TOOL_CALL:amap_maps_text_search:keywords={request.accommodation},city={request.city}]"
            )

            planner_query = self._build_planner_query(
                request=request,
                attractions=attraction_response,
                weather=weather_response,
                hotels=hotel_response,
                profile_context=profile_context,
                memory_context=memory_context,
                rag_context=rag_context,
            )
            planner_response = self.planner_agent.run(planner_query)
            return self._parse_response(planner_response, request)
        except Exception as exc:
            print(f"行程规划失败，启用兜底方案: {exc}")
            return self._create_fallback_plan(request)

    def _build_attraction_query(self, request: TripRequest) -> str:
        keywords = request.preferences[0] if request.preferences else "景点"
        return f"[TOOL_CALL:amap_maps_text_search:keywords={keywords},city={request.city}]"

    def _build_planner_query(
        self,
        request: TripRequest,
        attractions: str,
        weather: str,
        hotels: str,
        profile_context: str,
        memory_context: str,
        rag_context: str,
    ) -> str:
        context_blocks = []
        if profile_context.strip():
            context_blocks.append(profile_context.strip())
        if memory_context.strip():
            context_blocks.append(memory_context.strip())
        if rag_context.strip():
            context_blocks.append(rag_context.strip())
        context_text = "\n\n".join(context_blocks) if context_blocks else "无额外上下文。"

        return f"""
请为 {request.city} 生成 {request.travel_days} 天旅行行程。

基础需求：
- 城市：{request.city}
- 日期：{request.start_date} 到 {request.end_date}
- 交通偏好：{request.transportation}
- 住宿偏好：{request.accommodation}
- 兴趣偏好：{", ".join(request.preferences) if request.preferences else "无"}
- 预算等级：{request.budget_level or "未知"}
- 旅行风格：{", ".join(request.travel_style) if request.travel_style else "无"}
- 同行人群：{", ".join(request.companions) if request.companions else "无"}
- 饮食限制：{", ".join(request.dietary_restrictions) if request.dietary_restrictions else "无"}
- 行动需求：{", ".join(request.mobility_needs) if request.mobility_needs else "无"}
- 补充要求：{request.free_text_input or "无"}

增强上下文：
{context_text}

景点工具结果：
{attractions}

天气工具结果：
{weather}

酒店工具结果：
{hotels}

约束：
1. 每天安排 2-3 个景点。
2. 每天必须包含早/中/晚餐建议。
3. 每天给出一个酒店建议。
4. 结合天气与预算进行安排。
5. 只返回 JSON，不要 Markdown。
"""

    def _parse_response(self, response: str, request: TripRequest) -> TripPlan:
        try:
            json_str = self._extract_json(response)
            data = json.loads(json_str)
            if not isinstance(data, dict):
                raise ValueError("planner response root must be an object")
            normalized = self._normalize_plan_data(data, request)
            return TripPlan(**normalized)
        except Exception as exc:
            print(f"解析规划结果失败，启用兜底方案: {exc}")
            return self._create_fallback_plan(request)

    @staticmethod
    def _extract_json(response: str) -> str:
        if "```json" in response:
            start = response.find("```json") + len("```json")
            end = response.find("```", start)
            return response[start:end].strip()
        if "```" in response:
            start = response.find("```") + len("```")
            end = response.find("```", start)
            return response[start:end].strip()
        if "{" in response and "}" in response:
            start = response.find("{")
            end = response.rfind("}") + 1
            return response[start:end]
        raise ValueError("响应中未找到 JSON")

    def _normalize_plan_data(self, data: Dict[str, Any], request: TripRequest) -> Dict[str, Any]:
        raw_days = data.get("days")
        if not isinstance(raw_days, list):
            raw_days = data.get("itinerary") if isinstance(data.get("itinerary"), list) else []

        days = [self._normalize_day(day, idx, request) for idx, day in enumerate(raw_days)]
        if not days:
            for idx in range(request.travel_days):
                days.append(self._normalize_day({}, idx, request))

        budget = data.get("budget") if isinstance(data.get("budget"), dict) else {}
        total_attractions = self._to_int(budget.get("total_attractions"), default=0)
        total_hotels = self._to_int(budget.get("total_hotels"), default=len(days))
        total_meals = self._to_int(budget.get("total_meals"), default=0)
        total_transport = self._to_int(budget.get("total_transportation"), default=0)
        total_cost = self._to_int(
            budget.get("total"),
            default=total_attractions + total_hotels + total_meals + total_transport,
        )

        return {
            "city": str(data.get("city") or request.city),
            "start_date": str(data.get("start_date") or request.start_date),
            "end_date": str(data.get("end_date") or request.end_date),
            "days": days,
            "weather_info": data.get("weather_info") if isinstance(data.get("weather_info"), list) else [],
            "overall_suggestions": str(
                data.get("overall_suggestions")
                or data.get("summary")
                or f"{request.city} {request.travel_days} 天行程建议"
            ),
            "budget": {
                "total_attractions": total_attractions,
                "total_hotels": total_hotels,
                "total_meals": total_meals,
                "total_transportation": total_transport,
                "total": total_cost,
            },
        }

    def _normalize_day(self, raw_day: Any, day_index: int, request: TripRequest) -> Dict[str, Any]:
        day = raw_day if isinstance(raw_day, dict) else {}

        date_text = day.get("date")
        if not isinstance(date_text, str) or not date_text.strip():
            start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
            date_text = (start_date + timedelta(days=day_index)).strftime("%Y-%m-%d")

        attractions_raw = day.get("attractions") if isinstance(day.get("attractions"), list) else []
        meals_raw = day.get("meals") if isinstance(day.get("meals"), list) else []

        return {
            "date": date_text,
            "day_index": self._to_int(day.get("day_index"), default=day_index),
            "description": str(day.get("description") or day.get("theme") or f"第{day_index + 1}天行程"),
            "transportation": str(day.get("transportation") or request.transportation),
            "accommodation": str(day.get("accommodation") or request.accommodation),
            "attractions": [self._normalize_attraction(item, request.city) for item in attractions_raw],
            "meals": [self._normalize_meal(item, idx) for idx, item in enumerate(meals_raw)],
        }

    def _normalize_attraction(self, raw_item: Any, city: str) -> Dict[str, Any]:
        item = raw_item if isinstance(raw_item, dict) else {}
        return {
            "name": str(item.get("name") or item.get("title") or "推荐景点"),
            "address": str(item.get("address") or city),
            "location": self._normalize_location(item.get("location"), city),
            "visit_duration": self._parse_visit_duration(item.get("visit_duration")),
            "description": str(item.get("description") or item.get("reason") or ""),
            "category": str(item.get("category") or "attraction"),
            "ticket_price": self._to_int(
                item.get("ticket_price") or item.get("price") or item.get("estimated_cost"),
                default=0,
            ),
        }

    def _normalize_meal(self, raw_item: Any, index: int) -> Dict[str, Any]:
        item = raw_item if isinstance(raw_item, dict) else {}
        default_types = ["breakfast", "lunch", "dinner"]
        meal_type = str(item.get("type") or default_types[min(index, 2)])
        meal_name = item.get("name") or item.get("suggestion") or f"{meal_type} recommendation"
        return {
            "type": meal_type,
            "name": str(meal_name),
            "address": str(item.get("address")) if item.get("address") else None,
            "description": str(item.get("description") or item.get("suggestion") or ""),
            "estimated_cost": self._to_int(
                item.get("estimated_cost") or item.get("estimated_cost_per_person"),
                default=0,
            ),
        }

    def _normalize_location(self, raw_location: Any, city: str) -> Dict[str, float]:
        if isinstance(raw_location, dict):
            lng = raw_location.get("longitude", raw_location.get("lng", raw_location.get("lon", 116.40)))
            lat = raw_location.get("latitude", raw_location.get("lat", 39.90))
            return {
                "longitude": self._to_float(lng, default=116.40),
                "latitude": self._to_float(lat, default=39.90),
            }

        if isinstance(raw_location, str) and "," in raw_location:
            parts = [part.strip() for part in raw_location.split(",")]
            if len(parts) >= 2:
                return {
                    "longitude": self._to_float(parts[0], default=116.40),
                    "latitude": self._to_float(parts[1], default=39.90),
                }

        city_lng, city_lat = (116.40, 39.90) if city.lower() == "beijing" else (121.47, 31.23)
        return {"longitude": city_lng, "latitude": city_lat}

    def _parse_visit_duration(self, value: Any) -> int:
        if isinstance(value, (int, float)):
            return max(30, int(value))
        if isinstance(value, str):
            text = value.strip().lower()
            numbers = re.findall(r"\d+(?:\.\d+)?", text)
            if numbers:
                amount = float(numbers[0])
                if "小时" in text or "hour" in text or text.endswith("h"):
                    return max(30, int(amount * 60))
                return max(30, int(amount))
        return 120

    @staticmethod
    def _to_int(value: Any, default: int = 0) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            numbers = re.findall(r"-?\d+", value)
            if numbers:
                return int(numbers[0])
        return default

    @staticmethod
    def _to_float(value: Any, default: float = 0.0) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            numbers = re.findall(r"-?\d+(?:\.\d+)?", value)
            if numbers:
                return float(numbers[0])
        return default

    def _create_fallback_plan(self, request: TripRequest) -> TripPlan:
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        days = []
        for day_index in range(request.travel_days):
            date_text = (start_date + timedelta(days=day_index)).strftime("%Y-%m-%d")
            attractions = [
                Attraction(
                    name=f"{request.city} 景点 {idx + 1}",
                    address=request.city,
                    location=Location(
                        longitude=116.40 + 0.01 * day_index + 0.005 * idx,
                        latitude=39.90 + 0.01 * day_index + 0.005 * idx,
                    ),
                    visit_duration=120,
                    description=f"{request.city} 备选景点",
                    category="景点",
                    ticket_price=0,
                )
                for idx in range(2)
            ]
            meals = [
                Meal(type="breakfast", name="早餐建议", description="本地早餐"),
                Meal(type="lunch", name="午餐建议", description="本地午餐"),
                Meal(type="dinner", name="晚餐建议", description="本地晚餐"),
            ]
            days.append(
                DayPlan(
                    date=date_text,
                    day_index=day_index,
                    description=f"第 {day_index + 1} 天兜底行程",
                    transportation=request.transportation,
                    accommodation=request.accommodation,
                    attractions=attractions,
                    meals=meals,
                )
            )

        return TripPlan(
            city=request.city,
            start_date=request.start_date,
            end_date=request.end_date,
            days=days,
            weather_info=[],
            overall_suggestions=(
                f"这是 {request.city} 的 {request.travel_days} 天兜底行程。"
                "建议出发前确认景点开放时间。"
            ),
        )


_multi_agent_planner: Optional[MultiAgentTripPlanner] = None


def get_trip_planner_agent() -> MultiAgentTripPlanner:
    global _multi_agent_planner
    if _multi_agent_planner is None:
        _multi_agent_planner = MultiAgentTripPlanner()
    return _multi_agent_planner
