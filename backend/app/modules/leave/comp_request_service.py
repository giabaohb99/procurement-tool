"""NGHIỆP VỤ PHIẾU XIN NGHỈ BÙ (duoc-CR-715 C): lập · sửa · xóa · gửi duyệt · hủy, và cộng / trừ `comp_days`.

Luật chốt khi lập và khi gửi: ngày đi làm ≤ hôm nay; là ngày lễ HOẶC ngày nghỉ theo lịch làm việc của người đó
(`workday_service.count_leave_days` = 0 cho cả hai); một ngày một phiếu; số ngày 0.5 hoặc 1.
"""
from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.utils import generate_code
from app.core.vn_time import vn_today
from app.modules.employee.model import Employee

from . import balance_service, request_service, workday_service
from .catalog_model import LeaveType
from .comp_request_model import LeaveCompRequest
from .constants import (COMP_ACTIVE_STATUSES, COMP_DAYS_ALLOWED, COMP_EDITABLE_STATUSES,
                        LeaveCompStatus)

#  Hai trạng thái HẾT hiệu lực: phiếu ở đó không giữ "ngày đã có phiếu" (`active_key` = NULL).
INACTIVE_STATUSES = (LeaveCompStatus.REJECTED, LeaveCompStatus.CANCELLED)
CONFLICT_MESSAGE = "Phiếu vừa được xử lý bởi lượt khác — tải lại trang"

CODE_PREFIX = "NB"
ENTITY = "leave_comp_request"
FILTERABLE = ["status", "employee_id", "company_id", "department_id"]


def get_comp_type(db: Session) -> LeaveType:
    """Loại nghỉ NHẬN ngày bù: đang dùng + bật `is_compensatory` + trừ quỹ, `sort_order` nhỏ nhất."""
    lt = (db.query(LeaveType)
          .filter(LeaveType.is_active.is_(True), LeaveType.is_compensatory.is_(True),
                  LeaveType.counts_balance.is_(True))
          .order_by(LeaveType.sort_order, LeaveType.id).first())
    if lt is None:
        raise HTTPException(
            422, "Chưa có loại nghỉ nào bật \"Loại nhận ngày nghỉ bù\". Nhân sự vào Thiết lập nghỉ phép ▸ Loại nghỉ, "
                 "bật \"Loại nhận ngày nghỉ bù\" (kèm \"Trừ vào quỹ phép\") cho một loại rồi lập lại phiếu.")
    return lt


def resolve_credit_type(db: Session, obj: LeaveCompRequest) -> LeaveType:
    """Loại nghỉ ĐÃ CHỐT trên phiếu (lúc gửi duyệt) — còn dùng được không. Không dò lại danh mục: đổi danh mục
    giữa lúc chờ duyệt không được làm ngày bù rơi sang loại khác. Hết hợp lệ → 422 (hook bộ máy đổi thành `HookVeto`)."""
    leave_type = db.get(LeaveType, obj.comp_leave_type_id) if obj.comp_leave_type_id else None
    if leave_type is None:
        raise HTTPException(422, "Phiếu chưa chốt loại nghỉ nhận ngày bù. Gửi duyệt lại phiếu để chốt loại.")
    if not (leave_type.is_active and leave_type.is_compensatory and leave_type.counts_balance):
        raise HTTPException(
            422, f"Loại nghỉ \"{leave_type.name}\" chốt trên phiếu không còn là \"Loại nhận ngày nghỉ bù\" đang dùng. "
                 "Nhân sự bật lại loại đó (Thiết lập nghỉ phép ▸ Loại nghỉ) rồi duyệt lại.")
    return leave_type


def build_active_key(employee_id: int, work_date: date) -> str:
    return f"{employee_id}:{work_date.isoformat()}"


def duplicate_error(work_date: date) -> HTTPException:
    return HTTPException(409, f"Ngày {work_date:%d/%m/%Y} đã có phiếu nghỉ bù khác còn hiệu lực — mỗi ngày một phiếu")


