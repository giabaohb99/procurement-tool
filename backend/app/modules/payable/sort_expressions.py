"""Biểu thức SẮP XẾP tại server cho màn Công nợ phải trả (duoc-CR-744).

Trước đây `GET /api/payables` và `/export/xlsx` không đọc `sort_by`/`sort_dir` nên bấm tiêu đề
cột không đổi gì. Mỗi khóa dưới đây xếp theo ĐÚNG thứ giao diện đang hiện ở ô đó, trên CẢ TẬP
(đúng qua phân trang, và file Xuất Excel ra cùng thứ tự):

- Cột chữ / ngày: ô trống (hiện "—") luôn xuống CUỐI, cả chiều tăng lẫn giảm.
- Loại nợ, Trạng thái, Tuổi nợ: xếp theo hạng nghiệp vụ (bảng chữ ở giao diện hiện nhãn, nhưng
  DB lưu mã tắt nên xếp theo mã sẽ sai thứ tự đọc).
- Công ty: xếp theo TÊN (giao diện hiện tên; `company_id` thì ra thứ tự số vô nghĩa).
- Ngày hóa đơn: dùng lại `service.invoice_date_expr()` — cùng luật dò với bộ lọc.

Màn này không che cột nào theo quyền (khác Tiến độ báo giá), nên không có luật cấm xếp theo
cột bị che.
"""
from datetime import datetime, timedelta

from sqlalchemy import case, or_, select
from sqlalchemy.orm import Session

from app.modules.company.model import Company

from . import service
from .model import Payable

#  Khóa cần JOIN đợt giao / dòng hàng để dựng giá trị (xem `service.join_invoice_date`).
NEEDS_INVOICE_JOIN = frozenset({"invoice_date"})

#  Hạng của Loại nợ theo THỨ TỰ CHỮ giao diện hiện: Chi phí nhập khẩu < Hàng hóa < Vận chuyển.
_SOURCE_RANK = {"import_cost": 1, "goods": 2, "shipping": 3}
#  Hạng Trạng thái theo vòng đời: chờ thanh toán -> một phần -> đã thanh toán.
_STATUS_RANK = {service.ST_UNPAID: 1, service.ST_PARTIAL: 2, service.ST_PAID: 3}

#  Cột chữ / ngày thật trên bảng, xếp thẳng (ô trống xuống cuối).
_PLAIN_TEXT = {
    "supplier_code": Payable.supplier_code,
    "po_code": Payable.po_code,
    "invoice_no": Payable.invoice_no,
    "incur_date": Payable.incur_date,
    "due_date": Payable.due_date,
}
#  Cột số / giờ thật trên bảng, xếp thẳng.
_PLAIN_NUMBER = {
    #  Cột ID do `DataTable` tự thêm ở bìa trái (duoc-CR-738) gửi `sort_by=id`.
    "id": Payable.id,
    "created_at": Payable.created_at,
    "amount": Payable.amount,
    "vat": Payable.vat,
    "total": Payable.total,
    "paid_amount": Payable.paid_amount,
    "remaining": Payable.remaining,
}


def _aging_rank(today: datetime):
    """Hạng tuổi nợ 0..4 — cùng ngưỡng với `service.aging_bucket` và bộ lọc `aging`."""
    def days_ago(days: int) -> str:
        return (today - timedelta(days=days)).strftime("%Y-%m-%d")

    due = Payable.due_date
    return case(
        (or_(due == "", due.is_(None), due >= today.strftime("%Y-%m-%d")), 0),   # Chưa đến hạn
        (due >= days_ago(30), 1),    # 1-30
        (due >= days_ago(60), 2),    # 31-60
        (due >= days_ago(90), 3),    # 61-90
        else_=4,                     # >90
    )


def _text_expression(db: Session, key: str):
    """Biểu thức CHỮ của `key` (trống/NULL = ô hiện "—"); None nếu `key` không phải cột chữ."""
    if key in _PLAIN_TEXT:
        return _PLAIN_TEXT[key]
    if key == "supplier_name":
        #  Ô hiện tên, thiếu tên thì hiện mã NCC — xếp theo đúng chữ đó.
        return case((Payable.supplier_name != "", Payable.supplier_name), else_=Payable.supplier_code)
    if key == "company":
        return (select(Company.name).where(Company.id == Payable.company_id)
                .limit(1).scalar_subquery())
    if key == "invoice_date":
        return service.invoice_date_expr()
    return None


def build_order_by(db: Session, sort_by: str, sort_dir: str, today: datetime) -> list:
    """Danh sách mệnh đề ORDER BY cho cột `sort_by`; rỗng nếu khóa lạ (controller bỏ qua).

    Chỉ trả phần của cột được bấm — nơi gọi tự nối thứ tự mặc định phía sau làm khóa phụ.
    """
    descending = (sort_dir or "").strip().lower() == "desc"
    key = (sort_by or "").strip()

    text_expr = _text_expression(db, key)
    if text_expr is not None:
        blank_last = case((or_(text_expr.is_(None), text_expr == ""), 1), else_=0).asc()
        return [blank_last, text_expr.desc() if descending else text_expr.asc()]

    if key in _PLAIN_NUMBER:
        expr = _PLAIN_NUMBER[key]
    elif key == "source_type":
        expr = case(_SOURCE_RANK, value=Payable.source_type, else_=9)
    elif key == "status":
        expr = case(_STATUS_RANK, value=Payable.status, else_=9)
    elif key == "aging":
        expr = _aging_rank(today)
    else:
        return []
    return [expr.desc() if descending else expr.asc()]
