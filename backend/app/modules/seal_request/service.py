"""Nghiệp vụ Duyệt dấu (Yêu cầu đóng dấu).

Luồng 2 cổng: người tạo gửi duyệt → Trưởng bộ phận duyệt/trả/từ chối → Văn thư đóng
dấu (Hoàn thành) / trả / từ chối. Gác quyền + phạm vi ở controller; ở đây là máy trạng
thái + kiểm dữ liệu + nối nhãn hiển thị. Khuôn theo `vehicle_booking/service.py`.
"""
import re
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.attachment.model import FileLink
from app.modules.company.model import Company
from app.modules.employee.model import Employee
from app.modules.user.model import User

from .notify import notify

from .model import (
    EDITABLE_STATUSES,
    SEAL_APPROVED,
    SEAL_COMPLETED,
    SEAL_DRAFT,
    SEAL_PENDING,
    SEAL_REJECTED,
    SEAL_RETURNED,
    SEAL_STATUS_LABELS,
    SealRequest,
    SealType,
)
from .schema import (
    CompleteSealIn,
    ReasonIn,
    SealRequestCreate,
    SealRequestResponse,
    SealRequestUpdate,
)

FILTERABLE = ["status", "seal_type_id", "company_id", "department_id", "requester_id"]


def apply_keyword_search(query, keyword: str | None):
    """Tìm nhanh theo mã / mục đích / tên chứng từ."""
    kw = (keyword or "").strip()
    if not kw:
        return query
    like = f"%{kw}%"
    return query.filter(
        SealRequest.code.like(like)
        | SealRequest.purpose.like(like)
        | SealRequest.title.like(like)
    )


def _requester_context(db: Session, user) -> tuple[str, int, int]:
    """(tên hiển thị, phòng ban, công ty) của người tạo từ hồ sơ nhân sự.

    company mặc định = công ty người tạo, nhưng người dùng CÓ THỂ chọn công ty con
    dấu khác ở form (không đè khi client đã gửi company_id).
    """
    emp = db.get(Employee, user.employee_id) if getattr(user, "employee_id", 0) else None
    name = (emp.full_name if emp and emp.full_name else "") or getattr(user, "email", "") or ""
    dept_id = emp.department_id if emp else 0
    company_id = emp.company_id if emp else 0
    return name, dept_id or 0, company_id or 0


def _next_seal_code(db: Session) -> str:
    """Sinh mã DD kế tiếp — chỉ xét mã đúng dạng `DD<số>`, lấy max+1, nhảy nếu đụng.

    Không dùng `count()` hay sắp chuỗi: dữ liệu có mã kèm chữ sẽ làm `int()` vỡ và
    rơi về DD001 trùng khóa (đúng lỗi Đặt xe từng gặp).
    """
    rows = db.query(SealRequest.code).filter(SealRequest.code.like("DD%")).all()
    existing = {code for (code,) in rows if code}
    max_num = 0
    for code in existing:
        m = re.fullmatch(r"DD(\d+)", code)
        if m:
            max_num = max(max_num, int(m.group(1)))
    num = max_num + 1
    while f"DD{num:03d}" in existing:
        num += 1
    return f"DD{num:03d}"


def _now() -> str:
    return datetime.now().isoformat(timespec="minutes")


def _append_note(req: SealRequest, label: str, reason: str) -> None:
    """Ghi thêm một dòng có nhãn vào ô ghi chú (giữ lịch sử trả/từ chối/đóng dấu)."""
    reason = (reason or "").strip()
    if not reason:
        return
    line = f"[{label}] {reason}"
    req.note = f"{req.note}\n{line}".strip() if req.note else line


def count_attachments(db: Session, req_id: int) -> int:
    """Số tệp chứng từ đã đính kèm phiếu (mọi loại).

    NSYC đính kèm chứng từ có CHỮ KÝ SỐNG để Văn thư đối chiếu; cổng gửi duyệt đòi
    ≥1 tệp. Không lọc theo `doc_type` vì bộ đính kèm dùng chung (`DocumentAttachmentsCard`)
    không gắn nhãn `signed_doc` cố định — có tệp là coi như đã có chứng từ.
    """
    return (
        db.query(FileLink)
        .filter(FileLink.entity == "seal_request", FileLink.entity_id == req_id)
        .count()
    )


