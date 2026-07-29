from decimal import Decimal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import inspect as sa_inspect, select
from sqlalchemy.orm import Session

from app.core.auth import (get_current_user, get_perm_profile, require,
                           user_has_permission)
from app.core.base_controller import apply_filters, apply_range_filters, apply_equals, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope

from . import service
from .model import SurveyRequest, SurveyRequestLine
from .schema import LineStatusIn, RejectIn, SurveyRequestCreate, SurveyRequestUpdate

router = APIRouter(prefix="/api/survey-requests", tags=["survey_request"])


def _dict(obj) -> dict:
    d = {}
    for c in sa_inspect(obj).mapper.column_attrs:
        v = getattr(obj, c.key)
        d[c.key] = float(v) if isinstance(v, Decimal) else v
    return d


def _out(db: Session, s: SurveyRequest, user=None, profile=None) -> dict:
    from app.modules.employee.model import Employee
    base = _dict(s)
    lines = service.lines_of(db, s.id)
    order = getattr(s, "_ordered_line_ids", None)   # sau create/update: giữ đúng thứ tự dòng đã gửi
    if order:
        pos = {lid: i for i, lid in enumerate(order)}
        lines = sorted(lines, key=lambda ln: pos.get(ln.id, 10 ** 9))
    if user is not None and profile is not None:   # NSTM chỉ thấy dòng mình phụ trách
        lines = service.visible_lines_for(db, s, lines, user, profile)
    codes = {ln.assignee for ln in lines if ln.assignee}
    name_by_code = {}
    if codes:
        name_by_code = {e.code: e.full_name for e in db.query(Employee).filter(Employee.code.in_(codes)).all()}
    out_lines = []
    for x in lines:
        d = _dict(x)
        d["assignee_name"] = name_by_code.get(x.assignee, "")
        opts = service.valid_options_of(db, x.id)
        d["option_count"] = len(opts)
        d["has_chosen"] = any(o.is_chosen for o in opts)
        out_lines.append(d)
    base["lines"] = out_lines
    return base


def _can_edit_own(db, s, user) -> bool:
    """Người TẠO / người YÊU CẦU (admin tạo giùm) / người có quyền write."""
    rid = getattr(user, "employee_id", 0) or 0
    if s.created_by == user.id or (rid and getattr(s, "requester_id", 0) == rid):
        return True
    return user_has_permission(db, user, "survey_request", "write")


def _is_requester(s, user) -> bool:
    rid = getattr(user, "employee_id", 0) or 0
    return s.created_by == user.id or (rid and getattr(s, "requester_id", 0) == rid)


def _same_dept_as_requester(db, s, user) -> bool:
    """True nếu user CÙNG phòng ban với người yêu cầu của phiếu.
    Ưu tiên so `department_id` (qua Employee); fallback so tên phòng ban với `s.department`."""
    from app.modules.employee.model import Employee
    uid_emp = getattr(user, "employee_id", 0) or 0
    if not uid_emp:
        return False
    ue = db.get(Employee, uid_emp)
    if not ue:
        return False
    req_dept_id = 0
    if getattr(s, "requester_id", 0):
        re = db.get(Employee, s.requester_id)
        if re:
            req_dept_id = re.department_id or 0
    if req_dept_id and ue.department_id:
        return ue.department_id == req_dept_id
    return bool(s.department) and (ue.department_name or "") == s.department


def _can_act_as_requester_side(db, s, user) -> bool:
    """Quyền phía NGƯỜI YÊU CẦU: là người YC, hoặc cùng phòng ban người YC,
    hoặc Admin TM (quyền delete) để không khóa quản trị. Dùng cho Task 2/3."""
    return (_is_requester(s, user) or _same_dept_as_requester(db, s, user)
            or user_has_permission(db, user, "survey_request", "delete"))


_SR_LOCKED = ("cancelled", "done")   # Đã từ chối / Hoàn thành → khóa, KHÔNG cập nhật (kể cả QL/Admin)


def _ensure_sr_editable(s):
    if s.status in _SR_LOCKED:
        raise HTTPException(400, "Phiếu đã bị từ chối/hoàn thành — không thể cập nhật")


