"""CR-068 — xuất Excel màn Đơn mua hàng (ĐMH/PO).

Bố cục cột dùng LẠI đúng bộ cột của màn Tiến độ mua hàng (theo yêu cầu khách): mỗi hàng Excel là
một LẦN GIAO của một dòng hàng (dòng chưa có lần giao nào vẫn ra một hàng, phần giao để trống),
kèm cụm đầu đơn của bảng Đơn mua hàng lặp lại ở mọi hàng.

Số liệu dòng lấy từ `purchase_progress.export.row_values` — cùng một chỗ tính "Thành tiền ĐH",
"Thành tiền nhận" và các cột chênh lệch với màn Tiến độ, nên hai file không bao giờ lệch nhau.

Hai cột tiền dễ nhầm:
- "Tiền hàng" (đầu đơn) = tổng giá trị ĐẶT của cả đơn, tính một lần trên dòng hàng nên KHÔNG bị
  nhân lên theo số lần giao. Lọc "STT dòng = 1" rồi cộng cột này sẽ ra đúng tổng các đơn.
- "Thành tiền nhận" (dòng) = theo SL thực nhận của lần giao đó — đây mới là số ghi công nợ.
"""
from sqlalchemy.orm import Session

from app.core.export_xlsx import Col
from app.core.status_codes import PO_DOCUMENT_STATUS, PO_ITEM_LINE_STATUS
from app.modules.company.model import Company
from app.modules.purchase_progress import export as progress_ex
from .model import PODelivery, POItem, PurchaseOrder

STATUS_LABEL = {
    "draft": "Nháp", "submitted": "Chờ duyệt", "approved": "Đã duyệt",
    "partial": "Đã nhận một phần", "received": "Đã nhận đủ", "completed": "Hoàn thành",
    "rejected": "Bị trả lại", "cancelled": "Đã từ chối", "processing": "Đang xử lý",
}

# Hồ sơ chứng từ (B-06): cột lưu MÃ, nhãn lấy từ bộ mã dùng chung. Trước B-06 cột lưu chữ tiếng
# Việt viết thường và bảng dịch tay ở đây tồn tại chỉ để viết hoa lại — nay hết việc.
DOC_STATUS_LABEL = dict(PO_DOCUMENT_STATUS.labels)

# Cụm đầu đơn — key trùng cột trên bảng danh sách ĐMH, người dùng ẩn/hiện cột nào thì file theo cột đó
HEADER_COLS = [
    Col("code", "Mã PO", width=18),
    Col("misa_code", "Mã MISA", width=16),
    Col("created_at", "Ngày đặt", "datetime", 18),
    Col("note", "Ghi chú", width=26),
    Col("supplier_code", "Nhà cung cấp", width=26),
    Col("pr_code", "Mã PYC", width=18),
    Col("amount", "Tiền hàng", "money", 16),
    Col("is_urgent", "Gấp", "bool", 8),
    Col("document_status", "Hồ sơ chứng từ", width=18),
    Col("status", "Trạng thái", width=16),
]

# Cụm dòng — bê nguyên bộ cột màn Tiến độ mua hàng, bỏ những cột đã nằm ở cụm đầu đơn
# (STT/Mã ĐMH/Mã MISA/Mã PYC/Mã NCC/Hồ sơ CT) và đổi tên key `amount` -> `recv_amount`
# để không đụng cột "Tiền hàng" của đầu đơn. Ba cột cuối là phần riêng của màn ĐMH.
_SKIP_FROM_PROGRESS = {"stt", "po_code", "misa_code", "pr_code", "survey_code",
                       "supplier_code", "document_status"}
_RENAME = {
    "amount": Col("recv_amount", "Thành tiền nhận", "money", 16),
    # Đầu đơn đã có cột "Nhà cung cấp" (mã), đổi nhãn cột tên cho khỏi hai cột trùng tên
    "supplier_name": Col("supplier_name", "Tên NCC", width=28),
}

