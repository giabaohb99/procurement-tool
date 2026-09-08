from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.core.audit import record
from app.core.utils import generate_code

from app.modules.department.model import Department

from .model import Employee
from .schema import EmployeeCreate, EmployeeUpdate

# "status" trước đây thiếu trong whitelist nên ô lọc Trạng thái trên UI không ăn — bổ sung vào
# đây để cả lọc cơ bản lẫn lọc điều kiện đều chạy.
# B-03: cột này nay lưu MÃ (`official`…), nên ô lọc phải GỬI MÃ chứ không gửi nhãn tiếng Việt.
# Gửi nhãn thì câu lọc vẫn chạy, chỉ là ra 0 dòng — đúng cái bẫy CR-118 đã dính một lần.
FILTERABLE = ["code", "full_name", "email", "is_active", "position", "role_names", "department_id",
              "status"]
ENTITY = "employee"

# Ô tìm nhanh MỘT chỗ: một từ khoá quét đồng thời (OR) trên mã NV / họ tên / email /
# điện thoại. Khác apply_filters (mỗi tham số lọc riêng một cột rồi ghép AND) — ở đây
# nhập "0912" hay "an@" hay "NV001" đều ra, khỏi cần biết dữ liệu nằm ở cột nào.
SEARCH_FIELDS = ("code", "full_name", "email", "phone")


def apply_keyword_search(query, keyword: str | None):
    """Thêm điều kiện tìm gần đúng trên nhiều cột (OR). Từ khoá rỗng thì giữ nguyên."""
    kw = (keyword or "").strip()
    if not kw:
        return query
    like = f"%{kw}%"
    return query.filter(or_(*[getattr(Employee, f).like(like) for f in SEARCH_FIELDS]))


# ── CR-087: neo nhân sự trên chứng từ bằng ID ────────────────────────────────────
def emp_id_by_name(db: Session, name: str, company_id: int = 0) -> int:
    """Tra id nhân sự từ TÊN. Không suy ra chắc chắn được thì trả 0 — KHÔNG đoán bừa.

    `full_name` KHÔNG duy nhất (prod đang có cặp trùng tên, dev 4 cặp) nên trùng tên thì
    thử phân giải bằng pháp nhân; vẫn còn nhiều hơn một thì chịu, để 0 và giữ chuỗi tên.
    """
    name = (name or "").strip()
    if not name:
        return 0
    rows = db.query(Employee.id, Employee.company_id).filter(Employee.full_name == name).all()
    if len(rows) == 1:
        return int(rows[0][0])
    same = [int(r[0]) for r in rows if company_id and r[1] == company_id]
    return same[0] if len(same) == 1 else 0


def emp_id_by_code(db: Session, code: str) -> int:
    """Tra id từ MÃ nhân sự. `code` là UNIQUE nên không có chuyện nhập nhằng."""
    code = (code or "").strip()
    if not code:
        return 0
    row = db.query(Employee.id).filter(Employee.code == code).first()
    return int(row[0]) if row else 0


def sync_employee_ref(db: Session, obj, id_field: str, name_field: str) -> None:
    """Ghi kép id ↔ tên cho MỘT ô nhân sự trên chứng từ (vd. `nspt_id`/`nspt`).

    Có id thì TÊN chạy theo id (đổi tên nhân sự là phiếu in ra tên mới). Chỉ có tên thì suy
    ngược ra id. Không suy ra được thì giữ tên, `id = 0` — phần lùi nằm ở `scoping._emp_match`.
    """
    eid = int(getattr(obj, id_field, 0) or 0)
    if eid:
        emp = db.get(Employee, eid)
        if emp:
            setattr(obj, name_field, emp.full_name or "")
            return
        setattr(obj, id_field, 0)
    setattr(obj, id_field, emp_id_by_name(db, getattr(obj, name_field, "") or "",
                                          int(getattr(obj, "company_id", 0) or 0)))


