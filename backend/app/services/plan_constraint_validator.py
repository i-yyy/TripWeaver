"""Post-plan validation and lightweight repair for hard skill constraints."""

from __future__ import annotations

from typing import List, Sequence, Tuple

from ..models.agent_schemas import WeatherAgentOutput
from ..models.schemas import Budget, DayPlan, Meal, TripPlan, TripRequest
from ..models.skill_schemas import SelectedSkill, ValidationIssue, ValidationResult


class PlanConstraintValidator:
    """Validate and lightly repair hard constraints after planning."""

    def validate_and_repair(
        self,
        request: TripRequest,
        skills: Sequence[SelectedSkill],
        trip_plan: TripPlan,
        weather_result: WeatherAgentOutput,
    ) -> Tuple[TripPlan, ValidationResult]:
        repaired_plan = trip_plan.model_copy(deep=True)
        result = ValidationResult()
        skill_keys = {skill.key for skill in skills}

        if "dietary_safe" in skill_keys:
            repaired_plan, issues = self._repair_dietary_safe(request, repaired_plan)
            result.warnings.extend(issues)

        if "budget_guard" in skill_keys:
            repaired_plan, warnings, errors = self._validate_budget_guard(request, repaired_plan)
            result.warnings.extend(warnings)
            result.errors.extend(errors)

        if "heat_avoidance" in skill_keys:
            repaired_plan, issues = self._repair_heat_avoidance(repaired_plan, weather_result)
            result.warnings.extend(issues)

        if "rainy_day" in skill_keys:
            repaired_plan, issues = self._repair_rainy_day(repaired_plan, weather_result)
            result.warnings.extend(issues)

        if "weekend_peak_avoidance" in skill_keys:
            repaired_plan, issues = self._repair_weekend_peak_avoidance(repaired_plan)
            result.warnings.extend(issues)

        if "low_mobility" in skill_keys:
            repaired_plan, issues = self._repair_low_mobility(repaired_plan)
            result.warnings.extend(issues)

        result.passed = not result.errors
        return repaired_plan, result

    def _repair_dietary_safe(self, request: TripRequest, trip_plan: TripPlan) -> Tuple[TripPlan, List[ValidationIssue]]:
        restrictions = [self._restriction_label(item) for item in request.dietary_restrictions]
        if not restrictions:
            return trip_plan, []

        issues: List[ValidationIssue] = []
        joined = "、".join(restrictions)
        updated_days: List[DayPlan] = []

        for day in trip_plan.days:
            meals: List[Meal] = []
            touched = False
            for meal in day.meals:
                description = (meal.description or "").strip()
                if joined and joined not in description:
                    description = (
                        f"{description} 本餐建议已按{joined}要求做兼容安排。".strip()
                        if description
                        else f"本餐建议已按{joined}要求做兼容安排。"
                    )
                    touched = True
                meals.append(meal.model_copy(update={"description": description}))

            if touched:
                issues.append(
                    ValidationIssue(
                        code="dietary_safe_repaired",
                        severity="warning",
                        message=f"第 {day.day_index + 1} 天餐饮说明已补充饮食限制兼容说明。",
                        day_index=day.day_index,
                        repair_hint="在餐饮文案中补充饮食限制说明。",
                    )
                )
            updated_days.append(day.model_copy(update={"meals": meals}))

        return trip_plan.model_copy(update={"days": updated_days}), issues

    def _validate_budget_guard(
        self,
        request: TripRequest,
        trip_plan: TripPlan,
    ) -> Tuple[TripPlan, List[ValidationIssue], List[ValidationIssue]]:
        budget = trip_plan.budget or self._rebuild_budget(trip_plan)
        per_day_cap = {"low": 1200, "medium": 2200, "high": 4000}.get((request.budget_level or "").lower())
        if per_day_cap is None:
            return trip_plan.model_copy(update={"budget": budget}), [], []

        cap = per_day_cap * max(1, request.travel_days)
        warnings: List[ValidationIssue] = []
        errors: List[ValidationIssue] = []
        if budget.total > cap:
            warnings.append(
                ValidationIssue(
                    code="budget_guard_over_budget",
                    severity="warning",
                    message=f"当前预算估算约为 {budget.total}，高于目标预算上限 {cap}。",
                    repair_hint="适当降低酒店、餐饮或交通成本。",
                )
            )
        if budget.total > int(cap * 1.4):
            errors.append(
                ValidationIssue(
                    code="budget_guard_excessive",
                    severity="error",
                    message=f"当前预算估算约为 {budget.total}，明显超出目标预算上限 {cap}。",
                    repair_hint="需要重新压缩成本较高的安排。",
                )
            )

        suggestions = trip_plan.overall_suggestions
        if warnings and "预算" not in suggestions:
            suggestions = f"{suggestions} 当前方案需关注预算控制。".strip()

        return trip_plan.model_copy(update={"budget": budget, "overall_suggestions": suggestions}), warnings, errors

    def _repair_heat_avoidance(
        self,
        trip_plan: TripPlan,
        weather_result: WeatherAgentOutput,
    ) -> Tuple[TripPlan, List[ValidationIssue]]:
        hottest = max([int(item.day_temp) for item in weather_result.weather_info], default=0)
        if hottest < 30:
            return trip_plan, []

        issues: List[ValidationIssue] = []
        updated_days: List[DayPlan] = []
        for day in trip_plan.days:
            detail = day.transportation_detail or ""
            if "中午" not in detail and "室内" not in detail and "休息" not in detail:
                detail = f"{detail} 中午建议安排室内或休息时段，避开高温暴晒。".strip()
            updated_days.append(day.model_copy(update={"transportation_detail": detail}))

        issues.append(
            ValidationIssue(
                code="heat_avoidance_repaired",
                severity="warning",
                message="已根据高温天气补充避晒与休息说明。",
                repair_hint="增加午间室内或休息安排。",
            )
        )

        return trip_plan.model_copy(update={"days": updated_days}), issues

    def _repair_rainy_day(
        self,
        trip_plan: TripPlan,
        weather_result: WeatherAgentOutput,
    ) -> Tuple[TripPlan, List[ValidationIssue]]:
        weather_text = " ".join(
            [weather_result.summary, *weather_result.suggestions, *[item.day_weather for item in weather_result.weather_info]]
        ).lower()
        if "雨" not in weather_text and "rain" not in weather_text:
            return trip_plan, []

        if "雨天" in trip_plan.overall_suggestions or "室内" in trip_plan.overall_suggestions:
            return trip_plan, []

        issue = ValidationIssue(
            code="rainy_day_repaired",
            severity="warning",
            message="已在整体建议中补充雨天执行提示。",
            repair_hint="增加雨天室内备选和避雨说明。",
        )
        return (
            trip_plan.model_copy(
                update={
                    "overall_suggestions": f"{trip_plan.overall_suggestions} 如遇下雨，优先采用室内备选并减少长距离户外移动。".strip()
                }
            ),
            [issue],
        )

    def _repair_weekend_peak_avoidance(self, trip_plan: TripPlan) -> Tuple[TripPlan, List[ValidationIssue]]:
        if any(token in trip_plan.overall_suggestions for token in ("错峰", "预约", "高峰")):
            return trip_plan, []
        issue = ValidationIssue(
            code="weekend_peak_avoidance_repaired",
            severity="warning",
            message="已补充周末避峰提示。",
            repair_hint="增加预约和错峰说明。",
        )
        return (
            trip_plan.model_copy(
                update={
                    "overall_suggestions": f"{trip_plan.overall_suggestions} 周末建议提前预约热门点，并尽量错峰出发。".strip()
                }
            ),
            [issue],
        )

    def _repair_low_mobility(self, trip_plan: TripPlan) -> Tuple[TripPlan, List[ValidationIssue]]:
        issues: List[ValidationIssue] = []
        updated_days: List[DayPlan] = []
        for day in trip_plan.days:
            detail = day.transportation_detail or ""
            attractions = day.attractions
            if len(attractions) > 2:
                attractions = attractions[:2]
                issues.append(
                    ValidationIssue(
                        code="low_mobility_trimmed",
                        severity="warning",
                        message=f"第 {day.day_index + 1} 天景点数量已收敛到 2 个以内。",
                        day_index=day.day_index,
                        repair_hint="控制单日景点数量。",
                    )
                )
            if "休息" not in detail and "少走" not in detail:
                detail = f"{detail} 当天建议保留休息点，尽量减少连续步行。".strip()
                issues.append(
                    ValidationIssue(
                        code="low_mobility_repaired",
                        severity="warning",
                        message=f"第 {day.day_index + 1} 天已补充低步行负担说明。",
                        day_index=day.day_index,
                        repair_hint="增加休息点和低强度交通说明。",
                    )
                )
            updated_days.append(day.model_copy(update={"attractions": attractions, "transportation_detail": detail}))

        return trip_plan.model_copy(update={"days": updated_days}), issues

    @staticmethod
    def _restriction_label(token: str) -> str:
        mapping = {
            "vegetarian": "素食",
            "halal": "清真",
            "no_spicy": "少辣或不辣",
        }
        return mapping.get(token, token)

    @staticmethod
    def _rebuild_budget(trip_plan: TripPlan) -> Budget:
        total_hotels = 0
        total_meals = 0
        total_transportation = 0
        total_attractions = 0
        for day in trip_plan.days:
            total_transportation += int(day.transportation_cost or 0)
            if day.hotel:
                total_hotels += int(day.hotel.estimated_cost or 0)
            total_attractions += sum(int(item.ticket_price or 0) for item in day.attractions)
            total_meals += sum(int(item.estimated_cost or 0) for item in day.meals)

        return Budget(
            total_attractions=total_attractions,
            total_hotels=total_hotels,
            total_meals=total_meals,
            total_transportation=total_transportation,
            total=total_attractions + total_hotels + total_meals + total_transportation,
        )


_plan_constraint_validator: PlanConstraintValidator | None = None


def get_plan_constraint_validator() -> PlanConstraintValidator:
    global _plan_constraint_validator
    if _plan_constraint_validator is None:
        _plan_constraint_validator = PlanConstraintValidator()
    return _plan_constraint_validator
