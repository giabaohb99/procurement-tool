"""ĐMH — tạo, sửa, sao chép, xóa đơn; khóa sửa sau duyệt; đổi trạng thái, bỏ duyệt, mở lại (bao-CR-715 tách từ
service.py).
"""
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.base_model import mark_deleted
from app.core.central_purchasing import normalize_handler_dept_id
from app.core.status_codes import PO_DOCUMENT_STATUS
from app.modules.department.service import sync_department_ref
from app.modules.employee.service import sync_employee_ref
from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine

from .model import DEFAULT_CURRENCY, OrderType, POItem, PurchaseOrder
from .schema import POCreate, POUpdate
from .base_service import (ENTITY, PROG_CANCELLED, PROG_COMPLETED, _sync_pr, get_po, items_of, rate_of,
                           sync_urgent_group)
from .item_service import _save_items, fill_blank_invoice_name
from .delivery_service import recompute_effects
from .import_cost_service import block_delete_paid_import_cost, import_costs_of, sync_import_cost_payables
from .cost_allocation_service import _save_import_costs
from .progress_service import PROGRESS_ORDER, apply_auto_progress


# Các cột dòng hàng được sao chép khi Nhân bản (KHÔNG copy số đã nhận / lần giao / trạng thái;
# KHÔNG copy Số hóa đơn / Ngày hóa đơn — chứng từ riêng từng đơn, phải nhập lại ở bản sao)
_ITEM_COPY_FIELDS = ["product_code", "product_name", "invoice_name", "item_group", "spec",
                     "fg_code", "fg_name", "supplier_ready", "required_date", "unit",
                     "qty_request", "qty_order", "price", "vat", "warehouse_code", "note",
                     "currency", "exchange_rate", "weight_kg", "dimension"]


def copy_po(db: Session, pid: int, user_id: int) -> PurchaseOrder:
    """Nhân bản đơn thành 1 đơn Nháp mới: giữ dòng hàng, bỏ lần giao/số đã nhận, reset mã/MISA/trạng thái."""
    src = get_po(db, pid)
    po = PurchaseOrder(
        code="", misa_code="", pr_code=src.pr_code, survey_code=src.survey_code,
        company_id=src.company_id, supplier_code=src.supplier_code, supplier_name=src.supplier_name,
        department=src.department, department_id=src.department_id,
        # bao-CR-414: bản sao giữ phòng được nhờ; bao-CR-524: `0` cũ → phòng thu mua mặc định
        handler_dept_id=normalize_handler_dept_id(db, src.handler_dept_id),
        nspt=src.nspt, nspt_id=src.nspt_id, order_date=src.order_date, vat_rate=src.vat_rate,
        payment_terms=src.payment_terms, is_urgent=src.is_urgent, note=src.note,
        status="draft", created_by=user_id, updated_by=user_id,
        # bao-CR-319: nhân bản giữ loại đơn + tiền tệ; KHÔNG chép số tờ khai hải quan,
        # cũng KHÔNG chép bảng chi phí nhập khẩu (mỗi lô hàng một tờ khai và một bộ hóa
        # đơn cước riêng — chép sang là gán chứng từ của lô này cho lô khác).
        order_type=src.order_type or int(OrderType.DOMESTIC),
        currency=(src.currency or "").strip() or DEFAULT_CURRENCY,
        exchange_rate=rate_of(src),
        # bao-CR-321: điều khoản in đi theo NCC nên nhân bản giữ nguyên
        inspection_days=src.inspection_days or 0, return_days=src.return_days or 0,
        invoice_deadline=src.invoice_deadline or "",
    )
    sync_department_ref(db, po)     # CR-086
    sync_employee_ref(db, po, "nspt_id", "nspt")    # CR-087
    db.add(po)
    db.flush()
    po.code = f"PO{po.id:05d}"
    inv_cache: dict = {}
    for it in items_of(db, src.id):
        data = {k: getattr(it, k) for k in _ITEM_COPY_FIELDS}
        fill_blank_invoice_name(db, data, inv_cache)   # duoc-CR-663
        data["amount"] = round((float(data.get("qty_order") or 0)) * (float(data.get("price") or 0)) * (1 + (float(data.get("vat") or 0)) / 100), 2)
        db.add(POItem(po_id=po.id, created_by=user_id, updated_by=user_id, **data))
    db.commit()
    db.refresh(po)
    record(db, user_id, ENTITY, po.id, "create", f"Nhân bản từ {src.code}")
    return po


