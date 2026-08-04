from typing import Optional

from pydantic import BaseModel, ConfigDict


class FaqCreate(BaseModel):
    question: str
    answer: str = ""
    sort_order: int = 0
    is_active: bool = True


class FaqUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class FaqOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    answer: str
    sort_order: int
    is_active: bool
