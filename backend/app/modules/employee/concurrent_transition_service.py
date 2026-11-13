"""KIÊM NHIỆM — các đường GHI TỰ ĐỘNG từ nơi khác (duoc-CR-755 giai đoạn 03; hai loại dòng ở duoc-CR-756).

Tách khỏi `concurrent_service.py` (CRUD của tab Kiêm nhiệm) chỉ để mỗi tệp gọn dưới 200 dòng. Hai việc:

1. `create_from_kept_department` — ĐỔI PHÒNG CHÍNH (cùng công ty) mà giữ phòng cũ làm kiêm nhiệm loại PHÒNG BAN (bao-CR-709).
2. `upsert_from_work_history` — nút ÁP của quá trình công tác loại KIÊM NHIỆM (một dòng QTCT = một dòng kiêm nhiệm):
   cùng công ty chính -> loại Phòng ban; khác công ty -> loại Công ty (bỏ phòng của QTCT).

Luồng ĐỔI PHÁP NHÂN và hoàn tác lô Nhập Excel nằm ở `concurrent_company_change_service`.
"""
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.hr_concurrent_codes import ConcurrentKind
from app.core.vn_time import vn_today
from app.modules.department.model import Department

from . import concurrent_scope_audit, concurrent_service, department_service
from .concurrent_model import EmployeeConcurrent
from .model import Employee

KEPT_NOTE = "Giữ phòng cũ khi đổi phòng chính"


# ── 1. Giữ phòng cũ khi đổi phòng chính (cùng công ty) ───────────────────────

def create_from_kept_department(db: Session, emp: Employee, old_department_id: int, user_id: int,
                                today: date | None = None) -> bool:
    """Tạo dòng kiêm nhiệm loại PHÒNG BAN cho phòng chính CŨ (công ty chính của hồ sơ, từ hôm nay). `True` nếu có tạo.

    Chỉ dùng khi đổi phòng chính TRONG CÙNG công ty (đổi cả pháp nhân thì phòng cũ thuộc công ty cũ, đi đường
    `concurrent_company_change_service.keep_company_seat`). Không tạo (`False`) khi đã có dòng loại Phòng ban cùng
    phòng còn hiệu lực hoặc sắp tới — tránh chồng giai đoạn — hoặc hồ sơ chưa gắn pháp nhân. Không qua L2: phòng này
    vốn là phòng chính của người đó, giữ lại không mở thêm tầm nhìn nào.
    """
    today = today or vn_today()
    if not old_department_id or old_department_id == (emp.department_id or 0) or not (emp.company_id or 0):
        return False
    concurrent_service.lock_employee_row(db, emp.id)                                      # N2
    live = (db.query(EmployeeConcurrent.id)
            .filter(EmployeeConcurrent.employee_id == emp.id, EmployeeConcurrent.kind == ConcurrentKind.DEPARTMENT,
                    EmployeeConcurrent.department_id == old_department_id)
            .filter((EmployeeConcurrent.to_date.is_(None)) | (EmployeeConcurrent.to_date >= today))
            .with_for_update(read=True).first())                                                # N1: đọc-có-khóa
    if live:
        return False
    count = concurrent_service.locked_count(db, emp.id)
    if count >= concurrent_service.MAX_ROWS:
        raise HTTPException(400, f"Hồ sơ này đã có {count} dòng kiêm nhiệm — tối đa "
                                 f"{concurrent_service.MAX_ROWS} dòng/người, không giữ thêm phòng cũ được")
    db.add(EmployeeConcurrent(
        employee_id=emp.id, kind=ConcurrentKind.DEPARTMENT, company_id=emp.company_id,
        department_id=old_department_id, position_id=0,
        position_label="", from_date=today, to_date=None, decision_no="", decision_date=None,
        note=KEPT_NOTE, counts_scope=True, created_by=user_id, updated_by=user_id))
    db.flush()
    return True


# ── 2. Áp quá trình công tác loại KIÊM NHIỆM ─────────────────────────────────

def _link_decision_files(db: Session, work_history_id: int, concurrent_id: int, user_id: int) -> int:
    """Chép liên kết tệp QĐ của dòng QTCT sang dòng kiêm nhiệm (cùng `file_id`; tệp đã gắn thì bỏ qua)."""
    from app.modules.attachment.model import FileLink

    source = db.query(FileLink).filter(FileLink.entity == "employee_work_history",
                                       FileLink.entity_id == work_history_id).all()
    have = {r[0] for r in db.query(FileLink.file_id).filter(
        FileLink.entity == "employee_concurrent", FileLink.entity_id == concurrent_id).all()}
    added = 0
    for link in source:
        if link.file_id in have:
            continue
        db.add(FileLink(file_id=link.file_id, entity="employee_concurrent", entity_id=concurrent_id,
                        doc_type=link.doc_type, sort_order=link.sort_order,
                        created_by=user_id, updated_by=user_id))
        have.add(link.file_id)
        added += 1
    return added


def _name_of(db: Session, model, obj_id: int) -> str:
    return (db.query(model.name).filter(model.id == obj_id).scalar() or str(obj_id)) if obj_id else ""


