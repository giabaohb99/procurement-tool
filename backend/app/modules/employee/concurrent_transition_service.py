"""KIÊM NHIỆM — các đường GHI TỰ ĐỘNG từ nơi khác (duoc-CR-755, giai đoạn 03).

Tách khỏi `concurrent_service.py` (CRUD của tab Kiêm nhiệm) chỉ để mỗi tệp gọn dưới 200 dòng. Bốn việc:

1. `end_rows_at_company`  — ĐỔI PHÁP NHÂN chính A -> B: kết thúc dòng kiêm nhiệm ở công ty cũ A (Q4).
2. `create_from_kept_department` — ĐỔI PHÒNG CHÍNH mà giữ phòng cũ làm kiêm nhiệm (bao-CR-709).
3. `upsert_from_work_history` — nút ÁP của quá trình công tác loại KIÊM NHIỆM (một dòng QTCT = một dòng kiêm nhiệm).
4. `restore_ended` — HOÀN TÁC lô Nhập Excel nhân sự: trả lại `to_date` cũ của các dòng đã kết thúc.

⚠️ Dòng ở công ty KHÁC công ty cũ không bao giờ bị đụng khi đổi pháp nhân — lọc cứng `company_id == công ty cũ`.
Kết thúc dòng = đặt `to_date` chứ không xóa (giữ lịch sử, tệp quyết định, hoàn tác được); chỉ dòng CHƯA BẮT ĐẦU
mới xóa (không còn gì để giữ lịch sử).
"""
from dataclasses import dataclass, field
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.vn_time import vn_today
from app.modules.department.model import Department

from . import concurrent_service, department_service
from .concurrent_model import EmployeeConcurrent
from .model import Employee

KEPT_NOTE = "Giữ phòng cũ khi đổi phòng chính"

#  Câu lỗi dòng của đường Nhập Excel (không xóa được dòng chưa bắt đầu qua tệp vì hoàn tác không khôi phục được).
IMPORT_UNSTARTED_ERROR = "Còn kiêm nhiệm chưa bắt đầu ở công ty cũ — sửa ở tab Kiêm nhiệm trước"


@dataclass
class CompanyChange:
    """Kết quả kết thúc kiêm nhiệm ở công ty cũ — nơi gọi dùng cho nhật ký + bản chụp hoàn tác."""
    #  `[id, to_date cũ | None, to_date mới]` của các dòng được ĐẶT `to_date`.
    ended: list[tuple[int, date | None, date]] = field(default_factory=list)
    deleted: int = 0           # số dòng chưa bắt đầu đã xóa
    labels: list[str] = field(default_factory=list)   # "Phòng X (đến 11/11/2026)" cho câu nhật ký

    def note(self) -> str:
        if not self.ended and not self.deleted:
            return ""
        return (f"Đổi pháp nhân — kết thúc {len(self.ended) + self.deleted} dòng kiêm nhiệm ở công ty cũ: "
                + ", ".join(self.labels))


def _department_names(db: Session, ids) -> dict[int, str]:
    ids = {int(i) for i in ids if i}
    if not ids:
        return {}
    return {r[0]: r[1] for r in db.query(Department.id, Department.name).filter(Department.id.in_(ids)).all()}


def _block_file_loss(db: Session, user_id: int, row: EmployeeConcurrent) -> None:
    """Xóa dòng kéo theo xóa tệp quyết định → cùng chốt nhạy cảm với `DELETE /concurrents/{cid}`."""
    from app.modules.attachment.model import FileLink
    from app.modules.user.model import User

    from . import concurrent_access

    user = db.get(User, user_id)
    if user is not None:
        concurrent_access.block_delete_without_sensitive(db, user, row)
        return
    if db.query(FileLink.id).filter(FileLink.entity == "employee_concurrent",
                                    FileLink.entity_id == row.id).first() is not None:
        raise HTTPException(403, "Dòng kiêm nhiệm chưa bắt đầu có tệp quyết định đính kèm — "
                                 "không xác định được quyền của người thao tác để xóa")


# ── 1. Đổi pháp nhân ─────────────────────────────────────────────────────────