def _notify(db, users, title, body, link, creator_id, background_tasks=None):
    from app.modules.notification.model import Notification
    seen = set()
    for u in users:
        if u and u.id not in seen:
            seen.add(u.id)
            db.add(Notification(user_id=u.id, title=title, body=body, link=link, created_by=creator_id))
    db.commit()
    # Web Push (best-effort) — đẩy thông báo tới thiết bị đã bật của người nhận (parity với PYC)
    try:
        from app.modules.push import service as push_service
        from app.core.database import SessionLocal
        uids = list(seen)
        if uids:
            if background_tasks is not None:
                background_tasks.add_task(push_service.send_to_users, SessionLocal, uids, title, body, link)
            else:
                push_service.send_to_users(SessionLocal, uids, title, body, link)
    except Exception:
        pass


def _users_of_codes(db, codes):
    """Tài khoản user theo danh sách mã NV (để thông báo NSTM được phân công)."""
    codes = [c for c in codes if c]
    if not codes:
        return []
    from app.modules.employee.model import Employee
    from app.modules.user.model import User
    emp_ids = [e.id for e in db.query(Employee).filter(Employee.code.in_(codes)).all()]
    return db.query(User).filter(User.employee_id.in_(emp_ids)).all() if emp_ids else []


@router.get("/meta/dept-head")
def dept_head_(department: str = "", db: Session = Depends(get_db),
               user=Depends(require("survey_request", "read"))):
    from app.modules.purchase_request.service import find_dept_head
    return success({"head_of_dept": find_dept_head(db, department)})


@router.get("")
def list_(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
          user=Depends(require("survey_request", "read"))):
    q = apply_filters(db.query(SurveyRequest), SurveyRequest, request, service.FILTERABLE)
    q = apply_range_filters(q, SurveyRequest, request, ["request_date"])
    q = apply_equals(q, SurveyRequest, request, ["company_id"])
    item_group = (request.query_params.get("item_group") or "").strip()
    if item_group:
        sub = select(SurveyRequestLine.survey_request_id).where(SurveyRequestLine.item_group.like(f"%{item_group}%"))
        q = q.filter(SurveyRequest.id.in_(sub))
    assignee = (request.query_params.get("assignee") or "").strip()
    if assignee:
        sub2 = select(SurveyRequestLine.survey_request_id).where(SurveyRequestLine.assignee == assignee)
        q = q.filter(SurveyRequest.id.in_(sub2))
    q = apply_scope(q, SurveyRequest, "survey_request", user, get_perm_profile(db, user))
    total = q.count()
    items = q.order_by(SurveyRequest.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": total, "items": [_dict(x) for x in items]})


@router.get("/{sid}")
def get_(sid: int, db: Session = Depends(get_db), user=Depends(require("survey_request", "read"))):
    prof = get_perm_profile(db, user)
    s = apply_scope(db.query(SurveyRequest).filter(SurveyRequest.id == sid),
                    SurveyRequest, "survey_request", user, prof).first()
    if not s:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    return success(_out(db, s, user, prof))


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


@router.post("/{sid}/clone")
def clone_(sid: int, db: Session = Depends(get_db), user=Depends(require("survey_request", "create"))):
    """Nhân bản 1 YCKS thành phiếu nháp mới (sao chép header + dòng)."""
    prof = get_perm_profile(db, user)
    s = apply_scope(db.query(SurveyRequest).filter(SurveyRequest.id == sid),
                    SurveyRequest, "survey_request", user, prof).first()
    if not s:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    return success(_out(db, service.clone_sr(db, sid, user, prof)), "Đã nhân bản phiếu", 201)


@router.delete("/{sid}")
def delete_(sid: int, db: Session = Depends(get_db), user=Depends(require("survey_request", "delete"))):
    service.delete_sr(db, sid, user.id)
    return success(None, "Đã xóa")


@router.delete("")
def bulk_delete_survey_requests(ids: str, db: Session = Depends(get_db), user=Depends(require("survey_request", "delete"))):
    id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
    if not id_list:
        raise HTTPException(400, "Không có ID hợp lệ")
    for sid in id_list:
        try:
            service.delete_sr(db, sid, user.id)
        except Exception as e:
            raise HTTPException(400, f"Lỗi khi xóa phiếu ID {sid}: {str(e)}")
    return success(None, f"Đã xóa {len(id_list)} bản ghi")


@router.post("/{sid}/submit")
def submit_(sid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("survey_request", "read"))):
    s = service.get_sr(db, sid)
    if not _can_edit_own(db, s, user):
        raise HTTPException(403, "Không có quyền gửi duyệt phiếu này")
    if s.status not in ("draft", "rejected"):
        raise HTTPException(400, "Chỉ gửi duyệt phiếu ở trạng thái Nháp hoặc Bị trả lại")
    s = service.set_status(db, sid, "submitted", user.id)
    # Người duyệt YCKS (Quản lý/Admin TM), + Trưởng bộ phận nếu có gán
    from app.modules.notification.service import get_department_head_users, get_approvers_for_entity
    recips = get_approvers_for_entity(db, "survey_request") + get_department_head_users(db, s.department or "")
    _notify(db, recips,
            f"[Yêu cầu duyệt] Yêu cầu báo giá {s.code}",
            f"Có yêu cầu báo giá mới ({s.code}) cần bạn duyệt.",
            f"/survey-requests/{s.id}", s.created_by or user.id, background_tasks)
    return success(_out(db, s), "Đã gửi duyệt")


