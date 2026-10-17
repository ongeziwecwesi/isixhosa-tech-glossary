"""
Shapes of the data going in and out of the API.

Pydantic checks incoming data against these before our code sees it, so a
request with a missing field or a 5,000-character "term" is rejected with
a 422 error automatically.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config import CATEGORIES


class TermOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    english: str
    xhosa: str
    category: str
    definition: str
    definition_xh: str | None
    example_xh: str | None
    source: str | None


class TermPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[TermOut]


class CategoryOut(BaseModel):
    name: str
    count: int


class SuggestionIn(BaseModel):
    english: str = Field(min_length=1, max_length=120)
    xhosa: str = Field(min_length=1, max_length=160)
    category: str
    definition: str = Field(min_length=10, max_length=1000)
    example_xh: str | None = Field(default=None, max_length=500)
    note: str | None = Field(default=None, max_length=1000)
    submitted_by: str | None = Field(default=None, max_length=80)

    @field_validator("english", "xhosa", "definition")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("category")
    @classmethod
    def known_category(cls, value: str) -> str:
        if value not in CATEGORIES:
            raise ValueError(f"must be one of: {', '.join(CATEGORIES)}")
        return value


class SuggestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    english: str
    xhosa: str
    category: str
    definition: str
    example_xh: str | None
    note: str | None
    submitted_by: str | None
    status: Literal["pending", "approved", "rejected"]
    review_note: str | None
    created_at: datetime
    reviewed_at: datetime | None
    term_id: int | None


class ReviewIn(BaseModel):
    review_note: str | None = Field(default=None, max_length=1000)
