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


def phong_ban_cua(db: Session, employee_id: int) -> list[int]:
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


def phong_ban_cua_nhieu_nguoi(db: Session, employee_ids: list[int]) -> dict[int, list[int]]:
    """Bản gọi MỘT LƯỢT cho danh sách — tránh N+1 ở màn danh sách nhân sự."""
    if not employee_ids:
        return {}
    rows = (db.query(EmployeeDepartment)
            .filter(EmployeeDepartment.employee_id.in_(set(employee_ids)))
            .order_by(EmployeeDepartment.is_primary.desc(),
                      EmployeeDepartment.department_id.asc())
            .all())
    ket_qua: dict[int, list[int]] = {}
    for row in rows:
        ket_qua.setdefault(row.employee_id, []).append(row.department_id)
    return ket_qua


def nhan_su_cua_phong(db: Session, department_id: int) -> list[int]:
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

def _kiem_phong_co_that(db: Session, employee: Employee,
                        department_ids: list[int]) -> list[Department]:
    """L3 — phòng có thật, đang bật, và cùng pháp nhân với nhân sự."""
    if not department_ids:
        return []
    phong = db.query(Department).filter(Department.id.in_(set(department_ids))).all()
    theo_id = {row.id: row for row in phong}

    thieu = sorted(set(department_ids) - set(theo_id))
    if thieu:
        raise HTTPException(400, f"Phòng ban không tồn tại: {thieu}")

    #  Pháp nhân: chỉ chặn khi CẢ HAI bên đều khai. Dữ liệu cũ có phòng chưa gắn
    #  pháp nhân, chặn cứng là không sửa nổi hồ sơ nào.
    if employee.company_id:
        lac_cho = [row.name for row in phong
                   if row.company_id and row.company_id != employee.company_id]
        if lac_cho:
            raise HTTPException(
                400, f"Phòng ban thuộc pháp nhân khác: {', '.join(lac_cho)}. "
                     "Gán chéo pháp nhân là mở dữ liệu xuyên pháp nhân.")
    return phong


def chan_tu_sua_phong_ban_cua_minh(db: Session, employee_id: int, actor) -> None:
    """L1 — xem đầu tệp. Gọi ở MỌI cửa ghi vào bảng này.

    So theo `user.employee_id` chứ không theo `user.id`: cùng một con người,
    hai định danh khác nhau ở hai bảng.
    """
    cua_minh = getattr(actor, "employee_id", None)
    if cua_minh and cua_minh == employee_id:
        raise HTTPException(
            403, "Không tự đổi phòng ban của chính mình được — phòng ban quyết định "
                 "phạm vi dữ liệu bạn nhìn thấy. Nhờ một quản trị khác thao tác.")


#  Bậc phạm vi từ hẹp tới rộng — dùng để lấy bậc RỘNG NHẤT trong các vai trò.
_BAC = {"own": 0, "assigned": 1, "proc": 2, "dept": 3, "company": 4, "all": 5}


def _bac_rong_nhat(profile: dict, entity: str, action: str) -> str | None:
    """Bậc phạm vi rộng nhất mà người này có trên `(entity, action)`.

    `None` = không vai trò nào cấp hành động đó. Lấy bậc RỘNG NHẤT vì
    `scope_condition` cũng HỢP các grant lại — hẹp hơn ở đây là chặn nhầm người
    thật sự có quyền.
    """
    bac = None
    for grant in profile.get("grants", []):
        perms = grant["perms"].get(entity)
        if not perms or not perms.get(action):
            continue
        ten = perms.get("scope", "all")
        if bac is None or _BAC.get(ten, 5) > _BAC.get(bac, 5):
            bac = ten
    return bac


