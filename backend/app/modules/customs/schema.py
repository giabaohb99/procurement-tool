"""Schema màn sửa danh mục hóa chất theo văn bản (bao-CR-470, HQ6 P-01).

Mọi cột chữ khai `max_length` khớp ĐÚNG `String(n)` ở `model.py`: thiếu thì chuỗi quá
dài đi thẳng xuống MySQL và ra lỗi 500 thay vì câu "tối đa n ký tự" (duoc-CR-316).
Bộ test chạy SQLite, không ép độ dài — nên chốt phải nằm ở đây.
"""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .constants import ProductKind, RegulationList

_LIST_CODES = {int(x) for x in RegulationList}


def _check_list_code(v):
    if v is not None and int(v) not in _LIST_CODES:
        raise ValueError(f"Danh sách không hợp lệ: {v}")
    return v


class RegulationCreate(BaseModel):
    list_code: int
    name: str = Field(..., min_length=1, max_length=500)
    name_vi: str = Field("", max_length=500)
    cas_no: str = Field("", max_length=40)
    category: str = Field("", max_length=100)
    #  Ngưỡng khối lượng (kg) — chỉ có nghĩa với Phụ lục IV của NĐ 24/2026.
    threshold_kg: Decimal | None = Field(None, ge=0, le=Decimal("99999999999"))
    banned_year: int | None = Field(None, ge=1900, le=2100)
    legal_basis: str = Field("", max_length=255)
    note: str = Field("", max_length=500)
    is_active: bool = True

    _v_list = field_validator("list_code")(_check_list_code)


class RegulationUpdate(BaseModel):
    list_code: int | None = None
    name: str | None = Field(None, min_length=1, max_length=500)
    name_vi: str | None = Field(None, max_length=500)
    cas_no: str | None = Field(None, max_length=40)
    category: str | None = Field(None, max_length=100)
    threshold_kg: Decimal | None = Field(None, ge=0, le=Decimal("99999999999"))
    banned_year: int | None = Field(None, ge=1900, le=2100)
    legal_basis: str | None = Field(None, max_length=255)
    note: str | None = Field(None, max_length=500)
    is_active: bool | None = None

    _v_list = field_validator("list_code")(_check_list_code)


class RegulationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    list_code: int
    name: str = ""
    name_vi: str = ""
    cas_no: str = ""
    category: str = ""
    threshold_kg: float | None = None
    banned_year: int | None = None
    legal_basis: str = ""
    note: str = ""
    is_active: bool = True


# ── bao-CR-494: từ khóa Thành phẩm / Nguyên liệu ──────────────────────────────────────────

def _clean_keyword(v: str) -> str:
    v = " ".join((v or "").split())
    if not v:
        raise ValueError("Từ khóa không được để trống")
    return v


class KindKeywordCreate(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=100)
    kind: int = int(ProductKind.TECHNICAL)
    note: str = Field("", max_length=255)
    is_active: bool = True

    @field_validator("keyword")
    @classmethod
    def _kw(cls, v):
        return _clean_keyword(v)

    @field_validator("kind")
    @classmethod
    def _kind(cls, v):
        if v not in (int(ProductKind.FINISHED), int(ProductKind.TECHNICAL)):
            raise ValueError("Loại phải là 1 (Thành phẩm) hoặc 2 (Nguyên liệu)")
        return v


class KindKeywordUpdate(BaseModel):
    keyword: str | None = Field(None, min_length=1, max_length=100)
    kind: int | None = None
    note: str | None = Field(None, max_length=255)
    is_active: bool | None = None

    @field_validator("keyword")
    @classmethod
    def _kw(cls, v):
        return None if v is None else _clean_keyword(v)

    @field_validator("kind")
    @classmethod
    def _kind(cls, v):
        if v is not None and v not in (int(ProductKind.FINISHED), int(ProductKind.TECHNICAL)):
            raise ValueError("Loại phải là 1 (Thành phẩm) hoặc 2 (Nguyên liệu)")
        return v


class KindKeywordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    keyword: str = ""
    kind: int = 2
    note: str = ""
    is_active: bool = True


# ── bao-CR-495: từ đồng nghĩa tìm kiếm ────────────────────────────────────────────────────

def _clean_synonyms(v: str) -> str:
    parts = [" ".join(x.split()) for x in (v or "").replace(chr(10), ";").split(";")]
    seen: list[str] = []
    for part in parts:
        if part and part.casefold() not in {s.casefold() for s in seen}:
            seen.append(part)
    return "; ".join(seen)


class SearchSynonymCreate(BaseModel):
    term: str = Field(..., min_length=1, max_length=100)
    synonyms: str = Field("", max_length=1000)
    note: str = Field("", max_length=255)
    is_active: bool = True

    @field_validator("term")
    @classmethod
    def _term(cls, v):
        return _clean_keyword(v)

    @field_validator("synonyms")
    @classmethod
    def _syn(cls, v):
        return _clean_synonyms(v)


class SearchSynonymUpdate(BaseModel):
    term: str | None = Field(None, min_length=1, max_length=100)
    synonyms: str | None = Field(None, max_length=1000)
    note: str | None = Field(None, max_length=255)
    is_active: bool | None = None

    @field_validator("term")
    @classmethod
    def _term(cls, v):
        return None if v is None else _clean_keyword(v)

    @field_validator("synonyms")
    @classmethod
    def _syn(cls, v):
        return None if v is None else _clean_synonyms(v)


class SearchSynonymOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    term: str = ""
    synonyms: str = ""
    note: str = ""
    is_active: bool = True


# ── bao-CR-496: bộ lọc đã lưu ─────────────────────────────────────────────────────────────
#  `name` khai max_length khớp String(120) của model (luật duoc-CR-316: thiếu là 500 thay vì 422).
#  `params` là chuỗi tham số URL; trần 4000 ký tự để không ai dán cả trang web vào cột Text.
SAVED_FILTER_PARAMS_MAX = 4000


def _clean_filter_name(v: str) -> str:
    v = " ".join((v or "").split())
    if not v:
        raise ValueError("Tên bộ lọc không được để trống")
    return v


class SavedFilterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    params: str = Field("", max_length=SAVED_FILTER_PARAMS_MAX)

    @field_validator("name")
    @classmethod
    def _name(cls, v):
        return _clean_filter_name(v)


class SavedFilterUpdate(BaseModel):
    """Đổi tên và/hoặc ghi đè bộ tham số («Cập nhật» = lưu điều kiện đang áp vào tên cũ)."""
    name: str | None = Field(None, min_length=1, max_length=120)
    params: str | None = Field(None, max_length=SAVED_FILTER_PARAMS_MAX)

    @field_validator("name")
    @classmethod
    def _name(cls, v):
        return None if v is None else _clean_filter_name(v)


class SavedFilterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = ""
    params: str = ""
    is_shared: bool = False
    updated_at: datetime | None = None
