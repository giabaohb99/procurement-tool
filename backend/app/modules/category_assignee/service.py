from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.central_purchasing import get_central_dept_id, is_central_dept

from .model import CategoryAssignee
from .schema import CategoryAssigneeCreate, CategoryAssigneeUpdate

ENTITY = "category_assignee"

#  bao-CR-414: `0` từng là bộ phân công «Thu mua chung» (phòng ảo). bao-CR-524 bỏ phòng ảo: bộ
#  chung nay là bộ của PHÒNG THU MUA MẶC ĐỊNH (`core/central_purchasing`, mã PBA017). Dòng `0`
#  còn sót (chưa chạy `scripts/backfill_central_purchasing_dept.py`) vẫn được đọc như bộ đó.
GLOBAL_DEPT_ID = 0


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


# ── bao-CR-527: đúng 1 NSTM chính + tối đa 1 dự phòng, cả hai phải «Chính thức» ─────────────

def is_official_employee(emp) -> bool:
    """Nhân sự còn nhận việc được: hồ sơ «Chính thức» VÀ đang hoạt động — bao-CR-527.

    «Nghỉ thai sản», «Nghỉ việc», «Cộng tác viên» hay hồ sơ bị tắt đều KHÔNG tính: phân công
    cho họ là việc rơi vào người không có mặt để làm."""
    from app.modules.employee.service import STATUS_OFFICIAL
    return bool(emp and emp.is_active and (emp.status or "") == STATUS_OFFICIAL)


def _status_text(emp) -> str:
    """Tình trạng để nói trong câu chặn: nhãn trạng thái, hoặc «ngừng hoạt động» khi hồ sơ bị tắt."""
    if not emp.is_active:
        return "ngừng hoạt động"
    return emp.status_label or emp.status or "chưa rõ"


def _ensure_official(db: Session, emp_id: int, role_label: str):
    from app.modules.employee.model import Employee
    emp = db.get(Employee, int(emp_id)) if emp_id else None
    if not emp:
        raise HTTPException(400, f"Không thấy nhân sự được chọn làm {role_label} (id {emp_id})")
    if not is_official_employee(emp):
        raise HTTPException(400, f"{role_label} {emp.full_name} ({emp.code}) đang ở tình trạng "
                                 f"«{_status_text(emp)}» — chỉ phân công được nhân sự «Chính thức» "
                                 "đang hoạt động")
    return emp


def validate_assignee_pair(db: Session, primary_id: int, backup_id: int) -> None:
    """Chốt chung của MỌI cửa ghi bảng phân công (tạo · sửa · gán hàng loạt) — bao-CR-527.

    NSTM chính BẮT BUỘC và phải «Chính thức» + đang hoạt động; dự phòng không bắt buộc, nhưng có
    thì phải khác người chính và cũng phải «Chính thức» + đang hoạt động."""
    primary_id, backup_id = int(primary_id or 0), int(backup_id or 0)
    if not primary_id:
        raise HTTPException(400, "Phải chọn NSTM chính cho phân công")
    _ensure_official(db, primary_id, "NSTM chính")
    if not backup_id:
        return
    if backup_id == primary_id:
        raise HTTPException(400, "NSTM dự phòng phải là người khác NSTM chính")
    _ensure_official(db, backup_id, "NSTM dự phòng")


def normalize_department_id(db: Session, department_id) -> int:
    """Phòng áp dụng lúc GHI: `0` (bộ «Thu mua chung» cũ) → phòng thu mua mặc định — bao-CR-524.
    Danh mục chưa có phòng mặc định thì giữ `0` như trước."""
    return int(department_id or 0) or get_central_dept_id(db)


def list_all(db: Session):
    return db.query(CategoryAssignee).order_by(CategoryAssignee.id.desc()).all()


def get(db: Session, cid: int) -> CategoryAssignee:
    obj = db.get(CategoryAssignee, cid)
    if not obj:
        raise HTTPException(404, "Không tìm thấy phân công")
    return obj