def phong_ban_gan_duoc(db: Session, profile: dict) -> set[int] | None:
    """Những phòng người này được phép GÁN cho người khác. `None` = không giới hạn.

    ⚠️ Đo bằng phạm vi trên entity **`employee`** (thứ đang bị ghi), KHÔNG phải
    trên `department`. Hai cái khác nghĩa hẳn: `SCOPE_FIELDS["department"]` nói
    về quyền quản lý DANH MỤC phòng ban (ai được sửa tên phòng, ai được xóa) và
    nó không có chiều phòng ban, nên bậc `dept` ở đó rơi về "chỉ phòng do chính
    tôi tạo" — dùng làm thước thì người quản lý nhân sự phòng Kế toán không gán
    nổi chính phòng Kế toán.
    """
    bac = _bac_rong_nhat(profile, "employee", "write")
    if bac is None:
        return set()
    if bac == "all":
        return None
    if bac == "company":
        company_id = profile.get("company_id") or 0
        if not company_id:
            return set()
        return {row[0] for row in
                db.query(Department.id)
                .filter(Department.company_id == company_id).all()}

    #  Bậc `dept` (và hẹp hơn): đúng những phòng CHÍNH NGƯỜI ĐÓ có chân, cộng
    #  các phòng được cấp thêm đích danh ở màn Phân quyền (`tab_user_scope`).
    duoc = {x for x in (profile.get("dept_ids") or []) if x}
    if profile.get("dept_id"):
        duoc.add(profile["dept_id"])
    for grant in profile.get("grants", []):
        cap_them = (grant.get("scope") or {}).get("inc", {}).get("department") or []
        duoc.update(x for x in cap_them if x)
    return duoc


def chan_gan_phong_ngoai_tam(db: Session, department_ids: list[int], actor,
                             profile: dict) -> None:
    """L2 — chỉ gán được phòng nằm trong tầm của chính người thao tác.

    Không có chốt này thì người quản lý phạm vi *phòng ban* dựng ra được một
    người có tầm nhìn rộng hơn mình, rồi nhờ người đó xem hộ.
    """
    if not department_ids:
        return

    duoc = phong_ban_gan_duoc(db, profile)
    if duoc is None:
        return   # phạm vi *tất cả* — không siết

    ngoai_tam = sorted(set(department_ids) - duoc)
    if ngoai_tam:
        ten = {row[0]: row[1] for row in
               db.query(Department.id, Department.name)
               .filter(Department.id.in_(ngoai_tam)).all()}
        nhan = ", ".join(f"«{ten.get(i, i)}»" for i in ngoai_tam)
        raise HTTPException(
            403, f"Không gán được phòng ban mà chính bạn không có phạm vi trên đó: {nhan}. "
                 "Nhờ người phụ trách phòng đó thao tác.")


def dat_phong_ban(db: Session, employee: Employee, department_ids: list[int],
                  actor: int, *, phong_chinh: int | None = None) -> list[int]:
    """Đặt LẠI toàn bộ danh sách phòng ban của một nhân sự.

    Đây là chỗ DUY NHẤT ghi vào `tab_employee_department`, và cũng là chỗ duy
    nhất cập nhật `tab_employee.department_id` — hai thứ đó phải luôn khớp nhau,
    tách ra hai nơi ghi là sớm muộn lệch.

    `phong_chinh` bỏ trống thì lấy phần tử ĐẦU của danh sách. Danh sách rỗng =
    gỡ khỏi mọi phòng (nhân sự chưa phân công), hợp lệ.

    ⚠️ KHÔNG gọi thẳng từ controller — gọi ba hàm `chan_*` trước.
    """
    sach = list(dict.fromkeys(int(x) for x in department_ids if x))
    _kiem_phong_co_that(db, employee, sach)

    chinh = phong_chinh if phong_chinh in sach else (sach[0] if sach else 0)

    db.query(EmployeeDepartment).filter(
        EmployeeDepartment.employee_id == employee.id).delete(synchronize_session=False)
    for department_id in sach:
        db.add(EmployeeDepartment(
            employee_id=employee.id, department_id=department_id,
            is_primary=(department_id == chinh),
            created_by=actor, updated_by=actor))

    #  Giữ cột cũ khớp với phòng chính — 12 chỗ trong mã vẫn đọc nó.
    employee.department_id = chinh
    db.flush()

    #  Phạm vi dữ liệu của người này vừa đổi; hồ sơ quyền cache 60 giây nên
    #  không xóa là họ nhìn bằng tầm cũ suốt một phút.
    from app.core.auth import perm_cache_clear
    from app.modules.user.model import User

    for row in db.query(User.id).filter(User.employee_id == employee.id).all():
        perm_cache_clear(row[0])

    return [chinh] + [x for x in sach if x != chinh] if chinh else sach
