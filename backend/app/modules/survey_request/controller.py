from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.bulk_delete import ensure_all_draft
from app.core.auth import (get_current_user, get_perm_profile, require,
                           user_has_permission)
from app.core.base_controller import apply_sort_from_request, pagination
from app.core.central_purchasing import get_central_dept_id
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import (apply_scope, approves_only_in_dept_proc, holds_handling_dept,
                              scope_condition)

from . import service
#  bao-CR-711: dựng kết quả ở `serializer.py`, truy vấn + gửi chuông ở `service.py`.
#  Controller chỉ còn nhận · gác quyền + phạm vi · gọi · trả.
from .model import LS_RESURVEY, SurveyRequest
from .schema import (LineStatusIn, RejectIn, SurveyRequestCreate, SurveyRequestUpdate,
                     TransferDeptIn)
from .serializer import _dict, _out, _out_available_lines, _out_process, _out_result
from .service import notify as _notify, users_of_codes as _users_of_codes

router = APIRouter(prefix="/api/survey-requests", tags=["survey_request"])


def _scope_with_named_head(user, profile, action: str = "read"):
    """Điều kiện phạm vi `action` + MỞ THÊM cho người được chọn đích danh làm TBP duyệt.

    Người lập được chọn TBP phòng ban KHÁC duyệt phiếu (QA 29/08) — phiếu đó nằm
    ngoài phạm vi vai trò của TBP kia (scope 'dept' lọc theo phòng của phiếu),
    không mở thêm thì họ nhận thông báo mà bấm vào là 403. Chỉ mở từ lúc gửi duyệt
    (bỏ nháp); route vẫn gác `require(...)` nên người không có quyền đọc không lọt.
    Trả None = thấy tất cả, giữ nguyên ngữ nghĩa của `scope_condition`.

    ⚠️ `action` phải đi theo `require(...)` của route gọi. Nhất là nhánh DUYỆT: TBP được
    chọn đích danh đứng NGOÀI phạm vi vai trò của họ, nên nếu chỉ `scope_condition(approve)`
    thì đúng người được giao lại không ký được — vế `named_head` dưới đây là chỗ trả họ về.
    """
    from sqlalchemy import and_, or_
    cond = scope_condition(SurveyRequest, "survey_request", user, profile, action)
    if cond is None:
        return None
    emp_id = (profile or {}).get("employee_id") or 0
    if not emp_id:
        return cond
    named_head = and_(SurveyRequest.head_of_dept_id == emp_id,
                      SurveyRequest.status != "draft")
    return or_(cond, named_head)


def _in_scope(db: Session, sid: int, user, action: str) -> SurveyRequest:
    """Nạp YCBG theo id NHƯNG chỉ khi nó nằm trong phạm vi `action` của người gọi.

    Trước bản vá này mọi nhánh GHI (sửa · xóa · gửi duyệt · duyệt · trả đơn · từ chối ·
    trang Xử lý khảo sát · chốt phương án · sinh YCMH · hoàn thành) đều dừng ở
    `service.get_sr` = `db.get` trần: gõ id vào URL là thao tác được phiếu pháp nhân khác.

    Đi qua `_scope_with_named_head` chứ không gọi thẳng `apply_scope`, để giữ nguyên phần
    NỚI cho TBP được chọn đích danh (QA 29/08) — bỏ nó là chặn đúng người được giao duyệt.

    404 cho cả "không có" lẫn "ngoài phạm vi", cùng mã lỗi `service.get_sr` vẫn trả.
    """
    cond = _scope_with_named_head(user, get_perm_profile(db, user), action)
    #  ai-CR-170: không đi qua `apply_scope` (vì vế TBP đích danh) nên tự lọc phiếu đã xóa mềm.
    q = service.query_live_by_id(db, sid)
    sr = (q if cond is None else q.filter(cond)).first()
    if not sr:
        raise HTTPException(404, "Không tìm thấy phiếu yêu cầu báo giá")
    return sr


def _can_edit_own(db, s, user) -> bool:
    """Người TẠO / người YÊU CẦU (admin tạo giùm) / người có quyền write."""
    rid = getattr(user, "employee_id", 0) or 0
    if s.created_by == user.id or (rid and getattr(s, "requester_id", 0) == rid):
        return True
    return user_has_permission(db, user, "survey_request", "write")


def _is_requester(s, user) -> bool:
    rid = getattr(user, "employee_id", 0) or 0
    return s.created_by == user.id or (rid and getattr(s, "requester_id", 0) == rid)


