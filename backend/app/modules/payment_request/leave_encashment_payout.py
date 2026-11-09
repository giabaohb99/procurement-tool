"""YCTT NGUỒN THANH TOÁN NGHỈ PHÉP (duoc-CR-719, phase 02).

YCTT này CHỈ do máy tạo khi phiếu thanh toán nghỉ phép được duyệt (không nằm trong `SOURCE_TYPES` nên người dùng
không chọn được qua API tạo phiếu). Người nhận là nhân sự (`payee_employee_id`), không có NCC, một dòng duy nhất,
tiền = 0 lúc tạo; kế toán nhập số tiền rồi đi đúng luồng Nháp -> Chờ duyệt -> Đã duyệt -> Đã chi như mọi YCTT.

Gom luật của nguồn này vào MỘT tệp để `service.py` / `controller.py` chỉ gọi, không rải nhánh khắp nơi.

Bốn hàm phase 03 (phiếu thanh toán nghỉ phép) gọi: `create_payout_request`, `payout_state`, `void_draft_payout`,
`payout_allows_cancel`. Hàm thứ năm `notify_payout_created` phải gọi SAU KHI commit (nó commit chuông).
"""
import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.base_model import mark_deleted
from app.core.vn_time import vn_today

from .hr_payout_guard import PAYMENT_SOURCE_LEAVE_ENCASHMENT
from .model import PaymentRequest, PaymentRequestLine

log = logging.getLogger("app.payment_request.leave_encashment")

ENTITY = "payment_request"

#  Trần số tiền một dòng (đồng). Cột là Numeric(18,2); chặn ở đây để nhập nhầm thừa số 0 trả 400 chứ không phải 500.
MAX_PAYOUT_AMOUNT = 9_999_999_999_999

#  Trường của PRequestUpdate mà YCTT nguồn nghỉ phép nhận (kèm `lines` đúng một dòng, chỉ lấy `amount`).
PAYOUT_EDITABLE_FIELDS = frozenset({"request_date", "note", "payment_method", "print_texts",
                                    "head_of_dept_id", "head_of_dept", "lines"})

MSG_NO_DELETE = ("YCTT thanh toán nghỉ phép không xóa ở đây — hủy phiếu thanh toán nghỉ phép bên Nghỉ phép")
MSG_ENTER_AMOUNT = "Nhập số tiền thanh toán nghỉ phép trước khi gửi duyệt"


def is_payout(req: PaymentRequest) -> bool:
    """Phiếu là YCTT nguồn thanh toán nghỉ phép."""
    return (req.source_type or "") == PAYMENT_SOURCE_LEAVE_ENCASHMENT


# ───────────────────────────── 1. tạo / đọc / hủy (hợp đồng phase 03) ─────────────────────────────

def _fmt_days(days) -> str:
    return f"{float(days or 0):g}"


