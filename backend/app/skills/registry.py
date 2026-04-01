"""Static skill definitions for the MVP."""

from __future__ import annotations

from typing import List

from ..models.skill_schemas import SkillDefinition


SKILL_REGISTRY: List[SkillDefinition] = [
    SkillDefinition(
        key="rainy_day",
        name="雨天备选",
        description="Rain-aware itinerary mode that prioritizes indoor options.",
        priority=10,
        required_any_keywords=["rain", "rainy", "下雨", "雨天", "雨", "indoor", "室内"],
        attraction_query_boosts=["室内景点", "博物馆", "美术馆"],
        planning_rules=[
            "优先安排室内或半室内景点，并减少长距离步行。",
            "当天路线尽量集中，避免频繁跨区移动。",
            "在描述中明确雨天备选思路或避雨安排。",
        ],
        output_hints=["突出适合雨天执行的路线与休息点。"],
    ),
    SkillDefinition(
        key="family_friendly",
        name="亲子友好",
        description="Family-oriented pacing, routing, and stop selection.",
        priority=20,
        required_any_tags=["family", "亲子", "儿童", "带娃", "小孩"],
        required_any_keywords=["family", "亲子", "儿童", "带娃", "小朋友"],
        attraction_query_boosts=["亲子景点", "公园"],
        planning_rules=[
            "控制单日节奏，避免安排过密或过晚。",
            "每半天都要有明确的用餐或休息衔接说明。",
            "优先选择家庭出行更友好的景点与交通方式。",
        ],
        output_hints=["突出亲子友好、节奏舒适和休息补给。"],
    ),
    SkillDefinition(
        key="low_mobility",
        name="低步行负担",
        description="Reduce walking intensity and favor convenient transit links.",
        priority=5,
        required_any_tags=[
            "low walking load",
            "low walking",
            "wheelchair",
            "elderly",
            "行动不便",
            "低步行",
            "老人",
        ],
        required_any_keywords=["low walking", "wheelchair", "elderly", "行动不便", "少走路", "老人"],
        attraction_query_boosts=["室内景点", "休闲景点"],
        hotel_query_boosts=["交通便利酒店", "地铁附近酒店"],
        planning_rules=[
            "降低单日景点数量，优先安排近距离衔接。",
            "明确午间休息点或可短暂停留的场所。",
            "优先低步行负担的交通方式，并说明原因。",
        ],
        output_hints=["突出低强度节奏、休息点和交通便利性。"],
    ),
    SkillDefinition(
        key="food_explorer",
        name="美食优先",
        description="Food-first itinerary mode with concrete meal planning.",
        priority=30,
        required_any_tags=["food", "美食", "小吃", "吃"],
        required_any_keywords=["food", "美食", "小吃", "探店", "好吃", "吃什么"],
        planning_rules=[
            "每天三餐都要结合当天路线给出具体建议。",
            "餐饮描述必须回答吃什么以及为什么这样安排。",
            "优先体现本地特色、时段合理性和预算匹配。",
        ],
        output_hints=["突出本地特色餐饮与路线联动。"],
    ),
]


def get_skill_registry() -> List[SkillDefinition]:
    return list(SKILL_REGISTRY)
