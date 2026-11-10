"""API PHIẾU THANH TOÁN NGHỈ PHÉP — `/api/leave-encashments` (duoc-CR-719). Khuôn của `comp_request_controller`.

Phiếu chỉ ghi SỐ NGÀY; số tiền nằm ở YCTT sinh ra khi duyệt và chỉ hiện cho người được phép (xem `encashment_serializer`).
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record, resolve_actor
from app.core.auth import get_current_user, get_perm_profile, require
from app.core.base_controller import apply_filters, apply_sort_from_request, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, get_scoped
from app.core.vn_time import vn_today
from app.modules.approval import steps_service, task_service
from app.modules.approval.self_approval_policy import ensure_not_self_approval
from app.modules.employee.model import Employee

from . import encashment_approval_bridge as bridge, encashment_balance, encashment_serializer as view
from . import comp_encashment_sort_expressions as sort_expr
from . import encashment_service as service
from . import encashment_transitions as transitions, request_service
from .constants import LEAVE_ENCASHMENT_REASON_LABELS, LeaveEncashmentReason, LeaveEncashmentStatus as S, label
from .encashment_model import LeaveEncashment
from .encashment_schema import LeaveEncashmentCreate, LeaveEncashmentUpdate

router = APIRouter(prefix="/api/leave-encashments", tags=["leave"])
ENTITY = service.ENTITY


def _get_or_404(db: Session, rid: int, user, action: str = "read") -> LeaveEncashment:
    obj = get_scoped(db, LeaveEncashment, ENTITY, rid, user, get_perm_profile(db, user), action)
    #  Người ĐANG được giao ký đọc được phiếu dù phạm vi không với tới (như đơn nghỉ, CR-260) — chỉ cho `read`.
    if obj is None and action == "read" and bridge.can_read_request(db, rid, user):
        obj = db.get(LeaveEncashment, rid)
    if obj is None or obj.is_deleted:
        raise HTTPException(404, "Không tìm thấy phiếu thanh toán nghỉ phép")
    return obj


def _one(db: Session, obj: LeaveEncashment) -> dict:
    return view.dump_many(db, [obj])[0]


@router.get("")
def list_encashments(request: Request, pg: dict = Depends(pagination), q: str | None = None,
                     db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    """Danh sách phiếu thanh toán nghỉ phép trong phạm vi người xem.

    Quyền: `leave_encashment.read` (phạm vi của người xem). Lọc: `status`, `employee_id`, `company_id`, `department_id`,
    `leave_type_id`, `balance_year`, `reason_kind`, `q` (mã / tên nhân sự / ghi chú). Kèm trạng thái chi, không có số tiền.
    """
    query = db.query(LeaveEncashment).filter(LeaveEncashment.is_deleted.is_(False))
    query = apply_filters(query, LeaveEncashment, request, service.FILTERABLE, {})
    if q and q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(or_(LeaveEncashment.code.like(like), LeaveEncashment.note.like(like),
                                 LeaveEncashment.employee_id.in_(
                                     db.query(Employee.id).filter(Employee.full_name.like(like)))))
    query = apply_scope(query, LeaveEncashment, ENTITY, user, get_perm_profile(db, user))
    #  duoc-CR-744: cột đang hiện xếp qua `comp_encashment_sort_expressions` (tên nhân sự / loại nghỉ, hạng trạng
    #  thái chi, ô trống xuống cuối, khóa phụ `id`); khóa khác về đường cũ.
    order = sort_expr.build_encashment_order_by(request.query_params.get("sort_by") or "",
                                                request.query_params.get("sort_dir") or "asc")
    query = query.order_by(*order) if order else apply_sort_from_request(
        query, LeaveEncashment, request, default=(LeaveEncashment.id.desc(),))
    total = query.count()
    items = query.offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": total, "items": view.dump_many(db, items)})


@router.get("/to-approve")
def to_approve(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Phiếu ĐANG chờ chính tôi ký (kèm `task` = việc của tôi, `flow` = luồng duyệt). Đăng ký TRƯỚC `/{rid}`.

    Quyền: đăng nhập; chỉ trả phiếu có việc duyệt treo cho nhân sự của tài khoản này.
    """
    tasks = task_service.my_tasks(db, getattr(user, "employee_id", 0) or 0, ENTITY)
    ids = [t.get("entity_id") for t in tasks if t.get("entity_id")]
    rows = {o.id: o for o in db.query(LeaveEncashment).filter(
        LeaveEncashment.id.in_(ids), LeaveEncashment.is_deleted.is_(False)).all()} if ids else {}
    dumped = {d["id"]: d for d in view.dump_many(db, list(rows.values()))}
    flows = steps_service.steps_of_entities(db, ENTITY, list(rows)) if rows else {}
    items = []
    for task in tasks:
        data = dumped.get(task.get("entity_id"))
        if data is None:
            continue
        items.append({**data, "task": task, "flow": flows.get(data["id"])})
    return success({"total": len(items), "items": items})


