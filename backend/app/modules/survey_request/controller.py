from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.core.auth import (get_current_user, get_perm_profile, require,
                           user_has_permission)
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


def _out(db: Session, s: SurveyRequest, user=None, profile=None) -> dict:
    from app.modules.employee.model import Employee
    base = _dict(s)
    lines = service.lines_of(db, s.id)
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
        opts = service.options_of(db, x.id)
        d["option_count"] = len(opts)
        d["has_chosen"] = any(o.is_chosen for o in opts)
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
    # Báo cho các NSTM vừa được TỰ GÁN theo phân loại
    codes = {ln.assignee for ln in service.lines_of(db, s.id) if ln.assignee}
    if codes:
        _notify(db, _users_of_codes(db, list(codes)),
                f"[Phân công khảo sát] {s.code}",
                f"Bạn được phân công khảo sát trong phiếu {s.code} (vừa được duyệt).",
                f"/survey-requests/{s.id}/process", user.id)
    return success(_out(db, s), "Đã duyệt — chuyển sang xử lý")


@router.post("/{sid}/reject")
def reject_(sid: int, data: RejectIn, db: Session = Depends(get_db),
            user=Depends(require("survey_request", "approve"))):
    """TRẢ ĐƠN — trả về để người YC sửa & gửi lại (như nháp). status → rejected (còn sửa được)."""
    s = service.set_status(db, sid, "rejected", user.id, data.reason)
    from app.modules.user.model import User
    reqs = db.query(User).filter(User.id == (s.created_by or user.id)).all()
    _notify(db, reqs, f"[Trả đơn] Phiếu khảo sát {s.code}",
            f"Phiếu yêu cầu khảo sát {s.code} bị TRẢ LẠI để chỉnh sửa. Lý do: {data.reason or '(không nêu)'}",
            f"/survey-requests/{s.id}", s.created_by or user.id)
    return success(_out(db, s), "Đã trả đơn")


@router.post("/{sid}/cancel")
def cancel_(sid: int, data: RejectIn, db: Session = Depends(get_db),
            user=Depends(require("survey_request", "approve"))):
    """TỪ CHỐI — khóa đơn hẳn (không sửa được nữa, phải làm đơn mới). status → cancelled."""
    s = service.set_status(db, sid, "cancelled", user.id, data.reason)
    from app.modules.user.model import User
    reqs = db.query(User).filter(User.id == (s.created_by or user.id)).all()
    _notify(db, reqs, f"[Từ chối] Phiếu khảo sát {s.code}",
            f"Phiếu yêu cầu khảo sát {s.code} bị TỪ CHỐI (khóa đơn). Lý do: {data.reason or '(không nêu)'}",
            f"/survey-requests/{s.id}", s.created_by or user.id)
    return success(_out(db, s), "Đã từ chối (khóa đơn)")


@router.patch("/{sid}/lines/{line_id}/assignee")
def set_line_assignee_(sid: int, line_id: int, data: dict, db: Session = Depends(get_db),
                       user=Depends(require("survey_request", "process"))):
    """Gán/đổi NSTM phụ trách 1 dòng — CHỈ thu mua side (NSTM/QL/Admin TM). Người YC không được. Body: {assignee: mã NV}."""
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
                f"/survey-requests/{sid}/process", user.id)
    return success(_out(db, service.get_sr(db, sid)), "Đã gán nhân sự phụ trách")


@router.patch("/{sid}/lines/{line_id}/status")
def set_line_status_(sid: int, line_id: int, data: dict, db: Session = Depends(get_db),
                     user=Depends(require("survey_request", "write"))):
    """Đổi Tình trạng dòng (is_completed). Hoạt động ở mọi trạng thái phiếu. Body: {is_completed: bool}."""
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
        d["options"] = [_opt_internal(o) for o in service.options_of(db, ln.id)]
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
    return success(_out_process(db, s), "Đã thêm option", 201)


