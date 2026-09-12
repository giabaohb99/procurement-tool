"""Schema của khối Báo cáo thực hiện (YCBG).

⚠️ Mọi trường chuỗi khai `max_length` KHỚP ĐÚNG `String(n)` ở `report_model.py`
— thiếu là chuỗi dài đi thẳng xuống MySQL và trả 500 thay vì 422 (duoc-CR-316).
Test khoá ở tầng schema vì test backend chạy SQLite, nơi VARCHAR không bị ép.
"""
from pydantic import BaseModel, Field, field_validator

from .report_constants import MAX_DEPENDS, REPORT_DOC_STATUS_LABELS


class ReportItemIn(BaseModel):
    """Thêm/sửa một nút dòng hàng."""

    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Tên nút không được để trống")
        return v


class ReportPhaseIn(BaseModel):
    """Thêm/sửa một giai đoạn."""

    name: str = Field(min_length=1, max_length=255)
    location: str = Field(default="", max_length=255)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Tên giai đoạn không được để trống")
        return v


class ReportDocIn(BaseModel):
    """Thêm một hồ sơ. `phase_id` bắt buộc trỏ vào giai đoạn của cùng phiếu."""

    title: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=4000)
    phase_id: int = Field(ge=1)
    item_id: int = Field(default=0, ge=0)          # 0 = Chung
    required: bool = True
    status: int = 0
    file_note: str = Field(default="", max_length=500)
    depends: list[int] = Field(default_factory=list, max_length=MAX_DEPENDS)

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Tiêu đề hồ sơ không được để trống")
        return v

    @field_validator("status")
    @classmethod
    def known_status(cls, v: int) -> int:
        if v not in REPORT_DOC_STATUS_LABELS:
            raise ValueError("Trạng thái hồ sơ không hợp lệ")
        return v


class ReportDocPatch(BaseModel):
    """Sửa một hồ sơ — chỉ gửi trường muốn đổi (nút ✓ chỉ gửi mỗi `status`)."""

    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    phase_id: int | None = Field(default=None, ge=1)
    item_id: int | None = Field(default=None, ge=0)
    required: bool | None = None
    status: int | None = None
    file_note: str | None = Field(default=None, max_length=500)
    depends: list[int] | None = Field(default=None, max_length=MAX_DEPENDS)

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Tiêu đề hồ sơ không được để trống")
        return v

    @field_validator("status")
    @classmethod
    def known_status(cls, v: int | None) -> int | None:
        if v is not None and v not in REPORT_DOC_STATUS_LABELS:
            raise ValueError("Trạng thái hồ sơ không hợp lệ")
        return v
