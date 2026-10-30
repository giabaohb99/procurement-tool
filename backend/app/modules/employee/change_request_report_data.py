"""Dữ liệu hàng cho báo cáo E2 "Yêu cầu sửa hồ sơ" (khóa 27, duoc-CR-689).

Mỗi yêu cầu (`tab_employee_change_request`) là MỘT hàng. Hàng chỉ giữ TÊN các trường bị xin sửa
(`fields`) — giá trị cũ / mới (có thể là CCCD, số tài khoản) bị bỏ ngay lúc nạp, không bao giờ ra khỏi
tệp này. Phạm vi: bên gọi truyền `employees_q` đã qua `apply_scope(Employee, 'employee', ..., action)`;
yêu cầu của hồ sơ ngoài phạm vi không bao giờ tới đây.

Số truy vấn CỐ ĐỊNH: 1 (yêu cầu join hồ sơ).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.core.export_xlsx import VN_OFFSET
from app.core.hr_change_request_codes import EmployeeChangeRequestStatus as Status
from app.core.report_period import range_filter

from .change_request_model import EmployeeChangeRequest as Req
from .model import Employee

#  Nhãn trường xin sửa — đúng tập ô mà `change_request_schema` cho phép + nhóm hộ gia đình.
FIELD_LABELS = {
    "gender": "Giới tính", "date_of_birth": "Ngày sinh", "place_of_birth": "Nơi sinh",
    "ethnicity": "Dân tộc", "religion": "Tôn giáo", "marital_status": "Tình trạng hôn nhân",
    "children_count": "Số con", "personal_email": "Email cá nhân", "education_level": "Trình độ học vấn",
    "major": "Chuyên ngành", "bank_account_no": "Số tài khoản", "bank_account_name": "Tên chủ tài khoản",
    "bank_name": "Ngân hàng", "bank_branch": "Chi nhánh ngân hàng", "id_number": "Số CCCD",
    "id_issue_date": "Ngày cấp CCCD", "id_issue_place": "Nơi cấp CCCD", "id_expiry_date": "Ngày hết hạn CCCD",
    "tax_code": "Mã số thuế", "social_insurance_no": "Số BHXH", "health_care_place": "Nơi khám chữa bệnh",
    "health_care_code": "Mã khám chữa bệnh", "families": "Hộ gia đình",
}
STATUS_LABELS = {int(Status.PENDING): "Chờ duyệt", int(Status.APPROVED): "Đã duyệt",
                 int(Status.REJECTED): "Từ chối", int(Status.WITHDRAWN): "Đã rút lại"}
#  Quá ngần này ngày chưa xử lý thì tính là "chờ quá hạn".
OVERDUE_DAYS = 2


@dataclass(frozen=True)
class ChangeRow:
    request_id: int
    employee_id: int
    employee_code: str
    employee_name: str
    company_id: int
    department_id: int
    status: int
    created_date: date | None          # ngày gửi, giờ VN
    decided_date: date | None
    decided_by: int
    created_by: int                    # chỉ để `change_request_view.user_names` dùng chung
    fields: tuple[str, ...]            # CHỈ tên trường, không giá trị
    hours: float | None                # giờ xử lý (chỉ có khi đã duyệt / từ chối)
    pending_over: bool                 # đang chờ quá OVERDUE_DAYS ngày tính tới hôm nay


def _local(dt: datetime | None) -> datetime | None:
    return dt + VN_OFFSET if dt else None


def load_rows(db: Session, employees_q, d_from: date, d_to: date, today: date, *,
              company_id: int | None = None, department_id: int | None = None) -> list[ChangeRow]:
    """Yêu cầu GỬI trong `[d_from, d_to]` (giờ VN) của hồ sơ trong phạm vi."""
    q = employees_q.join(Req, Req.employee_id == Employee.id).filter(
        range_filter(Req.created_at, "datetime_utc", d_from, d_to))
    if company_id is not None:
        q = q.filter(Employee.company_id == company_id)
    if department_id is not None:
        q = q.filter(Employee.department_id == department_id)
    q = q.with_entities(Req.id, Req.employee_id, Req.status, Req.changes, Req.families, Req.created_at,
                        Req.decided_at, Req.decided_by, Req.created_by, Employee.code, Employee.full_name,
                        Employee.company_id, Employee.department_id)
    out: list[ChangeRow] = []
    for r in q.all():
        fields = list(dict.fromkeys(i.get("field") for i in (r.changes or []) if i.get("field")))
        if r.families:
            fields.append("families")
        created, decided = _local(r.created_at), _local(r.decided_at)
        done = int(r.status) in (int(Status.APPROVED), int(Status.REJECTED))
        hours = (max(0.0, (r.decided_at - r.created_at).total_seconds() / 3600.0)
                 if done and r.decided_at and r.created_at else None)
        pending = int(r.status) == int(Status.PENDING)
        out.append(ChangeRow(
            request_id=r.id, employee_id=r.employee_id, employee_code=r.code or "",
            employee_name=r.full_name or "", company_id=r.company_id or 0,
            department_id=r.department_id or 0, status=int(r.status),
            created_date=created.date() if created else None,
            decided_date=decided.date() if decided and done else None,
            decided_by=int(r.decided_by or 0) if done else 0, created_by=0,
            fields=tuple(fields), hours=hours,
            pending_over=bool(pending and created and (today - created.date()).days > OVERDUE_DAYS)))
    return out
