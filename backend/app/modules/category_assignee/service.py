from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record

from .model import CategoryAssignee
from .schema import CategoryAssigneeCreate, CategoryAssigneeUpdate

ENTITY = "category_assignee"

GLOBAL_DEPT_ID = 0   # bao-CR-414: bộ phân công "Thu mua chung" (dùng cho mọi phòng chưa có bộ riêng)


def _log_message(db: Session, primary_id: int, backup_id: int, department_id: int = 0) -> str:
    """Tóm tắt cặp NSTM cho dòng audit: 'Chính: X · Dự phòng: Y' (+ tên phòng nếu là bộ riêng)."""
    from app.modules.employee.model import Employee
    p = db.get(Employee, primary_id) if primary_id else None
    b = db.get(Employee, backup_id) if backup_id else None
    msg = f"Chính: {p.full_name if p else '—'} · Dự phòng: {b.full_name if b else '—'}"
    if department_id:
        from app.modules.department.model import Department
        d = db.get(Department, department_id)
        msg += f" · Phòng: {d.name if d else department_id}"
    return msg


def list_all(db: Session):
    return db.query(CategoryAssignee).order_by(CategoryAssignee.id.desc()).all()


def get(db: Session, cid: int) -> CategoryAssignee:
    obj = db.get(CategoryAssignee, cid)
    if not obj:
        raise HTTPException(404, "Không tìm thấy phân công")
    return obj


def _find_pair(db: Session, department_id: int, item_group_id: int):
    return (db.query(CategoryAssignee)
            .filter(CategoryAssignee.department_id == (department_id or 0),
                    CategoryAssignee.item_group_id == item_group_id)
            .first())


def create(db: Session, data: CategoryAssigneeCreate, user_id: int) -> CategoryAssignee:
    if _find_pair(db, data.department_id, data.item_group_id):
        raise HTTPException(400, "Phân loại này đã được cấu hình phụ trách cho phòng đó")
    obj = CategoryAssignee(**data.model_dump(), created_by=user_id, updated_by=user_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "create",
           _log_message(db, obj.primary_employee_id, obj.backup_employee_id, obj.department_id))
    return obj


def update(db: Session, cid: int, data: CategoryAssigneeUpdate, user_id: int) -> CategoryAssignee:
    obj = get(db, cid)
    changes = data.model_dump(exclude_unset=True)
    new_dept = changes.get("department_id", obj.department_id)
    new_group = changes.get("item_group_id", obj.item_group_id)
    if (new_dept, new_group) != (obj.department_id, obj.item_group_id):
        dup = _find_pair(db, new_dept, new_group)
        if dup and dup.id != obj.id:
            raise HTTPException(400, "Phân loại này đã được cấu hình phụ trách cho phòng đó")
    for k, v in changes.items():
        setattr(obj, k, v)
    obj.updated_by = user_id
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "update",
           _log_message(db, obj.primary_employee_id, obj.backup_employee_id, obj.department_id))
    return obj


def delete(db: Session, cid: int, user_id: int) -> None:
    obj = get(db, cid)
    oid = obj.id
    db.delete(obj)
    db.commit()
    record(db, user_id, ENTITY, oid, "delete", "Đã xóa phân công")


def bulk_upsert(db: Session, item_group_ids: list[int], primary_id: int, backup_id: int,
                user_id: int, department_id: int = GLOBAL_DEPT_ID) -> int:
    """Gán 1 cặp NSTM (chính + dự phòng) cho NHIỀU phân loại cùng lúc — có rồi thì cập nhật,
    chưa có thì tạo, khóa theo cặp (phòng, phân loại). `department_id` = 0 là bộ chung."""
    department_id = department_id or 0
    n = 0
    msg = _log_message(db, primary_id, backup_id, department_id)
    logs: list[tuple[int, str]] = []   # (row_id, action) — ghi audit sau khi commit
    for gid in item_group_ids:
        if not gid:
            continue
        row = _find_pair(db, department_id, gid)
        if row:
            row.primary_employee_id = primary_id
            row.backup_employee_id = backup_id
            row.updated_by = user_id
            action = "update"
        else:
            row = CategoryAssignee(department_id=department_id, item_group_id=gid,
                                   primary_employee_id=primary_id, backup_employee_id=backup_id,
                                   created_by=user_id, updated_by=user_id)
            db.add(row)
            action = "create"
        db.flush()   # lấy id cho dòng mới
        logs.append((row.id, action))
        n += 1
    db.commit()
    for rid, action in logs:
        record(db, user_id, ENTITY, rid, action, msg)
    return n


