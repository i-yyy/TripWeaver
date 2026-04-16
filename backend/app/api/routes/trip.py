"""Trip planning API routes."""

from __future__ import annotations

import logging
from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException

from ...agents.trip_planner_agent import get_trip_planner_agent
from ...db.models import User
from ...models.schemas import RecommendationReason, TripPlanResponse, TripRequest, TripScoreRequest, TripScoreResponse
from ...services.memory_service import get_memory_service
from ...services.plan_score_service import get_plan_score_service
from ...services.profile_service import get_profile_service
from ...services.retriever_service import get_retriever_service
from ...services.security_service import get_current_user
from ...services.skill_service import get_skill_service

logger = logging.getLogger(__name__)

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


@router.post("/plan", response_model=TripPlanResponse, summary="Generate a trip plan")
async def plan_trip(
    request: TripRequest,
    current_user: User = Depends(get_current_user),
) -> TripPlanResponse:
    try:
        started_at = perf_counter()
        request.user_id = current_user.id
        profile_service = get_profile_service()
        memory_service = get_memory_service()
        retriever_service = get_retriever_service()
        skill_service = get_skill_service()
        planner = get_trip_planner_agent()

        profile_started_at = perf_counter()
        profile_service.update_profile_from_request(request)
        memory_service.save_session_facts(request)
        logger.info(
            "[timing] Trip API profile/session prepared city=%s elapsed=%.2fs",
            request.city,
            perf_counter() - profile_started_at,
        )

        memory_started_at = perf_counter()
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
        logger.info(
            "[timing] Trip API memory context prepared city=%s elapsed=%.2fs memories=%s",
            request.city,
            perf_counter() - memory_started_at,
            len(memories),
        )

        rag_started_at = perf_counter()
        rag_bundle = retriever_service.retrieve_trip_bundle(
            request=request,
            profile_context=profile_context,
            memories=memories,
        )
        rag_context = str(rag_bundle.get("context_text", ""))
        recommendation_reasons = [
            reason
            if isinstance(reason, RecommendationReason)
            else RecommendationReason.model_validate(reason)
            for reason in rag_bundle.get("recommendation_reasons", [])
        ]
        logger.info(
            "[timing] Trip API rag prepared city=%s elapsed=%.2fs recall=%s rerank=%s reasons=%s",
            request.city,
            perf_counter() - rag_started_at,
            rag_bundle.get("recall_count", 0),
            rag_bundle.get("rerank_count", 0),
            len(recommendation_reasons),
        )

        skill_started_at = perf_counter()
        static_skills = skill_service.select_static_skills(
            request=request,
            profile_context=profile_context,
            memory_context=memory_context,
            rag_context=rag_context,
        )
        logger.info(
            "[timing] Trip API skills prepared city=%s elapsed=%.2fs skills=%s",
            request.city,
            perf_counter() - skill_started_at,
            len(static_skills),
        )

        planner_started_at = perf_counter()
        trip_plan = await planner.plan_trip(
            request=request,
            profile_context=profile_context,
            memory_context=memory_context,
            rag_context=rag_context,
            recommendation_reasons=recommendation_reasons,
            skills=static_skills,
        )
        trip_plan.recommendation_reasons = recommendation_reasons
        trip_plan.decision_score = get_plan_score_service().evaluate_trip_plan(trip_plan, request)
        logger.info(
            "[timing] Trip API planner completed city=%s elapsed=%.2fs days=%s",
            request.city,
            perf_counter() - planner_started_at,
            len(trip_plan.days),
        )

        save_started_at = perf_counter()
        memory_service.save_trip_summary(request, trip_plan)
        logger.info(
            "[timing] Trip API summary saved city=%s elapsed=%.2fs total_elapsed=%.2fs",
            request.city,
            perf_counter() - save_started_at,
            perf_counter() - started_at,
        )
        return TripPlanResponse(success=True, message="Trip plan generated successfully", data=trip_plan)
    except Exception as exc:
        logger.exception("Failed to generate trip plan")
        raise HTTPException(status_code=500, detail=f"Failed to generate trip plan: {exc}") from exc


@router.get("/health", summary="Trip planner health check")
async def health_check() -> dict:
    try:
        planner = get_trip_planner_agent()
        return {
            "status": "healthy",
            "service": "trip-planner",
            "attraction_tools": _tool_count(planner.attraction_agent),
            "weather_tools": _tool_count(planner.weather_agent),
            "hotel_tools": _tool_count(planner.hotel_agent),
            "meal_tools": _tool_count(planner.meal_agent),
            "planning_tools": _tool_count(planner.planning_agent),
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {exc}") from exc


@router.post("/score", response_model=TripScoreResponse, summary="Evaluate trip decision score")
async def score_trip_plan(
    request: TripScoreRequest,
    current_user: User = Depends(get_current_user),
) -> TripScoreResponse:
    del current_user
    try:
        scoring_service = get_plan_score_service()
        score = scoring_service.evaluate_trip_plan(request.plan, request.summary)
        return TripScoreResponse(success=True, message="Trip score evaluated successfully", data=score)
    except Exception as exc:
        logger.exception("Failed to evaluate trip score")
        raise HTTPException(status_code=500, detail=f"Failed to evaluate trip score: {exc}") from exc