def create_payout_request(db: Session, encashment, employee, actor: int) -> PaymentRequest:
    """Sinh YCTT Nháp (tiền 0) cho phiếu thanh toán nghỉ phép đã duyệt. CHỈ flush, KHÔNG commit.

    `created_by = 0` (máy tạo): không lọt phạm vi "của tôi" của người duyệt phiếu nghỉ; người thao tác ghi ở
    `updated_by`. Mỗi phiếu nguồn chỉ có MỘT YCTT còn sống — gọi lần hai thì 400 (không sinh trùng).
    """
    from app.modules.leave.catalog_model import LeaveType

    if employee is None or not getattr(employee, "id", None):
        raise HTTPException(400, "Không tìm thấy nhân sự nhận thanh toán nghỉ phép")
    if not getattr(encashment, "id", None):
        db.flush()   # phiếu mới tạo trong cùng giao dịch: cần id để gắn nguồn
    dup = db.query(PaymentRequest.id).filter(
        PaymentRequest.source_type == PAYMENT_SOURCE_LEAVE_ENCASHMENT,
        PaymentRequest.source_ref_id == encashment.id,
        PaymentRequest.is_deleted.is_(False)).first()
    if dup:
        raise HTTPException(400, "Phiếu thanh toán nghỉ phép này đã có yêu cầu thanh toán")

    leave_type = db.get(LeaveType, encashment.leave_type_id) if encashment.leave_type_id else None
    type_name = leave_type.name if leave_type else "nghỉ phép"
    note = (f"Thanh toán {_fmt_days(encashment.days)} ngày {type_name} năm {encashment.balance_year}"
            f" — phiếu {encashment.code}")
    req = PaymentRequest(
        supplier_code="", supplier_name=f"{employee.full_name} ({employee.code})"[:255],
        company_id=int(employee.company_id or 0), department_id=int(employee.department_id or 0),
        source_type=PAYMENT_SOURCE_LEAVE_ENCASHMENT, payee_employee_id=employee.id,
        source_ref_id=encashment.id, request_date=vn_today().isoformat(), status="draft",
        payment_method="transfer", prepay=0, total=0, note=note,
        created_by=0, updated_by=int(actor or 0))
    db.add(req)
    db.flush()
    req.code = f"YCTT{req.id:05d}"
    db.add(PaymentRequestLine(request_id=req.id, payable_id=0, po_code=encashment.code, amount=0,
                              created_by=0, updated_by=int(actor or 0)))
    db.flush()
    record(db, int(actor or 0), ENTITY, req.id, "create",
           f"Tự sinh từ phiếu thanh toán nghỉ phép {encashment.code}", commit=False)
    return req


def payout_state(db: Session, payment_request_id: int, *, lock: bool = False) -> dict | None:
    """Trạng thái YCTT cho phiếu thanh toán nghỉ phép đọc ra: `{id, code, status, status_label, total}`.

    `None` khi id = 0 hoặc YCTT đã bị xóa mềm / không còn. `lock=True` đọc CÓ KHÓA hàng YCTT (MySQL `FOR UPDATE`):
    dùng ở đường hủy phiếu để kế toán không kịp gửi duyệt YCTT giữa lúc kiểm và lúc hủy."""
    from . import service

    if not payment_request_id:
        return None
    if lock and db.bind is not None and db.bind.dialect.name in ("mysql", "postgresql"):
        req = (db.query(PaymentRequest).filter(PaymentRequest.id == int(payment_request_id))
               .with_for_update().populate_existing().first())
    else:
        req = db.get(PaymentRequest, int(payment_request_id))
    if req is None or req.is_deleted:
        return None
    return {"id": req.id, "code": req.code, "status": req.status,
            "status_label": service.STATUS_LABELS.get(req.status, req.status),
            "total": float(req.total or 0)}


def payout_allows_cancel(state: dict | None) -> bool:
    """Hủy phiếu thanh toán nghỉ phép (trả ngày về quỹ) chỉ khi YCTT không còn / còn Nháp / Đã từ chối.

    Chờ duyệt, Đã duyệt, Đã chi thì kế toán đã vào cuộc hoặc tiền đã đi -> không hủy."""
    return state is None or state.get("status") in ("draft", "cancelled")


def void_draft_payout(db: Session, payment_request_id: int, actor: int) -> None:
    """Xóa mềm YCTT nguồn nghỉ phép khi nó còn Nháp (lúc hủy phiếu thanh toán nghỉ phép). KHÔNG commit.

    Không còn YCTT (id 0 / đã xóa) thì không làm gì. Khác Nháp -> 400. Chỉ xóa YCTT đúng nguồn nghỉ phép."""
    if not payment_request_id:
        return
    req = db.get(PaymentRequest, int(payment_request_id))
    if req is None or req.is_deleted:
        return
    if not is_payout(req):
        raise HTTPException(400, "Đây không phải YCTT thanh toán nghỉ phép")
    if req.status != "draft":
        raise HTTPException(400, "YCTT thanh toán nghỉ phép không còn ở trạng thái Nháp — "
                                 "không hủy được phiếu khi kế toán đã gửi duyệt hoặc đã chi")
    mark_deleted(req, int(actor or 0))
    db.flush()
    record(db, int(actor or 0), ENTITY, req.id, "delete",
           f"Xóa mềm YCTT {req.code} do hủy phiếu thanh toán nghỉ phép", commit=False)