def _can_act_as_requester_side(db, s, user) -> bool:
    """Quyền phía NGƯỜI YÊU CẦU: là người YC, hoặc cùng phòng ban người YC,
    hoặc Admin TM (quyền delete) để không khóa quản trị. Dùng cho Task 2/3."""
    return (_is_requester(s, user) or service.same_dept_as_requester(db, s, user)
            or user_has_permission(db, user, "survey_request", "delete"))


_SR_LOCKED = ("cancelled", "done")   # Đã từ chối / Hoàn thành → khóa, KHÔNG cập nhật (kể cả QL/Admin)


def _ensure_sr_editable(s):
    if s.status in _SR_LOCKED:
        raise HTTPException(400, "Phiếu đã bị từ chối/hoàn thành — không thể cập nhật")


@router.get("/meta/approver-candidates")
def approver_candidates_meta(department: str = "", department_id: int = 0, company_id: int = 0,
                             handler_dept_id: int = 0, head_of_dept_id: int = 0, db: Session = Depends(get_db),
                             user=Depends(require("survey_request", "read"))):
    """bao-CR-499 — người duyệt được chứng từ ĐANG LẬP (chưa có id), cho ô "Trưởng phòng phê duyệt".

    Khai TRƯỚC `/{sid}` kẻo FastAPI nuốt "meta" thành id.
    """
    #  bao-CR-552: mọi người duyệt được (trừ Quản trị hệ thống) + Trưởng bộ phận.
    from app.core.approver_candidates import draft_fields, list_candidates_for_draft
    fields = draft_fields(db, user, department, department_id, company_id, handler_dept_id)
    return success({"items": list_candidates_for_draft(db, SurveyRequest, "survey_request", fields,
                                                       head_of_dept_id)})


@router.get("/meta/department-managers")
def department_managers_(db: Session = Depends(get_db), user=Depends(require("survey_request", "read"))):
    """bao-CR-552 — trưởng phòng mọi phòng đang hoạt động, cho ô "Trưởng bộ phận" YCBG của bản v1 chọn
    được (v2 dựng cùng bộ từ danh mục phòng ban). Chỉ đòi quyền đọc YCBG: người lập thường không có
    quyền đọc danh mục phòng ban/nhân sự. Khai TRƯỚC `/{sid}`."""
    from app.core.approver_candidates import department_managers
    return success({"items": department_managers(db)})


@router.get("/{sid}/approver-candidates")
def approver_candidates_(sid: int, db: Session = Depends(get_db),
                         user=Depends(require("survey_request", "read"))):
    """bao-CR-499 — người duyệt được ĐÚNG chứng từ này (hỏi apply_scope hành động approve)."""
    from app.core.approver_candidates import list_candidates_for_row
    row = _in_scope(db, sid, user, "read")
    return success({"items": list_candidates_for_row(db, SurveyRequest, "survey_request", row)})   # bao-CR-552


@router.get("/meta/dept-head")
def dept_head_(department: str = "", department_id: int = 0, db: Session = Depends(get_db),
               user=Depends(require("survey_request", "read"))):
    """Trưởng bộ phận của 1 phòng ban — cho người yêu cầu (không xem được DS nhân sự) tự điền TBP.

    CR-089: nhận `department_id` và trả kèm `head_of_dept_id`. Tra theo TÊN là đường lùi cho
    màn cũ, vì hai phòng trùng tên ở hai pháp nhân sẽ ra nhầm trưởng — id thì không nhầm được.
    """
    from app.modules.purchase_request.service import find_dept_head, find_dept_head_id
    return success({
        "head_of_dept": find_dept_head(db, department, department_id),
        "head_of_dept_id": find_dept_head_id(db, department, department_id),
    })


def _list_query(request: Request, db: Session, user):
    """Bộ lọc + phạm vi của màn danh sách — dùng chung cho danh sách và xuất Excel (CR-068)."""
    q = service.build_list_query(db, request)
    cond = _scope_with_named_head(user, get_perm_profile(db, user))
    return q if cond is None else q.filter(cond)


@router.get("")
def list_(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
          user=Depends(require("survey_request", "read"))):
    """Danh sách yêu cầu báo giá (YCBG) trong phạm vi được xem, có lọc và phân trang."""
    q = _list_query(request, db, user)
    total = q.count()
    q = apply_sort_from_request(q, SurveyRequest, request, default=SurveyRequest.id.desc())
    items = q.offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": total, "items": [_dict(x) for x in items]})