@router.post("/{sid}/sync-options")
def sync_options_(sid: int, db: Session = Depends(get_db), up=Depends(_purchaser)):
    """Lấy phương án tự động từ các Phiếu khảo sát đã duyệt liên kết với YCKS này (khớp phân loại)."""
    user, _prof = up
    s = service.get_sr(db, sid)
    if s.status not in ("processing", "survey_done"):
        raise HTTPException(400, "Chỉ lấy phương án khi phiếu đang xử lý hoặc đã khảo sát")
    n = service.sync_options_from_surveys(db, sid, user.id)
    return success(_out_process(db, s), f"Đã lấy {n} phương án từ khảo sát" if n else "Chưa có phương án mới từ khảo sát")


@router.delete("/{sid}/lines/{line_id}/options/{oid}")
def del_option_(sid: int, line_id: int, oid: int, db: Session = Depends(get_db), up=Depends(_purchaser)):
    user, prof = up
    ln = service.get_line(db, sid, line_id)
    if ln.is_completed:
        raise HTTPException(400, "Dòng đã tạo yêu cầu mua hàng — không xóa phương án được")
    if not service.can_process_line(db, ln, prof):
        raise HTTPException(403, "Bạn không phụ trách dòng này")
    service.delete_option(db, line_id, oid)
    return success(_out_process(db, service.get_sr(db, sid)), "Đã xóa option")


@router.patch("/{sid}/lines/{line_id}/options/{oid}")
def edit_option_(sid: int, line_id: int, oid: int, data: dict, db: Session = Depends(get_db), up=Depends(_purchaser)):
    user, prof = up
    ln = service.get_line(db, sid, line_id)
    if not service.can_process_line(db, ln, prof):
        raise HTTPException(403, "Bạn không phụ trách dòng này")
    service.set_option_fields(db, line_id, oid, user.id,
                              nstm_note=data.get("nstm_note"),
                              system_product_code=data.get("system_product_code"))
    return success(_out_process(db, service.get_sr(db, sid)), "Đã cập nhật")


@router.post("/{sid}/complete")
def complete_(sid: int, db: Session = Depends(get_db),
              up=Depends(_purchaser)):
    """Chốt hoàn thành khảo sát — NSTM chốt PHẦN DÒNG CỦA MÌNH; phiếu -> survey_done khi
    MỌI dòng (mọi NSTM) đã có option."""
    user, prof = up
    s, fully = service.complete_sr(db, sid, user, prof)
    if fully:   # cả phiếu xong -> báo người yêu cầu vào chọn phương án
        from app.modules.user.model import User
        reqs = db.query(User).filter(User.id == (s.created_by or user.id)).all()
        _notify(db, reqs, f"[Khảo sát xong] Phiếu {s.code}",
                f"Kết quả khảo sát cho phiếu {s.code} đã sẵn sàng — vào chọn phương án.",
                f"/survey-requests/{s.id}", s.created_by or user.id)
        return success(_out(db, s, user, prof), "Đã chốt hoàn thành khảo sát")
    return success(_out(db, s, user, prof), "Đã chốt phần khảo sát của bạn. Còn dòng của NSTM khác chưa xong.")


# ─────────────── Phase 5C: người YC xem kết quả (ẨN NCC) + chọn option ───────────────

