"""KIÊM NHIỆM — đọc, ghi, và các chốt chặn (duoc-CR-755). Bảng: `tab_employee_concurrent`.

⚠️ Thêm / sửa một dòng còn hiệu lực + bật `counts_scope` là MỞ RỘNG tầm nhìn dữ liệu của
người đó (hồ sơ quyền đọc bảng này mỗi request). Nên mọi cửa ghi đều qua đủ ba chốt của
`department_service`:

**L1** không tự sửa kiêm nhiệm của chính mình (kể cả quản trị).
**L2** chỉ gán cặp (phòng, công ty) nằm trong phạm vi GHI của người thao tác (`pair_in_write_scope`);
  sửa cặp thì đo cả cặp cũ lẫn cặp mới. Bật lại công tắc, nới ngày cũng là mở rộng nên luôn qua L2.
**L3** công ty + phòng có thật và phòng phục vụ công ty đó (`check_concurrent_target`).

Dòng được sửa TẠI CHỖ (không xóa-chèn lại) để id bền — tệp quyết định gắn theo id dòng.
"""
from datetime import date

from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.vn_time import vn_today
from app.modules.department.model import Department, DepartmentCompany

from . import department_service, position_service
from .concurrent_model import EmployeeConcurrent
from .concurrent_schema import ORDER_ERROR, ConcurrentIn, ConcurrentPatch
from .model import Employee

#  Trần dòng / nhân sự (kể cả dòng đã hết hạn — lịch sử kiêm nhiệm tính chung).
MAX_ROWS = 30


# ── Đọc ─────────────────────────────────────────────────────────────────────

def effective_filter(today: date):
    """Điều kiện SQL "còn hiệu lực tại `today`" — MỘT định nghĩa cho cả hồ sơ quyền lẫn danh sách.

    Khớp `hr_concurrent_codes.get_concurrent_status` == ACTIVE: từ ngày trống = đã có hiệu lực,
    đến ngày trống = chưa kết thúc, hai đầu bao gồm.
    """
    C = EmployeeConcurrent
    return and_(or_(C.from_date.is_(None), C.from_date <= today),
                or_(C.to_date.is_(None), C.to_date >= today))


def active_concurrent_rows(db: Session, employee_id: int, today: date | None = None, *,
                           counts_scope_only: bool = False) -> list[EmployeeConcurrent]:
    """Các dòng còn hiệu lực của một nhân sự — MỘT truy vấn (hồ sơ quyền, phase 03/05 dùng lại)."""
    if not employee_id:
        return []
    q = db.query(EmployeeConcurrent).filter(
        EmployeeConcurrent.employee_id == employee_id, effective_filter(today or vn_today()))
    if counts_scope_only:
        q = q.filter(EmployeeConcurrent.counts_scope.is_(True))
    return q.order_by(EmployeeConcurrent.id.asc()).all()


def same_company_department_ids(db: Session, emp: Employee) -> list[int]:
    """Phòng kiêm nhiệm hiệu lực CÙNG công ty chính (không xét công tắc) — cho GET /departments cũ."""
    primary = emp.department_id or 0
    seen: list[int] = []
    for row in active_concurrent_rows(db, emp.id):
        if (row.company_id or 0) == (emp.company_id or 0) and row.department_id != primary \
                and row.department_id not in seen:
            seen.append(row.department_id)
    return seen


def list_concurrents(db: Session, employee_id: int) -> list[EmployeeConcurrent]:
    """Mới nhất trước: `from_date desc, id desc` (dòng chép cũ không ngày xuống cuối)."""
    return (db.query(EmployeeConcurrent).filter(EmployeeConcurrent.employee_id == employee_id)
            .order_by(EmployeeConcurrent.from_date.is_(None), EmployeeConcurrent.from_date.desc(),
                      EmployeeConcurrent.id.desc()).all())


def get_row_in_employee(db: Session, employee_id: int, concurrent_id: int) -> EmployeeConcurrent:
    """`concurrent_id` PHẢI thuộc `employee_id` — lệch là 404 (chặn IDOR chéo người)."""
    row = db.get(EmployeeConcurrent, concurrent_id)
    if row is None or int(row.employee_id) != int(employee_id):
        raise HTTPException(404, "Không tìm thấy dòng kiêm nhiệm")
    return row


