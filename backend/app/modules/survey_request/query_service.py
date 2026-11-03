"""YCBG — truy vấn đọc cho controller / serializer: danh sách, lọc, tra người dùng, chuông, tệp đính kèm (bao-CR-715
tách từ service.py; phần lớn dời từ controller ở bao-CR-711).
"""
from sqlalchemy.orm import Session

from .model import SurveyRequest, SurveyRequestLine, SurveyRequestOption, SurveyRequestPr
from .base_service import FILTERABLE


# ═══════════════ Truy vấn + chuông dời từ controller (bao-CR-711, không đổi hành vi) ═══════════════
#
# Controller chỉ còn gác quyền + phạm vi rồi gọi xuống đây. Các hàm `query_*` trả câu truy
# vấn CHƯA lọc phạm vi — chỗ gọi phải tự lọc (`apply_scope` hoặc `_scope_with_named_head`).


def query_by_id(db: Session, sid: int):
    """Một YCBG theo id, CHƯA lọc phạm vi, CHƯA bỏ phiếu xóa mềm — nền của hai cổng cũ dùng
    thẳng `apply_scope` (nhân bản, xem kết quả); giữ nguyên câu truy vấn của chúng."""
    return db.query(SurveyRequest).filter(SurveyRequest.id == sid)


def query_live_by_id(db: Session, sid: int):
    """Như `query_by_id` nhưng bỏ phiếu đã xóa mềm (ai-CR-170) — nền của `_in_scope` và `GET /{sid}`."""
    from app.core.scoping import not_deleted_cond
    return db.query(SurveyRequest).filter(SurveyRequest.id == sid, not_deleted_cond(SurveyRequest))


def query_by_ids(db: Session, ids: list[int]):
    """Nhiều YCBG theo id — nền của xóa hàng loạt (lọc phạm vi `delete` ở controller)."""
    return db.query(SurveyRequest).filter(SurveyRequest.id.in_(ids))


def build_list_query(db: Session, request):
    """Bộ lọc màn danh sách YCBG (CHƯA lọc phạm vi) — dùng chung cho danh sách và xuất Excel
    (CR-068) qua `controller._list_query`."""
    from sqlalchemy import or_, select

    from app.core.base_controller import apply_equals, apply_filters, apply_range_filters
    from app.core.ref_filter import apply_ref_filters
    from app.core.scoping import not_deleted_cond

    # `code` chỉ bị loại khỏi lọc TRẦN (nhường cho ô tìm kiếm đa trường), bộ lọc điều kiện
    # `code__contains=...` vẫn phải chạy -> truyền FILTERABLE đầy đủ cho vế operator.
    filterable = [f for f in FILTERABLE if f != "code"]
    #  ai-CR-170: danh sách + xuất Excel bỏ phiếu đã xóa mềm (lọc tay vì phạm vi ở đây đi qua
    #  `_scope_with_named_head`, không qua `apply_scope`).
    q = apply_filters(db.query(SurveyRequest).filter(not_deleted_cond(SurveyRequest)),
                      SurveyRequest, request, filterable,
                      operator_filterable=FILTERABLE)
    q = apply_ref_filters(q, SurveyRequest, request, db)      # CR-088
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
    # Ô tìm kiếm nhanh: Tìm theo Mã phiếu, Mục đích, Người yêu cầu, Mô tả hoặc Mã/Tên sản phẩm ở dòng/phương án
    search = (request.query_params.get("code") or request.query_params.get("q") or request.query_params.get("search") or request.query_params.get("product") or "").strip()
    if search:
        like = f"%{search}%"
        chosen_line_ids = [
            r[0] for r in db.query(SurveyRequestOption.survey_request_line_id)
            .filter(
                SurveyRequestOption.is_chosen == True,  # noqa: E712
                or_(SurveyRequestOption.system_product_code.like(like), SurveyRequestOption.snap_product_name.like(like))
            ).all() if r[0]
        ]
        line_conds = [
            SurveyRequestLine.requirement_detail.like(like),
            SurveyRequestLine.other_requirement.like(like),
        ]
        if chosen_line_ids:
            line_conds.append(SurveyRequestLine.id.in_(chosen_line_ids))

        matching_sr_ids = [
            r[0] for r in db.query(SurveyRequestLine.survey_request_id)
            .filter(or_(*line_conds)).all() if r[0]
        ]

        conds = [
            SurveyRequest.code.like(like),
            SurveyRequest.purpose.like(like),
            SurveyRequest.requester.like(like),
        ]
        if matching_sr_ids:
            conds.append(SurveyRequest.id.in_(matching_sr_ids))
        q = q.filter(or_(*conds))
    return q