# WHITELIST field an toàn trả cho người YC (KHÔNG có supplier_*, snap_internal_code,
# nstm_note, supplier_survey_id, product_survey_line_id → không lộ NCC).
_OPT_PUBLIC_FIELDS = [
    "id", "public_id", "display_label", "is_chosen",
    "snap_product_name", "snap_spec", "snap_origin", "snap_quote_unit",
    "snap_moq", "snap_price_by_volume", "snap_volume_range", "snap_vat",
    "snap_delivery_time", "snap_delivery_place", "snap_shipping_cost",
    "snap_sample_ready", "snap_lab_result",
]
_LINE_PUBLIC_FIELDS = [
    "id", "item_group", "requirement_detail", "other_requirement",
    "request_qty", "uom", "proposed_price", "is_completed", "pr_id", "pr_code",
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
    return out


def _out_result(db: Session, s: SurveyRequest) -> dict:
    base = _dict(s)
    out_lines = []
    for ln in service.lines_of(db, s.id):
        d = {k: getattr(ln, k) for k in _LINE_PUBLIC_FIELDS}
        d["request_qty"] = float(d["request_qty"] or 0)
        d["proposed_price"] = float(d["proposed_price"] or 0)
        d["options"] = [_opt_public(o, db) for o in service.options_of(db, ln.id)]
        out_lines.append(d)
    base["lines"] = out_lines
    return base


@router.get("/{sid}/result")
def result_view_(sid: int, db: Session = Depends(get_db),
                 user=Depends(require("survey_request", "read"))):
    """Kết quả khảo sát cho người YC — ẩn NCC ở tầng backend (whitelist field)."""
    s = apply_scope(db.query(SurveyRequest).filter(SurveyRequest.id == sid),
                    SurveyRequest, "survey_request", user, get_perm_profile(db, user)).first()
    if not s:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    return success(_out_result(db, s))


@router.patch("/{sid}/lines/{line_id}/options/{oid}/choose")
def choose_option_(sid: int, line_id: int, oid: int, db: Session = Depends(get_db),
                   user=Depends(require("survey_request", "write"))):
    """Người YC chọn 1 phương án cho 1 sản phẩm (chỉ khi đã hoàn thành khảo sát)."""
    s = service.get_sr(db, sid)
    if not _can_edit_own(db, s, user):
        raise HTTPException(403, "Không có quyền chọn phương án cho phiếu này")
    if s.status != "survey_done":
        raise HTTPException(400, "Chỉ chọn phương án khi khảo sát đã hoàn thành")
    service.get_line(db, sid, line_id)
    service.choose_option(db, line_id, oid, user.id)
    return success(_out_result(db, s), "Đã chọn phương án")


# ─────────────── Phase 5D: sinh PYC + hoàn thành ───────────────

@router.post("/{sid}/create-prs")
def create_prs_(sid: int, db: Session = Depends(get_db),
                user=Depends(require("survey_request", "write"))):
    """Người YC tạo Yêu cầu mua hàng từ các phương án đã chọn (gom theo NCC)."""
    s = service.get_sr(db, sid)
    # Chỉ NGƯỜI YÊU CẦU (người tạo phiếu) hoặc Admin TM (quyền delete) được tạo YCMH — NSTM thì không.
    if not (s.created_by == user.id or user_has_permission(db, user, "survey_request", "delete")):
        raise HTTPException(403, "Chỉ người yêu cầu mới được tạo Yêu cầu mua hàng")
    prs = service.create_prs(db, sid, user.id)
    from app.modules.notification.service import get_users_by_role_codes
    _notify(db, get_users_by_role_codes(db, ["pur_manager", "pur_admin"]),
            f"[YCMH mới] Từ khảo sát {s.code}",
            f"Phiếu khảo sát {s.code} đã sinh {len(prs)} yêu cầu mua hàng: {', '.join(p.code for p in prs)}.",
            f"/survey-requests/{s.id}", s.created_by or user.id)
    return success({"created_prs": [{"id": p.id, "code": p.code} for p in prs], "sr": _out(db, s)},
                   f"Đã tạo {len(prs)} phiếu yêu cầu mua hàng")


@router.post("/{sid}/finalize")
def finalize_(sid: int, db: Session = Depends(get_db),
              user=Depends(require("survey_request", "approve"))):
    """Admin/Quản lý thu mua chuyển Hoàn thành (pr_created → done)."""
    if not service.is_purchaser(get_perm_profile(db, user)):
        raise HTTPException(403, "Chỉ Quản lý / Admin thu mua được chuyển Hoàn thành")
    s = service.finalize_sr(db, sid, user.id)
    from app.modules.user.model import User
    reqs = db.query(User).filter(User.id == (s.created_by or user.id)).all()
    _notify(db, reqs, f"[Hoàn thành] Phiếu khảo sát {s.code}",
            f"Phiếu {s.code} đã được chuyển sang Hoàn thành.",
            f"/survey-requests/{s.id}", s.created_by or user.id)
    return success(_out(db, s), "Đã chuyển Hoàn thành")
