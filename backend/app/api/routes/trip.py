"""Trip planning API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ...agents.trip_planner_agent import get_trip_planner_agent
from ...models.schemas import RecommendationReason, TripPlanResponse, TripRequest
from ...services.memory_service import get_memory_service
from ...services.profile_service import get_profile_service
from ...services.retriever_service import get_retriever_service

router = APIRouter(prefix="/trip", tags=["trip"])


def _tool_count(agent: object) -> int:
    list_tools_fn = getattr(agent, "list_tools", None)
    if callable(list_tools_fn):
        try:
            return len(list_tools_fn())
        except Exception:
            pass

    tools = getattr(agent, "tools", None)
    if isinstance(tools, list):
        return len(tools)
    return 0


@router.post("/plan", response_model=TripPlanResponse, summary="生成旅行规划")
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
        trip_plan.recommendation_reasons = [
            reason
            if isinstance(reason, RecommendationReason)
            else RecommendationReason.model_validate(reason)
            for reason in recommendation_reasons
        ]

        memory_service.save_trip_summary(request, trip_plan)
        return TripPlanResponse(success=True, message="旅行规划生成成功", data=trip_plan)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"生成旅行规划失败: {exc}") from exc


@router.get("/health", summary="行程服务健康检查")
async def health_check() -> dict:
    try:
        planner = get_trip_planner_agent()
        return {
            "status": "healthy",
            "service": "trip-planner",
            "attraction_tools": _tool_count(planner.attraction_agent),
            "weather_tools": _tool_count(planner.weather_agent),
            "hotel_tools": _tool_count(planner.hotel_agent),
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"服务不可用: {exc}") from exc
