"""BẢY CÁCH CHỌN NGƯỜI DUYỆT (I03).

Trả về **danh sách employee_id**, đã bỏ trùng và giữ nguyên thứ tự khai — thứ tự
có nghĩa với bước `lần lượt`.

Nguyên tắc chung: không tìm được ai thì trả danh sách RỖNG, không nổ và không tự
bịa ra người. Việc xử lý danh sách rỗng là của `instance_service` theo cột
`on_no_approver` của bước — và ở đó **cố ý không có lựa chọn "tự động duyệt
qua"**.
"""
from sqlalchemy.orm import Session

from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee

from .flow_model import (APPROVER_COMPANY_REP, APPROVER_DEPT_HEAD,
                         APPROVER_DEPT_HEAD_OF, APPROVER_EMPLOYEE,
                         APPROVER_FIELD, APPROVER_LEVEL_UP, APPROVER_ROLE)

#  Lên quá số cấp này thì dừng — cây phòng ban khai vòng (A là cha của B, B là
#  cha của A) sẽ treo vòng lặp, mà dữ liệu khai tay thì chuyện đó xảy ra thật.
MAX_LEVEL_UP = 10


def resolve(db: Session, node, subject: dict, submitter_employee_id: int | None) -> list[int]:
    """Ai phải xử lý bước này."""
    kind = node.approver_kind

    if kind == APPROVER_EMPLOYEE:
        ids = _refs_as_ints(node.approver_ref)
    elif kind == APPROVER_ROLE:
        ids = _theo_vai_tro(db, node.approver_ref)
    elif kind == APPROVER_DEPT_HEAD:
        ids = _truong_bo_phan(db, submitter_employee_id, subject)
    elif kind == APPROVER_LEVEL_UP:
        ids = _len_n_cap(db, submitter_employee_id, subject, node.approver_ref)
    elif kind == APPROVER_COMPANY_REP:
        ids = _dai_dien_phap_nhan(db, subject)
    elif kind == APPROVER_FIELD:
        ids = _tu_o_tren_phieu(subject, node.approver_ref)
    elif kind == APPROVER_DEPT_HEAD_OF:
        ids = _truong_cua_phong_chi_dinh(db, node.approver_ref)
    else:
        ids = []

    return _chi_nguoi_dang_lam_viec(db, ids)


def _chi_nguoi_dang_lam_viec(db: Session, ids: list[int]) -> list[int]:
    """Bỏ người đã nghỉ và bỏ trùng, GIỮ NGUYÊN thứ tự khai.

    Giao việc cho người đã tắt trạng thái là phiếu nằm im vĩnh viễn: không ai
    đăng nhập được vào tài khoản đó để bấm.
    """
    if not ids:
        return []
    dang_lam = {
        row[0] for row in
        db.query(Employee.id).filter(Employee.id.in_(ids), Employee.is_active.is_(True)).all()
    }
    ket_qua: list[int] = []
    for employee_id in ids:
        if employee_id in dang_lam and employee_id not in ket_qua:
            ket_qua.append(employee_id)
    return ket_qua


def _refs_as_ints(raw: str) -> list[int]:
    ids = []
    for phan in (raw or "").split(","):
        phan = phan.strip()
        if phan.isdigit():
            ids.append(int(phan))
    return ids


def _theo_vai_tro(db: Session, raw: str) -> list[int]:
    from app.modules.role.model import Role, UserRole
    from app.modules.user.model import User

    codes = [phan.strip() for phan in (raw or "").split(",") if phan.strip()]
    if not codes:
        return []

    role_ids = [row[0] for row in db.query(Role.id).filter(Role.code.in_(codes)).all()]
    if not role_ids:
        return []
    user_ids = [row[0] for row in
                db.query(UserRole.user_id).filter(UserRole.role_id.in_(role_ids)).all()]
    if not user_ids:
        return []
    return [
        row[0] for row in
        db.query(User.employee_id)
        .filter(User.id.in_(user_ids), User.is_active.is_(True), User.employee_id.isnot(None))
        .all()
        if row[0]
    ]