def _default_nspt(db: Session, data: POCreate, user_id: int) -> tuple[str, int]:
    """NSPT mặc định khi tạo ĐMH — trả về `(tên, id nhân sự)`:
    - Tạo TỪ YCMH (pr_code): lấy người phụ trách (assignee) của dòng trong đơn.
    - Không qua YCMH: người tạo đơn.

    CR-087: ở đây đã cầm sẵn bản ghi nhân sự nên trả luôn id, khỏi tra ngược lại theo tên
    (tra theo tên là chỗ trùng tên gây sai).
    """
    from app.modules.employee.model import Employee
    from app.modules.user.model import User
    from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
    if data.pr_code:
        pr = db.query(PurchaseRequest).filter(PurchaseRequest.code == data.pr_code).first()
        if pr:
            po_codes = {(it.product_code or "").strip() for it in (data.items or []) if (it.product_code or "").strip()}
            rows = db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).all()
            emp_code = ""
            for r in rows:   # ưu tiên dòng khớp sản phẩm trong đơn
                if (r.assignee or "").strip() and (not po_codes or (r.product_code or "").strip() in po_codes):
                    emp_code = r.assignee.strip(); break
            if not emp_code:   # fallback: bất kỳ dòng nào có người phụ trách
                for r in rows:
                    if (r.assignee or "").strip():
                        emp_code = r.assignee.strip(); break
            if emp_code:
                emp = db.query(Employee).filter(Employee.code == emp_code).first()
                if emp:
                    return emp.full_name, emp.id
    u = db.query(User).filter(User.id == user_id).first()   # người tạo
    if u and u.employee_id:
        emp = db.query(Employee).filter(Employee.id == u.employee_id).first()
        if emp:
            return emp.full_name, emp.id
    return "", 0


def _ensure_pr_dispatched(db: Session, pr_code: str) -> None:
    """CR-034 — chỉ tạo được ĐMH từ YCMH ĐÃ ĐIỀU PHỐI trở đi.
    Chặn ở đây chứ không chỉ ẩn nút bên giao diện: form ĐMH cho gõ thẳng mã YCMH.
    Mã không khớp phiếu nào (dữ liệu cũ / nhập tay) thì bỏ qua, không chặn."""
    if not pr_code:
        return
    from app.modules.purchase_request.model import PurchaseRequest
    pr = db.query(PurchaseRequest).filter(PurchaseRequest.code == pr_code,
                                          PurchaseRequest.is_deleted == False).first()
    if not pr:
        return
    # Công tắc điều phối TẮT → không còn bước duyệt lần 2, phiếu "Đã duyệt" (phiếu cũ còn kẹt lại
    # từ lúc công tắc còn bật) coi như làm việc được, nếu không sẽ không ai gỡ được cho nó.
    from app.modules.purchase_request.service import dispatch_enabled
    not_actionable_statuses = ["draft", "submitted", "rejected"]
    if dispatch_enabled():
        not_actionable_statuses.append("approved")
    if pr.status in not_actionable_statuses:
        raise HTTPException(400, f"YCMH {pr_code} chưa được điều phối (chưa có nhân sự phụ trách) "
                                 f"— chưa tạo được đơn mua hàng.")
    if pr.status == "cancelled":
        raise HTTPException(400, f"YCMH {pr_code} đã bị từ chối — không tạo được đơn mua hàng.")


def _handler_dept_of_pr(db: Session, pr_code: str) -> int:
    """bao-CR-414: phòng được nhờ trên YCMH nguồn (0 nếu không có / mã không khớp phiếu nào)."""
    if not pr_code:
        return 0
    from app.modules.purchase_request.model import PurchaseRequest
    pr = db.query(PurchaseRequest).filter(PurchaseRequest.code == pr_code,
                                          PurchaseRequest.is_deleted == False).first()
    return (pr.handler_dept_id or 0) if pr else 0


