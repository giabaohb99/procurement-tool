from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.status_codes import SUPPLIER_LEGAL_TYPE
from app.modules.employee.field_limits import Str20, Str25, Str30, Str50, Str100, Str255


class SupplierBase(BaseModel):
    code: Str50 = ""
    name: Str255
    # B-03: MÃ tiếng Anh (`SUPPLIER_LEGAL_TYPE`). Rỗng = chưa chọn, vẫn hợp lệ.
    legal_type: Str30 = ""
    tax_code: Str25 = ""
    address: str = ""
    supplier_type: Str20 = "goods"  # goods | transport
    contact_person: Str100 = ""
    phone: Str30 = ""
    payment_terms: Str255 = ""
    bank_account: Str50 = ""
    bank_name: Str255 = ""
    bank_account_name: Str255 = ""
    # VAT mặc định của NCC lưu dạng TỈ LỆ (0.08 = 8%), KHÁC vat/vat_pct cấp dòng (lưu %).
    # Chặn dưới 1 = dưới 100% (CR-058). Trang chi tiết NCC nhập theo % rồi chia 100 trước khi gửi.
    vat: float = Field(0.08, ge=0, lt=1)
    is_active: bool = True
    # bao-CR-321 — điều khoản in trên ĐMH theo NCC; 0 / rỗng = dùng mặc định của bản in
    inspection_days: int = Field(0, ge=0, le=365)
    return_days: int = Field(0, ge=0, le=365)
    invoice_deadline: str = Field("", max_length=255)


class SupplierCreate(SupplierBase):
    # Chặn ở CẢ Create lẫn Update — xem ghi chú cùng ý ở `employee/schema.py`.
    @field_validator("legal_type")
    @classmethod
    def _check_legal_type(cls, v: str) -> str:
        return SUPPLIER_LEGAL_TYPE.validate(v)


class SupplierUpdate(BaseModel):
    name: Str255 | None = None
    legal_type: Str30 | None = None
    tax_code: Str25 | None = None
    address: str | None = None
    supplier_type: Str20 | None = None
    contact_person: Str100 | None = None
    phone: Str30 | None = None
    payment_terms: Str255 | None = None
    bank_account: Str50 | None = None
    bank_name: Str255 | None = None
    bank_account_name: Str255 | None = None
    vat: float | None = Field(None, ge=0, lt=1)   # tỉ lệ, dưới 1 = dưới 100% (CR-058)
    is_active: bool | None = None
    inspection_days: int | None = Field(None, ge=0, le=365)
    return_days: int | None = Field(None, ge=0, le=365)
    invoice_deadline: str | None = Field(None, max_length=255)

    @field_validator("legal_type")
    @classmethod
    def _check_legal_type(cls, v: str | None) -> str | None:
        return SUPPLIER_LEGAL_TYPE.validate(v)


class SupplierOut(SupplierBase):
    id: int
    # B-03: nhãn tiếng Việt gửi kèm; đọc từ `Supplier.legal_type_label`.
    legal_type_label: str = ""
    updated_at: datetime | None = None   # bao-CR-294 — cột "Ngày cập nhật" ở màn danh sách
    model_config = {"from_attributes": True}
