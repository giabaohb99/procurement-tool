"""NGHIỆP VỤ PHIẾU THANH TOÁN NGHỈ PHÉP (duoc-CR-719): tính số được thanh toán · lập · sửa · xóa · chiếm trạng thái.

Phần đổi trạng thái có đụng quỹ (gửi duyệt · duyệt · từ chối · hủy) nằm ở `encashment_transitions`; tệp này giữ phần
đọc/tính và vòng đời Nháp. Khuôn của `comp_request_service`.

Luật chung:
  * Mọi đổi trạng thái đi qua `claim` (UPDATE … WHERE status IN …, thua -> 409) — hai lượt bấm cùng lúc không trừ quỹ hai lần.
  * Một phiếu còn hiệu lực / (người, loại, năm, lý do): khóa UNIQUE `active_key` (NULL khi Từ chối / Hủy / xóa).
  * Kết sổ cuối năm (`carryover_service`) KHÔNG sửa: ngày đang giữ chỗ / đã thanh toán không nằm trong `remaining_days`
    nên không bị mang đi. Phiếu bị từ chối SAU khi kết sổ thì ngày trả lại quỹ năm cũ và lượt kết sổ sau vét nốt
    (hành vi sẵn có của `carried_out_days`).
"""
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.utils import generate_code
from app.core.vn_time import vn_today
from app.modules.employee.model import Employee

from . import encashment_math, request_service
from .catalog_model import LeaveType
from .constants import ENCASH_EDITABLE_STATUSES, LeaveEncashmentReason, LeaveEncashmentStatus
from .encashment_balance import compute, get_row
from .encashment_model import LeaveEncashment

ENTITY = "leave_encashment"
CODE_PREFIX = "TTP"
CONFLICT_MESSAGE = "Phiếu vừa được xử lý bởi lượt khác — tải lại trang"
FILTERABLE = ["status", "employee_id", "company_id", "department_id", "leave_type_id", "balance_year", "reason_kind"]
#  Trạng thái HẾT hiệu lực: `active_key` về NULL để người đó lập lại được.
INACTIVE_STATUSES = (LeaveEncashmentStatus.REJECTED, LeaveEncashmentStatus.CANCELLED)


def build_active_key(employee_id: int, leave_type_id: int, year: int, reason_kind: int) -> str:
    """Khóa "còn hiệu lực": mỗi (người, loại, năm, LÝ DO) một phiếu — để khoản Nghỉ việc bắt buộc theo luật vẫn lập được
    sau khi đã thanh toán phép dư cuối năm (duoc-CR-719 M2)."""
    return f"{employee_id}:{leave_type_id}:{year}:{int(reason_kind)}"


def duplicate_error(year: int, reason_kind: int) -> HTTPException:
    reason = "nghỉ việc" if int(reason_kind) == int(LeaveEncashmentReason.RESIGNATION) else "cuối năm"
    return HTTPException(409, f"Đã có phiếu thanh toán nghỉ phép năm {year} lý do {reason} còn hiệu lực của người này "
                              "cho loại nghỉ này. Chỉ hủy (hoặc bị từ chối) phiếu đó thì mới lập được phiếu mới "
                              "cùng loại, năm và lý do.")


def try_claim(db: Session, obj: LeaveEncashment, expected, new: LeaveEncashmentStatus, **values) -> bool:
    """CHIẾM phiếu nguyên tử: `UPDATE … SET status=new WHERE id AND status IN (expected)`. `True` = thắng. Không commit.

    Giá trị đi kèm ghi trong CHÍNH câu UPDATE (gán lên đối tượng rồi commit sau khi thua sẽ ghi đè kết quả người thắng).
    Trạng thái hết hiệu lực -> `active_key` = NULL.
    """
    values["status"] = int(new)
    if int(new) in [int(s) for s in INACTIVE_STATUSES]:
        values["active_key"] = None
    won = (db.query(LeaveEncashment)
           .filter(LeaveEncashment.id == obj.id, LeaveEncashment.is_deleted.is_(False),
                   LeaveEncashment.status.in_([int(s) for s in expected]))
           .update(values, synchronize_session=False))
    db.refresh(obj)    # không `flush` trước: UPDATE đã chạy, flush sẽ ghi lại trạng thái CŨ của đối tượng lượt thua
    return won == 1