def _validate_for_submit(db: Session, req: SealRequest) -> None:
    """Điều kiện gửi duyệt (KHÔNG chặn lúc lưu nháp)."""
    if not (req.purpose or "").strip():
        raise HTTPException(400, "Vui lòng nhập mục đích sử dụng")
    if not req.seal_type_id:
        raise HTTPException(400, "Vui lòng chọn loại con dấu")
    if not req.company_id:
        raise HTTPException(400, "Vui lòng chọn công ty cần đóng dấu")
    if count_attachments(db, req.id) < 1:
        raise HTTPException(400, "Cần đính kèm ít nhất 1 chứng từ có chữ ký sống để gửi duyệt")


def create_seal_request(db: Session, data: SealRequestCreate, user, submit: bool,
                        background_tasks=None) -> SealRequest:
    """Tạo phiếu. submit=True → gửi duyệt ngay (kiểm dữ liệu + tệp); ngược lại lưu Nháp.

    ⚠️ Tệp chứng từ được upload RIÊNG qua /api/attachments sau khi có id phiếu; vì vậy
    submit lúc TẠO chỉ pass khi client đã upload trước rồi mới gọi tạo-kèm-submit — trên
    thực tế FE tạo nháp → upload → mới gửi duyệt (endpoint /submit).
    """
    name, dept_id, company_id = _requester_context(db, user)
    req = SealRequest(
        purpose=(data.purpose or "").strip(),
        title=(data.title or "").strip(),
        seal_type_id=data.seal_type_id or 0,
        company_id=data.company_id or company_id,
        department_id=data.department_id or dept_id,
        copies=data.copies or 1,
        first_approver_id=data.first_approver_id or 0,
        note=data.note or "",
        requester=name,
        requester_id=getattr(user, "id", 0),
        status=SEAL_DRAFT,
        created_by=getattr(user, "id", 0),
        updated_by=getattr(user, "id", 0),
    )
    db.add(req)
    db.flush()
    req.code = _next_seal_code(db)
    db.commit()
    db.refresh(req)
    if submit:
        submit_seal_request(db, req, user, background_tasks)
    return req


def update_seal_request(db: Session, req: SealRequest, data: SealRequestUpdate,
                        user, submit: bool, background_tasks=None) -> SealRequest:
    """Sửa — CHỈ khi còn Nháp hoặc bị Yêu cầu chỉnh sửa. Sau khi vào luồng thì khóa."""
    if req.status not in EDITABLE_STATUSES:
        raise HTTPException(400, "Phiếu đã vào luồng duyệt — không sửa được nữa")
    patch = data.model_dump(exclude_unset=True)
    for field, value in patch.items():
        setattr(req, field, value)
    req.updated_by = getattr(user, "id", 0)
    db.commit()
    db.refresh(req)
    if submit:
        submit_seal_request(db, req, user, background_tasks)
    return req


def submit_seal_request(db: Session, req: SealRequest, user, background_tasks=None) -> SealRequest:
    """Gửi duyệt: Nháp / Yêu cầu chỉnh sửa → Chờ duyệt (kiểm dữ liệu + tệp)."""
    if req.status not in EDITABLE_STATUSES:
        raise HTTPException(400, "Chỉ gửi duyệt được phiếu Nháp hoặc bị Yêu cầu chỉnh sửa")
    _validate_for_submit(db, req)
    req.status = SEAL_PENDING
    req.updated_by = getattr(user, "id", 0)
    db.commit()
    db.refresh(req)
    notify(db, "dd_submitted", req, background_tasks, actor=user)  # báo TBP
    return req


# --- Cổng 1: Trưởng bộ phận (quyền approve) --------------------------------

def approve_seal(db: Session, req: SealRequest, user, background_tasks=None) -> SealRequest:
    """TBP DUYỆT: Chờ duyệt → Đã duyệt (chờ Văn thư đóng dấu)."""
    if req.status != SEAL_PENDING:
        raise HTTPException(400, "Chỉ duyệt được phiếu đang Chờ duyệt")
    req.status = SEAL_APPROVED
    req.updated_by = getattr(user, "id", 0)
    db.commit()
    db.refresh(req)
    notify(db, "dd_approved", req, background_tasks, actor=user)  # báo NSYC + Văn thư + Giám đốc
    return req


def return_seal(db: Session, req: SealRequest, data: ReasonIn, user,
                background_tasks=None) -> SealRequest:
    """YÊU CẦU CHỈNH SỬA — từ Chờ duyệt (TBP) hoặc Đã duyệt (Văn thư) → trả người tạo."""
    if req.status not in (SEAL_PENDING, SEAL_APPROVED):
        raise HTTPException(400, "Chỉ yêu cầu chỉnh sửa khi phiếu Chờ duyệt hoặc Đã duyệt")
    req.status = SEAL_RETURNED
    _append_note(req, "Yêu cầu chỉnh sửa", data.reason)
    req.updated_by = getattr(user, "id", 0)
    db.commit()
    db.refresh(req)
    notify(db, "dd_returned", req, background_tasks, actor=user, reason=data.reason)
    return req