@router.get("/export/xlsx")
def export_xlsx(request: Request, ids: str = "", cols: str = "",
                db: Session = Depends(get_db), user=Depends(require("survey_request", "export"))):
    """CR-068 — xuất Excel danh sách YCBG: mỗi dòng yêu cầu một hàng, kèm phương án đã chốt.

    `ids` = phiếu người dùng tick chọn; rỗng thì theo bộ lọc đang đặt. `cols` = cột đang hiện.
    Khai báo TRƯỚC route `/{sid}` kẻo 'export' bị hiểu thành id.
    """
    from app.core.export_xlsx import check_row_limit, parse_ids, pick_columns, xlsx_response
    from . import export as ex

    q = _list_query(request, db, user)
    id_list = parse_ids(ids)
    if id_list:
        q = q.filter(SurveyRequest.id.in_(id_list))
    srs = q.order_by(SurveyRequest.id.desc()).all()
    check_row_limit(len(srs))
    profile = get_perm_profile(db, user)
    rows = ex.build_rows(db, srs, ex.line_visible_fn(db, user, profile))
    check_row_limit(len(rows))
    show_supplier = user_has_permission(db, user, "supplier", "read")
    columns = pick_columns(ex.HEADER_COLS, cols) + ex.columns_for(show_supplier)
    return xlsx_response(ex.FILE_NAME, columns, rows, ex.SHEET_TITLE)


@router.get("/{sid}")
def get_(sid: int, db: Session = Depends(get_db), user=Depends(require("survey_request", "read"))):
    """Chi tiết một YCBG; trưởng bộ phận được chỉ đích danh cũng xem được."""
    prof = get_perm_profile(db, user)
    cond = _scope_with_named_head(user, prof)
    q = service.query_live_by_id(db, sid)
    s = (q if cond is None else q.filter(cond)).first()
    if not s:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    return success(_out(db, s, user, prof))


@router.post("")
def create_(data: SurveyRequestCreate, db: Session = Depends(get_db),
            user=Depends(require("survey_request", "create"))):
    # user/profile: để kéo ảnh từ dòng YCMH nguồn sang (CR-027) đúng phạm vi dữ liệu người dùng thấy
    """Tạo YCBG mới ở trạng thái Nháp."""
    return success(_out(db, service.create_sr(db, data, user.id, user, get_perm_profile(db, user))), "Đã tạo", 201)


@router.patch("/{sid}")
def update_(sid: int, data: SurveyRequestUpdate, db: Session = Depends(get_db),
            user=Depends(require("survey_request", "read"))):
    # Phạm vi đi theo `read` (đúng `require` của route): người YÊU CẦU chỉ có read+create+write
    # phạm vi `own`, và chính họ là người sửa phiếu nháp của mình.
    """Sửa YCBG; chỉ người tạo khi phiếu còn sửa được, hoặc người có quyền sửa."""
    s = _in_scope(db, sid, user, "read")
    if not _can_edit_own(db, s, user):
        raise HTTPException(403, "Không có quyền sửa phiếu này")
    return success(_out(db, service.update_sr(db, sid, data, user.id, user, get_perm_profile(db, user))),
                   "Đã cập nhật")


@router.post("/{sid}/clone")
def clone_(sid: int, db: Session = Depends(get_db), user=Depends(require("survey_request", "create"))):
    """Nhân bản 1 YCKS thành phiếu nháp mới (sao chép header + dòng)."""
    prof = get_perm_profile(db, user)
    #  ⚠️ Phạm vi ở đây soi `read`, KHÔNG soi `create` — cố ý, và khác luật chung
    #  "action khớp `require`" mà các route quanh đây theo. Nguồn để nhân bản là
    #  thứ mình được ĐỌC; `create` mô tả mình được tạo ra cái gì, không mô tả
    #  mình được đọc cái gì. Đây cũng là cổng DUY NHẤT của module đã có lọc phạm
    #  vi từ trước, nên giữ nguyên cả mã 403 — đợt siết phạm vi 05/09/2026 không
    #  đổi hành vi của cổng đang chạy đúng.
    s = apply_scope(service.query_by_id(db, sid),
                    SurveyRequest, "survey_request", user, prof).first()
    if not s:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    return success(_out(db, service.clone_sr(db, sid, user, prof)), "Đã nhân bản phiếu", 201)


@router.delete("/{sid}")
def delete_(sid: int, db: Session = Depends(get_db), user=Depends(require("survey_request", "delete"))):
    """Xóa một YCBG."""
    _in_scope(db, sid, user, "delete")
    service.delete_sr(db, sid, user.id)
    return success(None, "Đã xóa")


