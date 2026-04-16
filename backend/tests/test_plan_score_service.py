from app.models.schemas import (
    Attraction,
    DayPlan,
    Hotel,
    Location,
    Meal,
    TripPlan,
    TripScoreSummary,
    WeatherInfo,
)
from app.services.plan_score_service import get_plan_score_service


def build_sample_plan() -> TripPlan:
    museum = Attraction(
        name="城市博物馆",
        address="中山路 1 号",
        location=Location(longitude=121.4737, latitude=31.2304),
        visit_duration=120,
        description="适合雨天参观的城市历史博物馆",
        category="museum",
        ticket_price=60,
    )
    old_street = Attraction(
        name="老街区",
        address="人民路 88 号",
        location=Location(longitude=121.4812, latitude=31.2361),
        visit_duration=100,
        description="老字号和本地巷子很多，适合 citywalk",
        category="citywalk",
        ticket_price=0,
    )
    riverside = Attraction(
        name="江景步道",
        address="滨江大道 6 号",
        location=Location(longitude=121.4901, latitude=31.2412),
        visit_duration=90,
        description="适合傍晚散步看夜景",
        category="nature",
        ticket_price=0,
    )

    meals = [
        Meal(type="breakfast", name="本帮早餐铺", estimated_cost=28),
        Meal(type="lunch", name="弄堂面馆", estimated_cost=45),
        Meal(type="dinner", name="江景餐厅", estimated_cost=88),
    ]

    hotel = Hotel(
        name="城市轻居酒店",
        address="中山路 20 号",
        location=Location(longitude=121.4751, latitude=31.2322),
        price_range="medium",
        rating="4.6",
        distance="800m",
        type="comfortable",
        estimated_cost=380,
    )

    return TripPlan(
        city="Shanghai",
        start_date="2026-04-20",
        end_date="2026-04-21",
        overall_suggestions="路线顺着老城区和滨江走，适合轻松两日游。",
        weather_info=[
            WeatherInfo(
                date="2026-04-20",
                day_weather="小雨",
                night_weather="阴",
                day_temp=24,
                night_temp=18,
                wind_direction="东南",
                wind_power="3级",
            )
        ],
        days=[
            DayPlan(
                date="2026-04-20",
                day_index=0,
                description="博物馆加老街区的轻松城市漫游",
                transportation="public transit",
                transportation_cost=36,
                accommodation="hotel",
                hotel=hotel,
                attractions=[museum, old_street, riverside],
                meals=meals,
            )
        ],
    )


def test_plan_score_returns_story_and_factor_breakdown():
    service = get_plan_score_service()
    plan = build_sample_plan()
    summary = TripScoreSummary(
        budget_level="medium",
        travel_style=["slow", "citywalk", "local", "food"],
        companions=["family"],
        dietary_restrictions=[],
        mobility_needs=["rest_friendly"],
        transportation="public transit",
        free_text_input="想要轻松一些，最好能下雨也照样玩。",
    )

    result = service.evaluate_trip_plan(plan, summary)

    assert result.overall > 0
    assert result.summary
    assert result.story
    assert len(result.dimensions) == 6
    assert all(dimension.narrative for dimension in result.dimensions)
    assert all(dimension.factors for dimension in result.dimensions)
    assert any(factor.label == "基础盘" for factor in result.dimensions[0].factors)
    assert any(factor.reason for dimension in result.dimensions for factor in dimension.factors)


def test_plan_score_factor_impacts_include_positive_and_neutral_entries():
    service = get_plan_score_service()
    plan = build_sample_plan()
    result = service.evaluate_trip_plan(plan, TripScoreSummary(transportation="public transit"))

    all_impacts = [factor.impact for dimension in result.dimensions for factor in dimension.factors]

    assert any(impact > 0 for impact in all_impacts)
    assert any(impact == 0 for impact in all_impacts)
