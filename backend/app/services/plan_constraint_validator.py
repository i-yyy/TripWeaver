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
        joined = " / ".join(restrictions)
        updated_days: List[DayPlan] = []

        for day in trip_plan.days:
            meals: List[Meal] = []
            touched = False
            for meal in day.meals:
                description = (meal.description or "").strip()
                if joined and joined not in description:
                    description = (
                        f"{description} \u672c\u9910\u5efa\u8bae\u5df2\u6309{joined}\u8981\u6c42\u505a\u517c\u5bb9\u5b89\u6392\u3002".strip()
                        if description
                        else f"\u672c\u9910\u5efa\u8bae\u5df2\u6309{joined}\u8981\u6c42\u505a\u517c\u5bb9\u5b89\u6392\u3002"
                    )
                    touched = True
                meals.append(meal.model_copy(update={"description": description}))

            if touched:
                issues.append(
                    ValidationIssue(
                        code="dietary_safe_repaired",
                        severity="warning",
                        message=f"\u7b2c {day.day_index + 1} \u5929\u9910\u996e\u8bf4\u660e\u5df2\u8865\u5145\u996e\u98df\u9650\u5236\u517c\u5bb9\u8bf4\u660e\u3002",
                        day_index=day.day_index,
                        repair_hint="\u5728\u9910\u996e\u6587\u6848\u4e2d\u8865\u5145\u996e\u98df\u9650\u5236\u8bf4\u660e\u3002",
                    )
                )
            updated_days.append(day.model_copy(update={"meals": meals}))

        if not issues:
            issues.append(
                ValidationIssue(
                    code="dietary_safe_checked",
                    severity="warning",
                    message="\u5df2\u6821\u9a8c\u9910\u996e\u4e0e\u996e\u98df\u9650\u5236\u7684\u4e00\u81f4\u6027\u3002",
                    repair_hint="\u9910\u996e\u8bf4\u660e\u9700\u6301\u7eed\u4fdd\u6301\u996e\u98df\u9650\u5236\u517c\u5bb9\u3002",
                )
            )

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
                    message=f"\u5f53\u524d\u9884\u7b97\u4f30\u7b97\u7ea6\u4e3a {budget.total}\uff0c\u9ad8\u4e8e\u76ee\u6807\u9884\u7b97\u4e0a\u9650 {cap}\u3002",
                    repair_hint="\u9002\u5f53\u964d\u4f4e\u9152\u5e97\u3001\u9910\u996e\u6216\u4ea4\u901a\u6210\u672c\u3002",
                )
            )
        if budget.total > int(cap * 1.4):
            errors.append(
                ValidationIssue(
                    code="budget_guard_excessive",
                    severity="error",
                    message=f"\u5f53\u524d\u9884\u7b97\u4f30\u7b97\u7ea6\u4e3a {budget.total}\uff0c\u660e\u663e\u8d85\u51fa\u76ee\u6807\u9884\u7b97\u4e0a\u9650 {cap}\u3002",
                    repair_hint="\u9700\u8981\u91cd\u65b0\u538b\u7f29\u6210\u672c\u8f83\u9ad8\u7684\u5b89\u6392\u3002",
                )
            )

        suggestions = trip_plan.overall_suggestions
        if warnings and "\u9884\u7b97" not in suggestions:
            suggestions = f"{suggestions} \u5f53\u524d\u65b9\u6848\u9700\u5173\u6ce8\u9884\u7b97\u63a7\u5236\u3002".strip()

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
            if all(token not in detail for token in ("\u4e2d\u5348", "\u5ba4\u5185", "\u4f11\u606f")):
                detail = f"{detail} \u4e2d\u5348\u5efa\u8bae\u5b89\u6392\u5ba4\u5185\u6216\u4f11\u606f\u65f6\u6bb5\uff0c\u907f\u5f00\u9ad8\u6e29\u66b4\u6652\u3002".strip()
            updated_days.append(day.model_copy(update={"transportation_detail": detail}))

        issues.append(
            ValidationIssue(
                code="heat_avoidance_repaired",
                severity="warning",
                message="\u5df2\u6839\u636e\u9ad8\u6e29\u5929\u6c14\u8865\u5145\u907f\u6652\u4e0e\u4f11\u606f\u8bf4\u660e\u3002",
                repair_hint="\u589e\u52a0\u5348\u95f4\u5ba4\u5185\u6216\u4f11\u606f\u5b89\u6392\u3002",
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
        if "\u96e8" not in weather_text and "rain" not in weather_text:
            return trip_plan, []

        if "\u96e8\u5929" in trip_plan.overall_suggestions or "\u5ba4\u5185" in trip_plan.overall_suggestions:
            return trip_plan, []

        issue = ValidationIssue(
            code="rainy_day_repaired",
            severity="warning",
            message="\u5df2\u5728\u6574\u4f53\u5efa\u8bae\u4e2d\u8865\u5145\u96e8\u5929\u6267\u884c\u63d0\u793a\u3002",
            repair_hint="\u589e\u52a0\u96e8\u5929\u5ba4\u5185\u5907\u9009\u548c\u907f\u96e8\u8bf4\u660e\u3002",
        )
        return (
            trip_plan.model_copy(
                update={
                    "overall_suggestions": f"{trip_plan.overall_suggestions} \u5982\u9047\u4e0b\u96e8\uff0c\u4f18\u5148\u91c7\u7528\u5ba4\u5185\u5907\u9009\u5e76\u51cf\u5c11\u957f\u8ddd\u79bb\u6237\u5916\u79fb\u52a8\u3002".strip()
                }
            ),
            [issue],
        )

    def _repair_weekend_peak_avoidance(self, trip_plan: TripPlan) -> Tuple[TripPlan, List[ValidationIssue]]:
        if "\u9519\u5cf0" in trip_plan.overall_suggestions or "\u9884\u7ea6" in trip_plan.overall_suggestions:
            return trip_plan, []
        issue = ValidationIssue(
            code="weekend_peak_avoidance_repaired",
            severity="warning",
            message="\u5df2\u8865\u5145\u5468\u672b\u9519\u5cf0\u4e0e\u9884\u7ea6\u63d0\u793a\u3002",
            repair_hint="\u5728\u70ed\u95e8\u666f\u70b9\u524d\u52a0\u5165\u9884\u7ea6\u6216\u9519\u5cf0\u63d0\u793a\u3002",
        )
        return (
            trip_plan.model_copy(
                update={
                    "overall_suggestions": f"{trip_plan.overall_suggestions} \u5468\u672b\u5efa\u8bae\u5c3d\u91cf\u9519\u5cf0\u51fa\u53d1\uff0c\u5fc5\u8981\u65f6\u63d0\u524d\u9884\u7ea6\u70ed\u95e8\u70b9\u4f4d\u3002".strip()
                }
            ),
            [issue],
        )

    def _repair_low_mobility(self, trip_plan: TripPlan) -> Tuple[TripPlan, List[ValidationIssue]]:
        issues: List[ValidationIssue] = []
        updated_days: List[DayPlan] = []
        for day in trip_plan.days:
            attractions = list(day.attractions)
            detail = day.transportation_detail or ""
            changed = False
            if len(attractions) > 2:
                attractions = attractions[:2]
                changed = True
            if all(token not in detail for token in ("\u4f11\u606f", "\u5c11\u8d70\u8def", "\u65e0\u969c\u788d")):
                detail = f"{detail} \u5f53\u5929\u5efa\u8bae\u63a7\u5236\u6b65\u884c\u5f3a\u5ea6\uff0c\u9002\u5f53\u9884\u7559\u4f11\u606f\u70b9\u3002".strip()
                changed = True
            updated_days.append(day.model_copy(update={"attractions": attractions, "transportation_detail": detail}))
            if changed:
                issues.append(
                    ValidationIssue(
                        code="low_mobility_repaired",
                        severity="warning",
                        message=f"\u7b2c {day.day_index + 1} \u5929\u5df2\u6309\u4f4e\u6b65\u884c\u8d1f\u62c5\u8981\u6c42\u6536\u7f29\u884c\u7a0b\u3002",
                        day_index=day.day_index,
                        repair_hint="\u51cf\u5c11\u5355\u65e5\u666f\u70b9\u4e2a\u6570\u5e76\u8865\u5145\u4f11\u606f\u63d0\u793a\u3002",
                    )
                )

        return trip_plan.model_copy(update={"days": updated_days}), issues

    @staticmethod
    def _restriction_label(token: str) -> str:
        mapping = {
            "vegetarian": "\u7d20\u98df",
            "halal": "\u6e05\u771f",
            "no_spicy": "\u5c11\u8fa3\u6216\u4e0d\u8fa3",
        }
        return mapping.get(token, token)

    @staticmethod
    def _rebuild_budget(trip_plan: TripPlan) -> Budget:
        total_attractions = 0
        total_hotels = 0
        total_meals = 0
        total_transportation = 0
        for day in trip_plan.days:
            total_attractions += sum(int(item.ticket_price or 0) for item in day.attractions)
            total_hotels += int(day.hotel.estimated_cost or 0) if day.hotel else 0
            total_meals += sum(int(item.estimated_cost or 0) for item in day.meals)
            total_transportation += int(day.transportation_cost or 0)
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
