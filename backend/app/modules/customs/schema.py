"""Schema màn sửa danh mục hóa chất theo văn bản (bao-CR-470, HQ6 P-01).

Mọi cột chữ khai `max_length` khớp ĐÚNG `String(n)` ở `model.py`: thiếu thì chuỗi quá
dài đi thẳng xuống MySQL và ra lỗi 500 thay vì câu "tối đa n ký tự" (duoc-CR-316).
Bộ test chạy SQLite, không ép độ dài — nên chốt phải nằm ở đây.
"""
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .constants import ProductKind, RegulationList, TransportMode

_LIST_CODES = {int(x) for x in RegulationList}


def _check_list_code(v):
    if v is not None and int(v) not in _LIST_CODES:
        raise ValueError(f"Danh sách không hợp lệ: {v}")
    return v


class RegulationCreate(BaseModel):
    list_code: int
    seq_no: str = Field("", max_length=20)          # duoc-CR-598 — STT trong phụ lục
    name: str = Field(..., min_length=1, max_length=500)
    name_vi: str = Field("", max_length=500)
    cas_no: str = Field("", max_length=40)
    formula: str = Field("", max_length=100)        # duoc-CR-598 — công thức hóa học
    category: str = Field("", max_length=100)
    #  Ngưỡng khối lượng (kg) — chỉ có nghĩa với Phụ lục IV của NĐ 24/2026.
    threshold_kg: Decimal | None = Field(None, ge=0, le=Decimal("99999999999"))
    mixture_pct: Decimal | None = Field(None, ge=0, le=100)
    banned_year: int | None = Field(None, ge=1900, le=2100)
    legal_basis: str = Field("", max_length=255)
    note: str = Field("", max_length=500)
    is_active: bool = True

    _v_list = field_validator("list_code")(_check_list_code)


class RegulationUpdate(BaseModel):
    list_code: int | None = None
    seq_no: str | None = Field(None, max_length=20)
    name: str | None = Field(None, min_length=1, max_length=500)
    name_vi: str | None = Field(None, max_length=500)
    cas_no: str | None = Field(None, max_length=40)
    formula: str | None = Field(None, max_length=100)
    category: str | None = Field(None, max_length=100)
    threshold_kg: Decimal | None = Field(None, ge=0, le=Decimal("99999999999"))
    mixture_pct: Decimal | None = Field(None, ge=0, le=100)
    banned_year: int | None = Field(None, ge=1900, le=2100)
    legal_basis: str | None = Field(None, max_length=255)
    note: str | None = Field(None, max_length=500)
    is_active: bool | None = None

    _v_list = field_validator("list_code")(_check_list_code)


class RegulationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    list_code: int
    seq_no: str = ""
    sort_order: int = 0
    name: str = ""
    name_vi: str = ""
    cas_no: str = ""
    formula: str = ""
    category: str = ""
    threshold_kg: float | None = None
    mixture_pct: float | None = None
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


# ── bao-CR-608: sửa tay MỘT dòng hàng trên màn «Giá thị trường» ──────────────────────────
#  Trần độ dài khớp ĐÚNG `String(n)` của `CustomsLine` (hai cột đối tượng khớp `CustomsParty`:
#  `tax_code` String(14), `name` String(255)). Số: trần theo độ chính xác của cột `Numeric(p, s)`
#  — vượt là MySQL báo «Out of range» thành 500. Ngày: dải hợp lý 2000 → 2100.
_MIN_LINE_DATE = date(2000, 1, 1)
_MAX_LINE_DATE = date(2100, 12, 31)
_Price = Field(None, ge=0, le=Decimal("999999999999"))          # Numeric(16, 4)
_FxRate = Field(None, ge=0, le=Decimal("9999999999"))           # Numeric(14, 4)
_Quantity = Field(None, ge=0, le=Decimal("99999999999999"))     # Numeric(18, 4)
_Rate = Field(None, ge=0, le=Decimal("9999"))                   # Numeric(6, 2) — thuế suất %
_Tax = Field(None, ge=0, le=Decimal("999999999999999"))         # Numeric(18, 3)
_Vnd = Field(None, ge=0, le=Decimal("9999999999999999"))        # Numeric(18, 2)


def _check_line_date(v):
    if v is not None and not (_MIN_LINE_DATE <= v <= _MAX_LINE_DATE):
        raise ValueError(f"Ngày phải trong khoảng {_MIN_LINE_DATE.year}–{_MAX_LINE_DATE.year}")
    return v


def _check_transport(v):
    if v is not None and int(v) not in {int(t) for t in TransportMode}:
        raise ValueError(f"Phương tiện vận chuyển không hợp lệ: {v}")
    return v


class CustomsLineUpdate(BaseModel):
    """Hộp sửa dòng — chỉ gửi trường nào đổi (PATCH). Trường bỏ trống chữ = để trống ô.

    Hai trường suy ra «Hoạt chất» / «Hàm lượng / dạng»: gửi chữ = giá trị DO NGƯỜI NHẬP (cờ
    `_from_file` = 1, `retag_all` không ghi đè); gửi chuỗi rỗng = trả về cho hệ thống suy ra từ
    tên hàng. Hai cột giá VND: gửi số = giữ số đó; gửi null = để hệ thống tính như cũ.
    """
    model_config = ConfigDict(extra="forbid")

    reg_date: date | None = None
    office_code: str | None = Field(None, max_length=10)
    importer_tax_code: str | None = Field(None, max_length=14)
    importer_name: str | None = Field(None, max_length=255)
    partner_name: str | None = Field(None, max_length=255)
    hs_code: str | None = Field(None, max_length=8)
    line_no: int | None = Field(None, ge=0, le=32767)                # SmallInteger
    product_name: str | None = Field(None, min_length=1, max_length=255)
    price_usd: Decimal | None = _Price
    price_nt: Decimal | None = _Price
    adj_price_usd: Decimal | None = _Price
    adj_price_nt: Decimal | None = _Price
    currency: str | None = Field(None, max_length=3)
    fx_rate: Decimal | None = _FxRate
    usd_rate: Decimal | None = _FxRate
    quantity: Decimal | None = _Quantity
    unit_code: str | None = Field(None, max_length=4)
    origin_country: str | None = Field(None, max_length=2)
    contract_no: str | None = Field(None, max_length=40)
    contract_date: date | None = None
    incoterm: str | None = Field(None, max_length=3)
    transport_mode: int | None = None
    rate_import: Decimal | None = _Rate
    rate_excise: Decimal | None = _Rate
    rate_vat: Decimal | None = _Rate
    rate_safeguard: Decimal | None = _Rate
    tax_import: Decimal | None = _Tax
    tax_excise: Decimal | None = _Tax
    tax_vat: Decimal | None = _Tax
    tax_environment: Decimal | None = _Tax
    tax_safeguard: Decimal | None = _Tax
    import_country: str | None = Field(None, max_length=2)
    active_ingredient: str | None = Field(None, max_length=255)
    formulation: str | None = Field(None, max_length=40)
    price_vnd_flat: Decimal | None = _Vnd
    price_vnd_line_tax: Decimal | None = _Vnd

    _v_dates = field_validator("reg_date", "contract_date")(_check_line_date)
    _v_transport = field_validator("transport_mode")(_check_transport)

    @field_validator("reg_date")
    @classmethod
    def _reg_date_required(cls, v):
        #  Gửi `reg_date: null` = xóa Ngày đăng ký — cột bắt buộc (khóa phân vùng), không cho.
        if v is None:
            raise ValueError("Ngày đăng ký không được để trống")
        return v
