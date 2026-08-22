"""CR-068 — xuất Excel màn Yêu cầu mua hàng (YCMH/PYC).

Mỗi DÒNG HÀNG là một hàng Excel; cụm đầu phiếu lặp lại ở mọi dòng của cùng một phiếu.
Vì lặp nên cột "Tổng tiền" không cộng thẳng được — dùng cột "STT dòng" lọc `= 1` khi
cần cộng theo phiếu, hoặc cộng cột "Thành tiền" khi cần cộng theo sản phẩm.

Phiếu chưa có dòng hàng nào vẫn ra một hàng (cụm dòng để trống) để không biến mất khỏi file.
"""
from sqlalchemy.orm import Session

from app.core.export_xlsx import Col
from app.core.status_codes import PR_LINE_STATUS
from .model import PurchaseRequest, PurchaseRequestItem

# Nhãn tiếng Việt của trạng thái — khớp badge trên màn danh sách
STATUS_LABEL = {
    "draft": "Nháp", "submitted": "Chờ duyệt", "approved": "Đã duyệt",
    "dispatched": "Đã điều phối", "rejected": "Bị trả lại", "cancelled": "Đã từ chối",
    "processing": "Đang xử lý", "completed": "Hoàn thành",
}

# Cụm đầu phiếu — key trùng key cột trên bảng danh sách để lọc theo "cột đang hiển thị"
HEADER_COLS = [
    Col("code", "Mã PYC", width=18),
    Col("created_at", "Ngày tạo", "datetime", 18),
    Col("requester", "Người yêu cầu", width=22),
    Col("department", "Bộ phận", width=18),
    Col("need_date", "Ngày cần hàng", "date", 14),
    Col("total", "Tổng tiền", "money", 16),
    Col("is_urgent", "Gấp", "bool", 8),
    Col("status", "Trạng thái", width=16),
]

# Cụm dòng hàng — luôn xuất, không phụ thuộc cột đang hiện trên bảng
LINE_COLS = [
    Col("line_no", "STT dòng", "int", 9),
    Col("product_code", "Mã SP", width=16),
    Col("product_name", "Tên SP", width=32),
    Col("item_group", "Phân loại", width=16),
    Col("unit", "ĐVT", width=8),
    Col("qty", "Số lượng", "qty", 12),
    Col("price", "Đơn giá", "price", 14),
    Col("vat_pct", "% VAT", "int", 8),
    Col("amount", "Thành tiền", "money", 16),
    Col("warehouse", "Kho nhận", width=18),
    Col("required_date", "Ngày cần hàng (dòng)", "date", 16),
    Col("expected_date", "Dự kiến có hàng", "date", 15),
    Col("assignee_name", "NSTM phụ trách", width=22),
    Col("line_status", "Trạng thái dòng", width=16),
    Col("qty_ordered", "SL đã đặt", "qty", 12),
    Col("qty_received", "SL đã nhận", "qty", 12),
    Col("note", "Ghi chú dòng", width=26),
]

SHEET_TITLE = "Yeu cau mua hang"
FILE_NAME = "yeu-cau-mua-hang"


def _employee_names(db: Session, codes: set[str]) -> dict[str, str]:
    """Mã NV -> "NV0087 — Trần Minh Đức" cho cột NSTM phụ trách."""
    codes = {c for c in codes if c}
    if not codes:
        return {}
    from app.modules.employee.model import Employee
    rows = db.query(Employee.code, Employee.full_name).filter(Employee.code.in_(codes)).all()
    return {c: (f"{c} — {n}" if n else c) for c, n in rows}


def build_rows(db: Session, prs: list[PurchaseRequest]) -> list[dict]:
    """Bung mỗi phiếu thành các hàng theo dòng hàng, kèm cụm đầu phiếu lặp lại."""
    if not prs:
        return []
    pr_ids = [p.id for p in prs]
    items = (db.query(PurchaseRequestItem)
             .filter(PurchaseRequestItem.pr_id.in_(pr_ids))
             .order_by(PurchaseRequestItem.pr_id, PurchaseRequestItem.id).all())
    by_pr: dict[int, list[PurchaseRequestItem]] = {}
    for it in items:
        by_pr.setdefault(it.pr_id, []).append(it)
    names = _employee_names(db, {it.assignee for it in items})

    rows: list[dict] = []
    for pr in prs:
        lines = by_pr.get(pr.id, [])
        # Tổng tiền + ngày cần hàng tính y như màn danh sách (theo dòng, bỏ dòng đã hủy)
        total = round(sum(float(it.amount or 0) for it in lines), 2)
        need_dates = [it.required_date for it in lines
                      if it.required_date and it.line_status != "cancelled"]
        head = {
            "code": pr.code,
            "created_at": pr.created_at,
            "requester": pr.requester,
            "department": pr.department,
            "need_date": min(need_dates) if need_dates else (pr.need_date or ""),
            "total": total,
            "is_urgent": bool(pr.is_urgent),
            "status": STATUS_LABEL.get(pr.status, pr.status or ""),
        }
        if not lines:
            rows.append(dict(head))
            continue
        for i, it in enumerate(lines, start=1):
            rows.append(head | {
                "line_no": i,
                "product_code": it.product_code,
                "product_name": it.product_name,
                "item_group": it.item_group,
                "unit": it.unit,
                "qty": float(it.qty or 0),
                "price": float(it.price or 0),
                "vat_pct": float(it.vat_pct or 0),
                "amount": float(it.amount or 0),
                "warehouse": it.warehouse,
                "required_date": it.required_date,
                "expected_date": it.expected_date,
                "assignee_name": names.get(it.assignee, it.assignee or ""),
                # B-06: cột lưu MÃ, file xuất phải ra chữ cho người đọc
                "line_status": PR_LINE_STATUS.label_of(it.line_status, it.line_status or ""),
                "qty_ordered": float(it.qty_ordered or 0),
                "qty_received": float(it.qty_received or 0),
                "note": it.note,
            })
    return rows
