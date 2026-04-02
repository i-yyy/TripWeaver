from __future__ import annotations

import unittest
from unittest.mock import patch

from app.agents.planning_agent import PlanningAgent
from app.models.agent_schemas import AgentExecutionStatus, AttractionAgentOutput, HotelAgentOutput, PlanningAgentInput, WeatherAgentOutput
from app.models.schemas import Attraction, DayPlan, Location, Meal, TripPlan, TripRequest


class RaisingPlannerRunner:
    def run(self, prompt):
        raise RuntimeError("LLM unavailable")


class FakeAmapService:
    def get_poi_photo_urls(self, poi_id: str):
        return []

    def build_static_map_url(self, locations, labels=None, zoom=12, size="750*420"):
        label = labels[0] if labels else "X"
        location = locations[0]
        return f"map:{label}:{location.longitude},{location.latitude}"

    def plan_route(self, origin_address, destination_address, origin_city, destination_city, route_type):
        return {"distance": 1200, "duration": 900}


class PlanningAgentContentTest(unittest.TestCase):
    def _build_request(self, dietary_restrictions=None) -> TripRequest:
        return TripRequest(
            user_id="user-content",
            session_id="session-content",
            city="Shanghai",
            start_date="2026-04-08",
            end_date="2026-04-08",
            travel_days=1,
            transportation="Public Transit",
            accommodation="Comfort Hotel",
            preferences=["food"],
            free_text_input="",
            budget_level="medium",
            travel_style=[],
            companions=[],
            dietary_restrictions=dietary_restrictions or [],
            mobility_needs=[],
        )

    def test_generic_meal_names_are_rewritten_to_concrete_foods(self) -> None:
        planner = PlanningAgent(planner_runner=RaisingPlannerRunner())
        request = self._build_request(["vegetarian"])

        meals = [
            Meal(type="breakfast", name="\u7b80\u9910", description="\u65b9\u4fbf\u8844\u63a5\u5f53\u5929\u884c\u7a0b", estimated_cost=0),
            Meal(type="lunch", name="\u7d20\u98df\u9910", description="", estimated_cost=0),
            Meal(type="dinner", name="\u665a\u9910", description="", estimated_cost=0),
        ]

        enriched = planner._enrich_meals(meals, request)

        self.assertIn("\u8c46\u6d46", enriched[0].name)
        self.assertIn("\u83cc\u83c7\u9762", enriched[1].description)
        self.assertNotIn("\u7b80\u9910", enriched[0].name)
        self.assertNotIn("\u7d20\u98df\u9910", enriched[1].name)

    def test_duplicate_attraction_images_fall_back_to_map(self) -> None:
        planner = PlanningAgent(planner_runner=RaisingPlannerRunner())
        request = self._build_request()
        trip_plan = TripPlan(
            city="Shanghai",
            start_date="2026-04-08",
            end_date="2026-04-08",
            overall_suggestions="test",
            weather_info=[],
            days=[
                DayPlan(
                    date="2026-04-08",
                    day_index=0,
                    description="test day",
                    transportation="Public Transit",
                    transportation_detail="",
                    transportation_cost=0,
                    accommodation="Comfort Hotel",
                    attractions=[
                        Attraction(
                            name="A",
                            address="addr-a",
                            location=Location(longitude=121.47, latitude=31.23),
                            visit_duration=120,
                            description="desc",
                            image_url="https://example.com/shared.jpg",
                        ),
                        Attraction(
                            name="B",
                            address="addr-b",
                            location=Location(longitude=121.48, latitude=31.24),
                            visit_duration=120,
                            description="desc",
                            image_url="https://example.com/shared.jpg",
                        ),
                    ],
                    meals=[
                        Meal(type="breakfast", name="x", description="x", estimated_cost=10),
                        Meal(type="lunch", name="y", description="y", estimated_cost=20),
                        Meal(type="dinner", name="z", description="z", estimated_cost=30),
                    ],
                )
            ],
        )
        payload = PlanningAgentInput(
            request=request,
            profile_context="",
            memory_context="",
            rag_context="",
            recommendation_reasons=[],
            attraction_result=AttractionAgentOutput(status=AgentExecutionStatus(success=True), search_queries=[], attractions=[]),
            weather_result=WeatherAgentOutput(status=AgentExecutionStatus(success=True), weather_info=[], summary="", suggestions=[]),
            hotel_result=HotelAgentOutput(status=AgentExecutionStatus(success=True), search_queries=[], hotels=[]),
            supervisor_warnings=[],
        )

        with patch("app.agents.planning_agent.get_amap_service", return_value=FakeAmapService()):
            enriched = planner._enrich_trip_plan(trip_plan, payload)

        day = enriched.days[0]
        self.assertEqual(day.attractions[0].image_url, "https://example.com/shared.jpg")
        self.assertTrue(str(day.attractions[1].image_url).startswith("map:2:"))


if __name__ == "__main__":
    unittest.main()
