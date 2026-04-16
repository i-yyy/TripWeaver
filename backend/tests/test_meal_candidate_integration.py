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
from app.models.schemas import Attraction, Hotel, Location, Meal, MealCandidate, TripRequest
from app.services.meal_candidate_service import MealCandidateService


class RaisingPlannerRunner:
    def run(self, prompt):
        raise RuntimeError('LLM unavailable')


class FakeAmapService:
    def __init__(self) -> None:
        self.queries: list[tuple[str, str]] = []

    def search_poi(self, keywords: str, city: str, citylimit: bool = True):
        self.queries.append((keywords, city))
        if '清真' in keywords:
            return [
                type(
                    'POI',
                    (),
                    {
                        'id': 'poi-halal',
                        'name': '清真牛肉面',
                        'type': '清真餐厅',
                        'address': '西城胡同',
                        'location': Location(longitude=116.40, latitude=39.90),
                    },
                )()
            ]
        return [
            type(
                'POI',
                (),
                {
                    'id': 'poi-breakfast',
                    'name': '胡同早餐铺',
                    'type': '早餐店',
                    'address': '西城胡同',
                    'location': Location(longitude=116.40, latitude=39.90),
                },
            )()
        ]


class FakeMealCandidateService:
    def __init__(self, candidates_by_day=None):
        self.candidates_by_day = candidates_by_day or {}

    def retrieve_day_candidates(self, request, day_index, attractions, hotel=None, skills=(), per_type_limit=5):
        return self.candidates_by_day.get(day_index, {})


class MealCandidateIntegrationTest(unittest.TestCase):
    def _build_request(self, dietary_restrictions=None) -> TripRequest:
        return TripRequest(
            user_id='user-content',
            session_id='session-content',
            city='Shanghai',
            start_date='2026-04-08',
            end_date='2026-04-08',
            travel_days=1,
            transportation='Public Transit',
            accommodation='Comfort Hotel',
            preferences=['food'],
            free_text_input='',
            budget_level='medium',
            travel_style=['food'],
            companions=[],
            dietary_restrictions=dietary_restrictions or [],
            mobility_needs=[],
        )

    def test_meal_candidate_service_includes_dietary_queries(self) -> None:
        service = MealCandidateService(amap_service=FakeAmapService())
        request = self._build_request(['halal'])
        attractions = [
            Attraction(
                name='什刹海',
                address='西城区',
                location=Location(longitude=116.39, latitude=39.94),
                visit_duration=120,
                description='test',
            )
        ]
        hotel = Hotel(name='鼓楼酒店', address='旧鼓楼大街', location=Location(longitude=116.40, latitude=39.93))

        result = service.retrieve_day_candidates(
            request=request,
            day_index=0,
            attractions=attractions,
            hotel=hotel,
            skills=[],
        )

        self.assertTrue(any('清真' in query for query, _ in service.amap_service.queries))
        self.assertIn('breakfast', result)
        self.assertEqual(result['breakfast'][0].name, '清真牛肉面')

    def test_generic_meals_use_candidates_before_default_templates(self) -> None:
        request = self._build_request()
        candidates_by_day = {
            0: {
                'breakfast': [
                    MealCandidate(
                        meal_type='breakfast',
                        name='弄堂生煎铺',
                        poi_id='m1',
                        address='上海黄浦区',
                        location=Location(longitude=121.47, latitude=31.23),
                        category='小吃快餐',
                        estimated_cost=22,
                        source_query='外滩 附近 早餐',
                    )
                ],
                'lunch': [
                    MealCandidate(
                        meal_type='lunch',
                        name='本帮面馆',
                        poi_id='m2',
                        address='上海黄浦区',
                        location=Location(longitude=121.48, latitude=31.24),
                        category='面馆',
                        estimated_cost=48,
                        source_query='外滩 附近 午餐',
                    )
                ],
                'dinner': [
                    MealCandidate(
                        meal_type='dinner',
                        name='老字号本帮菜',
                        poi_id='m3',
                        address='上海黄浦区',
                        location=Location(longitude=121.49, latitude=31.25),
                        category='本帮菜',
                        estimated_cost=88,
                        source_query='外滩 附近 晚餐',
                    )
                ],
            }
        }
        planner = PlanningAgent(
            planner_runner=RaisingPlannerRunner(),
            meal_candidate_service=FakeMealCandidateService(candidates_by_day),
        )
        payload = PlanningAgentInput(
            request=request,
            profile_context='',
            memory_context='',
            rag_context='',
            recommendation_reasons=[],
            attraction_result=AttractionAgentOutput(status=AgentExecutionStatus(success=True), search_queries=[], attractions=[]),
            weather_result=WeatherAgentOutput(status=AgentExecutionStatus(success=True), weather_info=[], summary='', suggestions=[]),
            hotel_result=HotelAgentOutput(status=AgentExecutionStatus(success=True), search_queries=[], hotels=[]),
            supervisor_warnings=[],
        )

        plan = planner.build_fallback_plan(payload, planner._retrieve_meal_candidates(payload))

        self.assertEqual(plan.days[0].meals[0].name, '弄堂生煎铺')
        self.assertEqual(plan.days[0].meals[1].name, '本帮面馆')
        self.assertEqual(plan.days[0].meals[2].name, '老字号本帮菜')

        generic_meals = [
            Meal(type='breakfast', name='早餐', description='', estimated_cost=0),
            Meal(type='lunch', name='午餐', description='', estimated_cost=0),
            Meal(type='dinner', name='晚餐', description='', estimated_cost=0),
        ]
        enriched = planner._enrich_meals(generic_meals, request, candidates_by_day[0])
        self.assertEqual(enriched[0].name, '弄堂生煎铺')
        self.assertIn('上海黄浦区', enriched[0].description or '')
        self.assertIn('可考虑点', enriched[0].description or '')
        self.assertNotIn('方向的候选店', enriched[0].description or '')

    def test_daily_meals_do_not_repeat_same_store(self) -> None:
        request = self._build_request()
        repeated = MealCandidate(
            meal_type='lunch',
            name='同名餐馆',
            poi_id='same-poi',
            address='上海静安区',
            location=Location(longitude=121.47, latitude=31.23),
            category='餐饮服务;中餐厅;中餐厅',
            estimated_cost=40,
            source_query='静安寺 附近 简餐',
        )
        candidates_by_day = {
            0: {
                'breakfast': [repeated],
                'lunch': [repeated],
                'dinner': [repeated],
            }
        }
        planner = PlanningAgent(
            planner_runner=RaisingPlannerRunner(),
            meal_candidate_service=FakeMealCandidateService(candidates_by_day),
        )
        meals = [
            Meal(type='breakfast', name='早餐', description='', estimated_cost=0),
            Meal(type='lunch', name='午餐', description='', estimated_cost=0),
            Meal(type='dinner', name='晚餐', description='', estimated_cost=0),
        ]

        enriched = planner._enrich_meals(meals, request, candidates_by_day[0])
        names = [item.name for item in enriched]
        self.assertEqual(len(set(names)), 3)


if __name__ == '__main__':
    unittest.main()
