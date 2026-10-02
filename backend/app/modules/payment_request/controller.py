from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.modules.notification.service import trigger_notification

from app.core.bulk_delete import ensure_all_draft
from app.core.audit import resolve_actor, resolve_actor_profile
from app.core.auth import get_perm_profile, require
from app.core.base_controller import apply_filters, apply_range_filters, apply_equals, apply_sort_from_request, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, get_scoped
from app.modules.company.model import Company
from app.modules.payable.model import Payable
from app.modules.supplier.model import Supplier

from . import service
from .model import PaymentRequest
from .schema import PRequestCreate, PRequestUpdate

router = APIRouter(prefix="/api/payment-requests", tags=["payment_request"])

HEADER = ["id", "code", "supplier_code", "supplier_name", "company_id", "department_id",
          "source_type", "request_date", "payment_method", "prepay", "total", "note",
          "reject_reason", "status",   # department_id: cột ẩn bao-CR-414 GĐ4, bản in không đọc
          "head_of_dept_id", "head_of_dept"]   # bao-CR-553


def _line(db, ln, misa_by_po: dict | None = None, sync: dict | None = None) -> dict:
    """Tổng nợ / Đã trả / Hạn trả luôn ĐỌC từ Công nợ (không lưu trên phiếu, tránh lệch số);
    còn mã PO / số hóa đơn / ngày hóa đơn là dữ liệu nhập trên phiếu (CR-066).
    Dòng chưa khớp khoản nợ nào (form trắng, hàng chưa về) thì các cột nợ trả về 0 / rỗng.

    `sync` (bao-CR-509): dòng tương ứng trong `service.plan_refresh` — số mà dòng ĐÁNG RA
    mang theo công nợ hiện tại, để màn chi tiết cảnh báo phiếu lệch công nợ."""
    req = db.get(PaymentRequest, ln.request_id) if ln.request_id else None
    if req:
        payables = service.payables_of_line(db, req, ln)
    else:
        p = db.get(Payable, ln.payable_id) if ln.payable_id else None
        payables = [p] if p else []

    tot = sum(float(px.total or 0) for px in payables)
    paid = sum(float(px.paid_amount or 0) for px in payables)
    due_date = min((px.due_date for px in payables if px.due_date), default="")
    incur_date = min((px.incur_date for px in payables if px.incur_date), default="")
    # Ngày hóa đơn: giá trị đã nhập trên phiếu > ngày hóa đơn của lần giao hàng
    invoice_date = (ln.invoice_date or "").strip() or service.delivery_invoice_date(db, payables)
    return {"id": ln.id, "payable_id": ln.payable_id, "po_code": ln.po_code,
            "misa_code": (misa_by_po or {}).get((ln.po_code or "").strip(), ""),
            "invoice_no": ln.invoice_no, "amount": float(ln.amount or 0),
            "invoice_date": invoice_date, "due_date": due_date, "incur_date": incur_date,
            "payable_total": tot, "payable_paid": paid,
            "matched": bool(payables),
            # CR-268 — tiền treo của phiếu trả trước: chỉ có nghĩa khi phiếu prepay=1 đã chi
            "allocated_amount": float(ln.allocated_amount or 0),
            "refunded_amount": float(ln.refunded_amount or 0),
            # CR-260 — phần đề nghị cấn trừ tiền treo, thực thi khi phiếu được DUYỆT
            "offset_amount": float(ln.offset_amount or 0),
            "hanging": service.line_hanging(ln),
            # bao-CR-509 — nợ còn lại hiện tại (None = dòng không gắn công nợ / không theo dõi)
            # và số đề nghị ĐÁNG RA theo công nợ; `out_of_sync` = số trên phiếu đang lệch.
            "payable_remaining": sync["payable_remaining"] if sync else None,
            "expected_amount": sync["amount_new"] if sync else None,
            "out_of_sync": bool(sync and sync["amount_changed"]),
            "sync_state": sync["state"] if sync else "",
            "sync_reason": sync["reason"] if sync else ""}