@router.post("/{sid}/approve")
def approve_(sid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("survey_request", "approve"))):
    s = service.set_status(db, sid, "approved", user.id)
    service.auto_assign(db, s)                       # tự gán NSTM theo phân loại (Task 4)
    s = service.set_status(db, sid, "processing", user.id)   # duyệt xong -> chuyển sang Đang xử lý
    from app.modules.notification.service import get_users_by_role_codes
    from app.modules.user.model import User
    reqs = db.query(User).filter(User.id == (s.created_by or user.id)).all()
    _notify(db, reqs + get_users_by_role_codes(db, ["pur_manager", "pur_admin"]),
            f"[Đã duyệt] Yêu cầu báo giá {s.code}",
            f"Yêu cầu báo giá {s.code} của bạn đã được duyệt, chuyển sang xử lý khảo sát.",
            f"/survey-requests/{s.id}", s.created_by or user.id, background_tasks)
    # Báo cho các NSTM vừa được TỰ GÁN theo phân loại
    codes = {ln.assignee for ln in service.lines_of(db, s.id) if ln.assignee}
    if codes:
        _notify(db, _users_of_codes(db, list(codes)),
                f"[Phân công khảo sát] {s.code}",
                f"Bạn được phân công khảo sát trong phiếu {s.code} (vừa được duyệt).",
                f"/survey-requests/{s.id}/process", user.id, background_tasks)
    return success(_out(db, s), "Đã duyệt — chuyển sang xử lý")


@router.post("/{sid}/reject")
def reject_(sid: int, data: RejectIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
            user=Depends(require("survey_request", "approve"))):
    """TRẢ ĐƠN — trả về để người YC sửa & gửi lại (như nháp). status → rejected (còn sửa được)."""
    s = service.set_status(db, sid, "rejected", user.id, data.reason)
    from app.modules.user.model import User
    reqs = db.query(User).filter(User.id == (s.created_by or user.id)).all()
    _notify(db, reqs, f"[Trả đơn] Yêu cầu báo giá {s.code}",
            f"Yêu cầu báo giá {s.code} của bạn bị TRẢ LẠI để chỉnh sửa. Lý do: {data.reason or '(không nêu)'}",
            f"/survey-requests/{s.id}", s.created_by or user.id, background_tasks)
    return success(_out(db, s), "Đã trả đơn")


@router.post("/{sid}/cancel")
def cancel_(sid: int, data: RejectIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
            user=Depends(require("survey_request", "approve"))):
    """TỪ CHỐI — khóa đơn hẳn (không sửa được nữa, phải làm đơn mới). status → cancelled."""
    s = service.set_status(db, sid, "cancelled", user.id, data.reason)
    from app.modules.user.model import User
    reqs = db.query(User).filter(User.id == (s.created_by or user.id)).all()
    _notify(db, reqs, f"[Từ chối] Yêu cầu báo giá {s.code}",
            f"Yêu cầu báo giá {s.code} của bạn bị TỪ CHỐI (khóa đơn). Lý do: {data.reason or '(không nêu)'}",
            f"/survey-requests/{s.id}", s.created_by or user.id, background_tasks)
    return success(_out(db, s), "Đã từ chối (khóa đơn)")