def _find_pair(db: Session, department_id: int, item_group_id: int):
    """Dòng phân công của cặp (phòng, phân loại). Phòng thu mua mặc định thì dòng `0` cũ cũng là
    của nó (bao-CR-524) — ưu tiên dòng mang id thật."""
    dept = int(department_id or 0)
    q = db.query(CategoryAssignee).filter(CategoryAssignee.item_group_id == item_group_id)
    if is_central_dept(db, dept):
        central = get_central_dept_id(db)
        rows = q.filter(CategoryAssignee.department_id.in_({GLOBAL_DEPT_ID, central})).all()
        rows.sort(key=lambda r: 0 if (central and r.department_id == central) else 1)
        return rows[0] if rows else None
    return q.filter(CategoryAssignee.department_id == dept).first()


def create(db: Session, data: CategoryAssigneeCreate, user_id: int) -> CategoryAssignee:
    validate_assignee_pair(db, data.primary_employee_id, data.backup_employee_id)   # bao-CR-527
    payload = data.model_dump()
    payload["department_id"] = normalize_department_id(db, payload.get("department_id"))   # bao-CR-524
    if _find_pair(db, payload["department_id"], data.item_group_id):
        raise HTTPException(400, "Phân loại này đã được cấu hình phụ trách cho phòng đó")
    obj = CategoryAssignee(**payload, created_by=user_id, updated_by=user_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "create",
           _log_message(db, obj.primary_employee_id, obj.backup_employee_id, obj.department_id))
    return obj


