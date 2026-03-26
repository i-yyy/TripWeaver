"""旅行规划路由。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ...agents.trip_planner_agent import get_trip_planner_agent
from ...models.schemas import TripPlanResponse, TripRequest
from ...services.memory_service import get_memory_service
from ...services.profile_service import get_profile_service
from ...services.retriever_service import get_retriever_service

router = APIRouter(prefix="/trip", tags=["旅行规划"])


@router.post(
    "/plan",
    response_model=TripPlanResponse,
    summary="生成旅行规划",
    description="根据用户输入生成多日行程。",
)
async def plan_trip(request: TripRequest) -> TripPlanResponse:
    try:
        profile_service = get_profile_service()
        memory_service = get_memory_service()
        retriever_service = get_retriever_service()
        planner = get_trip_planner_agent()

        profile_service.update_profile_from_request(request)
        memory_service.save_session_facts(request)

        profile_context = profile_service.build_profile_context(request.user_id)
        memories = memory_service.get_relevant_memories(
            user_id=request.user_id,
            session_id=request.session_id,
            city=request.city,
        )
        memory_context = memory_service.build_memory_context(
            user_id=request.user_id,
            session_id=request.session_id,
            city=request.city,
        )

        rag_bundle = retriever_service.retrieve_trip_bundle(
            request=request,
            profile_context=profile_context,
            memories=memories,
        )
        rag_context = str(rag_bundle.get("context_text", ""))
        recommendation_reasons = list(rag_bundle.get("recommendation_reasons", []))

        trip_plan = planner.plan_trip(
            request=request,
            profile_context=profile_context,
            memory_context=memory_context,
            rag_context=rag_context,
        )
        trip_plan.recommendation_reasons = recommendation_reasons

        memory_service.save_trip_summary(request, trip_plan)

        return TripPlanResponse(success=True, message="旅行规划生成成功", data=trip_plan)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"生成旅行规划失败: {exc}") from exc


@router.get(
    "/health",
    summary="行程路由健康检查",
    description="检查行程规划能力是否可用。",
)
async def health_check() -> dict:
    try:
        planner = get_trip_planner_agent()
        return {
            "status": "健康",
            "service": "trip-planner",
            "attraction_tools": len(planner.attraction_agent.list_tools()),
            "weather_tools": len(planner.weather_agent.list_tools()),
            "hotel_tools": len(planner.hotel_agent.list_tools()),
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"服务不可用: {exc}") from exc
