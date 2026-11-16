"""NGÀY BẮT ĐẦU TÍCH PHÉP của một người — nguồn DUY NHẤT cho chế độ `MONTHLY_AFTER` (duoc-CR-762).

Luật (người chủ chốt 16/11/2026, Q3 + Q4 + Q5, rồi vòng review):
  · Ngày làm chính thức = `start_date` của HĐLĐ ĐẦU TIÊN đã ký mà KHÔNG phải Thử việc, Dịch vụ, Cộng tác viên. "Đã ký" =
    `SIGNED` (kể cả đã hết hạn — hết hạn là suy ra, DB vẫn ghi `SIGNED`) hoặc `TERMINATED` (đã ký rồi mới chấm dứt, người
    đó vẫn đã làm). `DRAFT`, `CANCELLED` và HĐ xóa mềm không tính.
  · Chỉ có HĐ Thử việc đã ký (còn hạn hay đã hết) và chưa có HĐ chính thức → chưa tích.
  · Chỉ có HĐ Dịch vụ / Cộng tác viên (không có HĐLĐ) → không tích phép năm.
  · Không có Thử việc (và không có HĐ dịch vụ / cộng tác viên) mà HĐ chính thức đầu tiên bắt đầu muộn hơn MỘT THÁNG sau
    `hire_date` → lịch sử HĐ chưa đủ (mới nhập HĐ gần nhất): tính từ `hire_date`, trạng thái riêng.
  · Nhận lại sau khi nghỉ (rehire): HĐ đã kết thúc TRƯỚC `hire_date` hiện tại (trừ một ngày) bị bỏ qua; kết thúc = ngày
    chấm dứt thực tế nếu có, không thì `end_date`; HĐ không có ngày kết thúc luôn được giữ. Không có `hire_date` → giữ hết.
  · Không có HĐ đã ký nào → lấy `hire_date`, TRỪ khi hồ sơ đang để hình thức *Thử việc* (chưa tích).
  · Không có `hire_date` → giữ hành vi cũ của phần còn lại của hệ (tính từ 01/01), gắn cờ thiếu để màn hình nhắc.

Nạp GOM cho nhiều người: một câu hồ sơ (nếu chỉ có id) + một câu HĐLĐ, không phụ thuộc số người.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.labor_contract_codes import LaborContractStatus, LaborContractType
from app.core.vn_time import vn_today
from app.modules.employee.constants import EMPLOYMENT_PROBATION
from app.modules.employee.model import Employee
from app.modules.labor_contract.model import LaborContract

from .constants import LeaveAccrualStatus

#  Mốc "chưa tới ngày làm chính thức": năm 9999 lớn hơn mọi năm cấp quỹ nên `months_in_period` ra 0 tháng
#  (đưa thẳng vào các hàm thuần của `accrual_service` mà không cần nhánh riêng).
NOT_STARTED = date.max

#  Trạng thái HĐLĐ được coi là "đã ký" (xem docstring đầu tệp).
SIGNED_STATUSES = (int(LaborContractStatus.SIGNED), int(LaborContractStatus.TERMINATED))


@dataclass(frozen=True)
class ContractFacts:
    """Những gì HĐLĐ đã ký của một người nói về mốc tích phép."""

    official_start: date | None     # ngày bắt đầu HĐ chính thức sớm nhất (không Thử việc / Dịch vụ / Cộng tác viên)
    has_probation: bool             # có HĐ Thử việc đã ký (kể cả đã hết hạn)
    has_service: bool = False       # có HĐ Dịch vụ / Cộng tác viên đã ký


@dataclass(frozen=True)
class AccrualStart:
    """Kết quả cho một người.

    `start` là ngày làm chính thức (hoặc `hire_date` khi chưa có HĐ / lịch sử HĐ chưa đủ); `None` khi không biết ngày nào.
    `accruing=False` = chưa tích ngày nào (đang thử việc, hoặc chỉ có HĐ dịch vụ / cộng tác viên).
    `missing_contract=True` = chưa có HĐLĐ đã ký nào (mốc suy từ hồ sơ). `incomplete=True` = có HĐ chính thức nhưng
    lịch sử chưa đủ nên mốc là `hire_date`. `service_only=True` = chỉ có HĐ dịch vụ / cộng tác viên.
    """

    start: date | None
    accruing: bool
    missing_contract: bool
    incomplete: bool = False
    service_only: bool = False

    @property
    def math_date(self) -> date | None:
        """Giá trị đưa vào các hàm thuần (`months_in_period`…) thay cho `hire_date`."""
        return self.start if self.accruing else NOT_STARTED

    def status_at(self, today: date | None = None) -> int:
        """`LeaveAccrualStatus` tại `today` (mặc định hôm nay giờ VN). Thứ tự ưu tiên từ trên xuống."""
        today = today or vn_today()
        if self.service_only:
            return int(LeaveAccrualStatus.SERVICE_CONTRACT)
        if not self.accruing:
            return int(LeaveAccrualStatus.PROBATION)
        if self.start is not None and self.start > today:
            return int(LeaveAccrualStatus.NOT_YET_OFFICIAL)
        if self.incomplete:
            return int(LeaveAccrualStatus.INCOMPLETE_HISTORY)
        return int(LeaveAccrualStatus.MISSING_CONTRACT if self.missing_contract else LeaveAccrualStatus.ACCRUING)


def _plus_one_month(day: date) -> date:
    """Cùng ngày của tháng sau (kẹp về ngày cuối tháng nếu tháng sau ngắn hơn)."""
    year, month = (day.year + 1, 1) if day.month == 12 else (day.year, day.month + 1)
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def resolve(hire_date: date | None, employment_type: int | None, facts: ContractFacts | None) -> AccrualStart:
    """Hàm THUẦN: gộp hồ sơ + HĐLĐ thành mốc tích phép — xem docstring đầu tệp."""
    if facts is not None and facts.official_start is not None:
        #  Có HĐ dịch vụ / cộng tác viên thì KHÔNG lùi về ngày vào làm: giai đoạn đó không tích phép năm.
        if (not facts.has_probation and not facts.has_service and hire_date is not None
                and facts.official_start > _plus_one_month(hire_date)):
            return AccrualStart(hire_date, True, False, incomplete=True)
        return AccrualStart(facts.official_start, True, False)
    if facts is not None and facts.has_probation:
        return AccrualStart(None, False, False)
    if facts is not None and facts.has_service:
        return AccrualStart(None, False, False, service_only=True)
    if int(employment_type or 0) == EMPLOYMENT_PROBATION:
        return AccrualStart(None, False, True)
    return AccrualStart(hire_date, True, True)


def contract_facts(db: Session, employee_ids: Iterable[int],
                   hire_dates: dict[int, date | None] | None = None) -> dict[int, ContractFacts]:
    """`{employee_id: ContractFacts}` — MỘT câu truy vấn HĐLĐ cho cả nhóm. Người không có HĐ hợp lệ thì vắng mặt.

    `hire_dates` = `{employee_id: hire_date}` đã nạp sẵn: HĐ kết thúc trước `hire_date − 1 ngày` là của lần làm TRƯỚC
    (nhận lại sau khi nghỉ) và bị bỏ qua. Không truyền thì đọc thêm ngày vào làm từ hồ sơ (một truy vấn nữa). Người
    không có `hire_date` thì giữ mọi HĐ."""
    ids = {int(i) for i in employee_ids}
    if not ids:
        return {}
    if hire_dates is None:
        hire_dates = {i: h for i, h in db.query(Employee.id, Employee.hire_date).filter(Employee.id.in_(ids)).all()}
    probation = int(LaborContractType.PROBATION)
    non_labor = (int(LaborContractType.SERVICE), int(LaborContractType.COLLABORATOR))
    rows = (db.query(LaborContract.employee_id, LaborContract.contract_type, LaborContract.start_date,
                     LaborContract.end_date, LaborContract.terminated_date)
            .filter(LaborContract.employee_id.in_(ids),
                    LaborContract.status.in_(SIGNED_STATUSES),
                    LaborContract.is_deleted.is_(False)).all())
    starts: dict[int, date] = {}
    probation_of: set[int] = set()
    service_of: set[int] = set()
    for eid, ctype, start, end, terminated in rows:
        hire = hire_dates.get(eid)
        ended = terminated or end
        if hire is not None and ended is not None and ended < hire - timedelta(days=1):
            continue
        if ctype == probation:
            probation_of.add(eid)
        elif ctype in non_labor:
            service_of.add(eid)
        elif start is not None and (eid not in starts or start < starts[eid]):
            starts[eid] = start
    return {eid: ContractFacts(starts.get(eid), eid in probation_of, eid in service_of)
            for eid in starts.keys() | probation_of | service_of}


def official_start_map(db: Session, employees: Iterable) -> dict[int, AccrualStart]:
    """Mốc tích phép của nhiều người đã nạp sẵn hồ sơ (cần `id`, `hire_date`, `employment_type`) — MỘT truy vấn."""
    emps = list(employees)
    facts = contract_facts(db, (e.id for e in emps), {e.id: getattr(e, "hire_date", None) for e in emps})
    return {e.id: resolve(getattr(e, "hire_date", None), getattr(e, "employment_type", 0), facts.get(e.id))
            for e in emps}


def official_start_map_by_ids(db: Session, employee_ids: Iterable[int]) -> dict[int, AccrualStart]:
    """Như `official_start_map` nhưng chỉ có id: thêm MỘT câu đọc hồ sơ (tổng hai truy vấn)."""
    ids = {int(i) for i in employee_ids}
    if not ids:
        return {}
    rows = db.query(Employee.id, Employee.hire_date, Employee.employment_type).filter(Employee.id.in_(ids)).all()
    facts = contract_facts(db, ids, {eid: hire for eid, hire, _ in rows})
    return {eid: resolve(hire, etype, facts.get(eid)) for eid, hire, etype in rows}


def official_start(db: Session, employee) -> AccrualStart:
    """Mốc tích phép của MỘT người (một truy vấn HĐLĐ)."""
    return official_start_map(db, [employee])[employee.id]


def official_start_with_inputs(db: Session, employee_id: int, hire_date: date | None,
                               employment_type: int | None) -> AccrualStart:
    """Mốc tích phép của người này NẾU hồ sơ mang `hire_date` / `employment_type` cho trước (HĐLĐ đọc từ DB).

    Dùng để dựng mốc TRƯỚC khi sửa hồ sơ, so với mốc SAU khi sửa — chỉ làm mới quỹ khi mốc đổi thật."""
    return resolve(hire_date, employment_type,
                   contract_facts(db, [employee_id], {employee_id: hire_date}).get(employee_id))