@router.patch("/{sid}/lines/{line_id}/assignee")
def set_line_assignee_(sid: int, line_id: int, data: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
                       user=Depends(require("survey_request", "process"))):
    """Gán/đổi NSTM phụ trách 1 dòng — CHỈ thu mua side (NSTM/QL/Admin TM). Người YC không được. Body: {assignee: mã NV}."""
    _ensure_sr_editable(service.get_sr(db, sid))
    from .model import SurveyRequestLine
    ln = db.query(SurveyRequestLine).filter(SurveyRequestLine.id == line_id,
                                            SurveyRequestLine.survey_request_id == sid).first()
    if not ln:
        raise HTTPException(404, "Không tìm thấy dòng")
    ln.assignee = (data.get("assignee") or "").strip()
    # Ngày tiếp nhận = ngày NSTM được gán (tự tính); bỏ gán thì xóa
    if ln.assignee and not ln.received_date:
        from datetime import datetime
        ln.received_date = datetime.now().strftime("%Y-%m-%d")
    elif not ln.assignee:
        ln.received_date = ""
    ln.updated_by = user.id
    db.commit()
    if ln.assignee:                                   # báo cho NSTM vừa được gán
        s = service.get_sr(db, sid)
        _notify(db, _users_of_codes(db, [ln.assignee]),
                f"[Phân công khảo sát] {s.code}",
                f"Bạn được phân công phụ trách khảo sát trong phiếu {s.code}.",
                f"/survey-requests/{sid}/process", user.id, background_tasks)
    return success(_out(db, service.get_sr(db, sid)), "Đã gán nhân sự phụ trách")


@router.patch("/{sid}/lines/{line_id}/status")
def set_line_status_(sid: int, line_id: int, data: dict, db: Session = Depends(get_db),
                     user=Depends(require("survey_request", "write"))):
    """Đổi Tình trạng dòng (is_completed). Body: {is_completed: bool}. Chặn khi phiếu đã từ chối/hoàn thành."""
    _ensure_sr_editable(service.get_sr(db, sid))
    ln = service.get_line(db, sid, line_id)
    ln.is_completed = bool(data.get("is_completed"))
    ln.updated_by = user.id
    db.commit()
    return success(_out(db, service.get_sr(db, sid)), "Đã cập nhật tình trạng")


# ─────────────────── Phase 5B: màn xử lý NSTM (ẩn NCC ở tầng backend) ───────────────────

