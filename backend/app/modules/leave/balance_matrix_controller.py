"""Tổng hợp quỹ phép theo người (duoc-CR-717) — `/api/leave-balances/matrix` (+ `/matrix/export`).

Router RIÊNG, đăng ký trong `main.py` TRƯỚC `leave_balance_router` để `/matrix` không bị `/{bid}` nuốt (422).
Gác `leave_balance` read / export + `apply_scope(LeaveBalance)`; không phải báo cáo kiểu Haravan nên không có
khóa báo cáo riêng (cùng quyền xem màn Quỹ phép).
"""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.export_xlsx import Col, xlsx_response
from app.core.response import success
from app.core.vn_time import vn_today
from app.modules.report.procurement_summary_rows import valid_company_id, valid_department_id

from .balance_matrix_service import ENTITY, EXPORT_LIMIT, build_matrix
from .balance_report_spec import valid_employee_status

router = APIRouter(prefix="/api/leave-balances", tags=["leave"])


def _run(request: Request, db: Session, user, action: str, year: int, search: str | None,
         offset: int, limit: int) -> dict:
    qp = request.query_params
    return build_matrix(db, user, get_perm_profile(db, user), action, year or vn_today().year,
                        valid_company_id(qp.get("company_id")), valid_department_id(qp.get("department_id")),
                        valid_employee_status(qp.get("employee_status")), search, offset, limit)


@router.get("/matrix")
def leave_balance_matrix(request: Request, year: int = Query(0, ge=0, le=2100), search: str | None = None,
                         pg: dict = Depends(pagination), db: Session = Depends(get_db),
                         user=Depends(require(ENTITY, "read"))):
    return success(_run(request, db, user, "read", year, search, pg["offset"], pg["limit"]))


@router.get("/matrix/export")
def leave_balance_matrix_export(request: Request, year: int = Query(0, ge=0, le=2100), search: str | None = None,
                                db: Session = Depends(get_db), user=Depends(require(ENTITY, "export"))):
    data = _run(request, db, user, "export", year, search, 0, EXPORT_LIMIT)
    columns = [Col("code", "Mã NV", width=14), Col("name", "Họ tên", width=26),
               Col("department_name", "Phòng ban", width=24), Col("policy_name", "Chính sách", width=26)]
    columns += [Col(f"t{c['leave_type_id']}", c["name"], kind="qty", width=14) for c in data["columns"]]
    columns.append(Col("total", "Tổng còn lại", kind="qty", width=14))
    rows = [{"code": i["code"], "name": i["name"], "department_name": i["department_name"],
             "policy_name": i["policy_name"] or "Theo loại nghỉ", "total": i["total"],
             **{f"t{c['leave_type_id']}": i["cells"].get(str(c["leave_type_id"]), 0) for c in data["columns"]}}
            for i in data["items"]]
    return xlsx_response(f"tong-hop-quy-phep-{data['year']}", columns, rows, sheet_title="Quy phep")
