"""ĐỔI TRẠNG THÁI PHIẾU THANH TOÁN NGHỈ PHÉP có đụng quỹ (duoc-CR-719): gửi duyệt · duyệt · từ chối/trả về/rút · hủy.

Quỹ chạy theo bốn nhịp, mỗi nhịp sau một lần CHIẾM phiếu (`encashment_service.claim`):

    gửi duyệt            pending_days  += days                      (giữ chỗ, khóa dòng quỹ)
    duyệt                pending_days  -= days, encashed_days += days, sinh YCTT Nháp (số tiền do kế toán nhập)
    từ chối/trả về/rút   pending_days  -= days                      (MỘT hàm `release_and_set`, không chép ba bản)
    hủy phiếu đã duyệt   encashed_days -= days, xóa mềm YCTT nếu còn Nháp; chặn nếu kế toán đã vào cuộc (D7a)
"""
import logging
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.core.audit import record
from app.modules.payment_request import leave_encashment_payout as payout

from . import balance_service, encashment_math, encashment_service as service, request_service
from .encashment_balance import compute, get_row
from .constants import LeaveEncashmentStatus as S
from .encashment_model import LeaveEncashment
from .encashment_serializer import cancel_block_message

log = logging.getLogger("app.leave.encashment")
EDITABLE = service.ENCASH_EDITABLE_STATUSES


def prepare_submit(db: Session, obj: LeaveEncashment, user) -> None:
    """Gửi duyệt: kiểm lại trên số quỹ ĐÃ KHÓA, chiếm phiếu (Nháp/Trả về -> Chờ duyệt) rồi giữ chỗ. Chưa commit.

    Người gọi trình bộ máy duyệt rồi commit chung; lỗi giữa chừng thì giao dịch cuộn lại (phiếu về như cũ).
    """
    service.check_editable(obj)
    employee = request_service.get_employee(db, obj.employee_id)
    leave_type = service.load_leave_type(db, obj.leave_type_id)
    service.check_year(obj.balance_year)
    service.check_reason(employee, obj.reason_kind)
    row = get_row(db, employee, leave_type, obj.balance_year, lock=True, actor=user.id)
    if row is None:
        raise HTTPException(422, f"Chưa có quỹ phép \"{leave_type.name}\" năm {obj.balance_year} để thanh toán")
    info = compute(db, row, leave_type, obj.reason_kind)
    days = service.check_days(obj.days, info["encashable"])
    service.claim(db, obj, EDITABLE, S.PENDING, days=days, balance_snapshot=info["available"],
                  encashable_snapshot=info["encashable"], decision_note="", updated_by=user.id)
    row.pending_days = round((row.pending_days or 0.0) + days, 2)
    row.updated_by = user.id
    db.flush()


def release_and_set(db: Session, obj: LeaveEncashment, new: S, *, strict: bool, decision_note: str = "",
                    actor: int = 0) -> bool:
    """Từ chối / trả về / rút / hủy phiếu ĐANG CHỜ: chiếm Chờ duyệt -> `new` rồi TRẢ phần giữ chỗ. Một hàm cho cả ba.

    `strict` = thua thì 409 (đường thẳng); không strict = bỏ qua im lặng (hook bộ máy duyệt). Trả `True` nếu thắng.
    """
    values = {"decision_note": (decision_note or "")[:500], "decided_at": datetime.now(), "updated_by": actor}
    if new == S.DRAFT:
        values["decided_at"] = None
    if not service.try_claim(db, obj, (S.PENDING,), new, **values):
        if strict:
            raise HTTPException(409, service.CONFLICT_MESSAGE)
        return False
    balance_service.release(db, obj.employee_id, obj.balance_year, obj.leave_type_id, obj.days, actor)
    db.flush()
    return True


def _notify_after_commit(db: Session, payment_request_id: int) -> None:
    """Chuông kế toán chỉ gửi SAU KHI giao dịch duyệt đã commit (`trigger_notification` tự commit). Đăng ký một lần
    trên phiên; chạy bằng phiên MỚI cùng kết nối vì `after_commit` không cho phát SQL trên phiên đang commit."""
    from app.modules.payment_request.model import PaymentRequest

    bind = db.get_bind()
    done: list[bool] = []

    def run(session) -> None:
        #  Savepoint nhả cũng phát `after_commit`: lúc đó YCTT chưa commit thật, phiên mới không thấy -> chuông mất
        #  im lặng. Bỏ qua (giữ listener) và chờ lượt commit thật; chạy một lần duy nhất khi commit thật (L4).
        if session.in_nested_transaction():
            return
        if done:             # chạy đúng một lần; không gỡ listener giữa lúc phát sự kiện (sửa danh sách đang duyệt)
            return
        done.append(True)
        try:
            with Session(bind=bind) as fresh:
                req = fresh.get(PaymentRequest, payment_request_id)
                if req is not None and not req.is_deleted:
                    payout.notify_payout_created(fresh, req)
        except Exception:    # noqa: BLE001 — chuông hỏng không được làm hỏng việc đã duyệt
            log.exception("Không gửi được chuông YCTT thanh toán nghỉ phép (id %s)", payment_request_id)

    event.listen(db, "after_commit", run)


