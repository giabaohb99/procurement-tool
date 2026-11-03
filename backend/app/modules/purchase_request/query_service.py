"""YCMH — truy vấn đọc cho controller / serializer: danh sách, lọc, tra tên, chuông (bao-CR-715 tách từ service.py;
phần lớn dời từ controller ở bao-CR-711).
"""
from sqlalchemy.orm import Session

from .model import PurchaseRequest, PurchaseRequestItem
from .base_service import ENTITY, FILTERABLE, LINE_STATUS_CANCELLED, items_of


def list_pr(db: Session, base_query, pg: dict):
    total = base_query.count()
    items = base_query.order_by(PurchaseRequest.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


# ═══════════════ Truy vấn dời từ controller (bao-CR-711, không đổi hành vi) ═══════════════
#
# Controller chỉ còn gác quyền + phạm vi rồi gọi xuống đây. Các hàm `query_*` trả câu truy
# vấn CHƯA lọc phạm vi — chỗ gọi phải tự `apply_scope(...)`, đúng action của route.


def query_by_id(db: Session, pid: int):
    """Câu truy vấn một YCMH theo id, CHƯA lọc phạm vi và CHƯA bỏ phiếu xóa mềm (cổng đọc
    `GET /{pid}` cũ đi đúng câu này — giữ nguyên)."""
    return db.query(PurchaseRequest).filter(PurchaseRequest.id == pid)


def query_live_by_id(db: Session, pid: int):
    """Như `query_by_id` nhưng bỏ phiếu đã xóa mềm — nền của `_in_scope` ở controller."""
    return db.query(PurchaseRequest).filter(PurchaseRequest.id == pid,
                                            PurchaseRequest.is_deleted == False)  # noqa: E712


def query_live_by_ids(db: Session, ids: list[int]):
    """Nhiều YCMH theo id, bỏ phiếu xóa mềm — nền của xóa hàng loạt (lọc phạm vi ở controller)."""
    return db.query(PurchaseRequest).filter(PurchaseRequest.id.in_(ids),
                                            PurchaseRequest.is_deleted == False)  # noqa: E712


def build_list_query(db: Session, request):
    """Bộ lọc màn danh sách YCMH (CHƯA lọc phạm vi, CHƯA sắp xếp) — dùng chung cho màn danh
    sách và xuất Excel qua `controller._list_query`."""
    from sqlalchemy import or_, select

    from app.core.base_controller import apply_equals, apply_filters, apply_range_filters
    from app.core.ref_filter import apply_ref_filters

    # `code` bị loại khỏi lọc TRẦN vì param `code=` dưới đây là ô tìm kiếm đa trường; nhưng bộ
    # lọc điều kiện (`code__contains=...`) vẫn phải lọc được nên giữ nguyên FILTERABLE đầy đủ.
    filterable = [f for f in FILTERABLE if f != "code"]
    query = apply_filters(db.query(PurchaseRequest).filter(PurchaseRequest.is_deleted == False),  # noqa: E712
                          PurchaseRequest, request, filterable, operator_filterable=FILTERABLE)
    query = apply_ref_filters(query, PurchaseRequest, request, db)   # CR-088
    query = apply_range_filters(query, PurchaseRequest, request,
                                ["request_date", "received_date", "need_date"])
    query = apply_equals(query, PurchaseRequest, request, ["company_id"])
    item_group = (request.query_params.get("item_group") or "").strip()
    if item_group:
        sub = select(PurchaseRequestItem.pr_id).where(PurchaseRequestItem.item_group.like(f"%{item_group}%"))
        query = query.filter(PurchaseRequest.id.in_(sub))
    assignee = (request.query_params.get("assignee") or "").strip()
    if assignee:
        sub2 = select(PurchaseRequestItem.pr_id).where(PurchaseRequestItem.assignee == assignee)
        query = query.filter(PurchaseRequest.id.in_(sub2))
    # Ô tìm kiếm nhanh: Tìm theo Mã PYC, Người yêu cầu, Mục đích, Mã sản phẩm hoặc Tên sản phẩm ở dòng hàng
    search = (request.query_params.get("code") or request.query_params.get("q") or request.query_params.get("search") or request.query_params.get("product") or "").strip()
    if search:
        like = f"%{search}%"
        matching_ids = [
            r[0] for r in db.query(PurchaseRequestItem.pr_id)
            .filter(or_(PurchaseRequestItem.product_code.like(like), PurchaseRequestItem.product_name.like(like))).all()
            if r[0]
        ]
        conds = [
            PurchaseRequest.code.like(like),
            PurchaseRequest.requester.like(like),
            PurchaseRequest.purpose.like(like),
        ]
        if matching_ids:
            conds.append(PurchaseRequest.id.in_(matching_ids))
        query = query.filter(or_(*conds))
    return query


def list_line_summaries(db: Session, pr_ids: list[int]) -> tuple[dict, dict, set]:
    """Số liệu dòng cho một trang danh sách — ba truy vấn cho cả trang, không N+1.

    Trả `(tổng tiền gồm VAT theo phiếu, ngày cần sớm nhất của dòng chưa hủy, id phiếu có dòng hủy)`.
    """
    from sqlalchemy import func

    subtotals = {}
    need_dates = {}
    if pr_ids:
        subtotals = {
            pr_id: float(amount or 0) for pr_id, amount in db.query(
                PurchaseRequestItem.pr_id,
                func.sum(PurchaseRequestItem.amount)
            ).filter(PurchaseRequestItem.pr_id.in_(pr_ids)).group_by(PurchaseRequestItem.pr_id).all()
        }
        need_rows = db.query(
            PurchaseRequestItem.pr_id,
            func.min(PurchaseRequestItem.required_date)
        ).filter(
            PurchaseRequestItem.pr_id.in_(pr_ids),
            PurchaseRequestItem.required_date != "",
            PurchaseRequestItem.required_date.isnot(None),
            PurchaseRequestItem.line_status != LINE_STATUS_CANCELLED
        ).group_by(PurchaseRequestItem.pr_id).all()
        need_dates = {r[0]: r[1] for r in need_rows if r[1]}

    cancelled_ids = set()
    if pr_ids:
        cancelled_ids = {r[0] for r in db.query(PurchaseRequestItem.pr_id).filter(
            PurchaseRequestItem.pr_id.in_(pr_ids),
            PurchaseRequestItem.line_status == LINE_STATUS_CANCELLED).distinct().all()}
    return subtotals, need_dates, cancelled_ids


def assigned_user_ids(db: Session, pr: PurchaseRequest) -> list[int]:
    """Tài khoản ĐANG HOẠT ĐỘNG của NSTM phụ trách phiếu (NSTM đầu phiếu + NSTM từng dòng) —
    người nhận chuông "được phân công phụ trách". Rỗng = không ai để báo."""
    from app.modules.employee.model import Employee
    from app.modules.user.model import User as _User
    emp_ids = set()
    if pr.assignee_id:
        emp_ids.add(pr.assignee_id)
    codes = [it.assignee for it in items_of(db, pr.id) if it.assignee]
    if codes:
        emp_ids.update(e.id for e in db.query(Employee).filter(Employee.code.in_(codes)).all())
    if not emp_ids:
        return []
    return [u.id for u in db.query(_User).filter(_User.employee_id.in_(emp_ids), _User.is_active == True).all()]  # noqa: E712


def user_ids_of_employee_codes(db: Session, codes: list[str]) -> list[int]:
    from app.modules.employee.model import Employee
    from app.modules.user.model import User
    codes = [c for c in codes if c]
    if not codes:
        return []
    emp_ids = [e.id for e in db.query(Employee).filter(Employee.code.in_(codes)).all()]
    return [u.id for u in db.query(User).filter(User.employee_id.in_(emp_ids)).all()] if emp_ids else []


def notify_users(db: Session, user_ids: list[int], title: str, body: str, link: str,
                 creator_id: int, background_tasks=None) -> None:
    """Chuông trong app + Web Push (best-effort) cho một nhóm tài khoản — dùng cho sự kiện
    chuyển phòng (bao-CR-414 GĐ5), thứ chưa có mẫu câu trong `trigger_notification`."""
    from app.modules.notification.model import Notification
    uids = sorted({int(u) for u in user_ids if u})
    if not uids:
        return
    for uid in uids:
        db.add(Notification(user_id=uid, title=title, body=body, link=link, created_by=creator_id))
    db.commit()
    try:
        from app.modules.push import service as push_service
        from app.core.database import SessionLocal
        if background_tasks is not None:
            background_tasks.add_task(push_service.send_to_users, SessionLocal, uids, title, body, link)
        else:
            push_service.send_to_users(SessionLocal, uids, title, body, link)
    except Exception:
        pass


def purchasing_head(db: Session, dispatcher_uid: int) -> tuple[str, str, int]:
    """bao-CR-397 — TRƯỞNG PHÒNG của phòng ban mà người bấm Điều phối đang thuộc.

    Ô "TP/BP mua hàng" trên bản in là chữ ký của trưởng phòng thu mua, không phải của
    người bấm nút: trên prod người điều phối thường là ADMIN thu mua (Châu Phúc Hậu) nên
    tên admin in vào ô trưởng phòng. Hệ không có cờ "phòng thu mua", nên lấy phòng của
    chính người điều phối (tài khoản -> nhân sự -> `department_id`) rồi đọc
    `Department.manager_id` — cột trưởng bộ phận chọn cứng ở danh mục Phòng ban.

    Phần tử thứ ba là id NHÂN SỰ trưởng phòng — bao-CR-531 so nó với người đại diện pháp luật
    để gộp ô "Giám đốc".

    Trả `("", "", 0)` khi không suy ra được (tài khoản chưa gắn nhân sự, nhân sự chưa có
    phòng, phòng chưa gán trưởng) — chỗ gọi tự lùi về người điều phối như trước CR này.
    Chữ ký tra theo NHÂN SỰ trưởng phòng (`resolve_signature_by_employee`) để ảnh khớp
    đúng tên đang in.

    Bốn lần `db.get` dưới đây là tra tên để in, không phải cổng phạm vi: id người điều phối
    lấy từ nhật ký của chính phiếu đã qua cổng phạm vi ở route.
    """
    from app.core.audit import resolve_signature_by_employee
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    user = db.get(User, dispatcher_uid) if dispatcher_uid else None
    emp = db.get(Employee, user.employee_id) if (user and user.employee_id) else None
    dept = db.get(Department, emp.department_id) if (emp and emp.department_id) else None
    head = db.get(Employee, dept.manager_id) if (dept and dept.manager_id) else None
    if not head or not (head.full_name or "").strip():
        return "", "", 0
    return head.full_name, resolve_signature_by_employee(db, head.id), int(head.id)


def audit_actors_of(db: Session, pr_id: int, actions: list[str]) -> list:
    """`[(action, created_by)]` của phiếu trong nhật ký thao tác, MỚI NHẤT trước — nguồn chữ ký
    hai bước duyệt trên bản in (`serializer._approval_signers`)."""
    from app.modules.audit.model import AuditLog
    return (db.query(AuditLog.action, AuditLog.created_by)
            .filter(AuditLog.entity == ENTITY, AuditLog.entity_id == pr_id,
                    AuditLog.action.in_(actions))
            .order_by(AuditLog.id.desc()).all())


def has_quote_file(db: Session, pr) -> bool:
    """bao-CR-317 — phiếu này có BÁO GIÁ đính kèm hay không (ô tick trên bản in).

    Trước CR này bản in chỉ soi cột `quote_file_url` — ô tải đúng 1 file từ thời đầu, nay
    không màn nào ghi vào nữa (prod: 0/116 phiếu có giá trị). Chứng từ đã dời hết sang khối
    "Chứng từ & Tài liệu đính kèm" (`tab_file_link`, loại `quotation`), nên bản in luôn tick
    "Không" kể cả khi phiếu có báo giá thật. Đếm lại theo cả ba nguồn:
      1. cột cũ `quote_file_url` — phiếu đời đầu, giữ để không mất dữ liệu;
      2. file loại "Báo giá" trong khối đính kèm — đường đi hiện tại;
      3. entity cũ `purchase_request_quote` — khối tải báo giá riêng, loại chứng từ để rỗng.
    """
    from sqlalchemy import and_ as sa_and, or_ as sa_or

    from app.modules.attachment.model import FileLink

    if (pr.quote_file_url or "").strip():
        return True
    q = (db.query(FileLink.id)
         .filter(FileLink.entity_id == pr.id,
                 sa_or(sa_and(FileLink.entity == "purchase_request", FileLink.doc_type == "quotation"),
                       FileLink.entity == "purchase_request_quote")))
    return db.query(q.exists()).scalar() is True


def linked_survey_requests(db: Session, pr) -> list[dict]:
    """bao-CR-318 (mở rộng bao-CR-422) — MỌI YÊU CẦU BÁO GIÁ (YCBG) đã sinh ra phiếu này.

    Đơn mua hàng có `pr_code` trỏ ngược về YCMH, nhưng chiều YCMH -> YCBG thì chỉ nằm trong
    câu chữ ở ô Nội dung, bấm không ra. Liên kết thật vốn đã có sẵn trong CSDL:
      - `tab_survey_request_pr`: mỗi lần chốt phương án tạo YCMH ghi 1 dòng (nguồn chuẩn);
      - `tab_survey_request_line.pr_id`: đường cũ, dùng cho phiếu tạo trước khi có bảng trên.

    Bản đầu (bao-CR-318) chỉ lấy MỘT phiếu bằng `limit(1)`, và điều đó giấu bớt sự thật: một
    YCMH gom được nhiều dòng đã chốt phương án, mà các dòng ấy có thể nằm ở những YCBG khác
    nhau. Người xem thấy đúng một mã liền tưởng phiếu chỉ có một nguồn. Nay trả cả danh sách,
    xếp theo thứ tự liên kết được ghi (nguồn đầu tiên đứng đầu).

    Không tra ra thì trả danh sách rỗng — phiếu lập tay là chuyện bình thường, không phải lỗi.
    """
    from app.modules.survey_request.model import (SurveyRequest, SurveyRequestLine,
                                                  SurveyRequestPr)

    # Gom id theo ĐÚNG thứ tự gặp và khử trùng: một YCBG có nhiều dòng cùng đổ vào một YCMH
    # thì vẫn chỉ là một nguồn, bày hai lần là người đọc tưởng có hai phiếu.
    sr_ids: list[int] = []
    for (sr_id,) in (db.query(SurveyRequestPr.survey_request_id)
                     .filter(SurveyRequestPr.pr_id == pr.id)
                     .order_by(SurveyRequestPr.id.asc()).all()):
        if sr_id and sr_id not in sr_ids:
            sr_ids.append(int(sr_id))
    if not sr_ids:
        for (sr_id,) in (db.query(SurveyRequestLine.survey_request_id)
                         .filter(SurveyRequestLine.pr_id == pr.id)
                         .order_by(SurveyRequestLine.id.asc()).all()):
            if sr_id and sr_id not in sr_ids:
                sr_ids.append(int(sr_id))
    if not sr_ids:
        return []

    rows = (db.query(SurveyRequest.id, SurveyRequest.code, SurveyRequest.status,
                     SurveyRequest.request_date, SurveyRequest.requester)
            .filter(SurveyRequest.id.in_(sr_ids),
                    SurveyRequest.is_deleted == False).all())   # noqa: E712 — ai-CR-170: YCBG xóa mềm = không có
    by_id = {int(r[0]): r for r in rows}
    out: list[dict] = []
    for sid in sr_ids:
        r = by_id.get(sid)
        # Phiếu nguồn đã bị xóa thì bỏ qua: liên kết còn nhưng không có gì để bấm vào.
        if not r or not r[1]:
            continue
        out.append({"id": sid, "code": r[1], "status": r[2] or "",
                    "request_date": r[3] or "", "requester": r[4] or ""})
    return out


def company_of(db: Session, company_id: int):
    """Pháp nhân của phiếu — tra tên in lên phiếu (người xem không cần quyền đọc danh mục)."""
    from app.modules.company.model import Company
    return db.query(Company).filter(Company.id == company_id).first()


def product_thumbnails(db: Session, codes: set) -> tuple[dict[str, int], dict[int, str]]:
    """Ảnh gốc theo `product_code` cho cả phiếu — tối đa 2 truy vấn, tránh N+1.

    Trả `(id sản phẩm theo mã, url ảnh theo id sản phẩm)`; mỗi sản phẩm lấy ảnh có
    `sort_order` nhỏ nhất.
    """
    from app.modules.attachment.model import FileLink, StoredFile
    from app.modules.product.model import Product
    prod_by_code: dict[str, int] = {}
    if codes:
        for pid_, code_ in db.query(Product.id, Product.code).filter(Product.code.in_(codes)):
            prod_by_code.setdefault(code_, pid_)   # code catalog duy nhất
    thumb_by_pid: dict[int, str] = {}
    if prod_by_code:
        q = (db.query(FileLink.entity_id, StoredFile.url)
             .join(StoredFile, StoredFile.id == FileLink.file_id)
             .filter(FileLink.entity == "product", FileLink.entity_id.in_(prod_by_code.values()))
             .order_by(FileLink.entity_id, FileLink.sort_order.asc(), FileLink.id.desc()))
        for eid, url in q:
            thumb_by_pid.setdefault(eid, url)      # ảnh sort_order nhỏ nhất mỗi SP
    return prod_by_code, thumb_by_pid


def employee_names_by_code(db: Session, codes: set) -> dict[str, str]:
    """`{mã nhân sự: họ tên}` — tên NSTM phụ trách trả sẵn theo dòng (bao-CR-601)."""
    if not codes:
        return {}
    from app.modules.employee.model import Employee
    return dict(db.query(Employee.code, Employee.full_name)
                .filter(Employee.code.in_(codes)).all())
