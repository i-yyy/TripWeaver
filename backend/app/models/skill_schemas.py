"""Schemas for skill definition, selection, and validation."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class SkillDefinition(BaseModel):
    key: str
    name: str
    description: str = ""
    priority: int = 100
    layer: str = "static"  # static / dynamic
    category: str = "style"  # hard / dynamic-hard / style
    enabled: bool = True
    incompatible_with: List[str] = Field(default_factory=list)
    suppresses: List[str] = Field(default_factory=list)
    required_any_tags: List[str] = Field(default_factory=list)
    required_any_keywords: List[str] = Field(default_factory=list)
    required_budget_levels: List[str] = Field(default_factory=list)
    required_transport_modes: List[str] = Field(default_factory=list)
    required_companions: List[str] = Field(default_factory=list)
    required_dietary_restrictions: List[str] = Field(default_factory=list)
    required_mobility_needs: List[str] = Field(default_factory=list)
    weekend_only: bool = False
    min_temperature: Optional[int] = None
    max_temperature: Optional[int] = None
    weather_keywords: List[str] = Field(default_factory=list)
    hard_rules: List[str] = Field(default_factory=list)
    soft_rules: List[str] = Field(default_factory=list)
    meal_rules: List[str] = Field(default_factory=list)
    routing_rules: List[str] = Field(default_factory=list)
    planning_rules: List[str] = Field(default_factory=list)
    attraction_query_boosts: List[str] = Field(default_factory=list)
    hotel_query_boosts: List[str] = Field(default_factory=list)
    output_hints: List[str] = Field(default_factory=list)


class SelectedSkill(BaseModel):
    key: str
    name: str
    description: str = ""
    score: float = 0.0
    priority: int = 100
    layer: str = ""
    category: str = ""
    source: str = ""
    matched_fields: List[str] = Field(default_factory=list)
    matched_terms: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    incompatible_with: List[str] = Field(default_factory=list)
    suppresses: List[str] = Field(default_factory=list)
    hard_rules: List[str] = Field(default_factory=list)
    soft_rules: List[str] = Field(default_factory=list)
    meal_rules: List[str] = Field(default_factory=list)
    routing_rules: List[str] = Field(default_factory=list)
    planning_rules: List[str] = Field(default_factory=list)
    attraction_query_boosts: List[str] = Field(default_factory=list)
    hotel_query_boosts: List[str] = Field(default_factory=list)
    output_hints: List[str] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    code: str
    severity: str
    message: str
    day_index: Optional[int] = None
    repair_hint: str = ""


class ValidationResult(BaseModel):
    passed: bool = True
    warnings: List[ValidationIssue] = Field(default_factory=list)
    errors: List[ValidationIssue] = Field(default_factory=list)
