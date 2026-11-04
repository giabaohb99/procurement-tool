"""API CHÍNH SÁCH NGHỈ PHÉP (duoc-CR-717): gói chính sách + dòng của gói.

Gác bằng khóa `leave_type` (D4: không thêm khóa quyền) — chính sách là danh mục nền cùng "Thiết lập" nghỉ phép.
Sửa dòng của gói KHÔNG tự tính lại quỹ đã cấp (luật CR-715): chỉ áp cho lần cấp sau / lần tính lại ở phân bổ.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record
from app.core.auth import require
from app.core.crud import make_crud_router
from app.core.database import get_db
from app.core.response import success

from .catalog_model import LeaveType
from .policy_allocation import with_row_lock
from .policy_model import LeavePolicy, LeavePolicyAssignment, LeavePolicyLine
from .policy_schema import (PolicyCreate, PolicyLineResponse, PolicyLinesReplace, PolicyResponse,
                            PolicyUpdate)

ENTITY = "leave_type"
#  Nhật ký ghi dưới tên riêng (quyền vẫn là `leave_type`) — xem `make_crud_router(audit_entity=)`.
AUDIT_ENTITY = "leave_policy"


def _block_delete_assigned(db: Session, obj: LeavePolicy) -> None:
    """Chốt `before_delete`: gói còn phân bổ thì không xóa (để lại phân bổ mồ côi); xóa được thì dọn dòng của gói."""
    #  Khóa ĐỘC QUYỀN dòng gói rồi mới đếm phân bổ bằng đọc có khóa: tạo phân bổ khóa DÙNG CHUNG cùng dòng này
    #  (`policy_assignment_service.lock_policy`) nên hai bên không thể cùng qua chốt (review L4).
    with_row_lock(db, db.query(LeavePolicy.id).filter(LeavePolicy.id == obj.id), exclusive=True).first()
    count = len({row[0] for row in with_row_lock(db, db.query(LeavePolicyAssignment.employee_id).filter(
        LeavePolicyAssignment.policy_id == obj.id)).all()})
    if count:
        raise HTTPException(
            409, f"Chính sách đang được phân bổ cho {count} nhân sự — kết thúc / xóa phân bổ trước.")
    db.query(LeavePolicyLine).filter(LeavePolicyLine.policy_id == obj.id).delete(synchronize_session=False)


policy_router = make_crud_router(
    "/api/leave-policies", ENTITY, LeavePolicy,
    PolicyCreate, PolicyUpdate, PolicyResponse,
    filterable=["code", "name", "is_active"],
    unique_field="code",
    before_delete=_block_delete_assigned,
    audit_entity=AUDIT_ENTITY,
)

lines_router = APIRouter(prefix="/api/leave-policies", tags=["leave"])


def _list_lines(db: Session, policy_id: int) -> dict:
    rows = (db.query(LeavePolicyLine).filter(LeavePolicyLine.policy_id == policy_id)
            .order_by(LeavePolicyLine.leave_type_id).all())
    return {"total": len(rows), "items": [PolicyLineResponse.model_validate(r).model_dump() for r in rows]}


def _fmt_lines(lines: dict[int, float], names: dict[int, str]) -> str:
    return "; ".join(f"{names.get(tid, '#' + str(tid))}: {days:g}" for tid, days in sorted(lines.items())) or "trống"


def _require_policy(db: Session, policy_id: int) -> LeavePolicy:
    obj = db.query(LeavePolicy).filter(LeavePolicy.id == policy_id).first()
    if obj is None:
        raise HTTPException(404, "Không tìm thấy chính sách nghỉ phép")
    return obj


@lines_router.get("/{policy_id}/lines")
def list_lines(policy_id: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    """Dòng của gói (loại nghỉ → số ngày/năm). Không phân trang (trần 50 dòng)."""
    _require_policy(db, policy_id)
    return success(_list_lines(db, policy_id))


@lines_router.put("/{policy_id}/lines")
def replace_lines(policy_id: int, data: PolicyLinesReplace, db: Session = Depends(get_db),
                  user=Depends(require(ENTITY, "write"))):
    """THAY cả danh sách dòng. Loại phải trừ quỹ phép và không phải loại nghỉ bù; mỗi loại một dòng."""
    policy = _require_policy(db, policy_id)
    ids = [item.leave_type_id for item in data.items]
    if len(set(ids)) != len(ids):
        raise HTTPException(422, "Mỗi loại nghỉ chỉ được khai một dòng — có loại bị trùng.")
    types = {t.id: t for t in db.query(LeaveType).filter(LeaveType.id.in_(ids or [0])).all()}
    for type_id in ids:
        leave_type = types.get(type_id)
        if leave_type is None:
            raise HTTPException(422, f"Loại nghỉ #{type_id} không tồn tại.")
        if not leave_type.counts_balance:
            raise HTTPException(422, f"Loại nghỉ \"{leave_type.name}\" không trừ vào quỹ phép nên không đưa vào chính sách được.")
        if leave_type.is_compensatory:
            raise HTTPException(422, f"Loại nghỉ \"{leave_type.name}\" là nghỉ bù — số ngày do phiếu nghỉ bù cộng, không đưa vào chính sách.")
    try:
        #  Khóa dòng gói: hai PUT cùng lúc nối đuôi nhau (không vỡ UNIQUE policy/loại), và PUT không lọt giữa
        #  "xóa gói" với "tạo phân bổ".
        with_row_lock(db, db.query(LeavePolicy.id).filter(LeavePolicy.id == policy_id), exclusive=True).first()
        old = {row.leave_type_id: float(row.annual_days or 0.0) for row in with_row_lock(
            db, db.query(LeavePolicyLine).filter(LeavePolicyLine.policy_id == policy_id), exclusive=True).all()}
        db.query(LeavePolicyLine).filter(LeavePolicyLine.policy_id == policy_id).delete(synchronize_session=False)
        for item in data.items:
            db.add(LeavePolicyLine(policy_id=policy_id, leave_type_id=item.leave_type_id,
                                   annual_days=item.annual_days, created_by=user.id, updated_by=user.id))
        #  `query.delete()` đi vòng nhật ký thay đổi nên số CŨ chỉ còn trong câu audit này (cùng giao dịch với ghi).
        names = {t.id: t.name for t in db.query(LeaveType).filter(LeaveType.id.in_(set(old) | set(ids) or {0})).all()}
        audit_record(db, user.id, AUDIT_ENTITY, policy_id, "update",
                     f"Cập nhật dòng của chính sách \"{policy.name}\": trước [{_fmt_lines(old, names)}] → "
                     f"sau [{_fmt_lines({i.leave_type_id: i.annual_days for i in data.items}, names)}]",
                     commit=False)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Dòng của chính sách vừa được người khác sửa — tải lại rồi thử lại.")
    except Exception:
        db.rollback()
        raise
    return success(_list_lines(db, policy_id))
