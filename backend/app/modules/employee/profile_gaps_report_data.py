"""Dữ liệu hàng cho báo cáo "Hồ sơ & tài khoản còn thiếu" (duoc-CR-686, khóa 18).

Mỗi nhân sự trong phạm vi là một hàng mang các CỜ "thiếu gì" đã tính sẵn. Báo cáo chỉ đếm cờ.
Tình trạng HIỆN TẠI: không có trục thời gian.

Quyền của NGƯỜI XEM quyết định cờ nào được tính:
  - nhóm nhạy cảm (ngày sinh · CCCD · MST · BHXH · ngân hàng): chỉ khi có `employee_sensitive.read`;
    thiếu quyền thì KHÔNG nạp các cột đó khỏi DB, nên không thể lộ — kể cả qua số đếm;
  - nhóm tài khoản (`tab_user`, `tab_user_role`): chỉ khi có `user.read`.
Chỉ ĐẾM, không bao giờ trả giá trị của trường nhạy cảm (duy nhất `id_expiry_date` ở danh sách
của `id_expiring_90`, và cũng chỉ khi có quyền nhạy cảm).

Số truy vấn CỐ ĐỊNH: nhân sự · (tài khoản · vai trò, khi có `user.read`).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import and_, exists, or_
from sqlalchemy.orm import Session

from app.modules.user.model import User, UserRole

from .model import Employee
from .service import STATUS_RESIGNED

BASE_GAPS = ("missing_hire_date", "missing_position", "missing_manager", "missing_department")
SENSITIVE_GAPS = ("missing_dob", "missing_id_number", "missing_tax_code", "missing_social_insurance",
                  "missing_bank", "id_expiring_90")
ACCOUNT_GAPS = ("no_account", "account_no_role", "resigned_active_account")
#  Cờ "thiếu trường" — dùng cho `complete` (đủ hết mọi trường đang được đếm).
_FIELD_GAPS = BASE_GAPS + SENSITIVE_GAPS[:-1]

_BASE_COLS = (Employee.id, Employee.code, Employee.full_name, Employee.company_id, Employee.department_id,
              Employee.position, Employee.position_id, Employee.hire_date, Employee.manager_id,
              Employee.status, Employee.is_active)
_SENSITIVE_COLS = (Employee.date_of_birth, Employee.id_number, Employee.tax_code,
                   Employee.social_insurance_no, Employee.bank_account_no, Employee.id_expiry_date)


def load_group_names(db: Session, group_by: str | None, always: bool = False) -> tuple[dict, dict]:
    """(tên công ty, tên phòng ban) — chỉ tra khi chiều đó được chọn "Xem theo" (hoặc `always`, cho
    danh sách `/rows`). Dùng chung cho báo cáo HĐLĐ và báo cáo hồ sơ thiếu."""
    from app.modules.company.model import Company
    from app.modules.department.model import Department
    company = ({c.id: c.name for c in db.query(Company.id, Company.name).all()}
               if always or group_by == "company" else {})
    department = ({d.id: d.name for d in db.query(Department.id, Department.name).all()}
                  if always or group_by == "department" else {})
    return company, department


@dataclass(frozen=True)
class GapRow:
    employee_id: int
    employee_code: str
    employee_name: str
    company_id: int
    department_id: int
    position: str
    hire_date: date | None
    id_expiry_date: date | None     # CHỈ có giá trị khi người xem có quyền nhạy cảm
    flags: frozenset[str]


def load_rows(db: Session, employees_q, today: date, *, with_sensitive: bool, with_account: bool,
              company_id: int | None = None, department_id: int | None = None) -> list[GapRow]:
    """`employees_q` PHẢI đã qua `apply_scope(Employee, 'employee')`; hai bộ lọc chỉ thu hẹp thêm."""
    q = employees_q
    if company_id is not None:
        q = q.filter(Employee.company_id == company_id)
    if department_id is not None:
        q = q.filter(Employee.department_id == department_id)
    working_cond = and_(Employee.status != STATUS_RESIGNED, Employee.is_active == True)  # noqa: E712
    if with_account:
        #  Người đã nghỉ chỉ cần cho cờ "tài khoản còn mở" -> chỉ nạp người đã nghỉ CÓ tài khoản đang mở.
        has_open_account = exists().where(User.employee_id == Employee.id, User.is_active == True)  # noqa: E712
        q = q.filter(or_(working_cond, and_(Employee.status == STATUS_RESIGNED, has_open_account)))
    else:
        q = q.filter(working_cond)
    cols = _BASE_COLS + (_SENSITIVE_COLS if with_sensitive else ())
    employees = q.with_entities(*cols).all()

    active_users: dict[int, int] = {}          # employee_id -> user_id của tài khoản đang mở
    with_role: set[int] = set()
    if with_account:
        for uid, eid in db.query(User.id, User.employee_id).filter(
                User.is_active == True, User.employee_id > 0):  # noqa: E712
            active_users.setdefault(eid, uid)
        with_role = {uid for (uid,) in db.query(UserRole.user_id).distinct()}

    soon = today + timedelta(days=90)
    out: list[GapRow] = []
    for e in employees:
        resigned = (e.status or "") == STATUS_RESIGNED
        working = bool(e.is_active) and not resigned
        flags: set[str] = set()
        if working:
            flags.add("active_total")
            if not e.hire_date:
                flags.add("missing_hire_date")
            if not e.position_id:
                flags.add("missing_position")
            if not e.manager_id:
                flags.add("missing_manager")
            if not e.department_id:
                flags.add("missing_department")
            if with_sensitive:
                for flag, empty in (("missing_dob", not e.date_of_birth),
                                    ("missing_id_number", not (e.id_number or "").strip()),
                                    ("missing_tax_code", not (e.tax_code or "").strip()),
                                    ("missing_social_insurance", not (e.social_insurance_no or "").strip()),
                                    ("missing_bank", not (e.bank_account_no or "").strip())):
                    if empty:
                        flags.add(flag)
                if e.id_expiry_date and e.id_expiry_date <= soon:    # kể cả đã hết hạn
                    flags.add("id_expiring_90")
            if not flags & set(_FIELD_GAPS):
                flags.add("complete")
            if with_account:
                uid = active_users.get(e.id)
                if uid is None:
                    flags.add("no_account")
                elif uid not in with_role:
                    flags.add("account_no_role")
        elif resigned and with_account and e.id in active_users:
            flags.add("resigned_active_account")
        if flags:
            out.append(GapRow(
                employee_id=e.id, employee_code=e.code or "", employee_name=e.full_name or "",
                company_id=e.company_id or 0, department_id=e.department_id or 0,
                position=e.position or "", hire_date=e.hire_date,
                id_expiry_date=e.id_expiry_date if with_sensitive else None, flags=frozenset(flags)))
    return out