def create_po(db: Session, data: POCreate, user_id: int) -> PurchaseOrder:
    _ensure_pr_dispatched(db, (data.pr_code or "").strip())
    nspt, nspt_id = (data.nspt or "").strip(), data.nspt_id
    if not nspt and not nspt_id:
        nspt, nspt_id = _default_nspt(db, data, user_id)
    # bao-CR-414: đơn lập từ YCMH thừa kế phòng được nhờ, trừ khi form gửi rõ.
    # bao-CR-524: không có phòng nào (đơn lẻ / YCMH cũ còn `0`) → phòng thu mua mặc định.
    handler_dept_id = normalize_handler_dept_id(
        db, data.handler_dept_id or _handler_dept_of_pr(db, (data.pr_code or "").strip()))
    po = PurchaseOrder(
        code=data.code or "", misa_code=data.misa_code, pr_code=data.pr_code,
        survey_code=data.survey_code, company_id=data.company_id, supplier_code=data.supplier_code,
        supplier_name=data.supplier_name, department=data.department,
        department_id=data.department_id, handler_dept_id=handler_dept_id, nspt=nspt, nspt_id=nspt_id,
        order_date=data.order_date, vat_rate=data.vat_rate, payment_terms=data.payment_terms,
        is_urgent=data.is_urgent, note=data.note, status="draft", created_by=user_id, updated_by=user_id,
        order_type=data.order_type or int(OrderType.DOMESTIC),
        currency=(data.currency or "").strip() or DEFAULT_CURRENCY,
        exchange_rate=float(data.exchange_rate or 0) or 1,
        customs_decl_no=data.customs_decl_no, customs_decl_date=data.customs_decl_date,
        inspection_days=data.inspection_days or 0, return_days=data.return_days or 0,
        invoice_deadline=(data.invoice_deadline or "").strip(),
    )
    sync_department_ref(db, po)     # CR-086: neo phòng ban bằng id ngay từ lúc lập đơn
    sync_employee_ref(db, po, "nspt_id", "nspt")    # CR-087: NSPT cũng neo bằng id
    db.add(po)
    db.flush()
    if not po.code:
        po.code = f"PO{po.id:05d}"
    _save_items(db, po, data.items, user_id)
    _save_import_costs(db, po, data.import_costs, user_id)
    recompute_effects(db, po, user_id)
    db.commit()
    db.refresh(po)
    # CR-074: dòng YCMH phải đổi sang `not_ordered` NGAY khi đơn vừa được lập, kể cả đơn Nháp.
    _sync_pr(db, po.pr_code)
    record(db, user_id, ENTITY, po.id, "create")
    return po


# ───────────────────── Đơn ĐÃ DUYỆT: khóa phần đã được duyệt ─────────────────────
# CR-108 (phiếu hỗ trợ TK19082604): 'approved' không nằm trong danh sách khóa nên duyệt
# xong vẫn đổi được mã hàng, số lượng, đơn giá — trưởng phòng ký một đằng, đơn gửi nhà
# cung cấp một nẻo mà không để lại dấu vết nào. Từ nay đơn đã duyệt chỉ còn sửa được các
# ô PHÁT SINH SAU KHI DUYỆT; muốn đổi phần đã duyệt thì bấm "Hủy duyệt" (đơn về Nháp)
# rồi gửi duyệt lại — đi qua đúng cổng kiểm tra CR-095 một lần nữa.
APPROVED_STATUSES = ("approved", "partial", "received")

# Ô của DÒNG HÀNG còn sửa được sau khi duyệt (đúng các ô khoanh đỏ trong phiếu hỗ trợ).
LINE_FIELDS_EDITABLE_AFTER_APPROVAL = {
    "invoice_name",            # Tên trên hóa đơn — kế toán chốt sau khi có hóa đơn thật
    "expected_date",           # Ngày dự kiến có hàng — NCC hẹn lại liên tục
    "warehouse_code",          # Kho nhận mặc định
    "note",                    # Ghi chú
    # Ngày giao chứng từ cho KT: KHÔNG có trong phiếu hỗ trợ nhưng bắt buộc phải để mở.
    # Nó là điều kiện của bước tiến độ `doc_sent` (xem _step_ok) mà bước đó chỉ
    # xảy ra SAU khi duyệt — khóa lại thì mọi dòng đều kẹt tiến độ, không đơn nào xong.
    "document_delivery_date",
}

