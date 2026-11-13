"""KIÊM NHIỆM — đọc, ghi, và các chốt chặn (duoc-CR-755, hai loại dòng độc lập ở duoc-CR-756).
Bảng: `tab_employee_concurrent`.

Hai loại dòng (`ConcurrentKind`): **Phòng ban** (phòng của công ty chính, `company_id` = công ty chính) và **Công ty**
(công ty khác công ty chính, `department_id = 0`). `kind` không đổi qua PATCH (đổi loại = xóa + thêm).

⚠️ Thêm / sửa một dòng còn hiệu lực + bật `counts_scope` là MỞ RỘNG tầm nhìn dữ liệu của
người đó (hồ sơ quyền đọc bảng này mỗi request). Nên mọi cửa ghi đều qua đủ ba chốt của
`department_service`:

**L1** không tự sửa kiêm nhiệm của chính mình (kể cả quản trị).
**L2** chỉ gán dòng nằm trong phạm vi GHI của người thao tác (`block_out_of_scope_concurrent`): loại Phòng ban theo
  cặp (phòng, công ty chính), loại Công ty chặt hơn — cần bậc toàn công ty. Sửa dòng thì đo cả bộ cũ lẫn mới. Bật lại
  công tắc, nới ngày cũng là mở rộng nên luôn qua L2.
**L3** công ty / phòng có thật; loại Phòng ban: phòng phục vụ công ty chính (`check_concurrent_target`).

Dòng được sửa TẠI CHỖ (không xóa-chèn lại) để id bền — tệp quyết định gắn theo id dòng.
"""
from datetime import date

from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.hr_concurrent_codes import ConcurrentKind
from app.core.vn_time import vn_today
from app.modules.department.model import Department, DepartmentCompany

from . import concurrent_scope_audit, department_service, position_service
from .concurrent_model import EmployeeConcurrent
from .concurrent_schema import (KIND_COMPANY_NO_DEPARTMENT, KIND_DEPARTMENT_NO_COMPANY, ORDER_ERROR, ConcurrentIn,
                                ConcurrentPatch)
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
    """Phòng kiêm nhiệm hiệu lực loại PHÒNG BAN (không xét công tắc) — cho GET /departments cũ."""
    primary = emp.department_id or 0
    seen: list[int] = []
    for row in active_concurrent_rows(db, emp.id):
        if row.kind == ConcurrentKind.DEPARTMENT and row.department_id != primary \
                and row.department_id not in seen:
            seen.append(row.department_id)
    return seen


def list_concurrents(db: Session, employee_id: int) -> list[EmployeeConcurrent]:
    """Mới nhất trước: `from_date desc, id desc` (dòng chép cũ không ngày xuống cuối)."""
    return (db.query(EmployeeConcurrent).filter(EmployeeConcurrent.employee_id == employee_id)
            .order_by(EmployeeConcurrent.from_date.is_(None), EmployeeConcurrent.from_date.desc(),
                      EmployeeConcurrent.id.desc()).all())


def get_row_in_employee(db: Session, employee_id: int, concurrent_id: int, *, lock: bool = False) -> EmployeeConcurrent:
    """`concurrent_id` PHẢI thuộc `employee_id` — lệch là 404 (chặn IDOR chéo người).

    `lock=True` (đường GHI, sau `lock_employee_row`): đọc có khóa + nạp lại dòng từ DB — `db.get` trần đọc ảnh chụp
    REPEATABLE READ / bản trong bộ nhớ nên hai lần sửa song song ghi đè nhau (N1, rà mã CR-756)."""
    if lock:
        row = (db.query(EmployeeConcurrent).filter(EmployeeConcurrent.id == concurrent_id)
               .with_for_update().populate_existing().one_or_none())
    else:
        row = db.get(EmployeeConcurrent, concurrent_id)
    if row is None or int(row.employee_id) != int(employee_id):
        raise HTTPException(404, "Không tìm thấy dòng kiêm nhiệm")
    return row


# ── Chốt chặn ───────────────────────────────────────────────────────────────

