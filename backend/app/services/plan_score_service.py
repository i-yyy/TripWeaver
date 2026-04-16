"""Decision score service for trip plans."""

from __future__ import annotations

from typing import Callable, Optional, Sequence

from ..models.schemas import (
    Attraction,
    Budget,
    DayPlan,
    DecisionScoreDimension,
    DecisionScoreFactor,
    DecisionScoreSnapshot,
    Location,
    TripPlan,
    TripRequest,
    TripScoreSummary,
)


ScoreSummaryInput = Optional[TripScoreSummary | TripRequest]


class PlanScoreService:
    """Evaluate multi-dimensional decision scores for a trip plan."""

    SCORE_WEIGHTS = {
        "preference_fit": 0.25,
        "budget_fit": 0.20,
        "route_efficiency": 0.15,
        "comfort": 0.15,
        "resilience": 0.10,
        "richness": 0.15,
    }
    BUDGET_TARGET_PER_DAY = {
        "low": 420,
        "medium": 880,
        "high": 1800,
    }
    INDOOR_KEYWORDS = ("博物馆", "美术馆", "科技馆", "展览馆", "艺术馆", "图书馆", "室内", "商场", "购物中心")
    LOCAL_KEYWORDS = ("本地", "老字号", "胡同", "里弄", "街区", "古镇", "市集", "巷子")
    ICONIC_KEYWORDS = ("地标", "塔", "故宫", "外滩", "西湖", "长城", "江景", "夜景", "广场")
    MOBILITY_KEYS = {"less_walking", "wheelchair", "rest_friendly"}

    def evaluate_trip_plan(self, plan: TripPlan, summary: ScoreSummaryInput = None) -> DecisionScoreSnapshot:
        resolved_summary = self._normalize_summary(summary)
        budget = self.build_plan_budget(plan)
        attractions = [attraction for day in plan.days for attraction in day.attractions]
        meals = [meal for day in plan.days for meal in day.meals]
        days = max(1, len(plan.days))
        avg_attractions_per_day = len(attractions) / days
        avg_visit_minutes_per_day = sum(
            sum(int(attraction.visit_duration or 0) for attraction in day.attractions) for day in plan.days
        ) / days
        estimated_distance_km = sum(self._estimate_day_distance_km(day, plan.city) for day in plan.days)
        avg_distance_km = estimated_distance_km / days
        indoor_ratio = self._ratio(self._filter_count(attractions, self._is_indoor_attraction), len(attractions))
        local_ratio = self._ratio(self._filter_count(attractions, self._is_local_attraction), len(attractions))
        iconic_count = self._filter_count(attractions, self._is_iconic_attraction)
        unique_categories = {
            self._normalize_attraction_category(item) for item in attractions if self._normalize_attraction_category(item)
        }
        unique_meals = {str(item.name).strip() for item in meals if str(item.name).strip()}
        weather_severity = self._get_weather_severity(plan)
        mobility_needs = resolved_summary.mobility_needs
        travel_styles = resolved_summary.travel_style
        companions = resolved_summary.companions
        budget_level = str(resolved_summary.budget_level or "").lower()
        transportation_preference = str(resolved_summary.transportation or "").lower()
        missing_meals_days = sum(1 for day in plan.days if len(day.meals) < 3)
        missing_hotel_days = sum(1 for day in plan.days if not day.hotel)
        has_rain_skill = any(skill.key == "rainy_day" for skill in plan.applied_skills)
        has_heat_skill = any(skill.key == "heat_avoidance" for skill in plan.applied_skills)

        preference_score = 58.0
        preference_factors = [
            self._factor("基础盘", 58.0, "先给这份方案一个可出发的底分，再根据节奏、同行人与偏好往上加减。"),
        ]
        if "slow" in travel_styles:
            if avg_attractions_per_day <= 3 and avg_visit_minutes_per_day <= 420:
                preference_score += 10
                preference_factors.append(
                    self._factor(
                        "慢游节奏命中",
                        10.0,
                        "你想要轻松节奏，而当前日均景点和停留时长都控制在松弛区间。",
                        f"{avg_attractions_per_day:.1f} 个景点/天 · {round(avg_visit_minutes_per_day)} 分钟/天",
                    )
                )
            else:
                preference_factors.append(
                    self._factor(
                        "慢游节奏未吃满加分",
                        0.0,
                        "你选了轻松节奏，但当前安排还有一点满，暂时没有拿到这项加分。",
                        f"{avg_attractions_per_day:.1f} 个景点/天 · {round(avg_visit_minutes_per_day)} 分钟/天",
                    )
                )
        if "citywalk" in travel_styles:
            if 2 <= avg_distance_km <= 12:
                preference_score += 8
                preference_factors.append(
                    self._factor("城市漫游匹配", 8.0, "步行或公共交通的日均距离落在舒服区间，像一条能顺着走完的城市线。", f"{avg_distance_km:.1f} km/天")
                )
            else:
                preference_factors.append(
                    self._factor("城市漫游未触发", 0.0, "你想要 citywalk 氛围，但当前日均距离还没落到最顺手的区间。", f"{avg_distance_km:.1f} km/天")
                )
        if "checkin" in travel_styles:
            if iconic_count > 0:
                preference_score += 8
                preference_factors.append(
                    self._factor("标志性景点加分", 8.0, "方案里已经塞进城市记忆点，不会玩完却想不起这个城市的脸。", f"{iconic_count} 个地标点")
                )
            else:
                preference_factors.append(
                    self._factor("打卡感偏弱", 0.0, "你选了经典打卡路线，但当前还缺少明显的城市名片级景点。")
                )
        if "local" in travel_styles:
            if local_ratio >= 0.3:
                preference_score += 8
                preference_factors.append(
                    self._factor("本地感在线", 8.0, "本地街区、老味道和生活感内容占比不低，路线更像深入城市肌理。", f"{round(local_ratio * 100)}% 本地感点位")
                )
            else:
                preference_factors.append(
                    self._factor("本地感还可再加", 0.0, "当前路线还偏主流景点，本地生活气还可以再添一点。", f"{round(local_ratio * 100)}% 本地感点位")
                )
        if "food" in travel_styles:
            if len(meals) >= days * 3:
                preference_score += 6
                preference_factors.append(
                    self._factor("吃饭安排完整", 6.0, "餐食位排得比较齐，旅途不会总在临场找饭。", f"{len(meals)} 餐 / {days} 天")
                )
            else:
                preference_factors.append(
                    self._factor("餐食密度不足", 0.0, "你对美食有要求，但当前有些天的餐食安排还不够满。", f"{len(meals)} 餐 / {days} 天")
                )
        if "family" in companions:
            if avg_attractions_per_day <= 3:
                preference_score += 6
                preference_factors.append(
                    self._factor("亲子节奏友好", 6.0, "家庭出行更怕赶场，这份安排把每天控制在较稳的节奏里。")
                )
            else:
                preference_factors.append(
                    self._factor("亲子节奏偏满", 0.0, "同行里有家庭成员，但每天景点数略多，少了这项友好加分。")
                )
        if any(item in self.MOBILITY_KEYS for item in mobility_needs):
            mobility_impact = 12.0 if avg_distance_km <= 8 and avg_visit_minutes_per_day <= 360 else -8.0
            preference_score += mobility_impact
            preference_factors.append(
                self._factor(
                    "行动负担校准",
                    mobility_impact,
                    "系统会把少步行、轮椅或需要多休息的需求单独放大考虑。",
                    f"{avg_distance_km:.1f} km/天 · {round(avg_visit_minutes_per_day)} 分钟/天",
                )
            )
        if transportation_preference:
            if all(str(day.transportation or "").lower() == transportation_preference for day in plan.days):
                preference_score += 8
                preference_factors.append(
                    self._factor("交通偏好一致", 8.0, "每天的主交通方式和你的设定保持一致，执行起来更顺。", transportation_preference)
                )
            else:
                preference_factors.append(
                    self._factor("交通偏好未完全对齐", 0.0, "你有明确交通偏好，但当前并不是每一天都完全照着来。", transportation_preference)
                )
        if missing_meals_days > 0:
            preference_penalty = missing_meals_days * 4.0
            preference_score -= preference_penalty
            preference_factors.append(
                self._factor("餐食空档", -preference_penalty, "有些天少于三餐，行程完整度会被拉低。", f"{missing_meals_days} 天")
            )
        preference_dimension = self._clamp_score(preference_score)

        budget_target = self.BUDGET_TARGET_PER_DAY.get(budget_level, 0) * days
        if budget_target > 0:
            budget_score = 100.0
            budget_factors = [
                self._factor("预算目标线", 100.0, "以当前预算档位为目标，默认满分起步，再按偏离程度扣分。", self._currency(budget_target)),
            ]
            ratio = budget.total / budget_target if budget_target else 0.0
            if ratio < 0.72:
                under_penalty = (0.72 - ratio) * 28
                budget_score -= under_penalty
                budget_factors.append(
                    self._factor("预算压得太紧", -under_penalty, "花费明显低于目标区间，可能意味着体验密度被压缩。", f"{ratio:.2f} x 目标预算")
                )
            elif ratio <= 1:
                budget_factors.append(
                    self._factor("预算落点漂亮", 0.0, "花费落在预算舒适区，花得不冒头，也不显得太抠。", f"{ratio:.2f} x 目标预算")
                )
            else:
                over_penalty = min(75.0, (ratio - 1) * 115)
                budget_score -= over_penalty
                budget_factors.append(
                    self._factor("超预算扣分", -over_penalty, "总花费已经开始往预算线外探头，越超越扣。", f"{ratio:.2f} x 目标预算")
                )
        else:
            budget_score = 82.0
            budget_factors = [
                self._factor("默认预算分", 82.0, "你还没设预算档位，系统先按可接受但不满分的状态估算。"),
                self._factor("缺少预算锚点", 0.0, "后续如果补上低、中、高预算，系统能把这项算得更准。"),
            ]
        budget_dimension = self._clamp_score(budget_score)

        route_type = self._normalize_route_type(
            resolved_summary.transportation or (plan.days[0].transportation if plan.days else "walking")
        )
        ideal_distance = 6 if route_type == "walking" else 14 if route_type == "transit" else 90
        max_distance = 16 if route_type == "walking" else 36 if route_type == "transit" else 220
        route_score = 100.0
        route_factors = [
            self._factor("顺路底盘", 100.0, "先按最顺路的理想状态起算，再根据距离和密度扣分。", route_type),
        ]
        if avg_distance_km > ideal_distance:
            route_penalty = ((min(avg_distance_km, max_distance) - ideal_distance) / max(1, max_distance - ideal_distance)) * 36
            route_score -= route_penalty
            route_factors.append(
                self._factor("绕路成本", -route_penalty, "日均路程超过理想区间后，顺路感会开始下滑。", f"{avg_distance_km:.1f} km/天")
            )
        else:
            route_factors.append(
                self._factor("距离控制得住", 0.0, "日均距离还在理想区间内，路线像把珠子顺着线穿起来。", f"{avg_distance_km:.1f} km/天")
            )
        if avg_attractions_per_day > 3:
            density_penalty = (avg_attractions_per_day - 3) * 14
            route_score -= density_penalty
            route_factors.append(
                self._factor("景点过密", -density_penalty, "点位太多会让移动和切换频繁，路线再顺也会显得赶。", f"{avg_attractions_per_day:.1f} 个景点/天")
            )
        elif avg_attractions_per_day < 1.5:
            sparse_penalty = (1.5 - avg_attractions_per_day) * 8
            route_score -= sparse_penalty
            route_factors.append(
                self._factor("单日过稀", -sparse_penalty, "每天点位太少时，路线效率会偏松散。", f"{avg_attractions_per_day:.1f} 个景点/天")
            )
        route_dimension = self._clamp_score(route_score)

        comfort_score = 96.0
        comfort_factors = [
            self._factor("舒适底分", 96.0, "默认按较舒服的旅行节奏起步，避免动不动就满分。"),
        ]
        if avg_visit_minutes_per_day > 420:
            visit_penalty = min(28.0, (avg_visit_minutes_per_day - 420) / 14)
            comfort_score -= visit_penalty
            comfort_factors.append(
                self._factor("停留时长偏满", -visit_penalty, "一天里沉浸时间太长，会让体力像一直绷着的弦。", f"{round(avg_visit_minutes_per_day)} 分钟/天")
            )
        else:
            comfort_factors.append(
                self._factor("留白时间充足", 0.0, "停留总时长还在舒适区，不容易从早赶到晚。", f"{round(avg_visit_minutes_per_day)} 分钟/天")
            )
        if avg_distance_km > ideal_distance + 2:
            distance_penalty = min(22.0, (avg_distance_km - ideal_distance - 2) * 1.8)
            comfort_score -= distance_penalty
            comfort_factors.append(
                self._factor("移动负担上升", -distance_penalty, "日均距离超过舒适线后，脚程和换乘压力会明显冒头。", f"{avg_distance_km:.1f} km/天")
            )
        if weather_severity["severe_days"] > 0 and avg_attractions_per_day > 3:
            comfort_score -= 10.0
            comfort_factors.append(
                self._factor("坏天气叠加密度", -10.0, "天气一旦翻脸，密集行程会更容易变累。", f"{weather_severity['severe_days']} 个高压天气日")
            )
        if any(item in self.MOBILITY_KEYS for item in mobility_needs) and avg_distance_km > 8:
            comfort_score -= 12.0
            comfort_factors.append(
                self._factor("行动需求未完全照顾", -12.0, "有少步行或休息需求时，距离过长会直接拉低舒适度。", f"{avg_distance_km:.1f} km/天")
            )
        comfort_dimension = self._clamp_score(comfort_score)

        resilience_score = 62.0 if weather_severity["severe_days"] > 0 else 86.0
        resilience_factors = [
            self._factor(
                "天气基准分",
                resilience_score,
                "天气压力越大，稳健性的起点就越保守；天气平稳时起点会更高。",
                f"{weather_severity['severe_days']} 个高压天气日",
            )
        ]
        indoor_bonus = indoor_ratio * 24
        resilience_score += indoor_bonus
        resilience_factors.append(
            self._factor("室内缓冲", indoor_bonus, "室内点位越多，遇到下雨、高温或突发情况时越容易切换方案。", f"{round(indoor_ratio * 100)}% 室内占比")
        )
        if has_rain_skill:
            resilience_score += 5.0
            resilience_factors.append(self._factor("雨天技能加持", 5.0, "系统识别到了雨天应对策略，执行韧性更强。"))
        if has_heat_skill:
            resilience_score += 5.0
            resilience_factors.append(self._factor("避暑策略加持", 5.0, "高温回避策略已经介入，极端天气下更稳。"))
        if missing_meals_days > 0:
            meal_gap_penalty = missing_meals_days * 3.0
            resilience_score -= meal_gap_penalty
            resilience_factors.append(
                self._factor("餐食预案不足", -meal_gap_penalty, "餐位留白太多，会降低临场调整时的稳定度。", f"{missing_meals_days} 天")
            )
        if missing_hotel_days > 0:
            hotel_gap_penalty = missing_hotel_days * 4.0
            resilience_score -= hotel_gap_penalty
            resilience_factors.append(
                self._factor("住宿信息缺口", -hotel_gap_penalty, "住宿没有落稳时，整份行程的执行弹性会变差。", f"{missing_hotel_days} 天")
            )
        if not self._travel_weather_items(plan):
            resilience_score -= 12.0
            resilience_factors.append(self._factor("天气信息缺失", -12.0, "少了天气锚点，系统只能保守估计执行稳定度。"))
        resilience_dimension = self._clamp_score(resilience_score)

        richness_score = 50.0
        richness_factors = [
            self._factor("体验基底", 50.0, "默认给一半分，看这份路线能不能从单线打卡走向层次丰富。"),
        ]
        category_bonus = min(22.0, len(unique_categories) * 8.0)
        richness_score += category_bonus
        richness_factors.append(
            self._factor("景点类型层次", category_bonus, "景点类型越多，旅行越像一桌有冷热荤素的完整餐。", f"{len(unique_categories)} 类")
        )
        meal_bonus = min(14.0, len(unique_meals) * 2.0)
        richness_score += meal_bonus
        richness_factors.append(
            self._factor("餐饮多样性", meal_bonus, "不同餐厅和餐食越丰富，城市的味觉记忆越立得住。", f"{len(unique_meals)} 家")
        )
        local_bonus = min(8.0, local_ratio * 18.0)
        richness_score += local_bonus
        richness_factors.append(
            self._factor("本地纹理", local_bonus, "本地感内容会给路线加上城市自己的纹理，而不是哪里都像。", f"{round(local_ratio * 100)}%")
        )
        iconic_bonus = min(8.0, iconic_count * 4.0)
        richness_score += iconic_bonus
        richness_factors.append(
            self._factor("城市记忆点", iconic_bonus, "有地标和高识别度场景，玩完以后更容易记住这座城。", f"{iconic_count} 个")
        )
        if len(unique_categories) < 2:
            category_penalty = max(0.0, 2 - len(unique_categories)) * 6.0
            richness_score -= category_penalty
            richness_factors.append(
                self._factor("题材略单", -category_penalty, "如果几乎都在玩同一类内容，体验会显得有点单色。")
            )
        richness_dimension = self._clamp_score(richness_score)

        dimensions = [
            DecisionScoreDimension(
                key="preference_fit",
                label="偏好贴合",
                description="看这份行程是不是顺着你的节奏、同行关系和出行习惯在走。",
                score=preference_dimension,
                detail=f"日均 {avg_attractions_per_day:.1f} 个景点，当前节奏和需求的贴合度一眼能看出来。",
                narrative=self._preference_narrative(preference_dimension),
                factors=preference_factors,
            ),
            DecisionScoreDimension(
                key="budget_fit",
                label="预算友好",
                description="看当前花费有没有压在你能接受的预算区间里，不松也不勒。",
                score=budget_dimension,
                detail=(
                    f"当前估算 {self._currency(budget.total)}，目标区间约 {self._currency(budget_target)}。"
                    if budget_target > 0
                    else f"当前估算 {self._currency(budget.total)}，但你还没设置明确预算档位。"
                ),
                narrative=self._budget_narrative(budget_dimension),
                factors=budget_factors,
            ),
            DecisionScoreDimension(
                key="route_efficiency",
                label="路线顺手",
                description="看景点顺序和点位分布是否丝滑，少绕路、少折返、少赶场。",
                score=route_dimension,
                detail=f"当前顺序预计全程约 {estimated_distance_km:.1f} km，日均 {avg_distance_km:.1f} km。",
                narrative=self._route_narrative(route_dimension),
                factors=route_factors,
            ),
            DecisionScoreDimension(
                key="comfort",
                label="舒适轻松",
                description="关注每天的密度、步行负担和停留时长，避免快乐变体力活。",
                score=comfort_dimension,
                detail=f"日均停留 {round(avg_visit_minutes_per_day)} 分钟，整体行程留白感会直接影响这项分数。",
                narrative=self._comfort_narrative(comfort_dimension),
                factors=comfort_factors,
            ),
            DecisionScoreDimension(
                key="resilience",
                label="稳健弹性",
                description="遇到雨天、高温或信息不完整时，这套方案还能不能稳稳落地。",
                score=resilience_dimension,
                detail=f"室内点位占比 {round(indoor_ratio * 100)}%，天气高压日 {weather_severity['severe_days']} 天。",
                narrative=self._resilience_narrative(resilience_dimension),
                factors=resilience_factors,
            ),
            DecisionScoreDimension(
                key="richness",
                label="体验层次",
                description="看这趟旅行是不是有看点、有味道、有变化，不是单线条重复播放。",
                score=richness_dimension,
                detail=f"景点类型 {len(unique_categories)} 类，餐饮建议 {len(unique_meals)} 家，城市记忆点 {iconic_count} 个。",
                narrative=self._richness_narrative(richness_dimension),
                factors=richness_factors,
            ),
        ]

        overall = self._clamp_score(sum(item.score * self.SCORE_WEIGHTS[item.key] for item in dimensions))
        summary, story = self._overall_story(overall)
        sorted_dimensions = sorted(dimensions, key=lambda item: item.score, reverse=True)
        highlights = [self._highlight_text(item) for item in sorted_dimensions[:3]]
        risks = [self._risk_text(item) for item in sorted(dimensions, key=lambda item: item.score) if item.score < 78][:2]

        return DecisionScoreSnapshot(
            overall=overall,
            dimensions=dimensions,
            summary=summary,
            story=story,
            highlights=highlights,
            risks=risks,
            budget=budget,
            estimated_distance_km=round(estimated_distance_km, 2),
            estimated_distance_text=f"{estimated_distance_km:.1f} km",
            comfort_text=f"日均 {avg_attractions_per_day:.1f} 个景点 · {round(avg_visit_minutes_per_day)} 分钟停留",
        )

    def build_plan_budget(self, plan: TripPlan) -> Budget:
        totals = {
            "total_attractions": 0,
            "total_hotels": 0,
            "total_meals": 0,
            "total_transportation": 0,
        }
        for day in plan.days:
            totals["total_attractions"] += sum(int(item.ticket_price or 0) for item in day.attractions)
            totals["total_hotels"] += int(day.hotel.estimated_cost or 0) if day.hotel else 0
            totals["total_meals"] += sum(int(item.estimated_cost or 0) for item in day.meals)
            totals["total_transportation"] += int(day.transportation_cost or 0)
        return Budget(
            **totals,
            total=(
                totals["total_attractions"]
                + totals["total_hotels"]
                + totals["total_meals"]
                + totals["total_transportation"]
            ),
        )

    def _normalize_summary(self, summary: ScoreSummaryInput) -> TripScoreSummary:
        if summary is None:
            return TripScoreSummary()
        if isinstance(summary, TripScoreSummary):
            return summary
        return TripScoreSummary(
            budget_level=summary.budget_level,
            travel_style=list(summary.travel_style),
            companions=list(summary.companions),
            dietary_restrictions=list(summary.dietary_restrictions),
            mobility_needs=list(summary.mobility_needs),
            transportation=summary.transportation,
            free_text_input=summary.free_text_input,
        )

    def _travel_weather_items(self, plan: TripPlan):
        travel_dates = {day.date for day in plan.days}
        matched = [item for item in plan.weather_info if item.date in travel_dates]
        return matched or list(plan.weather_info)

    def _get_weather_severity(self, plan: TripPlan) -> dict:
        severe = 0
        hot = 0
        rainy = 0
        weather_items = self._travel_weather_items(plan)
        for item in weather_items:
            text = f"{item.day_weather} {item.night_weather}"
            if any(token in text for token in ("暴雨", "雷阵雨", "大雨")):
                severe += 1
            if "雨" in text:
                rainy += 1
            if int(item.day_temp or 0) >= 30:
                severe += 1
                hot += 1
        return {
            "severe_days": severe,
            "rainy_days": rainy,
            "hot_days": hot,
            "total_days": max(len(plan.days), len(weather_items), 1),
        }

    def _estimate_day_distance_km(self, day: DayPlan, city: str) -> float:
        route_type = self._normalize_route_type(day.transportation)
        ratio = 1.18 if route_type == "walking" else 1.32 if route_type == "transit" else 1.45
        stops = [
            item for item in (self._get_safe_route_location(attraction.location, city) for attraction in day.attractions) if item
        ]
        if len(stops) < 2:
            return 0.0
        total = 0.0
        for index in range(len(stops) - 1):
            total += self._haversine_km(stops[index], stops[index + 1]) * ratio
        return total

    def _haversine_km(self, left: Location, right: Location) -> float:
        from math import atan2, cos, pi, sin, sqrt

        def to_rad(value: float) -> float:
            return (value * pi) / 180

        earth_radius = 6371
        d_lat = to_rad(right.latitude - left.latitude)
        d_lng = to_rad(right.longitude - left.longitude)
        lat1 = to_rad(left.latitude)
        lat2 = to_rad(right.latitude)
        value = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lng / 2) ** 2
        return earth_radius * 2 * atan2(sqrt(value), sqrt(1 - value))

    def _get_safe_route_location(self, location: Optional[Location], city: str) -> Optional[Location]:
        if not self._has_valid_location(location):
            return None
        normalized_city = str(city or "").strip().lower()
        if "beijing" in normalized_city or "北京" in normalized_city:
            return location
        if abs(location.longitude - 116.4) <= 0.35 and abs(location.latitude - 39.9) <= 0.35:
            return None
        return location

    def _has_valid_location(self, location: Optional[Location]) -> bool:
        return bool(location and isinstance(location.longitude, (int, float)) and isinstance(location.latitude, (int, float)))

    def _normalize_route_type(self, transportation: str) -> str:
        text = str(transportation or "").lower()
        if any(token in text for token in ("metro", "subway", "bus", "transit", "地铁", "公交")):
            return "transit"
        if any(token in text for token in ("taxi", "car", "drive", "打车", "驾车", "网约车")):
            return "driving"
        return "walking"

    def _normalize_attraction_category(self, item: Attraction) -> str:
        text = self._attraction_text(item)
        if "博物馆" in text or "展览" in text or "科技馆" in text:
            return "museum"
        if any(token in text for token in ("公园", "山", "湖", "湿地")):
            return "nature"
        if any(token in text for token in ("古镇", "街区", "citywalk", "步行街")):
            return "citywalk"
        if any(token in text for token in ("遗址", "历史", "古")):
            return "history"
        if any(token in text for token in ("商场", "购物")):
            return "shopping"
        return str(item.category or "other").lower()

    def _attraction_text(self, item: Attraction) -> str:
        return " ".join([item.name, str(item.category or ""), item.description, item.address]).lower()

    def _is_indoor_attraction(self, item: Attraction) -> bool:
        text = self._attraction_text(item)
        return any(keyword.lower() in text for keyword in self.INDOOR_KEYWORDS)

    def _is_local_attraction(self, item: Attraction) -> bool:
        text = self._attraction_text(item)
        return any(keyword.lower() in text for keyword in self.LOCAL_KEYWORDS)

    def _is_iconic_attraction(self, item: Attraction) -> bool:
        text = self._attraction_text(item)
        return any(keyword.lower() in text for keyword in self.ICONIC_KEYWORDS)

    def _filter_count(self, items: Sequence[Attraction], predicate: Callable[[Attraction], bool]) -> int:
        return sum(1 for item in items if predicate(item))

    def _ratio(self, numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return numerator / denominator

    def _currency(self, value: int | float) -> str:
        amount = int(round(value or 0))
        return f"¥{amount}" if amount > 0 else "待确认"

    def _clamp_score(self, value: float) -> int:
        return max(0, min(100, round(value)))

    def _factor(self, label: str, impact: float, reason: str, value: str = "") -> DecisionScoreFactor:
        return DecisionScoreFactor(label=label, impact=round(impact, 1), reason=reason, value=value)

    def _overall_story(self, overall: int) -> tuple[str, str]:
        if overall >= 90:
            return (
                "这版方案已经很能打",
                "它像一条被熨平褶皱的旅行丝带，预算、节奏和路线基本都顺手，直接出发也比较安心。",
            )
        if overall >= 80:
            return (
                "这版方案已经可以稳稳出发",
                "它像一串已经串好的城市项链，主线很清楚，只剩少数环节再抛一抛光，体验会更亮。",
            )
        if overall >= 70:
            return (
                "这版方案有骨架，但还值得再收一收",
                "它像一张已经起好形的旅行草图，能玩，但还有几个拐点会决定你是顺着玩，还是边玩边修。",
            )
        return (
            "这版方案还需要继续打磨",
            "它像一辆刚装好的旅行车，零件都在，但上路前还得再紧几颗螺丝，不然途中容易觉得卡。",
        )

    def _highlight_text(self, item: DecisionScoreDimension) -> str:
        if item.score >= 88:
            return f"{item.label}表现很亮眼"
        if item.score >= 80:
            return f"{item.label}已经站稳"
        return f"{item.label}是当前强项"

    def _risk_text(self, item: DecisionScoreDimension) -> str:
        if item.score < 65:
            return f"{item.label}建议优先补一补"
        return f"{item.label}还能再抛光"

    def _preference_narrative(self, score: int) -> str:
        if score >= 85:
            return "这份行程像照着你的出行习惯裁过版，走起来比较贴身。"
        if score >= 75:
            return "主旋律已经对味，只是个别安排还没完全踩中你的偏好点。"
        return "能玩，但和你的习惯之间还有一点“鞋子略磨脚”的距离。"

    def _budget_narrative(self, score: int) -> str:
        if score >= 90:
            return "花钱的松紧度拿捏得比较准，像把钱包和体验放在了一条平衡线上。"
        if score >= 75:
            return "整体还在可控范围，但预算边缘已经有点起波纹。"
        return "这项像裤腰带要么勒得太紧，要么已经开始松出预算线了。"

    def _route_narrative(self, score: int) -> str:
        if score >= 85:
            return "路线像把几颗珠子顺着线穿起来，转场比较自然。"
        if score >= 75:
            return "主线还算顺，但局部可能会有一点折返或赶场感。"
        return "路线里有些弯拐得太硬，玩起来容易觉得脚程和节奏在互相拉扯。"

    def _comfort_narrative(self, score: int) -> str:
        if score >= 85:
            return "一天的体力留白还不错，像呼吸顺畅的节拍，不容易玩着玩着就累塌。"
        if score >= 75:
            return "舒适度整体在线，但部分时段可能会出现“快乐但有点累”的感觉。"
        return "这项已经开始提醒你，行程的兴奋值可能在和体力值打架。"

    def _resilience_narrative(self, score: int) -> str:
        if score >= 85:
            return "就算天气突然翻脸，这套方案也还有腾挪空间，不至于整天散架。"
        if score >= 75:
            return "有一定缓冲，但碰上天气或信息变化时，仍然需要临场补一把。"
        return "稳健性偏弱，一旦遇到雨、高温或临时变化，体验容易被拉扯。"

    def _richness_narrative(self, score: int) -> str:
        if score >= 85:
            return "这趟旅行的层次感不错，像一桌配齐冷热荤素的菜，不容易审美疲劳。"
        if score >= 75:
            return "内容已经不单薄，但还有机会再多加一点城市自己的味道。"
        return "体验还偏单线条，容易出现“玩得不差，但记忆点不够深”的情况。"


_plan_score_service: Optional[PlanScoreService] = None


def get_plan_score_service() -> PlanScoreService:
    global _plan_score_service
    if _plan_score_service is None:
        _plan_score_service = PlanScoreService()
    return _plan_score_service
