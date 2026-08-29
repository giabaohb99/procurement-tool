"""Phân hệ Công việc — cấu hình của một list: cột kanban · nhãn tùy biến.

Hai thứ này cùng một luật quyền: **xem** thì thành viên nào cũng được (thẻ việc
phải vẽ được tên cột, màu nhãn), **sửa** thì phải từ ADMIN trở lên (04 §3).

Nhãn tùy biến (B-08 + B-13) là "trường do list tự đặt" + "bộ giá trị của
trường", sáu kiểu. Luật "trường chọn-một chỉ giữ một giá trị" nằm ở
`label_value_service.write_value`, không phải ở tệp này.

**Tag cũng chỉ là một trường tùy biến** (kiểu CHỌN NHIỀU, tên "Tag") kể từ
migration `c8a1d4f60b72` — không còn bảng riêng và không còn CRUD riêng ở đây.
"""
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.audit import record
from app.modules.work import serializer as ser
from app.modules.work.label_model import (WorkLabelField, WorkLabelOption,
                                          WorkTaskLabel)
from app.modules.work.membership_service import (CAN_MANAGE, Actor,
                                                 block_if_archived,
                                                 get_list_or_403)
from app.modules.work.model import WorkLabelFieldType
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


def _clean_name(data, message: str) -> str | None:
    """Tên trong một lời gọi SỬA: `None` = không đổi, chuỗi rỗng = lỗi.

    Phân biệt hai thứ đó là điểm chính. Gộp lại thì lời gọi chỉ đổi màu (không
    gửi `name`) sẽ xóa trắng tên đang có, mà giá trị không tên thì trên thẻ việc
    là một chip rỗng không bấm sửa lại được.
    """
    name = getattr(data, "name", None)
    if name is None:
        return None
    name = name.strip()
    if not name:
        raise HTTPException(400, message)
    return name


# ── Nhãn tùy biến (B-08) ─────────────────────────────────────────────────────

#  Trường ĐỘ ƯU TIÊN nạp sẵn cho list mới. Bốn bậc y như cũ, nhưng từ nay chúng
#  là DỮ LIỆU của list: đổi tên, đổi màu, thêm bậc hay bỏ hẳn trường đều được.
PRIORITY_KEY = "priority"
PRIORITY_FIELD_NAME = "Độ ưu tiên"
PRIORITY_OPTIONS = [
    ("P1 — Khẩn", "red"),
    ("P2 — Cao", "orange"),
    ("P3 — Vừa", "sky"),
    ("P4 — Thấp", "slate"),
]

#  TAG nạp sẵn cho list mới nhưng KHÔNG mang `system_key`: nó là một trường tùy
#  biến bình thường kể từ migration `c8a1d4f60b72`, đổi tên hay xóa hẳn đều
#  được. Nạp không kèm giá trị nào — bộ tag của mỗi dự án mỗi khác.
TAG_FIELD_NAME = "Tag"


def seed_system_label_fields(db: Session, list_id: int, company_id: int, user_id: int) -> None:
    """Nạp bộ trường sẵn có cho một list VỪA TẠO. Không commit — nơi gọi commit.

    Gọi lại lần hai trên cùng một list là KHÔNG làm gì, để migration và
    `create_list` dùng chung được một đường.
    """
    da_co = (db.query(WorkLabelField)
             .filter(WorkLabelField.list_id == list_id,
                     WorkLabelField.system_key == PRIORITY_KEY).first())
    if da_co:
        return

    field = WorkLabelField(company_id=company_id, list_id=list_id,
                           name=PRIORITY_FIELD_NAME, sort_order=0,
                           field_type=int(WorkLabelFieldType.SINGLE),
                           system_key=PRIORITY_KEY,
                           created_by=user_id, updated_by=user_id)
    db.add(field)
    db.flush()
    for i, (name, color) in enumerate(PRIORITY_OPTIONS):
        db.add(WorkLabelOption(field_id=field.id, name=name, color=color, sort_order=i,
                               created_by=user_id, updated_by=user_id))

    #  Tên "Tag" có thể đã bị một trường do người dùng khai chiếm mất (unique
    #  `(list_id, name)`) — trùng thì thôi, không nạp, chứ đừng để cả lời gọi
    #  tạo dự án hỏng vì một trường tiện nghi.
    trung_ten = (db.query(WorkLabelField)
                 .filter(WorkLabelField.list_id == list_id,
                         WorkLabelField.name == TAG_FIELD_NAME).first())
    if not trung_ten:
        db.add(WorkLabelField(company_id=company_id, list_id=list_id,
                              name=TAG_FIELD_NAME, sort_order=1,
                              field_type=int(WorkLabelFieldType.MULTI),
                              system_key="",
                              created_by=user_id, updated_by=user_id))



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
    used = _count_values(db, [f.id for f in fields])
    return [ser.label_field_out(f, by_field.get(f.id, []), used.get(f.id, 0)) for f in fields]


def _count_values(db: Session, field_ids: list[int]) -> dict[int, int]:
    """Số giá trị ĐÃ GÁN cho việc, theo từng trường — giao diện khóa ô "kiểu
    trường" dựa vào đây."""
    if not field_ids:
        return {}
    rows = (db.query(WorkTaskLabel.field_id, func.count(WorkTaskLabel.id))
            .filter(WorkTaskLabel.field_id.in_(field_ids))
            .group_by(WorkTaskLabel.field_id).all())
    return {field_id: int(count) for field_id, count in rows}