def require_primary_company(emp: Employee) -> None:
    """Hồ sơ chưa gắn pháp nhân chính thì không khai được kiêm nhiệm nào (cả hai loại): loại Phòng ban lấy công ty
    chính làm công ty, loại Công ty cần công ty chính để biết "khác" (duoc-CR-756, câu hỏi mở 1)."""
    if not (emp.company_id or 0):
        raise HTTPException(400, "Hồ sơ chưa gắn pháp nhân chính — gắn pháp nhân chính trước khi khai kiêm nhiệm")


def check_concurrent_target(db: Session, company_id: int, department_id: int,
                            kind: int = ConcurrentKind.DEPARTMENT, *, allow_inactive_company: bool = False) -> None:
    """L3 — công ty (và phòng với loại Phòng ban) có thật; phòng PHỤC VỤ công ty chính.

    Loại Công ty còn đòi công ty ĐANG HOẠT ĐỘNG (xóa mềm = ngừng hoạt động): giao diện đã lọc `is_active` nhưng API
    gọi thẳng thì không — gán kiêm nhiệm sang công ty đã đóng là mở dữ liệu một pháp nhân không còn ai quản (rà mã
    CR-756, G1). `allow_inactive_company=True` chỉ cho Áp quá trình công tác ĐÃ KẾT THÚC (ghi nhận lịch sử, không mở gì).

    Phòng phục vụ công ty khi `Department.company_id IN (0, c)` (0 = phòng dùng chung) hoặc có
    dòng `DepartmentCompany(department_id, c, is_active)`. Loại Công ty không có phòng.
    """
    from app.modules.company.model import Company

    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(400, "Công ty không tồn tại")
    if kind == ConcurrentKind.COMPANY:
        if not company.is_active and not allow_inactive_company:
            raise HTTPException(400, "Công ty đã ngừng hoạt động hoặc đã xóa — không gán kiêm nhiệm sang công ty đó được")
        return
    dept = db.get(Department, department_id)
    if not dept:
        raise HTTPException(400, "Phòng ban không tồn tại")
    if dept.company_id in (0, company_id):
        return
    serves = db.query(DepartmentCompany.id).filter(
        DepartmentCompany.department_id == department_id, DepartmentCompany.company_id == company_id,
        DepartmentCompany.is_active.is_(True)).first()
    if not serves:
        raise HTTPException(400, f'Phòng ban "{dept.name}" không phục vụ công ty hiện tại')


def block_primary_duplicate(emp: Employee, kind: int, company_id: int, department_id: int) -> None:
    """Loại Phòng ban không trùng phòng chính; loại Công ty không trùng công ty chính."""
    if kind == ConcurrentKind.COMPANY:
        if company_id == (emp.company_id or 0):
            raise HTTPException(400, "Công ty kiêm nhiệm trùng công ty chính")
    elif department_id == (emp.department_id or 0):
        raise HTTPException(400, "Trùng phòng ban chính — phòng này đã là phòng chính của nhân sự")


def _overlaps(a_from, a_to, b_from, b_to) -> bool:
    """Hai khoảng ngày bao gồm hai đầu giao nhau không; `None` = vô cực về phía đó."""
    return ((a_from is None or b_to is None or a_from <= b_to)
            and (b_from is None or a_to is None or b_from <= a_to))


def lock_employee_row(db: Session, employee_id: int) -> Employee | None:
    """Khóa hàng hồ sơ CHA (`SELECT ... FOR UPDATE`) rồi NẠP LẠI nó từ DB trước khi kiểm chồng giai đoạn / trần dòng (N2, N1).

    MySQL REPEATABLE READ + SELECT thường: hai giao dịch song song (bấm hai tab, Áp quá trình công tác cùng lúc
    với thêm tay) cùng thấy "chưa có dòng chồng" rồi cùng chèn -> hai giai đoạn chồng nhau, hoặc vượt trần
    `MAX_ROWS`. Khóa hàng cha buộc các đường ghi dòng kiêm nhiệm của CÙNG một nhân sự xếp hàng.

    ⚠️ Khóa KHÔNG đủ (rà mã CR-756, N1): ảnh chụp REPEATABLE READ đã chốt từ truy vấn đầu của request, nên sau khi chờ khóa
    xong, SELECT thường vẫn đọc ảnh cũ và không thấy dòng giao dịch kia vừa chèn. Vì thế (a) hồ sơ cha nạp lại trong
    CHÍNH lệnh khóa (`populate_existing` — `emp.company_id` mới nhất, không phải bản trước khi chờ); (b) mọi truy vấn kiểm
    dòng kiêm nhiệm SAU khóa là đọc-có-khóa (`.with_for_update(read=True)`, xem `block_overlap`, `locked_count`).

    Session chạy `autoflush=False`: phải `flush` trước, nếu không `populate_existing` ĐÈ MẤT thay đổi chưa ghi của `emp`
    (vd ô `company_id` vừa gán ở `update_employee_core`). Gọi ở MỌI đường ghi dòng (tạo, sửa, Áp, giữ phòng cũ, đổi
    pháp nhân, hoàn tác), TRƯỚC `block_overlap` / đếm dòng. SQLite bỏ qua `FOR UPDATE` (bài kiểm soi câu SQL biên dịch
    sang MySQL).
    """
    db.flush()
    return (db.query(Employee).filter(Employee.id == employee_id)
            .with_for_update().populate_existing().one_or_none())


