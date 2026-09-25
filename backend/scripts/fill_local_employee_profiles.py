"""Điền cho ĐỦ hồ sơ nhân sự + quyền văn bản trên DB LOCAL — để bấm «Tạo văn bản»
không vấp lỗi thiếu thông tin người dùng (đại ca yêu cầu 25/09/2026).

Chạy:  docker compose exec -T api python -m scripts.fill_local_employee_profiles           # chạy thử, chỉ in
       docker compose exec -T api python -m scripts.fill_local_employee_profiles --apply   # ghi thật

CHỈ DÙNG Ở MÁY LOCAL. Chạy lại được: ô nào đã có giá trị hợp lệ thì GIỮ NGUYÊN,
chỉ điền ô đang trống / trỏ tới bản ghi không tồn tại. Giá trị cá nhân (ngày
sinh, ngày vào làm, số điện thoại) là dữ liệu MẪU, sinh cố định theo id — chạy
hai lần ra cùng một kết quả.

Vì sao cần: 238/272 nhân sự `company_id = 0` → form tạo văn bản không có pháp
nhân mặc định; 20 người chưa có phòng ban; 258 tài khoản thiếu `doc_folder.read`
(seed đã định cấp cho MỌI vai trò nhưng DB đang chạy không tự đồng bộ — D-018);
23 tài khoản vai trò thu mua không có quyền văn bản nào.

Cố ý KHÔNG đụng: email (thư thông báo thật sẽ bay tới địa chỉ bịa), trường
nhạy cảm (CCCD, ngân hàng, MST), tên chức vụ đang có.
"""
import sys
from datetime import date, timedelta

import app.core.all_models  # noqa: F401 — nạp đủ model, không thì mapper User gãy
from app.core.database import SessionLocal
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee import constants as K
from app.modules.employee.model import Employee
from app.modules.employee.position_model import JobPosition
from app.modules.role.model import Permission, Role
from app.modules.user.model import User, UserRole

#  Phòng mang tên công ty con → pháp nhân đó. Phòng dùng chung (Kế toán, Nhân
#  sự, IT…) → DEGO Holding. Khóa theo MÃ phòng/pháp nhân, không theo id.
DEPT_TO_COMPANY_CODE = {
    "PBA004": "N2SBIO",        # N2SBIO
    "PBA006": "ABA",           # ABA Chemical
    "PBA008": "ICARE",         # Icare
    "PBA009": "IDA",           # IDA Global
    "PBA010": "BAMBOO",        # Bamboo
    "PBA011": "NPP DR.XANH",   # Dr.Xanh
}
DEFAULT_COMPANY_CODE = "DEGO"

#  Văn thư từng pháp nhân: mã nhân sự `VT<hậu tố>` → mã pháp nhân.
CLERK_SUFFIX_TO_COMPANY_CODE = {
    "IDA": "IDA", "ABA": "ABA", "ICARE": "ICARE", "DRXANH": "NPP DR.XANH",
    "HKDDRXANH": "HỘ KD DR.XANH", "BAMBOO": "BAMBOO", "N2SBIO": "N2SBIO",
    "NNDEGO": "NN DEGO", "NNABA": "NN ABA", "AGRIPLANT": "AGRIPLANT", "SAM": "SAM",
    "AGC": "AGC", "DEGOHOLDING": "DEGO",
}
TEST_CLERK_TO_COMPANY_CODE = {"TESTMEDEGO": "DEGO", "TESTCONAGRI": "AGRIPLANT"}

#  Người chưa có phòng: văn thư → Hành chính; quản trị/HDSD → IT; demo thu mua → phòng demo.
DEPT_FOR_NO_DEPT = {
    "clerk": "PBA016",      # Hành chính
    "admin": "PBA014",      # Lập trình & IT nội bộ
    "DEMO_PURCHASER": "DEMODEPT",
    "default": "PBA016",
}

#  Thứ bậc để chọn trưởng phòng khi phòng chưa khai `manager_id`.
HEAD_KEYWORDS = [("giám đốc", 5), ("trưởng phòng", 4), ("trưởng bộ phận", 4),
                 ("quyền trưởng", 3), ("quản lý", 3), ("phó phòng", 2)]


def _rank(position: str) -> int:
    text = (position or "").lower()
    return max((r for k, r in HEAD_KEYWORDS if k in text), default=0)


def _job_level(position: str) -> int:
    text = (position or "").lower()
    if "giám đốc" in text:
        return K.JOB_LEVEL_DIRECTOR
    if "phó phòng" in text:
        return K.JOB_LEVEL_DEPUTY_MANAGER
    if "trưởng" in text or "quản lý" in text or "quản trị" in text or text == "admin":
        return K.JOB_LEVEL_MANAGER
    return K.JOB_LEVEL_STAFF


def _gender(full_name: str) -> int:
    #  Tên đệm «Thị» gần như chắc là nữ; còn lại để Nam — dữ liệu mẫu, sửa tay được.
    return K.GENDER_FEMALE if " thị " in f" {(full_name or '').lower()} " else K.GENDER_MALE


def _sample_dob(emp_id: int) -> date:
    return date(1975, 1, 1) + timedelta(days=(emp_id * 997) % (25 * 365))


def _sample_hire(emp_id: int) -> date:
    return date(2016, 1, 1) + timedelta(days=(emp_id * 373) % (9 * 365))


def _sample_phone(emp_id: int) -> str:
    return f"09{(emp_id * 7919) % 100000000:08d}"


