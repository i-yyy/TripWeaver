from __future__ import annotations

import unittest

from app.agents.planning_agent import PlanningAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.models.agent_schemas import (
    AgentExecutionStatus,
    AttractionAgentOutput,
    HotelAgentOutput,
    PlanningAgentInput,
    SupervisorAgentInput,
    WeatherAgentOutput,
)
from app.models.schemas import Attraction, Location, RecommendationReason, TripRequest, WeatherInfo


class StaticAttractionAgent:
    async def execute(self, payload):
        return AttractionAgentOutput(
            status=AgentExecutionStatus(success=True, degraded=False),
            search_queries=["museum"],
            attractions=[
                Attraction(
                    name="Palace Museum",
                    address="4 Jingshan Front Street",
                    location=Location(longitude=116.397026, latitude=39.918058),
                    visit_duration=180,
                    description="Historic landmark.",
                    category="museum",
                    ticket_price=80,
                ),
                Attraction(
                    name="National Museum of China",
                    address="16 East Changan Street",
                    location=Location(longitude=116.401394, latitude=39.904844),
                    visit_duration=180,
                    description="Large indoor collection.",
                    category="museum",
                    ticket_price=40,
                ),
            ],
        )

    def list_tools(self):
        return ["fake-attraction"]


class StaticWeatherAgent:
    async def execute(self, payload):
        return WeatherAgentOutput(
            status=AgentExecutionStatus(success=True, degraded=False),
            weather_info=[
                WeatherInfo(
                    date="2026-04-01",
                    day_weather="Sunny",
                    night_weather="Clear",
                    day_temp=26,
                    night_temp=18,
                    wind_direction="Southwest",
                    wind_power="<=3",
                )
            ],
            summary="Clear weather supports the main itinerary.",
            suggestions=["Put the main attractions in the first half of the day."],
        )

    def list_tools(self):
        return ["fake-weather"]


class DegradedHotelAgent:
    async def execute(self, payload):
        return HotelAgentOutput(
            status=AgentExecutionStatus(
                success=False,
                degraded=True,
                warnings=["Hotel service degraded"],
                error="hotel lookup unavailable",
            ),
            search_queries=["hotel"],
            hotels=[],
        )

    def list_tools(self):
        return ["fake-hotel"]


class RaisingPlannerRunner:
    def run(self, prompt):
        raise RuntimeError("LLM unavailable")


class SupervisorAgentTest(unittest.IsolatedAsyncioTestCase):
    def _build_request(self) -> TripRequest:
        return TripRequest(
            user_id="user-1",
            session_id="session-1",
            city="Beijing",
            start_date="2026-04-01",
            end_date="2026-04-02",
            travel_days=2,
            transportation="Public Transit",
            accommodation="Comfort Hotel",
            preferences=["museum"],
            free_text_input="Need indoor backup",
            budget_level="medium",
            travel_style=["citywalk"],
            companions=["family"],
            dietary_restrictions=[],
            mobility_needs=["low walking"],
        )

    async def test_supervisor_degrades_when_sub_agent_fails(self) -> None:
        request = self._build_request()
        supervisor = SupervisorAgent(
            attraction_agent=StaticAttractionAgent(),
            weather_agent=StaticWeatherAgent(),
            hotel_agent=DegradedHotelAgent(),
            planning_agent=PlanningAgent(planner_runner=RaisingPlannerRunner()),
        )

        result = await supervisor.execute(
            SupervisorAgentInput(
                request=request,
                profile_context="profile-context",
                memory_context="memory-context",
                rag_context="rag-context",
                recommendation_reasons=[RecommendationReason(source_type="profile", title="profile", reason="likes museums")],
            )
        )

        self.assertTrue(result.status.degraded)
        self.assertIn("Hotel service degraded", result.status.warnings)
        self.assertEqual(len(result.planning_result.trip_plan.days), 2)
        self.assertEqual(result.planning_result.trip_plan.days[0].attractions[0].name, "Palace Museum")


class PlanningAgentFallbackTest(unittest.IsolatedAsyncioTestCase):
    def _build_request(self) -> TripRequest:
        return TripRequest(
            user_id="user-2",
            session_id="session-2",
            city="Shanghai",
            start_date="2026-05-01",
            end_date="2026-05-03",
            travel_days=3,
            transportation="Walk",
            accommodation="Budget Hotel",
            preferences=["museum"],
            free_text_input="",
            budget_level="low",
            travel_style=["citywalk"],
            companions=[],
            dietary_restrictions=[],
            mobility_needs=[],
        )

    async def test_planning_fallback_returns_compatible_tripplan(self) -> None:
        request = self._build_request()
        planner = PlanningAgent(planner_runner=RaisingPlannerRunner())
        payload = PlanningAgentInput(
            request=request,
            profile_context="",
            memory_context="",
            rag_context="",
            recommendation_reasons=[],
            attraction_result=AttractionAgentOutput(
                status=AgentExecutionStatus(success=True),
                search_queries=["museum"],
                attractions=[
                    Attraction(
                        name="Shanghai Museum",
                        address="201 Renmin Avenue",
                        location=Location(longitude=121.4737, latitude=31.2304),
                        visit_duration=180,
                        description="Core indoor museum.",
                        category="museum",
                        ticket_price=40,
                    )
                ],
            ),
            weather_result=WeatherAgentOutput(
                status=AgentExecutionStatus(success=True),
                weather_info=[],
                summary="",
                suggestions=["Keep the itinerary flexible."],
            ),
            hotel_result=HotelAgentOutput(
                status=AgentExecutionStatus(success=True),
                search_queries=["hotel"],
                hotels=[],
            ),
            supervisor_warnings=["Hotel candidates unavailable"],
        )

        result = await planner.execute(payload)
        plan = result.trip_plan

        self.assertTrue(result.status.degraded)
        self.assertEqual(plan.city, "Shanghai")
        self.assertEqual(len(plan.days), 3)
        self.assertTrue(all(len(day.meals) == 3 for day in plan.days))
        self.assertIsNotNone(plan.budget)
        self.assertIn("Hotel candidates unavailable", plan.overall_suggestions)


if __name__ == "__main__":
    unittest.main()