def _out(db: Session, req: PaymentRequest) -> dict:
    d = {c: getattr(req, c) for c in HEADER}
    d["total"] = float(req.total or 0)
    # CR-149: trả dict đã parse (không trả chuỗi JSON thô) — màn chi tiết + bản in dùng chung
    d["print_texts"] = service.parse_print_texts(req.print_texts)
    d["created_by_name"] = resolve_actor(db, req.created_by)
    d["created_at"] = req.created_at
    lines = service.lines_of(db, req.id)
    # Ticket #26: mã MISA join theo mã PO một lượt cho cả phiếu
    misa_by_po = service.misa_by_po_code(db, [ln.po_code for ln in lines])
    # bao-CR-509 — so số trên phiếu với công nợ hiện tại. Chỉ tính khi phiếu còn phải bám
    # công nợ (nháp / chờ duyệt / đã duyệt, không phải phiếu trả trước); đã chi / đã từ
    # chối thì công nợ đổi là chuyện bình thường, cảnh báo chỉ gây nhiễu.
    sync_by_line: dict[int, dict] = {}
    d["out_of_sync"] = False
    if not req.prepay and req.status in ("draft", "submitted", "approved"):
        plan = service.plan_refresh(db, req)
        sync_by_line = {r["line_id"]: r for r in plan["lines"]}
        d["out_of_sync"] = plan["out_of_sync"]
    d["lines"] = [_line(db, ln, misa_by_po, sync_by_line.get(ln.id)) for ln in lines]
    return d


def _scoped(db: Session, rid: int, user, action: str) -> PaymentRequest:
    """Nạp phiếu CHỈ khi nó nằm trong phạm vi dữ liệu của người gọi.

    `require(...)` trả lời "vai trò này được làm hành động đó không"; nó KHÔNG trả lời
    "trên phiếu NÀO". Trước bản vá này chỉ đường XEM hỏi phạm vi (`get_`), còn bản in và
    toàn bộ đường GHI đi thẳng `service.*` → `db.get` — nên cùng một phiếu của pháp nhân
    khác thì đọc bị 403 mà **duyệt chi / xóa** lại trót lọt.

    ⚠️ `action` phải khớp ĐÚNG action của `require(...)` trên chính route gọi nó. Mượn tạm
    `read` cho mọi đường là dựng lại lỗ #27 của cụm khác: người "xem toàn công ty, chỉ
    duyệt phòng mình" sẽ duyệt được cả công ty, còn người chỉ có `approve` mà không có
    `read` thì bị chặn sạch.

    Trả **404** như `get_scoped` quy ước: người ngoài phạm vi không cần biết phiếu đó có
    thật hay không.
    """
    req = get_scoped(db, PaymentRequest, "payment_request", rid, user,
                     get_perm_profile(db, user), action)
    if not req:
        raise HTTPException(404, "Không tìm thấy phiếu yêu cầu thanh toán")
    return req


def _list_query(db: Session, request: Request, user, action: str = "read"):
    """Truy vấn phiếu theo bộ lọc trên URL + phạm vi dữ liệu — dùng chung cho màn danh sách
    và tệp xuất Excel (bao-CR-525), để tệp xuất ra ĐÚNG những phiếu người dùng đang thấy."""
    q = apply_filters(db.query(PaymentRequest), PaymentRequest, request, service.FILTERABLE)
    q = apply_range_filters(q, PaymentRequest, request, ["request_date"])
    q = apply_equals(q, PaymentRequest, request, ["company_id"])
    po_code = (request.query_params.get("po_code") or "").strip()
    if po_code:
        from sqlalchemy import select
        from .model import PaymentRequestLine
        sub = select(PaymentRequestLine.request_id).where(PaymentRequestLine.po_code.like(f"%{po_code}%"))
        q = q.filter(PaymentRequest.id.in_(sub))
    # Khối "YCTT của đơn này" trên chi tiết ĐMH cần khớp ĐÚNG mã đơn — lọc LIKE ở
    # trên sẽ vơ nhầm PO-1 vào PO-10, nên tách tham số riêng thay vì đổi hành vi cũ.
    po_exact = (request.query_params.get("po_code_exact") or "").strip()
    if po_exact:
        from sqlalchemy import select
        from .model import PaymentRequestLine
        sub = select(PaymentRequestLine.request_id).where(PaymentRequestLine.po_code == po_exact)
        q = q.filter(PaymentRequest.id.in_(sub))
    misa_code = (request.query_params.get("misa_code") or "").strip()
    if misa_code:
        # Ticket #26 (đợt 2): phiếu không lưu mã MISA -> lọc qua dòng phiếu + ĐMH
        q = service.filter_by_misa_code(q, misa_code)
    q = apply_scope(q, PaymentRequest, "payment_request", user, get_perm_profile(db, user), action)
    return q