@router.get("/preview")
def preview_encashable(leave_type_id: int = Query(..., ge=1), employee_id: int = Query(0, ge=0),
                       balance_year: int | None = Query(None, ge=2000, le=2100),
                       reason_kind: int = Query(int(LeaveEncashmentReason.YEAR_END)),
                       db: Session = Depends(get_db), user=Depends(require(ENTITY, "create"))):
    """Xem trước số ngày được thanh toán (chỉ đọc, không cấp quỹ, không khóa) để điền form.

    Quyền: `leave_encashment.create`; xem hộ người khác cần quyền lập hộ như khi lập phiếu. Trả số dùng được, phần
    mang sang chưa dùng, số giữ lại, trần năm, đã thanh toán, trần còn lại và `encashable` (tối đa, bước 0,5).
    """
    if reason_kind not in {int(r) for r in LeaveEncashmentReason}:
        raise HTTPException(422, "Lý do thanh toán chỉ nhận 1 (phép dư cuối năm) hoặc 2 (nghỉ việc)")
    employee = request_service.resolve_leave_taker(db, user, employee_id)
    request_service.ensure_can_create_for(db, user, employee, ENTITY)
    leave_type = service.load_leave_type(db, leave_type_id)
    year = balance_year or vn_today().year
    service.check_year(year)
    service.check_reason(employee, reason_kind)
    data = encashment_balance.preview(db, employee, leave_type, year, reason_kind)
    return success({**data, "employee_id": employee.id, "leave_type_id": leave_type.id, "balance_year": year,
                    "reason_kind": reason_kind, "reason_kind_label": label(LEAVE_ENCASHMENT_REASON_LABELS, reason_kind)})


@router.get("/{rid}")
def get_encashment(rid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    """Chi tiết phiếu. `payment` = YCTT sinh ra; `payment.total` chỉ có (khác null) khi người xem là chính nhân sự
    nhận tiền hoặc đọc được YCTT đó, còn lại null. `cancel_blocked_reason` khác rỗng = đang không hủy được.

    Quyền: `leave_encashment.read` (phạm vi), hoặc đang có việc duyệt treo trên phiếu.
    """
    obj = _get_or_404(db, rid, user)
    data = _one(db, obj)
    data["created_by_name"] = resolve_actor(db, obj.created_by)
    data["has_running_approval"] = bridge.running_instance(db, obj.id) is not None
    data["payment"] = view.payment_block(db, obj, user)
    data["cancel_blocked_reason"] = view.cancel_blocked_reason(db, obj)
    return success(data)


@router.post("")
def create_encashment(data: LeaveEncashmentCreate, db: Session = Depends(get_db),
                      user=Depends(require(ENTITY, "create"))):
    """Lập phiếu thanh toán nghỉ phép (Nháp) cho chính mình hoặc lập hộ.

    Quyền: `leave_encashment.create`; lập hộ cần phạm vi rộng hơn "của mình" và người đó nằm trong tầm. Lỗi riêng: 422
    loại nghỉ không cho thanh toán / năm ngoài năm nay và năm trước / thiếu ngày nghỉ việc / vượt số được phép;
    409 đã có phiếu còn hiệu lực cùng người, loại, năm.
    """
    obj = service.create(db, data, user)
    audit_record(db, user.id, ENTITY, obj.id, "create", f"Lập phiếu thanh toán nghỉ phép {obj.code}")
    return success(_one(db, obj), "Đã lưu phiếu thanh toán nghỉ phép")


@router.patch("/{rid}")
def update_encashment(rid: int, data: LeaveEncashmentUpdate, db: Session = Depends(get_db),
                      user=Depends(require(ENTITY, "write"))):
    """Sửa phiếu Nháp / Trả về (lý do, ngày, số ngày, ghi chú). Quyền: `leave_encashment.write`. 400 khi đã gửi duyệt."""
    obj = service.update(db, _get_or_404(db, rid, user, "write"), data, user)
    audit_record(db, user.id, ENTITY, obj.id, "update", f"Sửa phiếu thanh toán nghỉ phép {obj.code}")
    return success(_one(db, obj), "Đã cập nhật")


@router.delete("/{rid}")
def delete_encashment(rid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "delete"))):
    """Xóa mềm phiếu Nháp. Quyền: `leave_encashment.delete`. Phiếu đã gửi duyệt thì phải hủy (400)."""
    obj = _get_or_404(db, rid, user, "delete")
    code = obj.code
    service.soft_delete(db, obj, user)
    audit_record(db, user.id, ENTITY, rid, "delete", f"Xóa phiếu thanh toán nghỉ phép {code}")
    return success(None, "Đã xóa phiếu")