def end_rows_at_company(db: Session, emp: Employee, old_company_id: int, user_id: int, *,
                        keep_ids: frozenset[int] | set[int] = frozenset(), import_mode: bool = False,
                        today: date | None = None) -> CompanyChange:
    """Kết thúc dòng kiêm nhiệm của `emp` ở công ty CŨ `old_company_id`; chỉ flush, nơi gọi commit.

    - đã hết hạn (`to_date < hôm nay`) hoặc nằm trong `keep_ids` -> giữ nguyên;
    - chưa bắt đầu (`from_date >= hôm nay`) -> xóa kèm tệp (nhập Excel: LỖI DÒNG, vì hoàn tác không dựng lại được);
    - còn lại -> `to_date = hôm qua`.
    """
    result = CompanyChange()
    if not old_company_id:
        return result
    today = today or vn_today()
    yesterday = today - timedelta(days=1)
    concurrent_service.lock_employee_row(db, emp.id)                                      # N2
    rows = (db.query(EmployeeConcurrent)
            .filter(EmployeeConcurrent.employee_id == emp.id, EmployeeConcurrent.company_id == old_company_id)
            .order_by(EmployeeConcurrent.id.asc()).all())
    ending, removing = [], []
    for row in rows:
        if row.id in keep_ids or (row.to_date is not None and row.to_date < today):
            continue
        (removing if row.from_date is not None and row.from_date >= today else ending).append(row)

    if removing and import_mode:
        raise HTTPException(400, IMPORT_UNSTARTED_ERROR)
    names = _department_names(db, [r.department_id for r in ending + removing])
    for row in removing:
        _block_file_loss(db, user_id, row)
    for row in ending:
        result.ended.append((row.id, row.to_date, yesterday))
        result.labels.append(f'{names.get(row.department_id, row.department_id)} (đến {yesterday.strftime("%d/%m/%Y")})')
        row.to_date = yesterday
        row.updated_by = user_id
    if removing:
        from app.modules.attachment.service import delete_attachments_for

        delete_attachments_for(db, [("employee_concurrent", r.id) for r in removing], commit=False)
        for row in removing:
            result.labels.append(f'{names.get(row.department_id, row.department_id)} (chưa bắt đầu, đã xóa)')
            db.delete(row)
        result.deleted = len(removing)
    db.flush()
    return result


def restore_ended(db: Session, emp: Employee, entries, profile: dict) -> None:
    """Hoàn tác `end_rows_at_company`: trả `to_date` cũ. `entries` = `[[id, to_cũ|None, to_mới], ...]` (JSON bản chụp).

    Gọi SAU khi `revert_problems` đã kiểm; hàm vẫn kiểm lại L2 + chồng giai đoạn để không tin tuyệt đối bản chụp.
    """
    concurrent_service.lock_employee_row(db, emp.id)                                      # N2
    for cid, old_to, _new_to in entries:
        row = db.get(EmployeeConcurrent, int(cid))
        if row is None or row.employee_id != emp.id:
            continue
        department_service.block_out_of_scope_pair(db, [(row.department_id, row.company_id)], profile)
        restored = date.fromisoformat(old_to[:10]) if old_to else None
        concurrent_service.block_overlap(db, emp.id, row.company_id, row.department_id,
                                         row.from_date, restored, exclude_id=row.id)
        row.to_date = restored
    db.flush()


def revert_problems(db: Session, emp: Employee, entries, profile: dict) -> list[str]:
    """Lý do TỪ CHỐI hoàn tác phần kiêm nhiệm đã kết thúc (rỗng = được). Không nêu giá trị nhạy cảm."""
    problems: list[str] = []
    for cid, old_to, new_to in entries:
        row = db.get(EmployeeConcurrent, int(cid))
        if row is None or row.employee_id != emp.id:
            problems.append("dòng kiêm nhiệm đã bị xóa sau khi nhập")
            continue
        if (row.to_date.isoformat() if row.to_date else "") != (new_to or "")[:10]:
            problems.append("dòng kiêm nhiệm đã bị sửa sau khi nhập")
            continue
        try:
            department_service.block_out_of_scope_pair(db, [(row.department_id, row.company_id)], profile)
            restored = date.fromisoformat(old_to[:10]) if old_to else None
            concurrent_service.block_overlap(db, emp.id, row.company_id, row.department_id,
                                             row.from_date, restored, exclude_id=row.id)
        except HTTPException as e:
            problems.append(str(e.detail))
    return list(dict.fromkeys(problems))


# ── 2. Giữ phòng cũ khi đổi phòng chính ──────────────────────────────────────