def _phong_cua_nguoi_nop(db: Session, submitter_employee_id: int | None,
                         subject: dict) -> Department | None:
    """Phòng ban để tính cấp trên: ưu tiên phòng của NGƯỜI NỘP, sau mới tới phiếu.

    Thứ tự này quan trọng: thu mua lập phiếu hộ bộ phận khác thì "trưởng bộ phận
    người nộp" phải là trưởng của thu mua, không phải trưởng phòng ghi trên
    phiếu.
    """
    if submitter_employee_id:
        employee = db.get(Employee, submitter_employee_id)
        if employee and employee.department_id:
            return db.get(Department, employee.department_id)
    if subject.get("department_id"):
        return db.get(Department, int(subject["department_id"]))
    return None


def _truong_bo_phan(db: Session, submitter_employee_id: int | None, subject: dict) -> list[int]:
    phong = _phong_cua_nguoi_nop(db, submitter_employee_id, subject)
    if phong is None or not phong.manager_id:
        return []
    #  Trưởng bộ phận tự nộp phiếu thì bước này rỗng — để `on_no_approver` của
    #  bước quyết định (thường là đẩy lên cấp trên). Trả về chính họ là tự duyệt.
    if phong.manager_id == submitter_employee_id:
        return []
    return [phong.manager_id]


def _truong_cua_phong_chi_dinh(db: Session, raw: str) -> list[int]:
    """Trưởng bộ phận của những phòng ban ĐƯỢC KHAI THẲNG trong bước.

    Khác `_truong_bo_phan` ở đúng một chỗ, và đó là chỗ quan trọng: hàm kia bám
    theo phòng của NGƯỜI NỘP, hàm này bám theo phòng GHI TRONG LUỒNG. Nhờ vậy
    khai được những bước có thật mà trước đây không khai nổi — «đơn nghỉ phép của
    mọi phòng đều qua trưởng phòng Nhân sự», «hợp đồng qua trưởng phòng Pháp chế».

    Khai đích danh một CON NGƯỜI cũng ra kết quả giống hệt hôm nay, nhưng người
    đó chuyển việc là luồng trỏ sai mà không có gì báo. Trỏ vào GHẾ thì đổi người
    ngồi ghế là luồng tự đi theo.

    Khai được NHIỀU phòng: một bước có thể cần cả trưởng Nhân sự lẫn trưởng Tài
    chính cùng ký. Giữ nguyên thứ tự khai vì bước «lần lượt» đọc thứ tự đó.
    """
    phong_ids = _refs_as_ints(raw)
    if not phong_ids:
        return []

    #  Một câu truy vấn cho cả danh sách, rồi xếp lại theo ĐÚNG thứ tự khai —
    #  `IN (...)` không hứa thứ tự trả về.
    truong_theo_phong = {
        row[0]: row[1] for row in
        db.query(Department.id, Department.manager_id)
        .filter(Department.id.in_(phong_ids)).all()
    }
    return [truong_theo_phong[pid] for pid in phong_ids
            if truong_theo_phong.get(pid)]


def _len_n_cap(db: Session, submitter_employee_id: int | None, subject: dict,
               raw: str) -> list[int]:
    so_cap = int(raw) if (raw or "").strip().isdigit() else 1
    so_cap = max(1, min(so_cap, MAX_LEVEL_UP))

    phong = _phong_cua_nguoi_nop(db, submitter_employee_id, subject)
    da_qua: set[int] = set()

    for _ in range(so_cap):
        if phong is None or phong.id in da_qua:
            #  Đã đi qua phòng này rồi = cây khai vòng. Dừng, đừng quay tiếp.
            return []
        da_qua.add(phong.id)
        phong = db.get(Department, phong.parent) if phong.parent else None

    if phong is None or not phong.manager_id:
        return []
    return [phong.manager_id]


def _dai_dien_phap_nhan(db: Session, subject: dict) -> list[int]:
    company_id = subject.get("company_id")
    if not company_id:
        return []
    company = db.get(Company, int(company_id))
    if company is None or not company.legal_representative_id:
        return []
    return [company.legal_representative_id]


def _tu_o_tren_phieu(subject: dict, raw: str) -> list[int]:
    """Người duyệt ghi sẵn trên chính phiếu — vd ô "Người ký" của văn bản."""
    ten_o = (raw or "").strip()
    if not ten_o:
        return []
    gia_tri = subject.get(ten_o)
    if gia_tri in (None, "", 0):
        return []
    if isinstance(gia_tri, (list, tuple)):
        return [int(item) for item in gia_tri if str(item).isdigit()]
    return [int(gia_tri)] if str(gia_tri).isdigit() else []
