from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require, user_has_permission
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope

from . import service
from .model import SurveyRequest
from .schema import RejectIn, SurveyRequestCreate, SurveyRequestUpdate

router = APIRouter(prefix="/api/survey-requests", tags=["survey_request"])


def _dict(obj) -> dict:
    d = {}
    for c in sa_inspect(obj).mapper.column_attrs:
        v = getattr(obj, c.key)
        d[c.key] = float(v) if isinstance(v, Decimal) else v
    return d


def _out(db: Session, s: SurveyRequest) -> dict:
    from app.modules.employee.model import Employee
    base = _dict(s)
    lines = service.lines_of(db, s.id)
    codes = {ln.assignee for ln in lines if ln.assignee}
    name_by_code = {}
    if codes:
        name_by_code = {e.code: e.full_name for e in db.query(Employee).filter(Employee.code.in_(codes)).all()}
    out_lines = []
    for x in lines:
        d = _dict(x)
        d["assignee_name"] = name_by_code.get(x.assignee, "")
        out_lines.append(d)
    base["lines"] = out_lines
    return base


def _can_edit_own(db, s, user) -> bool:
    return s.created_by == user.id or user_has_permission(db, user, "survey_request", "write")


def _notify(db, users, title, body, link, creator_id):
    from app.modules.notification.model import Notification
    seen = set()
    for u in users:
        if u and u.id not in seen:
            seen.add(u.id)
            db.add(Notification(user_id=u.id, title=title, body=body, link=link, created_by=creator_id))
    db.commit()


@router.get("/meta/dept-head")
def dept_head_(department: str = "", db: Session = Depends(get_db),
               user=Depends(require("survey_request", "read"))):
    from app.modules.purchase_request.service import find_dept_head
    return success({"head_of_dept": find_dept_head(db, department)})


@router.get("")
def list_(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
          user=Depends(require("survey_request", "read"))):
    q = apply_filters(db.query(SurveyRequest), SurveyRequest, request, service.FILTERABLE)
    q = apply_scope(q, SurveyRequest, "survey_request", user, get_perm_profile(db, user))
    total = q.count()
    items = q.order_by(SurveyRequest.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": total, "items": [_dict(x) for x in items]})


@router.get("/{sid}")
def get_(sid: int, db: Session = Depends(get_db), user=Depends(require("survey_request", "read"))):
    s = apply_scope(db.query(SurveyRequest).filter(SurveyRequest.id == sid),
                    SurveyRequest, "survey_request", user, get_perm_profile(db, user)).first()
    if not s:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    return success(_out(db, s))


@router.post("")
def create_(data: SurveyRequestCreate, db: Session = Depends(get_db),
            user=Depends(require("survey_request", "create"))):
    return success(_out(db, service.create_sr(db, data, user.id)), "Đã tạo", 201)


@router.patch("/{sid}")
def update_(sid: int, data: SurveyRequestUpdate, db: Session = Depends(get_db),
            user=Depends(require("survey_request", "read"))):
    s = service.get_sr(db, sid)
    if not _can_edit_own(db, s, user):
        raise HTTPException(403, "Không có quyền sửa phiếu này")
    return success(_out(db, service.update_sr(db, sid, data, user.id)), "Đã cập nhật")


@router.delete("/{sid}")
def delete_(sid: int, db: Session = Depends(get_db), user=Depends(require("survey_request", "delete"))):
    service.delete_sr(db, sid, user.id)
    return success(None, "Đã xóa")


@router.post("/{sid}/submit")
def submit_(sid: int, db: Session = Depends(get_db), user=Depends(require("survey_request", "read"))):
    s = service.get_sr(db, sid)
    if not _can_edit_own(db, s, user):
        raise HTTPException(403, "Không có quyền gửi duyệt phiếu này")
    if s.status not in ("draft", "rejected"):
        raise HTTPException(400, "Chỉ gửi duyệt phiếu ở trạng thái Nháp/Từ chối")
    s = service.set_status(db, sid, "submitted", user.id)
    from app.modules.notification.service import get_department_head_users
    _notify(db, get_department_head_users(db, s.department or ""),
            f"[Yêu cầu duyệt] Phiếu khảo sát {s.code}",
            f"Có phiếu yêu cầu khảo sát mới ({s.code}) cần bạn duyệt.",
            f"/survey-requests/{s.id}", s.created_by or user.id)
    return success(_out(db, s), "Đã gửi duyệt")


@router.post("/{sid}/approve")
def approve_(sid: int, db: Session = Depends(get_db), user=Depends(require("survey_request", "approve"))):
    s = service.set_status(db, sid, "approved", user.id)
    service.auto_assign(db, s)                       # tự gán NSTM theo phân loại (Task 4)
    s = service.set_status(db, sid, "processing", user.id)   # duyệt xong -> chuyển sang Đang xử lý
    from app.modules.notification.service import get_users_by_role_codes
    from app.modules.user.model import User
    reqs = db.query(User).filter(User.id == (s.created_by or user.id)).all()
    _notify(db, reqs + get_users_by_role_codes(db, ["pur_manager", "pur_admin"]),
            f"[Đã duyệt] Phiếu khảo sát {s.code}",
            f"Phiếu yêu cầu khảo sát {s.code} đã được duyệt, chuyển sang xử lý khảo sát.",
            f"/survey-requests/{s.id}", s.created_by or user.id)
    return success(_out(db, s), "Đã duyệt — chuyển sang xử lý")


@router.post("/{sid}/reject")
def reject_(sid: int, data: RejectIn, db: Session = Depends(get_db),
            user=Depends(require("survey_request", "approve"))):
    s = service.set_status(db, sid, "rejected", user.id, data.reason)
    from app.modules.user.model import User
    reqs = db.query(User).filter(User.id == (s.created_by or user.id)).all()
    _notify(db, reqs, f"[Từ chối] Phiếu khảo sát {s.code}",
            f"Phiếu yêu cầu khảo sát {s.code} bị từ chối. Lý do: {data.reason or '(không nêu)'}",
            f"/survey-requests/{s.id}", s.created_by or user.id)
    return success(_out(db, s), "Đã từ chối")


@router.patch("/{sid}/lines/{line_id}/assignee")
def set_line_assignee_(sid: int, line_id: int, data: dict, db: Session = Depends(get_db),
                       user=Depends(require("survey_request", "write"))):
    """Gán/đổi NSTM phụ trách 1 dòng (Admin/AdminTM). Body: {assignee: mã NV}."""
    from .model import SurveyRequestLine
    ln = db.query(SurveyRequestLine).filter(SurveyRequestLine.id == line_id,
                                            SurveyRequestLine.survey_request_id == sid).first()
    if not ln:
        raise HTTPException(404, "Không tìm thấy dòng")
    ln.assignee = (data.get("assignee") or "").strip()
    ln.updated_by = user.id
    db.commit()
    return success(_out(db, service.get_sr(db, sid)), "Đã gán nhân sự phụ trách")
