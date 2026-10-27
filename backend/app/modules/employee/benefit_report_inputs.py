"""Tham số lọc của báo cáo H1 «Phúc lợi & sự kiện» (duoc-CR-688) — kiểm ở biên, sai là 422.

Bỏ người đang nghỉ phép (`include_on_leave=0`) đòi `leave_request.read`. Lọc theo ngày sinh / người thân (`age_min`, `age_max`, `birth_month`, `child_max_age`) đòi quyền
`employee_sensitive.read`: thiếu quyền thì 403 bằng câu tiếng Việt dễ hiểu (không lộ mã quyền).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Mapping

from fastapi import HTTPException

from app.core.labor_contract_codes import LaborContractType as T

from .constants import GENDER_VALUES, JOB_LEVEL_LABELS

MAX_AMOUNT = 1_000_000_000
MAX_AGE = 120
MAX_LABEL = 100
MAX_SENIORITY_ITEMS = 30
DEFAULT_EXCLUDED = (int(T.SERVICE), int(T.COLLABORATOR))
SENSITIVE_MSG = ("Bạn chưa có quyền xem ngày sinh và người thân của nhân sự nên không lọc được theo "
                 "tuổi, tháng sinh hay tuổi con. Hãy bỏ các bộ lọc đó hoặc nhờ quản trị cấp quyền.")
LEAVE_MSG = ("Bỏ người đang nghỉ phép sẽ cho biết ai đang nghỉ có phép nên cần quyền xem đơn nghỉ phép. "
             "Hãy chọn tính cả người đang nghỉ hoặc nhờ quản trị cấp quyền.")


@dataclass(frozen=True)
class Filters:
    gender: int | None = None
    age_min: int | None = None
    age_max: int | None = None
    birth_month: int | None = None
    seniority_years: tuple[int, ...] = ()
    job_level_min: int | None = None
    position_id: int | None = None
    exclude_contract_types: tuple[int, ...] = DEFAULT_EXCLUDED
    include_on_leave: bool = True
    child_max_age: int | None = None
    amount_staff: int = 0
    amount_manager: int = 0
    company_id: int | None = None
    department_id: int | None = None
    occasion_label: str = ""

    @property
    def needs_dob(self) -> bool:
        return any(v is not None for v in (self.age_min, self.age_max, self.birth_month))

    @property
    def needs_sensitive(self) -> bool:
        return self.needs_dob or self.child_max_age is not None


def _int(params: Mapping, name: str, lo: int, hi: int, label: str) -> int | None:
    raw = (params.get(name) or "").strip()
    if not raw:
        return None
    try:
        v = int(raw)
    except ValueError:
        raise HTTPException(422, f"{label} phải là số nguyên")
    if not lo <= v <= hi:
        raise HTTPException(422, f"{label} phải trong khoảng {lo} đến {hi}")
    return v


def _int_list(params: Mapping, name: str, lo: int, hi: int, label: str) -> tuple[int, ...]:
    parts = [p.strip() for p in (params.get(name) or "").split(",") if p.strip()]
    if len(parts) > MAX_SENIORITY_ITEMS:
        raise HTTPException(422, f"{label} tối đa {MAX_SENIORITY_ITEMS} giá trị")
    out = []
    for p in parts:
        sub = {name: p}
        out.append(_int(sub, name, lo, hi, label))
    return tuple(sorted(set(out)))


def parse_filters(params: Mapping, valid_company_id, valid_department_id) -> Filters:
    gender = _int(params, "gender", 0, 99, "Giới tính")
    if gender is not None and gender not in GENDER_VALUES:
        raise HTTPException(422, "Giới tính không hợp lệ")
    age_min = _int(params, "age_min", 0, MAX_AGE, "Tuổi từ")
    age_max = _int(params, "age_max", 0, MAX_AGE, "Tuổi đến")
    if age_min is not None and age_max is not None and age_min > age_max:
        raise HTTPException(422, "Tuổi từ không được lớn hơn tuổi đến")
    job_level_min = _int(params, "job_level_min", 0, max(JOB_LEVEL_LABELS), "Cấp bậc tối thiểu")
    if "exclude_contract_types" in params:
        excl = _int_list(params, "exclude_contract_types", 1, 99, "Loại hợp đồng loại trừ")
        if any(x not in {int(t) for t in T} for x in excl):
            raise HTTPException(422, "Loại hợp đồng loại trừ không hợp lệ")
    else:
        excl = DEFAULT_EXCLUDED
    label = (params.get("occasion_label") or "").strip()
    if len(label) > MAX_LABEL:
        raise HTTPException(422, f"Tên dịp tối đa {MAX_LABEL} ký tự")
    on_leave = (params.get("include_on_leave") or "1").strip()
    if on_leave not in ("0", "1"):
        raise HTTPException(422, "include_on_leave chỉ nhận 0 hoặc 1")
    return Filters(
        gender=gender, age_min=age_min, age_max=age_max,
        birth_month=_int(params, "birth_month", 1, 12, "Tháng sinh"),
        seniority_years=_int_list(params, "seniority_years", 1, MAX_AGE, "Thâm niên"),
        job_level_min=job_level_min, position_id=_int(params, "position_id", 1, 2**62, "Chức vụ"),
        exclude_contract_types=excl, include_on_leave=on_leave == "1",
        child_max_age=_int(params, "child_max_age", 0, MAX_AGE, "Tuổi con tối đa"),
        amount_staff=_int(params, "amount_staff", 0, MAX_AMOUNT, "Mức quà nhân viên") or 0,
        amount_manager=_int(params, "amount_manager", 0, MAX_AMOUNT, "Mức quà quản lý") or 0,
        company_id=valid_company_id(params.get("company_id")),
        department_id=valid_department_id(params.get("department_id")),
        occasion_label=label)


def age_on(dob: date, day: date) -> int:
    return day.year - dob.year - ((day.month, day.day) < (dob.month, dob.day))