def create_label_field(db: Session, actor: Actor, list_id: int, data) -> dict:
    lst = get_list_or_403(db, actor, list_id, CAN_MANAGE)
    block_if_archived(lst)
    if db.query(WorkLabelField).filter(WorkLabelField.list_id == list_id,
                                       WorkLabelField.name == data.name.strip()).first():
        raise HTTPException(400, "Danh sách đã có trường nhãn tên này")
    #  Kiểu lạ thì chặn ngay: lọt xuống CSDL là mọi nơi đọc `WorkLabelFieldType`
    #  đều ném `ValueError` và cả bảng kanban trắng trang.
    try:
        #  KHÔNG dùng `or 1`: `0 or 1` ra 1 nên kiểu 0 (không tồn tại) lọt qua
        #  thành "chọn một" một cách im lặng.
        raw = getattr(data, "field_type", None)
        kind = WorkLabelFieldType(int(1 if raw is None else raw))
    except ValueError:
        raise HTTPException(400, "Kiểu trường không hợp lệ")

    f = WorkLabelField(company_id=actor.company_id, list_id=list_id,
                       name=data.name.strip(), sort_order=data.sort_order or 0,
                       field_type=int(kind),
                       created_by=actor.user_id, updated_by=actor.user_id)
    db.add(f)
    db.commit()
    return ser.label_field_out(f, [])


def update_label_field(db: Session, actor: Actor, field_id: int, data) -> dict:
    """Đổi tên / kiểu / thứ tự một trường tùy biến."""
    f = db.get(WorkLabelField, field_id)
    if not f:
        raise HTTPException(404, "Không thấy trường nhãn này")
    lst = get_list_or_403(db, actor, f.list_id, CAN_MANAGE)
    block_if_archived(lst)

    name = _clean_name(data, "Tên trường không được để trống")
    if name is not None:
        if (db.query(WorkLabelField)
                .filter(WorkLabelField.list_id == f.list_id, WorkLabelField.name == name,
                        WorkLabelField.id != field_id).first()):
            raise HTTPException(400, "Danh sách đã có trường nhãn tên này")
        f.name = name

    kieu_moi = getattr(data, "field_type", None)
    if kieu_moi is not None and int(kieu_moi) != int(f.field_type):
        _assert_can_change_type(db, f)
        try:
            f.field_type = int(WorkLabelFieldType(int(kieu_moi)))
        except ValueError:
            raise HTTPException(400, "Kiểu trường không hợp lệ")

    if data.sort_order is not None:
        f.sort_order = data.sort_order
    f.updated_by = actor.user_id
    db.commit()

    opts = (db.query(WorkLabelOption).filter(WorkLabelOption.field_id == field_id)
            .order_by(WorkLabelOption.sort_order, WorkLabelOption.id).all())
    return ser.label_field_out(f, opts, _count_values(db, [field_id]).get(field_id, 0))


def _assert_can_change_type(db: Session, f: WorkLabelField) -> None:
    """Hai cửa chặn đổi KIỂU trường, cả hai đều là chặn mất dữ liệu:

    - **Trường hệ** (`system_key`) có mặt ở mọi dự án và có mã nguồn đọc theo
      kiểu của nó — đổi kiểu ở một dự án là chỗ khác đọc ra rỗng.
    - **Đã có giá trị gán cho việc**: mỗi kiểu ghi vào một cột `value_*` khác
      nhau, đổi kiểu là toàn bộ giá trị cũ nằm sai cột và biến mất khỏi giao
      diện — trong khi vẫn nằm nguyên dưới CSDL.
    """
    if f.system_key:
        raise HTTPException(400, "Trường hệ thống không đổi được kiểu")
    dang_dung = _count_values(db, [f.id]).get(f.id, 0)
    if dang_dung:
        raise HTTPException(
            400, f"{dang_dung} việc đang dùng trường này — xóa giá trị đã gán trước khi đổi kiểu")


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


def update_label_option(db: Session, actor: Actor, option_id: int, data) -> dict:
    """Sửa MỘT giá trị của trường tùy biến — sửa tại chỗ, task đang gán giữ nguyên.

    Cố ý không "xóa rồi tạo lại": xóa giá trị kéo theo `WorkTaskLabel` của mọi
    task đang gán nó, nên sửa lỗi chính tả một cái tên là mất sạch dữ liệu đã gán.
    """
    o = db.get(WorkLabelOption, option_id)
    if not o:
        raise HTTPException(404, "Không thấy giá trị nhãn này")
    f = db.get(WorkLabelField, o.field_id)
    if not f:
        raise HTTPException(404, "Không thấy trường nhãn này")
    lst = get_list_or_403(db, actor, f.list_id, CAN_MANAGE)
    block_if_archived(lst)

    name = _clean_name(data, "Tên giá trị không được để trống")
    if name is not None:
        if (db.query(WorkLabelOption)
                .filter(WorkLabelOption.field_id == o.field_id, WorkLabelOption.name == name,
                        WorkLabelOption.id != option_id).first()):
            raise HTTPException(400, "Trường nhãn đã có giá trị tên này")
        o.name = name
    if data.color is not None:
        o.color = data.color
    if data.sort_order is not None:
        o.sort_order = data.sort_order
    o.updated_by = actor.user_id
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
