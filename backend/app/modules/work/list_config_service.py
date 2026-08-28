"""Phân hệ Công việc — cấu hình của một list: cột kanban · tag · nhãn tùy biến.

Ba thứ này cùng một luật quyền: **xem** thì thành viên nào cũng được (thẻ việc
phải vẽ được tên cột, màu tag), **sửa** thì phải từ ADMIN trở lên (04 §3).

Nhãn tùy biến (B-08) là "trường do list tự đặt" + "bộ giá trị của trường",
kiểu CHỌN MỘT. Ràng buộc chọn-một nằm ở unique `(task_id, field_id)` của
`tab_work_task_label`, không phải ở tệp này.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.modules.work import serializer as ser
from app.modules.work.label_model import (WorkLabelField, WorkLabelOption,
                                          WorkTag, WorkTaskLabel, WorkTaskTag)
from app.modules.work.membership_service import (CAN_MANAGE, Actor,
                                                 block_if_archived,
                                                 get_list_or_403)
from app.modules.work.task_model import WorkSection, WorkTask


# ── Cột kanban (section) ─────────────────────────────────────────────────────

def get_sections(db: Session, actor: Actor, list_id: int) -> list[dict]:
    get_list_or_403(db, actor, list_id)
    rows = (db.query(WorkSection).filter(WorkSection.list_id == list_id)
            .order_by(WorkSection.sort_order, WorkSection.id).all())
    return [ser.section_out(s) for s in rows]


def create_section(db: Session, actor: Actor, list_id: int, data) -> dict:
    lst = get_list_or_403(db, actor, list_id, CAN_MANAGE)
    block_if_archived(lst)
    s = WorkSection(company_id=actor.company_id, list_id=list_id,
                    name=data.name.strip(), color=data.color or "",
                    sort_order=data.sort_order or 0,
                    created_by=actor.user_id, updated_by=actor.user_id)
    db.add(s)
    db.commit()
    return ser.section_out(s)


def update_section(db: Session, actor: Actor, section_id: int, data) -> dict:
    s = db.get(WorkSection, section_id)
    if not s:
        raise HTTPException(404, "Không thấy cột này")
    lst = get_list_or_403(db, actor, s.list_id, CAN_MANAGE)
    block_if_archived(lst)
    for field in ("name", "color", "sort_order"):
        val = getattr(data, field, None)
        if val is not None:
            setattr(s, field, val)
    s.updated_by = actor.user_id
    db.commit()
    return ser.section_out(s)


#  Bước giãn khi đánh lại số thứ tự cột. Cùng luật với thẻ trong cột — lý do
#  đầy đủ ở `task_service.move_task`.
SECTION_STEP = 1000


def move_section(db: Session, actor: Actor, section_id: int,
                 before_section_id: int | None) -> list[dict]:
    """Kéo cột sang chỗ khác: đặt NGAY TRƯỚC `before_section_id`, `None` = cuối.

    Nhận mốc tương đối rồi đánh số lại CẢ danh sách cột, y như kéo thẻ: cột seed
    sẵn lúc tạo list mang `sort_order` 0·1·2, chèn kiểu "lấy số ở giữa" là hết
    khe ngay từ lần kéo thứ hai.

    Trả về CẢ danh sách cột sau khi xếp — nơi gọi cần bản mới để vẽ lại, xin
    thêm một lượt `GET /sections` chỉ tổ nhấp nháy.
    """
    s = db.get(WorkSection, section_id)
    if not s:
        raise HTTPException(404, "Không thấy cột này")
    lst = get_list_or_403(db, actor, s.list_id, CAN_MANAGE)
    block_if_archived(lst)

    rows = (db.query(WorkSection).filter(WorkSection.list_id == s.list_id)
            .order_by(WorkSection.sort_order, WorkSection.id).all())
    others = [r for r in rows if r.id != section_id]

    if before_section_id == section_id:
        pos = min(rows.index(s), len(others))      # "chèn trước chính nó" = đứng yên
    else:
        #  Mốc lạ (cột vừa bị người khác xóa) thì đẩy xuống cuối, đừng ném về đầu.
        pos = next((i for i, r in enumerate(others) if r.id == before_section_id),
                   len(others))

    others.insert(pos, s)
    for i, r in enumerate(others):
        r.sort_order = (i + 1) * SECTION_STEP
        r.updated_by = actor.user_id
    db.commit()
    record(db, actor.user_id, "work_task", lst.id, "update", f"Xếp lại cột: {s.name}")
    return [ser.section_out(r) for r in others]


def delete_section(db: Session, actor: Actor, section_id: int, move_to: int | None) -> None:
    """Xóa cột. Còn task thì BẮT chọn cột nhận trước — không bỏ task mồ côi.

    Task mồ côi (`section_id = NULL`) trên kanban là task biến mất khỏi màn hình
    mà vẫn nằm trong CSDL: người dùng tưởng mất việc.
    """
    s = db.get(WorkSection, section_id)
    if not s:
        raise HTTPException(404, "Không thấy cột này")
    lst = get_list_or_403(db, actor, s.list_id, CAN_MANAGE)
    block_if_archived(lst)

    left = (db.query(WorkTask)
            .filter(WorkTask.section_id == section_id, WorkTask.deleted_at.is_(None))
            .count())
    if left:
        if not move_to:
            raise HTTPException(400, f"Cột còn {left} việc — chọn cột nhận trước khi xóa")
        target = db.get(WorkSection, move_to)
        if not target or target.list_id != s.list_id:
            raise HTTPException(400, "Cột nhận phải thuộc cùng danh sách")
        (db.query(WorkTask).filter(WorkTask.section_id == section_id)
         .update({WorkTask.section_id: move_to}, synchronize_session=False))
    db.delete(s)
    db.commit()


# ── Tag ──────────────────────────────────────────────────────────────────────

def get_tags(db: Session, actor: Actor, list_id: int) -> list[dict]:
    get_list_or_403(db, actor, list_id)
    rows = (db.query(WorkTag).filter(WorkTag.list_id == list_id)
            .order_by(WorkTag.sort_order, WorkTag.id).all())
    return [ser.tag_out(t) for t in rows]


def create_tag(db: Session, actor: Actor, list_id: int, data) -> dict:
    lst = get_list_or_403(db, actor, list_id, CAN_MANAGE)
    block_if_archived(lst)
    if db.query(WorkTag).filter(WorkTag.list_id == list_id,
                                WorkTag.name == data.name.strip()).first():
        raise HTTPException(400, "Danh sách đã có tag tên này")
    t = WorkTag(company_id=actor.company_id, list_id=list_id, name=data.name.strip(),
                color=data.color or "", sort_order=data.sort_order or 0,
                created_by=actor.user_id, updated_by=actor.user_id)
    db.add(t)
    db.commit()
    return ser.tag_out(t)


def delete_tag(db: Session, actor: Actor, tag_id: int) -> None:
    t = db.get(WorkTag, tag_id)
    if not t:
        raise HTTPException(404, "Không thấy tag này")
    lst = get_list_or_403(db, actor, t.list_id, CAN_MANAGE)
    block_if_archived(lst)
    db.query(WorkTaskTag).filter(WorkTaskTag.tag_id == tag_id).delete(synchronize_session=False)
    db.delete(t)
    db.commit()


# ── Nhãn tùy biến (B-08) ─────────────────────────────────────────────────────

def get_label_fields(db: Session, actor: Actor, list_id: int) -> list[dict]:
    get_list_or_403(db, actor, list_id)
    fields = (db.query(WorkLabelField).filter(WorkLabelField.list_id == list_id)
              .order_by(WorkLabelField.sort_order, WorkLabelField.id).all())
    if not fields:
        return []
    opts = (db.query(WorkLabelOption)
            .filter(WorkLabelOption.field_id.in_([f.id for f in fields]))
            .order_by(WorkLabelOption.sort_order, WorkLabelOption.id).all())
    by_field: dict[int, list] = {}
    for o in opts:
        by_field.setdefault(o.field_id, []).append(o)
    return [ser.label_field_out(f, by_field.get(f.id, [])) for f in fields]


def create_label_field(db: Session, actor: Actor, list_id: int, data) -> dict:
    lst = get_list_or_403(db, actor, list_id, CAN_MANAGE)
    block_if_archived(lst)
    if db.query(WorkLabelField).filter(WorkLabelField.list_id == list_id,
                                       WorkLabelField.name == data.name.strip()).first():
        raise HTTPException(400, "Danh sách đã có trường nhãn tên này")
    f = WorkLabelField(company_id=actor.company_id, list_id=list_id,
                       name=data.name.strip(), sort_order=data.sort_order or 0,
                       created_by=actor.user_id, updated_by=actor.user_id)
    db.add(f)
    db.commit()
    return ser.label_field_out(f, [])


def delete_label_field(db: Session, actor: Actor, field_id: int) -> None:
    f = db.get(WorkLabelField, field_id)
    if not f:
        raise HTTPException(404, "Không thấy trường nhãn này")
    lst = get_list_or_403(db, actor, f.list_id, CAN_MANAGE)
    block_if_archived(lst)
    db.query(WorkTaskLabel).filter(WorkTaskLabel.field_id == field_id).delete(
        synchronize_session=False)
    db.query(WorkLabelOption).filter(WorkLabelOption.field_id == field_id).delete(
        synchronize_session=False)
    db.delete(f)
    db.commit()


def create_label_option(db: Session, actor: Actor, field_id: int, data) -> dict:
    f = db.get(WorkLabelField, field_id)
    if not f:
        raise HTTPException(404, "Không thấy trường nhãn này")
    lst = get_list_or_403(db, actor, f.list_id, CAN_MANAGE)
    block_if_archived(lst)
    if db.query(WorkLabelOption).filter(WorkLabelOption.field_id == field_id,
                                        WorkLabelOption.name == data.name.strip()).first():
        raise HTTPException(400, "Trường nhãn đã có giá trị tên này")
    o = WorkLabelOption(field_id=field_id, name=data.name.strip(), color=data.color or "",
                        sort_order=data.sort_order or 0,
                        created_by=actor.user_id, updated_by=actor.user_id)
    db.add(o)
    db.commit()
    return ser.label_option_out(o)


def delete_label_option(db: Session, actor: Actor, option_id: int) -> None:
    o = db.get(WorkLabelOption, option_id)
    if not o:
        raise HTTPException(404, "Không thấy giá trị nhãn này")
    f = db.get(WorkLabelField, o.field_id)
    lst = get_list_or_403(db, actor, f.list_id, CAN_MANAGE)
    block_if_archived(lst)
    db.query(WorkTaskLabel).filter(WorkTaskLabel.option_id == option_id).delete(
        synchronize_session=False)
    db.delete(o)
    db.commit()
