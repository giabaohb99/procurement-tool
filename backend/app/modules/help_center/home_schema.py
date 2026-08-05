"""Schema cho cấu hình hiển thị trang chủ khu người dùng (4 khung cố định)."""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class HelpHomeSectionUpdate(BaseModel):
    title: Optional[str] = None
    is_visible: Optional[bool] = None
    sort_order: Optional[int] = None


class HelpHomeItemCreate(BaseModel):
    article_id: int
    background_image: Optional[str] = None
    gradient: Optional[str] = None
    sort_order: int = 0


class HelpHomeItemUpdate(BaseModel):
    background_image: Optional[str] = None
    gradient: Optional[str] = None
    sort_order: Optional[int] = None


class HelpHomeItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int
    # JOIN từ tab_help_article để trang chủ render thẳng, không phải gọi thêm request
    article_title: Optional[str] = None
    article_summary: Optional[str] = None
    article_icon: Optional[str] = None
    background_image: Optional[str] = None
    gradient: Optional[str] = None
    sort_order: int


class HelpHomeSectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    title: str
    is_visible: bool
    sort_order: int
    items: List[HelpHomeItemOut] = []