# ── Tra cứu người phụ trách theo PHÒNG XỬ LÝ (bao-CR-414 GĐ2) ────────────────────────────

def handling_dept_of(ticket) -> int:
    """Phòng đang XỬ LÝ một phiếu: phòng được nhờ (`handler_dept_id`) nếu có, không thì phòng lập
    phiếu (`department_id`). Dùng chung cho YCMH lẫn YCBG."""
    return int(getattr(ticket, "handler_dept_id", 0) or 0) or int(getattr(ticket, "department_id", 0) or 0)


# ── Người phụ trách CHỌN ĐƯỢC theo phòng xử lý (bao-CR-486) ──────────────────────────────

_PURCHASING_SCOPES = ("dept_proc", "proc", "all")


def _purchasing_employee_ids(db: Session, scopes: tuple[str, ...]) -> set[int]:
    """Nhân sự đang hoạt động có tài khoản giữ vai trò thu mua trên YCMH ở các bậc `scopes`.

    Cùng cách suy từ phân quyền với `list_self_purchasing_dept_ids`: ai được cấp bậc thu mua là
    người làm thu mua, không có ô «phòng thu mua» riêng để hai chỗ lệch nhau."""
    from app.modules.employee.model import Employee
    from app.modules.role.model import Permission
    from app.modules.user.model import User, UserRole

    rows = (db.query(Employee.id)
            .join(User, User.employee_id == Employee.id)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Permission, Permission.role_id == UserRole.role_id)
            .filter(Permission.entity == "purchase_request", Permission.scope.in_(scopes),
                    User.is_active == True, Employee.is_active == True)  # noqa: E712
            .distinct().all())
    return {int(r[0]) for r in rows}


def assignable_staff(db: Session, ticket) -> list:
    """Danh sách NSTM chọn được cho MỘT phiếu (YCMH hay YCBG) — đi theo ô «Phòng xử lý».

    Đại ca chốt 25/09/2026: *"nhân sự phụ trách sẽ đi theo phòng xử lý — đơn của nhà máy mà
    chọn được nhân sự ngoài đó là lỗi"*. Trước đó giao diện lọc theo TÊN phòng có chữ «thu
    mua», nên nhà máy thấy cả người thu mua chung, còn phòng «Sản xuất -Thu mua» (tên có chữ
    đó) lại lọt vào danh sách của mọi phiếu.

      · `handler_dept_id` ≠ 0 → người thu mua (bậc dept_proc/proc/all) THUỘC phòng đó;
      · = 0 (thu mua chung)  → người bậc proc/all KHÔNG thuộc phòng tự mua nào.
    Trả `Employee` đang hoạt động, xếp theo tên. Người đã gán từ trước mà nay ngoài danh sách
    thì giao diện tự bổ sung để không mất nhãn — cửa ghi mới chặn (`check_assignee_allowed`).
    """
    from app.modules.employee.model import Employee
    from app.modules.purchase_request.service import list_self_purchasing_dept_ids

    dept = int(getattr(ticket, "handler_dept_id", 0) or 0)
    if dept:
        ids = _purchasing_employee_ids(db, _PURCHASING_SCOPES)
        q = db.query(Employee).filter(Employee.department_id == dept)
    else:
        ids = _purchasing_employee_ids(db, ("proc", "all"))
        self_depts = list_self_purchasing_dept_ids(db)
        q = db.query(Employee)
        if self_depts:
            q = q.filter(~Employee.department_id.in_(self_depts))
    if not ids:
        return []
    return (q.filter(Employee.id.in_(ids), Employee.is_active == True)  # noqa: E712
            .order_by(Employee.full_name, Employee.id).all())


def check_assignee_allowed(db: Session, ticket, code: str) -> None:
    """Chặn gán NSTM ngoài phòng xử lý (bao-CR-486) — cửa ghi của cả YCMH lẫn YCBG.

    Luật kiểm LỎNG hơn danh sách gợi ý (chỉ so PHÒNG, không đòi vai trò): phiếu có phòng xử lý
    thì người được gán phải thuộc phòng đó; phiếu thu mua chung thì người đó không được thuộc
    phòng tự mua. Bỏ gán (mã rỗng) luôn được. Mã lạ → 400 chứ không lặng lẽ ghi chuỗi rác.
    """
    from app.modules.employee.model import Employee
    from app.modules.purchase_request.service import list_self_purchasing_dept_ids

    code = (code or "").strip()
    if not code:
        return
    emp = db.query(Employee).filter(Employee.code == code).first()
    if not emp:
        raise HTTPException(400, f"Không thấy nhân sự mã {code}")
    dept = int(getattr(ticket, "handler_dept_id", 0) or 0)
    emp_dept = int(emp.department_id or 0)
    if dept and emp_dept != dept:
        raise HTTPException(400, f"{emp.full_name} không thuộc phòng xử lý của phiếu — "
                                 "chỉ gán được người của phòng đang xử lý")
    if not dept and emp_dept and emp_dept in list_self_purchasing_dept_ids(db):
        raise HTTPException(400, f"{emp.full_name} thuộc phòng tự mua hàng — phiếu này do thu "
                                 "mua chung xử lý, chỉ gán được người thu mua chung")


