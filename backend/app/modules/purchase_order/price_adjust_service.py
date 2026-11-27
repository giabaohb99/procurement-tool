"""ĐMH — SỬA ĐƠN GIÁ SAU DUYỆT (bao-CR-794).

Vì sao có: đơn đã duyệt bị khóa đơn giá (`block_edit_approved_order`, CR-108); muốn sửa phải Hủy duyệt đưa đơn về Nháp, mà Hủy
duyệt bị chặn khi đơn đã nhận hàng (hàng đã vào kho, đã sinh công nợ). Giá NCC báo lại sau khi hàng về thì trước đây chỉ sửa được
bằng script vận hành. Đường này cho người có quyền DUYỆT sửa thẳng ĐƠN GIÁ của dòng, không đưa đơn về Nháp.

Chỉ đổi đơn giá. Mã hàng, số lượng, VAT, tiền tệ vẫn khóa như cũ. Sửa xong đi đúng đuôi của `update_po`: `recompute_effects` (thành
tiền dòng, tồn kho, công nợ hàng theo SL đã nhận) -> đồng bộ YCMH -> sổ giá -> lịch sử mua hàng.

Chặn (tiền đã đi tiếp theo giá cũ thì không sửa ngầm bên dưới):
  - đơn chưa duyệt (sửa thẳng trên đơn), đã Hoàn thành hoặc đã Hủy;
  - đơn có yêu cầu thanh toán đã gửi duyệt trở đi (`submitted` / `approved` / `paid`) — phiếu Nháp thì cho, trả tên phiếu để nhắc;
  - công nợ hàng của đơn đã trả tiền;
  - dòng đã Hoàn thành (bản ghi lịch sử đã chốt) hoặc đã Hủy.
"""
from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.audit import record
from app.modules.payable.model import Payable
from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine
from app.modules.product_price.ledger_sync_service import sync_po_price_ledger
from app.modules.purchase_history.service import sync_po_history_safe

from .base_service import ENTITY, PROG_CANCELLED, PROG_COMPLETED, _sync_pr, get_po, items_of
from .delivery_service import recompute_effects
from .edit_service import APPROVED_STATUSES, _differs
from .model import POItem, PurchaseOrder
from .schema import PriceAdjustIn

#  Phiếu YCTT ở các trạng thái này đã mang số tiền tính theo giá cũ đi trình / đi chi.
PRICE_ADJUST_BLOCKING_REQUEST_STATUSES = ("submitted", "approved", "paid")


def _money(value) -> str:
    """Số kiểu Việt (5.105 · 0,125) cho câu nhật ký và câu báo lỗi."""
    text = f"{float(value or 0):,.4f}".rstrip("0").rstrip(".")
    return text.translate(str.maketrans(",.", ".,"))


def _line_name(item: POItem) -> str:
    return (item.product_code or "").strip() or (item.product_name or "").strip() or f"#{item.id}"


def _linked_payment_requests(db: Session, po: PurchaseOrder) -> list[tuple[str, str]]:
    """(mã phiếu, trạng thái) của các YCTT còn sống có dòng gắn đơn này."""
    code = (po.code or "").strip()
    if not code:
        return []
    rows = (db.query(PaymentRequest.code, PaymentRequest.status)
            .join(PaymentRequestLine, PaymentRequestLine.request_id == PaymentRequest.id)
            .filter(PaymentRequestLine.po_code == code, PaymentRequest.status != "cancelled",
                    PaymentRequest.is_deleted.is_(False))
            .distinct().order_by(PaymentRequest.code).all())
    return [(request_code or "", status or "") for request_code, status in rows]


