"""Đường API YÊU CẦU SỬA HỒ SƠ (duoc-CR-676, C6) + đọc hộ gia đình của chính mình (C5, bản in).

Chung tiền tố `/api/employees` với `controller.py` nên router này PHẢI được include TRƯỚC
`employee_router` trong `main.py` — nếu không «me» và «change-requests» rơi vào `/{eid}` (422).

Hai nửa:
  * TỰ PHỤC VỤ (`/me/...`): chỉ đòi đăng nhập, hồ sơ lấy từ `user.employee_id` (cùng lý lẽ `GET /me`).
  * NHÂN SỰ DUYỆT (`/change-requests...`): `employee.write` + phạm vi GHI trên hồ sơ của yêu cầu,
    ngoài phạm vi = 404. Không có khóa quyền mới.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record
from app.core.auth import get_current_user, get_perm_profile, require
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.hr_change_request_codes import EmployeeChangeRequestStatus as Status
from app.core.response import success
from app.core.scoping import apply_scope, get_scoped

from . import change_request_service as svc
from . import change_request_view as view
from . import self_contact_service
from .change_request_model import EmployeeChangeRequest as Req
from .change_request_schema import ChangeRequestIn, RejectIn
from .model import Employee
from .schema import EmployeeFamilyOut

router = APIRouter(prefix="/api/employees", tags=["employee-change-request"])


def _one(db, req: Req, emp, user) -> dict:
    v = view.Viewer(db, user, get_perm_profile(db, user))
    return view.serialize(req, emp, v, view.user_names(db, [req]))


def _own_request(db: Session, rid: int, user) -> tuple[Req, Employee]:
    """Yêu cầu của CHÍNH MÌNH (kèm hồ sơ) — của người khác hay không có đều 404."""
    emp = self_contact_service.get_own_employee(db, user)
    req = db.get(Req, rid)
    if req is None or req.employee_id != emp.id:
        raise HTTPException(404, "Không tìm thấy yêu cầu sửa hồ sơ")
    return req, emp


def _scoped_request(db: Session, rid: int, user, profile: dict) -> tuple[Req, Employee]:
    """Yêu cầu của hồ sơ NẰM TRONG phạm vi GHI của người duyệt, không thì 404 (không lộ có hay không)."""
    req = db.get(Req, rid)
    emp = (get_scoped(db, Employee, "employee", req.employee_id, user, profile, "write")
           if req else None)
    if req is None or emp is None:
        raise HTTPException(404, "Không tìm thấy yêu cầu sửa hồ sơ")
    return req, emp


def _scoped_query(db: Session, user, profile: dict):
    q = db.query(Req).join(Employee, Employee.id == Req.employee_id)
    return apply_scope(q, Employee, "employee", user, profile, "write")


# ── Tự phục vụ ──────────────────────────────────────────────────────────────

@router.get("/me/families")
def list_my_families(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Hộ gia đình của CHÍNH MÌNH (trang in) — ngoại lệ `self`, không cần `employee_sensitive.read`."""
    emp = self_contact_service.get_own_employee(db, user)
    from . import contact_service
    rows = contact_service.list_families(db, emp.id)
    return success({"items": [EmployeeFamilyOut.model_validate(r).model_dump() for r in rows]})


@router.get("/me/change-requests")
def list_my_change_requests(db: Session = Depends(get_db), user=Depends(get_current_user)):
    emp = self_contact_service.get_own_employee(db, user)
    rows = (db.query(Req).filter(Req.employee_id == emp.id)
            .order_by(Req.id.desc()).limit(200).all())
    v, names = view.Viewer(db, user, get_perm_profile(db, user)), view.user_names(db, rows)
    return success({"items": [view.serialize(r, emp, v, names) for r in rows]})


@router.post("/me/change-requests")
def submit_change_request(data: ChangeRequestIn, db: Session = Depends(get_db),
                          user=Depends(get_current_user)):
    emp = self_contact_service.get_own_employee(db, user)
    pending_msg = "Bạn đang có một yêu cầu chờ duyệt — hãy rút lại hoặc đợi phòng Nhân sự xử lý"
    if svc.pending_of(db, emp.id):
        raise HTTPException(409, pending_msg)
    items, families = svc.build_diff(db, emp, data)
    if not items and not families:
        raise HTTPException(400, "Không có thay đổi nào để gửi")
    req = Req(employee_id=emp.id, status=int(Status.PENDING),
              pending_employee_id=emp.id, changes=items, families=families,
              note=(data.note or "").strip(), created_by=user.id, updated_by=user.id)
    db.add(req)
    try:
        db.commit()
    except IntegrityError:   # hai lượt gửi đồng thời: chỉ mục duy nhất `pending_employee_id` giữ một
        db.rollback()
        raise HTTPException(409, pending_msg) from None
    db.refresh(req)
    audit_record(db, user.id, "employee", emp.id, "submit",
                 "Gửi yêu cầu sửa hồ sơ: " + svc.group_summary(req), doc_code=emp.code or "")
    return success(_one(db, req, emp, user), "Đã gửi yêu cầu, chờ phòng Nhân sự duyệt")


