"""Nghiệp vụ GÁN LỊCH: kiểm đích/mẫu có thật, CẤM chồng khoảng ngày, tự đóng dòng "không
thời hạn" cũ khi TẠO dòng mới (chốt 05/10/2026), gắn tên đích bằng truy vấn gom.
"""
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.crud import commit_or_conflict
from app.core.vn_time import vn_today
from app.core.work_schedule_codes import WORK_SCHEDULE_LEVEL_LABELS, WorkScheduleLevel
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee

from .assignment_schema import (AssignmentCreate, AssignmentUpdate, check_period,
                                check_target)
from .assignment_heal import (clear_links, closed_link_ids, find_replaced_and_resume,
                              heal_before_delete, move_resume)
from .model import WorkSchedule, WorkScheduleAssignment

ENTITY = "work_schedule"
SYSTEM_NAME = "Toàn hệ thống"
CONFLICT_MESSAGE = ("Đối tượng này đã có dòng gán lịch bắt đầu cùng ngày (có thể vừa được tạo "
                    "ở nơi khác). Tải lại danh sách rồi thử lại.")


def _fmt(d: date | None) -> str:
    return d.strftime("%d/%m/%Y") if d else "…"


def target_names(db: Session, rows: list[WorkScheduleAssignment]) -> dict[tuple[int, int], str]:
    """`{(cấp, id): tên}` bằng tối đa 3 truy vấn (pháp nhân / phòng ban / nhân sự)."""
    want: dict[int, set[int]] = {}
    for a in rows:
        want.setdefault(a.target_level, set()).add(a.target_id)
    out: dict[tuple[int, int], str] = {}
    if int(WorkScheduleLevel.SYSTEM) in want:
        out[(int(WorkScheduleLevel.SYSTEM), 0)] = SYSTEM_NAME
    for level, model, col in ((WorkScheduleLevel.COMPANY, Company, "name"),
                              (WorkScheduleLevel.DEPARTMENT, Department, "name"),
                              (WorkScheduleLevel.EMPLOYEE, Employee, "full_name")):
        ids = want.get(int(level))
        if ids:
            for r in db.query(model).filter(model.id.in_(ids)).all():
                out[(int(level), r.id)] = getattr(r, col) or ""
    return out


def serialize_many(db: Session, rows: list[WorkScheduleAssignment]) -> list[dict]:
    names = target_names(db, rows)
    sids = {a.schedule_id for a in rows}
    scheds = ({s.id: s.name for s in db.query(WorkSchedule).filter(WorkSchedule.id.in_(sids)).all()}
              if sids else {})
    today = vn_today()   # giờ VN — container chạy UTC
    replacing = closed_link_ids(db, [a.id for a in rows])   # một truy vấn cho cả trang
    out = []
    for a in rows:
        level = WorkScheduleLevel(a.target_level)
        out.append({
            "id": a.id, "target_level": a.target_level,
            "target_level_label": WORK_SCHEDULE_LEVEL_LABELS[level],
            "target_id": a.target_id, "target_name": names.get((a.target_level, a.target_id), ""),
            "schedule_id": a.schedule_id, "schedule_name": scheds.get(a.schedule_id, ""),
            "effective_from": a.effective_from, "effective_to": a.effective_to,
            "note": a.note or "",
            "replaces_previous": a.id in replacing,   # dòng này đã tự đóng một dòng khác: không đổi đích / ngày bắt đầu
            "created_by": a.created_by,   # id TÀI KHOẢN người gán: giao diện ẩn Sửa / Xóa với dòng Trưởng phòng không tự gán
            "is_current": a.effective_from <= today and (a.effective_to is None or a.effective_to >= today),
        })
    return out


def _check_target_exists(db: Session, level: int, target_id: int) -> None:
    model = {int(WorkScheduleLevel.COMPANY): Company, int(WorkScheduleLevel.DEPARTMENT): Department,
             int(WorkScheduleLevel.EMPLOYEE): Employee}.get(level)
    if model is not None and db.get(model, target_id) is None:
        raise HTTPException(400, "Đối tượng được gán lịch không tồn tại")


