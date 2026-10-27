"""Dữ liệu NGƯỜI cho Sổ quản lý lao động và mẫu 01/PLI (duoc-CR-687) — mỗi nhân sự một hàng.

Tập người = nhân sự làm việc ở BẤT KỲ lúc nào trong kỳ: vào làm không sau cuối kỳ và (chưa nghỉ hoặc
ngày nghỉ không trước đầu kỳ). Thiếu `hire_date` thì lấy ngày tạo hồ sơ theo giờ VN (`hire_missing=True`;
`created_at` lưu UTC nên so với cận kỳ giờ VN qua `VN_OFFSET`). Người
đã đổi sang «Đã nghỉ» mà KHÔNG ghi `resign_date` không xác định được lúc nghỉ nên không vào tập.

HĐ áp cho mỗi người = HĐ đã ký (SIGNED / TERMINATED) còn hiệu lực tại `as_of = min(cuối kỳ, hôm nay)`
(luật «đã ký tại as_of» giống báo cáo HĐLĐ), không có thì HĐ bắt đầu gần nhất trước đó.

Số truy vấn CỐ ĐỊNH: nhân sự · HĐ của những người đó. Hàng mang cả trường nhạy cảm (CCCD, BHXH, ngày
sinh, địa chỉ, lương) để xuất Excel; lớp trả JSON (`/summary`, `/rows`) KHÔNG được đưa giá trị đó ra.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import and_, or_

from app.core.export_xlsx import VN_OFFSET
from app.core.labor_contract_codes import LaborContractStatus as S
from app.core.labor_contract_codes import LaborContractType as T
from app.core.report_period import to_local_date
from app.modules.employee.constants import GENDER_FEMALE, job_category_of
from app.modules.employee.model import Employee
from app.modules.employee.service import STATUS_RESIGNED
from app.modules.labor_contract.model import LaborContract

_EMP_COLS = (Employee.id, Employee.code, Employee.full_name, Employee.company_id, Employee.department_id,
             Employee.position, Employee.job_level, Employee.education_level, Employee.gender,
             Employee.date_of_birth, Employee.id_number, Employee.permanent_address, Employee.current_address,
             Employee.social_insurance_no, Employee.hire_date, Employee.created_at, Employee.status,
             Employee.resign_date)
_CON_COLS = (LaborContract.employee_id, LaborContract.contract_type, LaborContract.status,
             LaborContract.start_date, LaborContract.end_date, LaborContract.terminated_date,
             LaborContract.terminate_reason, LaborContract.base_salary, LaborContract.allowance)
#  Nhãn trường bắt buộc của sổ (thiếu một trong các trường này thì người đó bị đánh dấu).
REQUIRED_LABELS = {"dob": "Ngày sinh", "id": "CCCD", "address": "Nơi cư trú",
                   "education": "Trình độ", "hire": "Ngày vào làm", "contract": "Loại HĐ"}


@dataclass(frozen=True)
class PersonRow:
    employee_id: int
    employee_code: str
    employee_name: str
    company_id: int
    department_id: int
    position: str
    job_level: int
    education_level: int
    gender: int
    date_of_birth: date | None
    id_number: str
    address: str
    social_insurance_no: str
    hire_date: date | None
    hire_missing: bool           # đang dùng ngày tạo hồ sơ thay cho ngày vào làm
    resign_date: date | None
    working_at_end: bool
    left_in_period: bool
    contract_type: int           # 0 = chưa có HĐ
    contract_start: date | None
    contract_end: date | None
    contract_terminated: date | None
    terminate_reason: str
    base_salary: int
    allowance: int
    salary_history: tuple[tuple[date, int], ...]   # (ngày bắt đầu HĐ, lương) theo thứ tự thời gian

    @property
    def job_category(self) -> int:
        return job_category_of(self.job_level, self.education_level)

    @property
    def is_female(self) -> bool:
        return self.gender == GENDER_FEMALE

    @property
    def missing(self) -> tuple[str, ...]:
        """Nhãn các trường bắt buộc còn thiếu (chỉ nhãn, không có giá trị)."""
        gaps = [("dob", not self.date_of_birth), ("id", not (self.id_number or "").strip()),
                ("address", not (self.address or "").strip()), ("education", not self.education_level),
                ("hire", self.hire_missing), ("contract", not self.contract_type)]
        return tuple(REQUIRED_LABELS[k] for k, empty in gaps if empty)


def _pick_contract(items: list, as_of: date):
    """HĐ đã ký còn hiệu lực tại `as_of`, không có thì HĐ bắt đầu gần nhất trước đó (`items` đã xếp theo ngày bắt đầu)."""
    def in_force(c) -> bool:
        signed = c.status == int(S.SIGNED) or (
            c.status == int(S.TERMINATED) and c.terminated_date is not None and c.terminated_date > as_of)
        return signed and (c.end_date is None or c.end_date >= as_of)
    forced = [c for c in items if in_force(c)]
    return (forced or items or [None])[-1]


def _salary_history(items: list) -> tuple[tuple[date, int], ...]:
    """Mức lương các HĐ liên tiếp, bỏ mức lặp liền kề."""
    out: list[tuple[date, int]] = []
    for c in items:
        if not out or out[-1][1] != (c.base_salary or 0):
            out.append((c.start_date, c.base_salary or 0))
    return tuple(out)


def load_people(employees_q, contracts_q, d_from: date, d_to: date, today: date,
                company_id: int | None = None, department_id: int | None = None) -> list[PersonRow]:
    """`employees_q` / `contracts_q` PHẢI đã qua `apply_scope`; hai bộ lọc chỉ THU HẸP thêm."""
    as_of = min(d_to, today)
    #  `created_at` là UTC: 00:00 VN ngày kế cuối kỳ = (ngày đó 00:00) − 7h theo UTC.
    cutoff_utc = datetime.combine(d_to + timedelta(days=1), time.min) - VN_OFFSET
    q = employees_q.filter(
        or_(and_(Employee.hire_date.isnot(None), Employee.hire_date <= d_to),
            and_(Employee.hire_date.is_(None), Employee.created_at < cutoff_utc)),
        or_(Employee.status != STATUS_RESIGNED, Employee.resign_date >= d_from))
    if company_id is not None:
        q = q.filter(Employee.company_id == company_id)
    if department_id is not None:
        q = q.filter(Employee.department_id == department_id)
    emps = q.with_entities(*_EMP_COLS).all()
    by_emp: dict[int, list] = {}
    if emps:
        for c in (contracts_q.filter(
                LaborContract.employee_id.in_([e.id for e in emps]),
                LaborContract.status.in_((int(S.SIGNED), int(S.TERMINATED))),
                LaborContract.start_date <= as_of)
                .with_entities(*_CON_COLS).order_by(LaborContract.start_date, LaborContract.id).all()):
            by_emp.setdefault(c.employee_id, []).append(c)

    out: list[PersonRow] = []
    for e in emps:
        resigned = (e.status or "") == STATUS_RESIGNED
        items = by_emp.get(e.id, [])
        c = _pick_contract(items, as_of)
        left = resigned and e.resign_date is not None and e.resign_date <= as_of
        out.append(PersonRow(
            employee_id=e.id, employee_code=e.code or "", employee_name=e.full_name or "",
            company_id=e.company_id or 0, department_id=e.department_id or 0, position=e.position or "",
            job_level=e.job_level or 0, education_level=e.education_level or 0, gender=e.gender or 0,
            date_of_birth=e.date_of_birth, id_number=e.id_number or "",
            address=e.permanent_address or e.current_address or "",
            social_insurance_no=e.social_insurance_no or "",
            hire_date=e.hire_date or to_local_date(e.created_at),
            hire_missing=e.hire_date is None, resign_date=e.resign_date if resigned else None,
            working_at_end=not left,
            left_in_period=left and e.resign_date >= d_from,   # người nghỉ SAU `as_of` vẫn «đang làm»
            contract_type=int(c.contract_type) if c else 0, contract_start=c.start_date if c else None,
            contract_end=c.end_date if c else None,
            contract_terminated=c.terminated_date if c and c.status == int(S.TERMINATED) else None,
            terminate_reason=(c.terminate_reason or "") if c and c.status == int(S.TERMINATED) else "",
            base_salary=(c.base_salary or 0) if c else 0, allowance=(c.allowance or 0) if c else 0,
            salary_history=_salary_history(items)))
    return out


def is_civil_contract(r: PersonRow) -> bool:
    """Khoán việc / cộng tác viên là hợp đồng dân sự, không phải HĐLĐ nên không vào mẫu 01/PLI."""
    return r.contract_type in (int(T.SERVICE), int(T.COLLABORATOR))


def hire_fallback_note(people: list[PersonRow]) -> str:
    """Câu cảnh báo số người đang lấy ngày tạo hồ sơ thay ngày vào làm; rỗng khi không có ai."""
    n = sum(1 for p in people if p.hire_missing)
    return (f"Có {n} người chưa ghi ngày vào làm — báo cáo tạm lấy ngày tạo hồ sơ (giờ VN) làm ngày vào làm, "
            "Nhân sự cần bổ sung." if n else "")
