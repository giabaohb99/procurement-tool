import json

from pydantic import BaseModel, field_validator


class PurchaseHistoryOut(BaseModel):
    """Chỉ đọc — bảng snapshot không có API tạo/sửa/xóa."""

    id: int
    # Dòng DỮ LIỆU CŨ (nhập từ file lịch sử) không có ĐMH nên 2 cột này rỗng.
    po_item_id: int | None = None
    source: str = "system"
    po_id: int = 0
    po_code: str = ""
    product_code: str = ""
    product_name: str = ""
    supplier_code: str = ""
    supplier_name: str = ""
    company_id: int = 0
    company_name: str = ""
    order_date: str = ""
    unit: str = ""
    qty_order: float = 0
    price: float = 0
    vat: float = 0
    amount: float = 0
    completed_at: str = ""
    # Phần "Thông tin chung" + dòng hàng còn lại (DB lưu chuỗi JSON). Trả ra dạng object để
    # popup "Lịch sử mua hàng gần nhất" điền luôn Chi tiết dòng (tên trên hóa đơn, TSKT,
    # mã/tên HH, phân loại, kho nhận, ghi chú). Dòng legacy không có ĐMH → {}.
    extra: dict = {}

    @field_validator("extra", mode="before")
    @classmethod
    def _parse_extra(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v or "{}")
            except ValueError:      # dữ liệu cũ lỡ ghi chuỗi không phải JSON thì bỏ qua
                return {}
        return v or {}

    model_config = {"from_attributes": True}
