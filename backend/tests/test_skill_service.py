from __future__ import annotations

import unittest

from app.agents.attraction_agent import AttractionAgent
from app.agents.planning_agent import PlanningAgent
from app.models.agent_schemas import (
    AgentExecutionStatus,
    AttractionAgentOutput,
    HotelAgentOutput,
    PlanningAgentInput,
    WeatherAgentOutput,
)
from app.models.schemas import Attraction, Location, TripRequest
from app.models.skill_schemas import SelectedSkill
from app.services.skill_service import SkillService


class RaisingPlannerRunner:
    def run(self, prompt):
        raise RuntimeError("LLM unavailable")


class SkillServiceTest(unittest.TestCase):
    def test_select_skills_matches_request_signals(self) -> None:
        request = TripRequest(
            user_id="user-skill",
            session_id="session-skill",
            city="Shanghai",
            start_date="2026-05-01",
            end_date="2026-05-03",
            travel_days=3,
            transportation="public transit",
            accommodation="comfort hotel",
            preferences=["food"],
            free_text_input="Need rain backup and indoor options",
            budget_level="medium",
            travel_style=["citywalk"],
            companions=["family"],
            dietary_restrictions=[],
            mobility_needs=["low walking load"],
        )

        selected = SkillService().select_skills(
            request=request,
            profile_context="",
            memory_context="",
            rag_context="",
        )
        keys = [skill.key for skill in selected]

        self.assertIn("rainy_day", keys)
        self.assertIn("family_friendly", keys)
        self.assertIn("low_mobility", keys)
        self.assertEqual(len(selected), 3)


class AttractionSkillInjectionTest(unittest.TestCase):
    def test_attraction_queries_include_skill_boosts(self) -> None:
        request = TripRequest(
            user_id="user-queries",
            session_id="session-queries",
            city="Beijing",
            start_date="2026-04-01",
            end_date="2026-04-02",
            travel_days=2,
            transportation="walk",
            accommodation="comfort hotel",
            preferences=[],
            free_text_input="",
            budget_level="medium",
            travel_style=[],
            companions=[],
            dietary_restrictions=[],
            mobility_needs=[],
        )
        rainy_skill = SelectedSkill(
            key="rainy_day",
            name="雨天备选",
            attraction_query_boosts=["室内景点", "博物馆"],
        )

        payload = type(
            "Payload",
            (),
            {
                "request": request,
                "rag_context": "",
                "skills": [rainy_skill],
            },
        )()
        queries = AttractionAgent(amap_service=object())._build_queries(payload)

        self.assertGreaterEqual(len(queries), 2)
        self.assertEqual(queries[0], "室内景点")
        self.assertEqual(queries[1], "博物馆")


class PlanningSkillInjectionTest(unittest.IsolatedAsyncioTestCase):
    def _build_request(self) -> TripRequest:
        return TripRequest(
            user_id="user-plan",
            session_id="session-plan",
            city="Hangzhou",
            start_date="2026-06-01",
            end_date="2026-06-02",
            travel_days=2,
            transportation="public transit",
            accommodation="comfort hotel",
            preferences=["museum"],
            free_text_input="Need indoor plan",
            budget_level="medium",
            travel_style=["citywalk"],
            companions=["family"],
            dietary_restrictions=[],
            mobility_needs=[],
        )

    async def test_planner_prompt_and_fallback_include_skills(self) -> None:
        planner = PlanningAgent(planner_runner=RaisingPlannerRunner())
        rainy_skill = SelectedSkill(
            key="rainy_day",
            name="雨天备选",
            planning_rules=["优先安排室内景点"],
            reasons=["matched keyword: rain"],
        )
        payload = PlanningAgentInput(
            request=self._build_request(),
            profile_context="",
            memory_context="",
            rag_context="",
            recommendation_reasons=[],
            skills=[rainy_skill],
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
                weather_info=[],
                summary="Rain expected",
                suggestions=["Prefer indoor stops."],
            ),
            hotel_result=HotelAgentOutput(
                status=AgentExecutionStatus(success=True),
                search_queries=["hotel"],
                hotels=[],
            ),
            supervisor_warnings=[],
        )

        prompt = planner._build_prompt(payload)
        self.assertIn('"skills"', prompt)
        self.assertIn("rainy_day", prompt)
        self.assertIn("优先安排室内景点", prompt)

        result = await planner.execute(payload)
        self.assertEqual(len(result.trip_plan.applied_skills), 1)
        self.assertEqual(result.trip_plan.applied_skills[0].key, "rainy_day")


if __name__ == "__main__":
    unittest.main()