def notify_payout_created(db: Session, req: PaymentRequest, background_tasks=None) -> None:
    """Chuông báo kế toán có YCTT thanh toán nghỉ phép cần nhập số tiền. GỌI SAU KHI COMMIT (hàm này commit chuông).

    Người nhận = người duyệt YCTT (luật 3 của `get_approvers_for_entity`: không có thì rơi về quản trị), đã lọc theo
    phạm vi nên người không thấy phiếu không bị báo. Nội dung chuông KHÔNG có số tiền. Lỗi chuông không làm hỏng việc
    chính (YCTT đã commit): ghi log, không nuốt im."""
    from app.modules.notification.service import trigger_notification

    try:
        trigger_notification(db=db, event="pay_leave_created", doc_type=ENTITY, doc_code=req.code,
                             creator_id=0, background_tasks=background_tasks,
                             link=f"/payment-requests/{req.id}", doc_id=req.id)
    except Exception:
        db.rollback()
        log.exception("Không gửi được chuông YCTT thanh toán nghỉ phép %s", req.code)


def notify_payout_outcome(db: Session, req: PaymentRequest, event: str, background_tasks=None, reason: str = "") -> None:
    """Chuông khi YCTT nghỉ phép được CHI (`pay_paid`) hoặc bị kế toán TỪ CHỐI (`pay_rejected`).

    YCTT này có `created_by = 0` nên chuông mặc định không tới ai. Đã chi: báo chính nhân sự nhận tiền (tài khoản của
    họ), chữ trơn không số tiền. Bị từ chối: báo người đã duyệt phiếu thanh toán nghỉ phép và người lập phiếu để Nhân
    sự xử lý (hủy phiếu trả ngày, hoặc nhờ kế toán lập lại). Lỗi chuông chỉ ghi log. Gọi SAU khi YCTT đã commit."""
    from app.modules.leave.encashment_model import LeaveEncashment
    from app.modules.notification.service import trigger_notification
    from app.modules.user.model import User

    try:
        if event == "pay_paid":
            user_ids = [u for (u,) in db.query(User.id).filter(User.employee_id == req.payee_employee_id,
                                                               User.is_active.is_(True)).all()] \
                if req.payee_employee_id else []
            ev = "pay_leave_paid"
        else:
            form = db.get(LeaveEncashment, req.source_ref_id) if req.source_ref_id else None
            user_ids = sorted({int(i) for i in ((form.updated_by, form.created_by) if form else ()) if i})
            ev = "pay_leave_rejected"
        if not user_ids:
            return
        trigger_notification(db=db, event=ev, doc_type=ENTITY, doc_code=req.code, creator_id=0,
                             background_tasks=background_tasks, reason="",   # L6: lý do kế toán có thể chứa số tiền
                             link=f"/hr/leave-encashments/{req.source_ref_id}",
                             doc_id=req.id, recipient_ids=user_ids)
    except Exception:
        db.rollback()
        log.exception("Không gửi được chuông kết quả YCTT thanh toán nghỉ phép %s", req.code)


# ───────────────────────────── 1b. chốt người nhận + khóa dòng (service gọi) ─────────────────────────────

MSG_SELF_PAYOUT = ("Không tự xử lý yêu cầu thanh toán nghỉ phép của chính mình — nhờ người khác trong bộ phận "
                   "kế toán thực hiện")