def list_employees(db: Session, base_query, pg: dict):
    total = base_query.count()
    # selectinload(user): danh sách có cột ảnh đại diện (lưu ở tab_user.avatar) — nạp gộp
    # 1 truy vấn cho cả trang, không để mỗi dòng tự lazy-load thành N+1.
    # selectinload(company): cột Công ty (`EmployeeOut.company_name`) đọc qua
    # quan hệ, thiếu dòng này là mỗi dòng một truy vấn.
    #
    # ⚠️ `department` (+ `department.manager`) nạp gộp luôn: `EmployeeOut` đã trả
    # `department_name` và `manager_name` từ lâu, và cả hai đều đọc qua quan hệ —
    # tức danh sách nhân sự **vốn đã N+1 từ trước**, chỉ là không ai đo. Bài kiểm
    # `test_nhan_su_hien_cong_ty.py` đếm truy vấn nên nó lộ ra ngay lúc thêm cột
    # Công ty. `manager_name` đi qua HAI cấp (`Employee.department.manager`) nên
    # phải nối chuỗi loader, không thể chỉ nạp mỗi `department`.
    items = (
        base_query.options(
            selectinload(Employee.user),
            selectinload(Employee.company),
            selectinload(Employee.department).selectinload(Department.manager),
        )
        .order_by(Employee.id.desc())
        .offset(pg["offset"])
        .limit(pg["limit"])
        .all()
    )
    return total, items


def get_employee(db: Session, eid: int) -> Employee:
    obj = db.get(Employee, eid)
    if not obj:
        raise HTTPException(404, "Không tìm thấy nhân viên")
    return obj


def create_employee(db: Session, data: EmployeeCreate, user_id: int) -> Employee:
    if not data.code:
        data.code = generate_code(db, Employee, "NSU")
    elif db.query(Employee).filter(Employee.code == data.code).first():
        raise HTTPException(400, "Mã nhân viên đã tồn tại")
    obj = Employee(**data.model_dump(), created_by=user_id, updated_by=user_id)
    db.add(obj)
    db.flush()
    _sync_primary_department(db, obj, user_id)
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "create")
    return obj


def _sync_primary_department(db: Session, obj: Employee, user_id: int) -> None:
    """Giữ `tab_employee_department` khớp với `tab_employee.department_id`.

    ⚠️ KIÊM NHIỆM (CR-167) có HAI nguồn ghi phòng ban: cửa riêng
    `PUT /employees/{id}/departments`, và cột `department_id` mà màn hồ sơ, CSV
    import và seed vẫn ghi thẳng. Không nối hai nguồn thì chúng trôi khỏi nhau —
    hồ sơ hiện một phòng, phạm vi dữ liệu chạy theo phòng khác, mà không chỗ nào
    báo.

    Ở đây chỉ đụng tới PHÒNG CHÍNH: đổi `department_id` là đổi dòng `is_primary`,
    các phòng kiêm nhiệm khác giữ nguyên. Đổi cả danh sách thì dùng cửa riêng —
    nó có ba chốt chống vượt quyền, cột này thì không.
    """
    from .department_service import set_departments, departments_of

    existing = departments_of(db, obj.id)
    new = obj.department_id or 0
    if existing and existing[0] == new:
        return                        # phòng chính không đổi

    remaining = [x for x in existing if x != new]
    set_departments(db, obj, ([new] if new else []) + remaining, user_id,
                  primary_department=new or None)


def clear_perm_cache_of(db: Session, employee_id: int) -> None:
    """Xóa hồ sơ quyền đang cache của tài khoản gắn với nhân sự này — #28.

    `get_perm_profile` giữ `company_id`/`dept_id` trong `_PERM_CACHE` 60 giây, mà
    hai giá trị đó CHÍNH là phạm vi dữ liệu (`_role_scope_cond`). Đổi pháp nhân
    của một người mà không xóa cache = thu hồi tầm nhìn chậm một phút, đủ để họ
    kịp mở lại danh sách của pháp nhân cũ.

    `department_service.set_departments` đã làm đúng điều này từ CR-167; đây là
    cùng một việc cho cửa còn lại (màn hồ sơ nhân sự). Nhân sự CHƯA CÓ tài khoản
    thì không có gì để xóa — vòng lặp rỗng, không nổ.
    """
    from app.core.auth import perm_cache_clear
    from app.modules.user.model import User

    for row in db.query(User.id).filter(User.employee_id == employee_id).all():
        perm_cache_clear(row[0])