def update(db: Session, cid: int, data: CategoryAssigneeUpdate, user_id: int) -> CategoryAssignee:
    obj = get(db, cid)
    changes = data.model_dump(exclude_unset=True)
    if "department_id" in changes:
        changes["department_id"] = normalize_department_id(db, changes["department_id"])   # bao-CR-524
    # bao-CR-527: kiểm CẶP SAU KHI SỬA — dòng có người chính vừa nghỉ thì phải đổi người chính mới
    # lưu được, dù lần này chỉ sửa ô khác.
    validate_assignee_pair(db, changes.get("primary_employee_id", obj.primary_employee_id),
                           changes.get("backup_employee_id", obj.backup_employee_id))
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
    chưa có thì tạo, khóa theo cặp (phòng, phân loại). `department_id` = 0 là phòng thu mua mặc
    định (bao-CR-524); dòng `0` cũ của phòng đó được cập nhật tại chỗ và chuyển sang id thật."""
    validate_assignee_pair(db, primary_id, backup_id)   # bao-CR-527 — chặn trước khi ghi dòng nào
    department_id = normalize_department_id(db, department_id)
    n = 0
    msg = _log_message(db, primary_id, backup_id, department_id)
    logs: list[tuple[int, str]] = []   # (row_id, action) — ghi audit sau khi commit
    for gid in item_group_ids:
        if not gid:
            continue
        row = _find_pair(db, department_id, gid)
        if row:
            row.department_id = department_id
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

def handling_dept_of(ticket, central_id: int = 0) -> int:
    """Phòng đang XỬ LÝ một phiếu (YCMH lẫn YCBG) = ô «Phòng xử lý» (`handler_dept_id`).

    bao-CR-524: phiếu cũ còn `0` là phiếu phòng thu mua mặc định xử lý → trả `central_id` (người
    gọi tra bằng `core.central_purchasing.get_central_dept_id`). Chỉ khi danh mục chưa có phòng
    mặc định (`central_id` = 0) mới lùi về phòng lập phiếu như trước."""
    handler = int(getattr(ticket, "handler_dept_id", 0) or 0)
    if handler:
        return handler
    return int(central_id or 0) or int(getattr(ticket, "department_id", 0) or 0)


# ── Người phụ trách CHỌN ĐƯỢC theo phòng xử lý (bao-CR-486) ──────────────────────────────

#  «assigned» (được giao) là bậc của nhân sự thu mua thường (`pur_staff`) — thiếu nó thì chính
#  những người đang nhận việc biến mất khỏi ô chọn (rà trên bản sao prod 28/09/2026: 3/4 NSTM).
_PURCHASING_SCOPES = ("assigned", "dept_proc", "proc", "all")


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


def _other_self_purchasing_depts(db: Session, central_id: int) -> set[int]:
    """Phòng tự mua hàng TRỪ phòng thu mua mặc định — bao-CR-524.

    Phòng PBA017 có người giữ bậc `dept_proc` cũng lọt vào `list_self_purchasing_dept_ids`, nhưng
    người của nó chính là người thu mua chung: loại họ khỏi phiếu thu mua chung là loại nhầm."""
    from app.modules.purchase_request.service import list_self_purchasing_dept_ids
    return list_self_purchasing_dept_ids(db) - {int(central_id or 0)}


def assignable_staff(db: Session, ticket) -> list:
    """Danh sách NSTM chọn được cho MỘT phiếu (YCMH hay YCBG) — đi theo ô «Phòng xử lý».

    Đại ca chốt 25/09/2026: *"nhân sự phụ trách sẽ đi theo phòng xử lý — đơn của nhà máy mà
    chọn được nhân sự ngoài đó là lỗi"*. Trước đó giao diện lọc theo TÊN phòng có chữ «thu
    mua», nên nhà máy thấy cả người thu mua chung, còn phòng «Sản xuất -Thu mua» (tên có chữ
    đó) lại lọt vào danh sách của mọi phiếu.

      · phòng xử lý là phòng thu mua mặc định (bao-CR-524: id PBA017, hoặc `0` cũ)
          → người bậc assigned/proc/all KHÔNG thuộc một phòng tự mua KHÁC, cộng người thu mua
            (mọi bậc, kể cả `dept_proc`) thuộc chính phòng thu mua mặc định. Giữ nguyên tập người
            chọn được như thời «Thu mua chung» — chỉ thêm người `dept_proc` của phòng PBA017;
      · phòng khác → người thu mua (bậc assigned/dept_proc/proc/all) THUỘC phòng đó.
    Trả `Employee` đang hoạt động, xếp theo tên. Người đã gán từ trước mà nay ngoài danh sách
    thì giao diện tự bổ sung để không mất nhãn — cửa ghi mới chặn (`check_assignee_allowed`).
    """
    from app.modules.employee.model import Employee

    dept = int(getattr(ticket, "handler_dept_id", 0) or 0)
    if not is_central_dept(db, dept):
        ids = _purchasing_employee_ids(db, _PURCHASING_SCOPES)
        if not ids:
            return []
        q = db.query(Employee).filter(Employee.department_id == dept, Employee.id.in_(ids))
    else:
        central = get_central_dept_id(db)
        shared_ids = _purchasing_employee_ids(db, ("assigned", "proc", "all"))
        other_depts = _other_self_purchasing_depts(db, central)
        conds = []
        if shared_ids:
            conds.append(and_(Employee.id.in_(shared_ids), ~Employee.department_id.in_(other_depts))
                         if other_depts else Employee.id.in_(shared_ids))
        own_ids = _purchasing_employee_ids(db, _PURCHASING_SCOPES) if central else set()
        if own_ids:
            conds.append(and_(Employee.id.in_(own_ids), Employee.department_id == central))
        if not conds:
            return []
        q = db.query(Employee).filter(or_(*conds))
    return (q.filter(Employee.is_active == True)  # noqa: E712
            .order_by(Employee.full_name, Employee.id).all())


def check_assignee_allowed(db: Session, ticket, code: str) -> None:
    """Chặn gán NSTM ngoài phòng xử lý (bao-CR-486) — cửa ghi của cả YCMH lẫn YCBG.

    Luật kiểm LỎNG hơn danh sách gợi ý (chỉ so PHÒNG, không đòi vai trò): phiếu phòng khác xử
    lý thì người được gán phải thuộc phòng đó; phiếu phòng thu mua mặc định xử lý (bao-CR-524:
    id PBA017 hoặc `0` cũ) thì người đó không được thuộc một phòng tự mua KHÁC. Bỏ gán (mã rỗng)
    luôn được. Mã lạ → 400 chứ không lặng lẽ ghi chuỗi rác.
    """
    from app.modules.employee.model import Employee

    code = (code or "").strip()
    if not code:
        return
    emp = db.query(Employee).filter(Employee.code == code).first()
    if not emp:
        raise HTTPException(400, f"Không thấy nhân sự mã {code}")
    dept = int(getattr(ticket, "handler_dept_id", 0) or 0)
    emp_dept = int(emp.department_id or 0)
    if not is_central_dept(db, dept):
        if emp_dept != dept:
            raise HTTPException(400, f"{emp.full_name} không thuộc phòng xử lý của phiếu — "
                                     "chỉ gán được người của phòng đang xử lý")
        return
    if emp_dept and emp_dept in _other_self_purchasing_depts(db, get_central_dept_id(db)):
        raise HTTPException(400, f"{emp.full_name} thuộc phòng tự mua hàng — phiếu này do phòng "
                                 "thu mua mặc định xử lý, chỉ gán được người của phòng đó")


def load_configs(db: Session, department_id: int, allow_global: bool = True) -> dict[int, CategoryAssignee]:
    """Bộ phân công áp cho một phòng: dòng riêng của phòng đó trước, phân loại nào phòng chưa
    khai thì rơi về bộ của phòng thu mua mặc định — CHỈ khi `allow_global`.

    bao-CR-524: «bộ chung» = dòng của phòng thu mua mặc định (id PBA017) + dòng `0` cũ chưa
    backfill (id thật thắng `0` nếu cùng phân loại). Phòng đang xét CHÍNH LÀ phòng thu mua mặc
    định thì bộ chung là bộ riêng của nó, dùng được cả khi `allow_global=False`.

    `allow_global=False` dành cho người duyệt/điều phối chỉ có bậc `dept_proc` (quản lý thu mua
    của phòng tự mua): bộ chung là người của phòng thu mua mặc định, tự gán là đẩy việc của
    phòng ra ngoài. Trả dict item_group_id -> dòng cấu hình."""
    central = get_central_dept_id(db)
    dept = int(department_id or 0) or central
    shared = {GLOBAL_DEPT_ID} | ({central} if central else set())
    dept_ids = {dept}
    if allow_global or dept in shared:
        dept_ids |= shared
    rank = {GLOBAL_DEPT_ID: 0}
    if central:
        rank[central] = 1
    rank[dept] = 2                                           # bộ riêng đè bộ chung, id thật đè `0`
    rows = db.query(CategoryAssignee).filter(CategoryAssignee.department_id.in_(dept_ids)).all()
    configs: dict[int, CategoryAssignee] = {}
    for row in sorted(rows, key=lambda r: rank.get(r.department_id, 0)):
        configs[row.item_group_id] = row
    return configs


def pick_active_employee(db: Session, cfg: CategoryAssignee, emp_cache: dict | None = None):
    """Người được tự gán: NSTM CHÍNH nếu còn «Chính thức» + đang hoạt động, không thì DỰ PHÒNG
    nếu người đó đạt cùng điều kiện; không ai đạt → None (dòng để trống, chọn tay) — bao-CR-527.

    Trước bao-CR-527 chỉ xét `is_active`, và DỰ PHÒNG được trả thẳng dù đã nghỉ — nên việc có
    thể rơi vào người nghỉ thai sản / nghỉ việc mà hồ sơ chưa tắt."""
    from app.modules.employee.model import Employee
    cache = emp_cache if emp_cache is not None else {}

    def emp(eid):
        if not eid:
            return None
        if eid not in cache:
            cache[eid] = db.get(Employee, eid)
        return cache[eid]

    for eid in (cfg.primary_employee_id, cfg.backup_employee_id):
        candidate = emp(eid)
        if is_official_employee(candidate):
            return candidate
    return None


def resolve_for_group(db: Session, item_group_name: str, department_id: int = GLOBAL_DEPT_ID,
                      allow_global: bool = True):
    """Trả về nhân sự NSTM phụ trách 1 phân loại cho phòng `department_id` (chính; chính không còn
    «Chính thức» → dự phòng). Không có bộ riêng thì rơi về bộ của phòng thu mua mặc định khi
    `allow_global`. None nếu chưa cấu hình / không ai nhận được việc."""
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
    chính không còn «Chính thức» → DỰ PHÒNG (bao-CR-527). Tôn trọng gán tay: dòng đã có assignee
    thì bỏ qua. `allow_global=False` → chỉ dùng bộ riêng của phòng, không rơi về bộ chung. Trả số
    dòng được gán."""
    from app.modules.catalog.model import ItemGroup
    from app.modules.purchase_request.model import PurchaseRequestItem

    lines = db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).all()
    if not lines:
        return 0
    configs = load_configs(db, handling_dept_of(pr, get_central_dept_id(db)), allow_global)
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