@router.get("")
def list_(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
          user=Depends(require("payment_request", "read"))):
    q = _list_query(db, request, user)
    total = q.count()
    q = apply_sort_from_request(q, PaymentRequest, request, default=PaymentRequest.id.desc())
    items = q.offset(pg["offset"]).limit(pg["limit"]).all()
    # Ticket #26 (bao-CR-302): cột Mã MISA gộp theo phiếu, join một lượt cho cả trang
    misa_by_req = service.misa_codes_by_request(db, [p.id for p in items])
    out = [{c: getattr(p, c) for c in HEADER}
           | {"total": float(p.total or 0), "created_by_name": resolve_actor(db, p.created_by),
              "misa_code": misa_by_req.get(p.id, ""),
              "updated_at": p.updated_at}   # bao-CR-294 — cột "Ngày cập nhật" ở màn danh sách
           for p in items]
    return success({"total": total, "items": out})


@router.get("/export/xlsx")
def export_xlsx(request: Request, db: Session = Depends(get_db),
                user=Depends(require("payment_request", "export"))):
    """bao-CR-525 — xuất Excel THEO DÒNG CHI TIẾT: phiếu đúng bộ lọc + phạm vi màn danh sách,
    mỗi dòng PO / hóa đơn một hàng, thông tin phiếu lặp lại (xem `export.py`). Trần số dòng
    tính trên số DÒNG xuất ra, không phải số phiếu."""
    from app.core.export_xlsx import check_row_limit, parse_ids, xlsx_response

    from . import export as ex

    q = _list_query(db, request, user, "export")
    #  Khung xuất Excel dùng chung của bản cũ (CR-068) gửi kèm `ids` các phiếu đang tick:
    #  có thì chỉ xuất các phiếu đó (vẫn trong phạm vi), rỗng thì theo bộ lọc. `cols` của
    #  khung đó bỏ qua — cột màn danh sách là cột PHIẾU, tệp này là cột DÒNG.
    ids = parse_ids(request.query_params.get("ids"))
    if ids:
        q = q.filter(PaymentRequest.id.in_(ids))
    q = apply_sort_from_request(q, PaymentRequest, request, default=PaymentRequest.id.desc())
    pairs = ex.load_lines(db, q.all())
    check_row_limit(len(pairs))
    return xlsx_response(ex.FILE_NAME, ex.COLS, ex.build_rows(db, pairs), ex.SHEET_TITLE)


# CR-268 — LƯU Ý thứ tự route: /hanging PHẢI đứng TRƯỚC /{rid}, nếu không FastAPI
# đem "hanging" đi parse int cho tham số rid và trả 422.
@router.get("/hanging")
def get_hanging_(supplier_code: str, po_code: str = "", unlinked: int = 0,
                 source_type: str = "goods", db: Session = Depends(get_db),
                 user=Depends(require("payment_request", "read"))):
    """CR-268 — tiền treo (phiếu trả trước đã chi, chưa đối trừ/hoàn hết) của 1 NCC.

    - `po_code=POxxxxx` -> chỉ treo gắn đúng đơn đó (màn chi tiết ĐMH).
    - `unlinked=1`      -> chỉ treo CẤP NCC không gắn đơn (nút cấn trừ ở màn Công nợ).
    - Không truyền gì   -> toàn bộ treo của NCC."""
    pc = (po_code or "").strip() or ("" if unlinked else None)
    return success(service.summarize_hanging(db, supplier_code.strip(), source_type, pc))


@router.get("/meta/department-managers")
def department_managers_(db: Session = Depends(get_db),
                         user=Depends(require("payment_request", "read"))):
    """bao-CR-553 — ô «Trưởng bộ phận» của YCTT: trưởng phòng mọi phòng (có Ban Giám đốc).
    Khai TRƯỚC `/{rid}`, nếu không FastAPI đem «meta» đi parse int."""
    from app.core.approver_candidates import department_managers
    return success({"items": department_managers(db)})


@router.get("/{rid}")
def get_(rid: int, db: Session = Depends(get_db), user=Depends(require("payment_request", "read"))):
    req = apply_scope(db.query(PaymentRequest).filter(PaymentRequest.id == rid),
                      PaymentRequest, "payment_request", user, get_perm_profile(db, user)).first()
    if not req:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    return success(_out(db, req))


