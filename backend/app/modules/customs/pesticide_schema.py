"""Schema thêm / sửa MỘT thuốc BVTV trên màn (duoc-CR-490, 29/09/2026).

Mọi cột chữ khai `max_length` khớp ĐÚNG `String(n)` ở `model.py` — lấy thẳng từ trần của bộ đọc
tệp (`pesticide_reader._LIMITS`) để hai cửa ghi không lệch nhau. Thiếu thì chuỗi quá dài đi
thẳng xuống MySQL và ra lỗi 500 thay vì câu «tối đa n ký tự» (duoc-CR-316); pytest chạy SQLite
không ép độ dài nên chốt phải nằm ở đây.

Sửa là GỬI ĐỦ cả bản ghi lẫn danh sách phạm vi sử dụng (thay toàn bộ phạm vi) — màn sửa luôn
có đủ dữ liệu trong tay, còn vá từng dòng con thì phải khai thêm id dòng con cho chẳng được gì.
"""
from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator

from .constants import PesticideStatus
from .pesticide_reader import _LIMITS, _TEXT_LIMIT, _USE_LIMITS, MAX_USES_PER_RECORD

_STATUSES = {int(x) for x in PesticideStatus}


def _trim(v):
    return v.strip() if isinstance(v, str) else v


class PesticideUseIn(BaseModel):
    crop: str = Field("", max_length=_USE_LIMITS["crop"])
    pest: str = Field("", max_length=_USE_LIMITS["pest"])
    dosage: str = Field("", max_length=_USE_LIMITS["dosage"])
    pre_harvest_interval: str = Field("", max_length=_USE_LIMITS["pre_harvest_interval"])
    usage: str = Field("", max_length=_TEXT_LIMIT)

    _v_trim = field_validator("*", mode="before")(_trim)


class PesticideIn(BaseModel):
    #  Không khai `min_length`: nó chạy TRƯỚC `_not_blank` và trả câu tiếng Anh «String should have
    #  at least 1 character» lên màn. Chuỗi rỗng / toàn khoảng trắng do `_not_blank` chặn.
    trade_name: str = Field(..., max_length=_LIMITS["trade_name"])
    active_ingredient: str = Field(..., max_length=_LIMITS["active_ingredient"])
    concentration: str = Field("", max_length=_LIMITS["concentration"])
    pest_group: str = Field("", max_length=_LIMITS["pest_group"])
    sector: str = Field("", max_length=_LIMITS["sector"])
    registrant: str = Field("", max_length=_LIMITS["registrant"])
    registration_no: str = Field("", max_length=_LIMITS["registration_no"])
    #  Dải năm hợp lý: MySQL nhận tới năm 9999, gõ nhầm «0202» là hạn đăng ký hai nghìn năm trước.
    registered_on: date | None = None
    expires_on: date | None = None
    status: int = int(PesticideStatus.ACTIVE)
    toxicity: str = Field("", max_length=_LIMITS["toxicity"])
    resistance: str = Field("", max_length=_TEXT_LIMIT)
    source_url: str = Field("", max_length=_LIMITS["source_url"])
    #  Câu mô tả (duoc-CR-495) — thuốc tự thêm thì người nhập tự viết.
    summary: str = Field("", max_length=_TEXT_LIMIT)
    uses: list[PesticideUseIn] = Field(default_factory=list, max_length=MAX_USES_PER_RECORD)

    _v_trim = field_validator(
        "trade_name", "active_ingredient", "concentration", "pest_group", "sector", "registrant",
        "registration_no", "toxicity", "resistance", "source_url", "summary", mode="before")(_trim)

    @field_validator("trade_name", "active_ingredient")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v:
            raise ValueError("Không được để trống")
        return v

    @field_validator("status")
    @classmethod
    def _known_status(cls, v: int) -> int:
        if v not in _STATUSES:
            raise ValueError(f"Tình trạng không hợp lệ: {v}")
        return v

    @field_validator("registered_on", "expires_on")
    @classmethod
    def _sane_year(cls, v: date | None) -> date | None:
        if v is not None and not 1950 <= v.year <= 2100:
            raise ValueError("Năm phải trong khoảng 1950–2100")
        return v

    @field_validator("source_url")
    @classmethod
    def _http_only(cls, v: str) -> str:
        #  Giá trị này thành `<a href>` trên màn — không để lọt `javascript:`.
        if v and not v.lower().startswith(("http://", "https://")):
            raise ValueError("Đường dẫn nguồn phải bắt đầu bằng http:// hoặc https://")
        return v

    @model_validator(mode="after")
    def _expiry_after_issue(self):
        if self.registered_on and self.expires_on and self.expires_on < self.registered_on:
            raise ValueError("Ngày hết hạn đăng ký phải sau ngày cấp")
        return self