# Nhãn tiếng Việt để câu báo lỗi gọi đúng tên ô người dùng nhìn thấy trên màn hình.
LINE_FIELD_LABELS = {
    "product_code": "Mã hàng", "product_name": "Tên hàng", "item_group": "Phân loại",
    "spec": "Xuất xứ / TSKT / chất liệu", "fg_code": "Mã HH (thành phẩm)",
    "fg_name": "Tên HH (thành phẩm)", "invoice_no": "Số hóa đơn", "invoice_date": "Ngày hóa đơn",
    "supplier_ready": "NCC có sẵn hàng", "required_date": "Ngày yêu cầu có hàng",
    "unit": "ĐVT", "qty_request": "SL yêu cầu", "qty_order": "SL đặt NCC",
    "price": "Đơn giá", "vat": "VAT (%)",
    "currency": "Đồng tiền", "exchange_rate": "Tỷ giá",
    "weight_kg": "Khối lượng (kg)", "dimension": "Quy cách / kích thước",
}
ORDER_FIELD_LABELS = {
    "misa_code": "Số hóa đơn (MISA)", "pr_code": "Mã YCMH nguồn", "survey_code": "Mã YCBG nguồn",
    "company_id": "Pháp nhân", "supplier_code": "Nhà cung cấp", "supplier_name": "Tên NCC",
    "department": "Bộ phận", "nspt": "NSPT phụ trách", "order_date": "Ngày đặt hàng",
    "vat_rate": "VAT chung", "payment_terms": "Điều khoản thanh toán", "is_urgent": "Đơn gấp",
    "note": "Ghi chú đơn",
    "order_type": "Loại đơn", "currency": "Đồng tiền đơn hàng", "exchange_rate": "Tỷ giá",
    "customs_decl_no": "Số tờ khai hải quan", "customs_decl_date": "Ngày tờ khai",
    # bao-CR-321 — điều khoản in; là nội dung đã duyệt nên KHÔNG nằm trong danh sách sửa sau duyệt
    "inspection_days": "Số ngày kiểm tra hàng", "return_days": "Số ngày đổi trả",
    "invoice_deadline": "Hạn xuất hóa đơn",
}
# Ô của ĐƠN còn sửa được sau khi duyệt: hồ sơ chứng từ (đã có endpoint riêng, cập nhật
# được cả khi đơn Hoàn thành) và mã đơn MISA (kế toán nhập/sửa sau khi đã duyệt trên phần
# mềm MISA) — mọi ô còn lại là nội dung đã được duyệt.
# bao-CR-319: tờ khai hải quan cũng nằm ở đây — tờ khai chỉ có SAU khi hàng thông quan,
# mà lúc đó đơn đã duyệt từ lâu. Khóa lại thì không đơn nhập khẩu nào ghi được số tờ khai.
# bao-CR-471: cờ Đơn gấp cũng nằm ở đây. Nó là cờ VẬN HÀNH (ưu tiên xử lý), không phải nội
# dung thương mại đã duyệt; khóa nó thì một phép tính lại ở giao diện làm hỏng cả lượt lưu
# của một ô không liên quan (khách gặp 23/09 khi sửa "Ngày giao chứng từ cho KT").
ORDER_FIELDS_EDITABLE_AFTER_APPROVAL = {"document_status", "misa_code",
                            "customs_decl_no", "customs_decl_date", "is_urgent"}

_EDIT_HINT = "Bấm 'Hủy duyệt' để đưa đơn về Nháp, chỉnh rồi gửi duyệt lại."


def _differs(old, new) -> bool:
    """So sánh giá trị cũ (DB) với giá trị gửi lên, bỏ qua khác biệt kiểu Decimal/float
    và None/chuỗi rỗng — nếu không thì lần lưu nào cũng báo 'đã sửa' dù không ai chạm vào."""
    if isinstance(old, bool) or isinstance(new, bool):
        return bool(old) != bool(new)
    if isinstance(old, (int, float, Decimal)) or isinstance(new, (int, float, Decimal)):
        try:
            return abs(float(old or 0) - float(new or 0)) > 1e-6
        except (TypeError, ValueError):
            pass
    return (str(old or "").strip()) != (str(new or "").strip())