# ── Chốt chặn ───────────────────────────────────────────────────────────────

def check_concurrent_target(db: Session, company_id: int, department_id: int) -> None:
    """L3 — công ty + phòng có thật, và phòng PHỤC VỤ công ty đó.

    Phòng phục vụ công ty khi `Department.company_id IN (0, c)` (0 = phòng dùng chung) hoặc có
    dòng `DepartmentCompany(department_id, c, is_active)`.
    """
    from app.modules.company.model import Company

    if not db.get(Company, company_id):
        raise HTTPException(400, "Công ty không tồn tại")
    dept = db.get(Department, department_id)
    if not dept:
        raise HTTPException(400, "Phòng ban không tồn tại")
    if dept.company_id in (0, company_id):
        return
    serves = db.query(DepartmentCompany.id).filter(
        DepartmentCompany.department_id == department_id, DepartmentCompany.company_id == company_id,
        DepartmentCompany.is_active.is_(True)).first()
    if not serves:
        raise HTTPException(400, f'Phòng ban "{dept.name}" không phục vụ công ty đã chọn')


def block_primary_duplicate(emp: Employee, company_id: int, department_id: int) -> None:
    if department_id == (emp.department_id or 0) and company_id == (emp.company_id or 0):
        raise HTTPException(400, "Trùng phòng ban chính — phòng này đã là phòng chính của nhân sự")


def _overlaps(a_from, a_to, b_from, b_to) -> bool:
    """Hai khoảng ngày bao gồm hai đầu giao nhau không; `None` = vô cực về phía đó."""
    return ((a_from is None or b_to is None or a_from <= b_to)
            and (b_from is None or a_to is None or b_from <= a_to))


def lock_employee_row(db: Session, employee_id: int) -> None:
    """Khóa hàng hồ sơ CHA (`SELECT ... FOR UPDATE`) trước khi kiểm chồng giai đoạn / trần dòng (N2).

    MySQL REPEATABLE READ + SELECT thường: hai giao dịch song song (bấm hai tab, Áp quá trình công tác cùng lúc
    với thêm tay) cùng thấy "chưa có dòng chồng" rồi cùng chèn -> hai giai đoạn chồng nhau, hoặc vượt trần
    `MAX_ROWS`. Khóa hàng cha buộc các đường ghi dòng kiêm nhiệm của CÙNG một nhân sự xếp hàng. Gọi ở MỌI đường
    ghi dòng (tạo, sửa, Áp, giữ phòng cũ, đổi pháp nhân, hoàn tác), TRƯỚC `block_overlap` / đếm dòng. SQLite bỏ qua
    `FOR UPDATE` (bài kiểm soi câu SQL biên dịch sang MySQL).
    """
    db.query(Employee.id).filter(Employee.id == employee_id).with_for_update().first()


def block_overlap(db: Session, employee_id: int, company_id: int, department_id: int,
                  from_date, to_date, exclude_id: int = 0) -> None:
    """Không cho hai giai đoạn của CÙNG (phòng, công ty) chồng nhau → 409."""
    rows = db.query(EmployeeConcurrent).filter(
        EmployeeConcurrent.employee_id == employee_id, EmployeeConcurrent.company_id == company_id,
        EmployeeConcurrent.department_id == department_id, EmployeeConcurrent.id != exclude_id).all()
    for row in rows:
        if _overlaps(from_date, to_date, row.from_date, row.to_date):
            raise HTTPException(409, "Giai đoạn kiêm nhiệm chồng với một dòng khác của cùng phòng ban "
                                     "và công ty — sửa dòng cũ hoặc đổi ngày.")


def _position_label(db: Session, position_id: int) -> str:
    """Chặn chức vụ id chết / đã ngừng dùng (gán MỚI) rồi trả nhãn CHỤP."""
    obj = position_service.check_assignable(db, position_id)
    return obj.name if obj else ""


# ── Ghi (chỉ flush — nơi gọi commit) ────────────────────────────────────────