def ensure_not_payee(db: Session, req: PaymentRequest, user_id: int) -> None:
    """duoc-CR-719 H1: người NHẬN tiền không được sửa / gửi duyệt / duyệt / từ chối / ghi chi YCTT của chính mình,
    bất kể quyền `payment_request` (kể cả quản trị nếu họ chính là người nhận). Chốt ở tầng service nên phủ cả web,
    v1 lẫn công cụ AI. Tài khoản chưa gắn hồ sơ nhân sự (employee_id = 0) không thể là người nhận -> bỏ qua."""
    from app.modules.user.model import User

    if not is_payout(req) or not req.payee_employee_id or not user_id:
        return
    emp = db.query(User.employee_id).filter(User.id == int(user_id)).scalar() or 0
    if emp and int(emp) == int(req.payee_employee_id):
        raise HTTPException(403, MSG_SELF_PAYOUT)


def lock_live_payout(db: Session, rid: int) -> PaymentRequest:
    """duoc-CR-719 L2: đọc lại YCTT nguồn nghỉ phép CÓ KHÓA dòng (MySQL `FOR UPDATE`) và từ chối nếu đã xóa mềm.

    Hủy phiếu thanh toán nghỉ phép khóa cùng dòng này; có khóa hai chiều thì "hủy" và "gửi duyệt" đua nhau không thể
    để lại trạng thái Chờ duyệt trên YCTT đã xóa. SQLite (bài kiểm) bỏ qua `FOR UPDATE`."""
    q = db.query(PaymentRequest).filter(PaymentRequest.id == int(rid)).populate_existing()
    if db.bind is not None and db.bind.dialect.name in ("mysql", "postgresql"):
        q = q.with_for_update()
    req = q.first()
    if req is None or req.is_deleted:
        raise HTTPException(404, "Không tìm thấy phiếu yêu cầu thanh toán")
    return req


# ───────────────────────────── 2. luật sửa / gửi duyệt (service gọi) ─────────────────────────────

def apply_payout_update(db: Session, req: PaymentRequest, fields: dict, lines, user_id: int) -> None:
    """Soát payload sửa YCTT nguồn nghỉ phép + ghi số tiền của dòng duy nhất; ném 400 nếu đụng ngoài phạm vi.

    `fields` = `data.model_dump(exclude_unset=True)`; `lines` = `data.lines` (None = không đụng tiền).
    Chỉ nhận ô ở `PAYOUT_EDITABLE_FIELDS`; `prepay` chỉ chấp nhận giá trị 0 (màn gửi lại nguyên form)."""
    extra = set(fields) - PAYOUT_EDITABLE_FIELDS - {"prepay"}
    if extra or fields.get("prepay"):
        raise HTTPException(400, "YCTT thanh toán nghỉ phép chỉ sửa được ngày đề nghị, ghi chú, hình thức "
                                 "thanh toán, câu chữ bản in, trưởng bộ phận và số tiền")
    if lines is None:
        return
    existing = db.query(PaymentRequestLine).filter(PaymentRequestLine.request_id == req.id).all()
    if len(lines) != 1 or len(existing) != 1:
        raise HTTPException(400, "YCTT thanh toán nghỉ phép chỉ có đúng một dòng — không thêm hay bớt dòng")
    new, old = lines[0], existing[0]
    if int(new.payable_id or 0) != 0:
        raise HTTPException(400, "YCTT thanh toán nghỉ phép không gắn công nợ")
    if (new.po_code or "").strip() not in ("", old.po_code or ""):
        raise HTTPException(400, "Không đổi được mã phiếu thanh toán nghỉ phép trên dòng")
    if new.offset_amount not in (None, 0):
        raise HTTPException(400, "YCTT thanh toán nghỉ phép không có phần cấn trừ")
    amount = round(float(new.amount or 0), 2)
    if amount < 0 or amount > MAX_PAYOUT_AMOUNT:
        raise HTTPException(400, "Số tiền thanh toán nghỉ phép không hợp lệ")
    old.amount = amount
    old.updated_by = user_id
    req.total = amount


