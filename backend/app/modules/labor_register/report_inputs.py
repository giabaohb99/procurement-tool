"""Đầu vào chung của hai báo cáo lao động (duoc-CR-687): kỳ, bộ lọc, hai truy vấn đã qua phạm vi và cổng quyền.

Ngoài `require(employee, read|export)` + `require_report(key)` gắn ở route, báo cáo còn ĐÒI
`employee_sensitive.read` và `labor_contract.read` — sổ và mẫu chứa CCCD, mã BHXH, ngày sinh, địa chỉ, lương.
Thiếu quyền nào thì 403 nói rõ thiếu quyền nào, ở cả ba đường (`/summary`, `/summary/export`, `/summary/rows`).
"""
from __future__ import annotations

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile
from app.core.report_period import parse_period
from app.core.scoping import apply_scope
from app.modules.employee.model import Employee
from app.modules.leave.request_model import LeaveRequest
from app.modules.labor_contract.model import LaborContract
from app.modules.report.procurement_summary_rows import valid_company_id, valid_department_id

_REQUIRED = (("employee_sensitive", "xem thông tin nhạy cảm của nhân sự"),
             ("labor_contract", "xem hợp đồng lao động"))
_ASK_ADMIN = " — nhờ quản trị cấp ở Phân quyền."


def ensure_hr_permissions(prof: dict, export: bool = False) -> None:
    """Xuất tệp đòi thêm `labor_contract.export` (tệp mang lương hàng loạt, quyền xuất tách khỏi quyền xem)."""
    perms = prof.get("perms_union") or {}
    for entity, what in _REQUIRED:
        if not (perms.get(entity) or {}).get("read"):
            raise HTTPException(403, f"Bạn cần quyền {what} để mở báo cáo này{_ASK_ADMIN}")
    if export and not (perms.get("labor_contract") or {}).get("export"):
        raise HTTPException(403, f"Bạn cần quyền xuất hợp đồng lao động để xuất tệp báo cáo này{_ASK_ADMIN}")


def build_inputs(request: Request, db: Session, user, export: bool = False, with_leave: bool = False) -> dict:
    """Tham số cho `report_service` / hai hàm xuất tệp: truy vấn qua `apply_scope` + kỳ + bộ lọc thu hẹp.

    `export=True` (đường `/summary/export`): phạm vi lấy theo hành động `export` chứ không phải `read` — người
    được xem cả công ty nhưng chỉ được xuất phần của mình thì tệp chỉ có phần của mình. Đơn nghỉ phép luôn theo
    `leave_request.read` (chỉ dựng khi `with_leave`); thiếu quyền đó thì trả `leave_q=None` (tệp để trống cột nghỉ kèm ghi chú)."""
    prof = get_perm_profile(db, user)
    ensure_hr_permissions(prof, export)
    qp = request.query_params
    action = "export" if export else "read"
    out = dict(
        employees_q=apply_scope(db.query(Employee), Employee, "employee", user, prof, action),
        contracts_q=apply_scope(db.query(LaborContract), LaborContract, "labor_contract", user, prof, action),
        period=parse_period(qp), company_id=valid_company_id(qp.get("company_id")),
        department_id=valid_department_id(qp.get("department_id")))
    if with_leave:
        can_leave = (prof.get("perms_union") or {}).get("leave_request", {}).get("read")
        out["leave_q"] = apply_scope(db.query(LeaveRequest), LeaveRequest, "leave_request", user, prof) \
            if can_leave else None
    return out
