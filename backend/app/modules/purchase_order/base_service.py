"""Hằng và hàm nền của ĐMH — mọi tệp nghiệp vụ con dùng chung, KHÔNG import tệp anh em (bao-CR-715)."""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.supplier.model import Supplier

from .model import PODelivery, POItem, PurchaseOrder


def normalize_rate(value) -> float:
    """Đọc một ô tỷ giá thành số nhân được.

    bao-CR-319. Dòng cũ (trước khi có cột) và dòng VNĐ đều để trống hoặc 0 — phải đọc
    thành 1, vì nhân với 0 sẽ biến cả đơn hàng thành 0 đồng mà không báo lỗi ở đâu cả.
    Tách riêng khỏi `rate_of` để chỗ nào đọc thẳng cột (truy vấn gom cả trang) vẫn dùng
    chung đúng một luật, không phải chép lại.
    """
    return float(value or 0) or 1.0


def rate_of(obj) -> float:
    """Tỷ giá dùng để quy đổi về đồng tiền hạch toán, đọc từ một dòng hàng."""
    return normalize_rate(getattr(obj, "exchange_rate", 0))


def _pdate(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date() if s else None
    except ValueError:
        return None


def _days(a: str, b: str) -> int:
    """Số ngày = (a − b). a,b là 'YYYY-MM-DD'. Trả 0 nếu thiếu."""
    da, db_ = _pdate(a), _pdate(b)
    return (da - db_).days if da and db_ else 0

# order_date nằm trong whitelist để BỘ LỌC ĐIỀU KIỆN lọc theo ngày (order_date__between/gte…).
# Lọc khoảng kiểu cũ (order_date_from/_to của thanh lọc cơ bản) vẫn do apply_range_filters lo.
FILTERABLE = ["code", "status", "supplier_code", "pr_code", "misa_code", "nspt", "is_urgent",
              "department", "document_status", "order_date", "order_type",
              "nspt_id", "department_id", "company_id"]
ENTITY = "purchase_order"

# ── Mã trạng thái của cụm ĐMH (B-06) ─────────────────────────────────────────────────────
# Đặt tên cho mã thay vì gõ chuỗi trần ở từng chỗ: `_recalc` ghi bốn cột này, còn hơn chục chỗ
# khác trong ba phân hệ đọc chúng. Gõ thẳng chuỗi là lần sau đổi mã sẽ sót đúng một chỗ, mà chỗ
# sót đó im lặng cho ra trạng thái sai chứ không nổ.
DELIV_PENDING = "pending"
DELIV_SHORT = "short"
DELIV_DEFECT = "defect"
DELIV_RECEIVED = "received"

LINE_NOT_DELIVERED = "not_delivered"
LINE_PARTIAL = "partial"
LINE_FULL = "full"

# Tiến độ dòng — xem thêm PROGRESS_ORDER / PROGRESS_EXCEPTIONS ở giữa tệp.
PROG_NOT_ORDERED = "not_ordered"
PROG_ORDERED = "ordered"
PROG_RECEIVED = "received"
PROG_DOC_PENDING = "doc_pending"
PROG_DOC_SENT = "doc_sent"
PROG_COMPLETED = "completed"
PROG_PAUSED = "paused"
PROG_CANCELLED = "cancelled"


def get_po(db: Session, pid: int) -> PurchaseOrder:
    """Nạp đơn theo id. ai-CR-176: đơn đã xóa mềm coi như không có (404)."""
    obj = db.get(PurchaseOrder, pid)
    if not obj or obj.is_deleted:
        raise HTTPException(404, "Không tìm thấy đơn mua hàng")
    return obj


def items_of(db: Session, po_id: int):
    return db.query(POItem).filter(POItem.po_id == po_id).order_by(POItem.id.asc()).all()


def deliveries_of(db: Session, item_id: int):
    return (db.query(PODelivery).filter(PODelivery.po_item_id == item_id)
            .order_by(PODelivery.id.asc()).all())


def _supplier_map(db: Session) -> dict:
    return {s.code: s for s in db.query(Supplier).all()}


def sync_urgent_group(db: Session, pr_code: str, is_urgent: bool, *, exclude_po_id: int | None = None) -> None:
    """Đồng bộ cờ Đơn gấp cho cả NHÓM: YCMH + mọi ĐMH cùng pr_code = is_urgent.

    Dùng UPDATE trực tiếp (không đi qua endpoint) nên không gây vòng lặp sync.
    exclude_po_id: bỏ qua chính ĐMH vừa lưu (đã set giá trị rồi)."""
    if not pr_code:
        return
    from app.modules.purchase_request.model import PurchaseRequest
    q = db.query(PurchaseOrder).filter(PurchaseOrder.pr_code == pr_code)
    if exclude_po_id:
        q = q.filter(PurchaseOrder.id != exclude_po_id)
    q.update({PurchaseOrder.is_urgent: is_urgent}, synchronize_session=False)
    db.query(PurchaseRequest).filter(PurchaseRequest.code == pr_code).update(
        {PurchaseRequest.is_urgent: is_urgent}, synchronize_session=False)
    db.commit()


def _sync_pr(db: Session, pr_code: str) -> None:
    """Đồng bộ tiến độ dòng ĐMH → dòng YCMH nguồn (khớp product_code) + suy lại trạng thái phiếu."""
    if not pr_code:
        return
    try:
        from app.modules.purchase_request import service as pr_service
        pr_service.sync_from_purchase_orders(db, pr_code)
    except Exception:
        pass  # sync không được phép làm hỏng thao tác chính