@router.delete("")
def bulk_delete_survey_requests(ids: str, db: Session = Depends(get_db), user=Depends(require("survey_request", "delete"))):
    """Xóa nhiều YCBG theo danh sách id trong phạm vi được xóa."""
    id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
    if not id_list:
        raise HTTPException(400, "Không có ID hợp lệ")
    # Lọc phạm vi TRƯỚC vòng lặp (khuôn của `contract/controller.py`): xóa hàng loạt mà chỉ
    # lặp theo id thì gửi đại một dãy số là dọn sạch YCBG của mọi pháp nhân.
    rows = apply_scope(service.query_by_ids(db, id_list),
                       SurveyRequest, "survey_request", user,
                       get_perm_profile(db, user), "delete").all()
    if not rows:
        raise HTTPException(403, "Ngoài phạm vi được phép xóa")
    #  bao-CR-547: kiểm CẢ LÔ trước khi xóa phiếu nào — chỉ phiếu Nháp (đại ca chốt 01/10/2026).
    ensure_all_draft(rows, "phiếu yêu cầu báo giá")
    for sid in [r.id for r in rows]:
        try:
            service.delete_sr(db, sid, user.id)
        except Exception as e:
            raise HTTPException(400, f"Lỗi khi xóa phiếu ID {sid}: {str(e)}") from e
    # Báo đúng số ĐÃ xóa, không báo số đã gửi lên — lệch nhau là có id ngoài phạm vi.
    return success(None, f"Đã xóa {len(rows)} bản ghi")


@router.post("/{sid}/submit")
def submit_(sid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("survey_request", "read"))):
    """Gửi duyệt YCBG ở trạng thái Nháp hoặc Bị trả lại."""
    s = _in_scope(db, sid, user, "read")
    if not _can_edit_own(db, s, user):
        raise HTTPException(403, "Không có quyền gửi duyệt phiếu này")
    if s.status not in ("draft", "rejected"):
        raise HTTPException(400, "Chỉ gửi duyệt phiếu ở trạng thái Nháp hoặc Bị trả lại")
    from app.core.print_signers import default_approver_to_head
    default_approver_to_head(s)          # bao-CR-499: phiếu chưa chọn người duyệt → Trưởng bộ phận
    s = service.set_status(db, sid, "submitted", user.id)
    # CHỈ Trưởng bộ phận duyệt (1 người). Phiếu đã chọn đích danh TBP (kể cả TBP
    # phòng khác — QA 29/08) thì báo đúng người đó; chưa chọn thì lùi về TBP của
    # phòng YC như cũ.
    from app.modules.notification.service import get_department_head_users
    recips = []
    if s.head_of_dept_id:
        recips = service.active_users_of_employee(db, s.head_of_dept_id)
    if not recips:
        recips = get_department_head_users(db, s.department or "", s.department_id or 0)
    # bao-CR-499: người được CHỌN ở ô "Trưởng phòng phê duyệt" cũng nhận báo duyệt.
    if s.approver_employee_id:
        chosen = service.active_users_of_employee(db, s.approver_employee_id)
        seen = {u.id for u in recips}
        recips = list(recips) + [u for u in chosen if u.id not in seen]
    _notify(db, recips,
            f"{s.code} — Yêu cầu phê duyệt YCBG",
            f"Có yêu cầu báo giá mới ({s.code}) cần bạn duyệt.",
            f"/survey-requests/{s.id}", s.created_by or user.id, background_tasks, doc_code=s.code)
    return success(_out(db, s), "Đã gửi duyệt")


@router.post("/{sid}/approve")
def approve_(sid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("survey_request", "approve"))):
    """Duyệt YCBG và ghi người duyệt lên bản in."""
    _in_scope(db, sid, user, "approve")
    s = service.set_status(db, sid, "approved", user.id)
    # bao-CR-490: ghi nhân sự vừa duyệt vào "Trưởng phòng phê duyệt".
    from app.core.print_signers import stamp_approver
    stamp_approver(db, s, user.id)
    db.commit()
    # bao-CR-414: tự gán NSTM theo phân loại (Task 4) — tra theo phòng đang xử lý phiếu; người
    # duyệt chỉ có bậc `dept_proc` (quản lý thu mua CỦA PHÒNG) thì không rơi về bộ của phòng thu
    # mua mặc định (bao-CR-524, trước là "Thu mua chung").
    dept_only = approves_only_in_dept_proc(get_perm_profile(db, user), "survey_request")
    service.auto_assign(db, s, allow_global_assignee=not dept_only)
    s = service.set_status(db, sid, "processing", user.id)   # duyệt xong -> chuyển sang Đang xử lý
    from app.modules.notification.service import get_users_by_role_codes, get_user_display_name
    creator_user = service.user_with_id(db, s.created_by or user.id)
    creator_name = get_user_display_name(db, creator_user) if creator_user else "Hệ thống"

    # 1. Báo cho Người tạo (nội dung 'của bạn')
    if creator_user:
        _notify(db, [creator_user],
                f"{s.code} — Đã duyệt YCBG",
                f"Yêu cầu báo giá {s.code} của bạn đã được duyệt, chuyển sang xử lý khảo sát.",
                f"/survey-requests/{s.id}", s.created_by or user.id, background_tasks, doc_code=s.code)

    # 2. Báo cho Admin TM (nội dung 'tạo bởi {creator_name}')
    admins = get_users_by_role_codes(db, ["pur_admin"])
    _notify(db, admins,
            f"{s.code} — Thông báo đã duyệt YCBG",
            f"Yêu cầu báo giá {s.code} (tạo bởi {creator_name}) đã được duyệt, chuyển sang xử lý khảo sát.",
            f"/survey-requests/{s.id}", s.created_by or user.id, background_tasks, doc_code=s.code)
    # Báo cho các NSTM vừa được TỰ GÁN theo phân loại
    codes = {ln.assignee for ln in service.lines_of(db, s.id) if ln.assignee}
    if codes:
        _notify(db, _users_of_codes(db, list(codes)),
                f"{s.code} — Phân công khảo sát giá",
                f"Bạn được phân công khảo sát trong phiếu {s.code} (vừa được duyệt).",
                f"/survey-requests/{s.id}/process", user.id, background_tasks, doc_code=s.code)
    return success(_out(db, s), "Đã duyệt — chuyển sang xử lý")


