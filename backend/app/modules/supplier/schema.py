from pydantic import BaseModel, Field, field_validator

from app.core.status_codes import SUPPLIER_LEGAL_TYPE


class SupplierBase(BaseModel):
    code: str = ""
    name: str
    # B-03: MÃ tiếng Anh (`SUPPLIER_LEGAL_TYPE`). Rỗng = chưa chọn, vẫn hợp lệ.
    legal_type: str = ""
    tax_code: str = ""
    address: str = ""
    supplier_type: str = "goods"  # goods | transport
    contact_person: str = ""
    phone: str = ""
    payment_terms: str = ""
    bank_account: str = ""
    bank_name: str = ""
    bank_account_name: str = ""
    # VAT mặc định của NCC lưu dạng TỈ LỆ (0.08 = 8%), KHÁC vat/vat_pct cấp dòng (lưu %).
    # Chặn dưới 1 = dưới 100% (CR-058). Trang chi tiết NCC nhập theo % rồi chia 100 trước khi gửi.
    vat: float = Field(0.08, ge=0, lt=1)
    is_active: bool = True


class SupplierCreate(SupplierBase):
    # Chặn ở CẢ Create lẫn Update — xem ghi chú cùng ý ở `employee/schema.py`.
    @field_validator("legal_type")
    @classmethod
    def _check_legal_type(cls, v: str) -> str:
        return SUPPLIER_LEGAL_TYPE.validate(v)


class SupplierUpdate(BaseModel):
    name: str | None = None
    legal_type: str | None = None
    tax_code: str | None = None
    address: str | None = None
    supplier_type: str | None = None
    contact_person: str | None = None
    phone: str | None = None
    payment_terms: str | None = None
    bank_account: str | None = None
    bank_name: str | None = None
    bank_account_name: str | None = None
    vat: float | None = Field(None, ge=0, lt=1)   # tỉ lệ, dưới 1 = dưới 100% (CR-058)
    is_active: bool | None = None

    @field_validator("legal_type")
    @classmethod
    def _check_legal_type(cls, v: str | None) -> str | None:
        return SUPPLIER_LEGAL_TYPE.validate(v)


class SupplierOut(SupplierBase):
    id: int
    # B-03: nhãn tiếng Việt gửi kèm; đọc từ `Supplier.legal_type_label`.
    legal_type_label: str = ""
    model_config = {"from_attributes": True}
