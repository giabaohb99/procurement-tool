from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from app.modules.employee.field_limits import Str255, Str500


class HelpArticleSlideCreate(BaseModel):
    image_url: Str500
    caption: Optional[str] = None
    step_order: int = 0


class HelpArticleSlideUpdate(BaseModel):
    image_url: Str500 | None = None
    caption: Optional[str] = None
    step_order: Optional[int] = None


class HelpArticleSlideOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int
    image_url: str
    caption: Optional[str] = None
    step_order: int


class HelpArticleCreate(BaseModel):
    title: Str255
    parent_id: Optional[int] = None
    content: str = ""
    sort_order: int = 0
    summary: Str255 | None = None
    icon: Str500 | None = None


class HelpArticleUpdate(BaseModel):
    title: Str255 | None = None
    parent_id: Optional[int] = None
    content: Optional[str] = None
    sort_order: Optional[int] = None
    summary: Str255 | None = None
    icon: Str500 | None = None


class HelpArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    parent_id: Optional[int] = None
    sort_order: int
    summary: Optional[str] = None
    icon: Optional[str] = None

    # Chỉ có ở màn chi tiết, danh sách cây bỏ qua cho nhẹ
    content: Optional[str] = None
    slides: List[HelpArticleSlideOut] = []
