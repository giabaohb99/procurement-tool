"""Lõi nghiệp vụ YÊU CẦU SỬA HỒ SƠ (duoc-CR-676): dựng phần KHÁC BIỆT, áp vào hồ sơ, báo người gửi.

⚠️ Không hàm nào ở đây xét quyền hay commit — chốt quyền ở controller, commit MỘT lần ở controller
để «áp hồ sơ + đổi trạng thái yêu cầu» là một giao dịch.
"""
from datetime import date, datetime

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.hr_change_request_codes import EmployeeChangeRequestStatus as Status
from app.modules.notification.model import Notification

from . import contact_service, service
from .change_request_model import EmployeeChangeRequest
from .change_request_schema import GROUP_MODELS, ChangeRequestIn, clean_error
from .model import Employee
from .schema import EmployeeFamilyIn, EmployeeUpdate

#  Nhãn nhóm — dùng trong câu nhật ký/thông báo (KHÔNG chứa giá trị).
GROUP_LABELS = {"personal": "thông tin cá nhân", "bank": "ngân hàng", "documents": "giấy tờ",
                "families": "hộ gia đình"}
_DATE_FIELDS = frozenset({"date_of_birth", "id_issue_date", "id_expiry_date"})
_INT_FIELDS = frozenset({"gender", "marital_status", "children_count", "education_level"})
_FAMILY_COLS = ("full_name", "relation", "gender", "date_of_birth", "phone", "id_number")


def _norm(field: str, value):
    """Đưa giá trị về dạng so sánh được: ngày → date|None, số → int, chữ → đã cắt hai đầu."""
    if field in _DATE_FIELDS:
        return value or None
    if field in _INT_FIELDS:
        return int(value or 0)
    return (value or "").strip()


def to_json(value):
    return value.isoformat() if isinstance(value, date) else value


def _family_row(data: dict) -> dict:
    row = {c: data.get(c) for c in _FAMILY_COLS}
    for c in ("full_name", "phone", "id_number"):
        row[c] = (row[c] or "").strip()
    row["relation"] = int(row["relation"] or 0)
    row["gender"] = int(row["gender"] or 0)
    row["date_of_birth"] = to_json(row["date_of_birth"])
    return row


def current_families(db: Session, employee_id: int) -> list[dict]:
    return [_family_row({c: getattr(r, c) for c in _FAMILY_COLS})
            for r in contact_service.list_families(db, employee_id)]


def build_diff(db: Session, emp: Employee, body: ChangeRequestIn) -> tuple[list[dict], dict | None]:
    """Chỉ giữ ô ĐỔI THẬT so với hồ sơ hiện tại; hộ gia đình chỉ giữ khi danh sách khác."""
    items: list[dict] = []
    for group in GROUP_MODELS:
        sub = getattr(body, group)
        if sub is None:
            continue
        for field, raw in sub.model_dump(exclude_unset=True).items():
            after, before = _norm(field, raw), _norm(field, getattr(emp, field))
            if after != before:
                items.append({"group": group, "field": field,
                              "before": to_json(before), "after": to_json(after)})
    families = None
    if body.families is not None:
        #  Bỏ dòng rỗng họ tên — cùng luật `contact_service._replace_rows`.
        after_rows = [r for r in (_family_row(i.model_dump()) for i in body.families) if r["full_name"]]
        before_rows = current_families(db, emp.id)
        if after_rows != before_rows:
            families = {"before": before_rows, "after": after_rows}
    return items, families


def apply_request(db: Session, req: EmployeeChangeRequest, emp: Employee, user_id: int) -> None:
    """Ghi yêu cầu vào hồ sơ qua ĐÚNG các đường của phòng Nhân sự. KHÔNG commit."""
    if req.changes:
        try:
            data = EmployeeUpdate.model_validate({i["field"]: i["after"] for i in req.changes})
        except ValidationError as exc:   # bộ mã đổi sau lúc gửi — nói rõ thay vì 500
            raise HTTPException(400, f"Nội dung yêu cầu không còn hợp lệ: {clean_error(exc)}")
        service.update_employee_core(db, emp, data, user_id)
    if req.families:
        #  ⚠️ Hộ gia đình bị THAY TOÀN BỘ — nếu nhân sự đã sửa danh sách sau lúc gửi thì phần sửa đó sẽ mất im lặng.
        if current_families(db, emp.id) != req.families["before"]:
            raise HTTPException(
                409, "Danh sách hộ gia đình đã bị sửa sau khi gửi đề nghị — từ chối rồi để nhân viên gửi lại")
        rows = [EmployeeFamilyIn.model_validate(r) for r in req.families["after"]]
        contact_service.set_families(db, emp.id, rows, user_id)
        emp.updated_by = user_id


def decide(req: EmployeeChangeRequest, status: Status, user_id: int, reason: str = "") -> None:
    req.status = int(status)
    req.pending_employee_id = None   # nhả chỗ «một yêu cầu chờ duyệt» của nhân sự này
    req.decided_at = datetime.now()
    req.decided_by = user_id
    req.updated_by = user_id
    if reason:
        req.reject_reason = reason.strip()


def notify_requester(db: Session, req: EmployeeChangeRequest, by_user_id: int, title: str, body: str) -> None:
    """Chuông trong ứng dụng cho người đã gửi (tài khoản `created_by`)."""
    if int(req.created_by or 0) > 0:
        db.add(Notification(user_id=req.created_by, title=title[:255], body=body, link="/me",
                            created_by=by_user_id))


def group_summary(req: EmployeeChangeRequest) -> str:
    groups = list(dict.fromkeys(i["group"] for i in req.changes or []))
    if req.families:
        groups.append("families")
    return ", ".join(GROUP_LABELS[g] for g in groups)


def pending_of(db: Session, employee_id: int) -> EmployeeChangeRequest | None:
    return (db.query(EmployeeChangeRequest)
            .filter(EmployeeChangeRequest.employee_id == employee_id,
                    EmployeeChangeRequest.status == int(Status.PENDING)).first())