def reject_seal(db: Session, req: SealRequest, data: ReasonIn, user,
                background_tasks=None) -> SealRequest:
    """TỪ CHỐI — từ Chờ duyệt (TBP) hoặc Đã duyệt (Văn thư) → khóa."""
    if req.status not in (SEAL_PENDING, SEAL_APPROVED):
        raise HTTPException(400, "Chỉ từ chối khi phiếu Chờ duyệt hoặc Đã duyệt")
    req.status = SEAL_REJECTED
    _append_note(req, "Từ chối", data.reason)
    req.updated_by = getattr(user, "id", 0)
    db.commit()
    db.refresh(req)
    notify(db, "dd_rejected", req, background_tasks, actor=user, reason=data.reason)
    return req


# --- Cổng 2: Văn thư (quyền write, phạm vi company) ------------------------

def complete_seal(db: Session, req: SealRequest, data: CompleteSealIn, user,
                  background_tasks=None) -> SealRequest:
    """Văn thư HOÀN THÀNH: Đã duyệt → Hoàn thành (đã đóng dấu ngoài thực tế)."""
    if req.status != SEAL_APPROVED:
        raise HTTPException(400, "Chỉ hoàn thành được phiếu đã được duyệt")
    if data.copies_done and data.copies_done > 0:
        req.copies = data.copies_done
    req.status = SEAL_COMPLETED
    done_note = f"Đã đóng dấu {req.copies} bản"
    if (data.note or "").strip():
        done_note += f" — {data.note.strip()}"
    _append_note(req, "Đóng dấu", done_note)
    req.updated_by = getattr(user, "id", 0)
    db.commit()
    db.refresh(req)
    notify(db, "dd_completed", req, background_tasks, actor=user)  # báo NSYC
    return req


# --- Serialize -------------------------------------------------------------

def _emp_of_user(db: Session, user_id: int) -> Employee | None:
    if not user_id:
        return None
    u = db.get(User, user_id)
    return db.get(Employee, u.employee_id) if u and u.employee_id else None


def serialize_seal_request(db: Session, req: SealRequest) -> dict:
    """Một phiếu → dict, nối nhãn loại dấu / công ty (+MST) / thông tin người tạo / TBP."""
    out = SealRequestResponse.model_validate(req)
    out.status_label = SEAL_STATUS_LABELS.get(req.status, "")
    out.created_at = req.created_at.isoformat() if req.created_at else None

    if req.seal_type_id:
        st = db.get(SealType, req.seal_type_id)
        out.seal_type_name = st.name if st else ""
    if req.company_id:
        co = db.get(Company, req.company_id)
        if co:
            out.company_name = co.name
            out.company_tax_code = co.tax_code or ""
    emp = _emp_of_user(db, req.requester_id)
    if emp:
        out.requester_email = emp.email or ""
        out.requester_phone = emp.phone or ""
        out.requester_role = emp.position or ""
    approver = _emp_of_user(db, req.first_approver_id)
    if approver:
        out.approver_name = approver.full_name or ""
    out.signed_doc_count = count_attachments(db, req.id)
    return out.model_dump()


def serialize_seal_requests(db: Session, reqs: list[SealRequest]) -> list[dict]:
    """Danh sách phiếu → list dict, nối nhãn theo LÔ (tránh N+1)."""
    type_ids = {r.seal_type_id for r in reqs if r.seal_type_id}
    company_ids = {r.company_id for r in reqs if r.company_id}
    type_map = (
        {t.id: t for t in db.query(SealType).filter(SealType.id.in_(type_ids)).all()}
        if type_ids else {}
    )
    company_map = (
        {c.id: c for c in db.query(Company).filter(Company.id.in_(company_ids)).all()}
        if company_ids else {}
    )
    result = []
    for r in reqs:
        out = SealRequestResponse.model_validate(r)
        out.status_label = SEAL_STATUS_LABELS.get(r.status, "")
        out.created_at = r.created_at.isoformat() if r.created_at else None
        st = type_map.get(r.seal_type_id)
        out.seal_type_name = st.name if st else ""
        co = company_map.get(r.company_id)
        if co:
            out.company_name = co.name
            out.company_tax_code = co.tax_code or ""
        result.append(out.model_dump())
    return result
