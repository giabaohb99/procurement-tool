from pydantic import BaseModel
from app.modules.employee.field_limits import Str10, Str20, Str50, Str255


class LineIn(BaseModel):
    """CR-066: dòng phiếu nhập tay được. payable_id = 0 -> dòng gõ tay (form trắng),
    không gắn khoản công nợ nào; lúc GỬI DUYỆT server mới bắt phải khớp công nợ."""

    payable_id: int = 0
    po_code: Str50 = ""
    invoice_no: Str50 = ""
    invoice_date: Str10 = ""
    amount: float = 0
    # CR-260 — phần đề nghị CẤN TRỪ tiền treo cấp NCC vào khoản nợ của dòng;
    # chỉ thực thi khi phiếu được DUYỆT (xem apply_line_offsets trong service).
    # bao-CR-511: `None` = người gửi KHÔNG nói gì về cấn trừ (màn cũ chưa có ô này) —
    # lúc SỬA phiếu thì giữ nguyên phần cấn trừ đang lưu, không hiểu thành 0.
    offset_amount: float | None = None


class PRequestCreate(BaseModel):
    request_date: Str10 = ""
    note: str = ""
    payment_method: Str20 = "transfer"   # transfer = Chuyển khoản | cash = Tiền mặt (CR-035)
    prepay: int = 0                    # CR-146: 1 = thanh toán TRƯỚC (đơn trả trước), 0 = thanh toán công nợ
    # CR-066 — form trắng: không đi từ màn Công nợ nên NCC/công ty/loại do người lập chọn.
    # Chỉ dùng khi các dòng KHÔNG gắn khoản nợ; đi từ Công nợ thì lấy theo khoản nợ.
    supplier_code: Str50 = ""
    company_id: int = 0
    source_type: Str20 = "goods"         # goods = Hàng hóa | shipping = Vận chuyển | import_cost = Chi phí thu mua (bao-CR-319 P5)
    lines: list[LineIn] = []   # có thể gồm nhiều NCC -> server tự tách mỗi NCC 1 phiếu
    # bao-CR-553 — Trưởng bộ phận in trên phiếu (id NHÂN SỰ, 0 = trưởng phòng của người lập)
    head_of_dept_id: int = 0
    head_of_dept: Str255 = ""


class PRequestUpdate(BaseModel):
    request_date: Str10 | None = None
    note: str | None = None
    payment_method: Str20 | None = None
    prepay: int | None = None          # CR-146
    head_of_dept_id: int | None = None          # bao-CR-553
    head_of_dept: Str255 | None = None
    # CR-149: {"content", "line_desc", "transfer"} — câu chữ bản in người dùng sửa.
    # Payload CHỈ chứa print_texts thì được sửa cả khi phiếu đã gửi duyệt / đã duyệt.
    print_texts: dict | None = None
    lines: list[LineIn] | None = None
