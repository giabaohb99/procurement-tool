"""QUÁ TRÌNH CÔNG TÁC — đọc/ghi + validate (phase 02).

Chồng lấn/đóng dòng mở/cờ `can_apply` tách sang `work_history_rules.py`; gộp
tên + số tệp cho danh sách tách sang `work_history_serializer.py` — cả hai chỉ
vì lý do MODULARIZATION (tệp này đã gần 200 dòng), không phải khác nghiệp vụ.

Áp vào hồ sơ KHÔNG nằm ở đây — xem `work_history_apply_service.py` (A4: chỉ
qua `service.update_employee` / `department_service.set_extra_departments`).
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.hr_work_history_codes import MAIN_TRACK, POSITION_TRACK, WorkEventType

from .position_model import JobPosition
from .work_history_model import EmployeeWorkHistory
from .work_history_rules import close_open_main, overlap_warnings
from .work_history_schema import WorkHistoryIn, WorkHistoryUpdate

#  Validate #5 — trần 200 dòng/người (bảng «cha, mẹ, vợ/chồng» của hồ sơ đã có
#  trần riêng ở `field_limits.MAX_PEOPLE_ROWS`; đây là trần của bảng này).
MAX_ROWS = 200


def get_row_in_employee(db: Session, eid: int, hid: int) -> EmployeeWorkHistory:
    """`hid` PHẢI thuộc đúng `eid` — lệch là 404 (chặn IDOR chéo người, xem
    hợp đồng API). KHÔNG dùng `db.get` trần ở nơi gọi."""
    row = db.get(EmployeeWorkHistory, hid)
    if row is None or int(row.employee_id) != int(eid):
        raise HTTPException(404, "Không tìm thấy dòng quá trình công tác")
    return row


def list_rows(db: Session, eid: int) -> list[EmployeeWorkHistory]:
    """Xếp `from_date desc, id desc` — đúng hợp đồng API."""
    return (db.query(EmployeeWorkHistory)
            .filter(EmployeeWorkHistory.employee_id == eid)
            .order_by(EmployeeWorkHistory.from_date.desc(), EmployeeWorkHistory.id.desc())
            .all())


def check_row_cap(db: Session, eid: int) -> None:
    count = db.query(EmployeeWorkHistory).filter(EmployeeWorkHistory.employee_id == eid).count()
    if count >= MAX_ROWS:
        raise HTTPException(
            400, f"Hồ sơ này đã có {count} dòng quá trình công tác — tối đa {MAX_ROWS} dòng/người")


def _position_label(db: Session, position_id: int) -> str:
    """Nhãn CHỤP tại thời điểm ghi dòng — KHÔNG đi qua `position_service.sync_label`
    (lịch sử phải đứng yên, xem cảnh báo đầu `work_history_model.py`)."""
    if not position_id:
        return ""
    obj = db.get(JobPosition, position_id)
    return obj.name if obj else ""


def _check_close_open_main_scope(event_type: int, close_open_main: bool) -> None:
    """Low (review 03/10/2026) — `close_open_main` chỉ có nghĩa khi dòng ĐANG
    GHI là nhóm sự kiện CHÍNH (đóng một dòng chính đang mở để nhường chỗ cho
    dòng chính khác, validate #7). Gửi cờ này cho «Khác»/«Kiêm nhiệm» là báo
    sai nghiệp vụ — chặn 422 ngay, đừng âm thầm đóng nhầm một dòng không liên quan."""
    if close_open_main and WorkEventType(event_type) not in MAIN_TRACK:
        raise HTTPException(
            422, "close_open_main chỉ áp dụng cho nhóm sự kiện chính "
                 "(tuyển dụng/điều chuyển/bổ nhiệm/miễn nhiệm/thôi việc)")


def _check_required_fields(event_type: int, department_id: int, position_id: int) -> None:
    """Validate #3 — CONCURRENT bắt buộc phòng; nhóm vị trí chính (1,2,3,5) bắt
    ít nhất phòng hoặc chức vụ; RESIGN/OTHER không bắt gì (bỏ qua ba ô nếu gửi 0)."""
    et = WorkEventType(event_type)
    if et == WorkEventType.CONCURRENT and not department_id:
        raise HTTPException(400, "Kiêm nhiệm phải chọn phòng ban")
    if et in POSITION_TRACK and not (department_id or position_id):
        raise HTTPException(400, "Loại sự kiện này phải chọn ít nhất phòng ban hoặc chức vụ")


def _check_refs_exist(db: Session, company_id: int, department_id: int, position_id: int) -> None:
    """Validate #2 — id có thật; phòng + công ty cùng khai thì phòng phải thuộc
    công ty. Chức vụ NGỪNG DÙNG vẫn cho ghi vào lịch sử (validate #4) — chỉ
    kiểm TỒN TẠI, không kiểm `is_active` (khác `position_service.check_assignable`,
    chốt đó chỉ áp lúc ÁP vào hồ sơ)."""
    if company_id:
        from app.modules.company.model import Company
        if not db.get(Company, company_id):
            raise HTTPException(400, "Pháp nhân không tồn tại")

    dept = None
    if department_id:
        from app.modules.department.model import Department
        dept = db.get(Department, department_id)
        if not dept:
            raise HTTPException(400, "Phòng ban không tồn tại")

    if position_id and not db.get(JobPosition, position_id):
        raise HTTPException(400, "Chức vụ không tồn tại")

    if company_id and dept is not None and dept.company_id and dept.company_id != company_id:
        raise HTTPException(400, f"Phòng ban «{dept.name}» không thuộc pháp nhân đã chọn")


def create(db: Session, eid: int, data: WorkHistoryIn, actor
          ) -> tuple[EmployeeWorkHistory, list[str], list[str]]:
    """Trả (dòng mới, cảnh báo, dòng đã đóng do `close_open_main`). Chỉ `flush`
    — KHÔNG commit, xem «Một giao dịch» ở phase-02."""
    check_row_cap(db, eid)
    _check_required_fields(data.event_type, data.department_id, data.position_id)
    _check_refs_exist(db, data.company_id, data.department_id, data.position_id)
    _check_close_open_main_scope(data.event_type, data.close_open_main)

    row = EmployeeWorkHistory(
        employee_id=eid, event_type=data.event_type, from_date=data.from_date,
        to_date=data.to_date, company_id=data.company_id, department_id=data.department_id,
        position_id=data.position_id, position_label=_position_label(db, data.position_id),
        decision_no=data.decision_no, decision_date=data.decision_date, note=data.note,
        created_by=actor.id, updated_by=actor.id)
    db.add(row)
    db.flush()

    #  `close_open_main` TRƯỚC `overlap_warnings` (sửa 03/10/2026 — kiểm tay
    #  DevTools): đóng dòng chính đang mở rồi mới tính chồng lấn, không thì
    #  cảnh báo vẫn soi trúng dòng VỪA bị đóng (đã hết `to_date=None`, không
    #  còn chồng lấn thật) — xem test `test_qua_trinh_cong_tac_canh_bao_sau_dong.py`.
    closed = close_open_main(db, eid, row.from_date, actor.id) if data.close_open_main else []
    warnings = overlap_warnings(db, eid, row)
    return row, warnings, closed


def update(db: Session, eid: int, hid: int, data: WorkHistoryUpdate, actor
          ) -> tuple[EmployeeWorkHistory, list[str], list[str]]:
    """Cùng hình dạng trả về với `create`. Hợp nhất giá trị cũ + giá trị PATCH
    gửi lên TRƯỚC khi validate — màn hình chỉ gửi ô đã đổi."""
    row = get_row_in_employee(db, eid, hid)
    fields = data.model_dump(exclude_unset=True, exclude={"close_open_main", "apply_to_profile"})

    event_type = fields.get("event_type", row.event_type)
    department_id = fields.get("department_id", row.department_id)
    position_id = fields.get("position_id", row.position_id)
    company_id = fields.get("company_id", row.company_id)
    from_date = fields.get("from_date", row.from_date)
    to_date = fields["to_date"] if "to_date" in fields else row.to_date
    if to_date is not None and to_date < from_date:
        raise HTTPException(422, "Đến ngày phải sau hoặc bằng từ ngày")

    _check_required_fields(event_type, department_id, position_id)
    _check_refs_exist(db, company_id, department_id, position_id)
    _check_close_open_main_scope(event_type, data.close_open_main)

    for key, value in fields.items():
        setattr(row, key, value)
    if "position_id" in fields:
        row.position_label = _position_label(db, position_id)
    row.updated_by = actor.id
    db.flush()

    #  Cùng thứ tự với `create` ở trên — đóng TRƯỚC, tính chồng lấn SAU.
    closed = (close_open_main(db, eid, row.from_date, actor.id, exclude_id=row.id)
             if data.close_open_main else [])
    warnings = overlap_warnings(db, eid, row)
    return row, warnings, closed


def delete(db: Session, eid: int, hid: int, actor) -> None:
    """Xóa dòng + tệp đính kèm — `delete_attachments_for` tự commit nếu có tệp,
    rồi `db.commit()` ở đây chốt lại việc xóa dòng."""
    row = get_row_in_employee(db, eid, hid)
    from app.modules.attachment.service import delete_attachments_for
    delete_attachments_for(db, [("employee_work_history", row.id)])
    db.delete(row)
    db.commit()


def delete_all_of(db: Session, employee_id: int) -> None:
    """Dọn MỌI dòng + tệp của một người khi xóa hồ sơ cha (`service.delete_employee`
    gọi hàm này). KHÔNG tự `commit` — đi chung giao dịch với nơi gọi."""
    ids = [i for (i,) in db.query(EmployeeWorkHistory.id)
           .filter(EmployeeWorkHistory.employee_id == employee_id).all()]
    if not ids:
        return
    from app.modules.attachment.service import delete_attachments_for
    #  M7 (review 03/10/2026) — `commit=False`: giữ ĐÚNG một giao dịch với
    #  `service.delete_employee` (xem docstring `delete_attachments_for`).
    delete_attachments_for(db, [("employee_work_history", i) for i in ids], commit=False)
    db.query(EmployeeWorkHistory).filter(
        EmployeeWorkHistory.employee_id == employee_id).delete(synchronize_session=False)