def create_concurrent(db: Session, emp: Employee, data: ConcurrentIn, user, profile: dict) -> EmployeeConcurrent:
    department_service.block_edit_own_department(db, emp.id, user)                       # L1
    lock_employee_row(db, emp.id)                                                         # N2
    count = db.query(EmployeeConcurrent).filter(EmployeeConcurrent.employee_id == emp.id).count()
    if count >= MAX_ROWS:
        raise HTTPException(400, f"Hồ sơ này đã có {count} dòng kiêm nhiệm — tối đa {MAX_ROWS} dòng/người")
    check_concurrent_target(db, data.company_id, data.department_id)                     # L3
    department_service.block_out_of_scope_pair(                                           # L2
        db, [(data.department_id, data.company_id)], profile)
    block_primary_duplicate(emp, data.company_id, data.department_id)
    block_overlap(db, emp.id, data.company_id, data.department_id, data.from_date, data.to_date)
    label = _position_label(db, data.position_id)

    row = EmployeeConcurrent(
        employee_id=emp.id, company_id=data.company_id, department_id=data.department_id,
        position_id=data.position_id, position_label=label, from_date=data.from_date,
        to_date=data.to_date, decision_no=data.decision_no, decision_date=data.decision_date,
        note=data.note, counts_scope=data.counts_scope, created_by=user.id, updated_by=user.id)
    db.add(row)
    db.flush()
    return row


def update_concurrent(db: Session, emp: Employee, concurrent_id: int, data: ConcurrentPatch,
                      user, profile: dict) -> EmployeeConcurrent:
    department_service.block_edit_own_department(db, emp.id, user)                       # L1
    lock_employee_row(db, emp.id)                                                         # N2
    row = get_row_in_employee(db, emp.id, concurrent_id)
    fields = data.model_dump(exclude_unset=True)

    company_id = fields.get("company_id", row.company_id)
    department_id = fields.get("department_id", row.department_id)
    from_date = fields.get("from_date", row.from_date)
    to_date = fields["to_date"] if "to_date" in fields else row.to_date
    if from_date is not None and to_date is not None and to_date < from_date:
        raise HTTPException(422, ORDER_ERROR)

    pair_changed = (company_id, department_id) != (row.company_id, row.department_id)
    #  L2 đo cả cặp CŨ (không với tới cặp cũ thì không được cất / dời nó đi) lẫn cặp MỚI.
    if pair_changed:
        department_service.block_out_of_scope_pair(db, [(row.department_id, row.company_id)], profile)
        check_concurrent_target(db, company_id, department_id)                           # L3
        block_primary_duplicate(emp, company_id, department_id)
    department_service.block_out_of_scope_pair(db, [(department_id, company_id)], profile)
    block_overlap(db, emp.id, company_id, department_id, from_date, to_date, exclude_id=row.id)

    #  Chức vụ ngừng dùng: chặn gán MỚI, giữ nguyên khi chỉ sửa ô khác (xem `position_service`).
    if "position_id" in fields and fields["position_id"] != row.position_id:
        row.position_label = _position_label(db, fields["position_id"])
    for key, value in fields.items():
        setattr(row, key, value)
    row.updated_by = user.id
    db.flush()
    return row


def delete_concurrent(db: Session, emp: Employee, concurrent_id: int, user, profile: dict) -> EmployeeConcurrent:
    """Xóa dòng + tệp quyết định (cùng giao dịch; nơi gọi commit). Trả dòng đã xóa để ghi nhật ký."""
    department_service.block_edit_own_department(db, emp.id, user)                       # L1
    row = get_row_in_employee(db, emp.id, concurrent_id)
    department_service.block_out_of_scope_pair(db, [(row.department_id, row.company_id)], profile)  # L2
    from app.modules.attachment.service import delete_attachments_for
    delete_attachments_for(db, [("employee_concurrent", row.id)], commit=False)
    db.delete(row)
    db.flush()
    return row


def delete_all_of(db: Session, employee_id: int) -> None:
    """Dọn MỌI dòng + tệp khi xóa hồ sơ cha. KHÔNG commit — đi chung giao dịch với nơi gọi."""
    ids = [i for (i,) in db.query(EmployeeConcurrent.id)
           .filter(EmployeeConcurrent.employee_id == employee_id).all()]
    if not ids:
        return
    from app.modules.attachment.service import delete_attachments_for
    delete_attachments_for(db, [("employee_concurrent", i) for i in ids], commit=False)
    db.query(EmployeeConcurrent).filter(
        EmployeeConcurrent.employee_id == employee_id).delete(synchronize_session=False)
