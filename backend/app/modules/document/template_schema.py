"""Schema quản lý thư viện văn bản mẫu."""
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


def _strip(value: str) -> str:
    return (value or "").strip()


class DocumentTemplateBase(BaseModel):
    doc_type_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    is_active: bool = True

    @field_validator("name", "description", mode="before")
    @classmethod
    def strip_text(cls, value):
        return _strip(value) if isinstance(value, str) else value


class DocumentTemplateCreate(DocumentTemplateBase):
    content_html: str = ""


class DocumentTemplateUpdate(BaseModel):
    doc_type_id: int | None = Field(default=None, gt=0)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    content_html: str | None = None
    is_active: bool | None = None

    @field_validator("name", "description", mode="before")
    @classmethod
    def strip_text(cls, value):
        return _strip(value) if isinstance(value, str) else value


class DocumentTemplateListOut(DocumentTemplateBase):
    id: int
    doc_type_name: str = ""
    doc_type_code: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentTemplateDetailOut(DocumentTemplateListOut):
    content_html: str = ""
