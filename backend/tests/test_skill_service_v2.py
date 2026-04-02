from __future__ import annotations

import unittest

from app.agents.planning_agent import PlanningAgent
from app.models.agent_schemas import (
    AgentExecutionStatus,
    AttractionAgentOutput,
    HotelAgentOutput,
    PlanningAgentInput,
    WeatherAgentOutput,
)
from app.models.schemas import Attraction, Location, TripRequest, WeatherInfo
from app.models.skill_schemas import SelectedSkill
from app.services.skill_service import SkillService


class RaisingPlannerRunner:
    def run(self, prompt):
        raise RuntimeError("LLM unavailable")


class SkillServiceV2Test(unittest.TestCase):
    def _build_request(self) -> TripRequest:
        return TripRequest(
            user_id="user-v2",
            session_id="session-v2",
            city="Shanghai",
            start_date="2026-05-02",
            end_date="2026-05-03",
            travel_days=2,
            transportation="Public Transit",
            accommodation="Comfort Hotel",
            preferences=["food"],
            free_text_input="下雨也能玩，不想太挤，想要本地体验",
            budget_level="low",
            travel_style=["local", "citywalk"],
            companions=["family"],
            dietary_restrictions=["vegetarian"],
            mobility_needs=["rest_friendly"],
        )

    def _build_weather(self) -> WeatherAgentOutput:
        return WeatherAgentOutput(
            status=AgentExecutionStatus(success=True, degraded=False),
            weather_info=[
                WeatherInfo(
                    date="2026-05-02",
                    day_weather="大雨",
                    night_weather="阴",
                    day_temp=32,
                    night_temp=24,
                    wind_direction="East",
                    wind_power="<=3",
                )
            ],
            summary="Heavy rain and hot temperature.",
            suggestions=["Prefer indoor stops and avoid midday heat."],
        )

    def test_v2_selection_applies_stage_order_and_caps(self) -> None:
        service = SkillService()
        request = self._build_request()

        static_skills = service.select_static_skills(request=request)
        dynamic_skills = service.augment_dynamic_skills(request=request, weather_result=self._build_weather())
        final_skills = service.finalize_skills(static_skills, dynamic_skills)

        static_keys = [skill.key for skill in static_skills]
        dynamic_keys = [skill.key for skill in dynamic_skills]
        final_keys = [skill.key for skill in final_skills]

        self.assertIn("budget_guard", static_keys)
        self.assertIn("dietary_safe", static_keys)
        self.assertIn("transit_first", static_keys)
        self.assertIn("rainy_day", dynamic_keys)
        self.assertIn("heat_avoidance", dynamic_keys)
        self.assertIn("weekend_peak_avoidance", dynamic_keys)

        self.assertLessEqual(len(final_skills), SkillService.MAX_TOTAL_SKILLS)
        self.assertLessEqual(sum(1 for skill in final_skills if skill.layer == "dynamic"), SkillService.MAX_DYNAMIC_SKILLS)
        self.assertLessEqual(
            sum(1 for skill in final_skills if skill.category in {"hard", "dynamic-hard"}),
            SkillService.MAX_HARD_SKILLS,
        )
        self.assertIn("budget_guard", final_keys)
        self.assertIn("dietary_safe", final_keys)

    def test_v2_suppression_drops_conflicting_style_skill(self) -> None:
        service = SkillService()
        final_skills = service.finalize_skills(
            static_skills=[
                SelectedSkill(
                    key="checkin_spots",
                    name="经典打卡",
                    score=1.2,
                    priority=35,
                    layer="static",
                    category="style",
                )
            ],
            dynamic_skills=[
                SelectedSkill(
                    key="weekend_peak_avoidance",
                    name="周末避峰",
                    score=2.0,
                    priority=12,
                    layer="dynamic",
                    category="dynamic-hard",
                    suppresses=["checkin_spots"],
                )
            ],
        )

        keys = [skill.key for skill in final_skills]
        self.assertIn("weekend_peak_avoidance", keys)
        self.assertNotIn("checkin_spots", keys)


class PlanningValidationLoopV2Test(unittest.IsolatedAsyncioTestCase):
    async def test_planner_validation_repairs_hard_constraints(self) -> None:
        planner = PlanningAgent(planner_runner=RaisingPlannerRunner())
        payload = PlanningAgentInput(
            request=TripRequest(
                user_id="user-plan",
                session_id="session-plan",
                city="Hangzhou",
                start_date="2026-06-01",
                end_date="2026-06-02",
                travel_days=2,
                transportation="Public Transit",
                accommodation="Comfort Hotel",
                preferences=["food"],
                free_text_input="要注意饮食限制和高温",
                budget_level="low",
                travel_style=["local"],
                companions=[],
                dietary_restrictions=["vegetarian"],
                mobility_needs=[],
            ),
            profile_context="",
            memory_context="",
            rag_context="",
            recommendation_reasons=[],
            skills=[
                SelectedSkill(
                    key="dietary_safe",
                    name="饮食安全",
                    layer="static",
                    category="hard",
                    hard_rules=["所有餐饮建议必须符合饮食限制。"],
                    meal_rules=["每餐都要说明为何符合饮食限制。"],
                ),
                SelectedSkill(
                    key="heat_avoidance",
                    name="高温避暑",
                    layer="dynamic",
                    category="dynamic-hard",
                    hard_rules=["高温时优先安排上午和傍晚的重点活动。"],
                    routing_rules=["减少正午高强度户外移动。"],
                ),
            ],
            attraction_result=AttractionAgentOutput(
                status=AgentExecutionStatus(success=True),
                search_queries=["museum"],
                attractions=[
                    Attraction(
                        name="Hangzhou Museum",
                        address="18 Liangdaoshan Road",
                        location=Location(longitude=120.1551, latitude=30.2741),
                        visit_duration=120,
                        description="Indoor museum.",
                        category="museum",
                        ticket_price=0,
                    )
                ],
            ),
            weather_result=WeatherAgentOutput(
                status=AgentExecutionStatus(success=True),
                weather_info=[
                    WeatherInfo(
                        date="2026-06-01",
                        day_weather="Sunny",
                        night_weather="Clear",
                        day_temp=33,
                        night_temp=26,
                        wind_direction="East",
                        wind_power="<=3",
                    )
                ],
                summary="Hot weather",
                suggestions=["Avoid midday heat."],
            ),
            hotel_result=HotelAgentOutput(
                status=AgentExecutionStatus(success=True),
                search_queries=["hotel"],
                hotels=[],
            ),
            supervisor_warnings=[],
        )

        prompt = planner._build_prompt(payload)
        self.assertIn('"hard_rules"', prompt)
        self.assertIn('"meal_rules"', prompt)
        self.assertIn("dietary_safe", prompt)
        self.assertIn("heat_avoidance", prompt)

        result = await planner.execute(payload)
        self.assertEqual(len(result.trip_plan.applied_skills), 2)
        self.assertTrue(any("饮食限制" in warning for warning in result.status.warnings))
        self.assertTrue(any("高温" in warning for warning in result.status.warnings))


if __name__ == "__main__":
    unittest.main()