def update_employee(db: Session, eid: int, data: EmployeeUpdate, user_id: int) -> Employee:
    obj = get_employee(db, eid)
    old_email = (obj.email or "").strip()
    #  Hai cột QUYẾT ĐỊNH PHẠM VI DỮ LIỆU — chụp lại trước khi ghi đè để biết có
    #  phải xóa cache quyền không (xem `clear_perm_cache_of`).
    old_scope = (obj.company_id or 0, obj.department_id or 0)
    fields = data.model_dump(exclude_unset=True)
    for key, value in fields.items():
        setattr(obj, key, value)
    obj.updated_by = user_id
    if "department_id" in fields:
        _sync_primary_department(db, obj, user_id)
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "update")
    #  ⚠️ Sau `commit` chứ không trước: xóa cache rồi mới ghi thì một request khác
    #  chen vào giữa sẽ dựng lại hồ sơ CŨ và cache thêm 60 giây nữa.
    if (obj.company_id or 0, obj.department_id or 0) != old_scope:
        clear_perm_cache_of(db, obj.id)

    # CR-022: hồ sơ nhân sự KHÔNG còn cấp quyền cho tài khoản đăng nhập. Ô ở màn Nhân sự nay là
    # "Vị trí / Chức vụ" (`position`) — chỉ là chữ để hiển thị/in phiếu. Quyền thật của tài khoản
    # chỉ gán ở màn "Phân quyền tài khoản" (tab_user_role), không có đường đồng bộ ngầm nào nữa.

    # Đồng bộ email sang tài khoản đăng nhập (User.email) để đăng nhập bằng email được.
    # CHỈ khớp trong 2 trường hợp an toàn (tránh ghi đè "handle đăng nhập" như admin/TESTREQ mà
    # ai đó cố tình đặt khác email nhân sự):
    #   (a) User.email đang RỖNG → điền email nhân sự (đúng ca bug: tạo TK khi chưa có email, sau đó
    #       thêm email vào nhân sự — kể cả email đã nhập TRƯỚC bản vá, lần lưu sau tự khớp);
    #   (b) admin THỰC SỰ đổi field email trong lần lưu này (old != new) → đẩy email mới sang.
    email_changed = "email" in fields and (obj.email or "").strip() != old_email
    _sync_user_email_from_employee(db, obj, email_changed)
    return obj


def _sync_user_email_from_employee(db: Session, emp: Employee, email_changed: bool) -> None:
    """Khớp email đăng nhập (User.email) = email nhân sự khi tài khoản đang RỖNG email, hoặc khi admin
    vừa đổi email ở lần lưu này. Bỏ qua nếu nhân sự chưa có email (không xoá email đăng nhập đang có),
    hoặc email đã bị tài khoản KHÁC dùng (tránh 2 tài khoản trùng email → đăng nhập nhập nhằng)."""
    from app.modules.user.model import User

    new_email = (emp.email or "").strip()
    if not new_email:
        return
    user = db.query(User).filter(User.employee_id == emp.id).first()
    if not user:
        return
    cur = (user.email or "").strip()
    if cur == new_email:
        return
    if cur and not email_changed:
        return  # giữ nguyên handle/email khác khi admin không chủ động đổi email
    # CR-023: tài khoản đã khoá không còn giữ chỗ email nữa (chỉ tài khoản đang hoạt động mới tính)
    dup = db.query(User).filter(User.email == new_email, User.id != user.id,
                                User.is_active.is_(True)).first()
    if dup:
        raise HTTPException(400, "Email này đã được một tài khoản khác sử dụng")
    user.email = new_email
    db.commit()


def detach_users(db: Session, eid: int, actor_id: int) -> int:
    """CR-023: xoá hồ sơ nhân sự thì phải KHOÁ + GỠ LIÊN KẾT tài khoản đăng nhập của người đó.

    Trước đây xoá nhân sự là xoá cứng, không đụng gì tới `tab_user` → còn lại "tài khoản mồ côi":
    vẫn đăng nhập được, không còn hồ sơ nhân sự nên hệ thống hiển thị thông tin lấy từ bản ghi tài
    khoản, và nếu trùng email với tài khoản thật thì còn che mất tài khoản thật khi đăng nhập.

    Không xoá tài khoản (giữ lại để truy vết ai đã làm gì), chỉ `is_active = 0` + `employee_id = 0`.
    Trả về số tài khoản đã khoá. KHÔNG commit — để chung transaction với thao tác xoá nhân sự.
    """
    from app.core.auth import perm_cache_clear
    from app.modules.user.model import User

    users = db.query(User).filter(User.employee_id == eid).all()
    for u in users:
        u.is_active = False
        u.employee_id = 0
        u.updated_by = actor_id
        perm_cache_clear(u.id)
    return len(users)


def delete_employee(db: Session, eid: int, user_id: int) -> int:
    obj = get_employee(db, eid)
    locked = detach_users(db, eid, user_id)
    db.delete(obj)
    db.commit()
    msg = f"Khoá {locked} tài khoản đăng nhập kèm theo" if locked else ""
    record(db, user_id, ENTITY, eid, "delete", msg)
    return locked