def _check_schedule(db: Session, schedule_id: int, must_be_active: bool) -> None:
    #  Khóa dòng mẫu đến hết giao dịch: `delete_schedule` cũng khóa dòng này nên "đếm gán rồi xóa"
    #  không còn chen vào giữa "kiểm mẫu rồi chèn gán" (bug L4: gán trỏ vào mẫu vừa bị xóa).
    sched = (db.query(WorkSchedule).filter(WorkSchedule.id == schedule_id)
             .with_for_update().first())
    if sched is None:
        raise HTTPException(400, "Mẫu lịch không tồn tại")
    if must_be_active and not sched.is_active:
        raise HTTPException(400, f"Mẫu lịch \"{sched.name}\" đã tắt, không gán thêm được")


def _overlaps(db: Session, level: int, target_id: int, start: date, end: date | None,
              exclude_id: int = 0, exclude_ids: frozenset[int] = frozenset()) -> list[WorkScheduleAssignment]:
    """Dòng cùng đối tượng giao khoảng `[start, end]` (end None = vô hạn). Trùng mép 1 ngày cũng là chồng."""
    #  `with_for_update()` khóa các dòng của đối tượng: hai lệnh tạo sát nhau phải xếp hàng, người
    #  sau mới thấy dòng người trước vừa chèn (bug M2). SQLite bỏ qua. Chốt cuối là UNIQUE ở DB.
    q = db.query(WorkScheduleAssignment).with_for_update().filter(
        WorkScheduleAssignment.target_level == level,
        WorkScheduleAssignment.target_id == target_id,
        or_(WorkScheduleAssignment.effective_to.is_(None),
            WorkScheduleAssignment.effective_to >= start))
    if end is not None:
        q = q.filter(WorkScheduleAssignment.effective_from <= end)
    skip = set(exclude_ids) | ({exclude_id} if exclude_id else set())
    if skip:
        q = q.filter(WorkScheduleAssignment.id.notin_(skip))
    return q.order_by(WorkScheduleAssignment.effective_from).all()


def _raise_overlap(db: Session, a: WorkScheduleAssignment) -> None:
    sched = db.get(WorkSchedule, a.schedule_id)
    name = target_names(db, [a]).get((a.target_level, a.target_id), "")
    raise HTTPException(
        400, f"Đã có lịch \"{sched.name if sched else a.schedule_id}\" gán cho \"{name}\" từ "
             f"{_fmt(a.effective_from)} đến {_fmt(a.effective_to)}; đặt \"Đến ngày\" cho dòng đó trước.")


def create_assignment(db: Session, data: AssignmentCreate, user) -> WorkScheduleAssignment:
    _check_target_exists(db, data.target_level, data.target_id)
    _check_schedule(db, data.schedule_id, must_be_active=True)
    hits = _overlaps(db, data.target_level, data.target_id, data.effective_from, data.effective_to)
    #  Chỉ dòng "không thời hạn" BẮT ĐẦU TRƯỚC `from` mới được tự đóng; chồng kiểu khác → 400.
    closable = [a for a in hits if a.effective_to is None and a.effective_from < data.effective_from]
    for a in hits:
        if a not in closable:
            _raise_overlap(db, a)
    new_end = data.effective_from - timedelta(days=1)
    #  Lịch mới CÓ hạn = lịch tạm (VD một tháng làm ca khác): hết hạn thì người đó phải QUAY LẠI
    #  lịch cũ, không được rơi tụt xuống lịch phòng ban/hệ thống. Nên dòng cũ bị cắt đôi: nửa đầu
    #  đóng ở `from − 1`, nửa sau mở lại "không thời hạn" từ `to + 1`. Không chồng với dòng nào
    #  khác được, vì mọi dòng khác của đối tượng này vốn đã không chồng với dòng cũ vô hạn.
    resumes: list[WorkScheduleAssignment] = []
    for a in closable:
        a.effective_to = new_end
        a.updated_by = user.id
        if data.effective_to is not None:
            resumes.append(WorkScheduleAssignment(
                target_level=a.target_level, target_id=a.target_id, schedule_id=a.schedule_id,
                effective_from=data.effective_to + timedelta(days=1), effective_to=None,
                note=a.note or "", created_by=a.created_by, updated_by=user.id))   # giữ NGƯỜI GÁN gốc (duoc-CR-757 N4a)
    obj = WorkScheduleAssignment(**data.model_dump(), created_by=user.id, updated_by=user.id)
    db.add(obj)
    try:
        db.flush()   # cần `obj.id` để đánh dấu dòng bị đóng/nối (xóa dòng này sẽ mở lại, M4)
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, CONFLICT_MESSAGE) from None
    for a in (*closable, *resumes):
        a.linked_assignment_id = obj.id
    db.add_all(resumes)
    commit_or_conflict(db, CONFLICT_MESSAGE)
    db.refresh(obj)
    for a in closable:
        record(db, user.id, ENTITY, a.id, "update",
               f"Tự đóng dòng gán đến {_fmt(new_end)} do gán lịch mới từ {_fmt(data.effective_from)}")
    for r in resumes:
        record(db, user.id, ENTITY, r.id, "create",
               f"Tự nối lại lịch cũ từ {_fmt(r.effective_from)} sau lịch tạm đến {_fmt(data.effective_to)}")
    record(db, user.id, ENTITY, obj.id, "create", "Gán lịch làm việc")
    return obj


