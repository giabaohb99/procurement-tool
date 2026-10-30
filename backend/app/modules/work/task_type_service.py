"""Danh mục loại việc — CRUD (duoc-CR-656, D1b). Ghi chỉ dành cho quản trị (`setting.write`), đọc ai dùng Dự án cũng được.

Không xóa cứng loại đã có task dùng: chuyển `is_active = 0` để số liệu năng lực cũ vẫn đọc được tên.
"""
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.audit import record
from app.modules.work.audit_entity import AUDIT_TASK_TYPE
from app.modules.work.task_model import WorkTask
from app.modules.work.task_type_model import WorkTaskType


def type_out(t: WorkTaskType, used: int = 0) -> dict:
    return {
        "id": t.id, "company_id": t.company_id, "department_id": t.department_id,
        "code": t.code, "name": t.name,
        #  Chuỗi, không phải float: cùng lý do `value_number` ở `serializer.task_label_out`.
        "default_estimate_hours": None if t.default_estimate_hours is None else str(t.default_estimate_hours),
        "is_active": bool(t.is_active), "sort_order": t.sort_order, "task_count": used,
    }


#  Cột cho phép sắp xếp (whitelist — tên lạ bị bỏ qua, về thứ tự mặc định).
SORT_COLUMNS = {"code": WorkTaskType.code, "name": WorkTaskType.name, "sort_order": WorkTaskType.sort_order,
                "is_active": WorkTaskType.is_active, "updated_at": WorkTaskType.updated_at}
MAX_PAGE_SIZE = 500


def list_types(db: Session, *, company_id: int | None = None, is_active: bool | None = None, q: str = "",
               page: int = 1, page_size: int = 200, sort_by: str = "", sort_dir: str = "asc") -> dict:
    """`{total, items}` — cùng hình dạng danh mục chung (`make_crud_router`) để dùng được `CrudListPage`.

    `company_id` có giá trị: loại của pháp nhân đó + loại dùng chung (company_id = 0). Không truyền thì trả tất cả:
    nhân sự phần lớn chưa gắn pháp nhân (`company_id = 0`), lọc theo pháp nhân của người xem sẽ làm ô chọn trống trơn.
    `is_active=None` = cả loại đã ngừng (màn quản trị); ô chọn của task truyền `True`.
    """
    query = db.query(WorkTaskType)
    if company_id:
        query = query.filter(WorkTaskType.company_id.in_([0, company_id]))
    if is_active is not None:
        query = query.filter(WorkTaskType.is_active.is_(is_active))
    needle = (q or "").strip()
    if needle:
        like = f"%{needle}%"
        query = query.filter(WorkTaskType.name.like(like) | WorkTaskType.code.like(like))
    total = query.count()
    col = SORT_COLUMNS.get(sort_by)
    order = [(col.desc() if sort_dir == "desc" else col.asc())] if col is not None else [WorkTaskType.sort_order]
    page_size = max(1, min(int(page_size or 200), MAX_PAGE_SIZE))
    rows = (query.order_by(*order, WorkTaskType.id).offset((max(1, page) - 1) * page_size).limit(page_size).all())
    used = _usage_counts(db, [r.id for r in rows])
    return {"total": total, "items": [type_out(r, used.get(r.id, 0)) for r in rows]}


def _usage_counts(db: Session, ids: list[int]) -> dict[int, int]:
    if not ids:
        return {}
    rows = (db.query(WorkTask.task_type_id, func.count(WorkTask.id))
            .filter(WorkTask.task_type_id.in_(ids), WorkTask.deleted_at.is_(None))
            .group_by(WorkTask.task_type_id).all())
    return {int(i): int(n) for i, n in rows}


def _check_unique(db: Session, company_id: int, code: str, except_id: int = 0) -> None:
    q = db.query(WorkTaskType.id).filter(WorkTaskType.company_id == company_id, WorkTaskType.code == code)
    if except_id:
        q = q.filter(WorkTaskType.id != except_id)
    if q.first():
        raise HTTPException(409, f"Mã loại việc \"{code}\" đã có trong pháp nhân này")


def _clean(text: str, label: str) -> str:
    out = (text or "").strip()
    if not out:
        raise HTTPException(422, f"{label} không được để trống")
    return out


def _hours_or_none(v):
    """`0` coi như chưa khai — một loại việc không có "ước lượng mặc định 0 giờ"."""
    return v if v else None


def create_type(db: Session, user_id: int, data) -> dict:
    code = _clean(data.code, "Mã loại việc")
    _check_unique(db, data.company_id, code)
    t = WorkTaskType(company_id=data.company_id, department_id=data.department_id, code=code,
                     name=_clean(data.name, "Tên loại việc"),
                     default_estimate_hours=_hours_or_none(data.default_estimate_hours),
                     sort_order=data.sort_order, created_by=user_id, updated_by=user_id)
    db.add(t)
    db.commit()
    record(db, user_id, AUDIT_TASK_TYPE, t.id, "create", f"Tạo loại việc: {t.name}")
    return type_out(t)


def _get(db: Session, type_id: int) -> WorkTaskType:
    t = db.get(WorkTaskType, type_id)
    if not t:
        raise HTTPException(404, "Không thấy loại việc")
    return t


def update_type(db: Session, user_id: int, type_id: int, data) -> dict:
    t = _get(db, type_id)
    if data.code is not None:
        code = _clean(data.code, "Mã loại việc")
        if code != t.code:
            _check_unique(db, t.company_id, code, except_id=t.id)
            t.code = code
    if data.name is not None:
        t.name = _clean(data.name, "Tên loại việc")
    if data.department_id is not None:
        t.department_id = data.department_id
    if "default_estimate_hours" in data.model_fields_set:
        t.default_estimate_hours = _hours_or_none(data.default_estimate_hours)
    if data.is_active is not None:
        t.is_active = data.is_active
    if data.sort_order is not None:
        t.sort_order = data.sort_order
    t.updated_by = user_id
    db.commit()
    record(db, user_id, AUDIT_TASK_TYPE, t.id, "update", f"Sửa loại việc: {t.name}")
    return type_out(t, _usage_counts(db, [t.id]).get(t.id, 0))


def delete_type(db: Session, user_id: int, type_id: int) -> dict:
    """Chưa ai dùng → xóa hẳn; đã có task dùng → chỉ tắt. Trả `{"deleted": bool}` cho giao diện biết."""
    t = _get(db, type_id)
    used = _usage_counts(db, [t.id]).get(t.id, 0)
    if used:
        t.is_active = False
        t.updated_by = user_id
        db.commit()
        record(db, user_id, AUDIT_TASK_TYPE, t.id, "update", f"Ngừng dùng loại việc: {t.name}")
        return {"deleted": False, "is_active": False, "task_count": used}
    name = t.name
    db.delete(t)
    db.commit()
    record(db, user_id, AUDIT_TASK_TYPE, type_id, "delete", f"Xóa loại việc: {name}")
    return {"deleted": True}


def require_active_type(db: Session, type_id: int) -> WorkTaskType:
    """Dùng khi gán loại cho task: loại phải tồn tại và còn dùng."""
    t = db.get(WorkTaskType, type_id)
    if not t or not t.is_active:
        raise HTTPException(422, "Loại việc không tồn tại hoặc đã ngừng dùng")
    return t
