"""Hợp đồng nhận lô sự kiện giao diện (duoc-CR-641, phase 03). Mọi chuỗi có `max_length`
(luật `backend-input-limits`: SQLite không ép VARCHAR nên phải chặn ở tầng schema).

Không nhận `user_id`, `occurred_at`, `session_id` từ client: người ghi lấy từ token, giờ tính ở
server bằng `now − age_ms`. Không có trường từ khóa tìm kiếm — chỉ `result_count`.
"""
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.usage_codes import UiApp, UiEventType, UiForm

MAX_EVENTS_PER_BATCH = 100
MAX_BODY_BYTES = 64 * 1024
#  24 giờ: lô giữ lại qua đêm (401) gửi lại sau cùng vẫn rơi đúng ngày phát sinh. `age_ms` là khoảng cách, không phải đồng hồ
#  máy khách; người gửi chỉ ghi được sự kiện của chính mình nên kẹp 24 giờ là đủ chặn lệch ngày lớn.
MAX_AGE_MS = 86_400_000
MAX_DURATION_MS = 86_400_000
MAX_RESULT_COUNT = 1_000_000
MAX_TAB_KEY = 2**31 - 1

_ROUTE_PATTERN = r"^/[A-Za-z0-9/_:\-.]*$"


class UiEventError(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field("", max_length=60)
    message: str = Field("", max_length=200)


class UiEventIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: int
    route: str = Field(..., min_length=1, max_length=120, pattern=_ROUTE_PATTERN)
    form: int = 0
    duration_ms: int = Field(0, ge=0, le=MAX_DURATION_MS)
    result_count: int | None = Field(None, ge=0, le=MAX_RESULT_COUNT)
    age_ms: int = Field(0, ge=0)   # quá MAX_AGE_MS thì service kẹp, không từ chối cả lô
    tab_key: int = Field(0, ge=0, le=MAX_TAB_KEY)
    error: UiEventError | None = None

    @field_validator("type")
    @classmethod
    def _type_known(cls, v: int) -> int:
        if v not in {int(t) for t in UiEventType}:
            raise ValueError("Loại sự kiện không hợp lệ")
        return v

    @field_validator("form")
    @classmethod
    def _form_known(cls, v: int) -> int:
        if v != 0 and v not in {int(f) for f in UiForm}:
            raise ValueError("Biểu mẫu không hợp lệ")
        return v

    @model_validator(mode="after")
    def _error_only_for_client_error(self):
        if self.error is not None and self.type != int(UiEventType.CLIENT_ERROR):
            raise ValueError("`error` chỉ dùng cho sự kiện CLIENT_ERROR")
        return self


class UiEventBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    #  bao-CR-649: ứng dụng gửi, ở CẤP LÔ (một trang chỉ thuộc một app). Không khai = ERP v2 nên v2 không phải sửa;
    #  app cũ thumua gửi 2. Route của thumua được quy về route v2 ở service (`canonical_route`).
    app: int = int(UiApp.ERP_V2)
    events: list[UiEventIn] = Field(..., min_length=1, max_length=MAX_EVENTS_PER_BATCH)

    @field_validator("app")
    @classmethod
    def _app_known(cls, v: int) -> int:
        if v not in {int(a) for a in UiApp}:
            raise ValueError("Ứng dụng gửi sự kiện không hợp lệ")
        return v