def claim(db: Session, obj: LeaveEncashment, expected, new: LeaveEncashmentStatus, **values) -> None:
    """Như `try_claim` nhưng thua thì 409."""
    if not try_claim(db, obj, expected, new, **values):
        raise HTTPException(409, CONFLICT_MESSAGE)


def check_editable(obj: LeaveEncashment) -> None:
    if obj.status not in [int(s) for s in ENCASH_EDITABLE_STATUSES]:
        raise HTTPException(400, "Phiếu đã gửi duyệt nên không sửa được. Rút phiếu khỏi luồng duyệt hoặc hủy phiếu rồi lập lại.")


# ───────────────────────────── kiểm đầu vào ─────────────────────────────

def load_leave_type(db: Session, leave_type_id: int) -> LeaveType:
    """Loại nghỉ đang dùng, bật thanh toán và trừ quỹ — nếu không 422."""
    leave_type = db.get(LeaveType, leave_type_id) if leave_type_id else None
    if leave_type is None or not leave_type.is_active:
        raise HTTPException(422, "Loại nghỉ không tồn tại hoặc đã ngừng dùng")
    if not leave_type.counts_balance or not leave_type.allow_encashment:
        raise HTTPException(422, f"Loại nghỉ \"{leave_type.name}\" không cho thanh toán ra tiền. Nhân sự bật "
                                 "\"Cho phép thanh toán nghỉ phép\" ở Thiết lập nghỉ phép ▸ Loại nghỉ nếu cần.")
    return leave_type


def check_year(year: int) -> None:
    this_year = vn_today().year
    if year not in (this_year, this_year - 1):
        raise HTTPException(422, f"Chỉ thanh toán được quỹ phép năm {this_year} hoặc năm {this_year - 1}")


def check_reason(employee: Employee, reason_kind: int) -> None:
    resign = int(LeaveEncashmentReason.RESIGNATION)
    if int(reason_kind) == resign and employee.resign_date is None:
        raise HTTPException(422, "Nhập ngày nghỉ việc trên hồ sơ nhân sự trước khi thanh toán phép theo lý do nghỉ việc")
    if (employee.status or "") == "resigned" and int(reason_kind) != resign:
        raise HTTPException(422, "Nhân sự đã nghỉ việc chỉ được thanh toán theo lý do Nghỉ việc")


def check_days(days: float, encashable: float) -> float:
    value = round(float(days), 2)
    if value <= 0 or not encashment_math.is_on_step(value):
        raise HTTPException(422, "Số ngày thanh toán phải lớn hơn 0 và theo bước 0,5 ngày")
    if value > encashable + 1e-9:
        raise HTTPException(
            422, f"Số ngày thanh toán ({value:g}) vượt số được phép ({encashable:g} ngày) theo luật của loại nghỉ")
    return value


def _find_active(db: Session, key: str) -> LeaveEncashment | None:
    return (db.query(LeaveEncashment)
            .filter(LeaveEncashment.active_key == key, LeaveEncashment.is_deleted.is_(False)).first())


# ───────────────────────────── vòng đời Nháp ─────────────────────────────