def try_claim(db: Session, obj: LeaveCompRequest, expected, new: LeaveCompStatus, **values) -> bool:
    """CHIẾM phiếu nguyên tử: `UPDATE … SET status=new WHERE id AND status IN (expected)`. `True` = thắng.

    Mọi bước đổi trạng thái (gửi · duyệt · từ chối · hủy · rút · sửa · xóa) phải đi qua đây: hai lượt bấm cùng lúc
    mà cùng đọc "Chờ duyệt" rồi cùng cộng ngày bù thì phiếu một ngày thành hai ngày nghỉ. Giá trị đi kèm ghi trong
    CHÍNH câu UPDATE (không gán lên đối tượng rồi commit — gán sau khi thua sẽ ghi đè kết quả của người thắng).
    Phiếu về trạng thái hết hiệu lực thì `active_key` về NULL để ngày đó được lập phiếu khác. Không commit.
    """
    values["status"] = int(new)
    if int(new) in [int(s) for s in INACTIVE_STATUSES]:
        values["active_key"] = None
    try:
        won = (db.query(LeaveCompRequest)
               .filter(LeaveCompRequest.id == obj.id, LeaveCompRequest.is_deleted.is_(False),
                       LeaveCompRequest.status.in_([int(s) for s in expected]))
               .update(values, synchronize_session=False))
    except IntegrityError:
        #  `active_key` UNIQUE: lượt sửa ngày này thua lượt lập phiếu cùng ngày.
        db.rollback()
        raise duplicate_error(values.get("work_date") or obj.work_date)
    #  Không `flush` ở đây: UPDATE đã chạy ngay, còn flush sẽ ghi luôn trạng thái CŨ nằm trên đối tượng của lượt thua.
    db.refresh(obj)
    return won == 1


def claim(db: Session, obj: LeaveCompRequest, expected, new: LeaveCompStatus, **values) -> None:
    """Như `try_claim` nhưng thua thì 409 "Phiếu vừa được xử lý bởi lượt khác"."""
    if not try_claim(db, obj, expected, new, **values):
        raise HTTPException(409, CONFLICT_MESSAGE)


def check_days(days: float) -> float:
    value = round(float(days), 2)
    if value not in COMP_DAYS_ALLOWED:
        raise HTTPException(422, "Số ngày nghỉ bù chỉ nhận 0,5 hoặc 1 ngày")
    return value


def check_work_date(db: Session, employee: Employee, work_date: date, exclude_id: int = 0) -> None:
    """Chốt ngày đi làm: không ở tương lai, phải là ngày lễ / ngày nghỉ theo lịch, và chưa có phiếu khác."""
    today = vn_today()
    if work_date > today:
        raise HTTPException(422, "Ngày đi làm không được ở tương lai — đi làm xong mới xin nghỉ bù")
    #  Năm đã kết sổ từ lâu không nhận thêm ngày bù — chỉ xin cho năm nay và năm ngoái.
    if work_date < date(today.year - 1, 1, 1):
        raise HTTPException(
            422, f"Ngày đi làm quá cũ — chỉ xin nghỉ bù cho ngày từ 01/01/{today.year - 1} trở đi")
    if workday_service.count_leave_days(db, work_date, work_date, company_id=int(employee.company_id or 0),
                                        employee=employee) > 0:
        raise HTTPException(
            422, "Ngày này là ngày làm việc bình thường của bạn nên không có ngày nghỉ bù. "
                 "Chỉ xin được cho ngày lễ hoặc ngày nghỉ theo lịch làm việc.")
    dup = (db.query(LeaveCompRequest.code)
           .filter(LeaveCompRequest.employee_id == employee.id, LeaveCompRequest.work_date == work_date,
                   LeaveCompRequest.is_deleted.is_(False), LeaveCompRequest.id != exclude_id,
                   LeaveCompRequest.status.in_([int(s) for s in COMP_ACTIVE_STATUSES])).first())
    if dup:
        raise HTTPException(409, f"Ngày {work_date:%d/%m/%Y} đã có phiếu nghỉ bù {dup[0]} — mỗi ngày một phiếu")


