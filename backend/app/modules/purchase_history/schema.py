from pydantic import BaseModel


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

    model_config = {"from_attributes": True}