def _block_when_money_moved(db: Session, po: PurchaseOrder) -> list[str]:
    """Chặn khi tiền đã đi tiếp theo giá cũ. Trả mã các YCTT còn Nháp (được sửa, chỉ nhắc)."""
    requests = _linked_payment_requests(db, po)
    sent = [code for code, status in requests if status in PRICE_ADJUST_BLOCKING_REQUEST_STATUSES]
    if sent:
        raise HTTPException(400, f"Đơn đã có yêu cầu thanh toán {', '.join(sent)} gửi duyệt hoặc đã chi — không sửa giá được. "
                                 "Hủy phiếu thanh toán liên quan trước rồi sửa giá.")
    #  Tra theo CẢ id lẫn mã đơn: khoản nợ cũ có dòng để `po_id = 0`, chỉ mang `po_code` (gặp thật trên dev, PO00807).
    owner = Payable.po_id == po.id
    if (po.code or "").strip():
        owner = or_(owner, Payable.po_code == po.code)
    paid = db.query(Payable.id).filter(owner, Payable.source_type == "goods", Payable.paid_amount > 0).first()
    if paid:
        raise HTTPException(400, "Công nợ hàng của đơn đã trả tiền — không sửa giá được.")
    return [code for code, _status in requests]


def _plan_changes(db: Session, po: PurchaseOrder, data: PriceAdjustIn) -> list[tuple[POItem, float, float]]:
    """Kiểm HẾT rồi mới trả danh sách (dòng, giá cũ, giá mới) — một dòng sai thì chưa dòng nào bị đụng."""
    existing = {item.id: item for item in items_of(db, po.id)}
    plan: list[tuple[POItem, float, float]] = []
    seen: set[int] = set()
    for row in data.items:
        item = existing.get(row.id)
        if item is None:
            raise HTTPException(400, "Dòng hàng không thuộc đơn này.")
        if row.id in seen:
            raise HTTPException(400, f"Dòng '{_line_name(item)}' bị gửi hai lần.")
        seen.add(row.id)
        if not _differs(item.price, row.price):
            continue
        if (item.progress_status or "") in (PROG_COMPLETED, PROG_CANCELLED):
            raise HTTPException(400, f"Dòng '{_line_name(item)}' đã Hoàn thành hoặc đã Hủy — không sửa giá được.")
        plan.append((item, float(item.price or 0), float(row.price)))
    if not plan:
        raise HTTPException(400, "Không có dòng nào đổi giá.")
    return plan


def adjust_prices(db: Session, pid: int, data: PriceAdjustIn, user_id: int) -> dict:
    """Sửa đơn giá các dòng của đơn ĐÃ DUYỆT rồi tính lại mọi thứ đi theo giá.

    Trả {"po", "changed": [{id, product_code, old_price, new_price}], "draft_requests": [mã YCTT Nháp cần kiểm lại]}.
    """
    po = get_po(db, pid)
    reason = (data.reason or "").strip()
    if not reason:
        raise HTTPException(400, "Vui lòng nhập lý do sửa giá.")
    if po.status not in APPROVED_STATUSES:
        raise HTTPException(400, "Chỉ sửa giá sau duyệt cho đơn Đã duyệt / Nhận một phần / Đã nhận. "
                                 "Đơn chưa duyệt thì sửa thẳng trên đơn; đơn đã Hoàn thành hoặc đã Hủy thì không sửa được.")
    draft_requests = _block_when_money_moved(db, po)
    plan = _plan_changes(db, po, data)

    for item, _old, new in plan:
        item.price = new
        item.updated_by = user_id
    po.updated_by = user_id
    recompute_effects(db, po, user_id)
    db.commit()
    db.refresh(po)

    changed = [{"id": item.id, "product_code": item.product_code or "", "old_price": old, "new_price": new}
               for item, old, new in plan]
    detail = "; ".join(f"{_line_name(item)} {_money(old)} → {_money(new)}" for item, old, new in plan)
    record(db, user_id, ENTITY, pid, "adjust_price", f"Sửa giá sau duyệt: {detail}. Lý do: {reason}", doc_code=po.code or "")
    _sync_pr(db, po.pr_code)
    sync_po_price_ledger(db, po)   # duoc-CR-784: sổ giá đi theo giá mới
    sync_po_history_safe(db, po)   # bao-CR-790: bản ghi lịch sử mua hàng chưa chốt đi theo giá mới
    db.refresh(po)
    return {"po": po, "changed": changed, "draft_requests": draft_requests}