def create(db: Session, data, user) -> LeaveEncashment:
    """Lập phiếu — luôn ở **Nháp**. Chưa giữ chỗ gì (giữ chỗ lúc gửi duyệt)."""
    employee = request_service.resolve_leave_taker(db, user, data.employee_id)
    request_service.ensure_can_create_for(db, user, employee, ENTITY)
    leave_type = load_leave_type(db, data.leave_type_id)
    year = data.balance_year or vn_today().year
    check_year(year)
    check_reason(employee, data.reason_kind)
    key = build_active_key(employee.id, leave_type.id, year, data.reason_kind)
    if _find_active(db, key) is not None:
        raise duplicate_error(year, data.reason_kind)
    row = get_row(db, employee, leave_type, year)     # chỉ đọc: quỹ năm nay chưa có thì tính ra 0, không tự cấp
    if row is None and year != vn_today().year:
        raise HTTPException(422, f"Chưa có quỹ phép \"{leave_type.name}\" năm {year} của người này để thanh toán")
    info = compute(db, row, leave_type, data.reason_kind)
    wanted = data.days if data.days is not None else info["encashable"]
    if wanted <= 0:
        _no_days_error(leave_type)
    days = check_days(wanted, info["encashable"])
    obj = LeaveEncashment(
        code=generate_code(db, LeaveEncashment, CODE_PREFIX),
        company_id=employee.company_id or 0, department_id=employee.department_id or 0, employee_id=employee.id,
        leave_type_id=leave_type.id, balance_year=year, reason_kind=int(data.reason_kind),
        encashment_date=data.encashment_date or vn_today(), days=days, balance_snapshot=info["available"],
        encashable_snapshot=info["encashable"], note=(data.note or "").strip(), active_key=key,
        status=int(LeaveEncashmentStatus.DRAFT), created_by=user.id, updated_by=user.id)
    db.add(obj)
    try:
        db.commit()
    except IntegrityError:    # hai lượt lập cùng (người, loại, năm, lý do): lượt sau thua ở khóa UNIQUE `active_key`
        db.rollback()
        raise duplicate_error(year, data.reason_kind)
    db.refresh(obj)
    return obj


def _no_days_error(leave_type: LeaveType) -> None:
    raise HTTPException(422, f"Hiện không còn ngày phép \"{leave_type.name}\" nào được thanh toán "
                             "(đã trừ phần giữ lại, phần mang sang chưa dùng và trần năm)")


def update(db: Session, obj: LeaveEncashment, data, user) -> LeaveEncashment:
    """Sửa phiếu Nháp / Trả về: lý do, ngày thanh toán, số ngày, ghi chú. Người, loại nghỉ, năm quỹ giữ nguyên."""
    check_editable(obj)
    employee = request_service.get_employee(db, obj.employee_id)
    request_service.ensure_can_create_for(db, user, employee, ENTITY)
    leave_type = load_leave_type(db, obj.leave_type_id)
    reason_kind = int(data.reason_kind if data.reason_kind is not None else obj.reason_kind)
    check_reason(employee, reason_kind)
    check_year(obj.balance_year)
    #  Đổi lý do là đổi `active_key` (khóa gồm lý do) — kiểm trùng với phiếu còn hiệu lực khác.
    key = build_active_key(obj.employee_id, obj.leave_type_id, obj.balance_year, reason_kind)
    if key != obj.active_key:
        other = _find_active(db, key)
        if other is not None and other.id != obj.id:
            raise duplicate_error(obj.balance_year, reason_kind)
    info = compute(db, get_row(db, employee, leave_type, obj.balance_year), leave_type, reason_kind)
    days = check_days(data.days if data.days is not None else obj.days, info["encashable"])
    claim(db, obj, ENCASH_EDITABLE_STATUSES, LeaveEncashmentStatus(obj.status), reason_kind=reason_kind, active_key=key,
          encashment_date=data.encashment_date or obj.encashment_date, days=days,
          note=(data.note.strip() if data.note is not None else obj.note), balance_snapshot=info["available"],
          encashable_snapshot=info["encashable"], updated_by=user.id)
    try:
        db.commit()
    except IntegrityError:    # lượt khác vừa lập phiếu cùng khóa
        db.rollback()
        raise duplicate_error(obj.balance_year, reason_kind)
    db.refresh(obj)
    return obj


def soft_delete(db: Session, obj: LeaveEncashment, user) -> None:
    """Xóa mềm — chỉ Nháp (nhả `active_key`). Đã gửi / đã duyệt là hồ sơ, phải HỦY."""
    if obj.status != int(LeaveEncashmentStatus.DRAFT):
        raise HTTPException(400, "Chỉ xóa được phiếu nháp. Phiếu đã gửi duyệt thì hủy phiếu.")
    claim(db, obj, (LeaveEncashmentStatus.DRAFT,), LeaveEncashmentStatus.DRAFT, is_deleted=True, active_key=None,
          updated_by=user.id)
    db.commit()
