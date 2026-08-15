"""Schema API cho trang Quy tắc đánh số."""

from pydantic import BaseModel, Field, field_validator, model_validator

ALLOWED_TOKENS = {
    "STT", "Ngay", "Thang", "Nam", "LoaiVB", "PhongBan", "PhapNhan", "SoVB",
}


def _unknown_tokens(pattern: str) -> set[str]:
    import re

    return set(re.findall(r"\{([^{}]+)\}", pattern or "")) - ALLOWED_TOKENS


class DocumentNumberingRuleBase(BaseModel):
    direction: int = Field(ge=1, le=3)
    pattern: str = Field(min_length=1, max_length=200)
    start_no: int = Field(default=1, ge=1)
    reset_yearly: bool = True
    allow_manual: bool = False
    doc_type_mode: int = Field(default=1, ge=1, le=2)
    book_mode: int = Field(default=1, ge=1, le=3)
    priority: int = Field(default=100, ge=1, le=9999)
    is_active: bool = True
    doc_type_ids: list[int] = Field(default_factory=list)
    book_ids: list[int] = Field(default_factory=list)

    @field_validator("pattern")
    @classmethod
    def validate_pattern(cls, value: str):
        value = value.strip()
        unknown = _unknown_tokens(value)
        if unknown:
            raise ValueError(f"Token không hỗ trợ: {', '.join(sorted(unknown))}")
        if "{STT}" not in value:
            raise ValueError("Quy tắc phải có token {STT}")
        return value

    @field_validator("doc_type_ids", "book_ids")
    @classmethod
    def positive_unique_ids(cls, values: list[int]):
        return list(dict.fromkeys(value for value in values if value > 0))

    @model_validator(mode="after")
    def validate_scopes(self):
        if self.doc_type_mode == 2 and not self.doc_type_ids:
            raise ValueError("Hãy chọn ít nhất một loại văn bản")
        if self.book_mode == 2 and not self.book_ids:
            raise ValueError("Hãy chọn ít nhất một sổ văn bản")
        if self.book_mode != 2:
            self.book_ids = []
        if self.doc_type_mode != 2:
            self.doc_type_ids = []
        return self


class DocumentNumberingRuleCreate(DocumentNumberingRuleBase):
    pass


class DocumentNumberingRuleUpdate(BaseModel):
    direction: int | None = Field(default=None, ge=1, le=3)
    pattern: str | None = Field(default=None, min_length=1, max_length=200)
    start_no: int | None = Field(default=None, ge=1)
    reset_yearly: bool | None = None
    allow_manual: bool | None = None
    doc_type_mode: int | None = Field(default=None, ge=1, le=2)
    book_mode: int | None = Field(default=None, ge=1, le=3)
    priority: int | None = Field(default=None, ge=1, le=9999)
    is_active: bool | None = None
    doc_type_ids: list[int] | None = None
    book_ids: list[int] | None = None

    @field_validator("pattern")
    @classmethod
    def validate_pattern(cls, value: str | None):
        if value is None:
            return value
        value = value.strip()
        unknown = _unknown_tokens(value)
        if unknown:
            raise ValueError(f"Token không hỗ trợ: {', '.join(sorted(unknown))}")
        if "{STT}" not in value:
            raise ValueError("Quy tắc phải có token {STT}")
        return value

    @field_validator("doc_type_ids", "book_ids")
    @classmethod
    def positive_unique_ids(cls, values: list[int] | None):
        if values is None:
            return values
        return list(dict.fromkeys(value for value in values if value > 0))


class DocumentNumberingRuleOut(DocumentNumberingRuleBase):
    id: int
    direction_label: str = ""
    doc_type_names: list[str] = Field(default_factory=list)
    book_names: list[str] = Field(default_factory=list)
    has_issued_numbers: bool = False
    model_config = {"from_attributes": True}