@router.post("/{sid}/reject")
def reject_(sid: int, data: RejectIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
            user=Depends(require("survey_request", "approve"))):
    """TRẢ ĐƠN — trả về để người YC sửa & gửi lại (như nháp). status → rejected (còn sửa được).
    bao-CR-554: trả được cả phiếu đã duyệt / đang xử lý khi việc khảo sát chưa bắt đầu."""
    _in_scope(db, sid, user, "approve")
    s = service.return_to_requester(db, sid, data.reason, user.id)
    reqs = service.users_with_id(db, s.created_by or user.id)
    _notify(db, reqs, f"{s.code} — Bị trả lại YCBG",
            f"Yêu cầu báo giá {s.code} của bạn bị TRẢ LẠI để chỉnh sửa. Lý do: {data.reason or '(không nêu)'}",
            f"/survey-requests/{s.id}", s.created_by or user.id, background_tasks, doc_code=s.code)
    return success(_out(db, s), "Đã trả đơn")


@router.post("/{sid}/cancel")
def cancel_(sid: int, data: RejectIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
            user=Depends(require("survey_request", "approve"))):
    """TỪ CHỐI — khóa đơn hẳn (không sửa được nữa, phải làm đơn mới). status → cancelled."""
    _in_scope(db, sid, user, "approve")
    s = service.set_status(db, sid, "cancelled", user.id, data.reason)
    reqs = service.users_with_id(db, s.created_by or user.id)
    _notify(db, reqs, f"{s.code} — Từ chối YCBG",
            f"Yêu cầu báo giá {s.code} của bạn bị TỪ CHỐI (khóa đơn). Lý do: {data.reason or '(không nêu)'}",
            f"/survey-requests/{s.id}", s.created_by or user.id, background_tasks, doc_code=s.code)
    return success(_out(db, s), "Đã từ chối (khóa đơn)")


def _transfer_dept(db: Session, sid: int, data: TransferDeptIn, background_tasks: BackgroundTasks,
                   user, *, target: int, message: str):
    s = _in_scope(db, sid, user, "approve")
    if not holds_handling_dept(get_perm_profile(db, user), "survey_request", s, get_central_dept_id(db)):
        raise HTTPException(403, "Chỉ quản lý thu mua của phòng đang xử lý mới chuyển được phiếu này")
    old_assignees = [ln.assignee for ln in service.lines_of(db, sid) if ln.assignee]
    s = service.transfer_handler_dept(db, sid, target, data.reason, user.id)
    creator = service.users_with_id(db, s.created_by or user.id)
    where = "phòng thu mua" if not int(target or 0) else "phòng xử lý khác"   # bao-CR-524
    _notify(db, creator, f"{s.code} — Chuyển {where}",
            f"Yêu cầu báo giá {s.code} được chuyển sang {where}. Lý do: {data.reason.strip()}",
            f"/survey-requests/{s.id}", user.id, background_tasks, doc_code=s.code)
    if old_assignees:                                  # NSTM bị gỡ khỏi dòng cũng cần biết
        _notify(db, _users_of_codes(db, sorted(set(old_assignees))),
                f"{s.code} — Gỡ phân công khảo sát",
                f"Phiếu {s.code} đã chuyển {where}, phần khảo sát của bạn được gỡ. Lý do: {data.reason.strip()}",
                f"/survey-requests/{s.id}", user.id, background_tasks, doc_code=s.code)
    return success(_out(db, s, user), message)