def check_editable(obj: LeaveCompRequest) -> None:
    if obj.status not in [int(s) for s in COMP_EDITABLE_STATUSES]:
        raise HTTPException(400, "Phiếu đã gửi duyệt nên không sửa được. Rút phiếu duyệt hoặc hủy phiếu rồi lập lại.")


def create(db: Session, data, user) -> LeaveCompRequest:
    """Lập phiếu — luôn ở **Nháp**."""
    employee = request_service.resolve_leave_taker(db, user, data.employee_id)
    request_service.ensure_can_create_for(db, user, employee, ENTITY)
    get_comp_type(db)
    days = check_days(data.days)
    check_work_date(db, employee, data.work_date)
    obj = LeaveCompRequest(
        code=generate_code(db, LeaveCompRequest, CODE_PREFIX),
        company_id=employee.company_id or 0, department_id=employee.department_id or 0,
        employee_id=employee.id, work_date=data.work_date, days=days, reason=(data.reason or "").strip(),
        active_key=build_active_key(employee.id, data.work_date),
        status=int(LeaveCompStatus.DRAFT), created_by=user.id, updated_by=user.id)
    db.add(obj)
    try:
        db.commit()
    except IntegrityError:    # hai lượt lập cùng ngày: lượt sau thua ở khóa UNIQUE `active_key`
        db.rollback()
        raise duplicate_error(data.work_date)
    db.refresh(obj)
    return obj


def update(db: Session, obj: LeaveCompRequest, data, user) -> LeaveCompRequest:
    check_editable(obj)
    employee = request_service.get_employee(db, obj.employee_id)
    request_service.ensure_can_create_for(db, user, employee, ENTITY)
    work_date = data.work_date or obj.work_date
    days = check_days(data.days if data.days is not None else obj.days)
    check_work_date(db, employee, work_date, exclude_id=obj.id)
    claim(db, obj, COMP_EDITABLE_STATUSES, LeaveCompStatus(obj.status), work_date=work_date, days=days,
          reason=(data.reason.strip() if data.reason is not None else obj.reason),
          active_key=build_active_key(employee.id, work_date), updated_by=user.id)
    db.commit()
    db.refresh(obj)
    return obj


def soft_delete(db: Session, obj: LeaveCompRequest, user) -> None:
    """Xóa mềm — chỉ Nháp. Đã gửi / đã duyệt là hồ sơ, phải HỦY."""
    if obj.status != int(LeaveCompStatus.DRAFT):
        raise HTTPException(400, "Chỉ xóa được phiếu nháp. Phiếu đã gửi duyệt thì hủy phiếu.")
    claim(db, obj, (LeaveCompStatus.DRAFT,), LeaveCompStatus.DRAFT, is_deleted=True, active_key=None,
          updated_by=user.id)
    db.commit()


def prepare_submit(db: Session, obj: LeaveCompRequest, user=None) -> Employee:
    """Chốt chặn bước GỬI DUYỆT, rồi CHIẾM phiếu (Nháp / Trả về → Chờ duyệt) và chốt loại nhận ngày bù.

    Chưa commit: người gọi trình bộ máy duyệt (`start` commit cùng lúc) rồi `mark_submitted`. Lỗi giữa chừng thì
    giao dịch cuộn lại và phiếu về như cũ.
    """
    check_editable(obj)
    if not (obj.reason or "").strip():
        raise HTTPException(422, "Nhập lý do (đi làm việc gì) trước khi gửi duyệt")
    comp_type = get_comp_type(db)
    employee = request_service.get_employee(db, obj.employee_id)
    check_days(obj.days)
    check_work_date(db, employee, obj.work_date, exclude_id=obj.id)
    claim(db, obj, COMP_EDITABLE_STATUSES, LeaveCompStatus.PENDING, comp_leave_type_id=comp_type.id,
          decision_note="", updated_by=getattr(user, "id", None) or obj.updated_by)
    return employee


