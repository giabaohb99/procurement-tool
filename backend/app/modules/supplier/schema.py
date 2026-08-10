from pydantic import BaseModel, Field


class SupplierBase(BaseModel):
    code: str = ""
    name: str
    legal_type: str = ""          # Công ty | Cá nhân | Hợp danh | Hộ kinh doanh
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
    pass


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


class SupplierOut(SupplierBase):
    id: int
    model_config = {"from_attributes": True}