def check_payout_submit(db: Session, req: PaymentRequest) -> None:
    """Điều kiện GỬI DUYỆT của nguồn nghỉ phép: một dòng, số tiền > 0, không cấn trừ, không trả trước.

    Bỏ hẳn việc khớp công nợ (nguồn này không có công nợ)."""
    lines = db.query(PaymentRequestLine).filter(PaymentRequestLine.request_id == req.id).all()
    if len(lines) != 1:
        raise HTTPException(400, "YCTT thanh toán nghỉ phép phải có đúng một dòng")
    if req.prepay:
        raise HTTPException(400, "YCTT thanh toán nghỉ phép không phải phiếu thanh toán trước")
    if float(lines[0].offset_amount or 0) > 0.01:
        raise HTTPException(400, "YCTT thanh toán nghỉ phép không có phần cấn trừ")
    if float(lines[0].amount or 0) <= 0:
        raise HTTPException(400, MSG_ENTER_AMOUNT)


def mark_payout_paid(db: Session, req: PaymentRequest) -> None:
    """Ghi nhận Đã chi cho nguồn nghỉ phép: không có công nợ để trừ, chỉ chốt `allocated_amount = amount`."""
    for ln in db.query(PaymentRequestLine).filter(PaymentRequestLine.request_id == req.id).all():
        ln.allocated_amount = round(float(ln.amount or 0), 2)


# ───────────────────────────── 3. đọc ra (controller gọi) ─────────────────────────────

def leave_encashment_block(db: Session, req: PaymentRequest) -> dict | None:
    """Khối `leave_encashment` của `_out`: `{id, code, days, leave_type_name, balance_year, reason_kind}` — một
    truy vấn. Không có lương, không có số tài khoản. `None` khi phiếu không phải nguồn nghỉ phép / phiếu nguồn mất."""
    from app.modules.leave.catalog_model import LeaveType
    from app.modules.leave.encashment_model import LeaveEncashment

    if not is_payout(req) or not req.source_ref_id:
        return None
    row = (db.query(LeaveEncashment.id, LeaveEncashment.code, LeaveEncashment.days,
                    LeaveType.name, LeaveEncashment.balance_year, LeaveEncashment.reason_kind)
           .outerjoin(LeaveType, LeaveType.id == LeaveEncashment.leave_type_id)
           .filter(LeaveEncashment.id == req.source_ref_id).first())
    if row is None:
        return None
    return {"id": row[0], "code": row[1], "days": float(row[2] or 0), "leave_type_name": row[3] or "",
            "balance_year": int(row[4] or 0), "reason_kind": int(row[5] or 0)}


def print_payee_info(db: Session, req: PaymentRequest, profile: dict, method: str) -> dict:
    """Phần riêng của BẢN IN nguồn nghỉ phép (D2a): người nhận + số tài khoản.

    Số tài khoản lấy từ hồ sơ nhân sự CHỈ khi hình thức là chuyển khoản VÀ người in có `employee_sensitive.read`
    hoặc chính là nhân sự nhận; ngược lại để trống và đặt `bank_hidden = True` (kế toán tự điền)."""
    from app.modules.employee.model import Employee
    from app.modules.employee.sensitive import can_read_sensitive

    emp = db.get(Employee, req.payee_employee_id) if req.payee_employee_id else None
    out = {"payee": {"employee_id": emp.id if emp else 0, "code": emp.code if emp else "",
                     "full_name": emp.full_name if emp else req.supplier_name},
           "bank_account": "", "bank_name": "", "bank_hidden": False}
    if method == "transfer" and emp is not None:
        if can_read_sensitive(profile, emp.id):
            out["bank_account"] = emp.bank_account_no or ""
            out["bank_name"] = emp.bank_name or ""
        else:
            out["bank_hidden"] = True
    return out
