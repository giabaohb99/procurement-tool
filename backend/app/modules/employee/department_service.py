"""KIÊM NHIỆM PHÒNG BAN — đọc, ghi, và ba chốt chặn chống vượt quyền (CR-167).

⚠️ **Gán phòng ban KHÔNG phải thao tác hành chính vô hại.** Phạm vi dữ liệu bậc
*phòng ban* đọc thẳng từ bảng này (`core/auth.get_perm_profile` →
`core/scoping`), nên thêm một phòng cho ai đó là **mở rộng tầm nhìn dữ liệu của
họ** — đúng bằng việc tick thêm một ô trong ma trận quyền, chỉ là qua một cửa
trông hiền lành hơn.

Ba chốt, cùng một tinh thần với `core/privilege_escalation.py` (CR-158):

**L1 — KHÔNG TỰ SỬA PHÒNG BAN CỦA CHÍNH MÌNH.** Vai trò `employee.write` phạm vi
*own* là có thật (người dùng tự sửa hồ sơ mình), nên không có chốt này thì tự
thêm phòng cho mình là xong — không cần đụng tới màn Phân quyền.

**L2 — CHỈ GÁN ĐƯỢC PHÒNG MÌNH NHÌN THẤY.** Người quản lý phạm vi *phòng ban*
không được đẩy người khác sang một phòng mà chính họ không với tới; làm được thì
họ dựng ra một người có tầm nhìn rộng hơn mình rồi nhờ người đó xem hộ.

**L3 — PHÒNG PHẢI CÓ THẬT và CÙNG PHÁP NHÂN với nhân sự.** `tab_employee` và
`tab_department` không có khóa ngoại, nên id rác ghi vào được và nằm im; còn gán
sang phòng của pháp nhân khác là mở dữ liệu xuyên pháp nhân bằng một dòng.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.department.model import Department

from .department_model import EmployeeDepartment
from .model import Employee


def extra_departments_of(db: Session, employee_id: int) -> list[int]:
    """Phòng KIÊM NHIỆM — các phòng NGOÀI phòng chính.

    Phòng chính không nằm trong danh sách này: nó là ô «Phòng ban» của hồ sơ,
    một thứ khác hẳn. Gộp hai cái vào một danh sách rồi quy ước «phần tử đầu là
    phòng chính» là dựng ra một luật ngầm mà người dùng không có cách nào biết.
    """
    from .model import Employee

    emp = db.get(Employee, employee_id)
    primary = emp.department_id if emp else 0
    return [x for x in departments_of(db, employee_id) if x != primary]


def set_extra_departments(db: Session, employee: Employee, extra_ids: list[int],
                   actor: int) -> list[int]:
    """Đặt lại danh sách phòng KIÊM NHIỆM. Phòng chính giữ nguyên.

    Phòng chính đổi ở ô «Phòng ban» của hồ sơ, không đổi qua đây — hai thao tác
    khác nhau thì hai cửa khác nhau.
    """
    primary = employee.department_id or 0
    cleaned = [x for x in dict.fromkeys(int(v) for v in extra_ids if v) if x != primary]
    set_departments(db, employee, ([primary] if primary else []) + cleaned, actor,
                  primary_department=primary or None)
    return cleaned


def departments_of(db: Session, employee_id: int) -> list[int]:
    """Mọi phòng ban của một nhân sự, PHÒNG CHÍNH đứng đầu.

    Thứ tự có nghĩa: nơi gọi nào chỉ lấy được một phòng (dựng bối cảnh phiếu,
    chọn trưởng phòng để báo) thì lấy phần tử đầu là đúng phòng chính.
    """
    if not employee_id:
        return []
    rows = (db.query(EmployeeDepartment)
            .filter(EmployeeDepartment.employee_id == employee_id)
            .order_by(EmployeeDepartment.is_primary.desc(),
                      EmployeeDepartment.department_id.asc())
            .all())
    return [row.department_id for row in rows if row.department_id]


def departments_of_many(db: Session, employee_ids: list[int]) -> dict[int, list[int]]:
    """Bản gọi MỘT LƯỢT cho danh sách — tránh N+1 ở màn danh sách nhân sự."""
    if not employee_ids:
        return {}
    rows = (db.query(EmployeeDepartment)
            .filter(EmployeeDepartment.employee_id.in_(set(employee_ids)))
            .order_by(EmployeeDepartment.is_primary.desc(),
                      EmployeeDepartment.department_id.asc())
            .all())
    result: dict[int, list[int]] = {}
    for row in rows:
        result.setdefault(row.employee_id, []).append(row.department_id)
    return result


def employees_of_department(db: Session, department_id: int) -> list[int]:
    """Ai có chân ở phòng này — KỂ CẢ người chỉ kiêm nhiệm.

    Dùng cho gửi thông báo và đếm quân số. Truy vấn cũ lọc
    `Employee.department_id == X` nên bỏ sót đúng những người kiêm nhiệm.
    """
    if not department_id:
        return []
    return [row[0] for row in
            db.query(EmployeeDepartment.employee_id)
            .filter(EmployeeDepartment.department_id == department_id).all()]


# ── Ghi ─────────────────────────────────────────────────────────────────────

def _check_departments_exist(db: Session, employee: Employee,
                        department_ids: list[int]) -> list[Department]:
    """L3 — phòng có thật, đang bật, và cùng pháp nhân với nhân sự."""
    if not department_ids:
        return []
    department = db.query(Department).filter(Department.id.in_(set(department_ids))).all()
    by_id = {row.id: row for row in department}

    missing = sorted(set(department_ids) - set(by_id))
    if missing:
        raise HTTPException(400, f"Phòng ban không tồn tại: {missing}")

    #  Pháp nhân: chỉ chặn khi CẢ HAI bên đều khai. Dữ liệu cũ có phòng chưa gắn
    #  pháp nhân, chặn cứng là không sửa nổi hồ sơ nào.
    if employee.company_id:
        wrong_company_names = [row.name for row in department
                   if row.company_id and row.company_id != employee.company_id]
        if wrong_company_names:
            raise HTTPException(
                400, f"Phòng ban thuộc pháp nhân khác: {', '.join(wrong_company_names)}. "
                     "Gán chéo pháp nhân là mở dữ liệu xuyên pháp nhân.")
    return department


def block_edit_own_department(db: Session, employee_id: int, actor) -> None:
    """L1 — xem đầu tệp. Gọi ở MỌI cửa ghi vào bảng này.

    So theo `user.employee_id` chứ không theo `user.id`: cùng một con người,
    hai định danh khác nhau ở hai bảng.
    """
    mine = getattr(actor, "employee_id", None)
    if mine and mine == employee_id:
        raise HTTPException(
            403, "Không tự đổi phòng ban của chính mình được — phòng ban quyết định "
                 "phạm vi dữ liệu bạn nhìn thấy. Nhờ một quản trị khác thao tác.")


#  Bậc phạm vi từ hẹp tới rộng — dùng để lấy bậc RỘNG NHẤT trong các vai trò.
_SCOPE_RANK = {"own": 0, "assigned": 1, "proc": 2, "dept": 3, "company": 4, "all": 5}


def _widest_scope(profile: dict, entity: str, action: str) -> str | None:
    """Bậc phạm vi rộng nhất mà người này có trên `(entity, action)`.

    `None` = không vai trò nào cấp hành động đó. Lấy bậc RỘNG NHẤT vì
    `scope_condition` cũng HỢP các grant lại — hẹp hơn ở đây là chặn nhầm người
    thật sự có quyền.
    """
    widest = None
    for grant in profile.get("grants", []):
        perms = grant["perms"].get(entity)
        if not perms or not perms.get(action):
            continue
        scope_name = perms.get("scope", "all")
        if widest is None or _SCOPE_RANK.get(scope_name, 5) > _SCOPE_RANK.get(widest, 5):
            widest = scope_name
    return widest


def assignable_departments(db: Session, profile: dict) -> set[int] | None:
    """Những phòng người này được phép GÁN cho người khác. `None` = không giới hạn.

    ⚠️ Đo bằng phạm vi trên entity **`employee`** (thứ đang bị ghi), KHÔNG phải
    trên `department`. Hai cái khác nghĩa hẳn: `SCOPE_FIELDS["department"]` nói
    về quyền quản lý DANH MỤC phòng ban (ai được sửa tên phòng, ai được xóa) và
    nó không có chiều phòng ban, nên bậc `dept` ở đó rơi về "chỉ phòng do chính
    tôi tạo" — dùng làm thước thì người quản lý nhân sự phòng Kế toán không gán
    nổi chính phòng Kế toán.
    """
    widest = _widest_scope(profile, "employee", "write")
    if widest is None:
        return set()
    if widest == "all":
        return None
    if widest == "company":
        company_id = profile.get("company_id") or 0
        if not company_id:
            return set()
        return {row[0] for row in
                db.query(Department.id)
                .filter(Department.company_id == company_id).all()}

    #  Bậc `dept` (và hẹp hơn): đúng những phòng CHÍNH NGƯỜI ĐÓ có chân, cộng
    #  các phòng được cấp thêm đích danh ở màn Phân quyền (`tab_user_scope`).
    allowed_ids = {x for x in (profile.get("dept_ids") or []) if x}
    if profile.get("dept_id"):
        allowed_ids.add(profile["dept_id"])
    for grant in profile.get("grants", []):
        extra_grants = (grant.get("scope") or {}).get("inc", {}).get("department") or []
        allowed_ids.update(x for x in extra_grants if x)
    return allowed_ids


def block_out_of_scope_departments(db: Session, department_ids: list[int], actor,
                             profile: dict) -> None:
    """L2 — chỉ gán được phòng nằm trong tầm của chính người thao tác.

    Không có chốt này thì người quản lý phạm vi *phòng ban* dựng ra được một
    người có tầm nhìn rộng hơn mình, rồi nhờ người đó xem hộ.
    """
    if not department_ids:
        return

    allowed_ids = assignable_departments(db, profile)
    if allowed_ids is None:
        return   # phạm vi *tất cả* — không siết

    out_of_scope = sorted(set(department_ids) - allowed_ids)
    if out_of_scope:
        scope_name = {row[0]: row[1] for row in
               db.query(Department.id, Department.name)
               .filter(Department.id.in_(out_of_scope)).all()}
        label = ", ".join(f"«{scope_name.get(i, i)}»" for i in out_of_scope)
        raise HTTPException(
            403, f"Không gán được phòng ban mà chính bạn không có phạm vi trên đó: {label}. "
                 "Nhờ người phụ trách phòng đó thao tác.")


def set_departments(db: Session, employee: Employee, department_ids: list[int],
                  actor: int, *, primary_department: int | None = None) -> list[int]:
    """Đặt LẠI toàn bộ danh sách phòng ban của một nhân sự.

    Đây là chỗ DUY NHẤT ghi vào `tab_employee_department`, và cũng là chỗ duy
    nhất cập nhật `tab_employee.department_id` — hai thứ đó phải luôn khớp nhau,
    tách ra hai nơi ghi là sớm muộn lệch.

    `phong_chinh` bỏ trống thì lấy phần tử ĐẦU của danh sách. Danh sách rỗng =
    gỡ khỏi mọi phòng (nhân sự chưa phân công), hợp lệ.

    ⚠️ KHÔNG gọi thẳng từ controller — gọi ba hàm `chan_*` trước.
    """
    cleaned = list(dict.fromkeys(int(x) for x in department_ids if x))
    _check_departments_exist(db, employee, cleaned)

    primary = primary_department if primary_department in cleaned else (cleaned[0] if cleaned else 0)

    db.query(EmployeeDepartment).filter(
        EmployeeDepartment.employee_id == employee.id).delete(synchronize_session=False)
    for department_id in cleaned:
        db.add(EmployeeDepartment(
            employee_id=employee.id, department_id=department_id,
            is_primary=(department_id == primary),
            created_by=actor, updated_by=actor))

    #  Giữ cột cũ khớp với phòng chính — 12 chỗ trong mã vẫn đọc nó.
    employee.department_id = primary
    db.flush()

    #  Phạm vi dữ liệu của người này vừa đổi; hồ sơ quyền cache 60 giây nên
    #  không xóa là họ nhìn bằng tầm cũ suốt một phút.
    from app.core.auth import perm_cache_clear
    from app.modules.user.model import User

    for row in db.query(User.id).filter(User.employee_id == employee.id).all():
        perm_cache_clear(row[0])

    return [primary] + [x for x in cleaned if x != primary] if primary else cleaned
