from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class HelpArticleSlideCreate(BaseModel):
    image_url: str
    caption: Optional[str] = None
    step_order: int = 0


class HelpArticleSlideUpdate(BaseModel):
    image_url: Optional[str] = None
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
    title: str
    parent_id: Optional[int] = None
    content: str = ""
    sort_order: int = 0
    summary: Optional[str] = None
    icon: Optional[str] = None


class HelpArticleUpdate(BaseModel):
    title: Optional[str] = None
    parent_id: Optional[int] = None
    content: Optional[str] = None
    sort_order: Optional[int] = None
    summary: Optional[str] = None
    icon: Optional[str] = None


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