def update_assignment(db: Session, obj: WorkScheduleAssignment, data: AssignmentUpdate,
                      user) -> WorkScheduleAssignment:
    values = data.model_dump(exclude_unset=True)
    #  `effective_to` được phép set None (mở lại "không thời hạn"); các trường khác None = bỏ qua.
    for key in ("target_level", "target_id", "schedule_id", "effective_from", "note"):
        if key in values and values[key] is None:
            values.pop(key)
    level = values.get("target_level", obj.target_level)
    target_id = values.get("target_id", obj.target_id)
    start = values.get("effective_from", obj.effective_from)
    end = values["effective_to"] if "effective_to" in values else obj.effective_to
    try:
        check_target(level, target_id)
        check_period(start, end)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if (level, target_id) != (obj.target_level, obj.target_id):
        _check_target_exists(db, level, target_id)
    if "schedule_id" in values and values["schedule_id"] != obj.schedule_id:
        _check_schedule(db, values["schedule_id"], must_be_active=True)
    #  Chỉ đổi NGÀY KẾT THÚC của dòng đã tự đóng một dòng khác (dòng thay lịch tạm): dòng bị đóng phải nối lại liền
    #  mạch từ ngày kết thúc mới — tạo / dời / xóa bản nối lại cho khớp (duoc-CR-757), không gỡ liên kết như đổi ngày bắt đầu.
    end_only = (level, target_id, start) == (obj.target_level, obj.target_id, obj.effective_from) \
        and end != obj.effective_to
    prev, resume = find_replaced_and_resume(db, obj) if end_only else (None, None)
    follow = prev is not None and (obj.effective_to is None or resume is not None)
    skip = frozenset({obj.id} | ({resume.id} if follow and resume is not None else set()))
    #  PATCH KHÔNG BAO GIỜ tự đóng dòng khác — chỉ POST mới có đặc cách đó.
    for other in _overlaps(db, level, target_id, start, end, exclude_ids=skip):
        _raise_overlap(db, other)
    audits: list[tuple[int, str]] = []
    if follow:
        if end is not None:
            if resume is not None and resume.effective_to is not None and end >= resume.effective_to:
                raise HTTPException(400, "Ngày kết thúc mới chồng hết khoảng lịch cũ được nối lại; "
                                         "hãy xóa dòng nối lại hoặc chọn ngày sớm hơn")
            for other in _overlaps(db, level, target_id, end + timedelta(days=1),
                                   resume.effective_to if resume is not None else None, exclude_ids=skip):
                _raise_overlap(db, other)
        audits = move_resume(db, obj, prev, resume, end, user.id)
    #  Đổi ngày/đích của dòng gốc → mở lại khi xóa không còn an toàn: gỡ liên kết (M4).
    elif (level, target_id, start, end) != (obj.target_level, obj.target_id,
                                            obj.effective_from, obj.effective_to):
        clear_links(db, obj.id)
    for k, v in values.items():
        setattr(obj, k, v)
    obj.updated_by = user.id
    commit_or_conflict(db, CONFLICT_MESSAGE)
    db.refresh(obj)
    record(db, user.id, ENTITY, obj.id, "update", "Sửa gán lịch làm việc")
    for rid, text in audits:
        record(db, user.id, ENTITY, rid, "update", text)
    return obj


def delete_assignment(db: Session, obj: WorkScheduleAssignment, user) -> None:
    oid = obj.id
    audits = heal_before_delete(db, obj, user.id)
    db.delete(obj)
    db.commit()
    record(db, user.id, ENTITY, oid, "delete", "Xóa gán lịch làm việc")
    for rid, text in audits:
        record(db, user.id, ENTITY, rid, "update", text)
