"""Schemas for skill selection and runtime injection."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class SkillDefinition(BaseModel):
    key: str
    name: str
    description: str
    priority: int = 100
    enabled: bool = True
    required_any_tags: List[str] = Field(default_factory=list)
    required_any_keywords: List[str] = Field(default_factory=list)
    incompatible_with: List[str] = Field(default_factory=list)
    attraction_query_boosts: List[str] = Field(default_factory=list)
    hotel_query_boosts: List[str] = Field(default_factory=list)
    planning_rules: List[str] = Field(default_factory=list)
    output_hints: List[str] = Field(default_factory=list)


class SelectedSkill(BaseModel):
    key: str
    name: str
    description: str = ""
    score: float = 0.0
    reasons: List[str] = Field(default_factory=list)
    attraction_query_boosts: List[str] = Field(default_factory=list)
    hotel_query_boosts: List[str] = Field(default_factory=list)
    planning_rules: List[str] = Field(default_factory=list)
    output_hints: List[str] = Field(default_factory=list)
