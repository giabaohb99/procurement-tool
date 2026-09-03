"""Ticket #16 — xuất Excel màn Công nợ phải trả.

Một hàng = một khoản nợ, đúng bộ lọc + phạm vi dữ liệu người xem (`_filtered` bên
controller đã đi qua `apply_scope`); có tick chọn thì chỉ xuất các khoản được tick.
Trạng thái / loại nợ / tuổi nợ xuất NHÃN ĐẦY ĐỦ như màn hình (DB lưu mã tắt);
tiền giữ nguyên KIỂU SỐ để cộng / pivot ngay trong Excel — không kèm dòng tổng
(quy ước CR-068, khách chốt "tổng để trần").
"""
from sqlalchemy.orm import Session

from app.core.export_xlsx import Col
from app.modules.company.model import Company

from . import service
from .model import Payable

FILE_NAME = "cong-no-phai-tra"
SHEET_TITLE = "Cong no phai tra"

# Nhãn đầy đủ — trạng thái lấy từ bộ mã chuẩn (status_codes.PAYABLE_STATUS, xem B-06)
_SOURCE_LABEL = {"goods": "Hàng hóa", "shipping": "Vận chuyển"}

# Key và nhãn khớp bảng trên màn hình (cột tick chọn `sel` không có mặt trong file)
COLS = [
    Col("supplier_name", "Nhà cung cấp", width=28),
    Col("supplier_code", "Mã NCC", width=14),
    Col("source_type", "Loại", width=12),
    Col("company", "Công ty", width=26),
    Col("po_code", "PO", width=18),
    Col("invoice_no", "Số hóa đơn", width=16),
    Col("created_at", "Ngày phát sinh", "datetime", 17),
    Col("due_date", "Hạn trả", "date", 12),
    Col("aging", "Tuổi nợ", width=13),
    Col("total", "Tổng nợ", "money", 16),
    Col("paid_amount", "Đã trả", "money", 16),
    Col("remaining", "Còn lại", "money", 16),
    Col("status", "Trạng thái", width=18),
]


def build_rows(db: Session, items: list[Payable]) -> list[dict]:
    company_name = dict(db.query(Company.id, Company.name).all())
    rows = []
    for p in items:
        aging = service.aging_bucket(p.due_date)
        rows.append({
            "supplier_name": p.supplier_name or p.supplier_code,
            "supplier_code": p.supplier_code,
            "source_type": _SOURCE_LABEL.get(p.source_type, p.source_type),
            "company": company_name.get(p.company_id, ""),
            "po_code": p.po_code,
            "invoice_no": p.invoice_no,
            # như màn hình: khoản không có created_at rơi về ngày phát sinh nhập tay
            "created_at": p.created_at or p.incur_date,
            "due_date": p.due_date,
            "aging": aging if aging == "Chưa đến hạn" else f"{aging} ngày",
            "total": p.total,
            "paid_amount": p.paid_amount,
            "remaining": p.remaining,
            "status": service.status_label(p.status),
        })
    return rows