@router.post("/{rid}/submit")
def submit_encashment(rid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "write"))):
    """Gửi duyệt: khóa quỹ, kiểm lại số được phép, giữ chỗ ngày, trình bộ máy duyệt.

    Quyền: `leave_encashment.write`. Cờ duyệt tắt / chưa có luồng thì phiếu vào Chờ duyệt và duyệt thẳng bằng `/approve`.
    Lỗi riêng: 422 vượt số được phép tại thời điểm gửi; 409 phiếu vừa được xử lý bởi lượt khác.
    """
    obj = _get_or_404(db, rid, user, "write")
    transitions.prepare_submit(db, obj, user)       # chiếm phiếu + giữ chỗ trước khi đụng bộ máy duyệt
    instance_id = bridge.start_approval(db, obj, user)
    obj.approval_instance_id = instance_id
    obj.updated_by = user.id
    db.commit()
    db.refresh(obj)
    audit_record(db, user.id, ENTITY, obj.id, "update", f"Gửi duyệt phiếu thanh toán nghỉ phép {obj.code}")
    return success(_one(db, obj), "Đã gửi duyệt")


@router.post("/{rid}/approve")
def approve_encashment(rid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "approve"))):
    """Duyệt THẲNG — chỉ khi phiếu không chạy trong luồng nhiều bước. Sinh YCTT Nháp để kế toán nhập số tiền.

    Quyền: `leave_encashment.approve`. Luôn chặn tự duyệt phiếu của chính mình (403), bất kể công tắc cài đặt.
    """
    obj = _get_or_404(db, rid, user, "approve")
    if obj.status != int(S.PENDING):
        raise HTTPException(400, "Chỉ duyệt được phiếu đang ở trạng thái Chờ duyệt")
    bridge.block_legacy_path(db, obj)
    ensure_not_self_approval(ENTITY, getattr(user, "employee_id", 0), obj.employee_id)
    transitions.approve_now(db, obj, user.id)
    db.commit()
    db.refresh(obj)
    return success(_one(db, obj), "Đã duyệt phiếu")


@router.post("/{rid}/reject")
def reject_encashment(rid: int, reason: str = Query("", max_length=500), db: Session = Depends(get_db),
                      user=Depends(require(ENTITY, "approve"))):
    """Từ chối THẲNG (trả ngày giữ chỗ) — cùng điều kiện với `/approve`. Quyền: `leave_encashment.approve`."""
    obj = _get_or_404(db, rid, user, "approve")
    if obj.status != int(S.PENDING):
        raise HTTPException(400, "Chỉ từ chối được phiếu đang ở trạng thái Chờ duyệt")
    bridge.block_legacy_path(db, obj)
    transitions.release_and_set(db, obj, S.REJECTED, strict=True, decision_note=reason or "Bị từ chối", actor=user.id)
    db.commit()
    db.refresh(obj)
    audit_record(db, user.id, ENTITY, obj.id, "update", f"Từ chối phiếu thanh toán nghỉ phép {obj.code}")
    return success(_one(db, obj), "Đã từ chối phiếu")


@router.post("/{rid}/cancel")
def cancel_encashment(rid: int, reason: str = Query("", max_length=500), db: Session = Depends(get_db),
                      user=Depends(require(ENTITY, "cancel"))):
    """Hủy phiếu: Nháp / Chờ duyệt / Trả về -> Đã hủy (rút phiên duyệt trước); Đã duyệt -> trả ngày về quỹ.

    Quyền: `leave_encashment.cancel`. Phiếu Đã duyệt chỉ hủy được khi YCTT còn Nháp hoặc kế toán đã từ chối; YCTT đang
    Chờ duyệt / Đã duyệt / Đã chi thì 400 (kế toán từ chối YCTT trước).
    """
    obj = bridge.cancel_request(db, _get_or_404(db, rid, user, "cancel"), reason, user)
    audit_record(db, user.id, ENTITY, obj.id, "cancel", f"Hủy phiếu thanh toán nghỉ phép {obj.code}")
    return success(_one(db, obj), "Đã hủy phiếu")