def load_configs(db: Session, department_id: int, allow_global: bool = True) -> dict[int, CategoryAssignee]:
    """Bộ phân công áp cho một phòng: dòng riêng của phòng đó trước, phân loại nào phòng chưa
    khai thì rơi về bộ chung (phòng 0) — CHỈ khi `allow_global`.

    `allow_global=False` dành cho người duyệt/điều phối chỉ có bậc `dept_proc` (quản lý thu mua
    của phòng tự mua): bộ chung là người của thu mua chung, tự gán là đẩy việc của phòng ra ngoài.
    Trả dict item_group_id -> dòng cấu hình."""
    department_id = department_id or 0
    dept_ids = {department_id}
    if allow_global:
        dept_ids.add(GLOBAL_DEPT_ID)
    rows = db.query(CategoryAssignee).filter(CategoryAssignee.department_id.in_(dept_ids)).all()
    configs: dict[int, CategoryAssignee] = {}
    for row in rows:                                         # bộ chung điền trước, bộ riêng đè lên
        if row.department_id == GLOBAL_DEPT_ID:
            configs.setdefault(row.item_group_id, row)
    for row in rows:
        if row.department_id == department_id:
            configs[row.item_group_id] = row
    return configs


def pick_active_employee(db: Session, cfg: CategoryAssignee, emp_cache: dict | None = None):
    """Người CHÍNH nếu còn làm việc, không thì DỰ PHÒNG (có thể None)."""
    from app.modules.employee.model import Employee
    cache = emp_cache if emp_cache is not None else {}

    def emp(eid):
        if not eid:
            return None
        if eid not in cache:
            cache[eid] = db.get(Employee, eid)
        return cache[eid]

    primary = emp(cfg.primary_employee_id)
    if primary and primary.is_active:
        return primary
    return emp(cfg.backup_employee_id)


def resolve_for_group(db: Session, item_group_name: str, department_id: int = GLOBAL_DEPT_ID,
                      allow_global: bool = True):
    """Trả về nhân sự NSTM phụ trách 1 phân loại cho phòng `department_id` (chính; chính nghỉ →
    dự phòng). Không có bộ riêng thì rơi về bộ chung khi `allow_global`. None nếu chưa cấu hình."""
    if not item_group_name:
        return None
    from app.modules.catalog.model import ItemGroup
    g = db.query(ItemGroup).filter(ItemGroup.name == item_group_name).first()
    if not g:
        return None
    cfg = load_configs(db, department_id, allow_global).get(g.id)
    if not cfg:
        return None
    return pick_active_employee(db, cfg)


def auto_assign_by_category(db: Session, pr, allow_global: bool = True) -> int:
    """Sau khi duyệt/điều phối PYC: điền `assignee` (mã NV) cho các dòng CHƯA có người, theo phân
    loại của dòng và theo PHÒNG ĐANG XỬ LÝ phiếu (`handling_dept_of`). Ưu tiên người CHÍNH; người
    chính nghỉ (is_active=false) → DỰ PHÒNG. Tôn trọng gán tay: dòng đã có assignee thì bỏ qua.
    `allow_global=False` → chỉ dùng bộ riêng của phòng, không rơi về bộ chung. Trả số dòng được gán."""
    from app.modules.catalog.model import ItemGroup
    from app.modules.purchase_request.model import PurchaseRequestItem

    lines = db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).all()
    if not lines:
        return 0
    configs = load_configs(db, handling_dept_of(pr), allow_global)
    if not configs:
        return 0
    group_id_by_name = {g.name: g.id for g in db.query(ItemGroup).all()}
    emp_cache: dict = {}

    assigned = 0
    for ln in lines:
        if ln.assignee:                      # đã có (gán tay) → giữ nguyên
            continue
        gid = group_id_by_name.get(ln.item_group or "")
        cfg = configs.get(gid) if gid else None
        if not cfg:
            continue
        chosen = pick_active_employee(db, cfg, emp_cache)
        if chosen and chosen.code:
            ln.assignee = chosen.code
            assigned += 1
    if assigned:
        db.commit()
    return assigned