@router.post("/me/change-requests/{rid}/withdraw")
def withdraw_change_request(rid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    req, emp = _own_request(db, rid, user)
    db.refresh(req, with_for_update=True)   # khóa dòng: không đè lên yêu cầu vừa được duyệt/từ chối
    if req.status != int(Status.PENDING):
        raise HTTPException(409, "Yêu cầu này đã được xử lý, không rút lại được")
    svc.decide(req, Status.WITHDRAWN, user.id)
    db.commit()
    audit_record(db, user.id, "employee", emp.id, "withdraw", "Rút lại yêu cầu sửa hồ sơ",
                 doc_code=emp.code or "")
    return success(_one(db, req, emp, user), "Đã rút lại yêu cầu")


# ── Nhân sự duyệt ───────────────────────────────────────────────────────────

@router.get("/change-requests")
def list_change_requests(
    status: int | None = Query(None), employee_id: int | None = Query(None), q: str | None = Query(None, max_length=100),
    pg: dict = Depends(pagination), db: Session = Depends(get_db),
    user=Depends(require("employee", "write")),
):
    profile = get_perm_profile(db, user)
    query = _scoped_query(db, user, profile)
    if status is not None:
        query = query.filter(Req.status == status)
    if employee_id is not None:
        query = query.filter(Req.employee_id == employee_id)
    kw = (q or "").strip()
    if kw:
        #  Thoát % và _ để người gõ «NS_01» không khớp «NSx01».
        esc = kw.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"%{esc}%"
        query = query.filter(or_(Employee.code.like(like, escape="\\"),
                                 Employee.full_name.like(like, escape="\\")))
    total = query.count()
    rows = query.order_by(Req.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    emps = {e.id: e for e in db.query(Employee).filter(Employee.id.in_({r.employee_id for r in rows})).all()}
    v, names = view.Viewer(db, user, profile), view.user_names(db, rows)
    return success({"total": total,
                    "items": [view.serialize(r, emps.get(r.employee_id), v, names, in_scope=True)
                              for r in rows]})


@router.get("/change-requests/pending-count")
def count_pending_change_requests(db: Session = Depends(get_db),
                                  user=Depends(require("employee", "write"))):
    query = _scoped_query(db, user, get_perm_profile(db, user)).filter(Req.status == int(Status.PENDING))
    return success({"count": query.count()})


@router.get("/change-requests/{rid}")
def get_change_request(rid: int, db: Session = Depends(get_db), user=Depends(require("employee", "write"))):
    req, emp = _scoped_request(db, rid, user, get_perm_profile(db, user))
    v = view.Viewer(db, user, get_perm_profile(db, user))
    return success(view.serialize(req, emp, v, view.user_names(db, [req]), in_scope=True))


def _pending_for_decision(db: Session, rid: int, user) -> tuple[Req, Employee, view.Viewer]:
    """Nạp + khóa dòng + mọi chốt chung của duyệt/từ chối: phạm vi, đang chờ, không tự duyệt, nhạy cảm."""
    profile = get_perm_profile(db, user)
    req, emp = _scoped_request(db, rid, user, profile)
    db.refresh(req, with_for_update=True)
    if req.status != int(Status.PENDING):
        raise HTTPException(409, "Yêu cầu này đã được xử lý")
    v = view.Viewer(db, user, profile)
    reason = view.approve_block_reason(v, req)
    if reason:
        raise HTTPException(403, reason)
    return req, emp, v


@router.post("/change-requests/{rid}/approve")
def approve_change_request(rid: int, db: Session = Depends(get_db), user=Depends(require("employee", "write"))):
    req, emp, v = _pending_for_decision(db, rid, user)
    try:
        svc.apply_request(db, req, emp, user.id)   # chỉ flush
        svc.decide(req, Status.APPROVED, user.id)
        svc.notify_requester(db, req, user.id, "Yêu cầu sửa hồ sơ đã được duyệt",
                             "Phòng Nhân sự đã duyệt và cập nhật hồ sơ: " + svc.group_summary(req))
        db.commit()
    except Exception:
        db.rollback()   # hồ sơ + hộ gia đình + trạng thái yêu cầu: cùng thành hoặc cùng hỏng
        raise
    db.refresh(req)
    audit_record(db, user.id, "employee", emp.id, "update",
                 "Duyệt yêu cầu sửa hồ sơ: " + svc.group_summary(req), doc_code=emp.code or "")
    return success(view.serialize(req, emp, v, view.user_names(db, [req]), in_scope=True), "Đã duyệt")


@router.post("/change-requests/{rid}/reject")
def reject_change_request(rid: int, data: RejectIn, db: Session = Depends(get_db),
                          user=Depends(require("employee", "write"))):
    req, emp, v = _pending_for_decision(db, rid, user)
    svc.decide(req, Status.REJECTED, user.id, data.reason)
    svc.notify_requester(db, req, user.id, "Yêu cầu sửa hồ sơ bị từ chối",
                         "Lý do: " + req.reject_reason)
    db.commit()
    audit_record(db, user.id, "employee", emp.id, "reject",
                 "Từ chối yêu cầu sửa hồ sơ: " + svc.group_summary(req), doc_code=emp.code or "")
    return success(view.serialize(req, emp, v, view.user_names(db, [req]), in_scope=True), "Đã từ chối")