@router.post("/{sid}/transfer-dept")
def transfer_dept_(sid: int, data: TransferDeptIn, background_tasks: BackgroundTasks,
                   db: Session = Depends(get_db), user=Depends(require("survey_request", "approve"))):
    """bao-CR-414 GĐ5 — CHUYỂN PHÒNG XỬ LÝ: gỡ NSTM + ngày tiếp nhận mọi dòng, đổi phòng;
    trạng thái giữ nguyên (YCBG không có bước điều phối riêng). Lý do bắt buộc, ghi nhật ký."""
    return _transfer_dept(db, sid, data, background_tasks, user,
                          target=data.handler_dept_id, message="Đã chuyển phòng xử lý")


@router.post("/{sid}/return-dept")
def return_dept_(sid: int, data: TransferDeptIn, background_tasks: BackgroundTasks,
                 db: Session = Depends(get_db), user=Depends(require("survey_request", "approve"))):
    """bao-CR-414 GĐ5 — TRẢ VỀ THU MUA: cùng điều kiện, đích là phòng thu mua mặc định
    (bao-CR-524: ghi id thật của PBA017, không còn `0` = "Thu mua chung" ảo)."""
    return _transfer_dept(db, sid, data, background_tasks, user, target=0,
                          message="Đã trả phiếu về phòng thu mua")


@router.patch("/{sid}/lines/{line_id}/assignee")
def set_line_assignee_(sid: int, line_id: int, data: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
                       user=Depends(require("survey_request", "process"))):
    """Gán/đổi NSTM phụ trách 1 dòng — CHỈ thu mua side (NSTM/QL/Admin TM). Người YC không được. Body: {assignee: mã NV}.

    Phạm vi lấy theo `read`: `require(..., "process")` gác bằng CỜ suy ra (`is_purchaser`),
    không phải một hành động có trong `ACTIONS` — hỏi `scope_condition("process")` thì
    không grant nào có nó và cổng đóng sạch.
    """
    _in_scope(db, sid, user, "read")
    _ensure_sr_editable(service.get_sr(db, sid))
    # bao-CR-486: người phụ trách phải thuộc phòng xử lý của phiếu (kiểm trong service).
    ln = service.set_line_assignee(db, sid, line_id, data.get("assignee"), user.id)
    if ln.assignee:                                   # báo cho NSTM vừa được gán
        s = service.get_sr(db, sid)
        _notify(db, _users_of_codes(db, [ln.assignee]),
                f"{s.code} — Phân công khảo sát giá",
                f"Bạn được phân công phụ trách khảo sát trong phiếu {s.code}.",
                f"/survey-requests/{sid}/process", user.id, background_tasks, doc_code=s.code)
    return success(_out(db, service.get_sr(db, sid)), "Đã gán nhân sự phụ trách")


@router.patch("/{sid}/lines/{line_id}/status")
def set_line_completed_(sid: int, line_id: int, data: dict, db: Session = Depends(get_db),
                        user=Depends(require("survey_request", "write"))):
    """Đổi Tình trạng dòng (is_completed). Body: {is_completed: bool}. Chặn khi phiếu đã từ chối/hoàn thành.

    ⚠️ Tên hàm phải KHÁC `set_line_status_` ở dưới (route `/line-status`, đổi cột
    `line_status`) — hai hàm từng TRÙNG TÊN. FastAPI đăng ký theo decorator nên
    cả hai route vẫn chạy đúng, nhưng thuộc tính module bị bản sau đè: ai
    `import set_line_status_` lấy nhầm hàm, và mọi công cụ đọc mã chỉ thấy một.
    """
    _in_scope(db, sid, user, "write")
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


@router.get("/{sid}/assignable-staff")
def assignable_staff_(sid: int, db: Session = Depends(get_db),
                      user=Depends(require("survey_request", "read"))):
    """bao-CR-486 — NSTM chọn được cho YCBG này: đi theo ô "Phòng xử lý" (cùng luật YCMH)."""
    from app.modules.category_assignee.service import assignable_staff
    s = _in_scope(db, sid, user, "read")
    return success({"items": [{"id": e.id, "code": e.code, "full_name": e.full_name,
                               "department_id": int(e.department_id or 0)}
                              for e in assignable_staff(db, s)]})


@router.get("/{sid}/process")
def process_view_(sid: int, db: Session = Depends(get_db), up=Depends(_purchaser)):
    """Trang *Xử lý khảo sát* (CR-222).

    `_purchaser` là cổng VAI TRÒ (grant `survey_request.read` phạm vi proc|all) — nó chặt
    hơn `require()` nhưng KHÔNG biết phiếu thuộc pháp nhân nào. Thiếu `_in_scope` thì NSTM
    lộ đầu phiếu, còn Admin TM (đọc-chỉ, đi nhánh "giám sát" của `_see_all_lines`) lộ cả
    dòng của phiếu ngoài phạm vi.
    """
    user, prof = up
    s = _in_scope(db, sid, user, "read")
    return success(_out_process(db, s, user, prof))


