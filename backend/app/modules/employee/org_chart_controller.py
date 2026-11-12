"""Sơ đồ tổ chức (HR2-5 / V2-6, duoc-CR-669) — `GET /api/org-chart`.

KHÔNG lưu bản vẽ: mỗi lần mở là đọc thẳng `tab_employee` / `tab_department` /
`tab_company`, nên đổi phòng hay đổi quản lý xong sơ đồ tự đúng.

Trả DỮ LIỆU PHẲNG (pháp nhân · phòng ban có `parent` · nhân sự có `manager_id` · kiêm nhiệm);
giao diện dựng cây. Phẳng thì số truy vấn CỐ ĐỊNH (không phụ thuộc số người hay số dòng kiêm nhiệm — có bài canh),
và vòng `manager_id` / `parent` không thể làm treo phía backend.

PHẠM VI NGƯỜI XEM (không lộ người ngoài phạm vi):
  - nhân sự: `apply_scope(Employee, "employee")` — thấy ai thì vẽ người đó;
  - trưởng phòng / quản lý trực tiếp là người NGOÀI phạm vi → trả `0` (ẩn danh),
    không để tên hay id lọt ra qua con trỏ;
  - phòng ban: phòng nằm trong phạm vi `department` HOẶC có người xem được ở đó,
    kèm chuỗi phòng cha để cây liền mạch (chỉ lộ TÊN phòng, không lộ người);
  - nhân sự đã `resigned` hoặc ngưng hoạt động không vẽ;
  - NGƯỜI KIÊM NHIỆM (duoc-CR-755): khóa `concurrents` = dòng kiêm nhiệm đang hiệu lực mà phạm vi `employee.read`
    của người xem phủ cặp (phòng, công ty) của dòng — vẽ ở phòng kiêm nhiệm, nhãn Kiêm nhiệm. Truy vấn gốc
    `employees` KHÔNG đổi (không bật `include_concurrent`): người đó không thành thêm một nhân sự ở công ty
    khác, quân số không đếm trùng; phòng của dòng được thêm vào tập phòng cần vẽ.
Chỉ lấy cột công việc (mã, họ tên, chức vụ, phòng, quản lý) — không đụng nhóm
nhạy cảm của `employee.sensitive`.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core import app_settings
from app.core.auth import get_perm_profile, require
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, exclude_deleted, scope_condition
from app.modules.company.model import Company
from app.modules.department.model import Department

from . import concurrent_members_service
from .model import Employee

router = APIRouter(prefix="/api/org-chart", tags=["employee"])

#  Mã trạng thái nghỉ việc (`core/status_codes.EMPLOYEE_STATUS`).
_RESIGNED = "resigned"


def _visible_ancestors(wanted: set[int], parent_of: dict[int, int]) -> set[int]:
    """Thêm chuỗi phòng cha của các phòng cần vẽ. Có `seen` nên vòng `parent` không treo."""
    result = set(wanted)
    for dept_id in wanted:
        seen = {dept_id}
        cursor = parent_of.get(dept_id, 0)
        while cursor and cursor in parent_of and cursor not in seen:
            seen.add(cursor)
            result.add(cursor)
            cursor = parent_of.get(cursor, 0)
    return result


@router.get("")
def get_org_chart(db: Session = Depends(get_db), user=Depends(require("employee", "read"))):
    prof = get_perm_profile(db, user)
    #  duoc-CR-713: Cài đặt nhân sự "Sơ đồ tổ chức cho mọi nhân viên" TẮT → chỉ người xem được TOÀN BỘ hồ sơ (không giới
    #  hạn công ty / phòng / người — cùng tiêu chí `scope_condition(...) is None` của biến mẫu HĐLĐ) mới mở được.
    if not app_settings.get("org_chart_visible_to_all") and \
            scope_condition(Employee, "employee", user, prof) is not None:
        raise HTTPException(403, "Sơ đồ tổ chức đang chỉ mở cho người xem được toàn bộ hồ sơ nhân sự "
                                 "(Cài đặt nhân sự). Liên hệ phòng Nhân sự nếu bạn cần xem.")

    # 1) Nhân sự trong phạm vi.
    emp_rows = (
        apply_scope(
            db.query(Employee.id, Employee.code, Employee.full_name, Employee.position,
                     Employee.company_id, Employee.department_id, Employee.manager_id),
            Employee, "employee", user, prof,
        )
        .filter(Employee.is_active.is_(True), Employee.status != _RESIGNED)
        .order_by(Employee.full_name, Employee.id)
        .all()
    )
    visible_emp = {r.id for r in emp_rows}

    # 2) Phòng ban nằm trong phạm vi `department`.
    scoped_dept_ids = {
        r.id for r in apply_scope(
            db.query(Department.id).filter(Department.is_active.is_(True)),
            Department, "department", user, prof,
        ).all()
    }

    # 3) Toàn bộ phòng chưa xóa — lọc tiếp trong bộ nhớ (một truy vấn, không đệ quy SQL).
    all_depts = exclude_deleted(db.query(Department), Department).all()
    dept_by_id = {d.id: d for d in all_depts}
    parent_of = {d.id: (d.parent or 0) for d in all_depts}
    #  duoc-CR-755: người kiêm nhiệm hiện ở PHÒNG KIÊM NHIỆM — một truy vấn, số dòng không làm đổi số truy vấn.
    #  Lấy dư MỘT dòng để biết có bị cắt ở trần hay không (G2): cắt im lặng là người xem tin sơ đồ đã đủ.
    max_rows = concurrent_members_service.ORG_CHART_MAX_ROWS
    concurrents = concurrent_members_service.list_visible_members(
        db, user, prof, effective_only=True, limit=max_rows + 1)
    concurrents_truncated = len(concurrents) > max_rows
    concurrents = concurrents[:max_rows]
    wanted = (scoped_dept_ids | {r.department_id for r in emp_rows if r.department_id in dept_by_id}
              | {c["department_id"] for c in concurrents if c["department_id"] in dept_by_id})
    dept_ids = _visible_ancestors({i for i in wanted if i in dept_by_id}, parent_of)

    departments = [
        {
            "id": d.id, "code": d.code, "name": d.name, "kind": d.kind,
            "company_id": d.company_id or 0,
            "parent": d.parent if d.parent in dept_ids and d.parent != d.id else 0,
            "manager_id": d.manager_id if d.manager_id in visible_emp else 0,
        }
        for d in sorted(all_depts, key=lambda x: (x.name, x.id)) if d.id in dept_ids
    ]

    # 4) Pháp nhân của các nút sẽ vẽ (chỉ mã + tên).
    company_ids = ({r.company_id for r in emp_rows if r.company_id}
                   | {d["company_id"] for d in departments if d["company_id"]}
                   | {c["company_id"] for c in concurrents if c["company_id"]})
    company_rows = (
        exclude_deleted(db.query(Company.id, Company.code, Company.name), Company)
        .filter(Company.id.in_(company_ids))
        .order_by(Company.name, Company.id)
        .all()
    ) if company_ids else []

    employees = [
        {
            "id": r.id, "code": r.code, "full_name": r.full_name, "position": r.position or "",
            "company_id": r.company_id or 0, "department_id": r.department_id or 0,
            #  Quản lý ngoài phạm vi (hoặc tự quản lý chính mình) → 0, không lộ con trỏ.
            "manager_id": r.manager_id if r.manager_id in visible_emp and r.manager_id != r.id else 0,
        }
        for r in emp_rows
    ]
    return success({
        "companies": [{"id": c.id, "code": c.code, "name": c.name} for c in company_rows],
        "departments": departments,
        "employees": employees,
        "concurrents": concurrents,
        "concurrents_truncated": concurrents_truncated,
    })
