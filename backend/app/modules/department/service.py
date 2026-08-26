from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .model import Department, DepartmentCompany
from .schema import (DepartmentCompanyInput, DepartmentCreate,
                     DepartmentUpdate)


FILTERABLE = ["code", "name", "issue_code", "kind", "company_id", "is_active"]


def dept_id_by_name(db: Session, name: str, company_id: int = 0) -> int:
    """Id phòng ban theo TÊN — CR-086. Chỉ dùng cho đường vào cũ (FE chỉ gửi tên) và điền lùi.

    Tên trùng ở nhiều phòng thì ưu tiên phòng cùng pháp nhân; vẫn nhập nhằng thì trả 0. Đoán
    bừa một cái là sai âm thầm, mà cái sai đó nằm ở phân quyền — thà để 0 rồi rơi về so tên.
    """
    name = (name or "").strip()
    if not name:
        return 0
    rows = db.query(Department.id, Department.company_id).filter(Department.name == name).all()
    if len(rows) == 1:
        return int(rows[0][0])
    same = [int(r[0]) for r in rows if company_id and r[1] == company_id]
    return same[0] if len(same) == 1 else 0


def sync_department_ref(db: Session, obj) -> None:
    """Đồng bộ cặp (`department_id`, `department`) trên một phiếu — CR-086.

    `department_id` là nguồn sự thật: có id thì chép lại tên hiện hành làm BẢN CHỤP. Chỉ có
    tên (FE cũ gửi lên) thì tra ngược ra id; tra không ra thì để 0 và GIỮ nguyên tên đã nhập
    — phiếu đó vẫn khớp phạm vi theo đường lùi trong `core/scoping.py`.
    """
    did = int(getattr(obj, "department_id", 0) or 0)
    if did:
        dep = db.get(Department, did)
        if dep:
            obj.department = dep.name
            return
        obj.department_id = 0    # id trỏ vào phòng đã xóa → coi như chưa neo
    obj.department_id = dept_id_by_name(db, getattr(obj, "department", "") or "",
                                        int(getattr(obj, "company_id", 0) or 0))


def list_departments(db: Session, q: str | None, pg: dict, is_active: bool | None = None,
                     sort_by: str = "", sort_dir: str = "asc", request=None, scope_cond=None,
                     kind: int | None = None, company_id: int | None = None):
    """`scope_cond` — điều kiện phạm vi do controller dựng sẵn (B-07), `None` = thấy tất.

    Nhận điều kiện đã dựng thay vì tự gọi `apply_scope` để tầng service không phải biết
    tới user/profile; phần đếm `total` nằm SAU chỗ lọc nên số trang khớp với số dòng.

    `kind` / `company_id` là hai ô CHỌN trên thanh công cụ. Endpoint này KHÔNG chạy qua
    `apply_filters` (nó tự đọc `q` để tìm chung tên phòng HOẶC tên trưởng bộ phận), nên
    param trần phải khai tay ở đây — thả vào `FILTERABLE` không thôi thì nó rơi vào khoảng
    không y như `department_id` của màn Nhân sự.
    """
    from app.core.base_controller import apply_sort
    from app.core.filter_operators import apply_operator_filters
    query = db.query(Department)
    if scope_cond is not None:
        query = query.filter(scope_cond)
    # Bộ lọc điều kiện (`name__contains=...`) — ô "Tìm kiếm" chung `q` bên dưới vẫn giữ nguyên
    if request is not None:
        query = apply_operator_filters(query, Department, request, FILTERABLE)
    if q:
        # Tìm chung 1 ô: theo tên phòng ban HOẶC tên trưởng bộ phận (manager)
        from app.modules.employee.model import Employee
        query = query.outerjoin(Employee, Employee.id == Department.manager_id).filter(
            or_(Department.name.like(f"%{q}%"), Employee.full_name.like(f"%{q}%"))
        )
    if is_active is not None:
        query = query.filter(Department.is_active == is_active)
    if kind:
        query = query.filter(Department.kind == kind)
    if company_id:
        #  "Hiện diện ở pháp nhân này" = pháp nhân GỐC hoặc có mặt trong bảng ánh xạ A06.
        #  Chỉ lọc theo `Department.company_id` là hụt: một phòng dùng chung ở nhiều pháp
        #  nhân chỉ hiện ra ở đúng pháp nhân gốc, còn 12 pháp nhân kia coi như không có
        #  phòng đó. Cùng cách gộp hai nguồn với `phong_ban_cua_cac_phap_nhan`.
        present_at = (db.query(DepartmentCompany.department_id)
                      .filter(DepartmentCompany.company_id == company_id,
                              DepartmentCompany.is_active.is_(True)))
        query = query.filter(or_(Department.company_id == company_id,
                                 Department.id.in_(present_at)))
    total = query.count()
    query = apply_sort(query, Department, sort_by, sort_dir, default=Department.id.desc())
    items = query.offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def phong_ban_cua_cac_phap_nhan(db: Session, company_ids: list[int]) -> list[dict]:
    """Các CẶP (phòng ban × pháp nhân) trong những pháp nhân được hỏi.

    Trả về **cặp** chứ không phải danh sách phòng ban, vì một phòng có thể hiện
    diện ở nhiều pháp nhân (`tab_department_company`, A06). Ô chọn "phòng ban"
    của khối phạm vi áp dụng phải khai đúng cặp — khai trơ trọi *"phòng Kế toán"*
    là văn bản lan sang cả 13 công ty (xem `document/scope_service.py`).

    Gộp HAI nguồn vì dữ liệu chưa đồng nhất: bảng ánh xạ A06 là nguồn đầy đủ,
    còn `Department.company_id` là pháp nhân gốc của phòng và vẫn là thứ mã Thu
    mua cũ đọc. Phòng nào chưa được nạp vào bảng ánh xạ mà chỉ lấy theo bảng đó
    thì biến mất khỏi ô chọn.
    """
    from app.modules.company.model import Company

    ids = [int(row) for row in company_ids if row]
    if not ids:
        return []

    ten_cong_ty = {
        row.id: row.name
        for row in db.query(Company).filter(Company.id.in_(ids)).all()
    }

    #  Khóa là CẶP, nên hai nguồn trùng nhau tự gộp làm một.
    cap: dict[tuple[int, int], dict] = {}

    def _them(department: Department, company_id: int) -> None:
        if company_id not in ten_cong_ty:
            return
        cap[(department.id, company_id)] = {
            "department_id": department.id,
            "department_name": department.name,
            "department_code": department.code,
            "company_id": company_id,
            "company_name": ten_cong_ty[company_id],
        }

    for department, mapping in (
        db.query(Department, DepartmentCompany)
        .join(DepartmentCompany, DepartmentCompany.department_id == Department.id)
        .filter(DepartmentCompany.company_id.in_(ids),
                DepartmentCompany.is_active.is_(True),
                Department.is_active.is_(True))
        .all()
    ):
        _them(department, mapping.company_id)

    for department in (
        db.query(Department)
        .filter(Department.company_id.in_(ids), Department.is_active.is_(True))
        .all()
    ):
        _them(department, department.company_id)

    return sorted(cap.values(), key=lambda row: (row["company_name"], row["department_name"]))