@router.get("/{sid}/lines/{line_id}/available-survey-lines")
def available_survey_lines_(sid: int, line_id: int,
                            supplier_code: list[str] = Query(default=[]),
                            item_group: list[str] = Query(default=[]),
                            search: str = "", page: int = 1, page_size: int = 8,
                            sort_by: str = "", sort_dir: str = "desc",
                            db: Session = Depends(get_db), up=Depends(_purchaser)):
    """Dòng phiếu khảo sát đã duyệt có thể gắn làm phương án cho một dòng YCBG; phải có ít nhất một bộ lọc."""
    _in_scope(db, sid, up[0], "read")
    service.get_line(db, sid, line_id)   # xác thực dòng thuộc phiếu (sai thì 404)
    # Lọc MỞ (chọn NCC thủ công) — KHÔNG giới hạn liên kết YCKS: option có thể đã có khảo sát sẵn.
    # Phân loại mặc định = của dòng (FE gửi sẵn); có thể đổi hoặc để trống. Cần ≥1 tiêu chí.
    # bao-CR-487: `supplier_code` / `item_group` lặp được trên URL (?supplier_code=A&supplier_code=B)
    # = chọn NHIỀU; gửi một giá trị như cũ vẫn chạy.
    supplier_code = service.normalize_filter_values(supplier_code)
    item_group = service.normalize_filter_values(item_group)
    if not (supplier_code or item_group or (search or "").strip()):
        return success({"items": [], "total": 0})
    rows, total = service.available_survey_lines(
        db, supplier_code=supplier_code, item_group=item_group, search=search,
        page=page, page_size=page_size, sort_by=sort_by, sort_dir=sort_dir)
    return success({"items": _out_available_lines(db, rows), "total": total})


@router.post("/{sid}/lines/{line_id}/options")
def add_option_(sid: int, line_id: int, data: dict, db: Session = Depends(get_db), up=Depends(_purchaser)):
    """Gắn phương án cho một dòng YCBG khi phiếu đang xử lý hoặc đã khảo sát."""
    user, prof = up
    s = _in_scope(db, sid, user, "read")
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
    s = _in_scope(db, sid, user, "read")
    if s.status not in ("processing", "survey_done"):
        raise HTTPException(400, "Chỉ lấy phương án khi phiếu đang xử lý hoặc đã khảo sát")
    n = service.sync_options_from_surveys(db, sid, user.id)
    return success(_out_process(db, s, user, _prof), f"Đã lấy {n} phương án mới từ khảo sát" if n else "Đã lấy phương án từ khảo sát xong")


@router.delete("/{sid}/lines/{line_id}/options/{oid}")
def del_option_(sid: int, line_id: int, oid: int, db: Session = Depends(get_db), up=Depends(_purchaser)):
    """Gỡ một phương án của dòng YCBG chưa tạo YCMH."""
    user, prof = up
    _in_scope(db, sid, user, "read")
    ln = service.get_line(db, sid, line_id)
    if ln.is_completed:
        raise HTTPException(400, "Dòng đã tạo yêu cầu mua hàng — không xóa phương án được")
    if not service.can_process_line(db, ln, prof):
        raise HTTPException(403, "Bạn không phụ trách dòng này")
    service.delete_option(db, line_id, oid, user.id)
    return success(_out_process(db, service.get_sr(db, sid), user, prof), "Đã xóa option")


@router.patch("/{sid}/lines/{line_id}/options/{oid}")
def edit_option_(sid: int, line_id: int, oid: int, data: dict, db: Session = Depends(get_db), up=Depends(_purchaser)):
    """Sửa một phương án của dòng YCBG; chỉ người phụ trách dòng."""
    user, prof = up
    _in_scope(db, sid, user, "read")
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
    _in_scope(db, sid, user, "read")
    empty_ids = (data or {}).get("empty_line_ids") or []
    s, fully, resurveyed = service.complete_sr(db, sid, user, prof, empty_ids)
    if fully:   # cả phiếu xong -> báo người yêu cầu vào chọn phương án
        reqs = service.users_with_id(db, s.created_by or user.id)
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

#  Danh sách trắng trường trả cho người YC + `_out_result` nằm ở `serializer.py` (bao-CR-711).


@router.get("/{sid}/result")
def result_view_(sid: int, db: Session = Depends(get_db),
                 user=Depends(require("survey_request", "read"))):
    """Kết quả khảo sát cho người YC — ẩn NCC ở tầng backend (whitelist field)."""
    prof = get_perm_profile(db, user)
    s = apply_scope(service.query_by_id(db, sid),
                    SurveyRequest, "survey_request", user, prof).first()
    if not s:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    return success(_out_result(db, s, user, prof))