def locked_count(db: Session, employee_id: int) -> int:
    """Số dòng kiêm nhiệm của nhân sự (kể cả đã hết hạn) — đọc-có-khóa để thấy dòng giao dịch khác vừa chèn (N1)."""
    return len(db.query(EmployeeConcurrent.id).filter(EmployeeConcurrent.employee_id == employee_id)
               .with_for_update(read=True).all())


def block_overlap(db: Session, employee_id: int, kind: int, company_id: int, department_id: int,
                  from_date, to_date, exclude_id: int = 0) -> None:
    """Không cho hai giai đoạn CÙNG LOẠI và cùng đối tượng chồng nhau → 409.

    Loại Phòng ban: cùng (nhân sự, phòng). Loại Công ty: cùng (nhân sự, công ty). Hai loại khác nhau không chồng nhau.
    """
    q = db.query(EmployeeConcurrent).filter(
        EmployeeConcurrent.employee_id == employee_id, EmployeeConcurrent.kind == int(kind),
        EmployeeConcurrent.id != exclude_id)
    if kind == ConcurrentKind.COMPANY:
        q = q.filter(EmployeeConcurrent.company_id == company_id)
        what = "công ty"
    else:
        q = q.filter(EmployeeConcurrent.department_id == department_id)
        what = "phòng ban"
    for row in q.with_for_update(read=True).all():      # đọc-có-khóa: bỏ qua ảnh chụp cũ (N1)
        if _overlaps(from_date, to_date, row.from_date, row.to_date):
            raise HTTPException(409, f"Giai đoạn kiêm nhiệm chồng với một dòng khác của cùng {what} — "
                                     "sửa dòng cũ hoặc đổi ngày.")


def _position_label(db: Session, position_id: int) -> str:
    """Chặn chức vụ id chết / đã ngừng dùng (gán MỚI) rồi trả nhãn CHỤP."""
    obj = position_service.check_assignable(db, position_id)
    return obj.name if obj else ""


# ── Ghi (chỉ flush — nơi gọi commit) ────────────────────────────────────────

def create_concurrent(db: Session, emp: Employee, data: ConcurrentIn, user, profile: dict) -> EmployeeConcurrent:
    department_service.block_edit_own_department(db, emp.id, user)                       # L1
    lock_employee_row(db, emp.id)                                                         # N2
    count = locked_count(db, emp.id)
    if count >= MAX_ROWS:
        raise HTTPException(400, f"Hồ sơ này đã có {count} dòng kiêm nhiệm — tối đa {MAX_ROWS} dòng/người")
    require_primary_company(emp)
    kind = int(data.kind)
    #  Loại Phòng ban: công ty = công ty chính (máy chủ điền). Loại Công ty: không phòng.
    company_id = (emp.company_id or 0) if kind == ConcurrentKind.DEPARTMENT else data.company_id
    department_id = data.department_id if kind == ConcurrentKind.DEPARTMENT else 0
    check_concurrent_target(db, company_id, department_id, kind)                          # L3
    block_primary_duplicate(emp, kind, company_id, department_id)
    department_service.block_out_of_scope_concurrent(db, [(kind, company_id, department_id)], profile)   # L2
    block_overlap(db, emp.id, kind, company_id, department_id, data.from_date, data.to_date)
    label = _position_label(db, data.position_id)

    row = EmployeeConcurrent(
        employee_id=emp.id, kind=kind, company_id=company_id, department_id=department_id,
        position_id=data.position_id, position_label=label, from_date=data.from_date,
        to_date=data.to_date, decision_no=data.decision_no, decision_date=data.decision_date,
        note=data.note, counts_scope=data.counts_scope, created_by=user.id, updated_by=user.id)
    db.add(row)
    db.flush()
    concurrent_scope_audit.log_transition(db, user.id, emp, None, row)                   # CR-756: nhật ký mở phạm vi
    return row


