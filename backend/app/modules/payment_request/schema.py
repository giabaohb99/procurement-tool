from pydantic import BaseModel


class LineIn(BaseModel):
    """CR-066: dòng phiếu nhập tay được. payable_id = 0 -> dòng gõ tay (form trắng),
    không gắn khoản công nợ nào; lúc GỬI DUYỆT server mới bắt phải khớp công nợ."""

    payable_id: int = 0
    po_code: str = ""
    invoice_no: str = ""
    invoice_date: str = ""
    amount: float = 0


class PRequestCreate(BaseModel):
    request_date: str = ""
    note: str = ""
    payment_method: str = "transfer"   # transfer = Chuyển khoản | cash = Tiền mặt (CR-035)
    # CR-066 — form trắng: không đi từ màn Công nợ nên NCC/công ty/loại do người lập chọn.
    # Chỉ dùng khi các dòng KHÔNG gắn khoản nợ; đi từ Công nợ thì lấy theo khoản nợ.
    supplier_code: str = ""
    company_id: int = 0
    source_type: str = "goods"         # goods = Hàng hóa | shipping = Vận chuyển
    lines: list[LineIn] = []   # có thể gồm nhiều NCC -> server tự tách mỗi NCC 1 phiếu


class PRequestUpdate(BaseModel):
    request_date: str | None = None
    note: str | None = None
    payment_method: str | None = None
    lines: list[LineIn] | None = None
