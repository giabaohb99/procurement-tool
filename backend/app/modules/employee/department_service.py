"""KIÊM NHIỆM PHÒNG BAN — đọc, ghi, và ba chốt chặn chống vượt quyền (CR-167).

duoc-CR-755: kiêm nhiệm nay nằm ở `tab_employee_concurrent` (`concurrent_service.py`) và dùng lại ba chốt L1/L2/L3
của tệp này (L2 theo loại dòng, duoc-CR-756: loại Phòng ban theo CẶP phòng + công ty `pair_in_write_scope`, loại
Công ty theo công ty `company_in_write_scope`; gộp ở `block_out_of_scope_concurrent`). `tab_employee_department` CHỈ còn dòng phòng
CHÍNH — đường ghi duy nhất là `set_primary_department`.

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

from app.core.hr_concurrent_codes import ConcurrentKind
from app.modules.department.model import Department

from .department_model import EmployeeDepartment
from .model import Employee


def departments_of(db: Session, employee_id: int) -> list[int]:
    """Phòng CHÍNH của một nhân sự theo bảng `tab_employee_department` (danh sách tối đa một phần tử).

    Phòng kiêm nhiệm không nằm ở đây từ duoc-CR-755 — xem `concurrent_service`.
    """
    if not employee_id:
        return []
    rows = (db.query(EmployeeDepartment)
            .filter(EmployeeDepartment.employee_id == employee_id)
            .order_by(EmployeeDepartment.is_primary.desc(),
                      EmployeeDepartment.department_id.asc())
            .all())
    return [row.department_id for row in rows if row.department_id]


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


def _write_grants(profile: dict) -> list[dict]:
    """Các grant có `employee.write` — mỗi grant là một nguồn quyền ghi ĐỘC LẬP (hợp theo OR, như `scope_condition`)."""
    return [grant for grant in profile.get("grants", [])
            if (grant["perms"].get("employee") or {}).get("write")]


def _actor_companies(profile: dict) -> set[int]:
    """Công ty người thao tác "có chân": công ty chính + công ty KIÊM NHIỆM đang hiệu lực (loại Công ty, duoc-CR-756).

    Khóa `concurrent_companies` do `core/auth.get_perm_profile` dựng (chỉ dòng hiệu lực + bật công tắc phạm vi,
    khác công ty chính). Bỏ số 0.
    """
    return {int(c) for c in [profile.get("company_id"), *(profile.get("concurrent_companies") or [])] if c}


def _company_ids(values) -> list[int]:
    """Giá trị số trong một ô "công ty" của grant (`auth.py` giữ nguyên chuỗi rác; rác bị bỏ như `_parse_int_values`)."""
    ids: list[int] = []
    for value in values or []:
        try:
            ids.append(int(value))
        except (TypeError, ValueError):
            continue
    return ids


def grant_writes_company(grant: dict, company_id: int, reach: set[int]) -> bool:
    """MỘT grant `employee.write` có ghi được ở công ty `company_id` không — khớp `core/scoping._explicit_cond`.

    Phần theo BẬC: `all` không ràng công ty; mọi bậc khác cần `company_id` thuộc `reach` (công ty chính ∪ công ty
    kiêm nhiệm). Phần theo Ô của grant (áp cho MỌI bậc, AND như `_explicit_cond`): "Chỉ trong công ty" (`inc.company`)
    có giá trị thì `company_id` phải nằm trong đó — ô có giá trị mà không giá trị nào dùng được thì CHẶN (không nở ra
    bằng bậc vai trò); "Loại trừ công ty" (`exc.company`) thì `company_id` không được nằm trong đó. Cấu hình `all` +
    "Chỉ trong công ty A" là cách duy nhất để một người có phạm vi nhiều pháp nhân hẹp — bỏ qua ô này là cho họ gán
    kiêm nhiệm sang công ty tùy ý (duoc-CR-756, rà mã C1).
    """
    scope_name = grant["perms"]["employee"].get("scope", "all")
    if scope_name != "all" and company_id not in reach:
        return False
    box = grant.get("scope") or {}
    raw_inc = (box.get("inc") or {}).get("company") or []
    inc = _company_ids(raw_inc)
    if raw_inc and not inc:
        return False
    if inc and company_id not in inc:
        return False
    return company_id not in _company_ids((box.get("exc") or {}).get("company"))


def pair_in_write_scope(db: Session, profile: dict, department_id: int, company_id: int) -> bool:
    """L2 theo CẶP (phòng, công ty) — người này có ghi được vào cặp đó không (duoc-CR-755, theo bậc ở duoc-CR-756).

    Dùng cho kiêm nhiệm loại Phòng ban (cặp = phòng + công ty chính của hồ sơ) VÀ cho đổi phòng CHÍNH của hồ sơ
    (cặp = phòng mới + công ty của HỒ SƠ ĐÍCH). Đo trên `employee.write`, xét TỪNG grant rồi hợp (OR) — KHÔNG lấy
    bậc rộng nhất. Công ty của cặp phải qua `grant_writes_company` (bậc + ô "Chỉ trong công ty" / "Loại trừ công ty"
    của chính grant đó), rồi:
    - `all` / `company` → được;
    - `dept` trở xuống → phòng nằm trong `dept_ids`, hoặc trong ô "Phòng ban được xem" khi `company_id` = công ty chính.
    `company_id = 0` coi như công ty chính của người thao tác (dòng cũ của nhân sự chưa gắn pháp nhân; người sửa
    được hồ sơ đó đã qua `employee_in_scope`).

    ⚠️ Ô "Phòng ban được xem" (`inc.department`) CHỈ phủ công ty chính — chặt hơn phạm vi ĐỌC,
    cố ý: gán phòng là mở rộng tầm nhìn của người KHÁC, không được dựa vào một ô chọn
    không mang công ty. `db` giữ trong chữ ký cho đồng dạng với các chốt L2 khác.
    """
    grants = _write_grants(profile)
    if not grants:
        return False
    own_company = profile.get("company_id") or 0
    if not company_id:
        company_id = own_company
    reach = _actor_companies(profile)
    base_ids = {x for x in (profile.get("dept_ids") or []) if x}
    if profile.get("dept_id"):
        base_ids.add(profile["dept_id"])

    for grant in grants:
        if not grant_writes_company(grant, company_id, reach):
            continue
        if grant["perms"]["employee"].get("scope", "all") in ("all", "company"):
            return True
        extra_ids = {x for x in ((grant.get("scope") or {}).get("inc", {}).get("department") or []) if x}
        if department_id in base_ids or (company_id == own_company and department_id in extra_ids):
            return True
    return False


def company_in_write_scope(profile: dict, company_id: int) -> bool:
    """L2 cho kiêm nhiệm loại CÔNG TY — gán công ty B mở cả công ty B cho người khác, nên chặt hơn loại Phòng ban:
    chỉ grant `employee.write` bậc `all` hoặc `company` mà B qua `grant_writes_company` (bậc + ô công ty của chính
    grant đó) — xét từng grant rồi hợp. Bậc phòng ban trở xuống KHÔNG đủ (duoc-CR-756)."""
    reach = _actor_companies(profile)
    return any(grant["perms"]["employee"].get("scope", "all") in ("all", "company")
               and grant_writes_company(grant, company_id, reach)
               for grant in _write_grants(profile))


def _pair_label(db: Session, pairs: list[tuple[int, int]]) -> str:
    """`"Phòng" (Công ty), ...` cho câu báo lỗi; phòng 0 (loại Công ty) chỉ ghi tên công ty."""
    from app.modules.company.model import Company

    dept_names = {row[0]: row[1] for row in db.query(Department.id, Department.name)
                  .filter(Department.id.in_({d for d, _ in pairs if d})).all()}
    company_names = {row[0]: row[1] for row in db.query(Company.id, Company.name)
                     .filter(Company.id.in_({c for _, c in pairs})).all()}
    return ", ".join(f'"{dept_names.get(d, d)}" ({company_names.get(c, c)})' if d else f'"{company_names.get(c, c)}"'
                     for d, c in pairs)


def block_out_of_scope_primary_department(db: Session, department_id: int, target_company_id: int,
                                          profile: dict) -> None:
    """L2 cho đổi phòng CHÍNH — phòng mới phải nằm trong tầm GHI của người thao tác TRÊN CÔNG TY CỦA HỒ SƠ ĐÍCH.

    duoc-CR-755 (C1): đo bằng cặp (phòng mới, công ty ĐÍCH), không chỉ ID phòng. Từ khi kiêm nhiệm khác công ty mở
    quyền ghi hồ sơ công ty B qua cặp (X, B), chỉ so ID phòng thì người có (SH dùng chung, A) đẩy được nhân sự công ty
    B sang (SH, B) — cặp họ không phủ. `target_company_id` = công ty của hồ sơ SAU lần lưu (ô mới nếu có đổi pháp
    nhân, không thì công ty hiện tại). Gọi ở MỌI đường đổi phòng chính: PATCH hồ sơ, nhập Excel, hoàn tác lô nhập,
    Áp quá trình công tác.
    """
    if not department_id:
        return
    company_id = target_company_id or profile.get("company_id") or 0
    if not pair_in_write_scope(db, profile, department_id, target_company_id or 0):
        raise HTTPException(
            403, "Không gán được phòng ban mà chính bạn không có phạm vi trên đó: "
                 f"{_pair_label(db, [(department_id, company_id)])}. Nhờ người phụ trách phòng đó thao tác.")
    #  Phòng RIÊNG của một công ty khác (không phải phòng dùng chung, `company_id = 0`): người thao tác cũng phải với
    #  tới phòng đó ở chính công ty của nó — như L2 cũ (chỉ gán được phòng trong tầm mình). Phạm vi `all` qua được
    #  và bị L3 (`_check_departments_exist`) chặn 400 vì phòng thuộc pháp nhân khác với hồ sơ.
    owner = db.query(Department.company_id).filter(Department.id == department_id).scalar() or 0
    if owner and owner != company_id and not pair_in_write_scope(db, profile, department_id, owner):
        raise HTTPException(
            403, "Không gán được phòng ban mà chính bạn không có phạm vi trên đó: "
                 f"{_pair_label(db, [(department_id, owner)])}. Nhờ người phụ trách phòng đó thao tác.")


def block_out_of_scope_concurrent(db: Session, specs: list[tuple[int, int, int]], profile: dict) -> None:
    """L2 cho dòng kiêm nhiệm — `specs` = `[(kind, company_id, department_id), ...]`; 403 nêu tên nếu có dòng ngoài tầm.

    Loại Phòng ban đo theo CẶP (`pair_in_write_scope`), loại Công ty đo theo công ty (`company_in_write_scope`,
    chặt hơn). Sửa dòng thì truyền cả bộ CŨ lẫn MỚI.
    """
    bad_pairs = [(d, c) for k, c, d in specs
                 if k == ConcurrentKind.DEPARTMENT and d and not pair_in_write_scope(db, profile, d, c)]
    if bad_pairs:
        raise HTTPException(
            403, "Không gán được kiêm nhiệm ở phòng ban mà chính bạn không có phạm vi ghi trên đó: "
                 f"{_pair_label(db, bad_pairs)}. Nhờ người phụ trách phòng đó thao tác.")
    bad_companies = [(0, c) for k, c, _d in specs
                     if k == ConcurrentKind.COMPANY and not company_in_write_scope(profile, c)]
    if bad_companies:
        raise HTTPException(
            403, "Không gán được kiêm nhiệm ở công ty mà bạn không có phạm vi ghi toàn công ty: "
                 f"{_pair_label(db, bad_companies)}. Nhờ người phụ trách công ty đó thao tác.")


def check_primary_belongs(db: Session, employee: Employee) -> None:
    """L3 cho phòng chính HIỆN CÓ của hồ sơ — gọi khi pháp nhân vừa đổi mà ô phòng ban không đổi theo.

    Đổi pháp nhân A -> B mà phòng chính vẫn là phòng riêng của A thì 400 (cùng câu với `set_primary_department`),
    người dùng chọn phòng của B hoặc bỏ trống ô phòng ban rồi lưu lại.
    """
    #  Đọc phòng chính từ BẢNG (như `detach_other_company_departments` cũ), không từ cột: chạy thật hai nơi luôn
    #  khớp; hồ sơ chưa có dòng nào trong bảng (dữ liệu nhập thẳng cột) thì không có gì để chặn.
    current = departments_of(db, employee.id)
    if current:
        _check_departments_exist(db, employee, current)


def set_primary_department(db: Session, employee: Employee, department_id: int, actor: int) -> int:
    """Đặt phòng CHÍNH của một nhân sự (`0` = chưa phân công). Trả id phòng chính sau khi ghi.

    Đây là chỗ DUY NHẤT ghi vào `tab_employee_department` (nay chỉ chứa một dòng phòng chính), và cũng là chỗ
    duy nhất cập nhật `tab_employee.department_id` — hai thứ đó phải luôn khớp nhau, tách ra hai nơi ghi là
    sớm muộn lệch.

    ⚠️ KHÔNG gọi thẳng từ controller — gọi các hàm `block_*` trước.
    """
    primary = int(department_id or 0)
    _check_departments_exist(db, employee, [primary] if primary else [])

    db.query(EmployeeDepartment).filter(
        EmployeeDepartment.employee_id == employee.id).delete(synchronize_session=False)
    if primary:
        db.add(EmployeeDepartment(employee_id=employee.id, department_id=primary, is_primary=True,
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

    return primary
