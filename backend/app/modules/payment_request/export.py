"""bao-CR-525 — xuất Excel Yêu cầu thanh toán THEO DÒNG CHI TIẾT.

Một hàng = một dòng của phiếu (PO / số hóa đơn / số tiền đề nghị); thông tin phiếu (mã, ngày,
công ty, NCC, trạng thái…) LẶP LẠI ở mỗi hàng để lọc / pivot thẳng trong Excel — đại ca chốt
30/09/2026. Phiếu lấy đúng bộ lọc + phạm vi dữ liệu của màn danh sách (`_list_query` bên
controller đã qua `apply_scope`). Trạng thái / loại / hình thức xuất NHÃN như màn hình; tiền giữ
KIỂU SỐ, không kèm dòng tổng (quy ước CR-068, giống tệp Công nợ).

Chỉ đọc cột đã lưu trên dòng phiếu — không dò lại công nợ từng dòng như màn chi tiết (`_line`),
vì tệp xuất không phân trang: dò công nợ cho vài nghìn dòng là vài nghìn truy vấn.
"""
from sqlalchemy.orm import Session

from app.core.audit import resolve_actor
from app.core.export_xlsx import Col
from app.modules.company.model import Company

from . import service
from .model import PaymentRequest, PaymentRequestLine

FILE_NAME = "yeu-cau-thanh-toan-chi-tiet"
SHEET_TITLE = "YCTT theo dong"

_SOURCE_LABEL = {"goods": "Hàng hóa", "shipping": "Vận chuyển", "import_cost": "Chi phí thu mua"}
_METHOD_LABEL = {"transfer": "Chuyển khoản", "cash": "Tiền mặt"}

COLS = [
    Col("code", "Mã phiếu", width=14),
    Col("request_date", "Ngày đề nghị", "date", 13),
    Col("status", "Trạng thái", width=13),
    Col("company", "Công ty", width=26),
    Col("supplier_code", "Mã NCC", width=14),
    Col("supplier_name", "Nhà cung cấp", width=30),
    Col("source_type", "Loại", width=14),
    Col("payment_method", "Hình thức", width=13),
    Col("prepay", "Trả trước", width=10),
    Col("po_code", "PO", width=16),
    Col("misa_code", "Mã đơn Misa", width=15),
    Col("invoice_no", "Số hóa đơn", width=16),
    Col("invoice_date", "Ngày hóa đơn", "date", 13),
    Col("amount", "Số tiền đề nghị", "money", 16),
    Col("offset_amount", "Cấn trừ tiền treo", "money", 16),
    Col("request_total", "Tổng tiền phiếu", "money", 16),
    Col("created_by", "Người lập", width=22),
    Col("note", "Ghi chú phiếu", width=34),
]


def load_lines(db: Session, requests: list[PaymentRequest]) -> list[tuple[PaymentRequest, PaymentRequestLine]]:
    """Dòng của các phiếu, giữ thứ tự phiếu như danh sách rồi theo thứ tự dòng trong phiếu.
    Gom một truy vấn (chia khúc 1000 id cho khỏi vượt trần tham số của MySQL)."""
    by_req: dict[int, list[PaymentRequestLine]] = {}
    ids = [r.id for r in requests]
    for i in range(0, len(ids), 1000):
        chunk = ids[i:i + 1000]
        for ln in (db.query(PaymentRequestLine).filter(PaymentRequestLine.request_id.in_(chunk))
                   .order_by(PaymentRequestLine.id).all()):
            by_req.setdefault(ln.request_id, []).append(ln)
    return [(r, ln) for r in requests for ln in by_req.get(r.id, [])]


def build_rows(db: Session, pairs: list[tuple[PaymentRequest, PaymentRequestLine]]) -> list[dict]:
    company_name = dict(db.query(Company.id, Company.name).all())
    misa_by_po = service.misa_by_po_code(db, [ln.po_code for _, ln in pairs])
    actor: dict[int, str] = {}
    rows = []
    for req, ln in pairs:
        if req.created_by not in actor:
            actor[req.created_by] = resolve_actor(db, req.created_by)
        rows.append({
            "code": req.code,
            "request_date": req.request_date,
            "status": service.STATUS_LABELS.get(req.status, req.status),
            "company": company_name.get(req.company_id, ""),
            "supplier_code": req.supplier_code,
            "supplier_name": req.supplier_name,
            "source_type": _SOURCE_LABEL.get(req.source_type, req.source_type),
            "payment_method": _METHOD_LABEL.get(req.payment_method, req.payment_method),
            "prepay": "Có" if req.prepay else "",
            "po_code": ln.po_code,
            "misa_code": misa_by_po.get((ln.po_code or "").strip(), ""),
            "invoice_no": ln.invoice_no,
            "invoice_date": ln.invoice_date,
            "amount": ln.amount,
            "offset_amount": ln.offset_amount,
            "request_total": req.total,
            "created_by": actor[req.created_by],
            "note": req.note,
        })
    return rows