def mark_submitted(db: Session, obj: LeaveCompRequest, user, instance_id: int = 0) -> LeaveCompRequest:
    """Ghi mã phiên duyệt sau khi đã trình bộ máy. KHÔNG đụng `status` (bộ máy có thể đã duyệt xong ngay)."""
    obj.approval_instance_id = instance_id
    obj.updated_by = user.id
    db.commit()
    db.refresh(obj)
    return obj


def grant_days(db: Session, obj: LeaveCompRequest, actor: int) -> None:
    """Duyệt xong: cộng `days` vào `comp_days` của loại + năm ĐÃ CHỐT trên phiếu (`balance_year` đặt lúc duyệt)."""
    leave_type = resolve_credit_type(db, obj)
    employee = request_service.get_employee(db, obj.employee_id)
    row = balance_service.ensure_balance(db, employee, obj.balance_year, leave_type, actor, for_update=True)
    row.comp_days = round((row.comp_days or 0.0) + obj.days, 2)
    row.updated_by = actor
    db.flush()


def revoke_days(db: Session, obj: LeaveCompRequest, actor: int) -> None:
    """Hủy phiếu ĐÃ DUYỆT: trừ lại đúng loại + năm đã cộng — chỉ khi phần còn lại ≥ `days`, nếu không 422.
    Không dò lại danh mục: loại nhận ngày bù có thể đã đổi từ lúc duyệt."""
    row = (balance_service.get_balance(db, obj.employee_id, obj.balance_year, obj.comp_leave_type_id, for_update=True)
           if obj.comp_leave_type_id and obj.balance_year else None)
    if row is None:
        raise HTTPException(422, "Không hủy được: không tìm thấy dòng quỹ nghỉ bù đã nhận ngày của phiếu này.")
    if balance_service.available_days(db, row) + 1e-9 < obj.days:
        raise HTTPException(
            422, f"Không hủy được: ngày nghỉ bù của phiếu này ({obj.days:g} ngày) đã được dùng để nghỉ. "
                 "Hủy hoặc sửa đơn nghỉ đã dùng quỹ này trước.")
    row.comp_days = round((row.comp_days or 0.0) - obj.days, 2)
    row.updated_by = actor
    db.flush()


def cancel(db: Session, obj: LeaveCompRequest, reason: str, actor: int) -> LeaveCompRequest:
    """Hủy: Nháp / Chờ duyệt / Trả về → Đã hủy; Đã duyệt → trừ lại `comp_days` nếu còn đủ."""
    if obj.status == int(LeaveCompStatus.CANCELLED):
        return obj
    if obj.status == int(LeaveCompStatus.REJECTED):
        raise HTTPException(400, "Phiếu đã bị từ chối, không cần hủy")
    was_approved = obj.status == int(LeaveCompStatus.APPROVED)
    #  Chiếm TRƯỚC (đúng trạng thái vừa đọc) rồi mới trừ quỹ: hai lượt hủy cùng lúc thì chỉ một lượt thắng, lượt kia
    #  nhận 409 mà không trừ quỹ lần hai.
    claim(db, obj, (LeaveCompStatus(obj.status),), LeaveCompStatus.CANCELLED,
          decision_note=(reason or "")[:500], decided_at=datetime.now(), updated_by=actor)
    if was_approved:
        try:
            revoke_days(db, obj, actor)
        except HTTPException:
            db.rollback()    # trả phiếu về "Đã duyệt" — không để nửa chừng
            raise
    db.commit()
    db.refresh(obj)
    return obj