def upsert_from_work_history(db: Session, emp: Employee, wh, actor, profile: dict) -> list[str]:
    """Áp dòng QTCT loại KIÊM NHIỆM thành MỘT dòng kiêm nhiệm đầy đủ (khóa `work_history_id`). Trả câu thay đổi.

    Công ty của dòng QTCT trùng công ty chính (hoặc trống) -> loại PHÒNG BAN (cần phòng; trùng phòng chính -> bỏ qua);
    khác công ty chính -> loại CÔNG TY (bỏ phòng của QTCT, QTCT giữ nguyên). Áp lại sau khi QTCT đổi công ty thì đổi
    LOẠI TẠI CHỖ (cùng id dòng, tệp quyết định giữ) — L2 đo cả dòng cũ lẫn mới.

    Idempotent: Áp lại cùng dòng không đẻ thêm dòng, chỉ cập nhật trường đã đổi ở QTCT. Một chiều — sửa dòng
    kiêm nhiệm ở tab KHÔNG ghi ngược lại QTCT. Dòng QTCT đã kết thúc: dòng sẵn có chỉ nhận `to_date` (thành
    "Đã hết", không gỡ); chưa có dòng thì không tạo dòng đã chết. Không đổi công tắc `counts_scope` của dòng sẵn có.
    """
    primary_company = emp.company_id or 0
    company = wh.company_id or primary_company
    if company == primary_company:
        kind, dept = ConcurrentKind.DEPARTMENT, wh.department_id or 0
        if not dept or dept == (emp.department_id or 0):
            #  Không có phòng, hoặc trùng phòng chính — không có gì để kiêm nhiệm thêm. NHƯNG nếu lần Áp trước đã sinh
            #  một dòng (vd loại Công ty, khi QTCT còn ở công ty khác) thì dòng đó ở lại nguyên: không tự kết thúc
            #  (quyết định của HR), nên NÓI RA để người áp sửa / kết thúc ở tab Kiêm nhiệm (rà mã CR-756, G2).
            left = (db.query(EmployeeConcurrent.id)
                    .filter(EmployeeConcurrent.employee_id == emp.id, EmployeeConcurrent.work_history_id == wh.id).first())
            return [] if left is None else [
                "Kiêm nhiệm — quá trình công tác này nay trùng công ty và phòng chính, dòng kiêm nhiệm đã áp trước đó "
                "được giữ nguyên: sửa hoặc kết thúc ở tab Kiêm nhiệm"]
    else:
        kind, dept = ConcurrentKind.COMPANY, 0

    department_service.block_edit_own_department(db, emp.id, actor)                       # L1
    concurrent_service.lock_employee_row(db, emp.id)                                      # N2
    row = (db.query(EmployeeConcurrent)
           .filter(EmployeeConcurrent.employee_id == emp.id, EmployeeConcurrent.work_history_id == wh.id)
           .with_for_update().populate_existing().first())                                        # N1: khóa + nạp lại
    today = vn_today()
    if row is None and wh.to_date is not None and wh.to_date < today:
        return []

    concurrent_service.require_primary_company(emp)
    concurrent_service.check_concurrent_target(                                           # L3
        db, company, dept, kind, allow_inactive_company=wh.to_date is not None and wh.to_date < today)
    specs = [(int(kind), company, dept)] + ([(int(row.kind), row.company_id, row.department_id)]
                                            if row is not None else [])
    department_service.block_out_of_scope_concurrent(db, specs, profile)                   # L2 (dòng cũ lẫn mới)
    concurrent_service.block_overlap(db, emp.id, kind, company, dept, wh.from_date, wh.to_date,
                                     exclude_id=row.id if row is not None else 0)

    values = dict(kind=int(kind), company_id=company, department_id=dept, position_id=wh.position_id or 0,
                  position_label=wh.position_label or "", from_date=wh.from_date, to_date=wh.to_date,
                  decision_no=wh.decision_no or "", decision_date=wh.decision_date, note=wh.note or "")
    if kind == ConcurrentKind.COMPANY:
        from app.modules.company.model import Company
        what, label = "công ty", f'"{_name_of(db, Company, company)}"'
    else:
        what, label = "phòng", f'"{_name_of(db, Department, dept)}"'
    if row is None:
        row = EmployeeConcurrent(employee_id=emp.id, work_history_id=wh.id, counts_scope=True,
                                 created_by=actor.id, updated_by=actor.id, **values)
        db.add(row)
        db.flush()
        concurrent_scope_audit.log_transition(db, actor.id, emp, None, row)
        _link_decision_files(db, wh.id, row.id, actor.id)
        message = [f"Kiêm nhiệm — thêm {what} {label}"]
    else:
        changed = [k for k, v in values.items() if getattr(row, k) != v]
        scope_before = concurrent_scope_audit.scope_state(row)
        files = _link_decision_files(db, wh.id, row.id, actor.id)
        if not changed and not files:
            return []
        for key in changed:
            setattr(row, key, values[key])
        row.updated_by = actor.id
        concurrent_scope_audit.log_transition(db, actor.id, emp, scope_before, row)
        message = [f"Kiêm nhiệm — cập nhật {what} {label}"]
        if wh.to_date is not None and wh.to_date < today:
            message = [f"Kiêm nhiệm — kết thúc {what} {label} (đến {wh.to_date.strftime('%d/%m/%Y')})"]
    db.flush()
    #  Phạm vi dữ liệu của người này vừa đổi; hồ sơ quyền cache 60 giây.
    from .service import clear_perm_cache_of
    clear_perm_cache_of(db, emp.id)
    return message