@router.patch("/{sid}/lines/{line_id}/options/{oid}/choose")
def choose_option_(sid: int, line_id: int, oid: int, db: Session = Depends(get_db),
                   user=Depends(require("survey_request", "write"))):
    """Người YC chọn 1 phương án cho 1 sản phẩm (chỉ khi đã hoàn thành khảo sát)."""
    s = _in_scope(db, sid, user, "write")
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
    s = _in_scope(db, sid, user, "write")
    # Chỉ NGƯỜI YÊU CẦU (người tạo phiếu HOẶC người yêu cầu dù admin tạo giùm) hoặc Admin TM
    # (quyền delete) được tạo YCMH — NSTM thì không.
    rid = getattr(user, "employee_id", 0) or 0
    is_requester = s.created_by == user.id or (rid and s.requester_id == rid)
    if not (is_requester or user_has_permission(db, user, "survey_request", "delete")):
        raise HTTPException(403, "Chỉ người yêu cầu mới được tạo Yêu cầu mua hàng")
    prs = service.create_prs(db, sid, user.id)
    return success({"created_prs": [{"id": p.id, "code": p.code} for p in prs], "sr": _out(db, s)},
                   f"Đã tạo {len(prs)} phiếu yêu cầu mua hàng")


@router.patch("/{sid}/lines/{line_id}/line-status")
def set_line_status_(sid: int, line_id: int, body: LineStatusIn,
                     background_tasks: BackgroundTasks = None,
                     db: Session = Depends(get_db),
                     user=Depends(require("survey_request", "write"))):
    """Task 2: người YC / cùng phòng ban đổi trạng thái dòng khảo sát
    ("" chưa xác định · cần khảo sát lại · hoàn thành)."""
    s = _in_scope(db, sid, user, "write")
    _ensure_sr_editable(s)
    if not _can_act_as_requester_side(db, s, user):
        raise HTTPException(403, "Chỉ người yêu cầu hoặc cùng phòng ban được đổi trạng thái dòng")
    service.set_line_status(db, sid, line_id, body.line_status, user.id)
    # LỖI CŨ: chỗ này so với chuỗi tiếng Việt CÓ DẤU "cần khảo sát lại", trong khi giá trị hợp lệ
    # chỉ là slug -> nhánh không bao giờ chạy, NSTM/pur_admin chưa từng nhận chuông khi bị trả về.
    if (body.line_status or "").strip() == LS_RESURVEY:
        ln = service.get_line(db, sid, line_id)
        recips = []
        if ln and ln.assignee:
            recips += _users_of_codes(db, [ln.assignee])
        from app.modules.notification.service import get_users_by_role_codes
        recips += get_users_by_role_codes(db, ["pur_admin"])
        _notify(db, recips, f"[Khảo sát lại] YCBG {s.code}",
                f"Người yêu cầu đặt trạng thái dòng '{ln.item_group or 'sản phẩm'}' thành Cần khảo sát lại.",
                f"/survey-requests/{s.id}/process", user.id, background_tasks, doc_code=s.code)
    return success(_out(db, s, user, get_perm_profile(db, user)), "Đã cập nhật trạng thái dòng")


@router.post("/{sid}/finalize")
def finalize_(sid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
              user=Depends(require("survey_request", "write"))):
    """Chuyển Hoàn thành (pr_created/survey_done → done). Cho phép Quản lý/Admin thu mua
    (purchaser + quyền approve) HOẶC người yêu cầu / cùng phòng ban người yêu cầu (Task 3).
    Lưu ý: NSTM thường (purchaser nhưng không có approve) KHÔNG được đóng phiếu."""
    s = _in_scope(db, sid, user, "write")
    prof = get_perm_profile(db, user)
    is_mgr = service.is_purchaser(prof) and user_has_permission(db, user, "survey_request", "approve")
    if not (is_mgr or _can_act_as_requester_side(db, s, user)):
        raise HTTPException(403, "Chỉ Quản lý/Admin thu mua hoặc phòng ban yêu cầu được chuyển Hoàn thành")
    s = service.finalize_sr(db, sid, user.id)
    reqs = service.users_with_id(db, s.created_by or user.id)
    _notify(db, reqs, f"[Hoàn thành] Phiếu khảo sát {s.code}",
            f"Phiếu {s.code} đã được chuyển sang Hoàn thành.",
            f"/survey-requests/{s.id}", s.created_by or user.id, background_tasks)
    return success(_out(db, s), "Đã chuyển Hoàn thành")
