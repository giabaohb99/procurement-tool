"""ĐMH — tiến độ dòng hàng: thứ tự bước, điều kiện từng bước, tự nhảy bước, đặt tiến độ tay (bao-CR-715 tách từ
service.py).
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.status_codes import PO_PROGRESS_STATUS
from app.core.text_limits import column_limit, ensure_max_length

from .model import POItem, PurchaseOrder
from .base_service import (ENTITY, PROG_CANCELLED, PROG_COMPLETED, PROG_NOT_ORDERED, PROG_PAUSED, _sync_pr,
                           deliveries_of, get_po)


# ───────────────────────── Máy trạng thái TIẾN ĐỘ của DÒNG ĐMH (progress_status) ─────────────────────────
# Luồng chính tuần tự; `paused`/`cancelled` là ngoại lệ bấm nút, cần lý do.
# Task 8: tách `doc_pending` (có số hóa đơn) → `doc_sent` (có ngày giao chứng từ).
#
# B-06: hai list này KHÔNG còn gõ tay — sinh từ PO_PROGRESS_STATUS để không thể lệch với bộ mã.
# `ordered_values` đã loại sẵn hai mã `is_exception`, nên `PROGRESS_ORDER.index(...)` vẫn cho đúng
# số bước như trước; `PROGRESS_EXCEPTIONS` chính là phần bị loại ra đó.
PROGRESS_ORDER = list(PO_PROGRESS_STATUS.ordered_values)
PROGRESS_EXCEPTIONS = [c.value for c in PO_PROGRESS_STATUS.codes if c.is_exception]


def is_line_paid(db: Session, po: PurchaseOrder, item: POItem) -> bool:
    """Điều kiện 'đã thanh toán dòng' = MỌI khoản nợ HÀNG (goods, không tính vận chuyển)
    của các lần giao đã nhận của dòng đều đã trả đủ (còn lại ≈ 0)."""
    from app.modules.payable.model import Payable
    ref_ids = [d.id for d in deliveries_of(db, item.id) if float(d.received_qty or 0) > 0]
    if not ref_ids:
        return False   # chưa nhận hàng thì chưa thể 'đã trả đủ'
    pays = (db.query(Payable)
            .filter(Payable.source_type == "goods", Payable.ref_type == "delivery",
                    Payable.ref_id.in_(ref_ids)).all())
    if not pays:
        return False
    return all(float(p.remaining or 0) <= 0.01 for p in pays)


# Tên trường hiển thị còn thiếu cho từng bước tiến độ (index theo PROGRESS_ORDER)
_STEP_MISSING = {
    1: "Mã đơn MISA (trên phiếu)",
    2: "Có nhận hàng (số lượng nhận > 0)",
    3: "Số hóa đơn",
    4: "Ngày giao chứng từ cho KT",
    5: "Thanh toán cho dòng (NCC sản phẩm)",
}


def _step_ok(db: Session, po: PurchaseOrder, item: POItem, ti: int) -> bool:
    """Điều kiện ĐỦ để dòng đạt bước index ti (dùng chung cho auto-advance + validate_progress)."""
    if ti <= 0:
        return True
    if ti == 1:
        return bool((po.misa_code or "").strip())
    if ti == 2:
        return float(item.qty_received or 0) > 0
    if ti == 3:   # Chưa gửi ĐMH cho KT — đã có số hóa đơn (ở lần giao hoặc ở dòng sản phẩm)
        has_deliv_inv = any(bool((d.invoice_no or "").strip()) for d in deliveries_of(db, item.id))
        return has_deliv_inv or bool((item.invoice_no or "").strip())
    if ti == 4:   # Đã gửi ĐMH cho KT — đã có ngày giao chứng từ
        return bool((item.document_delivery_date or "").strip())
    if ti == 5:   # Hoàn thành — đã thanh toán dòng
        return is_line_paid(db, po, item)
    return False


def validate_progress(db: Session, po: PurchaseOrder, item: POItem, target: str):
    """Trả (ok, missing[]): missing là TÊN TRƯỜNG hiển thị còn thiếu. Điều kiện CỘNG DỒN theo bước."""
    if target not in PROGRESS_ORDER:
        return True, []
    ti = PROGRESS_ORDER.index(target)
    missing = [_STEP_MISSING[s] for s in range(1, ti + 1) if not _step_ok(db, po, item, s)]
    return (len(missing) == 0), missing


def highest_satisfied_step(db: Session, po: PurchaseOrder, item: POItem) -> int:
    """Bước cao nhất LIÊN TỤC thỏa (dừng ở bước hụt đầu tiên — gate cộng dồn)."""
    ti = 0
    for s in range(1, len(PROGRESS_ORDER)):
        if _step_ok(db, po, item, s):
            ti = s
        else:
            break
    return ti


def auto_advance_line(db: Session, po: PurchaseOrder, item: POItem) -> bool:
    """Chỉ TIẾN (forward-only). Bỏ qua dòng ở điểm cuối/tạm ngưng. Trả True nếu có đổi."""
    if item.progress_status in (PROG_COMPLETED, PROG_CANCELLED, PROG_PAUSED):
        return False
    cur = PROGRESS_ORDER.index(item.progress_status) if item.progress_status in PROGRESS_ORDER else 0
    target = highest_satisfied_step(db, po, item)
    if target > cur:
        item.progress_status = PROGRESS_ORDER[target]
        if item.progress_status == PROG_COMPLETED:
            # Chốt LỊCH SỬ MUA HÀNG: đây là chỗ DUY NHẤT dòng vào `completed`
            # (set_item_progress chặn set tay các trạng thái trong PROGRESS_ORDER), và hàm này
            # bỏ qua dòng đã ở điểm cuối → mỗi dòng chỉ ghi snapshot đúng 1 lần.
            # Chỉ add(), caller commit cùng transaction với việc đổi progress_status.
            from app.modules.purchase_history.service import snapshot_line_safe
            snapshot_line_safe(db, po, item)
        return True
    return False


def apply_auto_progress(db: Session, po: PurchaseOrder, user_id: int | None = None) -> bool:
    """Duyệt mọi dòng → auto tiến; nếu có đổi thì commit + đồng bộ YCMH. Trả True nếu có đổi."""
    changed = False
    for item in db.query(POItem).filter(POItem.po_id == po.id).all():
        if auto_advance_line(db, po, item):
            changed = True
            record(db, user_id or 0, ENTITY, po.id, "item_progress_auto",
                   f"{item.product_name}: {item.progress_status}")
    if changed:
        db.commit()
        _sync_pr(db, po.pr_code)
    return changed


def set_item_progress(db: Session, pid: int, item_id: int, target: str, reason: str, user_id: int) -> PurchaseOrder:
    po = get_po(db, pid)
    if po.status not in ("approved", "partial", "received", "processing", "completed"):
        raise HTTPException(400, "Chỉ cập nhật tiến độ dòng khi đơn đã được duyệt.")
    item = db.query(POItem).filter(POItem.id == item_id, POItem.po_id == pid).first()
    if not item:
        raise HTTPException(404, "Không tìm thấy dòng hàng.")
    if item.progress_status in (PROG_CANCELLED, PROG_COMPLETED):
        done = "hoàn thành" if item.progress_status == PROG_COMPLETED else "hủy"
        raise HTTPException(400, f"Dòng đã {done} — không thể đổi trạng thái (điểm cuối).")

    if target == "__resume__":
        # Tiếp tục đơn từ Tạm ngưng → khôi phục trạng thái trước đó
        if item.progress_status != PROG_PAUSED:
            raise HTTPException(400, "Dòng không ở trạng thái Tạm ngưng.")
        item.progress_status = item.status_before_pause or PROG_NOT_ORDERED
        item.status_before_pause = ""
    elif target in PROGRESS_EXCEPTIONS:
        if not (reason or "").strip():
            raise HTTPException(400, f"Cần nhập lý do {PO_PROGRESS_STATUS.label_of(target).lower()}.")
        #  bao-CR-538: chặn trước khi gán — cột `pause_reason` là String(500), để MySQL từ chối
        #  là ra 500 "lỗi không lường trước".
        clean_reason = ensure_max_length(reason.strip(), column_limit(POItem, "pause_reason"),
                                         "Lý do tạm ngưng / hủy")
        if target == PROG_PAUSED:
            item.status_before_pause = item.progress_status
        item.pause_reason = clean_reason
        item.progress_status = target
    elif target in PROGRESS_ORDER:
        raise HTTPException(400, "Trạng thái tiến độ tự động theo dữ liệu — không đặt tay. Chỉ dùng Tạm ngưng/Hủy đơn/Tiếp tục.")
    else:
        raise HTTPException(400, "Trạng thái không hợp lệ.")

    item.updated_by = user_id
    db.commit()
    label = "Tiếp tục" if target == "__resume__" else PO_PROGRESS_STATUS.label_of(target, target)
    record(db, user_id, ENTITY, pid, "item_progress", f"{item.product_name}: {label}")
    _sync_pr(db, po.pr_code)   # đồng bộ tiến độ sang YCMH nguồn
    db.refresh(po)
    return po