def get_department(db: Session, did: int) -> Department:
    obj = db.get(Department, did)
    if not obj:
        raise HTTPException(404, "Không tìm thấy phòng ban")
    return obj


def create_department(db: Session, data: DepartmentCreate, user_id: int) -> Department:
    if not data.code:
        from app.core.utils import generate_code
        data.code = generate_code(db, Department, "PBA")
    elif db.query(Department).filter(Department.code == data.code).first():
        raise HTTPException(400, "Mã phòng ban đã tồn tại")

    _validate_primary_assignment(db, data.company_id, data.manager_id)

    obj = Department(**data.model_dump(), created_by=user_id, updated_by=user_id)
    db.add(obj)
    db.flush()
    _sync_primary_company_link(db, obj, user_id)
    db.commit()
    db.refresh(obj)
    return obj


def update_department(db: Session, did: int, data: DepartmentUpdate, user_id: int) -> Department:
    obj = get_department(db, did)
    values = data.model_dump(exclude_unset=True)

    if "issue_code" in values:
        from app.modules.doc_catalog.issue_code_guard import ensure_department_issue_code_free
        ensure_department_issue_code_free(db, obj.id, obj.issue_code, values["issue_code"])
    if "kind" in values:
        from app.modules.doc_catalog.issue_code_guard import ensure_department_kind_free
        ensure_department_kind_free(db, obj.id, obj.kind, values["kind"])

    if {"company_id", "manager_id"} & values.keys():
        _validate_primary_assignment(
            db,
            values.get("company_id", obj.company_id),
            values.get("manager_id", obj.manager_id),
        )

    for key, value in values.items():
        setattr(obj, key, value)
    obj.updated_by = user_id
    if {"company_id", "manager_id"} & values.keys():
        _sync_primary_company_link(db, obj, user_id)
    db.commit()
    db.refresh(obj)
    return obj


def delete_department(db: Session, did: int, user_id: int) -> None:
    obj = get_department(db, did)
    db.delete(obj)
    db.commit()