def block_edit_approved_order(db: Session, po: PurchaseOrder, data: POUpdate) -> None:
    """Chặn mọi thay đổi ngoài danh sách cho phép khi đơn đã duyệt. So theo GIÁ TRỊ chứ
    không theo 'có gửi lên hay không': màn hình luôn gửi nguyên cả đơn mỗi lần Lưu."""
    if po.status not in APPROVED_STATUSES:
        return
    payload = data.model_dump(exclude_unset=True)
    for k, v in payload.items():
        # bao-CR-319 P3: bảng chi phí nhập khẩu KHÔNG bị khóa sau khi duyệt — hóa đơn cước,
        # tờ khai thuế, phí lưu bãi đều về sau ngày duyệt đơn hàng cả tháng. Khóa lại thì
        # không đơn nhập khẩu nào ghi được chi phí thật.
        if k in ("items", "import_costs") or k in ORDER_FIELDS_EDITABLE_AFTER_APPROVAL:
            continue
        if _differs(getattr(po, k, None), v):
            raise HTTPException(400, f"Đơn đã duyệt — không sửa được '{ORDER_FIELD_LABELS.get(k, k)}'. {_EDIT_HINT}")

    rows = payload.get("items")
    if rows is None:
        return
    existing = {it.id: it for it in items_of(db, po.id)}
    if any(not r.get("id") for r in rows):
        raise HTTPException(400, f"Đơn đã duyệt — không thêm dòng hàng mới. {_EDIT_HINT}")
    submitted_ids = {r.get("id") for r in rows}
    if set(existing) - submitted_ids:
        raise HTTPException(400, f"Đơn đã duyệt — không xóa dòng hàng. {_EDIT_HINT}")
    for r in rows:
        it = existing.get(r.get("id"))
        if it is None:
            raise HTTPException(400, "Dòng hàng không thuộc đơn này.")
        # Dòng Hoàn thành / Hủy đơn: _save_items đã bỏ qua nguyên dòng, không cần chặn thêm.
        if (it.progress_status or "") in (PROG_COMPLETED, PROG_CANCELLED):
            continue
        line_name = (it.product_name or "").strip() or (it.product_code or "").strip() or f"#{it.id}"
        for k, v in r.items():
            if k in ("id", "deliveries") or k in LINE_FIELDS_EDITABLE_AFTER_APPROVAL:
                continue
            if _differs(getattr(it, k, None), v):
                label = LINE_FIELD_LABELS.get(k, k)
                raise HTTPException(400, f"Đơn đã duyệt — dòng '{line_name}' không sửa được '{label}'. {_EDIT_HINT}")


def block_clear_misa_in_use(db: Session, po: PurchaseOrder, data: POUpdate) -> None:
    """Chặn XÓA TRẮNG Mã đơn MISA khi đã có dòng tiến qua bước cần mã đó.

    Bước 1 của máy trạng thái tiến độ dòng đòi đơn phải có mã MISA (xem `_step_ok`), mà
    `auto_advance_line` chỉ TIẾN chứ không bao giờ lùi. Nên xóa trắng ô này xong là dòng
    kẹt lại ở bậc cao trong khi điều kiện của bậc đó đã hết đúng — trên màn hiện ra cảnh
    "chưa có mã MISA mà đã Chưa gửi ĐMH cho KT".

    Sửa mã thành mã KHÁC thì vẫn cho: điều kiện "có mã" vẫn thỏa, gõ nhầm phải sửa được.
    """
    payload = data.model_dump(exclude_unset=True)
    if "misa_code" not in payload:
        return
    if (payload.get("misa_code") or "").strip():
        return
    if not (po.misa_code or "").strip():
        return

    def advanced(item: POItem) -> bool:
        #  Dòng Tạm ngưng giữ bậc cũ ở `status_before_pause` và sẽ quay lại đó khi tiếp tục.
        for value in (item.progress_status or "", item.status_before_pause or ""):
            if value in PROGRESS_ORDER and PROGRESS_ORDER.index(value) >= 1:
                return True
        return False

    stuck = [it for it in items_of(db, po.id) if advanced(it)]
    if stuck:
        names = ", ".join((it.product_code or it.product_name or f"#{it.id}") for it in stuck[:3])
        more = f" và {len(stuck) - 3} dòng nữa" if len(stuck) > 3 else ""
        raise HTTPException(400, f"Không xóa trắng được Mã đơn MISA: {len(stuck)} dòng đã tiến qua bước "
                                 f"cần mã này ({names}{more}). Nhập mã khác thì được.")


