"""Static and dynamic skill definitions for V2."""

from __future__ import annotations

from typing import List

from ..models.skill_schemas import SkillDefinition


SKILL_REGISTRY: List[SkillDefinition] = [
    SkillDefinition(
        key="budget_guard",
        name="预算守卫",
        description="Keep the itinerary within the requested budget range.",
        priority=5,
        layer="static",
        category="hard",
        required_budget_levels=["low"],
        required_any_keywords=["省钱", "便宜", "高性价比", "budget"],
        hard_rules=[
            "控制每日景点、餐饮和交通成本，避免明显超出预算档位。",
            "优先安排免费或低门票景点以及性价比较高的酒店方案。",
        ],
        meal_rules=[
            "餐饮建议要体现预算友好，不要默认高消费餐厅。",
        ],
        routing_rules=[
            "减少不必要的跨区移动，控制交通成本。",
        ],
        attraction_query_boosts=["免费景点", "公园", "博物馆"],
        hotel_query_boosts=["经济型酒店", "连锁酒店"],
        output_hints=["突出预算友好和性价比。"],
    ),
    SkillDefinition(
        key="dietary_safe",
        name="饮食安全",
        description="Enforce dietary restrictions in meal planning.",
        priority=6,
        layer="static",
        category="hard",
        required_dietary_restrictions=["vegetarian", "halal", "no_spicy"],
        hard_rules=[
            "所有餐饮建议必须符合用户饮食限制。",
        ],
        meal_rules=[
            "每餐都要明确写出吃什么，以及为什么符合饮食限制。",
        ],
        suppresses=["food_explorer"],
        output_hints=["突出饮食限制被认真执行。"],
    ),
    SkillDefinition(
        key="low_mobility",
        name="低步行负担",
        description="Reduce walking intensity and prioritize accessible routing.",
        priority=7,
        layer="static",
        category="hard",
        required_mobility_needs=["less_walking", "low walking load", "low walking", "wheelchair", "rest_friendly"],
        required_any_keywords=["少走路", "无障碍", "行动不便", "老人", "low walking", "wheelchair"],
        hard_rules=[
            "降低单日景点数量和步行强度。",
            "优先近距离衔接和低强度交通方式。",
        ],
        routing_rules=[
            "说明休息点和低强度交通衔接。",
        ],
        attraction_query_boosts=["室内景点", "休闲景点"],
        hotel_query_boosts=["交通便利酒店", "地铁附近酒店"],
        output_hints=["突出低强度节奏与休息友好。"],
    ),
    SkillDefinition(
        key="family_friendly",
        name="亲子友好",
        description="Keep pacing and stop selection family-friendly.",
        priority=14,
        layer="static",
        category="style",
        required_companions=["family"],
        required_any_keywords=["亲子", "家庭", "带娃", "小朋友"],
        soft_rules=[
            "控制单日节奏，避免安排过密或过晚。",
            "每半天都要有明确的用餐或休息衔接。",
        ],
        attraction_query_boosts=["亲子景点", "公园"],
        output_hints=["突出亲子友好和休息补给。"],
    ),
    SkillDefinition(
        key="food_explorer",
        name="美食优先",
        description="Highlight local food and concrete meal planning.",
        priority=30,
        layer="static",
        category="style",
        required_any_tags=["food"],
        required_any_keywords=["美食", "小吃", "探店", "food", "好吃"],
        soft_rules=[
            "每天三餐都要与当天路线发生联动。",
        ],
        meal_rules=[
            "餐饮描述必须回答吃什么以及为什么这样安排。",
            "尽量体现本地特色和时段合理性。",
        ],
        output_hints=["突出本地特色餐饮与路线联动。"],
    ),
    SkillDefinition(
        key="transit_first",
        name="公共交通优先",
        description="Favor transit-friendly routes and hotel locations.",
        priority=15,
        layer="static",
        category="style",
        required_transport_modes=["public transit"],
        soft_rules=[
            "优先公共交通可达性更好的景点和酒店。",
        ],
        routing_rules=[
            "减少跨区移动，尽量让换乘逻辑清晰。",
        ],
        attraction_query_boosts=["市区景点", "地铁可达景点"],
        hotel_query_boosts=["地铁附近酒店", "交通便利酒店"],
        output_hints=["突出公共交通换乘友好。"],
    ),
    SkillDefinition(
        key="drive_friendly",
        name="自驾友好",
        description="Favor driveable routes and parking-friendly hotel choices.",
        priority=25,
        layer="static",
        category="style",
        required_transport_modes=["drive"],
        soft_rules=[
            "路线可以更灵活，但要优先考虑停车与跨区顺序。",
        ],
        routing_rules=[
            "说明自驾停车和顺路串联逻辑。",
        ],
        hotel_query_boosts=["停车方便酒店", "自驾友好酒店"],
        output_hints=["突出停车便利与路线串联。"],
    ),
    SkillDefinition(
        key="checkin_spots",
        name="经典打卡",
        description="Prioritize landmarks, photo spots, and iconic routes.",
        priority=35,
        layer="static",
        category="style",
        required_any_tags=["checkin"],
        required_any_keywords=["打卡", "拍照", "出片"],
        soft_rules=[
            "优先安排地标型景点和拍照友好时段。",
        ],
        attraction_query_boosts=["热门景点", "地标景点"],
        output_hints=["突出经典打卡与拍照时段。"],
    ),
    SkillDefinition(
        key="local_immersion",
        name="本地体验",
        description="Lean on local knowledge and less touristy recommendations.",
        priority=18,
        layer="static",
        category="style",
        required_any_tags=["local"],
        required_any_keywords=["本地人", "不想太游客", "local"],
        soft_rules=[
            "优先体现街区感、在地感和本地知识。",
        ],
        meal_rules=[
            "尽量体现更在地的餐饮建议。",
        ],
        attraction_query_boosts=["本地人爱去景点", "街区漫游"],
        output_hints=["突出在地感和街区体验。"],
    ),
    SkillDefinition(
        key="couple_romantic",
        name="情侣氛围",
        description="Bias the itinerary toward a couple-friendly rhythm.",
        priority=28,
        layer="static",
        category="style",
        required_companions=["couple"],
        soft_rules=[
            "适当增加傍晚、夜景和氛围型餐饮安排。",
        ],
        output_hints=["突出情侣氛围和轻松节奏。"],
    ),
    SkillDefinition(
        key="rainy_day",
        name="雨天备选",
        description="Rain-aware itinerary mode that prioritizes indoor options.",
        priority=8,
        layer="dynamic",
        category="dynamic-hard",
        required_any_keywords=["下雨", "雨天", "雨", "rain", "indoor", "室内"],
        weather_keywords=["雨", "rain", "storm"],
        hard_rules=[
            "优先安排室内或半室内景点，并减少长距离步行。",
            "在结果中明确雨天备选说明。",
        ],
        routing_rules=[
            "减少暴露在户外的长距离路线。",
        ],
        attraction_query_boosts=["室内景点", "博物馆", "美术馆"],
        output_hints=["突出雨天可执行性和避雨安排。"],
    ),
    SkillDefinition(
        key="heat_avoidance",
        name="高温避暑",
        description="Adjust itinerary density and timeslots for hot weather.",
        priority=9,
        layer="dynamic",
        category="dynamic-hard",
        min_temperature=30,
        required_any_keywords=["怕热", "避暑", "中午别太晒"],
        hard_rules=[
            "高温时优先安排上午和傍晚的重点活动，中午增加休息或室内安排。",
        ],
        routing_rules=[
            "减少正午高强度户外移动。",
        ],
        attraction_query_boosts=["室内景点", "公园", "博物馆"],
        output_hints=["突出高温时段优化和补水休息。"],
    ),
    SkillDefinition(
        key="weekend_peak_avoidance",
        name="周末避峰",
        description="Avoid crowd peaks on weekends and busy periods.",
        priority=12,
        layer="dynamic",
        category="dynamic-hard",
        weekend_only=True,
        required_any_keywords=["不想太挤", "避开人多", "错峰"],
        suppresses=["checkin_spots"],
        hard_rules=[
            "尽量错峰安排热门点，减少同一时段扎堆热门景点。",
        ],
        routing_rules=[
            "给出预约、避峰或提前出发建议。",
        ],
        output_hints=["突出错峰、预约和避开拥挤。"],
    ),
]


def get_skill_registry() -> List[SkillDefinition]:
    return list(SKILL_REGISTRY)