LINE_COLS = (
    [Col("line_no", "STT dòng", "int", 9)]
    + [_RENAME.get(c.key, c) for c in progress_ex.COLS if c.key not in _SKIP_FROM_PROGRESS]
    + [
        Col("qty_remaining", "SL còn lại", "qty", 12),
        Col("line_status", "Trạng thái dòng", width=16),
        Col("line_note", "Ghi chú dòng", width=26),
    ]
)

# Cột chỉ dành cho người có `supplier.read` — cùng luật che của màn Tiến độ (trừ "Mã NCC" vì cột
# "Nhà cung cấp" ở đầu đơn vốn đã là cột mặc định của bảng ĐMH)
SUPPLIER_ONLY = progress_ex.SUPPLIER_ONLY - {"supplier_code"}

SHEET_TITLE = "Don mua hang"
FILE_NAME = "don-mua-hang"


def line_columns(show_supplier: bool) -> list[Col]:
    return list(LINE_COLS) if show_supplier else [c for c in LINE_COLS if c.key not in SUPPLIER_ONLY]


def build_rows(db: Session, pos: list[PurchaseOrder], show_supplier: bool = True) -> list[dict]:
    """Bung mỗi đơn thành các hàng theo LẦN GIAO (giống màn Tiến độ), kèm cụm đầu đơn lặp lại."""
    if not pos:
        return []
    po_ids = [p.id for p in pos]
    pairs = (db.query(POItem, PODelivery)
             .outerjoin(PODelivery, PODelivery.po_item_id == POItem.id)
             .filter(POItem.po_id.in_(po_ids))
             .order_by(POItem.po_id, POItem.id, PODelivery.delivery_no)
             .all())
    by_po: dict[int, list[tuple[POItem, PODelivery | None]]] = {}
    for it, dl in pairs:
        by_po.setdefault(it.po_id, []).append((it, dl))
    company_name = {c.id: c.name for c in db.query(Company).all()}

    rows: list[dict] = []
    for po in pos:
        lines = by_po.get(po.id, [])
        # Tiền hàng đầu đơn: cộng theo DÒNG HÀNG (mỗi dòng một lần), không cộng theo lần giao
        seen: set[int] = set()
        order_amount = 0.0
        for it, _ in lines:
            if it.id in seen:
                continue
            seen.add(it.id)
            order_amount += round(float(it.qty_order or 0) * float(it.price or 0)
                                  * (1 + float(it.vat or 0) / 100), 2)
        head = {
            "code": po.code,
            "misa_code": po.misa_code,
            "created_at": po.created_at,
            "note": po.note,
            # Cột "Nhà cung cấp" trên bảng hiện mã, thiếu mã mới rơi về tên
            "supplier_code": po.supplier_code or po.supplier_name or "",
            "pr_code": po.pr_code,
            "amount": round(order_amount, 2),
            "is_urgent": bool(po.is_urgent),
            "document_status": DOC_STATUS_LABEL.get(po.document_status, po.document_status or ""),
            "status": STATUS_LABEL.get(po.status, po.status or ""),
        }
        if not lines:
            rows.append(dict(head))
            continue
        for i, (it, dl) in enumerate(lines, start=1):
            # B-06: cột trạng thái lưu MÃ, file xuất hiện chữ (`head` đã dịch sẵn phần đầu đơn)
            r = progress_ex.translate_codes(progress_ex.row_values(po, it, dl, show_supplier))
            r["recv_amount"] = r.pop("amount", 0)
            r["company"] = company_name.get(po.company_id, "")
            r["line_no"] = i
            r["qty_remaining"] = float(it.qty_remaining or 0)
            r["line_note"] = it.note
            # `head` đè lên `r` ở các key trùng để giữ nhãn tiếng Việt của cụm đầu đơn
            rows.append(r | head)
    return rows