def unapprove_po(db: Session, pid: int, user_id: int, reason: str = "") -> PurchaseOrder:
    """Hủy duyệt: đưa đơn ĐÃ DUYỆT về Nháp để sửa rồi gửi duyệt lại (CR-108).

    Về Nháp chứ không về Chờ duyệt: ở Nháp màn hình mở khóa sẵn theo luồng đang có, và
    lần Gửi duyệt sau sẽ chạy lại cổng kiểm tra đủ trường (CR-095) — sửa xong mà thiếu ô
    thì không lọt lên người duyệt được.
    """
    po = get_po(db, pid)
    if po.status not in APPROVED_STATUSES:
        raise HTTPException(400, "Chỉ hủy duyệt được đơn đang ở trạng thái Đã duyệt / Nhận một phần / Đã nhận.")
    items = items_of(db, pid)
    if any(float(i.qty_received or 0) > 0 for i in items):
        raise HTTPException(400, "Đơn đã nhận hàng — không hủy duyệt được. Hàng đã vào kho và đã sinh công nợ; "
                                 "muốn dừng thì hủy từng dòng ở cột Trạng thái.")
    if any((i.progress_status or "") == PROG_COMPLETED for i in items):
        raise HTTPException(400, "Đơn có dòng đã Hoàn thành — không hủy duyệt được.")
    linked_payment_lines = db.query(PaymentRequestLine.id).join(
        PaymentRequest, PaymentRequest.id == PaymentRequestLine.request_id
    ).filter(
        PaymentRequestLine.po_code == (po.code or ""),
        PaymentRequest.status != "cancelled",
        PaymentRequest.is_deleted.is_(False),   # ai-CR-176: YCTT đã xóa mềm không còn chặn
    ).first()
    if linked_payment_lines:
        raise HTTPException(400, "Đơn đã có yêu cầu thanh toán — không hủy duyệt được. "
                                 "Hủy phiếu thanh toán liên quan trước.")
    return set_status(db, pid, "draft", user_id, reason)


def update_po(db: Session, pid: int, data: POUpdate, user_id: int) -> PurchaseOrder:
    po = get_po(db, pid)
    if po.status in ("completed", "cancelled"):
        raise HTTPException(400, "Đơn đã hoàn thành/đã hủy — không sửa được. Dùng 'Nhân bản' để tạo đơn mới.")
    block_edit_approved_order(db, po, data)
    block_clear_misa_in_use(db, po, data)
    _new_pr_code = (data.model_dump(exclude_unset=True).get("pr_code") or "").strip()
    if _new_pr_code and _new_pr_code != (po.pr_code or ""):
        _ensure_pr_dispatched(db, _new_pr_code)   # CR-034: đổi sang YCMH khác cũng phải đã điều phối
    old_urgent = bool(po.is_urgent)
    for k, v in data.model_dump(exclude_unset=True, exclude={"items", "import_costs"}).items():
        setattr(po, k, v)
    if data.handler_dept_id is not None:   # bao-CR-524: 0 → phòng thu mua mặc định
        po.handler_dept_id = normalize_handler_dept_id(db, data.handler_dept_id)
    # CR-086: FE cũ chỉ gửi TÊN phòng → bỏ id cũ rồi tra lại từ tên; gửi kèm id thì id thắng.
    if data.department is not None or data.department_id is not None:
        if data.department_id is None:
            po.department_id = 0
        sync_department_ref(db, po)
    # CR-087: y hệt vậy cho ô NSPT.
    if data.nspt is not None or data.nspt_id is not None:
        if data.nspt_id is None:
            po.nspt_id = 0
        sync_employee_ref(db, po, "nspt_id", "nspt")
    po.updated_by = user_id
    _save_items(db, po, data.items, user_id)
    _save_import_costs(db, po, data.import_costs, user_id)
    recompute_effects(db, po, user_id)
    db.commit()
    db.refresh(po)
    # Cờ Đơn gấp đổi → đồng bộ ngược về YCMH + các ĐMH anh em cùng pr_code (hai chiều)
    if bool(po.is_urgent) != old_urgent and po.pr_code:
        sync_urgent_group(db, po.pr_code, bool(po.is_urgent), exclude_po_id=po.id)
    record(db, user_id, ENTITY, pid, "update")
    try:
        apply_auto_progress(db, po, user_id)   # tự tiến trạng thái dòng + đồng bộ YCMH (chỉ khi có đổi)
    except Exception:
        db.rollback()   # auto-progress không được phép làm hỏng thao tác chính (đã commit)
    # LUÔN đồng bộ lại YCMH sau khi lưu ĐMH — kể cả khi trạng thái dòng KHÔNG đổi nhưng
    # SL đặt/nhận thay đổi (vd sửa SL nhận 1800→1900). apply_auto_progress chỉ sync khi có
    # đổi trạng thái nên nếu thiếu bước này, tiến độ SL bên YCMH sẽ bị cũ.
    _sync_pr(db, po.pr_code)
    db.refresh(po)
    return po