def fill_employees(db, log) -> None:
    companies = {c.code: c.id for c in db.query(Company).all()}
    company_ids = set(companies.values())
    depts = {d.id: d for d in db.query(Department).all()}
    dept_by_code = {d.code: d for d in depts.values()}
    positions = {p.name: p.id for p in db.query(JobPosition).all()}
    emps = db.query(Employee).all()

    for e in emps:
        code = (e.code or "").upper()
        # ── phòng ban
        if e.department_id not in depts:
            if code.startswith("VT") or code.startswith("TEST"):
                key = "clerk"
            elif code in ("ADMIN", "DEGOADMIN", "HDSD0001") or (e.position or "") == "Admin":
                key = "admin"
            elif code in DEPT_FOR_NO_DEPT:
                key = code
            else:
                key = "default"
            dept = dept_by_code[DEPT_FOR_NO_DEPT[key]]
            log(f"  phòng   #{e.id} {e.code:14s} {e.full_name[:28]:28s} → {dept.name}")
            e.department_id = dept.id
        # ── pháp nhân
        if e.company_id not in company_ids:
            if code.startswith("VT") and code[2:] in CLERK_SUFFIX_TO_COMPANY_CODE:
                ccode = CLERK_SUFFIX_TO_COMPANY_CODE[code[2:]]
            elif code in TEST_CLERK_TO_COMPANY_CODE:
                ccode = TEST_CLERK_TO_COMPANY_CODE[code]
            else:
                ccode = DEPT_TO_COMPANY_CODE.get(depts[e.department_id].code, DEFAULT_COMPANY_CODE)
            e.company_id = companies[ccode]
        # ── chức vụ: chỉ NỐI khóa khi tên đang có khớp đúng danh mục, không đổi tên
        if not e.position_id and e.position in positions:
            e.position_id = positions[e.position]
        # ── thông tin cá nhân mẫu
        if not e.gender:
            e.gender = _gender(e.full_name)
        if not e.date_of_birth:
            e.date_of_birth = _sample_dob(e.id)
        if not e.hire_date:
            e.hire_date = _sample_hire(e.id)
        if not e.phone:
            e.phone = _sample_phone(e.id)
        if not e.job_level:
            e.job_level = _job_level(e.position)
        if not e.employment_type:
            e.employment_type = K.EMPLOYMENT_FULL_TIME
    db.flush()

    # ── trưởng phòng + quản lý trực tiếp
    members: dict[int, list[Employee]] = {}
    for e in emps:
        members.setdefault(e.department_id, []).append(e)
    by_id = {e.id: e for e in emps}
    for dept in depts.values():
        if not dept.manager_id or dept.manager_id not in by_id:
            ranked = sorted(members.get(dept.id, []), key=lambda x: (-_rank(x.position), x.id))
            if ranked and _rank(ranked[0].position) > 0:
                dept.manager_id = ranked[0].id
                log(f"  trưởng  {dept.name:24s} → #{ranked[0].id} {ranked[0].full_name}")
    for e in emps:
        head = depts[e.department_id].manager_id
        if e.manager_id or not head or head == e.id:
            continue
        #  Chặn vòng: trưởng phòng này không được (gián tiếp) đang báo cáo cho e.
        cur, seen = by_id.get(head), set()
        while cur is not None and cur.manager_id and cur.id not in seen:
            seen.add(cur.id)
            cur = by_id.get(cur.manager_id)
        if e.id in seen:
            continue
        e.manager_id = head
    db.flush()


def fill_permissions(db, log) -> set[int]:
    """Trả id user bị đổi quyền — để xóa cache quyền."""
    touched: set[int] = set()
    # 1) `doc_folder.read` cho MỌI vai trò chưa có — đúng ý seed (vòng setdefault cuối seed.py).
    for role in db.query(Role).all():
        has = db.query(Permission).filter(Permission.role_id == role.id,
                                          Permission.entity == "doc_folder").first()
        if has is None:
            db.add(Permission(role_id=role.id, entity="doc_folder", can_read=True, scope="all"))
            log(f"  quyền   vai trò {role.code:22s} + doc_folder.read")
        elif not has.can_read:
            has.can_read = True
            log(f"  quyền   vai trò {role.code:22s} bật doc_folder.read")
    # 2) Ai cũng giữ vai trò nền `employee` (Nhân viên thường) — nó mang
    #    document.read/create/write (own) + doc_type.read. Vai trò thu mua thuần
    #    không có quyền văn bản nào; thêm vai trò nền thay vì nhét quyền văn bản
    #    vào vai trò thu mua (luật "một vai trò = một chức năng", 19/09/2026).
    base = db.query(Role).filter(Role.code == "employee").one()
    for user in db.query(User).filter(User.is_active.is_(True)).all():
        role_ids = {ur.role_id for ur in db.query(UserRole).filter(UserRole.user_id == user.id)}
        if base.id not in role_ids:
            db.add(UserRole(user_id=user.id, role_id=base.id))
            touched.add(user.id)
            log(f"  quyền   tài khoản #{user.id} {user.email or '':28s} + vai trò employee")
    db.flush()
    return touched


def main() -> None:
    apply = "--apply" in sys.argv
    db = SessionLocal()
    lines: list[str] = []
    try:
        fill_employees(db, lines.append)
        touched = fill_permissions(db, lines.append)
        print("\n".join(lines))
        print(f"\n{len(lines)} dòng thay đổi (chưa kể thông tin cá nhân mẫu điền vào ô trống).")
        if apply:
            db.commit()
            #  Cache quyền nằm trong tiến trình API (60 giây) — script không xóa hộ
            #  được; còn map quyền ở trình duyệt thì chỉ đổi khi đăng nhập lại.
            print(f"ĐÃ GHI ({len(touched)} tài khoản thêm vai trò). Người đang đăng nhập "
                  "phải đăng xuất/đăng nhập lại để nhận quyền mới.")
        else:
            db.rollback()
            print("CHẠY THỬ — chưa ghi gì. Thêm --apply để ghi.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
