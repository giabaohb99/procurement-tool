"""KIÊM NHIỆM — luồng ĐỔI PHÁP NHÂN chính và hoàn tác lô Nhập Excel (duoc-CR-756; gốc ở `concurrent_transition_service`).

Tách khỏi `concurrent_transition_service.py` chỉ để mỗi tệp gọn dưới 200 dòng. Bốn việc:

1. `end_rows_at_company` — ĐỔI PHÁP NHÂN chính A -> C: kết thúc dòng loại PHÒNG BAN ở A (phòng của A không còn là phòng
   của công ty chính) và dòng loại CÔNG TY trùng C (C đã thành công ty chính, kiêm nhiệm nó là thừa).
2. `keep_company_seat` — tùy chọn "giữ kiêm nhiệm ở công ty cũ A": tạo MỘT dòng loại CÔNG TY (A), qua L1/L2.
3. `restore_ended` — HOÀN TÁC lô Nhập Excel: trả lại `to_date` cũ của các dòng đã kết thúc.
4. `revert_problems` — lý do TỪ CHỐI hoàn tác phần đó.

⚠️ Dòng loại CÔNG TY ở công ty KHÁC (không phải C) không bao giờ bị đụng khi đổi pháp nhân. Kết thúc dòng = đặt `to_date`
chứ không xóa (giữ lịch sử, tệp quyết định, hoàn tác được); chỉ dòng CHƯA BẮT ĐẦU mới xóa.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.hr_concurrent_codes import ConcurrentKind
from app.core.vn_time import vn_today
from app.modules.department.model import Department

from . import concurrent_scope_audit, concurrent_service, department_service
from .concurrent_model import EmployeeConcurrent
from .model import Employee

KEEP_SEAT_NOTE = "Giữ kiêm nhiệm khi đổi pháp nhân"

#  Câu lỗi dòng của đường Nhập Excel (không xóa được dòng chưa bắt đầu qua tệp vì hoàn tác không khôi phục được).
IMPORT_UNSTARTED_ERROR = "Còn kiêm nhiệm chưa bắt đầu ở công ty cũ hoặc công ty mới — sửa ở tab Kiêm nhiệm trước"


@dataclass
class CompanyChange:
    """Kết quả kết thúc kiêm nhiệm khi đổi pháp nhân — nơi gọi dùng cho nhật ký + bản chụp hoàn tác."""
    #  `[id, to_date cũ | None, to_date mới]` của các dòng được ĐẶT `to_date`.
    ended: list[tuple[int, date | None, date]] = field(default_factory=list)
    deleted: int = 0           # số dòng chưa bắt đầu đã xóa
    labels: list[str] = field(default_factory=list)   # "Phòng X (đến 11/11/2026)" cho câu nhật ký

    def note(self) -> str:
        if not self.ended and not self.deleted:
            return ""
        return (f"Đổi pháp nhân — kết thúc {len(self.ended) + self.deleted} dòng kiêm nhiệm: "
                + ", ".join(self.labels))


def _names(db: Session, model, ids) -> dict[int, str]:
    ids = {int(i) for i in ids if i}
    if not ids:
        return {}
    return {r[0]: r[1] for r in db.query(model.id, model.name).filter(model.id.in_(ids)).all()}


def _row_label(row: EmployeeConcurrent, dept_names: dict[int, str], company_names: dict[int, str]) -> str:
    if row.kind == ConcurrentKind.COMPANY:
        return f'Công ty {company_names.get(row.company_id, row.company_id)}'
    return f'Phòng {dept_names.get(row.department_id, row.department_id)}'


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

def end_rows_at_company(db: Session, emp: Employee, old_company_id: int, new_company_id: int, user_id: int, *,
                        import_mode: bool = False, today: date | None = None) -> CompanyChange:
    """Kết thúc dòng kiêm nhiệm bị đổi pháp nhân A (`old_company_id`) -> C (`new_company_id`) làm vô nghĩa.

    Hai nhóm: loại PHÒNG BAN có `company_id == A`; loại CÔNG TY có `company_id == C`. Chỉ flush, nơi gọi commit.
    - đã hết hạn (`to_date < hôm nay`) -> giữ nguyên;
    - chưa bắt đầu (`from_date >= hôm nay`) -> xóa kèm tệp (nhập Excel: LỖI DÒNG, vì hoàn tác không dựng lại được);
    - còn lại -> `to_date = hôm qua`.
    """
    result = CompanyChange()
    #  Công ty cũ trống (hồ sơ chưa từng gắn pháp nhân) -> không có dòng Phòng ban nào để kết thúc.
    conds = []
    if old_company_id:
        conds.append(and_(EmployeeConcurrent.kind == ConcurrentKind.DEPARTMENT,
                          EmployeeConcurrent.company_id == old_company_id))
    if new_company_id:
        conds.append(and_(EmployeeConcurrent.kind == ConcurrentKind.COMPANY,
                          EmployeeConcurrent.company_id == new_company_id))
    if not conds:
        return result
    today = today or vn_today()
    yesterday = today - timedelta(days=1)
    C = EmployeeConcurrent
    concurrent_service.lock_employee_row(db, emp.id)                                      # N2
    #  Đọc-có-khóa + nạp lại: SELECT thường sau khóa vẫn đọc ảnh REPEATABLE READ cũ, không thấy dòng vừa chèn (N1).
    rows = (db.query(C).filter(C.employee_id == emp.id, or_(*conds)).order_by(C.id.asc())
            .with_for_update(read=True).populate_existing().all())
    ending, removing = [], []
    for row in rows:
        if row.to_date is not None and row.to_date < today:
            continue
        (removing if row.from_date is not None and row.from_date >= today else ending).append(row)

    if removing and import_mode:
        raise HTTPException(400, IMPORT_UNSTARTED_ERROR)
    from app.modules.company.model import Company

    dept_names = _names(db, Department, [r.department_id for r in ending + removing])
    company_names = _names(db, Company, [r.company_id for r in ending + removing])
    for row in removing:
        _block_file_loss(db, user_id, row)
    for row in ending:
        result.ended.append((row.id, row.to_date, yesterday))
        result.labels.append(f'{_row_label(row, dept_names, company_names)} (đến {yesterday.strftime("%d/%m/%Y")})')
        scope_before = concurrent_scope_audit.scope_state(row)
        row.to_date = yesterday
        row.updated_by = user_id
        if scope_before:
            concurrent_scope_audit.log_close(db, user_id, emp, scope_before, "kết thúc do đổi pháp nhân")
    if removing:
        from app.modules.attachment.service import delete_attachments_for

        delete_attachments_for(db, [("employee_concurrent", r.id) for r in removing], commit=False)
        for row in removing:
            result.labels.append(f'{_row_label(row, dept_names, company_names)} (chưa bắt đầu, đã xóa)')
            scope_before = concurrent_scope_audit.scope_state(row)
            db.delete(row)
            if scope_before:
                concurrent_scope_audit.log_close(db, user_id, emp, scope_before, "xóa do đổi pháp nhân")
        result.deleted = len(removing)
    db.flush()
    return result


# ── 2. Giữ kiêm nhiệm ở công ty cũ ───────────────────────────────────────────

def check_keep_company_seat(db: Session, emp: Employee, old_company_id: int, actor, profile: dict) -> None:
    """Các chốt L1 + L2 của "giữ kiêm nhiệm ở công ty cũ" — gọi SỚM, trước mọi thay đổi, để 403 là không đổi gì."""
    department_service.block_edit_own_department(db, emp.id, actor)                      # L1
    department_service.block_out_of_scope_concurrent(                                     # L2 loại Công ty
        db, [(ConcurrentKind.COMPANY, old_company_id, 0)], profile)


def keep_company_seat(db: Session, emp: Employee, old_company_id: int, actor, profile: dict,
                      today: date | None = None) -> bool:
    """Tạo MỘT dòng loại CÔNG TY (`old_company_id`, từ hôm nay, ghi chú `KEEP_SEAT_NOTE`). `True` nếu có tạo.

    Gọi SAU `end_rows_at_company` và SAU khi hồ sơ đã mang công ty mới. Bỏ qua (`False`) khi đã có dòng loại Công ty
    cùng công ty còn hiệu lực hoặc sắp tới, hoặc khi công ty cũ trống / trùng công ty chính mới. Đường duy nhất tạo
    dòng Công ty từ luồng đổi pháp nhân — nên qua đủ L1/L2 (`check_keep_company_seat`) như tab Kiêm nhiệm.
    """
    today = today or vn_today()
    if not old_company_id or old_company_id == (emp.company_id or 0):
        return False
    check_keep_company_seat(db, emp, old_company_id, actor, profile)
    concurrent_service.lock_employee_row(db, emp.id)                                      # N2
    C = EmployeeConcurrent
    live = (db.query(C.id).filter(C.employee_id == emp.id, C.kind == ConcurrentKind.COMPANY,
                                  C.company_id == old_company_id)
            .filter(or_(C.to_date.is_(None), C.to_date >= today)).with_for_update(read=True).first())   # N1
    if live:
        return False
    count = concurrent_service.locked_count(db, emp.id)
    if count >= concurrent_service.MAX_ROWS:
        raise HTTPException(400, f"Hồ sơ này đã có {count} dòng kiêm nhiệm — tối đa "
                                 f"{concurrent_service.MAX_ROWS} dòng/người, không giữ thêm công ty cũ được")
    row = C(employee_id=emp.id, kind=ConcurrentKind.COMPANY, company_id=old_company_id, department_id=0,
            position_id=0, position_label="", from_date=today, to_date=None, decision_no="",
            decision_date=None, note=KEEP_SEAT_NOTE, counts_scope=True,
            created_by=actor.id, updated_by=actor.id)
    db.add(row)
    db.flush()
    concurrent_scope_audit.log_transition(db, actor.id, emp, None, row)
    return True


# ── 3 + 4. Hoàn tác lô Nhập Excel ────────────────────────────────────────────

def restore_ended(db: Session, emp: Employee, entries, profile: dict, *, actor_id: int = 0) -> None:
    """Hoàn tác `end_rows_at_company`: trả `to_date` cũ. `entries` = `[[id, to_cũ|None, to_mới], ...]` (JSON bản chụp).

    Gọi SAU khi `revert_problems` đã kiểm; hàm vẫn kiểm lại L2 + chồng giai đoạn để không tin tuyệt đối bản chụp.
    `actor_id` = người hoàn tác (cho nhật ký mở phạm vi khi dòng loại Công ty được trả lại).
    """
    concurrent_service.lock_employee_row(db, emp.id)                                      # N2
    for cid, old_to, _new_to in entries:
        row = (db.query(EmployeeConcurrent).filter(EmployeeConcurrent.id == int(cid))
               .with_for_update().populate_existing().one_or_none())                              # N1
        if row is None or row.employee_id != emp.id:
            continue
        department_service.block_out_of_scope_concurrent(
            db, [(row.kind, row.company_id, row.department_id)], profile)
        restored = date.fromisoformat(old_to[:10]) if old_to else None
        concurrent_service.block_overlap(db, emp.id, row.kind, row.company_id, row.department_id,
                                         row.from_date, restored, exclude_id=row.id)
        row.to_date = restored
        db.flush()
        #  Dòng loại Công ty được trả lại về trước lúc kết thúc -> phạm vi mở lại (đã ghi "đóng" lúc đổi pháp nhân).
        if concurrent_scope_audit.scope_state(row):
            concurrent_scope_audit.log_open(db, actor_id, emp, row)
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
            department_service.block_out_of_scope_concurrent(
                db, [(row.kind, row.company_id, row.department_id)], profile)
            restored = date.fromisoformat(old_to[:10]) if old_to else None
            concurrent_service.block_overlap(db, emp.id, row.kind, row.company_id, row.department_id,
                                             row.from_date, restored, exclude_id=row.id)
        except HTTPException as e:
            problems.append(str(e.detail))
    return list(dict.fromkeys(problems))