@router.get("/{rid}/print")
def print_(rid: int, db: Session = Depends(get_db), user=Depends(require("payment_request", "print"))):
    # Khóa `print` chỉ trả lời "được in hay không", không trả lời "được in phiếu NÀO":
    # bản in còn RỘNG hơn màn chi tiết (tên pháp nhân, MST, **số tài khoản ngân hàng NCC**,
    # chức vụ + trưởng phòng người lập), nên nó phải chịu phạm vi ít nhất bằng đường xem.
    req = _scoped(db, rid, user, "print")
    data = _out(db, req)
    company = db.get(Company, req.company_id) if req.company_id else None
    data["company"] = {"name": company.name, "address": company.address,
                       "tax_code": company.tax_code} if company else {}
    prof = resolve_actor_profile(db, req.created_by)
    data["created_by_name"] = prof["name"]
    data["created_by_position"] = prof["position"]     # Chức vụ
    data["created_by_dept"] = prof["department"]        # Bộ phận
    # bao-CR-553: ô «Trưởng bộ phận» của phiếu thắng (chị Mi duyệt nhưng bản in nội bộ ghi anh
    # Dững); để trống thì vẫn là trưởng phòng của người lập như trước.
    data["dept_manager"] = (req.head_of_dept or "").strip() or prof["manager"]   # Trưởng phòng ban/bộ phận
    # Thông tin ngân hàng NCC (khớp theo mã NCC) để in mục HÌNH THỨC THANH TOÁN.
    # CR-035: phiếu chi TIỀN MẶT thì cụm chuyển khoản để trống — chặn ngay từ server,
    # không gửi số TK ra bản in.
    method = service.norm_method(req.payment_method)
    data["payment_method"] = method
    sup = db.query(Supplier).filter(Supplier.code == req.supplier_code).first() if req.supplier_code else None
    data["bank_account"] = (sup.bank_account if sup else "") if method == "transfer" else ""
    data["bank_name"] = (sup.bank_name if sup else "") if method == "transfer" else ""
    data["period"] = (req.request_date or "")[:7]  # YYYY-MM
    return success(data)


@router.post("")
def create_(data: PRequestCreate, db: Session = Depends(get_db),
            user=Depends(require("payment_request", "create"))):
    # bao-CR-274 — khoản nợ gắn vào phiếu phải nằm trong phạm vi `payable` người tạo được
    # xem: service lấy theo id (`db.get`) nên bỏ qua lọc phạm vi, gõ thẳng id qua API là
    # kéo được nợ của pháp nhân khác vào phiếu dù màn Công nợ không hiển thị khoản đó.
    from app.modules.payable.model import Payable

    ids = {ln.payable_id for ln in data.lines if ln.payable_id}
    if ids:
        visible = {pid for (pid,) in apply_scope(
            db.query(Payable.id).filter(Payable.id.in_(ids)), Payable, "payable",
            user, get_perm_profile(db, user)).all()}
        if ids - visible:
            raise HTTPException(403, "Có khoản công nợ ngoài phạm vi bạn được xem — "
                                     "không đưa vào phiếu được")
    reqs = service.create_requests(db, data, user.id)
    return success([_out(db, r) for r in reqs],
                   f"Đã tạo {len(reqs)} phiếu yêu cầu thanh toán", 201)


@router.patch("/{rid}")
def update_(rid: int, data: PRequestUpdate, db: Session = Depends(get_db),
            user=Depends(require("payment_request", "write"))):
    _scoped(db, rid, user, "write")
    return success(_out(db, service.update_request(db, rid, data, user.id)), "Đã cập nhật")


@router.get("/{rid}/refresh-preview")
def refresh_preview_(rid: int, db: Session = Depends(get_db),
                     user=Depends(require("payment_request", "read"))):
    """bao-CR-509 — XEM TRƯỚC số mới của từng dòng theo công nợ hiện tại, KHÔNG ghi gì.

    Mở cho người có quyền xem (người duyệt xem được phiếu chờ duyệt lệch chỗ nào);
    `can_apply` / `blocked_reason` cho biết có được bấm ghi hay không."""
    req = _scoped(db, rid, user, "read")
    return success(service.plan_refresh(db, req))


@router.post("/{rid}/refresh-from-payables")
def refresh_apply_(rid: int, db: Session = Depends(get_db),
                   user=Depends(require("payment_request", "write"))):
    """bao-CR-509 — GHI số mới theo công nợ vào phiếu NHÁP (tính lại từ DB lúc ghi)."""
    _scoped(db, rid, user, "write")
    req, plan = service.apply_refresh(db, rid, user.id)
    n = plan["changed_count"]
    msg = f"Đã cập nhật {n} dòng theo công nợ" if n else "Phiếu đã khớp công nợ, không có gì thay đổi"
    return success(_out(db, req), msg)


