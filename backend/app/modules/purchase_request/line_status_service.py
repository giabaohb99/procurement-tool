"""YCMH — trạng thái dòng và trạng thái phiếu tính lại từ Đơn mua hàng, tiến độ đặt hàng (bao-CR-715 tách từ
service.py).
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.status_codes import PO_PROGRESS_STATUS, PR_LINE_STATUS
from app.core.utils import assert_unique_product_codes

from .model import PurchaseRequest, PurchaseRequestItem
from .schema import ItemStatusIn
from .base_service import (ENTITY, LINE_STATUS_CANCELLED, LINE_STATUS_COMPLETED, LINE_STATUS_NOT_ORDERED,
                           LINE_STATUS_NO_PO, LINE_STATUS_ORDERED, LINE_STATUS_RECEIVED, get_pr, items_of)
from .lifecycle_service import _notify_survey_request_done


def has_cancelled_line(db: Session, pr_id: int) -> bool:
    return db.query(PurchaseRequestItem).filter(
        PurchaseRequestItem.pr_id == pr_id,
        PurchaseRequestItem.line_status == LINE_STATUS_CANCELLED).first() is not None


def _misa_covered_codes(db: Session, pr_code: str) -> set[str]:
    """bao-CR-292 (ticket 22) — các mã hàng ĐÃ được phủ bởi ĐMH có nhập mã đơn MISA.

    'Phủ' = tồn tại dòng ĐMH (khớp product_code) thuộc đơn còn sống (bỏ nháp/chờ duyệt/
    bị trả lại/đã từ chối — cùng rổ với sync_from_purchase_orders) mà đơn đó đã có
    `misa_code`, và bản thân dòng ĐMH không bị Hủy đơn."""
    if not pr_code:
        return set()
    from sqlalchemy import func
    from app.modules.purchase_order.model import PurchaseOrder, POItem
    rows = (db.query(POItem.product_code)
            .join(PurchaseOrder, PurchaseOrder.id == POItem.po_id)
            .filter(PurchaseOrder.pr_code == pr_code,
                    PurchaseOrder.is_deleted.is_(False),   # ai-CR-176
                    PurchaseOrder.status.notin_(["draft", "submitted", "cancelled", "rejected"]),
                    func.trim(func.coalesce(PurchaseOrder.misa_code, "")) != "",
                    # B-06: erp-v2 lưu MÃ (PO_PROGRESS_STATUS) — bản main so "Hủy đơn" tiếng Việt.
                    POItem.progress_status != "cancelled")
            .distinct().all())
    return {r[0] for r in rows}


#  bao-CR-619: đơn CÒN SỐNG nhưng chưa duyệt — chưa tính là "đã đặt", nhưng tạo thêm đơn mà không
#  thấy chúng là đặt trùng. "Bị trả lại" (rejected) vẫn sửa rồi trình lại được nên cũng nằm đây;
#  "Đã từ chối" (cancelled) là điểm cuối, không tính.
PO_PENDING_STATUSES = ("draft", "submitted", "rejected")
PO_DEAD_STATUSES = ("cancelled",)
PO_STATUS_LABELS = {
    "draft": "Nháp", "submitted": "Chờ duyệt", "rejected": "Bị trả lại", "approved": "Đã duyệt",
    "partial": "Đã nhận một phần", "received": "Đã nhận đủ", "completed": "Hoàn thành",
    "processing": "Đang xử lý",
}


def order_progress(db: Session, pr_code: str) -> dict:
    """Số đã đặt theo mã hàng của một YCMH, gộp từ mọi ĐMH cùng mã PYC.

    - `ordered`: CHỈ ĐMH đã duyệt trở đi, bỏ dòng "Chưa đặt hàng" / "Hủy đơn" — giữ nguyên nghĩa cũ
      (prefill "còn thiếu", khớp `sync_from_purchase_orders`).
    - `pending` (bao-CR-619): số trên đơn nháp / chờ duyệt / bị trả lại (bỏ dòng Hủy đơn).
    - `orders` (bao-CR-619): theo mã hàng, từng đơn còn sống kèm trạng thái + SL đặt + SL đã nhận,
      để cảnh báo đặt vượt nói được "đã đặt ở đơn nào, đơn đó tới đâu"."""
    from app.modules.purchase_order.model import PurchaseOrder, POItem
    from app.modules.purchase_order import service as po_service

    out: dict = {"ordered": {}, "pending": {}, "orders": {}}
    if not pr_code:
        return out
    rows = (db.query(PurchaseOrder.id, PurchaseOrder.code, PurchaseOrder.status, POItem.product_code,
                     POItem.qty_order, POItem.qty_received, POItem.progress_status)
            .join(POItem, POItem.po_id == PurchaseOrder.id)
            .filter(PurchaseOrder.pr_code == pr_code,
                    PurchaseOrder.is_deleted.is_(False),   # ai-CR-176: đơn đã xóa mềm = không có
                    PurchaseOrder.status.notin_(PO_DEAD_STATUSES),
                    POItem.progress_status != po_service.PROG_CANCELLED)
            .order_by(PurchaseOrder.id.asc()).all())
    per_po: dict[tuple[str, int], dict] = {}
    for po_id, po_code, status, code, qty, received, progress in rows:
        if not code:
            continue
        qty, received = float(qty or 0), float(received or 0)
        pending = status in PO_PENDING_STATUSES
        if pending:
            out["pending"][code] = out["pending"].get(code, 0.0) + qty
        elif progress != po_service.PROG_NOT_ORDERED:
            out["ordered"][code] = out["ordered"].get(code, 0.0) + qty
        entry = per_po.get((code, po_id))
        if entry is None:
            entry = {"id": po_id, "code": po_code, "status": status,
                     "status_label": PO_STATUS_LABELS.get(status, status),
                     "pending": pending, "qty": 0.0, "received": 0.0}
            per_po[(code, po_id)] = entry
            out["orders"].setdefault(code, []).append(entry)
        entry["qty"] += qty
        entry["received"] += received
    return out


def recompute_status(db: Session, pr: PurchaseRequest) -> None:
    """Tự suy trạng thái phiếu từ trạng thái các dòng (chỉ khi đã điều phối trở đi).

    CR-034: 'approved' (TP duyệt xong) KHÔNG nằm ở đây — lúc đó phiếu chưa có NSTM, chưa đặt
    hàng được nên không có gì để suy. Mốc "làm việc được" giờ là 'dispatched'.
    Ngoại lệ: công tắc điều phối TẮT thì 'approved' cũng là mốc làm việc (phiếu cũ còn kẹt lại).

    bao-CR-292 (ticket 22): 'Đang xử lý' tách thành BA mốc theo mã đơn MISA + độ phủ mã hàng
    (luật chốt với khách 05/09/2026, phải khớp nhãn tiến độ dòng của luồng gộp — doc/erp/12 P6-13):
      - processing  "Đang xử lý"  : đã có ĐMH (kể cả đơn Nháp) nhưng CHƯA đơn nào nhập MISA;
      - purchasing  "Đang mua hàng": có ĐMH nhập MISA nhưng mới phủ MỘT PHẦN mã hàng;
      - purchased   "Đã mua hàng" : MỌI mã hàng (trừ dòng Hủy) đều có ĐMH đã nhập MISA.
    Mốc lên 'processing' cũng ĐỔI theo khách: trước đây phải có dòng ĐÃ ĐẶT HÀNG, nay chỉ cần
    NSTM đã tạo ĐMH ('not_ordered' trở đi) là phiếu rời 'dispatched'."""
    # Gọi công tắc QUA cửa `service` (không import thẳng tên): bài kiểm monkeypatch `service.dispatch_enabled`.
    from . import service as pr_service

    threshold = ["dispatched", "processing", "purchasing", "purchased", "completed"]
    if not pr_service.dispatch_enabled():
        threshold.append("approved")
    if pr.status not in threshold:
        return
    items = items_of(db, pr.id)
    st = [(i.line_status or LINE_STATUS_NO_PO) for i in items]
    if not st:
        return
    was_completed = pr.status == "completed"
    # Dòng đã Hủy KHÔNG tính vào điều kiện hoàn thành (1 dòng hủy + các dòng còn lại đủ = vẫn hoàn thành)
    active = [s for s in st if s != LINE_STATUS_CANCELLED]
    if active and all(s == LINE_STATUS_COMPLETED for s in active):
        pr.status = "completed"
    elif any(s != LINE_STATUS_NO_PO for s in active):
        # Đã có ít nhất một dòng được lập ĐMH → nằm trong cụm ba mốc "đang xử lý".
        active_codes = {i.product_code for i in items
                        if (i.line_status or LINE_STATUS_NO_PO) != LINE_STATUS_CANCELLED}
        covered = _misa_covered_codes(db, pr.code) & active_codes
        if not covered:
            pr.status = "processing"
        elif active_codes - covered:
            pr.status = "purchasing"
        else:
            pr.status = "purchased"
    else:
        pr.status = "dispatched"   # chưa dòng nào có ĐMH → vẫn ở mốc đã điều phối
    db.commit()
    if pr.status == "completed" and not was_completed:
        _notify_survey_request_done(db, pr.id, pr.updated_by or 0)
        # Thông báo cho Người tạo PYC khi YCMH hoàn thành toàn bộ
        if pr.created_by:
            from app.modules.notification.service import trigger_notification
            trigger_notification(
                db=db, event="pr_completed", doc_type="purchase_request", doc_code=pr.code,
                creator_id=pr.created_by, background_tasks=None, link=f"/purchase-requests/{pr.id}",
                recipient_ids=[pr.created_by]
            )


# Thứ tự tiến độ dòng (đồng bộ với ĐMH); dòng YCMH = mức KÉM TIẾN NHẤT trong các dòng ĐMH liên kết
# Phải KHỚP PROGRESS_ORDER của ĐMH (Task 8 chèn `doc_pending`); thiếu sẽ khiến sync đặt
# nhầm dòng về mức `not_ordered`.
# B-06: trước đây đây là bản CHÉP TAY của list bên ĐMH — hai bản chép có thể trôi khỏi nhau mà
# không ai biết. Nay cả hai cùng đọc PO_PROGRESS_STATUS.ordered_values (đã loại ngoại lệ
# `paused`/`cancelled`, hai giá trị đó được xử lý riêng bên dưới).
_PROGRESS_ORDER = list(PO_PROGRESS_STATUS.ordered_values)

# Mã tiến độ của DÒNG ĐMH đọc ở đây. Không import từ `purchase_order.service` vì module đó
# import ngược lại chỗ này (sync_urgent_group) — cả hai cùng lấy từ bộ mã dùng chung thay vì
# gọi chéo nhau.
_PROG_NOT_ORDERED = "not_ordered"
_PROG_ORDERED = "ordered"
_PROG_COMPLETED = "completed"
_PROG_PAUSED = "paused"
_PROG_CANCELLED = "cancelled"


def sync_from_purchase_orders(db: Session, pr_code: str) -> None:
    """Suy trạng thái + tiến độ SL từng dòng YCMH từ các dòng ĐMH liên kết (khớp product_code),
    rồi suy lại trạng thái phiếu.
    - Chỉ tính ĐMH đã duyệt trở đi (bỏ nháp/chờ duyệt/bị trả lại/đã từ chối).
    - Dòng ĐMH Hủy: không cộng SL; dòng Tạm ngưng: dùng mức tiến độ trước khi tạm ngưng.
    - Trạng thái dòng YCMH rút gọn còn 6 mức; dòng bị Hủy THỦ CÔNG trên YCMH thì giữ nguyên.
    - qty_ordered/qty_received: tổng SL đặt/nhận theo product_code (đồng bộ vào DB).
    - CR-074: sản phẩm CHƯA có dòng ĐMH nào thì mang mã riêng `no_po` (Chưa tạo đơn mua hàng).
      Mốc "đã tạo đơn" tính CẢ đơn còn Nháp / Chờ duyệt / Bị trả lại — chỉ đơn đã Hủy là
      không tính, vì đơn đó chết rồi thì coi như chưa ai lập."""
    if not pr_code:
        return
    pr = db.query(PurchaseRequest).filter(PurchaseRequest.code == pr_code).first()
    if not pr:
        return
    from sqlalchemy import func
    from app.modules.purchase_order.model import PurchaseOrder, POItem, PODelivery
    #  ai-CR-176: đơn đã xóa mềm không tính ở cả hai rổ — xóa đơn nháp xong dòng YCMH quay về `no_po`.
    lines = (db.query(POItem).join(PurchaseOrder, PurchaseOrder.id == POItem.po_id)
             .filter(PurchaseOrder.pr_code == pr_code,
                     PurchaseOrder.is_deleted.is_(False),
                     PurchaseOrder.status.notin_(["draft", "submitted", "cancelled", "rejected"]))
             .all())
    # CR-074: rổ RỘNG HƠN `lines` — chỉ để trả lời "sản phẩm này đã có ai lập đơn chưa".
    # KHÔNG dùng để tính SL/tiến độ (đơn Nháp chưa phải cam kết gì).
    created_prods = {r[0] for r in
                     db.query(POItem.product_code).join(PurchaseOrder, PurchaseOrder.id == POItem.po_id)
                     .filter(PurchaseOrder.pr_code == pr_code,
                             PurchaseOrder.is_deleted.is_(False),
                             PurchaseOrder.status != "cancelled",
                             POItem.progress_status != _PROG_CANCELLED).distinct().all()}
    # Tổng SL đã nhận theo từng dòng ĐMH (gom các lần giao).
    recv_by_item: dict[int, float] = {}
    item_ids = [ln.id for ln in lines]
    if item_ids:
        rows = (db.query(PODelivery.po_item_id, func.coalesce(func.sum(PODelivery.received_qty), 0))
                .filter(PODelivery.po_item_id.in_(item_ids)).group_by(PODelivery.po_item_id).all())
        recv_by_item = {r[0]: float(r[1] or 0) for r in rows}
    ordered_min: dict[str, int] = {}      # sp -> mức KÉM TIẾN NHẤT trong các dòng ĐÃ ĐẶT (>= `ordered`)
    has_cancel: set[str] = set()          # sp có dòng Hủy đơn
    ordered_by_prod: dict[str, float] = {}   # sp -> tổng SL đã đặt
    received_by_prod: dict[str, float] = {}  # sp -> tổng SL đã nhận
    expected_max: dict[str, str] = {}        # sp -> ngày dự kiến có hàng MUỘN NHẤT trong các dòng ĐMH
    for ln in lines:
        p = ln.product_code
        ps = ln.progress_status or _PROG_NOT_ORDERED
        if ps == _PROG_CANCELLED:
            has_cancel.add(p); continue      # dòng hủy: không tính SL, không tính tiến độ
        # Dự kiến có hàng: một dòng YCMH có thể trải ra NHIỀU ĐMH (nhiều NCC, nhiều đợt) nên
        # lấy ngày MUỘN NHẤT — đó mới là lúc dòng được đáp ứng đủ. Ô trống không tính vào max.
        # Ngày lưu dạng ISO 'YYYY-MM-DD' nên so sánh chuỗi là so sánh đúng thứ tự thời gian.
        _ed = (ln.expected_date or "").strip()
        if _ed and _ed > expected_max.get(p, ""):
            expected_max[p] = _ed
        if ps == _PROG_PAUSED:
            ps = ln.status_before_pause or _PROG_ORDERED   # dùng mức trước khi tạm ngưng
        idx = _PROGRESS_ORDER.index(ps) if ps in _PROGRESS_ORDER else 0
        # Dòng ĐMH CHƯA đặt (kể cả đơn đã duyệt nhưng chưa bấm đặt, hoặc đơn nháp mới tạo)
        # KHÔNG kéo trạng thái/tiến độ YCMH xuống — bỏ qua hoàn toàn.
        if idx < 1:
            continue
        ordered_by_prod[p] = ordered_by_prod.get(p, 0.0) + float(ln.qty_order or 0)
        received_by_prod[p] = received_by_prod.get(p, 0.0) + recv_by_item.get(ln.id, 0.0)
        cur = ordered_min.get(p)
        ordered_min[p] = idx if cur is None else min(cur, idx)
    _DONE = _PROGRESS_ORDER.index(_PROG_COMPLETED)
    
    prev_statuses = {it.id: (it.line_status or "") for it in items_of(db, pr.id)}
    new_receives = False

    for it in items_of(db, pr.id):
        p = it.product_code
        ordered = ordered_by_prod.get(p, 0.0)
        received = received_by_prod.get(p, 0.0)
        it.qty_ordered = round(ordered, 3)
        it.qty_received = round(received, 3)
        old_st = prev_statuses.get(it.id, "")
        # Ngoại lệ đặt thủ công trên YCMH thì giữ nguyên Hủy đơn khi CHƯA có ĐMH mới (chưa tạo & chưa đặt).
        # Nếu đã tạo ĐMH mới hoặc đặt hàng mới cho sản phẩm này, trạng thái tự động cập nhật theo ĐMH mới.
        if ((it.line_status or "") == LINE_STATUS_CANCELLED
                and p not in ordered_min and p not in created_prods):
            continue
        # Dự kiến có hàng cuộn NGƯỢC từ ĐMH lên:
        #  - ô trên YCMH còn TRỐNG  -> ghi thẳng (đúng nhánh mà luật hiện hành cho sửa tự do)
        #  - ô đã CÓ giá trị và LỆCH -> KHÔNG ghi đè, và KHÔNG báo gì ở đây. Người sửa ĐMH đã
        #    được cảnh báo bằng popup ngay trên màn hình đơn mua hàng (CR-062); có sửa YCMH hay
        #    không là quyền của NSTM, và khi họ sửa thật thì update_item_status mới báo cho
        #    người yêu cầu. Ghi đè ở đây sẽ đi vòng qua luật "đổi ngày phải kèm lý do".
        _emax = expected_max.get(p, "")
        if _emax and not (it.expected_date or "").strip():
            it.expected_date = _emax
        # Suy trạng thái theo SL/tiến độ THỰC (không bị dòng ĐMH chưa đặt làm sai):
        if p not in ordered_min:
            if p in has_cancel and p not in created_prods:
                it.line_status = LINE_STATUS_CANCELLED
            else:
                # CR-074: có dòng ĐMH (kể cả đơn Nháp) → `not_ordered`; không có gì → `no_po`
                it.line_status = LINE_STATUS_NOT_ORDERED if p in created_prods else LINE_STATUS_NO_PO
        elif ordered_min[p] >= _DONE:
            it.line_status = LINE_STATUS_COMPLETED   # mọi dòng ĐMH đã đặt đều Hoàn thành
        elif received > 0:
            it.line_status = LINE_STATUS_RECEIVED    # đã nhận (một phần trở lên)
        else:
            it.line_status = LINE_STATUS_ORDERED     # đã đặt, chưa nhận

        _RECEIVED_STATUSES = (LINE_STATUS_RECEIVED, LINE_STATUS_COMPLETED)
        if it.line_status in _RECEIVED_STATUSES and old_st not in _RECEIVED_STATUSES:
            new_receives = True

    db.commit()
    recompute_status(db, pr)

    # Thông báo cho Người tạo PYC khi dòng hàng vừa được nhận đủ / hoàn thành
    if new_receives and pr.created_by:
        from app.modules.notification.service import trigger_notification
        trigger_notification(
            db=db, event="pr_items_received", doc_type="purchase_request", doc_code=pr.code,
            creator_id=pr.created_by, background_tasks=None, link=f"/purchase-requests/{pr.id}",
            recipient_ids=[pr.created_by]
        )


def _notify_expected_changed(db: Session, pr: PurchaseRequest, changes: list[str],
                             actor_id: int) -> None:
    """Báo cho NGƯỜI YÊU CẦU khi NSTM vừa đổi "thời gian dự kiến có hàng" trên YCMH.

    Chỉ chạy khi ngày thực sự đổi trên YCMH (không phải khi ĐMH lệch) — sửa hay không là
    quyền của NSTM, còn người yêu cầu thì cần biết hàng của mình lùi/sớm ngày.
    Người nhận: tài khoản của nhân sự người yêu cầu (`requester_id`), không có thì người tạo
    phiếu. Không tự báo cho chính người vừa thao tác.
    """
    from app.modules.user.model import User
    from app.modules.notification.service import trigger_notification

    uid = None
    if pr.requester_id:
        u = (db.query(User)
             .filter(User.employee_id == pr.requester_id, User.is_active == True)
             .first())
        uid = u.id if u else None
    uid = uid or pr.created_by
    if not uid or uid == actor_id:
        return

    trigger_notification(
        db=db, event="pr_expected_date_changed", doc_type="purchase_request", doc_code=pr.code,
        creator_id=actor_id or pr.created_by, background_tasks=None,
        reason="\n".join(f"- {c}" for c in changes),
        link=f"/purchase-requests/{pr.id}", recipient_ids=[uid])


def _set_item_product_code(db: Session, rows: dict, row: PurchaseRequestItem, raw: str,
                           changes: list[str]) -> None:
    """bao-CR-568 (02/10/2026) — gắn / đổi Mã VTBB cho một dòng SAU điều phối.

    Đại ca chốt luồng như YCBG: phiếu sinh từ YCBG có thể không mang mã, NSTM vẫn chốt hoàn
    thành xử lý được; nhưng muốn TẠO ĐƠN thì dòng phải có mã, nên nhân sự thu mua (hoặc quản
    lý) gắn mã ở đây. Chỉ khi dòng CHƯA lên ĐMH: dòng ĐMH nối ngược về dòng YCMH bằng chuỗi
    `product_code` (xem `sync_from_purchase_orders`), đổi mã khi đơn đã có là cắt dây nối.
    Mã phải có trong danh mục và không trùng dòng khác trên cùng phiếu (luật YCMH cũ).
    """
    from app.modules.product.model import Product
    new = (raw or "").strip()
    old = (row.product_code or "").strip()
    if new == old:
        return
    if (row.line_status or LINE_STATUS_NO_PO) != LINE_STATUS_NO_PO:
        raise HTTPException(400, f"Dòng '{row.product_name}' đã lên đơn mua hàng — không đổi mã VTBB được")
    if new:
        prod = db.query(Product).filter(Product.code == new).first()
        if prod is None:
            raise HTTPException(400, f"Mã VTBB \"{new}\" không có trong danh mục sản phẩm")
        if not prod.is_active:
            raise HTTPException(400, f"Mã VTBB \"{new}\" đã ngừng dùng")
    others = [(r.product_code or "") for r in rows.values() if r.id != row.id]
    assert_unique_product_codes(others + [new], old_codes=[(r.product_code or "") for r in rows.values()])
    row.product_code = new
    changes.append(f"{row.product_name}: mã VTBB {old or '—'} → {new or '—'}")


def update_item_status(db: Session, pid: int, data: ItemStatusIn, user_id: int, emp_code: str, is_manager: bool) -> PurchaseRequest:
    pr = get_pr(db, pid)
    if pr.status in ("cancelled", "completed"):
        raise HTTPException(400, "Phiếu đã bị từ chối/hoàn thành — không thể cập nhật")
    rows = {i.id: i for i in items_of(db, pid)}
    _expected_changes: list[str] = []
    _code_changes: list[str] = []
    for it in data.items:
        row = rows.get(it.id)
        if row is None:
            continue
        if not is_manager and (row.assignee or "") != (emp_code or "__none__"):
            continue  # NSTM chỉ sửa dòng được giao cho mình
        if it.product_code is not None:
            _set_item_product_code(db, rows, row, it.product_code, _code_changes)
        if it.line_status is not None:
            # B-06: cột lưu MÃ. Chặn ngay tại cửa thay vì để giá trị lạ nằm im trong CSDL —
            # dòng mang mã lạ rơi khỏi mọi bộ lọc VÀ khỏi cả điều kiện hoàn thành phiếu.
            if it.line_status not in PR_LINE_STATUS.values:
                raise HTTPException(400, f"Trạng thái dòng không hợp lệ: {it.line_status!r}")
            row.line_status = it.line_status
        if it.progress_note is not None:
            row.progress_note = it.progress_note
        if it.note is not None:
            row.note = it.note
        # Thời gian dự kiến có hàng: rỗng → cập nhật tự do; ĐÃ có giá trị → đổi phải kèm lý do.
        if it.expected_date is not None:
            old = (row.expected_date or "").strip()
            new = (it.expected_date or "").strip()
            if new != old:
                reason = (it.expected_date_reason or "").strip()
                if old and not reason:
                    raise HTTPException(400, f"Đổi 'thời gian dự kiến có hàng' của '{row.product_name}' "
                                             f"(từ {old}) phải kèm lý do.")
                row.expected_date = new
                _expected_changes.append(f"{row.product_name}: {old or '—'} → {new or '—'}"
                                         + (f" · lý do: {reason}" if reason else ""))
    pr.updated_by = user_id
    db.commit()
    recompute_status(db, pr)
    record(db, user_id, ENTITY, pid, "line_status", "Cập nhật trạng thái dòng")
    for msg in _expected_changes:
        record(db, user_id, ENTITY, pid, "expected_date", msg)
    for msg in _code_changes:
        record(db, user_id, ENTITY, pid, "product_code", msg)
    if _expected_changes:
        _notify_expected_changed(db, pr, _expected_changes, user_id)
    db.refresh(pr)
    return pr