def _purchaser(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Chỉ NSTM/Quản lý/Admin TM (scope proc|all). Người YC/Trưởng BP → 403 (không thấy NCC)."""
    if not user_has_permission(db, user, "survey_request", "read"):
        raise HTTPException(403, "Không có quyền")
    prof = get_perm_profile(db, user)
    if not service.is_purchaser(prof):
        raise HTTPException(403, "Chỉ nhân sự thu mua được xem/xử lý khảo sát")
    return user, prof


def _opt_internal(o) -> dict:
    return _dict(o)                      # đầy đủ, gồm supplier_* (NSTM/Admin xem được)


def _out_process(db: Session, s: SurveyRequest, user=None, profile=None) -> dict:
    from app.modules.employee.model import Employee
    base = _dict(s)
    lines = service.lines_of(db, s.id)
    if user is not None and profile is not None:   # NSTM chỉ thấy dòng mình phụ trách
        lines = service.visible_lines_for(db, s, lines, user, profile)
    codes = {ln.assignee for ln in lines if ln.assignee}
    name_by_code = {e.code: e.full_name for e in db.query(Employee).filter(Employee.code.in_(codes)).all()} if codes else {}
    out_lines = []
    for ln in lines:
        d = _dict(ln)
        d["assignee_name"] = name_by_code.get(ln.assignee, "")
        d["options"] = [_opt_internal(o) for o in service.valid_options_of(db, ln.id)]
        # Cờ cho FE: dòng này người xem có được GẮN/XÓA phương án không. Admin TM (đọc-chỉ)
        # thấy hết dòng nhưng chỉ sửa được dòng mình phụ trách -> dòng khác hiển thị read-only.
        d["can_process"] = (service.can_process_line(db, ln, profile)
                            if profile is not None else True)
        out_lines.append(d)
    base["lines"] = out_lines
    return base


@router.get("/{sid}/process")
def process_view_(sid: int, db: Session = Depends(get_db), up=Depends(_purchaser)):
    user, prof = up
    s = service.get_sr(db, sid)
    return success(_out_process(db, s, user, prof))


@router.get("/{sid}/lines/{line_id}/available-survey-lines")
def available_survey_lines_(sid: int, line_id: int, supplier_code: str = "", item_group: str = "",
                            search: str = "", db: Session = Depends(get_db), up=Depends(_purchaser)):
    from app.modules.survey.model import Survey
    ln = service.get_line(db, sid, line_id)
    # Lọc MỞ (chọn NCC thủ công) — KHÔNG giới hạn liên kết YCKS: option có thể đã có khảo sát sẵn.
    # Phân loại mặc định = của dòng (FE gửi sẵn); có thể đổi hoặc để trống. Cần ≥1 tiêu chí.
    if not (supplier_code or (item_group or "").strip() or (search or "").strip()):
        return success([])
    rows = service.available_survey_lines(db, supplier_code=supplier_code, item_group=item_group, search=search)
    _sv_cache: dict = {}
    out = []
    for r in rows:
        d = _dict(r)
        d["supplier_name"] = service.resolve_supplier_name(db, r.supplier_code or "")
        if r.survey_id not in _sv_cache:
            _sv_cache[r.survey_id] = db.get(Survey, r.survey_id)
        sv = _sv_cache[r.survey_id]
        d["survey_item_group"] = sv.item_group if sv else ""   # để FE cảnh báo khi khác phân loại dòng
        d["survey_code"] = sv.code if sv else ""
        d["survey_item_code"] = sv.item_code if sv else ""     # Mã VTBB/VL (lấy từ header phiếu khảo sát)
        # result_date (Ngày trả KQ của dòng NCC) đã có sẵn trong d -> FE dùng làm "Ngày khảo sát"
        out.append(d)
    return success(out)


@router.post("/{sid}/lines/{line_id}/options")
def add_option_(sid: int, line_id: int, data: dict, db: Session = Depends(get_db), up=Depends(_purchaser)):
    user, prof = up
    s = service.get_sr(db, sid)
    if s.status not in ("processing", "survey_done"):
        raise HTTPException(400, "Chỉ gắn phương án khi phiếu đang xử lý hoặc đã khảo sát")
    ln = service.get_line(db, sid, line_id)
    if ln.is_completed:
        raise HTTPException(400, "Dòng đã tạo yêu cầu mua hàng — không sửa phương án được")
    if not service.can_process_line(db, ln, prof):
        raise HTTPException(403, "Bạn không phụ trách dòng này")
    psl_id = int(data.get("product_survey_line_id") or 0)
    if not psl_id:
        raise HTTPException(400, "Thiếu product_survey_line_id")
    service.create_option(db, ln, psl_id, user.id)
    return success(_out_process(db, s, user, prof), "Đã thêm option", 201)


@router.post("/{sid}/sync-options")
def sync_options_(sid: int, db: Session = Depends(get_db), up=Depends(_purchaser)):
    """Lấy phương án tự động từ các Phiếu khảo sát đã duyệt liên kết với YCKS này (khớp phân loại)."""
    user, _prof = up
    s = service.get_sr(db, sid)
    if s.status not in ("processing", "survey_done"):
        raise HTTPException(400, "Chỉ lấy phương án khi phiếu đang xử lý hoặc đã khảo sát")
    n = service.sync_options_from_surveys(db, sid, user.id)
    return success(_out_process(db, s, user, _prof), f"Đã lấy {n} phương án mới từ khảo sát" if n else "Đã lấy phương án từ khảo sát xong")


@router.delete("/{sid}/lines/{line_id}/options/{oid}")
def del_option_(sid: int, line_id: int, oid: int, db: Session = Depends(get_db), up=Depends(_purchaser)):
    user, prof = up
    ln = service.get_line(db, sid, line_id)
    if ln.is_completed:
        raise HTTPException(400, "Dòng đã tạo yêu cầu mua hàng — không xóa phương án được")
    if not service.can_process_line(db, ln, prof):
        raise HTTPException(403, "Bạn không phụ trách dòng này")
    service.delete_option(db, line_id, oid)
    return success(_out_process(db, service.get_sr(db, sid), user, prof), "Đã xóa option")


@router.patch("/{sid}/lines/{line_id}/options/{oid}")
def edit_option_(sid: int, line_id: int, oid: int, data: dict, db: Session = Depends(get_db), up=Depends(_purchaser)):
    user, prof = up
    ln = service.get_line(db, sid, line_id)
    if not service.can_process_line(db, ln, prof):
        raise HTTPException(403, "Bạn không phụ trách dòng này")
    service.set_option_fields(db, line_id, oid, user.id,
                              nstm_note=data.get("nstm_note"),
                              system_product_code=data.get("system_product_code"))
    return success(_out_process(db, service.get_sr(db, sid), user, prof), "Đã cập nhật")


@router.post("/{sid}/complete")
def complete_(sid: int, background_tasks: BackgroundTasks, data: dict | None = None,
              db: Session = Depends(get_db), up=Depends(_purchaser)):
    """Chốt hoàn thành khảo sát — NSTM chốt PHẦN DÒNG CỦA MÌNH; phiếu -> survey_done khi
    MỌI dòng (mọi NSTM) đã có option HOẶC được chốt rỗng.
    Body tùy chọn: {empty_line_ids: [...]} — các dòng chưa có option, chốt rỗng (không có NCC phù hợp)."""
    user, prof = up
    empty_ids = (data or {}).get("empty_line_ids") or []
    s, fully, resurveyed = service.complete_sr(db, sid, user, prof, empty_ids)
    if fully:   # cả phiếu xong -> báo người yêu cầu vào chọn phương án
        from app.modules.user.model import User
        reqs = db.query(User).filter(User.id == (s.created_by or user.id)).all()
        # Phân biệt khảo sát LẦN ĐẦU vs KHẢO SÁT LẠI để người YC hiểu vì sao được gọi vào lại
        if resurveyed:
            title = f"[Đã khảo sát lại] Phiếu {s.code}"
            body = f"NSTM đã khảo sát lại {resurveyed} dòng của phiếu {s.code} — vào chọn lại phương án."
        else:
            title = f"[Khảo sát xong] Phiếu {s.code}"
            body = f"Kết quả khảo sát cho phiếu {s.code} đã sẵn sàng — vào chọn phương án."
        _notify(db, reqs, title, body,
                f"/survey-requests/{s.id}", s.created_by or user.id, background_tasks)
        msg = "Đã chốt khảo sát lại — đã báo người yêu cầu" if resurveyed else "Đã chốt hoàn thành khảo sát"
        return success(_out(db, s, user, prof), msg)
    return success(_out(db, s, user, prof), "Đã chốt phần khảo sát của bạn. Còn dòng của NSTM khác chưa xong.")


# ─────────────── Phase 5C: người YC xem kết quả (ẨN NCC) + chọn option ───────────────

# WHITELIST field an toàn trả cho người YC (KHÔNG có supplier_*, snap_internal_code,
# nstm_note, supplier_survey_id, product_survey_line_id → không lộ NCC).
_OPT_PUBLIC_FIELDS = [
    "id", "public_id", "display_label", "is_chosen",
    "system_product_code",   # Mã VTBB/VL hệ thống (mã vật tư của chính người YC — KHÔNG lộ NCC)
    "snap_product_name", "snap_spec", "snap_origin", "snap_quote_unit",
    "snap_moq", "snap_price_by_volume", "snap_volume_range", "snap_vat",
    "snap_delivery_time", "snap_delivery_place", "snap_shipping_cost",
    "snap_sample_ready", "snap_lab_result",
]
_LINE_PUBLIC_FIELDS = [
    "id", "item_group", "requirement_detail", "other_requirement",
    "request_qty", "uom", "proposed_price", "is_completed", "line_status",
    "pr_id", "pr_code", "no_option",
]


def _opt_attachments(db: Session, psl_id: int) -> list[dict]:
    """Đính kèm của dòng khảo sát SP (entity 'survey_line') → hiện trên option.
    Chạy trong /result (đã kiểm quyền survey_request read) nên không gọi API riêng."""
    from app.modules.attachment.model import FileLink, StoredFile
    if not psl_id:
        return []
    rows = (db.query(FileLink, StoredFile)
            .join(StoredFile, StoredFile.id == FileLink.file_id)
            .filter(FileLink.entity == "survey_line", FileLink.entity_id == psl_id)
            .order_by(FileLink.id.desc()).all())
    return [{"file_id": f.id, "filename": f.filename, "url": f.url,
             "content_type": f.content_type, "size": f.size} for _lk, f in rows]


def _opt_public(o, db: Session) -> dict:
    d = _dict(o)
    out = {k: d.get(k) for k in _OPT_PUBLIC_FIELDS}
    out["attachments"] = _opt_attachments(db, o.product_survey_line_id)
    # Ngày khảo sát = Ngày trả KQ của dòng khảo sát NCC nguồn (không lộ NCC nào).
    out["survey_result_date"] = ""
    if o.product_survey_line_id:
        from app.modules.survey.model import SurveyProductLine
        psl = db.get(SurveyProductLine, o.product_survey_line_id)
        if psl:
            out["survey_result_date"] = psl.result_date or ""
    return out


def _out_result(db: Session, s: SurveyRequest, user=None, profile=None) -> dict:
    base = _dict(s)
    # Mã NCC ẩn danh: đánh số theo thứ tự xuất hiện, cùng NCC -> cùng số (KHÔNG lộ tên/mã thật).
    # Dùng chung toàn phiếu để so được "cùng 1 NCC" giữa các sản phẩm.
    ncc_seq: dict = {}

    def _ncc_ref(code: str) -> int:
        c = (code or "").strip()
        if not c:
            return 0
        if c not in ncc_seq:
            ncc_seq[c] = len(ncc_seq) + 1
        return ncc_seq[c]

    # YCMH đã tạo theo option (đếm nhiều lần) — trong phạm vi phiếu này
    from .model import SurveyRequestPr
    from app.modules.purchase_request.model import PurchaseRequest
    links = db.query(SurveyRequestPr).filter(SurveyRequestPr.survey_request_id == s.id).order_by(SurveyRequestPr.id).all()
    pr_ids = {ln.pr_id for ln in links}
    pr_map = {p.id: p for p in db.query(PurchaseRequest).filter(PurchaseRequest.id.in_(pr_ids)).all()} if pr_ids else {}
    ycmh_by_opt: dict = {}
    for link in links:
        pr = pr_map.get(link.pr_id)
        ycmh_by_opt.setdefault(link.option_id, []).append({
            "id": link.pr_id, "code": link.pr_code,
            "date": (pr.request_date if pr else ""), "status": (pr.status if pr else ""),
        })

    # Lọc dòng theo NGƯỜI XEM: NSTM chỉ thấy dòng mình phụ trách; người tạo/Admin/QL TM thấy hết.
    lines = service.lines_of(db, s.id)
    if user is not None and profile is not None:
        lines = service.visible_lines_for(db, s, lines, user, profile)
    out_lines = []
    for ln in lines:
        d = {k: getattr(ln, k) for k in _LINE_PUBLIC_FIELDS}
        d["request_qty"] = float(d["request_qty"] or 0)
        d["proposed_price"] = float(d["proposed_price"] or 0)
        opts = []
        for o in service.valid_options_of(db, ln.id):
            od = _opt_public(o, db)
            ref = _ncc_ref(o.supplier_code)
            od["ncc_ref"] = ref
            od["display_label"] = f"Option {o.public_id} — NCC #{ref}" if ref else f"Option {o.public_id}"
            od["ycmh_list"] = ycmh_by_opt.get(o.id, [])
            od["ycmh_count"] = len(od["ycmh_list"])
            opts.append(od)
        d["options"] = opts
        out_lines.append(d)
    base["lines"] = out_lines
    return base


@router.get("/{sid}/result")
def result_view_(sid: int, db: Session = Depends(get_db),
                 user=Depends(require("survey_request", "read"))):
    """Kết quả khảo sát cho người YC — ẩn NCC ở tầng backend (whitelist field)."""
    prof = get_perm_profile(db, user)
    s = apply_scope(db.query(SurveyRequest).filter(SurveyRequest.id == sid),
                    SurveyRequest, "survey_request", user, prof).first()
    if not s:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    return success(_out_result(db, s, user, prof))


@router.patch("/{sid}/lines/{line_id}/options/{oid}/choose")
def choose_option_(sid: int, line_id: int, oid: int, db: Session = Depends(get_db),
                   user=Depends(require("survey_request", "write"))):
    """Người YC chọn 1 phương án cho 1 sản phẩm (chỉ khi đã hoàn thành khảo sát)."""
    s = service.get_sr(db, sid)
    if not _can_edit_own(db, s, user):
        raise HTTPException(403, "Không có quyền chọn phương án cho phiếu này")
    # Cho chọn/đổi/bỏ chọn khi: Đang xử lý (chốt từng dòng), Đã khảo sát, Đã tạo YCMH, Hoàn thành.
    if s.status not in ("processing", "survey_done", "pr_created", "done"):
        raise HTTPException(400, "Chỉ chọn phương án khi phiếu đang xử lý trở đi")
    service.get_line(db, sid, line_id)   # xác thực dòng thuộc phiếu
    service.choose_option(db, line_id, oid, user.id)
    return success(_out_result(db, s, user, get_perm_profile(db, user)), "Đã chọn phương án")


# ─────────────── Phase 5D: sinh PYC + hoàn thành ───────────────

@router.post("/{sid}/create-prs")
def create_prs_(sid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
                user=Depends(require("survey_request", "write"))):
    """Người YC tạo Yêu cầu mua hàng từ các phương án đã chọn (gom theo NCC)."""
    s = service.get_sr(db, sid)
    # Chỉ NGƯỜI YÊU CẦU (người tạo phiếu HOẶC người yêu cầu dù admin tạo giùm) hoặc Admin TM
    # (quyền delete) được tạo YCMH — NSTM thì không.
    rid = getattr(user, "employee_id", 0) or 0
    is_requester = s.created_by == user.id or (rid and s.requester_id == rid)
    if not (is_requester or user_has_permission(db, user, "survey_request", "delete")):
        raise HTTPException(403, "Chỉ người yêu cầu mới được tạo Yêu cầu mua hàng")
    prs = service.create_prs(db, sid, user.id)
    from app.modules.notification.service import get_users_by_role_codes
    _notify(db, get_users_by_role_codes(db, ["pur_manager", "pur_admin"]),
            f"[YCMH mới] Từ khảo sát {s.code}",
            f"Phiếu khảo sát {s.code} đã sinh {len(prs)} yêu cầu mua hàng: {', '.join(p.code for p in prs)}.",
            f"/survey-requests/{s.id}", s.created_by or user.id, background_tasks)
    return success({"created_prs": [{"id": p.id, "code": p.code} for p in prs], "sr": _out(db, s)},
                   f"Đã tạo {len(prs)} phiếu yêu cầu mua hàng")


@router.patch("/{sid}/lines/{line_id}/line-status")
def set_line_status_(sid: int, line_id: int, body: LineStatusIn,
                     db: Session = Depends(get_db),
                     user=Depends(require("survey_request", "write"))):
    """Task 2: người YC / cùng phòng ban đổi trạng thái dòng khảo sát
    ("" chưa xác định · cần khảo sát lại · hoàn thành)."""
    s = service.get_sr(db, sid)
    _ensure_sr_editable(s)
    if not _can_act_as_requester_side(db, s, user):
        raise HTTPException(403, "Chỉ người yêu cầu hoặc cùng phòng ban được đổi trạng thái dòng")
    service.set_line_status(db, sid, line_id, body.line_status, user.id)
    return success(_out(db, s, user, get_perm_profile(db, user)), "Đã cập nhật trạng thái dòng")


@router.post("/{sid}/finalize")
def finalize_(sid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
              user=Depends(require("survey_request", "write"))):
    """Chuyển Hoàn thành (pr_created/survey_done → done). Cho phép Quản lý/Admin thu mua
    (purchaser + quyền approve) HOẶC người yêu cầu / cùng phòng ban người yêu cầu (Task 3).
    Lưu ý: NSTM thường (purchaser nhưng không có approve) KHÔNG được đóng phiếu."""
    s = service.get_sr(db, sid)
    prof = get_perm_profile(db, user)
    is_mgr = service.is_purchaser(prof) and user_has_permission(db, user, "survey_request", "approve")
    if not (is_mgr or _can_act_as_requester_side(db, s, user)):
        raise HTTPException(403, "Chỉ Quản lý/Admin thu mua hoặc phòng ban yêu cầu được chuyển Hoàn thành")
    s = service.finalize_sr(db, sid, user.id)
    from app.modules.user.model import User
    reqs = db.query(User).filter(User.id == (s.created_by or user.id)).all()
    _notify(db, reqs, f"[Hoàn thành] Phiếu khảo sát {s.code}",
            f"Phiếu {s.code} đã được chuyển sang Hoàn thành.",
            f"/survey-requests/{s.id}", s.created_by or user.id, background_tasks)
    return success(_out(db, s), "Đã chuyển Hoàn thành")