# B-06: mã cố định, xem PO_DOCUMENT_STATUS. Trước đây là ba chuỗi tiếng Việt VIẾT THƯỜNG gõ tay.
DOCUMENT_STATUSES = tuple(PO_DOCUMENT_STATUS.ordered_values)


def set_document_status(db: Session, pid: int, value: str, user_id: int) -> PurchaseOrder:
    """Task 10b: cập nhật TAY trạng thái hồ sơ chứng từ. Cho phép cả khi đơn đã hoàn thành
    (chứng từ có thể bổ sung sau khi đơn xong)."""
    value = (value or "").strip()
    if value not in DOCUMENT_STATUSES:
        raise HTTPException(400, "Trạng thái hồ sơ chứng từ không hợp lệ")
    po = get_po(db, pid)
    po.document_status = value
    po.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, "document_status", value)
    db.refresh(po)
    return po


def delete_po(db: Session, pid: int, user_id: int):
    """Xóa MỀM đơn (ai-CR-176): chỉ đánh dấu `is_deleted` + thời điểm + người xóa.

    Dòng hàng / lần giao / chi phí nhập khẩu / đính kèm GIỮ NGUYÊN, không dọn phiếu nhập – tồn –
    công nợ kế tiếp nữa (đơn Nháp / Bị từ chối chưa sinh gì; có sót mà đã chi thì vẫn chặn như cũ
    ở `block_delete_paid_import_cost`). Luật trạng thái giữ như cũ."""
    po = get_po(db, pid)
    if po.status not in ("draft", "rejected"):
        raise HTTPException(400, "Chỉ xóa được đơn ở trạng thái Nháp hoặc Bị từ chối. Đơn đã duyệt/xử lý hãy dùng Hủy đơn.")
    for row in import_costs_of(db, pid):
        block_delete_paid_import_cost(db, row)
    mark_deleted(po, user_id)
    db.commit()
    # CR-074: xóa đơn xong thì dòng YCMH phải quay lại `no_po` nếu không còn đơn nào khác —
    # `sync_from_purchase_orders` đã bỏ đơn xóa mềm nên đồng bộ lại là đủ.
    _sync_pr(db, po.pr_code)
    record(db, user_id, ENTITY, pid, "delete", f"Xóa mềm đơn {po.code}")


def reopen_po(db: Session, pid: int, user_id: int) -> PurchaseOrder:
    """Mở lại đơn (từ Hoàn thành) để xử lý tiếp — trả về trạng thái theo TIẾN ĐỘ NHẬN,
    KHÔNG hạ về Nháp (giữ 'đã duyệt' để sửa/nhập Số HĐ + cập nhật tiến độ dòng ngay)."""
    po = get_po(db, pid)
    if po.status != "completed":
        raise HTTPException(400, "Chỉ mở lại đơn đã Hoàn thành.")
    items = items_of(db, pid)
    total_order = sum(float(i.qty_order or 0) for i in items)
    total_recv = sum(float(i.qty_received or 0) for i in items)
    if total_order > 0 and total_recv + 0.001 >= total_order:
        st = "received"
    elif total_recv > 0:
        st = "partial"
    else:
        st = "approved"
    return set_status(db, pid, st, user_id)


def set_status(db: Session, pid: int, status: str, user_id: int, message: str = "") -> PurchaseOrder:
    po = get_po(db, pid)
    po.status = status
    if message:
        po.approve_note = message
    po.updated_by = user_id
    # bao-CR-319 P5 — duyệt xong thì chi phí đã khai lúc lập đơn thành nợ; hủy/từ chối thì gỡ.
    sync_import_cost_payables(db, po, user_id)
    db.commit()
    record(db, user_id, ENTITY, pid, status, message)
    # Mọi đổi trạng thái ĐƠN đều ảnh hưởng việc đơn có được TÍNH vào YCMH hay không
    # (duyệt → bắt đầu tính; hủy/từ chối → thôi tính) nên luôn đồng bộ lại tiến độ dòng YCMH.
    _sync_pr(db, po.pr_code)
    db.refresh(po)
    return po