def create_from_kept_department(db: Session, emp: Employee, old_department_id: int, company_id: int,
                                user_id: int, today: date | None = None) -> bool:
    """Tạo dòng kiêm nhiệm cho phòng chính CŨ (công ty TRƯỚC lần lưu, từ hôm nay). `True` nếu có tạo.

    Không tạo (trả `False`) khi đã có dòng cùng cặp (phòng, công ty) còn hiệu lực hoặc sắp tới — tránh chồng
    giai đoạn. Không qua L2: phòng này vốn là phòng chính của người đó, giữ lại không mở thêm tầm nhìn nào.
    """
    today = today or vn_today()
    company_id = int(company_id or 0)
    if not old_department_id or (old_department_id, company_id) == (emp.department_id or 0, emp.company_id or 0):
        return False
    concurrent_service.lock_employee_row(db, emp.id)                                      # N2
    live = (db.query(EmployeeConcurrent.id)
            .filter(EmployeeConcurrent.employee_id == emp.id, EmployeeConcurrent.company_id == company_id,
                    EmployeeConcurrent.department_id == old_department_id)
            .filter((EmployeeConcurrent.to_date.is_(None)) | (EmployeeConcurrent.to_date >= today)).first())
    if live:
        return False
    count = db.query(EmployeeConcurrent).filter(EmployeeConcurrent.employee_id == emp.id).count()
    if count >= concurrent_service.MAX_ROWS:
        raise HTTPException(400, f"Hồ sơ này đã có {count} dòng kiêm nhiệm — tối đa "
                                 f"{concurrent_service.MAX_ROWS} dòng/người, không giữ thêm phòng cũ được")
    db.add(EmployeeConcurrent(
        employee_id=emp.id, company_id=company_id, department_id=old_department_id, position_id=0,
        position_label="", from_date=today, to_date=None, decision_no="", decision_date=None,
        note=KEPT_NOTE, counts_scope=True, created_by=user_id, updated_by=user_id))
    db.flush()
    return True


# ── 3. Áp quá trình công tác loại KIÊM NHIỆM ─────────────────────────────────

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


def upsert_from_work_history(db: Session, emp: Employee, wh, actor, profile: dict) -> list[str]:
    """Áp dòng QTCT loại KIÊM NHIỆM thành MỘT dòng kiêm nhiệm đầy đủ (khóa `work_history_id`). Trả câu thay đổi.

    Idempotent: Áp lại cùng dòng không đẻ thêm dòng, chỉ cập nhật trường đã đổi ở QTCT. Một chiều — sửa dòng
    kiêm nhiệm ở tab KHÔNG ghi ngược lại QTCT. Dòng QTCT đã kết thúc: dòng sẵn có chỉ nhận `to_date` (thành
    "Đã hết", không gỡ); chưa có dòng thì không tạo dòng đã chết. Không đổi công tắc `counts_scope` của dòng sẵn có.
    """
    dept = wh.department_id or 0
    company = wh.company_id or emp.company_id or 0
    if not dept or (dept, company) == (emp.department_id or 0, emp.company_id or 0):
        return []   # trùng phòng chính — không có gì để kiêm nhiệm thêm

    department_service.block_edit_own_department(db, emp.id, actor)                       # L1
    concurrent_service.lock_employee_row(db, emp.id)                                      # N2
    row = (db.query(EmployeeConcurrent)
           .filter(EmployeeConcurrent.employee_id == emp.id, EmployeeConcurrent.work_history_id == wh.id).first())
    today = vn_today()
    if row is None and wh.to_date is not None and wh.to_date < today:
        return []

    pairs = [(dept, company)] + ([(row.department_id, row.company_id)] if row is not None else [])
    if company:
        concurrent_service.check_concurrent_target(db, company, dept)                     # L3
    elif not db.get(Department, dept):
        raise HTTPException(400, "Phòng ban không tồn tại")
    department_service.block_out_of_scope_pair(db, pairs, profile)                         # L2 (cặp cũ lẫn mới)
    concurrent_service.block_overlap(db, emp.id, company, dept, wh.from_date, wh.to_date,
                                     exclude_id=row.id if row is not None else 0)

    values = dict(company_id=company, department_id=dept, position_id=wh.position_id or 0,
                  position_label=wh.position_label or "", from_date=wh.from_date, to_date=wh.to_date,
                  decision_no=wh.decision_no or "", decision_date=wh.decision_date, note=wh.note or "")
    names = _department_names(db, [dept])
    label = f'"{names.get(dept, dept)}"'
    if row is None:
        row = EmployeeConcurrent(employee_id=emp.id, work_history_id=wh.id, counts_scope=True,
                                 created_by=actor.id, updated_by=actor.id, **values)
        db.add(row)
        db.flush()
        _link_decision_files(db, wh.id, row.id, actor.id)
        message = [f"Kiêm nhiệm — thêm phòng {label}"]
    else:
        changed = [k for k, v in values.items() if getattr(row, k) != v]
        files = _link_decision_files(db, wh.id, row.id, actor.id)
        if not changed and not files:
            return []
        for key in changed:
            setattr(row, key, values[key])
        row.updated_by = actor.id
        message = [f"Kiêm nhiệm — cập nhật phòng {label}"]
        if wh.to_date is not None and wh.to_date < today:
            message = [f"Kiêm nhiệm — kết thúc phòng {label} (đến {wh.to_date.strftime('%d/%m/%Y')})"]
    db.flush()
    #  Phạm vi dữ liệu của người này vừa đổi; hồ sơ quyền cache 60 giây.
    from .service import clear_perm_cache_of
    clear_perm_cache_of(db, emp.id)
    return message