def _sync_primary_company_link(db: Session, department: Department, user_id: int) -> None:
    """Giữ dòng pháp nhân gốc trong A06 khớp hai cột legacy của phòng ban."""
    if not department.company_id:
        return
    link = (
        db.query(DepartmentCompany)
        .filter(DepartmentCompany.department_id == department.id,
                DepartmentCompany.company_id == department.company_id)
        .one_or_none()
    )
    manager_id = department.manager_id or None
    if link is None:
        db.add(DepartmentCompany(
            department_id=department.id,
            company_id=department.company_id,
            manager_employee_id=manager_id,
            issue_code_override="",
            is_active=True,
            created_by=user_id,
            updated_by=user_id,
        ))
        return
    link.manager_employee_id = manager_id
    link.is_active = True
    link.updated_by = user_id


def _validate_primary_assignment(db: Session, company_id: int, manager_id: int) -> None:
    """Chặn pháp nhân ảo và trưởng phòng thuộc nhầm pháp nhân ở hai cột legacy."""
    from app.modules.company.model import Company
    from app.modules.employee.model import Employee

    if company_id and db.get(Company, company_id) is None:
        raise HTTPException(400, "Pháp nhân gốc không tồn tại")
    if not manager_id:
        return
    manager = db.get(Employee, manager_id)
    if manager is None:
        raise HTTPException(400, "Nhân sự trưởng bộ phận không tồn tại")
    if company_id and manager.company_id not in (0, company_id):
        raise HTTPException(400, "Trưởng bộ phận không thuộc pháp nhân gốc")


def list_department_companies(db: Session, did: int) -> list[DepartmentCompany]:
    get_department(db, did)
    return (
        db.query(DepartmentCompany)
        .filter(DepartmentCompany.department_id == did)
        .order_by(DepartmentCompany.is_active.desc(), DepartmentCompany.company_id.asc())
        .all()
    )


def replace_department_companies(
    db: Session,
    did: int,
    items: list[DepartmentCompanyInput],
    user_id: int,
) -> list[DepartmentCompany]:
    """Thay danh sách pháp nhân của phòng trong một transaction.

    Không xóa vật lý dòng bị bỏ khỏi payload: chuyển `is_active=False` để lịch sử
    tổ chức và các luồng duyệt cũ vẫn giải thích được.
    """
    from app.modules.company.model import Company
    from app.modules.doc_catalog.issue_code_guard import (
        ensure_department_company_issue_code_free,
    )
    from app.modules.employee.model import Employee

    department = get_department(db, did)
    company_ids = [item.company_id for item in items]
    if len(company_ids) != len(set(company_ids)):
        raise HTTPException(400, "Một pháp nhân chỉ được khai một lần cho mỗi phòng ban")
    if department.company_id and department.company_id not in company_ids:
        raise HTTPException(400, "Danh sách phải chứa pháp nhân gốc của phòng ban")

    companies = {
        row.id: row for row in db.query(Company).filter(Company.id.in_(company_ids)).all()
    } if company_ids else {}
    missing = sorted(set(company_ids) - set(companies))
    if missing:
        raise HTTPException(400, f"Pháp nhân không tồn tại: {', '.join(map(str, missing))}")

    manager_ids = {item.manager_employee_id for item in items if item.manager_employee_id}
    managers = {
        row.id: row for row in db.query(Employee).filter(Employee.id.in_(manager_ids)).all()
    } if manager_ids else {}
    missing_managers = sorted(manager_ids - set(managers))
    if missing_managers:
        raise HTTPException(400, f"Nhân sự không tồn tại: {', '.join(map(str, missing_managers))}")

    existing = {
        row.company_id: row for row in
        db.query(DepartmentCompany).filter(DepartmentCompany.department_id == did).all()
    }
    submitted = set(company_ids)
    for company_id, row in existing.items():
        if company_id not in submitted:
            row.is_active = False
            row.updated_by = user_id

    for item in items:
        manager = managers.get(item.manager_employee_id) if item.manager_employee_id else None
        if manager and manager.company_id not in (0, item.company_id):
            raise HTTPException(
                400,
                f"{manager.full_name} không thuộc pháp nhân {companies[item.company_id].name}",
            )
        row = existing.get(item.company_id)
        values = item.model_dump()
        ensure_department_company_issue_code_free(
            db,
            did,
            item.company_id,
            row.issue_code_override if row else "",
            item.issue_code_override,
        )
        if row is None:
            row = DepartmentCompany(
                department_id=did,
                **values,
                created_by=user_id,
                updated_by=user_id,
            )
            db.add(row)
            existing[item.company_id] = row
        else:
            for key, value in values.items():
                setattr(row, key, value)
            row.updated_by = user_id

        # Hai cột cũ tiếp tục phản ánh đúng trưởng phòng tại pháp nhân gốc.
        if item.company_id == department.company_id:
            department.manager_id = item.manager_employee_id or 0
            department.updated_by = user_id

    db.commit()
    return list_department_companies(db, did)