def approve_now(db: Session, obj: LeaveEncashment, actor: int, error_cls=HTTPException) -> None:
    """DUYỆT thật: chiếm (Chờ duyệt -> Đã duyệt), chuyển ngày giữ chỗ sang đã thanh toán, sinh YCTT Nháp. Chưa commit.

    `error_cls` = `HookVeto` khi gọi từ bộ máy duyệt (lỗi thường bị `fire` NUỐT -> phiên Đã duyệt mà phiếu Chờ duyệt),
    `HTTPException` khi duyệt thẳng. Mọi lỗi sau khi chiếm đều ném lại để cả giao dịch cuộn.
    """
    #  Thứ tự khóa THỐNG NHẤT với từ chối / hủy: dòng phiếu trước, dòng quỹ sau (L1) — hai người bấm Duyệt và Từ chối
    #  cùng lúc thì một người nhận 409 chứ không đụng deadlock. Kiểm dòng quỹ có mặt (không khóa) TRƯỚC khi chiếm:
    #  hook phải ném trước khi đổi gì.
    if balance_service.get_balance(db, obj.employee_id, obj.balance_year, obj.leave_type_id) is None:
        raise error_cls(422, "Không tìm thấy dòng quỹ phép để trừ ngày thanh toán")
    if not service.try_claim(db, obj, (S.PENDING,), S.APPROVED, decided_at=datetime.now(), decision_note="",
                             updated_by=actor):
        raise error_cls(409, service.CONFLICT_MESSAGE)
    try:
        row = balance_service.get_balance(db, obj.employee_id, obj.balance_year, obj.leave_type_id, for_update=True)
        if row is None:
            raise error_cls(422, "Không tìm thấy dòng quỹ phép để trừ ngày thanh toán")
        #  M1: phần ngày lấy từ mang sang (chỉ lý do Nghỉ việc) — chốt trên phiếu để hủy trả đúng, và để quỹ qua hạn
        #  mang sang không bị thu hồi lần hai.
        carried = encashment_math.carried_part(
            obj.days, row.carried_days, row.used_days, max(0.0, (row.pending_days or 0.0) - obj.days),
            row.encashed_carried_days, obj.reason_kind)
        obj.carried_paid_days = carried
        row.encashed_carried_days = round((row.encashed_carried_days or 0.0) + carried, 2)
        row.pending_days = round(max(0.0, (row.pending_days or 0.0) - obj.days), 2)
        row.encashed_days = round((row.encashed_days or 0.0) + obj.days, 2)
        row.updated_by = actor
        employee = request_service.get_employee(db, obj.employee_id)
        req = payout.create_payout_request(db, obj, employee, actor)
        obj.payment_request_id = req.id
        db.flush()
        record(db, actor, service.ENTITY, obj.id, "approve",
               f"Duyệt phiếu thanh toán nghỉ phép {obj.code}, sinh YCTT {req.code}", commit=False)
        _notify_after_commit(db, req.id)
    except Exception as error:   # noqa: BLE001 — đã chiếm phiếu: hỏng ở đây phải làm cả giao dịch cuộn lại
        raise error_cls(getattr(error, "status_code", 500),
                        getattr(error, "detail", "Không duyệt được phiếu thanh toán nghỉ phép")) from error


def _check_payout_allows_cancel(db: Session, obj: LeaveEncashment) -> dict | None:
    """D7a: phiếu Đã duyệt chỉ hủy được khi YCTT chưa ai đụng (Nháp) hoặc kế toán đã từ chối. Đọc YCTT CÓ KHÓA."""
    state = payout.payout_state(db, obj.payment_request_id, lock=True)
    if not payout.payout_allows_cancel(state):
        raise HTTPException(400, cancel_block_message(state))
    return state


def cancel(db: Session, obj: LeaveEncashment, reason: str, actor: int) -> LeaveEncashment:
    """Hủy: Nháp / Chờ duyệt / Trả về -> Đã hủy (Chờ duyệt thì trả giữ chỗ); Đã duyệt -> trả ngày đã thanh toán (D7a)."""
    status = obj.status
    if status == int(S.CANCELLED):
        return obj
    if status == int(S.REJECTED):
        raise HTTPException(400, "Phiếu đã bị từ chối, không cần hủy")
    state = _check_payout_allows_cancel(db, obj) if status == int(S.APPROVED) else None
    values = {"decision_note": (reason or "")[:500], "decided_at": datetime.now(), "updated_by": actor}
    service.claim(db, obj, (S(status),), S.CANCELLED, **values)
    try:
        if status == int(S.PENDING):
            balance_service.release(db, obj.employee_id, obj.balance_year, obj.leave_type_id, obj.days, actor)
        elif status == int(S.APPROVED):
            row = balance_service.get_balance(db, obj.employee_id, obj.balance_year, obj.leave_type_id,
                                              for_update=True)
            if row is not None:
                row.encashed_days = round(max(0.0, (row.encashed_days or 0.0) - obj.days), 2)
                row.encashed_carried_days = round(
                    max(0.0, (row.encashed_carried_days or 0.0) - (obj.carried_paid_days or 0.0)), 2)
                row.updated_by = actor
            if state is not None and state["status"] == "draft":
                payout.void_draft_payout(db, obj.payment_request_id, actor)
    except HTTPException:
        db.rollback()    # trả phiếu về "Đã duyệt" — không để nửa chừng
        raise
    db.commit()
    db.refresh(obj)
    return obj