def employee_names_by_code(db: Session, codes: set) -> dict:
    """`{mã nhân sự: họ tên}` của NSTM phụ trách các dòng — một truy vấn cho cả phiếu."""
    if not codes:
        return {}
    from app.modules.employee.model import Employee
    return {e.code: e.full_name for e in db.query(Employee).filter(Employee.code.in_(codes)).all()}


def same_dept_as_requester(db: Session, s, user) -> bool:
    """True nếu user CÙNG phòng ban với người yêu cầu của phiếu.
    Ưu tiên so `department_id` (qua Employee); fallback so tên phòng ban với `s.department`.

    Hai lần `db.get(Employee)` là hồ sơ của CHÍNH người gọi và của người yêu cầu trên phiếu đã
    qua cổng phạm vi ở route — chỉ để so phòng ban (bao-CR-711 dời từ controller)."""
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
    # CR-086: chưa suy ra được phòng của người yêu cầu thì lấy phòng ghi trên phiếu — ưu tiên id,
    # tên chỉ dùng cho phiếu cũ chưa điền lùi được id (bỏ nhánh tên ở N-008).
    if s.department_id and ue.department_id:
        return ue.department_id == s.department_id
    return bool(s.department) and (ue.department_name or "") == s.department


def notify(db, users, title, body, link, creator_id, background_tasks=None, doc_code=""):
    """Chuông trong app + Web Push + email quy trình cho một nhóm tài khoản (khử trùng theo id)."""
    from app.modules.notification.model import Notification
    from app.modules.user.model import User
    recipients = []
    seen = set()
    for u in users:
        if u and u.id not in seen:
            seen.add(u.id)
            recipients.append(u)
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

    # EMAIL workflow (chỉ dev/UAT khi EMAIL_WORKFLOW_ENABLED)
    try:
        from app.modules.notification.service import _send_workflow_emails
        creator = db.query(User).filter(User.id == creator_id).first()
        creator_name = creator.email if creator else "Hệ thống"
        _send_workflow_emails(db, background_tasks, recipients, title, body,
                              "survey_request", doc_code, creator_name, "", "", False, link)
    except Exception:
        pass


def users_of_codes(db, codes):
    """Tài khoản user theo danh sách mã NV (để thông báo NSTM được phân công)."""
    codes = [c for c in codes if c]
    if not codes:
        return []
    from app.modules.employee.model import Employee
    from app.modules.user.model import User
    emp_ids = [e.id for e in db.query(Employee).filter(Employee.code.in_(codes)).all()]
    return db.query(User).filter(User.employee_id.in_(emp_ids)).all() if emp_ids else []


def users_with_id(db: Session, user_id: int) -> list:
    """Tài khoản có đúng id này, dạng danh sách (rỗng nếu không có) — người nhận chuông."""
    from app.modules.user.model import User
    return db.query(User).filter(User.id == user_id).all()


def user_with_id(db: Session, user_id: int):
    from app.modules.user.model import User
    return db.query(User).filter(User.id == user_id).first()


def active_users_of_employee(db: Session, employee_id: int) -> list:
    """Tài khoản ĐANG HOẠT ĐỘNG gắn với một nhân sự — người nhận báo duyệt."""
    from app.modules.user.model import User
    return db.query(User).filter(User.employee_id == employee_id,
                                 User.is_active == True).all()   # noqa: E712


def survey_line_files(db: Session, psl_id: int) -> list:
    """`[(FileLink, StoredFile)]` đính kèm của một dòng khảo sát SP (entity 'survey_line'), mới trước."""
    from app.modules.attachment.model import FileLink, StoredFile
    return (db.query(FileLink, StoredFile)
            .join(StoredFile, StoredFile.id == FileLink.file_id)
            .filter(FileLink.entity == "survey_line", FileLink.entity_id == psl_id)
            .order_by(FileLink.id.desc()).all())


def survey_product_line(db: Session, psl_id: int):
    """Dòng khảo sát SP nguồn của một phương án — chỉ lấy ngày trả kết quả + ghi chú để hiện,
    không lộ NCC (bao-CR-711 dời từ controller)."""
    from app.modules.survey.model import SurveyProductLine
    return db.get(SurveyProductLine, psl_id)


def pr_links_of(db: Session, sid: int) -> tuple[list, dict]:
    """Các YCMH đã tạo theo phương án của phiếu: `(dòng liên kết theo thứ tự ghi, {id YCMH: YCMH})`."""
    from app.modules.purchase_request.model import PurchaseRequest
    links = db.query(SurveyRequestPr).filter(SurveyRequestPr.survey_request_id == sid).order_by(SurveyRequestPr.id).all()
    pr_ids = {ln.pr_id for ln in links}
    pr_map = {p.id: p for p in db.query(PurchaseRequest).filter(PurchaseRequest.id.in_(pr_ids)).all()} if pr_ids else {}
    return links, pr_map