@router.delete("/{rid}")
def delete_(rid: int, db: Session = Depends(get_db), user=Depends(require("payment_request", "delete"))):
    _scoped(db, rid, user, "delete")
    service.delete_request(db, rid, user.id)
    return success(None, "Đã xóa")


@router.delete("")
def bulk_delete_requests(ids: str, db: Session = Depends(get_db), user=Depends(require("payment_request", "delete"))):
    id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
    if not id_list:
        raise HTTPException(400, "Không có ID hợp lệ")
    # Lọc phạm vi TRƯỚC vòng lặp (khuôn `contract/controller.py`): xóa hàng loạt mà chỉ
    # `db.get` theo id thì gửi đại một dãy id là xóa được phiếu của pháp nhân khác.
    rows = apply_scope(
        db.query(PaymentRequest).filter(PaymentRequest.id.in_(id_list)),
        PaymentRequest, "payment_request", user, get_perm_profile(db, user), "delete").all()
    if not rows:
        raise HTTPException(403, "Ngoài phạm vi được phép xóa")
    #  bao-CR-547: kiểm CẢ LÔ trước khi xóa phiếu nào — chỉ phiếu Nháp (đại ca chốt 01/10/2026).
    ensure_all_draft(rows, "phiếu yêu cầu thanh toán")
    in_scope = [r.id for r in rows]
    for rid in in_scope:
        try:
            service.delete_request(db, rid, user.id)
        except Exception as e:
            raise HTTPException(400, f"Lỗi khi xóa phiếu ID {rid}: {str(e)}")
    # Báo đúng số ĐÃ xóa, không báo số đã gửi lên — lệch nhau là có id ngoài phạm vi.
    return success(None, f"Đã xóa {len(in_scope)} bản ghi")


def _notify_pay(db, background_tasks, r, event, reason=""):
    trigger_notification(db=db, event=event, doc_type="payment_request", doc_code=r.code,
                         creator_id=r.created_by or 0, background_tasks=background_tasks,
                         reason=reason, link=f"/payment-requests/{r.id}")


@router.post("/{rid}/submit")
def submit_(rid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
            user=Depends(require("payment_request", "write"))):
    _scoped(db, rid, user, "write")
    r = service.set_status(db, rid, "submitted", user.id)
    _notify_pay(db, background_tasks, r, "pay_submitted")
    return success(_out(db, r), "Đã gửi duyệt")


@router.post("/{rid}/approve")
def approve_(rid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
             user=Depends(require("payment_request", "approve"))):
    _scoped(db, rid, user, "approve")
    r = service.set_status(db, rid, "approved", user.id)
    _notify_pay(db, background_tasks, r, "pay_approved")
    return success(_out(db, r), "Đã duyệt")


@router.post("/{rid}/reject")
def reject_(rid: int, data: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
            user=Depends(require("payment_request", "approve"))):
    """Từ chối phiếu yêu cầu thanh toán (khóa) — người duyệt thao tác. Body: {reason}."""
    reason = (data.get("reason") or "").strip()
    _scoped(db, rid, user, "approve")   # từ chối đi cùng cổng với duyệt
    r = service.set_status(db, rid, "cancelled", user.id, reason)
    _notify_pay(db, background_tasks, r, "pay_rejected", reason)
    return success(_out(db, r), "Đã từ chối")


@router.post("/{rid}/pay")
def pay_(rid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
         user=Depends(require("payment_request", "write"))):
    _scoped(db, rid, user, "write")
    r = service.set_status(db, rid, "paid", user.id)
    _notify_pay(db, background_tasks, r, "pay_paid")
    return success(_out(db, r), "Đã ghi nhận chi")


@router.post("/{rid}/refund")
def refund_(rid: int, data: dict, db: Session = Depends(get_db),
            user=Depends(require("payment_request", "write"))):
    """CR-268 — ghi nhận NCC HOÀN TIỀN phần treo của phiếu trả trước đã chi.

    Body: {amount, note} — amount bỏ trống/0 nghĩa là hoàn toàn bộ phần còn treo."""
    amount = float(data.get("amount") or 0)
    note = (data.get("note") or "").strip()
    _scoped(db, rid, user, "write")
    taken = service.record_refund(db, rid, amount, note, user.id)
    return success(_out(db, service.get_request(db, rid)),
                   f"Đã ghi nhận NCC hoàn {taken:,.0f} đ")
