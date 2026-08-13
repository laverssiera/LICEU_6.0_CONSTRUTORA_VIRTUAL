from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BusinessCreate(BaseModel):
    title: str = Field(min_length=1, max_length=220)
    portfolio: str = Field(min_length=1, max_length=120)
    program: str = Field(min_length=1, max_length=120)
    stage: str = Field(default="Ideia", min_length=1, max_length=40)
    estimated_cost: float
    expected_return: float


class BusinessResponse(BaseModel):
    id: UUID
    title: str
    portfolio: str
    program: str
    stage: str
    estimated_cost: float
    expected_return: float
    created_at: datetime

    model_config = {"from_attributes": True}
