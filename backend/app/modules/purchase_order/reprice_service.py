"""ĐMH — SỬA GIÁ SAU DUYỆT: đổi SL đặt / Đơn giá / VAT của dòng khi đơn đã duyệt mà không phải Hủy duyệt.

Khóa sau duyệt (CR-108, `edit_service.block_edit_approved_order`) GIỮ NGUYÊN cho đường Lưu chung; đây là
một đường riêng, gác bằng quyền DUYỆT, ghi nhật ký từng ô cũ → mới.

Lưu xong thì chuỗi phía sau tự tính lại bằng đúng `recompute_effects` của lần Lưu thường: thành tiền dòng,
tồn kho (đơn giá nhập của các lần đã nhận), công nợ hàng, rồi YCMH (SL đặt). YCTT NHÁP đang trỏ vào công
nợ của dòng được nạp lại theo công nợ mới (`payment_request.service.apply_refresh`).

Dòng bị CHẶN (lý do trả về cho giao diện qua `get_reprice_locks`):
- dòng Hoàn thành / Hủy đơn — điểm cuối, Lịch sử mua hàng đã chụp lại giá;
- công nợ của dòng đã có tiền trả (kể cả tiền trả trước đã đối trừ);
- công nợ của dòng nằm trên YCTT đã gửi duyệt / đã duyệt / đã chi — sửa thì số trên phiếu tiền lệch công nợ.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.modules.payable.model import Payable
from app.modules.payment_request import service as prq_service
from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine
from app.modules.product_price.ledger_sync_service import sync_po_price_ledger   # duoc-CR-784: sổ giá
from app.modules.purchase_history.service import sync_po_history_safe   # bao-CR-790: lịch sử mua hàng từ lúc nhận hàng

from .base_service import ENTITY, PROG_CANCELLED, PROG_COMPLETED, _sync_pr, get_po, items_of
from .delivery_service import recompute_effects
from .edit_service import APPROVED_STATUSES, _differs
from .model import POItem, PODelivery, PurchaseOrder
from .progress_service import apply_auto_progress
from .schema import RepriceIn

# Trạng thái YCTT mà số tiền đã "đi" (người duyệt / kế toán đã nhìn số đó) — dòng nằm trên phiếu này bị chặn.
_PAYMENT_LOCKED_STATUSES = ("submitted", "approved", "paid")
_PAYMENT_STATUS_LABELS = {"submitted": "đang chờ duyệt", "approved": "đã duyệt", "paid": "đã chi"}

# Các ô được sửa và nhãn hiện trong nhật ký — cùng chữ với tiêu đề cột trên bảng dòng.
_REPRICE_FIELD_LABELS = {"qty_order": "SL đặt", "price": "Đơn giá", "vat": "VAT (%)"}


def _goods_payables_by_item(db: Session, po: PurchaseOrder) -> dict[int, list[Payable]]:
    """Công nợ HÀNG của từng dòng — mỗi lần giao đã nhận sinh một khoản (`ref_id` = id lần giao)."""
    deliveries = db.query(PODelivery.id, PODelivery.po_item_id).filter(PODelivery.po_id == po.id).all()
    item_of_delivery = {d.id: d.po_item_id for d in deliveries}
    if not item_of_delivery:
        return {}
    rows = db.query(Payable).filter(
        Payable.source_type == "goods", Payable.ref_type == "delivery",
        Payable.ref_id.in_(list(item_of_delivery)),
    ).all()
    out: dict[int, list[Payable]] = {}
    for p in rows:
        out.setdefault(item_of_delivery[p.ref_id], []).append(p)
    return out


def _linked_payment_requests(db: Session, po: PurchaseOrder,
                             payables_by_item: dict[int, list[Payable]]) -> dict[int, list[PaymentRequest]]:
    """YCTT (chưa hủy, chưa xóa) có dòng trỏ vào công nợ của từng dòng ĐMH.

    Khớp bằng `payables_of_line` — cùng luật với lúc chi tiền, nên dòng phiếu gắn theo (mã PO + số HĐ) hay
    theo `payable_id` đều bắt được."""
    item_of_payable = {p.id: item_id for item_id, pays in payables_by_item.items() for p in pays}
    if not item_of_payable:
        return {}
    req_ids = {rid for (rid,) in db.query(PaymentRequestLine.request_id).filter(
        (PaymentRequestLine.po_code == (po.code or ""))
        | (PaymentRequestLine.payable_id.in_(list(item_of_payable)))
    ).distinct().all()}
    if not req_ids:
        return {}
    requests = db.query(PaymentRequest).filter(
        PaymentRequest.id.in_(req_ids), PaymentRequest.status != "cancelled",
        PaymentRequest.is_deleted.is_(False),
    ).all()
    out: dict[int, list[PaymentRequest]] = {}
    for req in requests:
        hit_items: set[int] = set()
        for ln in prq_service.lines_of(db, req.id):
            for p in prq_service.payables_of_line(db, req, ln):
                if p.id in item_of_payable:
                    hit_items.add(item_of_payable[p.id])
        for item_id in hit_items:
            out.setdefault(item_id, []).append(req)
    return out


def _lock_reason(item: POItem, payables: list[Payable], requests: list[PaymentRequest]) -> str:
    progress = item.progress_status or ""
    if progress == PROG_COMPLETED:
        return "Dòng đã Hoàn thành"
    if progress == PROG_CANCELLED:
        return "Dòng đã hủy"
    if any(float(p.paid_amount or 0) > 0.01 for p in payables):
        return "Công nợ của dòng đã có tiền trả"
    locked = [r for r in requests if r.status in _PAYMENT_LOCKED_STATUSES]
    if locked:
        req = locked[0]
        return (f"Dòng đã nằm trên YCTT {req.code} ({_PAYMENT_STATUS_LABELS.get(req.status, req.status)}) — "
                f"trả phiếu đó về trước")
    return ""


def get_reprice_locks(db: Session, po: PurchaseOrder) -> dict[int, str]:
    """Lý do KHÔNG sửa giá được của từng dòng; dòng sửa được không có mặt trong kết quả."""
    payables = _goods_payables_by_item(db, po)
    requests = _linked_payment_requests(db, po, payables)
    out: dict[int, str] = {}
    for it in items_of(db, po.id):
        reason = _lock_reason(it, payables.get(it.id, []), requests.get(it.id, []))
        if reason:
            out[it.id] = reason
    return out


def _format_value(field: str, value) -> str:
    """Số cho câu nhật ký theo kiểu Việt: chấm ngăn nghìn, phẩy thập phân, bỏ số 0 thừa (15.300 · 69.444,44)."""
    number = float(value or 0)
    if field == "vat":
        return f"{number:g}%"
    text = f"{number:,.4f}".rstrip("0").rstrip(".")
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def _validate_row(it: POItem, qty_order: float, price: float, vat: float) -> None:
    line_name = (it.product_name or "").strip() or (it.product_code or "").strip() or f"#{it.id}"
    if qty_order <= 0:
        raise HTTPException(400, f"Dòng '{line_name}': SL đặt phải lớn hơn 0.")
    received = float(it.qty_received or 0)
    if qty_order + 1e-9 < received:
        raise HTTPException(400, f"Dòng '{line_name}': SL đặt không được nhỏ hơn SL đã nhận ({received:g}).")
    if price < 0:
        raise HTTPException(400, f"Dòng '{line_name}': Đơn giá không được âm.")
    if not 0 <= vat <= 100:
        raise HTTPException(400, f"Dòng '{line_name}': VAT phải trong khoảng 0 – 100%.")


def reprice_po(db: Session, pid: int, data: RepriceIn, user_id: int) -> tuple[PurchaseOrder, int, list[str]]:
    """Ghi SL đặt / Đơn giá / VAT mới cho các dòng của đơn ĐÃ DUYỆT.

    Trả `(đơn, số dòng đổi, mã các YCTT nháp đã nạp lại)`. Dòng gửi lên mà không đổi gì thì bỏ qua."""
    po = get_po(db, pid)
    if po.status not in APPROVED_STATUSES:
        raise HTTPException(400, "Chỉ sửa giá được đơn đang ở trạng thái Đã duyệt / Nhận một phần / Đã nhận.")

    existing = {it.id: it for it in items_of(db, po.id)}
    locks = get_reprice_locks(db, po)
    changes: list[tuple[POItem, dict]] = []
    for row in data.items:
        it = existing.get(row.id)
        if it is None:
            raise HTTPException(400, "Dòng hàng không thuộc đơn này.")
        new_values = {"qty_order": float(row.qty_order), "price": float(row.price), "vat": float(row.vat)}
        diff = {k: v for k, v in new_values.items() if _differs(getattr(it, k, None), v)}
        if not diff:
            continue
        if it.id in locks:
            line_name = (it.product_name or "").strip() or (it.product_code or "").strip() or f"#{it.id}"
            raise HTTPException(400, f"Dòng '{line_name}' không sửa giá được: {locks[it.id]}.")
        _validate_row(it, **new_values)
        changes.append((it, diff))
    if not changes:
        raise HTTPException(400, "Không có dòng nào thay đổi.")

    log_parts: list[str] = []
    for it, diff in changes:
        line_name = (it.product_code or "").strip() or (it.product_name or "").strip() or f"#{it.id}"
        cells = ", ".join(
            f"{_REPRICE_FIELD_LABELS[k]} {_format_value(k, getattr(it, k))} → {_format_value(k, v)}"
            for k, v in diff.items())
        log_parts.append(f"{line_name}: {cells}")
        for k, v in diff.items():
            setattr(it, k, v)
        it.updated_by = user_id
    po.updated_by = user_id
    recompute_effects(db, po, user_id)
    db.commit()

    # YCTT nháp đang trỏ vào công nợ của các dòng vừa đổi: nạp lại theo công nợ mới. Phiếu nháp chưa ai duyệt
    # nên sửa số an toàn; phiếu đã đi duyệt thì dòng đã bị chặn ở trên.
    changed_ids = {it.id for it, _ in changes}
    payables = _goods_payables_by_item(db, po)
    requests = _linked_payment_requests(db, po, payables)
    draft_ids = sorted({r.id for item_id, reqs in requests.items() if item_id in changed_ids
                        for r in reqs if r.status == "draft"})
    refreshed: list[str] = []
    for rid in draft_ids:
        req, plan = prq_service.apply_refresh(db, rid, user_id)
        if plan.get("changed_count"):
            refreshed.append(req.code)

    message = f"Sửa giá sau duyệt ({len(changes)} dòng): " + "; ".join(log_parts)
    if refreshed:
        message += f". YCTT nháp đã cập nhật theo: {', '.join(refreshed)}"
    record(db, user_id, ENTITY, pid, "reprice", message[:4000])
    try:
        apply_auto_progress(db, po, user_id)
    except Exception:
        db.rollback()   # tiến độ tự động không được làm hỏng thao tác chính (đã commit) — như update_po
    _sync_pr(db, po.pr_code)   # SL đặt đổi → tiến độ dòng YCMH tính lại
    sync_po_price_ledger(db, po)   # bao-CR-799: giá / SL / VAT đổi → sổ giá của cụm Giá NVL đi theo
    sync_po_history_safe(db, po)   # bao-CR-799: bản ghi lịch sử mua hàng chưa chốt đi theo
    db.refresh(po)
    return po, len(changes), refreshed