def update_concurrent(db: Session, emp: Employee, concurrent_id: int, data: ConcurrentPatch,
                      user, profile: dict) -> EmployeeConcurrent:
    department_service.block_edit_own_department(db, emp.id, user)                       # L1
    lock_employee_row(db, emp.id)                                                         # N2
    row = get_row_in_employee(db, emp.id, concurrent_id, lock=True)
    scope_before = concurrent_scope_audit.scope_state(row)
    fields = data.model_dump(exclude_unset=True)
    kind = int(row.kind or ConcurrentKind.DEPARTMENT)
    #  Mỗi loại chỉ nhận ô của loại đó.
    if kind == ConcurrentKind.DEPARTMENT and "company_id" in fields:
        raise HTTPException(400, KIND_DEPARTMENT_NO_COMPANY)
    if kind == ConcurrentKind.COMPANY and "department_id" in fields:
        raise HTTPException(400, KIND_COMPANY_NO_DEPARTMENT)

    company_id = fields.get("company_id", row.company_id) if kind == ConcurrentKind.COMPANY \
        else (row.company_id or emp.company_id or 0)
    department_id = fields.get("department_id", row.department_id) if kind == ConcurrentKind.DEPARTMENT else 0
    from_date = fields.get("from_date", row.from_date)
    to_date = fields["to_date"] if "to_date" in fields else row.to_date
    if from_date is not None and to_date is not None and to_date < from_date:
        raise HTTPException(422, ORDER_ERROR)

    target_changed = (company_id, department_id) != (row.company_id, row.department_id)
    #  L2 đo cả dòng CŨ (không với tới thì không được cất / dời nó đi) lẫn dòng MỚI.
    if target_changed:
        department_service.block_out_of_scope_concurrent(
            db, [(kind, row.company_id, row.department_id)], profile)
        check_concurrent_target(db, company_id, department_id, kind)                      # L3
        block_primary_duplicate(emp, kind, company_id, department_id)
    department_service.block_out_of_scope_concurrent(db, [(kind, company_id, department_id)], profile)
    block_overlap(db, emp.id, kind, company_id, department_id, from_date, to_date, exclude_id=row.id)

    #  Chức vụ ngừng dùng: chặn gán MỚI, giữ nguyên khi chỉ sửa ô khác (xem `position_service`).
    if "position_id" in fields and fields["position_id"] != row.position_id:
        row.position_label = _position_label(db, fields["position_id"])
    for key, value in fields.items():
        setattr(row, key, value)
    row.updated_by = user.id
    db.flush()
    concurrent_scope_audit.log_transition(db, user.id, emp, scope_before, row)
    return row


def delete_concurrent(db: Session, emp: Employee, concurrent_id: int, user, profile: dict) -> EmployeeConcurrent:
    """Xóa dòng + tệp quyết định (cùng giao dịch; nơi gọi commit). Trả dòng đã xóa để ghi nhật ký."""
    department_service.block_edit_own_department(db, emp.id, user)                       # L1
    row = get_row_in_employee(db, emp.id, concurrent_id)
    department_service.block_out_of_scope_concurrent(                                      # L2
        db, [(row.kind, row.company_id, row.department_id)], profile)
    from app.modules.attachment.service import delete_attachments_for
    delete_attachments_for(db, [("employee_concurrent", row.id)], commit=False)
    scope_before = concurrent_scope_audit.scope_state(row)
    db.delete(row)
    db.flush()
    concurrent_scope_audit.log_transition(db, user.id, emp, scope_before, None, "xóa dòng kiêm nhiệm")
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
